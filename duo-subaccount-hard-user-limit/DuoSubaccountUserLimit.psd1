@{
    ModuleVersion     = '1.0.0'
    GUID              = 'a3f2c1d4-5e6b-7890-abcd-ef1234567890'
    Author            = 'MSP Admin'
    Description       = 'Manage hard user limits on Duo Security child accounts via the undocumented billing endpoint.'
    PowerShellVersion = '7.0'
    RootModule        = 'DuoSubaccountUserLimit.psm1'
    FunctionsToExport = @(
        'Get-DuoChildAccounts'
        'Get-DuoUserLimit'
        'Set-DuoUserLimit'
    )
    PrivateData       = @{
        PSData = @{
            Tags = @('Duo', 'Security', 'MFA', 'MSP', 'Admin')
        }
    }
}
