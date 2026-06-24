@description('Name prefix used for all resources (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = resourceGroup().location

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'S1'])
param sku string = 'B1'

@secure()
param authUsername string = 'lars'

@secure()
param authPassword string

@secure()
param authCookieKey string

var planName = '${appName}-plan'
var siteName = appName
var storageAccountName = replace(toLower(appName), '-', '')
var keyVaultName = '${appName}-kv'

// ── Storage Account ────────────────────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
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

resource userDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'userdata'
  properties: { publicAccess: 'None' }
}

var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'

// ── App Service Plan ───────────────────────────────────────────────────────
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: planName
  location: location
  kind: 'linux'
  sku: { name: sku }
  properties: { reserved: true }
}

// ── App Service (with system-assigned Managed Identity) ────────────────────
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: siteName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true'
      appSettings: [
        { name: 'WEBSITES_PORT',                    value: '8000' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT',   value: 'true' }
        // Key Vault references — Azure resolves these at runtime
        { name: 'AZURE_STORAGE_CONNECTION_STRING',  value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretStorage.properties.secretUri})' }
        { name: 'AUTH_USERNAME',                    value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretUsername.properties.secretUri})' }
        { name: 'AUTH_PASSWORD',                    value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretPassword.properties.secretUri})' }
        { name: 'AUTH_COOKIE_KEY',                  value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretCookieKey.properties.secretUri})' }
      ]
    }
    httpsOnly: true
  }
}

// ── Key Vault ──────────────────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true  // use RBAC instead of access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }

  resource secretStorage 'secrets' = {
    name: 'storage-connection-string'
    properties: { value: storageConnectionString }
  }

  resource secretUsername 'secrets' = {
    name: 'auth-username'
    properties: { value: authUsername }
  }

  resource secretPassword 'secrets' = {
    name: 'auth-password'
    properties: { value: authPassword }
  }

  resource secretCookieKey 'secrets' = {
    name: 'auth-cookie-key'
    properties: { value: authCookieKey }
  }
}

// ── Grant App Service Managed Identity read access to Key Vault ────────────
// Built-in role: Key Vault Secrets User = 4633458b-17de-408a-b874-0445c86b69e6
resource kvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appService.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────
output appUrl string = 'https://${appService.properties.defaultHostName}'
output appName string = appService.name
output keyVaultName string = keyVault.name
