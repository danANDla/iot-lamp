import random
import props
import re
from enum import Enum

from paho.mqtt import client as mqtt_client


class MqttClientState(Enum):
    idle = 1
    waiting_for_alarms = 2
    waiting_for_set = 3
    waiting_for_toggle = 4
    waiting_for_dawn_modes = 5
    waiting_for_dawn_mode_set = 6


class MqttClient:
    broker = '127.0.0.1'
    port = 1884
    topicControl = "lampBotControl"
    topicResponse = "lampBotControlResponse"
    topicAvailability = "alarmBot/availability"
    # Generate a Client ID with the subscribe prefix.
    client_id = f'subscribe-{random.randint(0, 100)}'

    username = props.mqtt_alarmbot_username
    password = props.mqtt_alarmbot_password

    client = None
    state = MqttClientState.idle

    alarms_states = []
    alarms_times = []
    dawn_mode = 0

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
                self.publish(self.topicAvailability, 'ON')
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = on_connect
        client.will_set(self.topicAvailability, "OFF", 0, True)
        client.connect(self.broker, self.port)
        return client

    def subscribe(self):
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

        self.client.subscribe(self.topic)
        self.client.on_message = on_message

    def publish(self, topic, msg):
        result = self.client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

    def init(self):
        self.client = self.connect_mqtt()
        self.state = MqttClientState.idle

        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            if msg.topic != 'lampBotControlResponse':
                return
            if self.state == MqttClientState.waiting_for_alarms:
                if self.decode_alarms(msg.payload.decode()) != 0:
                    self.state = MqttClientState.idle
            elif self.state == MqttClientState.waiting_for_set:
                if self.decode_alarm_set(msg.payload.decode()) != 0:
                    self.state = MqttClientState.idle
            elif self.state == MqttClientState.waiting_for_toggle:
                if self.decode_alarm_toggle(msg.payload.decode()) != 0:
                    self.state = MqttClientState.idle
            elif self.state == MqttClientState.waiting_for_dawn_modes:
                if self.decode_dawn_mode_get(msg.payload.decode()) != 0:
                    self.state = MqttClientState.idle
            elif self.state == MqttClientState.waiting_for_dawn_mode_set:
                if self.decode_dawn_mode_set(msg.payload.decode()) != 0:
                    self.state = MqttClientState.idle

        self.client.subscribe(self.topicResponse)
        self.client.on_message = on_message
        self.client.loop_start()

    def decode_alarms(self, msg: str):
        states = []
        times = []
        if re.match("\{ \"alarms:\".*", msg):
            alarms_packed = (msg.removeprefix("{ \"alarms:\" [")).removesuffix("]}")
            alarms = alarms_packed.split("),(")
            for alarm_packed in alarms:
                status, time = (alarm_packed.removeprefix("(")).removesuffix(")").split(",")
                states.append(1 if status == "on" else 0)
                time_int = 0
                if time != '0':
                    hours, minutes = time.split(":")
                    time_int = int(hours) * 60 + int(minutes)
                times.append(time_int)

            self.alarms_states = states
            self.alarms_times = times
            return 1
        else:
            return 0

    def decode_alarm_set(self, msg: str):
        if re.match("alarm_set_OK .*", msg):
            return 1
        return 0

    def decode_alarm_toggle(self, msg: str):
        if re.match("alarm_unset_OK .*", msg):
            return 1
        elif re.match("alarm_set_OK .*", msg):
            return 1
        return 0

    def decode_dawn_mode_get(self, msg: str):
        if re.match("\{ \"dawn_mode\":.*", msg):
            dawn_mode_packed = (msg.removeprefix("{ \"dawn_mode\": ")).removesuffix(" }")
            self.dawn_mode = int(dawn_mode_packed)
            return 1
        return 0

    def decode_dawn_mode_set(self, msg: str):
        if re.match("dawn_mode_set_OK .*", msg):
            return 1
        return 0

    def get_alarms(self):
        self.state = MqttClientState.waiting_for_alarms
        self.publish(self.topicControl, 'alarms_get_all')

    def set_alarm(self, day, time):
        self.state = MqttClientState.waiting_for_set
        self.publish(self.topicControl, 'alarm_set_ON ' + str(day) + ' ' + str(time))

    def toggle_alarm(self, day, time, state):
        self.state = MqttClientState.waiting_for_toggle
        if state:
            self.publish(self.topicControl, 'alarm_set_OFF ' + str(day))
        else:
            self.publish(self.topicControl, 'alarm_set_ON ' + str(day) + ' ' + str(time))

    def get_dawn_mode(self):
        self.state = MqttClientState.waiting_for_dawn_modes
        self.publish(self.topicControl, 'dawn_mode_get')

    def set_dawn_mode(self, mode):
        self.state = MqttClientState.waiting_for_dawn_mode_set
        self.publish(self.topicControl, 'dawn_mode_set ' + str(mode))
