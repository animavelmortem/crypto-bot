from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ChatJoinRequestHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import logging
import asyncio
import os
import json

# Состояния анкеты
ASK_DEPOSIT, ASK_AGE, ASK_EXPERIENCE, ASK_BIRGE, ASK_TRADE_EXP, CONFIRM = range(6)

# Настройки
ADMIN_ID = 7427253214
ADMIN_USERNAME = "Trading_Radar_Admin"
CHANNEL_ID = '-1002409235086'
SPREADSHEET_ID = '1fiVru2r6gAo5i8xiPTG7-RnvG43K4H5zevlk53MqjQs' # ID твоей таблицы
CHANNEL_LINK = 'https://t.me/+LjoBlLMpuIkzMDdi' # Новая переменная для ссылки

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials_json_string = os.environ.get("GOOGLE_CREDENTIALS")
if credentials_json_string:
    try:
        credentials_json = json.loads(credentials_json_string)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        logger.error(f"Ошибка чтения ключей Google Sheets из переменных окружения: {e}")
        client = None
else:
    logger.error("Переменная окружения GOOGLE_CREDENTIALS не найдена.")
    client = None

# Хранилище для проверки уникальности
existing_users = set()

async def load_existing_users():
    if not client:
        logger.error("Google Sheets клиент не инициализирован. Пропускаем загрузку пользователей.")
        return
    try:
        records = sheet.get_all_values()
        for row in records[1:]:
            existing_users.add(row[0])
    except Exception as e:
        logger.error(f"Ошибка загрузки из Google Sheets: {e}")

# Проверка подписки
async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# НОВАЯ ФУНКЦИЯ ДЛЯ ПРИНЯТИЯ ЗАЯВОК НА ВСТУПЛЕНИЕ
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Автоматически одобряет заявки на вступление в канал."""
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat

    await context.bot.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
    logger.info(f"Заявка на вступление от пользователя {user.full_name} (@{user.username}) в канал {chat.title} одобрена.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    await load_existing_users()

    # Проверка, заполнял ли пользователь анкету
    if user_id in existing_users:
        keyboard = [
            [InlineKeyboardButton("📝 Изменить анкету", callback_data='edit_survey')],
            [InlineKeyboardButton("💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Вы уже заполняли анкету. Хотите изменить данные или связаться с админом?",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Проверка подписки
    checking_message = await update.message.reply_text("🔍 Проверяю подписку...")
    await asyncio.sleep(1)
    if await check_subscription(context, update.message.from_user.id):
        await checking_message.delete()
        keyboard = [
            [InlineKeyboardButton("📝 Заполнить анкету", callback_data='start_survey')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚀 Добро пожаловать в мир крипты и трейдинга!\n\n"
            "Для начала заполните анкету, чтобы я лучше понимал вашу ситуацию.",
            reply_markup=reply_markup
        )
    else:
        await checking_message.delete()
        keyboard = [
            [InlineKeyboardButton("📌 Подписаться на канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Проверить подписку", callback_data='check_subscription')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚫 Сначала подпишитесь на канал, чтобы продолжить.",
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    if query.data == 'check_subscription':
        checking_message = await query.message.reply_text("🔍 Проверяю подписку...")
        await asyncio.sleep(1)
        if await check_subscription(context, query.from_user.id):
            await checking_message.delete()
            await query.message.reply_text("💬 Вопрос 1/5: Какой у тебя депозит для торговли? (Введите число, например, 1000 USD)")
            return ASK_DEPOSIT
        else:
            await checking_message.delete()
            keyboard = [
                [InlineKeyboardButton("📌 Подписаться на канал", url=CHANNEL_LINK)],
                [InlineKeyboardButton("🔄 Проверить подписку", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("🚫 Вы не подписаны. Подпишитесь и попробуйте снова.", reply_markup=reply_markup)

    elif query.data in ['start_survey', 'edit_survey']:
        await load_existing_users()
        if query.data == 'start_survey' and user_id in existing_users:
            keyboard = [
                [InlineKeyboardButton("📝 Изменить анкету", callback_data='edit_survey')],
                [InlineKeyboardButton("💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Вы уже заполняли анкету. Хотите изменить данные или связаться с админом?",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        await query.message.delete()
        await query.message.chat.send_message("💬 Вопрос 1/5: Какой у тебя депозит для торговли? (Введите число, например, 1000 USD)")
        return ASK_DEPOSIT

    elif query.data == 'confirm_data':
        await save_data(update, context, user_id, query.from_user)
        keyboard = [
            [InlineKeyboardButton("📌 Подписаться на канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton("💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "✅ Спасибо! Я получил твою анкету и скоро свяжусь с тобой лично.\n"
            "Выбери, что хочешь сделать дальше:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    elif query.data == 'edit_data':
        await query.message.delete()
        await query.message.chat.send_message("💬 Вопрос 1/5: Какой у тебя депозит для торговли? (Введите число, например, 1000 USD)")
        return ASK_DEPOSIT

async def ask_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        deposit = float(''.join(c for c in text if c.isdigit() or c == '.'))
        if deposit <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Пожалуйста, введите положительную сумму (например, 1000 или 500 USD).")
        return ASK_DEPOSIT

    context.user_data['deposit'] = text
    await update.message.reply_text("📅 Вопрос 2/5: Сколько тебе лет? (Введите число, например, 25)")
    return ASK_AGE

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 18:
        await update.message.reply_text("⚠️ Пожалуйста, введите возраст числом (не менее 18 лет).")
        return ASK_AGE

    context.user_data['age'] = text
    await update.message.reply_text("📈 Вопрос 3/5: Как давно интересуешься трейдингом?")
    return ASK_EXPERIENCE

async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text
    await update.message.reply_text("🏦 Вопрос 4/5: На какой бирже собираешься торговать? (Например, Binance, Bybit)")
    return ASK_BIRGE

async def ask_birge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['birge'] = update.message.text
    await update.message.reply_text("💹 Вопрос 5/5: Какой у тебя опыт в торговле? (Например, 'Торговал 1 год на Binance' или 'Новичок')")
    return ASK_TRADE_EXP

async def ask_trade_exp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['trade_exp'] = update.message.text

    # Подтверждение данных
    profile = (
        f"📌 Пожалуйста, проверь свои данные:\n"
        f"👤 Имя: {update.message.from_user.full_name}\n"
        f"🆔 @{update.message.from_user.username or 'unknown'}\n"
        f"💰 Депозит: {context.user_data['deposit']}\n"
        f"📅 Возраст: {context.user_data['age']}\n"
        f"📈 Интерес к трейдингу: {context.user_data['experience']}\n"
        f"🏦 Биржа: {context.user_data['birge']}\n"
        f"💹 Опыт торговли: {context.user_data['trade_exp']}"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Верно", callback_data='confirm_data')],
        [InlineKeyboardButton("✏️ Исправить", callback_data='edit_data')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(profile, reply_markup=reply_markup)
    return CONFIRM

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, user):
    profile = (
        f"📌 Новый клиент!\n"
        f"👤 Имя: {user.full_name}\n"
        f"🆔 @{user.username or 'unknown'}\n"
        f"💰 Депозит: {context.user_data['deposit']}\n"
        f"📅 Возраст: {context.user_data['age']}\n"
        f"📈 Интерес к трейдингу: {context.user_data['experience']}\n"
        f"🏦 Биржа: {context.user_data['birge']}\n"
        f"💹 Опыт торговли: {context.user_data['trade_exp']}"
    )

    # Отправка админу
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=profile)
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")

    # Сохранение в Google Sheets
    if not client:
        logger.error("Google Sheets клиент не инициализирован. Пропускаем сохранение.")
        return
    try:
        # Если пользователь уже есть, обновляем его строку
        records = sheet.get_all_values()
        for i, row in enumerate(records[1:], 2):
            if row[0] == user_id:
                sheet.update(f'A{i}:G{i}', [[
                    user_id,
                    user.username or 'unknown',
                    context.user_data['deposit'],
                    context.user_data['age'],
                    context.user_data['experience'],
                    context.user_data['birge'],
                    context.user_data['trade_exp']
                ]])
                break
        else:
            # Если новый пользователь, добавляем новую строку
            sheet.append_row([
                user_id,
                user.username or 'unknown',
                context.user_data['deposit'],
                context.user_data['age'],
                context.user_data['experience'],
                context.user_data['birge'],
                context.user_data['trade_exp']
            ])
            existing_users.add(user_id)
    except Exception as e:
        logger.error(f"Ошибка сохранения в Google Sheets: {e}")

    # Сохранение в CSV
    try:
        with open('users.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                user_id,
                user.username or 'unknown',
                context.user_data['deposit'],
                context.user_data['age'],
                context.user_data['experience'],
                context.user_data['birge'],
                context.user_data['trade_exp']
            ])
    except Exception as e:
        logger.error(f"Ошибка сохранения в CSV: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Анкета отменена.")
    return ConversationHandler.END

def main():
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Переменная окружения 'TELEGRAM_TOKEN' не установлена.")

    app = ApplicationBuilder().token(bot_token).build()

    # Обработчик заявок на вступление в канал
    app.add_handler(ChatJoinRequestHandler(callback=handle_join_request))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(button_handler, pattern='start_survey|check_subscription|edit_survey|confirm_data|edit_data')],
        states={
            ASK_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_deposit)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            ASK_BIRGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_birge)],
            ASK_TRADE_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_trade_exp)],
            CONFIRM: [CallbackQueryHandler(button_handler, pattern='confirm_data|edit_data')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
