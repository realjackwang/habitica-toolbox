from extensions import db
from flask_login import UserMixin, AnonymousUserMixin
from flask_babel import gettext as _
from flask import current_app


class User(UserMixin, db.Model):
    ROLES = ['user', 'developer', 'contributor', 'admin']
    LANGUAGES = {'en': 'English', 'zh': '中文'}
    id = db.Column(db.String(255), primary_key=True)
    api_token = db.Column(db.String(255))
    username = db.Column(db.String(64))
    tags = db.relationship("Tag", backref="users")
    language = db.Column(db.String(32), default="zh")
    active = db.Column(db.Boolean, default=True)
    locked = db.Column(db.Boolean, default=False)
    active_locked_msg = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()

    def __repr__(self):
        return "<User %s>" % self.username

    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

    def set_role(self):
        if self.role is None:
            if self.id == current_app.config['ADMIN_USER_ID']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()

    def get_language_display(self):
        return self.LANGUAGES[self.language]


class Guest(AnonymousUserMixin):
    @property
    def is_admin(self):
        return False

    def can(self, permission_name):
        return False


roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                             )


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    users = db.relationship('User', back_populates='role')
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles')

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked': ['BROWSE'],
            'User': ['BROWSE', 'CREATE'],
            'Administrator': ['BROWSE', 'CREATE', 'ADMINISTER']
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), unique=True)
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')


task_tag = db.Table("task_tag",
                    db.Column("task_id", db.String(255), db.ForeignKey("task.id"), primary_key=True),
                    db.Column("tag_id", db.String(255), db.ForeignKey("tag.id"), primary_key=True)
                    )


class Tag(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    tag_text = db.Column(db.String(255))
    tag_owner = db.Column(db.String(255), db.ForeignKey('user.id'))

    # tasks = db.relationship('Task', backref="tags", secondary=task_tag)

    def __repr__(self):
        return "<Tag %s>" % self.tag_text


class Task(db.Model):
    PRIORITY_CHOICES = {'0.1': '琐事', '1': '简单', '1.5': '中等', '2': '困难'}

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    notes = db.Column(db.Text())
    priority = db.Column(db.String(255), default='1.0')
    days = db.Column(db.Integer, default=0)
    delay = db.Column(db.Integer, default=0)
    owner = db.Column(db.String(255), db.ForeignKey('user.id'))
    tags = db.relationship('Tag', backref="tasks", secondary=task_tag)
    checklist = db.Column(db.Text())
    official = db.Column(db.Boolean, default=False)

    def get_priority_display(self):
        return _(self.PRIORITY_CHOICES[self.priority])

    def __repr__(self):
        return "<Task %s>" % self.name


class Changelog(db.Model):
    TYPES = {'feat': 'primary', 'fix': 'success', 'docs': '', 'style': 'dark', 'refactor': 'info', 'test': '',
             'chore': '', 'init': 'light', 'error': 'danger'}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    title = db.Column(db.String(255))
    type = db.Column(db.String(255))
    subject = db.Column(db.String(2048))

    def __repr__(self):
        return "<Changelog %s>" % self.title


class Notice(db.Model):
    TYPES = {'info': 'warning', 'maintenance': 'primary', 'error': 'danger'}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    content = db.Column(db.String(255))
    type = db.Column(db.String(32))
    pages = db.Column(db.String(32))
    expired = db.Column(db.Boolean())
    expire_time = db.Column(db.String(255))

    def __repr__(self):
        return "<Notice %s>" % self.content
