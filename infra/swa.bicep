@description('Name prefix (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = 'westeurope'

var swaName = '${appName}-app'

resource swa 'Microsoft.Web/staticSites@2023-01-01' = {
  name: swaName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: 'frontend'
      outputLocation: 'dist'
    }
  }
}

output swaUrl string = 'https://${swa.properties.defaultHostname}'
output swaName string = swa.name
