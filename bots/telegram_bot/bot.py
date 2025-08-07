"""
Запуск Telegram-бота для управления дроном.
"""
from handlers import handle_command

def start_bot():
    print("Telegram-бот запущен")
    while True:
        user_input = input("> ")
        response = handle_command(user_input)
        print(response)
