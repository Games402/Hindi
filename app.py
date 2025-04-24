from flask import Flask, request, jsonify
import threading
import time
import os

app = Flask(__name__)

# Shared state
is_running = False
stop_flag = False
pending_queue = []
MAX_QUEUE_SIZE = 10
lock = threading.Lock()

# Simulate browser task with 5-minute hold
def open_browser_task(url):
    global is_running, stop_flag

    try:
        print(f"[START] Processing: {url}")
        time.sleep(300)  # Hold for 5 minutes
    finally:
        with lock:
            is_running = False
            print("[END] Task finished")

            if stop_flag:
                pending_queue.clear()
                print("[STOP] System stopping, queue cleared")
                return

            if pending_queue:
                next_url = pending_queue.pop(0)
                is_running = True
                print(f"[QUEUE] Starting next: {next_url}")
                threading.Thread(target=open_browser_task, args=(next_url,)).start()

@app.route("/start")
def start():
    global is_running, stop_flag

    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing ?url="}), 400

    with lock:
        if stop_flag:
            stop_flag = False  # Auto-resume

        if is_running:
            if len(pending_queue) >= MAX_QUEUE_SIZE:
                return jsonify({"error": "Queue full"}), 429
            pending_queue.append(url)
            return jsonify({
                "status": "queued",
                "position": len(pending_queue)
            })

        is_running = True
        threading.Thread(target=open_browser_task, args=(url,)).start()
        return jsonify({"status": "started"})

@app.route("/stop")
def stop():
    global is_running, stop_flag, pending_queue
    with lock:
        stop_flag = True
        is_running = False
        pending_queue.clear()
        return jsonify({"status": "stopped and cleared queue"})

@app.route("/status")
def status():
    with lock:
        return jsonify({
            "running": is_running,
            "queue_count": len(pending_queue),
            "queue": pending_queue
        })

# For Render deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
