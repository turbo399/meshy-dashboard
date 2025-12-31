# Meshy Dashboard (Meshtastic Local UI)


A desktop-friendly **Meshtastic node list + map** (Flask web UI) for use on a LAN.
It’s basically what you see in the phone app (nodes + map), but handy on a desk screen without needing your phone.

## Features
- Live node table using `meshtastic --nodes`
- Status buckets: **Active / Stale / Missing** based on RF "LastHeard/Since"
- Map view with node markers + popups
- Uses your local Meshtastic radio (via IP host)

## Requirements
- Linux (tested on Raspberry Pi OS)
- Python 3
- Meshtastic CLI installed and working against your radio

## Quick start

### 1) Clone
```bash
git clone https://github.com/turbo399/meshy-dashboard.git
cd meshy-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export RADIO_HOST=<YOUR_MESH_DEVICE_IP_HERE>
python app.py

http://<pi-ip>:5001 (Meshy-Dasboard)

