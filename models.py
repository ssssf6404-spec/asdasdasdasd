from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id)


class Habit(db.Model):
    __tablename__ = 'habits'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    goal = db.Column(db.Integer, default=1)
    unit = db.Column(db.String(50), default='раз')
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    progress_data = db.Column(db.Text, default='{}')

    def get_progress(self):
        """Возвращает прогресс как словарь"""
        try:
            return json.loads(self.progress_data) if self.progress_data else {}
        except:
            return {}

    def set_progress(self, progress_dict):
        """Сохраняет прогресс из словаря"""
        self.progress_data = json.dumps(progress_dict, ensure_ascii=False)

    def add_progress(self, date_str, count=1):
        """Добавляет прогресс за конкретную дату"""
        progress = self.get_progress()
        current = progress.get(date_str, 0)
        progress[date_str] = current + count
        self.set_progress(progress)
        db.session.commit()

    def get_today_progress(self):
        """Возвращает прогресс за сегодня"""
        today = date.today().isoformat()
        progress = self.get_progress()
        return progress.get(today, 0)

    def get_weekly_stats(self):
        """Возвращает статистику за неделю"""
        stats = []
        progress = self.get_progress()
        for i in range(7):
            day = date.fromordinal(date.today().toordinal() - i)
            day_str = day.isoformat()
            count = progress.get(day_str, 0)
            stats.append({
                'date': day.strftime('%d.%m'),
                'count': count,
                'goal': self.goal,
                'completed': count >= self.goal
            })
        return stats


class Quote(db.Model):
    """Модель для хранения цитат из API"""
    __tablename__ = 'quotes'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)