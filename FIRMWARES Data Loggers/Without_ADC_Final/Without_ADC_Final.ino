#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "WiFi.h"
#include <time.h>

const char* ssid = "redmi10c";
const char* password = "12345678";
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

char filename[64];
String dataBuffer;
int bufferCount = 0;
const int bufferLimit = 1000;
unsigned long lastSampleTime = 0;  
const int sampleInterval = 4;      

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

    writeFile(SD, filename, "Timestamp,ADC Value\n");
    Serial.printf("Logging data to %s\n", filename);
}

void loop() {
    unsigned long currentTime = millis();
    if (currentTime - lastSampleTime >= sampleInterval) {
        lastSampleTime = currentTime;  // Update the last sample time
        checkWiFi();

        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
            Serial.println("Failed to obtain time");
            return;
        }
        char timeString[64];
        int millisPart = currentTime % 1000;
        sprintf(timeString, "%02d:%02d:%02d.%03d", timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec, millisPart);

        int adcValue = analogRead(34);

        String dataString = String(timeString) + "," + String(adcValue) + "\n";
        bufferData(dataString);
        delay(4);
    }
}

void writeFile(fs::FS &fs, const char * path, const char * message) {
    File file = fs.open(path, FILE_WRITE);
    if (!file) {
        Serial.println("Failed to open file for writing");
        return;
    }
    if (file.print(message)) {
        Serial.println("File written");
    }
    file.close();
}

void appendFile(fs::FS &fs, const char * path, const char * message) {
    File file = fs.open(path, FILE_APPEND);
    if (!file) {
        Serial.println("Failed to open file for appending");
        return;
    }
    if (file.print(message)) {
        Serial.println("Message appended");
    }
    file.close();
}

void bufferData(String data) {
    dataBuffer += data;
    bufferCount++;
    if (bufferCount >= bufferLimit) {
        appendFile(SD, filename, dataBuffer.c_str());
        dataBuffer = "";  
        bufferCount = 0;  
    }
}
