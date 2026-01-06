import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    """الاتصال الآمن بجوجل شيت"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_client()

# --- 2. دوال التعامل مع البيانات (الاستقرار) ---
def fetch_safe(worksheet_name):
    """جلب البيانات كقاموس (Dictionary) لضمان الربط بأسماء الأعمدة"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records() # تجلب البيانات مرتبطة بأسماء الأعمدة تلقائياً
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def get_col_index(ws, col_name):
    """دالة ذكية تجد رقم العمود بناءً على اسمه لمنع انهيار البرنامج عند تغيير الجدول"""
    try:
        headers = ws.row_values(1)
        return headers.index(col_name) + 1
    except:
        return None

# --- 3. التصميم المطور (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    .stButton>button { border-radius: 12px; font-weight: bold; transition: 0.3s; }
    /* منع ظهور الشاشة البيضاء بسبب أخطاء التنسيق */
    div[data-testid="stForm"] { border-radius: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. إدارة الجلسة ---
if "role" not in st.session_state:
    st.session_state.role = None

# --- [واجهة تسجيل الدخول - تظل كما هي مع تحسين جلب البيانات] ---
# ... (يمكنك الاحتفاظ بكود الدخول الخاص بك هنا) ...

# --- 5. واجهة المعلم الاحترافية ---
if st.session_state.role == "teacher":
    st.markdown("### 👨‍🏫 لوحة تحكم المعلم")
    
    tabs = st.tabs(["👥 إدارة الطلاب", "📈 رصد الدرجات", "🥇 السلوك", "⚙️ الإعدادات", "🚗 خروج"])

    # --- تبويب إدارة الطلاب (الحذف الآمن) ---
    with tabs[0]:
        st.markdown("#### 🗑️ حذف طالب (بناءً على الرقم الأكاديمي)")
        df_st = fetch_safe("students")
        if not df_st.empty:
            # نستخدم الرقم الأكاديمي كمفتاح أساسي فريد للبحث والحذف
            del_id = st.selectbox("اختر الرقم الأكاديمي للطالب:", [""] + df_st['الرقم الأكاديمي'].astype(str).tolist())
            
            if st.button("🚨 تنفيذ الحذف النهائي", use_container_width=True):
                if del_id:
                    ws = sh.worksheet("students")
                    cell = ws.find(del_id) # البحث عن السطر الذي يحتوي على هذا الرقم
                    if cell:
                        ws.delete_rows(cell.row)
                        st.success(f"✅ تم حذف الطالب صاحب الرقم {del_id} بنجاح")
                        time.sleep(1)
                        st.rerun()

    # --- تبويب رصد الدرجات (الاعتماد على الأسماء) ---
    with tabs[1]:
        st.markdown("#### 📝 إدخال درجات الطلاب")
        if not df_st.empty:
            with st.form("grades_pro_form"):
                student_name = st.selectbox("اختر الطالب:", df_st['الاسم الثلاثي'].tolist())
                col1, col2 = st.columns(2)
                p1 = col1.number_input("المشاركة (p1)", 0.0, 20.0)
                p2 = col2.number_input("الواجبات (p2)", 0.0, 20.0)
                
                if st.form_submit_button("💾 حفظ الدرجات"):
                    # جلب الرقم الأكاديمي للطالب المختار للربط الصحيح
                    s_id = df_st[df_st['الاسم الثلاثي'] == student_name]['الرقم الأكاديمي'].values[0]
                    ws_g = sh.worksheet("grades")
                    ws_g.append_row([str(s_id), p1, p2, datetime.date.today().isoformat()])
                    st.success("✅ تم حفظ الدرجات بنجاح")

    # --- تبويب السلوك (تحديث النقاط الذكي) ---
    with tabs[2]:
        st.markdown("#### 🥇 تحديث نقاط السلوك ديناميكياً")
        if not df_st.empty:
            target_student = st.selectbox("اختر الطالب للرصد:", df_st['الاسم الثلاثي'].tolist(), key="beh_select")
            b_type = st.radio("نوع الملاحظة:", ["🌟 متميز (+10)", "❌ مخالفة (-10)"])
            
            if st.button("🚀 تحديث الرصيد"):
                ws_st = sh.worksheet("students")
                # البحث عن رقم عمود "النقاط" بالاسم بدلاً من رقم (9)
                points_col_idx = get_col_index(ws_st, "النقاط")
                
                cell = ws_st.find(target_student)
                if cell and points_col_idx:
                    # جلب النقاط الحالية بأمان
                    current_val = ws_st.cell(cell.row, points_col_idx).value
                    current_points = int(current_val) if current_val else 0
                    
                    points_change = 10 if "+" in b_type else -10
                    ws_st.update_cell(cell.row, points_col_idx, current_points + points_change)
                    st.success(f"✅ تم تحديث نقاط {target_student}")
                    time.sleep(1)
                    st.rerun()

# --- خروج ---
if st.session_state.role:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب الاحترافية (Responsive Badges)
# ==========================================
if st.session_state.role == "student":
    
    # جلب البيانات باستخدام الدوال المستقرة
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    df_beh = fetch_safe("behavior")
    df_ex = fetch_safe("exams")

    try:
        # البحث عن بيانات الطالب باستخدام الرقم الأكاديمي (ID) لضمان الدقة
        student_row = df_st[df_st['الرقم الأكاديمي'].astype(str) == str(st.session_state.sid)]
        
        if not student_row.empty:
            s_data = student_row.iloc[0]
            s_name = s_data['الاسم الثلاثي']
            s_class = s_data['الصف']
            
            # جلب النقاط بأمان (معالجة القيم النصية أو الفارغة)
            points_val = s_data['النقاط']
            s_points = int(points_val) if str(points_val).isdigit() else 0
        else:
            st.error("⚠️ لم يتم العثور على بياناتك، يرجى مراجعة الإدارة.")
            st.stop()
    except Exception as e:
        st.error(f"❌ خطأ في جلب البيانات: {e}")
        st.stop()

    # --- 1. منطق الأوسمة التفاعلي ---
    # تحديد مستوى الوسام بناءً على النقاط
    badge_data = {
        "bronze": {"name": "البرونزي", "target": 10, "icon": "🥉", "color": "#cd7f32"},
        "silver": {"name": "الفضي", "target": 50, "icon": "🥈", "color": "#c0c0c0"},
        "gold": {"name": "الذهبي", "target": 100, "icon": "🥇", "color": "#ffd700"}
    }

    current_badge = "مبتدئ"
    points_to_next = 10
    next_badge_name = "البرونزي"

    if s_points >= 100:
        current_badge = "ذهبي"
        points_to_next = 0
    elif s_points >= 50:
        current_badge = "فضي"
        next_badge_name = "الذهبي"
        points_to_next = 100 - s_points
    elif s_points >= 10:
        current_badge = "برونزي"
        next_badge_name = "الفضي"
        points_to_next = 50 - s_points

    # --- 2. التصميم العلوي (الهوية البصرية) ---
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <h1 style="margin:0; font-size: 24px;">مرحباً بك، {s_name} 👋</h1>
            <p style="opacity: 0.9; margin-top: 5px;">فصل: {s_class} | نظام النقاط الذكي</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. عرض الأوسمة (UI) ---
    col_points, col_badge = st.columns([1, 1])

    with col_points:
        st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; border: 2px solid #e2e8f0; text-align: center;">
                <p style="color: #64748b; font-weight: bold; margin-bottom: 5px;">رصيد نقاطك الحالي</p>
                <h2 style="color: #1e40af; font-size: 48px; margin: 0;">{s_points}</h2>
                <p style="color: #059669; font-size: 14px;">🌟 أنت تبلي بلاءً حسناً!</p>
            </div>
        """, unsafe_allow_html=True)

    with col_badge:
        # عرض الوسام الحالي مع شريط التقدم
        st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; border: 2px solid #e2e8f0; text-align: center; height: 100%;">
                <p style="color: #64748b; font-weight: bold; margin-bottom: 5px;">وسامك الحالي</p>
                <div style="font-size: 40px;">{badge_data.get(current_badge, {'icon': '🌱'})['icon']}</div>
                <h3 style="margin: 0; color: #1e293b;">الوسام {current_badge.capitalize()}</h3>
                {f'<p style="font-size: 12px; color: #f59e0b;">بقي {points_to_next} نقطة للوسام {next_badge_name}</p>' if points_to_next > 0 else '<p style="color: #059669;">أنت بطل ذهبي! 🏆</p>'}
            </div>
        """, unsafe_allow_html=True)

    # --- 4. التبويبات التفاعلية ---
    t1, t2, t3 = st.tabs(["📢 التنبيهات", "📊 نتائجي", "🎭 سجل السلوك"])

    with t1:
        if not df_ex.empty:
            # فلترة التنبيهات بناءً على صف الطالب أو الإعلانات العامة "الكل"
            my_exams = df_ex[(df_ex['الصف'] == s_class) | (df_ex['الصف'] == "الكل")]
            for _, row in my_exams.iloc[::-1].iterrows():
                st.info(f"📅 **{row['التاريخ']}** | {row['العنوان']}")
        else:
            st.write("لا توجد تنبيهات جديدة حالياً.")

    with t2:
        # عرض الدرجات المسجلة في شيت grades
        st.markdown("#### 📈 درجات المواد")
        my_grades = df_grades[df_grades['student_id'].astype(str) == str(st.session_state.sid)]
        if not my_grades.empty:
            st.dataframe(my_grades, use_container_width=True, hide_index=True)
        else:
            st.warning("لم يتم رصد درجات لك بعد.")

    with t3:
        # عرض الملاحظات السلوكية
        st.markdown("#### 🎭 سجل الانضباط والمشاركة")
        my_behavior = df_beh[df_beh['الاسم'].astype(str) == str(s_name)]
        if not my_behavior.empty:
            for _, row in my_behavior.iloc[::-1].iterrows():
                color = "green" if "+" in str(row['النوع']) else "red"
                st.markdown(f"""
                    <div style="border-right: 5px solid {color}; padding: 10px; background: #f8fafc; margin-bottom: 5px;">
                        <b>{row['النوع']}</b> - {row['التاريخ']}<br>
                        <small>{row['الملاحظة']}</small>
                    </div>
                """, unsafe_allow_html=True)

    # --- خروج ---
    if st.button("🚗 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None
        st.rerun()
