#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#include <iostream>
#include <cstring>

#include <U8g2lib.h>
#include "display.h"
#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

U8G2_SSD1309_128X64_NONAME2_1_4W_SW_SPI u8g2(U8G2_R2, 8, 10, 20, 2, 3);

// Initialize all pointers
BLEServer *pServer = NULL;                   // Pointer to the server
BLECharacteristic *pCharacteristic_1 = NULL; // Pointer to Characteristic 1
BLECharacteristic *pCharacteristic_2 = NULL; // Pointer to Characteristic 2
BLEDescriptor *pDescr_1;                     // Pointer to Descriptor of Characteristic 1
BLEDescriptor *pDescr_2;                     // Pointer to Descriptor of Characteristic 2
BLE2902 *pBLE2902_1;                         // Pointer to BLE2902 of Characteristic 1
BLE2902 *pBLE2902_2;                         // Pointer to BLE2902 of Characteristic 2

// Some variables to keep track on device connected
bool deviceConnected = false;
bool oldDeviceConnected = false;

// Variable that will continuously be increased and written to the client
// uint32_t value = 0;

// Variables for timing
unsigned long last_time = 0;
unsigned long time_delay = 1000;

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

#define SERVICE_UUID "fcde0000-e5b0-4f32-ad25-d70e07e9eeea"
#define CHARACTERISTIC_UUID_1 "fcde0001-e5b0-4f32-ad25-d70e07e9eeea"
#define CHARACTERISTIC_UUID_2 "fcde0002-e5b0-4f32-ad25-d70e07e9eeea"

void display_speed(const char* speed);
void display_car_behind(const char* speed);
void display_car_approaching();
// Callback function that is called whenever a client is connected or disconnected
class MyServerCallbacks : public BLEServerCallbacks
{
  void onConnect(BLEServer *pServer)
  {
    deviceConnected = true;
  };

  void onDisconnect(BLEServer *pServer)
  {
    deviceConnected = false;
  }
};

void setup()
{
  Serial.begin(115200);

  // Create the BLE Device
  BLEDevice::init("BLE_TEST");

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pCharacteristic_1 = pService->createCharacteristic(
      CHARACTERISTIC_UUID_1,
      BLECharacteristic::PROPERTY_READ |
          BLECharacteristic::PROPERTY_WRITE);

  pCharacteristic_2 = pService->createCharacteristic(
      CHARACTERISTIC_UUID_2,
      BLECharacteristic::PROPERTY_READ |
          BLECharacteristic::PROPERTY_WRITE);

  // Create BLE Descriptors
  pDescr_1 = new BLEDescriptor((uint16_t)0x2901);
  pDescr_1->setValue("Car Status");
  pCharacteristic_1->addDescriptor(pDescr_1);

  pDescr_2 = new BLEDescriptor((uint16_t)0x2901);
  pDescr_2->setValue("Bike Speed");
  pCharacteristic_2->addDescriptor(pDescr_2);

  pCharacteristic_1->addDescriptor(new BLE2902());
  pCharacteristic_2->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  // pAdvertising->setMinPreferred(0x0); // set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();
  Serial.println("Waiting a client connection to notify...");
  u8g2.begin();
  u8g2.sendF("ca", 0xa0, 0x41); // Put display into mirror mode
}

void loop()
{
  // notify changed value
  if (deviceConnected && millis() - last_time > time_delay)
  {

    // the current value is read using getValue()
    // this is where we should add HUD connections for speed 
    std::string rxValue1 = pCharacteristic_1->getValue();
    Serial.print("Characteristic 1 (getValue): ");
    Serial.println(rxValue1.c_str());

    // Here the value is written to the Client using setValue()
    // should be unneeded once testing is finished
    pCharacteristic_1->setValue(rxValue1.c_str());
    Serial.print("Characteristic 1 (setValue): ");
    Serial.println(rxValue1.c_str());

    // the current value is read using getValue()
    // this is where we should add HUD connections for speed 
    std::string rxValue2 = pCharacteristic_2->getValue();
    Serial.print("Characteristic 2 (getValue): ");
    Serial.println(rxValue2.c_str());

    // Here the value is written to the Client using setValue()
    // should be unneeded once testing is finished
    pCharacteristic_2->setValue(rxValue2.c_str());
    Serial.print("Characteristic 2 (setValue): ");
    Serial.println(rxValue2.c_str());

    u8g2.firstPage();
    const char * speed;
    const char * car_status;
    speed = rxValue2.c_str();
    car_status = rxValue1.c_str();
    do {
      if (!strcmp(car_status, "CarStatus.NO_CAR")) {
        display_speed(speed);
      } else if (!strcmp(car_status, "CarStatus.CAR_BEHIND")){
        display_car_behind(speed);
      } else {
        display_car_approaching();
      }
    } while ( u8g2.nextPage() );
    last_time = millis();
  }
  // The code below keeps the connection status uptodate:
  // Disconnecting
  if (!deviceConnected && oldDeviceConnected)
  {
    delay(500);                  // give the bluetooth stack the chance to get things ready
    pServer->startAdvertising(); // restart advertising
    Serial.println("start advertising");
    oldDeviceConnected = deviceConnected;
  }
  // Connecting
  if (deviceConnected && !oldDeviceConnected)
  {
    // do stuff here on connecting
    oldDeviceConnected = deviceConnected;
  }
}


void display_speed(const char* speed) {
  u8g2.setFont(LARGE_FONT);
   u8g2.setCursor(50,45);
   u8g2.print(speed);
}

void display_car_behind(const char* speed){
  u8g2.setFont(LARGE_FONT);
  u8g2.drawXBM(10, 20, car_front_width, car_front_height, car_front_bits);
  u8g2.setCursor(70,45);
  u8g2.print(speed);
}

void display_car_approaching() {
  u8g2.drawBox(0,0,150,75);
}