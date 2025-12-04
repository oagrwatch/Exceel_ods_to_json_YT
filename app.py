import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import json

class ExcelToJsonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel → JSON YT Converter")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.file_path = None

        tk.Label(root, text="Excel → JSON Converter YT",
                 font=("Arial", 18, "bold")).pack(pady=20)

        tk.Button(root, text="Load Excel File",
                  font=("Arial", 14),
                  width=22, command=self.load_excel).pack(pady=10)

        tk.Button(root, text="Export JSON",
                  font=("Arial", 14),
                  width=22, command=self.export_json).pack(pady=10)

        self.status = tk.Label(root, text="", font=("Arial", 12), fg="green")
        self.status.pack(pady=20)

    def load_excel(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if path:
            self.file_path = path
            self.status.config(text="Excel file loaded successfully.")

    def export_json(self):
        if not self.file_path:
            messagebox.showerror("Error", "Load Excel file first.")
            return

        try:
            df = pd.read_excel(self.file_path, dtype=str)

            numeric_fields = [
                "Views", "Likes",
                "Duration in seconds", "Duration minutes", "Duration Hours",
                "Comments"
            ]

            for col in numeric_fields:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

            text_fields = [
                "TitleTest", "Description", "Video url", "Channel",
                "Uploaded_time_ext", "Uploaded T", "Time",
                "timestamp"
            ]

            for col in text_fields:
                if col in df.columns:
                    df[col] = df[col].fillna("null").astype(str)

            def esc(x):
                if isinstance(x, str):
                    return x.replace("/", "\\/")
                return x

            for col in text_fields:
                if col in df.columns:
                    df[col] = df[col].apply(esc)

            df["Μήνας"] = df["Uploaded T"].str[3:5]
            df["Έτος"] = df["Uploaded T"].str[6:10]
            df["Μήνας/Έτος"] = df["Μήνας"] + "/" + df["Έτος"]

            df["merge"] = df["TitleTest"] + " || Description: " + df["Description"]
            df["Title"] = df["merge"]

            output_file = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")]
            )

            if not output_file:
                return

            json_data = json.loads(df.to_json(orient="records", force_ascii=False))

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            self.status.config(text="JSON exported successfully!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

root = tk.Tk()
app = ExcelToJsonApp(root)
root.mainloop()


