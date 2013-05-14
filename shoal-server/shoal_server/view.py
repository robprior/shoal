import config
import math
import web
import re

from time import time
from __version__ import version
import utilities
import os

t_globals = dict(
  datestr=web.datestr,
  version=version,
  squid_active_time=config.squid_inactive_time,
  pid=os.getpid(),
)

render = web.template.render('templates/', cache=config.webpy_cache, globals=t_globals)
render._keywords['globals']['render'] = render

class index:
    def GET(self, size):
        return render.base(view_index(size))

class nearest:
    def GET(self, count):
        web.header('Content-Type', 'application/json')
        return view_nearest(count)

class wpad:
    def GET(self):
        web.header('Content-Type', 'application/x-ns-proxy-autoconfig')
        return view_wpad()

def view_index(size):
    params = web.input()
    page = int(params.page) if hasattr(params, 'page') else 1

    shoal_temp = utilities.get_shoal()
    shoal_list = []
    # shoal_temp is dictionary, this converts to an array
    for squid in shoal_temp:
        shoal_list.append(shoal_temp[squid])

    total = len(shoal_list)
    try:
        size = int(size)
    except (ValueError, TypeError):
        size = 20
    try:
        pages = int(math.ceil(total / float(size)))
    except ZeroDivisionError:
        return render.index(time(), total, shoal_list, 1, 1, 0)

    if page < 1:
        page = 1
    if page > pages:
        page = pages

    lower, upper = int(size * (page - 1)), int(size * page)
    return render.index(time(), total, shoal_list[lower:upper], page, pages, size)

def view_wpad(**k):
    return render.wpad(utilities.generate_wpad(web.ctx['ip']))

def view_nearest(count):
    return utilities.generate_nearest(web.ctx['ip'], count)
