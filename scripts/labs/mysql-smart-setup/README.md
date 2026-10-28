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
8. Configura `FEDERATED`, `InnoDB` y TCP en **127.0.0.1 por defecto**.
9. Solo con `-AllowLan` crea un usuario remoto y habilita una regla Windows Firewall para `LocalSubnet`.
10. Protege primero la cuenta root con acceso local y después habilita LAN, cuando se solicita.
11. Guarda estado sin contraseñas.

## Ejecución

Abre PowerShell como administrador y ejecuta:

```powershell
.\mysql-smart-setup.ps1
```

También puedes fijar un puerto si sabes que está libre:

```powershell
.\mysql-smart-setup.ps1 -Port 3308 -Database laboratorio
```

Si realmente necesitas conexiones desde otros equipos de **tu red local**:

```powershell
.\mysql-smart-setup.ps1 -Port 3308 -Database laboratorio -RemoteUser estudiante -AllowLan
```

## Seguridad

- No modifica `C:\xampp\mysql`.
- No reutiliza un directorio de datos desconocido.
- No guarda contraseñas.
- No otorga permisos globales al usuario remoto.
- No expone la instancia a la red por defecto (`bind-address=127.0.0.1`).
- `-AllowLan` es una decisión explícita: abre el puerto solo a `LocalSubnet`, pero exige una contraseña robusta y una red local de confianza.
- Si el servicio ya existía, se solicita su contraseña root **actual**, no una contraseña nueva.
- `FEDERATED` y las transacciones son cosas distintas: `FEDERATED` enlaza tablas remotas, mientras que `InnoDB` mantiene soporte transaccional para tablas locales.

## IA

La integración de IA del proyecto debe mantenerse como capa de diagnóstico opcional. El script base no envía datos a servicios externos ni ejecuta comandos generados por un modelo.
