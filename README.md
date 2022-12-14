# monitor

This repo builds a docker container that serves a graphical web UI for my other network monitoring tools, [lanscan](https://github.com/MegaMosquito/lanscan) and [portscan](https://github.com/MegaMosquito/portscan). It looks like this when it is deployed on my home network:

![monitor](https://raw.githubusercontent.com/MegaMosquito/monitor/master/monitor.png)

## Web UI configuration:

Before starting the monitor web UI you may **optionally** configure your shell environment with hard-coded values for the configuration variables described in this section. If you do so, the container will use the values you set in your environment. Otherwise the `Makefile` will use its default values for these variables.

The first set of variables must be provided. The default values are the recommended way to configure all these tools so they can easily communicate. That is, I suggest you run the **lanscan** tool on a host named **lanscan** that advertises its name using bonjour/zeroconf. Similarly, I suggest you run the **portscan** service on a host named **portscan**. I use Raspberry Pi model 3B+ for each of those and as long as you use Raspberry Pi OS and set the hostnames to those names, this will work beautifully. Here are the variables with their default values:

- **MY_LANSCAN_URL** (default: **http://lanscan.local/lanscan/json**)
- **MY_PORTSCAN_URL_BASE** (default: **http://portscan.local/portscan**)

If you wish to have the monitor distinguish between statically addressed hosts and those that are given random IP numbers by your DHCP server, then you will need to tell the monitor the DHCP address range your DHCP server uses. Otherwise just leave these variables both set to their default values of 0.

- **MY_DHCP_RANGE_START** (default: **0**)
- **MY_DHCP_RANGE_END** (default: **0**)

The last set of variables you may wish to configure are the ones below. They determine where the web UI will be made available on the host where you run this monitor:

- **MY_HOST_BIND_ADDRESS** (default **0.0.0.0**)
- **MY_HOST_BIND_PORT** (default **80**)
- **MY_CONTAINER_BIND_PORT** (default **80**)

The default settings will make the monitor web UI available on all host interfaces at the standard web server port, 80.

## The hosts you know in your LAN:

Optionally you may provide the monitor with information about the machines you know about on your local area network (LAN). If you do so this monitor will highlight them differently and display the identifiers you have provided for them. You can see this in the screenshot above for all the hosts in my LAN (except the unknown hosts I haven't figured out yet). If you wish to provide information about your known hosts then edit the [known_hosts.py](https://github.com/MegaMosquito/monitor/blob/master/known_hosts.py) file before starting the monitor.

To help you discover the MAC addresses of hosts you know on your LAN,
 you may wish to run the monitor
as-is (with the empty `KnownHosts` defined below) to begin and then use
the information it provides to figure out which of your machines are which.
As you figure out machines, one-by-one, put their MAC addresses in here
along with descriptive strings so you will recognize them in the monitor's
table. When you have made the changes you wish to this file, then simply
run the "make" command again to rebuild and re-launch the monitor.

For each host you enter into the KnownHosts variable you **must** provide its MAC
address, and it is strongly recommended to also give it an "info" field to
say what it is or does on your network. All of the other fields are all
entirely optional but I find it useful in my network to highlight the hosts
that I consider to be infrastructure, and to also note the last octets of
any hosts that have static addresses.

These are the fields I use in the entries in my KnownHosts array:

-   "mac"   MAC address, in colon-delimited capital letter format
-   "info"  a description of the host (any string can go here, or omit it)
-   "infra" (bool, optional) is this host providing infrastructure services?
-   "octet" (int, optional) last octet of IPv4 address (static addressed hosts)

Some example KnownHosts records are shown below.

```
    {"mac":'3C:37:86:5F:EC:39', "infra":True, "octet":1, "info":"Gateway"},
    {"mac":'10:A4:BE:4C:8C:3C', "infra":True, "info":"Security Cam #1, Porch"},
    {"mac":'18:FE:34:DD:BA:54', "info":"Purple Air ESP_DDBA54"},
```

## Starting the monitor:

First, start up the two required services (see their respective **README.md** files for details on how to do that):

- [lanscan](https://github.com/MegaMosquito/lanscan)
- [portscan](https://github.com/MegaMosquito/portscan)

Once those two services are running, and tested. Perform and desired configuration in the **Makefile** as described in the previous sections, then start up the monitor. To start it, just cd into this directory and execute this single command:

```
make
```

Or you can manually do the 2 steps that command does, to first build the container then run it, by using the two steps below:

```
make build
make run
```

## Notes on using the monitor:

To use the monitor, simply point your browser at the host where you ran it and once it starts up you should see something similar to the image above. If you configured the interfaces or ports used, then make the appropriate adjustments.

Each row in the table represents a single real or virtual host on your LAN. For each host, its IPv4 address and MAC address are always shown, along with the first time the host was discovered, and the most recent time the host was found active. If you provided **info** about a known host, then that info is shown on the right.

For any unknown hosts, the first three octets of the MAC address are used to look up the hardware manufacturer of that physical Network Interface Card (NIC) and show this in the **info** field. You can see the results of this manufacturer lookup in the screenshot above, for the two unknown hosts. I find this vendor lookup is often helpful in trying to figure out the identity of a particular host on my network. This lookup is provided by the monitor code using the [vendors.py](https://github.com/MegaMosquito/monitor/blob/master/vendors.py) file. See the comment at the top of this file for information about how to obtain updated data for these lookups.

Over time, the **portscan** tool will gradually populate the list of ports, but this is a very slow process, since there are potentially 65,535 TCP ports open on each hosts and they must be checked individually. On many hosts this can be fast (under a minute to a few minutes). However, on hosts with more secure IP stacks, this can be a slow process taking several hours for a single host. See the [portscan](https://github.com/MegaMosquito/portscan) documentation for more details on this.

By default, only the **unknown** hosts are shown at startup. You can check the checkboxes in the legend at the bottom of the page in order to show more hosts. Most of the categories of hosts in the legend are really only useful if you have provided info about which hosts you know, which are infrastructure and what is your DHCP range.

Typical MAC addresses are given by network interface manufacturers, are globally unique, and are called Universally Administered Addresses. In contrast, Locally Administered Addresses are non-physical and not globally unique network interface addresses that are used for various purposes. For example, Virtual Machiness (VMs) created within one of the hosts on your network can be exposed as a VM on your LAN using a Locally Administered Address. Locally Administered Addresses always have a **1** as thei second least significant bit of the first octet of the MAC address. The monitor highlights these addresses automatically.

The monitor also monitors the WAN connection (by checking connectivity to Google) and shows this status in the WAN checkbox at the top of the page. Beside that are status checkboxes for the requires **lanscan** and **portscan** services. And finally there is a checkbox for the underlying monitor web UI service that provides the data shown on the web page (Javascript code inside the web page HTML polls the monitor service reqularly to update the table and it also updates this last checkbox.

The monitor also provides some statustics at the bottom of the page.

## Author

Written by Glen Darling, November 2022.

