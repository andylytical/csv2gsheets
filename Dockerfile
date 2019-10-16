FROM python:3

# Add an init
RUN pip install dumb-init

# Setup entrypoint
ENV TIMEZONE UTC
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
COPY docker-entrypoint.d /docker-entrypoint.d/
ENTRYPOINT ["/usr/local/bin/dumb-init", "--", "/docker-entrypoint.sh"]

# Install common dependencies
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Install custom dependencies
ARG G_AUTH_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/googleauthorizedservice.py
ARG G_DRIVE_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/simplegoogledrive.py
ARG G_TSDB_URL=https://raw.githubusercontent.com/andylytical/simplegoogledrive/master/timeseriesdb.py
ADD ${G_AUTH_URL} ${G_DRIVE_URL} ${G_TSDB_URL} /

# Setup csv2gsheets
COPY *.py /
RUN chmod +x /csv2gsheets.py

#CMD ["bash"]
CMD ["/csv2gsheets.py"]
