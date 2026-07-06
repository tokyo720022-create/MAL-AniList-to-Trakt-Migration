# -*- coding: utf-8 -*-
import requests
import time
import json
import os
import unicodedata 
from tqdm import tqdm

# ==========================================
# --- ⚙️ CORE CONFIGURATION ---
# ==========================================
TRAKT_CLIENT_ID = "YOUR_TRAKT_CLIENT_ID" 
TRAKT_CLIENT_SECRET = "YOUR_TRAKT_CLIENT_SECRET" 
ANILIST_USERNAME = "YOUR_ANILIST_USERNAME" 

# ==========================================
# --- ⚠️ THE KILL SWITCH ---
# ==========================================
# WARNING: Setting this to True will ARM the reversal protocol. 
# It will delete your AniList matches from your Trakt History, Ratings, and Watchlist.
CONFIRM_NUCLEAR_REVERSAL = False  

MASTERPIECE_LIST_NAME = "Elite Masterpieces" 
SNIPER_DICTIONARY = {}

# ==========================================

TRAKT_TOKEN_FILE = "trakt_tokens.json"
ANILIST_API_URL = "https://graphql.anilist.co"
TRAKT_API_URL = "https://api.trakt.tv"
TRAKT_HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": TRAKT_CLIENT_ID,
}
API_CALL_DELAY = 1.5
SOURCE_API_DELAY = 0.8

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

# --- Custom List Finder ---
def get_masterpiece_list(access_token):
    headers = {**TRAKT_HEADERS, "Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(f"{TRAKT_API_URL}/users/me/lists", headers=headers, timeout=15)
        resp.raise_for_status()
        for t_list in resp.json():
            if t_list.get("name") == MASTERPIECE_LIST_NAME: return t_list.get("ids", {}).get("slug")
        return None
    except Exception: return None

# --- Data Extraction ---
def get_anilist_data(username):
    all_entries = []
    page = 1
    has_next = True
    query = """query ($username: String, $page: Int, $perPage: Int, $type: MediaType) {
        Page (page: $page, perPage: $perPage) { pageInfo { hasNextPage }
            mediaList (userName: $username, type: $type, status_in: [COMPLETED, CURRENT, PAUSED, DROPPED, REPEATING, PLANNING]) {
                status score(format: POINT_100) 
                media { idMal id title { romaji english } format type startDate { year } }
            } } }"""
    print(f"Fetching ANIME list for '{username}' for targeted removal...")
    while has_next:
        try:
            time.sleep(SOURCE_API_DELAY)
            r = requests.post(ANILIST_API_URL, json={'query': query, 'variables': {"username": username, "perPage": 50, "type": "ANIME", "page": page}}, timeout=20)
            r.raise_for_status(); data = r.json()
            if "errors" in data: return None
            
            page_data = data.get('data', {}).get('Page', {})
            all_entries.extend([e for e in page_data.get('mediaList', []) if e.get('media', {}).get('type') == 'ANIME'])
            has_next = page_data.get('pageInfo', {}).get('hasNextPage', False)
            if has_next: page += 1
        except Exception as e: 
            print(f"Error fetching AniList: {e}")
            return None
    return all_entries

# --- Targeted Removal Execution ---
def _send_remove_batch(endpoint, items, access_token, list_slug=None):
    if not items: return True, 0
    url = f"{TRAKT_API_URL}/{endpoint}" if not list_slug else f"{TRAKT_API_URL}/users/me/lists/{list_slug}/items/remove"
    payload = {"shows": [], "movies": []}
    count = 0
    for i in items:
        entry = {"ids": i["trakt_ids"]}
        payload[i["type"] + "s"].append(entry); count += 1
    try:
        r = requests.post(url, headers={**TRAKT_HEADERS, "Authorization": f"Bearer {access_token}"}, json=payload, timeout=30)
        if r.status_code == 429: time.sleep(int(r.headers.get('Retry-After', 15))); return _send_remove_batch(endpoint, items, access_token, list_slug)
        r.raise_for_status(); return True, count
    except Exception: return False, 0

if __name__ == "__main__":
    print(f"--- OMNI-CHANNEL REVERSAL PROTOCOL ---")
    if not CONFIRM_NUCLEAR_REVERSAL:
        print("\n[!] SAFETY CATCH ENGAGED.")
        print("To run the purge, open the script and set 'CONFIRM_NUCLEAR_REVERSAL = True'. Exiting.")
        exit(0)

    print("\n[!] SAFETY CATCH OFF. INITIATING PURGE SEQUENCE.")
    trakt_access_token = get_trakt_access_token()
    if not trakt_access_token: print("Auth failed."); exit(1)

    masterpiece_slug = get_masterpiece_list(trakt_access_token)
    source_entries = get_anilist_data(ANILIST_USERNAME)
    if not source_entries: exit(1)

    remove_history_batch, remove_ratings_batch, remove_watchlist_batch, remove_masterpiece_batch = [], [], [], []
    stats = {"history": 0, "ratings": 0, "watchlist": 0, "masterpieces": 0}

    print(f"\nScanning Trakt Grid for targets to eliminate...")
    for entry in tqdm(source_entries, desc="Locking Targets"):
        media = entry.get('media', {})
        source_id, title_eng, title_rom = media.get('id'), media.get('title', {}).get('english'), media.get('title', {}).get('romaji')
        year = media.get('startDate', {}).get('year')
        fmt = media.get('format')

        if not fmt or not (title_eng or title_rom) or fmt in ['MUSIC', 'UNKNOWN']: continue

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

            # Add to Kill Lists
            remove_history_batch.append({"type": i_type, "trakt_ids": t_ids})
            remove_ratings_batch.append({"type": i_type, "trakt_ids": t_ids})
            remove_watchlist_batch.append({"type": i_type, "trakt_ids": t_ids})
            remove_masterpiece_batch.append({"type": i_type, "trakt_ids": t_ids})

        # Fire Elimination Batches
        if len(remove_history_batch) >= 50: _, c = _send_remove_batch("sync/history/remove", remove_history_batch, trakt_access_token); stats["history"] += c; remove_history_batch = []; time.sleep(API_CALL_DELAY)
        if len(remove_ratings_batch) >= 50: _, c = _send_remove_batch("sync/ratings/remove", remove_ratings_batch, trakt_access_token); stats["ratings"] += c; remove_ratings_batch = []; time.sleep(API_CALL_DELAY)
        if len(remove_watchlist_batch) >= 50: _, c = _send_remove_batch("sync/watchlist/remove", remove_watchlist_batch, trakt_access_token); stats["watchlist"] += c; remove_watchlist_batch = []; time.sleep(API_CALL_DELAY)
        if len(remove_masterpiece_batch) >= 50 and masterpiece_slug: _, c = _send_remove_batch("", remove_masterpiece_batch, trakt_access_token, masterpiece_slug); stats["masterpieces"] += c; remove_masterpiece_batch = []; time.sleep(API_CALL_DELAY)

    # Final Elimination Batches
    if remove_history_batch: _, c = _send_remove_batch("sync/history/remove", remove_history_batch, trakt_access_token); stats["history"] += c
    if remove_ratings_batch: _, c = _send_remove_batch("sync/ratings/remove", remove_ratings_batch, trakt_access_token); stats["ratings"] += c
    if remove_watchlist_batch: _, c = _send_remove_batch("sync/watchlist/remove", remove_watchlist_batch, trakt_access_token); stats["watchlist"] += c
    if remove_masterpiece_batch and masterpiece_slug: _, c = _send_remove_batch("", remove_masterpiece_batch, trakt_access_token, masterpiece_slug); stats["masterpieces"] += c

    print(f"\n========================================")
    print(f"Purge Complete. Target Elimination Stats:")
    print(f"Removed from History: {stats['history']}")
    print(f"Removed from Ratings: {stats['ratings']}")
    print(f"Removed from Watchlist: {stats['watchlist']}")
    print(f"Removed from Masterpieces: {stats['masterpieces']}")
    print(f"========================================")
