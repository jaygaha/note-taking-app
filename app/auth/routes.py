from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from app.models import User

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register', form=form)    

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check if user exists, password is correct, and user is not deleted
        if user and user.check_password(form.password.data) and not user.is_deleted:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            # Redirect to the next page or the home page if no next page is specified
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('notes.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)    

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

