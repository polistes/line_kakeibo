#-*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone

def get_current_time():
  JST = timezone(timedelta(hours=+9), 'JST')
  return datetime.now(JST)

def is_today(date_str):
  now = get_current_time()
  current_date = datetime(now.year, now.month, now.day)
  record_date = datetime.strptime(date_str, '%Y/%m/%d')
  return record_date == current_date
