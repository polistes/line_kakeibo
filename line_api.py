#-*- coding: utf-8 -*-

import json

import logging

import hmac
import hashlib
import base64

from google.appengine.api import urlfetch

class LineAPI():

  def __init__(self):
    with open('conf/line.json') as f:
      self.line_conf = json.load(f)

  def validate_segnature(self, request):
    # https://developers.line.biz/ja/docs/messaging-api/building-bot/#spy-anchor-e0e7507abac7b64bdaa502657638da62bab4190e
    ## Calculate message signature
    # https://stackoverflow.com/a/29161688
    hash = hmac.new(str(self.line_conf['channel_secret']), request.body,
                    hashlib.sha256).digest()
    calc_signature = base64.b64encode(hash)

    ## Compare with header
    header_signature = ''
    try:
      header_signature = request.headers['X-Line-Signature']
    except KeyError:
      raise Exception('X-Line-Signature is not set')

    if header_signature != calc_signature:
      raise Exception('Signatures do not match')

    return True

  def is_text_message(self, event):
    if event['type'] == 'message':
      if event['message']['type'] == 'text':
        return True
    return False

  def get_display_name(self, user_id):
    ## TODO: modify to get displayName
    ## https://developers.line.biz/ja/reference/messaging-api/#anchor-0190762129db8ef085b86fff02f55c97027211f2
    return user_id

  def send_replay(self, event, response_body):
    response = {}
    response['replyToken'] = event['replyToken']
    response['messages'] = []
    response_event = {'type': 'text',
                      'text': response_body}
    response['messages'].append(response_event)

    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + str(self.line_conf['access_token'])}
    payload = json.dumps(response, ensure_ascii=False, encoding='utf8')

    try:
      result = urlfetch.fetch(
                 url = url,
                 payload = payload,
                 method = urlfetch.POST,
                 headers = headers)
      if result.status_code == 200:
        logging.info('succeeded')
      else:
        logging.warning('unexpected status code: %s', result.status_code)
        logging.warning(' --> message: %s', result.content)
    except urlfetch.Error:
      logging.error('Caught exception fetching url')
