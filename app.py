from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import requests
from dotenv import load_dotenv

# Импортируем модели и формы
from models import db, User, Habit, Quote
from forms import RegistrationForm, LoginForm, HabitForm, ProfileForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///habits.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализация БД
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание таблиц
with app.app_context():
    db.create_all()


# Функция для получения мотивационной цитаты из API
def get_motivational_quote():
    try:
        # Используем бесплатное API цитат
        response = requests.get('https://zenquotes.io/api/today', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'text': data[0]['q'],
                    'author': data[0]['a']
                }
    except:
        pass

    # Цитата по умолчанию
    return {
        'text': 'Маленькие шаги каждый день приводят к большим результатам',
        'author': 'Мудрость'
    }


@app.context_processor
def inject_quote():
    """Добавляет цитату на все страницы"""
    # Получаем цитату из сессии или API
    if 'daily_quote' not in session or session.get('quote_date') != date.today().isoformat():
        quote = get_motivational_quote()
        session['daily_quote'] = quote
        session['quote_date'] = date.today().isoformat()

    return {'daily_quote': session.get('daily_quote', {})}


@app.route('/')
def index():
    """Главная страница"""
    if current_user.is_authenticated:
        habits = Habit.query.filter_by(user_id=current_user.id).all()
        today = date.today().isoformat()
        return render_template('index.html', habits=habits, today=today)
    return render_template('index.html', habits=[], today=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash(f'С возвращением, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(
        original_username=current_user.username,
        original_email=current_user.email
    )

    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data

            if form.avatar.data:
                file = form.avatar.data
                # Генерируем уникальное имя файла
                filename = secure_filename(
                    f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Удаляем старый аватар, если это не стандартный
                if current_user.avatar != 'default.png' and current_user.avatar:
                    old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                current_user.avatar = filename

            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {str(e)}', 'danger')

    return render_template('profile.html', form=form, user=current_user)


@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    form = HabitForm()
    if form.validate_on_submit():
        try:
            habit = Habit(
                user_id=current_user.id,
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else '',
                goal=form.goal.data,
                unit=form.unit.data.strip() if form.unit.data else 'раз'
            )
            db.session.add(habit)
            db.session.commit()
            flash(f'Привычка "{habit.name}" успешно добавлена!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении привычки: {str(e)}', 'danger')

    return render_template('add_habit.html', form=form)


@app.route('/edit_habit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    form = HabitForm()

    if form.validate_on_submit():
        try:
            habit.name = form.name.data.strip()
            habit.description = form.description.data.strip() if form.description.data else ''
            habit.goal = form.goal.data
            habit.unit = form.unit.data.strip() if form.unit.data else 'раз'
            db.session.commit()
            flash('Привычка успешно обновлена!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении привычки: {str(e)}', 'danger')

    elif request.method == 'GET':
        form.name.data = habit.name
        form.description.data = habit.description
        form.goal.data = habit.goal
        form.unit.data = habit.unit

    return render_template('edit_habit.html', form=form, habit=habit)


@app.route('/delete_habit/<int:habit_id>')
@login_required
def delete_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    try:
        habit_name = habit.name
        db.session.delete(habit)
        db.session.commit()
        flash(f'Привычка "{habit_name}" удалена', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    return redirect(url_for('index'))


@app.route('/complete/<int:habit_id>', methods=['POST'])
@login_required
def complete_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    try:
        today = date.today().isoformat()
        habit.add_progress(today, 1)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            today_progress = habit.get_today_progress()
            return jsonify({
                'success': True,
                'count': today_progress,
                'goal': habit.goal,
                'percentage': min(100, (today_progress / habit.goal * 100))
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return redirect(url_for('index'))


# REST API для привычек
@app.route('/api/habits', methods=['GET'])
@login_required
def api_get_habits():
    """API: Получить все привычки пользователя"""
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': h.id,
        'name': h.name,
        'description': h.description,
        'goal': h.goal,
        'unit': h.unit,
        'today_progress': h.get_today_progress(),
        'created_date': h.created_date.isoformat() if h.created_date else None
    } for h in habits])


@app.route('/api/habits/<int:habit_id>/progress', methods=['GET'])
@login_required
def api_get_progress(habit_id):
    """API: Получить прогресс привычки за неделю"""
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    stats = habit.get_weekly_stats()
    return jsonify({
        'habit': habit.name,
        'weekly_stats': stats,
        'total_completed': sum(1 for s in stats if s['completed'])
    })


@app.route('/stats/<int:habit_id>')
@login_required
def habit_stats(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    stats = habit.get_weekly_stats()
    return render_template('stats.html', habit=habit, stats=stats)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)