#
# Simple Web UI for my Network Monitor
#
# Uses:
#   lanscan:   https://github.com/MegaMosquito/lanscan
#   portscan:  https://github.com/MegaMosquito/portscan
#
# Written by Glen Darling, November 2019.
#


import json
import os
import sys
import random
import subprocess
import threading
import socket
import datetime
import time

import requests
from io import BytesIO
from flask import Flask
from flask import send_file
from waitress import serve

from host import Host
from util import Util
from known_hosts import KnownHosts
from vendors import Vendors


# Get values from the environment or use defaults
def get_from_env(v, d):
  if v in os.environ and '' != os.environ[v]:
    return os.environ[v]
  else:
    return d
MY_CONTAINER_BIND_PORT   = int(get_from_env('MY_CONTAINER_BIND_PORT', '80'))
MY_LANSCAN_URL           = get_from_env('MY_LANSCAN_URL', '')
MY_PORTSCAN_URL_BASE     = get_from_env('MY_PORTSCAN_URL_BASE', '')
MY_DHCP_RANGE_START      = get_from_env('MY_DHCP_RANGE_START', '0')
MY_DHCP_RANGE_END        = get_from_env('MY_DHCP_RANGE_END', '0')


# Configuration constants
DISCARD_AFTER_SEC = 24*60*60     # (1 day worth of seconds)
REFRESH_LANSCAN_MSEC = 10000     # LAN scan request frequency in milliseconds
REFRESH_PORTSCAN_MSEC = 100000   # Port scan request frequency in msec
REFRESH_WAN_MSEC = 60000         # WAN scan frequency in msec
REFRESH_WEB_MSEC = 5000          # Web page call back frquency in msec
LONG_AGO_SEC = 100*365*24*60*60  # (100 years worth of seconds)
HTML_FILE = './site.html'
CSS_FILE = './site.css'
FAVICON_ICO = './favicon.ico'
LOGO_PNG = './logo.png'
YES_PNG = './yes.png'
NO_PNG = './no.png'


# Output control (yeah, there are better ways to do this)
def debug(str):
  print(str)
  sys.stdout.flush()
  pass


# Globals for the cached data
known_hosts = {}
infra_hosts = {}
# Saved time markers
startup_time = datetime.datetime.now()
last_update_time = startup_time
# Cached WAN status (JSON and HTML versions)
last_wan_json = False
last_wan_html = ''
# Cached LAN scanner status (JSON and HTML versions)
last_lan_json = False
last_lan_html = ''
# Cached port scanner status (JSON and HTML versions)
last_ports_json = False
last_ports_html = ''
# Cached LAN scanning status (JSON and HTML versions)
last_machines_json = {}
last_machines_html = ''
last_count_json = 0
# Cached timing info (JSON and HTML versions)
last_updated_json = {}
last_updated_html = ''


# Check port scanner for info on this node then add any to the 'ports' field
def add_ports (db, mac):
  global last_ports_json
  global last_ports_html
  try:
    url = MY_PORTSCAN_URL_BASE + '/' + mac + '/json'
    #debug(f'Requesting: "{url}".')
    port_info = requests.get(url, verify=False, timeout=10)
    #debug(f'Received: "{port_info.text.strip()}".')
    port_info_json = port_info.json()
    p = '     Portscan: &nbsp; <img src="/yes.png" class="monitor-wan" alt="yes" />\n'
    if p != last_ports_html:
      debug("Port scanner is now responding.")
    if 'ports' in port_info_json:
      if 0 == len(port_info_json['ports']):
        db[mac]['ports'] = '(none open)'
      else:
        ports = ','.join(list(map(str,port_info_json['ports'])))
        db[mac]['ports'] = '[' + ports + ']'
    else:
      db[mac]['ports'] = '???'
    out = db[mac]['ports']
    #debug(f'Port string: "{out}".')
    last_ports_json = True
  except:
    last_ports_json = False
    db[mac]['ports'] = '???'
    p = '     Portscan: &nbsp;<img src="/no.png" class="monitor-wan" alt="no" />\n'
    if p != last_ports_html:
      debug("Port scanner is NOT responding!")
  last_ports_html = p


# Code for the thread that invokes the lanscan API to get snapshots of the LAN
class LanThread(threading.Thread):

  m_prefix = "machine-"
  m_other = m_prefix + "other"
  m_static = m_prefix + "static"
  m_unknown = m_prefix + "unknown"
  m_laa = m_prefix + "local"
  m_infra_online = m_prefix + "infra-on"
  m_infra_offline = m_prefix + "infra-off"

  @classmethod
  def is_locally_administered_mac(cls, mac):
    hex_str = mac[0:2]
    hex = int(hex_str, base=16)
    bit = (hex & 2) == 2
    return bit

  @classmethod
  def string_first_3_octets(cls, k):
    o = k.split('.')
    return '.'.join(o[:3])

  @classmethod
  def numeric_last_octet(cls, k):
    b = k.split('.')
    return int(b[3])

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

    global last_lan_json
    global last_lan_html
    db = infra_hosts
    base = 255
    debug("LAN monitor thread started!")
    while True:

      try:
        snapshot = requests.get(MY_LANSCAN_URL, verify=False, timeout=10)
        snapshot_json = snapshot.json()
        lan = '     LANscan: &nbsp; <img src="/yes.png" class="monitor-wan" alt="yes" />\n'
        if lan != last_lan_html:
          debug("LANscan scanner is now responding.")
        last_lan_json = True
      except:
        last_lan_json = False
        snapshot = ''
        snapshot_json = {}
        lan = '     LAN: &nbsp;<img src="/no.png" class="monitor-wan" alt="no" />\n'
        if lan != last_lan_html:
          debug("LAN scanner is NOT responding!")
      last_lan_html = lan

      if 'scan' in snapshot_json:

        # Note the time of this scan
        when = snapshot_json['time']['utc']
        debug('Snapshot %s contains %d nodes.' % (when, len(snapshot_json['scan'])))

        # Merge scan results into the db clone
        for node in snapshot_json['scan']:

          # Force uppercase for all MACs
          node['mac'] = node['mac'].upper()

          mac = node['mac']
          ip = node['ipv4']

          # Seen (MAC is already in the DB)
          if mac in db:
            # Update it in the DB...
            node = db[mac]
            if ip != node['ip']:
              #debug('INFO: MAC %s has changed IPv4 from %s to %s!' % (mac, node['ip'], ip))
              node['ip'] = ip
            node['last_seen'] = when
            if not ('first_seen' in node):
              node['first_seen'] = when

          # Unseen (MAC is not yet in the DB)
          else:
            if mac in known_hosts:
              # Instantiate a known host
              node = Host.new_host_from_known_hosts(known_hosts, mac, ip, when)
              #debug('KNOWN: %s (%s) -> %s' % (mac, ip, known_hosts[mac]['info']))
            else:
              # Instantiate an unknown host
              oui = mac[:8] # Organizational Unique Identifier (OUI) prefix
              info = '(no info found)'
              if oui in Vendors:
                info = Vendors[oui]
              node = Host.new_unknown_host(mac, ip, info, when)

            # Insert the new node in the new DB
            #debug('INFO: Adding new node %s.' % str(node))
            db[mac] = node

          node['online'] = True

        # Find the most recent arrival(s) so they cn be highlighted
        most_recent_seconds = LONG_AGO_SEC
        most_recent_mac = ''
        for mac in db.keys():
          node = db[mac]
          if 'first_seen' in node:
            first_seen = node['first_seen']
            first_seen_how_long_ago_seconds = Util.seconds_since(first_seen)
            if first_seen_how_long_ago_seconds < most_recent_seconds:
              most_recent_seconds = first_seen_how_long_ago_seconds
              most_recent_mac = mac
        debug("Latest node %s arrived %d seconds ago." % \
          (most_recent_mac, most_recent_seconds))

        # Discard any old non-infra DB entries not seen for a long time
        for mac in db.keys():
          node = db[mac]
          if not (node['infra']):
            last_seen = node['last_seen']
            last_seen_how_long_ago_seconds = Util.seconds_since(last_seen)
            if last_seen_how_long_ago_seconds > DISCARD_AFTER_SEC:
              debug('INFO: Discarding node with mac %s from database.' % mac)
              del db[mac]

        # Set up port scanning
        for mac in db.keys():
          add_ports(db, mac)

        # Now generate the LAN scan portion of the web page
        rows = {}
        rows_json = {}
        for mac in db.keys():
          node = db[mac]

          #debug('INFO: Processing node %s.' % str(node))
          ip = node['ip']
          known = node['known']
          online = node['online']
          info = node['info']
          octet = node['octet']
          infra = node['infra']

          # Create human-radable time expressions for first/last seen times
          if 'first_seen' in node:
            first_seen = node['first_seen']
            first_seen_how_long_ago_seconds = Util.seconds_since(first_seen)
            first = LanThread.format_seconds(first_seen_how_long_ago_seconds)
          else:
            first = '(???)'
          if 'last_seen' in node:
            last_seen = node['last_seen']
            last_seen_how_long_ago_seconds = Util.seconds_since(last_seen)
            last = LanThread.format_seconds(last_seen_how_long_ago_seconds)
          else:
            last = '(???)'

          # Mark the most recently seen node
          most_recent_flag = ''
          if mac == most_recent_mac:
            # Use a "delta" Greek letter to indicate most recently seen
            most_recent_flag = '&#916;'

          # Is a static pool defined, and if so, is host in the static pool?
          static = False
          if 0 != int(MY_DHCP_RANGE_START):
            n = LanThread.numeric_last_octet(ip)
            static = ((n < int(MY_DHCP_RANGE_START)) or (n > int(MY_DHCP_RANGE_END)))
            #debug("%s -> %d -> %s" % (ip, n, str(static)))

          # Is there any port info for this node?
          port_html = node['ports']

          # Compute the type of this node's row (which determines its color)
          row_type = LanThread.m_other
          if not known:
            row_type = LanThread.m_unknown
            if LanThread.is_locally_administered_mac(mac):
              row_type = LanThread.m_laa
          elif infra and online:
            row_type = LanThread.m_infra_online
          elif infra and not online:
            row_type = LanThread.m_infra_offline
          elif static:
            row_type = LanThread.m_static

          # Octets of 255 are catch-alls for offline nodes. Handle this...
          ip_str = ip
          last_octet = LanThread.numeric_last_octet(ip)
          first3 = LanThread.string_first_3_octets(ip)
          if 255 == last_octet:
            ip_str = '???.???.???.???'
            ip = '255.255.255.' + str(base)
            base += 1
          elif '255.255.255' == first3:
            ip_str = '???.???.???.' + str(last_octet)

          rows[ip] = \
            '       <tr class="ROW-' + row_type + '">\n' + \
            '         <td> ' + most_recent_flag + ' </td>\n' + \
            '         <td class="' + row_type + '">' + first + '</td>\n' + \
            '         <td class="' + row_type + '">' + last + '</td>\n' + \
            '         <td class="' + row_type + '">' + ip_str + '</td>\n' + \
            '         <td class="' + row_type + '">' + mac + '</td>\n' + \
            '         <td class="' + row_type + '">' + port_html + '</td>\n' + \
            '         <td class="' + row_type + '">' + info + '</td>\n' + \
            '       </tr>\n' + \
            ''
          rows_json[ip] = { \
            'type':row_type[len(LanThread.m_prefix):], \
            'most_recent':('' != most_recent_flag), \
            'first':first, \
            'last':last, \
            'ip':ip_str, \
            'mac':mac, \
            'ports':(node['ports'].split(',')), \
            'info':info \
            }

        # Sort the HTML table "rows" by their IPv4 addresses
        ip_keys = sorted(rows.keys(), key=lambda k: LanThread.numeric_ip(k))
        out = ""
        for ip_key in ip_keys:
          out += rows[ip_key]

        # Wrap the "rows" with their table structure and column headers
        table = \
          '     <table class="monitor-table">\n' + \
          '       <tr>\n' + \
          '         <th> &nbsp; </th>\n' + \
          '         <th>First Seen</th>\n' + \
          '         <th>Last Seen</th>\n' + \
          '         <th>IPv4</th>\n' + \
          '         <th>MAC</th>\n' + \
          '         <th>Ports</th>\n' + \
          '         <th>Info</th>\n' + \
          '       </tr>\n' + \
          out + \
          '     </table>\n'

        # Update the global HTML string that the web server serves
        global last_machines_json
        global last_machines_html
        last_machines_html = table
        last_machines_json = rows_json

        # Compute uptime, and last update time
        since_start = datetime.datetime.now() - startup_time
        up = LanThread.format_seconds(since_start.total_seconds(), False)
        global last_update_time
        since_last = (datetime.datetime.now() - last_update_time).total_seconds()
        when_utc = Util.now_str()
        if last_update_time == startup_time:
          updated = ' (starting up... please be patient...)'
          updated_json = "starting"
        else:
          since_last_str = LanThread.format_seconds(since_last, False)
          updated = ' (last updated ' + since_last_str + ' ago, at ' + when_utc + ', UTC)'
          updated_json = since_last_str
        time_utc_json = when_utc

        # Update the global HTML string that the web server serves
        global last_updated_json
        global last_count_json
        global last_updated_html
        last_count_json = len(db.keys())
        last_updated_json = {"when_ago":updated_json,"utc":time_utc_json}
        last_updated_html = \
          '   <p>&nbsp;' + str(len(db.keys())) + ' hosts are on this network.</p>\n' + \
          '   <p>&nbsp;Up: ' + str(up) + updated + '</p>\n'

        # Note the time of this update
        last_update_time = datetime.datetime.now()

        # Go back to sleep until next cycle
        debug("LAN monitor thread is sleeping for " + str(REFRESH_LANSCAN_MSEC / 1000.0) + " seconds...")
        time.sleep(REFRESH_LANSCAN_MSEC / 1000.0)


# Loop forever checking WAN connectivity and constructing the HTML div
class WanThread(threading.Thread):
  def run(self):
    global last_wan_json
    global last_wan_html
    debug("WAN monitor thread started!")
    WAN_COMMAND = 'curl -sS https://google.com 2>/dev/null | wc -l'
    while True:
      yes_no = str(subprocess.check_output(WAN_COMMAND, shell=True)).strip()
      #debug("  WAN check = " + yes_no)
      wan = '     WAN: &nbsp;<img src="/no.png" class="monitor-wan" alt="no" />\n'
      if (yes_no != "0"):
        wan = '     WAN: &nbsp; <img src="/yes.png" class="monitor-wan" alt="yes" />\n'
      if wan != last_wan_html:
        if (yes_no != "0"):
          last_wan_json = True
          debug("WAN is now connected.")
        else:
          last_wan_json = False
          debug("WAN is now DISCONNECTED!")
      last_wan_html = wan
      debug("WAN monitor thread is sleeping for " + str(REFRESH_WAN_MSEC / 1000.0) + " seconds...")
      time.sleep(REFRESH_WAN_MSEC / 1000.0)


# Must define the webapp variable before the annotations below
webapp = Flask('lanmon')                             
webapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
  j['status'] = {}
  j['status']['lanscan'] = last_lan_json
  j['status']['portscan'] = last_ports_json
  j['status']['wan'] = last_wan_json
  j['status']['host_count'] = last_count_json
  j['status']['updated'] = last_updated_json
  j['machines'] = last_machines_json
  return (json.dumps(j) + '\n').encode('UTF-8')

@webapp.route("/jsonhtml")
def get_json_html():
  j = {}
  j['last_wan'] = last_wan_html
  j['last_lan'] = last_lan_html
  j['last_ports'] = last_ports_html
  j['last_machines'] = last_machines_html
  j['last_updated'] = last_updated_html
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
  out = site_html.replace('REFRESH_WEB_MSEC', str(REFRESH_WEB_MSEC), 1)
  return out

# Prevent caching on all requests
@webapp.after_request
def add_header(r):
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  return r


# Main program (instantiates and starts polling thread and then web server)
if __name__ == '__main__':

  # Populate the known_hosts and infra_hosts dictionaries from "known_hosts.py"
  for host in KnownHosts:
    # Force uppercase for all MACs
    mac = host['mac'].upper()
    host['known'] = True
    host['online'] = False
    known_hosts[mac] = host
    if 'infra' in host and host['infra']:
      if not ('octet' in host):
        host['octet'] = 255
      host['ip'] = '255.255.255.' + str(host['octet'])
      infra_hosts[mac] = host

  # Start the thread that repeatedly calls lanscan for snapshots of the LAN
  lanmon = LanThread()
  lanmon.start()

  # Start the thread that monitors WAN connectivity
  wanmon = WanThread()
  wanmon.start()

  # Read the site HTML template so it can be delivered by the web server
  with open(HTML_FILE) as f:
    site_html = ' '.join(f.readlines())

  # Start the web server thread
  debug('Starting the REST API server thread...')
  threading.Thread(target=lambda: serve(
    webapp,
    host='0.0.0.0',
    port=MY_CONTAINER_BIND_PORT)).start(),


