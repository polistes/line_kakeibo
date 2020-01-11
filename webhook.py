#-*- coding: utf-8 -*-

import json

import logging

from line_api import LineAPI
from spreadsheet import SpreadSheet

class Webhook():

  def __init__(self):
    self.line_api = LineAPI()
    self.logger = logging.getLogger('flask.app')
    self.spreadsheet = SpreadSheet()

  def post(self, request):
    self.line_api.validate_segnature(request)

    msg = json.loads(request.get_data())
    line_event = msg['events'][0]

    if self.line_api.is_text_message(line_event):
      display_name = self.line_api.get_display_name(line_event)

      message = line_event['message']['text']
      self.logger.info("user: %s sent message: %s" % (display_name, message))

      return_msg = self.spreadsheet.append(display_name, message)

      self.line_api.send_replay(line_event, return_msg)

    else:
      self.logger.info("ignored non text message")
      self.logger.info("  `-- event type: %s" % line_event['type'])
      if line_event['type'] == 'message':
        self.logger.info("  `-- message type: %s" % line_event['message']['type'])
