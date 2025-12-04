import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(page_title="Excel/ODS σε JSON", layout="wide")
st.title("Μετατροπή Excel/ODS σε JSON — ΔΙΟΡΘΩΜΕΝΟ (δεν χάνει γραμμές)")

uploaded_file = st.file_uploader(
    "📂 Ανέβασε το αρχείο σου (.xlsx ή .ods)",
    type=["xlsx", "ods"]
)

def escape_slashes(s):
    if isinstance(s, str):
        return s.replace("/", "\\/")
    return s

def to_safe_string(v):
    # Επιστρέφει "null" (string) για κενά/NaN, αλλιώς string
    if pd.isna(v) or v == "":
        return "null"
    return str(v)

def format_date_only(v):
    # Επιστρέφει dd/mm/YYYY as string, ή κενό string αν δεν μπορεί
    if pd.isna(v) or v == "":
        return ""
    try:
        d = pd.to_datetime(v)
        return d.strftime("%d/%m/%Y")
    except:
        return str(v)

def format_datetime_ext(date_val, time_val):
    # Ενώνει Uploaded T (ημερομηνία) και Time (ώρα) σε "dd/mm/YYYY HH:MM:SS" ή επιστρέφει empty
    try:
        if (pd.isna(date_val) or date_val == "") and (pd.isna(time_val) or time_val == ""):
            return ""
        d = pd.to_datetime(date_val)
        t_str = str(time_val) if not pd.isna(time_val) else "00:00:00"
        # αν t_str ήδη έχει milliseconds ή περίεργα, πάρουμε μόνο HH:MM:SS
        t_parts = t_str.split(".")[0]
        return f"{d.strftime('%d/%m/%Y')} {t_parts}"
    except:
        # fallback: simple concat if parsing fails
        try:
            return f"{str(date_val)} {str(time_val)}".strip()
        except:
            return ""

# Στήλες που θέλουμε να είναι numeric αν υπάρχουν
numeric_columns = [
    "Views", "Likes", "Comments",
    "Duration in seconds", "Duration minutes", "Duration Hours"
]

if uploaded_file is not None:
    try:
        st.info("⏳ Διαβάζω το αρχείο...")

        # Διαβάζουμε ΟΛΑ τα φύλλα και τα ενώνουμε, ώστε να μην χάνουμε καμία γραμμή.
        if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
            all_sheets = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")
        else:
            all_sheets = pd.read_excel(uploaded_file, sheet_name=None, engine="odf")

        # all_sheets είναι dict {sheetname: df}; ενώνουμε όλα τα dfs με ignore_index=True
        df = pd.concat(all_sheets.values(), ignore_index=True, sort=False)

        st.success(f"Διαβάστηκαν {len(all_sheets)} φύλλα. Συνολικές γραμμές (πριν): {len(df)}")
        st.dataframe(df.head(10))

        # Προσδιορίζουμε αριθμητικές στήλες με ασφαλή conversion χωρίς drop
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")  # NaN αν δεν γίνεται convert

        # Επεξεργασία κάθε γραμμής για να παράξουμε εγγραφές με το ακριβές format
        records = []
        row_count = 0
        for _, row in df.iterrows():
            row_count += 1
            # TitleTest & Description (αν υπάρχουν)
            TitleTest_val = row.get("TitleTest", "")
            Description_val = row.get("Description", "")

            TitleTest_str = to_safe_string(TitleTest_val)
            Description_str = to_safe_string(Description_val)

            # merge και Title όπως ζητάς
            merge_val = f"{'' if TitleTest_str=='null' else TitleTest_str} || Description: {'' if Description_str=='null' else Description_str}"
            Title_val = merge_val

            rec = {}

            # Προσθέτουμε πεδία ακριβώς με το όνομα που θες, μόνο αν υπήρχαν ή τα παράγουμε εμείς.
            # TitleTest & Description: αν υπήρχαν στην είσοδο, τα βάζουμε (αλλιώς βάλουμε "null")
            rec["TitleTest"] = TitleTest_str if "TitleTest" in df.columns else "null"
            rec["Description"] = Description_str if "Description" in df.columns else "null"

            rec["merge"] = merge_val
            rec["Title"] = Title_val

            # Numeric fields: αν υπάρχει η στήλη, βάζουμε αριθμό ή "null"
            for col in numeric_columns:
                if col in df.columns:
                    v = row[col]
                    if pd.isna(v):
                        rec[col] = 0 if col in ["Views","Likes","Comments"] else "null"
                        # Στο παράδειγμα σου, Comments ήταν 0 όταν υπήρχε (default 0). Για safety βάζουμε 0 για Views/Likes/Comments όταν κενά.
                        # Για durations, αν κενό -> "null" string (σύμφωνα με sample)
                    else:
                        # αν είναι integer-like
                        if float(v).is_integer():
                            rec[col] = int(v)
                        else:
                            rec[col] = float(v)

            # Uploaded_time_ext, Uploaded T, Time, timestamp, Video url, Channel
            # - Uploaded T πρέπει να είναι date string dd/mm/YYYY
            uploaded_T_raw = row.get("Uploaded T", "")
            time_raw = row.get("Time", "")

            uploaded_T_str = format_date_only(uploaded_T_raw)
            uploaded_time_ext_str = format_datetime_ext(uploaded_T_raw, time_raw)
            timestamp_str = (format_date_only(uploaded_T_raw) + " " + str(time_raw)).strip()

            rec["Uploaded_time_ext"] = escape_slashes(to_safe_string(uploaded_time_ext_str)) if uploaded_time_ext_str != "" else "null"
            rec["Uploaded T"] = escape_slashes(to_safe_string(uploaded_T_str)) if uploaded_T_str != "" else "null"
            # Μήνας, Έτος, Μήνας/Έτος
            if uploaded_T_str:
                try:
                    parts = uploaded_T_str.replace("\\/", "/").split("/")
                    mon = parts[1] if len(parts) >= 3 else ""
                    yr = parts[2] if len(parts) >= 3 else ""
                except:
                    mon = ""
                    yr = ""
                rec["Μήνας"] = mon if mon != "" else "null"
                rec["Έτος"] = yr if yr != "" else "null"
                rec["Μήνας/Έτος"] = f"{mon}/{yr}" if (mon != "" and yr != "") else "null"
            else:
                # αν υπάρχουν στο αρχείο ως στήλες, χρησιμοποιούμε τις τιμές τους
                if "Μήνας" in df.columns:
                    v = row.get("Μήνας", "")
                    rec["Μήνας"] = to_safe_string(v)
                else:
                    rec["Μήνας"] = "null"
                if "Έτος" in df.columns:
                    v = row.get("Έτος", "")
                    rec["Έτος"] = to_safe_string(v)
                else:
                    rec["Έτος"] = "null"
                if "Μήνας/Έτος" in df.columns:
                    v = row.get("Μήνας/Έτος", "")
                    rec["Μήνας/Έτος"] = to_safe_string(v)
                else:
                    rec["Μήνας/Έτος"] = "null"

            rec["Time"] = to_safe_string(time_raw) if "Time" in df.columns else "null"
            rec["timestamp"] = escape_slashes(to_safe_string(timestamp_str)) if timestamp_str.strip() != "" else "null"
            rec["Video url"] = escape_slashes(to_safe_string(row.get("Video url", ""))) if "Video url" in df.columns else "null"
            rec["Channel"] = to_safe_string(row.get("Channel", "")) if "Channel" in df.columns else "null"

            # Προσθέτουμε οποιεσδήποτε άλλες στήλες που υπήρχαν (ώστε να μην χάνεται τίποτα),
            # αλλά τις τοποθετούμε *μετά* τα κύρια πεδία.
            for col in df.columns:
                if col in rec:
                    continue
                # παραλείπουμε αυτές που ήδη χειριστήκαμε
                if col in ["TitleTest","Description","merge","Title"] + numeric_columns + [
                    "Uploaded_time_ext","Uploaded T","Μήνας","Έτος","Μήνας/Έτος","Time","timestamp","Video url","Channel"
                ]:
                    continue
                v = row.get(col, "")
                rec[col] = to_safe_string(v)

            records.append(rec)

        st.success(f"Συνολικές γραμμές που επεξεργάστηκαν: {len(records)}")

        # Τελικό JSON: ensure_ascii=False για ελληνικά, indent=2
        json_text = json.dumps(records, ensure_ascii=False, indent=2)
        # escape slashes όπως στο δείγμα
        json_text = json_text.replace("/", "\\/")

        st.download_button(
            label="📥 Κατέβασε JSON",
            data=json_text,
            file_name=uploaded_file.name.rsplit(".", 1)[0] + ".json",
            mime="application/json"
        )

        st.subheader("Preview (πρώτη εγγραφή)")
        if records:
            st.code(json.dumps(records[0], ensure_ascii=False, indent=2).replace("/", "\\/"), language="json")

    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")

