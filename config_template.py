class DevConfig(object):
    # 项目开发阶段的配置
    DEBUG = True
    TESTING = True
    SECRET_KEY = ''  # 填写SECRET_KEY
    SQLALCHEMY_DATABASE_PATH = 'habitica.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SCHEDULED_KEY = ''  # 应用的重复任务是通过外部云函数定时调用API来实现的，需要SCHEDULED_KEY来鉴权
    ADMIN_KEY = ''  # 应用中有些需要ADMIN_KEY才能运行的函数，如设定用户角色，删除数据库
    CIPHER_FILE = './app_functions/cipher.bin'
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    LANGUAGES = {
        'en': 'English',
        'zh': '中文'
    }


class ProdConfig(object):
    # 项目正式部署的配置
    SECRET_KEY = ''  # 填写SECRET_KEY
    SQLALCHEMY_DATABASE_PATH = '/mnt/habitica.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SCHEDULED_KEY = ''  # 应用的重复任务是通过外部云函数定时调用API来实现的，需要SCHEDULED_KEY来鉴权
    ADMIN_KEY = ''  # 应用中有些需要ADMIN_KEY才能运行的函数，如设定用户角色，删除数据库
    CIPHER_FILE = './app_functions/cipher.bin'
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    LANGUAGES = {
        'en': 'English',
        'zh': '中文'
    }
