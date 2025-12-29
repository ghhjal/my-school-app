# --- (القسم الأول: المكتبات والربط) ---
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# إعداد الصفحة وتنسيقها
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
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
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
        sid_input = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty:
                id_col = df_st.columns[0]
                if str(sid_input) in df_st[id_col].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid_input)
                    st.rerun()
                else:
                    st.error("الرقم الأكاديمي غير مسجل")
            else:
                st.error("خطأ في جلب بيانات الطلاب")
    st.stop()

# --- 3. واجهة المعلم ---
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
        with tab2:
            st.subheader("🎭 رصد السلوك والتحفيز")
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            sel_st = st.selectbox("اسم الطالب للسلوك", [""] + df_st[name_col].tolist()) if name_col else None
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

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    id_col = df_st.columns[0]
    s_data = df_st[df_st[id_col].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]
    
    st.markdown(f"<h2 style='text-align:center;'>🌟 أهلاً بك يا بطل: {s_name}</h2>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سجل السلوك", "⚙️ بياناتي"])
    
    with t2:
        df_bh = fetch_data("behavior")
        if not df_bh.empty:
            my_bh = df_bh[df_bh.iloc[:, 0] == s_name].copy().iloc[::-1]
            sh_bh = sh.worksheet("behavior")
            
            for idx, row in my_bh.iterrows():
                dt = str(row.iloc[1]); bh_type = str(row.iloc[2]); note = str(row.iloc[3])
                status = str(row.iloc[4]) if len(row) > 4 else "لم تُقرأ بعد"
                
                is_read = "تمت القراءة" in status
                bg = "#E8F5E9" if is_read else "#FFF3E0"
                border = "#1B5E20" if is_read else "#E65100"
                
                st.markdown(f"""
                    <div style="background-color: {bg}; padding: 15px; border-radius: 12px; border-right: 8px solid {border}; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <b style="color: {border};">{bh_type}</b>
                            <small>📅 {dt}</small>
                        </div>
                        <div style="margin-top: 8px; color: #1a1a1a;"><b>💬 الملاحظة:</b> {note}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                if not is_read:
                    # زر الشكر مع حماية من الضغط المتكرر
                    if st.button(f"🙏 شكراً أستاذي زياد (تأكيد القراءة)", key=f"thx_{idx}"):
                        try:
                            with st.spinner("جاري التحديث..."):
                                all_rows = sh_bh.get_all_values()
                                for i, r in enumerate(all_rows):
                                    if r[0] == s_name and r[1] == dt and r[3] == note:
                                        sh_bh.update_cell(i + 1, 5, "✅ تمت القراءة")
                                        st.balloons()
                                        st.success("شكراً لك! تم إرسال القراءة للأستاذ.")
                                        time.sleep(1)
                                        st.rerun()
                                        break
                        except:
                            st.warning("تم تحديث الحالة بالفعل، يرجى تحديث الصفحة.")
        else: st.info("سجلك نظيف!")
