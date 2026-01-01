#!/bin/bash

# Configuration
URL="http://localhost:5000/webhook"
SECRET="mywebshooksecret"
REPO="user/repo_name"
BRANCH="main"

# GitLab sends the secret in X-Gitlab-Token
# Payload ref: https://docs.gitlab.com/ee/user/project/integrations/webhooks.html

PAYLOAD=$(cat <<EOF
{
  "object_kind": "push",
  "ref": "refs/heads/$BRANCH",
  "project": {
    "path_with_namespace": "$REPO"
  }
}
EOF
)

echo "Sending GitLab webhook to $URL..."
echo "Payload: $PAYLOAD"
echo "Token: $SECRET"

curl -v -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Push Hook" \
     -H "X-Gitlab-Token: $SECRET" \
     -d "$PAYLOAD"
