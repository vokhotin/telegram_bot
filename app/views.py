from app import app
from flask import request, abort
from telebot import types, TeleBot
import requests
import json
import urllib.parse
TOKEN = "your bot token here"

bot = TeleBot(TOKEN)

COMMANDS = {"/help": "Справка по командам",
            "/conf": "Работа с confluence. Пример использования:\n\t"
                     " -seminars возвращает список семинаров",
            "/quiz": "Викторина",
            "/quiz2": "Викторина с кастомной клавиатурой",
            "/file": "открывает и выводит содержимое файла",

            "\nВ режиме inline (в поле ввода набрать @SoCall_bot)": "Набрать слово для перевода. Символ '/' означает, что слово набрано для перевода\n"
                                                                    "Пример: @SoCall_bot дом/."}



@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        print(request.get_json())
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)


@bot.message_handler(commands=['help', 'start', 'conf', 'quiz', 'quiz2', 'file'])
def command_handler(message):
    if message.text.split()[0] == '/help' or message.text.split()[0] == '/start':
        send_welcome(message)
    elif message.text.split()[0] == '/conf':
        confluence(message)
    elif message.text.split()[0] == '/quiz':
        quiz_question = "2 + 2 = ?"
        quiz(message, quiz_question)
    elif message.text.split()[0] == '/quiz2':
        quiz2(message)
    elif message.text.split()[0] == '/file':
        show_content(message)


@bot.inline_handler(func=lambda query: len(query.query) is not 0)
def query_text(inline_query):
    if inline_query.query.endswith("/"):
        text_to_translate = inline_query.query[:-1]
        translation = translate(text_to_translate)
        text_button = types.InlineQueryResultArticle('1', translation, types.InputTextMessageContent(translation))
        bot.answer_inline_query(inline_query.id, [text_button])


def translate(text_to_translate: str):
    text_to_translate = urllib.parse.quote_plus(text_to_translate)
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate?" \
          "key=yandex_api_key&" \
          "text={}&" \
          "lang=ru-en".\
        format(text_to_translate)
    result = requests.get(url, verify=False).text
    translation = json.loads(result)['text'][0]
    return translation




@bot.inline_handler(func=lambda query: len(query.query) is 0)
def empty_query(inline_query):
    hint = "Перевод с русского на английский"
    r = types.InlineQueryResultArticle(
        id='1',
        title="Введеный текст может быть автоматически переведен на английский язык",
        description=hint,
        input_message_content=types.InputTextMessageContent(
        message_text="Перевести текст с русского на английский")
    )
    bot.answer_inline_query(inline_query.id, [r])



@bot.callback_query_handler(func=lambda query: True)
def query_handler(query):
    if query.data == '4':
        bot.answer_callback_query(query.id, show_alert=True, text="Верно!")
    else:
        bot.answer_callback_query(query.id, show_alert=True, text="Неверно!")


def show_content(message):
    try:
        file_content = "Содержимое файла 'instruction'\n\n"
        with open("./instruction") as file:
            file_content += file.read()
        bot.reply_to(message, file_content)
    except:
        bot.reply_to(message, "Не удалось открыть файл")


def confluence(message):
    if message.text.split()[1] == "-seminars":
        login, password = 'login', 'password'
        url_seminars = "https://conf.socall.ru/rest/api/content/20319127/child/page"
        responce = requests.get(url_seminars, auth=(login, password)).text
        results = json.loads(responce)['results']
        results.sort(key=lambda r: r['id'])
        seminars = ""
        for index, title in enumerate(results, 1):
            seminars += str(index) + ": " + str(title['title']) + "\n"
        bot.reply_to(message, seminars)
    else:
        bot.reply_to(message, "Команда введена неверно")


def send_welcome(message):
    help_message = "Для работы с ботом используйте следующие команды\n"
    for key, value in COMMANDS.items():
        help_message += key + ": " + value + "\n"
    bot.reply_to(message, help_message)


def quiz(message, quiz_question):
    keyboard = types.InlineKeyboardMarkup()

    answers = [types.InlineKeyboardButton(text="Надо погуглить",
                                          url="https://www.google.ru"),
               types.InlineKeyboardButton(text="4", callback_data="4"),
               types.InlineKeyboardButton(text="i", callback_data="i"),
               types.InlineKeyboardButton(text="5", callback_data="5")]
    for answer in answers:
        keyboard.add(answer)
    bot.send_message(message.chat.id, quiz_question, reply_markup=keyboard)


def quiz2(message):
    pass
