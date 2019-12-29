#-*- coding: utf-8 -*-

from datetime import datetime
import time

def get_unixtime():
  now = datetime.now()
  return int(time.mktime(now.timetuple()))
