# DuoSubaccountUserLimit

> **Disclaimer:** This is an unofficial tool and is not supported by Cisco or Duo Security. It relies on an undocumented API endpoint that may change or be removed without notice. Use at your own risk.

PowerShell module for MSP admins to list Duo child accounts and get/set hard user limits via the undocumented `/admin/v1/billing/user_limit` endpoint.

No dependency on the DuoSecurity gallery module — signing is self-contained.

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

For persistent credentials, add these to your PowerShell profile (`$PROFILE`) or use a secrets manager.

### Why environment variables?

PowerShell has no standard `.conf` convention. Environment variables are the idiomatic approach for:
- Compatibility with CI/CD runners (GitHub Actions, Azure Pipelines, etc.)
- Consistency with the existing Python scripts in this repo
- Avoiding credentials at rest in plain text files

If you want secrets stored securely on a workstation, the [Microsoft.PowerShell.SecretManagement](https://learn.microsoft.com/en-us/powershell/utility-modules/secretmanagement/overview) module is the right tool — load secrets from it and assign to `$env:` before importing this module.

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
Get-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com
```

### Get user limits for all child accounts

```powershell
Get-DuoChildAccounts | Get-DuoUserLimit
```

### Set a user limit

```powershell
Set-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com -UserLimit 100
```

### Set a limit by account name (using pipeline)

```powershell
Get-DuoChildAccounts | Where-Object name -eq 'Acme Corp' | Set-DuoUserLimit -UserLimit 50
```

### Remove a limit (set to 0)

```powershell
Set-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com -UserLimit 0
```

### Preview a set operation without applying it (-WhatIf)

```powershell
Get-DuoChildAccounts | Where-Object name -eq 'Acme Corp' | Set-DuoUserLimit -UserLimit 50 -WhatIf
```

### Bulk report: all accounts with their current limits

```powershell
Get-DuoChildAccounts | Get-DuoUserLimit | Format-Table
```

## How it works

### Authentication

The module uses the **Accounts API credentials** with the **child account's API hostname** — the standard Duo MSP authentication pattern:

```
Accounts IKEY + Accounts SKEY  →  signed against child account's hostname
```

This is the same pattern used in the Python scripts in this repo.

### Signing

Duo uses HMAC-SHA1 over a canonical string of:
```
date\nMETHOD\nhost\npath\nparams
```

This is handled internally by `Invoke-DuoSignedRequest` (a private function — not callable directly).

## Module structure

```
duo-subaccount-hard-user-limit/
├── DuoSubaccountUserLimit.psd1      # Module manifest
├── DuoSubaccountUserLimit.psm1      # Module loader
├── Private/
│   ├── Invoke-DuoSignedRequest.ps1  # HMAC-SHA1 signing + HTTP (not exported)
│   └── Get-DuoCredentials.ps1       # Reads env vars, throws if missing (not exported)
└── Public/
    ├── Get-DuoChildAccounts.ps1
    ├── Get-DuoUserLimit.ps1
    └── Set-DuoUserLimit.ps1
```
