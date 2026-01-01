import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة والتصميم العام (Logo & Header)
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
        padding: 35px; border-radius: 0 0 35px 35px; color: white; text-align: center; 
        margin: -65px -20px 25px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); 
    }
    .logo-box { 
        background: rgba(255, 255, 255, 0.2); width: 65px; height: 65px; border-radius: 18px; 
        margin: 0 auto 10px auto; display: flex; justify-content: center; align-items: center; 
        border: 1px solid rgba(255, 255, 255, 0.3); 
    }
    .logo-box i { font-size: 32px; color: white; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; }
    </style>
    <div class="header-box">
        <div class="logo-box"><i class="bi bi-graph-up-arrow"></i></div>
        <h1 style="margin:0; font-size: 24px;">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.8; font-size: 14px;">نظام الإدارة المدرسية المتكامل</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال والبيانات
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        
        # تحويل البيانات إلى DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # 1. حذف الأعمدة التي ليس لها اسم (تظهر كأعمدة فارغة في الإكسل)
        df = df.loc[:, df.columns != '']
        
        # 2. التعامل مع الأسماء المكررة إن وجدت بإضافة رقم بجانبها
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                cols[i] = f"{col}_{i}"
        df.columns = cols
        
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات من {worksheet_name}: {e}")
        return pd.DataFrame()

# 3. نظام الجلسات والتحقق
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.sid = None  # لتخزين رقم الطالب الحالي

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        sid_input = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية")
        if st.button("دخول الطالب 🚀"):
            df_st = fetch_safe("students")
            if not df_st.empty:
                df_st['id'] = df_st['id'].astype(str).str.strip()
                match = df_st[df_st['id'] == str(sid_input).strip()]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid_input).strip()
                    st.rerun()
                else: st.error("❌ عذراً، رقم الهوية غير مسجل")

    with tab2:
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم 🔐"):
            u_df = fetch_safe("users")
            if not u_df.empty:
                user_row = u_df[u_df['username'] == u_name.strip()]
                if not user_row.empty:
                    hashed = hashlib.sha256(str.encode(u_pass)).hexdigest()
                    if hashed == user_row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"
                        st.rerun()
                    else: st.error("❌ كلمة المرور خطأ")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (كودك الأصلي)
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
   # --- القسم الرابع: شاشة التنبيهات (الإصدار المصحح والمنظم) ---

   # --- القسم الرابع: شاشة التنبيهات (الإصدار المصحح والمنظم) ---
    elif menu == "📢 شاشة الاختبارات":
        import urllib.parse
        st.markdown("""
            <div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
                <h1 style="margin:0;">📢 مركز التنبيهات والإعلانات</h1>
                <p style="margin:5px 0 0 0; opacity: 0.8;">إدارة المواعيد والتواصل الفوري - الأستاذ زياد</p>
            </div>
        """, unsafe_allow_html=True)

        # 1. نموذج الإضافة الصامت
        with st.expander("➕ إضافة تنبيه أو موعد جديد", expanded=True):
            with st.form("announcement_form_wa_v6", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                a_title = c2.text_input("📝 عنوان التنبيه")
                a_date = c3.date_input("📅 الموعد")
                
                btn_post = st.form_submit_button("🚀 نشر التنبيه الآن")
                
                if btn_post and a_title:
                    try:
                        sh.worksheet("exams").append_row([a_class, a_title, str(a_date)])
                        st.balloons()
                        time.sleep(0.5)
                        st.rerun()
                    except:
                        pass

        st.markdown("### 📋 التنبيهات المنشورة (الأحدث أولاً)")
        df_ann = fetch_safe("exams")
        
        if df_ann is not None and not df_ann.empty:
            reversed_df = df_ann.iloc[::-1]
            color_map = {
                "الكل": "#E0F2FE", "الأول": "#F0FDF4", "الثاني": "#FFF7ED", 
                "الثالث": "#FAF5FF", "الرابع": "#FEF2F2", "الخامس": "#F5F3FF", "السادس": "#ECFEFF"
            }

            for index, row in reversed_df.iterrows():
                bg_color = color_map.get(row[0], "#FFFFFF")
                
                # نص الرسالة المنسق للواتساب
                wa_msg = (
                    f"📢 *تنبيه من منصة الأستاذ زياد الذكية*\n"
                    f"----------------------------------\n"
                    f"🏫 *الصف:* {row[0]}\n"
                    f"📝 *الموضوع:* {row[1]}\n"
                    f"📅 *الموعد:* {row[2]}\n"
                    f"----------------------------------\n"
                    f"يرجى العلم والاستعداد. مع تمنياتي لكم بالتوفيق 🌟"
                )
                encoded_msg = urllib.parse.quote(wa_msg)
                wa_url = f"https://api.whatsapp.com/send?text={encoded_msg}"

                # عرض البطاقة الملونة
                st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-right: 5px solid #4F46E5; margin-bottom: 5px;">
                        <span style="color: #4F46E5; font-weight: bold;">[{row[0]}]</span> 
                        <span style="font-size: 1.1em; margin-right: 10px;">{row[1]}</span>
                        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">📅 الموعد: {row[2]}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # أزرار التحكم (واتساب وحذف)
                col1, col2, col_empty = st.columns([1.5, 1, 3])
                with col1:
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:5px 10px; border-radius:5px; text-align:center; font-size:14px; font-weight:bold;">💬 واتساب</div></a>', unsafe_allow_html=True)
                with col2:
                    if st.button(f"🗑️ حذف", key=f"del_wa_{index}"):
                        try:
                            ws_exam = sh.worksheet("exams")
                            ws_exam.delete_rows(int(index) + 2)
                            st.rerun()
                        except:
                            pass
        else:
            st.info("📭 لا توجد تنبيهات منشورة حالياً")


# ==========================================
# 👨‍🎓 واجهة الطالب (تم تصحيح جلب النقاط فقط)
# ==========================================
elif st.session_state.role == "student":
    # 1. جلب البيانات من الجداول (students & grades)
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name, s_class = s_row[1], s_row[2]
    
   # جلب النقاط السلوكية من العمود التاسع (I) والذي يحمل رقم 8 برمجياً
    try:
        # قمنا بتحويل القيمة لنص ثم تنظيفها ثم تحويلها لرقم لضمان عمل الأوسمة
        raw_val = str(s_row[8]).strip() if len(s_row) > 8 else "0"
        s_points = int(float(raw_val)) if raw_val and raw_val != "None" else 0
    except:
        s_points = 0
    # --------------------------------------------------------

    # جلب الدرجات الأكاديمية من ورقة grades
    try:
        g_row = df_grades[df_grades.iloc[:, 0].astype(str) == s_name].iloc[0]
        p1, p2, perf = g_row[1], g_row[2], g_row[3]
    except:
        p1, p2, perf = "-", "-", "-"

    # --- 📢 شريط الإعلانات العلوي ---
    st.markdown(f"""
        <div style="background: #1e3a8a; padding: 12px; margin: -1rem -1rem 1rem -1rem; border-bottom: 5px solid #f59e0b; text-align: center;">
            <h3 style="color: white; margin: 0; font-family: 'Cairo', sans-serif;">🎯 لوحة إنجاز الطالب: {s_name}</h3>
        </div>
    """, unsafe_allow_html=True)

    # --- 👤 بطاقة الأوسمة والنقاط ---
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="border: 3px solid #cd7f32; padding: 10px; border-radius: 15px; width: 30%; background: #fffcf9; opacity: {'1' if s_points >= 10 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥉</div><div style="font-weight: bold; color: #cd7f32; font-size: 0.8rem;">برونزي</div>
                </div>
                <div style="border: 3px solid #c0c0c0; padding: 10px; border-radius: 15px; width: 30%; background: #f8f9fa; opacity: {'1' if s_points >= 50 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥈</div><div style="font-weight: bold; color: #7f8c8d; font-size: 0.8rem;">فضي</div>
                </div>
                <div style="border: 3px solid #ffd700; padding: 10px; border-radius: 15px; width: 30%; background: #fffdf0; opacity: {'1' if s_points >= 100 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥇</div><div style="font-weight: bold; color: #d4af37; font-size: 0.8rem;">ذهبي</div>
                </div>
            </div>
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px;">
                <small style="font-size: 1rem;">رصيد النقاط السلوكية</small><br>
                <b style="font-size: 2.5rem;">{s_points}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات الرئيسية ---
    t_ex, t_grade, t_beh, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "⚙️ الإعدادات"])

    with t_ex:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.markdown(f"""
                    <div style="background: #002347; padding: 15px; border-radius: 12px; border-right: 8px solid #f59e0b; margin-bottom: 10px;">
                        <b style="color: #ffd700; font-size: 1.1rem;">📢 {r[1]}</b><br>
                        <span style="color: white; font-size: 0.9rem;">📅 الموعد: {r[2]}</span>
                    </div>
                """, unsafe_allow_html=True)

    with t_grade:
        st.markdown(f"""<h4 style="text-align:right; color:#1e3a8a; margin-top:10px;">📊 سجل الدرجات (p1, p2, perf)</h4>""", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">درجة المشاركة (p1)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{p1}</b>
                </div>
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">درجة الواجبات (p2)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{p2}</b>
                </div>
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">الاختبارات القصيرة (perf)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{perf}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with t_beh:
        st.markdown(f"""<h4 style="text-align:right; color:#1e3a8a; margin-top:10px;">🎭 ملاحظات السلوك والانضباط</h4>""", unsafe_allow_html=True)
        df_beh = fetch_safe("behavior")
        if not df_beh.empty:
            f_beh = df_beh[df_beh.iloc[:, 0] == s_name]
            for _, r in f_beh.iloc[::-1].iterrows():
                is_pos = "+" in str(r[2])
                bg = "#f0fdf4" if is_pos else "#fef2f2"
                text_color = "#166534" if is_pos else "#991b1b"
                icon = "✅" if is_pos else "⚠️"
                
                st.markdown(f"""
                    <div style="background: {bg}; padding: 15px; border-radius: 12px; border: 1px solid {text_color}44; border-right: 8px solid {text_color}; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b style="color: {text_color};">{icon} {r[2]}</b>
                            <small style="color: #64748b;">{r[1]}</small>
                        </div>
                        <div style="margin-top: 5px; color: #475569; font-size: 0.95rem;">{r[3]}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("سجلك السلوكي نظيف حالياً")

    with t_set:
        with st.form("st_settings_final"):
            new_mail = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            new_phone = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ البيانات", use_container_width=True):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail); ws.update_cell(cell.row, 8, new_phone)
                st.success("تم التحديث بنجاح!"); st.rerun()
        if st.button("🚗 تسجيل الخروج", use_container_width=True):
            st.session_state.role = None; st.rerun()
