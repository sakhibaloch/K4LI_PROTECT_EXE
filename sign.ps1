param(
    [string]$ExePath = "K4LI_EXE_PROTECT.exe"
)

Write-Host ""
Write-Host "  [SIG]   K4LI Code Signing"
Write-Host "  ----------------------------------------"

# Step 1: Get or create cert in CurrentUser\My
$cert = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -like "*K4LI*" } |
    Select-Object -First 1

if (-not $cert) {
    Write-Host "  [INFO]  Creating K4LI Software certificate..."
    $cert = New-SelfSignedCertificate `
        -Type CodeSigning `
        -Subject "CN=K4LI Software, O=K4LI, C=US" `
        -KeyUsage DigitalSignature `
        -FriendlyName "K4LI Code Signing" `
        -CertStoreLocation Cert:\CurrentUser\My `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") `
        -NotAfter (Get-Date).AddYears(5)
    Write-Host "  [OK]    Certificate created: $($cert.Thumbprint)"
} else {
    Write-Host "  [OK]    Cert found: $($cert.Thumbprint)"
}

# Step 2: Add cert to TrustedPublisher (needed for Valid status, no admin required)
$tp = New-Object System.Security.Cryptography.X509Certificates.X509Store(
    "TrustedPublisher", "CurrentUser")
$tp.Open("ReadWrite")
if (-not ($tp.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint })) {
    $tp.Add($cert)
    Write-Host "  [OK]    Added to TrustedPublisher store"
}
$tp.Close()

# Step 3: Add cert to Root (needed so chain is valid, no admin required for CurrentUser)
$root = New-Object System.Security.Cryptography.X509Certificates.X509Store(
    "Root", "CurrentUser")
$root.Open("ReadWrite")
if (-not ($root.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint })) {
    $root.Add($cert)
    Write-Host "  [OK]    Added to Root store (Windows may prompt to confirm)"
}
$root.Close()

# Step 4: Resolve path
if (-not [System.IO.Path]::IsPathRooted($ExePath)) {
    $ExePath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) $ExePath
}
if (-not (Test-Path $ExePath)) {
    Write-Host "  [ERROR] File not found: $ExePath"
    exit 1
}

Write-Host "  [INFO]  Signing: $(Split-Path -Leaf $ExePath)"

# Step 5: Sign with timestamp
$result = Set-AuthenticodeSignature `
    -FilePath $ExePath `
    -Certificate $cert `
    -TimestampServer "http://timestamp.digicert.com" `
    -HashAlgorithm SHA256

if ($result.Status -eq "Valid") {
    Write-Host "  [OK]    Signed successfully  -  Publisher: K4LI Software"
} else {
    # Retry without timestamp (offline fallback)
    Write-Host "  [WARN]  Timestamp failed, retrying without timestamp..."
    $result = Set-AuthenticodeSignature `
        -FilePath $ExePath `
        -Certificate $cert `
        -HashAlgorithm SHA256
    if ($result.Status -eq "Valid") {
        Write-Host "  [OK]    Signed OK (no timestamp)  -  Publisher: K4LI Software"
    } else {
        Write-Host "  [WARN]  Status: $($result.Status)"
        Write-Host "  [INFO]  EXE still works, just unsigned by Windows trust chain"
    }
}

Write-Host ""
