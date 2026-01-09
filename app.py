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
# ⚙️ 1. إعدادات النظام والاستقرار الأساسية
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# --- 🌗 زر التحويل (الوضع الداكن / الفاتح) ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = False 

with st.sidebar:
    st.session_state.theme_mode = st.toggle("🌙 الوضع الداكن", value=st.session_state.theme_mode)

# --- 🎨 تحديد الألوان ---
if st.session_state.theme_mode:
    main_bg = "#0e1117"
    card_bg = "#262730"
    text_color = "#ffffff"
    sub_text = "#a0a0a0"
    border_color = "#444444"
    input_bg = "#1e1e1e"
    input_text = "#ffffff"
    header_gradient = "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)"
    shadow_val = "0 4px 6px rgba(255,255,255,0.05)"
else:
    main_bg = "#f8fafc"
    card_bg = "#ffffff"
    text_color = "#000000"
    sub_text = "#555555"
    border_color = "#ddd"
    input_bg = "#f0f9ff"
    input_text = "#1e3a8a"
    header_gradient = "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)"
    shadow_val = "0 4px 6px rgba(0,0,0,0.1)"

# --- [دوال الخدمات الأساسية] ---
def clean_phone_number(phone):
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def get_professional_msg(name, b_type, b_desc, date):
    msg = (f"🔔 *إشعار من منصة الأستاذ زياد*\n"
            f"------------------\n"
            f"👤 *الطالب:* {name}\n"
            f"📍 *الملاحظة:* {b_type}\n"
            f"📝 *التفاصيل:* {b_desc if b_desc else 'متابعة دورية'}\n"
            f"📅 *التاريخ:* {date}\n"
            f"------------------\n"
            f"🏛️ *منصة زياد الذكية*")
    return urllib.parse.quote(msg)

def show_footer():
    st.markdown("<br><h3 style='text-align:center; color:#1e40af;'>📱 قنوات التواصل والدعم الفني</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown('<a href="#" class="contact-btn">📢 تليجرام الإدارة 👉</a>', unsafe_allow_html=True)
    c2.markdown('<a href="#" class="contact-btn">💬 واتساب المعلم 👉</a>', unsafe_allow_html=True)
    c3.markdown('<a href="#" class="contact-btn">📧 البريد الإلكتروني 👉</a>', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:{sub_text}; font-size:0.8rem; margin-top:20px;'>© 2026 جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية</p>", unsafe_allow_html=True)

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}"); return None

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
        row_to_append = [data_dict.get(h, "") for h in headers]
        ws.append_row(row_to_append); return True
    except: return False

# --- تحميل الإعدادات ---
if "class_options" not in st.session_state:
    try:
        sett_data = sh.worksheet("settings").get_all_records()
        settings_map = {row['key']: row['value'] for row in sett_data}
        st.session_state.max_tasks = int(settings_map.get('max_tasks', 60))
        st.session_state.max_quiz = int(settings_map.get('max_quiz', 40))
        st.session_state.current_year = str(settings_map.get('current_year', '1447هـ'))
        classes_str = str(settings_map.get('class_list', 'الأول, الثاني'))
        st.session_state.class_options = [c.strip() for c in classes_str.split(',') if c.strip()]
        stages_str = str(settings_map.get('stage_list', 'ابتدائي'))
        st.session_state.stage_options = [s.strip() for s in stages_str.split(',') if s.strip()]
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        st.session_state.class_options = ["الأول", "الثاني"]
        st.session_state.stage_options = ["ابتدائي"]

if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = None

# ==========================================
# 🎨 2. التصميم (CSS)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{ 
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; 
        background-color: {main_bg} !important; color: {text_color} !important;
    }}
    .block-container {{ padding-top: 0rem; padding-bottom: 5rem; }}
    
    .header-container {{
        display: flex; flex-direction: row-reverse; align-items: center; justify-content: center;
        background: {header_gradient};
        padding-top: 80px; padding-bottom: 40px; padding-left: 20px; padding-right: 20px;
        border-radius: 0 0 35px 35px; margin-top: -60px; margin-left: -5rem; margin-right: -5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15); color: white; text-align: center;
    }}
    .logo-icon {{ font-size: 6rem; margin-right: 25px; margin-top: 15px; filter: drop-shadow(0px 5px 10px rgba(0,0,0,0.3)); animation: float 3s ease-in-out infinite; }}
    .header-text h1 {{ margin: 0; font-size: 3rem; font-weight: 900; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); line-height: 1.2; color: #ffffff !important; }}
    .header-text p {{ margin: 5px 0 0 0; color: #dbeafe; font-size: 1.2rem; font-weight: bold; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}

    @media (max-width: 768px) {{
        .header-container {{ flex-direction: column; padding-top: 100px; padding-bottom: 30px; }}
        .logo-icon {{ font-size: 5rem; margin-right: 0; margin-top: 0; margin-bottom: 10px; }}
        .header-text h1 {{ font-size: 2.2rem; }}
    }}

    div[data-baseweb="input"] {{ background-color: {input_bg} !important; border: 2px solid {border_color} !important; border-radius: 12px !important; height: 50px; }}
    input {{ color: {input_text} !important; font-weight: bold !important; font-size: 1.1rem !important; }}
    
    .contact-btn {{ display: block; padding: 12px; background: {card_bg}; border: 2px solid {border_color}; border-radius: 12px; color: {text_color} !important; text-decoration: none; font-weight: bold; text-align: center; margin-bottom: 10px; transition: 0.3s; }}
    .contact-btn:hover {{ background: #eff6ff; border-color: #3b82f6; transform: translateY(-2px); color: #1e3a8a !important; }}
    
    /* تنسيقات الطالب */
    .app-header {{ background: {card_bg}; padding: 20px; border-radius: 15px; border-right: 10px solid #1e3a8a; box-shadow: {shadow_val}; margin-top: -20px; text-align: right; border: 1px solid {border_color}; }}
    .medal-flex {{ display: flex; justify-content: space-between; gap: 8px; margin: 15px 0; }}
    .m-card {{ flex: 1; background: {card_bg}; padding: 15px 5px; border-radius: 15px; text-align: center; border: 2px solid {border_color}; box-shadow: {shadow_val}; transition: 0.3s; }}
    .m-active {{ border-color: #f59e0b !important; background: #fffbeb !important; box-shadow: 0 4px 8px rgba(245,158,11,0.2) !important; }}
    .points-banner {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 6px 12px rgba(217, 119, 6, 0.2); }}
    .mobile-card {{ background: {card_bg}; color: {text_color}; padding: 18px; border-radius: 12px; border: 1.5px solid {border_color}; margin-bottom: 12px; font-weight: 800; box-shadow: {shadow_val}; border-right: 8px solid #1e3a8a; font-size: 1.1rem; }}
    .urgent-msg {{ background: #fff5f5; border: 2px solid #e53e3e; color: #c53030 !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; font-weight: 900; box-shadow: 0 4px 10px rgba(229, 62, 62, 0.1); }}
    
    h1, h2, h3, h4, h5, h6, p, span, div {{ color: {text_color}; }}
    small {{ color: {sub_text} !important; }}
    </style>

    <div class="header-container">
        <div class="logo-icon">🎓</div>
        <div class="header-text">
            <h1>منصة الأستاذ زياد الذكية</h1>
            <p>بوابة التعليم المتطورة والإدارة الشاملة - 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 3. نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم"])
    with t1:
        with st.form("st_log_v26"):
            sid_in = st.text_input("🆔 الرقم الأكاديمي الموحد").strip()
            if st.form_submit_button("انطلق للمنصة 🚀", use_container_width=True):
                df_st = fetch_safe("students")
                if not df_st.empty:
                    df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                    if sid_in.split('.')[0] in df_st['clean_id'].values:
                        st.session_state.username, st.session_state.role = sid_in.split('.')[0], "student"; st.rerun()
                    else: st.error("❌ الرقم غير مسجل. تواصل مع معلمك.")
    with t2:
        with st.form("admin_log_v26"):
            u = st.text_input("👤 اسم المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة 🛠️", use_container_width=True):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    user_data = df_u[df_u['username']==u].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role, st.session_state.username = "teacher", u; st.rerun()
                st.error("❌ بيانات خاطئة.")
    show_footer()

# ==========================================
# 👨‍🏫 4. واجهة المعلم
# ==========================================
elif st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # 👥 الطلاب
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            unique_classes = len(df_st.iloc[:, 2].unique()) if len(df_st.columns) > 2 else 0
            c2.metric("🏫 الفصول", unique_classes)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            st.divider()

            with st.expander("➕ إضافة طالب جديد", expanded=True):
                with st.form("add_st_v26", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    f_id = c1.text_input("🔢 الرقم الأكاديمي")
                    f_name = c2.text_input("👤 الاسم")
                    c3, c4, c5 = st.columns(3)
                    f_class = c3.selectbox("الصف", st.session_state.get('class_options', ['الأول']))
                    f_stage = c4.selectbox("المرحلة", st.session_state.get('stage_options', ['ابتدائي']))
                    f_year = c5.text_input("العام", st.session_state.get('current_year', '1447هـ'))
                    c6, c7 = st.columns(2)
                    f_phone = c6.text_input("📱 الجوال")
                    f_mail = c7.text_input("📧 الإيميل")
                    if st.form_submit_button("✅ حفظ"):
                        if f_id and f_name:
                            cl_p = clean_phone_number(f_phone) if f_phone else ""
                            st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "الجوال": cl_p, "الإيميل": f_mail.strip(), "النقاط": "0"}
                            if safe_append_row("students", st_map):
                                st.success("✅ تم الحفظ"); st.cache_data.clear(); st.rerun()
            
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
        st.subheader("📊 مركز التقييم")
        df_eval = fetch_safe("students")
        if not df_eval.empty:
            st_list = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_eval.iterrows()}
            sel = st.selectbox("🎯 اختر الطالب:", [""] + list(st_list.keys()))
            if sel:
                sid = st_list[sel]
                s_info = df_eval[df_eval.iloc[:, 0] == sid].iloc[0]
                s_name = s_info['name']
                cl_p = clean_phone_number(s_info.get('الجوال', ''))
                s_mail = s_info.get('الإيميل', '')
                
                c_g, c_b = st.columns(2)
                with c_g:
                    st.markdown("##### 📝 الدرجات")
                    df_gr_curr = fetch_safe("grades")
                    curr_p1 = 0; curr_p2 = 0
                    if not df_gr_curr.empty:
                        gr_row = df_gr_curr[df_gr_curr.iloc[:,0] == sid]
                        if not gr_row.empty:
                            curr_p1 = int(pd.to_numeric(gr_row.iloc[0]['p1'], errors='coerce') or 0)
                            curr_p2 = int(pd.to_numeric(gr_row.iloc[0]['p2'], errors='coerce') or 0)
                    
                    with st.form("gr_f"):
                        v1 = st.number_input("مشاركة", 0, st.session_state.max_tasks, curr_p1)
                        v2 = st.number_input("اختبار", 0, st.session_state.max_quiz, curr_p2)
                        if st.form_submit_button("💾 تحديث"):
                            ws_gr = sh.worksheet("grades")
                            cell = ws_gr.find(sid)
                            tot = v1 + v2
                            if cell:
                                ws_gr.update_cell(cell.row, 2, v1); ws_gr.update_cell(cell.row, 3, v2)
                                ws_gr.update_cell(cell.row, 4, tot); ws_gr.update_cell(cell.row, 5, str(datetime.date.today()))
                            else: ws_gr.append_row([sid, v1, v2, tot, str(datetime.date.today())])
                            st.success("✅ تم"); st.cache_data.clear()

                with c_b:
                    st.markdown("##### 🎭 السلوك")
                    with st.form("beh_f"):
                        bt = st.selectbox("السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🚫 سلبي (-10)"])
                        bm = st.text_area("ملاحظة")
                        if st.form_submit_button("💾 تسجيل"):
                            safe_append_row("behavior", {"student_id": sid, "date": str(datetime.date.today()), "type": bt, "note": bm})
                            # تحديث النقاط
                            score_match = re.search(r'\(([\+\-]?\d+)\)', bt)
                            chg = int(score_match.group(1)) if score_match else 0
                            if chg != 0:
                                ws_st = sh.worksheet("students"); cell = ws_st.find(sid)
                                if cell:
                                    headers = ws_st.row_values(1)
                                    if 'النقاط' in headers:
                                        c_idx = headers.index('النقاط') + 1
                                        cur = ws_st.cell(cell.row, c_idx).value
                                        ws_st.update_cell(cell.row, c_idx, (int(cur) if cur and str(cur).isdigit() else 0) + chg)
                            st.success("✅ تم"); st.cache_data.clear(); st.rerun()

                st.divider()
                df_beh = fetch_safe("behavior")
                if not df_beh.empty:
                    col_id = 'student_id' if 'student_id' in df_beh.columns else df_beh.columns[0]
                    my_beh = df_beh[df_beh[col_id].astype(str) == str(sid)]
                    for idx, r in my_beh.iterrows():
                        with st.container(border=True):
                            xc1, xc2, xc3 = st.columns([3, 1, 0.5])
                            with xc1: st.write(f"{r.get('type')} | {r.get('date')}"); st.caption(r.get('note'))
                            with xc2: 
                                msg = get_professional_msg(s_name, r.get('type'), r.get('note'), r.get('date'))
                                st.link_button("واتساب", f"https://api.whatsapp.com/send?phone={cl_p}&text={msg}", use_container_width=True)
                            with xc3:
                                if st.button("🗑️", key=f"del_{idx}"):
                                    sh.worksheet("behavior").delete_rows(int(idx)+2); st.success("تم"); st.cache_data.clear(); st.rerun()

    # 📢 التنبيهات
    with menu[2]:
        st.subheader("📢 التنبيهات")
        with st.form("ann_f"):
            at = st.text_input("العنوان"); ad = st.text_area("التفاصيل"); au = st.checkbox("عاجل")
            atg = st.selectbox("الفئة", ["الكل"] + st.session_state.class_options)
            if st.form_submit_button("نشر"):
                safe_append_row("exams", {"الصف": atg, "عاجل": "نعم" if au else "لا", "العنوان": at, "التاريخ": str(datetime.date.today()), "الرابط": ad})
                st.success("✅ تم"); st.cache_data.clear(); st.rerun()
        st.divider()
        df_ann = fetch_safe("exams")
        for idx, row in df_ann.iloc[::-1].iterrows():
            with st.container(border=True):
                ac1, ac2 = st.columns([3, 1])
                ac1.write(f"**{row.get('العنوان')}** ({row.get('الصف')})"); ac1.caption(row.get('الرابط'))
                if ac2.button("حذف", key=f"da_{idx}"):
                    sh.worksheet("exams").delete_rows(int(idx)+2); st.cache_data.clear(); st.rerun()

    # ⚙️ الإعدادات
    with menu[3]:
        st.subheader("⚙️ الإعدادات")
        with st.expander("🛠️ النظام والبيانات"):
            if st.button("🔄 تحديث"): st.cache_data.clear(); st.rerun()
            if st.button("🧹 تصفير النقاط"):
                ws = sh.worksheet("students"); d = ws.get_all_values()
                if len(d) > 1: ws.update(f"I2:I{len(d)}", [[0]]*(len(d)-1)); st.success("تم")

        with st.expander("📝 القوائم والدرجات"):
            cy = st.text_input("العام", st.session_state.current_year)
            cls = st.text_area("الصفوف", ",".join(st.session_state.class_options))
            stg = st.text_area("المراحل", ",".join(st.session_state.stage_options))
            mt = st.number_input("مشاركة", 0, 100, st.session_state.max_tasks)
            mq = st.number_input("اختبار", 0, 100, st.session_state.max_quiz)
            if st.button("حفظ الإعدادات"):
                ws = sh.worksheet("settings")
                ws.batch_update([{'range': 'B2', 'values': [[mt]]}, {'range': 'B3', 'values': [[mq]]}, {'range': 'B4', 'values': [[cy]]}, {'range': 'B5', 'values': [[cls]]}, {'range': 'B6', 'values': [[stg]]}])
                st.session_state.max_tasks = mt; st.session_state.max_quiz = mq
                st.session_state.current_year = cy
                st.session_state.class_options = [x.strip() for x in cls.split(',') if x.strip()]
                st.session_state.stage_options = [x.strip() for x in stg.split(',') if x.strip()]
                st.success("تم"); st.cache_data.clear(); st.rerun()

        with st.expander("📤 المزامنة (Excel)"):
            up = st.file_uploader("ملف XLSX", type=['xlsx'])
            ts = st.radio("الجدول", ["students", "grades"], horizontal=True)
            if st.button("بدء") and up:
                df = pd.read_excel(up).fillna("").dropna(how='all'); ws = sh.worksheet(ts)
                c_ids = [str(r.get('id', r.get('student_id', ''))) for r in ws.get_all_records()]
                h = ws.row_values(1)
                for _, r in df.iterrows():
                    d = r.to_dict(); raw_id = str(d.get('student_id', d.get('id', ''))).strip().split('.')[0]
                    if not raw_id or raw_id == '0': continue
                    if ts == "grades":
                        d.update({"student_id": raw_id, "p1": int(d.get('p1',0)), "p2": int(d.get('p2',0)), "perf": int(d.get('p1',0))+int(d.get('p2',0)), "date": str(datetime.date.today())})
                        if 'id' in d: del d['id']
                    else:
                        d['id'] = raw_id; d['الجوال'] = clean_phone_number(d.get('الجوال',''))
                        if 'النقاط' not in d or str(d.get('النقاط', '')).strip() == "": d['النقاط'] = 0
                    
                    if raw_id in c_ids: ws.update(f"A{c_ids.index(raw_id)+2}", [[str(d.get(k, "")) for k in h]])
                    else: ws.append_row([str(d.get(k, "")) for k in h])
                st.success("تم"); st.cache_data.clear(); st.rerun()

        with st.expander("🔐 المستخدمين"):
            with st.form("u_add"):
                nu = st.text_input("اسم"); np = st.text_input("باسورد", type="password")
                if st.form_submit_button("إضافة"):
                    safe_append_row("users", {"username": nu, "password_hash": hashlib.sha256(str.encode(np)).hexdigest(), "role": "teacher"})
                    st.success("تم")

    with menu[4]:
        if st.button("خروج"): st.session_state.role = None; st.rerun()
    show_footer()

# ==========================================
# 👨‍🎓 5. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    student_id = str(st.session_state.get('username', '')).strip()
    df_st = fetch_safe("students"); df_gr = fetch_safe("grades"); df_beh = fetch_safe("behavior"); df_ann = fetch_safe("exams")
    
    if not df_st.empty:
        df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
        my_info = df_st[df_st['clean_id'] == student_id]
    else: my_info = pd.DataFrame()

    if not my_info.empty:
        s_data = my_info.iloc[0]
        s_name = s_data.get('name', 'طالب'); s_class = str(s_data.get('class', '')).strip()
        s_points = int(pd.to_numeric(s_data.get('النقاط', 0), errors='coerce') or 0)

        st.markdown(f"""
            <div class="app-header"><h2>👋 مرحباً: {s_name}</h2><p>🏫 {s_class} | 🆔 {student_id}</p></div>
            <div class="medal-flex">
                <div class="m-card {'m-active' if s_points >= 100 else ''}">🥇<br><b>ذهبي</b></div>
                <div class="m-card {'m-active' if s_points >= 50 else ''}">🥈<br><b>فضي</b></div>
                <div class="m-card m-active">🥉<br><b>برونزي</b></div>
            </div>
            <div class="points-banner"><p>النقاط</p><h1>{s_points}</h1></div>
        """, unsafe_allow_html=True)

        # التنبيه العاجل
        if not df_ann.empty:
            df_ann['عاجل'] = df_ann['عاجل'].astype(str).str.strip(); df_ann['الصف'] = df_ann['الصف'].astype(str).str.strip()
            urgent = df_ann[(df_ann['عاجل'] == 'نعم') & (df_ann['الصف'].isin(['الكل', s_class]))]
            if not urgent.empty:
                u = urgent.tail(1).iloc[0]
                st.markdown(f"<div class='urgent-msg'>🚨 {u.get('العنوان')}</div>", unsafe_allow_html=True)

        tabs = st.tabs(["📢 تنبيهات", "📝 ملاحظات", "📊 درجات", "🏆 المتصدرين", "⚙️ إعدادات"])
        
        with tabs[0]:
            if not df_ann.empty:
                st_ann = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_class])]
                for _, r in st_ann.iloc[::-1].iterrows():
                    st.markdown(f"<div class='mobile-card'>📢 {r.get('العنوان')}<br><small>{r.get('التاريخ')}</small><p>{r.get('الرابط')}</p></div>", unsafe_allow_html=True)
            else: st.info("لا يوجد تنبيهات")

        with tabs[1]:
            if not df_beh.empty:
                df_beh['clean_id'] = df_beh.iloc[:, 0].astype(str).str.split('.').str[0]
                mn = df_beh[df_beh['clean_id'] == student_id]
                if not mn.empty:
                    for _, n in mn.iterrows():
                        st.markdown(f"<div class='mobile-card' style='border-right-color:#e53e3e'>📌 {n.get('type')}: {n.get('note')}<br><small>{n.get('date')}</small></div>", unsafe_allow_html=True)
                else: st.success("سجلك نظيف!")

        with tabs[2]:
            if not df_gr.empty:
                df_gr['clean_id'] = df_gr.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                mg = df_gr[df_gr['clean_id'] == student_id]
                if not mg.empty:
                    g = mg.iloc[0]
                    st.markdown(f"<div class='mobile-card'>📝 مشاركة: {g.get('p1')}</div><div class='mobile-card'>✍️ اختبار: {g.get('p2')}</div><div class='mobile-card' style='background:#f0fdf4'>🏆 المجموع: {g.get('perf')}</div>", unsafe_allow_html=True)
                else: st.info("لا توجد درجات")

        with tabs[3]:
            df_st['p_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            for i, (_, r) in enumerate(df_st.sort_values('p_num', ascending=False).head(10).iterrows(), 1):
                ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else str(i)
                style = "border:2px solid #1e3a8a" if str(r['clean_id']) == student_id else ""
                st.markdown(f"<div class='mobile-card' style='{style}'><span>{ic}</span> {r['name']} <span style='float:left;color:#f59e0b'>{int(r['p_num'])}</span></div>", unsafe_allow_html=True)

        with tabs[4]:
            with st.form("up_info"):
                nm = st.text_input("إيميل", s_data.get('الإيميل','')); np = st.text_input("جوال", s_data.get('الجوال',''))
                if st.form_submit_button("حفظ"):
                    try:
                        fp = clean_phone_number(np) if np else ""
                        ws = sh.worksheet("students"); cell = ws.find(student_id)
                        if cell:
                            h = ws.row_values(1)
                            if 'الإيميل' in h and 'الجوال' in h:
                                ws.update_cell(cell.row, h.index('الإيميل')+1, nm); ws.update_cell(cell.row, h.index('الجوال')+1, fp)
                                st.success("تم"); st.cache_data.clear(); st.rerun()
                    except: st.error("خطأ")
            st.divider()
            if st.button("خروج"): st.session_state.role = None; st.rerun()
    else: st.error("غير مسجل"); st.button("عودة", on_click=st.rerun)
    show_footer()
