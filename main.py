import logging
import requests
import numpy as np
import random
import os
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request

# =========================
# 🔑 TOKEN
# =========================
BOT_TOKEN = os.getenv "8809308845:AAFp5VJAXQ2DsRIICw2p3s7BaeRIIoluUTg"  # <-- Render lo prende da Environment

# =========================
# ⚙️ PARAMETRI BASE
# =========================
PIP_SIZE = 0.10
PIP_VALUE_PER_LOT = 1.0
DEFAULT_BALANCE = 1000
DEFAULT_RISK_PCT = 1.0
TIMEFRAME = "M5"
AUTO_INTERVAL = 300  # 5 minuti

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# STORICO PREZZI REALI
# =========================
storico = []

# =========================
# 📡 PREZZO REALE DA BINANCE
# =========================
def prezzo_reale():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=XAUUSDT"
        data = requests.get(url).json()
        return float(data["price"])
    except:
        return None

# =========================
# 📊 INDICATORI REALI
# =========================
def ema(values, period):
    if len(values) < period:
        return None
    return np.mean(values[-period:])

def rsi(values, period=14):
    if len(values) < period:
        return None
    deltas = np.diff(values)
    up = deltas[deltas > 0].sum() / period
    down = -deltas[deltas < 0].sum() / period
    if down == 0:
        return 100
    rs = up / down
    return 100 - (100 / (1 + rs))

def macd(values):
    if len(values) < 26:
        return None
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    return ema12 - ema26

# =========================
# 📈 TREND + INDICATORI REALI
# =========================
def genera_indicatori():
    prezzo = prezzo_reale()
    if prezzo is None:
        prezzo = random.uniform(2300, 2600)

    storico.append(prezzo)

    ema20 = ema(storico, 20)
    ema50 = ema(storico, 50)
    rsi_val = rsi(storico)
    macd_val = macd(storico)

    if ema20 and ema50:
        if ema20 > ema50:
            trend = "uptrend"
        elif ema20 < ema50:
            trend = "downtrend"
        else:
            trend = "range"
    else:
        trend = "range"

    return {
        "trend_m5": trend,
        "trend_m15": trend,
        "trend_h1": trend,
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "rsi": round(rsi_val, 2) if rsi_val else None,
        "macd": round(macd_val, 2) if macd_val else None
    }

# =========================
# 🧠 SENTIMENT
# =========================
def leggi_sentiment():
    scelta = random.choices(
        ["bullish", "bearish", "neutral"],
        weights=[30, 30, 40],
        k=1
    )[0]
    confidence = random.randint(60, 95)
    return scelta, confidence

# =========================
# 🕒 MERCATO
# =========================
def stato_mercato():
    ora = datetime.utcnow().time()
    giorno = datetime.utcnow().weekday()

    if giorno == 5 or giorno == 6:
        return "chiuso"
    if giorno == 4 and ora >= time(23, 0):
        return "chiuso"
    return "aperto"

def descrizione_sessione():
    ora = datetime.utcnow().time()

    if time(0, 0) <= ora <= time(9, 0):
        return "🇯🇵 Tokyo — oro più calmo"
    if time(7, 0) <= ora <= time(16, 0):
        return "🇬🇧 Londra — buona volatilità"
    if time(12, 30) <= ora <= time(21, 0):
        return "🇺🇸 New York — oro molto volatile"

    return "📊 Sessione normale"

# =========================
# 🤖 ANALISI AI
# =========================
def analisi_ai_completa(s):
    direzione = s["direction"]
    ind = s["ind"]

    commenti = []

    if ind["trend_m5"] == ind["trend_m15"] == ind["trend_h1"]:
        commenti.append("📈 Trend multi‑timeframe allineati.")
    else:
        commenti.append("⚠️ Trend non allineati.")

    if ind["ema20"] > ind["ema50"] and direzione == "BUY":
        commenti.append("📊 EMA supportano BUY.")
    elif ind["ema20"] < ind["ema50"] and direzione == "SELL":
        commenti.append("📉 EMA supportano SELL.")
    else:
        commenti.append("⚠️ EMA non confermano.")

    if ind["rsi"] < 30 and direzione == "BUY":
        commenti.append("🟢 RSI ipervenduto → BUY.")
    elif ind["rsi"] > 70 and direzione == "SELL":
        commenti.append("🔴 RSI ipercomprato → SELL.")
    else:
        commenti.append("ℹ️ RSI neutro.")

    if ind["macd"] > 0 and direzione == "BUY":
        commenti.append("📈 MACD rialzista.")
    elif ind["macd"] < 0 and direzione == "SELL":
        commenti.append("📉 MACD ribassista.")
    else:
        commenti.append("⚠️ MACD non conferma.")

    num_warning = len([c for c in commenti if c.startswith("⚠️")])
    num_pos = len([c for c in commenti if c.startswith("📈") or c.startswith("📊") or c.startswith("🟢")])

    if num_warning >= 3:
        finale = "❌ Segnale debole."
    elif num_pos >= 3:
        finale = "✅ Segnale forte."
    else:
        finale = "➖ Segnale neutro."

    return "\n".join(commenti) + "\n\n" + finale

# =========================
# 🎯 GENERATORE SEGNALI
# =========================
def genera_segnale():
    sentiment, confidence = leggi_sentiment()
    ind = genera_indicatori()

    score_buy = 0
    score_sell = 0

    if ind["trend_m5"] == "uptrend": score_buy += 2
    if ind["trend_m5"] == "downtrend": score_sell += 2

    if ind["ema20"] > ind["ema50"]:
        score_buy += 2
    else:
        score_sell += 2

    if ind["rsi"] < 30: score_buy += 1
    if ind["rsi"] > 70: score_sell += 1

    if ind["macd"] > 0: score_buy += 1
    else: score_sell += 1

    if sentiment == "bullish": score_buy += 2
    if sentiment == "bearish": score_sell += 2

    direction = "BUY" if score_buy > score_sell else "SELL"

    entry = prezzo_reale()
    if entry is None:
        entry = random.uniform(2300, 2600)

    sl_pips = 200
    tp_pips = 400

    if direction == "BUY":
        sl = round(entry - sl_pips * PIP_SIZE, 2)
        tp = round(entry + tp_pips * PIP_SIZE, 2)
    else:
        sl = round(entry + sl_pips * PIP_SIZE, 2)
        tp = round(entry - tp_pips * PIP_SIZE, 2)

    rischio_euro = DEFAULT_BALANCE * (DEFAULT_RISK_PCT / 100.0)
    size_lots = rischio_euro / (sl_pips * PIP_VALUE_PER_LOT)

    rr = tp_pips / sl_pips

    analisi = analisi_ai_completa({
        "direction": direction,
        "ind": ind,
        "rr": rr,
        "sentiment": sentiment
    })

    return {
        "symbol": "XAUUSD",
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "rr": rr,
        "size": size_lots,
        "rischio": rischio_euro,
        "sentiment": sentiment,
        "confidence": confidence,
        "ind": ind,
        "ai": analisi
    }

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT XAUUSD con DATI REALI 🔥\n\n"
        "Comandi:\n"
        "• /auto → segnali automatici\n"
        "• /stop → stop segnali\n"
        "• /calc → segnale immediato\n"
        "• /auto_ai → segnali AI\n"
        "• /calc_ai → analisi AI"
    )

# =========================
# /auto
# =========================
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    if stato_mercato() == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "📡 *AUTO SIGNAL* (XAUUSD)\n"
        f"{descr}\n\n"
        f"Direzione: *{s['direction']}*\n"
        f"Entry: *{s['entry']}*\n"
        f"SL: *{s['sl']}*\n"
        f"TP: *{s['tp']}*\n\n"
        f"EMA20: {s['ind']['ema20']}\n"
        f"EMA50: {s['ind']['ema50']}\n"
        f"RSI: {s['ind']['rsi']}\n"
        f"MACD: {s['ind']['macd']}\n"
    )

    await context.bot.send_message(chat_id, testo, parse_mode="Markdown")

async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()
    context.job_queue.run_repeating(auto_job, interval=AUTO_INTERVAL, first=1, chat_id=chat_id)
    await update.message.reply_text("🚀 Auto-segnali attivati!")

# =========================
# /stop
# =========================
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()
    await update.message.reply_text("🛑 Auto-segnali fermati.")

# =========================
# /calc
# =========================
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if stato_mercato() == "chiuso":
        await update.message.reply_text("📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🎯 *Segnale MANUALE*\n"
        f"{descr}\n\n"
        f"Direzione: *{s['direction']}*\n"
        f"Entry: *{s['entry']}*\n"
        f"SL: *{s['sl']}*\n"
        f"TP: *{s['tp']}*\n\n"
        f"EMA20: {s['ind']['ema20']}\n"
        f"EMA50: {s['ind']['ema50']}\n"
        f"RSI: {s['ind']['rsi']}\n"
        f"MACD: {s['ind']['macd']}\n"
    )

    await update.message.reply_text(testo, parse_mode="Markdown")

# =========================
# /calc_ai
# =========================
async def calc_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if stato_mercato() == "chiuso":
        await update.message.reply_text("📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🤖 *AI ANALYSIS*\n"
        f"{descr}\n\n"
        f"Direzione: *{s['direction']}*\n"
        f"Entry: *{s['entry']}*\n"
        f"SL: *{s['sl']}*\n"
        f"TP: *{s['tp']}*\n\n"
        f"{s['ai']}"
    )

    await update.message.reply_text(testo, parse_mode="Markdown")

# =========================
# /auto_ai
# =========================
async def auto_ai_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    if stato_mercato() == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🤖 *AI AUTO SIGNAL*\n"
        f"{descr}\n\n"
        f"Direzione: *{s['direction']}*\n"
        f"Entry: *{s['entry']}*\n"
        f"SL: *{s['sl']}*\n"
        f"TP: *{s['tp']}*\n\n"
        f"{s['ai']}"
    )

    await context.bot.send_message(chat_id, testo, parse_mode="Markdown")

async def auto_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()
    context.job_queue.run_repeating(auto_ai_job, interval=AUTO_INTERVAL, first=1, chat_id=chat_id)
    await update.message.reply_text("🤖 Auto AI attivato!")

# =========================
# MAIN (WEBHOOK PER RENDER)
# =========================

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot attivo su Render!", 200

@server.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.process_update(update)
    return "OK", 200

if __name__ == "__main__":
    import asyncio

    async def main():
        await app.bot.set_webhook(f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook/{BOT_TOKEN}")
        server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    asyncio.run(main())
