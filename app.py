from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. نموذج الطالب
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    # ربط الطالب بدرجاته (علاقة واحد لمتعدد)
    grades = db.relationship('Grade', backref='student', lazy=True)

# 2. نموذج الدرجات الأكاديمية (هذا ما قد ينقصك)
class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    student_db_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

# 3. دالة حفظ الدرجة الأكاديمية
@app.route('/add_grade/<int:student_id>', methods=['POST'])
def add_grade(student_id):
    if request.method == 'POST':
        subject = request.form.get('subject')
        score = request.form.get('score')
        
        # إنشاء سجل درجة جديد مرتبط بالطلبة عبر الـ ID
        new_grade = Grade(subject=subject, score=float(score), student_db_id=student_id)
        
        try:
            db.session.add(new_grade)
            db.session.commit() # الحفظ النهائي في قاعدة البيانات
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return f"خطأ في حفظ الدرجة: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # إنشاء الجداول الجديدة (Student و Grade)
    app.run(debug=True)
