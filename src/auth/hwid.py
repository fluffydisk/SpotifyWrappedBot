import uuid
import hashlib
import platform

def get_hwid():
    """
    Generates a unique Hardware ID for the machine.
    Combines MAC address and system info to create a consistent hash.
    """
    try:
        # MAC Address
        mac = uuid.getnode()
        
        # System Info
        system_info = f"{platform.system()}-{platform.node()}-{platform.version()}-{platform.machine()}-{mac}"
        
        # Hash it to create a nice string
        hwid = hashlib.sha256(system_info.encode()).hexdigest()
        return hwid
    except Exception:
        return "unknown_hwid"
