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
    return event['type'] == 'message' and event['message']['type'] == 'text'

  def get_display_name(self, line_event):
    # https://developers.line.biz/ja/reference/messaging-api/#anchor-0190762129db8ef085b86fff02f55c97027211f2
    #
    if 'source' not in line_event:
      self.logger.warning('key \'source\' not found in line_event: {}'.format(line_event))
      # TODO どうしよう
      return 'null'
    if 'userId' not in line_event['source'] or \
        'groupId' not in line_event['source']:
      self.logger.warning('key \'userId\' or \'groupId\' not found in source of line_event: {}'.format(line_event['source']))
      # TODO どうしよう
      return 'null'
    user_id = line_event['source']['userId']
    group_id = line_event['source']['groupId']

    self.logger.info('groupId: {}, userId: {}'.format(group_id, user_id))

    url = 'https://api.line.me/v2/bot/group/{}/member/{}'.format(group_id, user_id)
    headers = {'Authorization': 'Bearer {}'.format(self.line_conf['access_token'])}
    result = requests.get(url, headers = headers)
    profile = json.loads(result.text)
    if 'displayName' not in profile:
      self.logger.warning('key \'displayName\' not found in profile: {}'.format(result.text))
      return user_id

    self.id2name[user_id] = profile['displayName']
    if result.status_code == 200:
      self.logger.info('displayName found for userId: {} -> {}'.format(user_id, profile['displayName']))
      return profile['displayName']
    else:
      self.logger.warning('failed to get user profile of {} with status code: {}'.format(user_id, result.status_code))
      return user_id

  def post_request(self, url, data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(self.line_conf['access_token'])}

    result = requests.post(
                url,
                data = data,
                headers = headers)
    if result.status_code == 200:
      self.logger.info('succeeded')
    else:
      self.logger.warning('unexpected status code: %s', result.status_code)
      self.logger.warning(' --> message: %s', result.text)


  def send_replay(self, event, response_body):
    response = {}
    response['replyToken'] = event['replyToken']
    response['messages'] = []
    response_event = {'type': 'text',
                      'text': response_body}
    response['messages'].append(response_event)

    url = 'https://api.line.me/v2/bot/message/reply'
    payload = json.dumps(response, ensure_ascii=False)

    self.post_request(url, payload.encode('utf-8'))

  def push_message(self, msg_text):
    push_message = {
        'to': self.line_conf['group_id'],
        'messages': [
          {
            'type': 'text',
            'text': msg_text
          }
        ]
      }

    url = 'https://api.line.me/v2/bot/message/push'
    payload = json.dumps(push_message, ensure_ascii=False)
    self.post_request(url, payload.encode('utf-8'))
