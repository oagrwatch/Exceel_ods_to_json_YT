import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(page_title="Excel/ODS σε JSON", layout="wide")

st.title("Μετατροπή Excel/ODS σε JSON")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)

# -----------------------------
# Helper: ασφαλής ανάγνωση τιμών
# -----------------------------
def safe_value(v):
    """Μετατρέπει NaN σε 'null', αφήνει αριθμούς ως αριθμούς και όλα τα άλλα ως string."""
    if pd.isna(v):
        return "null"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    return str(v)

# -----------------------------
# Helper: δημιουργεί merge field
# -----------------------------
def create_merge(title, description):
    t = "" if title == "null" else title
    d = "" if description == "null" else description
    return f"{t} || Description: {d}"

# -----------------------------
# MAIN
# -----------------------------
if uploaded_file is not None:
    try:
        progress = st.progress(0, text="⏳ Επεξεργασία αρχείου...")

        time.sleep(0.4)
        progress.progress(20, text="📖 Διαβάζω το αρχείο...")

        # Διαβάζουμε με το σωστό engine
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        time.sleep(0.4)
        progress.progress(40, text="🔍 Επεξεργασία στηλών...")

        # Aσφαλής ανάγνωση τιμών για κάθε κελί
        df = df.applymap(lambda x: safe_value(x))

        # Προσθήκη merge και Title (ίδιο με merge)
        title_col = "TitleTest"
        desc_col = "Description"

        if title_col not in df.columns:
            df[title_col] = "null"
        if desc_col not in df.columns:
            df[desc_col] = "null"

        df["merge"] = df.apply(lambda r: create_merge(r[title_col], r[desc_col]), axis=1)
        df["Title"] = df["merge"]

        time.sleep(0.4)
        progress.progress(60, text="📊 Προεπισκόπηση...")

        st.subheader("📊 Προεπισκόπηση δεδομένων")
        st.dataframe(df)

        time.sleep(0.4)
        progress.progress(85, text="📝 Δημιουργία JSON...")

        # Μετατροπή dataframe σε records list
        records = []
        for _, row in df.iterrows():
            rec = {}
            for col in df.columns:
                v = row[col]

                # numeric → numeric
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    rec[col] = v
                else:
                    rec[col] = str(v)

            records.append(rec)

        json_data = json.dumps(records, ensure_ascii=False, indent=2)

        progress.progress(100, text="✅ Έτοιμο!")

        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_data,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"⚠️ Σφάλμα: {e}")

