import streamlit as st
import pandas as pd
import json
import time
import math

st.set_page_config(page_title="Excel/ODS σε JSON", layout="wide")

st.title("Μετατροπή Excel/ODS σε JSON")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)

def convert_time_to_iso8601(time_str):
    """Μετατρέπει ώρα από μορφή HH:mm:ss σε ISO 8601 duration (PTnHnMnS)."""
    if pd.isna(time_str) or time_str == "null" or time_str == "":
        return "PT0H0M0S"
    try:
        hours, minutes, seconds = map(int, str(time_str).split(":"))
        return f"PT{hours}H{minutes}M{seconds}S"
    except (ValueError, AttributeError):
        return "PT0H0M0S"

# Στήλες που πρέπει να παραμείνουν αριθμητικές
numeric_columns = [
    "Views", "Likes", "Comments",
    "Duration in seconds", "Duration minutes", "Duration Hours"
]

# Σειρά πεδίων στο output JSON
output_order = [
    "TitleTest",
    "Description",
    "merge",
    "Title",
    "Views",
    "Likes",
    "Comments",
    "Duration in seconds",
    "Duration minutes",
    "Duration Hours",
    "Uploaded_time_ext",
    "Uploaded T",
    "Μήνας",
    "Έτος",
    "Μήνας/Έτος",
    "Time",
    "timestamp",
    "Video url",
    "Channel"
]

def is_number_like(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not (isinstance(x, float) and math.isnan(x))

if uploaded_file is not None:
    try:
        # Progress bar
        progress_text = "⏳ Γίνεται επεξεργασία του αρχείου..."
        my_bar = st.progress(0, text=progress_text)

        time.sleep(0.4)
        my_bar.progress(20, text="📖 Διαβάζω το αρχείο...")

        # Διαβάζουμε το αρχείο με σωστό engine
        if uploaded_file.name.lower().endswith(".xlsx") or uploaded_file.name.lower().endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        time.sleep(0.3)
        my_bar.progress(45, text="📊 Δημιουργία προεπισκόπησης...")

        # Μετατροπή της στήλης 'time' σε ISO 8601 αν υπάρχει
        if 'time' in df.columns:
            df['time'] = df['time'].apply(convert_time_to_iso8601)

        # Διασφάλιση αριθμητικών τύπων
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        st.subheader("📊 Προεπισκόπηση δεδομένων")
        st.dataframe(df)

        time.sleep(0.3)
        my_bar.progress(75, text="📝 Μετατροπή σε JSON...")

        # Δημιουργία records σύμφωνα με το δείγμα
        records = []
        for _, row in df.iterrows():
            rec = {}

            # TitleTest και Description
            rec["TitleTest"] = str(row["TitleTest"]) if "TitleTest" in df.columns and not pd.isna(row["TitleTest"]) else "null"
            rec["Description"] = str(row["Description"]) if "Description" in df.columns and not pd.isna(row["Description"]) else "null"

            # Merge & Title
            title_for_merge = "" if "TitleTest" not in df.columns or pd.isna(row["TitleTest"]) else str(row["TitleTest"])
            desc_for_merge = "" if "Description" not in df.columns or pd.isna(row["Description"]) else str(row["Description"])
            rec["merge"] = f"{title_for_merge} || Description: {desc_for_merge}"
            rec["Title"] = rec["merge"]

            # Αριθμητικά πεδία
            for col in numeric_columns:
                if col in df.columns:
                    v = row[col]
                    if pd.isna(v):
                        rec[col] = "null"
                    else:
                        rec[col] = int(v) if float(v).is_integer() else float(v)

            # Άλλες στήλες
            for col in ["Uploaded_time_ext", "Uploaded T", "Time", "timestamp", "Video url", "Channel"]:
                if col in df.columns:
                    v = row[col]
                    rec[col] = "null" if pd.isna(v) or v=="" else str(v)

            # Μήνας, Έτος, Μήνας/Έτος
            if "Μήνας" in df.columns:
                rec["Μήνας"] = str(row["Μήνας"]) if not pd.isna(row["Μήνας"]) else "null"
            else:
                if "Uploaded T" in df.columns:
                    ut = str(row["Uploaded T"])
                    if ut and "/" in ut:
                        parts = ut.replace("\\/","/").split("/")
                        rec["Μήνας"] = parts[1] if len(parts)>=3 else "null"

            if "Έτος" in df.columns:
                rec["Έτος"] = str(row["Έτος"]) if not pd.isna(row["Έτος"]) else "null"
            else:
                if "Uploaded T" in df.columns:
                    ut = str(row["Uploaded T"])
                    if ut and "/" in ut:
                        parts = ut.replace("\\/","/").split("/")
                        rec["Έτος"] = parts[2] if len(parts)>=3 else "null"

            if "Μήνας/Έτος" in df.columns:
                rec["Μήνας/Έτος"] = str(row["Μήνας/Έτος"]) if not pd.isna(row["Μήνας/Έτος"]) else "null"
            else:
                if "Μήνας" in rec and "Έτος" in rec and rec["Μήνας"]!="null" and rec["Έτος"]!="null":
                    rec["Μήνας/Έτος"] = f"{rec['Μήνας']}/{rec['Έτος']}"

            # Όλες οι υπόλοιπες στήλες (δεν χάνονται)
            for col in df.columns:
                if col not in rec:
                    v = row[col]
                    rec[col] = "null" if pd.isna(v) or v=="" else str(v)

            # Προσθήκη στην λίστα
            records.append(rec)

        # JSON dump
        json_text = json.dumps(records, ensure_ascii=False, indent=2)
        # Escaping όπως στο δείγμα
        json_text = json_text.replace("/", "\\/")

        my_bar.progress(100, text="✅ Ολοκληρώθηκε!")

        # Download button
        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_text,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

        # Preview πρώτης εγγραφής
        st.subheader("Preview πρώτης εγγραφής")
        if records:
            st.code(json.dumps(records[0], ensure_ascii=False, indent=2).replace("/", "\\/"), language="json")
        else:
            st.write("Δεν παράχθηκαν εγγραφές.")

    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}"
