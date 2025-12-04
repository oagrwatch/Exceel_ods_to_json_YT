import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

st.set_page_config(page_title="Excel/ODS → JSON (YT Format)", layout="wide")

st.title("Μετατροπή Excel/ODS σε JSON")
st.markdown("### Ιδανικό για μετατροπή στατιστικών YT")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)

def safe_str(value):
    """Μετατρέπει οποιαδήποτε τιμή σε string, ποτέ None ή NaN"""
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()

def format_date(date_val):
    if pd.isna(date_val):
        return ""
    if isinstance(date_val, datetime):
        return date_val.strftime("%d/%m/%Y")
    try:
        dt = pd.to_datetime(date_val, errors='coerce')
        if pd.isna(dt):
            return ""
        return dt.strftime("%d/%m/%Y")
    except:
        return safe_str(date_val)

def format_time(time_val):
    if pd.isna(time_val):
        return ""
    if isinstance(time_val, datetime):
        return time_val.strftime("%H:%M:%S")
    if isinstance(time_val, str) and ":" in time_val:
        return time_val.strip()[:8]  # παίρνουμε μόνο HH:mm:ss
    return ""

def format_timestamp(date_val, time_val):
    d = format_date(date_val)
    t = format_time(time_val)
    if d and t:
        return f"{d} {t}"
    elif d:
        return d
    return ""

if uploaded_file is not None:
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Διαβάζω το αρχείο...")
        progress_bar.progress(20)

        # Διάβασμα ανάλογα με την κατάληξη
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        status_text.text("Επεξεργάζομαι τις στήλες...")
        progress_bar.progress(50)

        # Εξασφαλίζουμε ότι όλες οι απαραίτητες στήλες υπάρχουν (αλλιώς κενές)
        required_columns = [
            "TitleTest", "Description", "merge", "Title", "Views", "Likes", "Comments",
            "Duration in seconds", "Duration minutes", "Duration Hours",
            "Uploaded_time_UTC", "Uploaded T", "Μήνας", "Έτος", "Μήνας/Έτος",
            "Time", "timestamp", "Video url", "Channel"
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Καθαρίζουμε και τυποποιούμε τα δεδομένα
        records = []
        for _, row in df.iterrows():
            # Βασικά πεδία
            title_test = safe_str(row["TitleTest"])
            description = safe_str(row["Description"])
            views = int(row["Views"]) if pd.notna(row["Views"]) and str(row["Views"]).isdigit() else 0
            likes = int(row["Likes"]) if pd.notna(row["Likes"]) and str(row["Likes"]).isdigit() else 0
            comments = int(row["Comments"]) if pd.notna(row["Comments"]) and str(row["Comments"]).isdigit() else 0

            duration_sec = int(row["Duration in seconds"]) if pd.notna(row["Duration in seconds"]) else 0

            # Υπολογισμός λεπτών και ωρών (με ακρίβεια όπως στο παράδειγμά σου)
            duration_min = round(duration_sec / 60, 10)
            duration_hours = round(duration_sec / 3600, 10)

            # Ημερομηνίες & ώρες
            uploaded_t = format_date(row.get("Uploaded T") or row.get("Uploaded_time_UTC"))
            uploaded_time_ext = ""
            if uploaded_t:
                time_part = format_time(row.get("Time") or row.get("Uploaded_time_UTC"))
                uploaded_time_ext = f"{uploaded_t.replace('/', '\\/')} {time_part}" if time_part else ""

            time_str = format_time(row.get("Time"))
            timestamp_str = format_timestamp(row.get("Uploaded T") or row.get("Uploaded_time_UTC"), row.get("Time"))

            month = safe_str(row["Μήνας"])
            year = safe_str(row["Έτος"])
            month_year = f"{month}/{year}" if month and year else ""

            # Κατασκευή merge και Title (ακριβώς όπως στο παράδειγμά σου)
            desc_part = f" || Description: {description}" if description else " || Description:"
            merge_field = f"{title_test}{desc_part}"
            title_field = merge_field if title_test else desc_part[4:]  # αν δεν έχει TitleTest, μόνο description

            record = {
                "TitleTest": title_test,
                "Description": description,
                "merge": merge_field,
                "Title": title_field,
                "Views": views,
                "Likes": likes,
                "Comments": comments,
                "Duration in seconds": duration_sec,
                "Duration minutes": duration_min,
                "Duration Hours": duration_hours,
                "Uploaded_time_ext": uploaded_time_ext,
                "Uploaded T": uploaded_t,
                "Μήνας": month.zfill(2) if month.isdigit() else month,  # leading zero
                "Έτος": year,
                "Μήνας/Έτος": month_year,
                "Time": time_str,
                "timestamp": timestamp_str,
                "Video url": safe_str(row["Video url"]),
                "Channel": safe_str(row["Channel"])
            }
            records.append(record)

        status_text.text("Δημιουργώ το JSON...")
        progress_bar.progress(80)

        # Μετατροπή σε JSON με σωστό formatting
        json_output = json.dumps(records, ensure_ascii=False, indent=1)

        progress_bar.progress(100)
        status_text.text("✅ Έτοιμο!")

        # Προεπισκόπηση
        st.subheader("Προεπισκόπηση JSON")
        st.code(json_output[:2000] + ("\n..." if len(json_output) > 2000 else ""), language="json")

        # Download button
        filename = uploaded_file.name.rsplit(".", 1)[0]
        st.download_button(
            label="📥 Κατέβασε το JSON αρχείο",
            data=json_output,
            file_name=f"{filename}.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        st.exception(e)
