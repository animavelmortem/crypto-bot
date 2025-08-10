from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

ASK_DEPOSIT, ASK_AGE, ASK_EXPERIENCE, ASK_GOAL = range(4)

ADMIN_ID = 7427253214
ADMIN_USERNAME = "Trading_Radar_Admin"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Заполнить анкету", callback_data='start_survey')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем стартовое сообщение с кнопкой
    await update.message.reply_text(
        "🚀 Добро пожаловать в мир крипты и трейдинга!\n\n"
        "Для начала заполните анкету, чтобы я лучше понимал вашу ситуацию.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'start_survey':
        # Удаляем стартовое сообщение с кнопкой
        await query.message.delete()

        # Запускаем опрос - первый вопрос
        await query.message.chat.send_message("💬 Для начала — расскажи, какой у тебя депозит для торговли?")
        return ASK_DEPOSIT

async def ask_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['deposit'] = update.message.text
    await update.message.reply_text("📅 Сколько тебе лет?")
    return ASK_AGE

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("📈 Как давно интересуешься трейдингом?")
    return ASK_EXPERIENCE

async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text
    await update.message.reply_text("🎯 Какая у тебя цель в трейдинге?")
    return ASK_GOAL

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['goal'] = update.message.text

    profile = (
        f"📌 Новый клиент!\n"
        f"👤 Имя: {update.message.from_user.full_name}\n"
        f"🆔 @{update.message.from_user.username}\n"
        f"💰 Депозит: {context.user_data['deposit']}\n"
        f"📅 Возраст: {context.user_data['age']}\n"
        f"📈 Опыт: {context.user_data['experience']}\n"
        f"🎯 Цель: {context.user_data['goal']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=profile)

    # Показываем главное меню с кнопками
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url="https://t.me/+LjoBlLMpuIkzMDdi")],
        [InlineKeyboardButton("💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Спасибо! Я получил твою анкету и скоро свяжусь с тобой лично.\n"
        "Выбери, что хочешь сделать дальше:",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Анкета отменена.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("8038864177:AAETdG9oyMVnfsIAXobEdIO69JL0Nd75UIM").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern='start_survey')],
        states={
            ASK_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_deposit)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            ASK_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
