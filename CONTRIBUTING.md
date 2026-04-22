# CONTRIBUTING

Gracias por colaborar con RTVid.

## Alcance de las contribuciones

Se aceptan contribuciones en estas áreas:

- documentación técnica
- parser y validación de bitstream
- encoder / decoder
- tooling de inspección
- vectores de prueba
- ports a C y Rust
- integración con RT Stack

## Regla principal

No introducir cambios grandes sin preservar estas prioridades:

1. claridad del bitstream
2. compatibilidad hacia delante de la documentación
3. decoder determinista
4. separación entre núcleo del códec y compatibilidad externa

## Flujo recomendado

1. abrir issue describiendo el problema o propuesta
2. enlazar la parte de la documentación afectada
3. indicar si cambia:
   - bitstream
   - parser
   - semántica de reconstrucción
   - API pública
4. acompañar el cambio con tests

## Convenciones

### Documentación
- Markdown claro, directo y técnico
- evitar teoría suelta sin impacto de implementación
- cuando una decisión sea estructural, crear o actualizar un ADR en `docs/decisions/`

### Código
- nombres explícitos
- validaciones tempranas
- no mezclar parseo binario con reconstrucción
- reconstrucción del encoder debe seguir la misma lógica del decoder

### Commits sugeridos
- `docs: ...`
- `spec: ...`
- `parser: ...`
- `encoder: ...`
- `decoder: ...`
- `tests: ...`
- `tools: ...`

## Pull Requests

Un PR ideal incluye:

- contexto del problema
- decisión adoptada
- archivos afectados
- compatibilidad o ruptura de compatibilidad
- tests o ejemplos reproducibles

## Cambios de bitstream

Si un PR altera la sintaxis del bitstream:

- actualizar `SPEC.md`
- actualizar `docs/bitstream-v0.md`
- actualizar vectores de prueba
- documentar impacto en decoder y parser
- anotar si el cambio es compatible o rompe la v0

## No mezclar en un mismo PR

Evitar PRs que mezclen:

- rediseño del bitstream
- optimización de rendimiento
- refactor masivo
- cambios cosméticos de documentación

## Reporte de bugs

Al abrir un bug, incluir si es posible:

- archivo `.rtv`
- hash del archivo
- pasos para reproducir
- plataforma
- salida esperada
- salida real
