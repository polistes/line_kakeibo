from flask import Flask, request

from webhook import Webhook
from spreadsheet import SpreadSheet

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
  ss.append('ももこ', 'ももこ 200 テスト')
  return 'OK', 200

@app.route('/')
def hello_world():
  return "Hello, World!"

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
