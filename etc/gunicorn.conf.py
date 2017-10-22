# coding: utf-8

import gevent.monkey
gevent.monkey.patch_all()
import multiprocessing

bind = 'unix:/var/run/wqx-museum.sock'
#bind = '127.0.0.1:8000'
max_requests = 10
keepalive = 5

#workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = 'gunicorn.workers.ggevent.GeventWorker'

loglevel = 'info'
errorlog = '-'

x_forwarded_for_header = 'X-FORWARDED-FOR'

secure_scheme_headers = {
    'X-SCHEME': 'https',
}
