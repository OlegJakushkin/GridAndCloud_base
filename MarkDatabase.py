import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin, UserManager
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
photos = None


class Image(db.Model):
    id = db.Column(db.Integer(), primary_key=1)
    image = db.Column(db.String(256))
    updated_at = db.Column('updated_at', db.DateTime, default=datetime.now, onupdate=datetime.now)
    height = db.Column(db.Integer, nullable=False, default=0)
    width = db.Column(db.Integer, nullable=False, default=0)

class User(db.Model, UserMixin):
    active = True
    confirmed_at = datetime.utcnow()
    id = db.Column(db.Integer, primary_key=True)
    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    _password = db.Column(db.String(255), nullable=False, default='')

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, in_password):
        self._password = generate_password_hash(in_password, method='SHA256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

user_manager = ''

def CreateWallDatabase(app):
    global user_manager
    db.init_app(app)
    db.create_all()
    user_manager = UserManager(app, db, User)

    # Create 'admin' and 'user'
    if not User.query.filter(User.email == 'admin@example.com').first():
        passwd = os.getenv('ADMIN_PASSWORD', 'got')

        user_admin = User(email='admin@example.com', username='admin', \
                          password=passwd)
        user_admin.roles.append(Role(name='admin'))
        user_admin.roles.append(Role(name='uploader'))
        db.session.add(user_admin)

        db.session.commit()

    return db
