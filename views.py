from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash


class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('输入了错误的网址，或者你没有权限访问')
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class MyView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
