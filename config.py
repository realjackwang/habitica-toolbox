import os


class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY')  # 填写SECRET_KEY
    SCHEDULED_KEY = os.getenv('SCHEDULED_KEY')  # 应用的重复任务是通过外部云函数定时调用API来实现的，需要SCHEDULED_KEY来鉴权
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID', None)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_PATH = ''
    SQLALCHEMY_DATABASE_URI = ''
    CIPHER_FILE = ''
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'
    LANGUAGES = {
        'en': 'English',
        'zh': '中文'
    }
    JOBS = [
        {
            'id': 'job1',
            'func': 'utils.scheduled_script:run_task',
            'trigger': 'cron',
            'day_of_week': '0-6',
            'hour': 0,
            'minute': 0
        },
    ]


class DevelopmentConfig(BaseConfig):
    # 项目开发阶段的配置
    SQLALCHEMY_DATABASE_PATH = 'data.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    CIPHER_FILE = 'utils/cipher.bin'


class TestingConfig(DevelopmentConfig):
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_PATH = ':memory:'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH


class ProductionConfig(BaseConfig):
    # 项目正式部署的配置
    SQLALCHEMY_DATABASE_PATH = '/mnt/data.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    CIPHER_FILE = '/mnt/cipher.bin'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
