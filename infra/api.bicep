// API App Service for FastAPI — shares the same plan and storage as the Streamlit app
@description('Name prefix used for all resources (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = resourceGroup().location

@description('Google OAuth Client ID')
param googleClientId string

@secure()
@description('Google OAuth Client Secret')
param googleClientSecret string

var planName = '${appName}-plan'
var apiSiteName = '${appName}-api'
var storageAccountName = replace(toLower(appName), '-', '')
var keyVaultName = '${appName}-kv'

// ── Reference existing shared resources ────────────────────────────────────
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' existing = {
  name: planName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// ── API App Service ────────────────────────────────────────────────────────
resource apiService 'Microsoft.Web/sites@2023-01-01' = {
  name: apiSiteName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'uvicorn api.main:app --host 0.0.0.0 --port 8000'
      healthCheckPath: '/health'
      appSettings: [
        { name: 'WEBSITES_PORT',              value: '8000' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'AZURE_STORAGE_ACCOUNT_NAME', value: storageAccountName }
        { name: 'TOKEN_ENCRYPTION_KEY',       value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretTokenKey.properties.secretUri})' }
        { name: 'GOOGLE_PROVIDER_AUTHENTICATION_SECRET', value: '@Microsoft.KeyVault(SecretUri=${keyVault::secretGoogleClientSecret.properties.secretUri})' }
      ]
    }
    httpsOnly: true
  }
}

// ── Key Vault secrets referenced (must already exist, created by main.bicep) ──
resource secretTokenKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = {
  parent: keyVault
  name: 'token-encryption-key'
}

resource secretGoogleClientSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = {
  parent: keyVault
  name: 'google-client-secret'
}

// ── Grant API App Service read access to Key Vault ─────────────────────────
resource apiKvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, apiService.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: apiService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Grant API App Service read/write access to Blob Storage ───────────────
resource apiStorageBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, apiService.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: apiService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Easy Auth — require authentication, return 401 (not redirect) ──────────
// Mobile clients expect 401 JSON, not 302 HTML redirect
resource apiAuthSettings 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: apiService
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
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

output apiUrl string = 'https://${apiService.properties.defaultHostName}'
output apiName string = apiService.name
