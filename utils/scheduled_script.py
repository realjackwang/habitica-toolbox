"""Daily maintenance script - Habitica To Do Over tool

This script is run once a day to add repeats of tasks.
"""
from __future__ import print_function

from builtins import str

__author__ = "Katie Patterson kirska.com"
__license__ = "MIT"

from datetime import datetime
import time
import pytz
import requests

from models import Task, User
from utils.cipher_functions import decrypt_text
from utils.to_do_overs_data import ToDoOversData
from extensions import db


def check_recreate_task(tdo_data, req, task):
    req_json = req.json()
    if req_json['data']['completed'] and task.delay == 0:
        # Task was completed and there is no delay so recreate it

        # convert tags from their DB ID to the tag UUID
        tags = []
        for tag in task.tags:
            tags.append(tag.id)

        retry = True
        delay_seconds = 0
        while retry:
            try:
                user = User.query.get(task.owner)
                checklist = task.checklist.split('\n')
                if tdo_data.create_task(user, task, tags, checklist):
                    task.id = tdo_data.task_id
                    db.session.commit()
                    retry = False
                    delay_seconds = 0
                    print('task re-created successfully ' + task.id)
                else:
                    print('task creation failed ' + task.id)
                    if tdo_data.return_code == 429:
                        print('too many requests, sleeping')
                        retry = True
                        delay_seconds += 90
                        if delay_seconds > 500:
                            # stop trying
                            retry = False
                            delay_seconds = 0
                        else:
                            time.sleep(delay_seconds)
                    else:
                        print('unknown failure')
                        retry = False
                        delay_seconds = 0
            except AttributeError:
                print('attribute error, sleep and retry')
                retry = True
                delay_seconds += 90
                if delay_seconds > 500:
                    # stop trying
                    retry = False
                    delay_seconds = 0
                else:
                    time.sleep(delay_seconds)

    elif req_json['data']['completed']:
        # Task was completed but has a delay
        # Get completed date and set to UTC timezone
        completed_date_naive = datetime.strptime(
            req_json['data']['dateCompleted'], '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        utc_timezone = pytz.timezone("UTC")
        completed_date_aware = utc_timezone.localize(
            completed_date_naive
        )
        # Get current UTC time
        utc_now = pytz.utc.localize(datetime.utcnow())

        # Need to round the datetimes down to get rid of partial days
        completed_date_aware = completed_date_aware.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        utc_now = utc_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # TESTING - add days to current date
        # utc_now = utc_now + timedelta(days=2)

        elapsed_time = utc_now - completed_date_aware

        # The delay we want is 1 + delay value
        if elapsed_time.days > task.delay:
            # Task was completed and the delay has passed

            # convert tags from their DB ID to the tag UUID
            tags = []
            for tag in task.tags.all():
                tags.append(tag.tag_id)

            retry = True
            delay_seconds = 0

            while retry:
                user = User.query.get(task.owner)
                checklist = task.checklist.split('\n')
                if tdo_data.create_task(user, task, tags, checklist):
                    task.id = tdo_data.task_id
                    db.session.commit()
                    retry = False
                    delay_seconds = 0
                    print('task re-created successfully ' + task.id)
                else:
                    print('task creation failed ' + task.id)
                    if tdo_data.return_code == 429:
                        print('too many requests, sleeping')
                        retry = True
                        delay_seconds += 90
                        if delay_seconds > 500:
                            # stop trying
                            retry = False
                            delay_seconds = 0
                        else:
                            time.sleep(delay_seconds)
                    else:
                        print('unknown failure')
                        retry = False
                        delay_seconds = 0
        else:
            print('task completed but delay not met ' + task.id)

    else:
        print(
            'task not completed ' + task.id
        )


def run_task():
    TASKS = Task.query.all()
    user_tags_fetched = []

    for task_ in TASKS:
        tdo_data = ToDoOversData()

        too_many_requests_delay = True
        current_delay = 0

        # update user's tags
        if task_.owner not in user_tags_fetched:
            user_tags_fetched.append(task_.owner)
            while too_many_requests_delay:
                tdo_data.hab_user_id = task_.owner
                tdo_data.api_token = User.query.get(task_.owner).api_token
                if not tdo_data.get_user_tags(tdo_data.hab_user_id, tdo_data.api_token):
                    if tdo_data.return_code == 429:
                        # too many requests
                        current_delay += 90
                        too_many_requests_delay = True
                        print("too many requests, sleeping")
                        if current_delay > 500:
                            # stop trying
                            too_many_requests_delay = False
                            current_delay = 0
                        else:
                            time.sleep(current_delay)
                    else:
                        too_many_requests_delay = False
                        current_delay = 0
                else:
                    too_many_requests_delay = False
                    current_delay = 0

            too_many_requests_delay = True
            current_delay = 0

        while too_many_requests_delay:
            url = 'https://habitica.com/api/v3/tasks/' + str(task_.id)
            headers = {
                'x-api-user': str(task_.owner),
                'x-api-key': decrypt_text(
                    tdo_data.api_token
                )
            }

            req_ = requests.get(url, headers=headers)

            if req_.status_code == 429:
                # too many requests
                current_delay += 90
                too_many_requests_delay = True
                print("too many requests, sleeping")
                if current_delay > 500:
                    # stop trying
                    too_many_requests_delay = False
                    current_delay = 0
                else:
                    time.sleep(current_delay)
            elif req_.status_code == 200:
                check_recreate_task(tdo_data, req_, task_)
                too_many_requests_delay = False
            elif req_.status_code == 404:
                print("deleting task " + task_.id)
                task = Task.query.get(task_.id)
                db.session.delete(task)
                db.session.commit()
                too_many_requests_delay = False
            else:
                print("weird return code")
                print(req_.status_code)
                too_many_requests_delay = False
