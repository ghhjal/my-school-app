import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# ==========================================
# 1. تهيئة حالة الجلسة (منع الأخطاء)
# ==========================================
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# ==========================================
# 2. إعداد الاتصال بجوجل (دالة الربط الفعلية)
# ==========================================
def fetch_safe(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # تأكد من إضافة secrets في Streamlit Cloud
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # رابط ملفك الذي أرسلته
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit") 
        return pd.DataFrame(sh.worksheet(sheet_name).get_all_records()), sh
    except Exception as e:
        # st.error(f"خطأ في الاتصال: {e}") # يمكن تفعيله عند الفحص
        return pd.DataFrame(), None

# جلب البيانات الأولية لزوم الإحصائيات في الصفحة الرئيسية
df_st, sh = fetch_safe("students")

# ==========================================
# 🏠 3. الصفحة الرئيسية (واجهة الجوال)
# ==========================================
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 15px; text-align: center; border-radius: 15px; margin-bottom: 20px; color: white;">
            <h2 style="font-family: 'Cairo', sans-serif; font-size: 1.8rem; margin: 0;">🌟 منصة الأستاذ زياد العمري</h2>
            <p style="font-size: 1rem; opacity: 0.9; margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    total_students = len(df_st) if not df_st.empty else 0
    st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
            <div style="flex: 1; min-width: 100px; background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem;">👨‍🎓</div>
                <div style="color: #64748b; font-size: 0.7rem;">الطلاب</div>
                <div style="color: #1e3a8a; font-size: 1.2rem; font-weight: bold;">{total_students}</div>
            </div>
            <div style="flex: 1; min-width: 100px; background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem;">📝</div>
                <div style="color: #64748b; font-size: 0.7rem;">الدرجات</div>
                <div style="color: #1e3a8a; font-size: 1.2rem; font-weight: bold;">100%</div>
            </div>
            <div style="flex: 1; min-width: 100px; background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem;">🏆</div>
                <div style="color: #64748b; font-size: 0.7rem;">الأوسمة</div>
                <div style="color: #1e3a8a; font-size: 1.2rem; font-weight: bold;">مفعلة</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<h4 style='text-align: center; color: #1e3a8a; margin: 20px 0 15px 0;'>🔐 تسجيل الدخول</h4>", unsafe_allow_html=True)
        login_type = st.radio("الدخول كـ:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", placeholder="مثال: 1001")
        
        if st.button("🚀 دخول للمنصة", use_container_width=True, type="primary"):
            if login_type == "معلم":
                if user_id == "1234":
                    st.session_state.role = "teacher"
                    st.rerun()
                else: st.error("كود المعلم غير صحيح")
            else:
                if not df_st.empty and str(user_id) in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(user_id)
                    st.rerun()
                else: st.error("الكود غير مسجل")

    st.markdown("""<div style="margin-top: 40px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 20px;"><p style="color: #94a3b8; font-size: 0.75rem; margin: 0;">جميع الحقوق محفوظة © 2025</p><b style="color: #1e3a8a; font-size: 0.8rem;">الأستاذ زياد العمري</b></div>""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 4. واجهة المعلم (كما أرسلتها تماماً)
# ==========================================
elif st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))

    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st, _ = fetch_safe("students")
        with st.container(border=True):
            st.subheader("📋 السجل الحالي")
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        with st.form("add_student_pro", clear_on_submit=True):
            st.markdown("### ➕ تأسيس طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid, nname, nclass = c1.text_input("🔢 الرقم الأكاديمي"), c2.text_input("👤 الاسم الثلاثي"), c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            c4, c5, c6 = st.columns(3)
            nstage, nyear, nsub = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"]), c5.text_input("🗓️ العام", value="1447هـ"), c6.text_input("📚 المادة", value="لغة إنجليزية")
            
            if st.form_submit_button("✅ اعتماد التأسيس"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"])
                    st.success("تم التأسيس بنجاح"); st.rerun()

    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        df_st, _ = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g, _ = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("grade_pro_form"):
                st.markdown(f"**تحديث درجات الطالب: {target}**")
                c1, c2, c3 = st.columns(3)
                p1, p2, part = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1), c2.number_input("📉 الفترة الثانية", 0, 100, value=v2), c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                if st.form_submit_button("💾 حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ"); st.rerun()
        st.divider()
        st.dataframe(fetch_safe("grades")[0], use_container_width=True, hide_index=True)

    elif menu == "🎭 رصد السلوك":
        st.markdown('<div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;"><h1>🎭 رصد السلوك والتواصل الفوري</h1></div>', unsafe_allow_html=True)
        df_st, _ = fetch_safe("students")
        search_term = st.text_input("🔍 ابحث عن اسم الطالب (اكتب هنا)")
        filtered_names = [n for n in df_st.iloc[:, 1].tolist() if search_term in n] if search_term else df_st.iloc[:, 1].tolist()
        b_name = st.selectbox("🎯 اختر الطالب المطلوب:", [""] + filtered_names)
        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email, s_phone = student_info[6], str(student_info[7]).split('.')[0]
            with st.form("behavior_form"):
                c1, c2 = st.columns(2)
                b_type, b_date = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"]), c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 نص الملاحظة السلوكية")
                c1, c2, c3 = st.columns(3)
                if c1.form_submit_button("💾 حفظ فقط") or c2.form_submit_button("📧 إيميل") or c3.form_submit_button("💬 واتساب"):
                    if b_note:
                        sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                        # تحديث النقاط
                        try:
                            ws_st = sh.worksheet("students"); cell = ws_st.find(b_name)
                            p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                            curr_p = int(ws_st.cell(cell.row, 9).value or 0)
                            ws_st.update_cell(cell.row, 9, str(curr_p + p_map.get(b_type, 0)))
                        except: pass
                        st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

    elif menu == "📢 شاشة الاختبارات":
        st.markdown('<div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>📢 مركز التنبيهات</h1></div>', unsafe_allow_html=True)
        with st.form("announcement_form"):
            c1, c2, c3 = st.columns([1, 2, 1])
            a_class, a_title, a_date = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"]), c2.text_input("📝 عنوان التنبيه"), c3.date_input("📅 الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([a_class, a_title, str(a_date)]); st.rerun()
        df_ann, _ = fetch_safe("exams")
        if not df_ann.empty:
            for i, row in df_ann.iloc[::-1].iterrows():
                st.info(f"[{row[0]}] {row[1]} - 📅 {row[2]}")

# ==========================================
# 👨‍🎓 5. واجهة الطالب (كما أرسلتها تماماً)
# ==========================================
elif st.session_state.role == "student":
    df_st, _ = fetch_safe("students")
    df_grades, _ = fetch_safe("grades")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name, s_class = s_row[1], s_row[2]
    try: s_points = int(s_row[8]) if s_row[8] else 0
    except: s_points = 0
    try:
        g_row = df_grades[df_grades.iloc[:, 0].astype(str) == s_name].iloc[0]
        p1, p2, perf = g_row[1], g_row[2], g_row[3]
    except: p1, p2, perf = "-", "-", "-"

    st.markdown(f'<div style="background:#1e3a8a; padding:12px; border-bottom:5px solid #f59e0b; text-align:center;"><h3 style="color:white; margin:0;">🎯 لوحة إنجاز الطالب: {s_name}</h3></div>', unsafe_allow_html=True)
    
    # بطاقة الأوسمة
    st.markdown(f"""<div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
        <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
            <div style="opacity: {'1' if s_points >= 10 else '0.2'};">🥉<br>برونزي</div>
            <div style="opacity: {'1' if s_points >= 50 else '0.2'};">🥈<br>فضي</div>
            <div style="opacity: {'1' if s_points >= 100 else '0.2'};">🥇<br>ذهبي</div>
        </div>
        <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px;">رصيد النقاط: <b style="font-size: 2rem;">{s_points}</b></div>
    </div>""", unsafe_allow_html=True)

    t_ex, t_grade, t_beh, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "⚙️ الإعدادات"])
    
    with t_ex:
        df_ex, _ = fetch_safe("exams")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.markdown(f'<div style="background:#002347; padding:15px; border-radius:12px; border-right:8px solid #f59e0b; margin-bottom:10px; color:white;"><b>📢 {r[1]}</b><br><small>📅 الموعد: {r[2]}</small></div>', unsafe_allow_html=True)

    with t_grade:
        st.markdown(f'<div style="background:#f0f4f8; padding:15px; border-radius:10px; border:1px solid #1e3a8a; display:flex; justify-content:space-between;"><b>المشاركة (p1)</b><b style="color:#d97706;">{p1}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#f0f4f8; padding:15px; border-radius:10px; border:1px solid #1e3a8a; display:flex; justify-content:space-between; margin-top:5px;"><b>الواجبات (p2)</b><b style="color:#d97706;">{p2}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#f0f4f8; padding:15px; border-radius:10px; border:1px solid #1e3a8a; display:flex; justify-content:space-between; margin-top:5px;"><b>الاختبارات (perf)</b><b style="color:#d97706;">{perf}</b></div>', unsafe_allow_html=True)

    with t_beh:
        df_beh, _ = fetch_safe("behavior")
        if not df_beh.empty:
            for _, r in df_beh[df_beh.iloc[:, 0] == s_name].iloc[::-1].iterrows():
                is_pos = "+" in str(r[2])
                bg, clr = ("#f0fdf4", "#166534") if is_pos else ("#fef2f2", "#991b1b")
                st.markdown(f'<div style="background:{bg}; padding:15px; border-radius:12px; border-right:8px solid {clr}; color:{clr}; margin-bottom:10px;"><b>{r[2]}</b><br>{r[3]}</div>', unsafe_allow_html=True)

    with t_set:
        with st.form("st_settings"):
            new_mail = st.text_input("📧 البريد", value=str(s_row[6]))
            new_phone = st.text_input("📱 الجوال", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ"):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail); ws.update_cell(cell.row, 8, new_phone); st.rerun()
        if st.button("🚗 خروج", use_container_width=True):
            st.session_state.role = None; st.rerun()
