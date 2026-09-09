param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [switch]$Force
)

$sourcePath = [System.IO.Path]::GetFullPath($InputPath)
$targetPath = [System.IO.Path]::GetFullPath($OutputPath)

if (-not [System.IO.File]::Exists($sourcePath)) {
    throw "Input file not found: $sourcePath"
}
if ($sourcePath.Equals($targetPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Input and output paths must be different."
}
if ([System.IO.File]::Exists($targetPath) -and -not $Force) {
    throw "Output already exists. Use -Force to replace it: $targetPath"
}

$targetDirectory = [System.IO.Path]::GetDirectoryName($targetPath)
if (-not [System.IO.Directory]::Exists($targetDirectory)) {
    throw "Output directory not found: $targetDirectory"
}

$key = [byte[]][char[]]'BK26'
$buffer = New-Object byte[] 4096
$keyIndex = 0
$inputStream = $null
$outputStream = $null

try {
    $inputStream = [System.IO.File]::OpenRead($sourcePath)
    $createMode = if ($Force) {
        [System.IO.FileMode]::Create
    } else {
        [System.IO.FileMode]::CreateNew
    }
    $outputStream = New-Object System.IO.FileStream(
        $targetPath,
        $createMode,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )

    while (($bytesRead = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        for ($index = 0; $index -lt $bytesRead; $index++) {
            $buffer[$index] = $buffer[$index] -bxor $key[$keyIndex]
            $keyIndex = ($keyIndex + 1) -band 3
        }
        $outputStream.Write($buffer, 0, $bytesRead)
    }
} finally {
    if ($outputStream) {
        $outputStream.Dispose()
    }
    if ($inputStream) {
        $inputStream.Dispose()
    }
}

Write-Output "Created: $targetPath"
