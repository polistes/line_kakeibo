#-*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone

def get_current_time():
  JST = timezone(timedelta(hours=+9), 'JST')
  return datetime.now(JST)
