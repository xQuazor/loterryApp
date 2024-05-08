from datetime import datetime

import bcrypt
from flask_login import UserMixin
from app import db, app
from cryptography.fernet import Fernet
import pyotp


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information.
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    # User information
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='user')
    registered_on = db.Column(db.DateTime, nullable=False)
    current_login = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)

    # Define the relationship to Draw
    draws = db.relationship('Draw')

    # Post-key used for encryption
    postkey = db.Column(db.BLOB)
    # PIN-key used for encryption
    pinkey = db.Column(db.String(100), nullable=False)

    def __init__(self, email, firstname, lastname, phone, password, role):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.phone = phone
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role
        self.postkey = Fernet.generate_key()
        self.pinkey = pyotp.random_base32()
        self.registered_on = datetime.now()
        self.current_login = None
        self.last_login = None


class Draw(db.Model):
    __tablename__ = 'draws'

    id = db.Column(db.Integer, primary_key=True)

    # ID of user who submitted draw
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # 6 draw numbers submitted
    numbers = db.Column(db.String(100), nullable=False)

    # Draw has already been played (can only play draw once)
    been_played = db.Column(db.BOOLEAN, nullable=False, default=False)

    # Draw matches with master draw created by admin (True = draw is a winner)
    matches_master = db.Column(db.BOOLEAN, nullable=False, default=False)

    # True = draw is master draw created by admin. User draws are matched to master draw
    master_draw = db.Column(db.BOOLEAN, nullable=False)

    # Lottery round that draw is used
    lottery_round = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id, numbers, master_draw, lottery_round, postkey):
        self.user_id = user_id
        self.numbers = encrypt(numbers, postkey)
        self.been_played = False
        self.matches_master = False
        self.master_draw = master_draw
        self.lottery_round = lottery_round
        self.postkey = postkey

    def view_draw(self, postkey):
        self.numbers = decrypt(self.numbers, postkey)

# function to initialize db for 1 admin account
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(email='admin@email.com',
                     password='Admin1!',
                     firstname='Alice',
                     lastname='Jones',
                     phone='0191-123-4567',
                     role='admin')

        db.session.add(admin)
        db.session.commit()


# data encryption function
def encrypt(data, postkey):
    return Fernet(postkey).encrypt(bytes(data, 'utf-8'))


# data decryption function
def decrypt(data, postkey):
    return Fernet(postkey).decrypt(data).decode('utf-8')
