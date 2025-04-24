from flask import Flask, request, jsonify
from threading import Thread, Lock
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time

app = Flask(__name__)

is_running = False
pending_numbers = []
lock = Lock()
stop_flag = False
MAX_PENDING = 10

def run_browser(url):
    global is_running, stop_flag

    options = Options()
    options.headless = True

    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        driver.get(url)
        start_time = time.time()
        while time.time() - start_time < 300:
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
        with lock:
            is_running = False
            if not stop_flag and pending_numbers:
                next_url = pending_numbers.pop(0)
                is_running = True
                Thread(target=run_browser, args=(next_url,)).start()

@app.route("/start", methods=["GET"])
def start():
    global is_running, stop_flag
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing ?url="}), 400

    with lock:
        if stop_flag:
            return jsonify({"error": "System is stopping"}), 403

        if is_running:
            if len(pending_numbers) >= MAX_PENDING:
                return jsonify({"error": "Queue full"}), 429
            pending_numbers.append(url)
            return jsonify({
                "status": "queued",
                "position": len(pending_numbers)
            })

        is_running = True
        Thread(target=run_browser, args=(url,)).start()

    return jsonify({"status": "started"})

@app.route("/stop", methods=["GET"])
def stop():
    global stop_flag, is_running, pending_numbers
    with lock:
        stop_flag = True
        pending_numbers.clear()
        is_running = False
    return jsonify({"status": "stopped and cleared queue"})

@app.route("/status", methods=["GET"])
def status():
    with lock:
        return jsonify({
            "running": is_running,
            "queue_count": len(pending_numbers),
            "queue": pending_numbers
        })

if __name__ == "__main__":
    app.run()
