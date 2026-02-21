import tkinter as tk
from tkinter import filedialog, messagebox
from core.stapler import XPIIStapler
import os

class XPIIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XPII CHAIN - Deterministic Provenance Stapler")
        self.root.geometry("500x400")
        self.root.configure(bg="#000000") # Axiom Black

        self.stapler = XPIIStapler()

        # UI Elements
        self.label = tk.Label(root, text="XPII CHAIN", font=("Courier", 24, "bold"), fg="#00FF41", bg="#000000")
        self.label.pack(pady=20)

        self.desc = tk.Label(root, text="Deterministic Provenance Embedding", font=("Courier", 10), fg="#FFFFFF", bg="#000000")
        self.desc.pack(pady=5)

        self.file_btn = tk.Button(root, text="Select .docx File", command=self.select_file, font=("Courier", 12), bg="#333333", fg="#FFFFFF")
        self.file_btn.pack(pady=20)

        self.selected_file = None
        self.file_label = tk.Label(root, text="No file selected", fg="#FF0038", bg="#000000", font=("Courier", 8))
        self.file_label.pack()

        self.staple_btn = tk.Button(root, text="STAPLE METADATA", command=self.run_stapler, font=("Courier", 14, "bold"), bg="#00FF41", fg="#000000", state=tk.DISABLED)
        self.staple_btn.pack(pady=30)

    def select_file(self):
        self.selected_file = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if self.selected_file:
            self.file_label.config(text=os.path.basename(self.selected_file), fg="#00FF41")
            self.staple_btn.config(state=tk.NORMAL)

    def run_stapler(self):
        try:
            output_path = filedialog.asksaveasfilename(defaultextension=".docx", initialfile="stapled_" + os.path.basename(self.selected_file))
            if not output_path:
                return

            self.stapler.unpack(self.selected_file)
            self.stapler.inject_metadata(author="XPII-CHAIN-USER")
            self.stapler.pack(output_path)

            messagebox.showinfo("Success", f"Metadata stapled successfully!\nSaved to: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = XPIIApp(root)
    root.mainloop()
