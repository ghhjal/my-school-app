import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 20px; font-weight: bold; }
    .student-card { 
        background-color: white; padding: 15px; border-radius: 12px; 
        border-right: 6px solid #d4af37; margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    h1 { color: #1a1a1a; text-align: center; border-bottom: 3px solid #d4af37; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# مصفوفة ترجمة الأيام
def get_day_ar(day_en):
    days = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
            "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    return days.get(day_en, day_en)

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws_students = sh.worksheet("students")

    with st.sidebar:
        st.title("بوابة الأستاذ زياد")
        page = st.radio("انتقل إلى:", ["🏠 الرئيسية", "👥 إدارة الطلاب", "📊 الدرجات والسلوك", "🎓 شاشة الطلاب"])
        st.divider()
        st.info("v5.0 - النسخة الاحترافية")

   # --- شاشة إدارة الطلاب (المستقرة) ---
    if page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with tab1:
            with st.form("add_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ")
                    st.rerun()

        with tab2:
            data = ws_students.get_all_records()
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                for i, r in df.iterrows():
                    # جلب الاسم والتعامل مع حالات عدم وجوده
                    student_name = r.get("name", "؟؟")
                    
                    st.markdown(f'<div class="student-card"><strong>{student_name}</strong> (ID: {r.get("id", i)})</div>', unsafe_allow_html=True)
                    
                    if st.button("🗑️ حذف", key=f"ds_{i}"):
                        try:
                            # 1. الحذف من ورقة الطلاب الرئيسية
                            ws_students.delete_rows(i + 2)
                            
                            # 2. الحذف الذكي من ورقة الدرجات
                            try:
                                ws_g = sh.worksheet("grades")
                                g_data = ws_g.get_all_values()
                                for r_idx in range(len(g_data), 1, -1):
                                    if g_data[r_idx-1][0] == student_name:
                                        ws_g.delete_rows(r_idx)
                            except: pass

                            # 3. الحذف الذكي من ورقة السلوك
                            try:
                                ws_b = sh.worksheet("behavior")
                                b_data = ws_b.get_all_values()
                                for r_idx in range(len(b_data), 1, -1):
                                    if b_data[r_idx-1][0] == student_name:
                                        ws_b.delete_rows(r_idx)
                            except: pass
                            
                            st.success(f"تم حذف {student_name} وسجلاته")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")

# --- 📊 شاشة الدرجات والسلوك (النسخة المستقرة v6.0) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        
        all_students = ws_students.get_all_records()
        if not all_students:
            st.warning("⚠️ يرجى إضافة طلاب أولاً.")
        else:
            names_list = [r.get('Name', r.get('name', 'بدون اسم')) for r in all_students]
            t1, t2 = st.tabs(["📝 إدارة الدرجات", "🎭 إدارة السلوك والمواظبة"])
            
            days_map = {
                "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
                "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
            }

            # --- 1. تبويب الدرجات (تحديث بدون تكرار) ---
            with t1:
                with st.form("f_grades_final", clear_on_submit=True):
                    sel_st = st.selectbox("اختر الطالب", names_list)
                    c1, c2, c3 = st.columns(3)
                    with c1: v1 = st.number_input("درجة P1", min_value=0.0)
                    with c2: v2 = st.number_input("درجة P2", min_value=0.0)
                    with c3: vp = st.number_input("الأداء (perf)", min_value=0.0)
                    
                    if st.form_submit_button("✅ حفظ وتحديث الدرجات"):
                        try:
                            ws_g = sh.worksheet("grades")
                            all_g = ws_g.get_all_values()
                            found = False
                            for idx, row in enumerate(all_g):
                                if row[0] == sel_st:
                                    ws_g.update(f"A{idx+1}:D{idx+1}", [[sel_st, v1, v2, vp]])
                                    found = True; break
                            if not found:
                                ws_g.append_row([sel_st, v1, v2, vp])
                            st.success(f"تم تحديث بيانات {sel_st}")
                        except: st.error("خطأ في ورقة grades")

         # --- 2. تبويب السلوك (نسخة الرصد السريع) ---
            with t2:
                with st.form("f_behavior_quick_v13", clear_on_submit=True):
                    sel_b = st.selectbox("👤 اسم الطالب", names_list)
                    
                    b_type = st.radio("📌 نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    
                    # القائمة الآن تختار سلوكاً واحداً لتغلق تلقائياً
                    b_opts = [
                        "🌟 تميز", 
                        "📚 إحضار الكتاب", 
                        "✅ حل الواجب", 
                        "⚠️ إزعاج", 
                        "🚫 عدم تركيز", 
                        "➕ أخرى..."
                    ]
                    selected_b = st.selectbox("🎭 وصف السلوك", b_opts)
                    
                    custom = st.text_input("✍️ اكتب السلوك المخصص:") if "أخرى..." in selected_b else ""
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        sel_date = st.date_input("🗓️ التاريخ", value=datetime.now())
                    with c2:
                        day_en = sel_date.strftime('%A')
                        days_map = {
                            "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
                            "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
                        }
                        current_day_ar = days_map.get(day_en, "الأحد")
                        st.text_input("📅 اليوم", value=current_day_ar, disabled=True)
                    
                    if st.form_submit_button("🚀 حفظ ورصد الآن"):
                        try:
                            ws_b = sh.worksheet("behavior")
                            val = custom if "أخرى..." in selected_b else selected_b
                            # الحفظ في جوجل شيت بنفس ترتيب أعمدتك
                            ws_b.append_row([sel_b, str(sel_date), b_type, val, current_day_ar])
                            st.success(f"✅ تم رصد {val} للطالب {sel_b}")
                            st.rerun()
                        except:
                            st.info("🔄 جاري التحديث...")

                # عرض السجل المحمي لمنع الرسائل الحمراء
                st.markdown("### 📋 سجل السلوك الأخير")
                try:
                    ws_view = sh.worksheet("behavior")
                    data = ws_view.get_all_values()
                    if len(data) > 1:
                        for i, row in enumerate(reversed(data[1:])):
                            # عرض البيانات مع الرموز المحفوظة
                            st.warning(f"👤 **{row[0]}** | {row[2]} | {row[3]} | 🗓️ {row[1]}")
                            if i > 5: break # عرض آخر 6 سجلات فقط للسرعة
                except:
                    st.write("⌛ جاري مزامنة السجل...")
                                
    with t3:
                st.subheader("🔍 استعلام بيانات الطالب")
                # اختيار الطالب للمعاينة
                selected_student = st.selectbox("اختر اسم الطالب لعرض ملفه", names_list)
                
                if selected_student:
                    # تقسيم الشاشة لبطاقات إحصائية
                    col_info, col_chart = st.columns([2, 1])
                    
                    with col_info:
                        st.info(f"👤 ملف الطالب: **{selected_student}**")
                        # هنا سنقوم بجلب الدرجات والسلوكيات الخاصة بهذا الطالب فقط
                        # (سأزودك بكود الربط الذكي لها فور جاهزيتك)
                    
                    with col_chart:
                        st.metric(label="✅ السلوك الإيجابي", value="12") # مثال رقمي
                        st.metric(label="❌ السلوك السلبي", value="2")  # مثال رقمي
