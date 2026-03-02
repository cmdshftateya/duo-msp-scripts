# Duo Username Collision Finder for Delegated Access

This tool identifies username and alias collisions between your Duo parent account and all subaccounts. It helps you detect potential conflicts when using Delegated Access.

## Please note
This script is not officially maintained by Duo Security or Cisco Systems. Use at your own risk.

## What It Does

The collision finder:
- Scans all users in your parent account
- Checks each subaccount for matching usernames or aliases
- Generates detailed reports showing where collisions exist
- Provides both CSV and PDF output formats

## Requirements

- Python 3.7 or higher
- Duo Admin API access to parent account
- Duo Accounts API access

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API credentials:**
   - Open `duo.conf` in a text editor
   - Fill in your Duo API credentials (see Configuration section below)

## Configuration

Edit the `duo.conf` file with your Duo Security API credentials:

```ini
# Parent Account Admin API credentials
DUO_PARENT_IKEY=your_parent_integration_key
DUO_PARENT_SKEY=your_parent_secret_key
DUO_PARENT_HOST=api-XXXXXXXX.duosecurity.com

# Accounts API credentials
DUO_ACCOUNTS_IKEY=your_accounts_integration_key
DUO_ACCOUNTS_SKEY=your_accounts_secret_key
DUO_ACCOUNTS_HOST=api-XXXXXXXX.duosecurity.com
```

### Where to Find Your Credentials

**Parent Admin API:**
1. Log into the Duo Admin Panel for your parent account
2. Navigate to Applications
3. Protect an application or use an existing Admin API integration
4. Note the Integration Key, Secret Key, and API Hostname

**Accounts API:**
1. Log into the Duo Admin Panel for your parent account
2. Navigate to Accounts (MSP features)
3. Use your Accounts API integration credentials
4. Note the Integration Key, Secret Key, and API Hostname

## Usage

Run the script from the command line:

```bash
python username_collision_report.py
```

The script will:
1. Connect to your Duo parent account
2. Fetch all parent account users and their aliases
3. Scan all subaccounts for matching usernames/aliases
4. Generate collision reports

### Output

The script generates three outputs:

1. **Console Summary** - Real-time progress and summary statistics
2. **CSV Report** - `username_collision_report_YYYYMMDD_HHMMSS.csv`
   - Detailed collision data with all matches
   - One row per collision instance
   - Includes users with no collisions
3. **PDF Report** - `username_collision_report_YYYYMMDD_HHMMSS.pdf`
   - Professional formatted report
   - Summary statistics
   - Grouped collision details by parent user
   - List of users without collisions

### Sample Output

```
==================================================
COLLISION REPORT SUMMARY
==================================================
+---------------------------+---------+
| Metric                    |   Count |
+===========================+=========+
| Total Parent Users        |      35 |
+---------------------------+---------+
| Users with Collisions     |       1 |
+---------------------------+---------+
| Users without Collisions  |      34 |
+---------------------------+---------+
| Total Collision Instances |       1 |
+---------------------------+---------+
| Subaccounts Scanned       |      63 |
+---------------------------+---------+

CSV report saved to: username_collision_report_20251219_092634.csv
PDF report saved to: username_collision_report_20251219_092634.pdf

Total execution time: 36.11 seconds
```

## Understanding the Report

### Collision Types

The report identifies four types of collisions:

- **parent_username & sub_username** - Direct username match
- **parent_username & sub_alias** - Parent username matches subaccount alias
- **parent_alias & sub_username** - Parent alias matches subaccount username
- **parent_alias & sub_alias** - Alias to alias match

### What to Do With Results

**If collisions are found:**
- Review the specific matches in the detailed reports
- Determine if the collisions represent the same user or different users
- Plan remediation before performing account migrations or consolidations

**If no collisions are found:**
- Usernames are unique across parent and subaccounts
- Safe to proceed with account operations

## User Agent

The script identifies itself to Duo's API with the user agent:
```
Delegated Access Uname Collision Report
```

This helps you track these API calls in your Duo logs.

## Troubleshooting

**Authentication errors (401):**
- Verify your API credentials are correct in duo.conf
- Ensure the Parent Admin API has permissions to read users
- Ensure the Accounts API has permissions to access subaccounts

**Missing dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

**Slow execution:**
- Execution time depends on the number of subaccounts and users
- Typical performance: ~30-60 seconds for 60+ subaccounts

## Security Notes

- Store your `duo.conf` file securely
- Do not commit `duo.conf` to version control
- API credentials provide read-only access for this script
- All reports are generated locally on your machine

## Support

For issues or questions:
1. Check that all credentials are correctly configured
2. Verify API integrations have appropriate permissions
3. Review the console output for specific error messages

## Version Information

- Script: username_collision_report.py
- Requires: Python 3.7+
- Dependencies: duo_client, pandas, tabulate, reportlab
