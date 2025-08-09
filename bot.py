from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url="https://t.me/+LjoBlLMpuIkzMDdi")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚀 Добро пожаловать в мир крипты и трейдинга!\n"
        "Здесь ты получишь ценные знания, эксклюзивные обучающие материалы и вскоре — лучшие сигналы для торговли.\n\n"
        "Чтобы не пропустить важные обновления и всегда быть на шаг впереди, подпишись на наш канал!\n\n"
        "Жми на кнопку ниже и присоединяйся к крипто-элите! 💎🔥",
        reply_markup=reply_markup
    )

def main():
    app = ApplicationBuilder().token("8038864177:AAETdG9oyMVnfsIAXobEdIO69JL0Nd75UIM").build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == '__main__':
    main()
