# Narrow Highway / Concordance — pull-snapshot backup from the Hetzner server to this drive.
# Usage:  powershell -ExecutionPolicy Bypass -File D:\NarrowHighway-Backups\backup.ps1
# Design: the tarball is STREAMED over ssh — nothing is staged on the server (its /tmp is a
# small RAM-backed tmpfs; writing snapshots there would eat the engine's memory).
# What it protects: the ledger (seals = the "re-checkable forever" promise), the CAS,
# cards.jsonl (the keeping), Bibles/Strong's/xrefs, the MCP-registry signing key, the
# 1.0 archive — everything irreplaceable under /home/nh, minus regenerable junk.

$ErrorActionPreference = "Stop"
$Root     = "D:\NarrowHighway-Backups"
$SnapDir  = Join-Path $Root "snapshots"
$LogFile  = Join-Path $Root "backup.log"
$Stamp    = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$Name     = "nh-backup-$Stamp.tar.gz"
$Local    = Join-Path $SnapDir $Name

New-Item -ItemType Directory -Force $SnapDir | Out-Null
function Log($m) { $line = "$((Get-Date).ToUniversalTime().ToString('u'))  $m"; Add-Content -Encoding utf8 $LogFile $line; Write-Host $line }

Log "=== backup start: $Name ==="

# 0. Pick a path: the tailnet first (Tailscale SSH, identity = tailnet); if Tailscale is
#    down/expired, fall back to the public IP with the dedicated key (sshd is key-only,
#    passwords and root disabled — verified 2026-07-09).
$Key = "$env:USERPROFILE\.ssh\id_ed25519_nh"
$Paths = @(
    @{ Label = "tailnet";   SshArgs = "-o ConnectTimeout=10 -o BatchMode=yes nh@nh-engine-1" },
    @{ Label = "public-ip"; SshArgs = "-o ConnectTimeout=10 -o BatchMode=yes -i `"$Key`" nh@5.78.186.55" }
)

# 1. Stream the snapshot straight to this drive (cmd /c redirection is binary-safe;
#    PowerShell's own > would corrupt the byte stream in 5.1)
# 2026-10-03: the stream is tried over EVERY reachable path in order (tailnet, then the public IP with
# the key). The 2026-09-28 run picked the tailnet, went through a DERP relay, and died mid-stream after
# 18 minutes with no second attempt (backup.log: "FAILED: ssh/tar stream (exit 1)"). /home/nh/backups
# (the box's own nightly tars, ~9.6 GB) is excluded: it is the same data as concordance-2/data, streamed
# twice, and it is what made the stream long enough to drop.
$remoteCmd = "tar czf - --exclude='.venv' --exclude='__pycache__' --exclude='.cache' --exclude='.ollama' --exclude='node_modules' --exclude='nh/backups' -C /home nh 2>/dev/null"
$ok = $false
foreach ($p in $Paths) {
    cmd /c "ssh $($p.SshArgs) true 2>nul"
    if ($LASTEXITCODE -ne 0) { Log "path $($p.Label) unreachable, trying next"; continue }
    Log "path: $($p.Label)"
    cmd /c "ssh $($p.SshArgs) ""$remoteCmd"" > ""$Local"""
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Log "stream failed over $($p.Label) (exit $LASTEXITCODE); trying the next path"
    Remove-Item -Force $Local -ErrorAction SilentlyContinue
}
if (-not $ok) { Log "FAILED: ssh/tar stream over every path"; exit 1 }
$size = [math]::Round((Get-Item $Local).Length / 1GB, 2)
if ((Get-Item $Local).Length -lt 100MB) { Log "FAILED: snapshot suspiciously small (${size}GB)"; exit 1 }

# 2. Verify the archive END TO END with local bsdtar — a truncated or corrupted stream
#    fails the full listing; this is the integrity check.
$entries = & tar.exe -tzf $Local 2>$null
if ($LASTEXITCODE -ne 0) { Log "FAILED: archive integrity (tar -tzf exit $LASTEXITCODE)"; exit 1 }
$ledger = ($entries | Select-String 'concordance-2/data/ledger/.*\.json').Count
$keyOk  = ($entries | Select-String 'mcp-publish/key\.pem').Count
$cards  = ($entries | Select-String 'concordance-2/data/cards\.jsonl$').Count
if ($ledger -lt 1 -or $keyOk -lt 1 -or $cards -lt 1) {
    Log "FAILED: contents check (ledger=$ledger key=$keyOk cards=$cards)"; exit 1
}

# 3. Record the checksum so this stored file can be re-verified any time later
$sha = (Get-FileHash -Algorithm SHA256 $Local).Hash.ToLower()
Log "verified: ${size}GB, $($entries.Count) entries, ledger_seals=$ledger, key=present, sha256=$sha"

# 4. Mirror the local card-source dir (the durable per-card JSONs, currently under OneDrive)
$CardSrc = "C:\Users\hdven\OneDrive\Documents\Claude\Projects\Lighthouse\data\cards"
if (Test-Path $CardSrc) {
    robocopy $CardSrc (Join-Path $Root "card-source-mirror") /MIR /NFL /NDL /NJH /NP | Out-Null
    if ($LASTEXITCODE -le 7) { Log "card-source mirror: OK ($((Get-ChildItem (Join-Path $Root 'card-source-mirror') -File).Count) files)" }
    else { Log "WARN: robocopy exit $LASTEXITCODE" }
}

Log "=== backup complete: $Name (${size}GB, seals=$ledger) ==="
