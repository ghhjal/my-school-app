import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os

# --- إعداد قاعدة البيانات ---
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'school.db')
DATABASE_URL = f"sqlite:///{db_path}"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# تعريف النماذج (Models)
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    student_id = Column(String(20), unique=True, nullable=False)
    # Grades relation is not needed for this basic example view

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    subject = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)
    student_db_id = Column(Integer, ForeignKey('students.id'), nullable=False)

# إنشاء الجداول عند التشغيل الأول
Base.metadata.create_all(engine)

# --- واجهة المستخدم Streamlit ---

st.title("👨‍🎓 نظام إدارة الطلاب والدرجات (Streamlit)")

# تبويبات (Tabs) للتنقل بين إضافة طالب وإضافة درجة
tab1, tab2, tab3 = st.tabs(["إضافة طالب جديد", "إضافة درجة أكاديمية", "عرض البيانات"])

with tab1:
    st.header("إضافة طالب جديد")
    with st.form("add_student_form"):
        # حقول الإدخال
        name = st.text_input("الاسم الكامل", key="s_name")
        student_id = st.text_input("الرقم الجامعي", key="s_id")
        
        # زر الإرسال
        submitted = st.form_submit_button("حفظ الطالب")

        if submitted:
            try:
                new_student = Student(name=name, student_id=student_id)
                session.add(new_student)
                session.commit()
                st.success(f"تم حفظ الطالب **{name}** بنجاح!")
            except Exception as e:
                st.error(f"حدث خطأ: تأكد من أن الرقم الجامعي فريد. الخطأ: {e}")
                session.rollback()

with tab2:
    st.header("إضافة درجة أكاديمية")
    # جلب قائمة الطلاب لعرضها في قائمة منسدلة
    students = session.query(Student).all()
    student_options = {f"{s.name} ({s.student_id})": s.id for s in students}
    
    if not students:
        st.warning("الرجاء إضافة طالب واحد على الأقل أولاً.")
    else:
        with st.form("add_grade_form"):
            selected_student_name = st.selectbox("اختر الطالب", list(student_options.keys()))
            subject = st.text_input("المادة الدراسية")
            score = st.number_input("الدرجة", min_value=0, max_value=100)
            
            submitted_grade = st.form_submit_button("حفظ الدرجة")

            if submitted_grade:
                student_db_id = student_options[selected_student_name]
                new_grade = Grade(subject=subject, score=score, student_db_id=student_db_id)
                session.add(new_grade)
                session.commit()
                st.success(f"تم حفظ درجة **{subject}** للطالب {selected_student_name} بنجاح!")

with tab3:
    st.header("البيانات المخزنة")
    st.subheader("الطلاب")
    students_data = session.query(Student).all()
    st.table([{"الاسم": s.name, "الرقم الجامعي": s.student_id} for s in students_data])
    
    st.subheader("الدرجات")
    grades_data = session.query(Grade, Student.name).join(Student).all()
    grades_list = [{"الطالب": name, "المادة": g.subject, "الدرجة": g.score} for g, name in grades_data]
    st.table(grades_list)

