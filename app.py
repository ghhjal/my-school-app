# --- (القسم الأول: المكتبات والربط والوظائف تظل كما هي تماماً لضمان الاستقرار) ---
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

def send_email_alert(student_name, parent_email, behavior_type, note):
    try:
        sender_email = st.secrets["email_settings"]["sender_email"]
        sender_password = st.secrets["email_settings"]["sender_password"]
        subject = f"🔔 إشعار سلوكي: {student_name}"
        body = f"تحية طيبة،\nتم رصد ملاحظة سلوكية جديدة لابننا: {student_name}\nالنوع: {behavior_type}\nالملاحظة: {note}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}\n\nمع تحيات الأستاذ زياد المعمري."
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = parent_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, parent_email, msg.as_string())
        return True
    except:
        return False

# --- 2. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("كلمة المرور خاطئة")
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(sid)
                st.rerun()
            else:
                st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# --- 3. واجهة المعلم (تظل ثابتة ومستقرة تماماً) ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])
    df_st = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        st.divider()
        col_del, col_add = st.columns([1, 2])
        with col_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.error(f"تم حذف {to_del} من جميع السجلات"); time.sleep(1); st.rerun()
        with col_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                id_v = c1.text_input("الرقم الأكاديمي")
                name_v = c2.text_input("اسم الطالب")
                c3, c4, c5 = st.columns(3)
                cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = c4.text_input("العام", value="1447هـ")
                sub_v = c5.text_input("المادة", value="اللغة الإنجليزية")
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة بنجاح ✅"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with tab1:
            st.subheader("📝 رصد وتعديل الدرجات")
            target = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist())
            if target:
                with st.form("g_form"):
                    c1, c2, c3 = st.columns(3)
                    v1 = c1.number_input("درجة ف1 (p1)", min_value=0, max_value=100)
                    v2 = c2.number_input("درجة ف2 (p2)", min_value=0, max_value=100)
                    v3 = c3.number_input("المشاركة (perf)", min_value=0, max_value=100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            fnd = ws_g.find(target); ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                        except:
                            ws_g.append_row([target, v1, v2, v3])
                        st.success(f"تم تحديث درجات {target} ✅")
            st.dataframe(fetch_data("grades"), use_container_width=True, hide_index=True)
        with tab2:
            st.subheader("🎭 رصد السلوك والتحفيز")
            sel_st = st.selectbox("اسم الطالب للسلوك", [""] + df_st['name'].tolist())
            if sel_st:
                st_info = df_st[df_st['name'] == sel_st].iloc[0]
                target_email = st_info.get('الإيميل', '')
                with st.form("b_form", clear_on_submit=True):
                    d_v = st.date_input("التاريخ", datetime.now())
                    t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    n_v = st.text_input("ملاحظة السلوك")
                    if st.form_submit_button("حفظ وإرسال إيميل"):
                        pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                        sh.worksheet("behavior").append_row([sel_st, str(d_v), t_v, n_v])
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                        old_pts = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_pts + pts)
                        if target_email and "@" in str(target_email):
                            send_email_alert(sel_st, target_email, t_v, n_v)
                        st.success("تم الحفظ وتحديث النقاط ✅"); time.sleep(1); st.rerun()
               st.divider()
                st.subheader(f"📜 سجل ملاحظات الطالب: {sel_st}")
                df_bh_teacher = fetch_data("behavior")
                
                if not df_bh_teacher.empty:
                    # تنظيف أسماء الأعمدة وفلترة الطالب
                    my_bh_teacher = df_bh_teacher[df_bh_teacher['student_id'] == sel_st].copy()
                    my_bh_teacher = my_bh_teacher.iloc[::-1] # الأحدث أولاً
                    
                    for index, row in my_bh_teacher.iterrows():
                        status = str(row.get('الحالة', 'لم تُقرأ بعد'))
                        
                        # تحديد ألوان واضحة جداً للجوال
                        is_read = "تمت القراءة" in status
                        bg_c = "#E8F5E9" if is_read else "#FFEBEE"
                        txt_c = "#1B5E20" if is_read else "#B71C1C"
                        lbl = "✅ قرأها الطالب" if is_read else "🕒 لم تُقرأ بعد"

                        st.markdown(f"""
                            <div style="background-color: {bg_c}; padding: 12px; border-radius: 12px; 
                                        border: 2px solid {txt_c}; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <b style="color: {txt_c}; font-size: 1em;">{lbl}</b>
                                    <small style="color: #212121; font-weight: bold;">📅 {row.get('التاريخ', '---')}</small>
                                </div>
                                <div style="margin-top: 8px; color: #1a1a1a; font-weight: 500;">
                                    <p style="margin:0;"><b>نوع السلوك:</b> {row.get('النوع', 'عام')}</p>
                                    <p style="margin:5px 0 0 0;"><b>💬 الملاحظة:</b> {row.get('ملاحظة', 'لا يوجد نص')}</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد ملاحظات مسجلة لهذا الطالب.")
    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 إدارة إعلانات المواعيد")
        df_ex = fetch_data("exams")
        col_add, col_del = st.columns([2, 1])
        with col_add:
            st.subheader("📝 نشر إعلان جديد")
            with st.form("ex_form", clear_on_submit=True):
                e_cls = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                e_ttl = st.text_input("موضوع الاختبار")
                e_dt = st.date_input("الموعد")
                if st.form_submit_button("نشر الإعلان"):
                    sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                    st.success("تم النشر بنجاح ✅"); time.sleep(1); st.rerun()
        with col_del:
            st.subheader("🗑️ حذف إعلان")
            if not df_ex.empty:
                titles = df_ex['العنوان'].tolist()
                to_delete = st.selectbox("اختر الإعلان لحذفه", [""] + titles)
                if st.button("تأكيد الحذف"):
                    if to_delete:
                        ws_ex = sh.worksheet("exams"); cell = ws_ex.find(to_delete)
                        if cell: ws_ex.delete_rows(cell.row); st.error(f"تم حذف إعلان: {to_delete}"); time.sleep(1); st.rerun()
            else: st.info("لا توجد إعلانات حالياً")

# --- 4. واجهة الطالب المطورة (نسخة المتعة البصرية الفائقة) ---
elif st.session_state.role == "student":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    # 🔔 شريط التنبيهات بتصميم محسن للجوال
    df_ex = fetch_data("exams")
    if not df_ex.empty:
        my_ex = df_ex[df_ex['الصف'] == s_data.get('class', '')]
        for _, r in my_ex.iterrows():
            st.markdown(f"""<div style="background:#fff3cd; padding:12px; border-right:6px solid #ffc107; 
                border-radius:10px; margin-bottom:8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <strong style="color: #856404; font-size: 0.9em; display: block;">🔔 موعد اختبار: {r.get('العنوان', '')}</strong>
                <span style="color: #533f03; font-size: 0.85em;">📅 التاريخ: {r.get('التاريخ', '')}</span>
                </div>""", unsafe_allow_html=True)

    # 👤 الترويسة العلوية المحسنة
    st.markdown(f"<h2 style='text-align:center; color:#42A5F5; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>🌟 أهلاً بك يا بطل: {s_data['name']}</h2>", unsafe_allow_html=True)

    # 🏆 لوحة المؤشرات (إصلاح مشكلة بهتان الخط)
    pts = int(s_data.get('النقاط', 0))
    medal = "🏆 بطل التحدي" if pts >= 100 else "🥇 وسام ذهبي" if pts >= 50 else "🥈 وسام فضي" if pts >= 20 else "🥉 وسام برونزي"
    
    c_pts1, c_pts2 = st.columns(2)
    # 🏆 لوحة المؤشرات العلوية - تعديل التنسيق فقط للوضوح على الجوال
    with c_pts1:
        st.markdown(f"""<div style="background:#e3f2fd; padding:15px; border-radius:15px; text-align:center; border:2px solid #2196F3;">
            <p style="margin:0; color:#0d47a1; font-weight:bold; font-size:1.1em;">رصيد نقاطك</p>
            <h2 style="margin:0; color:#0d47a1; text-shadow: none;">⭐ {pts}</h2></div>""", unsafe_allow_html=True)
            
    with c_pts2:
        st.markdown(f"""<div style="background:#f1f8e9; padding:15px; border-radius:15px; text-align:center; border:2px solid #4CAF50;">
            <p style="margin:0; color:#1b5e20; font-weight:bold; font-size:1.1em;">لقبك الحالي</p>
            <h2 style="margin:0; color:#1b5e20; text-shadow: none;">{medal}</h2></div>""", unsafe_allow_html=True)

    st.divider()

    # --- التبويبات الجديدة ---
    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سجل السلوك", "⚙️ بياناتي"])
    
    with t1:
        st.markdown("### 📝 درجاتي")
        df_g = fetch_data("grades")
        my_g = df_g[df_g['student_id'] == s_data['name']]
        if not my_g.empty:
            g = my_g.iloc[0]
            # عرض الدرجات كبطاقات ملونة لمنع تكرار الجدول
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("فترة 1", g.get('p1', 0))
            col_b.metric("فترة 2", g.get('p2', 0))
            col_c.metric("المشاركة", g.get('perf', 0))
        else:
            st.info("لا توجد درجات مرصودة حالياً.")

    with t2:
        st.markdown("### 📜 سجل رحلتي السلوكية")
        df_bh = fetch_data("behavior")
        
        if not df_bh.empty:
            # 1. تنظيف شامل للبيانات وفلترة الطالب
            my_bh = df_bh[df_bh.iloc[:, 0].astype(str) == s_data['name']].copy()
            
            if not my_bh.empty:
                # 2. الترتيب من الأحدث للأقدم عبر عكس المصفوفة (تجنباً لخطأ التاريخ)
                my_bh = my_bh.iloc[::-1] 
                
                for index, row in my_bh.iterrows():
                    # 3. جلب البيانات حسب موقع العمود وليس اسمه (لضمان النجاح)
                    # نفترض: العمود 1=النوع، العمود 2=الملاحظة، العمود 3=التاريخ
                    bh_type = str(row.iloc[1]) if len(row) > 1 else "ملاحظة"
                    note_text = str(row.iloc[2]) if len(row) > 2 else "استمر في تألقك!"
                    date_val = str(row.iloc[3]) if len(row) > 3 else "---"

                    # 4. نظام تلوين ذكي (يفحص محتوى النص)
                    if any(word in bh_type for word in ["⭐", "متميز"]):
                        color, bg, icon = "#1B5E20", "#E8F5E9", "🏆"
                    elif any(word in bh_type for word in ["✅", "إيجابي"]):
                        color, bg, icon = "#2E7D32", "#F1F8E9", "🌟"
                    elif any(word in bh_type for word in ["⚠️", "تنبيه"]):
                        color, bg, icon = "#E65100", "#FFF3E0", "📢"
                    elif any(word in bh_type for word in ["❌", "سلبي"]):
                        color, bg, icon = "#B71C1C", "#FFEBEE", "🚫"
                    else:
                        color, bg, icon = "#0D47A1", "#E3F2FD", "📝"

                    # 5. عرض البطاقة بتصميم جذاب ومنظم
                    st.markdown(f"""
                        <div style="background-color: {bg}; padding: 15px; border-radius: 12px; 
                                    border-right: 10px solid {color}; margin-bottom: 10px; 
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between;">
                                <b style="color: {color}; font-size: 1.1em;">{icon} {bh_type}</b>
                                <small style="color: #666;">📅 {date_val}</small>
                            </div>
                            <div style="margin-top: 8px; color: #333; background: rgba(255,255,255,0.5); padding: 8px; border-radius: 8px;">
                                <b>💬 الملاحظة:</b> {note_text}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # زر الشكر التفاعلي مع إشعار للمعلم
                    if st.button(f"🙏 شكراً أستاذي", key=f"btn_thanks_{index}"):
                        try:
                            # تحديث حالة القراءة في جوجل شيت
                            # index + 2 للوصول للصف الصحيح في الشيت
                            sh_behavior.update_cell(index + 2, 5, "✅ تمت القراءة")
                            
                            st.balloons() # احتفال للطالب
                            st.toast("وصل شكرك للأستاذ زياد! 🌸")
                        except:
                            st.toast("شكراً لك يا بطل! استمر في تميزك")
                            
                            st.balloons() # احتفال للطالب
                            st.toast("تم إرسال تقديرك للمعلم زياد! 🌸") # تأكيد فوري
                        except:
                            st.toast("شكراً لك يا بطل!")
            else:
                st.info("سجلك السلوكي نظيف يا بطل! ✨")
    with t3:
        st.subheader("⚙️ تحديث البريد والجوال")
        with st.form("update_info"):
            new_mail = st.text_input("إيميل ولي الأمر", value=str(s_data.get('الإيميل', '')))
            new_phone = st.text_input("رقم الجوال", value=str(s_data.get('الجوال', '')))
            if st.form_submit_button("حفظ البيانات"):
                ws = sh.worksheet("students")
                cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail)
                ws.update_cell(cell.row, 8, new_phone)
                st.success("تم التحديث ✅"); time.sleep(1); st.rerun()
