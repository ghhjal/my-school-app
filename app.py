import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام متابعة الطالب اليومي", layout="wide")

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_daily_v4.db')
    c = conn.cursor()
    # جدول لتخزين السجلات اليومية
    c.execute('''CREATE TABLE IF NOT EXISTS daily_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  student_id TEXT,
                  log_date TEXT,
                  pos_behavior TEXT,
                  neg_behavior TEXT,
                  neg_count INTEGER,
                  reward TEXT,
                  notes TEXT)''')
    # جدول منفصل لأسماء الطلاب الأساسية
    c.execute('''CREATE TABLE IF NOT EXISTS students_master (student_id TEXT PRIMARY KEY, name TEXT)''')
    conn.commit()
    conn.close()

def get_master_students():
    conn = sqlite3.connect('school_daily_v4.db')
    df = pd.read_sql_query("SELECT * FROM students_master", conn)
    conn.close()
    return df

# --- واجهة البرنامج الرئيسية ---
init_db()
st.title("🗓️ نظام متابعة الطالب اليومي")

menu = st.sidebar.selectbox("اختر نوع الدخول:", ["لوحة الطالب", "لوحة المعلم 🔐"])

# ------------------- لوحة المعلم -------------------
if menu == "لوحة المعلم 🔐":
    password = st.sidebar.text_input("أدخل كلمة مرور المعلم", type="password")
    if password == "1234": # كلمة المرور: 1234
        st.sidebar.success("تم الدخول بنجاح")
        
        tab1, tab2, tab3 = st.tabs(["➕ إضافة سجل يومي", "จัดการ إدارة الطلاب الأساسية", "📋 عرض كل السجلات"])
        
        with tab1:
            st.subheader("إضافة سجل متابعة يومي جديد")
            df_master = get_master_students()
            if df_master.empty:
                st.warning("الرجاء إضافة أسماء الطلاب أولاً في التبويب المجاور.")
            else:
                with st.form("daily_log_form"):
                    selected_student = st.selectbox("اختر اسم الطالب", df_master['name'].tolist())
                    # نحصل على ال ID من الاسم
                    s_id = df_master[df_master['name'] == selected_student]['student_id'].iloc[0]
                    
                    log_date = st.date_input("اليوم / التاريخ", datetime.date.today())
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        pos_behavior = st.text_input("السلوك الإيجابي (مثال: مشاركة)")
                        reward = st.text_area("المكافأة / التعزيز (مثال: نجمتان)")
                    with col_b2:
                        neg_behavior = st.text_input("السلوك السلبي (مثال: صراخ)")
                        neg_count = st.number_input("عدد المخالفات", 0, 100, 0)
                    
                    notes = st.text_area("ملاحظات (مثال: كان متعباً)")
                    
                    submit = st.form_submit_button("حفظ السجل اليومي")
                    
                    if submit:
                        conn = sqlite3.connect('school_daily_v4.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO daily_logs (student_id, log_date, pos_behavior, neg_behavior, neg_count, reward, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (s_id, str(log_date), pos_behavior, neg_behavior, neg_count, reward, notes))
                        conn.commit()
                        st.success(f"تم تسجيل متابعة يوم {log_date} للطالب {selected_student}")

        with tab2:
            st.subheader("إدارة قائمة الطلاب الأساسية")
            with st.form("add_master_student"):
                new_s_id = st.text_input("الرقم الأكاديمي الجديد")
                new_s_name = st.text_input("اسم الطالب الجديد")
                if st.form_submit_button("إضافة طالب أساسي"):
                    try:
                        conn = sqlite3.connect('school_daily_v4.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO students_master VALUES (?, ?)", (new_s_id, new_s_name))
                        conn.commit()
                        st.success(f"تم إضافة {new_s_name} للقائمة الأساسية")
                    except:
                        st.error("الرقم الأكاديمي موجود مسبقاً.")
            st.dataframe(df_master)

        with tab3:
            st.subheader("كل السجلات اليومية")
            df_logs = pd.read_sql_query("SELECT * FROM daily_logs", sqlite3.connect('school_daily_v4.db'))
            st.dataframe(df_logs, use_container_width=True)
            
    else:
        st.warning("يرجى إدخال كلمة المرور الصحيحة.")

# ------------------- لوحة الطالب (ولي الأمر) -------------------
elif menu == "لوحة الطالب":
    st.header("🔍 استعلام الطالب وولي الأمر")
    search_id = st.text_input("أدخل الرقم الأكاديمي للطالب:")
    
    if st.button("عرض جدول المتابعة"):
        if search_id:
            conn = sqlite3.connect('school_daily_v4.db')
            df_logs = pd.read_sql_query("SELECT * FROM daily_logs WHERE student_id=?", conn, params=(search_id,))
            df_name = pd.read_sql_query("SELECT name FROM students_master WHERE student_id=?", conn, params=(search_id,))
            conn.close()

            if not df_logs.empty and not df_name.empty:
                student_name = df_name.iloc[0]['name']
                st.subheader(f"جدول المتابعة اليومي للطالب/ة: {student_name}")

                # إعادة تسمية الأعمدة لتتناسب مع الصورة تماماً
                df_logs_styled = df_logs[['log_date', 'pos_behavior', 'neg_behavior', 'neg_count', 'reward', 'notes']]
                df_logs_styled.columns = ['اليوم / التاريخ', 'السلوك الإيجابي (مثال: مشاركة)', 'السلوك السلبي (مثال: صراخ)', 'عدد المخالفات', 'المكافأة / التعزيز', 'ملاحظات']
                
                # عرض الجدول لولي الأمر
                st.table(df_logs_styled) 
                
            elif not df_name.empty and df_logs.empty:
                st.info(f"الطالب {df_name.iloc[0]['name']} مسجل في النظام الأساسي ولكن لا يوجد سجل متابعة يومي حتى الآن.")
            else:
                st.error("عذراً، هذا الرقم الأكاديمي غير مسجل في النظام.")
        else:
            st.warning("يرجى إدخال الرقم أولاً")
