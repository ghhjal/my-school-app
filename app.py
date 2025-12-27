import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS grades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, subject TEXT, score INTEGER, grade TEXT)''')
    conn.commit()
    conn.close()

def add_to_db(name, subject, score, grade):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO grades (name, subject, score, grade) VALUES (?, ?, ?, ?)", (name, subject, score, grade))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('school_data.db')
    df = pd.read_sql_query("SELECT name as الاسم, subject as المادة, score as الدرجة, grade as التقدير FROM grades", conn)
    conn.close()
    return df

# --- 2. واجهة البرنامج ---
st.set_page_config(page_title="نظام درجات الطلاب الدائم", layout="wide")
init_db()

st.title("💾 نظام إدارة الدرجات (مع حفظ البيانات)")

with st.sidebar:
    st.header("➕ إضافة طالب جديد")
    name = st.text_input("اسم الطالب")
    subject = st.selectbox("المادة", ["البرمجة", "الرياضيات", "الفيزياء", "الإنجليزية"])
    score = st.number_input("الدرجة", 0, 100, 50)
    
    if st.button("حفظ في قاعدة البيانات"):
        if name:
            # حساب التقدير
            if score >= 90: g = "ممتاز"
            elif score >= 80: g = "جيد جداً"
            elif score >= 50: g = "ناجح"
            else: g = "راسب"
            
            add_to_db(name, subject, score, g)
            st.success(f"تم حفظ بيانات {name}")
        else:
            st.warning("يرجى كتابة الاسم")

# --- 3. عرض البيانات والإحصائيات ---
df_students = load_data()

if not df_students.empty:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 سجل الدرجات المسجل")
        st.dataframe(df_students, use_container_width=True)
        
        # زر لمسح البيانات إذا أردت
        if st.button("تفريغ السجل (حذف الكل)"):
            conn = sqlite3.connect('school_data.db')
            conn.cursor().execute("DELETE FROM grades")
            conn.commit()
            st.rerun()

    with col2:
        st.subheader("📊 تحليل سريع")
        avg_score = df_students["الدرجة"].mean()
        st.metric("متوسط درجات الفصل", f"{avg_score:.1f}%")
        
        # رسم بياني لتوزيع الدرجات
        chart_data = df_students.groupby("التقدير").size()
        st.bar_chart(chart_data)
else:
    st.info("قاعدة البيانات فارغة حالياً.")
