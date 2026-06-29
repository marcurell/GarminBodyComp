// API App Service for FastAPI — shares the same plan and storage as the Streamlit app
@description('Name prefix used for all resources (e.g. "garminbodycomp")')
param appName string = 'garminbodycomp'

@description('Azure region')
param location string = resourceGroup().location

@description('Comma-separated allow-list of emails permitted to use the API')
param allowedEmails string = 'lars@joyyoga.se'

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

// Token-encryption key (created by main.bicep) — reused so the API can decrypt
// the same stored Garmin OAuth tokens as the Streamlit app.
resource secretTokenKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = {
  parent: keyVault
  name: 'token-encryption-key'
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
      // 'python -m uvicorn' (not the bare 'uvicorn' console script) so the app
      // directory /home/site/wwwroot is on sys.path and 'api' is importable.
      appCommandLine: 'python -m uvicorn api.main:app --host 0.0.0.0 --port 8000'
      healthCheckPath: '/health'
      appSettings: [
        { name: 'WEBSITES_PORT',                  value: '8000' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT',  value: 'true' }
        { name: 'AZURE_STORAGE_ACCOUNT_NAME',      value: storageAccountName }
        { name: 'ALLOWED_EMAILS',                  value: allowedEmails }
        { name: 'TOKEN_ENCRYPTION_KEY',            value: '@Microsoft.KeyVault(SecretUri=${secretTokenKey.properties.secretUri})' }
      ]
    }
    httpsOnly: true
  }
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

// ── Easy Auth DISABLED ─────────────────────────────────────────────────────
// The Static Web App is the authentication layer. It forwards the signed-in
// user to this backend via the `x-ms-client-principal` header (decoded in
// api/dependencies.py). App Service Easy Auth would STRIP that header if it
// were enabled, so it is turned off here. Identity is still enforced in code
// (a missing principal → 401) and gated by the ALLOWED_EMAILS allow-list.
resource apiAuthSettings 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: apiService
  name: 'authsettingsV2'
  properties: {
    platform: {
      enabled: false
    }
    globalValidation: {
      requireAuthentication: false
      unauthenticatedClientAction: 'AllowAnonymous'
    }
  }
}

output apiUrl string = 'https://${apiService.properties.defaultHostName}'
output apiName string = apiService.name
