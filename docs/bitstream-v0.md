# Bitstream RTVid v0

## 1. Objetivo

Definir una sintaxis binaria mínima, clara y portable para un elementary stream `.rtv`.

## 2. Endianness

Todos los enteros fijos en v0 se codifican en **little-endian**.

## 3. File Header

```text
magic[4]        = "RTV0"
u8  version
u16 width
u16 height
u16 fps_num
u16 fps_den
u16 block_size
u16 keyint
u16 frame_count
u8  colorspace      // 1 = YCbCr420
u8  qstep
u8  search_range
u8  reserved
```

### Campos
- `magic`: identifica el formato.
- `version`: versión del bitstream.
- `width`, `height`: dimensiones visibles originales.
- `fps_num`, `fps_den`: fracción del frame rate.
- `block_size`: en v0 debe ser 8.
- `keyint`: distancia entre I-frames planificados.
- `frame_count`: cantidad de frames en el archivo.
- `colorspace`: identificador del formato de color interno.
- `qstep`: cuantización base.
- `search_range`: rango de búsqueda entero para motion estimation.
- `reserved`: para futuro uso; en v0 debe escribirse a 0.

## 4. Frame Header

```text
u8  frame_type      // 0 = I, 1 = P
u32 payload_size
payload[payload_size]
```

### Reglas
- el parser debe validar que `payload_size` no exceda el remanente del buffer
- `frame_type` desconocido invalida el frame en v0

## 5. Organización del payload

Cada frame se serializa en el siguiente orden:

1. plano Y
2. plano Cb
3. plano Cr

Cada plano se recorre en bloques 8x8 en raster order.

## 6. Sintaxis por bloque

## 6.1 I-frame

```text
u8 intra_mode       // 0=DC, 1=vertical, 2=horizontal
coeff_stream
```

## 6.2 P-frame en Y

```text
u8 use_inter
if use_inter == 1:
    svarint mvx
    svarint mvy
else:
    u8 intra_mode
coeff_stream
```

## 6.3 P-frame en Cb / Cr para la referencia v0

```text
u8 intra_mode
coeff_stream
```

## 7. `coeff_stream`

La secuencia de coeficientes cuantizados sigue este flujo lógico:

1. tomar bloque 8x8 transformado y cuantizado
2. aplicar escaneo zigzag
3. determinar último coeficiente no cero
4. escribir `last_nonzero_plus_1`
5. escribir pares `(run_zeros, coeff)` hasta agotar coeficientes no nulos

## 8. Varints

### uvarint
Entero sin signo de longitud variable.

### svarint
Entero con signo usando zigzag signed mapping o equivalente documentado por implementación.

**Requisito:** todas las implementaciones deben compartir exactamente la misma convención.

## 9. Padding

Las dimensiones visibles pueden no ser múltiplos de 8. En ese caso:

- se aplica padding por repetición de borde
- el padding existe solo a nivel interno de codificación
- al exportar, la imagen visible final se recorta a `width x height`

## 10. Conformidad mínima

Un decoder v0 conforme debe:

- validar `magic`
- validar `version`
- validar `block_size`
- reconstruir planos con el mismo padding que la referencia
- respetar orden de planos y bloques
- interpretar correctamente `use_inter`, `mvx`, `mvy` e `intra_mode`

## 11. Extensiones futuras reservadas

Sin ser parte de la v0, pueden añadirse más adelante:
- flags por secuencia
- slices
- más modos intra
- chroma inter
- loop filter
- matrices de cuantización
- perfiles o niveles

## 12. Recomendación operativa

Mantener una colección de bitstreams golden pequeños y bien descritos:
- 1 I-frame
- 1 I + 1 P
- padding no múltiplo de 8
- movimiento simple
- bloques totalmente cero
- bloques de alta energía
