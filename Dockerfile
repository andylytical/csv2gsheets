FROM python:3

# Add an init
RUN pip install dumb-init

# Setup entrypoint
ENV TIMEZONE UTC
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
COPY docker-entrypoint.d /docker-entrypoint.d/
ENTRYPOINT ["/usr/local/bin/dumb-init", "--", "/docker-entrypoint.sh"]

# Get dependencies
ARG GAUTH_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/googleauthorizedservice.py
ARG GDRIVE_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/simplegoogledrive.py
ARG GTSDB_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/timeseriesdb.py
ADD ${GAUTH_URL} ${GDRIVE_URL} ${GTSDB_URL} /

# Setup csv2gsheets
COPY *.py /
RUN chmod +x /csv2gsheets.py

CMD ["bash"]
