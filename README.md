# Meshy Dashboard (Meshtastic Local UI)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](#requirements)
[![Flask](https://img.shields.io/badge/Flask-Web%20UI-black.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux-lightgrey.svg)](#)

A desktop-friendly **Meshtastic node list + map** you can run on your LAN (e.g. on a Raspberry Pi gateway).
It’s basically the same “Nodes + Map” view you see in the phone app — but on a bigger screen, so you don’t need to keep your phone open while working at a desk.

Meshy Dashboard is aimed at low-power gateways and headless systems — it runs directly on the node or gateway and is viewable from any device on the LAN.

It’s designed for ARM, older hardware, and solar/battery setups.

## Screenshots

**Node table**
![Table view](screenshots/Screenshot%20from%202025-12-31%2018-11-13.png)
**Map view**
![Map view](screenshots/Screenshot%20from%202025-12-31%2018-10-53.png)
## Features

- Live **node table** from `meshtastic --nodes`
- **Map view** (Leaflet) using node latitude/longitude
- Status classification (active / stale / missing) based on “last heard”
- Runs locally on a LAN (no cloud required)
- Systemd service example included (auto-start on boot)

## Requirements

- Linux (tested on Raspberry Pi OS / Debian)(Raspberry Pi Zero W 32bit)
- Python 3.9+ (3.11 is fine)
- A working Meshtastic CLI install (or venv path) (See bottom of page)
- Network access to your Meshtastic device / gateway IP

## Quick start

```bash
git clone https://github.com/turbo399/meshy-dashboard.git
cd meshy-dashboard

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

#open in browser
http://<pi-ip>:5001 (Meshy-Dasboard)

## Docker (optional)

If you prefer Docker:

“Docker is the easiest on Pi 4 / Pi 5 / home servers. For ultra-low power (Pi Zero / 32-bit), venv + systemd is lighter.”

```bash
git clone https://github.com/turbo399/meshy-dashboard.git
cd meshy-dashboard

docker compose up -d --build

Open:
http://<host-ip>:5001(Meshy-Dasboard)

docker-compose.yml`
services:
  meshy-dashboard:
    build: .
    container_name: meshy-dashboard
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      RADIO_HOST: "YOUR_IP"
      # Optional
      # REFRESH_SECONDS: "200"
    # If your app writes cache files, you can persist them:
    volumes:
      - ./data:/app/data

Open:
http://<host-ip>:5001(Meshy-Dasboard)
---

# One important reality check
If your Pi is **super low power** (Pi Zero / 32-bit), Docker *might* still work, but:
- it’s heavier than venv + systemd
- build time is slower
- RAM pressure is higher
---

### Meshtastic CLI

Meshy Dashboard uses the Meshtastic CLI.

Install (system-wide):

    pip install meshtastic

Or in a virtual environment:

    python3 -m venv ~/meshtastic-venv
    source ~/meshtastic-venv/bin/activate
    pip install meshtastic

If installed in a venv, set:

    export MESHTASTIC_BIN=~/meshtastic-venv/bin/meshtastic

Official docs:
https://meshtastic.org/docs/software/python/cli/

