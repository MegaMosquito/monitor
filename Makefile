#
# monitor  -- a simple web UI for my LAN monitor
#
# Written by Glen Darling (mosquito@darlingevil.com), December 2022.
#

NAME         := monitor
DOCKERHUB_ID := ibmosquito
VERSION      := 1.0.0

# This monitor uses https://github.com/MegaMosquito/lanscan and needs its URL:
LOCAL_IPV4_ADDRESS := $(word 7, $(shell sh -c "ip route | grep default | sed 's/dhcp src //'"))
LANSCAN_URL        := http://$(LOCAL_IPV4_ADDRESS):8003/lanscan/json

# Optionally specify the DHCP range used in your LAN, or just set these to 0
DHCP_RANGE_START := 100
DHCP_RANGE_END   := 199

# Running `make` with no target builds and runs this as a restarting daemon
default: build run

# Build the container and tag it
build:
	docker build -t $(DOCKERHUB_ID)/$(NAME):$(VERSION) .

# Running `make dev` will setup a working environment, just the way I like it.
# On entry to the container's bash shell, run `cd /outside` to work here.
dev: stop build
	docker run -it --volume `pwd`:/outside \
          --volume /proc/sysrq-trigger:/sysrq \
	  --name $(NAME) \
          -p 0.0.0.0:80:80 \
          -e LANSCAN_URL=$(LANSCAN_URL) \
          -e DHCP_RANGE_START=$(DHCP_RANGE_START) \
          -e DHCP_RANGE_END=$(DHCP_RANGE_END) \
	  $(DOCKERHUB_ID)/$(NAME):$(VERSION) /bin/bash

# Run the container as a daemon (build not forecd here, so build it first)
run: stop
	docker run -d --restart unless-stopped \
          --volume /proc/sysrq-trigger:/sysrq \
	  --name $(NAME) \
          -p 0.0.0.0:80:80 \
          -e LANSCAN_URL=$(LANSCAN_URL) \
          -e DHCP_RANGE_START=$(DHCP_RANGE_START) \
          -e DHCP_RANGE_END=$(DHCP_RANGE_END) \
	  $(DOCKERHUB_ID)/$(NAME):$(VERSION)

# Test the service by retrieving the web page (a browser is better for this)
test:
	@curl -s localhost:80/

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

