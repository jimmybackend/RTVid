# RTVid v0 prototype files

Archivos incluidos:
- `rtvid_proto.py` -> prototipo funcional en Python
- `rtvid.h` -> interfaz inicial para port a C
- `rtvid_lib.rs` -> base inicial para port a Rust

## Dependencias del prototipo Python

```bash
pip install numpy pillow
```

## Codificar

```bash
python rtvid_proto.py encode \
  --input-dir ./frames_in \
  --output ./demo.rtv \
  --fps 25 \
  --qstep 18 \
  --keyint 10 \
  --search-range 4
```

## Decodificar

```bash
python rtvid_proto.py decode \
  --input ./demo.rtv \
  --output-dir ./frames_out
```

## Notas honestas

- El bitstream es propio y byte-aligned con varints.
- La v0 usa YCbCr 4:2:0 de 8 bits.
- Los frames P aplican inter-frame solo en luma Y.
- Cb y Cr van intra en todos los frames para mantener simple la primera implementación.
- La transformada es DCT 8x8 en float; en C/Rust conviene migrar a versión entera o fixed-point.
