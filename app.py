from flask import Flask, request, jsonify
from threading import Thread, Lock
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

browser_thread = None
stop_flag = False
lock = Lock()

def launch_browser(url, duration=300):
    global stop_flag

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    start_time = time.time()
    while time.time() - start_time < duration:
        with lock:
            if stop_flag:
                break
        time.sleep(1)

    driver.quit()

@app.route('/start', methods=['GET'])
def start_browser():
    global browser_thread, stop_flag
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    with lock:
        if browser_thread and browser_thread.is_alive():
            return jsonify({"status": "Browser already running"}), 409
        stop_flag = False

    browser_thread = Thread(target=launch_browser, args=(url,))
    browser_thread.start()
    return jsonify({"status": "Browser launched"}), 200

@app.route('/stop', methods=['GET'])
def stop_browser():
    global stop_flag
    with lock:
        if not browser_thread or not browser_thread.is_alive():
            return jsonify({"status": "No active browser session"}), 404
        stop_flag = True
    return jsonify({"status": "Stop signal sent"}), 200

@app.route('/')
def index():
    return 'Automation server is running.'

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
