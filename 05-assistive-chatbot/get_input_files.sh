#!/bin/bash

if [ -z "${GURU_CARDS_URL_ID}" ]; then
  echo "Please set GURU_CARDS_URL_ID to the Google Drive file ID of the Guru cards zip file."
  echo "Copy it from the URL -- it looks like: 1AO-AbCDeF1234567890abcdefgh"
  echo "Example usage: GURU_CARDS_URL_ID=1AO-AbCDeF1234567890abcdefgh ./get_input_files.sh"
  exit 1
fi

set -e

GURU_CARDS_URL="https://docs.google.com/uc?export=download&id=${GURU_CARDS_URL_ID}"
echo "Downloading from ${GURU_CARDS_URL}"
curl -f -L "${GURU_CARDS_URL}" -o /tmp/download.zip
unzip -o /tmp/download.zip
rm -v /tmp/download.zip
mv -v guru_cards_for_nava--Multi-benefit.json guru_cards_for_nava.json
