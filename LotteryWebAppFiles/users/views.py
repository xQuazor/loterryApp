# IMPORTS
import bcrypt
from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from markupsafe import Markup
from datetime import datetime

from app import db
from models import User
from users.forms import RegisterForm, LoginForm
import logging

from flask_login import login_user, UserMixin, logout_user, current_user, login_required
import pyotp

from functools import wraps

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')
logger = logging.getLogger()


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                return render_template('errors/403.html')
            return f(*args, **kwargs)

        return wrapped

    return wrapper


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        role='user')

        # add the new user to the database
        logging.warning('SECURITY - User registration [%s, %s]',
                        form.email.data,
                        request.remote_addr)

        db.session.add(new_user)
        db.session.commit()

        # sends user to login page
        return redirect(url_for('users.login'))
    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


# view user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():

    # set authentication_attempts counter
    if not session.get('authentication_attempts'):
        session['authentication_attempts'] = 0

    # init login form
    form = LoginForm()

    if form.validate_on_submit():
        # search for any occurrences of submitted email in db
        user = User.query.filter_by(email=form.email.data).first()

        # check if user exists and if the password and one time pin are correct
        if not user \
                or not bcrypt.checkpw(form.password.data.encode('utf-8'), user.password):
                #\ or not pyotp.TOTP(user.pinkey).verify(form.pin.data):

            # log unsuccessful login attempt
            logger.warning('SECURITY - Invalid Log in [%s, %s]',
                           form.email.data,
                           request.remote_addr)

            # count session authentication_attempts
            session['authentication_attempts'] += 1
            print(session.get('authentication_attempts'))

            # if the maximum authentication threshold is reached, prohibit from login and ask to reset counter
            if session.get('authentication_attempts') >= 3:
                flash(Markup('Number of incorrect login attempts has been exceeded.'
                             ' Please click <a href="/reset">here</a> to reset.'))
                return render_template('users/login.html')

            flash('Try checking your login details and try again, '
                  '{} login attempts remaining'.format(3 - session.get('authentication_attempts')))
            return render_template('users/login.html', form=form)

        # log current login date and time
        current_user.current_login = datetime.now()
        current_user.last_login = current_user.current_login

        # update date and time of last login
        user.current_login = current_user.current_login
        user.last_login = user.current_login

        # update database with new login time values
        db.session.add(user)
        db.session.commit()

        # login user and log event in log file
        login_user(user)
        logger.warning('SECURITY - Log in [%s, %s, %s]',
                        current_user.id,
                        current_user.email,
                        request.remote_addr)

        # depending on the role, redirects guest to admin or user page
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin'))
        else:
            return redirect(url_for('users.profile'))

    return render_template('users/login.html', form=form)


# view user profile
@users_blueprint.route('/profile')
@login_required
@requires_roles('user')
def profile():
    return render_template('users/profile.html', name=current_user.firstname)


# view user account
@users_blueprint.route('/account')
@login_required
@requires_roles('user', 'admin')
def account():
    return render_template('users/account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)


# resets authentication attempts counter
@users_blueprint.route('/reset')
def reset():
    session['authentication_attempts'] = 0
    return redirect(url_for('users.login'))


# logs out user
@users_blueprint.route('/logout')
@login_required
@requires_roles('user', 'admin')
def logout():
    logger.warning('SECURITY - Log Out [%s, %s, %s]',
                   current_user.id,
                   current_user.email,
                   request.remote_addr)
    logout_user()
    return redirect(url_for('index'))
