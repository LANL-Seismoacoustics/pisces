
//Support for different OS - Note: stdint.h is provided in msvs 2013 (12.0) and later.
#ifdef _WIN32
typedef unsigned __int8 uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
typedef unsigned __int64 uint64_t;

typedef __int8 int8_t;
typedef __int16 int16_t;
typedef __int32 int32_t;
typedef __int64 int64_t;

#else
#include <stdint.h>
#endif

#include "convert.h"

void s3tos4(void *byte, register int32_t n) {
  /*
   * note:
   *    to use this routine, it is assumed byte is allocated
   *    long enough and has the correct alignment
   *
   * args:
   *    byte is the 4-byte aligned buffer of length at least 4 * n bytes
   *    n is the number of values to be converted in place
   *
   * how:
   *    it copies 3-byte to the 3 lsb of the 4-byte
   *    it has to set the sign extension (using sign extension directly
   *    is not endian-agnostic).
   *    also, unroll and use direct addressing since it is more efficient.
   */
  register int8_t *p4;
  register int8_t *p3;
  register int16_t *s;

  s = (int16_t *)byte;
  p4 = (int8_t *)byte;
  p3 = (int8_t *)byte;
  s  += 2 * n;
  p4 += 4 * n;
  p3 += 3 * n;

  for (; n > 3; n -= 4) {
    s  -= 8;
    p4 -= 16;
    p3 -= 12;
    p4[15] = p3[11];
    p4[14] = p3[10];
    p4[13] = p3[ 9];
    p4[12] = (p4[13] & 0x80) ? 0xff : 0;
    p4[11] = p3[ 8];
    p4[10] = p3[ 7];
    p4[ 9] = p3[ 6];
    p4[ 8] = (p4[ 9] & 0x80) ? 0xff : 0;
    p4[ 7] = p3[ 5];
    p4[ 6] = p3[ 4];
    p4[ 5] = p3[ 3];
    p4[ 4] = (p4[ 5] & 0x80) ? 0xff : 0;
    p4[ 3] = p3[ 2];
    p4[ 2] = p3[ 1];
    p4[ 1] = p3[ 0];
    p4[ 0] = (p4[ 1] & 0x80) ? 0xff : 0;
  }

  for (; n > 0; n--) {
    s  -= 2;
    p4 -= 4;
    p3 -= 3;
    p4[ 3] = p3[ 2];
    p4[ 2] = p3[ 1];
    p4[ 1] = p3[ 0];
    p4[ 0] = (p4[ 1] & 0x80) ? 0xff : 0;
  }
}

void s4tos3(void *byte, register int32_t n) {
  /*
   * NOTE - to use this routine, it is assumed that no value
   * in the original 4-byte array exceeds 3 significant bytes of data
   *
   * args:
   *    byte is the 4-byte aligned buffer of length at least 4 * n bytes
   *    n is the number of values to be converted in place
   *
   * How:
   *    it copies 3 lsb of the 4-byte to the 3-byte
   *    also, unroll and use direct addressing since it is more efficient.
   */
  register int8_t *p4;
  register int8_t *p3;
  
  p4 = (int8_t *)byte;
  p3 = (int8_t *)byte;

  for (; n > 3; n -= 4, p4 += 16, p3 += 12) {
    p3[ 0] = p4[ 1];
    p3[ 1] = p4[ 2];
    p3[ 2] = p4[ 3];
    p3[ 3] = p4[ 5];
    p3[ 4] = p4[ 6];
    p3[ 5] = p4[ 7];
    p3[ 6] = p4[ 9];
    p3[ 7] = p4[10];
    p3[ 8] = p4[11];
    p3[ 9] = p4[13];
    p3[10] = p4[14];
    p3[11] = p4[15];
  }

  for (; n > 0; n--, p4 += 4, p3 += 3) {
    p3[ 0] = p4[ 1];
    p3[ 1] = p4[ 2];
    p3[ 2] = p4[ 3];
  }

  /* 
   * what it looks like without direct addressing
  p4 = byte + 1;
  p3 = byte;
  for (; n > 0; n--) {
    *p3++ = *p4++;
    *p3++ = *p4++;
    *p3++ = *p4++;
    p4++;
  }
   */
}
