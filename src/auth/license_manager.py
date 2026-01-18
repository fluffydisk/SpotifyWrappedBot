from src.auth.hwid import get_hwid
import requests # For future use

class LicenseManager:
    """
    Manages license validation and hardware ID checks.
    """
    def __init__(self):
        self.is_verified = False
        self.hwid = get_hwid()

    def validate_license(self, key):
        """
        Validates the given license key against the server.
        
        Args:
            key (str): The license key to validate.
            
        Returns:
            tuple: (bool, str) -> (Success, Message)
        """
        payload = {"key": key, "hwid": self.hwid}
        
        # Log for dev purposes
        print(f"Validating License: {key} for HWID: {self.hwid}")
        
        # TODO: Implement API POST request to validation server
        # try:
        #     response = requests.post("https://api.yoursite.com/validate", json=payload)
        #     ...
        # except ...
        
        # bypass license check for dev
        return True, "Dev Mode: License Bypassed"
