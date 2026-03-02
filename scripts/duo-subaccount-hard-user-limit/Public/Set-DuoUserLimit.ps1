function Set-DuoUserLimit {
    <#
    .SYNOPSIS
    Sets the hard user limit for a Duo child account.

    .DESCRIPTION
    Calls the undocumented /admin/v1/billing/user_limit endpoint on the child
    account's Admin API using the Accounts API credentials (the standard MSP
    pattern: parent creds + child hostname).

    Set to 0 to remove the limit.

    Accepts pipeline input from Get-DuoChildAccounts.

    .PARAMETER AccountId
    The child account ID (DA-prefixed, e.g. DA12345).

    .PARAMETER ApiHostname
    The child account's Admin API hostname (e.g. api-XXXXXXXX.duosecurity.com).
    When piping from Get-DuoChildAccounts this is read from the api_hostname property.

    .PARAMETER UserLimit
    The maximum number of users allowed on the account. Use 0 to remove the limit.

    .EXAMPLE
    Set-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com -UserLimit 100

    .EXAMPLE
    # Pipe a specific account from the list
    Get-DuoChildAccounts | Where-Object name -eq 'Acme Corp' | Set-DuoUserLimit -UserLimit 50

    .EXAMPLE
    # Remove the limit
    Set-DuoUserLimit -AccountId DA12345 -ApiHostname api-XXXXXXXX.duosecurity.com -UserLimit 0

    .OUTPUTS
    PSCustomObject with account_id and user_limit properties reflecting the new state.
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [Alias('account_id')]
        [ValidatePattern('^DA')]
        [string]$AccountId,

        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [Alias('api_hostname')]
        [string]$ApiHostname,

        [Parameter(Mandatory)]
        [ValidateRange(0, [int]::MaxValue)]
        [int]$UserLimit
    )

    process {
        if (-not $PSCmdlet.ShouldProcess($AccountId, "Set user limit to $UserLimit")) {
            return
        }

        $creds = Get-DuoCredentials

        $result = Invoke-DuoSignedRequest `
            -Method         POST `
            -Host           $ApiHostname `
            -Path           '/admin/v1/billing/user_limit' `
            -Params         @{
                account_id = $AccountId
                user_limit = [string]$UserLimit
            } `
            -IntegrationKey $creds.IntegrationKey `
            -SecretKey      $creds.SecretKey

        [PSCustomObject]@{
            account_id = $AccountId
            user_limit = $result.user_limit
        }
    }
}
