# FreshSense Hardware Documentation

## Hardware Components
- ESP32 Development Board
- DHT22 Temperature/Humidity Sensor
- MQ-135 Gas Sensor  
- HX711 Load Cell Amplifier
- 5kg Load Cell

## Pin Connections
```
DHT22:
- Data Pin -> GPIO 18
- VCC -> 3.3V
- GND -> GND

MQ-135:
- A0 -> GPIO 34
- VCC -> 5V
- GND -> GND

HX711:
- DT -> GPIO 4
- SCK -> GPIO 5
- VCC -> 3.3V
- GND -> GND
```

## ESP32 Code
// Write your ESP32 code here