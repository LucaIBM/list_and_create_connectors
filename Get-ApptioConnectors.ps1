<#
.SYNOPSIS
    Retrieves the list of connectors from an Apptio customer account.

.DESCRIPTION
    This PowerShell script authenticates with Apptio API, retrieves the environment ID,
    and fetches all connectors, saving each as a separate JSON file.

.PARAMETER ConfigDir
    Directory containing configuration files (default: P2)

.PARAMETER OutputDir
    Directory to save connector JSON files (default: connectors)

.PARAMETER Debug
    Enable debug output

.EXAMPLE
    .\Get-ApptioConnectors.ps1
    
.EXAMPLE
    .\Get-ApptioConnectors.ps1 -ConfigDir "P2" -OutputDir "my_connectors" -Debug

.NOTES
    Requires configuration files in the specified directory:
    - frontdoor.conf
    - datalink.conf
    - customer.conf
    - keyAccess.conf
    - keySecret.conf
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigDir = "P2",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "connectors",
    
    [Parameter(Mandatory=$false)]
    [switch]$Debug
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Enable debug output if requested
if ($Debug) {
    $DebugPreference = "Continue"
}

#region Helper Functions

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Warning', 'Error', 'Success', 'Debug')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        'Info'    { 'Cyan' }
        'Warning' { 'Yellow' }
        'Error'   { 'Red' }
        'Success' { 'Green' }
        'Debug'   { 'Gray' }
    }
    
    if ($Level -eq 'Debug' -and -not $Debug) {
        return
    }
    
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Read-ConfigFile {
    param(
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        throw "Configuration file not found: $FilePath"
    }
    
    $content = Get-Content -Path $FilePath -Raw
    return $content.Trim()
}

function Sanitize-Filename {
    param(
        [string]$Name
    )
    
    # Remove invalid characters
    $sanitized = $Name -replace '[<>:"/\\|?*]', '_'
    # Replace spaces with underscores
    $sanitized = $sanitized -replace '\s+', '_'
    # Limit length
    if ($sanitized.Length -gt 200) {
        $sanitized = $sanitized.Substring(0, 200)
    }
    
    return $sanitized
}

#endregion

#region Main Script

try {
    Write-Log "Starting Apptio connector retrieval..." -Level Info
    
    # Step 0: Load configuration files
    Write-Log "Loading configuration from $ConfigDir..." -Level Info
    
    $configPath = Join-Path $PSScriptRoot $ConfigDir
    
    $config = @{
        frontdoor = Read-ConfigFile (Join-Path $configPath "frontdoor.conf")
        datalink  = Read-ConfigFile (Join-Path $configPath "datalink.conf")
        customer  = Read-ConfigFile (Join-Path $configPath "customer.conf")
        keyAccess = Read-ConfigFile (Join-Path $configPath "keyAccess.conf")
        keySecret = Read-ConfigFile (Join-Path $configPath "keySecret.conf")
    }
    
    Write-Log "Configuration loaded successfully" -Level Success
    Write-Log "Frontdoor: $($config.frontdoor)" -Level Debug
    Write-Log "Datalink: $($config.datalink)" -Level Debug
    Write-Log "Customer: $($config.customer)" -Level Debug
    
    # Step 1: Authenticate and get apptio-opentoken
    Write-Log "Step 1: Authenticating with Apptio API..." -Level Info
    
    $authUrl = "https://$($config.frontdoor)/service/apikeylogin"
    $authBody = @{
        keyAccess = $config.keyAccess
        keySecret = $config.keySecret
    } | ConvertTo-Json
    
    $authHeaders = @{
        'Content-Type' = 'application/json'
        'Accept' = 'application/json'
    }
    
    Write-Log "POST $authUrl" -Level Debug
    
    $authResponse = Invoke-WebRequest -Uri $authUrl `
                                       -Method Post `
                                       -Headers $authHeaders `
                                       -Body $authBody `
                                       -SessionVariable session
    
    # Extract apptio-opentoken from cookies
    $apptioOpenToken = $session.Cookies.GetCookies($authUrl) | 
                       Where-Object { $_.Name -eq 'apptio-opentoken' } | 
                       Select-Object -ExpandProperty Value
    
    if (-not $apptioOpenToken) {
        throw "Failed to retrieve apptio-opentoken from authentication response"
    }
    
    Write-Log "Authentication successful - token retrieved" -Level Success
    Write-Log "Token: $($apptioOpenToken.Substring(0, 20))..." -Level Debug
    
    # Step 2: Get environment ID
    Write-Log "Step 2: Retrieving environment ID..." -Level Info
    
    $envUrl = "https://$($config.frontdoor)/api/environment/$($config.customer)/main"
    $envHeaders = @{
        'Content-Type' = 'application/json'
        'apptio-opentoken' = $apptioOpenToken
    }
    
    Write-Log "GET $envUrl" -Level Debug
    
    $envResponse = Invoke-RestMethod -Uri $envUrl `
                                      -Method Get `
                                      -Headers $envHeaders `
                                      -WebSession $session
    
    if (-not $envResponse.id) {
        throw "No 'id' field found in environment response"
    }
    
    $apptioCurrentEnvironment = $envResponse.id
    Write-Log "Environment ID retrieved: $apptioCurrentEnvironment" -Level Success
    
    # Step 3: Get connectors list
    Write-Log "Step 3: Retrieving connectors list..." -Level Info
    
    $connectorsUrl = "https://$($config.datalink)/apptioconnect/api/v1/connections"
    $connectorsHeaders = @{
        'apptio-opentoken' = $apptioOpenToken
        'apptio-current-environment' = $apptioCurrentEnvironment
        'Accept' = 'application/json'
    }
    
    Write-Log "GET $connectorsUrl" -Level Debug
    
    $connectors = Invoke-RestMethod -Uri $connectorsUrl `
                                     -Method Get `
                                     -Headers $connectorsHeaders `
                                     -WebSession $session
    
    if (-not ($connectors -is [Array])) {
        throw "Response is not an array"
    }
    
    Write-Log "Retrieved $($connectors.Count) connectors" -Level Success
    
    # Step 4: Save connectors to files
    Write-Log "Saving connectors to $OutputDir/..." -Level Info
    
    # Create output directory
    $outputPath = Join-Path $PSScriptRoot $OutputDir
    if (-not (Test-Path $outputPath)) {
        New-Item -Path $outputPath -ItemType Directory -Force | Out-Null
        Write-Log "Created output directory: $outputPath" -Level Debug
    }
    
    $savedCount = 0
    for ($i = 0; $i -lt $connectors.Count; $i++) {
        $connector = $connectors[$i]
        
        try {
            # Determine filename from connector name or ID
            $filename = $null
            if ($connector.name) {
                $filename = Sanitize-Filename $connector.name
            }
            elseif ($connector.id) {
                $filename = Sanitize-Filename $connector.id.ToString()
            }
            else {
                $filename = "connector_$($i + 1)"
            }
            
            # Ensure .json extension
            if (-not $filename.EndsWith('.json')) {
                $filename += '.json'
            }
            
            $filePath = Join-Path $outputPath $filename
            
            # Convert to JSON and save
            $connector | ConvertTo-Json -Depth 10 | Set-Content -Path $filePath -Encoding UTF8
            
            Write-Log "Saved: $filename" -Level Info
            $savedCount++
        }
        catch {
            Write-Log "Failed to save connector $($i + 1): $($_.Exception.Message)" -Level Error
        }
    }
    
    Write-Log "Successfully saved $savedCount/$($connectors.Count) connectors" -Level Success
    
    # Final summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] Connector retrieval completed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Connectors saved to: $outputPath" -ForegroundColor Cyan
    Write-Host "Total connectors: $($connectors.Count)" -ForegroundColor Cyan
    Write-Host "Successfully saved: $savedCount" -ForegroundColor Cyan
    Write-Host ""
    
    exit 0
}
catch {
    Write-Log "Error: $($_.Exception.Message)" -Level Error
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level Debug
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[FAILED] Failed to retrieve connectors" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    exit 1
}

#endregion

# Made with Bob
