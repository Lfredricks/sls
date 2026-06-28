from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class ListingForm(FlaskForm):
    name = StringField('Business Name', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Category', choices=[
        ('contractor', 'Contractor'),
        ('vendor', 'Vendor'),
    ], validators=[DataRequired()])
    work_type = StringField('Work Type', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), URL(), Length(max=200)])
    image = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only')
    ])
    submit = SubmitField('Save')
