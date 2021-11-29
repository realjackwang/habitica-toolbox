import os

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_admin.helpers import is_safe_url
from flask_babel import gettext as _
from flask_login import login_user, login_required, current_user, logout_user
from pyotp import TOTP

from app_functions import scheduled_script
from app_functions.cipher_functions import encrypt_text, init_cipher_key
from app_functions.to_do_overs_data import ToDoOversData
from config import config
from decorators import permission_required, admin_required
from extensions import db, login_manager, admin, babel, bootstrap, migrate
from forms import Login, TasksModelForm
from models import User, Task, Tag, Changelog, Notice, Role, Guest
from views import MyView, MyAdminIndexView

app = Flask(__name__)

config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

db.app = app
db.init_app(app)
db.create_all()
babel.init_app(app)
login_manager.init_app(app)
login_manager.anonymous_user = Guest
migrate.init_app(app, db)
bootstrap.init_app(app)
admin.init_app(app, index_view=MyAdminIndexView(name='首页', template='admin/index.html'))
admin.add_view(MyView(User, db.session))
admin.add_view(MyView(Task, db.session))
admin.add_view(MyView(Changelog, db.session))
admin.add_view(MyView(Notice, db.session))
Role.init_role()
init_cipher_key()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    else:
        form = Login()
        return render_template('index.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        username = form.email.data
        password = form.password.data
        session_class = ToDoOversData()
        if '-' in username and len(username) == 32:
            user_id = username
            api_token = encrypt_text(password.encode('utf-8'))
            if session_class.login_api_key(user_id, api_token):
                next_url = request.args.get('next')
                if next_url and not is_safe_url(next_url):
                    return abort(400)
                user = User.query.get(session_class.hab_user_id)
                login_user(user)
                return redirect(next_url, url_for("dashboard"))
            else:
                flash(_('登录失败，请检查 User ID 或者 API token 是否错误'))
                return redirect(url_for("index"))
        elif '@' in username and '.' in username:
            if session_class.login(username, password):
                next_url = request.args.get('next')
                if next_url and not is_safe_url(next_url):
                    return abort(400)
                user = User.query.get(session_class.hab_user_id)
                if request.form.get('remember-me'):
                    login_user(user, remember=True)
                else:
                    login_user(user, remember=False)
                return redirect(next_url or url_for("dashboard"))
            else:
                flash(_('登录失败，请检查登录邮箱或者密码是否错误'))
                return redirect(url_for("index"))
        else:
            flash(_('登录失败，你输入的账号不符合邮箱或User ID的任何一种'))
            return redirect(url_for("index"))


@app.route('/dashboard', methods=['GET'])
@permission_required('BROWSE')
def dashboard():
    if current_user.is_authenticated:
        tasks = Task.query.filter(Task.owner == current_user.id).all()
        return render_template('dashboard.html', tasks=tasks)
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/create_task', methods=['GET', 'POST'])
@permission_required('CREATE')
def create_task():
    if current_user.is_authenticated:
        session_class = ToDoOversData()
        user_id = current_user.id
        api_token = current_user.api_token
        tags = session_class.get_user_tags(user_id, api_token)
        choices = [(tag['id'], tag['name']) for tag in tags]
        form = TasksModelForm()
        form.tags.choices = choices
        if request.method == 'GET':
            return render_template('create_task.html', form=form)
        elif request.method == 'POST':
            task = Task()
            if int(session_class.task_days) < 0:
                flash(_('警告：检测到非法请求！'), 'errors')
                return redirect(url_for('dashboard'))
            if form.validate_on_submit():
                task.name = form.name.data
                task.notes = form.notes.data
                task.days = form.days.data
                task.delay = form.delay.data
                task.priority = form.priority.data
                task.owner = user_id
                tags = form.tags.data
                task.tags = [Tag.query.get(tag) for tag in tags]
                if session_class.create_task(user_id, api_token, task.name, task.notes, task.days, task.priority,
                                             tags):
                    task.id = session_class.task_id
                    db.session.add(task)
                    db.session.commit()
                    return redirect(url_for('dashboard'))
                else:
                    flash('发生未知错误导致创建任务失败，请反馈')
                    return redirect(url_for('create_task'))
            else:
                return redirect(url_for('create_task'))
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/edit_task', methods=['GET', 'POST'])
@permission_required('CREATE')
def edit_task():
    if current_user.is_authenticated:
        session_class = ToDoOversData()
        user_id = current_user.id
        api_token = current_user.api_token
        tags = session_class.get_user_tags(user_id, api_token)
        choices = [(tag['id'], tag['name']) for tag in tags]
        form = TasksModelForm()
        form.tags.choices = choices
        task_id = request.args['id']
        task = Task.query.get(task_id)
        if not task or user_id != task.owner:
            flash(_('警告：你没有对他人任务进行修改的权限！多次尝试可能会被禁止登陆'), 'errors')
            return redirect(url_for('dashboard'))
        if request.method == 'GET':
            form.id = task_id
            form.name.data = task.name
            form.notes.data = task.notes
            form.days.data = task.days
            form.delay.data = task.delay
            form.priority.data = task.priority
            form.tags.default = task.tags
            return render_template('create_task.html', form=form)
        elif request.method == 'POST':
            if form.validate_on_submit():
                if int(session_class.task_days) < 0:
                    return redirect(url_for('edit_task'))
                task.name = form.name.data
                task.notes = form.notes.data
                task.days = form.days.data
                task.delay = form.delay.data
                task.priority = form.priority.data
                task.owner = user_id
                tags = form.tags.data
                task.tags = [Tag.query.get(tag) for tag in tags]
                if session_class.edit_task(user_id, api_token, task.id, task.name, task.notes, task.days, task.priority,
                                           tags):
                    db.session.commit()
                    return redirect(url_for('dashboard'))
                else:
                    flash(_('发生未知错误导致修改任务失败，请反馈'))
                    return redirect(url_for('edit_task'))
            else:
                return redirect(url_for('edit_task'))
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/delete_task', methods=['GET'])
@login_required
def delete_task():
    if current_user.is_authenticated:
        user_id = current_user.id
        task_id = request.args.get('id')
        task = Task.query.get(task_id)
        if not task or user_id != task.owner:
            flash(_('警告：你没有对他人任务进行修改的权限！多次尝试可能会被禁止登陆'))
            return redirect(url_for('dashboard'))
        else:
            db.session.delete(task)
            db.session.commit()
            return redirect(url_for('dashboard'))
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/about', methods=['GET'])
@login_required
def about():
    if current_user.is_authenticated:
        return render_template('about.html')
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/changelog', methods=['GET'])
@login_required
def changelog():
    if current_user.is_authenticated:
        changelogs = Changelog.query.all()
        changelogs.reverse()
        data = []
        for changelog in changelogs:
            changelog_title = changelog.title
            changelog_sub = []
            changelog_sub_type = changelog.type.split('|')
            changelog_sub_subject = changelog.subject.split('|')
            for i in range(len(changelog_sub_type)):
                changelog_sub.append(
                    [changelog_sub_type[i], changelog_sub_subject[i], Changelog.TYPES[changelog_sub_type[i]]])
            data.append([changelog_title, changelog_sub])
        return render_template('changelog.html', changelogs=data)
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/settings', methods=['GET'])
@login_required
def settings():
    if current_user.is_authenticated:
        return render_template('settings.html')
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/language', methods=['GET'])
@login_required
def language():
    if current_user.is_authenticated:
        locale = request.args.get('locale')
        current_user.language = locale
        db.session.commit()
        return redirect_back(url_for("language"))
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('成功登出')
    return redirect(url_for("index"))


@app.route('/scheduled', methods=['GET'])
@admin_required
def scheduled():
    if app.config['SCHEDULED_KEY']:
        if request.args.get('key') == app.config['SCHEDULED_KEY']:
            scheduled_script.run()
            return 'Success!'
    abort(401)


# @app.route('/database_migrate', methods=['GET'])
# def database_migrate():
#     if app.config['MIGRATE_KEY']:
#         if request.args.get('key') == app.config['MIGRATE_KEY']:
#             if request.args.get('totp') != TOTP(app.config['TOTP_SECRET']).now():
#                 import subprocess
#                 process = subprocess.Popen('flask db --help', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#                 process.wait()
#                 command_output = process.stdout.read().decode('utf-8')
#                 # os.remove(app.config['SQLALCHEMY_DATABASE_PATH'])
#                 # db.create_all()
#                 return command_output
#     abort(401)


# 函数功能，传入当前url 跳转回当前url的前一个url
def redirect_back(back_url, **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(back_url, **kwargs))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@babel.localeselector
def get_locale():
    if current_user.is_authenticated:
        return current_user.language
    else:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
