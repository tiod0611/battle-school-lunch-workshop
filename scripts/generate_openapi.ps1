# Excel 파일에서 API 명세를 추출하고 OpenAPI 3.0.4 JSON을 생성합니다

function Extract-ApiData {
    param([string]$FilePath)
    
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    
    try {
        $workbook = $excel.Workbooks.Open($FilePath, $null, $true)  # 읽기 전용 열기
        $sheet = $workbook.Sheets.Item(1)
        
        $data = @{
            ApiName = ""
            RequestUrl = ""
            BasicParams = @()
            RequestParams = @()
        }
        
        $maxRow = $sheet.UsedRange.Rows.Count
        
        for ($row = 1; $row -le $maxRow; $row++) {
            $col1 = $sheet.Cells.Item($row, 1).Value()
            
            if ($col1 -like "*(학교*" -or $col1 -like "*(급식*") {
                $data.ApiName = $col1.Trim()
            }
            
            if ($col1 -eq "• 요청주소") {
                $url = $sheet.Cells.Item($row + 1, 1).Value()
                if ($url) {
                    $data.RequestUrl = $url -replace "^- ", ""
                }
            }
            
            if ($col1 -eq "• 기본인자") {
                for ($prow = $row + 2; $prow -le $maxRow; $prow++) {
                    $name = $sheet.Cells.Item($prow, 1).Value()
                    if (-not $name -or $name -like "•*") { break }
                    
                    $type = $sheet.Cells.Item($prow, 2).Value()
                    $desc = $sheet.Cells.Item($prow, 3).Value()
                    
                    if ($name) {
                        $data.BasicParams += @{
                            name = $name
                            type = $type
                            desc = $desc
                        }
                    }
                }
            }
            
            if ($col1 -eq "• 요청인자") {
                for ($prow = $row + 2; $prow -le $maxRow; $prow++) {
                    $name = $sheet.Cells.Item($prow, 1).Value()
                    if (-not $name -or $name -like "•*") { break }
                    
                    $type = $sheet.Cells.Item($prow, 2).Value()
                    $desc = $sheet.Cells.Item($prow, 3).Value()
                    
                    if ($name) {
                        $data.RequestParams += @{
                            name = $name
                            type = $type
                            desc = $desc
                        }
                    }
                }
            }
        }
        
        $workbook.Close($false)
        return $data
    }
    finally {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
}

function ConvertTo-OpenAPIType {
    param([string]$ExcelType)
    
    if ($ExcelType -like "*STRING*") {
        return "string"
    } elseif ($ExcelType -like "*INTEGER*") {
        return "integer"
    } else {
        return "string"
    }
}

function IsRequired {
    param([string]$ExcelType)
    return $ExcelType -like "*필수*"
}

# 메인 실행
Write-Host "OpenAPI JSON 생성 중..."

$dataDir = "C:\Users\tiod0\.copilot\repos\copilot-worktrees\battle-school-lunch-workshop\tiod0611-fluffy-winner\data"
$files = Get-ChildItem "$dataDir\*.xlsx"

$apis = @()
foreach ($file in $files) {
    Write-Host "파일 읽중: $($file.Name)"
    $api = Extract-ApiData -FilePath $file.FullName
    if ($api.RequestUrl) {
        $apis += $api
    }
}

# OpenAPI 객체 생성
$openapi = @{
    openapi = "3.0.4"
    info = @{
        title = "NEIS Open API"
        description = "학교 기본정보 및 급식 식단정보 공개 API"
        version = "1.0.0"
    }
    servers = @(
        @{
            url = "https://open.neis.go.kr"
            description = "NEIS Open API Server"
        }
    )
    paths = @{}
    components = @{
        schemas = @{
            Error = @{
                type = "object"
                properties = @{
                    code = @{ type = "string" }
                    message = @{ type = "string" }
                }
            }
        }
    }
}

# 각 API에 대한 경로 생성
foreach ($api in $apis) {
    if (-not $api.RequestUrl) { continue }
    
    $pathKey = $api.RequestUrl -replace "https://open.neis.go.kr", ""
    $params = @()
    
    # 기본 파라미터 + 요청 파라미터
    $allParams = $api.BasicParams + $api.RequestParams
    
    foreach ($param in $allParams) {
        $params += @{
            name = $param.name
            `in = "query"
            required = IsRequired -ExcelType $param.type
            description = $param.desc
            schema = @{
                type = ConvertTo-OpenAPIType -ExcelType $param.type
            }
        }
    }
    
    $openapi.paths[$pathKey] = @{
        get = @{
            summary = $api.ApiName
            operationId = if ($api.ApiName -like "*학교*") { "getSchoolInfo" } else { "getMealServiceDietInfo" }
            description = "API 요청"
            parameters = $params
            responses = @{
                "200" = @{
                    description = "성공적인 응답"
                    content = @{
                        "application/json" = @{
                            schema = @{
                                type = "object"
                            }
                        }
                        "application/xml" = @{
                            schema = @{
                                type = "object"
                            }
                        }
                    }
                }
                "400" = @{
                    description = "요청 오류"
                    content = @{
                        "application/json" = @{
                            schema = @{
                                `"$ref`" = "#/components/schemas/Error"
                            }
                        }
                    }
                }
                "500" = @{
                    description = "서버 오류"
                    content = @{
                        "application/json" = @{
                            schema = @{
                                `"$ref`" = "#/components/schemas/Error"
                            }
                        }
                    }
                }
            }
        }
    }
}

# JSON으로 변환 후 저장
$json = $openapi | ConvertTo-Json -Depth 10
$outputPath = "$dataDir\openapi.json"

$json | Out-File -FilePath $outputPath -Encoding UTF8

Write-Host "✓ OpenAPI JSON 생성 완료!"
Write-Host "출력 파일: $outputPath"
Write-Host "파일 크기: $((Get-Item $outputPath).Length) bytes"
