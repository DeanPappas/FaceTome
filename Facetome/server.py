from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, URL, Email
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor, CKEditorField
import datetime as dt

app = Flask(__name__)
Bootstrap5(app)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Login Manager config
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# CREATE TABLE IN DB
class User(db.Model, UserMixin): # <-- UserMixin covers the required fields for flask login
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

class Post(db.Model):
    __tablename__ = 'post'
    id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), primary_key=True)
    content: Mapped[str] = mapped_column(String(250))
    date: Mapped[str] = mapped_column(String(30))


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    birthday = DateField('Birthday', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    user_id = current_user.get_id()
    result = db.session.execute(db.select(User).where(User.id == user_id))
    # user = current_user.name
    user = current_user
    # Passing True or False if the user is authenticated.
    return render_template("index.html", logged_in=current_user.is_authenticated, user=user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        email = form.email.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('register'))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            name=form.name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    # Passing True or False if the user is authenticated.
    return render_template("register.html", logged_in=current_user.is_authenticated, form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    # Passing True or False if the user is authenticated.
    return render_template("login.html", logged_in=current_user.is_authenticated, form=form)


@app.route('/logout')
def logout():
    # Log out current user
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)