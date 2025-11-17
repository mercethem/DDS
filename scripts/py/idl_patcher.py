#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDL Default Data Patcher for Fast-DDS - Cross-Platform Version
This script parses IDL files and patches PublisherApps with default data.
Works on Windows and Linux systems.
"""

import os
import re
import sys
import platform
from typing import Dict, List, Optional, Any, Set, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import copy
import traceback

# --- Configuration ---
try:
    CURRENT_SCRIPT_DIR = Path(__file__).parent
except NameError:
    CURRENT_SCRIPT_DIR = Path.cwd()
PROJECT_ROOT = CURRENT_SCRIPT_DIR.parent.parent
IDL_DIR = PROJECT_ROOT / "IDL"
# ---------------------

# === DATA MODELS (FOR IDL TYPES) ===
@dataclass
class IDLField:
    name: str; type_name: str; full_type_def: str; module_name: str
    is_array: bool = False; array_dims: List[str] = field(default_factory=list)
    is_sequence: bool = False; sequence_limit: Optional[str] = None
    string_limit: Optional[str] = None
@dataclass
class IDLStruct: name: str; module_name: str; fields: List[IDLField] = field(default_factory=list)
@dataclass
class IDLEnum: name: str; module_name: str; values: List[str] = field(default_factory=list)
@dataclass
class IDLUnionCase: discriminator_values: List[str]; field: IDLField
@dataclass
class IDLUnion: name: str; module_name: str; discriminator_type: str; cases: List[IDLUnionCase] = field(default_factory=list)
@dataclass
class IDLTypeDef: name: str; module_name: str; base_type_def: str; resolved_base_type: str = ""
IDLType = Union[IDLStruct, IDLEnum, IDLUnion, IDLTypeDef]


# === 1. COMPONENT: IDL PARSER (v9.3 - Multi-Stage, Robust) ===

class IDLParser:
    """Advanced parser that parses IDL files in 2 stages."""
    def __init__(self, primitive_types: Set[str]):
        self.primitive_types = primitive_types
        self.types: Dict[str, IDLType] = {}
        self.module_contents: Dict[str, str] = {}
        self.type_to_module_map: Dict[str, str] = {}

    def get_type(self, type_name_raw: str, current_module: str = "") -> Optional[IDLType]:
        """Finds a type by name, prioritizing module context."""
        if type_name_raw in self.primitive_types: return None
        if '::' in type_name_raw: return self.types.get(type_name_raw)
        if current_module:
            scoped_name = f"{current_module}::{type_name_raw}"
            if scoped_name in self.types: return self.types[scoped_name]
        if type_name_raw in self.type_to_module_map:
             module = self.type_to_module_map[type_name_raw]
             scoped_name = f"{module}::{type_name_raw}"
             return self.types.get(scoped_name)
        # Module-less (global) type
        if type_name_raw in self.types and not self.types[type_name_raw].module_name:
             return self.types.get(type_name_raw)
        return None

    def get_struct_def(self, type_name: str, current_module: str = "") -> Optional[IDLStruct]:
        type_obj = self.get_type(type_name, current_module)
        return type_obj if isinstance(type_obj, IDLStruct) else None

    def get_enum_def(self, type_name: str, current_module: str = "") -> Optional[IDLEnum]:
        type_obj = self.get_type(type_name, current_module)
        return type_obj if isinstance(type_obj, IDLEnum) else None

    def _remove_comments_and_includes(self, content: str) -> str:
        """Removes comments and #includes, reduces unnecessary whitespace."""
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'^\s*#.*$', '', content, flags=re.MULTILINE)
        # Only clean empty lines and leading/trailing whitespace
        content = "\n".join(line.strip() for line in content.splitlines() if line.strip())
        content = content.replace('=', ' = ') # For enum values
        return content

    # --- FIXED v9.3 ---
    def parse_all_idls(self, idl_path: Path):
        """Parses all IDLs in 2 stages. (v9.3 - Robust module parsing)"""
        print(f"Scanning IDL directory (including subdirectories): {idl_path}")
        idl_files = list(idl_path.glob("**/*.idl"))
        if not idl_files: print(f"✗ Warning: No .idl files found in {idl_path}."); return

        raw_contents: Dict[Path, str] = {}
        for idl_file in idl_files:
            try:
                with open(idl_file, 'r', encoding='utf-8') as f: content = self._remove_comments_and_includes(f.read())
                raw_contents[idl_file] = content
            except Exception as e: print(f"✗ Error reading {idl_file.name}: {e}")

        # --- STAGE 1: DISCOVER TYPES (FIXED LOGIC) ---
        print("  Stage 1/2: Discovering IDL types...")
        self.module_contents = {}; self.types = {}; self.type_to_module_map = {}
        
        # Temporarily store module and global contents
        temp_module_bodies = {}
        global_body = ""

        module_keyword = "module"

        for idl_file, content in raw_contents.items():
            idx = 0
            while idx < len(content):
                module_match_idx = content.find(module_keyword, idx)
                
                # If module not found, add remaining to global
                if module_match_idx == -1:
                    global_body += content[idx:]
                    break

                # Add part before module to global
                global_body += content[idx:module_match_idx]
                
                # Get module name
                start_name_idx = module_match_idx + len(module_keyword)
                while start_name_idx < len(content) and content[start_name_idx].isspace(): start_name_idx += 1
                end_name_idx = start_name_idx
                while end_name_idx < len(content) and (content[end_name_idx].isalnum() or content[end_name_idx] == '_'): end_name_idx += 1
                module_name = content[start_name_idx:end_name_idx].strip()
                
                if not module_name:
                    idx = end_name_idx
                    continue # 'module' keyword found but no name, skip

                # Find opening brace of module
                open_brace_idx = content.find('{', end_name_idx)
                if open_brace_idx == -1:
                    idx = end_name_idx
                    continue # Invalid module definition

                # Find closing brace of module using _find_closing_brace
                close_brace_idx = self._find_closing_brace(content, open_brace_idx)
                if close_brace_idx == -1:
                    print(f"WARNING: Closing brace not found for module '{module_name}' in file {idl_file.name}! Skipping rest of file.")
                    break # Skip rest of this file

                # Get module body
                module_body = content[open_brace_idx + 1 : close_brace_idx]
                
                # Discover and store
                self._discover_types(module_body, module_name)
                temp_module_bodies.setdefault(module_name, ""); temp_module_bodies[module_name] += module_body + "\n"
                
                # Move index to end of module
                idx = close_brace_idx + 1

        # Process global (module-less) types
        self._discover_types(global_body, "")
        
        # Transfer contents to main storage
        self.module_contents[""] = global_body
        for name, body in temp_module_bodies.items():
            self.module_contents[name] = body
        
        print(f"  ✓ Found {len(self.types)} type headers (struct/enum/union/typedef).")

        # --- STAGE 2: PARSE BODIES ---
        # (This section remains the same, will now work with correct 'module_contents')
        print("  Stage 2/2: Parsing Struct/Union/Enum/Typedef bodies...")
        for module_name, body in self.module_contents.items(): self._parse_typedefs(body, module_name)
        self._resolve_all_typedefs()
        for module_name, body in self.module_contents.items(): self._parse_enum_bodies(body, module_name)
        for module_name, body in self.module_contents.items():
            self._parse_struct_bodies(body, module_name)
            self._parse_union_bodies(body, module_name)
        print(f"✓ IDL parsing completed.")
    # --- FIX END ---

    def _get_scoped_key(self, module_name: str, type_name: str) -> str:
        """Creates full key from module name and type name."""
        return f"{module_name}::{type_name}" if module_name else type_name

    def _discover_types(self, content: str, module_name: str):
        """Finds all type names in given content and records them in self.types."""
        for match in re.finditer(r'struct\s+(\w+)', content): name = match.group(1); key = self._get_scoped_key(module_name, name); self.type_to_module_map.setdefault(name, module_name); self.types.setdefault(key, IDLStruct(name=name, module_name=module_name))
        for match in re.finditer(r'enum\s+(\w+)', content): name = match.group(1); key = self._get_scoped_key(module_name, name); self.type_to_module_map.setdefault(name, module_name); self.types.setdefault(key, IDLEnum(name=name, module_name=module_name))
        for match in re.finditer(r'union\s+(\w+)', content): name = match.group(1); key = self._get_scoped_key(module_name, name); self.type_to_module_map.setdefault(name, module_name); self.types.setdefault(key, IDLUnion(name=name, module_name=module_name, discriminator_type=""))
        # typedef regex should be more careful (for array typedef)
        for match in re.finditer(r'typedef.+?\s+([\w:]+)\s*(?:\[.*?\]\s*)?;', content): name = match.group(1); key = self._get_scoped_key(module_name, name); self.type_to_module_map.setdefault(name, module_name); self.types.setdefault(key, IDLTypeDef(name=name, module_name=module_name, base_type_def=""))

    def _parse_typedefs(self, content: str, module_name: str):
        typedef_regex = re.compile(r'typedef\s+(.+?)\s+([\w:]+)(\s*\[.*?\]\s*)?;', re.DOTALL)
        for match in typedef_regex.finditer(content):
            base_type_def, name, array_suffix = match.groups()
            key = self._get_scoped_key(module_name, name)
            base_type_def_clean = ' '.join(base_type_def.strip().split())
            if array_suffix: base_type_def_clean += array_suffix.strip()
            if key in self.types and isinstance(self.types[key], IDLTypeDef): self.types[key].base_type_def = base_type_def_clean

    def _parse_enum_bodies(self, content: str, module_name: str):
        # Non-greedy and start check to prevent nested definitions
        enum_regex = re.compile(r'(?:^|;|\})\s*enum\s+(\w+)\s*\{([^}]*?)\}', re.DOTALL | re.MULTILINE)
        for match in enum_regex.finditer(content):
            name, body = match.groups()
            key = self._get_scoped_key(module_name, name)
            if key in self.types and isinstance(self.types[key], IDLEnum) and not self.types[key].values:
                self.types[key].values = [v.split('=')[0].strip() for v in body.split(',') if v.strip()]

    def _find_closing_brace(self, text: str, start_idx: int) -> int:
        """Finds the matching '}' brace for the '{' brace at the given start index."""
        brace_level = 0; idx = start_idx
        in_string = False; in_char = False
        while idx < len(text):
            char = text[idx]
            if char == '"' and (idx == 0 or text[idx-1] != '\\'): in_string = not in_string
            elif char == '\'' and (idx == 0 or text[idx-1] != '\\'): in_char = not in_char
            elif not in_string and not in_char:
                if char == '{': brace_level += 1
                elif char == '}': brace_level -= 1
            if brace_level == 0 and char == '}': return idx # Return at exact match
            # Initialize counter after counting start brace
            if idx == start_idx and char == '{': brace_level = 1

            idx += 1
        return -1 # Match not found

    def _parse_struct_bodies(self, content: str, module_name: str):
        """Fills struct bodies (fields) (skipping nested structures)."""
        idx = 0
        struct_keyword = "struct"
        while idx < len(content):
            try:
                struct_match_idx = content.index(struct_keyword, idx)
            except ValueError:
                break # No more structs

            # Ensure no letter/digit before it (not part of something else)
            if struct_match_idx > 0 and (content[struct_match_idx-1].isalnum() or content[struct_match_idx-1] == '_'):
                idx = struct_match_idx + len(struct_keyword); continue

            start_name_idx = struct_match_idx + len(struct_keyword)
            while start_name_idx < len(content) and content[start_name_idx].isspace(): start_name_idx += 1
            end_name_idx = start_name_idx
            while end_name_idx < len(content) and (content[end_name_idx].isalnum() or content[end_name_idx] == '_'): end_name_idx += 1
            name = content[start_name_idx:end_name_idx].strip()
            if not name: idx = end_name_idx; continue

            open_brace_idx = content.find('{', end_name_idx)
            if open_brace_idx == -1: idx = end_name_idx; continue # Invalid definition

            close_brace_idx = self._find_closing_brace(content, open_brace_idx)
            if close_brace_idx == -1: 
                print(f"ERROR: Closing brace not found for struct {module_name}::{name}! Skipping.")
                # FIX v9.3: 'continue' instead of 'break'
                idx = open_brace_idx + 1 # Prevent infinite loop
                continue 

            body = content[open_brace_idx + 1 : close_brace_idx]
            key = self._get_scoped_key(module_name, name)
            if key in self.types and isinstance(self.types[key], IDLStruct):
                 struct_obj = self.types[key] # type: IDLStruct
                 if not struct_obj.fields: struct_obj.fields = self._parse_fields(body, module_name)
            idx = close_brace_idx + 1

    def _parse_union_bodies(self, content: str, module_name: str):
        """Fills union bodies (discriminator, cases)."""
        idx = 0
        union_keyword = "union"
        while idx < len(content):
            try:
                union_match_idx = content.index(union_keyword, idx)
            except ValueError:
                break
            if union_match_idx > 0 and (content[union_match_idx-1].isalnum() or content[union_match_idx-1] == '_'):
                idx = union_match_idx + len(union_keyword); continue

            # union Name switch ( Type ) { ... }
            header_match = re.search(r'union\s+(\w+)\s*switch\s*\((.+?)\)\s*\{', content[union_match_idx:])
            if not header_match: idx = union_match_idx + len(union_keyword); continue # Eşleşmedi

            name, disc_type_def = header_match.groups()
            key = self._get_scoped_key(module_name, name)
            open_brace_abs_idx = union_match_idx + header_match.end() - 1

            close_brace_abs_idx = self._find_closing_brace(content, open_brace_abs_idx)
            if close_brace_abs_idx == -1: 
                print(f"ERROR: Closing brace not found for union {key}! Skipping.")
                # FIX v9.3: 'continue' instead of 'break'
                idx = open_brace_abs_idx + 1 # Prevent infinite loop
                continue 

            body = content[open_brace_abs_idx + 1 : close_brace_abs_idx]
            if key in self.types and isinstance(self.types[key], IDLUnion):
                union_obj = self.types[key] # type: IDLUnion
                if not union_obj.discriminator_type:
                        union_obj.discriminator_type = self._resolve_type_name(disc_type_def.strip(), module_name)
                        union_obj.cases = self._parse_union_cases(body, module_name)
            idx = close_brace_abs_idx + 1


    def _resolve_all_typedefs(self):
        """Fills resolved_base_type for all typedefs (nested resolutions)."""
        print("  Resolving typedefs...")
        changed = True; passes = 0; max_passes = 15
        all_typedefs = [t for t in self.types.values() if isinstance(t, IDLTypeDef)]
        while changed and passes < max_passes:
            changed = False; passes += 1
            for type_obj in all_typedefs:
                if not type_obj.resolved_base_type and type_obj.base_type_def:
                    try:
                        temp_field = self._create_field_from_defs("temp", type_obj.base_type_def, "", type_obj.module_name, resolve_now=False)
                        resolved = self._resolve_type_name(temp_field.type_name, type_obj.module_name, resolve_typedefs=True, _depth=0, _max_depth=max_passes)
                    except RecursionError: print(f"  ERROR: Infinite loop while resolving typedef '{type_obj.module_name}::{type_obj.name}'!"); resolved = type_obj.base_type_def.split('::')[-1]
                    except Exception as e: print(f"  ERROR: Error resolving typedef '{type_obj.module_name}::{type_obj.name}': {e}"); resolved = type_obj.base_type_def.split('::')[-1]

                    base_type_obj = self.get_type(resolved, type_obj.module_name)
                    is_unresolved_typedef = isinstance(base_type_obj, IDLTypeDef) and not base_type_obj.resolved_base_type
                    if not is_unresolved_typedef: type_obj.resolved_base_type = resolved; changed = True
        if passes == max_passes and changed: print("  WARNING: Some nested typedefs could not be resolved or limit exceeded!")

    def _parse_fields(self, body: str, module_name: str) -> List[IDLField]:
        """Parses fields in struct or union body."""
        fields = []
        # Split fields by semicolon, but temporarily replace { } contents
        placeholder = "__BRACE__"; brace_stack = []; brace_map = {}
        body_replaced = list(body)
        for i, char in enumerate(body):
            if char == '{': brace_stack.append(i)
            elif char == '}':
                if brace_stack: start = brace_stack.pop(); placeholder_key = placeholder + str(len(brace_map)); brace_map[placeholder_key] = body[start:i+1]; body_replaced[start:i+1] = list(placeholder_key)
        body_no_braces = "".join(body_replaced)
        body_no_case = re.sub(r'(case\s+.+:|default:)', '', body_no_braces)

        for line in body_no_case.split(';'):
            line = re.sub(r'\[.*?\]', '', line.strip()).strip() # Annotation
            if not line: continue
            for key, val in brace_map.items(): line = line.replace(key, val) # Restore placeholder

            match = re.match(r'(.+?)\s+([\w:]+)\s*((?:\[[^\]]+\]\s*)*)$', line)
            if not match: continue
            type_def, name, array_def = match.groups()
            fields.append(self._create_field_from_defs(name, type_def.strip(), array_def.strip(), module_name))
        return fields

    def _parse_union_cases(self, union_body: str, module_name: str) -> List[IDLUnionCase]:
        """Parses 'case's in union body."""
        cases = []
        # Regex: (Case Labels) (Field Definition;)
        case_regex = re.compile(r'((?:case\s+[^:]+:|default:)\s*)((?:[^;]+;)+)', re.IGNORECASE | re.DOTALL)
        idx = 0
        while idx < len(union_body):
            match = case_regex.search(union_body, idx)
            if not match: break
            labels_raw = match.group(1); fields_raw = match.group(2).strip()
            field_def_line = fields_raw.split(';')[0].strip()
            field_def_line = re.sub(r'\[.*?\]', '', field_def_line).strip() # Annotation
            match_field = re.match(r'(.+?)\s+([\w:]+)\s*((?:\[[^\]]+\]\s*)*)$', field_def_line)
            if match_field:
                type_def, name, array_def = match_field.groups()
                field = self._create_field_from_defs(name, type_def.strip(), array_def.strip(), module_name)
                labels = [label.strip() for label in re.findall(r'(case\s+[^:]+:|default:)', labels_raw, re.IGNORECASE)]
                cases.append(IDLUnionCase(discriminator_values=labels, field=field))
            idx = match.end()
        return cases

    def _create_field_from_defs(self, name: str, type_def: str, array_def: str, module_name: str, resolve_now=True) -> IDLField:
        """Creates an IDLField object from parsed type, name, and array definition."""
        full_type_def = f"{type_def}{array_def}" if array_def else type_def
        field = IDLField(name=name, type_name=type_def, full_type_def=full_type_def, module_name=module_name)
        if array_def:
            field.is_array = True; dims = []
            for d_str in re.findall(r'\[(.*?)\]', array_def): dims.append(d_str.strip())
            field.array_dims = dims
        seq_match = re.match(r'sequence<(.+?)(?:,\s*(\S+))?>', type_def)
        if seq_match:
            field.is_sequence = True; field.type_name = seq_match.group(1).strip()
            if seq_match.group(2): field.sequence_limit = seq_match.group(2).strip()
        str_match = re.match(r'(?:string|std::string)(?:<(\S+)>)?', type_def)
        if str_match:
            field.type_name = "string";
            if str_match.group(1): field.string_limit = str_match.group(1).strip()
        wstr_match = re.match(r'(?:wstring|std::wstring)(?:<(\S+)>)?', type_def)
        if wstr_match:
            field.type_name = "wstring";
            if wstr_match.group(1): field.string_limit = wstr_match.group(1).strip()
        if resolve_now:
            field.type_name = self._resolve_type_name(field.type_name, module_name, resolve_typedefs=True)
        return field

    def _resolve_type_name(self, type_name_raw: str, current_module: str, resolve_typedefs: bool = True, _depth=0, _max_depth=15) -> str:
        """Resolves a type name to its base/final type."""
        if _depth > _max_depth: print(f"  WARNING: Typedef resolution depth limit exceeded: {type_name_raw}"); return type_name_raw.split('::')[-1]
        cleaned_type = type_name_raw.replace(" ", "")
        for prim in self.primitive_types:
            if cleaned_type == prim.replace(" ", ""): return type_name_raw

        parts = type_name_raw.split('::'); name_only = parts[-1]
        namespace = parts[0] if len(parts) > 1 else current_module

        if resolve_typedefs:
            type_def = self.get_type(name_only, namespace)
            if type_def and isinstance(type_def, IDLTypeDef):
                base_to_resolve = type_def.resolved_base_type or type_def.base_type_def
                if not base_to_resolve: return name_only
                return self._resolve_type_name(base_to_resolve, type_def.module_name, resolve_typedefs=True, _depth=_depth+1, _max_depth=_max_depth)
        return name_only


# === 2. COMPONENT: CODE GENERATOR (v9.4 - Smart Data Generation) ===

class CodeGenerator:
    """Generates C++ assignment code based on IDL models from Parser v9."""
    def __init__(self, parser: IDLParser):
        self.parser = parser
        # v9.4: This dictionary is now only used as a fallback.
        self.FALLBACK_VALUES: Dict[str, str] = {
            "float": "10.5f", "double": "123.456", "long": "123456789L",
            "unsigned long": "123456789UL", "short": "90", "unsigned short": "100",
            "long long": "9876543210LL", "unsigned long long": "9876543210ULL",
            "int8_t": "10", "uint8_t": "20", "int16_t": "30", "uint16_t": "40",
            "int32_t": "50", "uint32_t": "60", "int64_t": "70", "uint64_t": "80",
            "char": "'A'", "wchar_t": "L'B'", "boolean": "true",
            "string": '"Fallback String"', "wstring": 'L"Fallback WString"',
            "octet": "0x01",
            "int8": "10", "uint8": "20", "int16": "30", "uint16": "40",
            "int32": "50", "uint32": "60", "int64": "70", "uint64": "80",
            "long double": "123.456L"
        }

    # --- NEW FUNCTION v9.4 ---
    def _get_contextual_value(self, type_name: str, field_name: str) -> Optional[str]:
        """Generates 'smart' default value based on field name and type."""
        field_name_lower = field_name.lower()
        type_name_clean = type_name.replace(" ", "")

        # 1. Type-Based Priority Behavior (string)
        if type_name_clean == "string":
            if "id" in field_name_lower:
                if "sender" in field_name_lower: return '"Vehicle_Sender_01"'
                if "receiver" in field_name_lower: return '"Vehicle_Receiver_02"'
                if "target" in field_name_lower: return '"Target_789"'
                return '"DeviceID_123"'
            if "command" in field_name_lower:
                return '"Patrol"'
            if "description" in field_name_lower:
                return '"Detected person of interest"'
            if "link" in field_name_lower:
                return '"./data/raw.bin"'
            if "name" in field_name_lower:
                return '"DefaultName"'
            return '"Hello IDL v9.4"' # Default string

        # 2. Field Name-Based Priority Behavior (double/float)
        if "latitude" in field_name_lower:
            return "37.7749" # Value from example C++ code
        if "longitude" in field_name_lower:
            return "-122.4194" # Value from example C++ code
        if "altitude" in field_name_lower:
            return "100.0f" # Value from example C++ code
        if "speed" in field_name_lower:
            return "15.5f"
        if "confidence" in field_name_lower:
            return "0.95f" # Value from example C++ code
        if "signal" in field_name_lower:
            return "-70.0f" # Value from example C++ code

        # 3. Field Name-Based Priority Behavior (integers)
        if "seconds" in field_name_lower:
            return "1678886400L" # (Realistic timestamp)
        if "nano" in field_name_lower or "nanoseconds" in field_name_lower:
            return "500000000UL" # (Half second)
        if "orientation" in field_name_lower:
            return "180"
        if "battery" in field_name_lower:
            return "80" # unsigned short, value from example C++ code
        
        # 4. Field Name-Based Priority Behavior (boolean)
        if "error" in field_name_lower or "fail" in field_name_lower:
            return "false" # Value from example C++ code

        # 5. Fallback Dictionary
        return self.FALLBACK_VALUES.get(type_name_clean)

    def get_primitive_types(self) -> Set[str]:
        # v9.4: Based on FALLBACK_VALUES
        primitives = set(self.FALLBACK_VALUES.keys())
        primitives.update(["long double", "unsigned long", "long long", "unsigned long long"])
        return primitives

    def generate_assignments(self, struct_name: str, module_name: str, cpp_var_name: str) -> List[str]:
        """Generates C++ assignment code lines for a struct."""
        struct_def = self.parser.get_struct_def(struct_name, module_name)
        if not struct_def: return [f"// ERROR: CodeGenerator could not find definition for '{struct_name}' (Module: '{module_name}')."]
        code_lines = []
        self._generate_for_struct_fields(struct_def, cpp_var_name, code_lines)
        return code_lines

    def _generate_for_struct_fields(self, struct_def: IDLStruct, current_path: str, code_lines: List[str]):
        """Generates code for all fields of a struct."""
        # print(f"DEBUG: _generate_for_struct_fields: path='{current_path}', struct='{struct_def.name}'") # DEBUG
        for field in struct_def.fields:
            self._generate_for_field(field, current_path, struct_def.module_name, code_lines)

    def _generate_for_field(self, field: IDLField, base_path: str, module_name: str, code_lines: List[str]):
        """Generates C++ code for a single field. Main router."""
        resolved_type_name = field.type_name
        # print(f"DEBUG: _generate_for_field: base='{base_path}', field='{field.name}', type='{resolved_type_name}'") # DEBUG

        if field.is_array:
            array_path = f"{base_path}.{field.name}()"
            indices = "[0]" * len(field.array_dims)
            full_path = f"{array_path}{indices}"
            code_lines.append(f"// Array assignment: {field.name}")
            # v9.4: field.name parameter added
            self._generate_assignment(resolved_type_name, full_path, field.name, module_name, code_lines, is_member_access=False)
            return

        if field.is_sequence:
            seq_path = f"{base_path}.{field.name}()"
            code_lines.append(f"// Sequence assignment: {field.name}")
            temp_var_name = f"{base_path.replace('.', '_').replace('()', '')}_{field.name}_item"
            temp_var_lines: List[str] = []
            # v9.4: field.name parameter added (for temporary variable)
            temp_code_or_var = self._generate_assignment(
                resolved_type_name, temp_var_name, field.name + "_item", module_name, temp_var_lines,
                is_member_access=False, create_temp_var=True
            )
            if temp_code_or_var is None: code_lines.extend(temp_var_lines); return
            code_lines.extend(temp_var_lines)
            code_lines.append(f"{seq_path}.push_back({temp_code_or_var});")
            type_obj = self.parser.get_type(resolved_type_name, module_name)
            if isinstance(type_obj, (IDLStruct, IDLUnion)):
                 temp_var_name_2 = f"{temp_var_name}2"
                 temp_var_lines_2 : List[str] = []
                 # v9.4: field.name parameter added (for second temporary variable)
                 temp_code_or_var_2 = self._generate_assignment(resolved_type_name, temp_var_name_2, field.name + "_item2", module_name, temp_var_lines_2, is_member_access=False, create_temp_var=True)
                 if temp_code_or_var_2: code_lines.extend(temp_var_lines_2); code_lines.append(f"{seq_path}.push_back(std::move({temp_code_or_var_2}));")
            else: 
                 # v9.4: Add second value for primitive types (for better testing)
                 temp_code_or_var_2 = self._get_contextual_value(resolved_type_name, field.name + "_item2")
                 if temp_code_or_var_2 and temp_code_or_var_2 != temp_code_or_var:
                     code_lines.append(f"{seq_path}.push_back({temp_code_or_var_2});")

            return

        # Other types (Primitive, Struct, Enum, Union)
        field_path = f"{base_path}.{field.name}"
        # v9.4: field.name parameter added
        self._generate_assignment(resolved_type_name, field_path, field.name, module_name, code_lines, is_member_access=True)

    # v9.4: 'field_name' parameter added
    def _generate_assignment(self, resolved_type_name: str, path: str, field_name: str, module_name: str, code_lines: List[str], is_member_access: bool, create_temp_var: bool = False) -> Union[str, None]:
        """Generates final C++ assignment code (or value) for a type."""
        type_def = self.parser.get_type(resolved_type_name, module_name)

        # 1. TYPE: Primitive Type (v9.4 - Smart Generation)
        base_value = self._get_contextual_value(resolved_type_name, field_name)
        if base_value:
            value = base_value;
            if create_temp_var: return value
            if is_member_access: code_lines.append(f"{path}({value});") # Setter: path(value)
            else: code_lines.append(f"{path} = {value};") # Array element/Union member: path = value
            return None

        # 2. TYPE: Enum
        enum_def_direct = self.parser.get_enum_def(resolved_type_name, module_name)
        if enum_def_direct:
            # v9.4: Smart enum selection based on field
            value = None
            if "status" in field_name.lower():
                value = next((v for v in enum_def_direct.values if v == "IDLE" or v == "PATROL"), None)
            elif "type" in field_name.lower():
                value = next((v for v in enum_def_direct.values if v == "PERSON" or v == "VEHICLE"), None)
            
            # If not found, take the first one
            if not value:
                value = enum_def_direct.values[0] if enum_def_direct.values else "/*TODO_EMPTY_ENUM*/"
                
            full_value = f"{enum_def_direct.module_name}::{enum_def_direct.name}::{value}"
            if create_temp_var: return full_value
            if is_member_access: code_lines.append(f"{path}({full_value});") # Setter: path(Module::Enum::VAL)
            else: code_lines.append(f"{path} = {full_value};") # Array element/Union member
            return None

        # 3. TYPE: Struct
        struct_def_direct = self.parser.get_struct_def(resolved_type_name, module_name)
        if struct_def_direct:
            struct_path = path
            # NOTE: Use C++ getter () when accessing struct members
            if is_member_access: struct_path = f"{path}()"
            if create_temp_var:
                code_lines.append(f"{struct_def_direct.module_name}::{struct_def_direct.name} {path};")
                self._generate_for_struct_fields(struct_def_direct, path, code_lines)
                return path
            else: self._generate_for_struct_fields(struct_def_direct, struct_path, code_lines)
            return None

        # 4. TYPE: Union
        union_def_direct = None
        type_obj_union = self.parser.get_type(resolved_type_name, module_name)
        if isinstance(type_obj_union, IDLUnion): union_def_direct = type_obj_union
        if union_def_direct:
            union_path = path # Unions are usually accessed directly
            if create_temp_var: code_lines.append(f"{union_def_direct.module_name}::{union_def_direct.name} {path};")
            if not union_def_direct.cases: code_lines.append(f"// WARNING: Union '{union_def_direct.name}' is empty."); return path if create_temp_var else None
            
            # v9.3: Find first valid case for union (if not default)
            first_valid_case = None
            default_case = None
            for case in union_def_direct.cases:
                if any(label.lower().startswith("default") for label in case.discriminator_values):
                    default_case = case
                elif not first_valid_case:
                    first_valid_case = case
            
            # v9.4: Select case based on field name
            case_to_use = None
            if "status" in field_name.lower():
                case_to_use = next((c for c in union_def_direct.cases if "status" in c.field.name.lower()), None)
            elif "detection" in field_name.lower():
                case_to_use = next((c for c in union_def_direct.cases if "detection" in c.field.name.lower()), None)
            elif "command" in field_name.lower():
                case_to_use = next((c for c in union_def_direct.cases if "command" in c.field.name.lower()), None)
            
            if not case_to_use:
                case_to_use = first_valid_case or default_case # Fallback logic
                
            if not case_to_use:
                code_lines.append(f"// WARNING: No assignable 'case' found for union '{union_def_direct.name}'."); return path if create_temp_var else None

            disc_label = case_to_use.discriminator_values[0]

            if disc_label.lower().startswith("default"): case_value_str = "0 /* default case assumed */"
            else:
                case_value_str = disc_label.split(':')[-1].strip()
                disc_type_obj = self.parser.get_type(union_def_direct.discriminator_type, union_def_direct.module_name)
                if isinstance(disc_type_obj, IDLEnum): case_value_str = f"{disc_type_obj.module_name}::{disc_type_obj.name}::{case_value_str}"
                # TODO: Add quotes if discriminator is char/string

            code_lines.append(f"{union_path}._d({case_value_str});") # Set discriminator
            # Set case field. Use getter for accessing union members: path().member
            case_field_path_base = f"{union_path}()"
            case_field = case_to_use.field
            # Determine whether to use setter when filling field (_generate_assignment handles it)
            # v9.4: case_field.name parameter added
            self._generate_assignment(
                case_field.type_name, f"{case_field_path_base}.{case_field.name}", case_field.name, union_def_direct.module_name,
                code_lines, is_member_access=True # Try assignment with setter
            )
            if create_temp_var: return path
            return None

        # 5. TYPE: Unknown
        error_msg = f"// ERROR: Code could not be generated, unknown or unresolved type '{resolved_type_name}' (Path: {path}). Parser could not find type."
        print(f"!!! GENERATOR ERROR: Unknown type: '{resolved_type_name}' (path='{path}', module='{module_name}')")
        if create_temp_var: code_lines.append(error_msg); return f"/*TODO_UNKNOWN_TYPE:{resolved_type_name}*/"
        code_lines.append(error_msg)
        return None

# === 3. COMPONENT: FILE PATCHER ===
# (v9.4.1 - UnboundLocalError Fix)
class FilePatcher:
    """Scans C++ files and patches them with generated code."""
    def __init__(self, root_dir: Path, generator: CodeGenerator):
        self.root_dir = root_dir
        self.generator = generator
        self.backup_suffix = ".idl_patcher_v9.backup"
        self.BEGIN_MARKER = "// --- BEGIN AUTOGENERATED IDL PATCH (v9) ---"
        self.END_MARKER = "// --- END AUTOGENERATED IDL PATCH (v9) ---"

    def run(self):
        print(f"\nSearching for *PublisherApp.cxx files in {self.root_dir} directory...")
        publisher_files = list(self.root_dir.glob("**/*PublisherApp.cxx"))
        if not publisher_files: print("✗ No *PublisherApp.cxx files found."); return
        print(f"✓ Found {len(publisher_files)} PublisherApp files.")
        patched_count = 0
        for file_path in publisher_files:
            relative_path = file_path.relative_to(self.root_dir)
            print(f"\n--- Processing {relative_path} ---")
            try:
                if self.patch_file(file_path): patched_count += 1
            except Exception as e:
                print(f"✗ Serious error while processing file: {e}")
                import traceback; traceback.print_exc()
        print(f"\n=== Process Completed ===")
        print(f"✓ {patched_count} files successfully patched or updated.")

    def patch_file(self, file_path: Path) -> bool:
        """Patches a single C++ file and prints detected struct structure."""
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        
        # --- FIX v9.4.1: Initialize match_alt ---
        match_alt = None 
        # --- FIX END ---

        target_regex = re.compile(
            r'(\s*/\*\s*Initialize your structure here\s*\*/\s*)' # G1: Comment
            r'((?:\[[\w@]+\]\s*)*)'                          # G2: IDL Attrib.
            r'([\w::<>,\s]+\s+(\w+);)',                         # G3: Full line, G4: Variable name
            re.DOTALL
        )
        match = target_regex.search(content)
        if not match: 
            # v9.4: More flexible search, searches for either comment or variable
            target_regex_alt = re.compile(
                r'(// --- BEGIN AUTOGENERATED IDL PATCH.*?\n)' # G1: Old block start
                r'([\w::<>,\s]+\s+(\w+);)',                    # G2: Variable definition, G3: Variable name
                re.DOTALL
            )
            match_alt = target_regex_alt.search(content)
            if match_alt:
                print("  WARNING: `/* Initialize ... */` comment not found, searching for existing patch block...")
                # Manually set required groups
                comment_block = ""
                attributes_block = ""
                full_declaration_line = match_alt.group(2)
                cpp_var_name = match_alt.group(3)
                match = match_alt # Reassign 'match' object
            else:
                print("  WARNING: `/* Initialize ... */` and variable definition not found. Skipping."); return False

        # --- FIX v9.4.1: Fix 'match_alt' check ---
        # Previous code: if not match_alt:
        if not match_alt: # That is, if first (main) regex succeeded
        # --- FIX END ---
            comment_block, attributes_block, full_declaration_line, cpp_var_name = match.groups()

        # --- NEW (FIXED) TYPE EXTRACTION (v9.2) ---
        full_declaration_line_cleaned = full_declaration_line.strip() # e.g.: "const CoreData::Location m_data;"
        
        # Isolate type name by finding and removing variable name (G4) and trailing ;
        var_name_index = full_declaration_line_cleaned.rfind(cpp_var_name)
        
        # Safety check: Ensure variable name (G4) is actually at end of line (G3)
        if var_name_index == -1 or not full_declaration_line_cleaned.endswith(f"{cpp_var_name};"):
            print(f"  ERROR: Variable name '{cpp_var_name}' not properly found in declaration line. Skipping.")
            print(f"  Line: {full_declaration_line_cleaned}")
            return False

        # Take everything before variable name (e.g.: "const CoreData::Location")
        cpp_type_full_with_keywords = full_declaration_line_cleaned[:var_name_index].strip()
        
        # Remove keywords like 'const', take last word (actual type)
        # split() -> ["const", "CoreData::Location"]
        # [-1]    -> "CoreData::Location"
        cpp_type_full = cpp_type_full_with_keywords.split()[-1]
        # --- FIX END ---
        
        struct_name = cpp_type_full.split('::')[-1]
        module_name = cpp_type_full.split('::')[0] if '::' in cpp_type_full else file_path.stem.replace("PublisherApp", "")

        print(f"  Target found: Variable='{cpp_var_name}', Struct='{struct_name}', Module='{module_name}'")

        # --- Print Detected Struct Structure ---
        print(f"  Requesting '{struct_name}' (Module: '{module_name}') structure from parser...")
        struct_def = self.generator.parser.get_struct_def(struct_name, module_name)
        if not struct_def: print(f"  ERROR: Parser could not find struct definition for '{struct_name}' (Module: '{module_name}')!"); return False
        else:
            print(f"  --- Detected Structure: {struct_def.module_name}::{struct_def.name} ---")
            if not struct_def.fields: print("    (Struct is empty or fields could not be parsed)")
            else:
                for field in struct_def.fields: print(f"    - {field.name}: {field.full_type_def} (-> {field.type_name})")
            print(f"  --- End of Structure ---")
        # --- End of Printing ---

        # Generate Code
        code_lines = self.generator.generate_assignments(struct_name, module_name, cpp_var_name)

        # CORRECTED MULTI-LINE BLOCK:
        if not code_lines or code_lines[0].startswith("// ERROR"):
            print(f"  ERROR: Code could not be generated.")
            if code_lines:
                print(f"  {code_lines[0]}") # Print the error message if it exists
            return False # Exit the function

        indent = ' ' * 8
        generated_code_block = (f"\n{indent}{self.BEGIN_MARKER}\n" + f"{indent}" + f"\n{indent}".join(code_lines) + f"\n{indent}{self.END_MARKER}\n")
        
        # v9.4: Handle 'match_alt' case
        # --- FIX v9.4.1: Fix 'match_alt' check ---
        # Previous code: if 'match_alt' in locals() and match_alt:
        if match_alt: # That is, if alternative regex succeeded
        # --- FIX END ---
             # In 'match_alt' case, 'anchor_block' is just the variable definition.
            anchor_block = match_alt.group(2)
        else:
            anchor_block = f"{comment_block}{attributes_block}{match.group(3)}" # match.group(3) == full_declaration_line

        old_patch_regex_str = (rf'({re.escape(anchor_block)})' + rf'(\s*// --- BEGIN .*?PATCH(?: \(v\d+.*?\))? ---.*?// --- END .*?PATCH(?: \(v\d+.*?\))? ---)')
        old_patch_regex = re.compile(old_patch_regex_str, re.DOTALL)
        new_patch_block = f"{anchor_block}{generated_code_block}"

        new_content, count = old_patch_regex.subn(new_patch_block, content, count=1)
        if count == 0:
            anchor_regex = re.compile(re.escape(anchor_block))
            new_content, count = anchor_regex.subn(new_patch_block, content, count=1)
        if count == 0: print("  ERROR: Target (anchor) for code injection not found."); return False

        if new_content != content:
            backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)
            try:
                with open(backup_path, 'w', encoding='utf-8') as f_backup: f_backup.write(content)
                print(f"  Backup created: {backup_path.name}")
            except Exception as e: print(f"  WARNING: Backup could not be created: {e}")
            with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
            print("  ✓ File successfully patched.")
            return True
        else:
            print("  ✓ File already up to date. No changes made.")
            return True

# === MAIN EXECUTION FUNCTION ===
def main():
    print(f"=== IDL Default Data Patcher Starting (v9.4.1 - {CURRENT_SCRIPT_DIR.name}) ===")
    print(f"Project Root: {PROJECT_ROOT}")

    temp_gen = CodeGenerator(None) # type: ignore
    primitive_types = temp_gen.get_primitive_types()
    parser = IDLParser(primitive_types=primitive_types)
    parser.parse_all_idls(IDL_DIR)
    if not parser.types: print("IDL types not found. Exiting."); return
    generator = CodeGenerator(parser)
    patcher = FilePatcher(PROJECT_ROOT, generator)
    patcher.run()

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"\n!!! UNEXPECTED ERROR !!!\n{e}")
        import traceback; traceback.print_exc()
    if os.name == 'nt': input("\nPress Enter to exit...")

