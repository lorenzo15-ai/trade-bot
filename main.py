import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

# 🔑 METTI QUI IL TUO TOKEN
BOT_TOKEN = "8809308845:AAFp5VJAXQ2DsRIICw2p3s7BaeRIIoluUTg"

# ⚙️ PARAMETRI BASE
PIP_SIZE = 0.0001              # per EURUSD, GBPUSD ecc.
PIP_VALUE_PER_LOT = 1.0        # 1 lotto = 1 € per pip → 0.01 lotto = 0.01 €/pip
DEFAULT_BALANCE = 1000         # saldo “virtuale” per il calcolo
DEFAULT_RISK_PCT = 1.0         # rischio 1%
TIMEFRAME = "M5"               # timeframe logico dei segnali
AUTO_INTERVAL = 300            # 300 secondi = 5 minuti

# 📜 LOGGING
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
    giorno = datetime.utcnow().weekday()  # 0=lun ... 6=dom

    if giorno == 5 or giorno == 6:
        return "chiuso"

    if giorno == 4 and ora >= time(23, 0):
        return "chiuso"

    if time(0, 0) <= ora <= time(1, 0):
        return "rollover"

    if time(22, 0) <= ora <= time(23, 0):
        return "chiusura"

    if time(0, 0) <= ora <= time(9, 0):
        return "tokyo"
    if time(7, 0) <= ora <= time(16, 0):
        return "londra"
    if time(12, 30) <= ora <= time(21, 0):
        return "newyork"

    return "normale"


def descrizione_sessione(stato: str) -> str:
    if stato == "tokyo":
        return "🇯🇵 Tokyo — movimenti più lenti, spesso in range"
    if stato == "londra":
        return "🇬🇧 Londra — volatilità alta, rottura livelli"
    if stato == "newyork":
        return "🇺🇸 New York — movimenti forti, spike frequenti"
    if stato == "chiusura":
        return "🔚 Mercato in chiusura — volumi bassi"
    if stato == "rollover":
        return "⏰ Rollover — spread alti, dati sporchi"
    if stato == "chiuso":
        return "📉 Mercato chiuso"
    return "📊 Sessione normale"


# =========================
# “SENTIMENT” (finto ma estendibile)
# =========================
def leggi_sentiment():
    """
    Qui in futuro puoi collegare API vere.
    Ora: simulazione semplice.
    """
    scelta = random.choices(
        ["bullish", "bearish", "neutral"],
        weights=[30, 30, 40],
        k=1
    )[0]
    confidence = random.randint(60, 95)  # quanto è “convinto” il bot
    return scelta, confidence


# =========================
# GENERATORE SEGNALI COMPLETO
# =========================
def genera_segnale():
    sentiment, confidence = leggi_sentiment()

    # Direzione influenzata dal sentiment
    if sentiment == "bullish":
        direction = random.choices(["BUY", "SELL"], weights=[80, 20], k=1)[0]
    elif sentiment == "bearish":
        direction = random.choices(["BUY", "SELL"], weights=[20, 80], k=1)[0]
    else:
        direction = random.choice(["BUY", "SELL"])

    # Entry “finta” su EURUSD
    entry = round(random.uniform(1.05000, 1.15000), 5)

    # SL/TP logici: 20 pip di SL, 40 pip di TP
    sl_pips = 20
    tp_pips = 40

    if direction == "BUY":
        sl = round(entry - sl_pips * PIP_SIZE, 5)
        tp = round(entry + tp_pips * PIP_SIZE, 5)
    else:
        sl = round(entry + sl_pips * PIP_SIZE, 5)
        tp = round(entry - tp_pips * PIP_SIZE, 5)

    rr = tp_pips / sl_pips

    # Rischio e size
    rischio_euro = DEFAULT_BALANCE * (DEFAULT_RISK_PCT / 100.0)
    size_lots = rischio_euro / (sl_pips * PIP_VALUE_PER_LOT)

    return {
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
        "timeframe": TIMEFRAME,
    }


# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Benvenuto nel BOT TRADING DEFINITIVO 🔥\n\n"
        f"Timeframe logico: *{TIMEFRAME}* ⏱\n"
        "Size: 0.01 lotto = 0.01 € a pip 💰\n"
        f"Rischio base: *{DEFAULT_RISK_PCT:.1f}%* su *{DEFAULT_BALANCE}€*\n\n"
        "Comandi:\n"
        "• /auto → segnali automatici ogni 5 minuti 📡\n"
        "• /stop → ferma i segnali automatici 🛑\n"
        "• /calc → un segnale singolo, quando lo vuoi tu 🎯\n\n"
        "I segnali sono pensati per coppie tipo EURUSD su M5."
    , parse_mode="Markdown")


# =========================
# /auto (job ogni 5 minuti)
# =========================
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    stato = stato_mercato()

    if stato == "chiuso":
        await context.bot.send_message(chat_id, "📉 Mercato chiuso, nessun segnale ora.")
        return

    if stato == "rollover":
        await context.bot.send_message(chat_id, "⏰ Rollover (00–01 UTC), meglio evitare operazioni.")
        return

    if stato == "chiusura":
        await context.bot.send_message(chat_id, "🔚 Mercato in chiusura, segnali poco affidabili.")
        return

    descr = descrizione_sessione(stato)
    s = genera_segnale()

    testo = (
        "📡 *Segnale AUTO* (M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}*\n\n"
        f"➡️ Entra a: *{s['entry']}*\n"
        f"🛑 Stop Loss: *{s['sl']}*  ({s['sl_pips']} pip)\n"
        f"🎯 Take Profit: *{s['tp']}*  ({s['tp_pips']} pip)\n\n"
        f"💰 Rischio stimato: *{s['rischio']:.2f} €* (~{DEFAULT_RISK_PCT:.1f}% su {DEFAULT_BALANCE}€)\n"
        f"📊 Size consigliata: *{s['size']:.2f} lotti*  (0.01 = 1 cent/pip)\n"
        f"⚖️ Rapporto R:R: *{s['rr']:.2f}*\n\n"
        "📎 Esempio operativo:\n"
        f"• Apri *{s['direction']}* a {s['entry']}\n"
        f"• Metti SL a {s['sl']}\n"
        f"• Metti TP a {s['tp']}\n"
        f"• Usa circa {s['size']:.2f} lotti (0.01 = 1 cent/pip)\n"
    )

    await context.bot.send_message(chat_id, testo, parse_mode="Markdown")


async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # evita doppio auto: prima pulisco eventuali job vecchi per questa chat
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()

    context.job_queue.run_repeating(
        auto_job,
        interval=AUTO_INTERVAL,
        first=1,
        chat_id=chat_id
    )

    await update.message.reply_text(
        "🚀 Auto-previsioni M5 attivate!\n"
        "Riceverai un segnale completo circa ogni 5 minuti.\n"
        "Usa /stop per fermare tutto."
    )


# =========================
# /stop
# =========================
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    count = 0
    for job in context.job_queue.jobs():
        if job.chat_id == chat_id:
            job.schedule_removal()
            count += 1

    if count == 0:
        await update.message.reply_text("ℹ️ Nessun auto-segnale attivo per questa chat.")
    else:
        await update.message.reply_text("🛑 Auto-previsioni fermate per questa chat.")


# =========================
# /calc (segnale singolo “a comando tuo”)
# =========================
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stato = stato_mercato()

    if stato in ["chiuso", "rollover", "chiusura"]:
        descr = descrizione_sessione(stato)
        await update.message.reply_text(
            f"{descr}\n\n"
            "⚠️ In questa fase il segnale sarebbe poco affidabile.\n"
            "Meglio aspettare una sessione più pulita."
        )
        return

    descr = descrizione_sessione(stato)
    s = genera_segnale()

    testo = (
        "🎯 *Segnale MANUALE* (M5)\n"
        f"{descr}\n\n"
        f"🧠 Sentiment: *{s['sentiment']}* ({s['confidence']}%)\n"
        f"📌 Direzione: *{s['direction']}*\n\n"
        f"➡️ Entra a: *{s['entry']}*\n"
        f"🛑 Stop Loss: *{s['sl']}*  ({s['sl_pips']} pip)\n"
        f"🎯 Take Profit: *{s['tp']}*  ({s['tp_pips']} pip)\n\n"
        f"💰 Rischio stimato: *{s['rischio']:.2f} €* (~{DEFAULT_RISK_PCT:.1f}% su {DEFAULT_BALANCE}€)\n"
        f"📊 Size consigliata: *{s['size']:.2f} lotti*  (0.01 = 1 cent/pip)\n"
        f"⚖️ Rapporto R:R: *{s['rr']:.2f}*\n\n"
        "📎 Esempio operativo:\n"
        f"• Apri *{s['direction']}* a {s['entry']}\n"
        f"• Metti SL a {s['sl']}\n"
        f"• Metti TP a {s['tp']}\n"
        f"• Usa circa {s['size']:.2f} lotti (0.01 = 1 cent/pip)\n"
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
