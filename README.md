<div align="center">

  <h1>PeciTech Studio 🎛️</h1>

  <p>
    <em><strong>The Ultimate Open-Source Stream Controller & Macro Deck Ecosystem</strong></em>
  </p>

  <p>
    <img src="https://img.shields.io/badge/VERSION-1.1.0--STABLE-FF7A29?style=for-the-badge" alt="Version" />
    <img src="https://img.shields.io/badge/PLATFORM-WINDOWS-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform" />
    <img src="https://img.shields.io/badge/HARDWARE-ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white" alt="Hardware" />
    <img src="https://img.shields.io/badge/DESIGN-DARK_CYBERPUNK-FF7A29?style=for-the-badge" alt="Design" />
  </p>
  <p>
    <img src="https://img.shields.io/badge/OBS_STUDIO-WEBSOCKET_V5-302E31?style=for-the-badge&logo=obsstudio&logoColor=white" alt="OBS Studio" />
    <img src="https://img.shields.io/badge/PYTHON-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/LICENSE-MIT-22C55E?style=for-the-badge" alt="License" />
  </p>

  <p>
    <strong>Complete All-in-One ecosystem engineered for streamers, video editors, and power users.<br>
    Tactile physical macro deck with dual-state buttons, rotary encoder audio scrubbing, and zero-latency hardware sync.</strong>
  </p>

</div>

---

## 🧭 About PeciTech Studio

**PeciTech Studio** is a modern desktop suite and companion microcontroller firmware built from the ground up to bring tactile, hardware-grade control to your daily workflow.

Featuring a sleek visual design with a cyberpunk-inspired dark palette (`#0B0B0E` with `#FF7A29` warm accent), smooth CustomTkinter controls, and real-time bidirectional USB-Serial communication, PeciTech Studio pairs seamlessly with the **PeciDeck MK.1** physical macro pad to replace fragile hotkey setups with an intuitive, unified workstation.

---

## 🧩 Key Features & Modules

### 🎛️ 1. PeciDeck MK.1 — Hardware Companion
- ⚡ **High-Speed Bidirectional Serial Bridge**: Real-time communication over USB-Serial (115200 baud) with sub-millisecond trigger latency.
- 🖥️ **Live TFT Screen Rendering**: Dynamic color screen rendering showing active button icons, labels, page indicators, and encoder levels on the ST7789 display.
- 🎚️ **Triple Precision Encoders with Push Buttons**: Smooth scrubbing for master audio, discrete OBS audio tracks, song seeking, display brightness, and scene cycling.

### 🎨 2. Desktop Studio Suite & Property Inspector
- 🖌️ **Modern Dark-Themed UI**: Clean, responsive layout crafted with CustomTkinter, featuring high-contrast typography and glowing active badges.
- 🔍 **Interactive Property Inspector**: Click any button or rotary dial on the virtual deck to instantly inspect and configure its action, target, custom icons, and typography.
- 🔄 **Dual-State Dynamic Buttons**: Set separate icons and labels for active vs. inactive states (e.g., Mic Muted / Unmuted, Camera On / Off) with live hardware sync.
- 📁 **Profile & Hierarchical Folder System**: Create dedicated profiles (`Stream`, `Gaming`, `Editing`) and nest actions into multi-level folders with one-touch navigation.

### 📹 3. Deep OBS Studio Integration (WebSocket v5)
- 🔊 **Rotary Encoder Audio Scrubbing**: Rotate knobs to adjust specific audio inputs (Spotify, Mic/Aux, Game Audio) in precise 2 dB increments, and click to toggle mute.
- 🎬 **Scene Management**: One-touch scene transitions with automatic scene list discovery and visual feedback.
- 🔴 **Broadcast & Recording Control**: Start, pause, and stop streaming or recording sessions with color-coded status badges.

### ⌨️ 4. Universal Smart Hotkey Engine
- 🌐 **Hardware Scan-Code Capture**: 100% layout-independent key recording using physical scan codes — zero conflicts between QWERTY, QWERTZ, or localized keyboards.
- ⏱️ **Guaranteed Background Key Injection**: 45 ms hold time prevents dropped keystrokes in background apps, Discord, DaVinci Resolve, and DirectX games.
- 🏷️ **Interactive Key Badge Recorder**: Press any physical key combination to see real-time visual badges (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>M</kbd>) and save instantly.

### ⚡ 5. Low-Latency Performance & Single Instance
- 🖱️ **Gaming Mouse Optimized (1000 Hz)**: Tuned GIL switch interval eliminates mouse stutter and cursor lag even during intense gameplay.
- 🛡️ **Win32 Mutex Protection**: Prevents duplicate application instances, guarantees clean COM port acquisition, and restores existing windows from the system tray automatically.

---

## 🔌 Hardware Specifications (PeciDeck MK.1)

| Component | Specification | Description |
| :--- | :--- | :--- |
| **Microcontroller** | ESP32 Dev Module | Dual-core 240 MHz, 4MB Flash, high-speed hardware SPI |
| **Display** | 1.3" / 1.54" ST7789 IPS LCD | 240×240 / 240×280 resolution, 16-bit high-contrast color |
| **Keys** | 8× Mechanical Switches | Cherry MX / Gateron style tactile mechanical switches |
| **Encoders** | 3× EC11 Rotary Encoders | 20 pulses/rev with integrated tactile push buttons |
| **Connection** | USB Type-C | Hardware UART serial communication @ 115200 Baud |

---

## 📁 Project Structure

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

## 🚀 Quick Start Guide

### 1. Desktop Application (Windows)

1. Ensure **Python 3.10+** is installed on your computer.
2. Clone this repository:
   ```bash
   git clone https://github.com/Pecislav/PeciTech-Studio.git
   ```
3. Navigate to the application directory and install dependencies:
   ```bash
   cd PeciTech-Studio/PeciTech/Aplikace
   pip install customtkinter pillow pyserial pywin32 websocket-client pystray requests keyboard
   ```
4. Launch the application:
   ```bash
   python main.py
   ```
   *Tip: You can also double-click `Spustit_Aplikaci.bat` for an instant one-click launch!*

---

### 2. Flashing the ESP32 Firmware

1. Install **[Arduino IDE](https://www.arduino.cc/en/software)** (or PlatformIO).
2. Install the **ESP32 board package** in Arduino IDE (*Boards Manager -> `esp32` by Espressif*).
3. Install required libraries:
   - `TFT_eSPI` (configured for ST7789)
   - `Encoder` or native hardware interrupt pins
4. Open `PeciTech/Finware/PeciDeck_Firmware/PeciDeck_Firmware.ino`.
5. Select board **ESP32 Dev Module**, choose your COM port, and click **Upload**.
6. Refer to [`PeciTech/Finware/NAVOD_K_NAHRANI.md`](PeciTech/Finware/NAVOD_K_NAHRANI.md) for wiring schematics and pin assignments.

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
