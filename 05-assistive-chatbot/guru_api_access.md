## Get access to Guru API
Add the following in `.env`:
```
GURU_API_TOKEN=...
COLLECTION_ID=...
```

Get the value for `GURU_API_TOKEN` from https://navalabs.atlassian.net/browse/DST-127?focusedCommentId=10029
and `COLLECTION_ID` from https://navalabs.atlassian.net/browse/DST-127?focusedCommentId=10032


Apply environment variables to command line shell: `source .env`

Verify it works: `curl -u $COLLECTION_ID:$GURU_API_TOKEN https://api.getguru.com/api/v1/teams -D -`

Expect:
```
HTTP/2 200
date: Tue, 19 Mar 2024 19:49:16 GMT
content-type: application/json
content-length: 449
...

[ {
  "organization" : {
    "name" : "Benefits Data Trust",
    "id" : "..."
  },
  "totalUsers" : 294,
  "topLevelOrganizationId" : "...",
  "name" : "Benefits Data Trust",
  "id" : "...",
  "status" : "ACTIVE",
  "dateCreated" : "2017-07-06T13:09:52.980+0000",
  "profilePicUrl" : "https://pp.getguru.com/....jpeg"
} ]%
```

## Get cards
Use web UI: https://developer.getguru.com/reference/getv1cardsgetextendedfact
or the following, which retrieves all pages:
```
NEXT_URL='https://api.getguru.com/api/v1/search/cardmgr?queryType=cards&showArchived=false'
CURL_COUNTER=1
while [ "$NEXT_URL" ]
do
  RESP_HEADER=$(curl -sS -D - \
    -u "$COLLECTION_ID:$GURU_API_TOKEN" \
    --request GET -o "guru_cards_for_nava_$CURL_COUNTER.json" \
    --header 'accept: application/json' \
    --url "$NEXT_URL")
  NEXT_URL=$(echo $RESP_HEADER | ggrep -oP '^link: <\K.*(?=>)')
  let CURL_COUNTER=$CURL_COUNTER+1
done

# Merge files each containing a JSON list
jq -n '[inputs] | add' guru_cards_for_nava_?.json guru_cards_for_nava_??.json > guru_cards_for_nava.json

# Create simplified JSON for readability
python ingest.py guru_cards_for_nava.json

# Count cards
jq length guru_cards_for_nava.json

# Zip
zip guru_cards_for_nava.zip guru_cards_for_nava.json guru_cards_for_nava_simplified.json
```

Share zip file via Google Drive.

## Extract all HTML content

`cat guru_cards_for_nava.json | jq '.[] | .content' > guru_cards.html`

`jq -r '.[] | .preferredPhrase + "\n  tags: " + ( [.tags[]?.value] | join(",") ) +"\n  content: " + .content' guru_cards_for_nava--Multi-benefit.json`
