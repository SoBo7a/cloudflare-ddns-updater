import random
import socket
import requests
from datetime import datetime, timedelta
import subprocess

# List of services to get public IP from
IP_SERVICES = [
    {"name": "api.ipify.org", "url": "https://api.ipify.org/"},
    {"name": "checkip.amazonaws.com", "url": "https://checkip.amazonaws.com"},
    {"name": "dnsomatic.com", "url": "https://myip.dnsomatic.com"},
    {"name": "icanhazip.com", "url": "https://ipv4.icanhazip.com/"},
    {"name": "ident.me", "url": "https://ident.me/"},
    {"name": "ifconfig.co", "url": "https://ipv4.ifconfig.co/ip"},
    {"name": "ifconfig.me", "url": "https://ipv4.ifconfig.me/ip"},
    {"name": "ipecho.net", "url": "https://ipv4.ipecho.net/plain"},
    {"name": "ipinfo.io", "url": "https://ipinfo.io/json"},
    {"name": "myexternalip.com", "url": "https://myexternalip.com/raw"},
    {"name": "whatismyip.akamai.com", "url": "https://whatismyip.akamai.com/"}
]

def is_network_available(logger):
    """
    Checks if the network is available by pinging a reliable host.
    
    Args:
        logger (logging.Logger): Logger instance for logging connectivity status.
    
    Returns:
        bool: True if the network is available, False otherwise.
    """
    try:
        # Ping Google's public DNS server to check internet connectivity
        subprocess.check_call(
            ["ping", "-c", "1", "8.8.8.8"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info("Network is available.")
        return True
    except subprocess.CalledProcessError:
        logger.error("Network is unavailable. Skipping public IP check.")
        return False
    
def get_failed_services(logger, log_file_path):
    """
    Checks the log file for services that have failed in the last 24 hours.
    
    Args:
        logger (logging.Logger): The logger for logging messages.
        log_file_path (str): Path to the log file to check for errors.
    
    Returns:
        set: A set of service names that failed in the last 24 hours.
    """
    failed_services = set()
    try:
        # Calculate the timestamp for 24 hours ago
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                # Check if the line contains error information about a service
                if 'Error' in line or 'invalid' in line:  # Modify based on your log format for errors
                    timestamp_str = line.split()[0]  # Assuming timestamp is the first word
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')  # Adjust format if needed
                    if timestamp > twenty_four_hours_ago:
                        # Extract service name from the log line
                        for service in IP_SERVICES:
                            if service["name"] in line:
                                failed_services.add(service["name"])
                                logger.warning(f"Skipping {service['name']} since it failed in the last 24 hours.")
                                break
    except FileNotFoundError:
        logger.error(f"Log file not found: {log_file_path}")
    except Exception as e:
        logger.error(f"Error reading the log file: {e}")
    
    return failed_services

def get_public_ip(logger, log_file):
    """
    Attempts to fetch the public IPv4 address by trying multiple services.
    Randomly selects the service to avoid overusing one, and skips services that have failed in the last 24 hours.

    Returns:
        tuple: A tuple containing the public IPv4 address and the service provider name, or None if it could not be fetched.
    """
    if not is_network_available(logger):
        return None, None
    
    failed_services = get_failed_services(logger, log_file)
    available_services = [service for service in IP_SERVICES if service["name"] not in failed_services]

    if not available_services:
        logger.error("No available services to fetch public IP after checking logs.")
        return None, None

    random.shuffle(available_services)

    for service in available_services:
        try:
            ip = fetch_ip_from_service(service)
            if ip and is_valid_ip(ip):
                return ip, service["name"]
            logger.warning(f"Received an invalid or IPv6 address from {service['name']}: {ip}, trying the next service.")
        except Exception as e:
            logger.error(f"Error fetching public IP from {service['name']}: {e}")

    logger.error("All attempts to fetch a valid public IPv4 address failed.")
    return None, None

def fetch_ip_from_service(service):
    """
    Fetches the public IP address from a given service.

    Args:
        service (dict): The service information containing name and URL.

    Returns:
        str: The IP address as a string.
    """
    response = requests.get(service["url"])
    response.raise_for_status()  # Ensure we get a valid response

    if service["name"] == "ipinfo.io":
        return response.json().get("ip")
    return response.text.strip()

def is_valid_ip(ip):
    """
    Checks if the given IP address is a valid IPv4 address.

    Args:
        ip (str): The IP address to validate.

    Returns:
        bool: True if the IP is valid IPv4, False otherwise.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False
