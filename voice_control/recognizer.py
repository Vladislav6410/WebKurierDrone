"""
Модуль голосового распознавания команд для управления дроном.
Поддерживает несколько языков: ru, en, de, pl.
Работает с предварительно настроенным словарём команд.
"""

import speech_recognition as sr
import json
import os

# Загрузка команд
def load_commands(lang='en'):
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'voice_commands.json')
    with open(path, 'r', encoding='utf-8') as f:
        all_commands = json.load(f)
    return all_commands.get(lang, {})

class VoiceRecognizer:
    def __init__(self, lang='en'):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.commands = load_commands(lang)

    def listen_and_recognize(self):
        with sr.Microphone() as source:
            print(f"Слушаю... ({self.lang})")
            audio = self.recognizer.listen(source)

        try:
            result = self.recognizer.recognize_google(audio, language=self.lang)
            print(f"Распознано: {result}")
            return self._interpret_command(result)
        except sr.UnknownValueError:
            return "Команда не распознана."
        except sr.RequestError:
            return "Ошибка подключения к сервису распознавания."

    def _interpret_command(self, phrase):
        for key, keywords in self.commands.items():
            if phrase.lower() in keywords:
                return f"Команда распознана: {key}"
        return "Команда не распознана в словаре."

# Пример использования
if __name__ == "__main__":
    vr = VoiceRecognizer(lang='ru')  # можно 'de', 'pl', 'en'
    print(vr.listen_and_recognize())
