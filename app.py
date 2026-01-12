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

# --- 🎨 تعريف الألوان ---
main_bg = "#f8fafc"
card_bg = "#ffffff"
text_color = "#0f172a"
sub_text = "#64748b"
border_color = "#e2e8f0"
primary_color = "#1e3a8a"
accent_color = "#3b82f6"
header_grad = "linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)"
shadow_val = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"

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
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: {sub_text}; padding: 20px; border-top: 1px solid {border_color};'>
        <p style='margin-bottom: 10px; font-size: 0.9rem;'>جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية © 2026</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.link_button("📢 تليجرام الإدارة", "#", use_container_width=True)
    c2.link_button("💬 واتساب المعلم", "#", use_container_width=True)
    c3.link_button("📧 الدعم الفني", "#", use_container_width=True)

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
# 🎨 2. التصميم (CSS - Modern Theme)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
    
    section[data-testid="stSidebar"] {{ display: none; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    html, body, [data-testid="stAppViewContainer"] {{ 
        font-family: 'Tajawal', sans-serif !important; 
        direction: RTL; text-align: right; 
        background-color: {main_bg} !important; color: {text_color} !important; 
    }}
    
    .block-container {{ padding-top: 0rem; padding-bottom: 5rem; max-width: 1000px; }}
    
    /* --- الهيدر (تم تعديل المسافة العلوية) --- */
    .header-container {{
        background: {header_grad};
        padding: 80px 20px 40px 20px; /* زيادة المسافة العلوية لمنع القص */
        border-radius: 0 0 40px 40px;
        margin: -60px -5rem 30px -5rem;
        box-shadow: 0 10px 30px -10px rgba(30, 58, 138, 0.5);
        color: white; text-align: center;
        position: relative; overflow: visible; /* السماح للعناصر بالخروج */
    }}
    
    .logo-icon {{ 
        font-size: 5rem; margin-bottom: 15px; display: inline-block;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
        animation: float 4s ease-in-out infinite;
    }}
    
    .header-text h1 {{ margin: 0; font-size: 2.5rem; font-weight: 900; color: #fff !important; }}
    .header-text p {{ margin: 5px 0 0 0; color: #bfdbfe; font-size: 1.1rem; font-weight: 500; }}
    
    /* --- الحقول والأزرار --- */
    div[data-baseweb="input"] {{ background-color: #ffffff !important; border-radius: 16px !important; height: 55px; border: 1px solid #cbd5e1 !important; }}
    input {{ font-weight: 700 !important; font-size: 1.1rem !important; }}
    
    div.stButton > button {{
        background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%) !important;
        color: white !important; border: none !important; font-weight: 800 !important;
        font-size: 1.1rem !important; border-radius: 16px !important; padding: 12px 20px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); transition: transform 0.2s; width: 100%; height: 55px;
    }}
    div.stButton > button:active {{ transform: scale(0.98); }}
    button[kind="secondary"] {{ background: #f1f5f9 !important; color: #334155 !important; box-shadow: none !important; border: 1px solid #e2e8f0 !important; }}

    .app-card {{ background: {card_bg}; padding: 20px; border-radius: 24px; box-shadow: {shadow_val}; border: 1px solid #f1f5f9; margin-bottom: 15px; }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: transparent; border: none; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; color: #64748b; font-weight: bold; flex: 1; justify-content: center; }}
    .stTabs [aria-selected="true"] {{ background-color: {primary_color} !important; color: white !important; border: none !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); }}

    /* --- عناصر الطالب --- */
    .medal-flex {{ display: flex; gap: 10px; margin: 20px 0; direction: rtl; }}
    .m-card {{ flex: 1; background: white; padding: 15px 5px; border-radius: 20px; text-align: center; border: 1px solid #e2e8f0; box-shadow: {shadow_val}; transition: transform 0.3s; }}
    .m-active {{ border: 2px solid #f59e0b !important; background: linear-gradient(to bottom right, #fffbeb, #fef3c7) !important; transform: translateY(-5px); }}
    
    .points-banner {{ 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 25px; border-radius: 24px; 
        text-align: center; margin-bottom: 25px; box-shadow: 0 10px 20px -5px rgba(245, 158, 11, 0.4);
    }}
    
    /* بطاقة الترحيب */
    .welcome-card {{
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 20px; border-radius: 24px;
        margin-bottom: 15px; box-shadow: 0 8px 16px -4px rgba(30, 58, 138, 0.4);
        position: relative; overflow: hidden;
    }}
    
    .mobile-list-item {{ background: white; border-radius: 16px; padding: 16px; margin-bottom: 12px; border: 1px solid #f1f5f9; box-shadow: 0 2px 4px rgba(0,0,0,0.03); display: flex; align-items: center; justify-content: space-between; }}

    /* Animations */
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    
    /* وميض قوي للإعلان العاجل */
    @keyframes pulse-red {{
        0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); transform: scale(1); }}
        70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); transform: scale(1.02); }}
        100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); transform: scale(1); }}
    }}
    
    .urgent-box {{
        background-color: #fef2f2; border: 2px solid #ef4444; color: #b91c1c;
        padding: 15px; border-radius: 16px; text-align: center; 
        animation: pulse-red 2s infinite; /* تفعيل الوميض */
        font-weight: bold; margin-bottom: 25px;
    }}

    @media (max-width: 768px) {{
        .header-container {{ padding: 70px 20px 30px 20px; }}
        .header-text h1 {{ font-size: 1.8rem; }}
        .logo-icon {{ font-size: 4rem; }}
    }}
    </style>

    <div class="header-container">
        <div class="header-content">
            <div class="logo-icon">🎓</div>
            <div class="header-text">
                <h1>منصة الأستاذ زياد</h1>
                <p>بوابة التعليم الذكية 2026</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 3. نظام الدخول
# ==========================================
if st.session_state.role is None:
    c1, c2 = st.columns([1, 10]) 
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم"])
    
    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("st_login"):
            st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>تسجيل دخول الطالب</h4>", unsafe_allow_html=True)
            sid = st.text_input("رقم الهوية / الرقم الأكاديمي", placeholder="أدخل الرقم هنا...").strip()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 دخول للمنصة", type="primary", use_container_width=True):
                df = fetch_safe("students")
                if not df.empty:
                    df['clean_id'] = df.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
                    if sid.split('.')[0] in df['clean_id'].values:
                        st.session_state.username = sid.split('.')[0]
                        st.session_state.role = "student"
                        st.rerun()
                    else: st.error("⚠️ الرقم غير مسجل في النظام")
    with t2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("tr_login"):
            st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>تسجيل دخول المعلم</h4>", unsafe_allow_html=True)
            u = st.text_input("اسم المستخدم", placeholder="User"); 
            p = st.text_input("كلمة المرور", type="password", placeholder="******")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🛠️ دخول لوحة التحكم", type="primary", use_container_width=True):
                df = fetch_safe("users")
                if not df.empty and u in df['username'].values:
                    ud = df[df['username']==u].iloc[0]
                    if hashlib.sha256(p.encode()).hexdigest() == ud['password_hash']:
                        st.session_state.username = u; st.session_state.role = "teacher"; st.rerun()
                st.error("❌ بيانات الدخول غير صحيحة")
    show_footer()

# ==========================================
# 👨‍🏫 4. واجهة المعلم
# ==========================================
elif st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "⚙️ الإعدادات", "🛑 خروج"])

    # --- 👥 الطلاب ---
    with menu[0]:
        st.markdown("### 👥 سجل الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='app-card' style='text-align:center'><h4>الطلاب</h4><h2>{len(df_st)}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='app-card' style='text-align:center'><h4>الفصول</h4><h2>{len(df_st.iloc[:,2].unique()) if len(df_st.columns)>2 else 0}</h2></div>", unsafe_allow_html=True)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            with c3: st.markdown(f"<div class='app-card' style='text-align:center'><h4>متوسط النقاط</h4><h2>{round(df_st['النقاط'].mean(), 1)}</h2></div>", unsafe_allow_html=True)

            with st.expander("➕ تسجيل طالب جديد", expanded=False):
                with st.form("add_st_v26", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    f_id = c1.text_input("🔢 الرقم الأكاديمي")
                    f_name = c2.text_input("👤 اسم الطالب")
                    c3, c4, c5 = st.columns(3)
                    f_class = c3.selectbox("الصف", st.session_state.class_options)
                    f_stage = c4.selectbox("المرحلة", st.session_state.stage_options)
                    f_year = c5.text_input("العام الدراسي", st.session_state.current_year)
                    c6, c7 = st.columns(2)
                    f_phone = c6.text_input("📱 رقم الجوال")
                    f_mail = c7.text_input("📧 البريد الإلكتروني")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("✅ حفظ البيانات", type="primary"):
                        if f_id and f_name:
                            if f_id.strip() in df_st['clean_id'].values:
                                st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً!")
                            else:
                                cl_p = clean_phone_number(f_phone) if f_phone else ""
                                st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "الجوال": cl_p, "الإيميل": f_mail.strip(), "النقاط": "0"}
                                if safe_append_row("students", st_map):
                                    st.success("✅ تم الحفظ بنجاح"); st.cache_data.clear(); st.rerun()
                        else: st.warning("الرجاء إكمال البيانات الأساسية")
            
            st.divider()
            sq = st.text_input("🔍 بحث عن طالب (بالاسم أو الرقم):")
            if sq: st.dataframe(df_st[df_st.iloc[:,0].str.contains(sq)|df_st.iloc[:,1].str.contains(sq)], use_container_width=True, hide_index=True)
            else: st.dataframe(df_st, use_container_width=True, hide_index=True)

            with st.expander("🗑️ حذف طالب"):
                dq = st.text_input("أدخل اسم أو رقم الطالب للحذف:", key="dq")
                if dq:
                    for i, r in df_st[df_st.iloc[:,0].str.contains(dq)|df_st.iloc[:,1].str.contains(dq)].iterrows():
                        if st.button(f"🗑️ حذف السجل: {r.iloc[1]}", key=f"d{i}"):
                            sh.worksheet("students").delete_rows(int(i)+2); st.success("تم الحذف"); st.cache_data.clear(); st.rerun()
        else: st.info("قاعدة البيانات فارغة حالياً")

    # 📊 التقييم
    with menu[1]:
        st.markdown("### 📊 التقييم والمتابعة")
        df_ev = fetch_safe("students")
        if not df_ev.empty:
            st_dict = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_ev.iterrows()}
            sel = st.selectbox("🎯 اختر الطالب من القائمة:", [""] + list(st_dict.keys()))
            if sel:
                sid = st_dict[sel]
                s_inf = df_ev[df_ev.iloc[:,0] == sid].iloc[0]
                s_nm = s_inf['name']; clp = clean_phone_number(s_inf.get('الجوال',''))
                s_eml = s_inf.get('الإيميل', '')
                
                c1, c2 = st.columns(2)
                with c1:
                    st.container(border=True)
                    st.markdown("##### 📝 رصد الدرجات")
                    df_g = fetch_safe("grades")
                    cur_p1 = 0; cur_p2 = 0
                    if not df_g.empty:
                        gr = df_g[df_g.iloc[:,0]==sid]
                        if not gr.empty:
                            cur_p1 = int(pd.to_numeric(gr.iloc[0]['p1'], errors='coerce') or 0)
                            cur_p2 = int(pd.to_numeric(gr.iloc[0]['p2'], errors='coerce') or 0)
                    
                    with st.form("gr_upd"):
                        v1 = st.number_input("درجة المشاركة", 0, st.session_state.max_tasks, cur_p1)
                        v2 = st.number_input("درجة الاختبار", 0, st.session_state.max_quiz, cur_p2)
                        if st.form_submit_button("💾 حفظ الدرجات", type="primary"):
                            ws = sh.worksheet("grades"); cell = ws.find(sid); tot = v1+v2
                            if cell:
                                ws.update_cell(cell.row, 2, v1); ws.update_cell(cell.row, 3, v2)
                                ws.update_cell(cell.row, 4, tot); ws.update_cell(cell.row, 5, str(datetime.date.today()))
                            else: ws.append_row([sid, v1, v2, tot, str(datetime.date.today())])
                            st.success("✅ تم التحديث"); st.cache_data.clear(); st.rerun()
                    
                    st.caption(f"📊 المجموع الحالي: {cur_p1 + cur_p2}")

                with c2:
                    st.container(border=True)
                    st.markdown("##### 🎭 السلوك والملاحظات")
                    with st.form("beh_add"):
                        bt = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🚫 سلبي (-10)"])
                        bn = st.text_area("تفاصيل الملاحظة")
                        if st.form_submit_button("💾 تسجيل السلوك", type="primary"):
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
                                        st.toast(f"📈 الرصيد الجديد: {new_val}", icon="💰")
                            st.success("✅ تم التسجيل"); st.cache_data.clear(); st.rerun()

                st.markdown("#### 📜 سجل السلوك الأخير")
                df_b = fetch_safe("behavior")
                if not df_b.empty:
                    cid = 'student_id' if 'student_id' in df_b.columns else df_b.columns[0]
                    my_b = df_b[df_b[cid].astype(str) == str(sid)]
                    # عكس الترتيب هنا أيضاً للمعلم
                    for i, r in my_b.iloc[::-1].iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div class="mobile-list-item">
                                <div>
                                    <b>{r.get('type')}</b> | <small>{r.get('date')}</small><br>
                                    <span style="color:#64748b">{r.get('note')}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_del, c_wa, c_em = st.columns([0.5, 1, 1])
                            lnk = get_professional_msg(s_nm, r.get('type'), r.get('note'), r.get('date'))
                            c_wa.link_button("واتساب", f"https://api.whatsapp.com/send?phone={clp}&text={lnk}", use_container_width=True)
                            c_em.link_button("إيميل", f"mailto:{s_eml}?subject=ملاحظة: {s_nm}&body={lnk}", use_container_width=True)
                            if c_del.button("❌", key=f"dl{i}"):
                                sh.worksheet("behavior").delete_rows(int(i)+2); st.success("حُذف"); st.cache_data.clear(); st.rerun()

    # 📢 التنبيهات
    with menu[2]:
        st.markdown("### 📢 لوحة الإعلانات والتعاميم")
        with st.form("ann_add"):
            c1, c2 = st.columns([3, 1])
            at = c1.text_input("عنوان الإعلان")
            atg = c2.selectbox("الفئة المستهدفة", ["الكل"] + st.session_state.class_options)
            ad = st.text_area("نص الإعلان أو الرابط")
            au = st.checkbox("🔥 تعميم عاجل (يظهر بشكل بارز)")
            
            if st.form_submit_button("📣 نشر التعميم", type="primary"):
                safe_append_row("exams", {"الصف": atg, "عاجل": "نعم" if au else "لا", "العنوان": at, "التاريخ": str(datetime.date.today()), "الرابط": ad})
                st.success("✅ تم النشر"); st.cache_data.clear(); st.rerun()
        
        st.divider()
        df_a = fetch_safe("exams")
        for i, r in df_a.iloc[::-1].iterrows():
            with st.container():
                is_urgent = r.get('عاجل') == 'نعم'
                border_style = "2px solid #ef4444" if is_urgent else "1px solid #e2e8f0"
                bg_style = "#fef2f2" if is_urgent else "#ffffff"
                
                st.markdown(f"""
                <div style="background:{bg_style}; border:{border_style}; border-radius:12px; padding:15px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <h4 style="margin:0">{r.get('العنوان')}</h4>
                        <span style="background:white; padding:2px 8px; border-radius:8px; font-size:0.8rem">{r.get('التاريخ')}</span>
                    </div>
                    <p style="margin:5px 0 0 0; color:#475569">{r.get('الرابط')}</p>
                    <small>الفئة: {r.get('الصف')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                kc1, kc2 = st.columns([1, 4])
                msg_text = (f"📢 *تعميم هام من منصة الأستاذ زياد*\n"
                            f"━━━━━━━━━━━━\n"
                            f"📌 *العنوان:* {r.get('العنوان')}\n"
                            f"📄 *التفاصيل:* {r.get('الرابط')}\n"
                            f"📅 *التاريخ:* {r.get('التاريخ')}\n"
                            f"━━━━━━━━━━━━")
                grp_msg = urllib.parse.quote(msg_text)
                kc2.link_button("📲 مشاركة عبر واتساب", f"https://api.whatsapp.com/send?text={grp_msg}", use_container_width=True)
                if kc1.button("🗑️", key=f"da{i}"):
                    sh.worksheet("exams").delete_rows(int(i)+2); st.rerun()

    # --- ⚙️ الإعدادات ---
    with menu[3]:
        st.markdown("### ⚙️ إعدادات النظام")
        
        with st.expander("🛠️ أدوات الصيانة", expanded=True):
            c1, c2 = st.columns(2)
            if c1.button("🔄 تحديث البيانات (Refresh)", use_container_width=True): st.cache_data.clear(); st.rerun()
            if c2.button("🧹 تصفير جميع النقاط", use_container_width=True):
                ws = sh.worksheet("students"); d = ws.get_all_values()
                if len(d)>1: ws.update(f"I2:I{len(d)}", [[0]]*(len(d)-1)); st.success("تم تصفير النقاط")

        with st.expander("📝 تهيئة الصفوف والدرجات"):
            cy = st.text_input("العام الدراسي", st.session_state.current_year)
            cls = st.text_area("قائمة الصفوف (افصل بفاصلة)", ",".join(st.session_state.class_options))
            stg = st.text_area("قائمة المراحل", ",".join(st.session_state.stage_options))
            c1, c2 = st.columns(2)
            mt = c1.number_input("الدرجة العظمى (مشاركة)", 0, 100, st.session_state.max_tasks)
            mq = c2.number_input("الدرجة العظمى (اختبار)", 0, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ الإعدادات", type="primary"):
                ws = sh.worksheet("settings")
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
                st.success("تم الحفظ بنجاح"); st.cache_data.clear(); st.rerun()

        with st.expander("📤 استيراد وتصدير (Excel)"):
            up = st.file_uploader("رفع ملف Excel", type=['xlsx'])
            ts = st.radio("نوع البيانات", ["students", "grades"], horizontal=True, format_func=lambda x: "بيانات الطلاب" if x == "students" else "الدرجات")
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
                st.success("تمت المزامنة بنجاح"); st.cache_data.clear(); st.rerun()
            
            st.divider()
            c1, c2 = st.columns(2)
            b1 = io.BytesIO()
            pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط"]).to_excel(b1, index=False)
            c1.download_button("📥 قالب الطلاب", b1.getvalue(), "students_template.xlsx", use_container_width=True)
            b2 = io.BytesIO()
            pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(b2, index=False)
            c2.download_button("📥 قالب الدرجات", b2.getvalue(), "grades_template.xlsx", use_container_width=True)

        with st.expander("🔐 إدارة المعلمين"):
            t1, t2 = st.tabs(["إضافة مستخدم", "تغيير كلمة المرور"])
            with t1:
                with st.form("add_u"):
                    nu = st.text_input("اسم المستخدم الجديد"); np = st.text_input("كلمة المرور", type="password")
                    if st.form_submit_button("إضافة معلم"):
                        safe_append_row("users", {"username": nu, "password_hash": hashlib.sha256(np.encode()).hexdigest(), "role": "teacher"})
                        st.success("تمت الإضافة")
            with t2:
                with st.form("chg_pass"):
                    npwd = st.text_input("كلمة المرور الجديدة", type="password")
                    if st.form_submit_button("تغيير"):
                        df_u = fetch_safe("users")
                        if st.session_state.username in df_u['username'].values:
                            idx = df_u[df_u['username']==st.session_state.username].index[0] + 2
                            sh.worksheet("users").update_cell(idx, 2, hashlib.sha256(npwd.encode()).hexdigest())
                            st.success("تم التغيير بنجاح")

    with menu[4]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("تسجيل الخروج", type="secondary"): st.session_state.role = None; st.rerun()
    show_footer()

# ==========================================
# 👨‍🎓 5. واجهة الطالب (Mobile App Style)
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

        # ✅ التنبيه العاجل مع وميض
        if not df_ann.empty:
            df_ann['عاجل'] = df_ann['عاجل'].astype(str).str.strip(); df_ann['الصف'] = df_ann['الصف'].astype(str).str.strip()
            urg = df_ann[(df_ann['عاجل']=='نعم') & (df_ann['الصف'].isin(['الكل', s_cls]))]
            if not urg.empty:
                u = urg.tail(1).iloc[0]
                st.markdown(f"<div class='urgent-box'>🚨 {u.get('العنوان')}<br><small style='color:#7f1d1d'>{u.get('الرابط')}</small></div>", unsafe_allow_html=True)

        # بطاقة الترحيب (تصميم جديد كبطاقة هوية)
        st.markdown(f"""
            <div class="welcome-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h2 style="color:white; margin:0; font-size:1.5rem;">👋 أهلاً بك، {s_nm}</h2>
                        <p style="color:#dbeafe; margin:5px 0 0 0;">{s_cls}</p>
                    </div>
                    <div style="background:rgba(255,255,255,0.2); padding:5px 15px; border-radius:12px;">
                        <span style="font-weight:bold; font-size:0.9rem;">ID: {sid}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # بنر النقاط الذهبي
        st.markdown(f"""
            <div class="points-banner">
                <p style="margin:0; opacity:0.9; font-size:0.9rem;">رصيد النقاط الحالي</p>
                <h1 style="margin:0; font-size:3.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{pts}</h1>
                <p style="margin:0; font-size:0.8rem;">استمر في التفوق!</p>
            </div>
        """, unsafe_allow_html=True)

        # الميداليات
        st.markdown(f"""
            <div class="medal-flex">
                <div class="m-card {'m-active' if pts>=100 else ''}" style="color: #d97706;">🥇<br><b>ذهبي</b></div>
                <div class="m-card {'m-active' if pts>=50 else ''}" style="color: #64748b;">🥈<br><b>فضي</b></div>
                <div class="m-card m-active" style="color: #b45309;">🥉<br><b>برونزي</b></div>
            </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["📢", "📝", "📊", "🏆", "⚙️"])

        with tabs[0]: # تنبيهات
            st.caption("التعاميم والتنبيهات")
            if not df_ann.empty:
                anns = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_cls])]
                # تم عكس الترتيب للأحدث
                for _, r in anns.iloc[::-1].iterrows():
                    st.markdown(f"""
                    <div class='mobile-list-item'>
                        <div style="width:100%">
                            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                                <b>📢 {r.get('العنوان')}</b>
                                <small style="background:#f1f5f9; padding:2px 6px; border-radius:4px;">{r.get('التاريخ')}</small>
                            </div>
                            <span style="color:#475569; font-size:0.9rem;">{r.get('الرابط')}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else: st.info("لا يوجد تنبيهات حالياً")

        with tabs[1]: # ملاحظات
            st.caption("سجل السلوك والملاحظات")
            if not df_beh.empty:
                df_beh['clean_id'] = df_beh.iloc[:,0].astype(str).str.split('.').str[0]
                nts = df_beh[df_beh['clean_id']==sid]
                if not nts.empty:
                    # تم عكس الترتيب (الأحدث أولاً)
                    for _, n in nts.iloc[::-1].iterrows():
                        color = "#ef4444" if "سلبي" in str(n.get('type')) else "#1e3a8a"
                        st.markdown(f"""
                        <div class='mobile-list-item' style='border-right: 4px solid {color};'>
                            <div>
                                <b style="color:{color}">{n.get('type')}</b>
                                <p style="margin:0; font-size:0.9rem; color:#334155;">{n.get('note')}</p>
                                <small style="color:#94a3b8;">{n.get('date')}</small>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else: st.success("🌟 سجلك نظيف تماماً!")

        with tabs[2]: # درجات
            st.caption("درجاتي")
            if not df_gr.empty:
                df_gr['clean_id'] = df_gr.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                grs = df_gr[df_gr['clean_id']==sid]
                if not grs.empty:
                    g = grs.iloc[0]
                    st.markdown(f"""
                    <div class='mobile-list-item'><span>📝 المشاركة والواجبات</span><b>{g.get('p1')}</b></div>
                    <div class='mobile-list-item'><span>✍️ الاختبارات القصيرة</span><b>{g.get('p2')}</b></div>
                    <div class='mobile-list-item' style='background:#f0fdf4; border-color:#bbf7d0;'>
                        <span style="color:#166534; font-weight:bold;">🏆 المجموع النهائي</span>
                        <b style="color:#166534; font-size:1.2rem;">{g.get('perf')}</b>
                    </div>
                    """, unsafe_allow_html=True)
                else: st.info("لم يتم رصد درجات بعد")

        with tabs[3]: # المتصدرين
            st.caption("لوحة الشرف (أفضل 10 طلاب)")
            df_st['p_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            for i, (_, r) in enumerate(df_st.sort_values('p_num', ascending=False).head(10).iterrows(), 1):
                ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
                is_me = str(r['clean_id']) == sid
                sty = "border:2px solid #3b82f6; background:#eff6ff;" if is_me else ""
                st.markdown(f"""
                    <div class='mobile-list-item' style='{sty}'>
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-weight:900; font-size:1.2rem; width:30px;">{ic}</span>
                            <span>{r['name']}</span>
                        </div>
                        <span style='color:#f59e0b; font-weight:900;'>{int(r['p_num'])}</span>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[4]: # إعدادات
            st.caption("إدارة الملف الشخصي")
            with st.form("my_profile"):
                nm = st.text_input("📧 البريد الإلكتروني", s_dat.get('الإيميل',''))
                np = st.text_input("📱 رقم الجوال", s_dat.get('الجوال',''))
                if st.form_submit_button("💾 تحديث بياناتي", type="primary", use_container_width=True):
                    try:
                        fp = clean_phone_number(np) if np else ""
                        ws = sh.worksheet("students"); c = ws.find(sid)
                        if c:
                            h = ws.row_values(1)
                            if 'الإيميل' in h and 'الجوال' in h:
                                ws.update_cell(c.row, h.index('الإيميل')+1, nm)
                                ws.update_cell(c.row, h.index('الجوال')+1, fp)
                                st.success("✅ تم التحديث")
                            else: st.error("خطأ هيكلي")
                    except Exception as e: st.error(f"خطأ: {e}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 تسجيل الخروج", type="secondary", use_container_width=True):
                st.session_state.role = None; st.rerun()

    else: st.error("عذراً، لم يتم العثور على بياناتك"); st.button("العودة للقائمة الرئيسية", on_click=st.rerun)
    
    show_footer()
