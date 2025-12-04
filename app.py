import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(page_title="Excel/ODS σε JSON YT", layout="wide")

st.title("Μετατροπή Excel/ODS σε JSON YT")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)

if uploaded_file is not None:
    try:
        progress_text = "⏳ Γίνεται επεξεργασία του αρχείου..."
        my_bar = st.progress(0, text=progress_text)

        time.sleep(0.4)
        my_bar.progress(20, text="📖 Διαβάζω το αρχείο...")

        if uploaded_file.name.lower().endswith(".xlsx") or uploaded_file.name.lower().endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        time.sleep(0.3)
        my_bar.progress(45, text="📊 Δημιουργία προεπισκόπησης...")

        st.subheader("📊 Προεπισκόπηση δεδομένων")
        st.dataframe(df)

        time.sleep(0.3)
        my_bar.progress(75, text="📝 Μετατροπή σε JSON...")

        records = []
        for _, row in df.iterrows():
            rec = {}

            # TitleTest
            if "TitleTest" in df.columns:
                v = row["TitleTest"]
                rec["TitleTest"] = str(v) if not pd.isna(v) and v != "" else "null"
            
            # Description - μόνο αν υπάρχει τιμή
            if "Description" in df.columns:
                v = row["Description"]
                if not pd.isna(v) and v != "":
                    rec["Description"] = str(v)

            # merge
            title_val = rec.get("TitleTest", "")
            if title_val == "null":
                title_val = ""
            desc_val = rec.get("Description", "")
            rec["merge"] = f"{title_val} || Description: {desc_val}"
            
            # Title (ίδιο με merge)
            rec["Title"] = rec["merge"]

            # Numeric fields
            for col in ["Views", "Likes", "Comments", "Duration in seconds", "Duration minutes", "Duration Hours"]:
                if col in df.columns:
                    v = row[col]
                    if pd.isna(v):
                        rec[col] = "null"
                    else:
                        if isinstance(v, (int, float)):
                            if float(v).is_integer():
                                rec[col] = int(v)
                            else:
                                rec[col] = float(v)
                        else:
                            rec[col] = "null"

            # String fields
            for col in ["Uploaded_time_ext", "Uploaded T", "Time", "timestamp", "Video url", "Channel"]:
                if col in df.columns:
                    v = row[col]
                    rec[col] = str(v) if not pd.isna(v) and v != "" else "null"

            # Μήνας, Έτος, Μήνας/Έτος
            if "Μήνας" in df.columns:
                v = row["Μήνας"]
                rec["Μήνας"] = str(v) if not pd.isna(v) and v != "" else "null"
            elif "Uploaded T" in df.columns and not pd.isna(row["Uploaded T"]) and row["Uploaded T"] != "":
                parts = str(row["Uploaded T"]).replace("\\/", "/").split("/")
                if len(parts) >= 3:
                    rec["Μήνας"] = parts[1]

            if "Έτος" in df.columns:
                v = row["Έτος"]
                rec["Έτος"] = str(v) if not pd.isna(v) and v != "" else "null"
            elif "Uploaded T" in df.columns and not pd.isna(row["Uploaded T"]) and row["Uploaded T"] != "":
                parts = str(row["Uploaded T"]).replace("\\/", "/").split("/")
                if len(parts) >= 3:
                    rec["Έτος"] = parts[2]

            if "Μήνας/Έτος" in df.columns:
                v = row["Μήνας/Έτος"]
                rec["Μήνας/Έτος"] = str(v) if not pd.isna(v) and v != "" else "null"
            elif "Μήνας" in rec and "Έτος" in rec and rec["Μήνας"] != "null" and rec["Έτος"] != "null":
                rec["Μήνας/Έτος"] = f"{rec['Μήνας']}\/{rec['Έτος']}"

            records.append(rec)

        # Δημιουργία JSON με escaped slashes
        json_text = "[\n"
        for i, rec in enumerate(records):
            json_text += " {\n"
            
            keys_order = ["TitleTest", "Description", "merge", "Title", "Views", "Likes", "Comments",
                         "Duration in seconds", "Duration minutes", "Duration Hours",
                         "Uploaded_time_ext", "Uploaded T", "Μήνας", "Έτος", "Μήνας/Έτος",
                         "Time", "timestamp", "Video url", "Channel"]
            
            items = []
            for key in keys_order:
                if key in rec:
                    value = rec[key]
                    if isinstance(value, str):
                        # Escape slashes and quotes
                        value_escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("/", "\\/")
                        items.append(f'  "{key}": "{value_escaped}"')
                    elif value == "null":
                        items.append(f'  "{key}": "null"')
                    else:
                        items.append(f'  "{key}": {value}')
            
            json_text += ",\n".join(items)
            json_text += "\n }"
            
            if i < len(records) - 1:
                json_text += ","
            json_text += "\n"
        
        json_text += "]"

        my_bar.progress(100, text="✅ Ολοκληρώθηκε!")

        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_text,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

        st.subheader("Preview (πρώτη εγγραφή)")
        if len(records) > 0:
            # Show first record
            first_rec_text = "{\n"
            items = []
            for key in ["TitleTest", "Description", "merge", "Title", "Views", "Likes", "Comments",
                       "Duration in seconds", "Duration minutes", "Duration Hours",
                       "Uploaded_time_ext", "Uploaded T", "Μήνας", "Έτος", "Μήνας/Έτος",
                       "Time", "timestamp", "Video url", "Channel"]:
                if key in records[0]:
                    value = records[0][key]
                    if isinstance(value, str):
                        value_escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("/", "\\/")
                        items.append(f'  "{key}": "{value_escaped}"')
                    elif value == "null":
                        items.append(f'  "{key}": "null"')
                    else:
                        items.append(f'  "{key}": {value}')
            first_rec_text += ",\n".join(items)
            first_rec_text += "\n}"
            st.code(first_rec_text, language="json")

    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")
