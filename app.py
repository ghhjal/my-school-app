# -*- coding: utf-8 -*-
import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# =========================================================
# ✅ منصة الأستاذ زياد التعليمية (نسخة احترافية + إصلاحات)
# - تنظيم كامل للكود + واجهات RTL احترافية
# - إصلاح تبويبات المعلم (التنبيهات كانت خارج كتلة المعلم)
# - إصلاح حذف التنبيهات (delete_rows كان يحذف صف خاطئ)
# - تحسين التحديث بالـ ID قدر الإمكان
# - كاش للقراءة (cache_data) + تنظيف الأعمدة المكررة/الفارغة
# =========================================================

# ---------------------------
# 1) إعدادات الصفحة والتصميم
# ---------------------------
st.set_page_config(page_title="منصة الأستاذ زياد التعليمية", layout="wide")

BASE_CSS = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    font-family: 'Cairo', sans-serif !important;
    direction: RTL;
    text-align: right;
}
a { text-decoration: none; }

.header-hero {
    background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
    padding: 34px 26px;
    border-radius: 0 0 32px 32px;
    color: white;
    text-align: center;
    margin: -70px -20px 22px -20px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.12);
    border-bottom: 5px solid #f59e0b;
}
.logo-box {
    background: rgba(255,255,255,0.18);
    width: 68px; height: 68px;
    border-radius: 18px;
    margin: 0 auto 10px auto;
    display: flex; justify-content: center; align-items: center;
    border: 1px solid rgba(255,255,255,0.25);
}
.logo-box i { font-size: 34px; color: #fff; }

.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 6px 18px rgba(2,6,23,0.05);
}
.badge-chip {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.85rem;
    border: 1px solid rgba(2,6,23,0.08);
    background: rgba(255,255,255,0.7);
}

.stButton>button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    height: 3.1em;
}
div[data-testid="stForm"] {
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 14px;
    background: #ffffff;
}

@media (max-width: 768px) {
    .header-hero { padding: 28px 16px; }
    .header-hero h1 { font-size: 1.3rem !important; }
}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="header-hero">
        <div class="logo-box"><i class="bi bi-mortarboard-fill"></i></div>
        <h1 style="margin:0; font-size: 26px;">منصة الأستاذ زياد</h1>
        <p style="opacity:0.85; margin: 6px 0 0 0; font-size: 14px;">
            نظام الإدارة المدرسية المتكامل
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# 2) أدوات عامة
# ---------------------------
def _safe_str(x) -> str:
    return "" if x is None else str(x).strip()

def _normalize_phone(x) -> str:
    s = _safe_str(x)
    if "." in s:
        s = s.split(".")[0]
    return "".join(ch for ch in s if ch.isdigit() or ch == "+")

def _hash_password(p: str) -> str:
    return hashlib.sha256(str.encode(p)).hexdigest()

def _dupe_columns_fix(cols):
    seen = {}
    fixed = []
    for c in cols:
        c = _safe_str(c)
        if c == "":
            c = "col"
        if c not in seen:
            seen[c] = 0
            fixed.append(c)
        else:
            seen[c] += 1
            fixed.append(f"{c}_{seen[c]}")
    return fixed

# ---------------------------
# 3) الاتصال بجوجل شيت
# ---------------------------
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ],
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("تعذر الاتصال بـ Google Sheets. تأكد من إعدادات Secrets.")
        st.exception(e)
        return None

sh = get_client()

@st.cache_data(ttl=30)
def fetch_safe(worksheet_name: str) -> pd.DataFrame:
    try:
        if sh is None:
            return pd.DataFrame()
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()

        header = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=header)

        df = df.loc[:, df.columns != ""]
        df.columns = _dupe_columns_fix(df.columns.tolist())
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات من ({worksheet_name}).")
        st.exception(e)
        return pd.DataFrame()

def ws(worksheet_name: str):
    return sh.worksheet(worksheet_name)

def clear_cache_and_rerun(delay: float = 0.6):
    st.cache_data.clear()
    time.sleep(delay)
    st.rerun()

# ---------------------------
# 4) الجلسات (Auth)
# ---------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "sid" not in st.session_state:
    st.session_state.sid = None

# ===========================
# شاشة الدخول
# ===========================
if st.session_state.role is None:
    t1, t2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])

    with t1:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية/الرقم الأكاديمي", key="login_sid")
        if st.button("دخول الطالب 🚀", use_container_width=True):
            df_st = fetch_safe("students")
            if df_st.empty:
                st.error("لا توجد بيانات طلاب أو تعذر قراءة الشيت.")
            else:
                df_st.iloc[:, 0] = df_st.iloc[:, 0].astype(str).str.strip()
                match = df_st[df_st.iloc[:, 0] == _safe_str(sid_input)]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.sid = _safe_str(sid_input)
                    st.success("تم تسجيل الدخول ✅")
                    clear_cache_and_rerun(0.2)
                else:
                    st.error("❌ عذراً، الرقم غير مسجل")

    with t2:
        st.subheader("👨‍🏫 دخول المعلم")
        u_name = st.text_input("اسم المستخدم", key="login_user")
        u_pass = st.text_input("كلمة المرور", type="password", key="login_pass")
        if st.button("دخول المعلم 🔐", use_container_width=True):
            df_u = fetch_safe("users")
            if df_u.empty:
                st.error("تعذر قراءة شيت المستخدمين (users).")
            else:
                if "username" in df_u.columns and "password_hash" in df_u.columns:
                    row = df_u[df_u["username"].astype(str).str.strip() == _safe_str(u_name)]
                    if row.empty:
                        st.error("❌ المستخدم غير موجود")
                    else:
                        hashed = _hash_password(_safe_str(u_pass))
                        if hashed == _safe_str(row.iloc[0]["password_hash"]):
                            st.session_state.role = "teacher"
                            st.success("تم تسجيل الدخول ✅")
                            clear_cache_and_rerun(0.2)
                        else:
                            st.error("❌ كلمة المرور غير صحيحة")
                else:
                    row = df_u[df_u.iloc[:, 0].astype(str).str.strip() == _safe_str(u_name)]
                    if row.empty:
                        st.error("❌ المستخدم غير موجود")
                    else:
                        hashed = _hash_password(_safe_str(u_pass))
                        if hashed == _safe_str(row.iloc[0, 1]):
                            st.session_state.role = "teacher"
                            st.success("تم تسجيل الدخول ✅")
                            clear_cache_and_rerun(0.2)
                        else:
                            st.error("❌ كلمة المرور غير صحيحة")

    st.stop()

# =========================================================
# 👨‍🏫 واجهة المعلم
# =========================================================
if st.session_state.role == "teacher":
    st.markdown(
        """
        <div style="background: linear-gradient(135deg,#1e3a8a,#3b82f6); padding: 18px; border-radius: 16px; color:#fff; text-align:center; margin: 8px 0 18px 0; box-shadow: 0 8px 18px rgba(2,6,23,0.12);">
            <h2 style="margin:0; font-size: 1.4rem;">👨‍🏫 لوحة تحكم المعلم</h2>
            <p style="margin:6px 0 0 0; opacity:0.9; font-size:0.9rem;">إدارة الطلاب • الدرجات • السلوك • التنبيهات</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    t_manage, t_grades, t_behavior, t_exams, t_logout = st.tabs(
        ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 التنبيهات", "🚪 خروج"]
    )

    # ---------------------------
    # تبويب: إدارة الطلاب
    # ---------------------------
    with t_manage:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#0f172a,#1d4ed8); padding:18px; border-radius:16px; color:white; text-align:center;">'
            '<h3 style="margin:0;">👥 إدارة الطلاب</h3></div>',
            unsafe_allow_html=True
        )

        df_st = fetch_safe("students")

        colA, colB, colC = st.columns([1.2, 1.2, 1.6])
        with colA:
            st.markdown('<div class="kpi-card"><b>عدد الطلاب</b><div style="font-size:1.8rem; font-weight:800;">{}</div></div>'.format(
                0 if df_st.empty else len(df_st)
            ), unsafe_allow_html=True)
        with colB:
            st.markdown('<div class="kpi-card"><b>آخر تحديث</b><div style="font-size:1.0rem; font-weight:800;">⏱️ تلقائي</div><div style="opacity:0.7; font-size:0.85rem;">كاش 30 ثانية</div></div>',
                        unsafe_allow_html=True)
        with colC:
            st.info("نصيحة: اعتمد دائمًا على **الرقم الأكاديمي** في الحذف والتحديث لتجنب تشابه الأسماء.")

        st.write("")
        with st.container(border=True):
            st.subheader("📋 السجل الحالي للطلاب")
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.write("")
        st.markdown("### ➕ إضافة طالب جديد")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي (ID)")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])

            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nsub = c5.text_input("📚 المادة", value="لغة إنجليزية")
            nyear = c6.text_input("🗓️ العام", value="1447هـ")

            c7, c8 = st.columns(2)
            nmail = c7.text_input("📧 البريد الإلكتروني")
            nphone = c8.text_input("📱 جوال ولي الأمر")

            submit = st.form_submit_button("✅ اعتماد التأسيس", use_container_width=True)
            if submit:
                if not nid or not nname:
                    st.error("⚠️ الرجاء إدخال الرقم الأكاديمي والاسم.")
                else:
                    row_to_add = [
                        _safe_str(nid), _safe_str(nname), _safe_str(nclass),
                        _safe_str(nyear), _safe_str(nstage), _safe_str(nsub),
                        _safe_str(nmail), _safe_str(nphone), "0"
                    ]
                    try:
                        ws("students").append_row(row_to_add)
                        st.success(f"✅ تم إضافة الطالب: {_safe_str(nname)}")
                        clear_cache_and_rerun()
                    except Exception as e:
                        st.error("حدث خطأ أثناء الإضافة.")
                        st.exception(e)

        st.divider()
        st.markdown("### 🗑️ حذف نهائي (من جميع السجلات)")
        st.warning("⚠️ الحذف النهائي سيزيل الطالب من (students) و (grades) و (behavior).")

        if not df_st.empty:
            df_st_ids = df_st.copy()
            df_st_ids.iloc[:, 0] = df_st_ids.iloc[:, 0].astype(str).str.strip()
            df_st_ids.iloc[:, 1] = df_st_ids.iloc[:, 1].astype(str).str.strip()

            options = [""] + [
                f"{df_st_ids.iloc[i,1]} — ID:{df_st_ids.iloc[i,0]}"
                for i in range(len(df_st_ids))
            ]
        else:
            options = [""]

        del_pick = st.selectbox("🎯 اختر الطالب للحذف النهائي", options, key="del_pick")
        if st.button("🚨 تنفيذ الحذف النهائي الآن", use_container_width=True):
            if not del_pick:
                st.error("اختر طالبًا أولاً.")
            else:
                try:
                    del_id = del_pick.split("ID:")[-1].strip()
                    ws_st = ws("students")
                    ws_gr = ws("grades")
                    ws_bh = ws("behavior")

                    with st.spinner("جاري الحذف من جميع السجلات..."):
                        try:
                            cell = ws_st.find(del_id, in_column=1)
                            st_name = _safe_str(ws_st.cell(cell.row, 2).value)
                            ws_st.delete_rows(cell.row)
                        except:
                            st_name = "الطالب"

                        try:
                            if st_name:
                                matches = ws_gr.findall(st_name)
                                for m in reversed(matches):
                                    if m.col == 1:
                                        ws_gr.delete_rows(m.row)
                        except:
                            pass

                        try:
                            if st_name:
                                matches = ws_bh.findall(st_name)
                                for m in reversed(matches):
                                    if m.col == 1:
                                        ws_bh.delete_rows(m.row)
                        except:
                            pass

                    st.success(f"💥 تم الحذف النهائي بنجاح (ID: {del_id})")
                    clear_cache_and_rerun()
                except Exception as e:
                    st.error("حدث خطأ أثناء الحذف.")
                    st.exception(e)

    # ---------------------------
    # تبويب: الدرجات
    # ---------------------------
    with t_grades:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#6366f1,#4338ca); padding:18px; border-radius:16px; color:white; text-align:center;">'
            '<h3 style="margin:0;">📝 رصد الدرجات</h3></div>',
            unsafe_allow_html=True
        )

        df_st = fetch_safe("students")
        df_g = fetch_safe("grades")

        if df_st.empty:
            st.info("لا توجد بيانات طلاب.")
        else:
            names = [""] + df_st.iloc[:, 1].astype(str).tolist()
            target = st.selectbox("🎯 اختر الطالب", names, key="grade_target")

            if target:
                curr = df_g[df_g.iloc[:, 0].astype(str) == str(target)] if not df_g.empty else pd.DataFrame()

                def _to_int(x):
                    try:
                        return int(float(str(x)))
                    except:
                        return 0

                v1 = _to_int(curr.iloc[0, 1]) if not curr.empty and curr.shape[1] > 1 else 0
                v2 = _to_int(curr.iloc[0, 2]) if not curr.empty and curr.shape[1] > 2 else 0
                v3 = _to_int(curr.iloc[0, 3]) if not curr.empty and curr.shape[1] > 3 else 0

                with st.form("grade_form"):
                    st.markdown(f"**تحديث درجات الطالب:** <span class='badge-chip'>{target}</span>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("📌 الفترة الأولى", 0, 100, value=v1)
                    p2 = c2.number_input("📌 الفترة الثانية", 0, 100, value=v2)
                    part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)

                    save = st.form_submit_button("💾 حفظ الدرجات", use_container_width=True)
                    if save:
                        try:
                            w = ws("grades")
                            try:
                                cell = w.find(target, in_column=1)
                                w.update(f"B{cell.row}:D{cell.row}", [[p1, p2, part]])
                            except:
                                w.append_row([target, p1, p2, part])
                            st.success(f"✅ تم حفظ درجات {target}")
                            clear_cache_and_rerun()
                        except Exception as e:
                            st.error("حدث خطأ أثناء حفظ الدرجات.")
                            st.exception(e)

        st.divider()
        st.subheader("📊 جدول الدرجات العام")
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    # ---------------------------
    # تبويب: السلوك
    # ---------------------------
    with t_behavior:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        st.markdown(
            '<div style="background:linear-gradient(90deg,#10b981,#059669); padding:18px; border-radius:16px; color:white; text-align:center;">'
            '<h3 style="margin:0;">🎭 رصد السلوك والتواصل</h3></div>',
            unsafe_allow_html=True
        )

        st.caption("ملاحظة: إرسال Gmail عبر SMTP يحتاج عادةً **App Password** في الإعدادات (email_settings).")

        def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date) -> bool:
            try:
                email_set = st.secrets["email_settings"]
                msg = MIMEMultipart()
                msg["From"] = email_set["sender_email"]
                msg["To"] = to_email
                msg["Subject"] = f"🔔 إشعار سلوكي فوري: {student_name}"

                body = (
                    f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {student_name}\n"
                    f"----------------------------------------\n"
                    f"🏷️ نوع السلوك: {b_type}\n"
                    f"📝 الملاحظة: {b_note}\n"
                    f"📅 التاريخ: {b_date}\n"
                    f"----------------------------------------\n"
                    f"🏛️ منصة الأستاذ زياد الذكية"
                )
                msg.attach(MIMEText(body, "plain", "utf-8"))

                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(email_set["sender_email"], email_set["sender_password"])
                server.send_message(msg)
                server.quit()
                return True
            except:
                return False

        df_st = fetch_safe("students")
        if df_st.empty:
            st.info("لا توجد بيانات طلاب.")
        else:
            all_names = df_st.iloc[:, 1].astype(str).tolist()

            search_term = st.text_input("🔍 ابحث عن الطالب", placeholder="اكتب جزء من الاسم...", key="beh_search")
            filtered = [n for n in all_names if _safe_str(search_term) in _safe_str(n)] if search_term else all_names
            b_name = st.selectbox("🎯 اختر الطالب", [""] + filtered, key="beh_pick")

            if b_name:
                row = df_st[df_st.iloc[:, 1].astype(str) == str(b_name)]
                if row.empty:
                    st.error("تعذر جلب بيانات الطالب.")
                else:
                    s_row = row.iloc[0]
                    s_email = _safe_str(s_row[6]) if len(s_row) > 6 else ""
                    s_phone = _normalize_phone(s_row[7]) if len(s_row) > 7 else ""

                    with st.container(border=True):
                        c1, c2 = st.columns(2)
                        b_type = c1.selectbox(
                            "🏷️ نوع السلوك",
                            ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"],
                            key="beh_type"
                        )
                        b_date = c2.date_input("📅 التاريخ", key="beh_date")
                        b_note = st.text_area("📝 نص الملاحظة", key="beh_note", placeholder="اكتب ملاحظة واضحة...")

                        st.markdown("---")
                        st.write("✨ **خيارات الحفظ والتواصل:**")

                        col1, col2 = st.columns(2)
                        btn_save = col1.button("💾 حفظ فقط", use_container_width=True, key="beh_save")
                        btn_auto = col2.button("⚡ إشعار تلقائي (إيميل)", use_container_width=True, key="beh_auto")
                        btn_wa = col2.button("💬 حفظ + واتساب", use_container_width=True, key="beh_wa")

                        full_msg = (
                            f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\n"
                            f"----------------------------------------\n"
                            f"🏷️ نوع السلوك: {b_type}\n"
                            f"📝 الملاحظة: {b_note}\n"
                            f"📅 التاريخ: {b_date}\n"
                            f"----------------------------------------\n"
                            f"🏛️ منصة الأستاذ زياد الذكية"
                        )

                        p_map = {
                            "🌟 متميز (+10)": 10,
                            "✅ إيجابي (+5)": 5,
                            "⚠️ تنبيه (0)": 0,
                            "❌ سلبي (-5)": -5,
                            "🚫 مخالفة (-10)": -10,
                        }

                        def save_behavior_and_points():
                            if not _safe_str(b_note):
                                st.error("⚠️ اكتب نص الملاحظة أولاً.")
                                return False
                            try:
                                ws("behavior").append_row([b_name, str(b_date), b_type, b_note])

                                try:
                                    wst = ws("students")
                                    cell = wst.find(b_name, in_column=2)
                                    current = _safe_str(wst.cell(cell.row, 9).value)
                                    try:
                                        current_p = int(float(current)) if current else 0
                                    except:
                                        current_p = 0
                                    new_p = current_p + p_map.get(b_type, 0)
                                    wst.update_cell(cell.row, 9, str(new_p))
                                except:
                                    pass

                                return True
                            except Exception as e:
                                st.error("حدث خطأ أثناء الحفظ.")
                                st.exception(e)
                                return False

                        if btn_save:
                            if save_behavior_and_points():
                                st.success("✅ تم الحفظ وتحديث النقاط")
                                clear_cache_and_rerun()

                        if btn_auto:
                            if not s_email:
                                st.warning("⚠️ لا يوجد بريد لهذا الطالب.")
                            else:
                                if not _safe_str(b_note):
                                    st.error("⚠️ اكتب نص الملاحظة أولاً.")
                                else:
                                    with st.spinner("جاري الإرسال..."):
                                        ok = send_auto_email_silent(s_email, b_name, b_type, b_note, b_date)
                                        st.success(f"✅ تم الإرسال إلى {s_email}") if ok else st.error("❌ فشل الإرسال (تحقق من Secrets)")

                        if btn_wa:
                            if save_behavior_and_points():
                                if s_phone:
                                    wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(full_msg)}"
                                else:
                                    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(full_msg)}"
                                st.markdown(
                                    f"""
                                    <div style="background:#f0fff4; border: 1px solid #25D366; padding: 12px; border-radius: 12px; text-align:center; margin-top: 10px;">
                                        <a href="{wa_url}" target="_blank" style="color:white; background:#25D366; padding: 10px 18px; border-radius: 12px; font-weight: 800; display:inline-block;">
                                            💬 فتح واتساب وإرسال التقرير
                                        </a>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.success("✅ تم الحفظ (افتح واتساب للإرسال)")
                                st.cache_data.clear()

                    df_b = fetch_safe("behavior")
                    if not df_b.empty:
                        st.divider()
                        st.subheader(f"📜 السجل السلوكي للطالب: {b_name}")
                        show = df_b[df_b.iloc[:, 0].astype(str) == str(b_name)]
                        if show.empty:
                            st.info("لا توجد ملاحظات مسجلة لهذا الطالب.")
                        else:
                            st.dataframe(show.iloc[::-1, :4], use_container_width=True, hide_index=True)

    # ---------------------------
    # تبويب: التنبيهات (exams)
    # ---------------------------
    with t_exams:
        st.markdown(
            """
            <div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 18px; border-radius: 16px; color: white; text-align: center;">
                <h3 style="margin:0;">📢 مركز التنبيهات والإعلانات</h3>
                <p style="margin:6px 0 0 0; opacity: 0.85;">نشر مواعيد • مشاركة واتساب • حذف صحيح</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("➕ إضافة تنبيه/موعد جديد", expanded=True):
            with st.form("announcement_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                a_title = c2.text_input("📝 عنوان التنبيه", placeholder="مثال: اختبار شفهي الأسبوع القادم")
                a_date = c3.date_input("📅 الموعد")

                post = st.form_submit_button("🚀 نشر التنبيه الآن", use_container_width=True)
                if post:
                    if not _safe_str(a_title):
                        st.error("اكتب عنوان التنبيه.")
                    else:
                        try:
                            ws("exams").append_row([a_class, a_title, str(a_date)])
                            st.success("✅ تم نشر التنبيه")
                            clear_cache_and_rerun(0.4)
                        except Exception as e:
                            st.error("حدث خطأ أثناء النشر.")
                            st.exception(e)

        st.write("")
        st.markdown("### 📋 التنبيهات المنشورة (الأحدث أولاً)")
        df_ann = fetch_safe("exams")

        if df_ann.empty:
            st.info("📭 لا توجد تنبيهات منشورة حالياً.")
        else:
            df_ann = df_ann.reset_index(drop=True)
            df_ann["sheet_row"] = df_ann.index + 2  # +2 بسبب صف العناوين

            color_map = {
                "الكل": "#E0F2FE",
                "الأول": "#F0FDF4",
                "الثاني": "#FFF7ED",
                "الثالث": "#FAF5FF",
                "الرابع": "#FEF2F2",
                "الخامس": "#F5F3FF",
                "السادس": "#ECFEFF",
            }

            for _, row in df_ann.iloc[::-1].iterrows():
                cls = _safe_str(row.iloc[0])
                title = _safe_str(row.iloc[1])
                dt = _safe_str(row.iloc[2])
                sheet_row = int(row["sheet_row"])
                bg = color_map.get(cls, "#ffffff")

                wa_msg = (
                    f"📢 *تنبيه من منصة الأستاذ زياد الذكية*\n"
                    f"----------------------------------\n"
                    f"🏫 *الصف:* {cls}\n"
                    f"📝 *الموضوع:* {title}\n"
                    f"📅 *الموعد:* {dt}\n"
                    f"----------------------------------\n"
                    f"يرجى العلم والاستعداد 🌟"
                )
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"

                st.markdown(
                    f"""
                    <div style="background:{bg}; padding:14px; border-radius:14px; border-right:6px solid #4F46E5; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
                            <div>
                                <b style="font-size:1.0rem;">[{cls}]</b> <span style="font-weight:700;">{title}</span><br>
                                <span style="opacity:0.8;">📅 {dt}</span>
                            </div>
                            <span class="badge-chip">#Row {sheet_row}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2, c3 = st.columns([1.3, 1.0, 2.7])
                with c1:
                    st.markdown(
                        f'<a href="{wa_url}" target="_blank" style="display:inline-block; padding:10px 14px; background:#25D366; color:white; border-radius:12px; font-weight:800;">💬 مشاركة واتساب</a>',
                        unsafe_allow_html=True
                    )
                with c2:
                    if st.button("🗑️ حذف", key=f"del_exam_{sheet_row}", use_container_width=True):
                        try:
                            ws("exams").delete_rows(sheet_row)
                            st.success("✅ تم الحذف")
                            clear_cache_and_rerun(0.2)
                        except Exception as e:
                            st.error("تعذر الحذف.")
                            st.exception(e)
                with c3:
                    st.write("")

    # ---------------------------
    # تبويب: الخروج
    # ---------------------------
    with t_logout:
        st.markdown(
            '<div style="background:#fff; border:1px solid #e2e8f0; padding:16px; border-radius:16px;">'
            '<h4 style="margin:0;">🚪 تسجيل الخروج</h4>'
            '<p style="margin:8px 0 0 0; opacity:0.8;">سيتم إنهاء الجلسة والعودة لشاشة الدخول.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("🚨 تسجيل الخروج النهائي", use_container_width=True):
            st.session_state.role = None
            st.session_state.sid = None
            clear_cache_and_rerun(0.1)

# =========================================================
# 👨‍🎓 واجهة الطالب
# =========================================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades")
    df_beh = fetch_safe("behavior")
    df_ex = fetch_safe("exams")

    try:
        if df_st.empty:
            st.error("⚠️ لا توجد بيانات طلاب.")
            st.stop()

        df_st.iloc[:, 0] = df_st.iloc[:, 0].astype(str).str.strip()
        student_data = df_st[df_st.iloc[:, 0] == _safe_str(st.session_state.sid)]

        if student_data.empty:
            st.error("⚠️ لم يتم العثور على بيانات الطالب.")
            st.stop()

        s_row = student_data.iloc[0]
        s_name = _safe_str(s_row[1])
        s_class = _safe_str(s_row[2])

        val = _safe_str(s_row[8]) if len(s_row) >= 9 else "0"
        try:
            s_points = int(float(val)) if val else 0
        except:
            s_points = 0

    except Exception as e:
        st.error("❌ خطأ أثناء تحميل بيانات الطالب.")
        st.exception(e)
        st.stop()

    if s_points < 10:
        next_badge, points_to_next = "البرونزي 🥉", 10 - s_points
    elif s_points < 50:
        next_badge, points_to_next = "الفضي 🥈", 50 - s_points
    elif s_points < 100:
        next_badge, points_to_next = "الذهبي 🥇", 100 - s_points
    else:
        next_badge, points_to_next = "أنت في القمة 👑", 0

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 18px; border-radius: 16px; color: white; text-align: center; margin: 8px 0 16px 0; box-shadow: 0 8px 18px rgba(2,6,23,0.12); border-bottom: 5px solid #f59e0b;">
            <h2 style="margin:0; font-size: 1.45rem;">🎯 إنجاز الطالب: <span style="color:#ffd700;">{s_name}</span></h2>
            <div style="margin-top:10px;">
                <span class="badge-chip">🏫 {s_class}</span>
                <span class="badge-chip">🆔 {st.session_state.sid}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="kpi-card" style="text-align:center; padding:18px; border:2px solid rgba(245,158,11,0.25);">
            <div style="display:flex; gap:10px; justify-content:space-around; margin-bottom:12px; flex-wrap:wrap;">
                <div class="badge-chip" style="border-color:#cd7f32; opacity:{'1' if s_points>=10 else '0.35'};">🥉 برونزي</div>
                <div class="badge-chip" style="border-color:#c0c0c0; opacity:{'1' if s_points>=50 else '0.35'};">🥈 فضي</div>
                <div class="badge-chip" style="border-color:#ffd700; opacity:{'1' if s_points>=100 else '0.35'};">🥇 ذهبي</div>
            </div>
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color:white; padding:14px; border-radius:16px;">
                <div style="font-weight:800; font-size:1.0rem;">رصيد النقاط السلوكية</div>
                <div style="font-size:3.2rem; font-weight:900; line-height:1.1;">{s_points}</div>
                {"<div style='margin-top:8px; background: rgba(255,255,255,0.2); padding:8px; border-radius:12px; font-weight:800;'>🚀 بقي لك " + str(points_to_next) + " نقطة للوصول إلى " + next_badge + "</div>" if points_to_next>0 else "<div style='margin-top:8px; background: rgba(255,255,255,0.2); padding:8px; border-radius:12px; font-weight:800;'>👑 ممتاز! " + next_badge + "</div>"}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "🏆 المتصدرون", "⚙️ الإعدادات"])

    with t_ex:
        st.markdown('<h3 style="color:#1e3a8a;">📢 التنبيهات الخاصة بك</h3>', unsafe_allow_html=True)
        if df_ex.empty:
            st.info("لا توجد تنبيهات حالياً.")
        else:
            f_ex = df_ex[(df_ex.iloc[:, 0].astype(str) == s_class) | (df_ex.iloc[:, 0].astype(str) == "الكل")]
            if f_ex.empty:
                st.info("لا توجد تنبيهات لهذا الصف حالياً.")
            else:
                for _, r in f_ex.iloc[::-1].iterrows():
                    st.markdown(
                        f"""
                        <div style="background:#0b1b3a; padding:14px; border-radius:14px; border-right:7px solid #f59e0b; margin-bottom:10px;">
                            <b style="color:#ffd700; font-size:1.1rem;">📢 {_safe_str(r[1])}</b><br>
                            <span style="color:white; opacity:0.9;">📅 {_safe_str(r[2])}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with t_grade:
        st.markdown('<h3 style="color:#1e3a8a;">📊 السجل الأكاديمي</h3>', unsafe_allow_html=True)

        g_data = pd.DataFrame()
        if not df_grades.empty:
            g_data = df_grades[df_grades.iloc[:, 0].astype(str) == s_name]

        if g_data.empty:
            st.info("لا توجد درجات مسجلة لك حتى الآن.")
            p1 = p2 = part = "-"
        else:
            p1 = _safe_str(g_data.iloc[0, 1]) if g_data.shape[1] > 1 else "-"
            p2 = _safe_str(g_data.iloc[0, 2]) if g_data.shape[1] > 2 else "-"
            part = _safe_str(g_data.iloc[0, 3]) if g_data.shape[1] > 3 else "-"

        def grade_card(title, value, accent):
            return f"""
            <div class="kpi-card" style="display:flex; justify-content:space-between; align-items:center; border-right:6px solid {accent}; margin-bottom:10px;">
                <b style="font-size:1.05rem; color:#0f172a;">{title}</b>
                <b style="font-size:1.7rem; color:{accent};">{value}</b>
            </div>
            """

        st.markdown(grade_card("📌 الفترة الأولى", p1, "#3b82f6"), unsafe_allow_html=True)
        st.markdown(grade_card("📌 الفترة الثانية", p2, "#10b981"), unsafe_allow_html=True)
        st.markdown(grade_card("⭐ المشاركة", part, "#f59e0b"), unsafe_allow_html=True)

    with t_beh:
        st.markdown('<h3 style="color:#1e3a8a;">🎭 سجل الانضباط</h3>', unsafe_allow_html=True)
        if df_beh.empty:
            st.info("لا توجد سجلات سلوك.")
        else:
            f_beh = df_beh[df_beh.iloc[:, 0].astype(str) == s_name]
            if f_beh.empty:
                st.info("لا توجد ملاحظات سلوكية مسجلة لك.")
            else:
                for _, r in f_beh.iloc[::-1].iterrows():
                    typ = _safe_str(r[2])
                    is_pos = any(x in typ for x in ["+", "🌟", "✅"])
                    border = "#065f46" if is_pos else "#991b1b"
                    bg = "#f0fdf4" if is_pos else "#fef2f2"
                    icon = "✅" if is_pos else "⚠️"
                    st.markdown(
                        f"""
                        <div style="background:{bg}; padding:14px; border-radius:14px; border-right:7px solid {border}; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b style="color:{border}; font-size:1.05rem;">{icon} {typ}</b>
                                <span style="opacity:0.75;">{_safe_str(r[1])}</span>
                            </div>
                            <div style="margin-top:6px; font-weight:800; color:#0f172a;">{_safe_str(r[3])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with t_lead:
        st.markdown('<h3 style="color:#1e3a8a;">🏆 لوحة المتصدرين</h3>', unsafe_allow_html=True)
        if df_st.empty:
            st.info("لا توجد بيانات.")
        else:
            leader_list = df_st.values.tolist()

            def get_points(row) -> int:
                try:
                    return int(float(_safe_str(row[8])))
                except:
                    return 0

            leader_list.sort(key=get_points, reverse=True)
            top = leader_list[:10]

            for i, row in enumerate(top, start=1):
                name = _safe_str(row[1])
                pts = get_points(row)
                is_me = (name == s_name)

                if i == 1:
                    icon, col = "👑", "#ffd700"
                elif i == 2:
                    icon, col = "🥈", "#94a3b8"
                elif i == 3:
                    icon, col = "🥉", "#cd7f32"
                else:
                    icon, col = f"#{i}", "#64748b"

                st.markdown(
                    f"""
                    <div class="kpi-card" style="border:{'3px solid #1e3a8a' if is_me else '1px solid #e2e8f0'}; background:{'#eff6ff' if is_me else 'white'}; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="width:42px; text-align:center; font-weight:900; color:{col};">{icon}</div>
                            <div style="font-weight:800; color:#0f172a;">{name} {"<span class='badge-chip'>أنت</span>" if is_me else ""}</div>
                        </div>
                        <div style="background:{col}; color:white; padding:6px 14px; border-radius:12px; font-weight:900;">{pts}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with t_set:
        st.markdown('<h3 style="color:#1e3a8a;">⚙️ الإعدادات</h3>', unsafe_allow_html=True)
        with st.form("student_settings"):
            current_email = _safe_str(s_row[6]) if len(s_row) > 6 else ""
            current_phone = _safe_str(s_row[7]) if len(s_row) > 7 else ""

            m = st.text_input("📧 البريد الإلكتروني", value=current_email)
            p = st.text_input("📱 جوال ولي الأمر", value=current_phone)

            save = st.form_submit_button("✅ حفظ التعديلات", use_container_width=True)
            if save:
                try:
                    w = ws("students")
                    cell = w.find(_safe_str(st.session_state.sid), in_column=1)
                    w.update_cell(cell.row, 7, _safe_str(m))
                    w.update_cell(cell.row, 8, _safe_str(p))
                    st.success("✅ تم الحفظ")
                    clear_cache_and_rerun(0.4)
                except Exception as e:
                    st.error("تعذر حفظ التعديلات.")
                    st.exception(e)

    st.write("")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None
        st.session_state.sid = None
        clear_cache_and_rerun(0.1)
