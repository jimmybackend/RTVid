# RTVid

RTVid es el códec de video nativo de **RT Stack**, el ecosistema de transmisión resiliente de **Rethra Communications**. Su propósito no es reemplazar códecs web de propósito general, sino ofrecer una base controlable, auditable y extensible para codificación, transporte interno y reconstrucción de video dentro de infraestructura RT.

## Objetivos del proyecto

- Definir un **bitstream propio** y estable.
- Tener una implementación de referencia **entendible** antes de perseguir máxima compresión.
- Mantener separado el **núcleo del códec** de los **adaptadores externos**.
- Facilitar un ciclo de trabajo claro:
  1. ingestión externa
  2. conversión a formato RTVid
  3. transporte/procesamiento interno en RT Stack
  4. decodificación o exportación hacia fuera

## Estado actual

Este repositorio contiene una **base inicial para GitHub** orientada a que herramientas como Codex continúen el desarrollo:

- documentación técnica extensa
- especificación v0 del bitstream
- arquitectura del encoder/decoder/parser
- prototipo funcional en Python
- interfaz inicial para port a C
- esqueleto inicial para port a Rust
- estructura de herramientas, tests y adaptadores

## Perfil v0 propuesto

- **Color**: YCbCr 4:2:0, 8 bits
- **Resoluciones objetivo**: 640x360 y 1280x720
- **Frame rate**: 24/25/30 fps
- **Tipos de frame**: I y P
- **Predicción**:
  - intra: DC / vertical / horizontal
  - inter: búsqueda simple entera en luma
- **Bloque base**: 8x8
- **Transformada**: DCT 8x8
- **Cuantización**: escalar uniforme
- **Entropía**: zigzag + RLE + varints
- **Objetivo**: baja complejidad, bitstream claro y evolución ordenada

## Filosofía de diseño

RTVid se diseña como un códec para una **infraestructura controlada**. Eso permite tomar decisiones deliberadas:

- compatibilidad externa solo en los bordes
- formato interno único
- decoder determinista
- bitstream legible y validable
- camino claro desde referencia Python hacia C y Rust

## Estructura del repositorio

```text
rtvid/
├── README.md
├── LICENSE
├── ROADMAP.md
├── CONTRIBUTING.md
├── SPEC.md
├── docs/
├── reference/python/
├── c/
├── rust/
├── tools/
├── samples/
├── tests/
└── adapters/
```

## Archivos importantes

- `SPEC.md`: punto de entrada a la especificación.
- `docs/bitstream-v0.md`: sintaxis del contenedor y de los frames.
- `docs/architecture.md`: módulos, flujo de datos y responsabilidades.
- `docs/math-foundation.md`: base matemática del códec.
- `docs/rt-stack-integration.md`: integración con el ecosistema RT.
- `reference/python/rtvid_proto.py`: prototipo funcional v0.
- `c/include/rtvid.h`: API base propuesta en C.
- `rust/rtvid-core/src/lib.rs`: inicio del core en Rust.

## Cómo usar el prototipo Python

### Dependencias

```bash
pip install numpy pillow
```

### Codificar

```bash
python reference/python/rtvid_proto.py encode \
  --input-dir ./samples/in \
  --output ./samples/bitstreams/demo.rtv \
  --fps 25 \
  --qstep 18 \
  --keyint 10 \
  --search-range 4
```

### Decodificar

```bash
python reference/python/rtvid_proto.py decode \
  --input ./samples/bitstreams/demo.rtv \
  --output-dir ./samples/out
```

## Alcance realista de esta base

Este bootstrap no pretende cerrar la implementación completa del códec en C o Rust. Su objetivo es dejar:

- el **alcance congelado**
- el **bitstream descrito**
- los **módulos identificados**
- el **prototipo disponible**
- la **documentación lista para GitHub**
- una base ideal para que Codex complete piezas faltantes de forma consistente

## Próximos pasos

1. cerrar parser y decoder de conformidad
2. crear vectores de prueba pequeños
3. generar golden bitstreams
4. portar decoder a C
5. portar parser + decoder a Rust
6. integrar envelope RT y adaptadores de borde

## Licencia

Se incluye `LICENSE` con licencia MIT para facilitar adopción temprana. Si Rethra Communications requiere otra estrategia de licenciamiento, puede reemplazarse antes de publicar.
