param(
    [Parameter(Mandatory = $true)][string]$Text,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [string]$VoiceId = '',
    [double]$Rate = 1.0
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType = WindowsRuntime]
$null = [WindowsRuntimeSystemExtensions]

$awaiter = [WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'GetAwaiter' -and $_.IsGenericMethod -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } |
    Select-Object -First 1

function Wait-WinRt($operation, $resultType) {
    return $awaiter.MakeGenericMethod($resultType).Invoke($null, @($operation)).GetResult()
}

$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
try {
    if ($VoiceId) {
        $voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices |
            Where-Object { $_.Id -eq $VoiceId } |
            Select-Object -First 1
        if ($null -eq $voice) { throw "Voice not found: $VoiceId" }
        $synth.Voice = $voice
    }
    $synth.Options.SpeakingRate = $Rate
    $speechStream = Wait-WinRt ($synth.SynthesizeTextToStreamAsync($Text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    try {
        $inputStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($speechStream)
        $outputStream = [System.IO.File]::Create($OutputPath)
        try { $inputStream.CopyTo($outputStream) }
        finally { $outputStream.Dispose(); $inputStream.Dispose() }
    }
    finally { $speechStream.Dispose() }
}
finally { $synth.Dispose() }
