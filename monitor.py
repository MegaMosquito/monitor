#
# Simple Web UI for my Network Monitor
#
# Written by Glen Darling, November 2019.
#


import json
import os
import subprocess
import threading
import time


# Configure all of these "MY_" environment variables for your situation
MY_COUCHDB_ADDRESS        = os.environ['MY_COUCHDB_ADDRESS']
MY_COUCHDB_PORT           = int(os.environ['MY_COUCHDB_PORT'])
MY_COUCHDB_USER           = os.environ['MY_COUCHDB_USER']
MY_COUCHDB_PASSWORD       = os.environ['MY_COUCHDB_PASSWORD']
MY_COUCHDB_MACHINE_DB     = os.environ['MY_COUCHDB_MACHINE_DB']
MY_COUCHDB_TIME_FORMAT    = os.environ['MY_COUCHDB_TIME_FORMAT']


# Constants
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6666
CSS_FILE = '/site.css'
FAVICON_ICO = '/favicon.ico'
LOGO_PNG = '/logo.png'
YES_PNG = '/yes.png'
NO_PNG = '/no.png'


# Globals for the cached data
last_wan = "0"
last_rows = ""


# Get the Host and DB classes
from db import Host, DB

# Instantiate the db object (i.e., connect to CouchDB, and open our DB)
db = DB( \
  MY_COUCHDB_ADDRESS,
  MY_COUCHDB_PORT,
  MY_COUCHDB_USER,
  MY_COUCHDB_PASSWORD,
  MY_COUCHDB_MACHINE_DB,
  MY_COUCHDB_TIME_FORMAT)


if __name__ == '__main__':

  from io import BytesIO
  from flask import Flask
  from flask import send_file
  webapp = Flask('lanmon')                             
  webapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

  # Loop forever collecting from the couchdb (provided by netmon)
  class LanThread(threading.Thread):
    @classmethod
    def nice_time(cls, secs):
      secs = int(secs)
      out = str(secs) + ' sec'
      if (secs > 60):
        min = int(secs / 60)
        out = str(min) + ' min'
        if (min > 60):
          hr = int(min / 60)
          out = str(hr) + ' hr'
          if (hr > 24):
            day = int(hr / 24)
            if (1 == day):
              out = str(day) + ' day'
            else:
              out = str(day) + ' days'
      return out
    @classmethod
    def numeric_ip(cls, k):
      b = k.split('.')
      return int(b[0]) << 24 + \
             int(b[1]) << 16 + \
             int(b[2]) << 8 + \
             int(b[3])
    def run(self):
      m_ordinary = "machine-ordinary"
      m_static = "machine-static"
      m_unknown = "machine-unknown"
      m_missing = "machine-missing"
      global last_rows
      # print("\nLAN monitor thread started!")
      while True:
        ips = []
        rows = {}
        db_hosts = db.get_all()
        for host in db_hosts:
          h = db.get(host['key'])
          # print(json.dumps(h))
          ip = ""
          if ('ip' in h) and ('' != h['ip']):
            ip = h['ip']
          first = ""
          last = ""
          if ('last_seen' in h):
            last_seen = h['last_seen']
            last_seen_how_long_ago_seconds = db.seconds_since(last_seen)
            last = LanThread.nice_time(last_seen_how_long_ago_seconds)
            first_seen_how_long_ago_seconds = last_seen_how_long_ago_seconds
            if 'first_seen' in h:
              first_seen = h['first_seen']
              first_seen_how_long_ago_seconds = db.seconds_since(first_seen)
              first = LanThread.nice_time(first_seen_how_long_ago_seconds)
          mac = h['mac']
          info = h['info']
          # print("ip=" + str(ip))
          row_type = m_ordinary
          if (not h['known']):
            row_type = m_unknown
          elif (h['static']):
            row_type = m_static
          elif (h['known'] and h['infra']):
            row_type = m_static
          if (("" != ip)) or (h['infra'] and ("" == ip)):
            ip_key = "256.256.256.256." + mac
            if ("" != ip):
              ip_key = ip
            ips.append(ip_key)
            rows[ip_key] = \
              '     <tr class="' + row_type + '">\n' + \
              '       <td>' + str(first) + '</td>\n' + \
              '       <td>' + str(last) + '</td>\n' + \
              '       <td>' + str(ip) + '</td>\n' + \
              '       <td>' + str(mac) + '</td>\n' + \
              '       <td>' + str(info) + '</td>\n' + \
              '     </tr>\n' + \
              ''
        out = ""
        ip_keys = sorted(ips, key=lambda k: LanThread.numeric_ip(k))
        for ip_key in ip_keys:
          out += rows[ip_key]
        if ("" != out):
          last_rows = out
        # print(last_rows)
        # print("\nSleeping for " + str(5) + " seconds...\n")
        time.sleep(5)

  # Loop forever checking WAN connectivity
  class WanThread(threading.Thread):
    def run(self):
      global last_wan
      # print("\nWAN monitor thread started!")
      WAN_COMMAND = 'curl -sS https://google.com 2>/dev/null | wc -l'
      while True:
        yes_no = str(subprocess.check_output(WAN_COMMAND, shell=True)).strip()
        # print("\n\nWAN check = " + yes_no)
        last_wan = (yes_no != "0")
        # print(str(last_wan))
        # print("\nSleeping for " + str(5) + " seconds...\n")
        time.sleep(5)

  @webapp.route("/site.css")
  def get_css():
    return send_file(CSS_FILE)

  @webapp.route("/favicon.ico")
  def get_favicon_ico():
    return send_file(FAVICON_ICO)

  @webapp.route("/logo.png")
  def get_logo_png():
    return send_file(LOGO_PNG)

  @webapp.route("/yes.png")
  def get_yes_png():
    return send_file(YES_PNG)

  @webapp.route("/no.png")
  def get_no_png():
    return send_file(NO_PNG)

  @webapp.route("/")
  def get_page():

    wan = '     WAN: &nbsp;<img src="/no.png" class="monitor-wan" alt="no" />\n'
    if (last_wan):
      wan = '     WAN: &nbsp; <img src="/yes.png" class="monitor-wan" alt="yes" />\n'

    rows = last_rows

    OUT = \
      '<!DOCTYPE html>\n' + \
      '<html lang=en>\n' + \
      ' <head>\n' + \
      '   <title>DarlingEvil Network Monitor</title>\n' + \
      '   <meta charset="utf-8" />\n' + \
      '   <link rel="shortcut icon" href="/favicon.ico" />\n' + \
      '   <link rel="stylesheet" type="text/css" href="/site.css" />\n' + \
      '   <meta name="viewport" content="width=device-width, initial-scale=1" />\n' + \
      '   <meta name="theme-color" content="#000000" />\n' + \
      ' </head>\n' + \
      ' <body>\n' + \
      '   <header class="monitor-header">\n' + \
      '     &nbsp;&nbsp;\n' + \
      '     <img src="/logo.png" class="monitor-logo" alt="logo" />\n' + \
      '     <p class="monitor-p">\n' + \
      '       &nbsp;Network Monitor, from&nbsp;\n' + \
      '       <a\n' + \
      '         class="monitor-a"\n' + \
      '         href="https://darlingevil.com"\n' + \
      '         target="_blank"\n' + \
      '         rel="noopener noreferrer"\n' + \
      '       >\n' + \
      '         darlingevil.com\n' + \
      '       </a>\n' + \
      '       &nbsp;&nbsp; &nbsp;&nbsp; &nbsp;&nbsp; &nbsp;&nbsp; \n' + \
      '     </p>\n' + \
      wan + \
      '   </header>\n' + \
      '   <table class="monitor-table">\n' + \
      '     <tr>\n' + \
      '       <th>First</th>\n' + \
      '       <th>Last</th>\n' + \
      '       <th>IPv4</th>\n' + \
      '       <th>MAC</th>\n' + \
      '       <th>Info</th>\n' + \
      '     </tr>\n' + \
      rows + \
      '   </table>\n' + \
      ' </body>\n' + \
      '</html>\n'
    return (OUT)

  # Prevent caching everywhere
  @webapp.after_request
  def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

  # Main program (instantiates and starts polling thread and then web server)
  lanmon = LanThread()
  lanmon.start()
  wanmon = WanThread()
  wanmon.start()
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)

