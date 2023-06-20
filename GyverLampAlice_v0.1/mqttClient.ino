void reconnect() { 
  while (!client.connected()) {
    Serial.println(F("Attempting MQTT connection..."));
    Serial.print(F("Client ID:"));
    Serial.print(clientId);
    Serial.print(F(" "));
    Serial.print(mqtt_login);
    Serial.print(F(" "));
    Serial.print(mqtt_pass);
    Serial.print(F(" "));
    if (client.connect(clientId.c_str(), mqtt_login, mqtt_pass,
        mqtt_topic_availability, 0, true, "OFF")) {  
      Serial.println(F("connected"));

      // Публикация сообщения с идентификаторм клиента в топик, заданный значением 'mqtt_topic_status'
      client.publish(mqtt_topic_status, clientId.c_str());
      client.publish(mqtt_topic_availability, "ON");

      // Подписка на сообщения в топике, заданном значением mqtt_topic_in
      client.subscribe(mqtt_topic_in);
      // Если нужно подписаться на несколько топиков, то для каждого из них вызываем client.subscribe()
    } else {
      Serial.print(F("failed, rc="));
      Serial.print(client.state());
      Serial.println(F("try again in 5 seconds"));
      delay(5000);
    }
  }
}


// Функция обработки входящих сообщений
void callback(char* topic, byte* payload, unsigned int length) {
  // Печать информации о полученном сообщенийй
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  String input_buffer;
  for (int i = 0; i < length; i++) {
    input_buffer = input_buffer + (char) payload[i];
    Serial.print((char)payload[i]);
  }
  Serial.println();

  // Если получено сообщение и у нас подписка на несколько топиков, то определяем в каком топике сообщение опубликовано
  if (strcmp(topic, mqtt_topic_in) == 0) {
    if (input_buffer.startsWith("alarm_set_ON ", 0)) {
      byte alarmNum = (char)input_buffer[13] - '0';
      int alarm_time = input_buffer.substring(15).toInt();
      if(alarmNum < 7){
        alarm[alarmNum].state = 1;
        alarm[alarmNum].time = alarm_time;
        String answer = "alarm_set_OK " + String(alarmNum) + " " + String(alarm_time);
        Serial.printf("Publish message [%s]: ", mqtt_topic_out);
        Serial.println(answer);
        char buf[200];
        answer.toCharArray(buf, answer.length() + 1);
        client.publish(mqtt_topic_out, buf);
      }
      saveAlarm(alarmNum);
      manualOff = false;
    }
    else if (input_buffer.startsWith("alarm_set_OFF ", 0)) {
      byte alarmNum = (char)input_buffer[14] - '0';
      if(alarmNum < 7){
        alarm[alarmNum].state = 0;
        String answer = "alarm_unset_OK " + String(alarmNum) + " " + String(alarm[alarmNum].time);
        Serial.printf("Publish message [%s]: ", mqtt_topic_out);
        Serial.println(answer);
        char buf[200];
        answer.toCharArray(buf, answer.length() + 1);
        client.publish(mqtt_topic_out, buf);
      }
      saveAlarm(alarmNum);
      manualOff = false;
    }
    else if (input_buffer == "alarms_get_all") {
      String answer = "{ \"alarms:\" [(";
      for (byte i = 0; i < 6; i++) {
        if(!alarm[i].state){
          answer = answer + "off," + minutesToTimeString(alarm[i].time) + "),(";
        } else {
          answer = answer + "on," + minutesToTimeString(alarm[i].time) + "),(";
        }
      }
      if(!alarm[6].state){
        answer = answer + "off,0)]}";
      } else {
        answer = answer + "on," + minutesToTimeString(alarm[6].time) + ")]}";
      }
      Serial.printf("Publish message [%s]: ", mqtt_topic_out);
      Serial.println(answer);
      char buf[200];
      answer.toCharArray(buf, answer.length() + 1);
      client.publish(mqtt_topic_out, buf);
    }
    else if (input_buffer.startsWith("dawn_mode_set", 0)){
      dawnMode = input_buffer.substring(14).toInt();
      saveDawnMmode();
      String answer = "dawn_mode_set_OK " + String(dawnMode) + " " + String(dawnOffsets[dawnMode]);
      Serial.printf("Publish message [%s]: ", mqtt_topic_out);
      Serial.println(answer);
      char buf[200];
      answer.toCharArray(buf, answer.length() + 1);
      client.publish(mqtt_topic_out, buf);
    } 
    else if (input_buffer.startsWith("dawn_mode_get", 0)){
      String answer = "\{ \"dawn_mode\": " + String(dawnMode) + " \}";
      Serial.printf("Publish message [%s]: ", mqtt_topic_out);
      Serial.println(answer);
      char buf[200];
      answer.toCharArray(buf, answer.length() + 1);
      client.publish(mqtt_topic_out, buf);
    } 
  }
}

String minutesToTimeString(int time){
  byte hour = floor(time / 60);
  byte minute = time - hour * 60;
  String outputString = String(hour) + ":" + String(minute);
  return outputString;
}


void mqttTick(){
  if (!client.connected()) reconnect();
  client.loop();

  // Публикация сообщения с заданной периодичностью
  // long now = millis();
  // if (now - lastMsg > delayMS) {
  //   lastMsg = now;
  //   // ++value;
    
  //   // // Формирование сообщения и его публикация 
  //   // char msg[200];
  //   // snprintf (msg, sizeof(msg), "heartbeat #%ld", value);
  //   // Serial.print("Publish message: ");
  //   // Serial.println(msg);
  //   // client.publish(mqtt_topic_status, msg);
  //   // client.publish(mqtt_topic_availability, "ON");
  // }
}
