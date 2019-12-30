#-*- coding: utf-8 -*-

# import webapp2

import json

import logging

from line_api import LineAPI
from spreadsheet import SpreadSheet

# from pympler.tracker import SummaryTracker

class Webhook():

  def __init__(self):
    # self.tracker = SummaryTracker()
    # logging.info("before webhook initialize")
    # self.tracker.print_diff()

    self.line_api = LineAPI()
    self.spreadsheet = SpreadSheet()

    # logging.info("after webhook initialize")
    # self.tracker.print_diff()

  def post(self, request):

    # logging.info("post called")
    # self.tracker.print_diff()
    self.line_api.validate_segnature(request)

    # logging.info("validated")
    # self.tracker.print_diff()

    msg = json.loads(request.get_data())
    line_event = msg['events'][0]

    if self.line_api.is_text_message(line_event):
      display_name = self.line_api.get_display_name(line_event['source']['userId'])

      message = line_event['message']['text']
      logging.info("user: %s sent message: %s" % (display_name, message))

      return_msg = self.spreadsheet.append(display_name, message)

      # logging.info("after spreadsheet appended")
      # self.tracker.print_diff()

      self.line_api.send_replay(line_event, return_msg)

      # logging.info("after line replayed")
      # self.tracker.print_diff()
    else:
      logging.info("ignored non text message")
      logging.info("  `-- event type: %s" % line_event['type'])
      if line_event['type'] == 'message':
        logging.info("  `-- message type: %s" % line_event['message']['type'])

# app = webapp2.WSGIApplication(
#         [('/webhook', MyWebhook)]
#       )