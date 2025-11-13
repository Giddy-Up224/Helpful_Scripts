# A simple script to delete all files in all subdirectories except for the specified type. (*.png in this case)

$parentDirectoryPath = Read-Host "Please paste the file path to the directory you wish to search"

Write-Host "Deleting files..."

Get-ChildItem -Path $parentDirectoryPath -File -Recurse -Exclude *.png | ForEach-Object { Remove-Item $_.FullName }

Read-Host "Done!"