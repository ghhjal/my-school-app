from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# تعريف نموذج الطالب (Model)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

# الصفحة الرئيسية لعرض الطلاب
@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

# دالة إضافة طالب جديد (تم تصحيحها)
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        # الحصول على البيانات من الفورم
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')

        # إنشاء الكائن الجديد
        new_student = Student(name=name, student_id=student_id, email=email)

        try:
            db.session.add(new_student)
            db.session.commit()  # حفظ البيانات في قاعدة البيانات
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # تراجع في حال حدوث خطأ
            return f"حدث خطأ أثناء الحفظ: {str(e)}"
            
    return render_template('add_student.html')

# تشغيل التطبيق والتأكد من إنشاء الجداول
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ينشئ ملف students.db والجداول تلقائياً
    app.run(debug=True)
