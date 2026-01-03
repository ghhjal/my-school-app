# =========================================================
# منصة الأستاذ زياد التعليمية
# النسخة المستقرة – بدون تغيير أي تصميم أو وظائف
# =========================================================

import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# ================== ثوابت أسماء الأعمدة ==================
ST_ID = "id"
ST_NAME = "name"
ST_CLASS = "class"
ST_YEAR = "year"
ST_STAGE = "stage"
ST_SUBJECT = "subject"
ST_EMAIL = "email"
ST_PHONE = "phone"
ST_POINTS = "points"

GR_NAME = "name"
GR_P1 = "p1"
GR_P2 = "p2"
GR_PART = "part"

BH_NAME = "name"
BH_DATE = "date"
BH_TYPE = "type"
BH_NOTE = "note"

# ================== إعداد الصفحة (بدون تغيير) ==================
st.set_page_config(page_title="منصة الأستاذ زياد التعليمية", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
}
.header-box {
    background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
    padding: 35px; border-radius: 0 0 35px 35px; color: white;
    text-align: center; margin: -65px -20px 25px -20px;
}
.logo-box {
    background: rgba(255,255,255,0.2); width: 65px; height: 65px;
    border-radius: 18px; margin: auto;
    display: flex; justify-content: center; align-items: center;
}
.logo-box i { font-size: 32px; color: white; }
.stButton>button { border-radius: 12px !important; font-weight: bold; }
</style>

<div class="header-box">
  <div class="logo-box"><i class="bi bi-graph-up-arrow"></i></div>
  <h1 style="margin:0; font-size:24px;">منصة الأستاذ زياد</h1>
  <p style="opacity:0.8; font-size:14px;">نظام الإدارة المدرسية المتكامل</p>
</div>
""", unsafe_allow_html=True)

# ================== أدوات مساعدة ==================
def safe_int(val, default=0):
    try:
        return int(float(str(val)))
    except:
        return default

# ================== Google Sheets ==================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])

sh = get_client()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) < 2:
            return pd.DataFrame()

        headers = [h.strip() for h in data[0]]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)

        df = df.loc[:, df.columns.notna()]
        df = df.loc[:, df.columns != ""]

        df.columns = pd.io.parsers.ParserBase(
            {'names': df.columns}
        )._maybe_dedup_names(df.columns)

        return df
    except Exception as e:
        st.error(f"خطأ في جلب {sheet_name}: {e}")
        return pd.DataFrame()

# ================== Session ==================
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.sid = None

# ================== تسجيل الدخول ==================
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])

    with tab1:
        sid_input = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية")
        if st.button("دخول الطالب 🚀"):
            df_st = fetch_safe("students")
            if not df_st.empty:
                df_st[ST_ID] = df_st[ST_ID].astype(str).str.strip()
                sid = str(sid_input).strip()
                match = df_st[df_st[ST_ID] == sid]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.sid = sid
                    st.rerun()
                else:
                    st.error("❌ عذراً، رقم الهوية غير مسجل")

    with tab2:
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم 🔐"):
            u_df = fetch_safe("users")
            if not u_df.empty:
                user_row = u_df[u_df["username"] == u_name.strip()]
                if not user_row.empty:
                    hashed = hashlib.sha256(u_pass.encode()).hexdigest()
                    if hashed == user_row.iloc[0]["password_hash"]:
                        st.session_state.role = "teacher"
                        st.rerun()
                    else:
                        st.error("❌ كلمة المرور خطأ")
    st.stop()
# =========================================================
# واجهة المعلم
# =========================================================

if st.session_state.role == "teacher":

    st.sidebar.success("👨‍🏫 تم تسجيل الدخول كمعلم")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.sid = None
        st.rerun()

    # ================== جلب البيانات ==================
    df_students = fetch_safe("students")
    df_behavior = fetch_safe("behavior")

    st.subheader("📋 إدارة الطلاب")

    # ================== البحث ==================
    search_query = st.text_input("🔍 البحث باسم الطالب")

    if search_query:
        results = df_students[
            df_students[ST_NAME].str.contains(search_query, na=False)
        ]
    else:
        results = df_students.copy()

    # ================== عرض الجدول ==================
    st.dataframe(results, use_container_width=True)

    st.divider()

    # ================== إضافة نقاط سلوكية ==================
    st.subheader("⭐ إضافة نقاط سلوكية")

    col1, col2, col3 = st.columns(3)

    with col1:
        st_name = st.selectbox(
            "اسم الطالب",
            options=results[ST_NAME].dropna().unique()
        )

    with col2:
        b_type = st.selectbox(
            "نوع السلوك",
            ["مشاركة", "واجب", "التزام", "مخالفة"]
        )

    with col3:
        b_note = st.text_input("ملاحظة (اختياري)")

    # خريطة النقاط (كما هي منطقك – بدون تغيير)
    points_map = {
        "مشاركة": 5,
        "واجب": 10,
        "التزام": 7,
        "مخالفة": -5
    }

    if st.button("➕ تسجيل السلوك"):
        if st_name:
            ws_st = sh.worksheet("students")
            ws_bh = sh.worksheet("behavior")

            # تحديد الطالب
            student_row = df_students[df_students[ST_NAME] == st_name]

            if not student_row.empty:
                row_index = student_row.index[0] + 2  # +2 بسبب الهيدر

                # تحديث النقاط
                headers = ws_st.row_values(1)
                p_col = headers.index(ST_POINTS) + 1

                current_points = safe_int(
                    ws_st.cell(row_index, p_col).value
                )

                new_points = current_points + points_map.get(b_type, 0)

                ws_st.update_cell(row_index, p_col, new_points)

                # إضافة سجل السلوك
                ws_bh.append_row([
                    st_name,
                    time.strftime("%Y-%m-%d"),
                    b_type,
                    b_note
                ])

                st.success("✅ تم تسجيل السلوك بنجاح")
                st.rerun()
            else:
                st.error("❌ لم يتم العثور على الطالب")

    st.divider()

    # ================== إحصائيات سريعة ==================
    st.subheader("📊 إحصائيات سريعة")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👨‍🎓 عدد الطلاب", len(df_students))

    with col2:
        st.metric("⭐ مجموع النقاط", df_students[ST_POINTS].apply(safe_int).sum())

    with col3:
        st.metric("📘 عدد سجلات السلوك", len(df_behavior))
# =========================================================
# الدرجات + السلوك التفصيلي + الإرسال
# =========================================================

if st.session_state.role == "teacher":

    st.subheader("📝 رصد الدرجات")

    df_grades = fetch_safe("grades")

    if not df_students.empty:

        col1, col2, col3 = st.columns(3)

        with col1:
            g_name = st.selectbox(
                "اسم الطالب",
                df_students[ST_NAME].dropna().unique(),
                key="g_name"
            )

        with col2:
            g_part = st.selectbox(
                "الجزء",
                ["الأول", "الثاني"],
                key="g_part"
            )

        with col3:
            g_score = st.number_input(
                "الدرجة",
                min_value=0,
                max_value=100,
                step=1
            )

        if st.button("💾 حفظ الدرجة"):
            ws_gr = sh.worksheet("grades")

            headers = ws_gr.row_values(1)

            part_col = GR_P1 if g_part == "الأول" else GR_P2

            new_row = {
                GR_NAME: g_name,
                GR_PART: g_part,
                part_col: g_score
            }

            ws_gr.append_row([new_row.get(h, "") for h in headers])
            st.success("✅ تم حفظ الدرجة")
            st.rerun()

    st.divider()

    # ================== سجل السلوك ==================
    st.subheader("📒 سجل السلوك")

    if not df_behavior.empty:
        st.dataframe(df_behavior, use_container_width=True)
    else:
        st.info("لا يوجد سجلات سلوك بعد")

    st.divider()

    # ================== الإرسال ==================
    st.subheader("📤 التواصل مع الطالب")

    col1, col2 = st.columns(2)

    with col1:
        msg_email = st.text_area("📧 رسالة البريد الإلكتروني")

        if st.button("إرسال بريد"):
            student = df_students[df_students[ST_NAME] == g_name]
            if not student.empty:
                email = student.iloc[0][ST_EMAIL]
                if email:
                    st.success(f"📧 تم تجهيز الإرسال إلى {email}")
                else:
                    st.warning("لا يوجد بريد مسجل")

    with col2:
        msg_whatsapp = st.text_area("📱 رسالة واتساب")

        if st.button("إرسال واتساب"):
            student = df_students[df_students[ST_NAME] == g_name]
            if not student.empty:
                phone = student.iloc[0][ST_PHONE]
                if phone:
                    link = f"https://wa.me/{phone}?text={urllib.parse.quote(msg_whatsapp)}"
                    st.markdown(f"[📲 فتح واتساب]({link})")
                else:
                    st.warning("لا يوجد رقم مسجل")
# =========================================================
# واجهة الطالب
# =========================================================

if st.session_state.role == "student":

    st.sidebar.success("👨‍🎓 تم تسجيل الدخول كطالب")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.sid = None
        st.rerun()

    # ================== جلب البيانات ==================
    df_students = fetch_safe("students")
    df_grades = fetch_safe("grades")
    df_behavior = fetch_safe("behavior")

    # تحديد الطالب الحالي
    df_students[ST_ID] = df_students[ST_ID].astype(str).str.strip()
    student = df_students[df_students[ST_ID] == st.session_state.sid]

    if student.empty:
        st.error("❌ لم يتم العثور على بيانات الطالب")
        st.stop()

    s_row = student.iloc[0]

    s_name = s_row[ST_NAME]
    s_class = s_row[ST_CLASS]
    s_stage = s_row[ST_STAGE]
    s_points = safe_int(s_row[ST_POINTS])

    # ================== العنوان ==================
    st.subheader(f"👋 مرحبًا {s_name}")

    col1, col2, col3 = st.columns(3)
    col1.metric("🏫 الصف", s_class)
    col2.metric("📘 المرحلة", s_stage)
    col3.metric("⭐ النقاط", s_points)

    st.divider()

    # ================== الدرجات ==================
    st.subheader("📝 درجاتي")

    my_grades = df_grades[df_grades[GR_NAME] == s_name]

    if not my_grades.empty:
        st.dataframe(my_grades, use_container_width=True)
    else:
        st.info("لا توجد درجات مسجلة")

    st.divider()

    # ================== السلوك ==================
    st.subheader("📒 سجل السلوك")

    my_behavior = df_behavior[df_behavior[BH_NAME] == s_name]

    if not my_behavior.empty:
        st.dataframe(my_behavior, use_container_width=True)
    else:
        st.info("لا توجد سجلات سلوك")

    st.divider()

    # ================== لوحة الشرف ==================
    st.subheader("🏆 لوحة المتصدرين")

    leaderboard = df_students.copy()
    leaderboard[ST_POINTS] = leaderboard[ST_POINTS].apply(safe_int)
    leaderboard = leaderboard.sort_values(ST_POINTS, ascending=False)

    st.dataframe(
        leaderboard[[ST_NAME, ST_POINTS]].head(10),
        use_container_width=True
    )
