import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
import urllib.parse

# --- 1. إعدادات الاتصال والصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception:
        return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                # التأكد من مطابقة الأعمدة
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ""
                return df[expected_cols]
    except Exception:
        pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. التنسيق البصري ---
st.markdown("""
    <style>
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .main { direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { direction: rtl; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
            if not df_st.empty and any(df_st["الرقم"].astype(str) == str(sid_in)):
                st.session_state.role = "student"
                st.session_state.student_id = str(sid_in)
                st.rerun()
            else:
                st.error("الرقم غير مسجل")
    st.stop()

# --- 4. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 الاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والتحفيز")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        tab_b, tab_g = st.tabs(["🎭 السلوك والتحفيز", "📝 رصد الدرجات"])
        
        with tab_b:
            with st.form("beh_form"):
                sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد وحساب النقاط"):
                    pts_val = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, b_note])
                    ws_st = sh.worksheet("students")
                    cell = ws_st.find(sel_st)
                    cur_pts = int(ws_st.cell(cell.row, 9).value or 0)
                    ws_st.update_cell(cell.row, 9, cur_pts + pts_val)
                    st.success(f"✅ تم رصد السلوك لـ {sel_st}")
                    time.sleep(1)
                    st.rerun()
            
            st.subheader("📋 سجل السلوك")
            df_b_view = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
            st.dataframe(df_b_view, use_container_width=True, hide_index=True)

        with tab_g:
            st.subheader("📝 تحديث درجات الطالب")
            with st.form("grade_edit_form"):
                g_st = st.selectbox("اختر الطالب لتعديل درجته", df_all["الاسم"].tolist())
                
                # جلب القيم الحالية
                df_g_now = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
                cur_row = df_g_now[df_g_now["الطالب"] == g_st]
                v1 = float(cur_row.iloc[0]["ف1"]) if not cur_row.empty else 0.0
                v2 = float(cur_row.iloc[0]["ف2"]) if not cur_row.empty else 0.0
                v3 = float(cur_row.iloc[0]["مشاركة"]) if not cur_row.empty else 0.0

                c1, c2, c3 = st.columns(3)
                nf1 = c1.number_input("ف1", value=v1)
                nf2 = c2.number_input("ف2", value=v2)
                nwrk = c3.number_input("مشاركة", value=v3)
                
                if st.form_submit_button("🔄 حفظ التعديلات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(g_st.strip())
                        # تحديث نفس السطر لمنع التكرار
                        ws_g.update(range_name=f'B{cell.row}:D{cell.row}', values=[[nf1, nf2, nwrk]])
                        st.success(f"✅ تم تحديث درجات {g_st}")
                    except Exception:
                        ws_g.append_row([g_st.strip(), nf1, nf2, nwrk])
                        st.success(f"✅ تم إضافة درجات جديدة لـ {g_st}")
                    time.sleep(1)
                    st.rerun()
            
            st.divider()
            st.subheader("📋 كشف الدرجات")
            df_g_final = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
            st.dataframe(df_g_final, use_container_width=True, hide_index=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🗑️ حذف طالب")
        del_name = st.selectbox("اختر الاسم للحذف", [""] + df_st["الاسم"].tolist())
        if st.button("تأكيد الحذف النهائي"):
            if del_name:
                for sn in ["students", "behavior", "grades"]:
                    try:
                        ws = sh.worksheet(sn)
                        cell = ws.find(del_name)
                        ws.delete_rows(cell.row)
                    except Exception: continue
                st.success(f"🗑️ تم حذف {del_name} من كافة السجلات")
                time.sleep(1)
                st.rerun()

    elif menu == "📢 الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("ex_form"):
            e_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("موضوع الاختبار")
            e_date = st.date_input("التاريخ")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.success("🚀 تم النشر بنجاح")

# --- 5. واجهة الطالب ---
elif st.session_state.role == "student":
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {my_info['الاسم']}</h3></div>", unsafe_allow_html=True)
    
    st.metric("رصيد نقاط التميز 🌟", f"{my_info['النقاط']} نقطة")
    
    st.divider()
    st.subheader("📊 تقرير درجاتك")
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    my_grades = df_g[df_g["الطالب"] == my_info["الاسم"]]
    st.dataframe(my_grades, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("🎭 سجل سلوكك")
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    my_beh = df_b[df_b["الاسم"] == my_info["الاسم"]]
    st.dataframe(my_beh, use_container_width=True, hide_index=True)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
