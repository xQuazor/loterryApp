# IMPORTS
from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_talisman import Talisman
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
import os
import logging

# CONFIG
app = Flask(__name__)
app.config['SECRET_KEY'] = 'LongAndRandomSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')
app.config['GOOGLEMAPS_KEY'] = "8JZ7i18MjFuM35dJHq70n3Hx4"

# Logging code

class SecurityFilter(logging.Filter):
    def filter(self, record):
        return 'SECURITY' in record.getMessage()


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('lottery.log', 'a')
file_handler.setLevel(logging.WARNING)
file_handler.addFilter(SecurityFilter())
formatter = logging.Formatter('%(asctime)s : %(message)s', '%m/%d/%Y %I:%M:%S %p')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# initialise database
db = SQLAlchemy(app)

# initialise Google Maps

# configuration for talisman
csp = {
'default-src': [
            '\'self\'',
            'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'
],

'frame-src':[
            '\'self\'',
            'https://www.google.com/recaptcha/',
            'https://recaptcha.google.com/recaptcha/'
],
'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://www.google.com/recaptcha/',
            'https://www.gstatic.com/recaptcha/'
]
}

# initialise talisman
talisman = Talisman(app, content_security_policy=csp)

# HOME PAGE VIEW
@app.route('/')
def index():
    return render_template('main/index.html')

# Redirect page for error 400
@app.errorhandler(400)
def internal_error_400(error):
    return render_template('errors/400.html'), 400

# Redirect page for error 403
@app.errorhandler(403)
def internal_error_403(error):
    logger.warning('SECURITY - Invalid Access Attempt [%s, %s, %s, %s]',
                   current_user.id,
                   current_user.email,
                   current_user.role,
                   request.remote_addr)
    return render_template('errors/403.html'), 403


# Redirect page for error 404
@app.errorhandler(404)
def internal_error_404(error):
    return render_template('errors/404.html'), 404


# Redirect page for error 500
@app.errorhandler(500)
def internal_error_500(error):
    return render_template('errors/500.html'), 500


# Redirect page for error 503
@app.errorhandler(503)
def internal_error_503(error):
    return render_template('errors/503.html'), 503


# BLUEPRINTS
# import blueprints
from users.views import users_blueprint
from admin.views import admin_blueprint
from lottery.views import lottery_blueprint
# register blueprints with app
app.register_blueprint(users_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(lottery_blueprint)


# error blueprints
app.register_error_handler(400, internal_error_400)
app.register_error_handler(403, internal_error_403)
app.register_error_handler(404, internal_error_404)
app.register_error_handler(500, internal_error_500)
app.register_error_handler(503, internal_error_503)


from models import User

# initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.init_app(app)

# login manager loads current user id
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# Run app
if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))
