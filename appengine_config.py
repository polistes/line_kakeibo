#-*- coding: utf-8 -*-

# https://stackoverflow.com/questions/48792664/importerror-no-module-named-google-oauth2
# https://cloud.google.com/appengine/docs/standard/python/tools/using-libraries-python-27?hl=ja
# appengine_config.py
from google.appengine.ext import vendor

# Add any libraries install in the "libs" folder.
vendor.add('libs')
