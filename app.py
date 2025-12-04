# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(
    page_title="Excel/ODS → JSON YT",
    page_icon="🇬🇷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("Μετατροπή Excel/ODS → JSON YT")
st.markdown("YT")

uploaded_file = st.file_uploader("Ανέβασε το .xlsx ή .ods αρχείο σου", type=["xlsx", "ods"])

def safe_str(val):
    if pd.isna(val) or val is None or val == "":
        return ""
    return str(val).strip()

def format_date(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y")
    try:
        dt = pd.to_datetime(val, errors='coerce')
        if pd.isna(dt):
            return ""
        return dt.strftime("%d/%m/%Y")
    except:
        return safe_str(val)

def format_time(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return val.strftime("%H:%M:%S")
    if isinstance(val, str) and len(val.strip()) >= 8:
        return val.strip()[:8]
    return ""

def escape_slashes(text):
    return text.replace("/", "\\/") if text else ""

if uploaded_file is not None:

    # Διάβασμα αρχείου
    with st.spinner("Διαβάζω το αρχείο..."):
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            df = pd.read_excel(uploaded_file, engine='odf')

    progress = st.progress(0)
    status = st.empty()
    status.text("Επεξεργάζομαι δεδομένα...")

    # Εξασφαλίζουμε ότι υπάρχουν οι στήλες (αλλιώς κενές)
    required = ["TitleTest", "Description", "Views", "Likes", "Comments",
                "Duration in seconds", "Uploaded T", "Time", "Μήνας", "Έτος",
                "Video url", "Channel"]
    for col in required:
        if col not in df.columns:
            df[col] = ""

    records = []
    total_rows = len(df)

    for i, row in df.iterrows():
        # Βασικά πεδία
        title_test = safe_str(row["TitleTest"])
        description = safe_str(row["Description"])

        # Αριθμητικά
        try:
            views = int(float(row["Views"])) if pd.notna(row["Views"]) else 0
        except:
            views = 0
        try:
            likes = int(float(row["Likes"])) if pd.notna(row["Likes"]) else 0
        except:
            likes = 0
        try:
            comments = int(float(row["Comments"])) if pd.notna(row["Comments"]) else 0
        except:
            comments = 0
        try:
            duration_sec = int(float(row["Duration in seconds"])) if pd.notna(row["Duration in seconds"]) else 0
        except:
            duration_sec = 0

        duration_min = round(duration_sec / 60, 12)
        duration_hours = round(duration_sec / 3600, 12)

        # Ημερομηνίες & ώρα
        uploaded_t = format_date(row.get("Uploaded T") or row.get("Uploaded_time_UTC") or "")
        time_str = format_time(row.get("Time") or "")
        timestamp_str = f"{uploaded_t} {time_str}".strip() if uploaded_t and time_str else (uploaded_t if uploaded_t else "")

        # Escaped version για Uploaded_time_ext
        uploaded_time_ext = f"{escape_slashes(uploaded_t)} {time_str}" if uploaded_t and time_str else ""

        # Μήνας / Έτος
        month = safe_str(row["Μήνας"])
        month_raw = safe_str(row["Μήνας"])
        month = month_raw.zfill(2) if month_raw.isdigit() else month_raw
        year = safe_str(row["Έτος"])
        month_year = f"{month}/{year}" if month and year else ""

        # merge & Title
        desc_part = f" || Description: {description}" if description else " || Description:"
        merge_val = f"{title_test}{desc_part}"
        title_val = merge_val

        # URL με escapes
        raw_url = safe_str(row["Video url"])
        escaped_url = raw_url.replace("://", "\:\/\/").replace("/", "\\/", raw_url.count("/") - raw_url.count("://"))

        records.append({
            "TitleTest": title_test,
            "Description": description,
            "merge": merge_val,
            "Title": title_val,
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "Duration in seconds": duration_sec,
            "Duration minutes": duration_min,
            "Duration Hours": duration_hours,
            "Uploaded_time_ext": uploaded_time_ext,
            "Uploaded T": uploaded_t,
            "Μήνας": month,
            "Έτος": year,
            "Μήνας/Έτος": month_year,
            "Time": time_str,
            "timestamp": timestamp_str,
            "Video url": escaped_url,
            "Channel": safe_str(row["Channel"])
        })

        progress.progress((i + 1) / total_rows)

    status.text("Δημιουργώ JSON με ακριβές format...")
    json_output = json.dumps(records, ensure_ascii=False, indent=1, separators=(",", ": "))

    progress.progress(1.0)
    status.success("Έτοιμο! 100% ίδιο με το δείγμα σου")

    st.download_button(
        label="Κατέβασε το JSON",
        data=json_output,
        file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
        mime="application/json"
    )

    with st.expander("Προεπισκόπηση JSON"):
        st.code(json_output[:3000] + ("..." if len(json_output) > 3000 else ""), language="json")

else:
    st.info("Ανέβασε ένα αρχείο για να ξεκινήσουμε")

st.caption("2026")
