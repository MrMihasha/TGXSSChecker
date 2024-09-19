### SecureWeb Robot by mihasha ###
 
import telebot
import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import time

API_TOKEN = 'YOUR_BOT_TOKEN' 

bot = telebot.TeleBot(API_TOKEN)

headers = {
    "User-Agent: Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QPP6.190730.005) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36"
}


message_ids = {}

def scan_xss(url, stop_time, timeout):
    stop_time = time.time() + stop_time
    result = ""

    try:
        html = requests.get(url, headers=headers, timeout=timeout)
        soup = bs(html.content, "html.parser")
        forms = soup.find_all("form")
        js_script = "<Script>alert('XSS')</scripT>"

        for form in forms:
            if time.time() > stop_time:
                break
            details = {}
            action = form.attrs.get("action")
            method = form.attrs.get("method", "get")

            if action and not action.startswith("javascript"):
                action = action.lower()
                method = method.lower()
            else:
                continue

            inputs = []
            for input_tag in form.find_all("input"):
                input_type = input_tag.attrs.get("type", "text")
                input_name = input_tag.attrs.get("name")
                inputs.append({"type": input_type, "name": input_name})
            details["action"] = action
            details["method"] = method
            details["inputs"] = inputs
            form_details = details
            target_url = urljoin(url, form_details["action"])
            inputs = form_details["inputs"]
            data = {}

            for input in inputs:
                if input["type"] == "text" or input["type"] == "search":
                    input["value"] = js_script
                input_name = input.get("name")
                input_value = input.get("value")
                if input_name and input_value:
                    data[input_name] = input_value

            if form_details["method"] == "post":
                content = requests.post(target_url, data=data, headers=headers, timeout=timeout).content.decode('latin-1')
            else:
                content = requests.get(target_url, params=data, headers=headers, timeout=timeout).content.decode('latin-1')

            if js_script in content:
                result += f"🚨 XSS Detected on {url}\n👀 Form details:\n{details}\n"
                break

    except Exception as e:
        result += f"Error occurred: {str(e)}\n"

    return result

def main_menu_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton("About ℹ️", callback_data="about_bot")
    btn2 = telebot.types.InlineKeyboardButton("Check for XSS vulnerability ⛔️", callback_data="check_xss")
    markup.add(btn1, btn2)
    return markup

def back_button_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    back_btn = telebot.types.InlineKeyboardButton("Back ↩️", callback_data="back_to_menu")
    markup.add(back_btn)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global message_ids
    markup = main_menu_markup()
    msg = bot.reply_to(message, "👋 Hi! I'm a bot for checking XSS vulnerabilities. Please choose an option below:", reply_markup=markup)
    message_ids[message.chat.id] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data == "about_bot")
def bot_info(call):
    info = "This bot is created for checking XSS vulnerabilities."
    try:
        if message_ids.get(call.message.chat.id):
            bot.edit_message_text(text=info, chat_id=call.message.chat.id, message_id=message_ids.get(call.message.chat.id), reply_markup=back_button_markup())
    except Exception as e:
        print(f"Error: {e}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_xss")
def ask_for_url(call):
    try:
        if message_ids.get(call.message.chat.id):
            bot.edit_message_text(text="🔗 Please send the URL of the site for checking:", chat_id=call.message.chat.id, message_id=message_ids.get(call.message.chat.id), reply_markup=back_button_markup())
    except Exception as e:
        print(f"Error while editing the message.{e}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    try:
        if message_ids.get(call.message.chat.id):
            bot.edit_message_text(text="👋 Hi! I'm a bot for checking XSS vulnerabilities. Please choose an option below:", chat_id=call.message.chat.id, message_id=message_ids.get(call.message.chat.id), reply_markup=main_menu_markup())
    except Exception as e:
        print(f"Error while editing the message. {e}")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def check_url(message):
    url = message.text
    result = scan_xss(url, 180, 20)
    try:
        if result:
            msg = bot.reply_to(message, f"🛜 Result:\n{result}", reply_markup=back_button_markup())
        else:
            msg = bot.reply_to(message, "✅ No XSS vulnerabilities detected.", reply_markup=back_button_markup())
        

        message_ids[message.chat.id] = msg.message_id
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
