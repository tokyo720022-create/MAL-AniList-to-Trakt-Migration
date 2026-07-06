# 🚀 OMNI-CHANNEL ANIME SYNC ENGINE

An elite, automated, two-way synchronization engine that bridges your **AniList** (or **MyAnimeList**) watch history, scores, and plans directly into your **Trakt.tv** profile. 

This system is heavily optimized for speed, precision routing, and multi-channel notifications. It automatically fetches your existing Trakt history and ratings to avoid adding duplicates and uses a hyper-fast Delta Sync to only process new data.

**Source Acknowledgment:** Originally created by Nikoloz Taturashvili solely for AniList, adapted for MAL public API access, and heavily enhanced into a fully automated command grid.

---

## ⚡ Elite Features

*   **Delta Sync Engine (Hyper-Speed):** Skips scanning your entire library every run. It saves a local timestamp anchor and selectively pushes *only* the updates made since your last execution.
*   **Chronological Shift Protocol:** Resolves time paradoxes. If an anime has missing watch dates, the script automatically analyzes the original broadcast timeline and dynamically spaces the watch logs across authentic date matrix windows.
*   **Omni-Channel Alerts:** Fires simultaneous, live status updates directly to your personal command grid:
    *   **Discord:** Delivers sleek, color-coded Rich Embed status panels listing exact title updates.
    *   **Gmail:** Transmits full text-based developer mission logs.
    *   **WhatsApp:** Sends instant encrypted alerts straight to your phone.
*   **The Sniper Dictionary:** A dedicated structural block that completely bypasses Trakt's standard search engine to force-lock stubborn or mismatch-prone titles using precise hardcoded IDs.
*   **Masterpiece Routing Matrix:** Automatically scans your scores. Any title rated **90 or higher** is instantly routed into a dedicated, custom private list on Trakt called *'Elite Masterpieces'*.
*   **Safe Execution:** Sends data to Trakt in calculated batches to respect API limits and prevent server lockouts.

---

## 🛠️ System Architecture & Prerequisites

1.  **Python 3.x** environment.
2.  **External Libraries:** Managed via `requirements.txt`.
3.  **Accounts:** A Trakt.tv account, and a public AniList or MyAnimeList account.
4.  **API Credentials Required:**
    *   Trakt.tv API Application Client ID & Secret.
    *   *(Optional)* Discord Webhook URL, Google App Password, CallMeBot WhatsApp API Key.

---

## 📦 Setup & Deployment

### 1. Acquire Trakt API Keys
*   Go to [Trakt API Applications](https://trakt.tv/oauth/applications/new).
*   Click "NEW APPLICATION".
*   **Name:** "Anime Sync Engine" (or your preferred name).
*   **Redirect uri:** Enter exactly `urn:ietf:wg:oauth:2.0:oob`.
*   **Permissions:** Ensure `/sync` permissions are included.
*   Click "SAVE APP" and copy your `Client ID` and `Client Secret`.

### 2. Initialize the Grid
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
pip install -r requirements.txt

3. Hardwire the Core
Open sync_to_trakt_2.py, trakt_cleanup.py, and trakt_auth.py in your text editor. Locate the configuration blocks at the top of each file and paste your specific API keys, usernames, and communication credentials.


Generate Security Clearance (Auth)
Before running the main engine, establish a secure link to your Trakt account. Run the authentication gateway:

Bash

python trakt_auth.py

Follow the on-screen terminal instructions to input your device code. This will generate a secure trakt_tokens.json file locally. Once completed, your system is fully armed.

5. Execute the Sync Engine
Launch the main synchronization protocol:
BASH

python sync_to_trakt_2.py

⚠️ Important Note on Trakt Matching
This script relies on searching Trakt using the Anime Title and Start Year obtained from AniList/MAL. There is no direct ID mapping available through these public APIs. While highly accurate, variations in naming conventions (e.g., OVAs, Specials, English vs. Romaji titles) can occasionally cause mismatches.

If a specific anime fails to match correctly, utilize the built-in Sniper Dictionary inside sync_to_trakt_2.py to hardcode the exact source and Trakt IDs, forcing a perfect link.

🤖 Windows Ghost Protocol (Total Automation)
To run this script completely on autopilot every single day, wire it into the Windows Task Scheduler:

1 . Create a Trakt_Sync.bat file on your desktop containing:

DOS

@echo off
cd /d "C:\Path\To\Your\Script\Folder"
python sync_to_trakt_2.py
exit


2 .Open Windows Task Scheduler and choose Create Basic Task.

3 .Name it "Trakt Auto-Sync", set the Trigger to Daily (e.g., at 3:00 AM), and point the Action to your Trakt_Sync.bat file.

The script will execute invisibly in the background while you sleep, scanning your delta updates and dropping the mission report to your phone, email, and Discord instantly.


☢️ The Purge Protocol (Reversal Engine)
If you need to wipe the board clean, the repository includes trakt_cleanup.py. This script reads your AniList and systematically hunts down and removes every matched entry from your Trakt History, Ratings, Watchlist, and Custom Lists.

Safety Catch: By default, the script will not execute to prevent accidental wipes. To arm the weapon, open trakt_cleanup.py and change the safety switch:


Python
CONFIRM_NUCLEAR_REVERSAL = True

Execute with python trakt_cleanup.py and watch it clear the grid.

📜 License
This project is open-source and released under the MIT License. Modify, distribute, and upgrade the mainframe as you see fit. See the LICENSE file for details.

