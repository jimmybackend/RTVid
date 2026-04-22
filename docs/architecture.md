# Arquitectura de RTVid v0

## 1. Visión general

RTVid v0 sigue una arquitectura híbrida clásica pero deliberadamente simple:

1. conversión de color
2. particionado por bloques
3. predicción
4. residuo
5. transformada
6. cuantización
7. codificación entropía
8. reconstrucción
9. empaquetado en bitstream

La arquitectura se divide en módulos separados para mantener claridad y permitir ports limpios a C y Rust.

## 2. Módulos principales

## 2.1 Ingesta
Responsabilidad:
- leer frames externos
- normalizar dimensiones
- preparar buffers del frame

Entradas:
- imágenes o secuencias externas

Salidas:
- planos Y, Cb, Cr internos

## 2.2 Conversión de color
Responsabilidad:
- convertir RGB a YCbCr 4:2:0
- garantizar formato interno uniforme

Notas:
- cualquier compatibilidad externa se resuelve aquí o en adaptadores de borde

## 2.3 Particionador de bloques
Responsabilidad:
- aplicar padding a múltiplos del tamaño de bloque
- recorrer bloques 8x8 en orden raster

## 2.4 Predicción intra
Responsabilidad:
- producir predictor a partir de vecinos reconstruidos

Modos v0:
- DC
- vertical
- horizontal

## 2.5 Predicción inter
Responsabilidad:
- elegir predictor desde frame de referencia previo

Alcance v0:
- entero-pel
- búsqueda local simple
- luma primero

## 2.6 Transformada y cuantización
Responsabilidad:
- convertir residuo espacial a coeficientes
- reducir precisión con `qstep`

## 2.7 Entropía
Responsabilidad:
- serializar coeficientes cuantizados de forma compacta

v0:
- zigzag
- rachas de ceros
- varints

## 2.8 Parser
Responsabilidad:
- validar encabezados
- delimitar payloads
- exponer estructuras parseadas al decoder o tooling

No debe:
- mezclar lógica de parseo con reconstrucción de imagen

## 2.9 Decoder
Responsabilidad:
- reconstruir exactamente el frame desde el bitstream
- preservar referencias para P-frames

## 2.10 Tooling
Responsabilidad:
- inspección
- depuración
- validación
- generación de métricas y dumps

---

## 3. Flujo del encoder

```text
entrada externa
  -> conversión RGB->YCbCr420
  -> padding
  -> decisión I/P
  -> predicción por bloque
  -> residuo
  -> DCT
  -> cuantización
  -> entropía
  -> reconstrucción local
  -> reference frame update
  -> bitstream .rtv
```

## 4. Flujo del decoder

```text
bitstream .rtv
  -> parser
  -> frame header
  -> bloques por plano
  -> predictor
  -> entropía inversa
  -> dequant
  -> IDCT
  -> reconstrucción
  -> update reference frame
  -> salida interna o exportación
```

## 5. Responsabilidades por lenguaje

### Python
- referencia funcional
- facilidad de lectura
- baseline para tests

### C
- rendimiento
- integración nativa
- posible uso embebido

### Rust
- seguridad de memoria
- parser robusto
- librería reusable y tooling

## 6. Invariantes de arquitectura

- el parser no debe depender de detalles de UI ni exportación
- el decoder no debe asumir formatos externos
- el encoder reconstruye lo mismo que el decoder
- los frames P usan referencias reconstruidas, no originales
- el bitstream debe seguir siendo entendible y validable

## 7. Riesgos conocidos

- deriva por diferencias numéricas entre implementaciones
- ambigüedad si no se documenta padding exacto
- corrupción local propagada en GOP si P-frames dependen en cadena
- crecimiento desordenado del bitstream si se agregan features sin ADRs
