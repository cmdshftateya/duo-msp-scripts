function Invoke-DuoSignedRequest {
    <#
    .SYNOPSIS
    Makes a signed request to the Duo API using HMAC-SHA1 authentication.

    .DESCRIPTION
    Internal function. Handles RFC 2822 date generation, parameter canonicalization,
    HMAC-SHA1 signature computation, and the actual HTTP call. Not exported.

    .PARAMETER Method
    HTTP method: GET or POST.

    .PARAMETER Host
    Duo API hostname (e.g. api-XXXXXXXX.duosecurity.com).

    .PARAMETER Path
    API endpoint path (e.g. /admin/v1/billing/user_limit).

    .PARAMETER Params
    Hashtable of query/body parameters.

    .PARAMETER IntegrationKey
    Duo integration key (ikey).

    .PARAMETER SecretKey
    Duo secret key (skey).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('GET', 'POST')]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$Host,

        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter()]
        [hashtable]$Params = @{},

        [Parameter(Mandatory)]
        [string]$IntegrationKey,

        [Parameter(Mandatory)]
        [string]$SecretKey
    )

    # RFC 2822 date in UTC
    $date = (Get-Date).ToUniversalTime().ToString('ddd, dd MMM yyyy HH:mm:ss -0000')

    # Build sorted, encoded parameter string
    $paramCollection = [System.Web.HttpUtility]::ParseQueryString([string]::Empty)
    foreach ($entry in ($Params.GetEnumerator() | Sort-Object -CaseSensitive -Property Key)) {
        $paramCollection.Add($entry.Key, $entry.Value)
    }
    $canonicalParams = $paramCollection.ToString() `
        -replace '%7E', '~' `
        -replace '\+', '%20'
    $canonicalParams = [regex]::Replace($canonicalParams, '(%[0-9A-Fa-f][0-9A-Fa-f])', { $args[0].Value.ToUpperInvariant() })
    $canonicalParams = [regex]::Replace($canonicalParams, "([!'()*])", { '%' + [System.Convert]::ToByte($args[0].Value[0]).ToString('X') })

    # Canonical signature body (newline-separated)
    $signatureParts = @(
        $date
        $Method.ToUpper()
        $Host.ToLower()
        $Path
        $canonicalParams
    )
    $signatureBody = $signatureParts -join "`n"

    # HMAC-SHA1
    $keyBytes  = [System.Text.Encoding]::UTF8.GetBytes($SecretKey)
    $dataBytes = [System.Text.Encoding]::UTF8.GetBytes($signatureBody)
    $hmac      = New-Object System.Security.Cryptography.HMACSHA1
    $hmac.Key  = $keyBytes
    $null      = $hmac.ComputeHash($dataBytes)
    $signature = [System.BitConverter]::ToString($hmac.Hash).Replace('-', '').ToLower()

    # Base64-encoded Basic auth header: ikey:signature
    $authString = 'Basic ' + [System.Convert]::ToBase64String(
        [System.Text.Encoding]::ASCII.GetBytes(('{0}:{1}' -f $IntegrationKey, $signature))
    )

    $headers = @{
        'X-Duo-Date'    = $date
        'Authorization' = $authString
    }

    $uriBuilder = [System.UriBuilder]('https://{0}{1}' -f $Host, $Path)

    $restParams = @{
        Method             = $Method
        Uri                = $uriBuilder.Uri
        Headers            = $headers
        SkipHttpErrorCheck = $true
    }

    if ($Method -eq 'POST') {
        $headers.'Content-Type' = 'application/x-www-form-urlencoded'
        $restParams.Body        = $canonicalParams
    } else {
        $uriBuilder.Query  = $canonicalParams
        $restParams.Uri    = $uriBuilder.Uri
    }

    $response = Invoke-RestMethod @restParams

    if ($response.stat -ne 'OK') {
        $msg = if ($response.message) { $response.message } else { $response | ConvertTo-Json -Depth 5 }
        throw "Duo API error: $msg"
    }

    $response.response
}
