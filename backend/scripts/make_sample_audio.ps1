# Generate a synthetic English speech sample using a local Windows voice.
# No external TTS service, API key, microphone, or personal recording is used.
param([string]$OutputPath = 'artifacts/interview_answer_en.wav')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$sampleText = Get-Content -LiteralPath (Join-Path $repoRoot 'tests/fixtures/interview_answer_en.txt') -Raw
$resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputPath))
[void][System.IO.Directory]::CreateDirectory((Split-Path $resolvedOutput -Parent))
$voice = $null
$stream = $null
try {
    $voice = New-Object -ComObject SAPI.SpVoice
    $voices = $voice.GetVoices('Language=409')
    if ($voices.Count -eq 0) { throw 'An English US Windows speech voice is required.' }
    $voice.Voice = $voices.Item(0)
    $voice.Rate = 0
    $stream = New-Object -ComObject SAPI.SpFileStream
    $stream.Format.Type = 22 # 22.05 kHz, 16-bit, mono PCM
    $stream.Open($resolvedOutput, 3, $false)
    $voice.AudioOutputStream = $stream
    [void]$voice.Speak($sampleText)
    $stream.Close()
    Write-Output $resolvedOutput
} finally {
    if ($null -ne $stream) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($stream) }
    if ($null -ne $voice) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($voice) }
}
