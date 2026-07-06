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
2.  **External Libraries:** `requests` and `tqdm`.
3.  **Accounts:** A Trakt.tv account, and a public AniList or MyAnimeList account.
4.  **API Credentials Required:**
    *   Trakt.tv API Application Client ID & Secret[cite: 1].
    *   *(Optional)* Discord Webhook URL, Google App Password, CallMeBot WhatsApp API Key.

---

## 📦 Setup & Deployment

### 1. Acquire Trakt API Keys
*   Go to [Trakt API Applications](https://trakt.tv/oauth/applications/new)[cite: 1].
*   Click "NEW APPLICATION"[cite: 1].
*   **Name:** "Anime Sync Engine" (or whatever you prefer)[cite: 1].
*   **Redirect uri:** Enter exactly `urn:ietf:wg:oauth:2.0:oob`[cite: 1].
*   **Permissions:** Ensure `/sync` permissions are included[cite: 1].
*   Click "SAVE APP" and copy your `Client ID` and `Client Secret`[cite: 1].

### 2. Initialize the Grid
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
pip install requests tqdm
