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

# from pympler.tracker import SummaryTracker

class SpreadSheet():
  def __init__(self):
    # self.tracker = SummaryTracker()
    # print("before initialize")
    # self.tracker.print_diff()

    with open('conf/spreadsheet.json') as f:
      self.conf = json.load(f)

    # print("after read spreadsheet.json")
    # self.tracker.print_diff()

    self.credential_file = 'conf/key.json'

    with open('conf/spreadsheet.json') as f:
      self.spreadsheet_conf = json.load(f)
      self.spreadsheet = self.create_spreadsheets()

    # print("after create spreadsheet service")
    # self.tracker.print_diff()

    self.analyzer = MessageAnalyzer()

    # print("after initialized")
    # self.tracker.print_diff()

  def create_spreadsheets(self):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_file(
        self.credential_file,
        scopes=scope,
    )

    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

  def append(self, post_user, message):
    # print("append called")
    # self.tracker.print_diff()

    analyzed = self.analyzer.analyze_message(post_user, message)

    row_value = self.analyzer.convert_timed_row(
        utils.get_current_time(),
        analyzed)

    # print("analyzed")
    # self.tracker.print_diff()

    body = {'values': [row_value]}

    try:
      result = self.spreadsheet.values().append(spreadsheetId=self.spreadsheet_conf['id'],
                                     valueInputOption='RAW',
                                     range='A1',
                                     body=body).execute()
    except HttpError as e:
      logging.info(e._get_reason())
      traceback.print_exc()
      sys.exit(1)

    if analyzed['exp']:
      return u"解析失敗: %s" % message
    else:
      return u'%s が %s として %s 円払いました' % (analyzed['user'], analyzed['kind'], analyzed['price'])

    # print("finished")
    # self.tracker.print_diff()
