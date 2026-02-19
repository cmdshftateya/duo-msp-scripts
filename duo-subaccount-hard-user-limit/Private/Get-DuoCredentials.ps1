function Get-DuoCredentials {
    <#
    .SYNOPSIS
    Resolves Duo API credentials from environment variables.

    .DESCRIPTION
    Internal helper. Reads DUO_ACCOUNTS_IKEY, DUO_ACCOUNTS_SKEY, DUO_ACCOUNTS_HOST
    from the environment and returns them as a hashtable. Throws if any are missing.

    Credentials required:
        DUO_ACCOUNTS_IKEY  - Accounts API integration key
        DUO_ACCOUNTS_SKEY  - Accounts API secret key
        DUO_ACCOUNTS_HOST  - Accounts API hostname (api-accounts.duosecurity.com)
    #>
    [CmdletBinding()]
    [OutputType([hashtable])]
    param()

    $ikey = $env:DUO_ACCOUNTS_IKEY
    $skey = $env:DUO_ACCOUNTS_SKEY
    $host = $env:DUO_ACCOUNTS_HOST

    $missing = @()
    if (-not $ikey) { $missing += 'DUO_ACCOUNTS_IKEY' }
    if (-not $skey) { $missing += 'DUO_ACCOUNTS_SKEY' }
    if (-not $host) { $missing += 'DUO_ACCOUNTS_HOST' }

    if ($missing.Count -gt 0) {
        throw "Missing required environment variable(s): $($missing -join ', '). See README for setup instructions."
    }

    @{
        IntegrationKey = $ikey
        SecretKey      = $skey
        Host           = $host
    }
}
