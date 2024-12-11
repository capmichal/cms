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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Strona główna dla klientów
@app.route('/')
def home():
    content = Content.query.first()
    return render_template('public/home.html', content=content)

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

# Edycja zawartości
@app.route('/admin/edit', methods=['POST'])
@login_required
def edit_content():
    content = Content.query.first()
    if content is None:
        content = Content()
        db.session.add(content)
    
    content.title = request.form['title']
    content.description = request.form['description']
    content.opening_hours = request.form['opening_hours']
    
    if 'logo' in request.files:
        file = request.files['logo']
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            content.logo_path = filename

    db.session.commit()
    flash('Zaktualizowano zawartość')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)