import sqlite3
from pydbus import SystemBus
from gi.repository import GLib
from common.constants import DB_PATH, DBUS_INTERFACE, DBUS_PATH, DBUS_BUS_NAME

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, username, domain FROM dns_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs

    def ClearLogs(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dns_logs')
        conn.commit()
        conn.close()

def run_dbus_service():
    bus = SystemBus()
    bus.publish(DBUS_BUS_NAME, NetUserMonService())
    loop = GLib.MainLoop()
    print(f"D-Bus service {DBUS_BUS_NAME} started at {DBUS_PATH}")
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping D-Bus service...")

if __name__ == "__main__":
    run_dbus_service()
