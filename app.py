import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
import pandas as pd

# --- إعداد قاعدة البيانات والنموذج (كود الخلفية/البزنس لوجيك) ---
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'school.db')
DATABASE_URL = f"sqlite:///{db_path}"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
# استخدم session_state لتخزين الجلسة وضمان عدم إنشائها مع كل إعادة تشغيل
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    student_id = Column(String(20), unique=True, nullable=False)
    grades = relationship('Grade', backref='student', cascade="all, delete-orphan") # حذف الدرجات عند حذف الطالب

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    subject = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)
    student_db_id = Column(Integer, ForeignKey('students.id'), nullable=False)

Base.metadata.create_all(engine)

# --- وظائف إدارة البيانات (CRUD Functions) ---
def add_entity(entity):
    try:
        session.add(entity)
        session.commit()
        st.success("تم الحفظ بنجاح!")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        session.rollback()

def delete_student(student_id):
    student = session.query(Student).get(student_id)
    if student:
        session.delete(student)
        session.commit()
        st.warning("تم حذف الطالب وجميع درجاته بنجاح.")

# --- واجهة المستخدم Streamlit (الـ UI) ---
st.title("👨‍🎓 نظام إدارة الطلاب والدرجات المتكامل")

# استخدام الأشرطة الجانبية (Sidebar) لتنظيم أفضل
st.sidebar.header("إدارة النظام")
options = st.sidebar.selectbox("اختر الإجراء:", ["عرض البيانات", "إضافة طالب جديد", "إضافة درجة أكاديمية"])

if options == "إضافة طالب جديد":
    st.header("إضافة طالب جديد")
    with st.form("add_student_form"):
        name = st.text_input("الاسم الكامل")
        student_id = st.text_input("الرقم الجامعي")
        submitted = st.form_submit_button("حفظ الطالب")
        if submitted:
            add_entity(Student(name=name, student_id=student_id))

elif options == "إضافة درجة أكاديمية":
    st.header("إضافة درجة أكاديمية")
    students = session.query(Student).all()
    if students:
        student_options = {f"{s.name} ({s.student_id})": s.id for s in students}
        with st.form("add_grade_form"):
            selected_student_name = st.selectbox("اختر الطالب", list(student_options.keys()))
            subject = st.text_input("المادة الدراسية")
            score = st.number_input("الدرجة", min_value=0, max_value=100)
            submitted_grade = st.form_submit_button("حفظ الدرجة")
            if submitted_grade:
                student_db_id = student_options[selected_student_name]
                add_entity(Grade(subject=subject, score=score, student_db_id=student_db_id))
    else:
        st.warning("الرجاء إضافة طالب واحد على الأقل أولاً.")

elif options == "عرض البيانات":
    st.header("البيانات المخزنة وإدارة الطلاب")
    
    st.subheader("جدول الطلاب")
    students_data = session.query(Student).all()
    # استخدام st.data_editor لإتاحة التعديل والحذف السهل
    if students_data:
        df_students = pd.DataFrame([{"ID": s.id, "الاسم": s.name, "الرقم الجامعي": s.student_id, "عدد الدرجات": len(s.grades)} for s in students_data])
        st.dataframe(df_students, use_container_width=True)
        
        # إضافة إمكانية حذف طالب محدد
        st.subheader("حذف طالب")
        student_ids = [s.id for s in students_data]
        id_to_delete = st.selectbox("اختر ID الطالب لحذفه (سيتم حذف درجاته تلقائياً)", student_ids)
        if st.button("تأكيد حذف الطالب"):
            delete_student(id_to_delete)
            st.experimental_rerun() # إعادة تشغيل التطبيق لعرض التحديث

    st.subheader("جدول الدرجات الأكاديمية")
    grades_data = session.query(Grade, Student.name).join(Student).all()
    if grades_data:
        grades_list = [{"الطالب": name, "المادة": g.subject, "الدرجة": g.score, "ID الدرجة": g.id} for g, name in grades_data]
        st.dataframe(pd.DataFrame(grades_list), use_container_width=True)

