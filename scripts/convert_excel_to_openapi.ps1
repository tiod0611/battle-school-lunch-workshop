# Excel 파일을 분석해서 OpenAPI JSON을 생성합니다
# PowerShell로 Excel을 ZIP으로 열어서 데이터를 추출합니다

param(
    [string]$ExcelPath,
    [string]$OutputPath
)

function Read-ExcelFile {
    param([string]$FilePath)
    
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.Xml.Linq
    
    $tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    try {
        # Excel 파일을 ZIP으로 추출
        [System.IO.Compression.ZipFile]::ExtractToDirectory($FilePath, $tempDir)
        
        # workbook.xml에서 시트 이름 가져오기
        $workbookXml = [xml](Get-Content (Join-Path $tempDir "xl\workbook.xml"))
        $sheets = $workbookXml.workbook.sheets.sheet | Select-Object -ExpandProperty name
        
        $result = @{
            File = Split-Path -Leaf $FilePath
            Sheets = @()
        }
        
        # 각 시트에서 데이터 추출
        foreach ($sheet in $sheets) {
            $sheetData = Read-ExcelSheet -TempDir $tempDir -SheetName $sheet
            $result.Sheets += $sheetData
        }
        
        return $result
    }
    finally {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Read-ExcelSheet {
    param(
        [string]$TempDir,
        [string]$SheetName
    )
    
    # relationships에서 시트 파일 찾기
    $relsXml = [xml](Get-Content (Join-Path $TempDir "xl\_rels\workbook.xml.rels"))
    $sheetRels = $relsXml.Relationships.Relationship
    
    $relId = 0
    foreach ($rel in $sheetRels) {
        if ($rel.Target -like "worksheets/*.xml") {
            $relId++
            if ($relId -eq 1) { $sheetFile = $rel.Target; break }
        }
    }
    
    # 실제로 첫 번째 시트 파일 찾기
    $sheetFiles = Get-ChildItem -Path (Join-Path $TempDir "xl\worksheets") -Filter "sheet*.xml"
    if ($sheetFiles -and $sheetFiles.Count -gt 0) {
        $sheetFile = $sheetFiles[0]
        
        $sheetXml = [xml](Get-Content $sheetFile.FullName)
        $rows = $sheetXml.worksheet.sheetData.row
        
        $data = @()
        foreach ($row in $rows) {
            $rowData = @()
            foreach ($cell in $row.c) {
                $value = $cell.v
                if ($cell.t -eq "s") {
                    # 공유 문자열 참조
                    $stringIndex = [int]$value
                    # 나중에 처리
                }
                $rowData += $value
            }
            $data += @($rowData)
        }
        
        return @{
            Name = $SheetName
            RowCount = $rows.Count
            Data = $data
        }
    }
    
    return $null
}

# 테스트
$excelFile = "C:\Users\tiod0\.copilot\repos\copilot-worktrees\battle-school-lunch-workshop\tiod0611-fluffy-winner\data\학교기본정보_오픈API명세서.xlsx"

Write-Host "Analyzing Excel file: $excelFile"
$result = Read-ExcelFile -FilePath $excelFile

Write-Host "File: $($result.File)"
foreach ($sheet in $result.Sheets) {
    Write-Host "Sheet: $($sheet.Name) - Rows: $($sheet.RowCount)"
}
