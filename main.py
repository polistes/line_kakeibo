#-*- coding: utf-8 -*-

from flask import Flask, request

import google.cloud.logging

from webhook import Webhook
from spreadsheet import SpreadSheet

# ログ出力設定
# https://cloud.google.com/logging/docs/setup/python#connecting_the_library_to_python_logging
# https://qiita.com/yoko8ma/items/bfa108596d5025501705
client = google.cloud.logging.Client()
client.setup_logging()

app = Flask(__name__)
mywebhook = Webhook()

@app.route("/webhook", methods=['POST'])
def webhook():
  global mywebhook
  mywebhook.post(request)
  return 'OK', 200

@app.route("/spreadsheet")
def spreadsheet():
  ss = SpreadSheet()
  ss.append('だれか', 'だれか 200 テスト')
  return 'OK', 200

@app.route('/')
def hello_world():
  return "Hello, World!"

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
