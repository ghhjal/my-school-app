import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

# ==========================================
# 1. المحرك المطور (توسيع قواعد البيانات)
# ==========================================
class DataManager:
    def __init__(self):
        self.conn = self._connect()
        # إضافة جداول الواجبات والحضور
        self.sheets = ["students", "grades", "behavior", "users", "exams", "homework", "attendance"]

    def _connect(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
        except: return None

    def load_all_to_state(self, force=False):
        if 'data_loaded' not in st.session_state or force:
            for sheet in self.sheets:
                try:
                    ws = self.conn.worksheet(sheet)
                    data = ws.get_all_values()
                    st.session_state[f"df_{sheet}"] = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]]) if data else pd.DataFrame()
                except: st.session_state[f"df_{sheet}"] = pd.DataFrame()
            st.session_state.data_loaded = True

    def get_df(self, name): return st.session_state.get(f"df_{name}", pd.DataFrame())

    def save_attendance(self, date, student_ids, statuses):
        """حفظ الحضور والغياب بشكل جماعي"""
        try:
            ws = self.conn.worksheet("attendance")
            rows = [[s_id, date, status] for s_id, status in zip(student_ids, statuses)]
            ws.append_rows(rows)
            self.load_all_to_state(force=True)
            return True
        except: return False

if 'manager' not in st.session_state: st.session_state.manager = DataManager()
db = st.session_state.manager
db.load_all_to_state()

# ==========================================
# 2. واجهة المعلم (الإضافات التفاعلية)
# ==========================================
if st.session_state.get("role") == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📝 التحضير اليومي", "📚 الواجبات", "🥇 السلوك", "🚗 خروج"])

    # --- تبويب التحضير (جديد) ---
    with tabs[2]:
        st.subheader("🗓️ تحضير الطلاب اليومي")
        df_st = db.get_df("students")
        if not df_st.empty:
            today = str(datetime.date.today())
            st.info(f"تحضير يوم: {today}")
            
            # عرض الطلاب بنظام Checklist
            attendance_data = []
            for i, row in df_st.iterrows():
                c1, c2 = st.columns([3, 1])
                status = c2.toggle("حاضر", value=True, key=f"att_{row.iloc[0]}")
                c1.write(f"{row.iloc[1]} ({row.iloc[2]})")
                attendance_data.append("حاضر" if status else "غائب")
            
            if st.button("💾 حفظ كشف الحضور"):
                if db.save_attendance(today, df_st.iloc[:, 0].tolist(), attendance_data):
                    st.success("تم حفظ التحضير بنجاح")

    # --- تبويب الواجبات (جديد) ---
    with tabs[3]:
        st.subheader("📚 إدارة الواجبات الإلكترونية")
        with st.form("add_hw"):
            hw_title = st.text_input("عنوان الواجب")
            hw_desc = st.text_area("وصف الواجب والمطلوب")
            hw_date = st.date_input("آخر موعد للتسليم")
            if st.form_submit_button("نشر الواجب للطلاب"):
                db.conn.worksheet("homework").append_row([hw_title, hw_desc, str(hw_date), str(datetime.date.today())])
                db.load_all_to_state(force=True)
                st.success("تم نشر الواجب")

# ==========================================
# 3. واجهة الطالب التفاعلية (v4.0)
# ==========================================
elif st.session_state.get("role") == "student":
    df_st = db.get_df("students")
    s_id = str(st.session_state.sid)
    s_info = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
    
    st.markdown(f"### مرحباً {s_info.iloc[1]} 👋")
    
    t = st.tabs(["📌 مهامي اليومية", "📊 مستواي الأكاديمي", "🗓️ حضوري"])
    
    with t[0]:
        st.subheader("📝 الواجبات المطلوبة")
        df_hw = db.get_df("homework")
        if not df_hw.empty:
            for _, hw in df_hw.iloc[::-1].iterrows():
                with st.expander(f"🆕 {hw.iloc[0]} (موعد التسليم: {hw.iloc[2]})"):
                    st.write(hw.iloc[1])
                    st.text_area("اكتب حلك هنا أو ضع رابط ملفك:", key=f"sol_{hw.iloc[0]}")
                    if st.button("تسليم الواجب", key=f"btn_{hw.iloc[0]}"):
                        st.success("تم تسليم الواجب بنجاح!")
        else: st.info("لا توجد واجبات حالياً")

    with t[2]:
        st.subheader("🗓️ سجل الغياب والحضور")
        df_att = db.get_df("attendance")
        my_att = df_att[df_att.iloc[:, 0] == s_id]
        if not my_att.empty:
            absent_days = len(my_att[my_att.iloc[:, 2] == "غائب"])
            st.metric("عدد أيام الغياب", f"{absent_days} أيام")
            st.table(my_att.iloc[::-1])
        else: st.info("لا يوجد سجل حضور مرصود لك حتى الآن")

    if st.button("خروج"): st.session_state.role = None; st.rerun()
