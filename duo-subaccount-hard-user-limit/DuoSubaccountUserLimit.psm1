# Load private functions (not exported)
foreach ($private in Get-ChildItem -Path "$PSScriptRoot/Private/*.ps1" -ErrorAction SilentlyContinue) {
    . $private.FullName
}

# Load and export public functions
foreach ($public in Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue) {
    . $public.FullName
}

Export-ModuleMember -Function Get-DuoChildAccounts, Get-DuoUserLimit, Set-DuoUserLimit
