# Restly 

**WORK BETTER, FEEL BETTER**
**AI BASED EYE CARE AND PRODUCTIVITY APP**

**Restly gently helps you solve all your health and time management needs while using your favourite device(will soon expand to other platforms)**
**Restly helps you reduce eye strain,generate health and productivity reports, stay focused, and keep your energy up. No more headaches, no more deteriorating eyesignt, no more thickening glasses.**

Restly runs silently in the background and sends gentle popup notifications based on the 20-20-20 rule and follow best ergonomic practices for your health. Moreover you can setup your own customized notifications, all from the app or cli!

## ✨ Features

- 👁️ **Built-in eye care routine** - Guided eye exercises and neck stretches
- 🎨 **Beautiful notifications** - Elegant, non-intrusive popup design
- 🚀 **Auto-start** - Automatically starts with your system
- 🎯 **Custom messages** - Create your own popup messages
- ⏰ **Active hours** - Only show popups during specified time periods
- 🕐 **Customizable intervals** - Set break popups at your preferred frequency
- 🔧 **Swift operation** - Runs quietly in the background. Easy to start, configure and stop

## 📦 Installation

### Prerequisites

You'll need GTK+3 development libraries installed:

```bash
# Ubuntu/Debian
sudo apt install libgtk-3-dev

# Fedora
sudo dnf install gtk3-devel

# Arch Linux
sudo pacman -S gtk3
```

### Quick Install

1. Clone the repository:
```bash
git clone https://github.com/krednie/restly.git
cd restly
```

2. Run the installer:
```bash
chmod +x install.sh
./install.sh
```

The installer will:
- Compile the application
- Install it to `~/.local/bin/`
- Add the directory to your PATH
- Set up autostart configuration
- Optionally start the daemon immediately

## 🚀 Usage

### Basic Usage

```bash
# Start with default settings (20-minute intervals, eye care routine)
restly

# Custom interval (30 minutes)
restly --interval 30

# Custom message instead of eye care routine
restly --message "Time for a coffee break!" --eyecare 0

# Active during work hours only
restly --active-hours 09:00-17:00
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--interval` | `-i` | Break interval in minutes | `20` |
| `--duration` | `-d` | Popup duration in seconds | `20` |
| `--message` | `-m` | Custom popup message | `"Time to rest your eyes! (if eyecare disabled)"` |
| `--eyecare` | `-e` | Enable eye care routine (1) or custom message (0) | `1` |
| `--active-hours` | | Active time range (e.g., `09:00-17:00`) | `00:00-23:59` |
| `--stop` | | Stop the running daemon | |

### Eye Care Routine

When `--eyecare 1` is enabled, Restly guides you through a quick and easy yet cruicial routine.

This routine is based on the **20-20-20 rule**: Every 20 minutes, look at something 20 feet away for 20 seconds.


### Building Manually

```bash
gcc -o restly main.c config.c daemon.c timer.c popup.c $(pkg-config --cflags --libs gtk+-3.0)
```



***KREDNIE***
