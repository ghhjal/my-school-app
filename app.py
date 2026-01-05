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
            return None

    def load_all_to_state(self, force=False):
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
        try:
            ws = self.conn.worksheet(sheet_name)
            cells = ws.col_values(id_col_idx + 1)
            try:
                row_idx = cells.index(str(unique_val)) + 1
                ws.update(f"A{row_idx}", [new_row_data])
            except ValueError:
                ws.append_row(new_row_data)
            self.load_all_to_state(force=True)
            return True
        except: return False

    def delete_record(self, sheet_name, unique_val):
        try:
            ws = self.conn.worksheet(sheet_name)
            cell = ws.find(str(unique_val))
            if cell:
                ws.delete_rows(cell.row)
                self.load_all_to_state(force=True)
                return True
        except: return False

if 'manager' not in st.session_state: st.session_state.manager = DataManager()
db = st.session_state.manager
db.load_all_to_state()

# ==========================================
# 2. الدوال المساعدة (للأوسمة والتقارير)
# ==========================================
def get_badge(points):
    p = int(float(str(points or 0)))
    if p >= 100: return "🏆 القائد الذهبي"
    if p >= 50: return "🌟 الطالب المتميز"
    if p >= 20: return "✨ المتفاعل"
    if p < 0: return "⚠️ يحتاج توجيه"
    return "🌱 برعم صاعد"

def send_detailed_report(to_email, s_name, grade_data, beh_data):
    try:
        conf = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = conf["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = f"📊 التقرير الشهري للطالب: {s_name}"
        
        # بناء جسم التقرير (HTML)
        grade_html = "<h4>الدرجات الأكاديمية:</h4><ul>"
        if not grade_data.empty:
            g = grade_data.iloc[0]
            grade_html += f"<li>المهام (P1): {g[1]}</li><li>الاختبار (P2): {g[2]}</li><li><b>المجموع النهائي: {g[3]}</b></li>"
            if g[5]: grade_html += f"<li>ملاحظة المعلم: {g[5]}</li>"
        else: grade_html += "<li>لا توجد درجات مرصودة.</li>"
        grade_html += "</ul>"

        beh_html = "<h4>سجل السلوك والانضباط:</h4><ul>"
        if not beh_data.empty:
            for _, r in beh_data.iloc[::-1].iterrows():
                beh_html += f"<li>{r[1]} | {r[2]} | {r[3]}</li>"
        else: beh_html += "<li>سجل السلوك نظيف.</li>"
        beh_html += "</ul>"

        full_body = f"""
        <div dir="rtl" style="font-family: 'Cairo', sans-serif;">
            <h3>تحية طيبة لولي أمر الطالب: {s_name}</h3>
            <p>نرفق لكم التقرير الشهري لأداء ابنكم في منصة الأستاذ زياد:</p>
            <hr>
            {grade_html}
            {beh_html}
            <hr>
            <p style="font-size:12px; color:gray;">تم إرسال هذا التقرير تلقائياً من المنصة.</p>
        </div>
        """
        msg.attach(MIMEText(full_body, 'html', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(conf["sender_email"], conf["sender_password"])
            s.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. التصميم والواجهة (The View)
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
    .badge-gold { background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-shield-check" style="font-size:35px; color:white;"></i></div>
        <h1 style="font-size:24px; font-weight:700; margin:0;">منصة زياد الذكية المستقرة</h1>
        <p style="opacity:0.8; font-size:14px; margin-top:5px;">الإصدار 3.0 | هيكلة بيانات احترافية</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. إدارة الصلاحيات والدخول
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
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
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
# 5. واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1. الإحصائيات ---
    with tabs[0]:
        df_s = db.get_df("students"); df_g = db.get_df("grades")
        c1, c2, c3 = st.columns(3)
        c1.metric("عدد الطلاب", len(df_s))
        c2.metric("الدرجات المرصودة", len(df_g))
        avg_score = pd.to_numeric(df_g.iloc[:, 3], errors='coerce').mean() if not df_g.empty else 0
        c3.metric("متوسط أداء الصف", f"{avg_score:.1f}")
        
        if not df_s.empty:
            st.markdown("---"); st.write("🏆 **أعلى الطلاب نقاطاً (تحديث فوري)**")
            df_s['pts'] = pd.to_numeric(df_s.iloc[:, 8], errors='coerce').fillna(0)
            top5 = df_s.nlargest(5, 'pts')
            for _, r in top5.iterrows():
                st.write(f"• {r[1]} - {r['pts']} نقطة - {get_badge(r['pts'])}")

    # --- 2. إدارة الطلاب (إضافة زر التقارير) ---
    with tabs[1]:
        st.subheader("👥 السجل العام للطلاب")
        df_st = db.get_df("students")
        df_st['الوسام'] = df_st.iloc[:, 8].apply(get_badge)
        st.dataframe(df_st[['الرقم', 'الاسم', 'الصف', 'النقاط', 'الوسام']], use_container_width=True)
        
        with st.expander("📤 إرسال تقرير شهري"):
            st_list = df_st.iloc[:, 1].tolist()
            sel_rep = st.selectbox("اختر الطالب لإرسال التقرير", options=[""] + st_list)
            if sel_rep and st.button("🚀 إرسال التقرير الآن"):
                s_data = df_st[df_st.iloc[:, 1] == sel_rep].iloc[0]
                g_data = db.get_df("grades"); g_data = g_data[g_data.iloc[:, 0] == sel_rep]
                b_data = db.get_df("behavior"); b_data = b_data[b_data.iloc[:, 0] == sel_rep]
                if send_detailed_report(s_data.iloc[6], sel_rep, g_data, b_data):
                    st.success(f"تم إرسال التقرير بنجاح لولي أمر {sel_rep}")
                else: st.error("فشل الإرسال")

    # --- 3. الدرجات (إصلاح الخطأ + نقل الزر) ---
    with tabs[2]:
        st.subheader("📈 رصد وتعديل الدرجات")
        df_st = db.get_df("students"); df_gr = db.get_df("grades")
        sel_name = st.selectbox("👤 اختر الطالب للرصد:", options=[""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            current_grade = df_gr[df_gr.iloc[:, 0] == sel_name]
            has_prev = not current_grade.empty
            if has_prev: st.warning(f"هذا الطالب مرصود له مسبقاً: {current_grade.iloc[0, 3]} درجة")
            
            with st.container(border=True):
                with st.form(key=f"grade_form_{sel_name}"):
                    c1, c2 = st.columns(2)
                    p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(current_grade.iloc[0,1]) if has_prev else 0.0)
                    p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(current_grade.iloc[0,2]) if has_prev else 0.0)
                    # إصلاح الخطأ: التأكد من وجود عمود الملاحظات قبل قراءته
                    note_val = str(current_grade.iloc[0,5]) if has_prev and current_grade.shape[1] > 5 else ""
                    note = st.text_input("ملاحظات", value=note_val)
                    # إصلاح الخطأ: نقل الزر لداخل النموذج
                    if st.form_submit_button("💾 حفظ البيانات"):
                        total = p1 + p2
                        new_row = [sel_name, p1, p2, total, str(datetime.date.today()), note]
                        if db.update_record("grades", sel_name, new_row):
                            st.success("تم رصد الدرجة بنجاح"); st.rerun()

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
                    db.conn.worksheet("behavior").append_row([sel_b, str(datetime.date.today()), b_type, b_note])
                    ws_s = db.conn.worksheet("students"); c = ws_s.find(sel_b)
                    p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5}
                    old_p = int(df_st[df_st.iloc[:, 1] == sel_b].iloc[0, 8] or 0)
                    ws_s.update_cell(c.row, 9, old_p + p_map.get(b_type, 0))
                    db.load_all_to_state(force=True)
                    st.success("تم الحفظ"); st.rerun()

    with tabs[6]:
        if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 6. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    df_st = db.get_df("students")
    s_id = str(st.session_state.sid)
    student_data = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
    points = int(float(str(student_data.iloc[8] or 0)))
    
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; text-align: center; border: 1px solid #e2e8f0;">
            <h2 style="margin:0;">مرحباً، {student_data.iloc[1]} 👋</h2>
            <div style="margin: 15px 0;">
                <span class="badge-gold" style="font-size: 18px;">{get_badge(points)}</span>
            </div>
            <h4 style="color: #1e40af;">رصيدك الحالي: {points} نقطة</h4>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("خروج"): st.session_state.role = None; st.rerun()
