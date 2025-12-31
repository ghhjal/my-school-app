import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            # تنظيف وتوحيد أسماء الأعمدة لمنع الأخطاء
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("عذراً، الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (تصميم احترافي موحد)
# ==========================================
if st.session_state.role == "teacher":
    # 1. القائمة الجانبية الموحدة
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))

    # --- القسم الأول: إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        st.write("")
        with st.container(border=True):
            st.subheader("📋 السجل الحالي")
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        with st.form("add_student_pro", clear_on_submit=True):
            st.markdown("### ➕ تأسيس طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            
            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nyear = c5.text_input("🗓️ العام", value="1447هـ")
            nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
            
            if st.form_submit_button("✅ اعتماد التأسيس"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"])
                    st.success("تم التأسيس بنجاح"); st.rerun()

    # --- القسم الثاني: شاشة الدرجات (تم إصلاح الخطأ هنا) ---
    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            
            with st.form("grade_pro_form"):
                st.markdown(f"**تحديث درجات الطالب: {target}**")
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("📉 الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                
                if st.form_submit_button("💾 حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except:
                        ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ"); st.rerun()

        st.divider()
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    # --- باقي الأقسام تتبع نفس الهيكل ---
# --- القسم الثالث: رصد السلوك (إصدار الجوال والحاسوب المطور) ---
    elif menu == "🎭 رصد السلوك":
        import urllib.parse  # حل مشكلة علامات الاستفهام
        
        st.markdown("""
            <div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
                <h1 style="margin:0;">🎭 رصد السلوك والتواصل الفوري</h1>
                <p style="margin:5px 0 0 0; opacity: 0.8;">منصة الأستاذ زياد الذكية</p>
            </div>
        """, unsafe_allow_html=True)

        df_st = fetch_safe("students")
        
        # --- محرك البحث الذكي (متوافق مع الجوال) ---
        st.markdown('<div style="background-color: #fffbeb; padding: 10px; border-radius: 10px; border: 1px solid #fcd34d; margin-bottom: 15px;">', unsafe_allow_html=True)
        
        # 1. مربع نصي يفتح لوحة مفاتيح الجوال فوراً للبحث
        search_term = st.text_input("🔍 ابحث عن اسم الطالب (اكتب هنا)", placeholder="اكتب اسم الطالب للفلترة...")

        # 2. تصفية القائمة بناءً على البحث
        all_names = df_st.iloc[:, 1].tolist()
        if search_term:
            filtered_names = [name for name in all_names if search_term in name]
        else:
            filtered_names = all_names

        # 3. اختيار الاسم من القائمة المفلترة
        b_name = st.selectbox(
            "🎯 اختر الطالب المطلوب:", 
            [""] + filtered_names,
            help="إذا كتبت في المربع أعلاه، ستظهر هنا الأسماء المطابقة فقط"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if b_name:
            # جلب البيانات (العمود G للإيميل والعمود H للجوال)
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6] 
            s_phone = str(student_info[7]).split('.')[0] # تنظيف الرقم لضمان فتح الواتساب
            
            with st.container(border=True):
                with st.form("behavior_mobile_friendly_v14", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    b_type = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                    b_date = c2.date_input("📅 التاريخ")
                    b_note = st.text_area("📝 نص الملاحظة السلوكية")
                    
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    btn_save = col1.form_submit_button("💾 رصد وحفظ فقط")
                    btn_mail = col2.form_submit_button("📧 رصد وإيميل منظم")
                    btn_wa = col3.form_submit_button("💬 رصد وواتساب منظم")

                    if btn_save or btn_mail or btn_wa:
                        if b_note:
                            # 1. الحفظ وتحديث النقاط
                            sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                            try:
                                ws_st = sh.worksheet("students")
                                cell = ws_st.find(b_name)
                                p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                                current_p = int(ws_st.cell(cell.row, 9).value or 0)
                                ws_st.update_cell(cell.row, 9, str(current_p + p_map.get(b_type, 0)))
                            except: pass

                            # 2. نص الرسالة المنسق والاحترافي
                            full_msg = (
                                f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\n"
                                f"----------------------------------------\n"
                                f"🏷️ نوع السلوك: {b_type}\n"
                                f"📝 الملاحظة: {b_note}\n"
                                f"📅 التاريخ: {b_date}\n"
                                f"----------------------------------------\n"
                                f"🏛️ منصة الأستاذ زياد الذكية"
                            )
                            
                            # 3. إرسال الإيميل
                            if btn_mail and s_email:
                                mail_url = f"mailto:{s_email}?subject=تقرير سلوك: {b_name}&body={urllib.parse.quote(full_msg)}"
                                st.markdown(f'<meta http-equiv="refresh" content="0;url={mail_url}">', unsafe_allow_html=True)
                            
                            # 4. إرسال الواتساب (حل نهائي للرموز)
                            if btn_wa and s_phone:
                                encoded_msg = urllib.parse.quote(full_msg)
                                wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={encoded_msg}"
                                st.markdown(f"""
                                    <div style="background-color: #f0fff4; border: 1px solid #25D366; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px;">
                                        <p style="color: #2c3e50; font-weight: bold;">✅ تم الحفظ بنجاح</p>
                                        <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                                            <div style="background-color: #25D366; color: white; padding: 12px 25px; display: inline-block; border-radius: 5px; font-weight: bold;">
                                                💬 إرسال التقرير عبر واتساب
                                            </div>
                                        </a>
                                    </div>
                                """, unsafe_allow_html=True)

                            if btn_save:
                                st.success("✅ تم حفظ الملاحظة بنجاح")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("⚠️ يرجى كتابة نص الملاحظة")

            # عرض السجل التاريخي
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                st_history = df_b[df_b.iloc[:, 0] == b_name]
                st.dataframe(st_history.iloc[::-1, :4], use_container_width=True, hide_index=True)
   # --- القسم الرابع: شاشة الاختبارات (إصدار البحث الذكي للجوال) ---
   # --- القسم الرابع: شاشة التنبيهات والإعلانات (مع ميزة الحذف) ---
    elif menu == "📢 شاشة الاختبارات":
        st.markdown("""
            <div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
                <h1 style="margin:0;">📢 مركز التنبيهات والإعلانات</h1>
                <p style="margin:5px 0 0 0; opacity: 0.8;">إضافة وحذف مواعيد الاختبارات والنشاطات</p>
            </div>
        """, unsafe_allow_html=True)

        # 1. نموذج إضافة تنبيه جديد
        with st.expander("➕ إضافة تنبيه أو موعد جديد", expanded=True):
            with st.form("announcement_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                a_title = c2.text_input("📝 عنوان التنبيه", placeholder="مثال: اختبار لغتي الفصل الأول")
                a_date = c3.date_input("📅 الموعد")
                
                btn_post = st.form_submit_button("🚀 نشر التنبيه الآن")
                
                if btn_post:
                    if a_title:
                        try:
                            # الحفظ في جدول 'exams' حسب الترتيب الجديد
                            sh.worksheet("exams").append_row([a_class, a_title, str(a_date)])
                            st.success("✅ تم نشر التنبيه بنجاح")
                            time.sleep(1)
                            st.rerun()
                        except:
                            st.error("⚠️ تأكد من وجود ورقة 'exams' في ملفك")
                    else:
                        st.warning("⚠️ يرجى كتابة عنوان للتنبيه")

        # 2. عرض التنبيهات الحالية مع ميزة الحذف
        st.markdown("### 📋 التنبيهات المنشورة حالياً")
        df_ann = fetch_safe("exams")
        
        if not df_ann.empty:
            # عرض كل تنبيه في بطاقة منفصلة مع زر حذف
            for index, row in df_ann.iterrows():
                with st.container(border=True):
                    col_text, col_btn = st.columns([4, 1])
                    
                    with col_text:
                        st.markdown(f"**[{row[0]}]** - {row[1]}")
                        st.caption(f"📅 الموعد: {row[2]}")
                    
                    with col_btn:
                        # زر الحذف (يستخدم رقم الصف في جوجل شيت)
                        if st.button(f"🗑️ حذف", key=f"del_{index}"):
                            try:
                                ws_exam = sh.worksheet("exams")
                                # +2 لأن الفهرس يبدأ من 0 وهناك صف عناوين في جوجل شيت
                                ws_exam.delete_rows(index + 2)
                                st.toast(f"تم حذف: {row[1]}")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"فشل الحذف: {e}")
        else:
            st.info("📭 لا توجد تنبيهات منشورة حالياً")
# ==========================================
# 👨‍🎓 واجهة الطالب (تصميم احترافي وفعال)
# ==========================================
# --- شاشة الطالب (مستقلة تماماً لمنع الأخطاء) ---
if st.session_state.role == "student":
    # 1. جلب البيانات الأساسية
    df_st = fetch_safe("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid]
    
    if not s_data.empty:
        s_row = s_data.iloc[0]
        s_name = s_row.iloc[1]
        s_email = s_row.iloc[7]
        s_phone = s_row.iloc[8]
        s_points = s_row.iloc[9]
        s_class = s_row.iloc[2]

        # 2. قسم الإعلانات (أعلى الشاشة - وضوح تام للجوال)
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            my_ex = df_ex[(df_ex.iloc[:, 2] == s_class) | (df_ex.iloc[:, 2] == "الكل")]
            for _, ex in my_ex.iterrows():
                st.warning(f"🔔 **إعلان هام:** {ex.iloc[1]} \n\n 📅 التاريخ: {ex.iloc[0]}")

        # 3. واجهة الهوية والأوسمة (تصميم عمودي للجوال)
        st.markdown(f"""
            <div style="text-align: center; background-color: #ffffff; padding: 15px; border-radius: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); border-top: 5px solid #1E3A8A; margin-top: 10px;">
                <h3 style="color: #1E3A8A; margin-bottom: 5px;">مرحباً: {s_name}</h3>
                <p style="font-size: 13px; color: #666;">📧 {s_email} | 📱 {s_phone}</p>
                <div style="display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #eee; padding-top: 10px;">
                    <div style="text-align: center;">
                        <div style="font-size: 35px;">🏆</div>
                        <div style="font-weight: bold; color: #1E3A8A; font-size: 18px;">{s_points}</div>
                        <div style="font-size: 11px; color: #888;">نقطة</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 35px;">🥇</div>
                        <div style="font-weight: bold; color: #1E3A8A; font-size: 18px;">متميز</div>
                        <div style="font-size: 11px; color: #888;">وسام</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("") 

        # 4. التبويبات (النتائج والملاحظات)
        # تم استخدام metric بدلاً من جداول لمنع أخطاء DeltaGenerator
        t1, t2 = st.tabs(["📊 نتيجتي الدراسية", "🎭 سجل ملاحظاتي"])
        
        with t1:
            df_g = fetch_safe("grades")
            if not df_g.empty:
                my_g = df_g[df_g.iloc[:, 0] == s_name]
                if not my_g.empty:
                    st.metric("الفترة الأولى", f"{my_g.iloc[0, 1]}")
                    st.metric("الفترة الثانية", f"{my_g.iloc[0, 2]}")
                    st.metric("درجة المشاركة", f"{my_g.iloc[0, 3]}")
                else:
                    st.info("لا توجد درجات مرصودة حالياً.")

        with t2:
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                my_b = df_b[df_b.iloc[:, 0] == s_name]
                if not my_b.empty:
                    for _, row in my_b.iterrows():
                        # استخدام expander لسهولة القراءة من الجوال
                        with st.expander(f"🗓️ {row.iloc[1]} | {row.iloc[2]}", expanded=True):
                            st.info(f"📝 {row.iloc[3]}")
                else:
                    st.info("سجلك السلوكي نظيف.")

    # زر الخروج في أسفل القائمة الجانبية بعيداً عن كود الشاشة
    st.sidebar.markdown("---")
    st.sidebar.button("🚗 تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
