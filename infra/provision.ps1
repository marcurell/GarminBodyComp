# provision.ps1 — Run this once to create all Azure resources
#
# Prerequisites:
#   - Azure CLI installed and logged in:
#       az login --tenant a6017aee-56d1-484c-9b5a-5df2ab8d58fa
#       az account set --subscription 63621c47-1b51-4ac6-b577-9018793b8382
#
# Usage:
#   .\infra\provision.ps1 -ResourceGroup "garmin-rg" -AuthPassword "secret" -AuthCookieKey "random-string"

param(
    [Parameter(Mandatory=$true)]  [string]$ResourceGroup,
    [Parameter(Mandatory=$false)] [string]$AppName = "garminbodycomp",
    [Parameter(Mandatory=$false)] [string]$Location = "westeurope",
    [Parameter(Mandatory=$false)] [string]$Sku = "B1",
    [Parameter(Mandatory=$false)] [string]$AuthUsername = "lars",
    [Parameter(Mandatory=$true)]  [string]$AuthPassword,
    [Parameter(Mandatory=$true)]  [string]$AuthCookieKey
)

Write-Host "Creating resource group '$ResourceGroup' in '$Location'..."
az group create --name $ResourceGroup --location $Location

Write-Host "Deploying Bicep template (App Service + Storage + Key Vault)..."
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters `
        appName=$AppName `
        sku=$Sku `
        authUsername=$AuthUsername `
        authPassword=$AuthPassword `
        authCookieKey=$AuthCookieKey `
    --output table

Write-Host ""
Write-Host "All done! Resources created:"
Write-Host "  App Service : https://$AppName.azurewebsites.net"
Write-Host "  Key Vault   : $AppName-kv"
Write-Host "  Storage     : $($AppName.Replace('-',''))"
Write-Host ""
Write-Host "Next: update the GitHub publish profile secret if this is a fresh deployment."
Write-Host "  1. Azure Portal -> App Services -> $AppName -> Download publish profile"
Write-Host "  2. GitHub -> Settings -> Secrets -> AZURE_WEBAPP_PUBLISH_PROFILE"
