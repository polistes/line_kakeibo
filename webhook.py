#-*- coding: utf-8 -*-

from datetime import datetime
import json

import logging

from line_api import LineAPI
from spreadsheet import SpreadSheet
import utils

class Webhook():

  def __init__(self):
    self.line_api = LineAPI()
    self.spreadsheet = SpreadSheet()

  def daily_notice(self, request):
    # リクエストの検証
    # https://cloud.google.com/appengine/docs/standard/python3/scheduling-jobs-with-cron-yaml?hl=ja
    try:
      header_signature = request.headers['X-Appengine-Cron']
      if not header_signature:
        raise Exception('X-Appengine-Cron is set as False')
    except KeyError:
      raise Exception('X-Appengine-Cron is not set')

    latest_record = self.spreadsheet.get_latest_record()
    if utils.is_today(latest_record[0]):
      logging.info('There is today\'s record')
    else:
      self.line_api.push_message('今日の記録した？')

  def post(self, request):
    self.line_api.validate_segnature(request)

    msg = json.loads(request.get_data())
    line_event = msg['events'][0]

    if self.line_api.is_text_message(line_event):
      # テキストメッセージがやってきたので処理を継続
      display_name = self.line_api.get_display_name(line_event)
      message = line_event['message']['text']
      logging.info('text message received: user={}, message={}'.format(display_name, message))

      # 今月分のシートがあるかどうか判定し、なかったらtemplateからコピーする
      now = utils.get_current_time()
      sheet_title = '{}年{}月'.format(now.year, now.month)
      sheet_id = self.spreadsheet.get_sheet_id(title=sheet_title)
      if sheet_id < 0:
        self.spreadsheet.copy_sheet_from_template(title=sheet_title)

      if message == '削除' or message == '消して':
        removed_row = self.spreadsheet.remove_latest_record()
        return_msg = '以下の記録を消しました:\n{}'.format(removed_row)
      elif message == 'レポート':
        return_msg = self.spreadsheet.get_this_month_report()
      else:
        return_msg = self.spreadsheet.append(display_name, message)

      self.line_api.send_replay(line_event, return_msg)

    else:
      # テキストメッセージ以外は無視
      logging.info('ignored non text message')
      logging.info('  `-- event type: {}'.format(line_event['type']))
      if line_event['type'] == 'message':
        logging.info('  `-- message type: {}'.format(line_event['message']['type']))
