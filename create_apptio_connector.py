#!/usr/bin/env python3
"""
Apptio Connector Creation Script

This script creates a new connector in an Apptio customer account by reading
a connector JSON file, modifying its name, and posting it to the Apptio API.

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
    python create_apptio_connector.py --connector-file connectors/my_connector.json --name "New Connector Name"
"""

import requests
import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApptioConnectorCreator:
    """Handles creation of Apptio connectors through API calls."""
    
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
                logger.debug(f"Token: {self.apptio_opentoken[:20]}...")
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
    
    def load_connector_json(self, file_path: str) -> Optional[Dict]:
        """
        Load connector data from a JSON file.
        
        Args:
            file_path: Path to the connector JSON file
            
        Returns:
            Dict: Connector data, or None if failed
        """
        logger.info(f"Loading connector data from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                connector_data = json.load(f)
            
            logger.info("Connector data loaded successfully")
            logger.debug(f"Connector name: {connector_data.get('name', 'N/A')}")
            return connector_data
            
        except FileNotFoundError:
            logger.error(f"Connector file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in connector file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading connector file: {e}")
            return None
    
    def create_connector(self, connector_data: Dict) -> Optional[Dict]:
        """
        Step 3: Create a new connector by posting the connector data.
        
        Args:
            connector_data: The connector configuration to create
            
        Returns:
            Dict: Response from the API, or None if failed
        """
        logger.info("Step 3: Creating connector...")
        
        url = f"https://{self.config['datalink']}/apptioconnect/api/v1/connections"
        headers = {
            'apptio-opentoken': self.apptio_opentoken,
            'apptio-current-environment': self.apptio_current_environment,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            logger.debug(f"POST {url}")
            response = self.session.post(url, headers=headers, json=connector_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Connector created successfully!")
            
            if 'id' in result:
                logger.info(f"New connector ID: {result['id']}")
            if 'name' in result:
                logger.info(f"Connector name: {result['name']}")
            
            return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Connector creation request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse connector creation response: {e}")
            return None
    
    def run(self, connector_file: str) -> bool:
        """
        Execute the complete workflow to create a connector.
        
        Workflow:
        1. Authenticate with Apptio API
        2. Retrieve environment ID
        3. Load connector data from JSON file
        4. Create connector via POST request
        
        Args:
            connector_file: Path to the connector JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Starting Apptio connector creation...")
        
        # Step 1: Authenticate
        if not self.authenticate():
            logger.error("Failed at authentication step")
            return False
        
        # Step 2: Get environment ID
        if not self.get_environment_id():
            logger.error("Failed at environment ID retrieval step")
            return False
        
        # Load connector data from file
        connector_data = self.load_connector_json(connector_file)
        if connector_data is None:
            logger.error("Failed to load connector data")
            return False
        
        # Step 3: Create connector
        result = self.create_connector(connector_data)
        if result is None:
            logger.error("Failed to create connector")
            return False
        
        logger.info("Connector creation completed successfully!")
        return True


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create an Apptio connector from a JSON file'
    )
    parser.add_argument(
        '--connector-file',
        required=True,
        help='Path to the connector JSON file (e.g., connectors/my_connector.json)'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Name for the new connector (will override the name in the JSON file)'
    )
    parser.add_argument(
        '--config-dir',
        default='P2',
        help='Directory containing configuration files (default: P2)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Verify connector file exists
    if not os.path.exists(args.connector_file):
        logger.error(f"Connector file not found: {args.connector_file}")
        return 1
    
    try:
        creator = ApptioConnectorCreator(config_dir=args.config_dir)
        
        # Authenticate and get environment ID
        if not creator.authenticate():
            logger.error("Failed at authentication step")
            return 1
        
        if not creator.get_environment_id():
            logger.error("Failed at environment ID retrieval step")
            return 1
        
        # Load connector data
        connector_data = creator.load_connector_json(args.connector_file)
        if connector_data is None:
            logger.error("Failed to load connector data")
            return 1
        
        # Override the name field with the provided name
        original_name = connector_data.get('name', 'N/A')
        connector_data['name'] = args.name
        logger.info(f"Overriding connector name: '{original_name}' -> '{args.name}'")
        
        # Create connector and get response
        result = creator.create_connector(connector_data)
        
        if result is not None:
            print(f"\n✓ Connector '{args.name}' created successfully from {args.connector_file}")
            print("\n" + "="*60)
            print("SERVER RESPONSE:")
            print("="*60)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("="*60 + "\n")
            return 0
        else:
            print(f"\n✗ Failed to create connector from {args.connector_file}")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

# Made with Bob