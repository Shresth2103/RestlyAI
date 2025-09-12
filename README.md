# RestlyAI
WORK BETTER, FEEL BETTER

Restly gently helps you solve all your eyecare needs while using your favourite device(will soon expand to other platforms) Restly helps you reduce eye strain, stay focused, and keep your energy up. No more headaches, no more deteriorating eyesignt, no more thickening glasses.

Restly runs silently in the background and sends gentle popup notifications to remind you to take breaks, blink, and perform eye exercises based on the 20-20-20 rule and follow best ergonomic practices for your health. Moreover you can setup your own customized notifications!

✨ Features
👁️ Built-in eye care routine - Guided eye exercises and neck stretches
🎨 Beautiful notifications - Elegant, non-intrusive popup design
🚀 Auto-start - Automatically starts with your system
🎯 Custom messages - Create your own popup messages
⏰ Active hours - Only show popups during specified time periods
🕐 Customizable intervals - Set break popups at your preferred frequency
🔧 Swift operation - Runs quietly in the background. Easy to start, configure and stop
📦 Installation
Prerequisites
You'll need GTK+3 development libraries installed:

# Ubuntu/Debian
sudo apt install libgtk-3-dev

# Fedora
sudo dnf install gtk3-devel

# Arch Linux
sudo pacman -S gtk3
Quick Install
Clone the repository:
git clone https://github.com/Shresth2103/RestlyAI.git
cd restly
Run the installer:
chmod +x install.sh
./install.sh
The installer will:

Compile the application
Install it to ~/.local/bin/
Add the directory to your PATH
Set up autostart configuration
Optionally start the daemon immediately
🚀 Usage
Basic Usage
# Start with default settings (20-minute intervals, eye care routine)
restly

# Custom interval (30 minutes)
restly --interval 30

# Custom message instead of eye care routine
restly --message "Time for a coffee break!" --eyecare 0

# Active during work hours only
restly --active-hours 09:00-17:00
Command Line Options
Option	Short	Description	Default
--interval	-i	Break interval in minutes	20
--duration	-d	Popup duration in seconds	20
--message	-m	Custom popup message	"Time to rest your eyes! (if eyecare disabled)"
--eyecare	-e	Enable eye care routine (1) or custom message (0)	1
--active-hours		Active time range (e.g., 09:00-17:00)	00:00-23:59
--stop		Stop the running daemon	
Eye Care Routine
When --eyecare 1 is enabled, Restly guides you through a quick and easy yet cruicial routine.

This routine is based on the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds.

Managing the Daemon
# Start the daemon
restly --interval 25 --eyecare 1

# Stop the daemon
restly --stop





🙏 Acknowledgments
Inspired by the 20-20-20 rule for eye health
Built with GTK3 for native Linux integration
Thanks to all future contributors and users providing feedback in advance. You guys are awesome.
💡 Tips for Healthy Computer Usage
Follow the 20-20-20 rule: Every 20 minutes, look 20 feet away for 20 seconds
Blink frequently: Computer work reduces blink rate by up to 60%
Adjust screen brightness: Match your display to surrounding lighting
Position your screen: 20-24 inches away, top at or below eye level
Take regular breaks: Stand, stretch, and move around
Stay hydrated: Keep water nearby and drink regularly
Made with ❤️ for healthier computing KREDNIE
