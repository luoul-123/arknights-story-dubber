$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType = WindowsRuntime]
$awaiter = [WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'GetAwaiter' -and $_.IsGenericMethod -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await($operation, $resultType) { return $awaiter.MakeGenericMethod($resultType).Invoke($null, @($operation)).GetResult() }
$synth = $null
[Console]::WriteLine('{"ready":true}')
while ($null -ne ($raw = [Console]::ReadLine())) {
    try {
        $request = $raw | ConvertFrom-Json
        if ($request.op -eq 'quit') { break }
        if ($request.op -eq 'voices') {
            $voices = @([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.Language -like 'zh*' } | ForEach-Object { @{id=$_.Id; name=$_.DisplayName} })
            $answer = @{voices=$voices}
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
