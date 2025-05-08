from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User
from app.persistence import get_user_by_username, get_user_by_email, save_user, get_user_by_id
import os

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

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        user = get_user_by_id(current_user.id)
        user.email = form.email.data
        user.company = form.company.data
        # Manejo de foto de perfil
        if form.profile_picture.data:
            pic = form.profile_picture.data
            filename = secure_filename(pic.filename)
            # Guardar en app/static/profile_pics
            pic_folder = os.path.join(os.path.dirname(__file__), '..', 'static', 'profile_pics')
            pic_folder = os.path.abspath(pic_folder)
            os.makedirs(pic_folder, exist_ok=True)
            pic_path = os.path.join(pic_folder, filename)
            pic.save(pic_path)
            user.profile_picture = '/static/profile_pics/' + filename
        # Cambio de contraseña
        if form.new_password.data:
            user.set_password(form.new_password.data)
        save_user(user)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.edit_profile'))
    else:
        form.email.data = current_user.email
        form.company.data = getattr(current_user, 'company', '')
    return render_template('auth/edit_profile.html', form=form, user=current_user) 