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

  def append(self, post_user, message):
    '''spreadsheetの一番下に新しいメッセージを追加する'''
    analyzed = self.analyzer.analyze_message(post_user, message)

    row_value = self.analyzer.convert_timed_row(
        utils.get_current_time(),
        analyzed)

    body = {'values': [row_value]}

    request = self.spreadsheet.values().append(
        spreadsheetId=self.spreadsheet_conf['id'],
        valueInputOption='USER_ENTERED',
        range='A1',
        body=body)
    result = self.retry_request(request)

    if analyzed['exp']:
      return u"解析失敗: %s" % message
    else:
      return u'%s が %s として %s 円払いました' % (analyzed['user'], analyzed['kind'], analyzed['price'])

  def retry_request(self, request, retry_count=3):
    '''spreadsheetを操作するrequestを実行する関数
    エラーが発生してもretry_countの回数だけ再実行してくれる'''
    for i in range(0, retry_count):
      try:
        return request.execute()
      except HttpError as e:
        logging.warning('error detected: HttpError')
        logging.warning('  `-- retry count: {}'.format(retry_count))
        if i == retry_count - 1:
          raise e
        else:
          traceback.print_exc()
      except ConnectionError as e:
        logging.warning('error detected: ConnectionError')
        logging.warning('  `-- retry count: {}'.format(retry_count))
        if i == retry_count - 1:
          raise e
        else:
          traceback.print_exc()
          self.create_spreadsheets()

  def get_this_month_report(self):
    '''今月の家計簿を額のレポートの文字列にして返す'''
    request = self.spreadsheet.values().get(spreadsheetId=self.spreadsheet_conf['id'], range='H8:I')
    response = self.retry_request(request)

    # 金額が0でない項目を抽出
    filtered_report = filter(lambda x: x[1]!='0', response['values'])
    # 金額順にフィルタ
    sorted_report = sorted(filtered_report, key=lambda x:x[1], reverse=True)
    # テキスト変換準備
    maped_report = list(map(lambda x:'{}: {}円'.format(x[0], x[1]), sorted_report))

    # 改行で結合して返す
    return '\n'.join(maped_report)

  def get_records(self):
    request = self.spreadsheet.values().get(spreadsheetId=self.spreadsheet_conf['id'], range='A1:F')
    response = self.retry_request(request)

    return response['values']

  def get_latest_record(self):
    '''最新の記録を取得する'''
    records = self.get_records()

    row_index = len(records)
    if row_index == 1:
      return null

    return records[-1]

  def remove_latest_record(self):
    '''一番新しい行を削除して、削除した行の情報を返却する関数'''
    records = self.get_records()

    row_index = len(records)
    if row_index == 1:
      return ['今月の記録がありません']

    latest_record = records[-1]

    target_range = 'A{}:F{}'.format(row_index, row_index)
    request = self.spreadsheet.values().clear(spreadsheetId=self.spreadsheet_conf['id'], range=target_range)
    response = self.retry_request(request)

    return latest_record

  def get_sheet_id(self, title):
    '''指定したタイトルのシートが存在するか確認する関数
    見つかったらsheetIdを返す。
    見つからなかったら-1を返す'''

    if not title:
      return -1

    request = self.spreadsheet.get(spreadsheetId=self.spreadsheet_conf['id'])
    response = self.retry_request(request)

    sheets = response['sheets']
    for sheet in sheets:
      if sheet['properties']['title'] == title:
        logging.info('sheet titled={} found'.format(title))
        return sheet['properties']['sheetId']
    logging.info('sheet titled={} not found'.format(title))
    return -1


  def copy_sheet_from_template(self, title):
    '''templateシートをコピーして、一番左に適当な名前で配置する関数'''

    template_sheet_id = self.get_sheet_id(title='template')
    if template_sheet_id < 0:
      logging.info('template not found')
      sys.exit(1)

    dest_body = {
      'destination_spreadsheet_id': self.spreadsheet_conf['id']
    }

    request = self.spreadsheet.sheets().copyTo(
            spreadsheetId = self.spreadsheet_conf['id'],
            sheetId = template_sheet_id,
            body = dest_body)
    response = self.retry_request(request)
    logging.info(response)

    # 見つかったtemplateシートを0番目にtitleで指定されたシート名で作成する
    copied_sheet_id = response['sheetId']
    requests = []
    requests.append({
      'updateSheetProperties': {
        'properties': {
          'sheetId': copied_sheet_id,
          'title': title,
          'index': 0
        },
        'fields': 'title,index'
      }
    })

    body = {
        'requests': requests
    }

    request = self.spreadsheet.batchUpdate(
        spreadsheetId = self.spreadsheet_conf['id'],
        body = body)
    response = self.retry_request(request)
    logging.info('copied template and create sheet titled={} in index=0'.format(title))
