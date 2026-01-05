import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import urllib.parse
import io
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إعدادات المحرك والبيانات (The Engine)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية v3.0", layout="wide")

class DataManager:
    """فئة مسؤولة عن إدارة كافة عمليات البيانات لضمان الاستقرار"""
    def __init__(self):
        self.conn = self._connect()
        self.sheets = ["students", "grades", "behavior", "users", "exams"]

    def _connect(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
        except Exception as e:
            st.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return None

    def load_all_to_state(self, force=False):
        """تحميل كافة الجداول لذاكرة البرنامج لمرة واحدة"""
        if 'data_loaded' not in st.session_state or force:
            with st.spinner("جاري مزامنة البيانات..."):
                for sheet in self.sheets:
                    try:
                        ws = self.conn.worksheet(sheet)
                        data = ws.get_all_values()
                        if data:
                            st.session_state[f"df_{sheet}"] = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
                        else:
                            st.session_state[f"df_{sheet}"] = pd.DataFrame()
                    except:
                        st.session_state[f"df_{sheet}"] = pd.DataFrame()
                st.session_state.data_loaded = True

    def get_df(self, name):
        return st.session_state.get(f"df_{name}", pd.DataFrame())

    def update_record(self, sheet_name, unique_val, new_row_data, id_col_idx=0):
        """تحديث أو إضافة سجل مع مزامنة فورية"""
        try:
            ws = self.conn.worksheet(sheet_name)
            # البحث عن الصف بناءً على المعرف الفريد
            cells = ws.col_values(id_col_idx + 1)
            try:
                row_idx = cells.index(str(unique_val)) + 1
                ws.update(f"A{row_idx}", [new_row_data])
            except ValueError:
                ws.append_row(new_row_data)
            
            # تحديث الذاكرة المحلية فوراً لضمان السرعة
            self.load_all_to_state(force=True)
            return True
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ: {e}")
            return False

    def delete_record(self, sheet_name, unique_val, id_col_idx=1):
        """حذف سجل من جوجل والذاكرة"""
        try:
            ws = self.conn.worksheet(sheet_name)
            cell = ws.find(str(unique_val))
            if cell:
                ws.delete_rows(cell.row)
                self.load_all_to_state(force=True)
                return True
        except: return False

# تهيئة المحرك
if 'manager' not in st.session_state:
    st.session_state.manager = DataManager()

db = st.session_state.manager
db.load_all_to_state()

# ==========================================
# 2. الواجهة والتصميم (The View)
# ==========================================
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px; border-radius: 0 0 40px 40px;
        color: white; text-align: center; margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1); width: 65px; height: 65px; border-radius: 20px;
        margin: 0 auto 10px; display: flex; justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stButton>button {
        background: #2563eb !important; color: white !important;
        border-radius: 12px !important; font-weight: bold !important; height: 3.5em !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-shield-check" style="font-size:35px; color:white;"></i></div>
        <h1 style="font-size:24px; font-weight:700; margin:0;">منصة زياد الذكية المستقرة</h1>
        <p style="opacity:0.8; font-size:14px; margin-top:5px;">الإصدار 3.0 | هيكلة بيانات احترافية</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. إدارة الصلاحيات والدخول
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 الإدارة"])
    with t1:
        with st.form("student_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول للمنصة"):
                df_st = db.get_df("students")
                if not df_st.empty and sid in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid
                    st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("admin_login"):
            u, p = st.text_input("المستخدم"), st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = db.get_df("users")
                if not df_u.empty and u == df_u.iloc[0,0] and hashlib.sha256(p.encode()).hexdigest() == df_u.iloc[0,1]:
                    st.session_state.role = "teacher"; st.rerun()
                else: st.error("بيانات خاطئة")
    st.stop()

# ==========================================
# 4. واجهة المعلم (الهيكلة الجديدة)
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1. الإحصائيات (تعتمد على الذاكرة المحلية فوراً) ---
    with tabs[0]:
        df_s = db.get_df("students")
        df_g = db.get_df("grades")
        c1, c2, c3 = st.columns(3)
        c1.metric("عدد الطلاب", len(df_s))
        c2.metric("الدرجات المرصودة", len(df_g))
        avg_score = pd.to_numeric(df_g.iloc[:, 3], errors='coerce').mean() if not df_g.empty else 0
        c3.metric("متوسط أداء الصف", f"{avg_score:.1f}")
        
        if not df_s.empty:
            st.markdown("---")
            st.write("🏆 **أعلى الطلاب نقاطاً (تحديث فوري)**")
            df_s['pts'] = pd.to_numeric(df_s.iloc[:, 8], errors='coerce').fillna(0)
            st.bar_chart(df_s.nlargest(5, 'pts').set_index(df_s.columns[1])['pts'])

    # --- 2. إدارة الطلاب ---
    with tabs[1]:
        st.subheader("👥 السجل العام للطلاب")
        st.dataframe(db.get_df("students"), use_container_width=True)
        with st.expander("🗑️ حذف سجل طالب"):
            st_list = db.get_df("students").iloc[:, 1].tolist()
            name_to_del = st.selectbox("اختر الطالب للحذف النهائي", options=[""] + st_list)
            if st.button("🚨 تأكيد الحذف"):
                if db.delete_record("students", name_to_del):
                    st.success("تم الحذف وتحديث البيانات"); time.sleep(1); st.rerun()

    # --- 3. الدرجات (حل مشكلة النموذج الفارغ نهائياً) ---
    with tabs[2]:
        st.subheader("📈 رصد وتعديل الدرجات")
        df_st = db.get_df("students")
        df_gr = db.get_df("grades")
        
        # اختيار الطالب خارج النموذج لضمان تفاعل الـ State
        sel_name = st.selectbox("👤 اختر الطالب للرصد:", options=[""] + df_st.iloc[:, 1].tolist())
        
        if sel_name:
            # جلب البيانات الحالية من الذاكرة المحلية
            current_grade = df_gr[df_gr.iloc[:, 0] == sel_name]
            has_prev = not current_grade.empty
            
            # عرض البيانات الحالية قبل الدخول في النموذج
            if has_prev:
                st.warning(f"هذا الطالب مرصود له مسبقاً: {current_grade.iloc[0, 3]} درجة")
            
            with st.container(border=True):
                with st.form(key=f"grade_form_{sel_name}"):
                    c1, c2 = st.columns(2)
                    p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(current_grade.iloc[0,1]) if has_prev else 0.0)
                    p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(current_grade.iloc[0,2]) if has_prev else 0.0)
                    note = st.text_input("ملاحظات", value=str(current_grade.iloc[0,5]) if has_prev else "")
                    
                    if st.form_submit_button("💾 حفظ البيانات"):
                        total = p1 + p2
                        new_row = [sel_name, p1, p2, total, str(datetime.date.today()), note]
                        if db.update_record("grades", sel_name, new_row):
                            st.success("تم رصد الدرجة بنجاح")
                            st.rerun()

    # --- 4. السلوك ---
    with tabs[3]:
        st.subheader("🥇 رصد السلوك")
        df_st = db.get_df("students")
        sel_b = st.selectbox("🎯 اختر الطالب لتسجيل سلوك:", options=[""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("behavior_form"):
                b_type = st.selectbox("النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("حفظ"):
                    # إضافة السجل
                    db.conn.worksheet("behavior").append_row([sel_b, str(datetime.date.today()), b_type, b_note])
                    # تحديث النقاط في الذاكرة وجوجل
                    ws_s = db.conn.worksheet("students"); c = ws_s.find(sel_b)
                    p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5}
                    old_p = int(df_st[df_st.iloc[:, 1] == sel_b].iloc[0, 8] or 0)
                    ws_s.update_cell(c.row, 9, old_p + p_map.get(b_type, 0))
                    db.load_all_to_state(force=True)
                    st.success("تم الحفظ"); st.rerun()

    with tabs[6]:
        if st.button("تسجيل الخروج"):
            st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    df_st = db.get_df("students")
    s_id = str(st.session_state.sid)
    student_data = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
    
    st.markdown(f"### مرحباً {student_data.iloc[1]} 👋")
    st.metric("رصيد نقاطك", f"{student_data.iloc[8]} نقطة")
    
    df_g = db.get_df("grades")
    my_g = df_g[df_g.iloc[:, 0] == student_data.iloc[1]]
    if not my_g.empty:
        st.info(f"درجتك الحالية: {my_g.iloc[0, 3]}")
    
    if st.button("خروج"): st.session_state.role = None; st.rerun()
