#
# Known Hosts
#
# Provide information here about the machines you know about on your network.
# You can can run the monitor as-is (with no `KnownHosts` defined) and then
# use the information it provides to figure out which machines are which, then
# come back to add them here later (then rebuild/restart the network monitor).
#
# For each host you must provide its MAC address, and I recommend also giving
# it an "info" field to say what it is or does on your network. The other
# fields are all entirely optional.
#
#   "mac"   MAC address, in colon-delimited capital letter format
#   "info"  a description of the host (any string can go here, or omit it)
#   "infra" (optional) is this host "infrastructure"? (always expected online)
#   "octet" (optional) last octet of IPv4 address (for static addressed hosts)
#
# Some example host records are shown below.
#
# {"mac":'3C:37:86:5F:EC:39', "infra":True, "octet":1, "info":"Gateway"},
# {"mac":'10:A4:BE:4C:8C:3C', "infra":True, "info":"Security Cam #1, Porch"},
# {"mac":'18:FE:34:DD:CB:62', "info":"Purple Air ESP_DDBA54"},
#


KnownHosts = [
]

