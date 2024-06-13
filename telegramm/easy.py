from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import config  # Загружаем конфигурационный файл с токеном


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Увеличить", callback_data='increment')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Нажмите кнопку, чтобы увеличить счетчик:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if 'counter' not in context.bot_data:
        context.bot_data['counter'] = 0
    context.bot_data['counter'] += 1
    query.edit_message_text(text=f"Счетчик: {context.bot_data['counter']}")


def main():
    # Создание объекта Updater
    updater = Updater(token=config.TOKEN)

    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд и коллбэков
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Начало поиска новых сообщений
    updater.start_polling()

    # Запуск бота до прерывания (Ctrl+C)
    updater.idle()


if __name__ == '__main__':
    main()
