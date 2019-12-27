#-*- coding: utf-8 -*-

import webapp2
import base64
import hashlib
import hmac

import json

import logging
from google.appengine.api import urlfetch


# for spread sheet

# https://stackoverflow.com/questions/14850853/how-to-include-third-party-python-libraries-in-google-app-engine
# import traceback
# import sys
# sys.path.insert(0, 'libs')

import traceback
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# timestamp
from datetime import datetime
import time


class MyWebhook(webapp2.RequestHandler):


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
    with open('conf/line.json') as f:
      line_conf = json.load(f)

    ## Calculate message signature
    # https://stackoverflow.com/a/29161688
    hash = hmac.new(str(line_conf['channel_secret']), str(self.request.body),
                    hashlib.sha256).digest()
    calc_signature = base64.b64encode(hash)

    ## Compare with header
    header_signature = ''
    try:
      header_signature = self.request.headers['X-Line-Signature']
    except KeyError:
      raise Exception('X-Line-Signature is not set')

    if header_signature != calc_signature:
      raise Exception('Signatures do not match')

    msg = json.loads(self.request.body)
    request_type = msg['events'][0]['type']
  
    if request_type == 'message':

      message = msg['events'][0]['message']
      ## TODO: modify to get displayName
      ## https://developers.line.biz/ja/reference/messaging-api/#anchor-0190762129db8ef085b86fff02f55c97027211f2
      send_user = msg['events'][0]['source']['userId']

      return_msg = u"ほげ"
      if message['type'] == 'text':
        logging.info("user: %s sent message: %s" % (send_user, message['text']))
        return_msg = self.append_spread_sheet(message['text'])

      reply_token = msg['events'][0]['replyToken']

      json_payload = {}
      json_payload['replyToken'] = reply_token
      json_payload['messages'] = []
      msg_body = {}
      msg_body['type'] = 'text'
      msg_body['text'] = return_msg
      json_payload['messages'].append(msg_body)

      url = 'https://api.line.me/v2/bot/message/reply'
      headers = {'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + str(line_conf['access_token'])}
      try:
        result = urlfetch.fetch(
                   url = url,
                   payload = json.dumps(json_payload, ensure_ascii=False, encoding='utf8'),
                   method = urlfetch.POST,
                   headers = headers)
        if result.status_code == 200:
          logging.info('succeeded')
        else:
          logging.warning('unexpected status code: %s', result.status_code)
          logging.warning(' --> message: %s', result.content)
      except urlfetch.Error:
        logging.warning('Caught exception fetching url')

app = webapp2.WSGIApplication(
        [('/webhook', MyWebhook)]
      )
