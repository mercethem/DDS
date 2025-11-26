#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast DDS QoS Patcher

Purpose:
- Automatically, safely and compatibly apply DataWriter/DataReader QoS settings
  in Fast DDS sample code (fastddsgen outputs).
- User only selects HistoryQosPolicy; other policies are systematically assigned
  with standard, safe, production-compatible defaults.

Compatibility Requirement:
- All QoS fields match Fast DDS QoS standards exactly.
- All changes are cancelled if incompatibility/empty value/invalid type is detected.

Supported target files:
- IDL/*_idl_generated/*PublisherApp.cxx
- IDL/*_idl_generated/*SubscriberApp.cxx

Notes:
- Injections are idempotent (marker-based). Does not add again on second run.
- Original files are backed up before processing.
"""

import os
import re
import sys
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ————————————————————————————————————————————————————————————————————————
# User input model and constants
# ————————————————————————————————————————————————————————————————————————

HISTORY_KIND_ALLOWED = {"KEEP_LAST", "KEEP_ALL"}

# Fast DDS enum/value sets (for validation)
FASTDDS_QOS_ENUMS = {
    "ReliabilityQosPolicyKind": {"RELIABLE_RELIABILITY_QOS", "BEST_EFFORT_RELIABILITY_QOS"},
    "DurabilityQosPolicyKind": {"VOLATILE_DURABILITY_QOS", "TRANSIENT_LOCAL_DURABILITY_QOS"},
    "HistoryQosPolicyKind": {"KEEP_LAST_HISTORY_QOS", "KEEP_ALL_HISTORY_QOS"},
    "LivelinessQosPolicyKind": {
        "AUTOMATIC_LIVELINESS_QOS",
        "MANUAL_BY_TOPIC_LIVELINESS_QOS",
        "MANUAL_BY_PARTICIPANT_LIVELINESS_QOS",
    },
    "DestinationOrderQosPolicyKind": {
        "BY_RECEPTION_TIMESTAMP_DESTINATIONORDER_QOS",
        "BY_SOURCE_TIMESTAMP_DESTINATIONORDER_QOS",
    },
    "OwnershipQosPolicyKind": {"SHARED_OWNERSHIP_QOS", "EXCLUSIVE_OWNERSHIP_QOS"},
    "PresentationQosPolicyAccessScopeKind": {
        "INSTANCE_PRESENTATION_QOS",
        "TOPIC_PRESENTATION_QOS",
        "GROUP_PRESENTATION_QOS",
    },
}

# Default, safe and balanced QoS set (History comes from user)
DEFAULT_QOS = {
    "writer": {
        "reliability": "RELIABLE_RELIABILITY_QOS",
        "durability": "VOLATILE_DURABILITY_QOS",
        "liveliness": "AUTOMATIC_LIVELINESS_QOS",
        "destination_order": "BY_RECEPTION_TIMESTAMP_DESTINATIONORDER_QOS",
        "ownership": "SHARED_OWNERSHIP_QOS",
        "ownership_strength": 0,
        # history.kind, history.depth will come from user
        "resource_limits": {
            "max_samples": 1000,
            "allocated_samples": 50,
        },
        "publish_mode_async": True,
    },
    "reader": {
        "reliability": "RELIABLE_RELIABILITY_QOS",
        "durability": "VOLATILE_DURABILITY_QOS",
        "liveliness": "AUTOMATIC_LIVELINESS_QOS",
        "destination_order": "BY_RECEPTION_TIMESTAMP_DESTINATIONORDER_QOS",
        "ownership": "SHARED_OWNERSHIP_QOS",
        # history.kind, history.depth will come from user
        "resource_limits": {
            "max_samples": 1000,
            "allocated_samples": 50,
        },
    },
    "topic": {
        # keep defaults minimal here; extend as needed
    },
    "subscriber": {
        "presentation": {
            "access_scope": "INSTANCE_PRESENTATION_QOS",
            "coherent_access": False,
            "ordered_access": False,
        },
        "partition": {
            "names": [],
        },
    },
    "publisher": {
        "presentation": {
            "access_scope": "INSTANCE_PRESENTATION_QOS",
            "coherent_access": False,
            "ordered_access": False,
        },
        "partition": {
            "names": [],
        },
    },
}


# ————————————————————————————————————————————————————————————————————————
# Helpers
# ————————————————————————————————————————————————————————————————————————

def _project_root() -> Path:
    """Dynamically detect project root directory."""
    try:
        script_dir = Path(__file__).parent
    except NameError:
        script_dir = Path.cwd()
    
    current_dir = script_dir
    
    # Walk up the directory tree to find project root
    while current_dir != current_dir.parent:
        if (current_dir / "IDL").exists() and (current_dir / "scenarios").exists():
            return current_dir
        current_dir = current_dir.parent
    
    # Fallback logic
    if script_dir.name == 'py' and script_dir.parent.name == 'scripts':
        return script_dir.parent.parent
    elif script_dir.name in ['bat', 'sh'] and script_dir.parent.name == 'scripts':
        return script_dir.parent.parent
    elif script_dir.name == 'scripts':
        return script_dir.parent
    elif script_dir.name in ['sh', 'bat'] and script_dir.parent.name == 'init':
        return script_dir.parent.parent
    else:
        return Path.cwd()


def _find_target_files() -> List[Path]:
    root = _project_root()
    patterns = [
        "IDL/*_idl_generated/*PublisherApp.cxx",
        "IDL/*_idl_generated/*SubscriberApp.cxx",
    ]
    results: List[Path] = []
    for p in patterns:
        results.extend(root.glob(p))
    return [r for r in results if r.is_file()]


def _group_targets_by_module(files: List[Path]) -> Dict[str, Dict[str, Path]]:
    grouped: Dict[str, Dict[str, Path]] = {}
    for f in files:
        # .../IDL/<Module>_idl_generated/<Module>PublisherApp.cxx
        try:
            gen_dir = f.parent
            module_dirname = gen_dir.name  # <Module>_idl_generated
            module = module_dirname.replace("_idl_generated", "")
        except Exception:
            continue

        role = "publisher" if f.name.endswith("PublisherApp.cxx") else "subscriber"
        grouped.setdefault(module, {})[role] = f
    return grouped


def _print_target_variations(grouped: Dict[str, Dict[str, Path]]) -> None:
    print("")
    print("=== Current IDL Modules and Variations ===")
    if not grouped:
        print("(empty)")
        return
    idx = 1
    for module, roles in grouped.items():
        role_list = []
        if "publisher" in roles:
            role_list.append("Publisher")
        if "subscriber" in roles:
            role_list.append("Subscriber")
        print(f"[{idx}] {module} — {', '.join(role_list)}")
        # Sub-paths
        for r, p in roles.items():
            print(f"     - {r}: {p}")
        idx += 1


def _get_user_module_selection(grouped: Dict[str, Dict[str, Path]]) -> List[str]:
    modules = list(grouped.keys())
    if not modules:
        return []
    print("")
    print("Module selection: 'all' or numbers (e.g: 1,3) → Enter")
    sel = input("Selection: ").strip().lower()
    if sel in ("", "all", "*"):
        return modules
    chosen: List[str] = []
    for part in re.split(r"[\s,;]+", sel):
        if not part:
            continue
        if not part.isdigit():
            print(f"Ignored: {part}")
            continue
        i = int(part)
        if 1 <= i <= len(modules):
            chosen.append(modules[i - 1])
        else:
            print(f"Out of range: {i}")
    return list(dict.fromkeys(chosen))


def _get_user_role_selection() -> str:
    print("")
    print("Variation selection:")
    print("1) Publisher")
    print("2) Subscriber")
    print("3) Both")
    while True:
        s = input("Selection (1-3): ").strip()
        if s == "1":
            return "publisher"
        if s == "2":
            return "subscriber"
        if s == "3":
            return "both"
        print("Invalid selection.")


def backup_files(files: List[Path]) -> List[Path]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backups: List[Path] = []
    for f in files:
        bak = f.with_suffix(f.suffix + f".bak.{timestamp}")
        shutil.copy2(str(f), str(bak))
        backups.append(bak)
    return backups


def display_qos_menu() -> None:
    print("")
    print("=== QoS Modu ===")
    print("1) Simple: History only (recommended)")
    print("2) Advanced: All Reader/Writer QoS (with enums)")


def get_history_input() -> Dict[str, Optional[int]]:
    while True:
        sel = input("Selection (1-2): ").strip()
        if sel not in {"1", "2"}:
            print("Invalid selection. Enter 1 or 2.")
            continue

        if sel == "1":
            kind = "KEEP_LAST"
            depth_str = input("History depth (positive integer, e.g: 20): ").strip()
            if not depth_str.isdigit() or int(depth_str) <= 0:
                print("Invalid depth. Enter positive integer.")
                continue
            return {"kind": kind, "depth": int(depth_str)}
        else:
            kind = "KEEP_ALL"
            return {"kind": kind, "depth": None}


def _choose_enum(prompt: str, options: List[str], default_index: int = 0) -> str:
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        raw = input(f"{prompt} ({default_index+1}): ").strip()
        if raw == "":
            return options[default_index]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Invalid selection.")


def get_advanced_qos_inputs(base_qos: Dict[str, Dict], roles: str) -> Tuple[Dict, Dict, Dict[str, Optional[int]]]:
    print("")
    print("=== Advanced QoS: Reader/Writer ===")
    # History
    print("History.kind:")
    hist_kind = _choose_enum("Selection", ["KEEP_LAST", "KEEP_ALL"], 0)
    if hist_kind == "KEEP_LAST":
        while True:
            d = input("History depth (positive integer, default 10): ").strip()
            if d == "":
                hist = {"kind": "KEEP_LAST", "depth": 10}
                break
            if d.isdigit() and int(d) > 0:
                hist = {"kind": "KEEP_LAST", "depth": int(d)}
                break
                print("Invalid value.")
    else:
        hist = {"kind": "KEEP_ALL", "depth": None}

    # Enums for both roles
    rel_opts = sorted(list(FASTDDS_QOS_ENUMS["ReliabilityQosPolicyKind"]))
    dur_opts = sorted(list(FASTDDS_QOS_ENUMS["DurabilityQosPolicyKind"]))
    liv_opts = sorted(list(FASTDDS_QOS_ENUMS["LivelinessQosPolicyKind"]))
    dst_opts = sorted(list(FASTDDS_QOS_ENUMS["DestinationOrderQosPolicyKind"]))
    own_opts = sorted(list(FASTDDS_QOS_ENUMS["OwnershipQosPolicyKind"]))

    writer = dict(base_qos["writer"])  # shallow copy
    reader = dict(base_qos["reader"])  # shallow copy

    def _ask_int(prompt: str, default_val: int) -> int:
        while True:
            raw = input(f"{prompt} (default {default_val}): ").strip()
            if raw == "":
                return default_val
            if raw.isdigit() and int(raw) > 0:
                return int(raw)
                print("Invalid value.")
    if roles in ("publisher", "both"):
        print("")
        print("Writer.Reliability:")
        writer["reliability"] = _choose_enum("Selection", rel_opts, rel_opts.index(writer["reliability"]))
        print("Writer.Durability:")
        writer["durability"] = _choose_enum("Selection", dur_opts, dur_opts.index(writer["durability"]))
        print("Writer.Liveliness:")
        writer["liveliness"] = _choose_enum("Selection", liv_opts, liv_opts.index(writer["liveliness"]))
        print("Writer.DestinationOrder:")
        writer["destination_order"] = _choose_enum("Selection", dst_opts, dst_opts.index(writer["destination_order"]))
        print("Writer.Ownership:")
        writer["ownership"] = _choose_enum("Selection", own_opts, own_opts.index(writer["ownership"]))
        while True:
            os_raw = input("Writer.OwnershipStrength (int, default 0): ").strip()
            if os_raw == "":
                writer["ownership_strength"] = 0
                break
            try:
                os_val = int(os_raw)
                if os_val >= 0:
                    writer["ownership_strength"] = os_val
                    break
            except Exception:
                pass
                print("Invalid value.")
        while True:
            pm_raw = input("Writer.PublishMode Async? (y/N): ").strip().lower()
            if pm_raw in ("", "n", "no"):
                writer["publish_mode_async"] = False
                break
            if pm_raw in ("y", "yes"):
                writer["publish_mode_async"] = True
                break
            print("Invalid selection.")
        # Resource limits
        rlw = dict(writer.get("resource_limits", {}))
        rlw["max_samples"] = _ask_int("Writer.ResourceLimits.max_samples", rlw.get("max_samples", 1000))
        rlw["allocated_samples"] = _ask_int("Writer.ResourceLimits.allocated_samples", rlw.get("allocated_samples", 50))
        writer["resource_limits"] = rlw

    if roles in ("subscriber", "both"):
        print("")
        print("Reader.Reliability:")
        reader["reliability"] = _choose_enum("Selection", rel_opts, rel_opts.index(reader["reliability"]))
        print("Reader.Durability:")
        reader["durability"] = _choose_enum("Selection", dur_opts, dur_opts.index(reader["durability"]))
        print("Reader.Liveliness:")
        reader["liveliness"] = _choose_enum("Selection", liv_opts, liv_opts.index(reader["liveliness"]))
        print("Reader.DestinationOrder:")
        reader["destination_order"] = _choose_enum("Selection", dst_opts, dst_opts.index(reader["destination_order"]))
        print("Reader.Ownership:")
        reader["ownership"] = _choose_enum("Selection", own_opts, own_opts.index(reader["ownership"]))
        rlr = dict(reader.get("resource_limits", {}))
        rlr["max_samples"] = _ask_int("Reader.ResourceLimits.max_samples", rlr.get("max_samples", 1000))
        rlr["allocated_samples"] = _ask_int("Reader.ResourceLimits.allocated_samples", rlr.get("allocated_samples", 50))
        reader["resource_limits"] = rlr

    return writer, reader, hist


def validate_qos(history: Dict[str, Optional[int]], base_qos: Dict[str, Dict]) -> Tuple[bool, str]:
    # History validation
    kind = history.get("kind")
    depth = history.get("depth")
    if kind is not None:
        if kind not in HISTORY_KIND_ALLOWED:
            return False, "History.kind invalid (KEEP_LAST/KEEP_ALL)."
        if kind == "KEEP_LAST":
            if depth is None or not isinstance(depth, int) or depth <= 0:
                return False, "KEEP_LAST requires positive integer depth."
        if kind == "KEEP_ALL" and depth is not None:
            return False, "KEEP_ALL should not have depth specified."

    # Writer/Reader enum kontrolleri
    for role in ("writer", "reader"):
        cfg = base_qos.get(role, {})
        rel = cfg.get("reliability")
        dur = cfg.get("durability")
        liv = cfg.get("liveliness")
        if rel is not None and rel not in FASTDDS_QOS_ENUMS["ReliabilityQosPolicyKind"]:
            return False, f"{role} reliability invalid."
        if dur is not None and dur not in FASTDDS_QOS_ENUMS["DurabilityQosPolicyKind"]:
            return False, f"{role} durability invalid."
        if liv is not None and liv not in FASTDDS_QOS_ENUMS["LivelinessQosPolicyKind"]:
            return False, f"{role} liveliness invalid."
        # DestinationOrder & Ownership
        dest = cfg.get("destination_order")
        own = cfg.get("ownership")
        if dest is not None and dest not in FASTDDS_QOS_ENUMS["DestinationOrderQosPolicyKind"]:
            return False, f"{role} destination_order invalid."
        if own is not None and own not in FASTDDS_QOS_ENUMS["OwnershipQosPolicyKind"]:
            return False, f"{role} ownership invalid."

        rl = cfg.get("resource_limits")
        if rl is not None:
            if not isinstance(rl, dict):
                return False, f"{role} resource_limits must be a dictionary."
            for key in ("max_samples", "allocated_samples"):
                if key in rl:
                    val = rl.get(key)
                    if not isinstance(val, int) or val <= 0:
                        return False, f"{role} resource_limits.{key} must be a positive integer."

        if role == "writer":
            if "publish_mode_async" in cfg:
                pm = cfg.get("publish_mode_async")
                if not isinstance(pm, bool):
                    return False, "writer publish_mode_async must be boolean."
            if "ownership_strength" in cfg:
                os_val = cfg.get("ownership_strength")
                if not isinstance(os_val, int) or os_val < 0:
                    return False, "writer ownership_strength negatif olamaz."

    # Publisher/Subscriber presentation & partition
    for role in ("publisher", "subscriber"):
        cfg = base_qos.get(role, {})
        pres = cfg.get("presentation")
        if pres is not None:
            scope = pres.get("access_scope")
            if scope not in FASTDDS_QOS_ENUMS["PresentationQosPolicyAccessScopeKind"]:
                return False, f"{role} presentation.access_scope invalid."
            for b in ("coherent_access", "ordered_access"):
                if not isinstance(pres.get(b, False), bool):
                    return False, f"{role} presentation.{b} must be boolean."
        part = cfg.get("partition")
        if part is not None:
            names = part.get("names", [])
            if not isinstance(names, list) or not all(isinstance(x, str) for x in names):
                return False, f"{role} partition.names must be array[str]."

    return True, "OK"


def _history_kind_symbol(kind: str) -> str:
    if kind == "KEEP_LAST":
        return "KEEP_LAST_HISTORY_QOS"
    return "KEEP_ALL_HISTORY_QOS"


def _inject_or_replace(block_name: str, content: str, new_block: str) -> str:
    start_marker = f"// <QoSPatcher:{block_name}:BEGIN>"
    end_marker = f"// <QoSPatcher:{block_name}:END>"
    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker), re.MULTILINE
    )
    block = start_marker + "\n" + new_block.rstrip() + "\n" + end_marker
    if pattern.search(content):
        return pattern.sub(block, content)
    # Otherwise add: Place near main QoS usage (before create_datawriter/reader)
    # Heuristic: find create_datawriter or create_datareader line
    anchor = re.search(r"create_datawriter\(|create_datareader\(", content)
    if anchor:
        # Add block before the LINE WHERE function call STARTS
        pos = anchor.start()
        line_start = content.rfind("\n", 0, pos)
        insert_pos = 0 if line_start == -1 else line_start + 1
        # Get current line indentation and write block with same indentation
        indent_match = re.match(r"[\t ]*", content[insert_pos:pos])
        indent = indent_match.group(0) if indent_match else ""
        indented_block = _with_indent(block, indent)
        return content[:insert_pos] + indented_block + "\n" + content[insert_pos:]
    # If not found at all, add to end of file
    return content.rstrip() + "\n\n" + block + "\n"


def _build_qos_assignments_to_var(var_name: str, role: str, qos: Dict, history: Dict[str, Optional[int]]) -> str:
    hist_kind = _history_kind_symbol(history["kind"]) if history else "KEEP_LAST_HISTORY_QOS"
    lines: List[str] = []
    lines.append(f"// <QoSPatcher:{role}_qos:BEGIN>")
    lines.append(f"// {role.capitalize()} QoS - generated by QoSPatcher")
    if qos.get("reliability") is not None:
        lines.append(f"{var_name}.reliability().kind = eprosima::fastdds::dds::{qos['reliability']};")
    if qos.get("durability") is not None:
        lines.append(f"{var_name}.durability().kind = eprosima::fastdds::dds::{qos['durability']};")
    if qos.get("liveliness") is not None:
        lines.append(f"{var_name}.liveliness().kind = eprosima::fastdds::dds::{qos['liveliness']};")
    # DestinationOrder
    if qos.get("destination_order"):
        lines.append(f"{var_name}.destination_order().kind = eprosima::fastdds::dds::{qos['destination_order']};")
    # Ownership
    if qos.get("ownership"):
        lines.append(f"{var_name}.ownership().kind = eprosima::fastdds::dds::{qos['ownership']};")
    if history.get("kind") is not None:
        lines.append(f"{var_name}.history().kind = eprosima::fastdds::dds::{hist_kind};")
        if history.get("kind") == "KEEP_LAST":
            lines.append(f"{var_name}.history().depth = {int(history['depth'])};")
    rl = qos.get("resource_limits")
    if isinstance(rl, dict):
        if "max_samples" in rl:
            lines.append(f"{var_name}.resource_limits().max_samples = {int(rl['max_samples'])};")
        if "allocated_samples" in rl:
            lines.append(f"{var_name}.resource_limits().allocated_samples = {int(rl['allocated_samples'])};")
    if role == "writer":
        if qos.get("publish_mode_async") is True:
            lines.append(f"{var_name}.publish_mode().kind = eprosima::fastdds::dds::ASYNCHRONOUS_PUBLISH_MODE;")
        if isinstance(qos.get("ownership_strength"), int) and qos.get("ownership_strength") is not None:
            if int(qos["ownership_strength"]) > 0:
                lines.append(f"{var_name}.ownership_strength().value = {int(qos['ownership_strength'])};")
    lines.append(f"// <QoSPatcher:{role}_qos:END>")
    return "\n".join(lines)


def _with_indent(block: str, indent: str) -> str:
    lines = block.splitlines()
    return "\n".join([(indent + ln if ln.strip() != "" else ln) for ln in lines])


def _strip_qos_assignments(content: str, var_name: str, is_reader: bool) -> str:
    # Clean QoS assignments only between var definition and related create_* call
    decl = re.search(rf"\b(DataReaderQos|DataWriterQos)\s+{re.escape(var_name)}\s*=", content)
    if not decl:
        return content
    start = decl.end()
    if is_reader:
        create = re.search(r"create_datareader\(", content[start:])
    else:
        create = re.search(r"create_datawriter\(", content[start:])
    end = (start + create.start()) if create else len(content)
    segment = content[start:end]
    # Patterns to remove
    patterns = [
        rf"{re.escape(var_name)}\.reliability\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.durability\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.liveliness\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.destination_order\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.ownership\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.history\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.history\(\)\.depth\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.resource_limits\(\)\.max_samples\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.resource_limits\(\)\.allocated_samples\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.publish_mode\(\)\.kind\s*=.*?;\s*\n",
        rf"{re.escape(var_name)}\.ownership_strength\(\)\.value\s*=.*?;\s*\n",
    ]
    for pat in patterns:
        segment = re.sub(pat, "", segment)
    return content[:start] + segment + content[end:]


def _find_qos_var_and_segment(content: str, is_reader: bool) -> Tuple[Optional[str], Optional[str]]:
    match = re.search(r"\bDataReaderQos\s+(\w+)\s*=" if is_reader else r"\bDataWriterQos\s+(\w+)\s*=", content)
    if not match:
        return None, None
    var_name = match.group(1)
    start = match.end()
    create = re.search(r"create_datareader\(" if is_reader else r"create_datawriter\(", content[start:])
    end = (start + create.start()) if create else len(content)
    return var_name, content[start:end]


def extract_qos_from_content(content: str, is_reader: bool) -> Tuple[Dict, Dict[str, Optional[int]]]:
    qos: Dict = {}
    history: Dict[str, Optional[int]] = {"kind": None, "depth": None}
    var_name, seg = _find_qos_var_and_segment(content, is_reader)
    if not seg:
        return qos, history
    # Helper to find enum or int assignment
    def _find_enum(field: str) -> Optional[str]:
        m = re.search(rf"{re.escape(var_name)}\\.{field}\\(\\)\\.kind\\s*=\\s*(?:eprosima::fastdds::dds::)?([A-Z_]+)", seg)
        return m.group(1) if m else None
    def _find_int(field: str) -> Optional[int]:
        m = re.search(rf"{re.escape(var_name)}\\.{field}\\(\\)\\.depth\\s*=\\s*(\\d+)", seg)
        return int(m.group(1)) if m else None
    def _find_int_direct(pattern: str) -> Optional[int]:
        m = re.search(pattern, seg)
        return int(m.group(1)) if m else None
    # Core
    rel = _find_enum("reliability")
    if rel:
        qos["reliability"] = rel
    dur = _find_enum("durability")
    if dur:
        qos["durability"] = dur
    liv = _find_enum("liveliness")
    if liv:
        qos["liveliness"] = liv
    dst = _find_enum("destination_order")
    if dst:
        qos["destination_order"] = dst
    own = _find_enum("ownership")
    if own:
        qos["ownership"] = own
    # History
    hkind = _find_enum("history")
    if hkind:
        # Map to KEEP_LAST/KEEP_ALL
        if hkind.endswith("KEEP_LAST_HISTORY_QOS"):
            history["kind"] = "KEEP_LAST"
        elif hkind.endswith("KEEP_ALL_HISTORY_QOS"):
            history["kind"] = "KEEP_ALL"
    hdepth = _find_int("history")
    if hdepth is not None:
        history["depth"] = hdepth
    # Resource limits
    max_samples = _find_int_direct(rf"{re.escape(var_name)}\\.resource_limits\\(\\)\\.max_samples\\s*=\\s*(\\d+)")
    alloc_samples = _find_int_direct(rf"{re.escape(var_name)}\\.resource_limits\\(\\)\\.allocated_samples\\s*=\\s*(\\d+)")
    if max_samples or alloc_samples:
        qos["resource_limits"] = {}
        if max_samples is not None:
            qos["resource_limits"]["max_samples"] = max_samples
        if alloc_samples is not None:
            qos["resource_limits"]["allocated_samples"] = alloc_samples
    # Publish mode
    if not is_reader:
        async_set = re.search(rf"{re.escape(var_name)}\\.publish_mode\\(\\)\\.kind\\s*=\\s*(?:eprosima::fastdds::dds::)?ASYNCHRONOUS_PUBLISH_MODE", seg)
        qos["publish_mode_async"] = bool(async_set)
        ostr = _find_int_direct(rf"{re.escape(var_name)}\\.ownership_strength\\(\\)\\.value\\s*=\\s*(\\d+)")
        if ostr is not None:
            qos["ownership_strength"] = ostr
    return qos, history


def extract_qos_from_file(path: Path, is_reader: bool) -> Tuple[Dict, Dict[str, Optional[int]]]:
    try:
        content = Path(path).read_text(encoding="utf-8")
    except Exception:
        return {}, {"kind": None, "depth": None}
    return extract_qos_from_content(content, is_reader)


def _patch_single_file(path: Path, history: Dict[str, Optional[int]], base_qos: Dict[str, Dict]) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except Exception:
        return False

    content = original

    # Publisher/Subscriber distinction: find QoS variable names
    # Reader
    reader_qos_match = re.search(r"\bDataReaderQos\s+(\w+)\s*=", content)
    if reader_qos_match:
        reader_qos_var = reader_qos_match.group(1)
        # Clean old assignments
        content = _strip_qos_assignments(content, reader_qos_var, is_reader=True)
        # Add/update QoS assignments before create_datareader call
        reader_assign = _build_qos_assignments_to_var(reader_qos_var, "reader", base_qos["reader"], history)
        # Injection point: immediately before create_datareader call
        content = _inject_or_replace("reader_qos", content, reader_assign)

    # Writer
    writer_qos_match = re.search(r"\bDataWriterQos\s+(\w+)\s*=", content)
    if writer_qos_match:
        writer_qos_var = writer_qos_match.group(1)
        content = _strip_qos_assignments(content, writer_qos_var, is_reader=False)
        writer_assign = _build_qos_assignments_to_var(writer_qos_var, "writer", base_qos["writer"], history)
        content = _inject_or_replace("writer_qos", content, writer_assign)

    if content == original:
        return False

    try:
        path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def apply_qos_patch(history: Dict[str, Optional[int]],
                    target_files: Optional[List[Path]] = None) -> Dict[str, List[Path]]:
    files = target_files if target_files is not None else _find_target_files()
    if not files:
        return {"patched": [], "skipped": []}

    backups = backup_files(files)
    del backups  # only for guarantee, summary will return separately

    patched: List[Path] = []
    skipped: List[Path] = []
    for f in files:
        ok = _patch_single_file(f, history, DEFAULT_QOS)
        if ok:
            patched.append(f)
        else:
            skipped.append(f)
    return {"patched": patched, "skipped": skipped}


def print_summary(result: Dict[str, List[Path]]) -> None:
    patched = result.get("patched", [])
    skipped = result.get("skipped", [])
    print("")
    print("=== QoS Patch Summary ===")
    print(f"Patched: {len(patched)}")
    for p in patched:
        print(f"  - {p}")
    print(f"Skipped/Unchanged: {len(skipped)}")
    for s in skipped:
        print(f"  - {s}")


def main() -> None:
    print("🚀 Fast DDS QoS Patcher")
    root = _project_root()
    print(f"Project root: {root}")

    all_files = _find_target_files()
    if not all_files:
        print("⚠️  Target file not found (IDL/*_idl_generated/*PublisherApp.cxx | *SubscriberApp.cxx)")
        sys.exit(0)

    grouped = _group_targets_by_module(all_files)
    _print_target_variations(grouped)
    selected_modules = _get_user_module_selection(grouped)
    if not selected_modules:
        print("No selection made. Exiting.")
        sys.exit(0)

    role_sel = _get_user_role_selection()

    chosen_files: List[Path] = []
    for m in selected_modules:
        roles = grouped.get(m, {})
        if role_sel in ("publisher", "both") and "publisher" in roles:
            chosen_files.append(roles["publisher"])
        if role_sel in ("subscriber", "both") and "subscriber" in roles:
            chosen_files.append(roles["subscriber"])

    if not chosen_files:
        print("No files found matching selected criteria.")
        sys.exit(0)

    print("")
    print("Files to process:")
    for p in chosen_files:
        print(f"  - {p}")

    display_qos_menu()
    mode = input("Selection (1-2): ").strip()
    if mode == "2":
        writer_qos_cfg, reader_qos_cfg, history = get_advanced_qos_inputs(DEFAULT_QOS, role_sel)
        # Merge into a working copy of defaults
        effective_qos = {
            **DEFAULT_QOS,
            "writer": writer_qos_cfg,
            "reader": reader_qos_cfg,
        }
    else:
        history = get_history_input()
        effective_qos = DEFAULT_QOS

    ok, reason = validate_qos(history, effective_qos)
    if not ok:
        print(f"❌ QoS validation failed: {reason}")
        print("Changes not applied.")
        sys.exit(1)

    # Patch with the effective config by temporarily swapping DEFAULT_QOS usage
    result_files = []
    patched: List[Path] = []
    skipped: List[Path] = []
    files = chosen_files
    if not files:
        print("No files found matching selected criteria.")
        sys.exit(0)
    backup_files(files)
    for f in files:
        okfile = _patch_single_file(f, history, effective_qos)
        if okfile:
            patched.append(f)
        else:
            skipped.append(f)
    result = {"patched": patched, "skipped": skipped}
    print_summary(result)


if __name__ == "__main__":
    main()


