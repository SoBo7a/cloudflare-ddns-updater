import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
from helper.custom_logger import setup_logger, compress_old_logs, delete_old_gz_logs
from helper.ip_helper import get_public_ip, is_valid_ip

# Load environment variables from .env file
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Cloudflare API credentials
API_KEY = os.environ.get("API_KEY")
ZONE_ID = os.environ.get("ZONE_ID")

# Set up logging
log_file = '/var/log/cloudflare/dns_update.log'
logger = setup_logger(log_file)


def main():
    """
    Main function that checks if the public IP has changed and updates Cloudflare DNS records accordingly.
    """
    public_ip, service_name = get_public_ip(logger, log_file)

    if public_ip:
        logger.info(f"Current public IP: {public_ip} (from {service_name})")
        
        # Get the current DNS records
        dns_records = get_dns_records()

        if not dns_records:
            logger.warning("No valid DNS records found.")
            return

        # Iterate over DNS records and update them if the IP has changed
        for record in dns_records:
            if record['content'] != public_ip:
                logger.info(f"IP for {record['name']} has changed. Updating...")
                update_dns_record(record['id'], public_ip, dns_records)
            else:
                logger.info(f"IP for {record['name']} is already up-to-date.")
        
    log_dir = os.path.dirname(log_file)
    compress_old_logs(log_dir, 10080, 3) # 1 Week
    delete_old_gz_logs(log_dir, 40320, 4) # 4 Weeks


def get_dns_records():
    """
    Fetches all DNS records for the specified Cloudflare zone.

    Returns:
        list: A list of DNS records that have an IPv4 address.
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return parse_dns_records(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching DNS records: {e}")
        return []


def parse_dns_records(data):
    """
    Parses DNS records from the Cloudflare API response.

    Args:
        data (dict): The API response data.

    Returns:
        list: A list of DNS records that contain valid IPv4 addresses.
    """
    if not data.get("success"):
        logger.error(f"Error fetching DNS records: {data.get('errors')}")
        return []

    dns_records = []
    for record in data["result"]:
        if record['content'] and is_valid_ip(record['content']):
            dns_records.append({
                "id": record["id"],
                "name": record["name"],
                "content": record["content"]
            })
    return dns_records


def update_dns_record(record_id, new_ip, dns_records):
    """
    Updates a DNS record in Cloudflare with the new IP address.

    Args:
        record_id (str): The ID of the DNS record to update.
        new_ip (str): The new IP address to set.
        dns_records (list): The list of DNS records containing the record to update.
    """
    record = next((r for r in dns_records if r["id"] == record_id), None)
    if not record:
        logger.error(f"Record with ID {record_id} not found.")
        return

    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    data = {
        "type": "A",
        "name": record["name"],
        "content": new_ip,
        "ttl": 1,  # Automatic TTL
        "proxied": True  # Cloudflare proxy (orange cloud)
    }

    try:
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            logger.info(f"Successfully updated DNS record {record_id} to IP {new_ip}")
        else:
            logger.error(f"Error updating DNS record {record_id}: {result.get('errors')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating DNS record {record_id}: {e}")


if __name__ == "__main__":
    main()
