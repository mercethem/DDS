#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QoS Patcher GUI

Baslat: scripts/qos_patcher.bat

Özellikler:
- Modül ve varyasyon (Publisher/Subscriber) seçimi (çoklu seçim, scrollable)
- Basit mod: yalnızca History
- Gelişmiş mod: Reader/Writer için tüm desteklenen QoS alanları
- Uygula: Seçilen dosyalara idempotent QoS patch uygular (scripts/py/qos_patcher.py kullanır)
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Patcher modülünü içe aktarabilmek için sys.path ayarla
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import qos_patcher as qp
except Exception as e:
    messagebox.showerror("Import Hatası", f"qos_patcher.py import edilemedi: {e}")
    raise


class QosPatcherGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Fast DDS QoS Patcher")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Veri
        self.all_files = qp._find_target_files()
        self.grouped = qp._group_targets_by_module(self.all_files)

        # UI (grid tabanlı, tam ekran duyarlı)
        self._build_ui()

    def _build_ui(self) -> None:
        # Ana grid yapılandırması (0..4 satır)
        for r in range(5):
            self.rowconfigure(r, weight=(1 if r in (0, 3) else 0))
        self.columnconfigure(0, weight=1)

        # Üst kısım: Modül listesi + Varyasyon seçimleri
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ttk.Label(top, text="Modüller").grid(row=0, column=0, sticky="w")
        self.modules_list = tk.Listbox(top, selectmode=tk.EXTENDED, height=8)
        self._populate_modules()
        mod_scroll = ttk.Scrollbar(top, orient=tk.VERTICAL, command=self.modules_list.yview)
        self.modules_list.config(yscrollcommand=mod_scroll.set)
        self.modules_list.grid(row=1, column=0, sticky="nsew")
        mod_scroll.grid(row=1, column=1, sticky="ns")

        role_frame = ttk.LabelFrame(top, text="Varyasyon")
        role_frame.grid(row=1, column=2, padx=15, sticky="n")
        self.role_pub = tk.BooleanVar(value=True)
        self.role_sub = tk.BooleanVar(value=True)
        ttk.Checkbutton(role_frame, text="Publisher", variable=self.role_pub).pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(role_frame, text="Subscriber", variable=self.role_sub).pack(anchor="w", padx=10, pady=5)

        # Mod seçimi
        mode_frame = ttk.LabelFrame(self, text="Mod")
        mode_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.mode = tk.StringVar(value="simple")
        ttk.Radiobutton(mode_frame, text="Basit (Sadece History)", value="simple", variable=self.mode).pack(anchor="w", padx=10, pady=5)
        ttk.Radiobutton(mode_frame, text="Gelişmiş (Reader/Writer tüm QoS)", value="advanced", variable=self.mode).pack(anchor="w", padx=10)

        # Basit QoS alanı
        simple_frame = ttk.LabelFrame(self, text="History QoS")
        simple_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Label(simple_frame, text="History.kind:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.hist_kind = tk.StringVar(value="Seçiniz")
        self.hist_kind_cb = ttk.Combobox(simple_frame, values=["Seçiniz", "KEEP_LAST", "KEEP_ALL"], textvariable=self.hist_kind, state="readonly", width=20)
        self.hist_kind_cb.grid(row=0, column=1, sticky="w")
        ttk.Label(simple_frame, text="History.depth:").grid(row=0, column=2, sticky="e", padx=10)
        self.hist_depth = tk.StringVar(value="")
        self.hist_depth_entry = ttk.Entry(simple_frame, textvariable=self.hist_depth, width=10)
        self.hist_depth_entry.grid(row=0, column=3, sticky="w")

        # Gelişmiş QoS alanı
        # Gelişmiş QoS alanı (kaydırılabilir)
        adv_container = ttk.LabelFrame(self, text="Gelişmiş QoS Seçimleri")
        adv_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        adv_container.rowconfigure(0, weight=1)
        adv_container.columnconfigure(0, weight=1)
        self.adv_canvas = tk.Canvas(adv_container, highlightthickness=0)
        adv_scroll = ttk.Scrollbar(adv_container, orient=tk.VERTICAL, command=self.adv_canvas.yview)
        self.adv_frame = ttk.Frame(self.adv_canvas)
        self.adv_frame.bind(
            "<Configure>",
            lambda e: self.adv_canvas.configure(scrollregion=self.adv_canvas.bbox("all")),
        )
        self.adv_canvas.create_window((0, 0), window=self.adv_frame, anchor="nw")
        self.adv_canvas.configure(yscrollcommand=adv_scroll.set)
        self.adv_canvas.grid(row=0, column=0, sticky="nsew")
        adv_scroll.grid(row=0, column=1, sticky="ns")
        # Fill advanced widgets
        self._build_advanced_section(self.adv_frame)
        self._attach_tooltips()

        # Alt: Butonlar
        bottom = ttk.Frame(self)
        bottom.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        bottom.columnconfigure(0, weight=1)
        btns = ttk.Frame(bottom)
        btns.grid(row=0, column=1, sticky="e")
        ttk.Button(btns, text="İptal", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Kaydet", command=self.on_save).pack(side=tk.RIGHT)

        # Başlangıçta gelişmiş alanı disable et
        self._sync_mode_state()
        self.mode.trace_add("write", lambda *args: self._sync_mode_state())

        # Grid yapılandırma
        top.columnconfigure(0, weight=1)
        top.rowconfigure(1, weight=1)
        # Canvas boyutunu pencere ile senkronla
        def _sync_canvas_width(event):
            self.adv_canvas.configure(width=event.width - 16)
        self.bind("<Configure>", _sync_canvas_width)

    def _populate_modules(self) -> None:
        self.modules_list.delete(0, tk.END)
        for module in sorted(self.grouped.keys()):
            roles = []
            if "publisher" in self.grouped[module]:
                roles.append("Publisher")
            if "subscriber" in self.grouped[module]:
                roles.append("Subscriber")
            self.modules_list.insert(tk.END, f"{module} — {', '.join(roles)}")

    def _build_advanced_section(self, parent: ttk.LabelFrame) -> None:
        # Enums
        enums = qp.FASTDDS_QOS_ENUMS
        rel_opts = sorted(list(enums["ReliabilityQosPolicyKind"]))
        dur_opts = sorted(list(enums["DurabilityQosPolicyKind"]))
        liv_opts = sorted(list(enums["LivelinessQosPolicyKind"]))
        dst_opts = sorted(list(enums["DestinationOrderQosPolicyKind"]))
        own_opts = sorted(list(enums["OwnershipQosPolicyKind"]))

        # Writer widgets
        wf = ttk.LabelFrame(parent, text="Writer QoS")
        wf.pack(fill=tk.X, padx=10, pady=8)
        self.w_rel = tk.StringVar(value="Seçiniz")
        self.w_dur = tk.StringVar(value="Seçiniz")
        self.w_liv = tk.StringVar(value="Seçiniz")
        self.w_dst = tk.StringVar(value="Seçiniz")
        self.w_own = tk.StringVar(value="Seçiniz")
        self.w_ostr = tk.StringVar(value="")
        self.w_async = tk.BooleanVar(value=False)
        self.w_rl_max = tk.StringVar(value="")
        self.w_rl_alloc = tk.StringVar(value="")
        self.w_rl_enable = tk.BooleanVar(value=False)

        self.w_rel_cb = self._row_writer(wf, "Reliability", self.w_rel, ["Seçiniz"] + rel_opts, 0)
        self.w_dur_cb = self._row_writer(wf, "Durability", self.w_dur, ["Seçiniz"] + dur_opts, 1)
        self.w_liv_cb = self._row_writer(wf, "Liveliness", self.w_liv, ["Seçiniz"] + liv_opts, 2)
        self.w_dst_cb = self._row_writer(wf, "DestinationOrder", self.w_dst, ["Seçiniz"] + dst_opts, 3)
        self.w_own_cb = self._row_writer(wf, "Ownership", self.w_own, ["Seçiniz"] + own_opts, 4)
        ttk.Label(wf, text="OwnershipStrength").grid(row=5, column=0, sticky="e", padx=6, pady=4)
        self.w_ostr_entry = ttk.Entry(wf, textvariable=self.w_ostr, width=10)
        self.w_ostr_entry.grid(row=5, column=1, sticky="w")
        ttk.Checkbutton(wf, text="PublishMode Async", variable=self.w_async).grid(row=5, column=2, sticky="w")
        ttk.Checkbutton(wf, text="ResourceLimits'i ayarla", variable=self.w_rl_enable).grid(row=6, column=0, sticky="e", padx=6, pady=4)
        self.w_rl_max_entry = ttk.Entry(wf, textvariable=self.w_rl_max, width=10)
        self.w_rl_max_entry.grid(row=6, column=1, sticky="w")
        ttk.Label(wf, text="allocated_samples").grid(row=6, column=2, sticky="e", padx=6, pady=4)
        self.w_rl_alloc_entry = ttk.Entry(wf, textvariable=self.w_rl_alloc, width=10)
        self.w_rl_alloc_entry.grid(row=6, column=3, sticky="w")

        # Reader widgets
        rf = ttk.LabelFrame(parent, text="Reader QoS")
        rf.pack(fill=tk.X, padx=10, pady=8)
        self.r_rel = tk.StringVar(value="Seçiniz")
        self.r_dur = tk.StringVar(value="Seçiniz")
        self.r_liv = tk.StringVar(value="Seçiniz")
        self.r_dst = tk.StringVar(value="Seçiniz")
        self.r_own = tk.StringVar(value="Seçiniz")
        self.r_rl_max = tk.StringVar(value="")
        self.r_rl_alloc = tk.StringVar(value="")
        self.r_rl_enable = tk.BooleanVar(value=False)

        self.r_rel_cb = self._row_reader(rf, "Reliability", self.r_rel, ["Seçiniz"] + rel_opts, 0)
        self.r_dur_cb = self._row_reader(rf, "Durability", self.r_dur, ["Seçiniz"] + dur_opts, 1)
        self.r_liv_cb = self._row_reader(rf, "Liveliness", self.r_liv, ["Seçiniz"] + liv_opts, 2)
        self.r_dst_cb = self._row_reader(rf, "DestinationOrder", self.r_dst, ["Seçiniz"] + dst_opts, 3)
        self.r_own_cb = self._row_reader(rf, "Ownership", self.r_own, ["Seçiniz"] + own_opts, 4)
        ttk.Checkbutton(rf, text="ResourceLimits'i ayarla", variable=self.r_rl_enable).grid(row=5, column=0, sticky="e", padx=6, pady=4)
        self.r_rl_max_entry = ttk.Entry(rf, textvariable=self.r_rl_max, width=10)
        self.r_rl_max_entry.grid(row=5, column=1, sticky="w")
        ttk.Label(rf, text="allocated_samples").grid(row=5, column=2, sticky="e", padx=6, pady=4)
        self.r_rl_alloc_entry = ttk.Entry(rf, textvariable=self.r_rl_alloc, width=10)
        self.r_rl_alloc_entry.grid(row=5, column=3, sticky="w")

        # Grid expansion for writer/reader frames
        for f in (wf, rf):
            for c in range(1, 4):
                f.columnconfigure(c, weight=1)

    def _row_writer(self, parent, label, var, options, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=6, pady=4)
        cb = ttk.Combobox(parent, values=options, textvariable=var, state="readonly", width=48)
        cb.grid(row=row, column=1, columnspan=3, sticky="w")
        cb._qos_label = label
        return cb

    def _row_reader(self, parent, label, var, options, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=6, pady=4)
        cb = ttk.Combobox(parent, values=options, textvariable=var, state="readonly", width=48)
        cb.grid(row=row, column=1, columnspan=3, sticky="w")
        cb._qos_label = label
        return cb

    def _sync_mode_state(self) -> None:
        adv = self.mode.get() == "advanced"
        state = tk.NORMAL if adv else tk.DISABLED
        for child in self.adv_frame.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass

    def _selected_modules(self):
        indices = self.modules_list.curselection()
        labels = [self.modules_list.get(i) for i in indices]
        modules = [lbl.split(" — ")[0] for lbl in labels]
        return modules

    def _selected_roles(self) -> str:
        pub = self.role_pub.get()
        sub = self.role_sub.get()
        if pub and sub:
            return "both"
        if pub:
            return "publisher"
        if sub:
            return "subscriber"
        return "none"

    def on_save(self) -> None:
        modules = self._selected_modules()
        if not modules:
            messagebox.showwarning("Seçim", "En az bir modül seçin")
            return
        roles = self._selected_roles()
        if roles == "none":
            messagebox.showwarning("Seçim", "En az bir varyasyon seçin (Publisher/Subscriber)")
            return

        # Dosya listesi
        chosen_files = []
        for m in modules:
            rmap = self.grouped.get(m, {})
            if roles in ("publisher", "both") and "publisher" in rmap:
                chosen_files.append(rmap["publisher"])
            if roles in ("subscriber", "both") and "subscriber" in rmap:
                chosen_files.append(rmap["subscriber"])
        if not chosen_files:
            messagebox.showinfo("Bilgi", "Kriterlere uygun dosya bulunamadı")
            return

        # QoS girdi derle
        if self.mode.get() == "simple":
            hkind = self.hist_kind.get()
            if hkind not in ("KEEP_LAST", "KEEP_ALL"):
                messagebox.showerror("Hata", "History.kind geçersiz")
                return
            if hkind == "KEEP_LAST":
                try:
                    depth = int(self.hist_depth.get())
                    if depth <= 0:
                        raise ValueError
                except Exception:
                    messagebox.showerror("Hata", "History.depth pozitif tamsayı olmalıdır")
                    return
                history = {"kind": "KEEP_LAST", "depth": depth}
            else:
                history = {"kind": "KEEP_ALL", "depth": None}
            effective_qos = qp.DEFAULT_QOS
        else:
            # Advanced
            writer_cfg = ({}) if roles in ("publisher", "both") else qp.DEFAULT_QOS["writer"]
            reader_cfg = ({}) if roles in ("subscriber", "both") else qp.DEFAULT_QOS["reader"]
            # Writer
            if roles in ("publisher", "both"):
                if self.w_rel.get() != "Seçiniz":
                    writer_cfg["reliability"] = self.w_rel.get()
                if self.w_dur.get() != "Seçiniz":
                    writer_cfg["durability"] = self.w_dur.get()
                if self.w_liv.get() != "Seçiniz":
                    writer_cfg["liveliness"] = self.w_liv.get()
                if self.w_dst.get() != "Seçiniz":
                    writer_cfg["destination_order"] = self.w_dst.get()
                if self.w_own.get() != "Seçiniz":
                    writer_cfg["ownership"] = self.w_own.get()
                if self.w_ostr.get().strip() != "":
                    writer_cfg["ownership_strength"] = int(self.w_ostr.get())
                if self.w_async.get():
                    writer_cfg["publish_mode_async"] = True
                if self.w_rl_enable.get():
                    rlw = {}
                    if self.w_rl_max.get().strip() != "":
                        rlw["max_samples"] = int(self.w_rl_max.get())
                    if self.w_rl_alloc.get().strip() != "":
                        rlw["allocated_samples"] = int(self.w_rl_alloc.get())
                    if rlw:
                        writer_cfg["resource_limits"] = rlw
            # Reader
            if roles in ("subscriber", "both"):
                if self.r_rel.get() != "Seçiniz":
                    reader_cfg["reliability"] = self.r_rel.get()
                if self.r_dur.get() != "Seçiniz":
                    reader_cfg["durability"] = self.r_dur.get()
                if self.r_liv.get() != "Seçiniz":
                    reader_cfg["liveliness"] = self.r_liv.get()
                if self.r_dst.get() != "Seçiniz":
                    reader_cfg["destination_order"] = self.r_dst.get()
                if self.r_own.get() != "Seçiniz":
                    reader_cfg["ownership"] = self.r_own.get()
                if self.r_rl_enable.get():
                    rlr = {}
                    if self.r_rl_max.get().strip() != "":
                        rlr["max_samples"] = int(self.r_rl_max.get())
                    if self.r_rl_alloc.get().strip() != "":
                        rlr["allocated_samples"] = int(self.r_rl_alloc.get())
                    if rlr:
                        reader_cfg["resource_limits"] = rlr
            # History (her iki role için aynı)
            history = {"kind": None, "depth": None}
            if self.hist_kind.get() in ("KEEP_LAST", "KEEP_ALL"):
                history["kind"] = self.hist_kind.get()
                if history["kind"] == "KEEP_LAST":
                    if self.hist_depth.get().strip() != "":
                        history["depth"] = int(self.hist_depth.get())
            effective_qos = {
                **qp.DEFAULT_QOS,
                "writer": writer_cfg,
                "reader": reader_cfg,
            }

        ok, reason = qp.validate_qos(history, effective_qos)
        if not ok:
            messagebox.showerror("Doğrulama", f"QoS doğrulama hatası: {reason}")
            return

        # Patch uygula
        qp.backup_files(chosen_files)
        patched, skipped = [], []
        for f in chosen_files:
            if qp._patch_single_file(Path(f), history, effective_qos):
                patched.append(f)
            else:
                skipped.append(f)

        # Özet
        msg = ["QoS Patch Özeti:"]
        msg.append(f"Patched: {len(patched)}")
        for p in patched:
            msg.append(f"  - {p}")
        msg.append(f"Skipped: {len(skipped)}")
        for s in skipped:
            msg.append(f"  - {s}")
        messagebox.showinfo("Sonuç", "\n".join(msg))

    def on_cancel(self) -> None:
        self.destroy()

    # Otomatik doldurma: modül/role seçimleri değiştiğinde mevcut QoS'u tara
    def _autofill_from_code(self) -> None:
        modules = self._selected_modules()
        roles = self._selected_roles()
        if not modules or roles == "none":
            return
        # İlk uygun dosyayı baz al (UI basitliği için)
        chosen_files = []
        for m in modules:
            rmap = self.grouped.get(m, {})
            if roles in ("publisher", "both") and "publisher" in rmap:
                chosen_files.append(rmap["publisher"])
            if roles in ("subscriber", "both") and "subscriber" in rmap:
                chosen_files.append(rmap["subscriber"])
        if not chosen_files:
            return
        # Reader
        reader_file = next((f for f in chosen_files if str(f).endswith("SubscriberApp.cxx")), None)
        if reader_file:
            rqos, rhist = qp.extract_qos_from_file(reader_file, is_reader=True)
            # History
            if rhist.get("kind") in ("KEEP_LAST", "KEEP_ALL"):
                self.hist_kind.set(rhist["kind"])
            if rhist.get("depth"):
                self.hist_depth.set(str(rhist["depth"]))
            # Reader fields (advanced)
            if "reliability" in rqos:
                self.r_rel.set(rqos["reliability"])
            if "durability" in rqos:
                self.r_dur.set(rqos["durability"])
            if "liveliness" in rqos:
                self.r_liv.set(rqos["liveliness"])
            if "destination_order" in rqos:
                self.r_dst.set(rqos["destination_order"])
            if "ownership" in rqos:
                self.r_own.set(rqos["ownership"])
            if "resource_limits" in rqos:
                rl = rqos["resource_limits"]
                if "max_samples" in rl:
                    self.r_rl_max.set(str(rl["max_samples"]))
                if "allocated_samples" in rl:
                    self.r_rl_alloc.set(str(rl["allocated_samples"]))
        # Writer
        writer_file = next((f for f in chosen_files if str(f).endswith("PublisherApp.cxx")), None)
        if writer_file:
            wqos, whist = qp.extract_qos_from_file(writer_file, is_reader=False)
            # History (UI tek alan, yazılanda da gösterelim)
            if whist.get("kind") in ("KEEP_LAST", "KEEP_ALL"):
                self.hist_kind.set(whist["kind"])
            if whist.get("depth"):
                self.hist_depth.set(str(whist["depth"]))
            # Writer fields
            if "reliability" in wqos:
                self.w_rel.set(wqos["reliability"])
            if "durability" in wqos:
                self.w_dur.set(wqos["durability"])
            if "liveliness" in wqos:
                self.w_liv.set(wqos["liveliness"])
            if "destination_order" in wqos:
                self.w_dst.set(wqos["destination_order"])
            if "ownership" in wqos:
                self.w_own.set(wqos["ownership"])
            if "ownership_strength" in wqos:
                self.w_ostr.set(str(wqos["ownership_strength"]))
            self.w_async.set(bool(wqos.get("publish_mode_async", False)))
            if "resource_limits" in wqos:
                rlw = wqos["resource_limits"]
                if "max_samples" in rlw:
                    self.w_rl_max.set(str(rlw["max_samples"]))
                if "allocated_samples" in rlw:
                    self.w_rl_alloc.set(str(rlw["allocated_samples"]))

    def _bind_autofill(self) -> None:
        # Modül listesi ve role checkleri değiştiğinde otomatik doldur
        def _on_sel_change(*args):
            self._autofill_from_code()
        self.modules_list.bind("<<ListboxSelect>>", lambda e: _on_sel_change())
        self.role_pub.trace_add("write", lambda *a: _on_sel_change())
        self.role_sub.trace_add("write", lambda *a: _on_sel_change())
        # Enable/disable numeric fields based on selections
        def _sync_numeric_state(*args):
            # History depth only if KEEP_LAST
            hd_state = tk.NORMAL if self.hist_kind.get() == "KEEP_LAST" else tk.DISABLED
            try:
                self.hist_depth_entry.configure(state=hd_state)
            except Exception:
                pass
            # Writer ownership_strength only if ownership set
            wos_state = tk.NORMAL if self.w_own.get() != "Seçiniz" else tk.DISABLED
            try:
                self.w_ostr_entry.configure(state=wos_state)
            except Exception:
                pass
            # Resource limits only if enable checked
            try:
                self.w_rl_max_entry.configure(state=(tk.NORMAL if self.w_rl_enable.get() else tk.DISABLED))
                self.w_rl_alloc_entry.configure(state=(tk.NORMAL if self.w_rl_enable.get() else tk.DISABLED))
                self.r_rl_max_entry.configure(state=(tk.NORMAL if self.r_rl_enable.get() else tk.DISABLED))
                self.r_rl_alloc_entry.configure(state=(tk.NORMAL if self.r_rl_enable.get() else tk.DISABLED))
            except Exception:
                pass
        # Bind changes
        self.hist_kind.trace_add("write", _sync_numeric_state)
        self.w_own.trace_add("write", _sync_numeric_state)
        self.w_rl_enable.trace_add("write", _sync_numeric_state)
        self.r_rl_enable.trace_add("write", _sync_numeric_state)
        # Initial state
        _sync_numeric_state()

    def _attach_tooltips(self) -> None:
        # Basit tooltip aracı
        tips = {
            "Reliability": "Veri teslimat güvencesi. RELIABLE: paket kaybı tespit edilir ve telafi edilir. BEST_EFFORT: düşük gecikme, kayıp mümkün.",
            "Durability": "Verinin yeni abonelere sunulma kalıcılığı. VOLATILE: geçmiş sunulmaz. TRANSIENT_LOCAL: yazar tarafında cachelenmiş geçmiş sunulabilir.",
            "Liveliness": "Yayıncı/abonenin canlılığının nasıl doğrulandığı. AUTOMATIC veya MANUAL_BY_TOPIC/PARTICIPANT.",
            "DestinationOrder": "Teslim sırası. Kaynak zaman damgasına (BY_SOURCE) veya alım zamanına (BY_RECEPTION) göre.",
            "Ownership": "Aynı instance üzerinde SHARED (birden çok yazar) ya da EXCLUSIVE (tek yazar) sahiplik.",
        }

        def bind_tooltip(widget, label_key):
            text = tips.get(label_key, "")
            if not text:
                return
            tipwin = {"win": None}

            def show_tip(event):
                if tipwin["win"] is not None:
                    return
                x = event.x_root + 12
                y = event.y_root + 12
                tw = tk.Toplevel(widget)
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f"+{x}+{y}")
                lbl = ttk.Label(tw, text=text, justify="left", relief="solid", borderwidth=1, padding=6, background="#ffffe0")
                lbl.pack()
                tipwin["win"] = tw

            def hide_tip(event):
                if tipwin["win"] is not None:
                    tipwin["win"].destroy()
                    tipwin["win"] = None

            widget.bind("<Enter>", show_tip)
            widget.bind("<Leave>", hide_tip)

        # Writer tooltips
        for cb in (self.w_rel_cb, self.w_dur_cb, self.w_liv_cb, self.w_dst_cb, self.w_own_cb):
            bind_tooltip(cb, cb._qos_label)
        # Reader tooltips
        for cb in (self.r_rel_cb, self.r_dur_cb, self.r_liv_cb, self.r_dst_cb, self.r_own_cb):
            bind_tooltip(cb, cb._qos_label)

    # Başlangıçta çağır
    def after_idle_init(self) -> None:
        self._bind_autofill()
        self._autofill_from_code()


if __name__ == "__main__":
    app = QosPatcherGUI()
    app.after(200, app.after_idle_init)
    app.mainloop()


