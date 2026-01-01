#!/bin/bash

# Configuration
URL="https://app.cesaer.inrae.fr/endpoint"
SECRET="mywebshooksecret"
REPO="user/repo_name"
BRANCH="main"

# Payload
PAYLOAD=$(cat <<EOF
{
  "ref": "refs/heads/$BRANCH",
  "repository": {
    "full_name": "$REPO"
  }
}
EOF
)

# Calculate signature
# Mac/Linux specific
if [[ "$OSTYPE" == "darwin"* ]]; then
  SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
else
  SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
fi

echo "Sending webhook to $URL..."
echo "Payload: $PAYLOAD"
echo "Signature: sha256=$SIGNATURE"

curl -v -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: push" \
     -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
     -d "$PAYLOAD"
