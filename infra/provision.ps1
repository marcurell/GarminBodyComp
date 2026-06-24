# provision.ps1 — Run this once to create Azure resources
# Prerequisites: Azure CLI installed and logged in (az login)
#
# Usage:
#   .\infra\provision.ps1 -ResourceGroup "garmin-rg" -AppName "garminbodycomp"

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$false)]
    [string]$AppName = "garminbodycomp",

    [Parameter(Mandatory=$false)]
    [string]$Location = "westeurope",

    [Parameter(Mandatory=$false)]
    [string]$Sku = "B1"
)

Write-Host "Creating resource group '$ResourceGroup' in '$Location'..."
az group create --name $ResourceGroup --location $Location

Write-Host "Deploying Bicep template..."
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters appName=$AppName sku=$Sku `
    --output table

Write-Host ""
Write-Host "Done! Next step: download the publish profile from the Azure Portal"
Write-Host "  1. Go to: https://portal.azure.com -> App Services -> $AppName"
Write-Host "  2. Click 'Download publish profile'"
Write-Host "  3. Add it as a GitHub secret named AZURE_WEBAPP_PUBLISH_PROFILE"
Write-Host "     in: https://github.com/marcurell/GarminBodyComp/settings/secrets/actions"
