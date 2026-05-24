import threading
import signal
import sys
from daemon.interceptor import run_interceptor
from daemon.dbus_service import run_dbus_service

def main():
    # Start the Interceptor in a background thread
    interceptor_thread = threading.Thread(target=run_interceptor, daemon=True)
    interceptor_thread.start()

    # Start the D-Bus service in the main thread (or vice-versa)
    # D-Bus service handles its own main loop
    run_dbus_service()

if __name__ == "__main__":
    main()
