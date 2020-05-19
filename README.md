# RPi_Antenna_Driver
This repository contains a Python3 Tkinter GUI script written for Raspberry Pi (RPi) SBC hardware. The script controls a DC motor-tuned antenna via an H-Bridge and pulse encoder feedback. The H-Bridge drives single DC motor using Pulse Width Modulation (PWM). The antenna must contain a simple pulse encoder output such as a reed switch activated by the antenna's drive mechanism. One compatible antenna is called a "Screwdriver Antenna" such as those made by Scorpion Antennas, Tarheel Antennas, Hi-Q-Antennas™, among others. Another antenna might be a tuned loop with a multi-turn variable capacitor.

Due to the fast response of the Raspberry Pi hardware I/O, it is highly recommended the encoder signal be conditioned and isolated with an opto-coupler and Schmitt trigger. One such integrated circuit that contains both is the ON Semiconductor / Fairchild H11L1M. An example schematic is available in this repository (RPiAntDrv Example Schematic.pdf).

**Dependencies:** See requirements.txt file in this repository. May also work fine with latest Python3 and RPi libraries.

**Installation:** Refer to RPiAntDrv Users Guide.md in this repository.

**Screen shot:**

![Alt text](RPiAntDrv_Screenshot.png?raw=true "Screenshot")

*This open source project is licensed under the terms of the MIT license.*