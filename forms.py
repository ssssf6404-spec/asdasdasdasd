from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно'),
        Length(min=3, max=80, message='Имя должно быть от 3 до 80 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email'),
        Length(max=120)
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message='Подтвердите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен')
    ])
    submit = SubmitField('Войти')


class HabitForm(FlaskForm):
    name = StringField('Название привычки', validators=[
        DataRequired(message='Название привычки обязательно'),
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        Optional(),
        Length(max=500, message='Описание не должно превышать 500 символов')
    ])
    goal = IntegerField('Цель (количество)', validators=[
        DataRequired(message='Укажите цель'),
        NumberRange(min=1, max=1000, message='Цель должна быть от 1 до 1000')
    ], default=1)
    unit = StringField('Единица измерения', validators=[
        Optional(),
        Length(max=50, message='Единица измерения не должна превышать 50 символов')
    ], default='раз')
    submit = SubmitField('Сохранить')


class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно'),
        Length(min=3, max=80, message='Имя должно быть от 3 до 80 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    avatar = FileField('Аватар', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения! Разрешены: JPG, PNG, GIF')
    ])
    submit = SubmitField('Обновить профиль')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже зарегистрирован')