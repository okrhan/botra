import json, time, requests, os
from datetime import datetime

TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DATA_FILE = "data.json"

def telegram(metn):
    if not TOKEN or not CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": int(CHAT_ID), "text": metn},
            timeout=8)
        return r.status_code == 200
    except:
        return False

def data_yaz(fusretler, scan_sayi, son_scan):
    try:
        data = {
            "son_scan": son_scan,
            "scan_sayi": scan_sayi,
            "furset_sayi": len(fusretler),
            "fusretler": fusretler[:20]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Fayl yazma xetasi: {e}")

def scan(scan_sayi):
    zaman = datetime.now().strftime("%H:%M:%S")
    print(f"\nBOTRA | {zaman}")
    try:
        r = requests.get("https://gamma-api.polymarket.com/markets",
            params={"active":"true","closed":"false","limit":"100","order":"volume24hr"},
            timeout=10)
        bazarlar = r.json()
    except Exception as e:
        print(f"Bazar xetasi: {e}")
        return

    fusretler = []
    for b in bazarlar:
        try:
            prices = b.get("outcomePrices","[]")
            if isinstance(prices, str):
                prices = json.loads(prices)
            yes = float(prices[0])
            no  = float(prices[1])
            vol = float(b.get("volume24hr") or 0)
            ferq = 1.0 - yes - no
            if (yes < 0.07 or ferq >= 0.04) and vol >= 3000:
                fusretler.append({
                    "sual":  b.get("question","")[:70],
                    "yes":   round(yes, 3),
                    "no":    round(no, 3),
                    "ferq":  round(ferq, 3),
                    "hacim": int(vol),
                    "nov":   "obvious_no" if yes < 0.07 else "arbitraj"
                })
        except:
            continue

    fusretler = sorted(fusretler, key=lambda x: abs(x["ferq"]), reverse=True)
    print(f"{len(fusretler)} furset tapildi")
    data_yaz(fusretler, scan_sayi, zaman)

    if fusretler:
        metn = f"BOTRA [{zaman}]\n{len(fusretler)} furset\n\n"
        for f in fusretler[:3]:
            metn += f"{f['sual']}\nYES={f['yes']}  Nov={f['nov']}\n\n"
        ok = telegram(metn)
        print("Telegram OK!" if ok else "Telegram XETA!")

print("BOTRA ishleyir. Ctrl+C ile dayandirin.\n")
scan_sayi = 0
while True:
    try:
        scan_sayi += 1
        scan(scan_sayi)
        print("Novbeti scan 60 saniye sonra...")
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nDayandırildi.")
        break
