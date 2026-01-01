#!/bin/bash

URL="http://localhost:5000/webhook"
REPO="user/repo_name"
BRANCH="main"
PAYLOAD='{"ref": "refs/heads/main", "repository": {"full_name": "user/repo_name"}}'

echo "Testing missing secret for GitHub..."
curl -v -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: push" \
     -d "$PAYLOAD"

echo -e "\n\nTesting missing secret for GitLab..."
# GitLab payload slightly different but detection relies on header first for this test
curl -v -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Push Hook" \
     -d "$PAYLOAD"
