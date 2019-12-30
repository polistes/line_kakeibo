#-*- coding: utf-8 -*-

import json

import logging

import hmac
import hashlib
import base64
import requests

class LineAPI():

  def __init__(self):
    with open('conf/line.json') as f:
      self.line_conf = json.load(f)
      self.logger = logging.getLogger('flask.app')
      self.id2name = {}

  def validate_segnature(self, request):
    # https://developers.line.biz/ja/docs/messaging-api/building-bot/#spy-anchor-e0e7507abac7b64bdaa502657638da62bab4190e
    ## Calculate message signature
    # https://stackoverflow.com/a/29161688
    hash = hmac.new(bytearray(self.line_conf['channel_secret'], 'utf-8'), request.get_data(),
                    hashlib.sha256).digest()
    calc_signature = base64.b64encode(hash).decode('utf-8')

    ## Compare with header
    header_signature = ''
    try:
      header_signature = request.headers['X-Line-Signature']
    except KeyError:
      raise Exception('X-Line-Signature is not set')

    if header_signature != calc_signature:
      self.logger.error('signatures not match: header={} calculated={}'.format(header_signature, calc_signature))
      # raise Exception('Signatures do not match')
      return False

    return True

  def is_text_message(self, event):
    if event['type'] == 'message':
      if event['message']['type'] == 'text':
        return True
    return False

  def get_display_name(self, user_id):
    # https://developers.line.biz/ja/reference/messaging-api/#anchor-0190762129db8ef085b86fff02f55c97027211f2
    if user_id in self.id2name:
      return self.id2name[user_id]
    else:
      url = 'https://api.line.me/v2/bot/profile/{}'.format(user_id)
      headers = {'Authorization': 'Bearer {}'.format(self.line_conf['access_token'])}
      result = requests.get(url, headers = headers)
      profile = json.loads(result.text)
      self.id2name[user_id] = profile['displayName']
      if result.status_code == 200:
        self.logger.info('successfully get user profile {} -> {}'.format(user_id, profile['displayName']))
        return profile['displayName']
      else:
        self.logger.warning('failed to get user profile of {} with status code: {}'.format(user_id, result.status_code))
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
               'Authorization': 'Bearer {}'.format(self.line_conf['access_token'])}
    payload = json.dumps(response, ensure_ascii=False)

    result = requests.post(
                url,
                data = payload.encode('utf-8'),
                headers = headers)
    if result.status_code == 200:
      self.logger.info('succeeded')
    else:
      self.logger.warning('unexpected status code: %s', result.status_code)
      self.logger.warning(' --> message: %s', result.text)
