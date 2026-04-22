# Base matemática de RTVid v0

## 1. Frame como señal discreta

Un frame puede modelarse como una función discreta:

F_t(x, y, c)

donde:
- `t` es el tiempo
- `x, y` son coordenadas espaciales
- `c` es el canal

En la práctica, trabajamos con matrices de enteros de 8 bits.

## 2. Representación por planos

RTVid v0 utiliza YCbCr 4:2:0.

- `Y`: luminancia
- `Cb`, `Cr`: crominancia

La razón es práctica: la percepción humana es más sensible a errores en luminancia que en crominancia.

## 3. Conversión de color

Una aproximación típica:

- `Y  = 0.299R + 0.587G + 0.114B`
- `Cb = -0.168736R - 0.331264G + 0.5B + 128`
- `Cr = 0.5R - 0.418688G - 0.081312B + 128`

Luego `Cb` y `Cr` se submuestrean a 4:2:0.

## 4. Partición en bloques

Cada plano se divide en bloques 8x8. Esa decisión permite:

- localidad espacial
- predicción simple
- transformada estándar
- complejidad controlada

## 5. Predicción intra

Sea `B` un bloque original y `P` un predictor basado en vecinos reconstruidos.

El residuo es:

`E = B - P`

Si el predictor es bueno, `E` tiene menor energía y es más fácil de comprimir.

### Modos v0
- DC: promedio de vecinos
- Vertical: copia de borde superior
- Horizontal: copia de borde izquierdo

## 6. Predicción inter

En un P-frame, el bloque predictor proviene de una referencia previa:

`P(x, y) = R(x + vx, y + vy)`

donde:
- `R` es el frame de referencia reconstruido
- `(vx, vy)` es el vector de movimiento

## 7. Motion estimation

La búsqueda de movimiento intenta minimizar una métrica como SAD:

`SAD(vx, vy) = sum(|B - R_shifted(vx, vy)|)`

En v0 se propone:
- búsqueda exhaustiva local
- entero-pel
- rango pequeño

## 8. Motion compensation

Una vez elegido el mejor vector:
- se extrae el bloque predictor desde la referencia
- no hay interpolación fraccional en v0

## 9. Transformada

El residuo espacial se transforma a un dominio de frecuencia con DCT 8x8.

Objetivo:
- concentrar energía
- producir más ceros tras cuantización
- facilitar entropía simple

## 10. Cuantización

Cada coeficiente transformado `C[i,j]` se cuantiza mediante un paso `qstep`:

`Q[i,j] = round(C[i,j] / qstep)`

Reconstrucción aproximada:

`C'[i,j] = Q[i,j] * qstep`

Esta es la etapa con pérdida principal.

## 11. Escaneo zigzag

El recorrido zigzag ordena primero bajas frecuencias y luego altas frecuencias. Eso tiende a agrupar coeficientes no nulos al inicio y ceros al final.

## 12. Entropía

La v0 usa:
- zigzag
- rachas de ceros
- varints

No es la máxima eficiencia posible, pero sí una muy buena relación entre simplicidad y utilidad para una referencia inicial.

## 13. Reconstrucción

El decoder realiza:

1. lectura de coeficientes cuantizados
2. dequant
3. IDCT
4. suma con predictor
5. saturación a rango `[0,255]`

El encoder debe seguir esa misma reconstrucción internamente para evitar drift temporal.

## 14. Riesgo numérico

Cuando se porte a C o Rust, hay que definir con exactitud:
- redondeos
- saturación
- orden de operaciones
- fixed-point o float

Si no, dos implementaciones pueden divergir en bloques reconstruidos.
