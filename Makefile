# A simple Web UI for my Network Monitor

# Some bits from https://github.com/MegaMosquito/netstuff/blob/master/Makefile
LOCAL_DEFAULT_ROUTE     := $(shell sh -c "ip route | grep default")
LOCAL_IP_ADDRESS        := $(word 7, $(LOCAL_DEFAULT_ROUTE))

# CouchDB config
MY_COUCHDB_ADDRESS        := $(LOCAL_IP_ADDRESS)
MY_COUCHDB_PORT           := 5984
MY_COUCHDB_USER           := 'admin'
MY_COUCHDB_PASSWORD       := 'p4ssw0rd'
MY_COUCHDB_MACHINE_DB     := 'lan_hosts'
MY_COUCHDB_TIME_FORMAT    := '%Y-%m-%d %H:%M:%S'

# ----------------------------------------------------------------------------

all: build run

# Build the docker container
build:
	docker build -t monitor -f ./Dockerfile .

# Remove the local container image
clean:
	@docker rmi monitor 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	-docker rm -f monitor 2>/dev/null || :
	docker run -it -p 0.0.0.0:8000:6666 \
            --name monitor --restart unless-stopped \
            -e MY_COUCHDB_ADDRESS=$(MY_COUCHDB_ADDRESS) \
            -e MY_COUCHDB_PORT=$(MY_COUCHDB_PORT) \
            -e MY_COUCHDB_USER=$(MY_COUCHDB_USER) \
            -e MY_COUCHDB_PASSWORD=$(MY_COUCHDB_PASSWORD) \
            -e MY_COUCHDB_MACHINE_DB=$(MY_COUCHDB_MACHINE_DB) \
            -e MY_COUCHDB_TIME_FORMAT=$(MY_COUCHDB_TIME_FORMAT) \
            monitor /bin/sh

run:
	-docker rm -f monitor 2>/dev/null || :
	docker run --rm -d -p 0.0.0.0:80:6666 \
            --name monitor --restart unless-stopped \
            -e MY_COUCHDB_ADDRESS=$(MY_COUCHDB_ADDRESS) \
            -e MY_COUCHDB_PORT=$(MY_COUCHDB_PORT) \
            -e MY_COUCHDB_USER=$(MY_COUCHDB_USER) \
            -e MY_COUCHDB_PASSWORD=$(MY_COUCHDB_PASSWORD) \
            -e MY_COUCHDB_MACHINE_DB=$(MY_COUCHDB_MACHINE_DB) \
            -e MY_COUCHDB_TIME_FORMAT=$(MY_COUCHDB_TIME_FORMAT) \
            monitor

clean:
	-docker rm -f monitor 2>/dev/null || :
	-docker rmi -f monitor 2>/dev/null || :
