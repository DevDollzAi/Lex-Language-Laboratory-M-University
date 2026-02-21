import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.stapler import XPIIStapler
import os
from datetime import datetime

# Status color palette (matches UIX_GUIDE §1.1)
COLOR_READY = "#00FF41"    # Terminal Green — system ready / verified
COLOR_ERROR = "#FF0038"    # Miami Red — error / unselected
COLOR_WORKING = "#FFAA00"  # Amber — operation in progress

class XPIIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("XPII CHAIN | Deterministic Provenance Stapler")
        self.geometry("800x680")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.stapler = XPIIStapler()
        self.selected_file = None

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="XPII CHAIN", font=ctk.CTkFont(size=24, weight="bold", family="Courier"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="SYSTEM: READY", text_color=COLOR_READY, font=ctk.CTkFont(family="Courier"))
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

        self.info_box = ctk.CTkTextbox(self.sidebar, width=180, height=200, font=ctk.CTkFont(size=10, family="Courier"))
        self.info_box.grid(row=2, column=0, padx=10, pady=20)
        self.info_box.insert("0.0", "STAPLER PARADIGM:\n\n1. UNPACK\n2. EDIT (XML DOM)\n3. PACK (AUTO-REPAIR)\n\nL0 INVARIANT CONTRACT ENFORCED.")
        self.info_box.configure(state="disabled")

        # Main Content
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text="PROVENANCE STAPLER", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=20)

        # File Selection
        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.select_btn = ctk.CTkButton(self.file_frame, text="SELECT DOCUMENT (.DOCX)", command=self.select_file)
        self.select_btn.grid(row=0, column=0, padx=10, pady=10)
        
        self.file_name_label = ctk.CTkLabel(self.file_frame, text="No file selected", text_color=COLOR_ERROR)
        self.file_name_label.grid(row=0, column=1, padx=10, pady=10)

        # Metadata Configuration
        self.meta_frame = ctk.CTkFrame(self.main_frame)
        self.meta_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.meta_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.meta_frame, text="AUTHOR:").grid(row=0, column=0, padx=10, pady=5)
        self.author_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="e.g., Axiom Hive")
        self.author_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.author_entry.insert(0, "XPII-CHAIN-PROVENANCE")

        ctk.CTkLabel(self.meta_frame, text="SESSION ID:").grid(row=1, column=0, padx=10, pady=5)
        self.session_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="Auto-generated if empty")
        self.session_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Hash Display
        self.hash_frame = ctk.CTkFrame(self.main_frame)
        self.hash_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.hash_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.hash_frame, text="SHA-256:", font=ctk.CTkFont(family="Courier")).grid(row=0, column=0, padx=10, pady=5)
        self.hash_label = ctk.CTkLabel(self.hash_frame, text="—", text_color=COLOR_READY,
                                       font=ctk.CTkFont(size=10, family="Courier"), wraplength=380, justify="left")
        self.hash_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.staple_btn = ctk.CTkButton(self.btn_frame, text="EXECUTE STAPLE", command=self.run_stapler,
                                        height=50, font=ctk.CTkFont(size=16, weight="bold"), state="disabled")
        self.staple_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.verify_btn = ctk.CTkButton(self.btn_frame, text="VERIFY DOCUMENT", command=self.run_verify,
                                        height=50, font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color="#1a6b3c", hover_color="#145530")
        self.verify_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Log Output
        self.log_output = ctk.CTkTextbox(self.main_frame, height=150, font=ctk.CTkFont(size=11, family="Courier"))
        self.log_output.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.log(f"XPII CHAIN INITIALIZED AT {datetime.now().strftime('%H:%M:%S')}")

    def log(self, message):
        self.log_output.insert("end", f"> {message}\n")
        self.log_output.see("end")

    def select_file(self):
        self.selected_file = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if self.selected_file:
            self.file_name_label.configure(text=os.path.basename(self.selected_file), text_color=COLOR_READY)
            self.staple_btn.configure(state="normal")
            self.log(f"FILE SELECTED: {os.path.basename(self.selected_file)}")

    def run_stapler(self):
        try:
            output_path = filedialog.asksaveasfilename(defaultextension=".docx",
                                                       initialfile="stapled_" + os.path.basename(self.selected_file))
            if not output_path:
                return

            self.status_label.configure(text="SYSTEM: WORKING", text_color=COLOR_WORKING)
            self.update()

            self.log("PHASE 1: UNPACKING ARCHIVE...")
            source_hash = self.stapler.unpack(self.selected_file)

            author = self.author_entry.get()
            session = self.session_entry.get() or None

            self.log("PHASE 2: INJECTING DETERMINISTIC METADATA...")
            self.stapler.inject_metadata(author=author, session_id=session)

            self.log("PHASE 3: REPACKING AND AUTO-REPAIR...")
            self.stapler.pack(output_path)

            self.hash_label.configure(text=source_hash)
            self.log(f"SHA-256 FINGERPRINT: {source_hash}")
            self.log(f"SUCCESS: {os.path.basename(output_path)} GENERATED.")
            self.status_label.configure(text="SYSTEM: READY", text_color=COLOR_READY)
            messagebox.showinfo("XPII CHAIN", "Deterministic Provenance Stapled Successfully.")
        except Exception as e:
            self.status_label.configure(text="SYSTEM: ERROR", text_color=COLOR_ERROR)
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("XPII CHAIN ERROR", f"Process Failed: {str(e)}")

    def run_verify(self):
        path = filedialog.askopenfilename(
            title="Select Stapled Document to Verify",
            filetypes=[("Word Documents", "*.docx")]
        )
        if not path:
            return
        try:
            result = self.stapler.verify(path)
            self.log(f"VERIFY: {os.path.basename(path)}")
            self.log(f"  AUTHOR   : {result.get('author', 'N/A')}")
            self.log(f"  SESSION  : {result.get('XPII-CHAIN-PROVENANCE', 'N/A')}")
            self.log(f"  SHA-256  : {result.get('XPII-CHAIN-SHA256', 'N/A')}")
            self.log(f"  MODIFIED : {result.get('modified', 'N/A')}")
            messagebox.showinfo("XPII CHAIN | VERIFY",
                                f"Provenance verified.\n\n"
                                f"Author:   {result.get('author', 'N/A')}\n"
                                f"Session:  {result.get('XPII-CHAIN-PROVENANCE', 'N/A')}\n"
                                f"SHA-256:  {result.get('XPII-CHAIN-SHA256', 'N/A')}")
        except ValueError as e:
            self.log(f"VERIFY FAILED: {str(e)}")
            messagebox.showerror("XPII CHAIN | VERIFY", f"Verification Failed:\n{str(e)}")

if __name__ == "__main__":
    app = XPIIApp()
    app.mainloop()
