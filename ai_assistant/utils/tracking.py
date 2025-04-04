"""
Installation tracking utility for QuackQuery.
Tracks the number of systems where QuackQuery is installed.
"""

import os
import uuid
import requests
import platform
import logging
import json
from pathlib import Path
import threading

logger = logging.getLogger("ai_assistant")

# Configuration
TRACKING_URL = "https://api.quackquery.com/track"  # Replace with your actual tracking endpoint
BACKUP_TRACKING_URL = "https://quackquery-tracking.herokuapp.com/track"  # Backup URL

class InstallationTracker:
    """Tracks installations of QuackQuery."""
    
    def __init__(self):
        """Initialize the installation tracker."""
        self.installation_id = self._get_or_create_installation_id()
        self.user_home = str(Path.home())
        self.config_dir = os.path.join(self.user_home, ".quackquery")
        
    def _get_or_create_installation_id(self):
        """
        Get existing installation ID or create a new one.
        
        Returns:
            str: Installation ID
        """
        try:
            # Create config directory if it doesn't exist
            user_home = str(Path.home())
            config_dir = os.path.join(user_home, ".quackquery")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # Installation ID file
            id_file = os.path.join(config_dir, "installation_id")
            
            # Check if ID already exists
            if os.path.exists(id_file):
                with open(id_file, 'r') as f:
                    return f.read().strip()
            
            # Create new ID if it doesn't exist
            installation_id = str(uuid.uuid4())
            with open(id_file, 'w') as f:
                f.write(installation_id)
                
            return installation_id
                
        except Exception as e:
            logger.error(f"Error getting/creating installation ID: {e}")
            # Fallback to a temporary ID
            return str(uuid.uuid4())
    
    def track_installation(self):
        """
        Track a new installation or update.
        Sends data in a background thread to avoid slowing down startup.
        """
        # Create a background thread to perform the tracking
        threading.Thread(target=self._send_tracking_data, daemon=True).start()
    
    def _send_tracking_data(self):
        """Send tracking data to the server."""
        try:
            # Collect system information
            system_info = {
                "installation_id": self.installation_id,
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "machine": platform.machine()
            }
            
            # Try primary URL first
            try:
                response = requests.post(
                    TRACKING_URL,
                    json=system_info,
                    headers={"Content-Type": "application/json"},
                    timeout=5  # Short timeout to prevent slowing down startup
                )
                
                if response.status_code == 200:
                    logger.debug("Installation tracking successful")
                    return
                    
            except requests.RequestException:
                # If primary URL fails, try backup
                pass
                
            # Try backup URL if primary failed
            try:
                requests.post(
                    BACKUP_TRACKING_URL,
                    json=system_info,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                logger.debug("Installation tracking successful (backup)")
            except requests.RequestException as e:
                logger.debug(f"Tracking request failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error tracking installation: {e}")
    
    def get_installation_stats(self):
        """
        Get installation statistics from the server.
        
        Returns:
            dict: Statistics about installations, or None if request fails
        """
        try:
            response = requests.get(
                f"{TRACKING_URL}/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
                
            # Try backup URL if primary failed
            response = requests.get(
                f"{BACKUP_TRACKING_URL}/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting installation stats: {e}")
            return None


# Singleton instance
tracker = InstallationTracker()

def track_installation():
    """Track a new installation or update."""
    tracker.track_installation()

def get_installation_stats():
    """Get installation statistics."""
    return tracker.get_installation_stats() 