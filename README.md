# Cloudflare Dynamic DNS Updater

## Overview

This tool keeps your Cloudflare DNS "A" records updated with your current public IPv4 address, making it ideal for environments with dynamic IPs (e.g., home networks). It uses multiple fallback services to retrieve your public IP and maintains detailed logs with automatic compression and cleanup.

## Features

- **DNS Update:** Automatically updates Cloudflare DNS records when your IP changes.
- **Fallback System:** Uses multiple services to fetch your IP in case of failures.
- **Efficient Logging:** Logs events and errors, compresses old logs, and removes outdated ones.
- **Error Resilience:** Skips recently failed services to ensure reliability.

## Requirements

- Python 3.8+
- A Cloudflare API token with DNS edit permissions.
- `pip` to install dependencies.
- Git (if cloning the repository).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SoBo7a/cloudflare-ddns-updater.git
cd <repo-name>
```

### 2. Install Dependencies
Create and activate a virtual environment (optional):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a .env file in the project root:
```
API_KEY=<your-cloudflare-api-key>
ZONE_ID=<your-cloudflare-zone-id>
```

## Usage
Run the updater:

```bash
python3 update_domains.py
```

To schedule this script via cron, add the following to your crontab:

1. Edit the crontab file:
```bash
crontab -e
```

2. Add an entry to run the script periodically. For example, to run it every 10 minutes:
```
*/10 * * * * /usr/bin/python3 /path/to/your/repo/update_domains.py
```
Replace /usr/bin/python3 with the full path to your Python 3 executable, and /path/to/your/repo with the directory containing the script.

3. Save and exit the crontab editor.

## Important Notes
Avoid running this script more frequently than once per minute to prevent throttling or blocking by IP provider services.
Ensure the environment variables in .env are correctly set and accessible.
Logs will be appended to /var/log/cloudflare_updater.log. You can change this path or include log rotation policies as needed.

## Logs
Logs are stored at /var/log/cloudflare/dns_update.log by default. You can change this path in the script. Old logs are compressed and removed based on retention settings.

## Customization
- IP Services: Add or adjust IP-fetching services in helper/ip_helper.py.
- Log Settings: Update log directory or retention policies in helper/custom_logger.py.

## License
This project is licensed under the [MIT License](LICENSE.txt).
