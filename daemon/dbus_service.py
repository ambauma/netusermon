import sqlite3
import signal
from pydbus import SystemBus
from gi.repository import GLib
from common import constants
from daemon.storage import init_db

class NetUserMonService:
    """
    <node>
        <interface name="org.netusermon.Daemon">
            <method name="GetLogs">
                <arg type="i" name="limit" direction="in"/>
                <arg type="a(isss)" name="logs" direction="out"/>
            </method>
            <method name="ClearLogs">
            </method>
        </interface>
    </node>
    """

    def GetLogs(self, limit):
        conn = sqlite3.connect(constants.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, username, domain FROM dns_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs

    def ClearLogs(self):
        conn = sqlite3.connect(constants.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dns_logs')
        conn.commit()
        conn.close()

def run_dbus_service():
    # Ensure database is initialized
    init_db()
    
    bus = SystemBus()
    bus.publish(constants.DBUS_BUS_NAME, NetUserMonService())
    loop = GLib.MainLoop()
    
    def shutdown(sig=None, frame=None):
        if sig:
            print(f"Stopping D-Bus service (received signal {sig})...")
        else:
            print("Stopping D-Bus service...")
        loop.quit()

    # Register signal handlers in the main thread
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"D-Bus service {constants.DBUS_BUS_NAME} started")
    try:
        loop.run()
    except Exception as e:
        print(f"D-Bus service encountered an error: {e}")

if __name__ == "__main__":
    run_dbus_service()
