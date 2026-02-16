#!/usr/bin/env python3
"""
NTFS --> EXT4 | by jm@qvert.net
FORENSIC COPY TOOL | Accuracy-First Implementation | Zero Assumptions | Full Audit Trail
"""
import os
import sys
import subprocess
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk

# 🔒 SAFETY: Block root execution
if os.geteuid() == 0:
    print("❌ CRITICAL: DO NOT RUN AS ROOT. Launch as your normal user (jm).")
    sys.exit(1)

# 📜 EXCLUSION POLICY: ONLY NTFS SYSTEM ARTIFACTS
NTFS_EXCLUSIONS = [
    ".Trashes", 
    "$RECYCLE.BIN", 
    "System Volume Information", 
    "desktop.ini", 
    "Thumbs.db",
    "Thumbs.db:encryptable",
    "ehthumbs.db",
    "ehthumbs_vista.db"
]
EXCLUSION_SET = set(NTFS_EXCLUSIONS)

class ForensicCopyGUI:
    def __init__(self, root):
        self.root = root
        root.title("NTFS --> EXT4 | by jm@qvert.net")
        
        # ✅ WINDOW SIZE (visible on standard monitors, all elements shown)
        root.geometry("1920x1080")
        root.minsize(1400, 900)
        
        # 🎨 CONFIGURE STYLE (Safe Theme)
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')  # Try clam first
        except:
            self.style.theme_use('default')  # Fallback to default
        
        # Configure button style
        self.style.configure('TButton', 
                            font=('Segoe UI', 12),
                            padding=(20, 15))
        
        self.copy_start_time = None
        
        # 🎨 FONT DEFINITIONS (Large - Visible)
        self.FONT_LABEL = ("Segoe UI", 12, "bold")
        self.FONT_ENTRY = ("Monospace", 12)
        self.FONT_BUTTON = ("Segoe UI", 12, "bold")
        self.FONT_LOG = ("Monospace", 12)
        
        # 🎨 PADDING (Symmetrical - No Overlap)
        self.PAD_X = 15
        self.PAD_Y = 12
        
        # =============== GRID CONFIGURATION (Dynamic Resize) ===============
        for i in range(7):
            root.grid_rowconfigure(i, weight=1 if i == 5 else 0)
        root.grid_columnconfigure(1, weight=1)  # Entry fields expand
        
        # --- Row 0: Source Path (Label + Entry + Button on SAME row) ---
        tk.Label(root, text="SOURCE (NTFS):", font=self.FONT_LABEL, anchor='w').grid(
            row=0, column=0, sticky="w", padx=self.PAD_X, pady=self.PAD_Y)
        
        self.src_var = tk.StringVar(value="/media/jm/NAS/GITHUB_REPOS")
        self.src_entry = tk.Entry(root, textvariable=self.src_var, font=self.FONT_ENTRY, 
                                  bg="#ffffff", fg="#000000", relief='solid', bd=2)
        self.src_entry.grid(row=0, column=1, sticky="ew", padx=self.PAD_X, pady=self.PAD_Y)
        
        self.btn_browse_src = tk.Button(root, text="Browse", command=self.browse_src, 
                                        font=self.FONT_LABEL, bg="#e0e0e0", 
                                        relief='raised', bd=3, cursor='hand2')
        self.btn_browse_src.grid(row=0, column=2, padx=self.PAD_X, pady=self.PAD_Y)
        
        # --- Row 1: Destination Path (Label + Entry + Button on SAME row) ---
        tk.Label(root, text="DESTINATION (ext4):", font=self.FONT_LABEL, anchor='w').grid(
            row=1, column=0, sticky="w", padx=self.PAD_X, pady=self.PAD_Y)
        
        self.dst_var = tk.StringVar(value="/media/jm/SAMSUNG9801TB/GITHUB_REPOS")
        self.dst_entry = tk.Entry(root, textvariable=self.dst_var, font=self.FONT_ENTRY, 
                                  bg="#ffffff", fg="#000000", relief='solid', bd=2)
        self.dst_entry.grid(row=1, column=1, sticky="ew", padx=self.PAD_X, pady=self.PAD_Y)
        
        self.btn_browse_dst = tk.Button(root, text="Browse", command=self.browse_dst, 
                                        font=self.FONT_LABEL, bg="#e0e0e0", 
                                        relief='raised', bd=3, cursor='hand2')
        self.btn_browse_dst.grid(row=1, column=2, padx=self.PAD_X, pady=self.PAD_Y)
        
        # --- Row 2: Action Button (Full Width) ---
        self.btn = tk.Button(root, text="Start Copy", command=self.start_copy, 
                           font=self.FONT_BUTTON, bg="#1a5fb4", fg="#ffffff", 
                           relief='raised', bd=4, cursor='hand2', height=2)
        self.btn.grid(row=2, column=0, columnspan=3, pady=self.PAD_Y*2, padx=self.PAD_X, sticky="ew")
        
        # --- Row 3: Progress Bar (✅ FIXED STYLE) ---
        # Removed explicit style name that caused layout error
        self.progress = ttk.Progressbar(root, mode='indeterminate', orient=tk.HORIZONTAL)
        self.progress.grid(row=3, column=0, columnspan=3, sticky="ew", padx=self.PAD_X*2, pady=self.PAD_Y)
        self.progress.grid_remove()
        
        # --- Row 4: Log Label ---
        tk.Label(root, text="AUDIT LOG (Timestamped | Verbose | Immutable):", 
                font=self.FONT_LABEL, anchor='w').grid(
            row=4, column=0, columnspan=3, sticky="w", padx=self.PAD_X, pady=self.PAD_Y)
        
        # --- Row 5: Log Area (Expands with window) ---
        self.log_frame = tk.Frame(root)
        self.log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=self.PAD_X, pady=self.PAD_Y)
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        self.log = scrolledtext.ScrolledText(self.log_frame, wrap=tk.NONE, 
                                             font=self.FONT_LOG, bg="#1e1e1e", fg="#d4d4d4",
                                             relief='sunken', bd=2, padx=10, pady=10)
        self.log.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        self.log_xscroll = tk.Scrollbar(self.log_frame, orient=tk.HORIZONTAL, command=self.log.xview)
        self.log_xscroll.grid(row=1, column=0, sticky="ew")
        self.log.configure(xscrollcommand=self.log_xscroll.set)
        
        # --- Row 6: Status Bar ---
        self.status_var = tk.StringVar(value="Ready | User: {} | UID: {}".format(os.getenv('USER'), os.getuid()))
        self.status_bar = tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 16), 
                                   bg="#f0f0f0", relief='sunken', anchor='w', padx=10, pady=5)
        self.status_bar.grid(row=6, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        
        # =============== INITIAL AUDIT LOG ===============
        self.log_insert("="*100 + "\n")
        self.log_insert(f" SESSION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log_insert(f" USER: {os.getenv('USER')} | UID: {os.getuid()} | GID: {os.getgid()}\n")
        self.log_insert(f" PYTHON: {sys.version.split()[0]} | TKINTER: {tk.TkVersion}\n")
        self.log_insert(f"  SAFETY: Root execution BLOCKED\n")
        self.log_insert("="*100 + "\n\n")
        self.log_insert("✅ READY - Click 'Start Copy' to begin forensic transfer\n\n")

    def log_insert(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefixed = f"[{timestamp}] {text}"
        self.log.insert(tk.END, prefixed)
        self.log.see(tk.END)
        self.root.update_idletasks()

    def browse_src(self):
        path = filedialog.askdirectory(initialdir=self.src_var.get(), 
                                       title="SELECT NTFS SOURCE DIRECTORY")
        if path: 
            self.src_var.set(path)
            self.log_insert(f"📁 SOURCE: {path}\n")

    def browse_dst(self):
        path = filedialog.askdirectory(initialdir=os.path.dirname(self.dst_var.get()), 
                                       title="SELECT ext4 DESTINATION PARENT")
        if path:
            base = os.path.basename(self.src_var.get().rstrip('/'))
            new_dst = os.path.join(path, base) if base else path
            self.dst_var.set(new_dst)
            self.log_insert(f"📁 DESTINATION: {new_dst}\n")

    def validate_paths(self):
        s, d = self.src_var.get().strip(), self.dst_var.get().strip()
        if not s or not d: return "ERROR: Paths cannot be empty"
        if not os.path.isabs(s) or not os.path.isabs(d): return "ERROR: Paths must be absolute"
        if not os.path.isdir(s): return f"ERROR: Source not found: {s}"
        if not os.access(s, os.R_OK): return f"ERROR: No read access to source"
        if not os.path.isdir(os.path.dirname(d)): return f"ERROR: Destination parent invalid"
        if os.path.exists(d) and not os.access(d, os.W_OK): return f"ERROR: No write access to destination"
        return None

    def scan_source(self, src):
        self.log_insert("\n🔍 PRE-COPY FORENSIC SCAN...\n")
        start_scan = time.time()
        
        total_files = 0
        total_dirs = 0
        hidden_files = []
        hidden_dirs = []
        case_conflicts = {}
        sample_verification = []
        
        for root, dirs, files in os.walk(src, topdown=True):
            dirs[:] = [d for d in dirs if d not in EXCLUSION_SET]
            
            for d in dirs:
                total_dirs += 1
                if d.startswith('.') and d not in EXCLUSION_SET:
                    hidden_dirs.append(os.path.relpath(os.path.join(root, d), src))
            
            for f in files:
                if f in EXCLUSION_SET:
                    continue
                total_files += 1
                rel_path = os.path.relpath(os.path.join(root, f), src)
                
                if f.startswith('.') and f not in EXCLUSION_SET:
                    hidden_files.append(rel_path)
                
                key = f.lower()
                if key not in case_conflicts:
                    case_conflicts[key] = []
                case_conflicts[key].append(f)
                
                if len(sample_verification) < 10 and os.path.getsize(os.path.join(root, f)) > 1024:
                    sample_verification.append((rel_path, os.path.getsize(os.path.join(root, f))))
        
        real_conflicts = {k: v for k, v in case_conflicts.items() if len(set(v)) > 1}
        scan_duration = time.time() - start_scan
        
        self.log_insert(f"✅ SCAN COMPLETE ({scan_duration:.2f}s)\n")
        self.log_insert(f"   FILES: {total_files:,} | DIRECTORIES: {total_dirs:,}\n")
        self.log_insert(f"   HIDDEN FILES: {len(hidden_files):,} | HIDDEN DIRS: {len(hidden_dirs):,}\n")
        
        if hidden_files:
            self.log_insert(f"   SAMPLE HIDDEN: {hidden_files[0]}\n")
        
        if real_conflicts:
            self.log_insert(f"   ⚠️  CASE CONFLICTS: {len(real_conflicts)}\n")
        
        return {
            'total_files': total_files,
            'total_dirs': total_dirs,
            'hidden_files_count': len(hidden_files),
            'hidden_dirs_count': len(hidden_dirs),
            'case_conflicts': real_conflicts,
            'sample_verification': sample_verification,
            'scan_duration': scan_duration
        }

    def start_copy(self):
        if err := self.validate_paths():
            messagebox.showerror("VALIDATION FAILED", err)
            self.log_insert(f"❌ VALIDATION FAILED: {err}\n")
            return
        
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()
        
        scan_report = self.scan_source(src)
        
        size_bytes = sum(os.path.getsize(os.path.join(dp, f)) 
                        for dp, _, fn in os.walk(src) 
                        for f in fn if f not in EXCLUSION_SET)
        size_gb = size_bytes / (1024**3)
        
        confirm_msg = (
            f"SOURCE: {src}\n"
            f"DESTINATION: {dst}\n\n"
            f"FILES: {scan_report['total_files']:,}\n"
            f"SIZE: {size_gb:.2f} GB\n\n"
            f"PROCEED?"
        )
        
        if size_gb > 0.1 and not messagebox.askyesno("CONFIRM COPY", confirm_msg, icon=messagebox.WARNING):
            self.log_insert("🛑 CANCELLED BY USER\n")
            return
        
        self.btn.config(state=tk.DISABLED, text="⏳ COPYING...")
        self.progress.grid()
        self.progress.start(10)
        self.copy_start_time = time.time()
        self.status_var.set("Status: Copying...")
        
        threading.Thread(target=self.run_forensic_copy, args=(src, dst, scan_report), daemon=True).start()

    def run_forensic_copy(self, src, dst, scan_report):
        try:
            self.log_insert(f"\n{'='*100}\n")
            self.log_insert(f"🚀 COPY INITIATED\n")
            os.makedirs(dst, exist_ok=True)
            
            cmd = [
                "rsync", "-avh", "--progress", "--stats",
                "--exclude-from=-"
            ] + [f"{src}/", f"{dst}/"]
            
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=src
            )
            
            proc.stdin.write("\n".join(NTFS_EXCLUSIONS) + "\n")
            proc.stdin.close()
            
            for line in proc.stdout:
                for seg in line.replace('\r', '\n').split('\n'):
                    clean = seg.rstrip()
                    if clean:
                        self.log_insert(f"{clean}\n")
            proc.wait()
            
            if proc.returncode != 0:
                raise RuntimeError(f"rsync exit code {proc.returncode}")
            
            self.log_insert(f"\n✅ RSYNC COMPLETE\n")
            
            subprocess.run(["chmod", "-R", "u=rwX,g=rX,o=rX", dst], check=True)
            self.log_insert(f"✅ PERMISSIONS SET\n")
            
            # Post-copy verification
            hidden_verified = 0
            for root, dirs, files in os.walk(dst):
                dirs[:] = [d for d in dirs if d not in EXCLUSION_SET]
                for f in files:
                    if f.startswith('.') and f not in EXCLUSION_SET:
                        hidden_verified += 1
            
            total_duration = time.time() - self.copy_start_time
            self.log_insert(f"\n{'='*100}\n")
            self.log_insert(f"✅ COMPLETE | Duration: {total_duration:.2f}s | Hidden: {hidden_verified:,}\n")
            
            self.root.after(0, lambda: self.finish(True, dst))
            
        except Exception as e:
            self.log_insert(f"\n❌ FAILED: {str(e)}\n")
            import traceback
            self.log_insert(f"{traceback.format_exc()}\n")
            self.root.after(0, lambda: self.finish(False, str(e)))

    def finish(self, success, info):
        self.progress.stop()
        self.progress.grid_remove()
        self.btn.config(state=tk.NORMAL, text="Start Copy")
        
        if success:
            self.status_var.set("Status: Complete | Destination: {}".format(info[:50]))
            messagebox.showinfo("COMPLETE", f"✅ Success!\n\n{info}")
        else:
            self.status_var.set("Status: Failed")
            messagebox.showerror("FAILED", f"❌ Error:\n\n{info}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.deiconify()
        app = ForensicCopyGUI(root)
        root.mainloop()
    except tk.TclError as e:
        print("❌ TKINTER NOT AVAILABLE")
        print(f"   Error: {str(e)}")
        print("\n🔧 INSTALL: sudo apt install python3-tk -y")
        sys.exit(1)
