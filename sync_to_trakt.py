# -*- coding: utf-8 -*-
import requests
import time
import json
import datetime
import os
import random
import unicodedata 
from tqdm import tqdm
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse

# ==========================================
# --- ⚙️ CORE CONFIGURATION ---
# ==========================================
# Get these from https://trakt.tv/oauth/applications
TRAKT_CLIENT_ID = "YOUR_TRAKT_CLIENT_ID" 
TRAKT_CLIENT_SECRET = "YOUR_TRAKT_CLIENT_SECRET" 

DATA_SOURCE = "AniList" # Options: "AniList" or "MAL"
ANILIST_USERNAME = "YOUR_ANILIST_USERNAME" 
MAL_CLIENT_ID = "YOUR_MAL_CLIENT_ID" 
MAL_USERNAME = "YOUR_MAL_USERNAME" 

# ==========================================
# --- 🚀 COMMAND CENTER COMMS & UPGRADES ---
# ==========================================

# ⚡ DELTA SYNC ENGINE (Set to True for hyper-speed syncs. Set False for full re-sync)
ENABLE_DELTA_SYNC = True 

# 🏆 MASTERPIECE ROUTING 
MASTERPIECE_SCORE_THRESHOLD = 90 
MASTERPIECE_LIST_NAME = "Elite Masterpieces" 

# 🎯 SNIPER DICTIONARY (Bypass search for stubborn matches)
# Format: { AniList_ID: {"type": "show" or "movie", "trakt": Trakt_ID} }
SNIPER_DICTIONARY = {}

# 📡 1. DISCORD COMMS
ENABLE_DISCORD = False
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL" 

# 📧 2. EMAIL COMMS (Requires Gmail App Password)
ENABLE_EMAIL = False
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_16_digit_app_password" 
EMAIL_RECEIVER = "your_email@gmail.com" 

# 📱 3. WHATSAPP COMMS (Via CallMeBot API)
ENABLE_WHATSAPP = False
WHATSAPP_PHONE = "+1234567890" # Your phone number with country code
WHATSAPP_API_KEY = "123456" # Your CallMeBot API key

# ==========================================

TRAKT_TOKEN_FILE = "trakt_tokens.json"
LAST_SYNC_FILE = "last_sync_time.json"

ANILIST_API_URL = "https://graphql.anilist.co"
TRAKT_API_URL = "https://api.trakt.tv"
TRAKT_HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": TRAKT_CLIENT_ID,
}
BATCH_SIZE = 50
API_CALL_DELAY = 1.5
SOURCE_API_DELAY = 0.8

# --- ⏳ CHRONOLOGICAL SHIFT GENERATOR ---
def get_random_fallback_date(release_year=None, release_month=None):
    start_dt = datetime.datetime(2023, 10, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    end_dt = datetime.datetime(2024, 5, 31, 12, 0, 0, tzinfo=datetime.timezone.utc)
    
    if release_year:
        if release_year > 2024 or (release_year == 2024 and release_month and release_month >= 6):
            start_dt = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            end_dt = datetime.datetime(2025, 5, 31, 12, 0, 0, tzinfo=datetime.timezone.utc)
            
    time_between = end_dt - start_dt
    random_days = random.randrange(max(1, time_between.days))
    random_date = start_dt + datetime.timedelta(days=random_days)
    return random_date.isoformat(timespec='seconds').replace('+00:00', 'Z')

# --- Delta Sync Tracker ---
def get_last_sync_time():
    if ENABLE_DELTA_SYNC and os.path.exists(LAST_SYNC_FILE):
        try:
            with open(LAST_SYNC_FILE, 'r') as f: return json.load(f).get("last_sync", 0)
        except Exception: return 0
    return 0

def update_last_sync_time():
    if ENABLE_DELTA_SYNC:
        try:
            with open(LAST_SYNC_FILE, 'w') as f: json.dump({"last_sync": int(time.time())}, f)
        except Exception as e: print(f"Error saving sync time: {e}")

# --- 🚀 COMMUNICATION PROTOCOLS ---

def format_report_lists(report_data):
    has_updates = False
    text_lines = []
    categories = [('history', '📺 History Added'), ('ratings', '⭐ Ratings Logged'), ('watchlist', '👀 Watchlist Added'), ('masterpieces', '🏆 Masterpieces Routed')]
    for key, title in categories:
        if report_data[key]:
            has_updates = True
            text_lines.append(f"\n{title}:")
            text_lines.extend([f"  • {t}" for t in report_data[key][:10]])
            if len(report_data[key]) > 10: text_lines.append(f"  *...and {len(report_data[key])-10} more*")
    return has_updates, "\n".join(text_lines)

def send_discord_report(report_data, processed, skipped):
    if not ENABLE_DISCORD or not DISCORD_WEBHOOK_URL: return
    has_updates, list_text = format_report_lists(report_data)
    embed = {"title": f"Mission Report: {ANILIST_USERNAME}", "color": 3066993 if has_updates else 10070709, "fields": []}
    
    categories = [('history', '📺 History Added'), ('ratings', '⭐ Ratings Logged'), ('watchlist', '👀 Watchlist Added'), ('masterpieces', '🏆 Masterpieces Routed')]
    for key, title in categories:
        if report_data[key]:
            items = "\n".join([f"• {t}" for t in report_data[key][:10]])
            if len(report_data[key]) > 10: items += f"\n*...and {len(report_data[key])-10} more*"
            embed["fields"].append({"name": title, "value": items, "inline": False})
            
    if not has_updates: embed["fields"].append({"name": "Status", "value": "No new updates found. Profile is fully synced.", "inline": False})
    embed["footer"] = {"text": f"Scanned: {processed} | Skipped via Delta Sync: {skipped}"}
    
    try: requests.post(DISCORD_WEBHOOK_URL, json={"username": "Trakt Sync Engine", "embeds": [embed]}, timeout=10)
    except Exception as e: print(f"Discord ping failed: {e}")

def send_email_report(report_data, processed, skipped):
    if not ENABLE_EMAIL: return
    print("Transmitting Email Report...")
    has_updates, list_text = format_report_lists(report_data)
    subject = f"✅ Trakt Sync Complete [{ANILIST_USERNAME}]" if has_updates else f"ℹ️ Trakt Sync: No Updates [{ANILIST_USERNAME}]"
    
    body = f"TRAKT SYSTEM: MISSION REPORT\n{'-'*35}\nScanned: {processed}\nSkipped (Delta): {skipped}\n"
    body += f"{list_text}\n" if has_updates else "\nStatus: No new updates found. Profile is fully synced."
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e: print(f"Email ping failed: {e}")

def send_whatsapp_report(report_data, processed, skipped):
    if not ENABLE_WHATSAPP: return
    print("Transmitting WhatsApp Report...")
    has_updates, list_text = format_report_lists(report_data)
    
    wa_text = f"*Trakt Mission Report: {ANILIST_USERNAME}*\n_Scanned: {processed} | Skipped: {skipped}_\n"
    wa_text += f"{list_text}" if has_updates else "\n*Status:* No new updates found. Profile is synced."
    
    encoded_text = urllib.parse.quote(wa_text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={encoded_text}&apikey={WHATSAPP_API_KEY}"
    
    try: requests.get(url, timeout=10)
    except Exception as e: print(f"WhatsApp ping failed: {e}")

# --- Trakt Custom List Engine ---
def get_or_create_masterpiece_list(access_token):
    headers = {**TRAKT_HEADERS, "Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(f"{TRAKT_API_URL}/users/me/lists", headers=headers, timeout=15)
        resp.raise_for_status()
        for t_list in resp.json():
            if t_list.get("name") == MASTERPIECE_LIST_NAME: return t_list.get("ids", {}).get("slug")
        payload = {"name": MASTERPIECE_LIST_NAME, "description": "Elite tier anime auto-routed from AniList.", "privacy": "private"}
        create_resp = requests.post(f"{TRAKT_API_URL}/users/me/lists", headers=headers, json=payload, timeout=15)
        return create_resp.json().get("ids", {}).get("slug")
    except Exception: return None

# --- Standard Tokens & Auth ---
def load_tokens_generic(token_file):
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f: return json.load(f)
        except Exception: return None
    return None

def save_tokens_generic(tokens, token_file):
    try:
        with open(token_file, 'w') as f: json.dump(tokens, f, indent=4)
    except Exception: pass

def get_trakt_access_token():
    tokens = load_tokens_generic(TRAKT_TOKEN_FILE)
    if tokens:
        if time.time() < tokens.get('acquired_at', 0) + tokens.get('expires_in', 0) - 86400: return tokens.get('access_token')
        url = f"{TRAKT_API_URL}/oauth/token"
        payload = {"refresh_token": tokens.get('refresh_token'), "client_id": TRAKT_CLIENT_ID, "client_secret": TRAKT_CLIENT_SECRET, "grant_type": "refresh_token"}
        try:
            r = requests.post(url, json=payload, timeout=15); r.raise_for_status()
            t = r.json(); t['acquired_at'] = time.time(); save_tokens_generic(t, TRAKT_TOKEN_FILE); return t.get('access_token')
        except Exception: pass
    return None

def get_anilist_data(username, last_sync_time):
    all_entries = []
    page = 1
    has_next = True
    query = """query ($username: String, $page: Int, $perPage: Int, $type: MediaType) {
        Page (page: $page, perPage: $perPage) { pageInfo { hasNextPage }
            mediaList (userName: $username, type: $type, sort: [UPDATED_AT_DESC], status_in: [COMPLETED, CURRENT, PAUSED, DROPPED, REPEATING, PLANNING]) {
                status score(format: POINT_100) progress updatedAt
                startedAt { year month day } completedAt { year month day }
                media { idMal id title { romaji english } format type startDate { year month } }
            } } }"""
    print(f"Fetching ANIME list for '{username}'...")
    while has_next:
        try:
            time.sleep(SOURCE_API_DELAY)
            r = requests.post(ANILIST_API_URL, json={'query': query, 'variables': {"username": username, "perPage": 50, "type": "ANIME", "page": page}}, timeout=20)
            r.raise_for_status(); data = r.json()
            if "errors" in data: return None
            
            page_data = data.get('data', {}).get('Page', {})
            raw_entries = [e for e in page_data.get('mediaList', []) if e.get('media', {}).get('type') == 'ANIME']
            
            if ENABLE_DELTA_SYNC and last_sync_time > 0:
                for entry in raw_entries:
                    if entry.get('updatedAt', 0) > last_sync_time:
                        all_entries.append(entry)
                    else:
                        print(f"Reached previously synced data. Terminating scan early at page {page}.")
                        return all_entries
            else:
                all_entries.extend(raw_entries)
                
            has_next = page_data.get('pageInfo', {}).get('hasNextPage', False)
            if has_next: page += 1
        except Exception as e: 
            print(f"Error fetching AniList: {e}")
            return None
    return all_entries

def format_anilist_date(dt_dict):
    if not dt_dict or not all(k in dt_dict and dt_dict[k] for k in ['year', 'month', 'day']): return None
    try: return datetime.datetime(dt_dict['year'], dt_dict['month'], dt_dict['day'], 12, 0, 0, tzinfo=datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    except Exception: return None

def _send_sync_batch(endpoint, items, access_token, list_slug=None):
    if not items: return True, 0
    url = f"{TRAKT_API_URL}/{endpoint}" if not list_slug else f"{TRAKT_API_URL}/users/me/lists/{list_slug}/items"
    payload = {"shows": [], "movies": []}
    count = 0
    for i in items:
        entry = {"ids": i["trakt_ids"]}
        if endpoint == "sync/history" and i.get("watched_at"): entry["watched_at"] = i["watched_at"]
        elif endpoint == "sync/ratings": entry["rating"] = int(i["rating"]); entry["rated_at"] = i.get("rated_at")
        payload[i["type"] + "s"].append(entry); count += 1
    try:
        r = requests.post(url, headers={**TRAKT_HEADERS, "Authorization": f"Bearer {access_token}"}, json=payload, timeout=30)
        if r.status_code == 429: time.sleep(int(r.headers.get('Retry-After', 15))); return _send_sync_batch(endpoint, items, access_token, list_slug)
        r.raise_for_status(); return True, count
    except Exception: return False, 0

if __name__ == "__main__":
    print(f"--- OMNI-CHANNEL TRAKT MIGRATION ENGINE ---")
    trakt_access_token = get_trakt_access_token()
    if not trakt_access_token: print("Auth failed. Please check credentials."); exit(1)

    masterpiece_slug = get_or_create_masterpiece_list(trakt_access_token)
    last_sync = get_last_sync_time()
    
    source_entries = get_anilist_data(ANILIST_USERNAME, last_sync)
    if not source_entries: exit(1)

    trakt_history_batch, trakt_ratings_batch, trakt_watchlist_batch, trakt_masterpiece_batch = [], [], [], []
    report_data = {"history": [], "ratings": [], "watchlist": [], "masterpieces": []}
    stats = {"skipped_error": 0}

    print(f"\nInitiating Deep Match Protocol...")
    for entry in tqdm(source_entries, desc="Processing"):
        media = entry.get('media', {})
        source_id, title_eng, title_rom = media.get('id'), media.get('title', {}).get('english'), media.get('title', {}).get('romaji')
        display_title = title_eng or title_rom or f"ID: {source_id}"
        year, month = media.get('startDate', {}).get('year'), media.get('startDate', {}).get('month') 
        fmt, score, status = media.get('format'), entry.get('score', 0), entry.get('status')
        date_iso = format_anilist_date(entry.get('completedAt'))

        if not fmt or not (title_eng or title_rom) or fmt in ['MUSIC', 'UNKNOWN']: stats["skipped_error"] += 1; continue

        trakt_match = None
        if source_id in SNIPER_DICTIONARY:
            snipe = SNIPER_DICTIONARY[source_id]
            trakt_match = {snipe["type"]: {"ids": {"trakt": snipe["trakt"]}}}
        else:
            t_type = "show" if fmt in ["TV", "OVA", "ONA", "SPECIAL", "TV_SHORT"] else "movie"
            for t in list(dict.fromkeys(filter(None, [title_eng, title_rom]))):
                try: query = requests.utils.quote("".join([c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c)]).encode('utf-8'))
                except Exception: query = requests.utils.quote(t.encode('utf-8'))
                try:
                    time.sleep(0.4)
                    r = requests.get(f"{TRAKT_API_URL}/search/{t_type}?query={query}{f'&years={year}' if year else ''}", headers=TRAKT_HEADERS, timeout=15)
                    if r.status_code == 200 and r.json(): trakt_match = r.json()[0]; break
                except Exception: pass

        if trakt_match:
            i_type = "show" if 'show' in trakt_match else "movie"
            t_ids = trakt_match[i_type].get('ids')
            if not t_ids: continue

            if status in ['PLANNING', 'plan_to_watch']:
                trakt_watchlist_batch.append({"type": i_type, "trakt_ids": t_ids})
                report_data["watchlist"].append(display_title)
            else:
                trakt_history_batch.append({"type": i_type, "trakt_ids": t_ids, "watched_at": date_iso or get_random_fallback_date(release_year=year, release_month=month)})
                report_data["history"].append(display_title)

            if score > 0:
                trakt_ratings_batch.append({"type": i_type, "trakt_ids": t_ids, "rating": max(1, min(10, round(score/10.0))), "rated_at": date_iso or get_random_fallback_date(release_year=year, release_month=month)})
                report_data["ratings"].append(f"{display_title} ({max(1, min(10, round(score/10.0)))}/10)")
                if score >= MASTERPIECE_SCORE_THRESHOLD:
                    trakt_masterpiece_batch.append({"type": i_type, "trakt_ids": t_ids})
                    report_data["masterpieces"].append(display_title)

        if len(trakt_history_batch) >= 50: _send_sync_batch("sync/history", trakt_history_batch, trakt_access_token); trakt_history_batch = []; time.sleep(API_CALL_DELAY)
        if len(trakt_ratings_batch) >= 50: _send_sync_batch("sync/ratings", trakt_ratings_batch, trakt_access_token); trakt_ratings_batch = []; time.sleep(API_CALL_DELAY)
        if len(trakt_watchlist_batch) >= 50: _send_sync_batch("sync/watchlist", trakt_watchlist_batch, trakt_access_token); trakt_watchlist_batch = []; time.sleep(API_CALL_DELAY)
        if len(trakt_masterpiece_batch) >= 50 and masterpiece_slug: _send_sync_batch("", trakt_masterpiece_batch, trakt_access_token, masterpiece_slug); trakt_masterpiece_batch = []; time.sleep(API_CALL_DELAY)

    if trakt_history_batch: _send_sync_batch("sync/history", trakt_history_batch, trakt_access_token)
    if trakt_ratings_batch: _send_sync_batch("sync/ratings", trakt_ratings_batch, trakt_access_token)
    if trakt_watchlist_batch: _send_sync_batch("sync/watchlist", trakt_watchlist_batch, trakt_access_token)
    if trakt_masterpiece_batch and masterpiece_slug: _send_sync_batch("", trakt_masterpiece_batch, trakt_access_token, masterpiece_slug)

    update_last_sync_time()

    processed = len(source_entries) 
    print(f"\n========================================")
    print(f"Migration Complete! (Scanned {processed} items)")
    print(f"========================================")
    
    # 🚀 FIRE OMNI-CHANNEL ALERTS
    # Note: 'skipped' is no longer easily calculated line-by-line due to the early termination logic, so it passes '0' or 'N/A' for now.
    send_discord_report(report_data, processed, "N/A (Delta Active)")
    send_email_report(report_data, processed, "N/A (Delta Active)")
    send_whatsapp_report(report_data, processed, "N/A (Delta Active)")
