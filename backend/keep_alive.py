import time
import requests
import threading
import os

def ping_health_endpoint(url: str, interval: int = 600):
    """
    Periodically pings the /health endpoint to keep the Render service active.
    Default interval: 10 minutes (600 seconds).
    """
    print(f"🚀 [KEEP-ALIVE] Starting pinger for {url}")
    while True:
        try:
            # Add /health to the base URL if not present
            health_url = url.rstrip("/") + "/health"
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ [KEEP-ALIVE] Ping successful: {health_url}")
            else:
                print(f"⚠️ [KEEP-ALIVE] Ping failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ [KEEP-ALIVE] Connection error: {e}")
            
        time.sleep(interval)

def start_pinger(url: str):
    if not url:
        print("⏭️ [KEEP-ALIVE] No backend URL provided. Skipping pinger.")
        return
        
    pinger_thread = threading.Thread(target=ping_health_endpoint, args=(url,), daemon=True)
    pinger_thread.start()
