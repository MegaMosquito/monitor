#!/usr/bin/python3


import datetime


DEBUG = True
def debug(s):
  if DEBUG:
    print(s)


# Some utilities for dealing with time
class Util:

  TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

  # Class method to get an appropriately formatted string representing "now"
  @classmethod
  def now_str(cls):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return now_utc.strftime(Util.TIME_FORMAT)

  # Class method to get seconds since a specified datetime
  @classmethod
  def seconds_since(cls, t):
    then = datetime.datetime.strptime(t, Util.TIME_FORMAT)
    now = datetime.datetime.now()
    return (now - then).total_seconds()

  # Class method to compute the older of two dates
  @classmethod
  def older(cls, date0, date1):
    if not date0: return date1
    if not date1: return date0
    now = datetime.datetime.now()
    d0 = now - datetime.datetime.strptime(date0, Util.TIME_FORMAT)
    d1 = now - datetime.datetime.strptime(date1, Util.TIME_FORMAT)
    if d0.total_seconds() > d1.total_seconds():
      return date0
    else:
      return date1

  # Class method to compute the younger of two dates
  @classmethod
  def younger(cls, date0, date1):
    if not date0: return date1
    if not date1: return date0
    now = datetime.datetime.now()
    d0 = now - datetime.datetime.strptime(date0, Util.TIME_FORMAT)
    d1 = now - datetime.datetime.strptime(date1, Util.TIME_FORMAT)
    if d0.total_seconds() < d1.total_seconds():
      return date0
    else:
      return date1



