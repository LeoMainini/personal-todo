from flask import Flask, redirect, render_template, sessions, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', "sqlite:///todo.db")
db = SQLAlchemy(app)
Bootstrap(app)

class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(40), nullable=False, unique=True)
    tasks = relationship("Task")
    
class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    folder = relationship('Folder', back_populates="tasks")
    
class FolderForm(FlaskForm):
    title = StringField("Folder title:", validators=[DataRequired(), Length(max=40)])
    submit = SubmitField('Add')

class TaskForm(FlaskForm):
    title = StringField("Folder title:", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add')
    
    
db.create_all()

@app.route('/')
def home():
    folders = db.session.query(Folder).all()
    return render_template('index.htm', folders = folders)

@app.route('/add/folder', methods=["GET", "POST"])
def add_folder():
    form = FolderForm()
    if form.validate_on_submit():
        
        new_folder = Folder(title=form.title.data)
        try:
            db.session.add(new_folder)
            db.session.commit()
        except IntegrityError:
            flash('Folder already exists')
            return render_template('add.htm', form = form)
        return redirect(url_for('home'))
    print(form.validate_on_submit())
    print(form.title.data)
    return render_template('add.htm', form = form)
    
@app.route('/add/task/<int:folder_id>' , methods=["GET", "POST"])
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
            return render_template('add_task.htm', form = form, folder=folder)
        return redirect(url_for('home'))
    print(form.validate_on_submit())
    print(form.title.data)
    return render_template('add_task.htm', form = form, folder= folder)

@app.route('/del/task/<int:id>')
def delete_task(id):
    task = db.session.query(Task).get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/del/folder/<int:id>')
def delete_folder(id):
    tasks = db.session.query(Task).filter_by(folder_id = id).all()
    if len(tasks) > 0:
        for task in tasks:
            db.session.delete(task)
        db.session.commit()
    folder = db.session.query(Folder).get(id)
    db.session.delete(folder)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
