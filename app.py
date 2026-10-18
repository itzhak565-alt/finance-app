import streamlit as st
import pandas as pd
import datetime
import os
import json
import re
import plotly.express as px

# הגדרת כיוון טקסט מימין לשמאל ועיצוב מותאם למובייל
st.markdown("""
    <style>
    body {direction: RTL; text-align: right;}
    .stTextInput, .stSelectbox {direction: RTL; text-align: right;}
    </style>
""", unsafe_allow_html=True)

st.title("אפליקציית ניהול הכספים האישית 💰")

# --- מילון משתמשים וסיסמאות מורשים ---
USERS_DB = {
    "יצחק": "1234",
    "חבר": "5678"
}

# --- מערכת התחברות מאובטחת ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.subheader("🔐 התחברות למערכת")
    with st.form("login_form"):
        username_input = st.text_input("שם משתמש:")
        password_input = st.text_input("סיסמה:", type="password")
        login_btn = st.form_submit_button("התחבר")
        
        if login_btn:
            clean_name = username_input.strip()
            if clean_name in USERS_DB and USERS_DB[clean_name] == password_input.strip():
                st.session_state.logged_in = True
                st.session_state.username = clean_name
                st.session_state.file_key = re.sub(r'[^\w]', '_', clean_name)
                st.rerun()
            else:
                st.error("שם משתמש או סיסמה שגויים. נסה שוב.")
    st.stop()

# ברגע שהמשתמש מחובר בהצלחה
username = st.session_state.username
file_key = st.session_state.file_key
CSV_FILE = f"expenses_{file_key}.csv"
BUDGET_FILE = f"budget_{file_key}.json"

col1, col2 = st.columns([3, 1])
with col1:
    st.success(f"👤 מחובר כ: **{username}**")
with col2:
    if st.button("התנתק"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.file_key = ""
        st.rerun()

st.markdown("---")

# פונקציות טעינה ושמירה
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if not df.empty:
                return df.to_dict('records')
        except:
            pass
    return []

def save_data_to_file(transactions_list):
    if transactions_list:
        df = pd.DataFrame(transactions_list)
        df.to_csv(CSV_FILE, index=False)
    else:
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)

def load_budget():
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("budget", 0.0)
        except:
            pass
    return 0.0

def save_budget(amount):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump({"budget": amount}, f)

if 'transactions' not in st.session_state or st.session_state.get('current_user_file') != file_key:
    st.session_state.transactions = load_data()
    st.session_state.monthly_budget = load_budget()
    st.session_state.current_user_file = file_key

# --- הגדרת תקציב חודשי ---
with st.expander("⚙️ הגדרת תקציב חודשי"):
    budget_input_str = st.text_input("הכנס תקציב חודשי מקסימלי (₪):", value=str(st.session_state.monthly_budget))
    if st.button("שמור תקציב"):
        try:
            new_budget = float(budget_input_str)
            st.session_state.monthly_budget = new_budget
            save_budget(new_budget)
            st.success("התקציב עודכן בהצלחה!")
            st.rerun()
        except ValueError:
            st.warning("נא להזין מספר תקין בלבד עבור התקציב.")

# --- הוספת הוצאה חדשה ---
st.subheader("➕ הוספת הוצאה חדשה")
amount_str = st.text_input("מה הסכום? (בשקלים, למשל: 150.50)", value="", key="new_amount")
category = st.selectbox("בחר קטגוריה:", ["סופרמרקט", "רכב ודלק", "השקעות וחיסכון", "בילויים", "קניות ברשת", "חשבונות ובית", "אחר"], key="new_cat")
note = st.text_input("הערה קצרה (לא חובה):", key="new_note")
date = st.date_input("תאריך:", datetime.date.today(), key="new_date")

if st.button("שמור נתונים"):
    try:
        amount = float(amount_str.strip())
        if amount > 0:
            new_id = int(datetime.datetime.now().timestamp() * 1000)
            new_tx = {
                "id": new_id,
                "תאריך": str(date),
                "סכום (₪)": amount,
                "קטגוריה": category,
                "הערה": note if note else ""
            }
            st.session_state.transactions.append(new_tx)
            save_data_to_file(st.session_state.transactions)
            st.success("הנתון נשמר בהצלחה!")
            st.rerun()
        else:
            st.warning("נא להזין סכום הגדול מ-0")
    except ValueError:
        st.warning("נא להזין סכום מספרי תקין.")

# הצגת נתונים, עריכה וסיכומים
if st.session_state.transactions:
    df = pd.DataFrame(st.session_state.transactions)
    
    total_spent = df["סכום (₪)"].sum()
    budget = st.session_state.monthly_budget
    
    st.markdown("---")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric(label="📊 סך ההוצאות", value=f"{total_spent:,.2f} ₪")
    col_m2.metric(label="🎯 תקציב חודשי", value=f"{budget:,.2f} ₪")
    
    if budget > 0:
        remaining = budget - total_spent
        col_m3.metric(label="💰 יתרה בתקציב", value=f"{remaining:,.2f} ₪", delta=f"{-total_spent:,.2f} ₪" if remaining < 0 else None)
        if remaining < 0:
            st.error("⚠️ חרגת מהתקציב החודשי שהגדרת!")
    else:
        col_m3.metric(label="💰 יתרה בתקציב", value="לא הוגדר")

    st.markdown("---")

    st.subheader("📋 עריכה וניהול ההוצאות שלך")
    st.caption("💡 טיפ: אפשר ללחוץ ישירות על התאים בטבלה למטה כדי לשנות סכומים, תאריכים או הערות בקלות!")

    # הפרדת עמודת ה-id הפנימית כדי לא לבלבל בעריכה, ומציגים טבלה ניתנת לעריכה
    display_df = df.drop(columns=["id"])
    
    # st.data_editor מאפשר עריכת שורות ישירה מול המשתמש
    edited_df = st.data_editor(display_df, use_container_width=True, key="expenses_editor")

    # כפתור לשמירת השינויים שבוצעו בתוך הטבלה
    if st.button("💾 שמור שינויים בטבלה"):
        # מחזירים בחזרה את ה-id המקורי לפי שורות הטבלה המעודכנת
        updated_records = []
        for index, row in edited_df.iterrows():
            # שומרים על ה-id המקורי של השורה אם קיים, או מייצרים חדש
            original_id = df.loc[index, "id"] if index < len(df) else int(datetime.datetime.now().timestamp() * 1000)
            updated_records.append({
                "id": original_id,
                "תאריך": str(row["תאריך"]),
                "סכום (₪)": float(row["סכום (₪)"]),
                "קטגוריה": str(row["קטגוריה"]),
                "הערה": str(row["הערה"]) if pd.notna(row["הערה"]) else ""
            })
        st.session_state.transactions = updated_records
        save_data_to_file(st.session_state.transactions)
        st.success("השינויים עודכנו ונשמרו בהצלחה בקובץ!")
        st.rerun()

    # כפתור ייצוא לקובץ
    csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 הורד את הנתונים כקובץ אקסל (CSV)",
        data=csv_data,
        file_name=f"expenses_{file_key}.csv",
        mime="text/csv",
    )

    st.subheader("🗑️ מחיקת שורה מהירה")
    transaction_options = {f"תאריך: {row['תאריך']} | {row['קטגוריה']} | {row['סכום (₪)']} ₪": row['id'] for index, row in df.iterrows()}
    
    selected_to_delete = st.selectbox("בחר הוצאה למחיקה:", ["בחר מהרשימה..."] + list(transaction_options.keys()))
    
    if selected_to_delete != "בחר מהרשימה...":
        if st.button("מחק הוצאה נבחרת"):
            target_id = transaction_options[selected_to_delete]
            st.session_state.transactions = [t for t in st.session_state.transactions if t["id"] != target_id]
            save_data_to_file(st.session_state.transactions)
            st.success("ההוצאה נמחקה בהצלחה!")
            st.rerun()

    st.subheader("📈 פילוח הוצאות מודרני")
    fig = px.pie(
        df, 
        values='סכום (₪)', 
        names='קטגוריה', 
        hole=0.4, 
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("עדיין אין הוצאות שמורות בחשבון זה. הגדר תקציב או הוסף הוצאה ראשונה למעלה!")