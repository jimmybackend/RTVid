
from __future__ import annotations

import argparse
import io
import math
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

MAGIC = b"RTV0"
VERSION = 1
BLOCK = 8
COLORSPACE_YCBCR420 = 1
FRAME_I = 0
FRAME_P = 1


def clamp_uint8(a: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def pad_to_multiple(arr: np.ndarray, mult_y: int, mult_x: int) -> np.ndarray:
    h, w = arr.shape
    pad_h = (mult_y - (h % mult_y)) % mult_y
    pad_w = (mult_x - (w % mult_x)) % mult_x
    if pad_h == 0 and pad_w == 0:
        return arr.copy()
    return np.pad(arr, ((0, pad_h), (0, pad_w)), mode="edge")


def rgb_to_ycbcr420(img: Image.Image) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    y = 0.2990 * r + 0.5870 * g + 0.1140 * b
    cb = -0.168736 * r - 0.331264 * g + 0.500000 * b + 128.0
    cr = 0.500000 * r - 0.418688 * g - 0.081312 * b + 128.0

    y = clamp_uint8(y)

    if cb.shape[0] % 2 == 1:
        cb = np.pad(cb, ((0, 1), (0, 0)), mode="edge")
        cr = np.pad(cr, ((0, 1), (0, 0)), mode="edge")
    if cb.shape[1] % 2 == 1:
        cb = np.pad(cb, ((0, 0), (0, 1)), mode="edge")
        cr = np.pad(cr, ((0, 0), (0, 1)), mode="edge")

    cb_ds = (cb[0::2, 0::2] + cb[1::2, 0::2] + cb[0::2, 1::2] + cb[1::2, 1::2]) / 4.0
    cr_ds = (cr[0::2, 0::2] + cr[1::2, 0::2] + cr[0::2, 1::2] + cr[1::2, 1::2]) / 4.0
    return y, clamp_uint8(cb_ds), clamp_uint8(cr_ds)


def upsample_420_plane(plane: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    up = np.repeat(np.repeat(plane, 2, axis=0), 2, axis=1)
    return up[:out_h, :out_w]


def ycbcr420_to_rgb(y: np.ndarray, cb: np.ndarray, cr: np.ndarray, out_h: int, out_w: int) -> Image.Image:
    y_f = y[:out_h, :out_w].astype(np.float32)
    cb_up = upsample_420_plane(cb, out_h, out_w).astype(np.float32) - 128.0
    cr_up = upsample_420_plane(cr, out_h, out_w).astype(np.float32) - 128.0

    r = y_f + 1.4020 * cr_up
    g = y_f - 0.344136 * cb_up - 0.714136 * cr_up
    b = y_f + 1.7720 * cb_up

    rgb = np.stack([r, g, b], axis=2)
    return Image.fromarray(clamp_uint8(rgb), mode="RGB")


def frame_to_planes(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    img = Image.open(path)
    return rgb_to_ycbcr420(img)


def list_frames(input_dir: Path) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg", ".bmp"}
    files = [p for p in sorted(input_dir.iterdir()) if p.suffix.lower() in exts]
    if not files:
        raise FileNotFoundError(f"No se encontraron imágenes en {input_dir}")
    return files


class ByteWriter:
    def __init__(self) -> None:
        self.buf = bytearray()

    def write_u8(self, value: int) -> None:
        self.buf += struct.pack("<B", value & 0xFF)

    def write_u16(self, value: int) -> None:
        self.buf += struct.pack("<H", value & 0xFFFF)

    def write_u32(self, value: int) -> None:
        self.buf += struct.pack("<I", value & 0xFFFFFFFF)

    def write_bytes(self, data: bytes) -> None:
        self.buf += data

    def write_uvarint(self, value: int) -> None:
        if value < 0:
            raise ValueError("uvarint no admite negativos")
        while True:
            b = value & 0x7F
            value >>= 7
            if value:
                self.write_u8(b | 0x80)
            else:
                self.write_u8(b)
                break

    def write_svarint(self, value: int) -> None:
        zz = (value << 1) ^ (value >> 31)
        self.write_uvarint(zz)

    def get_bytes(self) -> bytes:
        return bytes(self.buf)


class ByteReader:
    def __init__(self, data: bytes) -> None:
        self.bio = io.BytesIO(data)

    def read_u8(self) -> int:
        b = self.bio.read(1)
        if len(b) != 1:
            raise EOFError("EOF en u8")
        return struct.unpack("<B", b)[0]

    def read_u16(self) -> int:
        b = self.bio.read(2)
        if len(b) != 2:
            raise EOFError("EOF en u16")
        return struct.unpack("<H", b)[0]

    def read_u32(self) -> int:
        b = self.bio.read(4)
        if len(b) != 4:
            raise EOFError("EOF en u32")
        return struct.unpack("<I", b)[0]

    def read_bytes(self, n: int) -> bytes:
        b = self.bio.read(n)
        if len(b) != n:
            raise EOFError("EOF en bytes")
        return b

    def read_uvarint(self) -> int:
        shift = 0
        value = 0
        while True:
            b = self.read_u8()
            value |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                return value
            shift += 7
            if shift > 63:
                raise ValueError("uvarint demasiado largo")

    def read_svarint(self) -> int:
        zz = self.read_uvarint()
        return (zz >> 1) ^ -(zz & 1)

    def eof(self) -> bool:
        cur = self.bio.tell()
        b = self.bio.read(1)
        self.bio.seek(cur)
        return len(b) == 0


def dct_matrix(n: int = BLOCK) -> np.ndarray:
    m = np.zeros((n, n), dtype=np.float32)
    factor = math.pi / (2.0 * n)
    scale0 = math.sqrt(1.0 / n)
    scale = math.sqrt(2.0 / n)
    for k in range(n):
        for i in range(n):
            alpha = scale0 if k == 0 else scale
            m[k, i] = alpha * math.cos((2 * i + 1) * k * factor)
    return m


DCT8 = dct_matrix(BLOCK)
IDCT8 = DCT8.T


def fdct2(block: np.ndarray) -> np.ndarray:
    return DCT8 @ block @ DCT8.T


def idct2(coeff: np.ndarray) -> np.ndarray:
    return IDCT8 @ coeff @ IDCT8.T


ZIGZAG = [
    0, 1, 8, 16, 9, 2, 3, 10,
    17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46,
    53, 60, 61, 54, 47, 55, 62, 63,
]


def zigzag_scan(block: np.ndarray) -> List[int]:
    flat = np.asarray(block, dtype=np.int32).reshape(-1)
    return [int(flat[idx]) for idx in ZIGZAG]


def zigzag_unscan(values: List[int]) -> np.ndarray:
    flat = np.zeros(BLOCK * BLOCK, dtype=np.int32)
    for i, idx in enumerate(ZIGZAG):
        flat[idx] = values[i]
    return flat.reshape((BLOCK, BLOCK))


def write_coeffs(writer: ByteWriter, qcoeff: np.ndarray) -> None:
    zz = zigzag_scan(qcoeff)
    last = -1
    for i in range(len(zz) - 1, -1, -1):
        if zz[i] != 0:
            last = i
            break
    writer.write_uvarint(last + 1)
    if last < 0:
        return

    i = 0
    while i <= last:
        run = 0
        while i <= last and zz[i] == 0:
            run += 1
            i += 1
        if i > last:
            break
        writer.write_uvarint(run)
        writer.write_svarint(zz[i])
        i += 1


def read_coeffs(reader: ByteReader) -> np.ndarray:
    last_plus_1 = reader.read_uvarint()
    zz = [0] * (BLOCK * BLOCK)
    if last_plus_1 == 0:
        return zigzag_unscan(zz)
    i = 0
    last = last_plus_1 - 1
    while i <= last:
        run = reader.read_uvarint()
        i += run
        if i > last:
            raise ValueError("Run inválido en coeficientes")
        zz[i] = reader.read_svarint()
        i += 1
    return zigzag_unscan(zz)


@dataclass
class PlaneReconCtx:
    top_cache: np.ndarray | None
    plane: np.ndarray


def get_intra_predictor(ctx: PlaneReconCtx, x: int, y: int, mode: int) -> np.ndarray:
    plane = ctx.plane
    block = np.empty((BLOCK, BLOCK), dtype=np.float32)

    has_top = y > 0
    has_left = x > 0

    if has_top:
        top = plane[y - 1, x:x + BLOCK].astype(np.float32)
    else:
        top = None

    if has_left:
        left = plane[y:y + BLOCK, x - 1].astype(np.float32)
    else:
        left = None

    if mode == 1 and has_top:  # vertical
        block[:] = top.reshape(1, BLOCK)
        return block
    if mode == 2 and has_left:  # horizontal
        block[:] = left.reshape(BLOCK, 1)
        return block

    values = []
    if has_top:
        values.append(float(np.mean(top)))
    if has_left:
        values.append(float(np.mean(left)))
    dc = sum(values) / len(values) if values else 128.0
    block.fill(dc)
    return block


def choose_intra_mode(orig: np.ndarray, ctx: PlaneReconCtx, x: int, y: int) -> Tuple[int, np.ndarray]:
    best_mode = 0
    best_pred = None
    best_cost = None
    for mode in (0, 1, 2):
        pred = get_intra_predictor(ctx, x, y, mode)
        cost = float(np.sum(np.abs(orig.astype(np.float32) - pred)))
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_mode = mode
            best_pred = pred
    assert best_pred is not None
    return best_mode, best_pred


def full_search_mv(orig: np.ndarray, ref: np.ndarray, x: int, y: int, search_range: int) -> Tuple[int, int, np.ndarray, float]:
    h, w = ref.shape
    best_cost = None
    best_mv = (0, 0)
    best_pred = None
    for dy in range(-search_range, search_range + 1):
        ry = y + dy
        if ry < 0 or ry + BLOCK > h:
            continue
        for dx in range(-search_range, search_range + 1):
            rx = x + dx
            if rx < 0 or rx + BLOCK > w:
                continue
            cand = ref[ry:ry + BLOCK, rx:rx + BLOCK].astype(np.float32)
            cost = float(np.sum(np.abs(orig.astype(np.float32) - cand)))
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_mv = (dx, dy)
                best_pred = cand
    assert best_pred is not None and best_cost is not None
    return best_mv[0], best_mv[1], best_pred, best_cost


def quantize(coeff: np.ndarray, qstep: int) -> np.ndarray:
    return np.rint(coeff / float(qstep)).astype(np.int32)


def dequantize(qcoeff: np.ndarray, qstep: int) -> np.ndarray:
    return qcoeff.astype(np.float32) * float(qstep)


def reconstruct_block(pred: np.ndarray, qcoeff: np.ndarray, qstep: int) -> np.ndarray:
    rec_res = idct2(dequantize(qcoeff, qstep))
    rec = pred.astype(np.float32) + rec_res
    return clamp_uint8(rec)


def encode_plane_intra(plane: np.ndarray, qstep: int, writer: ByteWriter) -> np.ndarray:
    h, w = plane.shape
    recon = np.zeros((h, w), dtype=np.uint8)
    ctx = PlaneReconCtx(top_cache=None, plane=recon)
    for y in range(0, h, BLOCK):
        for x in range(0, w, BLOCK):
            orig = plane[y:y + BLOCK, x:x + BLOCK]
            mode, pred = choose_intra_mode(orig, ctx, x, y)
            residual = orig.astype(np.float32) - pred
            coeff = fdct2(residual)
            qcoeff = quantize(coeff, qstep)
            writer.write_u8(mode)
            write_coeffs(writer, qcoeff)
            rec = reconstruct_block(pred, qcoeff, qstep)
            recon[y:y + BLOCK, x:x + BLOCK] = rec
    return recon


def encode_plane_p_luma(plane: np.ndarray, ref_recon: np.ndarray, qstep: int, search_range: int, writer: ByteWriter) -> np.ndarray:
    h, w = plane.shape
    recon = np.zeros((h, w), dtype=np.uint8)
    ctx = PlaneReconCtx(top_cache=None, plane=recon)
    for y in range(0, h, BLOCK):
        for x in range(0, w, BLOCK):
            orig = plane[y:y + BLOCK, x:x + BLOCK]

            intra_mode, intra_pred = choose_intra_mode(orig, ctx, x, y)
            intra_cost = float(np.sum(np.abs(orig.astype(np.float32) - intra_pred)))

            mvx, mvy, inter_pred, inter_cost = full_search_mv(orig, ref_recon, x, y, search_range)

            use_inter = inter_cost + 4.0 < intra_cost
            writer.write_u8(1 if use_inter else 0)
            if use_inter:
                writer.write_svarint(mvx)
                writer.write_svarint(mvy)
                pred = inter_pred
            else:
                writer.write_u8(intra_mode)
                pred = intra_pred

            residual = orig.astype(np.float32) - pred
            coeff = fdct2(residual)
            qcoeff = quantize(coeff, qstep)
            write_coeffs(writer, qcoeff)
            rec = reconstruct_block(pred, qcoeff, qstep)
            recon[y:y + BLOCK, x:x + BLOCK] = rec
    return recon


def decode_plane_intra(shape: Tuple[int, int], qstep: int, reader: ByteReader) -> np.ndarray:
    h, w = shape
    recon = np.zeros((h, w), dtype=np.uint8)
    ctx = PlaneReconCtx(top_cache=None, plane=recon)
    for y in range(0, h, BLOCK):
        for x in range(0, w, BLOCK):
            mode = reader.read_u8()
            pred = get_intra_predictor(ctx, x, y, mode)
            qcoeff = read_coeffs(reader)
            rec = reconstruct_block(pred, qcoeff, qstep)
            recon[y:y + BLOCK, x:x + BLOCK] = rec
    return recon


def decode_plane_p_luma(shape: Tuple[int, int], ref_recon: np.ndarray, qstep: int, reader: ByteReader) -> np.ndarray:
    h, w = shape
    recon = np.zeros((h, w), dtype=np.uint8)
    ctx = PlaneReconCtx(top_cache=None, plane=recon)
    for y in range(0, h, BLOCK):
        for x in range(0, w, BLOCK):
            use_inter = reader.read_u8()
            if use_inter:
                mvx = reader.read_svarint()
                mvy = reader.read_svarint()
                pred = ref_recon[y + mvy:y + mvy + BLOCK, x + mvx:x + mvx + BLOCK].astype(np.float32)
            else:
                mode = reader.read_u8()
                pred = get_intra_predictor(ctx, x, y, mode)
            qcoeff = read_coeffs(reader)
            rec = reconstruct_block(pred, qcoeff, qstep)
            recon[y:y + BLOCK, x:x + BLOCK] = rec
    return recon


@dataclass
class CodecConfig:
    fps_num: int = 25
    fps_den: int = 1
    qstep: int = 18
    keyint: int = 10
    search_range: int = 4


@dataclass
class DecodedFrame:
    y: np.ndarray
    cb: np.ndarray
    cr: np.ndarray


class RTVidCodec:
    def __init__(self, config: CodecConfig) -> None:
        self.config = config

    def encode(self, input_dir: Path, output_file: Path) -> None:
        frame_paths = list_frames(input_dir)
        y0, cb0, cr0 = frame_to_planes(frame_paths[0])
        src_h, src_w = y0.shape

        y_w = pad_to_multiple(y0, BLOCK, BLOCK).shape[1]
        y_h = pad_to_multiple(y0, BLOCK, BLOCK).shape[0]
        c_w = pad_to_multiple(cb0, BLOCK, BLOCK).shape[1]
        c_h = pad_to_multiple(cb0, BLOCK, BLOCK).shape[0]

        bw = ByteWriter()
        bw.write_bytes(MAGIC)
        bw.write_u8(VERSION)
        bw.write_u16(src_w)
        bw.write_u16(src_h)
        bw.write_u16(self.config.fps_num)
        bw.write_u16(self.config.fps_den)
        bw.write_u16(BLOCK)
        bw.write_u16(self.config.keyint)
        bw.write_u16(len(frame_paths))
        bw.write_u8(COLORSPACE_YCBCR420)
        bw.write_u8(self.config.qstep)
        bw.write_u8(self.config.search_range)
        bw.write_u8(0)

        prev_y = None

        for idx, frame_path in enumerate(frame_paths):
            y, cb, cr = frame_to_planes(frame_path)
            y = pad_to_multiple(y, BLOCK, BLOCK)
            cb = pad_to_multiple(cb, BLOCK, BLOCK)
            cr = pad_to_multiple(cr, BLOCK, BLOCK)

            frame_type = FRAME_I if idx % self.config.keyint == 0 or prev_y is None else FRAME_P
            payload = ByteWriter()

            if frame_type == FRAME_I:
                recon_y = encode_plane_intra(y, self.config.qstep, payload)
            else:
                recon_y = encode_plane_p_luma(y, prev_y, self.config.qstep, self.config.search_range, payload)

            # En v0, chroma siempre intra para simplificar implementación.
            recon_cb = encode_plane_intra(cb, self.config.qstep, payload)
            recon_cr = encode_plane_intra(cr, self.config.qstep, payload)

            frame_payload = payload.get_bytes()
            bw.write_u8(frame_type)
            bw.write_u32(len(frame_payload))
            bw.write_bytes(frame_payload)

            prev_y = recon_y

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(bw.get_bytes())

    def decode(self, input_file: Path, output_dir: Path) -> None:
        data = input_file.read_bytes()
        br = ByteReader(data)

        magic = br.read_bytes(4)
        if magic != MAGIC:
            raise ValueError("Archivo RTVid inválido")
        version = br.read_u8()
        if version != VERSION:
            raise ValueError(f"Versión no soportada: {version}")

        src_w = br.read_u16()
        src_h = br.read_u16()
        fps_num = br.read_u16()
        fps_den = br.read_u16()
        block = br.read_u16()
        keyint = br.read_u16()
        frame_count = br.read_u16()
        colorspace = br.read_u8()
        qstep = br.read_u8()
        search_range = br.read_u8()
        _reserved = br.read_u8()

        if block != BLOCK:
            raise ValueError("BLOCK no compatible")
        if colorspace != COLORSPACE_YCBCR420:
            raise ValueError("Solo YCbCr 4:2:0 soportado en v0")

        y_h = pad_to_multiple(np.zeros((src_h, src_w), dtype=np.uint8), BLOCK, BLOCK).shape[0]
        y_w = pad_to_multiple(np.zeros((src_h, src_w), dtype=np.uint8), BLOCK, BLOCK).shape[1]
        c_h = pad_to_multiple(np.zeros(((src_h + 1) // 2, (src_w + 1) // 2), dtype=np.uint8), BLOCK, BLOCK).shape[0]
        c_w = pad_to_multiple(np.zeros(((src_h + 1) // 2, (src_w + 1) // 2), dtype=np.uint8), BLOCK, BLOCK).shape[1]

        prev_y = None
        output_dir.mkdir(parents=True, exist_ok=True)

        for idx in range(frame_count):
            frame_type = br.read_u8()
            payload_len = br.read_u32()
            payload = br.read_bytes(payload_len)
            fr = ByteReader(payload)

            if frame_type == FRAME_I:
                recon_y = decode_plane_intra((y_h, y_w), qstep, fr)
            else:
                if prev_y is None:
                    raise ValueError("Frame P sin referencia previa")
                recon_y = decode_plane_p_luma((y_h, y_w), prev_y, qstep, fr)

            recon_cb = decode_plane_intra((c_h, c_w), qstep, fr)
            recon_cr = decode_plane_intra((c_h, c_w), qstep, fr)

            img = ycbcr420_to_rgb(recon_y, recon_cb, recon_cr, src_h, src_w)
            img.save(output_dir / f"frame_{idx:04d}.png")
            prev_y = recon_y

        meta = {
            "width": src_w,
            "height": src_h,
            "fps_num": fps_num,
            "fps_den": fps_den,
            "frame_count": frame_count,
            "keyint": keyint,
            "qstep": qstep,
            "search_range": search_range,
        }
        (output_dir / "rtvid_meta.txt").write_text(
            "\n".join(f"{k}={v}" for k, v in meta.items()),
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="RTVid v0 prototype codec")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="Codifica un directorio de frames a .rtv")
    enc.add_argument("--input-dir", required=True, type=Path)
    enc.add_argument("--output", required=True, type=Path)
    enc.add_argument("--fps", default=25, type=int)
    enc.add_argument("--qstep", default=18, type=int)
    enc.add_argument("--keyint", default=10, type=int)
    enc.add_argument("--search-range", default=4, type=int)

    dec = sub.add_parser("decode", help="Decodifica un .rtv a PNG")
    dec.add_argument("--input", required=True, type=Path)
    dec.add_argument("--output-dir", required=True, type=Path)

    args = parser.parse_args()

    if args.cmd == "encode":
        cfg = CodecConfig(
            fps_num=args.fps,
            fps_den=1,
            qstep=args.qstep,
            keyint=args.keyint,
            search_range=args.search_range,
        )
        RTVidCodec(cfg).encode(args.input_dir, args.output)
    elif args.cmd == "decode":
        RTVidCodec(CodecConfig()).decode(args.input, args.output_dir)
    else:
        raise ValueError("Comando no soportado")


if __name__ == "__main__":
    main()
