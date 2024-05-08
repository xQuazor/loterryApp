from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

# check whether submitted form has any banned characters
def character_check(form, field):
    excluded_chars = '* ? ! \' ^ + % & / ( ) = } ] [ { $ # @ < >'

    for char in field.data:
        if char in excluded_chars:
            raise ValidationError(f"Character {char} is not allowed")

# check whether password meets security criteria
def validate_password(self, data_field):

    p = re.compile("(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*\W)")

    if not p.match(data_field.data):
        raise ValidationError("Password must contain atleast 1 digit\n 1 uppercase character\n 1 lowercase character"
                              "\n and a special character")

# check whether phone number meets structure and length criteria
def validate_phone(self, data_field):

    p = re.compile("(?=[0-9]{4}-[0-9]{3}-[0-9]{4})")

    if not p.match(data_field.data):
        raise ValidationError("The phone number must be in XXXX-XXX-XXXX format (including the dashes)")

# check whether pin input is numerical
def validate_pin(self, data_field):

    p = re.compile("(?=.*\d)")

    if not p.match(data_field.data):
        raise ValidationError("The PIN should be made up of numbers only")

# flask registration form
class RegisterForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email("This is not an email!!!")])
    firstname = StringField(validators=[DataRequired(), character_check])
    lastname = StringField(validators=[DataRequired(), character_check])
    phone = StringField(validators=[DataRequired(), Length(min=13, max=13), validate_phone])
    password = PasswordField(validators=[DataRequired(), Length(min=6, max=12)])
    confirm_password = PasswordField(validators=[DataRequired(), validate_password,
                                                 EqualTo('password', message='Both password fields should be equal!')])
    submit = SubmitField()

# flask login form
class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    recaptcha = RecaptchaField()
    #pin = StringField(validators=[DataRequired(), validate_pin, Length(min=6, max=6)])
    submit = SubmitField()
