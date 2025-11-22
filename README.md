# ZestyPing

ZestyPing is a multi-host ping and latency visualization tool built with Python and Tkinter.

It’s designed for network engineers (and curious humans) who want a quick way to:

- Continuously ping multiple hosts (IP, FQDN, or subnets via CIDR/ranges)
- See live latency graphs over time
- Capture packet loss and jitter at a glance
- Generate a run summary with useful statistics for documentation or email

---

## ✨ Features

- **Multi-host pinging**
  - Add single hosts, ranges, or CIDR blocks
  - Bulk add via text *or* CSV (host + description)
- **Live summary table**
  - Host, IP, description
  - Last latency
  - Min / Avg / Max
  - Loss %, Sent, Recv
  - Last seen time
- **Live latency graph**
  - Per-host lines on a single chart
  - X-axis shows real time (`HH:MM:SS`)
- **Run Summary pane**
  - Per-host stats over the run (Min / Avg / Max / StDev)
  - Optional analytics hooks via `analytics.py`
  - Copy summary as TSV for easy paste into Excel/Sheets
- **Host descriptions**
  - Short (20-char) description per host (e.g. “Core SVI Bldg A”)
  - Persisted between runs in `config.json`
- **Bulk CSV import**
  - First column: host / range / CIDR
  - Second column: description
  - Subnets/ranges expand into individual hosts, each tagged with that description
- **Nice touches**
  - “Help → About ZestyPing” dialog with version info and link back to [ZestyMoo.com](https://zestymoo.com)
  - Configurable ping interval, timeout, and sample window size
  - Settings saved to `config.json`

---

## 🧰 Prerequisites

- **Operating System:** Windows 10/11 (Linux/macOS may also work but are not the primary target)
- **Python:** 3.10+ recommended
- **Internet / Network access:** To reach the hosts you’re pinging

If you don’t have Python yet, follow the steps below.

---

## 🐍 Install Python on Windows

1. **Download Python**
   - Go to the official Python website:  
     https://www.python.org/downloads/windows/
   - Download the latest stable **Python 3.x** Windows installer (64-bit).

2. **Run the installer**
   - Double-click the downloaded `.exe`.
   - **Important:** On the first screen, check the box:
     > ✅ “Add Python 3.x to PATH”
   - Click **Install Now** (or **Customize installation** if you prefer, but defaults are usually fine).

3. **Verify installation**
   - Open **Command Prompt** or **PowerShell**.
   - Run:
     ```powershell
     python --version
     ```
     or
     ```powershell
     py --version
     ```
   - You should see something like:
     ```text
     Python 3.12.1
     ```

If that works, you’re good to go.

---

## 📦 pip (Python package manager)

Modern Python installers for Windows include `pip` by default. To confirm:

```powershell
python -m pip --version
```

If you see a version string (e.g. `pip 24.x`), you’re set.

If for some reason `pip` is missing:

1. Try bootstrapping it with `ensurepip`:
   ```powershell
   python -m ensurepip --upgrade
   ```
2. Then verify again:
   ```powershell
   python -m pip --version
   ```

From here on, we’ll use `python -m pip` so it always targets the right Python install.

---

## 📥 Getting ZestyPing

Clone the repository or download it as a ZIP.

### Option 1: Clone with Git

```powershell
cd C:\path\where\you\want\the\project
git clone https://github.com/your-org-or-user/zesty-ping.git
cd zesty-ping
```

### Option 2: Download ZIP

1. Download the ZIP from your repo hosting (GitHub, etc.).
2. Extract it somewhere, e.g.:
   ```text
   C:\Users\YourName\Documents\ZestyPing\
   ```
3. Open a terminal (Command Prompt or PowerShell) and cd into that folder:
   ```powershell
   cd "C:\Users\YourName\Documents\ZestyPing"
   ```

---

## 📦 Install Python dependencies

From the ZestyPing project directory, run:

```powershell
python -m pip install -r requirements.txt
```

The `requirements.txt` includes:

- `matplotlib` (for the graphs)
- plus any other libraries ZestyPing needs

If you see errors, make sure:

- You’re using the **same** Python you installed earlier (`python --version`)
- You have an internet connection for `pip` to download packages

---

## 🚀 Running ZestyPing

From the project directory:

```powershell
python app.py
```

The ZestyPing GUI should open.

If Windows asks you about firewall rules when pinging, allow outbound ICMP (ping) as needed.

---

## 🧪 Basic Usage

1. **Configure interval / timeout / count**
   - Use the controls at the top:
     - **Interval:** How often to ping each host (seconds)
     - **Timeout:** Max wait per ping (ms)
     - **Count:** Number of pings per host for a run

2. **Add hosts**
   - On the left side:
     - Enter a host (IP or FQDN) and optional short description
     - Click **Add**
   - You can also use **Bulk Add…**:
     - Paste host lists / ranges / CIDRs in the text area  
       *or*
     - Use **Import CSV…** with:
       ```csv
       8.8.8.8,Google DNS
       10.0.0.0/29,Branch LAN Subnet
       ```

3. **Start the test**
   - Click **Start**
   - ZestyPing will:
     - Spawn workers per host
     - Populate the live table
     - Draw per-host latency lines over time

4. **Stop and review**
   - Click **Stop** (or let the run finish when `Count` is reached)
   - A **Run Summary** window opens:
     - Per-host stats: Sent / Recv / Loss%, Min / Avg / Max, StDev
     - Start time, End time, Duration
     - A static latency graph for the entire run
   - You can click **Copy TSV** to paste into Excel/Sheets for reports.

---

## ⚙️ Configuration & Persistence

ZestyPing stores user configuration in:

```text
config.json
```

This includes:

- Default hosts
- Per-host descriptions
- Interval / timeout defaults
- Sample window size

You can:

- Use the **Save Settings** button in the UI to persist changes.
- Manually edit `config.json` if needed (while the app is closed).

---

## 💡 Tips

- Use **descriptions** to label SVIs, WAN IPs, or devices so non-technical viewers know what each host represents (e.g. “Core SVI – HS”, “Branch Router”, “ISP GW”).
- Use **CSV bulk import** to load test scenarios quickly for different sites/customers.
- The **Run Summary** is great to screenshot or paste into emails for “before/after” comparisons.

---

## 🔍 Future Enhancements (Planned / In Progress)

Some ideas ZestyPing is evolving towards:

- Smarter analytics via `analytics.py`:
  - Outlier detection (pings above N standard deviations)
  - Loss and latency “episodes” (streaks of bad behavior)
  - Jitter scoring per host
- Export runs as CSV/JSON for offline analysis
- Per-host detail graphs and reports

---

## 🐄 Credits

ZestyPing is part of the broader **ZestyMoo** universe.  
Visit: https://zestymoo.com
