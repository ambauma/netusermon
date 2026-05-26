# Project Specification: NetUserMon
**Version:** 0.1.0-alpha  
**License:** GNU GPLv3  
**Target Environment:** Linux Desktop (GNOME 40+ / Wayland / Systemd)  
**Primary Language:** Python 3  

---

## 1. Executive Summary & Intent
NetUserMon is a light, native Linux system utility designed to aggregate, audit, and log user-specific web browsing and search history on a shared or dedicated local machine. While generically architected as a device-auditing tool, its primary design constraint is robust, un-bypassable parental transparency. 

Unlike network-level DNS logging (which only resolves down to a device IP), NetUserMon explicitly bridges network packets to the unique Unix User ID (`uid`) that generated them, maintaining absolute user separation on shared hardware.

---

## 2. Core Architectural Design (Split-Layer & Modular)
To satisfy the Linux security model and modern Wayland display server restrictions, NetUserMon uses a modular split-process architecture:

+-----------------------------------------------------------+
|               Modular Frontends (User Space)              |
|   - GUI: Native GNOME GTK4 / Libadwaita                   |
|   - CLI: Python-based terminal tool (Future)              |
|   - KDE: Qt-based interface (Future)                      |
+-----------------------------+-----------------------------+
|
Secure D-Bus Queries (Dynamic Introspection)
|
v
+-----------------------------------------------------------+
|             Root Background Daemon (System Space)         |
|       - Runs continuously as a root systemd service       |
+--------+--------------------+--------------------+--------+
|                    |                    |
Configures Policy     Reads Sessions       Captures Packets
|                    |                    |
v                    v                    v
+------------------+ +------------------+ +------------------+
|   Enterprise     | |    loginctl      | |   iptables       |
| Browser Policies | | (systemd-logind) | |  -j NFQUEUE      |
|                  | |                  | |                  |
| - Disables DoH   | | - Tracks active  | | - Intercepts UDP |
| - Locks History  | |   sessions/UIDs  | |   Port 53 DNS    |
+------------------+ +------------------+ +--------+---------+
|
Saves Aggregated
Data Rows To
|
v
+------------------+
|   Protected      |
|   SQLite DB      |
|                  |
| /var/lib/        |
| netusermon/      |
+------------------+

### A. The Backend Daemon (`daemon/`)
* **Privilege:** Runs continuously in the background as `root` via a custom systemd service.
* **Network Hook:** Appends kernel rules via `iptables`/`nftables` to direct outbound Port 53 (DNS) queries into a user-space queue (`-j NFQUEUE`).
* **Packet Processing:** Uses `python-netfilterqueue` and `Scapy` to intercept DNS packets mid-flight, extract the requested domain string, and read the network socket owner's `uid`.
* **Session Tracking:** Interacts with `systemd-logind` via D-Bus to monitor `loginctl` states, matching UIDs to active human user accounts (e.g., `alice`, `bob`).
* **Storage:** Writes timestamps, usernames, and resolved domains to a local SQLite database secured in a root-only directory (`/var/lib/netusermon/data.db`).

### B. The Modular Frontends (e.g., `gui-gnome/`)
* **Privilege:** Run in standard **User Space** under the administrator/parent's account profile.
* **IPC Channel:** Communicate securely with the root daemon using custom **D-Bus** methods to query logs, view statistical charts, or change configurations.
* **GNOME Interface:** Built with Python (**PyGObject**), **GTK4**, and **Libadwaita** to match modern native GNOME design patterns.
* **Elevation:** Uses **Polkit (Privilege Authority)** to prompt for the admin password on first run or when updating system configurations.

---

## 3. Critical Technical Countermeasures
To guarantee logging accuracy, NetUserMon deploys system-wide overrides to prevent tech-savvy bypasses:

* **Encrypted DNS Defeat:** Writes a mandatory JSON system file to `/etc/firefox/policies/policies.json` (and Chromium counterparts) that explicitly disables DNS-over-HTTPS (DoH). This forces browsers to drop back to standard system DNS routing where `NFQUEUE` can read the plaintext payloads.
* **Browser Integrity Lock:** The enterprise policy configuration explicitly disables Incognito/Private Browsing modes, blocks users from clearing browser history, and prevents disabling mandatory logging extensions.
* **Transparency Notifications:** Implements user privacy alerts by placing an autostart desktop entry in `/etc/xdg/autostart/`. Upon login, a user-space helper script triggers native desktop notifications via `GNotification` informing the child that device activity is monitored.
* **Asynchronous Weekly Reports:** The backend daemon utilizes Python's built-in `smtplib` and `jinja2` HTML templating to process database tables once a week and route a clean markdown summary report to the administrator's primary email via an input SMTP configuration relay.

---
## 4. Repository & Directory Target Blueprint (Monorepo)
```text
netusermon/
├── common/                  # Shared constants, D-Bus definitions, and utilities
├── daemon/                  # Core root service (DNS interception, SQLite, D-Bus server)
├── gui-gnome/               # GNOME GTK4 / Libadwaita frontend
├── cli/                     # (Future) Command-line interface frontend
├── etc/
│   ├── systemd/system/
│   │   └── netusermon.service       # Service manager profile
│   ├── dbus-1/system.d/
│   │   └── org.netusermon.Daemon.conf # D-Bus security policy
│   ├── xdg/autostart/
│   │   └── netusermon-alert.desktop # Automatic user notification hook
│   └── firefox/policies/
│       └── policies.json            # Base system-wide browser rules
└── GEMINI.md                        # This project specification file
```
