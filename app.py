import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
import urllib.parse

# --- 1. إعدادات الاتصال ---
@st.cache_resource(ttl=600)
def get_db():
    try:import streamlit as st
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
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. التنسيق البصري ---
st.markdown("""
    <style>
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .main { direction: rtl; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
            if any(df_st["الرقم"].astype(str) == str(sid_in)):
                st.session_state.role = "student"; st.session_state.student_id = str(sid_in); st.rerun()
    st.stop()

# --- 4. واجهة المعلم (الدرجات والسلوك) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة:", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 الاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والتحفيز")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        tab_b, tab_g = st.tabs(["🎭 السلوك والتحفيز", "📝 رصد الدرجات"])
        
        with tab_b:
            # نموذج السلوك
            with st.form("beh_form"):
                sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد وحساب النقاط"):
                    pts_val = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, b_note])
                    ws_st = sh.worksheet("students"); cell = ws_st.find(sel_st)
                    cur_pts = int(ws_st.cell(cell.row, 9).value or 0)
                    ws_st.update_cell(cell.row, 9, cur_pts + pts_val)
                    st.success("✅ تم الرصد وتحديث النقاط"); time.sleep(1); st.rerun()
            
            # عرض جدول السلوك أسفل النموذج
            st.divider()
            st.subheader("📋 سجل السلوك")
            df_b_view = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
            st.dataframe(df_b_view, use_container_width=True, hide_index=True)

        with tab_g:
            # نموذج الدرجات (تحديث بدون تكرار)
            st.subheader("📝 تحديث درجات الطالب")
            with st.form("grade_edit_form"):
                g_st = st.selectbox("اختر الطالب لتعديل درجته", df_all["الاسم"].tolist())
                
                # جلب القيم الحالية للطالب
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
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[nf1, nf2, nwrk]])
                        st.success(f"✅ تم تحديث {g_st}")
                    except:
                        ws_g.append_row([g_st.strip(), nf1, nf2, nwrk])
                        st.success(f"✅ تم إضافة {g_st}")
                    time.sleep(1); st.rerun()
            
            # عرض جدول الدرجات أسفل النموذج
            st.divider()
            st.subheader("📋 كشف الدرجات")
            df_g_final = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
            st.dataframe(df_g_final, use_container_width=True, hide_index=True)

# --- 5. واجهة الطالب (نظام النقاط) ---
elif st.session_state.role == "student":
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {my_info['الاسم']}</h3></div>", unsafe_allow_html=True)
    
    st.metric("رصيد نقاط التميز 🌟", f"{my_info['النقاط']} نقطة")
    
    st.divider()
    st.subheader("📊 درجاتك")
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    my_grades = df_g[df_g["الطالب"] == my_info["الاسم"]]
    st.dataframe(my_grades, use_container_width=True, hide_index=True)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. التنسيق والوضوح العالي ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .main { direction: rtl; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
            if any(df_st["الرقم"].astype(str) == str(sid_in)):
                st.session_state.role = "student"; st.session_state.student_id = str(sid_in); st.rerun()
    st.stop()

# --- 4. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة:", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 الاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والتحفيز")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        tab_b, tab_g = st.tabs(["🎭 السلوك والتحفيز", "📝 رصد الدرجات"])
        
        with tab_b:
            # نموذج رصد السلوك
            with st.form("beh_form"):
                sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد وحساب النقاط"):
                    pts_val = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, b_note])
                    ws_st = sh.worksheet("students"); cell = ws_st.find(sel_st)
                    cur_pts = int(ws_st.cell(cell.row, 9).value or 0)
                    ws_st.update_cell(cell.row, 9, cur_pts + pts_val)
                    st.success("✅ تم الرصد وتحديث النقاط"); time.sleep(1); st.rerun()
            
            # استعادة جدول السلوك
            st.subheader("📋 سجل السلوك الحالي")
            df_b_view = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
            st.dataframe(df_b_view, use_container_width=True, hide_index=True)

        with tab_g:
            with tab_g:
            # نموذج رصد الدرجات المطور لمنع التكرار
            st.subheader("📝 تحديث درجات الطالب")
            with st.form("grade_form", clear_on_submit=False):
                g_st = st.selectbox("اختر الطالب للدرجات", df_all["الاسم"].tolist())
                
                # محاولة جلب الدرجات الحالية لعرضها قبل التعديل
                df_g_now = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
                current_val = df_g_now[df_g_now["الطالب"] == g_st]
                
                c1, c2, c3 = st.columns(3)
                # إذا كان الطالب له درجات سابقة تظهر تلقائياً في الخانات
                val_f1 = float(current_val.iloc[0]["ف1"]) if not current_val.empty else 0.0
                val_f2 = float(current_val.iloc[0]["ف2"]) if not current_val.empty else 0.0
                val_wrk = float(current_val.iloc[0]["مشاركة"]) if not current_val.empty else 0.0

                f1 = c1.number_input("ف1", value=val_f1)
                f2 = c2.number_input("ف2", value=val_f2)
                wrk = c3.number_input("مشاركة", value=val_wrk)
                
                if st.form_submit_button("🔄 تحديث الدرجات (بدون تكرار)"):
                    ws_g = sh.worksheet("grades")
                    try:
                        # البحث عن الخلية التي تحتوي على اسم الطالب بدقة
                        cell = ws_g.find(g_st.strip())
                        # إذا وجد الطالب، يتم تحديث الصف الخاص به فقط (الأعمدة B, C, D)
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[f1, f2, wrk]])
                        st.success(f"✅ تم تحديث درجات {g_st} بنجاح")
                    except:
                        # إذا لم يجد الاسم (طالب جديد)، يضيفه في سطر جديد
                        ws_g.append_row([g_st.strip(), f1, f2, wrk])
                        st.success(f"✅ تم إضافة درجات جديدة للطالب {g_st}")
                    
                    time.sleep(1)
                    st.rerun()
            
            # عرض جدول الدرجات المحدث
            st.divider()
            st.subheader("📋 كشف الدرجات النهائي")
            df_g_display = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
            # إزالة أي فراغات قد تسبب تكراراً بصرياً
            df_g_display["الطالب"] = df_g_display["الطالب"].str.strip()
            # عرض الجدول مرتباً حسب الاسم لسهولة المتابعة
            st.dataframe(df_g_display.sort_values("الطالب"), use_container_width=True, hide_index=True)

    # (بقية القوائم تبقى كما هي في الكود السابق لضمان استقرار النظام)
    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب والحذف")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # ميزة الحذف الفردي
        st.divider()
        del_name = st.selectbox("🗑️ اختر طالب للحذف نهائياً", [""] + df_st["الاسم"].tolist())
        if st.button("تأكيد حذف الطالب المحدد فقط"):
            if del_name:
                for sn in ["students", "behavior", "grades"]:
                    try:
                        ws = sh.worksheet(sn); cell = ws.find(del_name); ws.delete_rows(cell.row)
                    except: continue
                st.success("🗑️ تم الحذف بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📢 الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("ex_form"):
            e_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("موضوع الاختبار")
            e_date = st.date_input("موعد الاختبار")
            if st.form_submit_button("إرسال التنبيه"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.success("🚀 تم نشر الإعلان لطلاب الصف المحدد")

# --- 5. واجهة الطالب (نظام التحفيز) ---
elif st.session_state.role == "student":
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {my_info['الاسم']}</h3></div>", unsafe_allow_html=True)
    
    # بطاقة النقاط والأوسمة
    pts = int(my_info["النقاط"])
    st.metric("رصيد نقاط التميز 🌟", f"{pts} نقطة")
    
    st.divider()
    st.subheader("📊 درجاتك الحالية")
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    my_grades = df_g[df_g["الطالب"] == my_info["الاسم"]]
    st.dataframe(my_grades, use_container_width=True, hide_index=True)
