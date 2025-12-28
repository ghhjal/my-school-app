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

            # --- 2. تبويب السلوك (اليوم التلقائي + منع الأخطاء) ---
            with t2:
                # تصميم واجهة الرصد
                with st.form("f_behavior_smart", clear_on_submit=True):
                    sel_b = st.selectbox("اسم الطالب", names_list)
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_opts = ["تميز", "إحضار الكتاب", "حل الواجب", "إزعاج", "عدم تركيز", "أخرى..."]
                    selected_b = st.multiselect("وصف السلوك", b_opts)
                    custom = st.text_input("سلوك مخصص:") if "أخرى..." in selected_b else ""
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        sel_date = st.date_input("اختر التاريخ", value=datetime.now())
                    with c2:
                        # استخراج اليوم تلقائياً من التاريخ المختصر
                        day_en = sel_date.strftime('%A')
                        current_day_ar = days_map.get(day_en, "الأحد")
                        st.text_input("اليوم (تلقائي)", value=current_day_ar, disabled=True)
                    
                   if st.form_submit_button("🚀 رصد السلوك"):
                        try:
                            ws_b = sh.worksheet("behavior")
                            # التأكد من التاريخ بصيغة نصية واضحة لقوقل شيت
                            formatted_date = sel_date.strftime('%Y-%m-%d')
                            
                            for b in selected_b:
                                val = custom if b == "أخرى..." else b
                                
                                # الترتيب الصحيح حسب أعمدة ملفك:
                                # A: الاسم | B: النوع | C: الوصف | D: التاريخ | E: اليوم
                                row_to_add = [sel_b, b_type, val, formatted_date, current_day_ar]
                                
                                ws_b.append_row(row_to_add)
                            
                            st.success(f"تم رصد السلوك لـ {sel_b} بنجاح")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ في المزامنة: {e}")

                st.markdown("### 📋 سجل السلوك الحالي")
                try:
                    # عرض آمن يمنع الرسالة الحمراء
                    ws_b_view = sh.worksheet("behavior")
                    b_vals = ws_b_view.get_all_values()
                    if len(b_vals) > 1:
                        for i, row in enumerate(b_vals[1:]):
                            ci, cd = st.columns([5, 1])
                            with ci:
                                # معالجة مرنة للأعمدة
                                n = row[0] if len(row)>0 else "?"
                                t = row[1] if len(row)>1 else ""
                                v = row[2] if len(row)>2 else ""
                                d = row[3] if len(row)>3 else ""
                                dy = row[4] if len(row)>4 else ""
                                st.warning(f"👤 **{n}** | {t} | 🎭 {v} | 🗓️ {d} ({dy})")
                            with cd:
                                if st.button("🗑️", key=f"db_del_{i}"):
                                    ws_b_view.delete_rows(i + 2); st.rerun()
                except: st.info("جاري تحديث السجل...")
                                
    # --- 🎓 شاشة الطلاب ---
    elif page == "🎓 شاشة الطلاب":
        st.markdown("<h1>🎓 بوابة الطلاب</h1>", unsafe_allow_html=True)
        all_s = ws_students.get_all_records()
        if all_s:
            s_name = st.selectbox("اختر اسمك للعرض:", [r['name'] for r in all_s])
            if s_name:
                c1, c2 = st.columns(2)
                with c1:
                    st.info("📊 درجاتك")
                    dg = pd.DataFrame(sh.worksheet("grades").get_all_records())
                    st.dataframe(dg[dg['name']==s_name])
                with c2:
                    st.warning("🎭 سلوكك")
                    db = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                    st.dataframe(db[db['name']==s_name])

except Exception as e:
    st.error(f"حدث خطأ: {e}")
