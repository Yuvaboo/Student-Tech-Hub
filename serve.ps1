# MURUGAN IMPEX — Local Development Server
# Built-in PowerShell HTTP Server (No Node.js or Python required)
param([int]$Port = 3000)

$listener = New-Object System.Net.HttpListener
$prefix = "http://localhost:$Port/"
$listener.Prefixes.Add($prefix)

try {
    $listener.Start()
} catch {
    Write-Host "Port $Port is in use. Trying port 8080..." -ForegroundColor Yellow
    $Port = 8080
    $prefix = "http://localhost:$Port/"
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add($prefix)
    $listener.Start()
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MURUGAN IMPEX™ — Dental Import & Knowledge Platform" -ForegroundColor Green
Write-Host "  Local Dev Server Running At: $prefix" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot
if (!$root) { $root = (Get-Location).Path }

$mimeMap = @{
    ".html" = "text/html; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".png"  = "image/png"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
    ".pdf"  = "application/pdf"
}

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        try {
            $req = $context.Request
            $res = $context.Response

            $path = $req.Url.LocalPath
            if ($path -eq "/" -or $path -eq "") { $path = "/index.html" }
            $path = $path.TrimStart("/")

            $fullPath = Join-Path $root $path

            if (Test-Path $fullPath -PathType Leaf) {
                $ext = [System.IO.Path]::GetExtension($fullPath).ToLower()
                $mime = $mimeMap[$ext]
                if (!$mime) { $mime = "application/octet-stream" }

                $bytes = [System.IO.File]::ReadAllBytes($fullPath)
                $res.ContentType = $mime
                $res.ContentLength64 = $bytes.Length
                $res.StatusCode = 200

                if ($req.HttpMethod -ne "HEAD") {
                    $res.OutputStream.Write($bytes, 0, $bytes.Length)
                }
            } else {
                $res.StatusCode = 404
                $msg = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found: $path")
                $res.ContentType = "text/plain"
                $res.ContentLength64 = $msg.Length
                if ($req.HttpMethod -ne "HEAD") {
                    $res.OutputStream.Write($msg, 0, $msg.Length)
                }
            }
            $res.OutputStream.Close()
        } catch {
            # Safely handle client disconnects
            try { $context.Response.OutputStream.Close() } catch {}
        }
    }
} finally {
    $listener.Stop()
    $listener.Close()
}
