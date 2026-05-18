import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import os

# 🔑 TOKEN
# Per Render è meglio usare:
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# Se vuoi tenerlo fisso in locale:
BOT_TOKEN = "8809308845:AAFp5VJAXQ2DsRIICw2p3s7BaeRIIoluUTg"

# ⚙️ PARAMETRI BASE PER XAUUSD
PIP_SIZE = 0.10              # 0.10 = 1 pip oro
PIP_VALUE_PER_LOT = 1.0      # 1 pip per 1 lotto ≈ 1$
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

    # Sabato e domenica chiuso
    if giorno == 5 or giorno == 6:
        return "chiuso"

    # Venerdì sera chiusura
    if giorno == 4 and ora >= time(23, 0):
        return "chiuso"

    return "aperto"


def descrizione_sessione():
    ora = datetime.utcnow().time()

    if time(0, 0) <= ora <= time(9, 0):
        return "🇯🇵 Tokyo — oro più calmo"
    if time(7, 0) <= ora <= time(16, 0):
        return "🇬🇧 Londra — buona volatilità su XAUUSD"
    if time(12, 30) <= ora <= time(21, 0):
        return "🇺🇸 New York — oro molto volatile"

    return "📊 Sessione normale su XAUUSD"


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
# INDICATORI E TREND (XAUUSD)
# =========================
def genera_indicatori():
    trend_m5 = random.choice(["uptrend", "downtrend", "range"])
    trend_m15 = random.choice(["uptrend", "downtrend", "range"])
    trend_h1 = random.choice(["uptrend", "downtrend", "range"])

    # Prezzi oro in zona 2300–2600
    ema20 = round(random.uniform(2300.0, 2600.0), 2)
    ema50 = round(random.uniform(2300.0, 2600.0), 2)
    rsi = random.randint(20, 80)
    macd = round(random.uniform(-5.0, 5.0), 2)

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
# ANALISI AI COMPLETA
# =========================
def analisi_ai_completa(s):
    direzione = s["direction"]
    ind = s["ind"]

    commenti = []

    # TREND
    if ind["trend_m5"] == ind["trend_m15"] == ind["trend_h1"]:
        commenti.append("📈 I trend multi‑timeframe sono allineati, buona conferma di direzione.")
    else:
        commenti.append("⚠️ I trend non sono completamente allineati, possibile volatilità.")

    # EMA
    if ind["ema20"] > ind["ema50"] and direzione == "BUY":
        commenti.append("📊 Le EMA supportano il BUY (EMA20 sopra EMA50).")
    elif ind["ema20"] < ind["ema50"] and direzione == "SELL":
        commenti.append("📉 Le EMA supportano il SELL (EMA20 sotto EMA50).")
    else:
        commenti.append("⚠️ Le EMA non confermano pienamente la direzione.")

    # RSI
    if ind["rsi"] < 30 and direzione == "BUY":
        commenti.append("🟢 RSI in ipervenduto: possibile rimbalzo favorevole al BUY.")
    elif ind["rsi"] > 70 and direzione == "SELL":
        commenti.append("🔴 RSI in ipercomprato: possibile correzione favorevole al SELL.")
    else:
        commenti.append("ℹ️ RSI neutro, non dà segnali forti.")

    # MACD
    if ind["macd"] > 0 and direzione == "BUY":
        commenti.append("📈 MACD positivo: momentum rialzista.")
    elif ind["macd"] < 0 and direzione == "SELL":
        commenti.append("📉 MACD negativo: momentum ribassista.")
    else:
        commenti.append("⚠️ MACD non conferma la direzione.")

    # SL/TP
    rr = s["rr"]
    if rr >= 2:
        commenti.append("💰 Ottimo rapporto R:R, configurazione profittevole.")
    elif rr >= 1:
        commenti.append("📊 R:R accettabile.")
    else:
        commenti.append("⚠️ R:R sfavorevole, rischio alto.")

    # SENTIMENT
    if s["sentiment"] == "bullish" and direzione == "BUY":
        commenti.append("🧠 Il sentiment supporta il BUY.")
    elif s["sentiment"] == "bearish" and direzione == "SELL":
        commenti.append("🧠 Il sentiment supporta il SELL.")
    else:
        commenti.append("⚠️ Il sentiment non è allineato alla direzione.")

    # RISULTATO FINALE
    num_warning = len([c for c in commenti if c.startswith("⚠️")])
    num_pos = len([c for c in commenti if c.startswith("📈") or c.startswith("📊") or c.startswith("🟢")])

    if num_warning >= 3:
        finale = "❌ Analisi AI: segnale debole, indicatori contrastanti."
    elif num_pos >= 3:
        finale = "✅ Analisi AI: segnale forte, indicatori ben allineati."
    else:
        finale = "➖ Analisi AI: segnale neutro, alcuni indicatori concordano."

    return "\n".join(commenti) + "\n\n" + finale


# =========================
# GENERATORE SEGNALI XAUUSD
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
    if ind["ema20"] > ind["ema50"]:
        score_buy += 2
    else:
        score_sell += 2

    # RSI influence
    if ind["rsi"] < 30:
        score_buy += 1
    if ind["rsi"] > 70:
        score_sell += 1

    # MACD influence
    if ind["macd"] > 0:
        score_buy += 1
    else:
        score_sell += 1

    # Sentiment influence
    if sentiment == "bullish":
        score_buy += 2
    if sentiment == "bearish":
        score_sell += 2

    direction = "BUY" if score_buy > score_sell else "SELL"

    # Entry oro in zona 2300–2600
    entry = round(random.uniform(2300.0, 2600.0), 2)

    # SL/TP in pip oro (0.10 = 1 pip)
    sl_pips = 200   # 200 pip = 20.0$
    tp_pips = 400   # 400 pip = 40.0$

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
        "🔥 Benvenuto nel BOT TRADING XAUUSD (ORO) 🔥\n\n"
        f"Strumento: *XAUUSD*\n"
        f"Timeframe: *{TIMEFRAME}*\n"
        "Size: 1 lotto ≈ 1$/pip (0.10)\n"
        f"Rischio: {DEFAULT_RISK_PCT}% su {DEFAULT_BALANCE}€\n\n"
        "Comandi:\n"
        "• /auto → segnali automatici ogni 5 minuti 🚀\n"
        "• /stop → ferma i segnali 🛑\n"
        "• /calc → segnale immediato 🎯\n"
        "• /auto_ai → segnali automatici con analisi AI 🤖\n"
        "• /calc_ai → analisi AI immediata 🤖"
    , parse_mode="Markdown")


# =========================
# /auto (normale)
# =========================
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    stato = stato_mercato()

    if stato == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso su XAUUSD.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "📡 *Segnale AUTO* (XAUUSD M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}* su *{s['symbol']}*\n\n"
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

    await update.message.reply_text("🚀 Auto-segnali XAUUSD attivati! Ogni 5 minuti riceverai un segnale.")


# =========================
# /stop
# =========================
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()

    await update.message.reply_text("🛑 Auto-segnali XAUUSD fermati.")


# =========================
# /calc (normale)
# =========================
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stato = stato_mercato()

    if stato == "chiuso":
        await update.message.reply_text("📉 Mercato chiuso su XAUUSD.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🎯 *Segnale MANUALE* (XAUUSD M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}* su *{s['symbol']}*\n\n"
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
# /calc_ai
# =========================
async def calc_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stato = stato_mercato()

    if stato == "chiuso":
        await update.message.reply_text("📉 Mercato chiuso su XAUUSD.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🤖 *AI ANALYSIS* (XAUUSD M5)\n"
        f"{descr}\n\n"
        f"📌 Direzione: *{s['direction']}* su *{s['symbol']}*\n"
        f"➡️ Entry: *{s['entry']}*\n"
        f"🛑 SL: *{s['sl']}* ({s['sl_pips']} pip)\n"
        f"🎯 TP: *{s['tp']}* ({s['tp_pips']} pip)\n\n"
        f"📈 EMA20: {s['ind']['ema20']}\n"
        f"📉 EMA50: {s['ind']['ema50']}\n"
        f"📊 RSI: {s['ind']['rsi']}\n"
        f"📉 MACD: {s['ind']['macd']}\n\n"
        f"🕒 Trend M5: {s['ind']['trend_m5']}\n"
        f"🕒 Trend M15: {s['ind']['trend_m15']}\n"
        f"🕒 Trend H1: {s['ind']['trend_h1']}\n\n"
        f"{s['ai']}"
    )

    await update.message.reply_text(testo, parse_mode="Markdown")


# =========================
# /auto_ai
# =========================
async def auto_ai_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    stato = stato_mercato()

    if stato == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso su XAUUSD.")
        return

    descr = descrizione_sessione()
    s = genera_segnale()

    testo = (
        "🤖 *AI AUTO SIGNAL* (XAUUSD M5)\n"
        f"{descr}\n\n"
        f"📌 Direzione: *{s['direction']}* su *{s['symbol']}*\n"
        f"➡️ Entry: *{s['entry']}*\n"
        f"🛑 SL: *{s['sl']}* ({s['sl_pips']} pip)\n"
        f"🎯 TP: *{s['tp']}* ({s['tp_pips']} pip)\n\n"
        f"📈 EMA20: {s['ind']['ema20']}\n"
        f"📉 EMA50: {s['ind']['ema50']}\n"
        f"📊 RSI: {s['ind']['rsi']}\n"
        f"📉 MACD: {s['ind']['macd']}\n\n"
        f"🕒 Trend M5: {s['ind']['trend_m5']}\n"
        f"🕒 Trend M15: {s['ind']['trend_m15']}\n"
        f"🕒 Trend H1: {s['ind']['trend_h1']}\n\n"
        f"{s['ai']}"
    )

    await context.bot.send_message(chat_id, testo, parse_mode="Markdown")


async def auto_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()

    context.job_queue.run_repeating(auto_ai_job, interval=AUTO_INTERVAL, first=1, chat_id=chat_id)

    await update.message.reply_text("🤖 Auto-segnali XAUUSD con AI attivati! Ogni 5 minuti riceverai un segnale con analisi.")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auto", auto))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("calc_ai", calc_ai))
    app.add_handler(CommandHandler("auto_ai", auto_ai))

    app.run_polling()


if __name__ == "__main__":
    main()
