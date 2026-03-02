# DuoSubaccountUserLimit

> **Disclaimer:** This is an unofficial tool and is not supported by Cisco or Duo Security. It relies on an undocumented API endpoint that may change or be removed without notice. Use at your own risk.

PowerShell module for MSP admins to list Duo child accounts and get/set hard user limits via the undocumented `/admin/v1/billing/user_limit` endpoint.

## Requirements

- PowerShell 7+
- Duo **Accounts API** credentials (not Admin API) from your parent MSP account

## Setup

Set the following environment variables before importing the module:

```powershell
$env:DUO_ACCOUNTS_IKEY = 'your-accounts-integration-key'
$env:DUO_ACCOUNTS_SKEY = 'your-accounts-secret-key'
$env:DUO_ACCOUNTS_HOST = 'api-accounts.duosecurity.com'
```

## Import

```powershell
Import-Module ./duo-subaccount-hard-user-limit/DuoSubaccountUserLimit.psd1
```

## Usage

### List all child accounts

```powershell
Get-DuoChildAccounts
```

Returns objects with `name`, `account_id`, `api_hostname`, and other fields from the Accounts API.

### Get user limit for a specific account

```powershell
Get-DuoUserLimit -AccountId DA12345 `
    -ApiHostname api-XXXXXXXX.duosecurity.com
```

### Get user limits for all child accounts

```powershell
Get-DuoChildAccounts | Get-DuoUserLimit
```

### Set a user limit

```powershell
Set-DuoUserLimit -AccountId DA12345 `
    -ApiHostname api-XXXXXXXX.duosecurity.com `
    -UserLimit 100
```

### Set a limit by account name (using pipeline)

```powershell
Get-DuoChildAccounts |
    Where-Object name -eq 'Acme Corp' |
    Set-DuoUserLimit -UserLimit 50
```

### Remove a limit (set to 0)

```powershell
Set-DuoUserLimit -AccountId DA12345 `
    -ApiHostname api-XXXXXXXX.duosecurity.com `
    -UserLimit 0
```

### Preview a set operation without applying it (-WhatIf)

```powershell
Get-DuoChildAccounts |
    Where-Object name -eq 'Acme Corp' |
    Set-DuoUserLimit -UserLimit 50 -WhatIf
```

### Bulk report: all accounts with their current limits

```powershell
Get-DuoChildAccounts | Get-DuoUserLimit | Format-Table
```

## Example walkthrough

A full session: list accounts, check limits, set limits on a couple, then remove one.

```powershell
# 1. Import the module
Import-Module /path/to/duo-subaccount-hard-user-limit/DuoSubaccountUserLimit.psd1

# 2. Set credentials
$env:DUO_ACCOUNTS_IKEY = 'DIXXXXXXXXXXXXXXXXXX'
$env:DUO_ACCOUNTS_SKEY = 'your-accounts-secret-key'
$env:DUO_ACCOUNTS_HOST = 'api-accounts.duosecurity.com'

# 3. List all child accounts
Get-DuoChildAccounts

# account_id             api_hostname                      name
# ----------             ------------                      ----
# DAXXXXXXXXXXXXXXXXXX   api-XXXXXXXX.duosecurity.com      Acme Corp
# DAYYYYYYYYYYYYYYYYYY   api-YYYYYYYY.duosecurity.com      Globex Corporation
# DAZZZZZZZZZZZZZZZZZZ   api-ZZZZZZZZ.duosecurity.com      Initech

# 4. Check current limits across all accounts
Get-DuoChildAccounts | Get-DuoUserLimit | Format-Table

# account_id             user_limit
# ----------             ----------
# DAXXXXXXXXXXXXXXXXXX   Not set
# DAYYYYYYYYYYYYYYYYYY   Not set
# DAZZZZZZZZZZZZZZZZZZ   Not set

# 5. Set a limit of 50 on Acme Corp
Get-DuoChildAccounts |
    Where-Object name -eq 'Acme Corp' |
    Set-DuoUserLimit -UserLimit 50

# 6. Set a limit of 100 on Globex Corporation
Get-DuoChildAccounts |
    Where-Object name -eq 'Globex Corporation' |
    Set-DuoUserLimit -UserLimit 100

# 7. Verify the limits were applied
Get-DuoChildAccounts | Get-DuoUserLimit | Format-Table

# account_id             user_limit
# ----------             ----------
# DAXXXXXXXXXXXXXXXXXX   50
# DAYYYYYYYYYYYYYYYYYY   100
# DAZZZZZZZZZZZZZZZZZZ   Not set

# 8. Remove the limit from Acme Corp (set to 0)
Set-DuoUserLimit -AccountId 'DAXXXXXXXXXXXXXXXXXX' `
    -ApiHostname 'api-XXXXXXXX.duosecurity.com' `
    -UserLimit 0

# 9. Confirm it was removed
Get-DuoUserLimit -AccountId 'DAXXXXXXXXXXXXXXXXXX' `
    -ApiHostname 'api-XXXXXXXX.duosecurity.com'

# account_id             user_limit
# ----------             ----------
# DAXXXXXXXXXXXXXXXXXX   Not set
```

## How it works

### Authentication

The module uses the **Accounts API credentials** with the **child account's API hostname** — the standard Duo MSP authentication pattern:

```
Accounts IKEY + Accounts SKEY  ->  signed against child account's hostname
```

This is the same pattern used in the Python scripts in this repo.

### Signing

Duo uses HMAC-SHA1 over a canonical string of:

```
date / METHOD / host / path / params
```

This is handled internally and not exposed as a callable function.

## Module structure

```
duo-subaccount-hard-user-limit/
  DuoSubaccountUserLimit.psd1      Module manifest
  DuoSubaccountUserLimit.psm1      Module loader
  Private/
    Invoke-DuoSignedRequest.ps1    HMAC-SHA1 signing + HTTP (not exported)
    Get-DuoCredentials.ps1         Reads env vars (not exported)
  Public/
    Get-DuoChildAccounts.ps1
    Get-DuoUserLimit.ps1
    Set-DuoUserLimit.ps1
```
