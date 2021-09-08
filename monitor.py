#
# Simple Web UI for my Network Monitor
#
# Written by Glen Darling, November 2019.
#


import json
import os
import sys
import subprocess
import threading
import datetime
import time


# Configure all of these "MY_" environment variables for your situation
MY_SUBNET_CIDR            = os.environ['MY_SUBNET_CIDR']
MY_COUCHDB_ADDRESS        = os.environ['MY_COUCHDB_ADDRESS']
MY_COUCHDB_PORT           = int(os.environ['MY_COUCHDB_PORT'])
MY_COUCHDB_USER           = os.environ['MY_COUCHDB_USER']
MY_COUCHDB_PASSWORD       = os.environ['MY_COUCHDB_PASSWORD']
MY_COUCHDB_MACHINE_DB     = os.environ['MY_COUCHDB_MACHINE_DB']
MY_COUCHDB_TIME_FORMAT    = os.environ['MY_COUCHDB_TIME_FORMAT']


# Constants
IGNORE_AFTER_SEC = 24 * 60 * 60  # (1 day worth of seconds)
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6666
HTML_FILE = './site.html'
CSS_FILE = './site.css'
FAVICON_ICO = './favicon.ico'
LOGO_PNG = './logo.png'
YES_PNG = './yes.png'
NO_PNG = './no.png'
REFRESH_LAN_MSEC = 1000
REFRESH_WAN_MSEC = 5000
REFRESH_WEB_MSEC = 750
LONG_AGO_SEC = 100 * 365 * 24 * 60 * 60  # (100 years worth of seconds)


# Globals for the cached data
startup = datetime.datetime.now()
last = startup
last_wan = ""
last_machines = ""
last_updated = ""


# Output control (yeah, there are better ways to do this)
def show(str):
  #print(str)
  #sys.stdout.flush()
  pass


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

  # Loop forever collecting from the couchdb (whose data is provided by netmon)
  class LanThread(threading.Thread):
    @classmethod
    def is_locally_administered_mac(cls, mac):
      hex_str = mac[0:2]
      hex = int(hex_str, base=16)
      bit = (hex & 2) == 2
      return bit
    @classmethod
    def numeric_ip(cls, k):
      b = k.split('.')
      return int(b[0]) << 24 + \
             int(b[1]) << 16 + \
             int(b[2]) << 8 + \
             int(b[3])
    @classmethod
    def format_seconds(cls, secs, brief=True):
      out=[]
      periods = [
        ('day', 60*60*24),
        ('hr',  60*60),
        ('min', 60),
        ('sec', 1)
      ]
      if 1 > secs:
        return "0 secs"
      for period_name, period_seconds in periods:
        if secs >= period_seconds:
          period_value, secs = divmod(secs, period_seconds)
          has_s = 's' if int(period_value) > 1 else ''
          out.append("%d %s%s" % (int(period_value), period_name, has_s))
      if brief and 0 < len(out):
        return out[0]
      else:
        return ", ".join(out)
    def run(self):
      m_other = "machine-other"
      m_static = "machine-static"
      m_unknown = "machine-unknown"
      m_laa = "machine-local"
      m_infra = "machine-infra"
      show("LAN monitor thread started!")
      while True:
        fewest_seconds = LONG_AGO_SEC
        rows = {}
        db_hosts = db.get_all()
        # Find the most recent arrival(s)
        long_ago_sec = LONG_AGO_SEC
        for host in db_hosts:
          h = db.get(host['key'])
          if ('last_seen' in h and h['last_seen']):
            last_seen = h['last_seen']
            last_seen_how_long_ago_seconds = db.seconds_since(last_seen)
            first_seen_how_long_ago_seconds = last_seen_how_long_ago_seconds
            if ('first_seen' in h and h['first_seen']):
              first_seen = h['first_seen']
              first_seen_how_long_ago_seconds = db.seconds_since(first_seen)
            if first_seen_how_long_ago_seconds < long_ago_sec:
              long_ago_sec = first_seen_how_long_ago_seconds
        long_ago_sec += 10
        show("Latest: " + str(long_ago_sec) + "seconds ago.")
        for host in db_hosts:
          h = db.get(host['key'])
          show(json.dumps(h))
          ip = ""
          if ('ip' in h) and ('' != h['ip']):
            ip = h['ip']
          first = ""
          last = ""
          ignore = False
          latest = '&nbsp;'
          if ('last_seen' in h and h['last_seen']):
            last_seen = h['last_seen']
            last_seen_how_long_ago_seconds = db.seconds_since(last_seen)
            if last_seen_how_long_ago_seconds > IGNORE_AFTER_SEC:
              ignore = True
            if fewest_seconds > last_seen_how_long_ago_seconds:
              fewest_seconds = last_seen_how_long_ago_seconds
            last = LanThread.format_seconds(last_seen_how_long_ago_seconds, False)
            first_seen_how_long_ago_seconds = last_seen_how_long_ago_seconds
            if ('first_seen' in h and h['first_seen']):
              first_seen = h['first_seen']
              first_seen_how_long_ago_seconds = db.seconds_since(first_seen)
            # Mark the most recently seen "unknown" host
            if (not h['known']) and long_ago_sec > first_seen_how_long_ago_seconds:
              # Use a "delta" Greek letter to indicate most recently seen
              latest = '&#916;'
            first = LanThread.format_seconds(first_seen_how_long_ago_seconds)
          mac = h['mac']
          info = h['info']
          row_type = m_other
          if (not h['known']):
            row_type = m_unknown
            if LanThread.is_locally_administered_mac(mac):
              row_type = m_laa
          elif (h['infra']):
            row_type = m_infra
          elif (h['static'] and ("" != ip)):
            row_type = m_static
          if (("" != ip)) or (h['infra'] and ("" == ip)):
            ip_key = "256.256.256.256." + mac
            if ("" != ip):
              ip_key = ip
            if (not (ip_key in rows)) and (not ignore):
              rows[ip_key] = \
                '       <tr class="ROW-' + row_type + '">\n' + \
                '         <td> ' + latest + ' </td>\n' + \
                '         <td class="' + row_type + '">' + str(first) + '</td>\n' + \
                '         <td class="' + row_type + '">' + str(last) + '</td>\n' + \
                '         <td class="' + row_type + '">' + str(ip) + '</td>\n' + \
                '         <td class="' + row_type + '">' + str(mac) + '</td>\n' + \
                '         <td class="' + row_type + '">' + str(info) + '</td>\n' + \
                '       </tr>\n' + \
                ''
        out = ""
        ip_keys = sorted(rows.keys(), key=lambda k: LanThread.numeric_ip(k))
        for ip_key in ip_keys:
          out += rows[ip_key]
        if ("" != out):
          global last_machines
          last_machines = \
            '     <table class="monitor-table">\n' + \
            '       <tr>\n' + \
            '         <th> &nbsp; </th>\n' + \
            '         <th>First Seen</th>\n' + \
            '         <th>Last Seen</th>\n' + \
            '         <th>IPv4</th>\n' + \
            '         <th>MAC</th>\n' + \
            '         <th>Info</th>\n' + \
            '       </tr>\n' + \
            out + \
            '     </table>\n'
        delta = datetime.datetime.now() - startup
        up = LanThread.format_seconds(delta.total_seconds(), False)
        if 1 > fewest_seconds:
          updated = ' (updated just now)'
        elif LONG_AGO_SEC <= fewest_seconds:
          updated = ' (not updated yet)'
        else:
          fewest_str = LanThread.format_seconds(fewest_seconds, False)
          show("f_s=%d, str=%s" % (fewest_seconds, fewest_str))
          updated = ' (last updated: ' + fewest_str + ' ago)'
        global last_updated
        last_updated = \
          '   <p>&nbsp;Up: ' + str(up) + updated + '</p>\n'
        show("LAN monitor thread is sleeping for " + str(REFRESH_LAN_MSEC / 1000.0) + " seconds...")
        time.sleep(REFRESH_LAN_MSEC / 1000.0)

  # Loop forever checking WAN connectivity and constructing the HTML div
  class WanThread(threading.Thread):
    def run(self):
      global last_wan
      show("WAN monitor thread started!")
      WAN_COMMAND = 'curl -sS https://google.com 2>/dev/null | wc -l'
      while True:
        yes_no = str(subprocess.check_output(WAN_COMMAND, shell=True)).strip()
        # show("  WAN check = " + yes_no)
        wan = '     WAN: &nbsp;<img src="/no.png" class="monitor-wan" alt="no" />\n'
        if (yes_no != "0"):
          wan = '     WAN: &nbsp; <img src="/yes.png" class="monitor-wan" alt="yes" />\n'
        if wan != last_wan:
          if (yes_no != "0"):
            show("WAN is now connected.")
          else:
            show("WAN is now DISCONNECTED!")
        last_wan = wan
        show("WAN monitor thread is sleeping for " + str(REFRESH_WAN_MSEC / 1000.0) + " seconds...")
        time.sleep(REFRESH_WAN_MSEC / 1000.0)

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

  @webapp.route("/json")
  def get_json():
    j = {}
    j['last_wan'] = last_wan
    j['last_machines'] = last_machines
    j['last_updated'] = last_updated
    return (json.dumps(j) + '\n').encode('UTF-8')

  @webapp.route("/reboot")
  def post_reboot():
    # Before reboot, must sync all mounted filesystems
    os.system('sh -c "echo s > /sysrq"')
    # Then remount all mounted filesystems read-only so we can continue
    os.system('sh -c "echo u > /sysrq"')
    # Sleep, then force immediate reboot
    # Note that "b" does not sync or unmount, hence the "s" & "u" commands above
    os.system('sh -c "sleep 1 && echo b > /sysrq"')
    return '{"rebooting":true}\n'

  @webapp.route("/")
  def get_page():
    out = site_html.replace('MY_SUBNET_CIDR', MY_SUBNET_CIDR, 1)
    return out.replace('REFRESH_WEB_MSEC', str(REFRESH_WEB_MSEC), 1)

  # Prevent caching everywhere
  @webapp.after_request
  def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

  # Main program (instantiates and starts polling thread and then web server)
  print(MY_SUBNET_CIDR)
  lanmon = LanThread()
  lanmon.start()
  wanmon = WanThread()
  wanmon.start()
  # Read the site HTML template
  with open(HTML_FILE) as f:
    site_html= ' '.join(f.readlines())
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)

