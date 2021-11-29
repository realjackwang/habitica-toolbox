from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user
from flask_babel import gettext as _
from models import Notice


def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(func):
    return permission_required('ADMINISTER')(func)


def no_maintenance_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if Notice.query.filter_by(type='maintenance', expired=False).first() is not None:
            return redirect(url_for("index"))
        return func(*args, **kwargs)

    return decorated_function
