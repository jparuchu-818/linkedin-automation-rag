import uvicorn
from pyngrok import ngrok
import os
import subprocess
import time

NGROK_AUTH_TOKEN = "2ztUSHj7MQ5CrCwQALsE7uHVrQv_6KE2ZX9wvdNCPWrdjpb7b" 

def start_ngrok_and_server():
    """
    Starts the ngrok tunnel and then starts the FastAPI server.
    This process is designed to be left running in the background.
    """
    if NGROK_AUTH_TOKEN:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    else:
        print("[CRITICAL] NGROK_AUTH_TOKEN is not set. Cannot start server.")
        return

    print("[INFO] Starting persistent ngrok tunnel for FastAPI server...")
    try:
        tunnel = ngrok.connect(8000, "http")
        print(f"[INFO] Ngrok tunnel is LIVE at: {tunnel.public_url}")
        print("[INFO] This tunnel will remain active. Leave this terminal open.")
    except Exception as e:
        print(f"[ERROR] Could not start ngrok tunnel: {e}")
        return
        
    print("[INFO] Starting FastAPI approval server on port 8000...")
    subprocess.run(["uvicorn", "approval_server:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    try:
        start_ngrok_and_server()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down servers.")
        ngrok.disconnectall()