pub const MAGIC: [u8; 4] = *b"RTV0";
pub const VERSION: u8 = 1;
pub const BLOCK: usize = 8;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ColorSpace {
    YCbCr420 = 1,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FrameType {
    I = 0,
    P = 1,
}

#[derive(Debug, Clone)]
pub struct FileHeader {
    pub version: u8,
    pub width: u16,
    pub height: u16,
    pub fps_num: u16,
    pub fps_den: u16,
    pub block_size: u16,
    pub keyint: u16,
    pub frame_count: u16,
    pub colorspace: u8,
    pub qstep: u8,
    pub search_range: u8,
}

#[derive(Debug, Clone)]
pub struct FrameHeader {
    pub frame_type: FrameType,
    pub payload_size: u32,
}

#[derive(Debug, Clone)]
pub struct Plane {
    pub width: usize,
    pub height: usize,
    pub stride: usize,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct Frame420 {
    pub y: Plane,
    pub cb: Plane,
    pub cr: Plane,
}

#[derive(Debug, Clone)]
pub struct EncoderConfig {
    pub fps_num: u16,
    pub fps_den: u16,
    pub qstep: u8,
    pub keyint: u16,
    pub search_range: u8,
}

pub type RtResult<T> = Result<T, String>;

pub struct Reader<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self { data, pos: 0 }
    }

    pub fn read_u8(&mut self) -> RtResult<u8> {
        if self.pos >= self.data.len() {
            return Err("EOF en u8".into());
        }
        let v = self.data[self.pos];
        self.pos += 1;
        Ok(v)
    }

    pub fn read_u16(&mut self) -> RtResult<u16> {
        let lo = self.read_u8()? as u16;
        let hi = self.read_u8()? as u16;
        Ok(lo | (hi << 8))
    }

    pub fn read_u32(&mut self) -> RtResult<u32> {
        let b0 = self.read_u8()? as u32;
        let b1 = self.read_u8()? as u32;
        let b2 = self.read_u8()? as u32;
        let b3 = self.read_u8()? as u32;
        Ok(b0 | (b1 << 8) | (b2 << 16) | (b3 << 24))
    }

    pub fn read_bytes(&mut self, n: usize) -> RtResult<&'a [u8]> {
        if self.pos + n > self.data.len() {
            return Err("EOF en bytes".into());
        }
        let s = &self.data[self.pos..self.pos + n];
        self.pos += n;
        Ok(s)
    }

    pub fn read_uvarint(&mut self) -> RtResult<u64> {
        let mut shift = 0u32;
        let mut value = 0u64;
        loop {
            let b = self.read_u8()?;
            value |= ((b & 0x7f) as u64) << shift;
            if (b & 0x80) == 0 {
                return Ok(value);
            }
            shift += 7;
            if shift > 63 {
                return Err("uvarint demasiado largo".into());
            }
        }
    }

    pub fn read_svarint(&mut self) -> RtResult<i64> {
        let zz = self.read_uvarint()?;
        Ok(((zz >> 1) as i64) ^ (-((zz & 1) as i64)))
    }
}

pub fn parse_header(r: &mut Reader<'_>) -> RtResult<FileHeader> {
    let magic = r.read_bytes(4)?;
    if magic != MAGIC {
        return Err("Magic RTVid inválido".into());
    }

    let version = r.read_u8()?;
    let width = r.read_u16()?;
    let height = r.read_u16()?;
    let fps_num = r.read_u16()?;
    let fps_den = r.read_u16()?;
    let block_size = r.read_u16()?;
    let keyint = r.read_u16()?;
    let frame_count = r.read_u16()?;
    let colorspace = r.read_u8()?;
    let qstep = r.read_u8()?;
    let search_range = r.read_u8()?;
    let _reserved = r.read_u8()?;

    Ok(FileHeader {
        version,
        width,
        height,
        fps_num,
        fps_den,
        block_size,
        keyint,
        frame_count,
        colorspace,
        qstep,
        search_range,
    })
}

/*
Port plan a Rust:
- crate rtvid-core
  - bitstream.rs
  - transform.rs
  - intra.rs
  - motion.rs
  - entropy.rs
  - encoder.rs
  - decoder.rs
  - colorspace.rs
  - io_png.rs
- crate rtvid-cli
  - src/main.rs

Objetivo del port:
1) conservar el bitstream exacto del prototipo Python
2) reemplazar float DCT por entero/fijo
3) usar slices y iteradores sobre bloques
4) añadir tests dorados con round-trip y fixtures .rtv
*/
