function Get-DuoUserLimit {
    <#
    .SYNOPSIS
    Gets the hard user limit for a Duo child account.

    .DESCRIPTION
    Calls the undocumented /admin/v1/billing/user_limit endpoint on the child
    account's Admin API using the Accounts API credentials (the standard MSP
    pattern: parent creds + child hostname).

    Accepts pipeline input from Get-DuoChildAccounts.

    .PARAMETER AccountId
    The child account ID (DA-prefixed, e.g. DA12345).

    .PARAMETER ApiHostname
    The child account's Admin API hostname (e.g. api-XXXXXXXX.duosecurity.com).
    When piping from Get-DuoChildAccounts this is read from the api_hostname property.

    .EXAMPLE
    Get-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com

    .EXAMPLE
    # Pipe from account list
    Get-DuoChildAccounts | Get-DuoUserLimit

    .OUTPUTS
    PSCustomObject with account_id and user_limit properties.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [Alias('account_id')]
        [ValidatePattern('^DA')]
        [string]$AccountId,

        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [Alias('api_hostname')]
        [string]$ApiHostname
    )

    process {
        $creds = Get-DuoCredentials

        $result = Invoke-DuoSignedRequest `
            -Method         GET `
            -Host           $ApiHostname `
            -Path           '/admin/v1/billing/user_limit' `
            -Params         @{ account_id = $AccountId } `
            -IntegrationKey $creds.IntegrationKey `
            -SecretKey      $creds.SecretKey

        [PSCustomObject]@{
            account_id = $AccountId
            user_limit = $result.user_limit
        }
    }
}
