# Prompt user for the text to search, folder path, and file type
$folderToSearch = Read-Host "Please paste the file path to the folder where you wish to search"
$searchText = Read-Host "Enter the text to search"
$fileType1 = Read-Host "Enter the file type to search"
$fileType = "*.$fileType1"

$resultPaths = @()
$count = 0

# Get files and search for the specified text
Get-ChildItem -Path $folderToSearch -Recurse -Filter $fileType | Where-Object { $_.PSIsContainer -eq $false } | ForEach-Object {
    $filePath = $_.FullName

    $content = Get-Content $filePath -Raw
    if ($content -match $searchText) {
        $resultPaths += $filePath
		Write-Host "Found in $filePath"
    }
	else {
		$count++
		Write-Host "Searching $count file"
	}
}

# Set the .zip filepath to the current user's Downloads folder.
$zipFilePath = Join-Path $env:USERPROFILE "Downloads\SearchResults.zip"

# Check if the zip file already exists
if (Test-Path $zipFilePath) {
    Write-Host "The 'SearchResults.zip' file already exists in the Downloads folder."
    $choice = Read-Host "Do you want to overwrite it (O) or auto-rename the new one (A)? [O/A]"

    if ($choice -eq "O" -or "o") {
        # Overwrite the existing zip file
        Compress-Archive -Path $resultPaths -DestinationPath $zipFilePath -Force
        Write-Host "Result files have been overwritten in the 'SearchResults.zip' file."
    }
    elseif ($choice -eq "A" -or "a") {
        # Auto-rename the new zip file
        $newZipFilePath = Join-Path $env:USERPROFILE "Downloads\SearchResults_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
        Compress-Archive -Path $resultPaths -DestinationPath $newZipFilePath
        Write-Host "Result files have been compressed into a new zip file: '$newZipFilePath'."
    }
    else {
        Write-Host "Invalid choice. No action taken."
    }
}
else {
    # Zip file doesn't exist, create a new one
    Compress-Archive -Path $resultPaths -DestinationPath $zipFilePath
    Write-Host "Result files have been compressed into a zip file and placed in Downloads."
}

Read-Host "Press Enter to exit..."