# Quick Start Guide - Apptio Connector Retrieval

## 5-Minute Setup

### Step 1: Install Python and Dependencies (2 minutes)

**Windows:**
```bash
# Check if Python is installed
python --version

# If not installed, download from python.org and install

# Install requests library
pip install requests
```

**macOS/Linux:**
```bash
# Check if Python is installed
python3 --version

# Install requests library
pip3 install requests
```

### Step 2: Verify Configuration Files (1 minute)

Ensure you have these 5 files in the `P2` directory:

```
P2/
├── frontdoor.conf      # Example: frontdoor-eu.apptio.com
├── datalink.conf       # Example: datalink-eu.apptio.com
├── customer.conf       # Example: a2a.eu
├── keyAccess.conf      # Your API access key (UUID)
└── keySecret.conf      # Your API secret key
```

Each file should contain **only one line** with the appropriate value.

### Step 3: Run the Script (1 minute)

```bash
# Windows
python get_apptio_connectors.py

# macOS/Linux
python3 get_apptio_connectors.py
```

### Step 4: Check Results (1 minute)

Look for the `connectors/` directory with your connector JSON files:

```
connectors/
├── Connector_Name_1.json
├── Connector_Name_2.json
└── ...
```

---

## Expected Output

```
2024-06-11 10:30:00 - INFO - Starting Apptio connector retrieval...
2024-06-11 10:30:00 - INFO - Loading configuration from P2
2024-06-11 10:30:01 - INFO - Step 1: Authenticating with Apptio API...
2024-06-11 10:30:02 - INFO - Authentication successful - token retrieved
2024-06-11 10:30:02 - INFO - Step 2: Retrieving environment ID...
2024-06-11 10:30:03 - INFO - Environment ID retrieved: env-xxxxx
2024-06-11 10:30:03 - INFO - Step 3: Retrieving connectors list...
2024-06-11 10:30:05 - INFO - Retrieved 15 connectors
2024-06-11 10:30:05 - INFO - Saving connectors to connectors/...
2024-06-11 10:30:06 - INFO - Successfully saved 15/15 connectors
2024-06-11 10:30:06 - INFO - Connector retrieval completed successfully!

✓ Connectors saved to connectors/
```

---

## Troubleshooting

### Problem: "Configuration file not found"
**Solution:** Make sure all 5 `.conf` files exist in the `P2` directory

### Problem: "No module named 'requests'"
**Solution:** Run `pip install requests` (or `pip3 install requests`)

### Problem: "Authentication failed"
**Solution:** Verify your API credentials in `keyAccess.conf` and `keySecret.conf`

---

## Advanced Usage

### Custom Output Directory
```bash
python get_apptio_connectors.py --output-dir my_connectors
```

### Enable Debug Mode
```bash
python get_apptio_connectors.py --debug
```

### Different Config Location
```bash
python get_apptio_connectors.py --config-dir /path/to/configs
```

---

## What the Script Does

1. **Authenticates** with Apptio API using your credentials
2. **Retrieves** your environment ID
3. **Fetches** all connectors for your customer account
4. **Saves** each connector as a separate JSON file

---

## Need More Help?

See the full [README.md](README.md) for:
- Detailed API documentation
- Complete troubleshooting guide
- Security best practices
- Code examples

---

## File Structure After Running

```
your-project/
├── get_apptio_connectors.py    # The script
├── README.md                    # Full documentation
├── QUICKSTART.md               # This file
├── P2/                         # Configuration files
│   ├── frontdoor.conf
│   ├── datalink.conf
│   ├── customer.conf
│   ├── keyAccess.conf
│   └── keySecret.conf
└── connectors/                 # Output (created automatically)
    ├── connector1.json
    ├── connector2.json
    └── ...
```

---

## Success Checklist

- [ ] Python 3.6+ installed
- [ ] `requests` library installed
- [ ] All 5 configuration files in `P2/` directory
- [ ] Script runs without errors
- [ ] `connectors/` directory created with JSON files

---

**That's it! You're ready to retrieve Apptio connectors.**