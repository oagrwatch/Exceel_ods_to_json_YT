import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

st.set_page_config(page_title="Excel/ODS σε JSON YT", layout="wide")

st.title("Μετατροπή Excel/ODS σε JSON YT")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)


# -------------------------------------------
#   ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# -------------------------------------------

def safe_str(v):
    """Μετατρέπει τιμές σε string εκτός από αριθμούς. Κενά → 'null'."""
    if pd.isna(v):
        return "null"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    return str(v)


def convert_timestamp(row):
    """Δημιουργεί timestamp όπως στο δείγμα."""
    try:
        date = row["Uploaded T"]
        time_value = row["Time"]
        if pd.isna(date) or pd.isna(time_value):
            return "null"
        dt = datetime.strptime(str(date) + " " + str(time_value), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "null"


def convert_uploaded_time_utc(row):
    """Υπολογισμός Uploaded_time_UTC (Υποθέτουμε -2 ώρες όπως στο δείγμα)."""
    try:
        date = row["Uploaded T"]
        time_value = row["Time"]
        if pd.isna(date) or pd.isna(time_value):
            return "null"

        dt = datetime.strptime(str(date) + " " + str(time_value), "%Y-%m-%d %H:%M:%S")
        dt_utc = dt - pd.Timedelta(hours=2)
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "null"


# -------------------------------------------
#   ΜΟΝΤΕΛΟ JSON ΟΠΩΣ ΤΟ ΖΗΤΗΣΕΣ
# -------------------------------------------
def create_final_json(df):

    # Εδώ κρατάμε ΟΛΕΣ τις στήλες όπως είναι στο excel σου
    df = df.fillna("null")

    # Υπολογισμοί όπως στο δείγμα
    if "Uploaded T" in df.columns and "Time" in df.columns:
        df["timestamp"] = df.apply(convert_timestamp, axis=1)
        df["Uploaded_time_UTC"] = df.apply(convert_uploaded_time_utc, axis=1)
    else:
        df["timestamp"] = "null"
        df["Uploaded_time_UTC"] = "null"

    # Το πεδίο merge όπως στο παράδειγμα
    if "TitleTest" in df.columns and "Description" in df.columns:
        df["merge"] = df["TitleTest"].astype(str) + " || Description: " + df["Description"].astype(str)

    # Το πεδίο Title όπως στο παράδειγμα (ίδιο με το merge)
    if "merge" in df.columns:
        df["Title"] = df["merge"]

    records = []

    for _, row in df.iterrows():
        fixed = {}
        for col in df.columns:
            v = row[col]

            # Αριθμοί μένουν αριθμοί
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                fixed[col] = v
            else:
                # Όλα τα strings -> string
                # Τα "null" μένουν "null"
                if v == "null":
                    fixed[col] = "null"
                else:
                    fixed[col] = str(v)

        records.append(fixed)

    return json.dumps(records, ensure_ascii=False, indent=2)


# -------------------------------------------
#  ΚΥΡΙΟ APP
# -------------------------------------------
if uploaded_file is not None:
    try:
        progress_text = "⏳ Γίνεται επεξεργασία..."
        my_bar = st.progress(0, text=progress_text)

        time.sleep(0.4)
        my_bar.progress(20, text="📖 Διαβάζω το αρχείο...")

        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        time.sleep(0.4)
        my_bar.progress(50, text="📊 Προεπισκόπηση...")

        st.subheader("📊 Προεπισκόπηση δεδομένων")
        st.dataframe(df)

        time.sleep(0.4)
        my_bar.progress(80, text="📝 Δημιουργία JSON...")

        json_output = create_final_json(df)

        my_bar.progress(100, text="✅ Ολοκληρώθηκε!")

        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_output,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"⚠️ Σφάλμα: {e}")
