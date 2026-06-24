@description('Name prefix used for all resources (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = resourceGroup().location

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'S1'])
param sku string = 'B1'

// Auth credentials — set these at deploy time or update via Azure Portal afterwards
@secure()
param authUsername string = 'lars'

@secure()
param authPassword string

var planName = '${appName}-plan'
var siteName = appName
var storageAccountName = replace(toLower(appName), '-', '')  // storage names must be lowercase alphanumeric

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// One container per user — already structured for multi-user expansion
resource userDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'userdata'
  properties: {
    publicAccess: 'None'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: planName
  location: location
  kind: 'linux'
  sku: {
    name: sku
  }
  properties: {
    reserved: true
  }
}

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: siteName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true'
      appSettings: [
        { name: 'WEBSITES_PORT',               value: '8000' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'AZURE_STORAGE_CONNECTION_STRING', value: storageAccount.listKeys().keys[0].value == '' ? '' : 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net' }
        { name: 'AUTH_USERNAME',               value: authUsername }
        { name: 'AUTH_PASSWORD',               value: authPassword }
      ]
    }
    httpsOnly: true
  }
}

output appUrl string = 'https://${appService.properties.defaultHostName}'
output appName string = appService.name
output storageAccountName string = storageAccount.name
