#-*- coding: utf-8 -*-

from datetime import datetime
import json

import logging

from line_api import LineAPI
from spreadsheet import SpreadSheet

class Webhook():

  def __init__(self):
    self.line_api = LineAPI()
    self.spreadsheet = SpreadSheet()

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
      now = datetime.now()
      sheet_title = '{}年{}月'.format(now.year, now.month)
      sheet_id = self.spreadsheet.get_sheet_id(title=sheet_title)
      if sheet_id < 0:
        self.spreadsheet.copy_sheet_from_template(title=sheet_title)

      if message == '削除' or message == '消して':
        removed_row = self.spreadsheet.remove_last_row()
        if len(removed_row) > 5 and removed_row[2] and removed_row[3] and removed_row[4]:
          return_msg = '{} が {} に {} 円払った記録を消しました'.format(removed_row[2], removed_row[3], removed_row[4])
        elif len(removed_row) > 6 and removed_row[5]:
          return_msg = '備考: {} の記録を消しました'.format(removed_row[5])
        else:
          return_msg = '{} の記録を消しました'.format(removed_row)
      else:
        return_msg = self.spreadsheet.append(display_name, message)

      self.line_api.send_replay(line_event, return_msg)

    else:
      # テキストメッセージ以外は無視
      logging.info('ignored non text message')
      logging.info('  `-- event type: {}'.format(line_event['type']))
      if line_event['type'] == 'message':
        logging.info('  `-- message type: {}'.format(line_event['message']['type']))
