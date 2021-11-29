from flask import abort, redirect, url_for, flash
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from decorators import admin_required
from extensions import scheduler


class MyAdminIndexView(AdminIndexView):

    @expose('/')
    @admin_required
    def index(self):
        if not current_user.is_admin:
            abort(403)
        return super(MyAdminIndexView, self).index()

    @expose('/scheduled')
    @admin_required
    def scheduled(self):
        scheduler.run_job('job1')
        flash('执行成功')
        return redirect(url_for('admin.index'))


class MyView(ModelView):

    def is_accessible(self):
        return current_user.is_admin
