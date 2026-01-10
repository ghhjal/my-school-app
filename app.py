import streamlit as st
import pandas as pd
import gspread
import urllib.parse
import datetime
import hashlib
import io
import re
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 تعريف الألوان (الوضع النهاري عالي التباين) ---
main_bg = "#f8fafc"        
card_bg = "#ffffff"        
text_color = "#000000"     
sub_text = "#333333"       
border_color = "#1e3a8a"   
input_bg = "#ffffff"       
input_text = "#000000"     
header_grad = "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)"
shadow_val = "0 4px 10px rgba(0,0,0,0.1)"

# --- [الدوال المساعدة] ---
def clean_phone_number(phone):
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def get_professional_msg(name, b_type, b_desc, date):
    msg = (f"🔔 *إشعار من منصة الأستاذ زياد*\n👤 *الطالب:* {name}\n📍 *الملاحظة:* {b_type}\n📝 *التفاصيل:* {b_desc if b_desc else 'متابعة'}\n📅 *التاريخ:* {date}")
    return urllib.parse.quote(msg)

def show_footer():
    st.markdown("<br><hr>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    # ✅ التصحيح: إضافة بادئة الروابط
    c1.link_button("📢 تليجرام الإدارة", "https://t.me/ZiyadAlmoami", use_container_width=True)
    c2.link_button("💬 واتساب المعلم", "https://wa.me/966534900049", use_container_width=True)
    c3.link_button("📧 البريد الإلكتروني", "mailto:ziad.platform.alerts@gmail.com", use_container_width=True)
    
    st.markdown(f"<p style='text-align:center; color:{sub_text}; margin-top:20px; font-size:0.8rem;'>© 2026 جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية</p>", unsafe_allow_html=True)

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e: st.error(f"⚠️ خطأ اتصال: {e}"); return None

sh = get_gspread_client()

@st.cache_data(ttl=10)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name); data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty: df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def safe_append_row(worksheet_name, data_dict):
    try:
        ws = sh.worksheet(worksheet_name); headers = ws.row_values(1)
        row = [data_dict.get(h, "") for h in headers]
        ws.append_row(row); return True
    except: return False

# --- تحميل الإعدادات ---
if "class_options" not in st.session_state:
    try:
        sett = sh.worksheet("settings").get_all_records()
        s_map = {row['key']: row['value'] for row in sett}
        st.session_state.max_tasks = int(s_map.get('max_tasks', 60))
        st.session_state.max_quiz = int(s_map.get('max_quiz', 40))
        st.session_state.current_year = str(s_map.get('current_year', '1447هـ'))
        st.session_state.class_options = [x.strip() for x in str(s_map.get('class_list', 'الأول')).split(',') if x.strip()]
        st.session_state.stage_options = [x.strip() for x in str(s_map.get('stage_list', 'ابتدائي')).split(',') if x.strip()]
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        st.session_state.class_options = ["الأول"]; st.session_state.stage_options = ["ابتدائي"]

if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = None

# ==========================================
# 🎨 2. التصميم (CSS)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    section[data-testid="stSidebar"] {{ display: none; }}
    
    html, body, [data-testid="stAppViewContainer"] {{ 
        font-family: 'Cairo'; direction: RTL; text-align: right; 
        background-color: {main_bg} !important; color: {text_color} !important; 
    }}
    .block-container {{ padding-top: 0rem; padding-bottom: 5rem; }}
    
    /* الهيدر */
    .header-container {{
        display: flex; flex-direction: row-reverse; align-items: center; justify-content: center;
        background: {header_grad};
        padding-top: 80px; padding-bottom: 40px; 
        border-radius: 0 0 35px 35px; margin-top: -60px; margin-left: -5rem; margin-right: -5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15); color: white; text-align: center;
    }}
    .logo-icon {{ font-size: 6rem; margin-right: 25px; margin-top: 15px; filter: drop-shadow(0 5px 10px rgba(0,0,0,0.3)); animation: float 3s ease-in-out infinite; }}
    .header-text h1 {{ margin: 0; font-size: 3rem; font-weight: 900; color: #fff !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
    .header-text p {{ margin: 5px 0 0 0; color: #dbeafe; font-size: 1.2rem; font-weight: bold; }}
    
    @keyframes blinker {{ 50% {{ opacity: 0.6; transform: scale(0.98); }} }}
    .urgent-anim {{ animation: blinker 1.5s linear infinite; border: 2px solid red !important; background-color: #fff5f5 !important; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}

    @media (max-width: 768px) {{
        .header-container {{ flex-direction: column; padding-top: 100px; padding-bottom: 30px; }}
        .logo-icon {{ font-size: 5rem; margin: 0 0 10px 0; }}
        .header-text h1 {{ font-size: 2.2rem; }}
    }}

    div[data-baseweb="input"] {{ background-color: #ffffff !important; border: 2px solid {border_color} !important; border-radius: 12px; height: 50px; }}
    input {{ color: #000000 !important; font-weight: 900 !important; font-size: 1.1rem !important; -webkit-text-fill-color: #000000 !important; }}
    div[data-baseweb="select"] {{ background-color: #ffffff !important; color: #000000 !important; }}
    div[data-baseweb="base-input"] {{ background-color: #ffffff !important; }}
    label {{ color: #000000 !important; font-weight: 800 !important; font-size: 1rem !important; }} 
    
    div.stButton > button {{
        background-color: white !important;
        color: #1e3a8a !important; 
        border: 2px solid #1e3a8a !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        transition: 0.3s;
        width: 100%;
    }}
    div.stButton > button:hover {{ background-color: #1e3a8a !important; color: white !important; }}
    button[kind="primary"] {{ background-color: #1e3a8a !important; color: white !important; border: none !important; }}

    .app-header {{ background: {card_bg}; padding: 20px; border-radius: 15px; border-right: 10px solid #1e3a8a; box-shadow: {shadow_val}; margin-top: -20px; border: 1px solid {border_color}; text-align: right !important; direction: rtl !important; }}
    .medal-flex {{ display: flex; gap: 8px; margin: 15px 0; direction: rtl; }}
    .m-card {{ flex: 1; background: {card_bg}; padding: 15px 5px; border-radius: 15px; text-align: center; border: 2px solid {border_color}; box-shadow: {shadow_val}; }}
    .m-active {{ border-color: #f59e0b !important; background: #fffbeb !important; box-shadow: 0 4px 8px rgba(245,158,11,0.2) !important; color: #000 !important; }}
    .points-banner {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 20px; }}
    
    .mobile-card {{ 
        background: {card_bg}; color: {text_color}; 
        padding: 18px; border-radius: 12px; 
        border: 2px solid {border_color}; 
        margin-bottom: 12px; font-weight: 800; 
        box-shadow: {shadow_val}; border-right: 8px solid #1e3a8a; 
        font-size: 1.1rem; text-align: right !important; direction: rtl !important;
    }}
    
    .leaderboard-row {{ display: flex; justify-content: space-between; align-items: center; direction: rtl; }}
    .urgent-msg {{ border: 2px solid #e53e3e; color: #c53030 !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; font-weight: 900; direction: rtl; }}
    
    h1, h2, h3, h4, h5, h6, p, span, div {{ color: {text_color}; }}
    small {{ color: {sub_text} !important; font-weight: bold; }}
    </style>

    <div class="header-container">
        <div class="logo-icon">🎓</div>
        <div class="header-text">
            <h1>منصة زياد الذكية</h1>
            <p>نظام متابعة الطلاب والتواصل مع أولياء الأمور - 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 3. نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم"])
    with t1:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول 🚀", type="primary", use_container_width=True):
                df = fetch_safe("students")
                if not df.empty:
                    df['clean_id'] = df.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
                    if sid.split('.')[0] in df['clean_id'].values:
                        st.session_state.username = sid.split('.')[0]
                        st.session_state.role = "student"
                        st.rerun()
                    else: st.error("غير مسجل")
    with t2:
        with st.form("tr_login"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول 🛠️", type="primary", use_container_width=True):
                df = fetch_safe("users")
                if not df.empty and u in df['username'].values:
                    ud = df[df['username']==u].iloc[0]
                    if hashlib.sha256(p.encode()).hexdigest() == ud['password_hash']:
                        st.session_state.username = u; st.session_state.role = "teacher"; st.rerun()
                st.error("بيانات خاطئة")
    show_footer()

# ==========================================
# 👨‍🏫 4. واجهة المعلم
# ==========================================
elif st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 👥 الطلاب ---
    with menu[0]:
        st.subheader("👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("العدد", len(df_st))
            c2.metric("الفصول", len(df_st.iloc[:,2].unique()) if len(df_st.columns)>2 else 0)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            st.divider()

            with st.expander("➕ إضافة طالب جديد", expanded=True):
                with st.form("add_st_v26", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    f_id = c1.text_input("🔢 الرقم الأكاديمي")
                    f_name = c2.text_input("👤 الاسم")
                    c3, c4, c5 = st.columns(3)
                    f_class = c3.selectbox("الصف", st.session_state.class_options)
                    f_stage = c4.selectbox("المرحلة", st.session_state.stage_options)
                    f_year = c5.text_input("العام", st.session_state.current_year)
                    c6, c7 = st.columns(2)
                    f_phone = c6.text_input("📱 الجوال")
                    f_mail = c7.text_input("📧 الإيميل")
                    
                    if st.form_submit_button("✅ حفظ", type="primary"):
                        if f_id and f_name:
                            if f_id.strip() in df_st['clean_id'].values:
                                st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً!")
                            else:
                                cl_p = clean_phone_number(f_phone) if f_phone else ""
                                st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "الجوال": cl_p, "الإيميل": f_mail.strip(), "النقاط": "0"}
                                if safe_append_row("students", st_map):
                                    st.success("✅ تم الحفظ"); st.cache_data.clear(); st.rerun()
                        else: st.warning("أكمل البيانات")
            
            st.write("---")
            sq = st.text_input("🔍 بحث:")
            if sq: st.dataframe(df_st[df_st.iloc[:,0].str.contains(sq)|df_st.iloc[:,1].str.contains(sq)], use_container_width=True, hide_index=True)
            else: st.dataframe(df_st, use_container_width=True, hide_index=True)

            with st.expander("🗑️ حذف"):
                dq = st.text_input("بحث للحذف:", key="dq")
                if dq:
                    for i, r in df_st[df_st.iloc[:,0].str.contains(dq)|df_st.iloc[:,1].str.contains(dq)].iterrows():
                        if st.button(f"حذف {r.iloc[1]}", key=f"d{i}"):
                            sh.worksheet("students").delete_rows(int(i)+2); st.success("تم"); st.cache_data.clear(); st.rerun()
        else: st.info("فارغة")

    # 📊 التقييم
    with menu[1]:
        st.subheader("📊 التقييم والمتابعة")
        df_ev = fetch_safe("students")
        if not df_ev.empty:
            st_dict = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_ev.iterrows()}
            sel = st.selectbox("🎯 اختر الطالب:", [""] + list(st_dict.keys()))
            if sel:
                sid = st_dict[sel]
                s_inf = df_ev[df_ev.iloc[:,0] == sid].iloc[0]
                s_nm = s_inf['name']; clp = clean_phone_number(s_inf.get('الجوال',''))
                s_eml = s_inf.get('الإيميل', '')
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 📝 الدرجات")
                    df_g = fetch_safe("grades")
                    cur_p1 = 0; cur_p2 = 0
                    if not df_g.empty:
                        gr = df_g[df_g.iloc[:,0]==sid]
                        if not gr.empty:
                            cur_p1 = int(pd.to_numeric(gr.iloc[0]['p1'], errors='coerce') or 0)
                            cur_p2 = int(pd.to_numeric(gr.iloc[0]['p2'], errors='coerce') or 0)
                    
                    with st.form("gr_upd"):
                        v1 = st.number_input("مشاركة", 0, st.session_state.max_tasks, cur_p1)
                        v2 = st.number_input("اختبار", 0, st.session_state.max_quiz, cur_p2)
                        if st.form_submit_button("💾 تحديث الدرجات", type="primary"):
                            ws = sh.worksheet("grades"); cell = ws.find(sid); tot = v1+v2
                            if cell:
                                ws.update_cell(cell.row, 2, v1); ws.update_cell(cell.row, 3, v2)
                                ws.update_cell(cell.row, 4, tot); ws.update_cell(cell.row, 5, str(datetime.date.today()))
                            else: ws.append_row([sid, v1, v2, tot, str(datetime.date.today())])
                            st.success("✅ تم التحديث"); st.cache_data.clear(); st.rerun()
                    
                    st.caption(f"الدرجات الحالية: مشاركة {cur_p1} | اختبار {cur_p2}")

                with c2:
                    st.markdown("##### 🎭 السلوك")
                    with st.form("beh_add"):
                        bt = st.selectbox("نوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🚫 سلبي (-10)"])
                        bn = st.text_area("ملاحظة")
                        if st.form_submit_button("💾 تسجيل وتحديث النقاط", type="primary"):
                            safe_append_row("behavior", {"student_id": sid, "date": str(datetime.date.today()), "type": bt, "note": bn})
                            match = re.search(r'\(([\+\-]?\d+)\)', bt)
                            chg = int(match.group(1)) if match else 0
                            if chg != 0:
                                ws = sh.worksheet("students"); c = ws.find(sid)
                                if c:
                                    h = ws.row_values(1)
                                    if 'النقاط' in h:
                                        idx = h.index('النقاط') + 1
                                        cur = ws.cell(c.row, idx).value
                                        new_val = (int(cur) if cur and str(cur).isdigit() else 0) + chg
                                        ws.update_cell(c.row, idx, new_val)
                                        st.toast(f"📈 الرصيد الجديد: {new_val}")
                            st.success("✅ تم"); st.cache_data.clear(); st.rerun()

                st.divider()
                df_b = fetch_safe("behavior")
                if not df_b.empty:
                    cid = 'student_id' if 'student_id' in df_b.columns else df_b.columns[0]
                    my_b = df_b[df_b[cid].astype(str) == str(sid)]
                    for i, r in my_b.iterrows():
                        with st.container(border=True):
                            kc1, kc2, kc3 = st.columns([3, 1.2, 0.5])
                            with kc1: st.write(f"**{r.get('type')}** | {r.get('date')}"); st.caption(r.get('note'))
                            with kc2: 
                                lnk = get_professional_msg(s_nm, r.get('type'), r.get('note'), r.get('date'))
                                c_wa, c_em = st.columns(2)
                                c_wa.link_button("واتساب", f"https://api.whatsapp.com/send?phone={clp}&text={lnk}", use_container_width=True)
                                c_em.link_button("إيميل", f"mailto:{s_eml}?subject=ملاحظة: {s_nm}&body={lnk}", use_container_width=True)
                            with kc3:
                                if st.button("🗑️", key=f"dl{i}"):
                                    sh.worksheet("behavior").delete_rows(int(i)+2); st.success("حُذف"); st.cache_data.clear(); st.rerun()

    # 📢 التنبيهات
    with menu[2]:
        st.subheader("📢 التنبيهات")
        with st.form("ann_add"):
            at = st.text_input("العنوان"); ad = st.text_area("التفاصيل"); au = st.checkbox("عاجل")
            atg = st.selectbox("الفئة", ["الكل"] + st.session_state.class_options)
            if st.form_submit_button("📣 نشر", type="primary"):
                safe_append_row("exams", {"الصف": atg, "عاجل": "نعم" if au else "لا", "العنوان": at, "التاريخ": str(datetime.date.today()), "الرابط": ad})
                st.success("✅ تم"); st.cache_data.clear(); st.rerun()
        st.divider()
        df_a = fetch_safe("exams")
        for i, r in df_a.iloc[::-1].iterrows():
            with st.container(border=True):
                kc1, kc2 = st.columns([3, 1])
                kc1.write(f"**{r.get('العنوان')}** ({r.get('الصف')})"); kc1.caption(r.get('الرابط'))
                # زر نشر مجموعة بتنسيق احترافي
                msg_text = (f"📢 *تعميم هام من منصة الأستاذ زياد*\n"
                            f"━━━━━━━━━━━━\n"
                            f"📌 *العنوان:* {r.get('العنوان')}\n"
                            f"📄 *التفاصيل:* {r.get('الرابط')}\n"
                            f"📅 *التاريخ:* {r.get('التاريخ')}\n"
                            f"━━━━━━━━━━━━")
                grp_msg = urllib.parse.quote(msg_text)
                kc2.link_button("📲 نشر للمجموعة", f"https://api.whatsapp.com/send?text={grp_msg}", use_container_width=True)
                if kc2.button("🗑️ حذف", key=f"da{i}"):
                    sh.worksheet("exams").delete_rows(int(i)+2); st.rerun()

    # --- ⚙️ الإعدادات ---
    with menu[3]:
        st.subheader("⚙️ الإعدادات")
        
        with st.expander("🛠️ صيانة وتصفير", expanded=True):
            if st.button("🔄 تحديث النظام"): st.cache_data.clear(); st.rerun()
            if st.button("🧹 تصفير نقاط الطلاب"):
                ws = sh.worksheet("students"); d = ws.get_all_values()
                if len(d)>1: ws.update(f"I2:I{len(d)}", [[0]]*(len(d)-1)); st.success("تم التصفير")

        with st.expander("📝 القوائم والدرجات"):
            cy = st.text_input("عام", st.session_state.current_year)
            cls = st.text_area("صفوف", ",".join(st.session_state.class_options))
            stg = st.text_area("مراحل", ",".join(st.session_state.stage_options))
            mt = st.number_input("مشاركة", 0, 100, st.session_state.max_tasks)
            mq = st.number_input("اختبار", 0, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ الإعدادات", type="primary"):
                ws = sh.worksheet("settings")
                # إصلاح مشكلة حفظ المراحل
                batch_updates = [
                    {'range': 'A2:B2', 'values': [['max_tasks', mt]]},
                    {'range': 'A3:B3', 'values': [['max_quiz', mq]]},
                    {'range': 'A4:B4', 'values': [['current_year', cy]]},
                    {'range': 'A5:B5', 'values': [['class_list', cls]]},
                    {'range': 'A6:B6', 'values': [['stage_list', stg]]} 
                ]
                ws.batch_update(batch_updates)
                st.session_state.max_tasks = mt; st.session_state.max_quiz = mq
                st.session_state.current_year = cy
                st.session_state.class_options = [x.strip() for x in cls.split(',') if x.strip()]
                st.session_state.stage_options = [x.strip() for x in stg.split(',') if x.strip()]
                st.success("تم الحفظ"); st.cache_data.clear(); st.rerun()

        with st.expander("📤 مزامنة (Excel)"):
            up = st.file_uploader("ملف", type=['xlsx'])
            ts = st.radio("الجدول", ["students", "grades"], horizontal=True)
            if st.button("🚀 بدء المزامنة", type="primary") and up:
                df = pd.read_excel(up).fillna("").dropna(how='all')
                ws = sh.worksheet(ts); cur = ws.get_all_records()
                cids = [str(r.get('id', r.get('student_id', ''))) for r in cur]
                hd = ws.row_values(1)
                for _, r in df.iterrows():
                    d = r.to_dict(); raw = str(d.get('student_id', d.get('id', ''))).strip().split('.')[0]
                    if not raw or raw=='0': continue
                    
                    if ts == "grades":
                        d.update({"student_id": raw, "p1": int(d.get('p1',0)), "p2": int(d.get('p2',0)), "perf": int(d.get('p1',0))+int(d.get('p2',0)), "date": str(datetime.date.today())})
                        if 'id' in d: del d['id']
                    else:
                        d['id'] = raw; d['الجوال'] = clean_phone_number(d.get('الجوال',''))
                        if 'النقاط' not in d or str(d.get('النقاط', '')).strip() == "": d['النقاط'] = 0
                    
                    if raw in cids: ws.update(f"A{cids.index(raw)+2}", [[str(d.get(k,"")) for k in hd]])
                    else: ws.append_row([str(d.get(k,"")) for k in hd])
                st.success("تمت المزامنة"); st.cache_data.clear(); st.rerun()

        with st.expander("📥 تنزيل القوالب"):
            b1 = io.BytesIO()
            pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط"]).to_excel(b1, index=False)
            st.download_button("قالب الطلاب", b1.getvalue(), "students_template.xlsx")
            b2 = io.BytesIO()
            pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(b2, index=False)
            st.download_button("قالب الدرجات", b2.getvalue(), "grades_template.xlsx")

        with st.expander("🔐 المستخدمين"):
            t1, t2 = st.tabs(["إضافة مستخدم", "تغيير المرور"])
            with t1:
                with st.form("add_u"):
                    nu = st.text_input("الاسم"); np = st.text_input("الباسورد", type="password")
                    if st.form_submit_button("إضافة"):
                        safe_append_row("users", {"username": nu, "password_hash": hashlib.sha256(np.encode()).hexdigest(), "role": "teacher"})
                        st.success("تم")
            with t2:
                with st.form("chg_pass"):
                    npwd = st.text_input("الجديدة", type="password")
                    if st.form_submit_button("تغيير"):
                        df_u = fetch_safe("users")
                        if st.session_state.username in df_u['username'].values:
                            idx = df_u[df_u['username']==st.session_state.username].index[0] + 2
                            sh.worksheet("users").update_cell(idx, 2, hashlib.sha256(npwd.encode()).hexdigest())
                            st.success("تم")

    with menu[4]:
        if st.button("خروج", type="primary"): st.session_state.role = None; st.rerun()
    show_footer()

# ==========================================
# 👨‍🎓 5. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    sid = str(st.session_state.get('username', '')).strip()
    df_st = fetch_safe("students"); df_gr = fetch_safe("grades"); df_beh = fetch_safe("behavior"); df_ann = fetch_safe("exams")
    
    if not df_st.empty:
        df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
        info = df_st[df_st['clean_id'] == sid]
    else: info = pd.DataFrame()

    if not info.empty:
        s_dat = info.iloc[0]
        s_nm = s_dat.get('name', 'طالب'); s_cls = str(s_dat.get('class', '')).strip()
        pts = int(pd.to_numeric(s_dat.get('النقاط', 0), errors='coerce') or 0)

        # ✅ التنبيه العاجل (مكانه الجديد بالأعلى مع الوميض)
        if not df_ann.empty:
            df_ann['عاجل'] = df_ann['عاجل'].astype(str).str.strip(); df_ann['الصف'] = df_ann['الصف'].astype(str).str.strip()
            urg = df_ann[(df_ann['عاجل']=='نعم') & (df_ann['الصف'].isin(['الكل', s_cls]))]
            if not urg.empty:
                u = urg.tail(1).iloc[0]
                st.markdown(f"<div class='urgent-msg urgent-anim'>🚨 {u.get('العنوان')}<br><small>{u.get('الرابط')}</small></div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class="app-header"><h2>👋 مرحباً: {s_nm}</h2><p>🏫 {s_cls} | 🆔 {sid}</p></div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="medal-flex">
                <div class="m-card {'m-active' if pts>=100 else ''}">🥇<br><b>ذهبي</b></div>
                <div class="m-card {'m-active' if pts>=50 else ''}">🥈<br><b>فضي</b></div>
                <div class="m-card m-active">🥉<br><b>برونزي</b></div>
            </div>
            <div class="points-banner"><p>النقاط</p><h1>{pts}</h1></div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["📢 تنبيهات", "📝 ملاحظات", "📊 درجات", "🏆 المتصدرين", "⚙️ حسابي"])

        with tabs[0]:
            if not df_ann.empty:
                anns = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_cls])]
                for _, r in anns.iloc[::-1].iterrows():
                    st.markdown(f"<div class='mobile-card'>📢 {r.get('العنوان')}<br><small>{r.get('التاريخ')}</small><br>{r.get('الرابط')}</div>", unsafe_allow_html=True)
            else: st.info("لا يوجد تنبيهات")

        with tabs[1]:
            if not df_beh.empty:
                df_beh['clean_id'] = df_beh.iloc[:,0].astype(str).str.split('.').str[0]
                nts = df_beh[df_beh['clean_id']==sid]
                if not nts.empty:
                    for _, n in nts.iterrows():
                        st.markdown(f"<div class='mobile-card' style='border-right-color:#e53e3e'>📌 {n.get('type')}: {n.get('note')}<br><small>{n.get('date')}</small></div>", unsafe_allow_html=True)
                else: st.success("سجلك نظيف")

        with tabs[2]:
            if not df_gr.empty:
                df_gr['clean_id'] = df_gr.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                grs = df_gr[df_gr['clean_id']==sid]
                if not grs.empty:
                    g = grs.iloc[0]
                    st.markdown(f"<div class='mobile-card'>📝 مشاركة: {g.get('p1')}</div><div class='mobile-card'>✍️ اختبار: {g.get('p2')}</div><div class='mobile-card' style='background:#f0fdf4'>🏆 المجموع: {g.get('perf')}</div>", unsafe_allow_html=True)
                else: st.info("لا درجات")

        with tabs[3]:
            df_st['p_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            for i, (_, r) in enumerate(df_st.sort_values('p_num', ascending=False).head(10).iterrows(), 1):
                ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else str(i)
                sty = "border:2px solid #1e3a8a" if str(r['clean_id']) == sid else ""
                st.markdown(f"""
                    <div class='mobile-card leaderboard-row' style='{sty}'>
                        <span>{ic}</span>
                        <span>{r['name']}</span>
                        <span style='color:#f59e0b; font-weight:900;'>{int(r['p_num'])} ن</span>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[4]:
            st.write("#### ⚙️ تحديث البيانات")
            nm = st.text_input("📧 إيميل", s_dat.get('الإيميل',''))
            np = st.text_input("📱 جوال", s_dat.get('الجوال',''))
            
            st.write("")
            c1, c2 = st.columns(2)
            if c1.button("💾 حفظ التعديلات", use_container_width=True):
                try:
                    fp = clean_phone_number(np) if np else ""
                    ws = sh.worksheet("students"); c = ws.find(sid)
                    if c:
                        h = ws.row_values(1)
                        if 'الإيميل' in h and 'الجوال' in h:
                            ws.update_cell(c.row, h.index('الإيميل')+1, nm)
                            ws.update_cell(c.row, h.index('الجوال')+1, fp)
                            st.success("✅ تم تحديث بياناتك بنجاح")
                            st.toast("تم الحفظ بنجاح", icon="✅")
                        else: st.error("خطأ في الجدول")
                except Exception as e: st.error(f"خطأ: {e}")
            
            if c2.button("🚪 خروج", type="primary", use_container_width=True):
                st.session_state.role = None; st.rerun()

    else: st.error("غير مسجل"); st.button("عودة", on_click=st.rerun)
    
    show_footer()
