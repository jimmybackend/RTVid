# ADR 0003: v0 con I/P y P-frame simple

## Estado
Aceptado

## Contexto
Un códec de video real requiere al menos dependencia temporal básica, pero sin explotar complejidad demasiado pronto.

## Decisión
La v0 soportará:
- I-frames
- P-frames simples
- referencia única al frame previo reconstruido

## Razones
- intra-only no representa bien video temporal
- P simple permite validar referencia, motion vectors y drift
- evita la complejidad de B-frames y referencias múltiples

## Consecuencias
- eficiencia temporal modesta
- implementación razonable en Python
- muy buen punto de partida para ports a C y Rust
