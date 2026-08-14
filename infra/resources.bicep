@description('리소스를 배포할 Azure 리전')
param location string

@description('azd 환경 이름')
param environmentName string

@description('공통 태그')
param tags object

@secure()
@description('NEIS Open API 인증키')
param neisApiKey string

@description('백엔드가 허용할 프론트엔드 오리진(CORS). 비워두면 프론트엔드 Container App의 FQDN을 자동으로 사용합니다.')
param frontendOrigin string = ''

param tournamentRunHour string = '0'
param tournamentRunMinute string = '10'

// 리소스 이름 충돌을 피하기 위한 리소스 그룹 단위 고유 토큰
var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName))
var abbrs = {
  logAnalytics: 'log-'
  containerAppsEnv: 'cae-'
  containerRegistry: 'acr'
  storageAccount: 'st'
  identity: 'id-'
  backendApp: 'ca-backend-'
  mcpApp: 'ca-mcp-'
  frontendApp: 'ca-frontend-'
}

var placeholderImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
var fileShareName = 'backend-data'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${abbrs.logAnalytics}${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: '${abbrs.containerRegistry}${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

// Container App들이 ACR에서 이미지를 pull할 때 사용하는 사용자 할당 관리 ID
resource acrPullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${abbrs.identity}acrpull-${resourceToken}'
  location: location
  tags: tags
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, acrPullIdentity.id, 'AcrPull')
  scope: containerRegistry
  properties: {
    principalId: acrPullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    // AcrPull 내장 역할
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  }
}

// 백엔드 SQLite DB(오늘의 왕 캐시 포함)를 컨테이너 재시작/재배포 후에도 보존하기 위한 Azure Files 공유
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${abbrs.storageAccount}${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }

  resource fileServices 'fileServices' = {
    name: 'default'

    resource share 'shares' = {
      name: fileShareName
      properties: {
        shareQuota: 5
      }
    }
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${abbrs.containerAppsEnv}${resourceToken}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource envStorage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: containerAppsEnvironment
  name: fileShareName
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: fileShareName
      accessMode: 'ReadWrite'
    }
  }
}

resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${abbrs.backendApp}${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${acrPullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: acrPullIdentity.id
        }
      ]
      secrets: [
        {
          name: 'neis-api-key'
          value: neisApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: placeholderImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'NEIS_API_KEY', secretRef: 'neis-api-key' }
            {
              name: 'FRONTEND_ORIGIN'
              value: empty(frontendOrigin) ? 'https://${frontendApp.properties.configuration.ingress.fqdn}' : frontendOrigin
            }
            { name: 'DATABASE_PATH', value: '/app/data/app.db' }
            { name: 'TOURNAMENT_RUN_HOUR', value: tournamentRunHour }
            { name: 'TOURNAMENT_RUN_MINUTE', value: tournamentRunMinute }
          ]
          volumeMounts: [
            {
              volumeName: fileShareName
              mountPath: '/app/data'
            }
          ]
        }
      ]
      volumes: [
        {
          name: fileShareName
          storageType: 'AzureFile'
          storageName: envStorage.name
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

resource mcpApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${abbrs.mcpApp}${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'mcp' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${acrPullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8100
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: acrPullIdentity.id
        }
      ]
      secrets: [
        {
          name: 'neis-api-key'
          value: neisApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'mcp'
          image: placeholderImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'NEIS_API_KEY', secretRef: 'neis-api-key' }
            { name: 'MCP_HOST', value: '0.0.0.0' }
            { name: 'MCP_PORT', value: '8100' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${abbrs.frontendApp}${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${acrPullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: acrPullIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: placeholderImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output backendUri string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output mcpUri string = 'https://${mcpApp.properties.configuration.ingress.fqdn}'
output frontendUri string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
