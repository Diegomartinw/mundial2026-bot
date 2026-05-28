import os
import time
import requests
from datetime import datetime
import pytz

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY      = os.environ.get("API_KEY", "7a7a4dc82592564a322d7afa5147f2f7")
WA_PHONE     = os.environ.get("WA_PHONE", "5491153894820")
WA_BOT_KEY   = os.environ.get("WA_BOT_KEY", "9518094")
FIFA_LEAGUE  = 1
SEASON       = 2026
TZ           = pytz.timezone("America/Argentina/Buenos_Aires")
CHECK_EVERY  = 60  # segundos

FLAGS = {
    "Argentina":"🇦🇷","Brazil":"🇧🇷","France":"🇫🇷","Spain":"🇪🇸",
    "Germany":"🇩🇪","Mexico":"🇲🇽","Uruguay":"🇺🇾","Portugal":"🇵🇹",
    "England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","United States":"🇺🇸","Canada":"🇨🇦",
    "Japan":"🇯🇵","Morocco":"🇲🇦","Colombia":"🇨🇴","Ecuador":"🇪🇨",
    "Peru":"🇵🇪","Chile":"🇨🇱","Senegal":"🇸🇳","Croatia":"🇭🇷",
    "Switzerland":"🇨🇭","Netherlands":"🇳🇱","Serbia":"🇷🇸","Belgium":"🇧🇪",
    "Venezuela":"🇻🇪","Australia":"🇦🇺","Poland":"🇵🇱","Denmark":"🇩🇰",
    "Sweden":"🇸🇪","South Korea":"🇰🇷","Iran":"🇮🇷","Saudi Arabia":"🇸🇦",
}

prev_scores  = {}
prev_status  = {}
daily_sent   = ""

# ── WHATSAPP ──────────────────────────────────────────────────────────────────
def send_wa(msg):
    try:
        url = (
            f"https://api.callmebot.com/whatsapp.php"
            f"?phone={WA_PHONE}&text={requests.utils.quote(msg)}&apikey={WA_BOT_KEY}"
        )
        requests.get(url, timeout=10)
        print(f"[WA] {msg[:60]}...")
    except Exception as e:
        print(f"[WA ERROR] {e}")

def flag(name):
    return FLAGS.get(name, "🏳️")

def arg_time(utc_str):
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    return dt.astimezone(TZ).strftime("%H:%M")

# ── API FOOTBALL ──────────────────────────────────────────────────────────────
def get_fixtures(date_str):
    try:
        url = f"https://v3.football.api-sports.io/fixtures?league={FIFA_LEAGUE}&season={SEASON}&date={date_str}"
        res = requests.get(url, headers={"x-apisports-key": API_KEY}, timeout=15)
        data = res.json()
        return data.get("response", [])
    except Exception as e:
        print(f"[API ERROR] {e}")
        return []

def today_str():
    return datetime.now(TZ).strftime("%Y-%m-%d")

# ── DAILY SUMMARY ─────────────────────────────────────────────────────────────
def send_daily_summary(fixtures):
    if not fixtures:
        send_wa("☀️ *Buenos días!* No hay partidos del Mundial hoy. 🏆")
        return
    msg = "☀️ *¡Buenos días! Partidos del Mundial hoy:*\n\n"
    for f in fixtures:
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        time_arg = arg_time(f["fixture"]["date"])
        city = f["fixture"]["venue"]["city"] or ""
        msg += f"{flag(home)} {home} vs {away} {flag(away)}\n"
        msg += f"🕐 {time_arg} hs · 📍 {city}\n\n"
    msg += "¡A disfrutar el fútbol! ⚽🏆"
    send_wa(msg)

# ── MATCH EVENTS ──────────────────────────────────────────────────────────────
def check_events(fixtures):
    global prev_scores, prev_status

    for f in fixtures:
        fid      = f["fixture"]["id"]
        home     = f["teams"]["home"]["name"]
        away     = f["teams"]["away"]["name"]
        status   = f["fixture"]["status"]["short"]
        elapsed  = f["fixture"]["status"]["elapsed"] or "?"
        g_home   = f["goals"]["home"] or 0
        g_away   = f["goals"]["away"] or 0
        total    = g_home + g_away
        city     = f["fixture"]["venue"]["city"] or ""

        prev_s = prev_status.get(fid)
        prev_t = prev_scores.get(fid)

        LIVE     = {"1H","HT","2H","ET","BT","P"}
        DONE     = {"FT","AET","PEN"}
        UPCOMING = {"NS","TBD"}

        # Partido arrancó
        if prev_s in UPCOMING and status in LIVE:
            send_wa(
                f"🟢 *¡Arranca el partido!*\n"
                f"{flag(home)} {home} vs {away} {flag(away)}\n"
                f"📍 {city}"
            )

        # Partido terminó
        if prev_s in LIVE and status in DONE:
            extra = ""
            if status == "PEN": extra = "\n⚽ Definido por penales"
            elif status == "AET": extra = "\n⏱️ Tiempo extra"
            send_wa(
                f"🔴 *¡Partido finalizado!*\n"
                f"{flag(home)} {home} *{g_home} - {g_away}* {away} {flag(away)}{extra}"
            )

        # Gol
        if prev_t is not None and total > prev_t and status in LIVE:
            send_wa(
                f"⚽ *¡GOL!*\n"
                f"{flag(home)} {home} *{g_home} - {g_away}* {away} {flag(away)}\n"
                f"⏱️ Min {elapsed}"
            )

        prev_status[fid] = status
        prev_scores[fid] = total

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    global daily_sent
    print("🏆 Bot Mundial 2026 iniciado")
    send_wa("🏆 *Bot Mundial 2026 activado*\nVas a recibir alertas de goles, inicios y finales. ¡Listo!")

    while True:
        now = datetime.now(TZ)
        date = today_str()

        # Resumen 8 AM
        if now.hour == 8 and now.minute == 0 and daily_sent != date:
            daily_sent = date
            fixtures = get_fixtures(date)
            send_daily_summary(fixtures)

        # Chequeo de partidos
        fixtures = get_fixtures(date)
        if fixtures:
            check_events(fixtures)

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
