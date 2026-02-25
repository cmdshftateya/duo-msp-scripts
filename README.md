# Duo API Scripts for MSPs

> **Disclaimer:** This project is **not** affiliated with, endorsed by, or supported by Cisco or Duo Security. These are personal scripts written by me because I found them handy for day-to-day MSP tasks. They may be compatible with the Duo MSP product, but there are no guarantees. **Use at your own risk.** Cisco and Duo Security bear no responsibility for the use or misuse of anything in this repository.

A collection of Python CLI scripts for Duo Security MSP administrators. These automate common tasks like managing child accounts, generating reports, and bulk operations via the Duo Admin API and Duo Accounts API.

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Set environment variables for API credentials (required by most scripts):
```bash
export DUO_PARENT_IKEY='your-parent-integration-key'
export DUO_PARENT_SKEY='your-parent-secret-key'
export DUO_PARENT_HOST='your-parent-api-hostname'
export DUO_ACCOUNTS_IKEY='your-accounts-integration-key'
export DUO_ACCOUNTS_SKEY='your-accounts-secret-key'
export DUO_ACCOUNTS_HOST='your-accounts-api-hostname'
```

## Repository Structure

```
scripts/                          Standalone Python scripts
communications-impact-report/     Web-based communications impact report tool
duo-subaccount-hard-user-limit/   PowerShell module for managing user limits
```

## Running Scripts

Each script is standalone and run directly from the `scripts/` directory:
```bash
python scripts/retrieve_account_list.py
python scripts/msp_user_report.py
python scripts/admin_manager.py
python scripts/child_account_hard_user_limit.py --account_id DA<id> --action get
python scripts/create_child_account.py --batch "Account1,Account2"
python scripts/username_collision_report.py
```
