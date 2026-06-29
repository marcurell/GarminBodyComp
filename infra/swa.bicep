@description('Name prefix (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region for the Static Web App')
param location string = 'westeurope'

var swaName = '${appName}-app'
var apiSiteName = '${appName}-api'

// The FastAPI App Service we link as the SWA's backend (created by api.bicep).
resource apiService 'Microsoft.Web/sites@2023-01-01' existing = {
  name: apiSiteName
}

// Standard tier is REQUIRED for "bring your own backend" (linked App Service).
// The Free tier only supports managed Azure Functions, not a linked App Service.
resource swa 'Microsoft.Web/staticSites@2023-01-01' = {
  name: swaName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    buildProperties: {
      appLocation: 'frontend'
      outputLocation: 'dist'
    }
  }
}

// Link the API under the SWA's /api/* route. SWA becomes the auth layer and
// forwards the authenticated user to the backend via x-ms-client-principal,
// so the browser never talks to the API cross-origin (no CORS, same origin).
resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2023-01-01' = {
  parent: swa
  name: 'api'
  properties: {
    backendResourceId: apiService.id
    region: apiService.location
  }
}

output swaUrl string = 'https://${swa.properties.defaultHostname}'
output swaName string = swa.name
