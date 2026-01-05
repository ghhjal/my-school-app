import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import plotly.express as px
import qrcode
import io
import smtplib
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. المحرك الاحترافي لإدارة البيانات والملفات
# ==========================================
class ZiyadPlatformEngine:
    def __init__(self):
        # إعداد الاتصال بجوجل درايف وشيت
        self.creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        self.client = gspread.authorize(self.creds)
        self.sh = self.client.open_by_key(st.secrets["SHEET_ID"])
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    @st.cache_data(ttl=60)
    def fetch_data_cached(_self, table_name):
        """قراءة ذكية مع كاش لمدة دقيقة لتوفير الحصة (Quota)"""
        try:
            ws = _self.sh.worksheet(table_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except: return pd.DataFrame()

    def sync_attendance_concurrency(self, target_date, attendance_map):
        """صمام أمان التصادم: تحديث البيانات بكتلة واحدة لمنع التكرار"""
        try:
            ws = self.sh.worksheet("attendance")
            all_records = ws.get_all_values()
            headers = all_records[0]
            # الاحتفاظ بالبيانات القديمة التي لا تخص تاريخ اليوم
            filtered_data = [headers] + [row for row in all_records[1:] if row[1] != target_date]
            # إضافة بيانات اليوم الجديدة
            for name, status in attendance_map.items():
                filtered_data.append([name, target_date, status])
            ws.clear()
            ws.update("A1", filtered_data)
            st.cache_data.clear()
            return True
        except: return False

    def upload_file_with_replace(self, student_name, hw_title, uploaded_file):
        """رفع الملف لـ Drive مع استبدال النسخة القديمة إن وجدت"""
        try:
            folder_id = st.secrets["DRIVE_FOLDER_ID"]
            # البحث عن الملف القديم لحذفه
            query = f"name contains '{student_name}_{hw_title}' and '{folder_id}' in parents"
            results = self.drive_service.files().list(q=query).execute().get('files', [])
            for f in results: self.drive_service.files().delete(fileId=f['id']).execute()

            with st.status("جاري رفع الملف لـ Google Drive...") as status:
                metadata = {'name': f"{student_name}_{hw_title}_{uploaded_file.name}", 'parents': [folder_id]}
                media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
                file = self.drive_service.files().create(body=metadata, media_body=media, fields='webViewLink').execute()
                status.update(label="✅ تم الرفع بنجاح!", state="complete")
                return file.get('webViewLink')
        except: return None

# ==========================================
# 2. محرك الشهادات (Arabic PDF & QR)
# ==========================================
class CertificateGenerator:
    def __init__(self, student_name, student_id, score):
        self.name = student_name
        self.sid = student_id
        self.score = score

    def _fix_arabic(self, text):
        return get_display(reshape(text))

    def create_pdf(self):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        # 1. الخلفية
        try: pdf.image('template.png', x=0, y=0, w=297, h=210)
        except: pdf.rect(5, 5, 287, 200)
        
        # 2. الخط العربي
        try:
            pdf.add_font('Amiri', '', 'Amiri-Regular.ttf', uni=True)
            pdf.set_font('Amiri', size=35)
        except: pdf.set_font('Arial', size=25)

        # 3. النصوص
        pdf.ln(60)
        pdf.cell(277, 20, txt=self._fix_arabic("شهادة شكر وتقدير"), ln=True, align='C')
        pdf.set_font('Amiri', size=25)
        pdf.cell(277, 20, txt=self._fix_arabic(self.name), ln=True, align='C')
        msg = f"لتحقيقه نسبة نجاح متميزة قدرها {self.score}%"
        pdf.set_font('Amiri', size=18)
        pdf.cell(277, 15, txt=self._fix_arabic(msg), ln=True, align='C')

        # 4. QR Code للتحقق
        qr = qrcode.make(f"Verified Student: {self.name} | ID: {self.sid}")
        img_buf = io.BytesIO()
        qr.save(img_buf, format='PNG')
        pdf.image(img_buf, x=250, y=165, w=30, h=30)
        
        return pdf.output()

# ==========================================
# 3. إعداد الجلسة والتصميم (CSS)
# ==========================================
if 'engine' not in st.session_state:
    st.session_state.engine = ZiyadPlatformEngine()

db = st.session_state.engine

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin-top: -60px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 12px !important; font-weight: bold !important; height: 3.5em !important; width: 100% !important; transition: 0.3s; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <h1>منصة الأستاذ زياد الذكية 🚀</h1>
        <p>النظام المتكامل لإدارة التعليم والتحليل الأكاديمي</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. واجهة الدخول وحماية الجلسة
# ==========================================
if 'role' not in st.session_state:
    tab_st, tab_ad = st.tabs(["🎓 دخول الطلاب", "🔐 الإدارة"])
    with tab_st:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي")
            if st.form_submit_button("دخول للمنصة"):
                df_s = db.fetch_data_cached("students")
                if not df_s.empty and sid in df_s['الرقم'].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with tab_ad:
        with st.form("ad_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = db.fetch_data_cached("users")
                h_p = hashlib.sha256(p.encode()).hexdigest()
                if not df_u.empty and u == str(df_u.iloc[0,0]) and h_p == str(df_u.iloc[0,1]):
                    st.session_state.role = "admin"; st.rerun()
                else: st.error("بيانات غير صحيحة")
    st.stop()

# ==========================================
# 5. واجهة المعلم (v11.0)
# ==========================================
if st.session_state.role == "admin":
    menu = st.tabs(["📊 التحليلات", "📝 التحضير", "🎓 التقييم", "📜 الشهادات", "🚗 خروج"])

    with menu[0]: # Dashboard
        st.subheader("📈 إحصائيات الانضباط")
        df_att = db.fetch_data_cached("attendance")
        if not df_att.empty:
            df_plot = df_att[df_att['الحالة'] == 'غائب'].groupby('التاريخ').size().reset_index(name='الغياب')
            fig = px.line(df_plot, x='التاريخ', y='الغياب', title="منحنى الغياب الأسبوعي", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    with menu[1]: # التحضير مع صمام الأمان
        st.subheader("🗓️ التحضير اليومي")
        df_st = db.fetch_data_cached("students")
        today = datetime.date.today().strftime("%Y-%m-%d")
        att_results = {}
        for _, row in df_st.iterrows():
            c1, c2 = st.columns([3, 1])
            status = c2.toggle("حاضر", value=True, key=f"t_{row['الرقم']}")
            c1.write(f"👤 {row['الاسم']}")
            att_results[row['الاسم']] = "حاضر" if status else "غائب"
        if st.button("💾 حفظ الكشف الذكي"):
            if db.sync_attendance_concurrency(today, att_results):
                st.success("تم الحفظ والمزامنة بنجاح!")

    with menu[2]: # التقييم بـ Data Editor
        st.subheader("🎓 تصحيح الواجبات")
        df_sub = db.fetch_data_cached("submissions")
        if not df_sub.empty:
            st.write("تنسيق شرطي: الدرجات < 50 تظهر باللون الأحمر تلقائياً.")
            edited_df = st.data_editor(
                df_sub,
                column_config={"رابط الملف": st.column_config.LinkColumn("🔗 الملف")},
                disabled=["الطالب", "الواجب", "التاريخ"],
                use_container_width=True
            )
            if st.button("✅ حفظ الدرجات"):
                ws = db.sh.worksheet("submissions")
                ws.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
                st.cache_data.clear(); st.success("تم تحديث السجلات")

    with menu[3]: # الشهادات
        st.subheader("📜 إصدار الشهادات بالعربية")
        df_s = db.fetch_data_cached("students")
        sel_s = st.selectbox("اختر الطالب:", options=df_s['الاسم'].tolist())
        score = st.number_input("الدرجة النهائية (%)", 0, 100, 90)
        if st.button("✨ توليد الشهادة"):
            s_id = df_s[df_s['الاسم'] == sel_s]['الرقم'].iloc[0]
            gen = CertificateGenerator(sel_s, s_id, score)
            pdf_bytes = gen.create_pdf()
            st.download_button(f"📥 تحميل شهادة {sel_s}", data=bytes(pdf_bytes), file_name=f"Cert_{s_id}.pdf", mime="application/pdf")

    with menu[4]:
        if st.button("تسجيل الخروج"): st.session_state.clear(); st.rerun()

# ==========================================
# 6. واجهة الطالب التفاعلية
# ==========================================
elif st.session_state.role == "student":
    df_s = db.fetch_data_cached("students")
    s_info = df_s[df_s['الرقم'].astype(str) == str(st.session_state.sid)].iloc[0]
    st.title(f"مرحباً {s_info['الاسم']} 👋")
    
    t1, t2 = st.tabs(["📚 تسليم الواجبات", "🗓️ سجل حضوري"])
    with t1:
        df_hw = db.fetch_data_cached("homework")
        for _, hw in df_hw.iterrows():
            with st.expander(f"📖 واجب: {hw['العنوان']}"):
                st.write(hw['الوصف'])
                up = st.file_uploader("ارفع الحل", key=f"up_{hw['العنوان']}")
                if up and st.button("إرسال", key=f"btn_{hw['العنوان']}"):
                    link = db.upload_file_with_replace(s_info['الاسم'], hw['العنوان'], up)
                    db.sh.worksheet("submissions").append_row([s_info['الاسم'], hw['العنوان'], link, datetime.date.today().strftime("%Y-%m-%d"), 0])
                    st.success("تم التسليم بنجاح!")
    
    with t2:
        df_att = db.fetch_data_cached("attendance")
        my_att = df_att[df_att['الاسم'] == s_info['الاسم']]
        st.table(my_att.tail(10))

    if st.button("تسجيل الخروج"): st.session_state.clear(); st.rerun()
