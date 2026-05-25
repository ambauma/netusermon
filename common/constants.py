import os

DBUS_INTERFACE = "org.netusermon.Daemon"
DBUS_PATH = "/org/netusermon/Daemon"
DBUS_BUS_NAME = "org.netusermon.Daemon"

def __getattr__(name):
    if name == "DB_PATH":
        return os.environ.get("NETUSERMON_DB_PATH", "/var/lib/netusermon/data.db")
    if name == "CONFIG_DIR":
        return os.environ.get("NETUSERMON_CONFIG_DIR", "/etc/netusermon")
    raise AttributeError(f"module {__name__} has no attribute {name}")
