import json, time, requests, os, threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN     = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
PORT      = int(os.environ.get("PORT", 8080))

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
    print(f"BOTRA | {zaman}", flush=True)
    try:
        r = requests.get("https://gamma-api.polymarket.com/markets",
            params={"active":"true","closed":"false","limit":"100","order":"volume24hr"},
            timeout=10)
        bazarlar = r.json()
    except Exception as e:
        print(f"Xeta: {e}", flush=True)
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
    print(f"{len(fusretler)} furset", flush=True)
    data_store.update({
        "son_scan": zaman,
        "scan_sayi": scan_sayi,
        "furset_sayi": len(fusretler),
        "fusretler": fusretler[:20]
    })
    if fusretler:
        metn = f"BOTRA [{zaman}]\n{len(fusretler)} furset\n\n"
        for f in fusretler[:3]:
            metn += f"{f['sual']}\nYES={f['yes']}\n\n"
        telegram(metn)

INDEX_HTML = open("index.html", "rb").read() if os.path.exists("index.html") else b"<h1>BOTRA</h1>"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        if self.path.startswith("/data.json"):
            body = json.dumps(data_store, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(INDEX_HTML)

def web():
    print(f"Server :{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

threading.Thread(target=web, daemon=True).start()

scan_sayi = 0
while True:
    try:
        scan_sayi += 1
        scan(scan_sayi)
        time.sleep(60)
    except KeyboardInterrupt:
        break
