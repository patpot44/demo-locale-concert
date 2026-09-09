# =============================================================================
# IBM Concert Secure Coder 3.0.1 - Windows Fix Patch
# =============================================================================
# Problème : l'extension ne s'installe pas correctement sur Windows car :
#   1. install-bobshell.sh : bash (Git Bash) ne reconnaît pas npm.cmd comme
#      exécutable (-x), et les chemins Windows (backslashes) cassent les
#      opérations de path bash.
#   2. managedToolchainEnv.js : spawn() Node.js ne peut pas lancer .cmd sans
#      shell:true -> "spawn EINVAL". L'extension cherche bob.exe à la place.
#   3. bobApiKeyValidation.js : le cwd du probe utilise os.tmpdir() qui
#      retourne le chemin court Windows 8.3 (ex: PATRIC~1) -> crash libuv
#      "Assertion failed: !_wcsnicmp ... fs-event.c:72".
#
# Prérequis :
#   - Git for Windows installé (C:\Program Files\Git\bin\bash.exe)
#   - IBM Concert Secure Coder extension 3.0.1 installée dans VS Code
#   - VS Code fermé avant d'exécuter ce script (ou Reload Window après)
#
# Usage :
#   PowerShell> .\ibm-concert-secure-coder-3.0.1-windows-fix.ps1
#
# Après exécution :
#   1. Rouvrir VS Code (ou Ctrl+Shift+P > Developer: Reload Window)
#   2. Dans le panneau IBM Concert Secure Coder : Retry setup
#   3. Coller la clé API Bobshell et cliquer Verify API Key
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "IBM Concert Secure Coder 3.0.1 - Windows Fix Patch" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 0. Localiser l'extension
# ---------------------------------------------------------------------------
$extDir = "c:\Users\$env:USERNAME\.vscode\extensions\ibm.concert-secure-coder-3.0.1"
if (-not (Test-Path $extDir)) {
    Write-Error "Extension non trouvée : $extDir`nVérifiez que IBM Concert Secure Coder 3.0.1 est installée dans VS Code."
}
Write-Host "[0] Extension trouvée : $extDir" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 1. Vérifier Git Bash
# ---------------------------------------------------------------------------
$gitBash = "C:\Program Files\Git\bin\bash.exe"
if (-not (Test-Path $gitBash)) {
    $gitBash = "${env:LOCALAPPDATA}\Programs\Git\bin\bash.exe"
}
if (-not (Test-Path $gitBash)) {
    Write-Error "Git Bash non trouvé. Installez Git for Windows : https://git-scm.com/download/win"
}
Write-Host "[1] Git Bash trouvé : $gitBash" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Chemins des outils manages
# ---------------------------------------------------------------------------
$toolsRoot   = "$env:USERPROFILE\.concert-protect\tools"
$nodeDir     = "$toolsRoot\node"
$npmPrefix   = "$toolsRoot\npm"
$toolsBin    = "$toolsRoot\bin"
$nodeExe     = "$nodeDir\node.exe"
$npmCmd      = "$nodeDir\npm.cmd"
$bobJs       = "$npmPrefix\node_modules\bobshell\dist\bob.js"

# ---------------------------------------------------------------------------
# PATCH 1 - install-bobshell.sh
# Accepte npm.cmd (Windows) et convertit les backslashes en slashes bash
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[PATCH 1] install-bobshell.sh - Windows npm.cmd + backslash fix" -ForegroundColor Yellow

$shFile = "$extDir\scripts\install-bobshell.sh"
$sh = [System.IO.File]::ReadAllText($shFile, [System.Text.UTF8Encoding]::new($false))

# Patch 1a : accepter npm.cmd comme exécutable valide sous bash
$old1a = @'
# Managed npm from ~/.concert-protect/tools (required when invoked by the extension).
if [[ -z "${CONCERT_MANAGED_NPM:-}" || ! -x "${CONCERT_MANAGED_NPM}" ]]; then
  echo "Managed npm is required (CONCERT_MANAGED_NPM). Install Node.js from the Concert Secure Coder dashboard first." >&2
  exit 1
fi
'@
$new1a = @'
# Managed npm from ~/.concert-protect/tools (required when invoked by the extension).
# On Windows (Git Bash), .cmd files are not marked -x; accept them if the file exists.
_npm_ok=false
if [[ -n "${CONCERT_MANAGED_NPM:-}" ]]; then
  if [[ -x "${CONCERT_MANAGED_NPM}" ]]; then
    _npm_ok=true
  elif [[ "${CONCERT_MANAGED_NPM}" == *.cmd ]] && [[ -f "${CONCERT_MANAGED_NPM}" ]]; then
    _npm_ok=true
  fi
fi
if [[ "${_npm_ok}" != "true" ]]; then
  echo "Managed npm is required (CONCERT_MANAGED_NPM). Install Node.js from the Concert Secure Coder dashboard first." >&2
  exit 1
fi
'@

# Patch 1b : convertir backslashes Windows en slashes bash pour NPM_BIN et PREFIX
$old1b = 'NPM_BIN="${CONCERT_MANAGED_NPM}"
MANAGED_NODE_BIN="${NPM_BIN%/*}/node"
CONCERT_NPM_PREFIX="${CONCERT_MANAGED_NPM_PREFIX}"'

$new1b = 'NPM_BIN="${CONCERT_MANAGED_NPM}"
# On Windows, backslashes must be converted to forward slashes for bash path operations
NPM_BIN_UNIX="${NPM_BIN//\\//}"
MANAGED_NODE_BIN="${NPM_BIN_UNIX%/*}/node"
CONCERT_NPM_PREFIX="${CONCERT_MANAGED_NPM_PREFIX//\\//}"'

# Patch 1c : accepter bob sans bin/ (Windows npm n'utilise pas de sous-dossier bin/)
$old1c = 'BOB_BIN="${CONCERT_NPM_PREFIX}/bin/bob"
if [[ -x "$BOB_BIN" ]]; then'

$new1c = 'BOB_BIN="${CONCERT_NPM_PREFIX}/bin/bob"
# On Windows, npm installs binaries directly in the prefix (no bin/ subdir); check both
if [[ ! -x "$BOB_BIN" ]] && [[ -f "${CONCERT_NPM_PREFIX}/bob" ]]; then
  BOB_BIN="${CONCERT_NPM_PREFIX}/bob"
fi
if [[ -x "$BOB_BIN" ]] || [[ -f "$BOB_BIN" ]]; then'

$applied = 0
if ($sh.Contains($old1a)) { $sh = $sh.Replace($old1a, $new1a); $applied++ }
if ($sh.Contains($old1b)) { $sh = $sh.Replace($old1b, $new1b); $applied++ }
if ($sh.Contains($old1c)) { $sh = $sh.Replace($old1c, $new1c); $applied++ }

[System.IO.File]::WriteAllText($shFile, $sh, [System.Text.UTF8Encoding]::new($false))
Write-Host "  -> $applied/3 sous-patches appliqués" -ForegroundColor Green

# ---------------------------------------------------------------------------
# PATCH 2 - managedToolchainEnv.js
# Cherche bob.exe au lieu de bob.cmd (spawn() ne peut pas lancer .cmd sans shell)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[PATCH 2] managedToolchainEnv.js - bob.exe au lieu de bob.cmd" -ForegroundColor Yellow

$jsEnv = "$extDir\out\utils\managedToolchainEnv.js"
$envContent = [System.IO.File]::ReadAllText($jsEnv, [System.Text.UTF8Encoding]::new($false))
$old2 = "const name = process.platform === 'win32' ? 'bob.cmd' : 'bob';"
$new2 = "const name = process.platform === 'win32' ? 'bob.exe' : 'bob';"
if ($envContent.Contains($old2)) {
    $envContent = $envContent.Replace($old2, $new2)
    [System.IO.File]::WriteAllText($jsEnv, $envContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  -> Patch appliqué (bob.cmd -> bob.exe)" -ForegroundColor Green
} elseif ($envContent.Contains($new2)) {
    Write-Host "  -> Déjà patché (bob.exe présent)" -ForegroundColor Cyan
} else {
    Write-Warning "  -> Pattern non trouvé dans managedToolchainEnv.js (version différente ?)"
}

# ---------------------------------------------------------------------------
# PATCH 3 - bobApiKeyValidation.js
# Utilise realpathSync.native pour résoudre le chemin court Windows 8.3
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[PATCH 3] bobApiKeyValidation.js - résolution chemin long Windows" -ForegroundColor Yellow

$jsVal = "$extDir\out\utils\bobApiKeyValidation.js"
$valContent = [System.IO.File]::ReadAllText($jsVal, [System.Text.UTF8Encoding]::new($false))
$old3 = "function resolveBobApiKeyProbeCwd() {
    const t = node_os_1.default.tmpdir();
    try { return require('fs').realpathSync(t); } catch (e) { return t; }
}"
$new3 = "function resolveBobApiKeyProbeCwd() {
    const t = node_os_1.default.tmpdir();
    try {
        // Force long path on Windows - realpathSync may not resolve 8.3 short names
        const fs = require('fs');
        const longPath = fs.realpathSync.native ? fs.realpathSync.native(t) : fs.realpathSync(t);
        return longPath;
    } catch (e) { return t; }
}"
if ($valContent.Contains($old3)) {
    $valContent = $valContent.Replace($old3, $new3)
    [System.IO.File]::WriteAllText($jsVal, $valContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  -> Patch appliqué (realpathSync.native)" -ForegroundColor Green
} elseif ($valContent.Contains("realpathSync.native")) {
    Write-Host "  -> Déjà patché (realpathSync.native présent)" -ForegroundColor Cyan
} else {
    Write-Warning "  -> Pattern non trouvé dans bobApiKeyValidation.js (version différente ?)"
}

# ---------------------------------------------------------------------------
# ETAPE 4 - Installer bobshell avec Git Bash
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[ETAPE 4] Installation de bobshell via Git Bash" -ForegroundColor Yellow

if (-not (Test-Path $nodeExe)) {
    Write-Warning "  Node.js manage non trouvé ($nodeExe). Cliquez d'abord sur 'Install Bobshell CLI' dans le dashboard."
} elseif (-not (Test-Path $npmCmd)) {
    Write-Warning "  npm.cmd non trouvé ($npmCmd). Node.js incomplet ?"
} else {
    # Créer le dossier prefix et bin/
    New-Item -ItemType Directory -Path "$npmPrefix\bin" -Force | Out-Null

    $npmUnix   = ($npmCmd   -replace '\\','/' -replace '^C:','/c')
    $prefixUnix = ($npmPrefix -replace '\\','/' -replace '^C:','/c')
    $scriptUnix = ($shFile    -replace '\\','/' -replace '^c:','/c' -replace '^C:','/c')

    $env:CONCERT_MANAGED_NPM = $npmCmd
    $env:CONCERT_MANAGED_NPM_PREFIX = $npmPrefix

    $result = & $gitBash -c "bash '$scriptUnix' --pm npm 2>&1 | tail -5"
    if ($LASTEXITCODE -eq 0 -or ($result -join "") -match "Installation Complete") {
        Write-Host "  -> bobshell installé avec succès" -ForegroundColor Green
    } else {
        Write-Warning "  -> Installation partielle. Résultat :`n$($result -join "`n")"
    }
}

# ---------------------------------------------------------------------------
# ETAPE 5 - Creer bob.exe (wrapper node + bob.js, launchable par spawn())
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[ETAPE 5] Creation de bob.exe (wrapper spawn-compatible)" -ForegroundColor Yellow

if (-not (Test-Path $nodeExe)) {
    Write-Warning "  node.exe non trouve - bob.exe sera cree apres installation de Node.js"
} elseif (-not (Test-Path $bobJs)) {
    Write-Warning "  bob.js non trouve ($bobJs) - relancer apres installation de bobshell"
} else {
    New-Item -ItemType Directory -Path $toolsBin -Force | Out-Null

    # Ecrire le source C# dans un fichier temporaire
    $csSrc = "$env:TEMP\bob_wrapper.cs"
    $csExe = "$toolsBin\bob.exe"
    @"
using System;
using System.Diagnostics;
class Bob {
    static int Main(string[] args) {
        var p = new Process();
        p.StartInfo.FileName = @"$nodeExe";
        p.StartInfo.Arguments = "\"$bobJs\"";
        foreach (var a in args) {
            p.StartInfo.Arguments += " " + (a.Contains(" ") ? "\"" + a + "\"" : a);
        }
        p.StartInfo.UseShellExecute = false;
        p.Start();
        p.WaitForExit();
        return p.ExitCode;
    }
}
"@ | Set-Content -Path $csSrc -Encoding UTF8

    # Trouver csc.exe (compilateur C# natif Windows - toujours present)
    $csc = Get-ChildItem "C:\Windows\Microsoft.NET\Framework64" -Filter "csc.exe" -Recurse -ErrorAction SilentlyContinue |
           Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $csc) {
        $csc = Get-ChildItem "C:\Windows\Microsoft.NET\Framework" -Filter "csc.exe" -Recurse -ErrorAction SilentlyContinue |
               Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
    }

    if (-not $csc) {
        Write-Warning "  csc.exe non trouve - bob.exe non cree. Verifiez que .NET Framework est installe."
    } else {
        & $csc /nologo /out:"$csExe" /target:exe "$csSrc" 2>&1 | Out-Null

        if (Test-Path $csExe) {
            # Copier bob.exe aux emplacements candidats
            foreach ($dest in @("$npmPrefix\bin\bob.exe", "$nodeDir\bin\bob.exe")) {
                New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
                Copy-Item $csExe $dest -Force
            }
            $ver = & $csExe --version 2>&1 | Select-Object -First 1
            Write-Host "  -> bob.exe cree - version : $ver" -ForegroundColor Green
        } else {
            Write-Warning "  Compilation echouee - bob.exe non cree"
        }
        Remove-Item $csSrc -Force -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# ETAPE 6 - Corriger les variables TEMP/TMP (chemin long)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[ETAPE 6] Correction variables TEMP/TMP (chemin long Windows)" -ForegroundColor Yellow

$longTemp = [System.IO.Path]::GetFullPath($env:TEMP)
[System.Environment]::SetEnvironmentVariable("TEMP", $longTemp, "User")
[System.Environment]::SetEnvironmentVariable("TMP",  $longTemp, "User")
Write-Host "  -> TEMP = $longTemp" -ForegroundColor Green
Write-Host "  -> TMP  = $longTemp" -ForegroundColor Green

# ---------------------------------------------------------------------------
# ETAPE 7 - Installer les scanners CLI (Trivy, Gitleaks, Snyk)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[ETAPE 7] Installation des scanners CLI (Trivy, Gitleaks, Snyk)" -ForegroundColor Yellow

$cacheDir = "$toolsRoot\cache"
New-Item -ItemType Directory -Path $toolsBin, $cacheDir -Force | Out-Null

$scanners = @(
    @{
        Name    = "trivy.exe"
        Version = "0.71.2"
        Url     = "https://github.com/aquasecurity/trivy/releases/download/v0.71.2/trivy_0.71.2_windows-64bit.zip"
        IsZip   = $true
        Entry   = "trivy.exe"
        ZipName = "trivy.zip"
    },
    @{
        Name    = "gitleaks.exe"
        Version = "8.30.1"
        Url     = "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_windows_x64.zip"
        IsZip   = $true
        Entry   = "gitleaks.exe"
        ZipName = "gitleaks.zip"
    },
    @{
        Name    = "snyk.exe"
        Version = "latest"
        Url     = "https://github.com/snyk/cli/releases/download/v1.1297.1/snyk-win.exe"
        IsZip   = $false
        Entry   = $null
        ZipName = $null
    }
)

foreach ($s in $scanners) {
    $dest = "$toolsBin\$($s.Name)"
    if (Test-Path $dest) {
        Write-Host "  -> $($s.Name) deja present - skip" -ForegroundColor Cyan
        continue
    }
    Write-Host "  Telechargement de $($s.Name) $($s.Version)..." -NoNewline
    try {
        if ($s.IsZip) {
            $zipPath  = "$cacheDir\$($s.ZipName)"
            $unzipDir = "$cacheDir\$($s.ZipName -replace '\.zip','')"
            Invoke-WebRequest $s.Url -OutFile $zipPath -UseBasicParsing
            Expand-Archive -Path $zipPath -DestinationPath $unzipDir -Force
            $bin_file = Get-ChildItem $unzipDir -Filter $s.Entry -Recurse | Select-Object -First 1
            Copy-Item $bin_file.FullName $dest -Force
        } else {
            Invoke-WebRequest $s.Url -OutFile $dest -UseBasicParsing
        }
        $sizeMB = [math]::Round((Get-Item $dest).Length / 1MB, 1)
        Write-Host " OK ($($sizeMB) MB)" -ForegroundColor Green
    } catch {
        Write-Warning " ECHEC - $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "  Verification des versions :"
foreach ($s in $scanners) {
    $dest = "$toolsBin\$($s.Name)"
    if (Test-Path $dest) {
        $ver = & $dest --version 2>&1 | Select-Object -First 1
        Write-Host "    $($s.Name) : $ver" -ForegroundColor Green
    } else {
        Write-Host "    $($s.Name) : MANQUANT" -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Patch termine. Actions requises :" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Dans VS Code : Ctrl+Shift+P > 'Developer: Reload Window'" -ForegroundColor White
Write-Host "  2. Ouvrir le panneau IBM Concert Secure Coder" -ForegroundColor White
Write-Host "  3. Cliquer 'Retry setup'" -ForegroundColor White
Write-Host "  4. Coller la cle API Bobshell et cliquer 'Verify API Key'" -ForegroundColor White
Write-Host ""
Write-Host "Si l'erreur persiste apres Reload Window :" -ForegroundColor Yellow
Write-Host "  -> Fermer completement VS Code et le rouvrir" -ForegroundColor Yellow
Write-Host "    (necessaire pour heriter des nouvelles variables TEMP/TMP)" -ForegroundColor Yellow
Write-Host ""
