# This works. It throws an error, but it works as it's supposed to.

# Enter the text you wish to search for btween the double quotes.
$searchText = ""

# Enter the new text (replacement text) between the double quotes.
$replacementText = ""


Get-ChildItem | ForEach-Object {
    $newName = $_.FullName -replace $searchText, $replacementText
    Rename-Item -Path $_.FullName -NewName $newName
}
