from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.fields import DateField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from flask_wtf.file import FileAllowed
import re

class RegistrationForm(FlaskForm):
    student_number = StringField('Student Number', validators=[
        DataRequired(),
        Length(min=8, max=8, message='Student number must be 8 digits')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    id_number = StringField('ID Number', validators=[
        DataRequired(),
        Length(min=13, max=13, message='ID number must be 13 digits')
    ])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message='Phone number must be 10 digits')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'JPG', 'PNG', 'JPEG', 'GIF', 'webp', 'WEBP'], 'Images only!')
    ])
    submit = SubmitField('Register')
    
    def validate_student_number(self, student_number):
        if not student_number.data.isdigit():
            raise ValidationError('Student number must contain only digits')
    
    def validate_id_number(self, id_number):
        if not id_number.data.isdigit():
            raise ValidationError('ID number must contain only digits')
    
    def validate_phone_number(self, phone_number):
        if not phone_number.data.isdigit():
            raise ValidationError('Phone number must contain only digits')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')

class AccommodationForm(FlaskForm):
    title = StringField('Accommodation Title', validators=[
        DataRequired(),
        Length(min=5, max=200)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10)
    ])
    room_type = SelectField('Room Type', choices=[
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('shared', 'Shared Room'),
        ('studio', 'Studio Apartment'),
        ('apartment', 'Full Apartment')
    ], validators=[DataRequired()])
    price_per_month = FloatField('Price per Month (ZAR)', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    location = StringField('Location', default='Sandton, Johannesburg', validators=[
        DataRequired()
    ])
    capacity = IntegerField('Capacity (Number of people)', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    current_occupancy = IntegerField('Current Occupancy', validators=[
        NumberRange(min=0)
    ], default=0)
    amenities = StringField('Amenities (comma-separated)')
    images = FileField('Accommodation Images', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'JPG', 'PNG', 'JPEG', 'GIF', 'webp', 'WEBP'], 'Images only!')
    ])
    submit = SubmitField('Add Accommodation')

class BookingForm(FlaskForm):
    duration = SelectField('Duration', choices=[
        ('annual', 'Annual (10 months)'),
        ('semester', 'Semester (5 months)')
    ], validators=[DataRequired()])
    period = SelectField('Period (if Semester)', choices=[
        ('', 'Select period'),
        ('SEM1', 'Semester 1'),
        ('SEM2', 'Semester 2')
    ])
    payment_responsible = SelectField('Payment Responsible', choices=[
        ('nsfas', 'NSFAS'),
        ('bursary', 'Bursary'),
        ('parent', 'Parent'),
        ('guardian', 'Guardian'),
        ('self', 'Self')
    ], validators=[DataRequired()])
    submit = SubmitField('Book Now')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[
        (5, '5 - Excellent'),
        (4, '4 - Very Good'),
        (3, '3 - Good'),
        (2, '2 - Fair'),
        (1, '1 - Poor')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    submit = SubmitField('Submit Review')

class SearchForm(FlaskForm):
    room_type = SelectField('Room Type', choices=[
        ('', 'All Types'),
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('shared', 'Shared Room'),
        ('studio', 'Studio Apartment'),
        ('apartment', 'Full Apartment')
    ])
    min_price = FloatField('Min Price')
    max_price = FloatField('Max Price')
    amenities = StringField('Amenities')
    submit = SubmitField('Search')