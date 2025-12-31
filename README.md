# Meshy Dashboard (Meshtastic Local UI)
## Screenshots

### Node table
![Node table](screenshots/Screenshot%20from%202025-12-31%2018-10-53.png)

### Map view
![Map view](screenshots/Screenshot%20from%202025-12-31%2018-11-13.png)


#'Screenshot from 2025-12-31 18-10-53.png'
#'Screenshot from 2025-12-31 18-11-13.png'


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

