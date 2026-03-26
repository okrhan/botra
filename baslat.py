import json, time, requests, os, threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN     = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
PORT      = int(os.environ.get("PORT", 8080))
DATA_FILE = "data.json"

data_store = {
    "son_scan": "--:--:--",
    "scan_sayi": 0,
    "furset_sayi": 0,
    "fusretler": []
}

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
            yes  = float(prices[0])
            no   = float(prices[1])
            vol  = float(b.get("volume24hr") or 0)
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

    data_store["son_scan"]    = zaman
    data_store["scan_sayi"]   = scan_sayi
    data_store["furset_sayi"] = len(fusretler)
    data_store["fusretler"]   = fusretler[:20]

    if fusretler:
        metn = f"BOTRA [{zaman}]\n{len(fusretler)} furset\n\n"
        for f in fusretler[:3]:
            metn += f"{f['sual']}\nYES={f['yes']}  Nov={f['nov']}\n\n"
        ok = telegram(metn)
        print("Telegram OK!" if ok else "Telegram XETA!")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/data.json" or self.path.startswith("/data.json?"):
            body = json.dumps(data_store, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/" or self.path == "/index.html":
            try:
                with open("index.html", "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(body)
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def web_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Web server port {PORT}-da ishleyir")
    server.serve_forever()

threading.Thread(target=web_server, daemon=True).start()

print("BOTRA ishleyir.\n")
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
