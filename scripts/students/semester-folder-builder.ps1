#requires -Version 5.1

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [string]$BasePath,

    [Parameter(Mandatory = $true)]
    [string[]]$Subjects,

    [string]$Semester = "Semestre",

    [switch]$IncludeResearch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-SafeName {
    param([string]$Name)
    $safe = ($Name -replace '[\\/:*?"<>|]', '_').Trim()
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "El nombre '$Name' no produce una carpeta válida."
    }
    return $safe
}

$semesterName = ConvertTo-SafeName $Semester
$semesterPath = Join-Path $BasePath $semesterName

$folders = @(
    "01_Apuntes",
    "02_Tareas",
    "03_Proyectos",
    "04_Examenes",
    "05_Recursos"
)

if ($IncludeResearch) {
    $folders += "06_Investigacion"
}

if ($PSCmdlet.ShouldProcess($semesterPath, "Crear estructura académica")) {
    New-Item -ItemType Directory -Path $semesterPath -Force | Out-Null

    foreach ($subject in $Subjects) {
        $safeSubject = ConvertTo-SafeName $subject
        $subjectPath = Join-Path $semesterPath $safeSubject
        New-Item -ItemType Directory -Path $subjectPath -Force | Out-Null

        foreach ($folder in $folders) {
            New-Item -ItemType Directory -Path (Join-Path $subjectPath $folder) -Force | Out-Null
        }
    }

    Write-Host "Estructura creada en: $semesterPath"
}
