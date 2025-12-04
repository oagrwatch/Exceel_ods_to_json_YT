# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import re

st.set_page_config(
    page_title="Excel → JSON for YT",
    page_icon="🇬🇷",
    layout="centered"
)

st.title("Μετατροπή Excel/ODS → JSON YT")
st.markdown("excel YT")

uploaded_file = st.file_uploader(
    "Ανέβασε το αρχείο Excel ή ODS",
    type=["xlsx", "ods"],
    help="Υποστηρίζονται .xlsx και .ods"
)

def safe_str(value):
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()

def escape_slashes(text):
    """Προσθέτει \/ escapes όπως στο δείγμα"""
    if not text:
        return ""
    return re.sub(r'/', r'\/', text)

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
        return time_val.strip()[:8]
    return ""

def format_timestamp(date_val, time_val):
    d = format_date(date_val)
    t = format_time(time_val)
    if d and t:
        return f"{d} {t}"
    return d

def escape_url(url):
    """Escapes για Video url όπως https:\/\/..."""
    if not url:
        return ""
    return re.sub(r'://', r:\/\/', re.sub(r'/', r\/', url))

if uploaded_file is not None:
    with st.spinner("Διαβάζω το αρχείο..."):
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

    progress_bar = st.progress(0)
    status = st.empty()

    status.text("Δημιουργώ τις στήλες και υπολογίζω...")
    progress_bar.progress(30)

    # Όλες οι στήλες πάντα παρόντες
    cols = ["TitleTest", "Description", "Views", "Likes", "Comments",
            "Duration in seconds", "Uploaded_time_UTC", "Uploaded T",
            "Time", "Μήνας", "Έτος", "Video url", "Channel"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    records = []
    total = len(df)
    for idx, row in df.iterrows():
        title_test = safe_str(row["TitleTest"])
        description = safe_str(row["Description"])

        views = int(row["Views"]) if pd.notna(row["Views"]) and str(row["Views"]).replace('.','').isdigit() else 0
        likes = int(row["Likes"]) if pd.notna(row["Likes"]) and str(row["Likes"]).isdigit() else 0
        comments = int(row["Comments"]) if pd.notna(row["Comments"]) and str(row["Comments"]).isdigit() else 0
        duration_sec = int(row["Duration in seconds"]) if pd.notna(row["Duration in seconds"]) else 0
        duration_min = round(duration_sec / 60, 12)  # Ακριβές rounding όπως δείγμα
        duration_hours = round(duration_sec / 3600, 12)

        uploaded_t = format_date(row.get("Uploaded T") or row.get("Uploaded_time_UTC"))
        time_str = format_time(row.get("Time"))
        timestamp_str = format_timestamp(row.get("Uploaded T") or row.get("Uploaded_time_UTC"), row.get("Time"))

        # Escapes για Uploaded_time_ext
        uploaded_t_escaped = escape_slashes(uploaded_t)
        uploaded_time_ext = f"{uploaded_t_escaped} {time_str}" if uploaded_t and time_str else ""

        month = safe_str(row["Μήνας"]).zfill(2) if safe_str(row["Μήνας"]).isdigit() else safe_str(row["Μήνας"])
        year = safe_str(row["Έτος"])
        month_year = f"{month}/{year}" if month and year else ""

        desc_part = f" || Description: {description}" if description else " || Description:"
        merge_field = f"{title_test}{desc_part}"
        title_field = merge_field

        records.append({
            "TitleTest": title_test,
            "Description": description,
            "merge": merge_field,
            "Title": title_field,
            "Views": views,  # int
            "Likes": likes,  # int
            "Comments": comments,  # int
            "Duration in seconds": duration_sec,  # int
            "Duration minutes": duration_min,  # float με 12 decimals
            "Duration Hours": duration_hours,  # float με 12 decimals
            "Uploaded_time_ext": uploaded_time_ext,
            "Uploaded T": uploaded_t,
            "Μήνας": month,
            "Έτος": year,
            "Μήνας/Έτος": month_year,
            "Time": time_str,
            "timestamp": timestamp_str,
            "Video url": escape_url(safe_str(row["Video url"])),  # Με escapes
            "Channel": safe_str(row["Channel"])
        })

        progress_bar.progress(30 + int(50 * (idx+1)/total))

    status.text("Δημιουργώ το JSON με ακριβή format...")
    
    # JSON με compact separators και indent=1 (πιο κοντά στο δείγμα)
    json_output = json.dumps(records, ensure_ascii=False, indent=1, separators=(',', ': '))

    progress_bar.progress(100)
    status.success("Έτοιμο 100%! Τώρα με escapes & ακριβή decimals.")

    st.download_button(
        label="Κατέβασε το JSON (Τώρα τέλειο format)",
        data=json_output,
        file_name=uploaded_file.name.split('.')[0] + ".json",
        mime="application/json"
    )

    with st.expander("Προεπισκόπηση JSON"):
        st.code(json_output[:2000] + ("..." if len(json_output)>2000 else ""), language="json")

st.markdown("---")
st.caption("2026")
