# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'twoj-tajny-klucz'  # Zmień to na bezpieczny klucz
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cms.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Model użytkownika (administrator)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

# Model zawartości strony
class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    opening_hours = db.Column(db.String(200), nullable=False)
    logo_path = db.Column(db.String(200))

# Nowy model nauczyciela
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    photo_path = db.Column(db.String(200))
    courses = db.relationship('Course', backref='teacher', lazy=True)

# Nowy model kursu
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Strona główna dla klientów
@app.route('/')
def home():
    content = Content.query.first()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('public/home.html', content=content, teachers=teachers, courses=courses)

# Panel logowania
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Nieprawidłowe dane logowania')
    return render_template('admin/login.html')

# Panel administratora
@app.route('/admin')
@login_required
def admin_dashboard():
    content = Content.query.first()
    return render_template('admin/dashboard.html', content=content)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("Zostałeś wylogowany")
    return redirect(url_for('login'))


# Edycja zawartości
@app.route('/admin/edit/title', methods=['POST'])
@login_required
def edit_title():
    content = Content.query.first()
    if content:
        content.title = request.form['title']
        db.session.commit()
        flash('Tytuł został zaktualizowany')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/description', methods=['POST'])
@login_required
def edit_description():
    content = Content.query.first()
    if content:
        content.description = request.form['description']
        db.session.commit()
        flash('Opis został zaktualizowany')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/opening_hours', methods=['POST'])
@login_required
def edit_opening_hours():
    content = Content.query.first()
    if content:
        content.opening_hours = request.form['opening_hours']
        db.session.commit()
        flash('Godziny otwarcia zostały zaktualizowane')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/logo', methods=['POST'])
@login_required
def edit_logo():
    content = Content.query.first()
    if 'logo' in request.files:
        file = request.files['logo']
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if content:
                content.logo_path = filename
                db.session.commit()
                flash('Logo zostało zaktualizowane')
    return redirect(url_for('admin_dashboard'))


# Nowe endpointy dla nauczycieli
@app.route('/admin/teachers')
@login_required
def manage_teachers():
    teachers = Teacher.query.all()
    return render_template('admin/teachers.html', teachers=teachers)

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        # Check if email already exists
        existing_teacher = Teacher.query.filter_by(email=request.form['email']).first()
        if existing_teacher:
            flash('Nauczyciel z tym adresem email już istnieje w Twojej szkole!')
            return redirect(url_for('manage_teachers'))
            
        try:
            photo = request.files['photo']
            if photo:
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename
            else:
                photo_path = None

            teacher = Teacher(
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                email=request.form['email'],
                specialization=request.form['specialization'],
                bio=request.form['bio'],
                photo_path=photo_path
            )
            db.session.add(teacher)
            db.session.commit()
            flash('Nauczyciel został dodany')
            return redirect(url_for('manage_teachers'))
            
        except Exception as e:
            db.session.rollback()
            flash('Wystąpił błąd podczas dodawania nauczyciela')
            return redirect(url_for('manage_teachers'))
            
    return render_template('admin/add_teacher.html')


@app.route('/admin/teacher/delete/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def delete_teacher(teacher_id):
    
    teacher = Teacher.query.get(teacher_id)

    if teacher.courses:
        flash("Próbujesz usunąć nauczyciela, który prowadzi obecnie kursy!")
        return redirect(url_for('manage_teachers'))

    db.session.delete(teacher)
    db.session.commit()
    flash('Nauczyciel został usunięty')
    return redirect(url_for('manage_teachers'))

@app.route('/admin/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    
    if request.method == 'POST':
        # Check if email changed and if new email already exists
        new_email = request.form['email']
        if new_email != teacher.email:
            existing_teacher = Teacher.query.filter_by(email=new_email).first()
            if existing_teacher:
                flash('Nauczyciel z tym adresem email już istnieje w Twojej szkole!')
                return redirect(url_for("manage_teachers"))

        try:
            teacher.first_name = request.form['first_name']
            teacher.last_name = request.form['last_name']
            teacher.email = new_email
            teacher.specialization = request.form['specialization']
            teacher.bio = request.form['bio']
            
            # Obsługa zdjęcia
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    # Usuń stare zdjęcie jeśli istnieje
                    if teacher.photo_path:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], teacher.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Zapisz nowe zdjęcie
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    teacher.photo_path = filename

            db.session.commit()
            flash('Dane nauczyciela zostały zaktualizowane')
            return redirect(url_for('manage_teachers'))
            
        except Exception as e:
            db.session.rollback()
            flash('Wystąpił błąd podczas aktualizacji danych nauczyciela')
            return redirect(url_for("manage_teachers"))
        
    return render_template('admin/edit_teacher.html', teacher=teacher)






# Nowe endpointy dla kursów
@app.route('/admin/courses')
@login_required
def manage_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course = Course(
            name=request.form['name'],
            description=request.form['description'],
            level=request.form['level'],
            price=float(request.form['price']),
            duration=int(request.form['duration']),
            teacher_id=int(request.form['teacher_id']),
            is_active=True if request.form.get('is_active') else False
        )
        db.session.add(course)
        db.session.commit()
        flash('Kurs został dodany')
        return redirect(url_for('manage_courses'))
    teachers = Teacher.query.all()
    return render_template('admin/add_course.html', teachers=teachers)

@app.route('/admin/courses/delete/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    
    course = Course.query.get(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Kurs został usunięty')
    return redirect(url_for('manage_courses'))



@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    
    course = Course.query.get(course_id)
    
    if request.method == 'POST':
        course.name = request.form['name']
        course.description = request.form['description']
        course.level = request.form['level']
        course.price = float(request.form['price'])
        course.duration = int(request.form['duration'])
        course.teacher_id = int(request.form['teacher_id'])
        course.is_active = True if request.form.get('is_active') else False

        db.session.commit()
        flash('Kurs został edytowany')
        return redirect(url_for('manage_courses'))
    
    teachers = Teacher.query.all()
    return render_template('admin/edit_course.html', course=course, teachers=teachers)

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Nieprawidłowa nazwa użytkownika')
            return redirect(url_for('change_password'))
            
        if not check_password_hash(user.password_hash, old_password):
            flash('Nieprawidłowe obecne hasło')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('Nowe hasła nie są identyczne')
            return redirect(url_for('change_password'))
            
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Hasło zostało zmienione pomyślnie')
        return redirect(url_for('login'))
        
    return render_template('admin/change_password.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)