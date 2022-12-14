#
# Known Hosts
#
# You can optionally provide information here in this file about the machines
# you know about on your local area network.
#
# To help you identify the hosts you know, you may wish to run the monitor
# as-is (with the empty `KnownHosts` defined below) to begin and then use
# the information it provides to figure out which of your machines are which.
# As you figure out machines, one-by-one, put their MAC addresses in here
# along with descriptive strings so you will recognize them in the monitor's
# table. When you have made the changes you wish to this file, then simply
# run the "make" command again to rebuild and re-launch the monitor.
#
# For each host you enter into KnownHosts below you **must** provide its MAC
# address, and it is strongly recommended to also give it an "info" field to
# say what it is or does on your network. All of the other fields are all
# entirely optional but I find it useful in my network to highlight the hosts
# that I consider to be infrastructure, and to also note the last octets of
# any hosts that have static addresses.
#
# These are the fields I use in the entries in my KnownHosts array:
#   "mac"   MAC address, in colon-delimited capital letter format
#   "info"  a description of the host (any string can go here, or omit it)
#   "infra" (bool, optional) is this host providing infrastructure services?
#   "octet" (int, optional) last octet of IPv4 address (static addressed hosts)
#
# Some example host records are shown below.
#
# {"mac":'3C:37:86:5F:EC:39', "infra":True, "octet":1, "info":"Gateway"},
# {"mac":'10:A4:BE:4C:8C:3C', "infra":True, "info":"Security Cam #1, Porch"},
# {"mac":'18:FE:34:DD:BA:54', "info":"Purple Air ESP_DDBA54"},
#

KnownHosts = [
]

