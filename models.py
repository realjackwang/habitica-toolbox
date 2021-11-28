from extensions import db
from flask_login import UserMixin
from flask_babel import gettext as _


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    ROLES = ['user', 'developer', 'contributor', 'admin']
    LANGUAGES = {'en': 'English', 'zh': '中文'}
    id = db.Column(db.String(255), primary_key=True)
    role = db.Column(db.String(32), default=ROLES[0])
    api_token = db.Column(db.String(255))
    username = db.Column(db.String(64))
    tags = db.relationship("Tag", backref="users")
    language = db.Column(db.String(32), default="zh")

    def __init__(self, id, api_key, username):
        super(User, self).__init__()
        self.id = id
        self.api_token = api_key
        self.username = username

    def __repr__(self):
        return "<User %s>" % self.username

    def get_language_display(self):
        return self.LANGUAGES[self.language]


task_tag = db.Table("task_tag",
                    # 定义两个外键，是两个多对多文章的主键
                    db.Column("task_id", db.String(255), db.ForeignKey("task.id"), primary_key=True),
                    db.Column("tag_id", db.String(255), db.ForeignKey("tag.id"), primary_key=True)
                    )


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.String(255), primary_key=True)
    tag_text = db.Column(db.String(255))
    tag_owner = db.Column(db.String(255), db.ForeignKey('user.id'))

    # tasks = db.relationship('Task', backref="tags", secondary=task_tag)

    def __repr__(self):
        return "<Tag %s>" % self.tag_text


class Task(db.Model):
    __tablename__ = 'task'
    PRIORITY_CHOICES = {'0.1': '琐事', '1.0': '简单', '1.5': '中等', '2.0': '困难'}

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    notes = db.Column(db.Text())
    priority = db.Column(db.String(255), default='1.0')
    days = db.Column(db.Integer, default=0)
    delay = db.Column(db.Integer, default=0)
    owner = db.Column(db.String(255), db.ForeignKey('user.id'))
    tags = db.relationship('Tag', backref="tasks", secondary=task_tag)

    def get_priority_display(self):
        return _(self.PRIORITY_CHOICES[self.priority])

    def __repr__(self):
        return "<Task %s>" % self.name


class Changelog(db.Model):
    __tablename__ = 'changelog'
    TYPES = {'feat': 'primary', 'fix': 'success', 'docs': '', 'style': 'dark', 'refactor': 'info', 'test': '',
             'chore': '', 'init': 'light', 'error': 'danger'}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    title = db.Column(db.String(255))
    type = db.Column(db.String(255))
    subject = db.Column(db.String(2048))

    def __repr__(self):
        return "<Changelog %s>" % self.title


class Notice(db.Model):
    __tablename__ = 'notice'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    content = db.Column(db.String(255))
    expired = db.Column(db.Boolean())
    expire_time = db.Column(db.String(255))

    def __repr__(self):
        return "<Notice %s>" % self.content
