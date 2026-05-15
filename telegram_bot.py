import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Importa le funzioni dal tuo agente esistente
from news_agent import cerca_notizie, analizza_notizie_con_claude

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN").strip()

# Log per debug
logging.basicConfig(level=logging.INFO)

# Comando /start — messaggio di benvenuto
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Ciao! Sono il tuo agente notizie personale.\n\n"
        "Dimmi su cosa vuoi essere aggiornato e cerco subito le ultime notizie!\n\n"
        "Esempi:\n"
        "• Politica italiana\n"
        "• Bitcoin e crypto\n"
        "• Intelligenza artificiale\n"
        "• Serie A"
    )

# Risponde ai messaggi normali
async def gestisci_messaggio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    argomento = update.message.text
    
    # Manda un messaggio di attesa
    await update.message.reply_text(f"🔍 Cerco notizie su '{argomento}'...\nUn momento!")
    
    try:
        # Cerca le notizie
        notizie = cerca_notizie(argomento, quante=5)
        
        if not notizie:
            await update.message.reply_text("😕 Nessuna notizia trovata. Prova con parole diverse!")
            return
        
        await update.message.reply_text("🧠 Claude sta analizzando...")
        
        # Claude analizza
        analisi = analizza_notizie_con_claude(notizie, argomento)
        
        # Manda il briefing
        await update.message.reply_text(
            f"📋 *BRIEFING: {argomento.upper()}*\n\n{analisi}",
            parse_mode="Markdown"
        )
        
        # Manda le fonti
        fonti = "\n".join([f"• [{n['titolo'][:50]}...]({n['url']})" for n in notizie[:3]])
        await update.message.reply_text(
            f"📎 *Fonti:*\n{fonti}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore: {str(e)}\nRiprova tra poco!")

# Avvia il bot
def main():
    print("🤖 Bot avviato! Scrivi su Telegram.")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestisci_messaggio))
    app.run_polling()

if __name__ == "__main__":
    main()