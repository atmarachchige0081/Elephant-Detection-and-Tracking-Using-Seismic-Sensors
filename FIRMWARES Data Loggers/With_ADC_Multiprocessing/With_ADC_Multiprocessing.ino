#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "WiFi.h"
#include <time.h>
#include <Adafruit_ADS1X15.h>

const char* ssid = "redmi10c";
const char* password = "12345678";
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

Adafruit_ADS1115 ads;

QueueHandle_t dataQueue;  // Queue for transferring data between cores

char filename[64];

void connectToWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" connected");
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
}

void checkWiFi() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi lost, reconnecting...");
        connectToWiFi();
    }
}

void setup() {
    Serial.begin(115200);
    ads.setGain(GAIN_SIXTEEN);
    if (!ads.begin()) {
        Serial.println("Failed to initialize ADS.");
        while (1);
    }

    connectToWiFi();

    if (!SD.begin()) {
        Serial.println("Card Mount Failed");
        return;
    }

    uint8_t cardType = SD.cardType();
    Serial.print("SD Card Type: ");
    if (cardType == CARD_NONE) {
        Serial.println("No SD card attached");
        return;
    }

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        Serial.println("Failed to obtain time");
        return;
    }

    sprintf(filename, "/data_%04d-%02d-%02d_%02d-%02d-%02d.csv", 
            timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
            timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);

    dataQueue = xQueueCreate(10, sizeof(String));  // Create a queue to hold up to 10 String objects

    xTaskCreatePinnedToCore(
        dataAcquisitionTask, "DataAcquisition", 10000, NULL, 1, NULL, 0);  // Task on core 0
    xTaskCreatePinnedToCore(
        dataWritingTask, "DataWriting", 10000, NULL, 1, NULL, 1);  // Task on core 1
}

void loop() {
}

void dataAcquisitionTask(void * parameter) {
    for (;;) {
        checkWiFi();  

        int16_t diff_0_1 = ads.readADC_Differential_0_1();
        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
            Serial.println("Failed to obtain time");
            continue;
        }
        int millisPart = (int)(millis() % 1000);
        char timeString[64];
        sprintf(timeString, "%02d:%02d:%02d.%03d", timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec, millisPart);

        String dataString = String(timeString) + "," + String(diff_0_1) + "\n";
        xQueueSend(dataQueue, &dataString, portMAX_DELAY);  

        vTaskDelay(4 / portTICK_PERIOD_MS);  
    }
}

void dataWritingTask(void * parameter) {
    String dataString;
    for (;;) {
        if (xQueueReceive(dataQueue, &dataString, portMAX_DELAY)) {
            File file = SD.open(filename, FILE_APPEND);
            if (file) {
                file.print(dataString);
                file.close();
            } else {
                Serial.println("Failed to open file for appending");
            }
        }
    }
}
