import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.stapler import XPIIStapler
from core.agent import LocalAssistantAgent
import os
from datetime import datetime


class XPIIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("XPII CHAIN | Deterministic Provenance Stapler")
        self.geometry("960x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.stapler = XPIIStapler()
        self.agent = LocalAssistantAgent()
        self.selected_file = None

        # Root layout: sidebar + tabview
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="XPII CHAIN",
            font=ctk.CTkFont(size=24, weight="bold", family="Courier"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(
            self.sidebar, text="SYSTEM: READY",
            text_color="#00FF41", font=ctk.CTkFont(family="Courier"),
        )
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

        self.info_box = ctk.CTkTextbox(
            self.sidebar, width=180, height=220,
            font=ctk.CTkFont(size=10, family="Courier"),
        )
        self.info_box.grid(row=2, column=0, padx=10, pady=20)
        self.info_box.insert(
            "0.0",
            "STAPLER PARADIGM:\n\n"
            "1. UNPACK\n"
            "2. EDIT (XML DOM)\n"
            "3. PACK (AUTO-REPAIR)\n\n"
            "L0 INVARIANT CONTRACT\nENFORCED.\n\n"
            "──────────────────\n\n"
            "AGENT: LOCAL\nMODE: OFFLINE\nMODEL: RULE-BASED",
        )
        self.info_box.configure(state="disabled")

        # ── Tab view ─────────────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Document")
        self.tabview.add("Assistant")

        self._build_document_tab(self.tabview.tab("Document"))
        self._build_agent_tab(self.tabview.tab("Assistant"))

    # ── Document tab ─────────────────────────────────────────────────────────

    def _build_document_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            parent, text="PROVENANCE STAPLER",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=20)

        # File selection
        file_frame = ctk.CTkFrame(parent)
        file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkButton(
            file_frame, text="SELECT DOCUMENT (.DOCX)", command=self.select_file,
        ).grid(row=0, column=0, padx=10, pady=10)

        self.file_name_label = ctk.CTkLabel(
            file_frame, text="No file selected", text_color="#FF0038",
        )
        self.file_name_label.grid(row=0, column=1, padx=10, pady=10)

        # Metadata configuration
        meta_frame = ctk.CTkFrame(parent)
        meta_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        meta_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_frame, text="AUTHOR:").grid(row=0, column=0, padx=10, pady=5)
        self.author_entry = ctk.CTkEntry(meta_frame, placeholder_text="e.g., Axiom Hive")
        self.author_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.author_entry.insert(0, "XPII-CHAIN-PROVENANCE")

        ctk.CTkLabel(meta_frame, text="SESSION ID:").grid(row=1, column=0, padx=10, pady=5)
        self.session_entry = ctk.CTkEntry(meta_frame, placeholder_text="Auto-generated if empty")
        self.session_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Execute button
        self.staple_btn = ctk.CTkButton(
            parent, text="EXECUTE STAPLE", command=self.run_stapler,
            height=50, font=ctk.CTkFont(size=16, weight="bold"), state="disabled",
        )
        self.staple_btn.grid(row=3, column=0, padx=20, pady=30, sticky="ew")

        # Log output
        self.log_output = ctk.CTkTextbox(
            parent, height=180, font=ctk.CTkFont(size=11, family="Courier"),
        )
        self.log_output.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        parent.grid_rowconfigure(4, weight=1)
        self.log(f"XPII CHAIN INITIALIZED AT {datetime.now().strftime('%H:%M:%S')}")

    # ── Agent / Assistant tab ─────────────────────────────────────────────────

    def _build_agent_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            parent, text="LOCAL ASSISTANT AGENT",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 5))

        ctk.CTkLabel(
            parent,
            text="Offline · Rule-based · No network required",
            text_color="#888888",
            font=ctk.CTkFont(size=11, family="Courier"),
        ).grid(row=1, column=0, padx=20, pady=(0, 10))

        # Chat history display
        self.chat_output = ctk.CTkTextbox(
            parent, font=ctk.CTkFont(size=12, family="Courier"), wrap="word",
        )
        self.chat_output.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        parent.grid_rowconfigure(2, weight=1)

        self._agent_append(
            "AGENT",
            "Welcome to the XPII CHAIN Local Assistant.\n"
            "Type 'help' for a list of topics I can assist with.",
        )

        # Input area
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.agent_input = ctk.CTkEntry(
            input_frame, placeholder_text="Ask a question...",
            font=ctk.CTkFont(size=12),
        )
        self.agent_input.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.agent_input.bind("<Return>", lambda _e: self.send_agent_message())

        ctk.CTkButton(
            input_frame, text="SEND", width=80, command=self.send_agent_message,
        ).grid(row=0, column=1, pady=0)

        ctk.CTkButton(
            parent, text="CLEAR HISTORY", width=140,
            fg_color="transparent", border_width=1,
            command=self.clear_agent_history,
        ).grid(row=4, column=0, padx=20, pady=(0, 15))

    # ── Event handlers ────────────────────────────────────────────────────────

    def log(self, message: str) -> None:
        self.log_output.insert("end", f"> {message}\n")
        self.log_output.see("end")

    def select_file(self) -> None:
        self.selected_file = filedialog.askopenfilename(
            filetypes=[("Word Documents", "*.docx")]
        )
        if self.selected_file:
            self.file_name_label.configure(
                text=os.path.basename(self.selected_file), text_color="#00FF41"
            )
            self.staple_btn.configure(state="normal")
            self.log(f"FILE SELECTED: {os.path.basename(self.selected_file)}")
            self.status_label.configure(text="SYSTEM: FILE LOADED", text_color="#00FF41")

    def run_stapler(self) -> None:
        try:
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                initialfile="stapled_" + os.path.basename(self.selected_file),
            )
            if not output_path:
                return

            self.status_label.configure(text="SYSTEM: RUNNING...", text_color="#FFAA00")
            self.update_idletasks()

            self.log("PHASE 1: UNPACKING ARCHIVE...")
            self.stapler.unpack(self.selected_file)

            author = self.author_entry.get()
            session = self.session_entry.get() or None

            self.log("PHASE 2: INJECTING DETERMINISTIC METADATA...")
            self.stapler.inject_metadata(author=author, session_id=session)

            self.log("PHASE 3: REPACKING AND AUTO-REPAIR...")
            self.stapler.pack(output_path)

            self.log(f"SUCCESS: {os.path.basename(output_path)} GENERATED.")
            self.status_label.configure(text="SYSTEM: READY", text_color="#00FF41")
            messagebox.showinfo("XPII CHAIN", "Deterministic Provenance Stapled Successfully.")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.status_label.configure(text="SYSTEM: ERROR", text_color="#FF0038")
            messagebox.showerror("XPII CHAIN ERROR", f"Process Failed: {str(e)}")

    def send_agent_message(self) -> None:
        user_text = self.agent_input.get().strip()
        if not user_text:
            return
        self.agent_input.delete(0, "end")
        self._agent_append("YOU", user_text)
        response = self.agent.respond(user_text)
        # Strip the "[HH:MM:SS] AGENT > " prefix already in the response
        self.chat_output.insert("end", f"\n{response}\n")
        self.chat_output.see("end")

    def clear_agent_history(self) -> None:
        self.agent.clear_history()
        self.chat_output.configure(state="normal")
        self.chat_output.delete("1.0", "end")
        self._agent_append(
            "AGENT",
            "History cleared. Type 'help' to see available topics.",
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _agent_append(self, speaker: str, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.chat_output.insert("end", f"\n[{ts}] {speaker} > {text}\n")
        self.chat_output.see("end")


if __name__ == "__main__":
    app = XPIIApp()
    app.mainloop()
