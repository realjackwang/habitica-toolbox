# 引入Form基类
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
# 引入Form元素父类
from wtforms import StringField, PasswordField, SubmitField, widgets
from wtforms import TextAreaField, SelectMultipleField, SelectField, IntegerField
# 引入Form验证父类
from wtforms.validators import DataRequired, InputRequired, NumberRange


class Login(FlaskForm):
    email = StringField(_l('邮箱'), validators=[DataRequired(message=_l("邮箱或User ID不能为空"))],
                        render_kw={'placeholder': _l('邮箱 或 User ID')})
    password = PasswordField(_l('密码'), validators=[DataRequired(message=_l("密码或API Token不能为空"))],
                             render_kw={'placeholder': _l('密码 或 API Token')})
    submit = SubmitField(_l('提交'))


class MultiCheckboxField(SelectMultipleField):
    """多选Checkbox"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class TasksModelForm(FlaskForm):
    id = None
    user = None
    name = StringField(_l('*任务名称：'), validators=[DataRequired(message=u"任务名称不能为空")],
                       render_kw={'placeholder': _l('输入任务名称')})
    notes = TextAreaField(_l(u'备注：'), render_kw={'placeholder': _l(u'输入备注（可选，支持markdown语法）')})
    priority = SelectField(_l(u'难度：'), choices=[('0.1', _l('琐事')), ('1.0', _l('简单')), ('1.5', _l('中等')), ('2.0', _l('困难'))],
                           default='1.0')
    days = IntegerField(_l('分配完成任务的天数（输入 0 表示没有截止日期）：'), validators=[InputRequired(), NumberRange(min=0)], default=0)
    delay = IntegerField(_l('重新创建任务之前延迟的天数（输入 0 表示没有延迟）：'), validators=[InputRequired(), NumberRange(min=0)], default=0)
    checklist = TextAreaField(_l(u'子任务：'), render_kw={'placeholder': _l(u'输入子任务（可选，每一行为一个子任务）')})
    tags = MultiCheckboxField(_l('标签：'), choices=[], default=['0.1', '1.0'])
    submit = SubmitField(_l('提交'))
