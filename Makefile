#
# monitor  -- a simple web UI for my LAN monitor
#
# Uses:
#   https://github.com/MegaMosquito/lanscan
#   https://github.com/MegaMosquito/portscan
#
# Written by Glen Darling (mosquito@darlingevil.com), December 2022.
#

NAME         := monitor
DOCKERHUB_ID := ibmosquito
VERSION      := 1.0.0

# *****************************************************************************
# NOTE: If any of the following capitalized "MY_..." variables exist in your
# shell environment, then  your shell values will be used instead of the
# values provided here in the Makefile.
# *****************************************************************************

# Where will HTTP requests be served (e.g., port 80 on all host interfaces)?
MY_HOST_BIND_ADDRESS   ?=0.0.0.0
MY_HOST_BIND_PORT      ?=80
MY_CONTAINER_BIND_PORT ?=80

# URLs must be provided for the lanscan and portscan REST API services
MY_LANSCAN_URL         ?=http://lanscan.local/lanscan/json
MY_PORTSCAN_URL_BASE   ?=http://portscan.local/portscan

# If the DHCP range of your LAN is specified, it will be used (0 means ignore)
MY_DHCP_RANGE_START    ?=0
MY_DHCP_RANGE_END      ?=0

# Running `make` with no target builds and runs this as a restarting daemon
default: build run

# Build the container and tag it
build:
	docker build -t $(DOCKERHUB_ID)/$(NAME):$(VERSION) .

# Running `make dev` will setup a working environment, just the way I like it.
# On entry to the container's bash shell, run `cd /outside` to work here.
dev: stop build
	docker run -it --volume `pwd`:/outside \
	  --name $(NAME) \
	  --volume /var/run/dbus:/var/run/dbus \
	  --volume /var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket \
          --volume /proc/sysrq-trigger:/sysrq \
          -p $(MY_HOST_BIND_ADDRESS):$(MY_HOST_BIND_PORT):$(MY_CONTAINER_BIND_PORT) \
          -e MY_CONTAINER_BIND_PORT=$(MY_CONTAINER_BIND_PORT) \
          -e MY_LANSCAN_URL=$(MY_LANSCAN_URL) \
          -e MY_PORTSCAN_URL_BASE=$(MY_PORTSCAN_URL_BASE) \
          -e MY_DHCP_RANGE_START=$(MY_DHCP_RANGE_START) \
          -e MY_DHCP_RANGE_END=$(MY_DHCP_RANGE_END) \
	  $(DOCKERHUB_ID)/$(NAME):$(VERSION) /bin/bash

# Run the container as a daemon (build not forecd here, so build it first)
run: stop
	docker run -d --restart unless-stopped \
	  --name $(NAME) \
	  --volume /var/run/dbus:/var/run/dbus \
	  --volume /var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket \
          --volume /proc/sysrq-trigger:/sysrq \
          -p $(MY_HOST_BIND_ADDRESS):$(MY_HOST_BIND_PORT):$(MY_CONTAINER_BIND_PORT) \
          -e MY_CONTAINER_BIND_PORT=$(MY_CONTAINER_BIND_PORT) \
          -e MY_LANSCAN_URL=$(MY_LANSCAN_URL) \
          -e MY_PORTSCAN_URL_BASE=$(MY_PORTSCAN_URL_BASE) \
          -e MY_DHCP_RANGE_START=$(MY_DHCP_RANGE_START) \
          -e MY_DHCP_RANGE_END=$(MY_DHCP_RANGE_END) \
	  $(DOCKERHUB_ID)/$(NAME):$(VERSION)

# Test the service by retrieving the web page (a browser is better for this)
test:
	@curl -s localhost:$(HOST_BIND_PORT)/

# Enter the context of the daemon container
exec:
	@docker exec -it ${NAME} /bin/sh

# Push the conatiner to DockerHub (you need to `docker login` first of course)
push:
	docker push $(DOCKERHUB_ID)/$(NAME):$(VERSION) 

# Stop the daemon container
stop:
	@docker rm -f ${NAME} >/dev/null 2>&1 || :

# Stop the daemon container, and cleanup
clean: stop
	@docker rmi -f $(DOCKERHUB_ID)/$(NAME):$(VERSION) >/dev/null 2>&1 || :

# Declare all of these non-file-system targets as .PHONY
.PHONY: default build dev run test exec push stop clean

