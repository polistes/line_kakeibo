#-*- coding: utf-8 -*-

import json
import logging
import sys
import traceback

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import utils
from message_analyzer import MessageAnalyzer

class SpreadSheet():
  def __init__(self):
    with open('conf/spreadsheet.json') as f:
      self.conf = json.load(f)

    self.credential_file = 'conf/key.json'

    with open('conf/spreadsheet.json') as f:
      self.spreadsheet_conf = json.load(f)
      self.spreadsheet = self.create_spreadsheets()

    self.analyzer = MessageAnalyzer()

  def create_spreadsheets(self):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_file(
        self.credential_file,
        scopes=scope,
    )

    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

  def append(self, post_user, message, retry_count=3):
    analyzed = self.analyzer.analyze_message(post_user, message)

    row_value = self.analyzer.convert_timed_row(
        utils.get_current_time(),
        analyzed)

    body = {'values': [row_value]}

    try:
      result = self.spreadsheet.values().append(spreadsheetId=self.spreadsheet_conf['id'],
                                     valueInputOption='RAW',
                                     range='A1',
                                     body=body).execute()
    except HttpError as e:
      logging.warning('error detected: HttpError')
      logging.warning('  `-- retry count: {}'.format(retry_count))
      if retry_count > 0:
        traceback.print_exc()
        retry_count = retry_count - 1
        self.append(post_user, message, retry_count=retry_count)
      else:
        raise e
    except ConnectionError as e:
      logging.warning('error detected: ConnectionError')
      logging.warning('  `-- retry count: {}'.format(retry_count))
      if retry_count > 0:
        self.create_spreadsheets()
        retry_count = retry_count - 1
        self.append(post_user, message, retry_count=retry_count)
      else:
        traceback.print_exc()
        raise e

    if analyzed['exp']:
      return u"解析失敗: %s" % message
    else:
      return u'%s が %s として %s 円払いました' % (analyzed['user'], analyzed['kind'], analyzed['price'])
