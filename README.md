# NetUserMon

**Native User Activity Monitoring & Transparency for Linux**

NetUserMon is a lightweight, system-level utility designed to provide absolute transparency into web activity on shared or dedicated Linux desktops. Unlike network-wide filters that only identify devices, NetUserMon bridges the gap between network packets and the specific **Unix User ID (UID)** that generated them.

## 核心 (The Core): `netusermon-daemon`

The heart of the project is a root-level background service (`netusermon-daemon`) that ensures activity is logged accurately, regardless of which user is logged in.

### Key Features
*   **User-Specific Auditing**: Explicitly maps every DNS request to a local Linux username (e.g., `alice`, `bob`).
*   **Un-bypassable Logging**: Intercepts DNS queries at the kernel level using `NFQUEUE`, preventing users from bypassing logs via simple browser settings.
*   **Encrypted DNS Defeat**: (In progress) Automatically configures browser policies to disable DNS-over-HTTPS (DoH), ensuring transparency.
*   **Secure Storage**: Logs are saved to a protected SQLite database (`/var/lib/netusermon/data.db`) accessible only by the root user/administrator.
*   **High Performance**: Uses an optimized in-memory cache for user identity resolution to ensure minimal system impact.

## How it Works
1.  **Intercept**: The daemon uses `iptables` to route outbound DNS traffic into a secure processing queue.
2.  **Identify**: It identifies the owner of the network socket and maps their UID to a human-readable username.
3.  **Log**: The domain name, timestamp, and user identity are recorded for administrative review.

## Installation
NetUserMon is currently in early development. Automated builds generate native installers for major Linux distributions:

*   **Debian/Ubuntu**: `.deb` packages
*   **Fedora/RHEL**: `.rpm` packages

*Note: Administrative (root) privileges are required for installation and operation.*

## Verifying the Daemon
After installation, you can verify that the NetUserMon daemon is active and intercepting traffic:

1.  **Check Service Status**:
    ```bash
    systemctl status netusermon.service
    ```
2.  **Verify D-Bus Interface**:
    Use `busctl` to ensure the daemon has registered its secure communication channel:
    ```bash
    busctl introspect org.netusermon.Daemon /org/netusermon/Daemon
    ```
3.  **Monitor Live Logs**:
    If running the daemon manually for debugging, you will see output like:
    `Logging: alice (1000) -> google.com`

## Accessing Data
There are two primary ways to access the monitoring data:

### 1. Via D-Bus (Recommended)
You can query the daemon directly from the command line using `busctl`. For example, to get the last 5 logs:
```bash
busctl call org.netusermon.Daemon /org/netusermon/Daemon org.netusermon.Daemon GetLogs i 5
```

### 2. Direct Database Access
The raw logs are stored in a protected SQLite database. You must have root privileges to read it:
```bash
sudo sqlite3 /var/lib/netusermon/data.db "SELECT * FROM dns_logs ORDER BY timestamp DESC LIMIT 10;"
```

## Future Roadmap
While the backend daemon handles the heavy lifting of data collection, NetUserMon is architected to be modular. Future updates will include:
*   **GNOME GUI**: A native GTK4/Libadwaita dashboard for parents/administrators.
*   **CLI Tool**: A command-line interface for quick log querying.
*   **Automated Reports**: Weekly email summaries of user activity.

## License
NetUserMon is Open Source under the **GNU GPLv3** License.
