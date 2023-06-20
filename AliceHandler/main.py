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
    dawn_modes = 6


class AliceHandlerBot:
    current_state = AlarmBotState.root

    alarms = []
    alarms_states = []

    dawn_modes = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60]
    active_dawn_mode = 0

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

        @self.bot.channel_post_handler(content_types=['text'])
        def get_text_messages(message):
            self.root_handler(message)

        self.get_alarms()
        self.bot.polling(none_stop=True, interval=0)

    def root_handler(self, message):
        self.handle_control_command(message)

    def handle_control_command(self, message):
        self.get_alarms()
        print(self.alarms_states)
        self.bot.set_chat_title(-1001672365693, self.get_alarms_string(), )

        if re.match("set_\d", message.text):
            alarm_id = int(str(message.text).removeprefix("set_"))
            print(f"Alice wants to turn on {alarm_id} alarm")
            if not self.alarms_states[alarm_id]:
                self.toggle_alarm(alarm_id)
        elif re.match("unset_\d", message.text):
            alarm_id = int(str(message.text).removeprefix("unset_"))
            print(f"Alice wants to turn off {alarm_id} alarm")
            if self.alarms_states[alarm_id] == 1:
                self.toggle_alarm(alarm_id)
        else:
            print("someting")

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
        self.alarms_states[day] = self.alarms_states[day] ^ 1
        self.bot.set_chat_title(-1001672365693, self.get_alarms_string(), )
        return 1

    def set_alarm(self, day, time):
        self.mqtt.set_alarm(day, time)
        while self.mqtt.state != MqttClientState.idle:
            pass
        return 1

    def unknown_command_err_msg(self, message):
        self.bot.send_message(message.from_user.id, 'неизвестная команда', parse_mode='Markdown')

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

    def get_alarms_string(self):
        answer = []
        for idx, alarm in enumerate(self.alarms):
            if self.alarms_states[idx]:
                answer.append(str(alarm))
            else:
                if alarm == 0:
                    answer.append(str(-1))
                else:
                    answer.append(str(-alarm))
        breaker = ","
        return breaker.join(answer)


if __name__ == "__main__":
    AliceHandlerBot()
