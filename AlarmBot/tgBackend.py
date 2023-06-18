#
# UNUSED
#

import telebot
import re
import props
import multiprocessing

bots_chat_id = props.bots_chat_id
alice_token = props.alice_token


class AlarmBotBackEnd:
    current_state = ''
    alarms = []
    alarm_buffer = ''
    states = ['idle',
              'get_alarms', 'set_alarm', 'unset_alarm',
              'set_dawn_mode']
    bot = None
    queue = None

    def __init__(self, q: multiprocessing.Queue):
        self.current_state = 'idle'
        self.bot = telebot.TeleBot(alice_token)
        self.queue = q

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            if self.current_state == 'idle':
                self.idle_handler(message)
            elif self.current_state == 'get_alarms':
                self.get_alarms_handler(message)
            elif self.current_state == 'set_alarm':
                self.set_alarm_handler(message)
            elif self.current_state == 'unset_alarm':
                self.unset_alarm_handler(message)
            elif self.current_state == 'set_dawn_mode':
                self.set_dawn_mode_handler(message)
            else:
                print("undefined state:", message)

    def get_alarms_handler(self, message):
        if re.match("lamp: \{ \"alarms:\".*", message.text):
            print(re.match("(?<=lamp: \{ \"alarms:\" \[).*(?=\]\})", message.text))
            self.current_state = 'idle'
        elif re.match("lamp: .*", message.text):
            print(re.match("(?<=lamp: ).*", message))
            self.current_state = 'idle'
        else:
            print(message)
            pass
        self.queue.put(message.text)
        print("putted message in queue")
        print(self.queue.empty())

    def idle_handler(self, message):
        print("IDLE:", message)
