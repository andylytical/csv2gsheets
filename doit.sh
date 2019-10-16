#!/bin/bash
set -x

IMAGE=andylytical/csv2gsheets:20191014-672e357
CSV_BASEDIR=tiltdata
BEERNAME='20191013 Pumpkin Joe Brown'

declare -A ENVIRON
ENVIRON[CSV2GSHEETS_INFILE]=/${CSV_BASEDIR:-.}/${BEERNAME:-tiltdata}.csv
ENVIRON[CLOUD_BACKUP_INTERVAL_SECONDS]=3600
ENVIRON[GOOGLE_AUTH_CLIENT_SECRETS_FILE]=/.googleauth/client_secret.json
ENVIRON[GOOGLE_AUTH_CREDENTIALS_FILE]=/.googleauth/credentials.json
ENVIRON[GOOGLE_DRIVE_FOLDER_ID]=1d57i-VAQRbCfLDIb9JCHGI3GPBK8cZ4O
ENVIRON[GOOGLE_SHEETS_FILENAME]="${BEERNAME}"
ENVIRON[GOOGLE_SHEETS_SHEETNAME]='Tilt Data'
ENVIRON[PYTHONUNBUFFERED]=TRUE

for k in "${!ENVIRON[@]}"; do
    envs+=('-e')
    envs+=("$k=${ENVIRON[$k]}")
done

docker run -d \
--volume=${HOME}/${CSV_BASEDIR:-.}:/${CSV_BASEDIR} \
--volume=${HOME}/.googleauth:/.googleauth \
"${envs[@]}" \
$IMAGE

