import random
import requests
import urllib.parse
import telebot
from telebot import types
from bs4 import BeautifulSoup

bot = telebot.TeleBot("YOUR_TOKEN")
all_users = {}

size_list = ["large", "medium", ""]

markup = types.InlineKeyboardMarkup()
button1 = telebot.types.InlineKeyboardButton(text='More photos like this!', callback_data="buttonmore")
markup.add(button1)

def mistake(message):
    bot.send_message(chat_id=message.from_user.id,
                     text="Wrong prompt, here are some right prompts examples:\n"
                          "/search beautiful mid journey arts|site=example.com|size=large\n"
                          "/search wide view of megalopolis|site=example.com|\n"
                          "/search insane 3d works|size=random\n"
                          "Note that size needs to be entered last and main prompt needs to be entered first. "
                          "Else u will get an error or not right result")

@bot.message_handler(commands=["search"])
def search(message):
    if message.text != "/search":
        try:
            pr = message.text[8:message.text.index("|")]
            text = message.text[message.text.index("|") + 6:]
            if "site=" in message.text:
                site = text[:text.index("|")]
                try:
                    text = text[text.index("|") + 6:]
                except Exception:
                    pass
            else:
                site = ""

            if "size=" in message.text:
                size = text.replace("random", random.choice(size_list))
            else:
                size = ""

            main_url = f"https://yandex.ru/images/search?text={pr}&site={site}&isize={size}"
            response = requests.get(main_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            img1 = str(soup.select('.serp-item__link'))

            print(soup)
            if "captcha" in str(soup):
                bot.send_message(chat_id=message.chat.id, text="Seems like we got a captcha. Try to use "
                                                               "Buttons of previous photo to get more images")
                return
            if len(img1) == 2:
                bot.send_message(chat_id=message.chat.id, text="Got no images. Try to enter another prompt, please")
                return

            all_users[message.chat.id] = {'prompt': message.text, 'main_url': main_url, 'links': []}
            while True:
                try:
                    img1 = img1[img1.index("img_url=") + 8:]
                    link = img1[:img1.index('&')]
                    link_final = urllib.parse.unquote(link).replace('\n', "")
                    all_users[message.chat.id]['links'].append(link_final)
                except ValueError:
                    break
            bot.send_photo(chat_id=message.chat.id,
                           photo=all_users[message.chat.id]['links'].pop(),
                           reply_markup=markup)

        except Exception as e:
            e = str(e)
            if "Bad Request" in e:
                bot.send_message(chat_id=message.chat.id,
                                 text="Invalid link. Just press button one more time")
            else:
                bot.send_message(chat_id=message.chat.id,
                                 text="Got an error, try again, please. Error text:\n"
                                      f"{e}")
    else:
        mistake(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        id = call.message.chat.id
        if call.data == "buttonmore":
            if len(all_users[id]['links']) != 0:
                bot.send_photo(chat_id=id,
                               photo=all_users[id]['links'].pop(),
                               reply_markup=markup)
            else:
                bot.send_message(chat_id=call.message.chat.id,
                                     text=f"Search again to get more. Your last command:"
                                          f"\n{all_users[id]['prompt']}\n\n"
                                          f'<a href="{all_users[id]["main_url"]}">All Results</a>',
                                     parse_mode='HTML')
    except Exception as e:
        e = str(e)
        if str(call.message.chat.id) == e:
            bot.send_message(chat_id=call.message.chat.id,
                             text="Seems like there are no images in storage. Please, /search")
        elif "Bad Request" in e:
            bot.send_message(chat_id=call.message.chat.id,
                             text="Invalid link. Just press button one more time")
        else:
            bot.send_message(chat_id=call.message.chat.id,
                             text="Got an error, try again, please. Error text:\n"
                                  f"{e}")

bot.polling()
