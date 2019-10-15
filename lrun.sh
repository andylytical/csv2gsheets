#!/bin/bash

[[ $# -eq 1 ]] && container_name="$1"

BEERNAME='20191013 Pumpkin Joe Brown'

### Set Environment Variable(s) for Container
declare -A ENVIRON

# Google OAuth secret and credentials
ENVIRON['GOOGLE_AUTH_CLIENT_SECRETS_FILE']="$HOME/.googleauth/client_secrets.json"
ENVIRON['GOOGLE_AUTH_CREDENTIALS_FILE']="$HOME/.googleauth/credentials.json"

# Parent folder of the spreadsheets
# Existing spreadsheets must reside in this folder
ENVIRON['GOOGLE_DRIVE_FOLDER_ID']='1d57i-VAQRbCfLDIb9JCHGI3GPBK8cZ4O'

# Inside the spreadsheet, which sheet to populate with data
ENVIRON['GOOGLE_SHEETS_SHEETNAME']='Tilt Data'

# Which column (in GOOGLE_SHEETS_SHEET_NAME) has the timestamp
#ENVIRON['GOOGLE_SHEETS_TSDB_PRIMARY_COLUMN']='A'

# Update frequency (in seconds)
ENVIRON['CLOUD_BACKUP_INTERVAL_SECONDS']=60

# CSV Input file
ENVIRON['CSV2GSHEETS_INFILE']="$HOME/tiltdata/${BEERNAME}.csv"

# Google Sheets output file
ENVIRON['GOOGLE_SHEETS_FILENAME']="${BEERNAME}"

# Volume mounts
# Associative array; key=src, val=tgt
declare -A MOUNTPOINTS=( ["$HOME"]="$HOME" )

image_name=cloudpusherdev

# Build Image
docker build . -t $image_name

envs=()
for k in "${!ENVIRON[@]}"; do
    envs+=( '-e' "$k=${ENVIRON[$k]}" )
done

mounts=()
for src in "${!MOUNTPOINTS[@]}"; do
    dst="${MOUNTPOINTS[$src]}"
    mounts+=( '--mount' "type=bind,src=$src,dst=$dst" )
done

# Run Image
docker run --rm -it \
    "${envs[@]}" \
    "${mounts[@]}" \
    "$image_name"
