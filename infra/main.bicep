targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('azd 환경 이름. 리소스 이름의 접미사(고유 토큰 계산)에 사용됩니다.')
param environmentName string

@minLength(1)
@description('리소스를 배포할 Azure 리전')
param location string

@secure()
@description('NEIS Open API 인증키 (https://open.neis.go.kr 에서 발급)')
param neisApiKey string

@description('백엔드가 허용할 프론트엔드 오리진(CORS). 비워두면 프론트엔드 Container App의 FQDN을 자동으로 사용합니다.')
param frontendOrigin string = ''

@description('오늘의 왕 배치 실행 시각(시)')
param tournamentRunHour string = '0'

@description('오늘의 왕 배치 실행 시각(분)')
param tournamentRunMinute string = '10'

var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    tags: tags
    neisApiKey: neisApiKey
    frontendOrigin: frontendOrigin
    tournamentRunHour: tournamentRunHour
    tournamentRunMinute: tournamentRunMinute
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.containerRegistryLoginServer
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = resources.outputs.containerAppsEnvironmentId
output BACKEND_URI string = resources.outputs.backendUri
output MCP_URI string = resources.outputs.mcpUri
output FRONTEND_URI string = resources.outputs.frontendUri
