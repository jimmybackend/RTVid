# ROADMAP

## Objetivo general

Construir un códec de video interno, con bitstream propio, orientado a RT Stack, comenzando por una referencia simple y portable antes de optimizar rendimiento o eficiencia de compresión.

## Fase 0 — Congelación de alcance y especificación

**Meta:** cerrar decisiones que no deben moverse mientras se implementa la v0.

### Entregables
- perfil `rtv0-main`
- resolución objetivo y frame rates soportados
- bitstream v0 documentado
- decisiones ADR iniciales
- estructura de repositorio estable

### Criterio de salida
- `SPEC.md` y `docs/bitstream-v0.md` revisados
- parser puede validar cabeceras sin ambigüedades

---

## Fase 1 — Referencia intra-only

**Meta:** construir la primera ruta completa end-to-end con I-frames.

### Entregables
- parser base
- DCT/IDCT 8x8
- cuantización
- zigzag + RLE + varints
- predicción intra DC/vertical/horizontal
- roundtrip estable con secuencias pequeñas

### Criterio de salida
- encoder y decoder Python reproducen secuencias simples
- tests golden de I-frame pasan

---

## Fase 2 — P-frames simples

**Meta:** convertir RTVid en un códec de video real, no solo una compresión de imágenes.

### Entregables
- referencia al frame reconstruido previo
- motion estimation entero-pel
- motion compensation simple
- señalización de P-frame para luma
- reconstrucción libre de drift

### Criterio de salida
- roundtrip sobre secuencias con movimiento moderado
- decoder reproduce exactamente las salidas de referencia

---

## Fase 3 — Tooling y conformidad

**Meta:** facilitar inspección y depuración del bitstream.

### Entregables
- `rtvid-info`
- `rtvid-dump`
- `rtvid-verify`
- vectores de prueba
- bitstreams golden
- validadores de estructura

### Criterio de salida
- un tercero puede inspeccionar un `.rtv` sin leer el código

---

## Fase 4 — Port a C

**Meta:** disponer de una implementación de mayor rendimiento y más cercana a despliegue embebido o integración nativa.

### Entregables
- parser C
- decoder C
- fixed-point DCT/IDCT
- CLI mínima
- benchmark

### Criterio de salida
- decoder C pasa tests de conformidad contra golden vectors

---

## Fase 5 — Port a Rust

**Meta:** disponer de un core seguro para parseo, validación y librería reusable.

### Entregables
- bitstream parser en Rust
- decoder base
- crate reutilizable
- CLI en Rust
- FFI opcional

### Criterio de salida
- decoder Rust lee los mismos bitstreams que Python y C

---

## Fase 6 — Integración con RT Stack

**Meta:** insertar RTVid en el flujo real del ecosistema.

### Entregables
- envelope RT
- timestamps RT
- prioridad, sequence id y grupos FEC
- adaptadores de ingestión y exportación
- pruebas de resiliencia

### Criterio de salida
- secuencias RTVid circulan por RT Stack con trazabilidad end-to-end

---

## Fase 7 — Optimización y perfiles futuros

**Posibles líneas**
- subpel
- loop filter
- chroma inter
- slices
- referencias múltiples
- profiles low-latency / archive / monitor
- 10-bit
- rate control

## Prioridad recomendada

1. Correctitud
2. Estabilidad del bitstream
3. Tests
4. Portabilidad
5. Rendimiento
6. Eficiencia de compresión
