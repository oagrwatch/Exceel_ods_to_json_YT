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

# Οι στήλες που *πρέπει* να παραμείνουν αριθμητικές (αν υπάρχουν)
numeric_columns = [
    "Views", "Likes", "Comments",
    "Duration in seconds", "Duration minutes", "Duration Hours"
]

# Η σειρά των πεδίων στο output - θα συμπεριλάβουμε μόνο όσα υπάρχουν ή παράγουμε
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

        # Διαβάζουμε αρχείο με σωστό engine
        if uploaded_file.name.lower().endswith(".xlsx") or uploaded_file.name.lower().endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="odf")

        time.sleep(0.3)
        my_bar.progress(45, text="📊 Δημιουργία προεπισκόπησης...")

        # Αν υπάρχει ρητά η 'time' στήλη (μικρό γράμμα), εφαρμόζουμε την conversion που είχες
        if 'time' in df.columns:
            df['time'] = df['time'].apply(convert_time_to_iso8601)

        # Διασφαλίζουμε τους αριθμητικούς τύπους (αν υπάρχουν)
        for col in numeric_columns:
            if col in df.columns:
                # Προσπαθούμε να τη μετατρέψουμε σε αριθμό (float ή int). Διατηρούμε NaN αν δεν μπορεί.
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Προετοιμασία preview (δείχνουμε την πρώτη σελίδα όπως ήθελες)
        st.subheader("📊 Προεπισκόπηση δεδομένων")
        st.dataframe(df)

        time.sleep(0.3)
        my_bar.progress(75, text="📝 Μετατροπή σε JSON...")

        # Δημιουργία records: για κάθε row δημιουργούμε dict μόνο με τις επιθυμητές keys
        records = []
        for _, row in df.iterrows():
            rec = {}

            # TitleTest, Description πρώτα (αν υπάρχουν στο αρχείο)
            if "TitleTest" in df.columns:
                v = row["TitleTest"]
                rec["TitleTest"] = "null" if (pd.isna(v) or v == "") else str(v)
            # αν Description υπάρχει, το βάζουμε, αλλιώς το παραλείπουμε (όπως στο δείγμα σου)
            if "Description" in df.columns:
                v = row["Description"]
                rec["Description"] = "null" if (pd.isna(v) or v == "") else str(v)

            # Δημιουργία merge (χρησιμοποιούμε τιμή TitleTest αν υπάρχει αλλιώς κενό string,
            # και Description αν υπάρχει αλλιώς κενό string) — έτσι ταιριάζει με το δείγμα σου.
            title_for_merge = ""
            if "TitleTest" in df.columns:
                tv = row["TitleTest"]
                title_for_merge = "" if pd.isna(tv) else str(tv)
            desc_for_merge = ""
            if "Description" in df.columns:
                dv = row["Description"]
                desc_for_merge = "" if pd.isna(dv) else str(dv)
            rec["merge"] = f"{title_for_merge} || Description: {desc_for_merge}"
            rec["Title"] = rec["merge"]

            # Numeric fields: αν η στήλη υπάρχει και η τιμή είναι αριθμός -> αριθμός,
            # αν υπάρχει αλλά NaN -> "null" (string)
            for col in ["Views", "Likes", "Comments", "Duration in seconds", "Duration minutes", "Duration Hours"]:
                if col in df.columns:
                    v = row[col]
                    if pd.isna(v):
                        rec[col] = "null"
                    else:
                        # Αν είναι ακέραιος χωρίς υπολοιπο, κάνουμε int, αλλιώς float
                        if float(v).is_integer():
                            rec[col] = int(v)
                        else:
                            rec[col] = float(v)

            # Άλλες στήλες: Uploaded_time_ext, Uploaded T, Time, timestamp, Video url, Channel
            for col in ["Uploaded_time_ext", "Uploaded T", "Time", "timestamp", "Video url", "Channel"]:
                if col in df.columns:
                    v = row[col]
                    rec[col] = "null" if (pd.isna(v) or v == "") else str(v)

            # Μήνας, Έτος, Μήνας/Έτος: αν υπάρχουν ήδη στο αρχείο, χρησιμοποιούμε αυτές.
            # Αν δεν υπάρχουν αλλά υπάρχει "Uploaded T", προσπαθούμε να τις εξάγουμε από την τιμή.
            if "Μήνας" in df.columns:
                v = row["Μήνας"]
                rec["Μήνας"] = "null" if (pd.isna(v) or v == "") else str(v)
            else:
                # try derive from 'Uploaded T' if present
                if "Uploaded T" in df.columns:
                    ut = row["Uploaded T"]
                    if pd.isna(ut) or str(ut) == "":
                        # δεν ορίζουμε
                        pass
                    else:
                        s = str(ut)
                        # αναμένουμε μορφή dd/mm/YYYY ή dd\/mm\/YYYY
                        parts = s.replace("\\/", "/").split("/")
                        if len(parts) >= 3:
                            rec["Μήνας"] = parts[1]
                        else:
                            # fallback: leave out
                            pass

            if "Έτος" in df.columns:
                v = row["Έτος"]
                rec["Έτος"] = "null" if (pd.isna(v) or v == "") else str(v)
            else:
                if "Uploaded T" in df.columns:
                    ut = row["Uploaded T"]
                    if pd.isna(ut) or str(ut) == "":
                        pass
                    else:
                        s = str(ut)
                        parts = s.replace("\\/", "/").split("/")
                        if len(parts) >= 3:
                            rec["Έτος"] = parts[2]
                        else:
                            pass

            if "Μήνας/Έτος" in df.columns:
                v = row["Μήνας/Έτος"]
                rec["Μήνας/Έτος"] = "null" if (pd.isna(v) or v == "") else str(v)
            else:
                # αν προκύπτει από τα παραπάνω
                if ("Μήνας" in rec) and ("Έτος" in rec) and rec["Μήνας"] != "null" and rec["Έτος"] != "null":
                    rec["Μήνας/Έτος"] = f"{rec['Μήνας']}/{rec['Έτος']}"

            # Προσθέτουμε οποιεσδήποτε άλλες στήλες υπήρχαν στο αρχείο αλλά δεν είναι στη λίστα παραπάνω,
            # ώστε να μην χάνεται τίποτα. Τις προσθέτουμε μετά όμως (το δείγμα σου δεν περιλάμβανε τέτοιες).
            # Θα τις προσθέσουμε με μετατροπή σε string ή "null".
            for col in df.columns:
                if col in rec:
                    continue  # ήδη χειρισμένη
                if col in ["TitleTest","Description","Views","Likes","Comments",
                           "Duration in seconds","Duration minutes","Duration Hours",
                           "Uploaded_time_ext","Uploaded T","Μήνας","Έτος","Μήνας/Έτος",
                           "Time","timestamp","Video url","Channel"]:
                    continue
                # για οποιαδήποτε άλλη στήλη: αν υπάρχει τιμή -> string, αλλιώς "null"
                v = row[col]
                rec[col] = "null" if (pd.isna(v) or v == "") else str(v)

            # Τέλος, προσθέτουμε το rec στη λίστα
            records.append(rec)

        # Βασικό JSON dump (ensure_ascii=False για ελληνικά σωστά)
        json_text = json.dumps(records, ensure_ascii=False, indent=2)

        # Στο δείγμα σου τα slashes είναι escaped (\/). Κάνουμε global replace μόνο μέσα στο τελικό JSON text.
        # Αυτό θα μετατρέψει όλα τα / σε \/ μέσα στα string values (ακριβώς όπως στο δείγμα).
        json_text = json_text.replace("/", "\\/")

        my_bar.progress(100, text="✅ Ολοκληρώθηκε!")

        # Download button
        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_text,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

        st.subheader("Preview (πρώτη εγγραφή)")
        if len(records) > 0:
            # δείχνουμε το πρώτο record prettified
            st.code(json.dumps(records[0], ensure_ascii=False, indent=2).replace("/", "\\/"), language="json")
        else:
            st.write("No records produced.")

    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")
