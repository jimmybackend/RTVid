# Integración de RTVid con RT Stack

## 1. Rol dentro del ecosistema

RTVid es el **códec de video** del ecosistema RT. Su posición ideal es la de un formato nativo interno que vive entre la ingestión y la exportación.

```text
fuente externa -> adapter ingest -> RTVid / RT buffers -> transporte RT -> decoder / export adapter
```

## 2. Principio rector

La compatibilidad con formatos externos no debe condicionar el núcleo del códec. El núcleo RTVid define:
- representación interna
- bitstream
- semántica de reconstrucción
- integración con la capa RT

Los formatos externos se resuelven en adaptadores.

## 3. Separación de capas

### 3.1 Elementary stream RTVid
Define:
- cabeceras
- frames
- bloques
- predicción
- coeficientes

### 3.2 Envelope RT
Puede añadir:
- stream id
- timestamp RT
- sequence number
- priority class
- fec group
- channel id
- flags de retransmisión

### 3.3 Adaptadores
- importación desde FFmpeg u otras fuentes
- exportación a formatos estándar
- bridging hacia herramientas de terceros

## 4. Recomendaciones de integración

- no meter metadata de red directamente en el elementary stream
- mantener bitstream compacto y estable
- envolver RTVid con un encabezado RT separado cuando viaje por red
- diseñar el parser de envelope independiente del parser del códec

## 5. Beneficios operativos

- control de extremo a extremo
- mejor trazabilidad
- menor dependencia de formatos externos
- posibilidad de perfilar resiliencia, prioridad y recuperación según necesidades RT

## 6. Extensiones futuras alineadas con RT Stack

- slices para resiliencia por paquetes
- sincronización de reloj RT
- FEC por grupos de bloques o slices
- perfiles específicos por canal:
  - monitor
  - producción interna
  - archivo
  - baja latencia

## 7. Riesgos de integración

- acoplar demasiado el envelope con la sintaxis del códec
- usar metadata de red como si fuera semántica de compresión
- introducir dependencias externas dentro del core

## 8. Recomendación práctica

Publicar el repo con esta narrativa:

- RTVid = compresión y reconstrucción
- RT envelope = transporte y resiliencia
- adapters = interoperabilidad externa

Esa separación evita confusiones al crecer el proyecto.
