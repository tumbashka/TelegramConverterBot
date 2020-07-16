import requests
import telebot
import xmltodict
from telebot import types
import config

bot = telebot.TeleBot(config.Token)

country_dict = dict()
count = -1
valutes_str = ""
in_valute = ""
out_valute = ""


@bot.message_handler(commands=['start', 'help'])
def bot_phrases(message):
    bot_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    button_reset = types.KeyboardButton('Сброс')
    bot_markup.add(button_reset)
    if in_valute == "":
        get_valutes(message)
        sms = bot.send_message(message.chat.id,
                               "Выберите валюту из которой конвертируем:", reply_markup=bot_markup)
    elif out_valute == "":
        get_valutes(message)
        sms = bot.send_message(message.chat.id,
                               "Выберите валюту в которую конвертируем:", reply_markup=bot_markup)
    elif (count == -1):
        sms = bot.send_message(message.chat.id,
                               "Введите количество конвертируемой валюты:", reply_markup=bot_markup)
    else:
        sms = bot.send_message(message.chat.id,
                               "Чтобы продолжить, используйте /reset", reply_markup=bot_markup)

    bot.register_next_step_handler(sms, process_select_step)


# Проверка на число
def is_digit(string):
    if string.isdigit():
        return True
    else:
        try:
            float(string)
            return True
        except ValueError:
            return False


def process_select_step(req):
    global country_dict, valutes_str, in_valute, out_valute, count
    if req.text in country_dict:
        choose_valute(req.text)
        bot_phrases(req)
    elif is_digit(req.text) and (out_valute != ""):  # если это число и обе валюты выбраны, то считаем
        calculate(req)
    elif (req.text == 'Сброс') or (req.text == '/reset'):
        country_dict = dict()
        valutes_str = ""
        in_valute = ""
        out_valute = ""
        count = -1
        bot_phrases(req)
    elif req.text == "/start" or req.text == "/help":
        bot_phrases(req)
    else:
        bot.send_message(req.chat.id, "Команда не распознана\n")
        bot_phrases(req)


# Расчет курса
def calculate(message):
    global country_dict, in_valute, out_valute, count
    first_value = float(country_dict[in_valute][0])
    first_nominal = float(country_dict[in_valute][1])
    second_value = float(country_dict[out_valute][0])
    second_nominal = float(country_dict[out_valute][1])
    count = float(message.text)
    out_value = (first_value / first_nominal) / (second_value / second_nominal) * count
    string = ('{:.1f} {} равно по стоимости {:.1f} {}'.format(count, in_valute, out_value, out_valute))
    bot.send_message(message.chat.id, string)
    bot_phrases(message)


# Запоминамем валюты
def choose_valute(valute):
    global in_valute, out_valute
    if in_valute == "":
        in_valute = valute

    elif out_valute == "":
        out_valute = valute


# Выводим список валют
def get_valutes(message):
    global country_dict, valutes_str
    if len(country_dict) != 0:
        bot.send_message(message.chat.id, valutes_str)
        return

    url = "https://www.cbr-xml-daily.ru/daily.xml"
    rec = requests.get(url)
    data = xmltodict.parse(rec.text)

    for item in data['ValCurs']['Valute']:
        country_dict["/" + item['CharCode']] = [item['Value'].replace(",", "."), item['Nominal']]

    country_dict["/RUB"] = [1,1]

    country_list = list(country_dict.keys())
    country_list.sort()

    for item in country_list:
        valutes_str += (item + '\n')

    bot.send_message(message.chat.id, valutes_str)


if __name__ == '__main__':
    bot.polling(none_stop=True)
