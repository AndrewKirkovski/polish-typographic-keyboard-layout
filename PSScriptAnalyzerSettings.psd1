@{
    Severity = @('Error', 'Warning')
    # Only exclude style rules that don't apply to an interactive installer script.
    # PSUseBOMForUnicodeEncodedFile is intentionally NOT excluded: suppressing it
    # masked a real parse-breaking bug (em-dash + no BOM under Win PS 5.1 ANSI decode).
    ExcludeRules = @(
        'PSAvoidUsingWriteHost',                      # installer UX needs colored console output
        'PSUseShouldProcessForStateChangingFunctions', # internal helpers, not exported cmdlets
        'PSUseSingularNouns'                           # Find-ResidualTrace/Layouts naming matches intent
    )
    Rules = @{
        PSUseCompatibleSyntax = @{
            Enable = $true
            TargetVersions = @('5.1')
        }
    }
}
