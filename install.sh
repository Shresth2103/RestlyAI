#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
cd "$script_dir"

app_name="Restly Eye Care"
bin_name="restly"
install_bin_dir="$HOME/.local/bin"
install_bin_path="$install_bin_dir/$bin_name"
wrapper_path="$install_bin_dir/restly-start"
systemd_user_dir="$HOME/.config/systemd/user"
unit_path="$systemd_user_dir/restly.service"
autostart_dir="$HOME/.config/autostart"
desktop_path="$autostart_dir/restly.desktop"

say() { printf "[*] %s\n" "$1"; }
ok()  { printf "[OK] %s\n" "$1"; }
fail() { printf "[!] %s\n" "$1" >&2; exit 1; }

say "Installing $app_name …"

command -v gcc >/dev/null 2>&1 || fail "gcc not found (install your C compiler)"
command -v pkg-config >/dev/null 2>&1 || fail "pkg-config not found"
command -v python3 >/dev/null 2>&1 || fail "python3 not found"
if ! pkg-config --exists gtk+-3.0; then
  fail "GTK+3 development libraries not found. Install with:\n  - Debian/Ubuntu: sudo apt install libgtk-3-dev\n  - Fedora:        sudo dnf install gtk3-devel\n  - Arch:          sudo pacman -S gtk3"
fi

# Check Python dependencies
say "Checking Python dependencies..."
python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || fail "PyGObject not found. Install with:\n  - Debian/Ubuntu: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0\n  - Fedora:        sudo dnf install python3-gobject gtk3\n  - Arch:          sudo pacman -S python-gobject gtk3"
python3 -c "import httpx" 2>/dev/null || fail "httpx not found. Install with:\n  - Debian/Ubuntu: sudo apt install python3-httpx\n  - Fedora:        sudo dnf install python3-httpx\n  - Arch:          sudo pacman -S python-httpx"
python3 -c "import aiohttp" 2>/dev/null || fail "aiohttp not found. Install with:\n  - Debian/Ubuntu: sudo apt install python3-aiohttp\n  - Fedora:        sudo dnf install python3-aiohttp\n  - Arch:          sudo pacman -S python-aiohttp"

ok "Build prerequisites present"

say "Compiling $bin_name …"
mkdir -p "$install_bin_dir"

# Use Makefile for proper build with all dependencies
make clean
make all

install -m 0755 "$bin_name" "$install_bin_path"
ok "Installed binary to ${install_bin_path/$HOME/~}"

# Install Python scripts
say "Installing Python scripts..."
install -m 0755 restly_controller.py "$install_bin_dir/"
install -m 0755 daily_summary.py "$install_bin_dir/"
install -m 0755 ai_summary.py "$install_bin_dir/"
install -m 0755 setup_gemini.py "$install_bin_dir/"
install -m 0755 dashboard_server.py "$install_bin_dir/"
ok "Installed Python scripts to ${install_bin_dir/$HOME/~}"

cat > "$wrapper_path" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
# Do not start a duplicate instance if one is already running for this user
if pgrep -x "restly" >/dev/null 2>&1; then
  exit 0
fi
exec "$HOME/.local/bin/restly" \
  --interval 20 \
  --duration 20 \
  --eyecare 1 \
  --active-hours 00:00-23:59
EOF
chmod +x "$wrapper_path"
ok "Created launcher ${wrapper_path/$HOME/~}"

use_systemd=0
if command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1; then
  mkdir -p "$systemd_user_dir"
  cat > "$unit_path" <<EOF
[Unit]
Description=$app_name
After=graphical-session.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=%h/.local/bin/restly-start
ExecStop=%h/.local/bin/restly --stop

[Install]
WantedBy=default.target
WantedBy=graphical-session.target
EOF
  if systemctl --user daemon-reload >/dev/null 2>&1 && \
     systemctl --user enable --now restly.service >/dev/null 2>&1; then
    ok "Enabled systemd user service (restly.service)"
    use_systemd=1
  else
    say "systemd user enable failed; proceeding with desktop autostart"
  fi
else
  say "systemd user not available; using desktop autostart"
fi

mkdir -p "$autostart_dir"
cat > "$desktop_path" <<EOF
[Desktop Entry]
Type=Application
Name=$app_name
Comment=Eye care reminder daemon
Exec=$wrapper_path
Icon=applications-utilities
StartupNotify=false
NoDisplay=true
Hidden=false
X-GNOME-Autostart-enabled=true
OnlyShowIn=GNOME;KDE;XFCE;LXDE;LXQt;Unity;
X-GNOME-Autostart-Delay=5
EOF

if [[ "$use_systemd" -eq 1 ]]; then
  sed -i 's/^Hidden=false/Hidden=true/' "$desktop_path" || true
  ok "Autostart .desktop created (hidden; managed by systemd)"
else
  ok "Autostart entry created at ${desktop_path/$HOME/~}"
fi

if [[ "$use_systemd" -ne 1 ]]; then
  nohup "$wrapper_path" >/dev/null 2>&1 &
  ok "$bin_name started in background"
fi

printf "\nInstallation complete!\n"
printf '%s\n' "- Binary:   ${install_bin_path/$HOME/~}"
printf '%s\n' "- Launcher: ${wrapper_path/$HOME/~}"
printf '%s\n' "- Controller: ${install_bin_dir/$HOME/~}/restly_controller.py"
printf '%s\n' "- Dashboard: ${install_bin_dir/$HOME/~}/dashboard_server.py"
if [[ "$use_systemd" -eq 1 ]]; then
  printf '%s\n' "- systemd:  ${unit_path/$HOME/~}"
fi
printf '%s\n' "- Autostart: ${desktop_path/$HOME/~}"
printf "\nrestly is not running right now!\n"
printf "\nNew Features:\n"
printf "  - Activity tracking and AI-powered summaries\n"
printf "  - Beautiful web dashboard with Apple Watch-style rings\n"
printf "  - Python controller GUI for easy management\n"
printf "  - Google Gemini AI integration\n"
printf "\nTo get started:\n"
printf "  1. Run: restly_controller.py (GUI interface)\n"
printf "  2. Or: restly (command line daemon)\n"
printf "  3. Setup AI: setup_gemini.py (optional)\n"
printf "\nMade with ❤ | KREDNIE\n"
