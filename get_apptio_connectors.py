#!/usr/bin/env python3
"""
Apptio Connector Retrieval Script

This script retrieves the list of connectors from an Apptio customer account
and saves each connector as a separate JSON file.

Requirements:
    - Python 3.6+
    - requests library (pip install requests)
    - Configuration files in P2 folder:
        * frontdoor.conf
        * datalink.conf
        * customer.conf
        * keyAccess.conf
        * keySecret.conf

Usage:
    python get_apptio_connectors.py [--config-dir P2] [--output-dir connectors]
"""

import requests
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApptioConnectorRetriever:
    """Handles retrieval of Apptio connectors through API calls."""
    
    def __init__(self, config_dir: str = "P2"):
        """Initialize with configuration directory path."""
        self.config_dir = Path(config_dir)
        self.config = self._load_config()
        self.session = requests.Session()
        self.apptio_opentoken = None
        self.apptio_current_environment = None
    
    def _load_config(self) -> Dict[str, str]:
        """Load all configuration files from the config directory."""
        logger.info(f"Loading configuration from {self.config_dir}")
        
        config_files = {
            'frontdoor': 'frontdoor.conf',
            'datalink': 'datalink.conf',
            'customer': 'customer.conf',
            'keyAccess': 'keyAccess.conf',
            'keySecret': 'keySecret.conf'
        }
        
        config = {}
        for key, filename in config_files.items():
            file_path = self.config_dir / filename
            try:
                with open(file_path, 'r') as f:
                    config[key] = f.read().strip()
                logger.debug(f"Loaded {filename}: {config[key][:20]}...")
            except FileNotFoundError:
                logger.error(f"Configuration file not found: {file_path}")
                raise
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                raise
        
        return config
    
    def authenticate(self) -> bool:
        """
        Step 1: Authenticate with Apptio API and retrieve apptio-opentoken.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        logger.info("Step 1: Authenticating with Apptio API...")
        
        url = f"https://{self.config['frontdoor']}/service/apikeylogin"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {
            'keyAccess': self.config['keyAccess'],
            'keySecret': self.config['keySecret']
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Extract apptio-opentoken from cookies
            if 'apptio-opentoken' in response.cookies:
                self.apptio_opentoken = response.cookies['apptio-opentoken']
                logger.info("Authentication successful - token retrieved")
                return True
            else:
                logger.error("Authentication failed - no token in response")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            return False
    
    def get_environment_id(self) -> bool:
        """
        Step 2: Retrieve the apptio-current-environment ID.
        
        Returns:
            bool: True if environment ID retrieved, False otherwise
        """
        logger.info("Step 2: Retrieving environment ID...")
        
        url = f"https://{self.config['frontdoor']}/api/environment/{self.config['customer']}/main"
        headers = {
            'Content-Type': 'application/json',
            'apptio-opentoken': self.apptio_opentoken
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            # Extract first 'id' as apptio-current-environment
            if 'id' in data:
                self.apptio_current_environment = data['id']
                logger.info(f"Environment ID retrieved: {self.apptio_current_environment}")
                return True
            else:
                logger.error("No 'id' field found in environment response")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Environment request failed: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse environment response: {e}")
            return False
    
    def get_connectors(self) -> Optional[List[Dict]]:
        """
        Step 3: Retrieve the list of connectors.
        
        Returns:
            List[Dict]: Array of connector objects, or None if failed
        """
        logger.info("Step 3: Retrieving connectors list...")
        
        url = f"https://{self.config['datalink']}/apptioconnect/api/v1/connections"
        headers = {
            'apptio-opentoken': self.apptio_opentoken,
            'apptio-current-environment': self.apptio_current_environment,
            'Accept': 'application/json'
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            connectors = response.json()
            if isinstance(connectors, list):
                logger.info(f"Retrieved {len(connectors)} connectors")
                return connectors
            else:
                logger.error("Response is not an array")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Connectors request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse connectors response: {e}")
            return None
    
    def get_connector_details(self, connector_id: str) -> Optional[Dict]:
        """
        Step 4: Retrieve detailed information for a specific connector.
        
        Args:
            connector_id: The ID of the connector to retrieve
            
        Returns:
            Dict: Detailed connector object, or None if failed
        """
        logger.debug(f"Fetching details for connector ID: {connector_id}")
        
        url = f"https://{self.config['datalink']}/apptioconnect/api/v1/connections/{connector_id}"
        headers = {
            'apptio-opentoken': self.apptio_opentoken,
            'apptio-current-environment': self.apptio_current_environment,
            'Accept': 'application/json'
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            connector_details = response.json()
            logger.debug(f"Successfully retrieved details for connector {connector_id}")
            return connector_details
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve connector {connector_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse connector {connector_id} response: {e}")
            return None
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        Args:
            name: The string to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        # Limit length
        name = name[:200]
        return name
    
    def save_connectors(self, connectors: List[Dict], output_dir: str = "connectors") -> int:
        """
        Save each connector as a separate JSON file with detailed information.
        
        Args:
            connectors: List of connector objects from the connections list
            output_dir: Directory to save connector files
            
        Returns:
            int: Number of connectors saved successfully
        """
        logger.info(f"Fetching detailed information and saving connectors to {output_dir}/")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        for idx, connector in enumerate(connectors, 1):
            try:
                # Extract connector ID
                connector_id = connector.get('id')
                if not connector_id:
                    logger.warning(f"Connector {idx} has no ID, skipping...")
                    continue
                
                logger.info(f"Processing connector {idx}/{len(connectors)}: {connector_id}")
                
                # Fetch detailed connector information
                connector_details = self.get_connector_details(connector_id)
                if connector_details is None:
                    logger.warning(f"Could not retrieve details for connector {connector_id}, using list data")
                    connector_details = connector
                
                # Try to get connector name or ID for filename
                filename = None
                if 'name' in connector_details:
                    filename = self.sanitize_filename(connector_details['name'])
                elif 'name' in connector:
                    filename = self.sanitize_filename(connector['name'])
                else:
                    filename = self.sanitize_filename(str(connector_id))
                
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'
                
                file_path = output_path / filename
                
                # Write detailed connector information to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(connector_details, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved: {filename}")
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save connector {idx}: {e}")
        
        logger.info(f"Successfully saved {saved_count}/{len(connectors)} connectors")
        return saved_count
    
    def run(self, output_dir: str = "connectors") -> bool:
        """
        Execute the complete workflow to retrieve and save connectors with detailed information.
        
        Workflow:
        1. Authenticate with Apptio API
        2. Retrieve environment ID
        3. Get list of connectors
        4. For each connector, fetch detailed information via /connections/<id>
        5. Save detailed connector data to individual JSON files
        
        Args:
            output_dir: Directory to save connector files
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Starting Apptio connector retrieval...")
        
        # Step 1: Authenticate
        if not self.authenticate():
            logger.error("Failed at authentication step")
            return False
        
        # Step 2: Get environment ID
        if not self.get_environment_id():
            logger.error("Failed at environment ID retrieval step")
            return False
        
        # Step 3: Get connectors list
        connectors = self.get_connectors()
        if connectors is None:
            logger.error("Failed at connectors retrieval step")
            return False
        
        # Step 4: Fetch detailed information for each connector and save to files
        saved_count = self.save_connectors(connectors, output_dir)
        
        if saved_count > 0:
            logger.info("Connector retrieval completed successfully!")
            return True
        else:
            logger.error("No connectors were saved")
            return False


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Retrieve Apptio connectors and save as JSON files'
    )
    parser.add_argument(
        '--config-dir',
        default='P2',
        help='Directory containing configuration files (default: P2)'
    )
    parser.add_argument(
        '--output-dir',
        default='connectors',
        help='Directory to save connector JSON files (default: connectors)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        retriever = ApptioConnectorRetriever(config_dir=args.config_dir)
        success = retriever.run(output_dir=args.output_dir)
        
        if success:
            print(f"\n✓ Connectors saved to {args.output_dir}/")
            return 0
        else:
            print("\n✗ Failed to retrieve connectors")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
