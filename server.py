from flask import Flask, redirect, render_template, sessions, url_for, request, flash, abort
from flask_bootstrap import Bootstrap
from flask_login.utils import login_url
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from wtforms import StringField, SubmitField, EmailField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Length, Email
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, login_required, login_user, logout_user, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urljoin
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL1', "sqlite:///todo.db")
db = SQLAlchemy(app)
Bootstrap(app=app)
login_manager = LoginManager(app)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    folders = relationship('Folder')


class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False, unique=True)
    tasks = relationship("Task")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', back_populates="folders")


class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    folder = relationship('Folder', back_populates="tasks")


class FolderForm(FlaskForm):
    title = StringField("Folder title:", validators=[
                        DataRequired(), Length(max=40)])
    submit = SubmitField('Add')


class TaskForm(FlaskForm):
    title = StringField("Folder title:", validators=[
                        DataRequired(), Length(max=100)])
    submit = SubmitField('Add')


class RegisterForm(FlaskForm):
    first_name = StringField('First name:', validators=[
                             DataRequired(), Length(max=20)])
    last_name = StringField('Last name:', validators=[
                            DataRequired(), Length(max=20)])
    email = EmailField('Email:', validators=[
                       DataRequired(), Length(max=250), Email()])
    email_val = EmailField('Confirm email::', validators=[
                           DataRequired(), Length(max=250), Email()])
    password = PasswordField('Password:', validators=[
                             DataRequired(), Length(max=250)])
    password_val = PasswordField('Confirm password:', validators=[
                                 DataRequired(), Length(max=250)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = EmailField('Email:', validators=[
                       DataRequired(), Length(max=250), Email()])
    password = PasswordField('Password:', validators=[
                             DataRequired(), Length(max=250)])
    submit = SubmitField('Login')
    
db.create_all()

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def check_existing_user(email):
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return True
    return False


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/')
def home():
    folders = db.session.query(Folder).all()
    return render_template('index.htm', folders=folders)

@app.route('/add/folder', methods=["GET", "POST"])
@login_required
def add_folder():
    form = FolderForm()
    if form.validate_on_submit():

        new_folder = Folder(title=form.title.data, user_id=current_user.id)
        try:
            db.session.add(new_folder)
            db.session.commit()
        except IntegrityError:
            flash('Folder already exists')
            return render_template('add.htm', form=form)
        return redirect(url_for('home'))
    print(form.validate_on_submit())
    print(form.title.data)
    return render_template('add.htm', form=form)

@app.route('/add/task/<int:folder_id>', methods=["GET", "POST"])
@login_required
def add_task(folder_id):
    form = TaskForm()
    folder = db.session.query(Folder).get(folder_id)
    if form.validate_on_submit():
        new_task = Task(content=form.title.data, folder_id=folder_id)
        try:
            db.session.add(new_task)
            db.session.commit()
        except IntegrityError:
            flash('Folder already exists')
            return render_template('add_task.htm', form=form, folder=folder)
        return redirect(url_for('home'))
    print(form.validate_on_submit())
    print(form.title.data)
    return render_template('add_task.htm', form=form, folder=folder)

@app.route('/del/task/<int:id>')
@login_required
def delete_task(id):
    task = db.session.query(Task).get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/del/folder/<int:id>')
@login_required
def delete_folder(id):
    tasks = db.session.query(Task).filter_by(folder_id=id).all()
    if len(tasks) > 0:
        for task in tasks:
            db.session.delete(task)
        db.session.commit()
    folder = db.session.query(Folder).get(id)
    db.session.delete(folder)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/register', methods=["GET", "POST"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        if not form.password.data == form.password_val.data:
            flash("Passwords do not match")
            return redirect(url_for('register_user'))
        elif not form.email.data == form.email_val.data:
            flash("Emails do not match")
            return redirect(url_for('register_user'))
        else:
            pw_hash = generate_password_hash(
                method='pbkdf2:sha256:80000', password=form.password.data)
            new_user = User(first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            email=form.email.data,
                            password=pw_hash)
            if check_existing_user(form.email.data):
                flash("User already registered.")
                return redirect(url_for('login'))
            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.htm', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if check_existing_user(form.email.data):
            user = db.session.query(User).filter_by(email=form.email.data).first()
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Incorrect password')
                return redirect(url_for('login'))
        else:
            flash('Email not found, please register.')
            return redirect(url_for('register_user'))
    return render_template('login.htm', form=form)
    
@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
