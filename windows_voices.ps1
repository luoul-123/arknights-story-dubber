param([Parameter(Mandatory = $true)][string]$OutputPath)

$ErrorActionPreference = 'Stop'
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Foundation, ContentType = WindowsRuntime]
$voices = @([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices |
    Where-Object { $_.Language -like 'zh*' } |
    ForEach-Object { @{ name = $_.DisplayName; id = $_.Id; language = $_.Language } })
@{ voices = $voices } | ConvertTo-Json -Depth 4 -Compress |
    Set-Content -LiteralPath $OutputPath -Encoding UTF8
