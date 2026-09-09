# CH32V203G8R6 based HappyBell
## Project Overview

This project implements a simple HappyBell player using:

- CH32V203G8R6 RISC-V MCU
- MicroSD card with FAT32 filesystem
- Helix MP3 decoder software
- PWM based audio DAC
- Analog low pass filter
- 16x2 LCD display
- Control keys
- Relay outputs
- I2C expansion interface

The goal is to create a low-cost embedded MP3 player without using an external MP3 decoder IC such as VS1053.

---

# Hardware Architecture

```
                 CH32V203G8R6

                      |
          +-----------+------------+
          |                        |
       SPI1                      TIMER1
          |                        |
     MicroSD Card              PWM DAC
          |                        |
        FAT32                   LPF Filter
          |                        |
      MP3 File                  AUX OUT
          |
     FatFs Driver
          |
    Helix MP3 Decoder
          |
      PCM 16-bit
          |
    PWM Audio Buffer


          I2C
           |
          RTC


          GPIO
           |
   LCD / Keys / Relay
```

---

# Main Features

## Audio

- MP3 playback from MicroSD
- FAT32 filesystem support
- Software MP3 decoding
- Stereo PCM output
- PWM DAC output
- Analog AUX output

Supported target:

| Parameter | Value |
|-|-|
| Sampling Rate | 44.1 kHz |
| Bit Depth | 16-bit |
| Channel | Stereo |
| MP3 Bitrate | 32-192 kbps |

---

# Hardware Components

## MCU

### CH32V203G8R6

Specification:

| Item | Value |
|-|-|
| Core | RISC-V |
| Frequency | 144 MHz |
| Flash | 64 KB |
| SRAM | 20 KB |
| Package | QSOP28 |
| Voltage | 3.3V |

---

# Pin Assignment

## Final Pin Mapping

| Pin No | MCU Pin | Function |
|-|-|-|
| 1 | PA14 | SWD CLK Debug |
| 2 | PB6 | I2C SCL |
| 3 | PB7 | I2C SDA |
| 4 | BOOT0 | Boot Select |
| 5 | PB8 | LCD D7 |
| 6 | VDD | 3.3V Supply |
| 7 | VSS | Ground |
| 8 | NRST | Reset |
| 9 | PA0 | Key 1 |
| 10 | PA1 | Key 2 |
| 11 | PA2 | Key 3 |
| 12 | PA3 | Relay Output 1 |
| 13 | PA6 | SD Card MISO |
| 14 | PB0 | Relay Output 2 |
| 15 | PA4 | SD Card CS |
| 16 | PA5 | SD Card SCK |
| 17 | PA7 | SD Card MOSI |
| 18 | PB10 | LCD D4 |
| 19 | PB11 | LCD D5 |
| 20 | PB1 | LCD D6 |
| 21 | PB13 | LCD RS |
| 22 | PB14 | LCD EN |
| 23 | PB15 | Spare GPIO |
| 24 | PA8 | PWM Audio Output |
| 25 | PA9 | UART TX Debug |
| 26 | PA10 | UART RX Debug |
| 27 | PA11 | Spare GPIO |
| 28 | PA13 | SWD IO Debug |

---

# Peripheral Mapping

## MicroSD Interface

Interface:

```
SPI1

PA5  -> SD_CLK
PA6  -> SD_MISO
PA7  -> SD_MOSI
PA4  -> SD_CS
```

Filesystem:

- FAT32
- 512 byte sector access
- Long file name support optional

---

# LCD Interface

Display:

- 16x2 Character LCD
- HD44780 compatible
- 4-bit mode


Connection:

| LCD | MCU |
|-|-|
| RS | PB13 |
| EN | PB14 |
| D4 | PB10 |
| D5 | PB11 |
| D6 | PB1 |
| D7 | PB8 |


LCD Functions:

- File name display
- Playback status
- Volume
- Track number

---

# Key Interface

Three keys:

| Key | Function |
|-|-|
| KEY1 | Play / Pause |
| KEY2 | Next Track |
| KEY3 | Previous Track |


Pins:

```
KEY1 -> PA0
KEY2 -> PA1
KEY3 -> PA2
```

Recommended:

- Internal pull-up enabled
- Switch to GND

---

# Relay Outputs

Two GPIO outputs:

| Relay | MCU |
|-|-|
| Relay 1 | PA3 |
| Relay 2 | PB0 |


Driver:

```
MCU GPIO
   |
NPN/MOSFET Driver
   |
Relay Coil
```

Protection:

- Flyback diode required

---

# PWM Audio DAC

PWM Output:

```
PA8
 |
TIM1_CH1
 |
PWM
 |
Low Pass Filter
 |
AUX OUT
```

Target:

| Parameter | Value |
|-|-|
| PWM Frequency | 100-200 kHz |
| Resolution | 10-12 bit |
| Audio Rate | 44.1 kHz |

---

# Audio Processing Flow

```
MP3 File

   |

FatFs Read

   |

MP3 Frame Buffer

   |

Helix Decoder

   |

PCM 16-bit Samples

   |

PWM DMA Buffer

   |

Timer PWM Output

   |

LPF

   |

Analog Audio
```

---

# Recommended Audio Filter

2nd order low pass filter:

Target:

```
Cutoff > 20kHz
PWM ripple attenuation
```

Example:

```
PWM

 |
 R
 |
 +------ AUDIO OUT
 |
 C
 |
 GND

```

For better quality:

Use active Sallen-Key filter.
