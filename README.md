# FTP ZAN
<p align="center">
<img width="1536" height="1024" alt="ChatGPT Image Sep 4, 2025, 02_02_50 PM" src="https://github.com/user-attachments/assets/00ee4a7e-6514-4998-9eee-37d663e3f33e" />
</p>
# FTP ZAN

# Advanced FTP/SFTP Connection Tester

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

A powerful and flexible tool to test FTP/SFTP connections.  
Supports FileZilla XML import, direct host input, multi-threaded checking, and multiple output formats.

---

## ✨ Features

- ✅ Test **FTP** and **SFTP** connections  
- ✅ Import server settings from **FileZilla XML**  
- ✅ Support for **custom ports**  
- ✅ Multi-threaded checks with configurable workers  
- ✅ Path existence check on remote servers  
- ✅ Export results to **TXT, XML, JSON, CSV**  
- ✅ Debug mode for troubleshooting  
- ✅ Quiet mode for silent operations  

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/CodeZANKO/FTP-ZAN.git
cd FTP-ZAN
````

Make sure you have **Python 3.8+** installed.
Install dependencies if any (e.g., `paramiko` for SFTP):

```bash
pip install -r requirements.txt
```

---

## ⚡ Usage

```bash
python ftp_checker.py [-h] (--filezilla-xml FILEZILLA_XML | --host HOST)
                      [--port PORT] [--username USERNAME] [--password PASSWORD]
                      [--protocol {0,1}] [--timeout TIMEOUT]
                      [--max-workers MAX_WORKERS] [--check-path CHECK_PATH]
                      [--txt TXT] [--xml XML] [--json JSON] [--csv CSV]
                      [--quiet] [--debug]
```

---

## 🔧 Options

| Argument           | Description                                      |
| ------------------ | ------------------------------------------------ |
| `-h, --help`       | Show help message and exit                       |
| `--filezilla-xml`  | Path to FileZilla XML configuration file         |
| `--host`           | FTP/SFTP server hostname or IP address           |
| `--port`           | Server port (default: 21 for FTP, 22 for SFTP)   |
| `--username`       | Username for authentication                      |
| `--password`       | Password for authentication                      |
| `--protocol {0,1}` | Protocol: `0` for FTP, `1` for SFTP (default: 0) |
| `--timeout`        | Connection timeout in seconds                    |
| `--max-workers`    | Maximum concurrent connections                   |
| `--check-path`     | Path to check on the server                      |
| `--txt`            | Output TXT filename                              |
| `--xml`            | Output XML filename                              |
| `--json`           | Output JSON filename                             |
| `--csv`            | Output CSV filename                              |
| `--quiet`          | Suppress console output                          |
| `--debug`          | Enable debug logging                             |

---

## 📚 Examples

### Test a single FTP server

```bash
python ftp_ZAN.py --host ftp.example.com --username user --password pass
```

### Test an SFTP server on custom port

```bash
python ftp_ZAN.py --host sftp.example.com --port 2222 --username user --password pass --protocol 1
```

### Import from FileZilla XML and save results

```bash
python ftp_ZAN.py --filezilla-xml SiteManager.xml --json results.json --csv results.csv
```

### Run with 10 concurrent workers and check path

```bash
python ftp_ZAN.py --filezilla-xml servers.xml --max-workers 10 --check-path /uploads
```

---

## 🖥️ Demo (Sample Output)

```bash
$ python ftp_ZAN.py --host ftp.example.com --username user --password pass

[✔] Connected successfully: ftp.example.com:21
[✔] Login successful: user
[✔] Path check passed: /
[ℹ] Protocol: FTP
[ℹ] Response time: 0.45s

$ python ftp_ZAN.py --host sftp.example.com --port 2222 --username wrong --password wrong --protocol 1

[✖] Connection failed: Authentication error
```

---

## 📤 Output Formats

* Console output (unless `--quiet` is used)
* Export formats:

  * `.txt`
  * `.xml`
  * `.json`
  * `.csv`

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

Developed by **\[Zanko H. Aziz]** 🚀


