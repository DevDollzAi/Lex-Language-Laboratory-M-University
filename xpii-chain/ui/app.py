import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.stapler import XPIIStapler
import os
from datetime import datetime

class XPIIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("XPII CHAIN | Deterministic Provenance Stapler")
        self.geometry("800x600")
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
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="SYSTEM: READY", text_color="#00FF41", font=ctk.CTkFont(family="Courier"))
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
        
        self.file_name_label = ctk.CTkLabel(self.file_frame, text="No file selected", text_color="#FF0038")
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

        # Action Button
        self.staple_btn = ctk.CTkButton(self.main_frame, text="EXECUTE STAPLE", command=self.run_stapler, 
                                       height=50, font=ctk.CTkFont(size=16, weight="bold"), state="disabled")
        self.staple_btn.grid(row=3, column=0, padx=20, pady=40, sticky="ew")

        # Log Output
        self.log_output = ctk.CTkTextbox(self.main_frame, height=150, font=ctk.CTkFont(size=11, family="Courier"))
        self.log_output.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.log(f"XPII CHAIN INITIALIZED AT {datetime.now().strftime('%H:%M:%S')}")

    def log(self, message):
        self.log_output.insert("end", f"> {message}\n")
        self.log_output.see("end")

    def select_file(self):
        self.selected_file = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if self.selected_file:
            self.file_name_label.configure(text=os.path.basename(self.selected_file), text_color="#00FF41")
            self.staple_btn.configure(state="normal")
            self.log(f"FILE SELECTED: {os.path.basename(self.selected_file)}")

    def run_stapler(self):
        try:
            output_path = filedialog.asksaveasfilename(defaultextension=".docx", 
                                                       initialfile="stapled_" + os.path.basename(self.selected_file))
            if not output_path:
                return

            self.log("PHASE 1: UNPACKING ARCHIVE...")
            self.stapler.unpack(self.selected_file)
            
            author = self.author_entry.get()
            session = self.session_entry.get() or None
            
            self.log("PHASE 2: INJECTING DETERMINISTIC METADATA...")
            self.stapler.inject_metadata(author=author, session_id=session)
            
            self.log("PHASE 3: REPACKING AND AUTO-REPAIR...")
            self.stapler.pack(output_path)
            
            self.log(f"SUCCESS: {os.path.basename(output_path)} GENERATED.")
            messagebox.showinfo("XPII CHAIN", "Deterministic Provenance Stapled Successfully.")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("XPII CHAIN ERROR", f"Process Failed: {str(e)}")

if __name__ == "__main__":
    app = XPIIApp()
    app.mainloop()
