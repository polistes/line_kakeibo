#!/bin/bash

# https://cloud.google.com/appengine/docs/standard/python/tools/using-libraries-python-27?hl=ja 

if [ ! -d libs ]
then
  mkdir libs
else
  echo "libs directory already exists"
fi

pip install -t libs -r requirements.txt

