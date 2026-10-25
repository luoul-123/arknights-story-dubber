$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType = WindowsRuntime]
$awaiter = [WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'GetAwaiter' -and $_.IsGenericMethod -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await($operation, $resultType) { return $awaiter.MakeGenericMethod($resultType).Invoke($null, @($operation)).GetResult() }
$ocr = $null
$synth = $null
[Console]::WriteLine('{"ready":true}')
while ($null -ne ($raw = [Console]::ReadLine())) {
    try {
        $request = $raw | ConvertFrom-Json
        if ($request.op -eq 'quit') { break }
        if ($request.op -eq 'voices') {
            $voices = @([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.Language -like 'zh*' } | ForEach-Object { @{id=$_.Id; name=$_.DisplayName} })
            $answer = @{voices=$voices}
        } elseif ($request.op -eq 'ocr') {
            if ($null -eq $ocr) {
                $language = New-Object Windows.Globalization.Language('zh-Hans-CN')
                $ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
                if ($null -eq $ocr) { $ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
                if ($null -eq $ocr) { throw 'Windows Chinese OCR is unavailable.' }
            }
            $inputFile = [IO.File]::OpenRead($request.path)
            $stream = [IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($inputFile)
            try {
                $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
                $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
                try {
                    $result = Await ($ocr.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
                    $lines = @($result.Lines | ForEach-Object {
                        $words = @($_.Words)
                        $x = ($words | ForEach-Object {$_.BoundingRect.X} | Measure-Object -Minimum).Minimum
                        $y = ($words | ForEach-Object {$_.BoundingRect.Y} | Measure-Object -Minimum).Minimum
                        $right = ($words | ForEach-Object {$_.BoundingRect.X+$_.BoundingRect.Width} | Measure-Object -Maximum).Maximum
                        $bottom = ($words | ForEach-Object {$_.BoundingRect.Y+$_.BoundingRect.Height} | Measure-Object -Maximum).Maximum
                        @{text=$_.Text; x=$x; y=$y; width=($right-$x); height=($bottom-$y); confidence=1.0}
                    })
                    $answer = @{lines=$lines}
                } finally { $bitmap.Dispose() }
            } finally { $stream.Dispose(); $inputFile.Dispose() }
        } elseif ($request.op -eq 'tts') {
            if ($null -eq $synth) { $synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer }
            if ($request.voice) {
                $voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object {$_.Id -eq $request.voice} | Select-Object -First 1
                if ($null -ne $voice) { $synth.Voice = $voice }
            }
            $speech = Await ($synth.SynthesizeTextToStreamAsync($request.text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
            try {
                $read = [IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($speech)
                $output = [IO.File]::Create($request.path)
                try { $read.CopyTo($output) } finally { $output.Dispose(); $read.Dispose() }
            } finally { $speech.Dispose() }
            $answer = @{path=$request.path}
        } else { throw 'Unknown operation' }
        [Console]::WriteLine(($answer | ConvertTo-Json -Depth 5 -Compress))
    } catch { [Console]::WriteLine((@{error=$_.Exception.Message} | ConvertTo-Json -Compress)) }
}
if ($null -ne $synth) { $synth.Dispose() }
