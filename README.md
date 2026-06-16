# Apptio Connector Retrieval Script

## Overview

This Python script retrieves the list of connectors from an Apptio customer account and saves each connector as a separate JSON file. The script performs a three-step authentication and data retrieval process using Apptio's REST API.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Output](#output)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Prerequisites

### System Requirements
- **Python**: Version 3.6 or higher
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for API calls to Apptio services

### Python Dependencies
- `requests` library (for HTTP requests)

---

## Installation

### Step 1: Install Python

If Python is not already installed on your system:

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```

**macOS/Linux:**
```bash
# macOS (using Homebrew)
brew install python3

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3 python3-pip

# Verify installation
python3 --version
```

### Step 2: Install Required Dependencies

Install the `requests` library:

```bash
# Windows
pip install requests

# macOS/Linux
pip3 install requests
```

### Step 3: Download the Script

Place the `get_apptio_connectors.py` script in your working directory.

---

## Configuration

### Configuration Files

The script requires five configuration files in the `P2` directory (or a custom directory specified via command-line argument):

| File | Description | Example Content |
|------|-------------|-----------------|
| `frontdoor.conf` | Apptio API gateway URL | `frontdoor-eu.apptio.com` |
| `datalink.conf` | Apptio Datalink service URL | `datalink-eu.apptio.com` |
| `customer.conf` | Customer identifier | `a2a.eu` |
| `keyAccess.conf` | API access key (UUID format) | `2a150545-80d5-49d7-b691-45624c38b54a` |
| `keySecret.conf` | API secret key | `Zq7KgzLVHmVPyUEGoJPLo2E0Mt1JztE7...` |

### Directory Structure

```
your-project/
├── get_apptio_connectors.py
├── P2/
│   ├── frontdoor.conf
│   ├── datalink.conf
│   ├── customer.conf
│   ├── keyAccess.conf
│   └── keySecret.conf
└── connectors/          # Created automatically
    ├── connector1.json
    ├── connector2.json
    └── ...
```

### Creating Configuration Files

Each configuration file should contain a single line with the appropriate value:

```bash
# Example: Create frontdoor.conf
echo "frontdoor-eu.apptio.com" > P2/frontdoor.conf

# Example: Create customer.conf
echo "a2a.eu" > P2/customer.conf
```

---

## Usage

### Basic Usage

Run the script with default settings (reads from `P2/` directory, saves to `connectors/`):

```bash
python get_apptio_connectors.py
```

### Advanced Usage

#### Custom Configuration Directory

```bash
python get_apptio_connectors.py --config-dir /path/to/config
```

#### Custom Output Directory

```bash
python get_apptio_connectors.py --output-dir /path/to/output
```

#### Enable Debug Logging

```bash
python get_apptio_connectors.py --debug
```

#### Combined Options

```bash
python get_apptio_connectors.py --config-dir P2 --output-dir my_connectors --debug
```

### Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--config-dir` | N/A | Directory containing configuration files | `P2` |
| `--output-dir` | N/A | Directory to save connector JSON files | `connectors` |
| `--debug` | N/A | Enable debug logging | `False` |

---

## How It Works

### Three-Step Process

The script follows a three-step authentication and data retrieval process:

#### Step 1: Authentication
```
POST https://{frontdoor}/service/apikeylogin
Headers:
  - Content-Type: application/json
  - Accept: application/json
Body:
  {
    "keyAccess": "{keyAccess}",
    "keySecret": "{keySecret}"
  }
Response:
  - Cookie: apptio-opentoken
```

**Purpose**: Authenticate with Apptio API and retrieve the `apptio-opentoken` cookie for subsequent requests.

#### Step 2: Get Environment ID
```
GET https://{frontdoor}/api/environment/{customer}/main
Headers:
  - Content-Type: application/json
  - apptio-opentoken: {token from Step 1}
Response:
  {
    "id": "{environment-id}",
    ...
  }
```

**Purpose**: Retrieve the `apptio-current-environment` ID needed for the connectors API.

#### Step 3: Get Connectors
```
GET https://{datalink}/apptioconnect/api/v1/connections
Headers:
  - apptio-opentoken: {token from Step 1}
  - apptio-current-environment: {id from Step 2}
  - Accept: application/json
Response:
  [
    { connector object 1 },
    { connector object 2 },
    ...
  ]
```

**Purpose**: Retrieve the array of connector objects.

### Data Flow Diagram

```
┌─────────────────┐
│ Load Config     │
│ Files from P2/  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 1:         │
│ Authenticate    │──► Get apptio-opentoken
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 2:         │
│ Get Environment │──► Get apptio-current-environment
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 3:         │
│ Get Connectors  │──► Receive connector array
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save Each       │
│ Connector as    │──► {name/id}.json files
│ Separate JSON   │
└─────────────────┘
```

---

## Output

### File Naming Convention

Each connector is saved with a filename based on:
1. **Connector Name** (if available): Sanitized and used as filename
2. **Connector ID** (if name not available): Used as filename
3. **Sequential Number** (fallback): `connector_1.json`, `connector_2.json`, etc.

### Filename Sanitization

Invalid characters are replaced with underscores:
- Characters removed: `< > : " / \ | ? *`
- Spaces replaced with: `_`
- Maximum length: 200 characters

### Example Output

```
connectors/
├── AWS_Production_Connector.json
├── Azure_Dev_Environment.json
├── GCP_Analytics_Connector.json
└── On_Premise_Database.json
```

### JSON File Format

Each connector file contains the complete connector object with proper indentation:

```json
{
  "id": "12345",
  "name": "AWS Production Connector",
  "type": "AWS",
  "status": "active",
  "configuration": {
    "region": "us-east-1",
    "accountId": "123456789012"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-06-10T14:22:00Z"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Configuration File Not Found

**Error:**
```
Configuration file not found: P2/frontdoor.conf
```

**Solution:**
- Verify all configuration files exist in the `P2` directory
- Check file names match exactly (case-sensitive on Linux/macOS)
- Use `--config-dir` to specify a different directory

#### 2. Authentication Failed

**Error:**
```
Authentication failed - no token in response
```

**Solution:**
- Verify `keyAccess` and `keySecret` are correct
- Check if API credentials are still valid
- Ensure network connectivity to Apptio services

#### 3. No Environment ID Found

**Error:**
```
No 'id' field found in environment response
```

**Solution:**
- Verify the customer identifier in `customer.conf` is correct
- Check if the customer account is active
- Ensure the API token has proper permissions

#### 4. Requests Library Not Found

**Error:**
```
ModuleNotFoundError: No module named 'requests'
```

**Solution:**
```bash
pip install requests
```

#### 5. Permission Denied When Saving Files

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'connectors/...'
```

**Solution:**
- Check write permissions for the output directory
- Run with appropriate user permissions
- Use `--output-dir` to specify a different location

### Debug Mode

Enable debug mode for detailed logging:

```bash
python get_apptio_connectors.py --debug
```

Debug output includes:
- Configuration values (first 20 characters)
- Full API URLs
- Token information (truncated)
- Detailed error stack traces

---

## API Reference

### Apptio API Endpoints

#### Authentication Endpoint
- **URL**: `https://{frontdoor}/service/apikeylogin`
- **Method**: POST
- **Authentication**: API Key/Secret in request body
- **Response**: Sets `apptio-opentoken` cookie

#### Environment Endpoint
- **URL**: `https://{frontdoor}/api/environment/{customer}/main`
- **Method**: GET
- **Authentication**: `apptio-opentoken` header
- **Response**: JSON object with environment details

#### Connectors Endpoint
- **URL**: `https://{datalink}/apptioconnect/api/v1/connections`
- **Method**: GET
- **Authentication**: `apptio-opentoken` and `apptio-current-environment` headers
- **Response**: JSON array of connector objects

### Script Classes and Methods

#### `ApptioConnectorRetriever` Class

**Constructor:**
```python
ApptioConnectorRetriever(config_dir: str = "P2")
```

**Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `authenticate()` | Authenticate and get token | `bool` |
| `get_environment_id()` | Retrieve environment ID | `bool` |
| `get_connectors()` | Fetch connector list | `List[Dict]` or `None` |
| `save_connectors(connectors, output_dir)` | Save connectors to files | `int` (count saved) |
| `run(output_dir)` | Execute complete workflow | `bool` |

---

## Security Considerations

### Protecting API Credentials

1. **Never commit configuration files to version control**
   ```bash
   # Add to .gitignore
   echo "P2/*.conf" >> .gitignore
   ```

2. **Use environment variables** (alternative approach):
   ```python
   import os
   keyAccess = os.getenv('APPTIO_KEY_ACCESS')
   keySecret = os.getenv('APPTIO_KEY_SECRET')
   ```

3. **Restrict file permissions**:
   ```bash
   chmod 600 P2/*.conf
   ```

### Network Security

- All API calls use HTTPS
- Tokens are transmitted securely
- Session cookies are managed automatically

---

## License

This script is provided as-is for use with Apptio services.

---

## Support

For issues related to:
- **Script functionality**: Check the Troubleshooting section
- **Apptio API**: Contact Apptio support
- **API credentials**: Contact your Apptio administrator

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-06-11 | Initial release |

---

## Example Session

```bash
$ python get_apptio_connectors.py --debug

2024-06-11 10:30:00 - INFO - Starting Apptio connector retrieval...
2024-06-11 10:30:00 - INFO - Loading configuration from P2
2024-06-11 10:30:00 - DEBUG - Loaded frontdoor.conf: frontdoor-eu.apptio...
2024-06-11 10:30:00 - DEBUG - Loaded datalink.conf: datalink-eu.apptio.c...
2024-06-11 10:30:00 - DEBUG - Loaded customer.conf: a2a.eu...
2024-06-11 10:30:01 - INFO - Step 1: Authenticating with Apptio API...
2024-06-11 10:30:02 - INFO - Authentication successful - token retrieved
2024-06-11 10:30:02 - INFO - Step 2: Retrieving environment ID...
2024-06-11 10:30:03 - INFO - Environment ID retrieved: env-12345-abcde
2024-06-11 10:30:03 - INFO - Step 3: Retrieving connectors list...
2024-06-11 10:30:05 - INFO - Retrieved 15 connectors
2024-06-11 10:30:05 - INFO - Saving connectors to connectors/...
2024-06-11 10:30:05 - INFO - Saved: AWS_Production.json
2024-06-11 10:30:05 - INFO - Saved: Azure_Development.json
...
2024-06-11 10:30:06 - INFO - Successfully saved 15/15 connectors
2024-06-11 10:30:06 - INFO - Connector retrieval completed successfully!

✓ Connectors saved to connectors/