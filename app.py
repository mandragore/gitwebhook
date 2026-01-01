import os
import json
import logging
import hmac
import hashlib
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_FILE = '/app/config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found at {CONFIG_FILE}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {CONFIG_FILE}")
        return []

def verify_signature(payload_body, secret_token, signature_header):
    if not signature_header:
        return False
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        return False
    return True

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Detect provider
    is_github = 'X-GitHub-Event' in request.headers
    is_gitlab = 'X-Gitlab-Event' in request.headers

    if not is_github and not is_gitlab:
        return jsonify({'msg': 'Unknown provider'}), 400

    payload = request.get_json()
    if not payload:
        return jsonify({'msg': 'Invalid JSON'}), 400

    config = load_config()
    matched = False

    repo_full_name = None
    branch_name = None
    
    # --- GitHub Logic ---
    if is_github:
        event = request.headers.get('X-GitHub-Event', 'ping')
        if event == 'ping':
            return jsonify({'msg': 'pong'}), 200
        if event != 'push':
            return jsonify({'msg': 'Event ignored'}), 200

        repo_full_name = payload.get('repository', {}).get('full_name')
        ref = payload.get('ref') # e.g., refs/heads/main
        if ref:
            branch_name = ref.split('/')[-1]

        if not repo_full_name or not branch_name:
             return jsonify({'msg': 'Missing repository or ref'}), 400

    # --- GitLab Logic ---
    elif is_gitlab:
        event = request.headers.get('X-Gitlab-Event')
        # GitLab push events usually send "Push Hook" or "Tag Push Hook"
        if event != 'Push Hook': 
             return jsonify({'msg': 'Event ignored'}), 200
        
        # GitLab specific payload parsing
        # project.path_with_namespace is roughly equivalent to github full_name
        repo_full_name = payload.get('project', {}).get('path_with_namespace')
        ref = payload.get('ref') # e.g., refs/heads/main
        if ref:
             branch_name = ref.split('/')[-1]

        if not repo_full_name or not branch_name:
             return jsonify({'msg': 'Missing project or ref'}), 400

    # Match config
    for item in config:
        if item.get('repo_name') == repo_full_name and item.get('branch') == branch_name:
            secret = item.get('secret')
            
            # Verify Signature / Secret
            if secret:
                if is_github:
                    signature = request.headers.get('X-Hub-Signature-256')
                    if not verify_signature(request.data, secret, signature):
                        logger.warning(f"Invalid signature for {repo_full_name}")
                        return jsonify({'msg': 'Invalid signature'}), 403
                elif is_gitlab:
                    # GitLab sends the secret token in X-Gitlab-Token
                    token = request.headers.get('X-Gitlab-Token')
                    if not token or token != secret:
                        logger.warning(f"Invalid token for {repo_full_name}")
                        return jsonify({'msg': 'Invalid token'}), 403
            
            # Execute actions
            path = item.get('path')
            container_name = item.get('container_name')
            
            logger.info(f"Triggering update for {repo_full_name} on branch {branch_name}")
            matched = True
            
            # 1. Git Pull
            if path:
                if os.path.exists(path):
                    try:
                        logger.info(f"Pulling in {path}")
                        subprocess.check_call(['git', '-C', path, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        logger.info(f"Successfully pulled {path}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to git pull: {e}")
                        return jsonify({'msg': 'Git pull failed'}), 500
                else:
                    logger.error(f"Path does not exist: {path}")
                    return jsonify({'msg': 'Path not found'}), 500
            
            # 2. Docker Restart
            if container_name:
                try:
                    logger.info(f"Restarting container {container_name}")
                    subprocess.check_call(['docker', 'restart', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logger.info(f"Successfully restarted {container_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to restart container: {e}")
                    return jsonify({'msg': 'Container restart failed'}), 500

    if matched:
        return jsonify({'msg': 'Success'}), 200
    else:
        return jsonify({'msg': 'No matching config found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
