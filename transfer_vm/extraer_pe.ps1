# Extrae el adjunto binario (base64) de un .eml SIN ejecutarlo.
# Localiza la parte MIME del adjunto (base64 + attachment/name) y decodifica su cuerpo.
# Uso (en la VM):  powershell -ExecutionPolicy Bypass -File extraer_pe.ps1 -Eml <ruta.eml> -Out <salida>
param(
  [Parameter(Mandatory = $true)][string]$Eml,
  [Parameter(Mandatory = $true)][string]$Out
)

$raw = [System.IO.File]::ReadAllText($Eml)

$m = [regex]::Match($raw, 'boundary="?([^";\r\n]+)"?', 'IgnoreCase')
if (-not $m.Success) { Write-Host "No se encontro el boundary MIME."; exit 1 }
$sep = '--' + $m.Groups[1].Value
$parts = $raw -split [regex]::Escape($sep)

$target = $null
foreach ($p in $parts) {
  if ($p -match '(?i)content-transfer-encoding:\s*base64' -and
      ($p -match '(?i)content-disposition:\s*attachment' -or $p -match '(?i)name=')) {
    $target = $p; break
  }
}
if (-not $target) { Write-Host "No se encontro una parte adjunta en base64."; exit 1 }

# El cuerpo empieza tras la primera linea en blanco (fin de cabeceras de la parte).
$sepBody = [regex]::Match($target, '\r?\n\r?\n')
$body = $target.Substring($sepBody.Index + $sepBody.Length)
$b64 = ($body -replace '[^A-Za-z0-9+/=]', '')
$b64 = $b64.TrimEnd('=')
$rem = $b64.Length % 4
if ($rem -gt 0) { $b64 = $b64 + ('=' * (4 - $rem)) }

$bytes = [Convert]::FromBase64String($b64)
[System.IO.File]::WriteAllBytes($Out, $bytes)

$mz = ($bytes.Length -ge 2 -and $bytes[0] -eq 0x4D -and $bytes[1] -eq 0x5A)
Write-Host ("Extraido a {0}  ({1} bytes).  Cabecera MZ (PE): {2}" -f $Out, $bytes.Length, $mz)
