# Run the reg query command to get the hexadecimal ID
$rawID = (reg query "HKEY_LOCAL_MACHINE\SOFTWARE\TeamViewer" /v ClientID | Select-String -Pattern "0x[0-9A-Fa-f]+" -AllMatches).Matches.Value

# Convert the hexadecimal ID to decimal
$decimalID = [Convert]::ToInt32($rawID, 16)

# Display the results
Write-Host "TeamViewer ID: $decimalID"
