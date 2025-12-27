import streamlit as st
import pandas as pd
import sqlite3

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام متابعة الطالب", layout="wide")

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_v3.db')
    c = conn.cursor()
    # إنشاء جدول الطلاب بالحقول الجديدة
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (student_id TEXT PRIMARY KEY, 
                  name TEXT, 
                  pos_behavior TEXT, 
                  pos_count INTEGER,
                  neg_behavior TEXT, 
                  neg_count INTEGER,
                  participation INTEGER, 
                  projects INTEGER,
                  total_score INTEGER)''')
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect('school_v3.db')
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

# --- واجهة البرنامج الرئيسية ---
init_db()
st.title("📑 نظام متابعة الطالب")

# القائمة الجانبية
menu = st.sidebar.selectbox("اختر نوع الدخول:", ["لوحة الطالب", "لوحة المعلم 🔐"])

# ------------------- لوحة المعلم -------------------
if menu == "لوحة المعلم 🔐":
    st.header("👨‍🏫 لوحة التحكم الخاصة بالمعلم")
    
    # نظام كلمة المرور
    password = st.sidebar.text_input("أدخل كلمة مرور المعلم", type="password")
    if password == "1234":  # يمكنك تغيير كلمة المرور من هنا
        st.sidebar.success("تم الدخول بنجاح")
        
        tab1, tab2, tab3 = st.tabs(["➕ إضافة بيانات طالب", "✏️ تعديل / حذف", "📋 عرض سجل المتابعة"])
        
        with tab1:
            with st.form("add_form"):
                col1, col2 = st.columns(2)
                with col1:
                    s_id = st.text_input("الرقم الأكاديمي للطالب")
                    s_name = st.text_input("اسم الطالب")
                    s_participation = st.number_input("درجة المشاركة", 0, 50, 0)
                    s_projects = st.number_input("درجة المشاريع", 0, 50, 0)
                with col2:
                    s_pos_txt = st.text_area("السلوك الإيجابي (ملاحظات)")
                    s_pos_cnt = st.number_input("عدد السلوكيات الإيجابية", 0, 100, 0)
                    s_neg_txt = st.text_area("السلوك السلبي (ملاحظات)")
                    s_neg_cnt = st.number_input("عدد المخالفات السلبية", 0, 100, 0)
                
                submit = st.form_submit_button("حفظ البيانات")
                
                if submit:
                    if s_id and s_name:
                        total = s_participation + s_projects
                        try:
                            conn = sqlite3.connect('school_v3.db')
                            c = conn.cursor()
                            c.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                      (s_id, s_name, s_pos_txt, s_pos_cnt, s_neg_txt, s_neg_cnt, s_participation, s_projects, total))
                            conn.commit()
                            st.success(f"تم تسجيل بيانات {s_name}")
                        except:
                            st.error("الرقم موجود مسبقاً! استخدم التعديل.")
                    else:
                        st.warning("الاسم والرقم مطلوبان")

        with tab2:
            df = get_all_data()
            if not df.empty:
                selected_id = st.selectbox("اختر الرقم الأكاديمي للتعديل", df['student_id'].tolist())
                # ... منطق التعديل والحذف هنا ...
                if st.button("حذف هذا الطالب", type="primary"):
                    conn = sqlite3.connect('school_v3.db')
                    c.cursor().execute("DELETE FROM students WHERE student_id=?", (selected_id,))
                    conn.commit()
                    st.rerun()
        
        with tab3:
            st.dataframe(get_all_data(), use_container_width=True)
            
    else:
        st.warning("يرجى إدخال كلمة المرور الصحيحة في القائمة الجانبية للوصول للوحة التحكم")

# ------------------- لوحة الطالب -------------------
elif menu == "لوحة الطالب":
    st.header("🔍 استعلام الطالب")
    search_id = st.text_input("أدخل رقمك الأكاديمي")
    
    if st.button("عرض ملف المتابعة"):
        conn = sqlite3.connect('school_v3.db')
        df = pd.read_sql_query("SELECT * FROM students WHERE student_id=?", conn, params=(search_id,))
        conn.close()
        
        if not df.empty:
            s = df.iloc[0]
            st.subheader(f"مرحباً، {s['name']}")
            
            # عرض البيانات في كروت
            c1, c2, c3 = st.columns(3)
            c1.metric("المشاركة", f"{s['participation']}")
            c2.metric("المشاريع", f"{s['projects']}")
            c3.metric("المجموع", f"{s['total_score']}")
            
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.success("🌟 السلوك الإيجابي")
                st.write(f"**عدد المرات:** {s['pos_count']}")
                st.info(f"**ملاحظات:** {s['pos_behavior']}")
            with col_b:
                st.error("⚠️ السلوك السلبي (المخالفات)")
                st.write(f"**عدد المخالفات:** {s['neg_count']}")
                st.info(f"**ملاحظات:** {s['neg_behavior']}")
        else:
            st.error("الرقم غير موجود.")
