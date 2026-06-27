// Infra version: 4 — Easy Auth config managed in Bicep to survive redeployments
@description('Name prefix used for all resources (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = resourceGroup().location

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'S1'])
param sku string = 'B1'

@secure()
param tokenEncryptionKey string

@description('Google OAuth Client ID')
param googleClientId string

@secure()
@description('Google OAuth Client Secret')
param googleClientSecret string

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

// ── App Service Plan ───────────────────────────────────────────────────────
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: planName
  location: location
  kind: 'linux'
  sku: { name: sku }
  properties: { reserved: true }
}

// ── App Service ────────────────────────────────────────────────────────────
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: siteName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true'
      appSettings: [
        { name: 'WEBSITES_PORT',                          value: '8000' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT',         value: 'true' }
        { name: 'AZURE_STORAGE_ACCOUNT_NAME',             value: storageAccountName }
        { name: 'TOKEN_ENCRYPTION_KEY',                   value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretTokenKey.properties.secretUri})' }
        { name: 'GOOGLE_PROVIDER_AUTHENTICATION_SECRET',  value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretGoogleClientSecret.properties.secretUri})' }
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
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }

  resource secretTokenKey 'secrets' = {
    name: 'token-encryption-key'
    properties: { value: tokenEncryptionKey }
  }

  resource secretGoogleClientSecret 'secrets' = {
    name: 'google-client-secret'
    properties: { value: googleClientSecret }
  }
}

// ── Grant App Service read access to Key Vault ─────────────────────────────
resource kvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appService.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Grant App Service read/write access to Blob Storage ───────────────────
resource storageBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appService.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Easy Auth (Google OAuth) ───────────────────────────────────────────────
resource authSettings 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'google'
    }
    identityProviders: {
      google: {
        enabled: true
        registration: {
          clientId: googleClientId
          clientSecretSettingName: 'GOOGLE_PROVIDER_AUTHENTICATION_SECRET'
        }
        login: {
          scopes: ['openid', 'profile', 'email']
        }
      }
    }
    login: {
      tokenStore: {
        enabled: true
      }
    }
    httpSettings: {
      requireHttps: true
    }
  }
}

output appUrl string = 'https://${appService.properties.defaultHostName}'
output appName string = appService.name
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
