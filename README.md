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
git clone https://github.com/<YOUR_GITHUB_USER>/meshy-dashboard.git
cd meshy-dashboard
