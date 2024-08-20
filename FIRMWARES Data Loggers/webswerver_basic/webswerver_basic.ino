#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include <time.h>
#include <Adafruit_ADS1X15.h>

#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

const char* ssid = "sambro";
const char* password = "krak0594";
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

Adafruit_ADS1115 ads; 
constexpr int READY_PIN = 4;

WebServer server(80);
String webOutput;

unsigned long previousMillis = 0;
const long interval = 4;
char filename[64];
String dataBuffer;  
int bufferCount = 3000;  

void printAndWebOutput(String message);
void setupWebServer();
void handleClientRequests();

volatile bool new_data = false;
void IRAM_ATTR NewDataReadyISR() {
    new_data = true;
}

void setup() {
    Serial.begin(115200);
    connectToWiFi();
    setupWebServer();

    if (!SD.begin()) {
        printAndWebOutput("Card Mount Failed\n");
        return;
    }
    ads.setDataRate(RATE_ADS1115_860SPS);
    ads.setGain(GAIN_SIXTEEN);
    pinMode(READY_PIN, INPUT);

    if (!ads.begin()) {
        printAndWebOutput("Failed to initialize ADS.\n");
        while (1);
    } 

    uint8_t cardType = SD.cardType();
    printAndWebOutput("SD Card Type: ");
    if (cardType == CARD_NONE) {
        printAndWebOutput("No SD card attached\n");
        return;
    }

    attachInterrupt(digitalPinToInterrupt(READY_PIN), NewDataReadyISR, FALLING);
    ads.startADCReading(ADS1X15_REG_CONFIG_MUX_DIFF_0_1, /*continuous=*/true);

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        printAndWebOutput("Failed to obtain time\n");
        return;
    }

    sprintf(filename, "/data_%04d-%02d-%02d_%02d-%02d-%02d.csv", 
            timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
            timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);

    writeFile(SD, filename, "Timestamp,Data\n");
    printAndWebOutput((String)"Logging data to " + filename + "\n");
}

void loop() {
    handleClientRequests();

    static unsigned long lastTime = 0;
    unsigned long currentTime = millis();

    if (currentTime - lastTime >= interval) {
        lastTime = currentTime;

        if (!new_data) {
            return;
        }

        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
            printAndWebOutput("Failed to obtain time\n");
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
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

void printAndWebOutput(String message) {
    Serial.print(message);
    message.replace("\n", "<br>");  // Modify the message in place.
    webOutput += message;           // Append the modified message to webOutput.
}

void setupWebServer() {
    server.on("/", HTTP_GET, []() {
        server.send(200, "text/html", "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
            "<title>Elephant Detection Using Seismic Sensors</title>"
            "<style>"
            "body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; }"
            "h1 { color: #5a5a5a; font-size: 24px; }"
            "h2, h3 { color: #4a4a4a; font-size: 18px; }"
            "p { font-size: 16px; color: #4a4a4a; }"
            "pre { background-color: #fff; border: 1px solid #ddd; padding: 15px; font-size: 16px; line-height: 1.5; overflow-x: auto; }"
            "</style>"
            "</head>"
            "<body>"
            "<h1>Serial Output</h1>"
            "<pre id='serialOutput'>" + webOutput + "</pre>"
            "<h2>Elephant Detection Using Seismic Sensors</h2>"
            "<h3>Data Logger Server</h3>"
            "<p>Firmware by – Buddhila Siriwardena and Akitha Munasinghe</p>"
            "</body>"
            "</html>");
    });

    server.begin();
    if (MDNS.begin("esp32")) {
        MDNS.addService("http", "tcp", 80);
    }
}

void handleClientRequests() {
    server.handleClient();
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
        printAndWebOutput("Failed to open file for writing\n");
        return;
    }
    if (file.print(message)) {
        printAndWebOutput("File written\n");
    }
    file.close();
}

void appendFile(fs::FS &fs, const char * path, const char * message) {
    File file = fs.open(path, FILE_APPEND);
    if (!file) {
        printAndWebOutput("Failed to open file for appending\n");
        return;
    }
    if (file.print(message)) {
        printAndWebOutput("Message appended\n");
    }
    file.close();
}
