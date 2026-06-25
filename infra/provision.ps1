# provision.ps1 — Run this once to create all Azure resources
#
# Prerequisites:
#   az login --tenant a6017aee-56d1-484c-9b5a-5df2ab8d58fa
#   az account set --subscription 63621c47-1b51-4ac6-b577-9018793b8382
#
# Usage:
#   .\infra\provision.ps1 -ResourceGroup "garmin-rg" -AuthPassword "yourpassword"
#
# TOKEN_ENCRYPTION_KEY is auto-generated if not provided.

param(
    [Parameter(Mandatory=$true)]  [string]$ResourceGroup,
    [Parameter(Mandatory=$false)] [string]$AppName = "garminbodycomp",
    [Parameter(Mandatory=$false)] [string]$Location = "westeurope",
    [Parameter(Mandatory=$false)] [string]$Sku = "B1",
    [Parameter(Mandatory=$false)] [string]$AuthUsername = "lars",
    [Parameter(Mandatory=$true)]  [string]$AuthPassword,
    [Parameter(Mandatory=$false)] [string]$TokenEncryptionKey = "",
    [Parameter(Mandatory=$false)] [string]$AuthCookieKey = ""
)

# Auto-generate a Fernet-compatible key if not provided
if (-not $TokenEncryptionKey) {
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $bytes = New-Object byte[] 32
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $TokenEncryptionKey = [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_')
    Write-Host "Generated TOKEN_ENCRYPTION_KEY: $TokenEncryptionKey"
    Write-Host "IMPORTANT: Save this key somewhere safe. You will need it if you re-provision."
    Write-Host ""
}

if (-not $AuthCookieKey) {
    $rng2 = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $bytes2 = New-Object byte[] 32
    $rng2.GetBytes($bytes2)
    $rng2.Dispose()
    $AuthCookieKey = [Convert]::ToBase64String($bytes2).Replace('+', '-').Replace('/', '_')
    Write-Host "Generated AUTH_COOKIE_KEY (save this too): $AuthCookieKey"
    Write-Host ""
}

Write-Host "Creating resource group '$ResourceGroup' in '$Location'..."
az group create --name $ResourceGroup --location $Location

Write-Host "Deploying Bicep template..."
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters `
        appName=$AppName `
        sku=$Sku `
        authUsername=$AuthUsername `
        authPassword=$AuthPassword `
        tokenEncryptionKey=$TokenEncryptionKey `
        authCookieKey=$AuthCookieKey `
    --output table

Write-Host ""
Write-Host "Done! Resources created:"
Write-Host "  App:       https://$AppName.azurewebsites.net"
Write-Host "  Key Vault: $AppName-kv"
Write-Host "  Storage:   $($AppName.Replace('-',''))"
Write-Host ""
Write-Host "Next: update publish profile secret in GitHub."
Write-Host "  1. Azure Portal -> App Services -> $AppName -> Download publish profile"
Write-Host "  2. GitHub -> Settings -> Secrets -> AZURE_WEBAPP_PUBLISH_PROFILE (update value)"
Write-Host ""
Write-Host "Reminder: Rotate AuthPassword and TokenEncryptionKey every 90 days."
