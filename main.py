#-*- coding: utf-8 -*-

import webapp2

import json
import sys
import time
import traceback
from datetime import datetime

import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from line_api import LineAPI


class MyWebhook(webapp2.RequestHandler):

  def __init__(self, request, response):
    # https://stackoverflow.com/a/15624669
    # https://webapp2.readthedocs.io/en/latest/api/webapp2.html#request-handlers
    self.initialize(request, response)

    self.line_api = LineAPI()

  def append_spread_sheet(self, text):
    with open('conf/spreadsheet.json') as f:
      spreadsheet_conf = json.load(f)

    credential_file = 'conf/key.json'

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_file(
        credential_file,
        scopes=scope,
    )

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    now = datetime.now()
    unixtime = int(time.mktime(now.timetuple()))

    body = {'values': [[unixtime, text]]}

    try:
      result = sheet.values().append(spreadsheetId=spreadsheet_conf['id'],
                                     valueInputOption='RAW',
                                     range='A1',
                                     body=body).execute()
    except HttpError as e:
      print e._get_reason()
      traceback.print_exc()
      sys.exit(1)

    return result.get('updates')['updatedRange']


  def post(self):

    self.line_api.validate_segnature(self.request)

    msg = json.loads(self.request.body)
    line_event = msg['events'][0]

    if self.line_api.is_text_message(line_event):
      display_name = self.line_api.get_display_name(line_event['source']['userId'])

      message = line_event['message']['text']
      logging.info("user: %s sent message: %s" % (display_name, message))
      return_msg = self.append_spread_sheet(message)

      self.line_api.send_replay(line_event, return_msg)
    else:
      logging.info("ignored non text message")
      logging.info("  `-- event type: %s" % line_event['type'])
      if line_event['type'] == 'message':
        logging.info("  `-- message type: %s" % line_event['message']['type'])


app = webapp2.WSGIApplication(
        [('/webhook', MyWebhook)]
      )
