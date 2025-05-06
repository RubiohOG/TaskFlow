from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from app.persistence import get_user_by_username, get_user_by_email, save_user

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_username(form.username.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verificar que el usuario no exista
        if get_user_by_username(form.username.data) is not None:
            flash('Username already taken.')
            return redirect(url_for('auth.register'))
        
        if get_user_by_email(form.email.data) is not None:
            flash('Email already registered.')
            return redirect(url_for('auth.register'))
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        save_user(user)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form) 