# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an unofficial collection of Python CLI scripts for Duo Security MSP (Managed Service Provider) administrators. Scripts automate management of a parent Duo account and its child accounts (subaccounts) via the Duo Admin API and Duo Accounts API.

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

Some scripts (`username_collision_report.py`, `msp_user_report.py`) also support a `duo.conf` file with `KEY=value` pairs as an alternative.

## Running Scripts

Each script is standalone and run directly:
```bash
python retrieve_account_list.py
python msp_user_report.py
python admin_manager.py
python child_account_hard_user_limit.py --account_id DA<id> --action get
python create_child_account.py --batch "Account1,Account2"
python username_collision_report.py
```

## Architecture

### Authentication Model
Scripts use two API credential sets:
- **Parent Admin API** (`DUO_PARENT_*`): Manage users/admins on the parent account directly
- **Accounts API** (`DUO_ACCOUNTS_*`): List and manage child accounts; also used as credentials when targeting child account Admin API endpoints (pointing to the child's API hostname)

```python
# Pattern for targeting a child account's Admin API
child_admin = duo_client.Admin(
    ikey=accounts_ikey,
    skey=accounts_skey,
    host=child_api_hostname  # child-specific hostname
)
```

### Multi-Account Traversal
The common pattern across reporting scripts:
1. Init Accounts API client → get list of all child accounts
2. For each child account, init a separate Admin client using Accounts credentials + child hostname
3. Collect data across parent + all children
4. Aggregate and output (CSV, PDF, or console table)

Failures on individual child accounts are logged and skipped; traversal continues.

### Custom API Extensions
- `child_account_hard_user_limit.py` extends `duo_client.admin.AccountAdmin` to call the undocumented `/admin/v1/billing/user_limit` endpoint
- `admin_manager.py` wraps `duo_client.Admin` with role mapping and interactive CRUD operations

### Output Formats
- **Console**: `tabulate` for formatted tables
- **CSV**: `pandas` DataFrames exported with timestamped filenames (`report_YYYYMMDD_HHMMSS.csv`)
- **PDF**: `reportlab` with styled tables and summary statistics

### Child Account ID Format
Child account IDs always start with `"DA"` (e.g., `DA12345`). Scripts validate this on input.
