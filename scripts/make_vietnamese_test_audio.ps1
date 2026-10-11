# Generate synthetic Vietnamese fixtures using the installed Windows voice.
# The stories are fictional test inputs, not recordings of the user's experience.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$fixtureDir = Join-Path $repoRoot 'tests/fixtures'
$wavDir = Join-Path $repoRoot 'artifacts/vietnamese-fixtures'
[void][IO.Directory]::CreateDirectory($wavDir)
$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Install the project virtual environment first.' }
$ffmpeg = & $python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'
if ($LASTEXITCODE -ne 0) { throw 'Cannot locate the bundled FFmpeg.' }

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$synthType = [Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]
$streamType = [Windows.Media.SpeechSynthesis.SpeechSynthesisStream,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]
$voiceInfo = $synthType::AllVoices | Where-Object { $_.Language -eq 'vi-VN' } | Select-Object -First 1
if ($null -eq $voiceInfo) { throw 'Install the Vietnamese Windows speech voice first.' }
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
$synth = $null
try {
    $synth = [Activator]::CreateInstance($synthType)
    $synth.Voice = $voiceInfo
    foreach ($name in @('answer_vi_01', 'answer_vi_02', 'answer_vi_03')) {
        $text = Get-Content -LiteralPath (Join-Path $fixtureDir ($name + '.txt')) -Raw -Encoding UTF8
        $wavPath = Join-Path $wavDir ($name + '.wav')
        $webmPath = Join-Path $fixtureDir ($name + '.webm')
        $speechStream = $null
        $readStream = $null
        $fileStream = $null
        try {
            $operation = $synth.SynthesizeTextToStreamAsync($text)
            $task = $asTask.MakeGenericMethod($streamType).Invoke($null, @($operation))
            $task.Wait()
            $speechStream = $task.Result
            $readStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($speechStream)
            $fileStream = [IO.File]::Create($wavPath)
            $readStream.CopyTo($fileStream)
        } finally {
            if ($null -ne $fileStream) { $fileStream.Dispose() }
            if ($null -ne $readStream) { $readStream.Dispose() }
            if ($null -ne $speechStream) { $speechStream.Dispose() }
        }
        & $ffmpeg -nostdin -hide_banner -loglevel error -y -i $wavPath -vn -ac 1 -ar 48000 -c:a libopus -b:a 32k $webmPath
        if ($LASTEXITCODE -ne 0) { throw "Cannot encode $name as WebM." }
        Write-Output $webmPath
    }
} finally {
    if ($null -ne $synth) { $synth.Dispose() }
}
