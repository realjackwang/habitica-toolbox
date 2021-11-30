"""Application controller code - Habitica To Do Over tool

App controller functions for the Habitica To Do Over tool.
For functions that don't fit in the model or views.
"""
from __future__ import absolute_import

from builtins import object
from builtins import str

__author__ = "Katie Patterson kirska.com"
__license__ = "MIT"

from datetime import datetime, timedelta
import requests

from extensions import db
from models import User, Tag, Task
from .cipher_functions import encrypt_text, decrypt_text, CIPHER_FILE


class ToDoOversData(object):
    """Session data and application functions that don't fall in models or views.

    This class will be stored in a cookie for a login session.

    Attributes:
        username (str): Username from Habitica.
        hab_user_id (str): User ID from Habitica.
        api_token (str): API token from Habitica.
        logged_in (bool): Goes to true once user has successfully logged in.
        task_name (str): The name/title of the task being created.
        task_days (int): The number of days that a task should last
            before expiring for the task being created.
        task_id (str): The created task ID from Habitica.
        priority (str): Difficulty of the task being created.
            See models.py for choices.
        notes (str): The description/notes of the task being created.
        tags (list): The user's tags.
    """

    def __init__(self):
        self.username = ''
        self.hab_user_id = ''
        self.api_token = ''
        self.logged_in = False
        self.tags = []
        self.tasks = []
        self.task_name = ''
        self.task_days = 0
        self.task_delay = 0
        self.task_id = ''
        self.priority = ''
        self.notes = ''

        self.return_code = 0

    def login(self, username, password):
        """Login with a username and password to Habitica.

        Args:
            password: The password.

        Returns:
            True for success, False for failure.
            :param password:
            :param username:
        """
        req = requests.post(
            'https://habitica.com/api/v3/user/auth/local/login',
            data={'username': username, 'password': password}
        )
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()
            self.hab_user_id = req_json['data']['id']
            self.api_token = encrypt_text(
                req_json['data']['apiToken'].encode('utf-8')
            )
            self.username = req_json['data']['username']

            if User.query.get(self.hab_user_id) is not None:
                user = User.query.get(self.hab_user_id)
                user.api_token = self.api_token
                user.username = self.username
                db.session.commit()
            else:
                user = User(id=self.hab_user_id, api_token=self.api_token, username=self.username)
                db.session.add(user)
                db.session.commit()

            self.logged_in = True

            return True
        else:
            return False

    def login_api_key(self, user_id, api_token):
        """Login with user ID and API token to Habitica.

        Returns:
            True for success, False for failure.
        """
        headers = {
            'x-api-user': user_id,
            'x-api-key': decrypt_text(api_token),
            'Content-Type': 'application/json'
        }

        req = requests.get('https://habitica.com/api/v3/user', headers=headers)
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()
            self.username = req_json['data']['profile']['name']
            if User.query.get(user_id) is not None:
                user = User.query.get(user_id)
                user.api_token = api_token
                user.username = self.username
                db.session.commit()
            else:
                user = User(id=user_id, api_token=api_token, username=self.username)
                db.session.add(user)
                db.session.commit()
            self.logged_in = True
            return True
        return False

    def create_task(self, user, task, tags, checklist=None):
        """Create a task on Habitica.
        Returns:
            True for success, False for failure.
        """
        headers = {
            'x-api-user': user.id,
            'x-api-key': decrypt_text(
                user.api_token,
                CIPHER_FILE
            ).decode()
        }
        data = {
            'text': task.name,
            'type': 'todo',
            'notes': task.notes,
            'priority': task.priority,
            'tags': tags,
        }
        if int(task.days) > 0:
            due_date = datetime.now() + timedelta(days=int(task.days))
            due_date = due_date.isoformat()
            data['date'] = due_date
        req = requests.post(
            'https://habitica.com/api/v3/tasks/user',
            headers=headers,
            data=data
        )
        self.return_code = req.status_code
        if req.status_code == 201:
            req_json = req.json()
            self.task_id = req_json['data']['id']
            task.id = req_json['data']['id']
            if checklist:
                self.add_items_to_checklist(user, task, checklist)
            return True
        else:
            return False

    def edit_task(self, user, task, tags=None):
        """Edit a task on Habitica.

        Returns:
            True for success, False for failure.
        """
        headers = {'x-api-user': user.id,
                   'x-api-key': decrypt_text(user.api_token)}
        url = 'https://habitica.com/api/v3/tasks/' + task.id
        data = {
            'text': task.name,
            'notes': task.notes,
            'priority': task.priority,
            'tags': tags,
        }
        if int(task.days) > 0:
            due_date = datetime.now() + timedelta(days=int(task.days))
            due_date = due_date.isoformat()
            data['date'] = due_date
        req = requests.put(url, headers=headers, data=data)
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()
            self.task_id = req_json['data']['id']
            return True
        else:
            return False

    def add_items_to_checklist(self, user, task, items):
        headers = {
            'x-api-user': task.owner.encode('utf-8'),
            'x-api-key': decrypt_text(
                user.api_token,
                CIPHER_FILE,
            )
        }
        for item in items:
            req = requests.post(
                'https://habitica.com/api/v3/tasks/%s/checklist' % task.id,
                headers=headers,
                data={'text': item}
            )
            self.return_code = req.status_code
        if self.return_code == 200:
            return True
        else:
            return False

    def get_user_tags(self, user_id, api_token, cipher_file_path=CIPHER_FILE):
        """Get the list of a user's tags.

        Returns:
            Dict of tags for success, False for failure.
        """
        headers = {
            'x-api-user': user_id.encode('utf-8'),
            'x-api-key': decrypt_text(
                api_token,
                cipher_file_path,
            )
        }

        req = requests.get(
            'https://habitica.com/api/v3/tags',
            headers=headers,
            data={}
        )
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()

            user = User.query.get(user_id)

            current_tags = Tag.query.filter(Tag.tag_owner == user.id).all()
            current_tag_ids = []
            for tag in current_tags:
                current_tag_ids.append(tag.id)

            if req_json['data']:
                # Add/update tags in database
                for tag_json in req_json['data']:

                    if tag_json['id'] in current_tag_ids:
                        tag = Tag.query.get(tag_json['id'])
                        tag.tag_text = tag_json['name']
                        db.session.commit()
                    else:
                        tag = Tag(id=tag_json['id'], tag_text=tag_json['name'], tag_owner=user.id)
                        db.session.add(tag)
                        db.session.commit()

                    if tag_json['id'] in current_tag_ids:
                        current_tag_ids.remove(tag_json['id'])

                for leftover_tag in current_tag_ids:
                    print('deleting tag ' + leftover_tag)
                    tag = Tag.query.filter(Tag.id == leftover_tag).all()
                    db.session.delete(tag)
                    db.session.commit()

                return req_json['data']
            return False
        return False

    def load_user_tasks(self, user_id, api_token):
        """Get the list of a user's tasks.

        Returns:
            Dict of tags for success, False for failure.
        """
        headers = {
            'x-api-user': user_id.encode('utf-8'),
            'x-api-key': decrypt_text(
                api_token,
                CIPHER_FILE,
            )
        }

        req = requests.get(
            'https://habitica.com/api/v3/tasks/user?type=todos',
            headers=headers,
            data={}
        )
        self.return_code = req.status_code
        req_json = req.json()
        if self.return_code == 200:
            if req_json['data']:
                for task_json in req_json['data']:
                    task = Task.query.get(task_json['_id'])
                    tags = Tag.query.filter(Tag.id.in_(task_json['tags'])).all()
                    if task is None:
                        task = Task(
                            id=task_json['_id'],
                            name=task_json['text'],
                            notes=task_json['notes'],
                            tags=tags,
                            priority=str(task_json['priority']),
                            owner=task_json['userId'],
                            official=True
                        )
                        db.session.add(task)
                        db.session.commit()
                    elif task.official:
                        task.name = task_json['text']
                        task.notes = task_json['notes']
                        task.tags = tags
                        task.priority = str(task_json['priority'])
                        db.session.commit()
                return True
            else:
                return False
        else:
            return False
