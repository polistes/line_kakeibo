#-*- coding: utf-8 -*-

import json
import re

import logging

class MessageAnalyzer():

  def __init__(self):
    self.load_user_dict()

  def load_user_dict(self):
    with open('conf/user_dict.json') as f:
      raw_dict = json.load(f)

    self.user_dict = {}
    for name in raw_dict:
      self.user_dict[name] = name
      for alter in raw_dict[name]:
        self.user_dict[alter] = name

  def analyze_message(self, post_user, message):
    match = re.search(r'([0-9]{3,}(円)?)', message)
    if match and len(match.groups()) <= 2:
      if len(match.groups()) == 1:
        price = match.group(0)
      if len(match.groups()) == 2:
        price = match.group(0).replace(u'円', '')
    else:
      logging.info('price not found in "%s"' % message)
      return self.create_value(exp=message)

    message = re.sub(ur'[0-9]{3,}(円)?', u' ', message)
    message = re.sub(r' +', u' ', message)
    split_msg = message.split()

    if len(split_msg) == 1:
      # ex) 2000 食費
      return self.create_value(user=post_user, price=price, kind=split_msg[0])

    elif len(split_msg) == 2:
      written_user = self.get_user_name(split_msg[0])
      if written_user:
        # ex) 太郎 食費 2000
        return self.create_value(user=written_user, price=price, kind=split_msg[1])

      written_user = self.get_user_name(split_msg[1])
      if written_user:
        # ex) 食費 太郎 2000
        return self.create_value(user=written_user, price=price, kind=split_msg[0])
      else:
        logging.info('user name not found in "%s"' % message)
        return self.create_value(exp=message)
    else:
      logging.info('input data contains more than 3 words "%s"' % message)
      return self.create_value(exp=message)

  def create_value(self, user='', price='', kind='', exp=''):
      return {'user': user,
              'price': price,
              'kind': kind,
              'exp': exp}

  def get_user_name(self, user_name):
    if user_name in self.user_dict:
      return self.user_dict[user_name]
    else:
      logging.info('user_name(%s) not found in dict' % user_name)
      return None

  def print_result(self, values):
    for key in values:
      print '%s = %s' % (key, values[key])
    print '-----'

  def convert_timed_row(self, unixtime, analyzed_msg):
    return [unixtime,
            analyzed_msg['user'],
            analyzed_msg['price'],
            analyzed_msg['kind'],
            analyzed_msg['exp']]

if __name__ == '__main__':
  analyzer = MessageAnalyzer()
  analyzer.print_result(analyzer.analyze_message(u"花子", u"太郎 2000円 食費"))
  analyzer.print_result(analyzer.analyze_message(u"花子", u"太郎 2000 食費"))
  analyzer.print_result(analyzer.analyze_message(u"花子", u"2000円 食費 たろう"))
  analyzer.print_result(analyzer.analyze_message(u"花子", u"2000円 食費"))

