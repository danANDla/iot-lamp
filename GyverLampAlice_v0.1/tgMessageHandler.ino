void newMsg(FB_msg& msg) {
  Serial.println(msg.toString());
  if (msg.chatID != white_id_list[0]) {
    return;
  }
  if (msg.text == "greetings") {
    currentMode = 14;
    FastLED.setBrightness(modes[currentMode].brightness);
    loadingFlag = true;
    settChanged = true;
    eepromTimer = millis();
    FastLED.clear();
    delay(1);
    sendSettings_flag = true;
  }
  else if (msg.text.startsWith("alarm_set_ON ", 0)) {
    byte alarmNum = (char)msg.text[13] - '0';
    int alarm_time = msg.text.substring(15).toInt();
    if(alarmNum < 7){
      alarm[alarmNum].state = 1;
      alarm[alarmNum].time = alarm_time;
      String answer = "lamp: alarm_set_OK " + String(alarmNum) + " " + String(alarm_time);
      bot.sendMessage(answer, white_id_list[0]);
    }
    saveAlarm(alarmNum);
    manualOff = false;
  }
  else if (msg.text.startsWith("alarm_set_OFF ", 0)) {
    byte alarmNum = (char)msg.text[14] - '0';
    if(alarmNum < 7){
      alarm[alarmNum].state = 0;
      String answer = "lamp: alarm_unset_OK " + String(alarmNum) + " " + String(alarm[alarmNum].time);
      bot.sendMessage(answer, white_id_list[0]);
    }
    saveAlarm(alarmNum);
    manualOff = false;
  }
  else if (msg.text == "alarmbot: alarms_get_all" || msg.text == "alice: alarms_get_all") {
    String answer = "lamp: { \"alarms:\" [(";
    for (byte i = 0; i < 6; i++) {
      if(!alarm[i].state){
        answer = answer + "off,0),(";
      } else {
        answer = answer + "on," + minutesToTimeString(alarm[i].time) + "),(";
      }
    }
    if(!alarm[6].state){
      answer = answer + "off,0)]}";
    } else {
      answer = answer + "on," + minutesToTimeString(alarm[6].time) + ")]}";
    }
    bot.sendMessage(answer, white_id_list[0]);
  }
  else if (msg.text.startsWith("alarmbot: dawn_mode", 0)){
    dawnMode = msg.text.substring(20).toInt();
    saveDawnMmode();
    String answer = "lamp: dawn_mode_set_OK " + String(dawnMode) + " " + String(dawnOffsets[dawnMode]);
    bot.sendMessage(answer, white_id_list[0]);
  }
  else {
    Serial.println(msg.text);
  }
}

String minutesToTimeString(int time){
  byte hour = floor(time / 60);
  byte minute = time - hour * 60;
  String outputString = String(hour) + ":" + String(minute);
  return outputString;
}

