#
# UNUSED
#

import telebot
from telebot import types
from datetime import datetime
from datetime import timedelta
import re
import props
import multiprocessing

token = props.token
bots_chat_id = props.bots_chat_id


class AlarmBotFrontEnd:
    current_state = ''
    alarms = []
    alarm_buffer = ''
    states = ['root',
              'alarms_list', 'alarms_create', 'alarms_delete', 'delete_confirm', 'create_confirm',
              'dawn_settings']
    bot = None
    queue = None

    def __init__(self, q: multiprocessing.Queue):
        self.current_state = 'root'
        self.bot = telebot.TeleBot(token)
        self.queue = q

        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.current_state = 'root'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("👋 Поздороваться")
            markup.add(btn1)
            self.bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-помошник!", reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            if self.current_state == 'root':
                self.root_handler(message)
            elif self.current_state == 'alarms_list':
                self.alarm_list_handler(message)
            elif self.current_state == 'alarms_delete':
                self.alarms_delete_handler(message)
            elif self.current_state == 'delete_confirm':
                self.delete_confirm_handler(message)
            elif self.current_state == 'alarms_create':
                self.alarms_create_handler(message)
            elif self.current_state == 'create_confirm':
                self.create_confirm_handler(message)
            else:
                print("unknown state")

        self.bot.polling(none_stop=True, interval=0)

    def get_alarms(self):
        self.bot.send_message(bots_chat_id, "alarmbot: alarms_get_all")
        while self.queue.empty():
            pass
        while not self.queue.empty():
            print(self.queue.get())

    def unknown_command_err_msg(self, message):
        self.bot.send_message(message.from_user.id, 'неизвестная команда', parse_mode='Markdown')

    def root_menu(self, message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
        btn1 = types.KeyboardButton('Будильники')
        btn2 = types.KeyboardButton('Настройки рассвета')
        markup.add(btn1, btn2)
        self.bot.send_message(message.from_user.id, 'Чего❓', reply_markup=markup)  # ответ бота

    def alarm_list_menu(self, message):
        alarms_list = self.get_alarms()
        if not isinstance(alarms_list, list):
            alarms_list = ['1', '2', '3']
        breaker = '\n'
        answer = breaker.join(alarms_list)
        btn1 = types.KeyboardButton('Добавить будильник')
        btn2 = types.KeyboardButton('Удалить будильник')
        button_back = types.KeyboardButton('Назад')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
        markup.add(btn1, btn2, button_back)
        self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

    def delete_menu(self, message):
        alarms_list = self.get_alarms()
        buttons = []
        for idx, alarm in enumerate(alarms_list):
            buttons.append(types.KeyboardButton(str(idx + 1) + ". " + str(alarm)))
        answer = 'Выберите будильник, который необходимо удалить'
        button_back = types.KeyboardButton('Назад')
        buttons.append(button_back)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*buttons)
        self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

    def create_menu(self, message):
        msg = 'Введите дату и время в формате:\n- dd.mm.yy hh:mm\n- hh:mm на ближайший день'
        button_back = types.KeyboardButton('Назад')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(button_back)
        self.bot.send_message(message.from_user.id, msg, reply_markup=markup)

    def root_handler(self, message):
        if message.text == '👋 Поздороваться':
            self.root_menu(message)

        elif message.text == 'Будильники':
            self.current_state = 'alarms_list'
            self.alarm_list_menu(message)

        elif message.text == 'Настройки рассвета':
            self.bot.send_message(message.from_user.id,
                                  'Прочитать правила сайта вы можете по ' + '[ссылке](https://habr.com/ru/docs/help/rules/)',
                                  parse_mode='Markdown')

        elif message.text == 'Выход':
            self.bot.send_message(message.from_user.id,
                                  'Подробно про советы по оформлению публикаций прочитать по ' + '[ссылке](https://habr.com/ru/docs/companies/design/)',
                                  parse_mode='Markdown')
        else:
            self.unknown_command_err_msg(message)

    def alarms_delete_handler(self, message):
        if message.text == 'Назад':
            self.current_state = 'alarms_list'
            self.alarm_list_menu(message)
        elif not re.match("\d*\. (\d{2})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})", message.text):
            self.unknown_command_err_msg(message)
        else:
            self.current_state = 'delete_confirm'
            alarm_id = int(str(message.text).split('.')[0]) - 1
            btn1 = types.KeyboardButton('Да')
            btn2 = types.KeyboardButton('Нет')
            button_back = types.KeyboardButton('Назад')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(btn1, btn2, button_back)
            self.alarm_buffer = self.get_alarms()[alarm_id]
            self.bot.send_message(message.from_user.id, f'Будет удален будилльник \'{self.alarm_buffer}\'',
                                  reply_markup=markup)

    def delete_confirm_handler(self, message):
        if message.text == 'Да':
            self.current_state = 'alarms_list'
            self.alarms.remove(self.alarm_buffer)
            self.alarm_list_menu(message)
        elif message.text == 'Нет':
            self.current_state = 'alarms_delete'
            self.delete_menu(message)
        elif message.text == 'Назад':
            self.current_state = 'alarms_list'
            self.alarm_list_menu(message)
        else:
            self.unknown_command_err_msg(message)

    def get_date_time_string(self, message):
        if re.match("(\d{2})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})", message):
            try:
                date = datetime.strptime(message, "%d.%m.%y %H:%M")
                if date < datetime.now():
                    date = date + timedelta(days=1)
                return date.strftime("%d.%m.%y %H:%M")
            except ValueError:
                return 'bad'
        else:
            try:
                date = datetime.strptime(message, "%H:%M")
                if date.time() < datetime.now().time():
                    today = date.today()
                    fdate = today.replace(hour=date.hour, minute=date.minute)
                    fdate = fdate + timedelta(days=1)
                    return fdate.strftime("%d.%m.%y %H:%M")
                return date.strftime("%d.%m.%y %H:%M")
            except ValueError:
                return 'bad'

    def alarms_create_handler(self, message):
        if message.text == 'Назад':
            self.current_state = 'alarms_list'
            self.alarm_list_menu(message)
        elif (not re.match("(\d{2})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})", message.text)) and (
                not re.match("(\d{2}):(\d{2})", message.text)):
            self.unknown_command_err_msg(message)
        else:
            self.alarm_buffer = self.get_date_time_string(message.text)
            if self.alarm_buffer == 'bad':
                self.unknown_command_err_msg(message)
            else:
                self.current_state = 'create_confirm'
                btn1 = types.KeyboardButton('Да')
                btn2 = types.KeyboardButton('Нет')
                button_back = types.KeyboardButton('Назад')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(btn1, btn2, button_back)
                self.bot.send_message(message.from_user.id,
                                      f'Будет добавлен новый будилльник \'{self.alarm_buffer}\'',
                                      reply_markup=markup)

    def create_confirm_handler(self, message):
        if message.text == 'Да':
            self.current_state = 'alarms_list'
            self.alarms.append(self.alarm_buffer)
            self.alarm_list_menu(message)
        elif message.text == 'Нет':
            self.current_state = 'alarms_create'
            self.create_menu(message)
        elif message.text == 'Назад':
            self.current_state = 'alarms_list'
            self.alarm_list_menu(message)
        else:
            self.unknown_command_err_msg(message)

    def alarm_list_handler(self, message):
        if message.text == 'Добавить будильник':
            self.current_state = 'alarms_create'
            self.create_menu(message)

        elif message.text == 'Удалить будильник':
            self.current_state = 'alarms_delete'
            self.delete_menu(message)

        elif message.text == 'Назад':
            self.current_state = 'root'
            self.root_menu(message)

        else:
            self.unknown_command_err_msg(message)
