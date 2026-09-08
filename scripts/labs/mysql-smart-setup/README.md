# MySQL Smart Setup

Automatización de laboratorio para Windows que prepara una instancia **MySQL Community Server** independiente sin modificar XAMPP/MariaDB existente.

## Qué hace

1. Requiere permisos de administrador.
2. Detecta listeners TCP y archivos `my.ini` conocidos de XAMPP/MySQL.
3. Reserva los puertos encontrados aunque un servidor esté apagado.
4. Elige automáticamente un puerto libre entre `3306` y `3399`.
5. Busca MySQL Community Server en `Program Files`.
6. Si no existe, intenta instalar `Oracle.MySQL` mediante `winget`.
7. Crea una instancia separada bajo `C:\ProgramData\AcademicAutomationKit\MySQL\instances\<puerto>`.
8. Configura `FEDERATED`, `InnoDB`, TCP y acceso LAN.
9. Abre Windows Firewall únicamente para `LocalSubnet`.
10. Crea una base y un usuario remoto con permisos limitados a esa base.
11. Guarda estado sin contraseñas.

## Ejecución

Abre PowerShell como administrador y ejecuta:

```powershell
.\mysql-smart-setup.ps1
```

También puedes fijar un puerto si sabes que está libre:

```powershell
.\mysql-smart-setup.ps1 -Port 3308 -Database laboratorio -RemoteUser estudiante
```

## Seguridad

- No modifica `C:\xampp\mysql`.
- No reutiliza un directorio de datos desconocido.
- No guarda contraseñas.
- No otorga permisos globales al usuario remoto.
- No abre el puerto a Internet; la regla de firewall usa `LocalSubnet`.
- `FEDERATED` y las transacciones son cosas distintas: `FEDERATED` enlaza tablas remotas, mientras que `InnoDB` mantiene soporte transaccional para tablas locales.

## IA

La integración de IA del proyecto debe mantenerse como capa de diagnóstico opcional. El script base no envía datos a servicios externos ni ejecuta comandos generados por un modelo.
