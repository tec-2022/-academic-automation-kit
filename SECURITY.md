# Security Policy

Academic Automation Kit puede procesar datos académicos y modificar entornos de laboratorio. La seguridad es parte del diseño.

## Reglas

- No almacenar credenciales en el repositorio.
- No incluir nombres, matrículas, correos o calificaciones reales en ejemplos.
- Crear copias de seguridad antes de modificar configuración persistente.
- Usar mínimos privilegios.
- No abrir puertos a Internet por defecto.
- Preferir `LocalSubnet` para reglas de firewall de prácticas.
- No enviar datos estudiantiles a servicios de IA sin consentimiento y configuración explícita.
- No permitir que un modelo de IA ejecute comandos arbitrarios con privilegios.
- Incluir validación de entradas y manejo de errores.

## Reporte de vulnerabilidades

No publiques secretos ni información sensible en issues públicos. Describe el problema sin datos reales y proporciona pasos mínimos para reproducirlo.
