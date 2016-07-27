"""Old django celery integration project."""
# :copyright: (c) 2009 - 2015 by Ask Solem.
# :license:   BSD, see LICENSE for more details.
from __future__ import absolute_import, unicode_literals

import os
import sys

VERSION = (3, 2, 0, 'a1')
__version__ = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])
__author__ = 'Ask Solem'
__contact__ = 'ask@celeryproject.org'
__homepage__ = 'http://celeryproject.org'
__docformat__ = 'restructuredtext'
__license__ = 'BSD (3 clause)'

# -eof meta-


if sys.version_info[0] == 3:

    def setup_loader():
        os.environ.setdefault(
            'CELERY_LOADER', 'djcelery.loaders.DjangoLoader',
        )

else:

    def setup_loader():  # noqa
        os.environ.setdefault(
            b'CELERY_LOADER', b'djcelery.loaders.DjangoLoader',
        )

from celery.app.task import Context
from celery.signals import before_task_publish
from django.conf import settings
from django.utils.timezone import now
from celery.states import PENDING
from celery import current_app as celery  # noqa


if getattr(settings, 'CELERY_TRACK_PUBLISH', False):
    @before_task_publish.connect
    def update_sent_state(sender=None, body=None, exchange=None,
                          routing_key=None, **kwargs):
        if not getattr(settings, 'CELERY_TRACK_PUBLISH', False):
            # Check again to support dynamic change of this settings
            return
        task = celery.tasks.get(sender)
        if getattr(task, 'ignore_result', False) or getattr(
                settings, 'CELERY_IGNORE_RESULT', False):
            # Do not save this task result
            return

        backend = task.backend if task else celery.backend
        request = Context()
        request.update(**body)
        request.date_submitted = now()
        request.delivery_info = {
            "exchange": exchange,
            "routing_key": routing_key
        }
        backend.store_result(body["id"], None, PENDING, traceback=None,
                             request=request, body=body)
