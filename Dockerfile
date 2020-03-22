FROM arm32v6/python:3-alpine

RUN apk --no-cache --update add curl

# Install flask (for the REST API server)
RUN pip install Flask

# Install couchdb interface
RUN pip install couchdb

# Copy over needed files
WORKDIR /
COPY site.css /
COPY favicon.ico /
COPY logo.png /
COPY yes.png /
COPY no.png /

# Copy over the source code
WORKDIR /
COPY *.py /

# Run the daemon
WORKDIR /
CMD python monitor.py >/dev/null 2>&1

