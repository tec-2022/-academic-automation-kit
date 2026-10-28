# Diseño de interfaz / Desktop UI design

## Objetivo

Academic Automation Kit es una herramienta de administración de PC para estudiantes
y personal de soporte TI. La interfaz debe responder tres preguntas en cada paso:
qué se hará, qué pasará en el equipo y cómo verificar que terminó correctamente.

Se conserva **Tkinter + ttk sin dependencias gráficas externas**. El diseño toma
principios generales de interfaces Windows, pero es una implementación propia y no
una aplicación oficial de Microsoft.

## Antes y después

| Antes | Ahora | Motivo |
|---|---|---|
| Cinco pestañas pequeñas arriba | Navegación lateral estable y atajos Ctrl+1…5 | Encontrar secciones sin perder el contexto |
| Inicio con cuatro botones idénticos «Abrir» | Tarjetas con nombres y acciones específicas | Facilitar el reconocimiento |
| Estilo nativo variable por sistema | Tokens visuales consistentes y contraste verificado | Mejorar jerarquía, legibilidad y confianza |
| Solo el identificador Winget | Nombre, identificador, versión y fuente | Evitar confundir programas |
| Instalación con barra indeterminada | Contador por paquete y barra determinada en la preparación por carrera | Saber cuánto trabajo avanzó |
| Sin control del resto de la cola | Solicitud de detener al terminar la instalación actual | Mantener control sin abortar el instalador activo |
| Botones de instalar/desinstalar siempre disponibles | Deshabilitados hasta seleccionar y durante una operación | Evitar acciones accidentales y concurrentes |
| Limpieza junto a otras acciones sin distinción | Acción de eliminación diferenciada y explicación del alcance | Comunicar el riesgo real |

## Pantallas

1. **Inicio**: resumen del equipo y cuatro caminos de trabajo identificables.
2. **Preparar mi PC**: elección de carrera → niveles → análisis → tabla de plan →
   confirmación → instalación con estado → verificación.
3. **Programas**: buscar → leer nombre e ID → seleccionar → confirmar instalar o
   desinstalar → consultar resultado.
4. **Mantenimiento**: leer alcance limitado → analizar caché propia → confirmar
   eliminación opcional → recibir resultado.
5. **Asistente**: ejemplo de solicitud → interpretación local → explicación. Ollama
   continúa siendo opcional; la interpretación no ejecuta cambios críticos.

El progreso de un paquete instalado por Winget **no se presenta como un porcentaje
falso**. La barra determinada representa *paquetes finalizados / paquetes previstos*
en la preparación por carrera. Las búsquedas y operaciones individuales emplean
progreso indeterminado.

## Tokens de diseño

La fuente de verdad para los colores y estilos es
`academic_toolkit/ui_theme.py`.

| Rol | Valor |
|---|---|
| Fondo de app | `#F3F6FA` |
| Superficie | `#FFFFFF` |
| Navegación | `#13243A` |
| Acción principal | `#175CD3` |
| Texto | `#152538` |
| Texto secundario | `#53657A` |
| Éxito | `#16794B` |
| Riesgo / eliminación | `#B42332` |
| Bordes | `#D9E3ED` |
| Tipografía | Segoe UI; respaldo provisto por Tk |

El sistema usa separaciones en múltiplos aproximados de 4 y 8 píxeles. Todas las
acciones críticas exigen una confirmación independiente de su color.

## Accesibilidad y verificación

- Las cinco secciones se alcanzan mediante botones con foco y atajos de teclado.
- Los estados de instalación se expresan **con palabras**, no solo con colores.
- La tabla permite desplazamiento vertical y horizontal.
- Los botones de instalar y desinstalar requieren selección previa.
- La cancelación de una preparación se procesa **entre programas**: no mata el
  proceso Winget activo ni promete revertir instalaciones finalizadas.
- Las pruebas sin pantalla se ejecutan con
  `python -m unittest discover -s tests -v`.
- En Windows, `python tests/gui_smoke.py` prueba la creación de la ventana, la
  navegación, los botones bloqueados y el progreso sin instalar nada.
- Antes de etiquetar un lanzamiento, se requiere inspección manual en Windows,
  incluido escalado de 125 % y pantallas pequeñas, con capturas reales.
- La CI de Windows captura las cinco páginas y guarda diagnósticos como artefacto
  descargable; Inicio y Preparar mi PC se publican en el README como evidencia
  verificable de la interfaz a 1000 × 690.

## Referencias públicas

Las referencias guían patrones generales; no se han copiado logos ni diseños:

1. [Microsoft — Windows app design basics](https://learn.microsoft.com/en-us/windows/apps/design/basics/): estructura, espaciado y jerarquía.
2. [Microsoft — Windows design guidelines](https://learn.microsoft.com/en-us/windows/apps/design/guidelines-overview): navegación, usabilidad y estados.
3. [Microsoft Fluent 2 — Design tokens](https://fluent2.microsoft.design/design-tokens): uso de tokens semánticos.
4. [Microsoft Fluent 2 — Progressbar guidance](https://fluent2.microsoft.design/components/web/react/core/progressbar/usage): progreso real versus indeterminado.
5. [Python — ttk official documentation](https://docs.python.org/3/library/tkinter.ttk.html): estilos, tablas y controles.
