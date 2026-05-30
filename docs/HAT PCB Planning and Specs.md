# Compact Raspberry Pi 5 / Pi 4 Retro TV HAT – Manufacturing Spec

## Overview

Design a compact Raspberry Pi HAT/HAT+ board for both Raspberry Pi 5 and Raspberry Pi 4.

The PCB must not exceed the footprint of a Raspberry Pi 5 board.

The board integrates:
- LCD display support
- Stereo audio amplification (2x10W)
- NVMe storage (M.2 2230)
- User control interfaces
- Power distribution for Pi + peripherals

The system is intended to function as a compact retro-style television for video playback.

---

# 🧾 Fabrication Settings (REQUIRED)

## Layer Stack
- **4-layer PCB (required for PCIe Gen3 + NVMe stability)**

---

## 📏 Manufacturing Specs

### Min Track / Spacing
- **6 / 6 mil (0.15 / 0.15 mm)**

Recommended balance of:
- PCIe signal integrity
- Manufacturability
- Cost control

---

### Surface Finish
- **ENIG (Electroless Nickel Immersion Gold)**

Required for:
- PCIe Gen3 signal integrity
- M.2 connector reliability
- Long-term oxidation resistance
- Fine-pitch component stability

---

### Via Process
- **Tented vias (standard)**

Optional upgrade (recommended for high-speed region):
- **Plugged + capped vias near PCIe / M.2 area**

---

### Finished Copper
- **1 oz outer copper (35 µm)**

---

### Inner Copper
- **0.5 oz inner copper (17 µm)**

---

# 📐 Stack-Up Requirement (CRITICAL)

Controlled impedance stack-up required:

- Layer 1: High-speed signals (PCIe, routing-critical nets)
- Layer 2: Continuous ground plane (no splits)
- Layer 3: Power distribution plane
- Layer 4: Low-speed signals / auxiliary I/O

## High-speed requirements:
- PCIe Gen3 differential impedance: **85Ω ±10%**
- Tight pair matching (≤ 5 mil preferred)
- Continuous ground reference under all high-speed traces

---

# ⚡ Power Integrity Requirements

The design must support:
- Raspberry Pi 5 system power
- NVMe SSD power spikes (>2–3A transient)
- 2x10W audio amplifier load
- LCD display power output (USB-C)

## Mandatory requirements:
- Do NOT rely on GPIO traces for primary power delivery
- Use wide copper pours / planes for all power nets
- Strong, uninterrupted ground plane continuity
- Local bulk capacitance near NVMe socket
- Dedicated **3.3V regulator near M.2 connector**

Poor power design may cause:
- Intermittent PCIe Gen3 instability
- False signal integrity diagnostics
- Random NVMe disconnects

---

# 🧠 PCIe / NVMe Routing Requirements

## Signal Integrity:
- 85Ω differential impedance target
- Length matching ≤ 5 mil preferred
- Continuous ground reference under pairs
- No sharp corners (45° or curved routing only)
- Minimize vias on PCIe lanes
- Avoid unnecessary layer transitions

## Mechanical / Electrical:
- M.2 2230 NVMe slot supported
- Stable Gen3 operation required under load

---

# 🔊 Audio System Requirements

Integrated amplifier:
- 2x10W stereo output

## Audio quality goals:
- No hiss or background noise
- No power-on or connect pop
- Low distortion output
- Clean separation from digital switching noise

## Recommended implementation:
- Separate analog and digital grounding strategy
- Optional dedicated analog regulator
- Output filtering on speaker lines
- Careful layout isolation from PCIe/NVMe zones

---

# 🔌 Connector Placement Requirements

## Rear Edge
- GPIO stacking header: top rear
- PCIe connector: left rear

## Power
- Main power input capable of supplying:
  - Raspberry Pi 5
  - NVMe SSD
  - LCD display
- USB-C power output dedicated to display

## Audio Outputs
- 2x screw terminals:
  - Left speaker terminal placed on RIGHT side of board
  - Right speaker terminal placed on LEFT side of board

## User Controls (Left Side)
- 1x volume control connector (analog)
- 1x left/right rotary control connector

---

# 🧩 Raspberry Pi HAT+ Compliance

Must include:
- HAT EEPROM
- Proper HAT+ mechanical and electrical compliance
- Correct PCIe capability advertisement for Pi 5

Avoid:
- Interference with cooling solutions
- Blocking display or enclosure mounting

---

# 🧪 Reliability & Manufacturing Goals

Design must prioritize:
- Stable long-term operation under thermal load
- EMI reduction (PCIe + switching audio coexistence)
- Clean power distribution architecture
- Ease of assembly and routing clarity

## Recommended:
- 4-layer impedance-controlled stack-up (mandatory)
- Solid ground plane (no segmentation)
- Clear silkscreen labeling for all connectors
- Proper decoupling near all power-hungry subsystems
- Test points for power rails and PCIe bring-up
