#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "WiFi.h"
#include <time.h>
#include <Adafruit_ADS1X15.h>

#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

const char* ssid = "redmi10c";
const char* password = "12345678";
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

Adafruit_ADS1115 ads; 

constexpr int READY_PIN = 4;

unsigned long previousMillis = 0;
const long interval = 4; // If you need to change the sample time change this variable currently its set to 4ms
char filename[64];
String dataBuffer;  
int bufferCount = 3000;  

void connectToWiFi();
void checkWiFi();
void bufferData(String data);
void writeFile(fs::FS &fs, const char * path, const char * message);
void appendFile(fs::FS &fs, const char * path, const char * message);

volatile bool new_data = false;
void IRAM_ATTR NewDataReadyISR() {
  new_data = true;
}


void setup() {
    Serial.begin(115200);
    connectToWiFi();

    if (!SD.begin()) {
        Serial.println("Card Mount Failed");
        return;
    }
    ads.setDataRate(RATE_ADS1115_860SPS);
    ads.setGain(GAIN_SIXTEEN);
    pinMode(READY_PIN, INPUT);
    
    if (!ads.begin()) {
      Serial.println("Failed to initialize ADS.");
      while (1);
    } 

    uint8_t cardType = SD.cardType();
    Serial.print("SD Card Type: ");
    if (cardType == CARD_NONE) {
        Serial.println("No SD card attached");
        return;
    }
    
    attachInterrupt(digitalPinToInterrupt(READY_PIN), NewDataReadyISR, FALLING);
    ads.startADCReading(ADS1X15_REG_CONFIG_MUX_DIFF_0_1, /*continuous=*/true);

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
      Serial.println("Failed to obtain time");
      return;
    }
    
    sprintf(filename, "/data_%04d-%02d-%02d_%02d-%02d-%02d.csv", 
            timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
            timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);

    writeFile(SD, filename, "Timestamp,Data\n");
    Serial.printf("Logging data to %s\n", filename);
}

void loop() {
    static unsigned long lastTime = 0;
    unsigned long currentTime = millis();
    
    if (currentTime - lastTime >= interval) {
        lastTime = currentTime;

        if (!new_data) {
          return;
        }
        
        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
          Serial.println("Failed to obtain time");
          return;
        }
        char timeString[64];
        int millisPart = currentTime % 1000;
        sprintf(timeString, "%02d:%02d:%02d.%03d", timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec, millisPart);
        
        int16_t results = ads.getLastConversionResults();
        String dataString = String(timeString) + "," + String(results) + "\n";
        bufferData(dataString);
        new_data = false;    
       
    }
}


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

void bufferData(String data) {
    dataBuffer += data;
    bufferCount--;
    if (bufferCount <= 0) {
        appendFile(SD, filename, dataBuffer.c_str());
        dataBuffer = "";  
        bufferCount = 3000;  
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
