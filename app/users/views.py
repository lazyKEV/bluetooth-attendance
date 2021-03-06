from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import User
from app.tasks import send_reset_mail
from app.users.forms import LoginForm, RequestResetForm, ResetPasswordForm

users = Blueprint("users", __name__)


# User login
@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome {user.name}!', 'success')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for("users.dashboard"))
        else:
            flash(f'Invalid username or password!', category='danger')

    return render_template('login.html', form=form, title='Login')


# User Logout
@users.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You are now logged out', category='info')

    return redirect(url_for('index'))


# User dashboard
@users.route('/dashboard')
@login_required
def dashboard():
    if current_user.type == "students":
        return render_template('dashboardStu.html')
    else:
        return render_template('dashboardPro.html')


# Request password reset
@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        email = user.email
        url = url_for('users.reset_password', token=user.get_reset_token(),
                      _external=True)
        send_reset_mail.queue(email, url)
        flash('An email has been sent with the instructions to reset your password!', 'warning')
        return redirect(url_for('users.login'))

    return render_template('reset_request.html', title='Reset Password',
                           form=form)


# Reset password
@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('The token is invalid or expired!', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = user.generate_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset successfully! Please Login", 'info')
        return redirect(url_for('users.login'))

    return render_template('reset_password.html', title='Reset Password',
                           form=form)
