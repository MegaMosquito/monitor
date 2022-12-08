#!/usr/bin/python3


import copy
from util import Util


DEBUG = True
def debug(s):
  if DEBUG:
    print(s)


# A simple class for host objects
#
# Host fields:
#        mac: The host's unique MAC address (str)
#       info: A string to describe the host (user data or interface info) (str)
#         ip: The IPv4 address of this host on the LAN (str)
#      known: Whether or not this is a known host (bool)
#      infra: Whether or not this is an always up infrastructure host (bool)
#      octet: Last IP address octet if statically addressed, or 255 if not (int)
# first_seen: Timestamp when this host was first observed (str)
#  last_seen: Timestamp of the most recent time this host was observed (str)
#
class Host:

  # Generic pseudo-constructor
  @staticmethod
  def new_host(mac, known, ip, octet, infra, info, first_seen, last_seen):
    host = dict()
    host['mac'] = mac
    host['known'] = known
    host['octet'] = octet
    host['infra'] = infra
    host['info'] = info
    host['ip'] = ip
    host['first_seen'] = first_seen
    host['last_seen'] = last_seen
    return host

  # Pseudo-constructor for known hosts
  @staticmethod
  def new_host_from_known_hosts(known_hosts, mac, ipv4, when):

    kh = known_hosts[mac]

    host = dict()
    host['mac'] = mac

    info = '(no info provided)'
    if 'info' in kh:
      info = kh['info']
    host['info'] = info

    host['ip'] = ipv4

    host['known'] = True

    infra = False
    if 'infra' in kh and kh['infra']:
      infra = True
    host['infra'] = infra

    octet = 255
    if 'octet' in kh:
      octet = kh['octet']
    host['octet'] = octet

    host['first_seen'] = when
    host['last_seen'] = when

    return host

  # Pseudo-constructor for discovered unknown hosts
  @staticmethod
  def new_unknown_host(mac, ip, info, now):
    host = dict()
    host['mac'] = mac
    host['info'] = info
    host['ip'] = ip
    host['known'] = False
    host['infra'] = False
    host['octet'] = ip.split('.')[-1]
    host['first_seen'] = now
    host['last_seen'] = now
    return host

  # Merge an existing host with some updated data in an other host object
  def merge(self, other):
    assert(self['mac'] == other['mac'])
    self['known'] = False
    if other['known']:
      self['known'] = True
      self['info'] = other['info']
    if other['octet'] != 255:
      self['octet'] = other['octet']
    if other['infra']:
      self['infra'] = True
    if 'ip' in other:
      self['ip'] = other['ip']
    if 'first_seen' in other:
      if 'first_seen' in self:
        self['first_seen'] = Util.older(self['first_seen'], other['first_seen'])
      else:
        self['first_seen'] = other['first_seen']
    if 'last_seen' in other:
      if 'last_seen' in self:
        self['last_seen'] = Util.younger(self['last_seen'], other['last_seen'])
      else:
        self['last_seen'] = other['last_seen']

  # Return a deep copy of the host
  def deepcopy(self):
    return copy.deepcopy(self)

  # Stringification method
  def __str__(self):
    ip = "(none)"
    if 'ip' in host: ip = host['ip']
    return('Host( ' + \
      'mac:' + host['mac'] + \
      ', ip:' + ip + \
      ', info:"' + info + \
      '" )')


