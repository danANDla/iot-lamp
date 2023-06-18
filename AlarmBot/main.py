import telebot
from telebot import types
from datetime import datetime
import re
import props
from enum import Enum
from mqttClient import MqttClient
from mqttClient import MqttClientState

token = props.token
bots_chat_id = props.bots_chat_id


class AlarmBotState(Enum):
    root = 1
    alarms_list = 2
    alarms_pick_edit = 3
    alarms_edit = 4
    alarms_toggle = 5


class AlarmBot:
    current_state = AlarmBotState.root
    alarms = [
        600,
        600,
        600,
        600,
        600,
        600,
        600
    ]
    alarms_states = [
        0,
        0,
        0,
        0,
        0,
        0,
        0
    ]

    alarm_buffer = ''
    picked = -1
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']

    bot = None
    mqtt = None

    def __init__(self):
        self.current_state = 'root'
        self.bot = telebot.TeleBot(token)

        self.mqtt = MqttClient()
        self.mqtt.init()

        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.current_state = AlarmBotState.root
            self.root_menu(message)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            if self.current_state == AlarmBotState.root:
                self.root_handler(message)
            elif self.current_state == AlarmBotState.alarms_list:
                self.alarm_list_handler(message)
            elif self.current_state == AlarmBotState.alarms_pick_edit:
                self.alarms_pick_edit_handler(message)
            elif self.current_state == AlarmBotState.alarms_edit:
                self.alarm_edit_handler(message)
            elif self.current_state == AlarmBotState.alarms_toggle:
                self.pick_toggle_handler(message)
            else:
                print("unknown state")

        self.bot.polling(none_stop=True, interval=0)

    def root_handler(self, message):
        if message.text == 'Будильники':
            self.current_state = AlarmBotState.alarms_list
            self.alarm_list_menu(message)

        elif message.text == 'Настройки рассвета':
            self.bot.send_message(message.from_user.id,
                                  'Прочитать правила сайта вы можете по ' + '[ссылке](https://habr.com/ru/docs/help/rules/)',
                                  parse_mode='Markdown')
        else:
            self.unknown_command_err_msg(message)

    def alarm_list_handler(self, message):
        if message.text == 'Изменить будильник':
            self.current_state = AlarmBotState.alarms_pick_edit
            self.pick_edit_menu(message)

        elif message.text == 'Переключить будильник':
            self.current_state = AlarmBotState.alarms_toggle
            self.pick_toggle_menu(message)

        elif message.text == 'Назад':
            self.current_state = AlarmBotState.root
            self.root_menu(message)

        else:
            self.unknown_command_err_msg(message)

    def alarms_pick_edit_handler(self, message):
        if message.text == 'Назад':
            self.current_state = AlarmBotState.alarms_list
            self.alarm_list_menu(message)
        elif not re.match("(ПН|ВТ|СР|ЧТ|ПТ|СБ|ВС) (\d{2}):(\d{2})", message.text):
            self.unknown_command_err_msg(message)
        else:
            res = self.get_day(message.text)
            if res == -1:
                self.unknown_command_err_msg(message)
            else:
                self.current_state = AlarmBotState.alarms_edit
                self.picked = res
                self.edit_menu(message)

    def alarm_edit_handler(self, message):
        if message.text == 'Назад':
            self.current_state = AlarmBotState.alarms_pick_edit
            self.alarm_list_menu(message)
        elif not re.match("(\d{2}):(\d{2})", message.text):
            self.unknown_command_err_msg(message)
        else:
            res = self.get_time_minutes(message.text)
            if res == -1:
                self.unknown_command_err_msg(message)
            else:
                self.set_alarm(self.picked, res)
                self.current_state = AlarmBotState.alarms_list
                self.alarm_list_menu(message)

    def pick_toggle_handler(self, message):
        if message.text == 'Назад':
            self.current_state = AlarmBotState.alarms_list
            self.alarm_list_menu(message)
        elif not re.match("(ПН|ВТ|СР|ЧТ|ПТ|СБ|ВС) (\d{2}):(\d{2})", message.text):
            self.unknown_command_err_msg(message)
        else:
            res = self.get_day(message.text)
            if res == -1:
                self.unknown_command_err_msg(message)
            else:
                self.toggle_alarm(res)
                self.current_state = AlarmBotState.alarms_list
                self.alarm_list_menu(message)

    def get_alarms(self):
        self.mqtt.get_alarms()
        while self.mqtt.state != MqttClientState.idle:
            pass
        self.alarms = self.mqtt.alarms_times
        self.alarms_states = self.mqtt.alarms_states
        return 1

    def toggle_alarm(self, day):
        self.mqtt.toggle_alarm(day, self.alarms[day], self.alarms_states[day])
        while self.mqtt.state != MqttClientState.idle:
            pass
        return 1

    def set_alarm(self, day, time):
        self.mqtt.set_alarm(day, time)
        while self.mqtt.state != MqttClientState.idle:
            pass
        return 1

    def unknown_command_err_msg(self, message):
        self.bot.send_message(message.from_user.id, 'неизвестная команда', parse_mode='Markdown')

    def root_menu(self, message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
        btn1 = types.KeyboardButton('Будильники')
        btn2 = types.KeyboardButton('Настройки рассвета')
        markup.add(btn1, btn2)
        self.bot.send_message(message.from_user.id, 'Чего❓', reply_markup=markup)  # ответ бота

    def alarm_list_menu(self, message):
        self.get_alarms()
        on_ch = "✅ "
        off_ch = "❌ "
        alarms_list = [(on_ch if self.alarms_states[i] else off_ch) + self.days[i] + " " + self.get_time_string_from_minutes(self.alarms[i]) for i in range(len(self.alarms))]
        breaker = '\n'
        answer = breaker.join(alarms_list)
        btn1 = types.KeyboardButton('Изменить будильник')
        btn2 = types.KeyboardButton('Переключить будильник')
        button_back = types.KeyboardButton('Назад')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
        markup.add(btn1, btn2, button_back)
        self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

    def pick_edit_menu(self, message):
        self.get_alarms()
        alarms_list = [self.get_time_string_from_minutes(self.alarms[i]) for i in range(len(self.alarms))]
        buttons = []
        for idx, alarm in enumerate(alarms_list):
            buttons.append(types.KeyboardButton(self.days[idx] + " " + alarm))
        answer = 'Выберите будильник, который необходимо изменить'
        button_back = types.KeyboardButton('Назад')
        buttons.append(button_back)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*buttons)
        self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

    def edit_menu(self, message):
        msg = 'Введите время в формате hh:mm '
        button_back = types.KeyboardButton('Назад')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(button_back)
        self.bot.send_message(message.from_user.id, msg, reply_markup=markup)

    def pick_toggle_menu(self, message):
        self.get_alarms()

        alarms_list = [self.get_time_string_from_minutes(self.alarms[i]) for i in range(len(self.alarms))]
        buttons = []
        for idx, alarm in enumerate(alarms_list):
            buttons.append(types.KeyboardButton(self.days[idx] + " " + alarm))
        answer = 'Выберите будильник, который необходимо переключить'
        button_back = types.KeyboardButton('Назад')
        buttons.append(button_back)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*buttons)
        self.bot.send_message(message.from_user.id, answer, reply_markup=markup)

    def get_day(self, message):
        day = re.match("(ПН|ВТ|СР|ЧТ|ПТ|СБ|ВС)(?= (\d{2}):(\d{2}))", message)
        if day.group(0):
            return self.days.index(day.group(0))
        return -1

    def get_time_minutes(self, message):
        try:
            time = datetime.strptime(message, "%H:%M")
            time_minutes_int = time.hour * 60 + time.minute
            return time_minutes_int
        except ValueError:
            return -1

    def get_time_string_from_minutes(self, minutes):
        hour = minutes // 60
        minutes = minutes % 60
        hour_str = str(hour)
        minutes_str = str(minutes)
        if hour < 10:
            hour_str = "0" + hour_str
        if minutes < 10:
            minutes_str = "0" + minutes_str
        return hour_str + ":" + minutes_str

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


if __name__ == "__main__":
    AlarmBot()
