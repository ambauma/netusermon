#!/bin/bash
set -ex

echo "--- Entrypoint starting ---"
id
pwd

# 1. Setup D-Bus System Bus
echo "Setting up D-Bus..."
mkdir -p /var/run/dbus /var/lib/dbus /run/dbus

# Try to find the dbus user (usually 'dbus' or 'messagebus')
DBUS_USER=$(grep -E '^(dbus|messagebus):' /etc/passwd | cut -d: -f1 || echo "root")
echo "Using D-Bus user: $DBUS_USER"
chown "$DBUS_USER":"$DBUS_USER" /var/run/dbus /var/lib/dbus /run/dbus

# Robust Machine ID generation
if [ ! -f /etc/machine-id ]; then
    if command -v dbus-uuidgen >/dev/null 2>&1; then
        dbus-uuidgen --ensure=/etc/machine-id
    else
        # Fallback for minimal systems
        cat /proc/sys/kernel/random/uuid | tr -d '-' > /etc/machine-id
    fi
fi

# Start dbus-daemon
# Some systems have it in /usr/bin, others in /bin or /usr/sbin
DBUS_DAEMON_BIN=$(command -v dbus-daemon || echo "/usr/bin/dbus-daemon")
$DBUS_DAEMON_BIN --system --fork

# 2. Setup Iptables for NFQUEUE
echo "Setting up Iptables..."
if ! iptables -A OUTPUT -p udp --dport 53 -j NFQUEUE --queue-num 1; then
    echo "Failed to set up iptables NFQUEUE rule. Ensure the container has --privileged or NET_ADMIN capability."
    # Non-fatal for some test environments if we just want to test D-Bus
fi

# 3. Initialize Database directory
echo "Setting up Database directory..."
export NETUSERMON_DB_PATH="/var/lib/netusermon/data.db"
mkdir -p /var/lib/netusermon
chmod 777 /var/lib/netusermon
# Pre-create the DB file so it's writable by testuser
touch /var/lib/netusermon/data.db
chmod 666 /var/lib/netusermon/data.db

# 4. Start the daemon in the background, redirecting output to a log file
echo "Starting daemon..."
export PYTHONPATH=$PYTHONPATH:.
python3 -u daemon/main.py > /var/log/netusermon-daemon.log 2>&1 &
DAEMON_PID=$!

# Wait for daemon to initialize and register with D-Bus
echo "Waiting for org.netusermon.Daemon to appear on D-Bus..."
MAX_RETRIES=15
COUNT=0
while ! dbus-send --system --dest=org.freedesktop.DBus --type=method_call --print-reply /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep -q org.netusermon.Daemon; do
    if ! kill -0 $DAEMON_PID 2>/dev/null; then
        echo "Daemon process died unexpectedly. Logs:"
        cat /var/log/netusermon-daemon.log
        exit 1
    fi
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "Timeout waiting for daemon to register on D-Bus. D-Bus names:"
        dbus-send --system --dest=org.freedesktop.DBus --type=method_call --print-reply /org/freedesktop/DBus org.freedesktop.DBus.ListNames
        echo "Daemon logs:"
        cat /var/log/netusermon-daemon.log
        exit 1
    fi
done
echo "Daemon registered."

# 5. Keep the container alive for external orchestration
echo "Services ready. Waiting for instructions..."
wait $DAEMON_PID
