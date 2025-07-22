
# from flask import Flask, jsonify, send_from_directory
# import psycopg2
# from flask_cors import CORS

# app = Flask(__name__, static_folder='.')
# CORS(app)  # Enable CORS to allow fetch from browser

# @app.route('/data')
# def get_data():
#     try:
#         conn = psycopg2.connect(
#             host='localhost',
#             database='postgres',
#             user='postgres',
#             password='Sbt@1904'
#         )
#         cursor = conn.cursor()
#         cursor.execute('SELECT Expiry, PNLCE, PNLPE FROM mytable')
#         data = cursor.fetchall()
#         conn.close()
#         return jsonify(data)
#     except psycopg2.Error as e:
#         return jsonify({'error': f'Database error: {str(e)}'}), 500
#     except Exception as e:
#         return jsonify({'error': f'Server error: {str(e)}'}), 500

# @app.route('/')
# def serve_index():
#     return send_from_directory('.', 'index.html')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5100, debug=True)









from flask import Flask, jsonify, send_from_directory
import psycopg2
from flask_cors import CORS
import json
import requests
import schedule
import time
import threading
from base64 import b64encode

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS to allow fetch from browser

# GitHub configuration
GITHUB_TOKEN = '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'  # Replace with a valid GitHub PAT with repo scope
REPO_OWNER = 'SagarTarsariya'  # Verify this matches your GitHub username
REPO_NAME = 'Charts'  # Verify this matches your repository name
FILE_PATH = 'data.json'  # Ensure this matches the file path in the repo
BRANCH = 'main'  # Verify the branch name

def get_db_data():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='Sbt@1904'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT Expiry, PNLCE, PNLPE FROM mytable')
        data = cursor.fetchall()
        conn.close()
        if not data:
            print("Warning: No data retrieved from mytable")
            return [{'Expiry': '', 'PNLCE': 0, 'PNLPE': 0}]  # Return default data if empty
        return [{'Expiry': str(row[0]), 'PNLCE': float(row[1]) if row[1] is not None else 0, 'PNLPE': float(row[2]) if row[2] is not None else 0} for row in data]
    except psycopg2.Error as e:
        print(f'Database error: {str(e)}')
        return None
    except Exception as e:
        print(f'Server error: {str(e)}')
        return None

def update_github_file():
    print("Attempting to update data.json...")
    # Fetch data from database
    data = get_db_data()
    if not data:
        print("Failed to fetch data, skipping GitHub update")
        return

    # Save data to data.json
    try:
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)
        # print(f"Successfully saved data to data.json: {json.dumps(data)}")
    except Exception as e:
        print(f"Error saving to data.json: {str(e)}")
        return

    # GitHub API setup
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    print(f"Attempting to update URL: {url}")  # Debug URL

    # Get the current file's SHA (optional for creation)
    sha = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get('sha')
        elif response.status_code == 404:
            print(f"File not found at {url}. Will attempt to create it.")
        else:
            print(f"Failed to get file SHA: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Error fetching file SHA from GitHub: {str(e)}")
        return

    # Read the file content and encode it
    try:
        with open('data.json', 'rb') as f:
            content = b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading data.json: {str(e)}")
        return

    # Update or create the file on GitHub
    payload = {
        'message': f'Update data.json at {time.ctime()}',
        'content': content,
        'branch': BRANCH
    }
    if sha:
        payload['sha'] = sha  # Include SHA for updates
    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"Successfully updated data.json on GitHub at {time.ctime()}")
        else:
            print(f"Failed to update GitHub: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error updating GitHub: {str(e)}")

@app.route('/data')
def get_data():
    data = get_db_data()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Failed to fetch data'}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Schedule the GitHub update every 5 minutes
def schedule_task():
    schedule.every(5).minutes.do(update_github_file)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_task, daemon=True)
    scheduler_thread.start()
    # Force an immediate update
    print("Forcing initial data.json update...")
    update_github_file()
    app.run(host='0.0.0.0', port=5100, debug=True)

# After modifying this file in VS Code, commit and push to GitHub:
# git add app.py
# git commit -m "Handle initial file creation for 404 error"
# git push origin main