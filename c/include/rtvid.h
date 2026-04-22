#ifndef RTVID_H
#define RTVID_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define RTVID_MAGIC_0 'R'
#define RTVID_MAGIC_1 'T'
#define RTVID_MAGIC_2 'V'
#define RTVID_MAGIC_3 '0'

#define RTVID_VERSION 1
#define RTVID_BLOCK_SIZE 8

typedef enum {
    RTVID_COLORSPACE_YCBCR420 = 1
} rtvid_colorspace_t;

typedef enum {
    RTVID_FRAME_I = 0,
    RTVID_FRAME_P = 1
} rtvid_frame_type_t;

typedef struct {
    uint8_t magic[4];
    uint8_t version;
    uint16_t width;
    uint16_t height;
    uint16_t fps_num;
    uint16_t fps_den;
    uint16_t block_size;
    uint16_t keyint;
    uint16_t frame_count;
    uint8_t colorspace;
    uint8_t qstep;
    uint8_t search_range;
    uint8_t reserved;
} rtvid_file_header_t;

typedef struct {
    uint8_t frame_type;
    uint32_t payload_size;
} rtvid_frame_header_t;

typedef struct {
    const uint8_t *data;
    size_t size;
    size_t pos;
} rtvid_reader_t;

typedef struct {
    uint8_t *data;
    size_t size;
    size_t capacity;
} rtvid_writer_t;

typedef struct {
    uint16_t width;
    uint16_t height;
    uint16_t stride_y;
    uint16_t stride_c;
    uint8_t *y;
    uint8_t *cb;
    uint8_t *cr;
} rtvid_frame_t;

typedef struct {
    uint16_t fps_num;
    uint16_t fps_den;
    uint8_t qstep;
    uint16_t keyint;
    uint8_t search_range;
} rtvid_encoder_config_t;

int rtvid_parse_header(rtvid_reader_t *r, rtvid_file_header_t *out_header);
int rtvid_parse_frame_header(rtvid_reader_t *r, rtvid_frame_header_t *out_header);

int rtvid_encode_file(const char *frames_dir, const char *output_path, const rtvid_encoder_config_t *cfg);
int rtvid_decode_file(const char *input_path, const char *output_dir);

int rtvid_decode_next_frame(rtvid_reader_t *r, const rtvid_file_header_t *header, rtvid_frame_t *ref_frame, rtvid_frame_t *dst_frame);
void rtvid_free_frame(rtvid_frame_t *frame);

/*
Port plan a C:
1) parser.c       -> varints, lectura de cabeceras, validación del bitstream
2) transform.c    -> DCT/IDCT 8x8 fija o entera
3) intra.c        -> predicción DC/vertical/horizontal
4) motion.c       -> búsqueda entera ±N y compensación
5) entropy.c      -> RLE + zigzag + varints
6) encoder.c      -> pipeline completo con reconstrucción
7) decoder.c      -> pipeline inverso
8) cli.c          -> comando rtvidenc / rtviddec
*/

#ifdef __cplusplus
}
#endif

#endif
