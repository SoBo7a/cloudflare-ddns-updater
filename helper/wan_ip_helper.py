import requests

def get_ipv4(api_url, logger):
    """
    Fetches the IPv4 address from the provided API URL.
    
    Args:
        api_url (str): The base URL of the WAN IP Provider API.
        
    Returns:
        tuple: A tuple containing the IPv4 address and the string "wan-ip-provider".
    """
    try:
        response = requests.get(f"{api_url}/ipv4")
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        if "ipv4" in data:
            return data["ipv4"], "wan-ip-provider"
        else:
            return None, None
    except requests.RequestException as e:
        logger.error(f"Error fetching IPv4: {e}")
        return None, None