import os

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_admin.helpers import is_safe_url
from flask_babel import gettext as _
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import and_

from config import config
from decorators import permission_required, no_maintenance_required
from extensions import db, login_manager, admin, babel, bootstrap, migrate, scheduler
from forms import Login, TasksModelForm
from models import User, Task, Tag, Changelog, Notice, Role, Guest
from utils.cipher_functions import encrypt_text, init_cipher_key
from utils.scheduled_script import run_task
from utils.to_do_overs_data import ToDoOversData
from views import MyView, MyAdminIndexView

# from pyotp import TOTP

app = Flask(__name__)

config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

db.app = app
db.init_app(app)
db.create_all()
babel.init_app(app)
scheduler.init_app(app)
scheduler.start()
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
    if Notice.query.filter_by(type='maintenance', expired=False).first() is None:
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        else:
            form = Login()
            return render_template('index.html', form=form, maintenance=False)
    else:
        form = Login()
        flash(_('系统维护中'))
        return render_template('index.html', form=form, maintenance=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        username = form.email.data
        password = form.password.data
        tdo_data = ToDoOversData()
        if '-' in username and len(username) == 32:
            user_id = username
            api_token = encrypt_text(password.encode('utf-8'))
            if tdo_data.login_api_key(user_id, api_token):
                next_url = request.args.get('next')
                if next_url and not is_safe_url(next_url):
                    return abort(400)
                user = User.query.get(tdo_data.hab_user_id)
                login_user(user)
                return redirect(next_url, url_for("dashboard"))
            else:
                flash(_('登录失败，请检查 User ID 或者 API token 是否错误'))
                return redirect(url_for("index"))
        elif '@' in username and '.' in username:
            if tdo_data.login(username, password):
                next_url = request.args.get('next')
                if next_url and not is_safe_url(next_url):
                    return abort(400)
                user = User.query.get(tdo_data.hab_user_id)
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
@no_maintenance_required
def dashboard():
    if current_user.is_authenticated:
        tdo_data = ToDoOversData()
        tdo_data.load_user_tasks(current_user.id, current_user.api_token)
        toolbox_tasks = Task.query.filter(and_(Task.owner == current_user.id, Task.official == False)).all()
        habitica_tasks = Task.query.filter(and_(Task.owner == current_user.id, Task.official)).all()
        notices = Notice.query.filter_by(pages='dashboard', expired=False)
        return render_template('dashboard.html', tasks=[toolbox_tasks, habitica_tasks], notices=notices)
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/create_task', methods=['GET', 'POST'])
@permission_required('CREATE')
@no_maintenance_required
def create_task():
    if current_user.is_authenticated:
        tdo_data = ToDoOversData()
        user_id = current_user.id
        api_token = current_user.api_token
        tags = tdo_data.get_user_tags(user_id, api_token)
        choices = [(tag['id'], tag['name']) for tag in tags]
        form = TasksModelForm()
        form.tags.choices = choices
        if request.method == 'GET':
            return render_template('create_task.html', form=form)
        elif request.method == 'POST':
            if int(tdo_data.task_days) < 0:
                flash(_('警告：检测到非法请求！'), 'errors')
                return redirect(url_for('dashboard'))
            if form.validate_on_submit():
                task = Task()
                task.name = form.name.data
                task.notes = form.notes.data
                task.days = form.days.data
                task.delay = form.delay.data
                task.priority = form.priority.data
                task.owner = user_id
                tags = form.tags.data
                checklist = form.checklist.data.replace('\r', '').split('\n')
                checklist_len = len(checklist)
                for i in range(len(checklist)):
                    if not checklist[checklist_len - i - 1]:
                        checklist.pop(checklist_len - i - 1)
                if tdo_data.create_task(current_user, task, tags, checklist):
                    task.id = tdo_data.task_id
                    task.tags = Tag.query.filter(Tag.id.in_(
                        tags)).all()  # 放在task.id被赋值后，因为autoflush会在执行Query的时候将之前未提交的数据库变动给提交到数据库内存，此时id未赋值，会出错
                    task.checklist = form.checklist.data
                    db.session.add(task)
                    db.session.commit()
                    flash(_('任务创建成功'))
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
@no_maintenance_required
def edit_task():
    if current_user.is_authenticated:
        tdo_data = ToDoOversData()
        user_id = current_user.id
        api_token = current_user.api_token
        tags = tdo_data.get_user_tags(user_id, api_token)
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
            form.checklist.data = task.checklist
            form.checklist.label.text = _(u'子任务：（不会立即生效，只会修改下一次任务的子任务）')
            form.days.data = task.days
            form.delay.data = task.delay
            form.priority.data = task.priority
            form.tags.data = [tag.id for tag in task.tags]
            return render_template('create_task.html', form=form)
        elif request.method == 'POST':
            if form.validate_on_submit():
                if int(tdo_data.task_days) < 0:
                    return redirect(url_for('edit_task'))
                task.name = form.name.data
                task.notes = form.notes.data
                task.checklist = form.checklist.data
                task.days = form.days.data
                task.delay = form.delay.data
                task.priority = form.priority.data
                task.owner = user_id
                tags = form.tags.data
                task.tags = Tag.query.filter(Tag.id.in_(tags)).all()
                if tdo_data.edit_task(current_user, task, tags):
                    db.session.commit()
                    flash(_('任务修改成功'))
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
@no_maintenance_required
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
            flash(_('任务删除成功'))
            return redirect(url_for('dashboard'))
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/about', methods=['GET'])
@login_required
@no_maintenance_required
def about():
    if current_user.is_authenticated:
        notices = Notice.query.filter_by(pages='about', expired=False)
        return render_template('about.html', notices=notices)
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/changelog', methods=['GET'])
@login_required
@no_maintenance_required
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
        notices = Notice.query.filter_by(pages='changelog', expired=False)
        return render_template('changelog.html', changelogs=data, notices=notices)
    else:
        flash(_('登录过期，请重新登录'))
        return redirect(url_for("index"))


@app.route('/settings', methods=['GET'])
@login_required
@no_maintenance_required
def settings():
    if current_user.is_authenticated:
        notices = Notice.query.filter_by(pages='settings', expired=False)
        return render_template('settings.html', notices=notices)
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
def scheduled():
    if app.config['SCHEDULED_KEY']:
        if request.args.get('key') == app.config['SCHEDULED_KEY']:
            run_task()
            return 'Success!'
    abort(401)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def err_404_page(err):
    flash(str(err), 'error')
    return redirect(url_for("index"))


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
