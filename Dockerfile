#
# A network monitor daemon container
#
# Written by Glen Darling (mosquito@darlingevil.com), December 2022.
#
FROM ubuntu:latest

# Install required stuff
RUN apt update && apt install -y python3 python3-pip avahi-utils
RUN pip3 install flask waitress requests

# Setup a workspace directory
RUN mkdir /lanmon
WORKDIR /lanmon

# Install convenience tools (may omit these in production)
# RUN apt install -y curl jq

# Copy over needed files
WORKDIR /lanmon
COPY site.html /lanmon/
COPY site.css /lanmon/
COPY favicon.ico /lanmon/
COPY logo.png /lanmon/
COPY yes.png /lanmon/
COPY no.png /lanmon/

# Convenience tools for development
#RUN apt update && apt install -y curl jq

# Copy over the source code
WORKDIR /lanmon
COPY *.py /lanmon/

# Start up the daemon process
CMD python3 monitor.py >/dev/null 2>&1
#CMD python3 monitor.py

