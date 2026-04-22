# Tests

## Objetivo

Cubrir:
- parser
- roundtrip básico
- conformidad de bitstream
- padding
- vectores de movimiento
- reproducibilidad

## Tipos de test

- unitarios: funciones pequeñas
- integración: encode -> decode
- golden: comparación con bitstreams y frames esperados

## Nota
La v0 debe priorizar correctitud sobre rendimiento.
