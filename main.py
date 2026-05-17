import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import os

# 🔑 TOKEN DA RENDER
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ⚙️ PARAMETRI BASE
PIP_SIZE = 0.0001
PIP_VALUE_PER_LOT = 1.0
DEFAULT_BALANCE = 1000
DEFAULT_RISK_PCT = 1.0
TIMEFRAME = "M5"
AUTO_INTERVAL = 300  # 5 minuti

# LOGGING
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =========================
# LOGICA MERCATO
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
        return "🇯🇵 Tokyo — movimenti più lenti"
    if time(7, 0) <= ora <= time(16, 0):
        return "🇬🇧 Londra — volatilità alta"
    if time(12, 30) <= ora <= time(21, 0):
        return "🇺🇸 New York — movimenti forti"

    return "📊 Sessione normale"


# =========================
# SENTIMENT
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
# INDICATORI E TREND
# =========================
def genera_indicatori():
    trend_m5 = random.choice(["uptrend", "downtrend", "range"])
    trend_m15 = random.choice(["uptrend", "downtrend", "range"])
    trend_h1 = random.choice(["uptrend", "downtrend", "range"])

    ema20 = round(random.uniform(1.05000, 1.15000), 5)
    ema50 = round(random.uniform(1.05000, 1.15000), 5)
    rsi = random.randint(20, 80)
    macd = round(random.uniform(-0.0020, 0.0020), 5)

    return {
        "trend_m5": trend_m5,
        "trend_m15": trend_m15,
        "trend_h1": trend_h1,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi,
        "macd": macd
    }


# =========================
# GENERATORE SEGNALI
# =========================
def genera_segnale():
    sentiment, confidence = leggi_sentiment()
    ind = genera_indicatori()

    score_buy = 0
    score_sell = 0

    # Trend influence
    if ind["trend_m5"] == "uptrend": score_buy += 2
    if ind["trend_m5"] == "downtrend": score_sell += 2

    if ind["trend_m15"] == "uptrend": score_buy += 1
    if ind["trend_m15"] == "downtrend": score_sell += 1

    if ind["trend_h1"] == "uptrend": score_buy += 1
    if ind["trend_h1"] == "downtrend": score_sell += 1

    # EMA influence
    if ind["ema20"] > ind["ema50"]: score_buy += 2
    else: score_sell += 2

    # RSI influence
    if ind["rsi"] < 30: score_buy += 1
    if ind["rsi"] > 70: score_sell += 1

    # MACD influence
    if ind["macd"] > 0: score_buy += 1
    else: score_sell += 1

    # Sentiment influence
    if sentiment == "bullish": score_buy += 2
    if sentiment == "bearish": score_sell += 2

    direction = "BUY" if score_buy > score_sell else "SELL"

    entry = round(random.uniform(1.05000, 1.15000), 5)

    sl_pips = 20
    tp_pips = 40

    if direction == "BUY":
        sl = round(entry - sl_pips * PIP_SIZE, 5)
        tp = round(entry + tp_pips * PIP_SIZE, 5)
    else:
        sl = round(entry + sl_pips * PIP_SIZE, 5)
        tp = round(entry - tp_pips * PIP_SIZE, 5)

    rischio_euro = DEFAULT_BALANCE * (DEFAULT_RISK_PCT / 100.0)
    size_lots = rischio_euro / (sl_pips * PIP_VALUE_PER_LOT)

    return {
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "rr": tp_pips / sl_pips,
        "size": size_lots,
        "rischio": rischio_euro,
        "sentiment": sentiment,
        "confidence": confidence,
        "ind": ind
    }


# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Benvenuto nel BOT TRADING M5 🔥\n\n"
        f"Timeframe: *{TIMEFRAME}*\n"
        "Size: 0.01 lotto = 0.01 €/pip\n"
        f"Rischio: {DEFAULT_RISK_PCT}% su {DEFAULT_BALANCE}€\n\n"
        "Comandi:\n"
        "• /auto → segnali automatici ogni 5 minuti 🚀\n"
        "• /stop → ferma i segnali 🛑\n"
        "• /calc → segnale immediato 🎯"
    , parse_mode="Markdown")


# =========================
# /auto
# =========================
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    stato = stato_mercato()

    if stato == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "📡 *Segnale AUTO* (M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}*\n\n"
        f"📈 EMA20: {s['ind']['ema20']}\n"
        f"📉 EMA50: {s['ind']['ema50']}\n"
        f"📊 RSI: {s['ind']['rsi']}\n"
        f"📉 MACD: {s['ind']['macd']}\n\n"
        f"🕒 Trend M5: {s['ind']['trend_m5']}\n"
        f"🕒 Trend M15: {s['ind']['trend_m15']}\n"
        f"🕒 Trend H1: {s['ind']['trend_h1']}\n\n"
        f"➡️ Entry: *{s['entry']}*\n"
        f"🛑 SL: *{s['sl']}* ({s['sl_pips']} pip)\n"
        f"🎯 TP: *{s['tp']}* ({s['tp_pips']} pip)\n\n"
        f"💰 Rischio: *{s['rischio']:.2f} €*\n"
        f"📊 Size: *{s['size']:.2f} lotti*\n"
        f"⚖️ R:R = *{s['rr']:.2f}*"
    )

    await context.bot.send_message(chat_id, testo, parse_mode="Markdown")


async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()

    context.job_queue.run_repeating(auto_job, interval=AUTO_INTERVAL, first=1, chat_id=chat_id)

    await update.message.reply_text("🚀 Auto-segnali attivati! Ogni 5 minuti riceverai un segnale.")


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
    stato = stato_mercato()

    if stato == "chiuso":
        await update.message.reply_text("📉 Mercato chiuso.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🎯 *Segnale MANUALE* (M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}*\n\n"
        f"📈 EMA20: {s['ind']['ema20']}\n"
        f"📉 EMA50: {s['ind']['ema50']}\n"
        f"📊 RSI: {s['ind']['rsi']}\n"
        f"📉 MACD: {s['ind']['macd']}\n\n"
        f"🕒 Trend M5: {s['ind']['trend_m5']}\n"
        f"🕒 Trend M15: {s['ind']['trend_m15']}\n"
        f"🕒 Trend H1: {s['ind']['trend_h1']}\n\n"
        f"➡️ Entry: *{s['entry']}*\n"
        f"🛑 SL: *{s['sl']}* ({s['sl_pips']} pip)\n"
        f"🎯 TP: *{s['tp']}* ({s['tp_pips']} pip)\n\n"
        f"💰 Rischio: *{s['rischio']:.2f} €*\n"
        f"📊 Size: *{s['size']:.2f} lotti*\n"
        f"⚖️ R:R = *{s['rr']:.2f}*"
    )

    await update.message.reply_text(testo, parse_mode="Markdown")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auto", auto))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("calc", calc))

    app.run_polling()


if __name__ == "__main__":
    main()
    
