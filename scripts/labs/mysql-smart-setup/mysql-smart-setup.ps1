#requires -Version 5.1

[CmdletBinding()]
param(
    [ValidateRange(0, 65535)]
    [int]$Port = 0,

    [ValidatePattern('^[A-Za-z0-9_]{1,64}$')]
    [string]$Database = 'federated_lab',

    [ValidatePattern('^[A-Za-z0-9_]{1,32}$')]
    [string]$RemoteUser = 'remoto',

    [switch]$NoLan,
    [switch]$NoFederated
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RootDir = Join-Path $env:ProgramData 'AcademicAutomationKit\MySQL\instances'

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Administrator {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function ConvertFrom-SecureStringPlain {
    param([Parameter(Mandatory = $true)][Security.SecureString]$Secure)
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Get-MyIniPorts {
    $files = New-Object System.Collections.Generic.List[string]
    $direct = @(
        'C:\xampp\mysql\bin\my.ini',
        'C:\xampp\mysql\bin\my.cnf',
        'C:\ProgramData\MySQL'
    )

    foreach ($item in $direct) {
        if (-not (Test-Path $item)) { continue }
        $resolved = Get-Item $item
        if ($resolved.PSIsContainer) {
            foreach ($file in @(Get-ChildItem $item -Include my.ini,my.cnf -File -Recurse -ErrorAction SilentlyContinue)) {
                if (-not $files.Contains($file.FullName)) { [void]$files.Add($file.FullName) }
            }
        }
        elseif (-not $files.Contains($resolved.FullName)) {
            [void]$files.Add($resolved.FullName)
        }
    }

    foreach ($service in @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -match '(?i)(mysqld|mariadbd)\.exe' })) {
        $pathName = [string]$service.PathName
        if ($pathName -match '--defaults-file\s*=\s*"([^"]+)"') {
            $config = $matches[1]
            if ((Test-Path $config) -and -not $files.Contains($config)) { [void]$files.Add($config) }
        }
    }

    $ports = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($file in $files) {
        $section = ''
        foreach ($line in @(Get-Content -LiteralPath $file -ErrorAction SilentlyContinue)) {
            $trim = $line.Trim()
            if ($trim -match '^\[([^\]]+)\]$') { $section = $matches[1]; continue }
            if ($trim -match '^[#;]') { continue }
            if ($section -notmatch '^(mysqld|server|client|mysql)$') { continue }
            if ($trim -match '^(port|mysqlx_port)\s*=\s*(\d+)') {
                [void]$ports.Add([int]$matches[2])
            }
        }
    }
    return $ports
}

function Get-ReservedPorts {
    $ports = Get-MyIniPorts
    foreach ($listener in @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue)) {
        if ($listener.LocalPort -ge 3306 -and $listener.LocalPort -le 3399) {
            [void]$ports.Add([int]$listener.LocalPort)
        }
    }
    return $ports
}

function Get-FreePort {
    param([int]$Start = 3306, [int]$End = 3399)
    $reserved = Get-ReservedPorts
    for ($candidate = $Start; $candidate -le $End; $candidate++) {
        if (-not $reserved.Contains($candidate)) { return $candidate }
    }
    throw "No hay puertos libres entre $Start y $End."
}

function Get-MySqlBinaries {
    $candidates = New-Object System.Collections.Generic.List[object]
    $roots = @('C:\Program Files\MySQL', 'C:\Program Files (x86)\MySQL')

    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        foreach ($mysqld in @(Get-ChildItem $root -Filter mysqld.exe -File -Recurse -ErrorAction SilentlyContinue)) {
            if ($mysqld.FullName -match '(?i)(xampp|mariadb)') { continue }
            $mysql = Join-Path $mysqld.DirectoryName 'mysql.exe'
            if (-not (Test-Path $mysql)) { continue }
            [void]$candidates.Add([pscustomobject]@{
                Mysqld = $mysqld.FullName
                Mysql = $mysql
                BinDir = $mysqld.DirectoryName
                BaseDir = Split-Path $mysqld.DirectoryName -Parent
                Version = [string]$mysqld.VersionInfo.ProductVersion
            })
        }
    }

    if ($candidates.Count -eq 0) { return $null }
    return $candidates | Sort-Object Version -Descending | Select-Object -First 1
}

function Install-MySqlCommunity {
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'No se encontró winget. Instala App Installer desde Microsoft Store y vuelve a ejecutar.'
    }

    Write-Step 'Validando paquete Oracle.MySQL en winget'
    & winget.exe show --id Oracle.MySQL -e --accept-source-agreements | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'winget no encontró Oracle.MySQL.' }

    Write-Step 'Instalando MySQL Community Server mediante winget'
    & winget.exe install --id Oracle.MySQL -e --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget terminó con código $LASTEXITCODE." }
}

function New-InstanceDescriptor {
    param([int]$SelectedPort)
    $dir = Join-Path $RootDir ([string]$SelectedPort)
    return [pscustomobject]@{
        Dir = $dir
        Data = Join-Path $dir 'data'
        Logs = Join-Path $dir 'logs'
        Ini = Join-Path $dir 'my.ini'
        State = Join-Path $dir 'state.json'
        Service = "AcademicMySQL$SelectedPort"
        Firewall = "Academic Automation Kit - MySQL $SelectedPort"
    }
}

function Write-MyIni {
    param($Binary, $Instance, [int]$SelectedPort)

    New-Item -ItemType Directory -Path $Instance.Dir -Force | Out-Null
    New-Item -ItemType Directory -Path $Instance.Data -Force | Out-Null
    New-Item -ItemType Directory -Path $Instance.Logs -Force | Out-Null

    $base = $Binary.BaseDir -replace '\\', '/'
    $data = $Instance.Data -replace '\\', '/'
    $errorLog = (Join-Path $Instance.Logs 'error.log') -replace '\\', '/'

    $lines = @(
        '[mysqld]',
        "basedir=$base",
        "datadir=$data",
        "port=$SelectedPort",
        'bind-address=0.0.0.0',
        'default-storage-engine=InnoDB',
        'mysqlx=0',
        "log-error=$errorLog"
    )
    if (-not $NoFederated) { $lines += 'federated' }
    $lines += '', '[client]', "port=$SelectedPort"

    [IO.File]::WriteAllLines($Instance.Ini, $lines, (New-Object Text.UTF8Encoding($false)))
}

function Set-LanFirewall {
    param($Instance, [int]$SelectedPort)

    Get-NetFirewallRule -DisplayName $Instance.Firewall -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    if (-not $NoLan) {
        New-NetFirewallRule `
            -DisplayName $Instance.Firewall `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $SelectedPort `
            -RemoteAddress LocalSubnet `
            -Action Allow `
            -Profile Any | Out-Null
    }
}

function Wait-Port {
    param([int]$SelectedPort, [int]$Seconds = 35)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (@(Get-NetTCPConnection -LocalPort $SelectedPort -State Listen -ErrorAction SilentlyContinue).Count -gt 0) {
            return $true
        }
        Start-Sleep -Milliseconds 750
    }
    return $false
}

function Invoke-MySql {
    param(
        [string]$MysqlExe,
        [int]$SelectedPort,
        [string]$Sql,
        [string]$Password,
        [switch]$NoPassword
    )

    $old = $env:MYSQL_PWD
    try {
        if ($NoPassword) { Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue }
        else { $env:MYSQL_PWD = $Password }

        $output = & $MysqlExe --protocol=TCP -h 127.0.0.1 -P $SelectedPort -u root -N -B -e $Sql 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($output -join "`n") }
        return ($output -join "`n")
    }
    finally {
        if ($null -eq $old) { Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue }
        else { $env:MYSQL_PWD = $old }
    }
}

function Escape-SqlLiteral {
    param([string]$Value)
    return $Value.Replace("'", "''")
}

if (-not (Test-Administrator)) {
    throw 'Ejecuta PowerShell como Administrador.'
}

Write-Step 'Analizando instalaciones y puertos existentes'
$reserved = Get-ReservedPorts
if ($reserved.Count -gt 0) {
    Write-Host ('Puertos reservados detectados: ' + (($reserved | Sort-Object) -join ', '))
}
else {
    Write-Host 'No se detectaron puertos MySQL reservados entre 3306 y 3399.'
}

if ($Port -eq 0) {
    $Port = Get-FreePort
}
elseif ($reserved.Contains($Port)) {
    throw "El puerto $Port está reservado por otra configuración o proceso."
}

Write-Host "Puerto elegido: $Port" -ForegroundColor Green

$binary = Get-MySqlBinaries
if (-not $binary) {
    Install-MySqlCommunity
    Start-Sleep -Seconds 3
    $binary = Get-MySqlBinaries
}
if (-not $binary) { throw 'MySQL Community Server se instaló o detectó, pero no pude localizar mysqld.exe/mysql.exe.' }

Write-Host "MySQL detectado: $($binary.BaseDir)"
$instance = New-InstanceDescriptor -SelectedPort $Port

$alreadyOwned = Test-Path $instance.State
if ((Test-Path $instance.Data) -and -not $alreadyOwned) {
    $items = @(Get-ChildItem $instance.Data -Force -ErrorAction SilentlyContinue)
    if ($items.Count -gt 0) {
        throw "El directorio $($instance.Data) tiene datos y no pertenece a Academic Automation Kit. No se modificará."
    }
}

Write-Step 'Escribiendo configuración independiente'
Write-MyIni -Binary $binary -Instance $instance -SelectedPort $Port

$initialize = -not $alreadyOwned
if ($initialize) {
    Write-Step 'Inicializando nuevo directorio de datos'
    $initOutput = & $binary.Mysqld "--defaults-file=$($instance.Ini)" --initialize-insecure --console 2>&1
    $initOutput | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw 'Falló mysqld --initialize-insecure.' }
}

$service = Get-CimInstance Win32_Service -Filter "Name='$($instance.Service)'" -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Step "Creando servicio $($instance.Service)"
    $serviceOutput = & $binary.Mysqld --install $instance.Service "--defaults-file=$($instance.Ini)" 2>&1
    $serviceOutput | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el servicio de Windows.' }
}

Write-Step 'Configurando Firewall'
Set-LanFirewall -Instance $instance -SelectedPort $Port

Write-Step 'Iniciando MySQL'
$svc = Get-Service -Name $instance.Service -ErrorAction Stop
if ($svc.Status -eq 'Running') { Restart-Service -Name $instance.Service -Force }
else { Start-Service -Name $instance.Service }

if (-not (Wait-Port -SelectedPort $Port)) {
    throw "MySQL no empezó a escuchar en $Port. Revisa $($instance.Logs)\error.log"
}

$rootSecure = Read-Host 'Contraseña ROOT para esta instancia' -AsSecureString
$remoteSecure = Read-Host "Contraseña para $RemoteUser" -AsSecureString
$rootPassword = ConvertFrom-SecureStringPlain $rootSecure
$remotePassword = ConvertFrom-SecureStringPlain $remoteSecure
if ([string]::IsNullOrWhiteSpace($rootPassword) -or [string]::IsNullOrWhiteSpace($remotePassword)) {
    throw 'Las contraseñas no pueden quedar vacías.'
}

$rootSql = Escape-SqlLiteral $rootPassword
$remoteSql = Escape-SqlLiteral $remotePassword

if ($initialize) {
    $sql = @"
ALTER USER 'root'@'localhost' IDENTIFIED BY '$rootSql';
CREATE DATABASE IF NOT EXISTS ``$Database``;
CREATE USER IF NOT EXISTS '$RemoteUser'@'%' IDENTIFIED BY '$remoteSql';
GRANT ALL PRIVILEGES ON ``$Database``.* TO '$RemoteUser'@'%';
FLUSH PRIVILEGES;
"@
    [void](Invoke-MySql -MysqlExe $binary.Mysql -SelectedPort $Port -Sql $sql -NoPassword)
}
else {
    $sql = @"
CREATE DATABASE IF NOT EXISTS ``$Database``;
CREATE USER IF NOT EXISTS '$RemoteUser'@'%' IDENTIFIED BY '$remoteSql';
ALTER USER '$RemoteUser'@'%' IDENTIFIED BY '$remoteSql';
GRANT ALL PRIVILEGES ON ``$Database``.* TO '$RemoteUser'@'%';
FLUSH PRIVILEGES;
"@
    [void](Invoke-MySql -MysqlExe $binary.Mysql -SelectedPort $Port -Sql $sql -Password $rootPassword)
}

Write-Step 'Verificando motores'
$fed = Invoke-MySql -MysqlExe $binary.Mysql -SelectedPort $Port -Password $rootPassword -Sql "SELECT CONCAT(ENGINE,'=',SUPPORT) FROM INFORMATION_SCHEMA.ENGINES WHERE ENGINE='FEDERATED';"
$innodb = Invoke-MySql -MysqlExe $binary.Mysql -SelectedPort $Port -Password $rootPassword -Sql "SELECT CONCAT(ENGINE,'=',SUPPORT) FROM INFORMATION_SCHEMA.ENGINES WHERE ENGINE='InnoDB';"
Write-Host "FEDERATED: $fed"
Write-Host "InnoDB:    $innodb"

$state = [ordered]@{
    version = 1
    configuredAt = (Get-Date).ToString('o')
    port = $Port
    serviceName = $instance.Service
    database = $Database
    remoteUser = $RemoteUser
    baseDir = $binary.BaseDir
    lanEnabled = (-not $NoLan)
    federatedEnabled = (-not $NoFederated)
}
$state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $instance.State -Encoding UTF8

$ips = @(Get-NetIPConfiguration -ErrorAction SilentlyContinue |
    Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq 'Up' } |
    ForEach-Object { $_.IPv4Address.IPAddress } |
    Where-Object { $_ -and $_ -notlike '127.*' -and $_ -notlike '169.254.*' } |
    Select-Object -Unique)

Write-Host "`nCONFIGURACIÓN COMPLETA" -ForegroundColor Green
Write-Host "Servicio: $($instance.Service)"
Write-Host "Puerto:   $Port"
Write-Host "Base:     $Database"
Write-Host "Usuario:  $RemoteUser"
if ($ips.Count -gt 0) { Write-Host ('IP LAN:   ' + ($ips -join ', ')) }
Write-Host 'Las contraseñas no se guardaron en state.json.'
