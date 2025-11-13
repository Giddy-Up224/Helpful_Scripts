# Function to find the Arduino port
function Find-Arduino {
    $ports = Get-WmiObject Win32_SerialPort
    foreach ($port in $ports) {
        if ($port.Description -like "*Arduino*") {  # Adjust this based on your device's description
            return $port.DeviceID
        }
    }
    return $null
}

# Find the Arduino port
$arduinoPort = Find-Arduino
if ($arduinoPort -eq $null) {
    Write-Host "Arduino not found. Please check the connection."
    exit
} else {
    Write-Host "Arduino found on $arduinoPort"
}

# Open the serial port
$port = new-Object System.IO.Ports.SerialPort $arduinoPort,9600,None,8,one
$port.Open()

Write-Host "Monitoring USB for shutdown signal..."

while ($true) {
    if ($port.BytesToRead -gt 0) {
        $line = $port.ReadLine().Trim()
        if ($line -eq "shutdown") {
            Write-Host "Shutdown signal received. Shutting down in 30 seconds. Press 'N' to cancel."
            
            $cancelShutdown = $false
            $timer = [System.Diagnostics.Stopwatch]::StartNew()
            
            while ($timer.Elapsed.TotalSeconds -lt 30) {
                if ($host.UI.RawUI.KeyAvailable) {
                    $key = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    if ($key.Character -eq 'N') {
                        $cancelShutdown = $true
                        Write-Host "Shutdown canceled."
                        break
                    }
                }
                Start-Sleep -Milliseconds 100
            }
            
            if (-not $cancelShutdown) {
                Write-Host "Proceeding with shutdown..."
                Stop-Computer -Force
                break
            }
        }
    }
    Start-Sleep -Milliseconds 100
}

# Close the serial port
$port.Close()