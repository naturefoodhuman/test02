// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-04 04:30:00

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "config.h"

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

String buildMockPayload() {
  unsigned long now = millis();
  return String("{\"presence\":true,") +
         "\"state\":\"moving\"," +
         "\"breathing_rate\":32," +
         "\"heart_rate\":120," +
         "\"abnormal_event\":null," +
         "\"timestamp\":" + String(now) + "}";
}

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  while (!mqtt.connected()) {
    mqtt.connect("parenting-mmwave-xiao-esp32c6");
    delay(500);
  }
}

void setup() {
  Serial.begin(115200);
  connectWifi();
  connectMqtt();
}

void loop() {
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();
  String payload = buildMockPayload();
  Serial.println(payload);
  mqtt.publish(MQTT_TOPIC, payload.c_str());
  delay(1000);
}
