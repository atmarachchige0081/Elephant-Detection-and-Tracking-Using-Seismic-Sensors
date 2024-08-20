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

unsigned long previousMillis = 0; 
const long interval = 4; 

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
 
    Serial.println("Getting differential reading from AIN0 and AIN1 at 250Hz");
    Serial.println("ADC Range: +/- 0.256V (1 bit = 0.0078125mV for ADS1115 with GAIN_SIXTEEN)");
  
    ads.setGain(GAIN_SIXTEEN); 
  
    if (!ads.begin())
    {
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

    writeFile(SD, filename, "Timestamp,Geophone Data\n");
    Serial.printf("Logging data to %s\n", filename);
}

void loop() {
    checkWiFi();
    
    unsigned long startTime = millis();  

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
      Serial.println("Failed to obtain time");
      return;
    }
    char timeString[64];
    int millisPart = (int)(millis() % 1000);
    sprintf(timeString, "%02d:%02d:%02d.%03d", timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec, millisPart);
    
    int16_t diff_0_1;
    float volts_diff_0_1;

    diff_0_1 = ads.readADC_Differential_0_1();

    String dataString = String(timeString) + "," + String(diff_0_1) + "\n";
    appendFile(SD, filename, dataString.c_str());

    Serial.print(timeString);
    Serial.print(", ");
    Serial.println(diff_0_1);

    unsigned long loopTime = millis() - startTime;
    if (loopTime < 4) {
        delay(4 - loopTime);
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
