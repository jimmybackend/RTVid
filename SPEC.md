# SPEC

Este documento es la entrada principal a la especificación de **RTVid v0**.

## 1. Propósito

RTVid define un formato de video interno para RT Stack. La v0 se concentra en:

- codificación híbrida simple por bloques
- bitstream propio y pequeño
- soporte de I/P frames
- reconstrucción determinista
- base clara para una evolución futura controlada

## 2. Perfil base v0

- nombre sugerido: `rtv0-main`
- color: YCbCr 4:2:0 de 8 bits
- bloque base: 8x8
- transformada: DCT 8x8
- cuantización: uniforme
- entropía: zigzag + RLE + varints
- tipos de frame: I y P
- referencia temporal: frame previo reconstruido
- motion estimation: entero-pel
- chroma en P-frame: intra en la referencia Python v0

## 3. Documentos normativos internos de este repositorio

- `docs/bitstream-v0.md`
- `docs/architecture.md`
- `docs/math-foundation.md`
- `docs/rt-stack-integration.md`
- `docs/decisions/*.md`

## 4. Lectura recomendada

1. `README.md`
2. `docs/architecture.md`
3. `docs/bitstream-v0.md`
4. `reference/python/rtvid_proto.py`

## 5. Alcance y no alcance

### Dentro del alcance v0
- definición de elementary stream `.rtv`
- implementación de referencia Python
- port plan a C y Rust
- herramientas de inspección

### Fuera del alcance v0
- B-frames
- CABAC o entropía avanzada
- subpel
- loop filter sofisticado
- HDR / 10-bit
- compatibilidad directa con contenedores externos como parte del núcleo

## 6. Requisito de correctitud

La reconstrucción interna del encoder debe ser equivalente a la del decoder. Toda futura implementación debe preservar este principio para evitar drift en P-frames.

## 7. Estado del documento

- versión: borrador técnico v0
- intención: base estable para implementación
- siguiente paso: convertir secciones clave en tests de conformidad
