from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import _token  # Импортируем файл конфигурации
from telegram.ext import Updater
from telegram import Bot
import asyncio


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Увеличить", callback_data='increment')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Нажмите кнопку, чтобы увеличить счетчик:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    # Добавляем логику увеличения счетчика
    if 'counter' not in context.bot_data:
        context.bot_data['counter'] = 0
    context.bot_data['counter'] += 1
    query.edit_message_text(text=f"Счетчик: {context.bot_data['counter']}")


def main():
    # Используем токен из файла config
    bot = Bot(token=_token.TOKEN)  # Создаем объект Bot
    update_queue = asyncio.Queue()  # Создаем очередь для обновлений

    updater = Updater(bot=bot, update_queue=update_queue)


    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
