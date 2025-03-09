# Signal Reciver Finder (Faster Than Lightning)

ELE495 Senior Project - Embedded component for an autonomous signal transmitter finding vehicle.

## Overview

This project implements a signal direction finding system using a desktop app. The vehicle autonomously scans for radio signals, determines the strongest signal direction, and navigates toward the signal source.

## Features

- Full 360° and targeted half-scan signal detection
- PID-controlled precision movement
- Bluetooth connectivity for remote control and data visualization
- Real-time signal strength visualization
- Gyroscope-based direction sensing

## Hardware Requirements

- Raspberry Pi
- RTL-SDR USB receiver and Antenna
- MPU6050 gyroscope
- DC motors with L298N motor driver
- Power supply

## Software Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

## Getting Started

1. Connect all hardware components according to your pin configuration
2. Install required dependencies
3. Run the embedded application:

```bash
python src/main.py
```

4. Connect to the system using the companion app

## Project Structure

- `lib/`: Core libraries for hardware interaction
  - `BluetoothModule.py`: Handles Bluetooth communication
  - `CircularBuffer.py`: Implements data buffer for signal processing
  - `Gyroscope.py`: Interfaces with MPU6050
  - `PIDController.py`: PID controller for movement precision
  - `SDRModule.py`: Software Defined Radio interface
  - `Vehicle.py`: Motor control and movement functions
- `src/`: Source code
  - `main.py`: Main application entry point
  - `test/`: Test scripts for individual components

## Project Demo

![Video](https://github.com/ELE495-2425Spring/capstoneproject-mcqueen-grup-4/blob/main/images%20and%20video/WhatsApp%20Video%202025-03-07%20at%2018.20.57_f3115946.mp4)
Video

## Project Photos
![Vehicle Photo](https://github.com/ELE495-2425Spring/capstoneproject-mcqueen-grup-4/blob/main/images%20and%20video/araba%20(1).jpg?raw=true)
Vehicle Photo

![Desktop App Photo](https://github.com/ELE495-2425Spring/capstoneproject-mcqueen-grup-4/blob/main/images%20and%20video/uygulama_1.png)
Desktop App Photo

## Team Members

- 201201022 Celal Efe Çin
- 201201039 Mehmet Mert Ataman
- 201201055 Yalın Hoşgör
- 201201068 Reşat Gökay Yiğit
- 211201068 Ali Murat Büyükaşık
