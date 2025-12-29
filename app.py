import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# الربط بقاعدة البيانات مع حماية من تكرار الطلبات (تجنب الرسالة الحمراء)
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

# --- نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="t_pwd_main")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور خاطئة")
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي", key="s_id_main")
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

# --- واجهة المعلم ---
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
                        st.success(f"تم حذف {to_del} بنجاح"); st.rerun()
        
        with col_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                id_v = c1.text_input("الرقم الأكاديمي")
                name_v = c2.text_input("اسم الطالب")
                
                c3, c4 = st.columns(2)
                cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                lev_v = c4.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                
                yr_v = st.text_input("العام الدراسي", value="1447هـ")
                sub_v = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("إضافة الطالب"):
                    if id_v and name_v:
                        sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                        st.success(f"تمت إضافة {name_v} بنجاح ✅")
                        time.sleep(1); st.rerun()
                    else: st.warning("يرجى ملء الاسم والرقم الأكاديمي")

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with tab1:
            st.subheader("📝 رصد الدرجات")
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            target = st.selectbox("اختر الطالب للدرجات", [""] + df_st[name_col].tolist())
            if target:
                with st.form("g_form"):
                    v1 = st.number_input("درجة ف1", 0, 100)
                    v2 = st.number_input("درجة ف2", 0, 100)
                    v3 = st.number_input("المشاركة", 0, 100)
                    if st.form_submit_button("حفظ"):
                        ws_g = sh.worksheet("grades")
                        try: 
                            fnd = ws_g.find(target)
                            ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                        except: 
                            ws_g.append_row([target, v1, v2, v3])
                        st.success("تم التحديث ✅")
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with tab2:
            st.subheader("🎭 رصد وفلترة السلوك")
            name_col = df_st.columns[1] if len(df_st.columns) > 1 else ""
            sel_st = st.selectbox("اسم الطالب للملاحظة", [""] + df_st[name_col].tolist())
            if sel_st:
                with st.form("b_form_t", clear_on_submit=True):
                    d_v = st.date_input("التاريخ", datetime.now())
                    t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    n_v = st.text_input("الملاحظة")
                    if st.form_submit_button("حفظ وإرسال"):
                        pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                        sh.worksheet("behavior").append_row([sel_st, str(d_v), t_v, n_v, "🕒 لم تُقرأ بعد"])
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                        old_pts = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_pts + pts)
                        st.success("تم الحفظ ✅"); time.sleep(1); st.rerun()
                
                st.divider()
                st.write(f"🔍 سجل الطالب المختار: {sel_st}")
                df_bh_all = fetch_data("behavior")
                if not df_bh_all.empty:
                    f_bh = df_bh_all[df_bh_all.iloc[:, 0] == sel_st].iloc[::-1]
                    st.dataframe(f_bh, use_container_width=True, hide_index=True)

    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 إدارة إعلانات المواعيد")
        df_ex = fetch_data("exams")
        st.dataframe(df_ex, use_container_width=True, hide_index=True)
        with st.form("ex_form"):
            e_cls = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = st.text_input("موضوع الاختبار")
            e_dt = st.date_input("الموعد")
            if st.form_submit_button("نشر الموعد"):
                sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                st.success("تم النشر ✅"); st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    id_col = df_st.columns[0]
    s_data = df_st[df_st[id_col].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]
    
    st.markdown(f"<h2 style='text-align:center;'>🌟 أهلاً بك: {s_name}</h2>", unsafe_allow_html=True)
    
    pts = int(s_data.iloc[8] or 0)
    medal = "🏆 بطل التحدي" if pts >= 100 else "🥇 وسام ذهبي" if pts >= 50 else "🥈 وسام فضي"
    c1, c2 = st.columns(2)
    c1.metric("رصيد نقاطك ⭐", pts)
    c2.metric("لقبك الحالي 🏆", medal)

    st.divider()
    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سجل السلوك", "⚙️ بياناتي"])
    
    with t1:
        df_g = fetch_data("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                g = my_g.iloc[0]
                ca, cb, cc = st.columns(3)
                ca.metric("فترة 1", g.iloc[1]); cb.metric("فترة 2", g.iloc[2]); cc.metric("المشاركة", g.iloc[3])
    
    with t2:
        st.subheader("🎭 سجل السلوك")
        df_bh = fetch_data("behavior")
        if not df_bh.empty:
            df_bh['row_idx'] = range(2, len(df_bh) + 2)
            my_bh = df_bh[df_bh.iloc[:, 0] == s_name].copy().iloc[::-1]
            sh_bh = sh.worksheet("behavior")
            
            for _, row in my_bh.iterrows():
                dt, bh_type, note = str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3])
                status = str(row.iloc[4]) if len(row) > 4 else "🕒 لم تُقرأ بعد"
                is_read = "✅" in status
                r_idx = int(row['row_idx'])
                
                bg = "#E8F5E9" if is_read else "#FFF3E0"
                st.markdown(f"<div style='background-color:{bg}; padding:15px; border-radius:10px; border-right:8px solid {'#1B5E20' if is_read else '#E65100'}; margin-bottom:10px;'><b>{bh_type}</b> | 📅 {dt}<br>{note}<br><small>الحالة: {status}</small></div>", unsafe_allow_html=True)
                
                if not is_read:
                    if st.button("🙏 شكراً أستاذي زياد (تأكيد القراءة)", key=f"btn_thx_{r_idx}"):
                        sh_bh.update_cell(r_idx, 5, "✅ تمت القراءة")
                        st.balloons(); time.sleep(0.5); st.rerun()

    with t3:
        with st.form("up"):
            mail = st.text_input("إيميل ولي الأمر", value=str(s_data.iloc[6]))
            phone = st.text_input("رقم الجوال", value=str(s_data.iloc[7]))
            if st.form_submit_button("حفظ التغييرات"):
                ws = sh.worksheet("students"); c = ws.find(st.session_state.sid)
                ws.update_cell(c.row, 7, mail); ws.update_cell(c.row, 8, phone)
                st.success("تم التحديث ✅"); st.rerun()
