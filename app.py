from flask import Flask, request, jsonify
from threading import Thread, Lock
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from collections import deque
import time
import os

app = Flask(__name__)

# Shared state
browser_thread = None
stop_flag = False
lock = Lock()
pending_queue = deque()
is_running = False
MAX_QUEUE_SIZE = 5

def launch_browser_task(url):
    global is_running, stop_flag

    with lock:
        is_running = True
        stop_flag = False

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
with lock:
    if stop_flag:
        driver.quit()
        return

time.sleep(300)


    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        try:
            driver.quit()
        except:
            pass

        with lock:
            is_running = False

        check_pending_tasks()

def check_pending_tasks():
    with lock:
        if pending_queue and not is_running:
            next_url = pending_queue.popleft()
            Thread(target=launch_browser_task, args=(next_url,)).start()

@app.route('/start', methods=['GET'])
def start_browser():
    global is_running

    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    with lock:
        if is_running:
            if len(pending_queue) >= MAX_QUEUE_SIZE:
                return jsonify({
                    "status": "Queue full, try again later",
                    "max_queue_size": MAX_QUEUE_SIZE
                }), 429
            pending_queue.append(url)
            position = len(pending_queue)
            return jsonify({
                "status": "Browser busy, URL added to pending queue",
                "pending_count": position,
                "your_position": position
            }), 202
        else:
            browser_thread = Thread(target=launch_browser_task, args=(url,))
            browser_thread.start()
            return jsonify({"status": "Browser launched"}), 200

@app.route('/stop', methods=['GET'])
def stop_browser():
    global stop_flag, pending_queue

    with lock:
        if not is_running:
            return jsonify({"status": "No active browser session"}), 404
        stop_flag = True
        pending_queue.clear()
    return jsonify({"status": "Stop signal sent, queue cleared"}), 200

@app.route('/pending', methods=['GET'])
def show_pending():
    with lock:
        return jsonify({
            "pending_list": list(pending_queue),
            "pending_count": len(pending_queue)
        })

@app.route('/')
def index():
    return '📡 Automation system is running.'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
