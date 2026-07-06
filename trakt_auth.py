# -*- coding: utf-8 -*-
import requests
import time
import json
import os

# ==========================================
# --- ⚙️ AUTHENTICATION CONFIGURATION ---
# ==========================================
# Get these from https://trakt.tv/oauth/applications
TRAKT_CLIENT_ID = "YOUR_TRAKT_CLIENT_ID" 
TRAKT_CLIENT_SECRET = "YOUR_TRAKT_CLIENT_SECRET" 

TRAKT_TOKEN_FILE = "trakt_tokens.json"
TRAKT_API_URL = "https://api.trakt.tv"
# ==========================================

def save_tokens(tokens, token_file):
    try:
        with open(token_file, 'w') as f: 
            json.dump(tokens, f, indent=4)
        print(f"\n[+] SUCCESS: Tokens secured and encrypted in '{token_file}'.")
        print("[+] You are now cleared to run the Omni-Channel Sync Engine.")
    except Exception as e: 
        print(f"\n[!] CRITICAL ERROR: Failed to save tokens: {e}")

def authenticate_trakt():
    print(f"--- TRAKT.TV SECURITY GATEWAY ---")
    print("Initiating handshake with Trakt API...")
    
    if os.path.exists(TRAKT_TOKEN_FILE):
        print(f"[*] Alert: '{TRAKT_TOKEN_FILE}' already exists.")
        override = input("Do you want to overwrite it and re-authenticate? (y/n): ").strip().lower()
        if override != 'y':
            print("Auth sequence aborted. Existing clearance maintained.")
            return

    try:
        # Step 1: Request Device Code
        dc_req = requests.post(f"{TRAKT_API_URL}/oauth/device/code", json={"client_id": TRAKT_CLIENT_ID}, timeout=10)
        dc_req.raise_for_status()
        dc_info = dc_req.json()
        
        print("\n" + "="*40)
        print(f"🔒 AUTHORIZATION REQUIRED")
        print("="*40)
        print(f"1. Open this link in your browser:")
        print(f"   >> {dc_info['verification_url']}")
        print(f"\n2. Enter this exact security code:")
        print(f"   >> {dc_info['user_code']}")
        print("="*40)
        print("\nWaiting for your approval on Trakt.tv... (Do not close this window)")
        
        # Step 2: Poll for Token Approval
        start_t = time.time()
        while time.time() - start_t < dc_info['expires_in']:
            time.sleep(dc_info['interval'])
            chk = requests.post(
                f"{TRAKT_API_URL}/oauth/device/token", 
                json={
                    "client_id": TRAKT_CLIENT_ID, 
                    "client_secret": TRAKT_CLIENT_SECRET, 
                    "code": dc_info['device_code']
                }, 
                timeout=10
            )
            
            if chk.status_code == 200:
                # Token acquired successfully!
                tokens = chk.json()
                tokens['acquired_at'] = time.time()
                save_tokens(tokens, TRAKT_TOKEN_FILE)
                return
            elif chk.status_code == 400:
                # Pending - user hasn't entered code yet
                continue
            elif chk.status_code == 429:
                # Polling too fast - slow down
                time.sleep(2)
            elif chk.status_code == 418:
                print("\n[!] Auth denied by user. Sequence terminated.")
                return
            elif chk.status_code == 410:
                print("\n[!] The security code expired. Please run the script again.")
                return

        print("\n[!] Timeout: The authentication window has closed.")
    except Exception as e: 
        print(f"\n[!] SYSTEM ERROR: {e}")

if __name__ == "__main__":
    authenticate_trakt()
