param(
    [Parameter(Mandatory = $true)][string]$ImagePath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType = WindowsRuntime]
$null = [WindowsRuntimeSystemExtensions]

$awaiter = [WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'GetAwaiter' -and $_.IsGenericMethod -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } |
    Select-Object -First 1

function Wait-WinRt($operation, $resultType) {
    return $awaiter.MakeGenericMethod($resultType).Invoke($null, @($operation)).GetResult()
}

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) { throw 'Windows OCR language pack is unavailable.' }
$input = [System.IO.File]::OpenRead($ImagePath)
$stream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($input)
try {
    $decoder = Wait-WinRt ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Wait-WinRt ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    try {
        $result = Wait-WinRt ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $lines = @($result.Lines | ForEach-Object {
            $words = @($_.Words)
            $first = $words | Select-Object -First 1
            @{ text = $_.Text; x = if ($first) { [double]$first.BoundingRect.X } else { 0.0 }; y = if ($first) { [double]$first.BoundingRect.Y } else { 0.0 }; height = if ($first) { [double]$first.BoundingRect.Height } else { 24.0 } }
        })
        @{ text = $result.Text; lines = $lines } |
            ConvertTo-Json -Depth 4 -Compress |
            Set-Content -LiteralPath $OutputPath -Encoding UTF8
    }
    finally { $bitmap.Dispose() }
}
finally { $stream.Dispose(); $input.Dispose() }
