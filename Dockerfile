FROM balenalib/rpi-debian-python:latest

# Install flask (for the REST API server)
RUN pip install Flask

# Install couchdb interface
RUN pip install couchdb

# Copy over needed files
WORKDIR /
COPY site.html /
COPY site.css /
COPY favicon.ico /
COPY logo.png /
COPY yes.png /
COPY no.png /

# Convenience tools for development
#RUN apt update && apt install -y curl jq

# Copy over the source code
WORKDIR /
COPY *.py /

# Run the daemon
WORKDIR /
CMD python monitor.py >/dev/null 2>&1
#CMD python monitor.py

