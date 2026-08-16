"""Launcher script for Sched 3 web application."""
import sys
import os
import uvicorn
import webbrowser
import threading
import time

def open_browser(port):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"  Sched 3 is live at: {url}")
    print(f"  Opening browser automatically...")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    port = 8000
    # Launch browser thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    # Run uvicorn server
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
