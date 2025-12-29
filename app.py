# --- (القسم الأول: المكتبات والربط والوظائف) ---
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
            else: st.error("كلمة المرور خاطئة")
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty:
                id_col = df_st.columns[0]
                if str(sid_input) in df_st[id_col].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid_input)
                    st.rerun()
                else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# --- 3. واجهة المعلم (بكامل المميزات) ---
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
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            if name_col:
                to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st[name_col].tolist())
                if st.button("تأكيد الحذف الشامل"):
                    if to_del:
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s); cell = ws.find(to_del)
                                if cell: ws.delete_rows(cell.row)
                            except: pass
                        st.success(f"تم حذف {to_del} بنجاح"); time.sleep(1); st.rerun()
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
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            target = st.selectbox("اختر الطالب", [""] + df_st[name_col].tolist())
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
                        except: ws_g.append_row([target, v1, v2, v3])
                        st.success(f"تم تحديث درجات {target} ✅")
            st.dataframe(fetch_data("grades"), use_container_width=True, hide_index=True)
        
        with tab2:
            st.subheader("🎭 رصد السلوك والتحفيز")
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            sel_st = st.selectbox("اسم الطالب للسلوك", [""] + df_st[name_col].tolist())
            if sel_st:
                st_info = df_st[df_st[name_col] == sel_st].iloc[0]
                email_col = next((c for c in df_st.columns if 'إيميل' in str(c) or 'Email' in str(c)), "")
                target_email = st_info.get(email_col, '') if email_col else ""
                with st.form("b_form", clear_on_submit=True):
                    d_v = st.date_input("التاريخ", datetime.now())
                    t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    n_v = st.text_input("ملاحظة السلوك")
                    if st.form_submit_button("حفظ وإرسال إيميل"):
                        pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                        sh.worksheet("behavior").append_row([sel_st, str(d_v), t_v, n_v, "🕒 لم تُقرأ بعد"])
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                        old_pts = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_pts + pts)
                        if target_email and "@" in str(target_email):
                            send_email_alert(sel_st, target_email, t_v, n_v)
                        st.success("تم الحفظ ✅"); time.sleep(1); st.rerun()

                st.divider()
                st.subheader(f"📜 سجل ملاحظات الطالب: {sel_st}")
                df_bh_teacher = fetch_data("behavior")
                if not df_bh_teacher.empty:
                    my_bh_teacher = df_bh_teacher[df_bh_teacher.iloc[:, 0] == sel_st].iloc[::-1]
                    for idx, row in my_bh_teacher.iterrows():
                        status = str(row.iloc[4]) if len(row) > 4 else "🕒 لم تُقرأ بعد"
                        is_read = "تمت القراءة" in status
                        bg_c = "#E8F5E9" if is_read else "#FFEBEE"
                        txt_c = "#1B5E20" if is_read else "#B71C1C"
                        st.markdown(f"<div style='background-color:{bg_c}; padding:10px; border-radius:10px; border:1px solid {txt_c}; margin-bottom:5px;'><b>{status}</b> | 📅 {row.iloc[1]} | {row.iloc[2]}: {row.iloc[3]}</div>", unsafe_allow_html=True)

    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 إدارة إعلانات المواعيد")
        df_ex = fetch_data("exams")
        st.dataframe(df_ex, use_container_width=True, hide_index=True)
        with st.form("ex_form", clear_on_submit=True):
            e_cls = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = st.text_input("موضوع الاختبار")
            e_dt = st.date_input("الموعد")
            if st.form_submit_button("نشر موعد"):
                sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                st.success("تم النشر بنجاح ✅"); time.sleep(1); st.rerun()

# --- 4. واجهة الطالب (مع إصلاح زر الشكر) ---
elif st.session_state.role == "student":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    id_col = df_st.columns[0]
    s_data = df_st[df_st[id_col].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]
    
    st.markdown(f"<h2 style='text-align:center;'>🌟 أهلاً بك يا بطل: {s_name}</h2>", unsafe_allow_html=True)
    
    pts = int(s_data.iloc[8] or 0)
    medal = "🏆 بطل التحدي" if pts >= 100 else "🥇 وسام ذهبي" if pts >= 50 else "🥈 وسام فضي" if pts >= 20 else "🥉 وسام برونزي"
    c1, c2 = st.columns(2)
    c1.metric("رصيد نقاطك ⭐", pts)
    c2.metric("لقبك الحالي 🏆", medal)

    st.divider()
    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سجل السلوك", "⚙️ بياناتي"])
    
    with t1:
        st.subheader("📊 درجاتي")
        df_g = fetch_data("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                g = my_g.iloc[0]
                ca, cb, cc = st.columns(3)
                ca.metric("فترة 1", g.iloc[1]); cb.metric("فترة 2", g.iloc[2]); cc.metric("المشاركة", g.iloc[3])
            else: st.info("الدرجات لم ترفع بعد")
        else: st.info("لا توجد بيانات")

    with t2:
        st.subheader("🎭 سجل ملاحظات السلوك")
        df_bh = fetch_data("behavior")
        if not df_bh.empty:
            my_bh = df_bh[df_bh.iloc[:, 0] == s_name].copy().iloc[::-1]
            sh_bh = sh.worksheet("behavior")
            
            for idx, row in my_bh.iterrows():
                dt, bh_type, note = str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3])
                status = str(row.iloc[4]) if len(row) > 4 else "لم تُقرأ بعد"
                is_read = "تمت القراءة" in status
                
                # إنشاء مفتاح فريد جداً للزر لضمان عدم حدوث تداخل
                btn_key = f"thx_{s_name}_{dt}_{idx}"
                
                bg = "#E8F5E9" if is_read else "#FFF3E0"
                border = "#1B5E20" if is_read else "#E65100"
                
                st.markdown(f"""
                    <div style="background-color: {bg}; padding: 15px; border-radius: 12px; border-right: 8px solid {border}; margin-bottom: 10px;">
                        <b>{bh_type}</b> | <small>📅 {dt}</small><br>
                        <b>💬 الملاحظة:</b> {note}<br>
                        <small>الحالة: {status}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                if not is_read:
                    # التحقق إذا كان الزر قد ضغط في هذه الجلسة
                    if btn_key not in st.session_state:
                        if st.button("🙏 شكراً أستاذي زياد (تأكيد القراءة)", key=btn_key):
                            try:
                                with st.spinner("جاري إبلاغ الأستاذ..."):
                                    # التحديث في جوجل شيت أولاً
                                    all_rows = sh_bh.get_all_values()
                                    for i, r in enumerate(all_rows):
                                        if r[0] == s_name and r[1] == dt and r[3] == note:
                                            sh_bh.update_cell(i + 1, 5, "✅ تمت القراءة")
                                            # تسجيل الضغط في الذاكرة لإخفاء الزر بعد التحديث
                                            st.session_state[btn_key] = True
                                            st.balloons()
                                            st.success("تم إرسال شكرك! 🌸")
                                            time.sleep(1)
                                            st.rerun()
                                            break
                            except Exception as e:
                                st.error(f"عذراً، حدث خطأ أثناء التحديث. حاول مرة أخرى.")
        else: st.info("سجلك نظيف ومتميز! ✨")

    with t3:
        st.subheader("⚙️ تحديث البيانات")
        with st.form("up"):
            mail = st.text_input("إيميل ولي الأمر", value=str(s_data.iloc[6]))
            phone = st.text_input("رقم الجوال", value=str(s_data.iloc[7]))
            if st.form_submit_button("حفظ"):
                ws = sh.worksheet("students"); c = ws.find(st.session_state.sid)
                ws.update_cell(c.row, 7, mail); ws.update_cell(c.row, 8, phone)
                st.success("تم التحديث ✅"); time.sleep(1); st.rerun()
