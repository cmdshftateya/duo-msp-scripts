function Get-DuoChildAccounts {
    <#
    .SYNOPSIS
    Lists all child accounts under the MSP parent.

    .DESCRIPTION
    Calls the Duo Accounts API (/accounts/v1/account/list) using credentials from
    environment variables and returns all child account objects.

    Each returned object includes:
        name          - Account display name
        account_id    - Account ID (DA-prefixed, e.g. DA12345)
        api_hostname  - The child account's Admin API hostname

    .EXAMPLE
    Get-DuoChildAccounts

    .EXAMPLE
    Get-DuoChildAccounts | Select-Object name, account_id

    .EXAMPLE
    # Pipe directly into Get-DuoUserLimit
    Get-DuoChildAccounts | Get-DuoUserLimit

    .OUTPUTS
    PSCustomObject[]
    #>
    [CmdletBinding()]
    param()

    $creds = Get-DuoCredentials

    Invoke-DuoSignedRequest `
        -Method         POST `
        -Host           $creds.Host `
        -Path           '/accounts/v1/account/list' `
        -IntegrationKey $creds.IntegrationKey `
        -SecretKey      $creds.SecretKey
}
