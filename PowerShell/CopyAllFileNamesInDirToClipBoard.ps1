# Paste your file path here between the double quotes
$directoryPath = ""

# Get all file names in the directory
$fileNames = Get-ChildItem -Path $directoryPath -File | Select-Object -ExpandProperty Name

# Join the file names into a single string with newline characters
$fileNamesString = $fileNames -join "`n"

# Copy the file names to the clipboard
Set-Clipboard -Value $fileNamesString

Write-Output "File names have been copied to the clipboard."