import requests
import json
import time
import os
 
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
CHECK_INTERVAL = 60
SEEN_FILE      = "seen_bounties.json"
 
# Endpoints da provare in ordine
API_URLS = [
    "https://frontend-api-v3.pump.fun/bounties?offset=0&limit=20&orderBy=newest",
    "https://frontend-api-v2.pump.fun/bounties?offset=0&limit=20&orderBy=newest",
    "https://frontend-api.pump.fun/bounties?offset=0&limit=20&orderBy=newest",
]
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, */*",
    "Origin": "https://pump.fun",
    "Referer": "https://pump.fun/",
}
 
 
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()
 
 
def save_seen(ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)
 
 
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("[Telegram] Messaggio inviato!")
    except Exception as e:
        print(f"[Telegram error] {e}")
 
 
def fetch_bounties():
    for url in API_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            print(f"[OK] Risposta da: {url}")
            if isinstance(data, list):
                return data
            return data.get("bounties", data.get("data", []))
        except Exception as e:
            print(f"[Fetch error] {url} → {e}")
    return []
 
 
def format_message(bounty):
    title     = bounty.get("name") or bounty.get("title") or "Senza titolo"
    reward    = bounty.get("reward") or bounty.get("rewardUsd") or bounty.get("total_reward") or "N/D"
    creator   = bounty.get("creator") or bounty.get("createdBy") or bounty.get("username") or "anonimo"
    bounty_id = bounty.get("id") or bounty.get("bountyId") or bounty.get("slug") or ""
    link      = f"https://pump.fun/bounties/{bounty_id}" if bounty_id else "https://pump.fun/bounties"
 
    return (
        f"🎯 <b>Nuova Bounty su Pump.fun!</b>\n\n"
        f"📌 <b>{title}</b>\n"
        f"💰 Reward: <b>{reward}</b>\n"
        f"👤 Creator: {creator}\n"
        f"🔗 <a href='{link}'>Apri bounty</a>"
    )
 
 
def main():
    print("✅ Bounty Notifier avviato. Controllo ogni", CHECK_INTERVAL, "secondi...")
    seen = load_seen()
 
    if not seen:
        bounties = fetch_bounties()
        if bounties:
            seen = {str(b.get("id") or b.get("bountyId") or b.get("slug", "")) for b in bounties}
            seen.discard("")
            save_seen(seen)
            print(f"[Init] Trovate {len(seen)} bounty esistenti, nessuna notifica inviata.")
            send_telegram("🤖 <b>Bounty Notifier attivo!</b>\nTi avviserò appena escono nuove bounty su Pump.fun.")
        else:
            print("[Init] Nessuna bounty trovata al primo avvio, riprovo al prossimo ciclo.")
 
    while True:
        time.sleep(CHECK_INTERVAL)
        bounties = fetch_bounties()
        new_ones = []
 
        for b in bounties:
            bid = str(b.get("id") or b.get("bountyId") or b.get("slug", ""))
            if bid and bid not in seen:
                new_ones.append(b)
                seen.add(bid)
 
        if new_ones:
            save_seen(seen)
            print(f"[+] {len(new_ones)} nuova/e bounty trovata/e!")
            for b in new_ones:
                msg = format_message(b)
                send_telegram(msg)
                print(f"    → Notifica inviata: {b.get('name') or b.get('title')}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Nessuna novità.")
 
 
if __name__ == "__main__":
    main()
