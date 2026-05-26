import threading
import signal
import sys
from daemon.interceptor import run_interceptor
from daemon.dbus_service import run_dbus_service
from daemon.storage import init_db

def main():
    # Initialize the database/directories before anything else
    print("Initializing NetUserMon Daemon...")
    init_db()

    # Start the Interceptor in a background thread
    interceptor_thread = threading.Thread(target=run_interceptor, daemon=True)
    interceptor_thread.start()

    # Start the D-Bus service in the main thread
    run_dbus_service()

if __name__ == "__main__":
    main()
