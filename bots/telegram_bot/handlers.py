"""
Обработка команд, получаемых Telegram-ботом.
"""
def handle_command(command):
    if command.lower() == "старт":
        return "Бот активирован."
    elif command.lower() == "статус":
        return "Все дроны в порядке."
    else:
        return "Неизвестная команда."
