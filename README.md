# PeciTech-Studio

<p align="center">
  <strong>The Ultimate Open-Source Stream Controller & Macro Deck Ecosystem</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="https://www.espressif.com/"><img src="https://img.shields.io/badge/Hardware-ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white" alt="ESP32" /></a>
  <a href="https://obsproject.com/"><img src="https://img.shields.io/badge/OBS_Studio-WebSocket_v5-302E31?style=for-the-badge&logo=obsstudio&logoColor=white" alt="OBS Studio" /></a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/badge/UI-CustomTkinter-FF7A29?style=for-the-badge" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge" alt="MIT License" />
</p>

---

## ⚡ Overview

**PeciTech Studio** is a modern, high-performance desktop controller suite and companion firmware for the **PeciDeck MK.1** — a DIY macro pad featuring **8 mechanical switches**, **3 rotary encoders**, and a **vibrant ST7789 IPS display**.

Whether you're streaming on Twitch/YouTube, scrubbing timelines in DaVinci Resolve, managing Discord audio, or automating complex workflows with multi-step macros, PeciTech Studio gives you full tactile control at your fingertips.

---

## ✨ Features at a Glance

### 🎛️ Hardware Companion (PeciDeck MK.1)
- **Live Bidirectional USB-Serial Protocol**: High-speed communication (115200 baud) for instant button triggers, encoder feedback, and real-time screen icon rendering.
- **Vibrant TFT Display**: Live rendering of active profiles, button labels, icons, and encoder feedback.
- **Triple Rotary Encoders with Push Buttons**: Smooth scrubbing for master volume, discrete OBS audio tracks, song seeking, display brightness, and scene cycling.

### 🎨 Desktop Studio Experience
- **Modern Dark UI**: Built with CustomTkinter in a clean cyberpunk-inspired palette (`#0B0B0E` / `#FF7A29` accent).
- **Interactive Property Inspector**: Click any key or encoder on your virtual deck to customize action targets, titles, font styles, and icons on the fly.
- **Dual-State Toggle Buttons**: Assign separate icons, labels, and actions for state 1 / state 2 (e.g. Mute/Unmute, Camera On/Off).
- **Profile & Folder Management**: Create dedicated profiles (`Stream`, `Gaming`, `Editing`) and nest actions into hierarchical folders with one-click return.

### 📹 Deep OBS Studio Integration (WebSocket v5)
- **Audio Scrubbing on Encoders**: Rotate encoders to increase/decrease specific audio tracks (Spotify, Mic, Desktop Audio) in 2 dB steps, and press to toggle mute.
- **Scene Switching**: One-touch scene transitions with automatic scene list fetching.
- **Stream & Recording Control**: Start, pause, and stop broadcast/recording with visual feedback.

### ⌨️ Universal Smart Hotkey Engine
- **Layout-Independent Recording**: Captures physical hardware scan codes directly — zero conflicts between QWERTY/QWERTZ or Czech/English layouts.
- **Visual Key Badges**: Interactive recording dialog showing physical keys (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>2</kbd>).
- **Reliable Background Dispatch**: Guaranteed 45 ms key-hold time ensures background apps, Discord, and DirectX games never miss a shortcut.

### 🚀 Performance & Low Latency
- **Gaming Mouse Optimized**: Custom GIL switch interval prevents cursor stutter even with high-polling rate gaming mice (1000 Hz).
- **Native Single-Instance Mutex**: Prevents duplicate processes, protects serial port access, and restores the window from the tray automatically.

---

## 📁 Repository Structure

```plaintext
PeciTech-Studio/
├── PeciTech/
│   ├── Aplikace/             # Python Desktop Studio Suite
│   │   ├── assets/           # Application icons, logos, and graphic assets
│   │   ├── profiles/         # User profile configurations (JSON)
│   │   ├── ui/               # CustomTkinter views, modals, and inspector panels
│   │   ├── action_handler.py # High-reliability macro & shortcut execution engine
│   │   ├── hardware_serial.py# USB-Serial bridge communicating with PeciDeck
│   │   ├── obs_controller.py # OBS WebSocket v5 controller
│   │   └── main.py           # Application entry point & tray management
│   │
│   └── Finware/              # ESP32 Arduino Firmware
│       ├── PeciDeck_Firmware/# Main Arduino sketch (ST7789 TFT, Encoders, Buttons)
│       └── NAVOD_K_NAHRANI.md# Step-by-step firmware flashing guide
│
├── .gitignore                # Git exclusions
└── README.md                 # Project documentation
```

---

## 🔌 Hardware Specs (PeciDeck MK.1)

| Component | Specification |
| :--- | :--- |
| **Microcontroller** | ESP32 Dev Module (Dual-core 240 MHz, 4MB Flash) |
| **Display** | 1.3" / 1.54" ST7789 IPS LCD (240×240 / 240×280 via SPI) |
| **Keys** | 8× Mechanical Switches (Cherry MX / Gateron style) |
| **Encoders** | 3× EC11 Rotary Encoders with Integrated Push Buttons |
| **Connection** | USB Type-C (Serial over UART @ 115200 Baud) |

---

## 🚀 Getting Started

### 1. Running PeciTech Studio (Windows)

1. Ensure **Python 3.10+** is installed on your computer.
2. Clone this repository:
   ```bash
   git clone https://github.com/Pecislav/PeciTech-Studio.git
   ```
3. Navigate to the application folder and install dependencies:
   ```bash
   cd PeciTech-Studio/PeciTech/Aplikace
   pip install customtkinter pillow pyserial pywin32 websocket-client pystray requests keyboard
   ```
4. Launch the application:
   ```bash
   python main.py
   ```
   *Tip: You can also double-click `Spustit_Aplikaci.bat` for a one-click launch!*

---

### 2. Flashing the ESP32 Firmware

1. Install **[Arduino IDE](https://www.arduino.cc/en/software)** (or PlatformIO).
2. Add the ESP32 board package in Arduino IDE (*Boards Manager -> `esp32` by Espressif*).
3. Install required libraries:
   - `TFT_eSPI` (configured for ST7789)
   - `Encoder` or native interrupt pin config
4. Open `PeciTech/Finware/PeciDeck_Firmware/PeciDeck_Firmware.ino`.
5. Select board **ESP32 Dev Module**, choose your COM port, and click **Upload**.
6. Refer to [`PeciTech/Finware/NAVOD_K_NAHRANI.md`](PeciTech/Finware/NAVOD_K_NAHRANI.md) for pinout details and wiring diagrams.

---

## 🛠️ Built With

- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** – Modern, dark-themed GUI library
- **[Pillow](https://python-pillow.org/)** – Image processing and icon rendering
- **[PySerial](https://pythonhosted.org/pyserial/)** – Serial communication with the ESP32
- **[OBS-WebSocket](https://github.com/obsproject/obs-websocket)** – OBS Studio v5 control
- **[pystray](https://github.com/moses-palmer/pystray)** – Windows System Tray integration
- **[ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)** – Microcontroller firmware framework

---

## 📄 License & Credits

Distributed under the **MIT License**. Created with ❤️ for the **PeciTech** community by **Pecislav**.
