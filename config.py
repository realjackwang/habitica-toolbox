import os


class DevConfig(object):
    # 项目开发阶段的配置
    DEBUG = True
    TESTING = True
    if os.path.exists('config.txt'):
        with open('config.txt') as f:  # 创建一个txt用于本地设置快捷的设置参数
            SECRET_KEY = f.readline().replace('\n', '')  # 填写SECRET_KEY
            SCHEDULED_KEY = f.readline().replace('\n', '')  # 应用的重复任务是通过外部云函数定时调用API来实现的，需要SCHEDULED_KEY来鉴权
            ADMIN_KEY = f.readline().replace('\n', '')  # 应用中有些需要ADMIN_KEY才能运行的函数，如设定用户角色，删除数据库
            TOTP_SECRET = f.readline().replace('\n', '')  # 二次验证，防止ADMIN_KEY泄露
    else:
        print('本地运行前，请先创建一个config.txt，并填写相应的KEY')
    SQLALCHEMY_DATABASE_PATH = 'habitica.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    CIPHER_FILE = './app_functions/cipher.bin'
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    LANGUAGES = {
        'en': 'English',
        'zh': '中文'
    }


class ProdConfig(object):
    # 项目正式部署的配置
    SECRET_KEY = os.getenv('SECRET_KEY') if 'SECRET_KEY' in os.environ else None
    SCHEDULED_KEY = os.getenv('SCHEDULED_KEY') if 'SCHEDULED_KEY' in os.environ else None
    ADMIN_KEY = os.getenv('ADMIN_KEY') if 'ADMIN_KEY' in os.environ else None
    TOTP_SECRET = os.getenv('TOTP_SECRET') if 'TOTP_SECRET' in os.environ else None
    SQLALCHEMY_DATABASE_PATH = '/mnt/habitica.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    CIPHER_FILE = '/mnt/cipher.bin'
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    LANGUAGES = {
        'en': 'English',
        'zh': '中文'
    }
