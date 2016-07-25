/*
 * NOTE:  The algorithms in this file require that, on this machine:
 * integer types are big-endian (most significant byte stored in lowest
 *   byte address of the integer type)
 * the sign bit is the most significant bit of each integer type
 * signed integer are 2's-complement
 *
 * Otherwise, behavior is undefined and probably incorrect.
 *
 * Future enhancements could include tests and branches to account for
 * variations in architecture.  However, the raw compressed data must
 * be 2's complement, big-endian, and sign in most significant bit.
 */

/*
 * DEBUG 1 prints out status along the way, and then specifics about
 *   a chosen packet in block_e_decomp.  Note that the "calls" counter
 *   does not get reset, so this really only works the first time through.
 *   Re-define ONEPACK to be the correct number of calls.
 * DEBUG 2 populates an external array of 7 ints called "packtype", gving
 *   the number of packets of each type (or blocks in the case of
 *   uncompressed blocks).
 * DEBUG 3 prints info at various places in various routines.  It also
 *   will print specific data on one block, again using ONEPACK.
 */

#if defined DEBUG && (DEBUG == 1 || DEBUG == 3)
#include <stdio.h>
#endif

#include <string.h>
#include <stdlib.h>

//Support for different OS
#ifdef _WIN32
#include <python.h>
#include <WinSock2.h>
#pragma comment(lib, "WS2_32.lib")
#else
#include <sys/types.h>
#include <netinet/in.h>
#endif

#define EC_C
#include "e_compression.h"

#if defined DEBUG && DEBUG == 1
/* #define ONEPACK 19472 */
#define ONEPACK 0
#endif

#if defined DEBUG && DEBUG == 2
  extern int32_t packtype[6];
#endif

#if defined DEBUG && DEBUG == 3
#define ONEPACK 19472
#endif

#define ABS(x) (((x) > 0) ? (x) : (-x))

#define EC_UNCOMP 0x10000000

#define EC_MAKECHECK(x) ((((x) & 0x00ffffff) << 8) >> 8)


/* Python C extensions for Windows expects the symbol initModuleName when building the library.
* This declaration gives msvc compiler this symbol to compile correctly.
* Note : This not the documented way to build C extensions for Windows. It is typically expected to
* use wrapper methods. What this does is prevents a statement such as 'import libecompression' in Python.
* Instead, the only way to load the library is through a ctypes.CDLL call. Which in this case, is all that
* is needed as seen in readwaveform.py.
*/
#ifdef _WIN32
void initlibecompression(){}
#endif

/*
 * e-format in general consists of a series of buffers, each a multiple
 * of 4 bytes.  Each buffer begins witha header follwed by a series of
 * compressed packets.  There is no index block, the index is provided
 * with each packet.
 * The header 8 bytes long, consisting of:
 * 1) a 2-byte integer giving the length of the buffer in bytes, including
 *    the 8-byte header.
 * 2) a 2-byte integer giving the number of samples represented by the
 *    buffer.
 * 3) a 4-bit integer that is 1 if the following data are uncompressed
 *    32-bit integers, or 0 for compressed.
 * 4) a 4-bit integer that is the number of difference operations applied to
 *    the data.
 * 5) a 24-bit value that is the equivalent to the last sample in the
 *    block once the block is fully decompressed.
 *
 * This header is then immediately followed by either the compressed
 * packets or the uncompressed data if the uncompressed flag is 1.
 *
 * Compressed packets come in 6 index types.  If the first bit of the
 * packet is 0, the packet will be 8 bytes long and have 7 samples using
 * 9 bits per sample immediately following that first bit.  For all packets,
 * the data bits immediately follow the index bits.  The following
 * table give the 6 index types:
 *
 * index bits  bytes for packet  samples  bits per sample
 * ----------  ----------------  -------  ---------------
 *    0                    2        7                9
 *    10                   1        3               10
 *    1100                 1        4                7
 *    1101                 2        5               12
 *    1110                 2        4               15
 *    1111                 1        1               28
 *
 * Note that on compression, the 3rd case (7 bps) is checked first, and
 * therefore will come first in the order of packet types.
 */

/*
 * e_decomp_inplace simply runs e_decomp and copies the result back
 * into the input buffer.  This requires the user to allocate the input buffer
 * large enough to hold the uncompressed data.
 */

int32_t e_decomp_inplace(int32_t *in,
                 int32_t insamp,
                 int32_t inbyte,
                 int32_t out0,
                 int32_t outsamp) {

  int32_t *out;
  int32_t ret;

  out = (int32_t *)malloc(outsamp * sizeof(int32_t));
  if (!out) return EC_MEMORY_ERROR;
  (void)memset(out, 0, outsamp * sizeof(int32_t));
  ret = e_decomp((uint32_t *)in, out, insamp, inbyte, out0, outsamp);
  if (ret != EC_SUCCESS) {
    (void)free((void *)out);
    return ret;
  }
  (void)memcpy(in, out, outsamp * sizeof(int32_t));
  (void)free((void *)out);
  return EC_SUCCESS;
}

/*
 * e_decomp will decompress an output array from an input buffer
 * consisting of one or more e-style compression blocks.  Calling routine
 * provides the input buffer of compressed data, the output array buffer,
 * the total number of samples represented by the input buffer, the total
 * number of bytes in the input buffer, the starting sample for output,
 * and requested number of output samples.
 */

int32_t e_decomp(uint32_t *in,
                 int32_t *out,
                 int32_t insamp,
                 int32_t inbyte, int32_t out0,
                 int32_t outsamp) {

  static int32_t unbuf[EC_MAX_BUFFER];
  int32_t skipsamp = 0, packsamp, packbyte, bsamp, bbyte, nsamp = 0;
  int32_t unbuf0;
  uint32_t *lastin = in + (inbyte / sizeof(uint32_t));
  int32_t ret;

  /*
   * lastin would be the pointer to the next value beyond the input.
   * The last processed block can increment to that point exactly,
   * without processing it, before completing.
   */

  if (outsamp == 0) return EC_SUCCESS;

  if (!in || !out || insamp <= 0 || inbyte <= 0 || out0 < 0 || out0 >= insamp
    || outsamp <= 0 || (out0 + outsamp) > insamp) return EC_ARG_ERROR;

  /*
   * Skip to first output sample.  It's probably in the middle of
   * a compressed packet, so skip to that packet.
   */
  packbyte = (int32_t)ntohs(((uint16_t *)in)[0]);
  packsamp = (int32_t)ntohs(((uint16_t *)in)[1]);
  if (packsamp < 0 || packsamp > EC_MAX_BUFFER / sizeof(int32_t))
    return EC_SAMP_ERROR;
  if (packbyte < (2 * sizeof(int32_t)) || packbyte > EC_MAX_BUFFER)
    return EC_LENGTH_ERROR;
  if (packbyte < (packsamp + 2 * sizeof(int32_t)) ||
    packbyte > ((packsamp + 2) * sizeof(int32_t)))
    return EC_SAMP_ERROR;
  if (packbyte % sizeof(int32_t)) return EC_LENGTH_ERROR;
  packbyte /= sizeof(int32_t);
  if ((in + packbyte) > lastin) return EC_LENGTH_ERROR;
  while ((skipsamp + packsamp) <= out0) {
    skipsamp += packsamp;
    in += packbyte;
    packbyte = (int32_t)ntohs(((uint16_t *)in)[0]);
    packsamp = (int32_t)ntohs(((uint16_t *)in)[1]);
    if (packsamp < 0 || packsamp > EC_MAX_BUFFER / sizeof(int32_t))
      return EC_SAMP_ERROR;
    if (packbyte < (2 * sizeof(int32_t)) || packbyte > EC_MAX_BUFFER)
      return EC_LENGTH_ERROR;
    if (packbyte < (packsamp + 2 * sizeof(int32_t)) ||
      packbyte > ((packsamp + 2) * sizeof(int32_t)))
      return EC_SAMP_ERROR;
    if (packbyte % sizeof(int32_t)) return EC_LENGTH_ERROR;
    packbyte /= sizeof(int32_t);
    if ((in + packbyte) > lastin) return EC_LENGTH_ERROR;
  }
  unbuf0 = out0 - skipsamp;

  /*
   * Decompress data until we have all the samples requested.
   * Treat fragment at end separately from the loop.
   * unbuf0 accounts for the fragment at the start.
   * Ignore bsamp and bbyte, since this routine is handling those values.
   */
  while ((nsamp + packsamp - unbuf0) <= outsamp) {
    ret = block_e_decomp(in, unbuf, &bsamp, &bbyte);
    if (ret != EC_SUCCESS) return ret;
    (void)memcpy(out + nsamp, unbuf + unbuf0,
      (packsamp - unbuf0) * sizeof(int32_t));
    nsamp += packsamp - unbuf0;
    unbuf0 = 0;
    if (nsamp == outsamp) break;

    in += packbyte;
    packbyte = (int32_t)ntohs(((uint16_t *)in)[0]);
    packsamp = (int32_t)ntohs(((uint16_t *)in)[1]);
#if defined DEBUG && DEBUG >= 1
    (void)fprintf(stderr, "packbyte %d, packsamp %d, rem %d\n",
      packbyte, packsamp, (int32_t)(lastin - in));
#endif
    if (packsamp < 0 || packsamp > EC_MAX_BUFFER / sizeof(int32_t))
      return EC_SAMP_ERROR;
    if (packbyte < (2 * sizeof(int32_t)) || packbyte > EC_MAX_BUFFER)
      return EC_LENGTH_ERROR;
    if (packbyte < (packsamp + 2 * sizeof(int32_t)) ||
      packbyte > ((packsamp + 2) * sizeof(int32_t)))
      return EC_SAMP_ERROR;
    if (packbyte % sizeof(int32_t)) return EC_LENGTH_ERROR;
    packbyte /= sizeof(int32_t);
#if defined DEBUG && DEBUG == 3
  if ((in + packbyte) > lastin)
    (void)fprintf(stderr, "packbyte %d, rem %d\n",
      packbyte, (int32_t)(lastin - in));
#endif
    if ((in + packbyte) > lastin) return EC_LENGTH_ERROR;
  }
  if (nsamp < outsamp) {
    ret = block_e_decomp(in, unbuf, &bsamp, &bbyte);
    if (ret != EC_SUCCESS) return ret;
    (void)memcpy(out + nsamp, unbuf + unbuf0,
      (outsamp - nsamp) * sizeof(int32_t));
  }

  return EC_SUCCESS;
}

/*
 * index_map:
 * An array to translate the first 4 bits of the block into the index.
 * Since index 0 is marked only with 1 bit and 1 is marked with 2, they
 * end up with multiple values here, accounting for all bit combinations
 * that can be present in the first part of that sample.
 */
static int32_t index_map[16] =
  {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 3, 4, 5};

/*
 * block_e_decomp decompresses a single block of e-style compression.
 * It tries to do this with minimum operations and overhead.
 * Algorithm might be made slightly faster using 64-bit long integers
 * in some places, but the speed-up would be small.
 *
 * Output array is assumed to be of sufficient size.
 *
 *
 * There is no need to check overflow on un-differencing: the largest
 * compressed value is 28 bits, and the maximum number of differences
 * is 4, so the maximum resulting value is 32 bits.
 * Makes all other available checks.
 *
 * Returns EC_SUCCESS (0) on success or an error-specific code on failure.
 * Sets the values of of the pointers nsamp and nbyte.
 * The output array will contain the data on success, may contain the (failed)
 * data on failure.
 */
int32_t block_e_decomp(uint32_t *in,
                       int32_t *out,
                       int32_t *nsamp,
                       int32_t *nbyte) {

  int32_t ndiff, check, bytes = 0, samps = 0;
  uint32_t *pout = (uint32_t *)out;
  union {
    int32_t s;
    uint32_t u;
  } hin;
  int32_t i, k;
#if defined DEBUG && (DEBUG == 1 || DEBUG == 3)
  static int32_t calls = 0;
#endif

  /*
   * number of bytes and samples in this block
   */
  *nbyte = (int32_t)ntohs(((uint16_t *)in)[0]);
  *nsamp = (int32_t)ntohs(((uint16_t *)in)[1]);
#if defined DEBUG && DEBUG >= 1
  (void)fprintf(stderr, "nbyte %d, nsamp %d\n", *nbyte, *nsamp);
#endif
  if (*nsamp < 0 || *nsamp > EC_MAX_BUFFER / sizeof(int32_t))
    return EC_SAMP_ERROR;
  if (*nbyte < (2 * sizeof(int32_t)) || *nbyte > EC_MAX_BUFFER)
    return EC_LENGTH_ERROR;
  if (*nbyte < (*nsamp + 2 * sizeof(int32_t)) ||
    *nbyte > ((*nsamp + 2) * sizeof(int32_t)))
    return EC_SAMP_ERROR;

  /*
   * if the bit 0x10 of the 5th byte is set, then the block is uncompressed
   * 32-bit integers
   */
  in++;
  if (ntohl(*in) & EC_UNCOMP) {
#if defined DEBUG && DEBUG == 2
  packtype[6]++;
#endif
    if (*nbyte != ((*nsamp + 2) * sizeof(int32_t))) return EC_LENGTH_ERROR;
#if defined DEBUG && DEBUG == 3
  (void)fprintf(stderr, "D: (u)pack %d, %d samps\n",
    calls++, *nsamp);
#endif
/* only works on big-endian machines
    (void)memcpy(out, in + 1, *nsamp * sizeof(int32_t));
*/
    in++;
    for (k = 0; k < *nsamp; k++) {
      *out++ = ntohl(*in++);
    }
    return EC_SUCCESS;
  }

  /*
   * number of differences applied to this block
   * and the check value
   */
  ndiff = (ntohl(*in) & 0x0f000000) >> 24;
  check = EC_MAKECHECK(ntohl(*in++));
  if (ndiff > EC_MAX_NDIFF) return EC_DIFF_ERROR;
#if defined DEBUG && DEBUG == 1
  (void)fprintf(stderr, "calls, bytes, samps, nd, check = %d, %d, %d, %d, %d\n",
    calls, *nbyte, *nsamp, ndiff, check);
#endif
#if defined DEBUG && DEBUG == 3
  (void)fprintf(stderr, "D: pack %d, diff %d: %d samps, last = %d\n",
    calls++, ndiff, *nsamp, check);
#endif

  while (samps < *nsamp) {
    switch (index_map[(ntohl(*in) & 0xf0000000) >> 28]) {

    case 0:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x7fc00000) <<  1) >> 23;
      *pout++ = ((hin.s & 0x003fe000) << 10) >> 23;
      *pout++ = ((hin.s & 0x00001ff0) << 19) >> 23;
      *pout   = ((hin.s & 0x0000000f) << 28) >> 23;
      hin.u = ntohl(*in++);
      *pout++ |= (hin.s & 0xf8000000) >> 27;
      *pout++ = ((hin.s & 0x07fc0000) <<  5) >> 23;
      *pout++ = ((hin.s & 0x0003fe00) << 14) >> 23;
      *pout++ = ((hin.s & 0x000001ff) << 23) >> 23;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 0, s %d, b %d, %x %x\n",
      samps, bytes, in[-2], in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[1]++;
#endif
      samps += 7;
      bytes += 8;
      break;

    case 1:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x3ff00000) <<  2) >> 22;
      *pout++ = ((hin.s & 0x000ffc00) << 12) >> 22;
      *pout++ = ((hin.s & 0x000003ff) << 22) >> 22;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 1, s %d, b %d, %x\n",
      samps, bytes, in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[2]++;
#endif
      samps += 3;
      bytes += 4;
      break;

    case 2:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x0fe00000) <<  4) >> 25;
      *pout++ = ((hin.s & 0x001fc000) << 11) >> 25;
      *pout++ = ((hin.s & 0x00003f80) << 18) >> 25;
      *pout++ = ((hin.s & 0x0000007f) << 25) >> 25;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 2, s %d, b %d, %x\n",
      samps, bytes, in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[0]++;
#endif
      samps += 4;
      bytes += 4;
      break;

    case 3:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x0fff0000) <<  4) >> 20;
      *pout++ = ((hin.s & 0x0000fff0) << 16) >> 20;
      *pout   = ((hin.s & 0x0000000f) << 28) >> 20;
      hin.u = ntohl(*in++);
      *pout++ |= (hin.s & 0xff000000) >> 24;
      *pout++ = ((hin.s & 0x00fff000) <<  8) >> 20;
      *pout++ = ((hin.s & 0x00000fff) << 20) >> 20;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 3, s %d, b %d, %x %x\n",
      samps, bytes, in[-2], in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[3]++;
#endif
      samps += 5;
      bytes += 8;
      break;

    case 4:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x0fffe000) <<  4) >> 17;
      *pout   = ((hin.s & 0x00001fff) << 19) >> 17;
      hin.u = ntohl(*in++);
      *pout++ |= (hin.s & 0xc0000000) >> 30;
      *pout++ = ((hin.s & 0x3fff8000) <<  2) >> 17;
      *pout++ = ((hin.s & 0x00007fff) << 17) >> 17;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 4, s %d, b %d, %x %x\n",
      samps, bytes, in[-2], in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[4]++;
#endif
      samps += 4;
      bytes += 8;
      break;

    case 5:
      hin.u = ntohl(*in++);
      *pout++ = ((hin.s & 0x0fffffff) <<  4) >>  4;
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK)
    (void)fprintf(stderr, "case 5, s %d, b %d, %x\n",
      samps, bytes, in[-1]);
#endif
#if defined DEBUG && DEBUG == 2
  packtype[5]++;
#endif
      samps += 1;
      bytes += 4;
      break;
    }
  }

/*
  if (bytes != *nbyte) return EC_LENGTH_ERROR;
*/
#if defined DEBUG && DEBUG == 1
  if (samps != *nsamp) 
    (void)fprintf(stderr, "samps %d, nsamp %d\n", samps, *nsamp);
#endif
  if (samps != *nsamp) return EC_SAMP_ERROR;

  while (ndiff--) {
#if defined DEBUG && DEBUG == 1
  if (calls == ONEPACK) {
    (void)fprintf(stderr, "last is %d\n", pout[-1]);
    for (i = 0; (i + 4) < *nsamp; i += 5)
      (void)fprintf(stderr, "%6d %10d %10d %10d %10d %10d\n",
        i, out[i], out[i+1], out[i+2], out[i+3], out[i+4]);
    (void)fprintf(stderr, "%6d", i);
    for (; i < *nsamp; i++)
      (void)fprintf(stderr, " %10d", out[i]);
    (void)fprintf(stderr, "\n", i);
  }
#endif
    for (i = 1, pout = (uint32_t *)out + 1; i < *nsamp; i++, pout++)
      *pout += pout[-1];
  }

#if defined DEBUG && DEBUG == 1
  (void)fprintf(stderr, "last is %d\n", pout[-1]);
  if (calls == ONEPACK) {
    for (i = 0; (i + 4) < *nsamp; i += 5)
      (void)fprintf(stderr, "%6d %10d %10d %10d %10d %10d\n",
        i, out[i], out[i+1], out[i+2], out[i+3], out[i+4]);
    (void)fprintf(stderr, "%6d", i);
    for (; i < *nsamp; i++)
      (void)fprintf(stderr, " %10d", out[i]);
    (void)fprintf(stderr, "\n", i);
  }
  calls++;
#endif
  if (check != EC_MAKECHECK(pout[-1])) return EC_CHECK_ERROR;

  return EC_SUCCESS;
}

/*
 * e_comp_inplace simply runs e_comp and copies the result back
 * into the input buffer.  The buffer need only be 8 bytes per block
 * larger than the input data (in case no compression at all is
 * possible).  Smallest block is 400 bytes.  User needs to make
 * sure the input buffer is large enough, or that the data contain
 * large sections that are less than 28 bits.
 */

int32_t e_comp_inplace(int32_t *in,
                       int32_t insamp,
                       int32_t *outbytes,
                       char datatype[],
                       int32_t block_flag) {

  uint32_t *out;
  int32_t ret;
  int32_t maxout = (int32_t)(((double)insamp / EC_MAX_BUFFER) + 2) *
    (int32_t)(EC_MAX_BUFFER * 1.02);

  out = (uint32_t *)malloc(maxout * sizeof(uint32_t));
  if (!out) return EC_MEMORY_ERROR;
  (void)memset(out, 0, maxout * sizeof(uint32_t));
  ret = e_comp(in, out, insamp, outbytes, datatype, block_flag);
  if (ret != EC_SUCCESS) {
    (void)free((void *)out);
    return ret;
  }
  (void)memcpy(in, out, *outbytes);
  (void)free((void *)out);
  return EC_SUCCESS;
}

/*
 * e_comp compresses an array of s4 data.
 * It assumes that the entire array given as input is to be compressed.
 */
int32_t e_comp(int32_t *in,
               uint32_t *out,
               int32_t insamp,
               int32_t *outbytes,
               char datatype[],
               int32_t block_flag) {
  int32_t i, j, k;
  int32_t datanum, dchoose;
  int32_t bufbytes, bufints, didsamp, maxsamp, maxdiff, samp0 = 0;
  static uint32_t a[EC_MAX_NDIFF + 1][EC_MAX_BUFFER], *pa;
  static int32_t d[EC_MAX_NDIFF + 1][EC_MAX_BUFFER], *pd;
  static uint32_t dmaxbit[EC_MAX_NDIFF + 1];
  static double dsum[EC_MAX_NDIFF + 1];
  int32_t *pdmax, *lastin;
  uint32_t *outmax, *pout;
#if defined DEBUG && DEBUG == 3
  int32_t pck = 0;
#endif

  if (insamp == 0) {
    *outbytes = 0;
    return EC_SUCCESS;
  }

  datanum = datatype[1] - '0';
  if (datatype[0] == 'e') {
    if (datanum < 0 || datanum > 8) return EC_TYPE_ERROR;
    if (datanum == 0) bufbytes = 1024;
    else bufbytes = datanum * 2048;
  }
  else if (datatype[0] == 'E') {
    if (datanum < 0 || datanum > 9) return EC_TYPE_ERROR;
    if (datanum == 0) bufbytes = 1200;
    else bufbytes = (datanum + 1) * 400;
  }
  else return EC_TYPE_ERROR;
  bufints = bufbytes / sizeof(int32_t) - 2;

  if (!in || !out || insamp <= 0 || !outbytes) return EC_ARG_ERROR;

  /*
   * Continue loop that constructs output buffers until all of input is
   * consumed.  Assume output buffer has already been allocated large
   * enough.
   */
  lastin = in + insamp - 1;
  didsamp = 0;
  maxsamp = 0;
  maxdiff = 0;
  *outbytes = 0;
  while (in <= lastin) {

    /*
     * zero the output buffer
     */
    (void)memset(out, 0, bufbytes);

    /*
     * Need to choose which difference is best (0 thru 4).  These can
     * be saved during this check so they are computed only once.
     * In addition, they can be checked to see if any value >= 2^28.
     * The smallest absolute sum that has no value >= 2^28 is the best
     * choice for the number of differences.
     * Note - it is important that the 2^28 check be performed after the
     * differences are computed, since it is possible that the difference
     * itself could result in this condition failing.
     * EX: (2^28 - 1) - (-1)) = 2^28
     * Differences can also, of course, eliminate such high values as well.
     * e-compression was originally designed for 24-bit data, and
     * 4 differences can never exceed 28 bits (the original 24 plus one bit
     * for every difference op).  It was later modified to accept data that
     * would otherwise clip at 24 bits by allowing uncompressed segments.
     * It is then advantageous to allow data to be compressed up to the full
     * 28 bits of the compression, rather than only 24 bits.
     */

    /*
     * First, copy any remaining differences back to the start.
     * and re-initialize differences and checks.
     *
    samp0 = maxsamp - didsamp;
    if (samp0 > EC_MAX_NDIFF) {
      (void)memmove(d[0], d[0] + didsamp, samp0);
      (void)memmove(a[0], a[0] + didsamp, samp0);
      d[0][0] = in[0];
      a[0][0] = (uint32_t)ABS(in[0]);
      dmaxbit[0] = a[0][0];
      dsum[0] = (double)a[0][0];
      for (j = 1; j <= EC_MAX_NDIFF; j++) {
        (void)memmove(d[j], d[j] + didsamp, samp0);
        (void)memmove(a[j], a[j] + didsamp, samp0);
        d[j][0] = in[0];
        a[j][0] = (uint32_t)ABS(in[0]);
        dmaxbit[j] = a[j][0];
        dsum[j] = (double)a[j][0];
        for (i = 1; i <= j; i++) {
          d[j][i] = d[j - 1][i] - d[j - 1][i - 1];
          a[j][i] = (uint32_t)ABS(d[j][i]);
          dsum[j] += (double)a[j][i];
          dmaxbit[j] |= a[j][i];
        }
        for (; i < samp0; i++) {
          dsum[j] += (double)a[j][i];
          dmaxbit[j] |= a[j][i];
        }
      }
    }
     */

    maxsamp = (insamp > bufbytes) ? bufbytes : insamp;
    maxdiff = (insamp > bufints) ? bufints : insamp;
    for (i = samp0; i < maxdiff; i++) {
      if (i == 0) {
        for (j = 0; j <= EC_MAX_NDIFF; j++) {
          d[j][0] = in[0];
          a[j][0] = (uint32_t)ABS(in[0]);
          dmaxbit[j] = a[j][0];
          dsum[j] = (double)a[j][0];
        }
        continue;
      }
      d[0][i] = in[i];
      a[0][i] = (uint32_t)ABS(d[0][i]);
      dsum[0] += (double)a[0][i];
      dmaxbit[0] |= a[0][i];
      for (j = 1; j <= EC_MAX_NDIFF; j++) {
        d[j][i] = d[j - 1][i] - d[j - 1][i - 1];
        a[j][i] = (uint32_t)ABS(d[j][i]);
        dsum[j] += (double)a[j][i];
        dmaxbit[j] |= a[j][i];
      }
    }
    for (; i < maxsamp; i++) {
      d[0][i] = in[i];
      a[0][i] = (uint32_t)ABS(d[0][i]);
      dsum[0] += (double)a[0][i];
      for (j = 1; j <= EC_MAX_NDIFF; j++) {
        d[j][i] = d[j - 1][i] - d[j - 1][i - 1];
        a[j][i] = (uint32_t)ABS(d[j][i]);
        dsum[j] += (double)a[j][i];
      }
    }
#if defined DEBUG && DEBUG == 3
  if (pck == ONEPACK) {
    (void)fprintf(stderr, "maxsamp=%d, insamp=%d, bufints=%d, samp0=%d\n",
      maxsamp, insamp, bufints, samp0);
    (void)fprintf(stderr, "dsum: %f, %f, %f, %f, %f\n",
      dsum[0], dsum[1], dsum[2], dsum[3], dsum[4]);
    (void)fprintf(stderr, "dmaxbit: %x, %x, %x, %x, %x\n",
      dmaxbit[0], dmaxbit[1], dmaxbit[2], dmaxbit[3], dmaxbit[4]);
  }
#endif

    /*
     * Find the first difference having no values >= 2^28
     */
    dchoose = -1;
    for (j = 0; j <= EC_MAX_NDIFF; j++) {
      if (dmaxbit[j] & 0xf8000000) continue;
      dchoose = j;
      break;
    }

    if (dchoose < 0) {
      /*
       * All of the differences violate the 28-bit requirement.
       * Segment must be left uncompressed.
       * Note: check value is not set on uncompressed data.
       */
#if defined DEBUG && DEBUG == 2
  packtype[6]++;
#endif
      if (insamp > bufints) {
        didsamp = bufints;
        ((uint16_t *)out)[0] = htons((uint16_t)bufbytes);
        ((uint16_t *)out)[1] = htons((uint16_t)didsamp);
        out++;
        *out++ = htonl((uint32_t)EC_UNCOMP);
/* only works on big-endian machines
        (void)memcpy(out, in, didsamp * sizeof(int32_t));
*/
        for (k = 0; k < didsamp; k++) {
          *out++ = htonl(*(uint32_t *)in++);
        }
#if defined DEBUG && DEBUG == 3
  (void)fprintf(stderr, "(u)pack %d, %d samps, %d remain\n",
    pck++, didsamp, insamp - didsamp);
#endif
        insamp -= didsamp;
/*
        in += didsamp;
        out += didsamp;
*/
        *outbytes += bufbytes;
        continue;
      }
      didsamp = insamp;
      bufbytes = (block_flag == EC_SHORT_END) ?
        (sizeof(int32_t) * (didsamp + 2)) : bufbytes;
      ((uint16_t *)out)[0] = htons((uint16_t)bufbytes);
      ((uint16_t *)out)[1] = htons((uint16_t)didsamp);
      out++;
      *out++ = htonl((uint32_t)EC_UNCOMP);
/* only works on big-endian machines
      (void)memcpy(out, in, didsamp * sizeof(int32_t));
*/
      for (k = 0; k < didsamp; k++) {
        *out++ = htonl(*(uint32_t *)in++);
      }
      *outbytes += bufbytes;
      return EC_SUCCESS;
    }

    /*
     * Select the apparent best difference for this portion of the series
     */
    for (j = dchoose + 1; j <= EC_MAX_NDIFF; j++) {
      if (dmaxbit[j] & 0xf8000000) continue;
      if (dsum[j] < dsum[dchoose]) dchoose = j;
    }

    /*
     * Compress d[dchoose][]
     */
    pd = d[dchoose];
    pdmax = pd + maxsamp;
    pa = a[dchoose];
    pout = out;
    out += 2;
    outmax = out + bufints;
    didsamp = 0;
    while (out < outmax && pd < pdmax) {

      /*
       * 4 7-bit samples in 1 int32_t
       */
      if ((pdmax - pd) >= 4 &&
        pa[0] < 0x00000040 && pa[1] < 0x00000040 &&
        pa[2] < 0x00000040 && pa[3] < 0x00000040) {
        *out++ = htonl(0xc0000000 |
                 ((pd[0] & 0x0000007f) << 21) |
                 ((pd[1] & 0x0000007f) << 14) |
                 ((pd[2] & 0x0000007f) << 7) |
                  (pd[3] & 0x0000007f));
        pa += 4;
        pd += 4;
        didsamp += 4;
#if defined DEBUG && DEBUG == 2
  packtype[0]++;
#endif
        continue;
      }

      /*
       * 7 9-bit samples in 2 int32_ts
       */
      if ((pdmax - pd) >= 7 && (outmax - out) > 1 &&
        pa[0] < 0x00000100 && pa[1] < 0x00000100 &&
        pa[2] < 0x00000100 && pa[3] < 0x00000100 &&
        pa[4] < 0x00000100 && pa[5] < 0x00000100 &&
        pa[6] < 0x00000100) {
        *out++ = htonl(((pd[0] & 0x000001ff) << 22) |
                       ((pd[1] & 0x000001ff) << 13) |
                       ((pd[2] & 0x000001ff) << 4) |
                       ((pd[3] & 0x000001ff) >> 5));
        *out++ =  htonl((pd[3]               << 27) |
                       ((pd[4] & 0x000001ff) << 18) |
                       ((pd[5] & 0x000001ff) << 9) |
                        (pd[6] & 0x000001ff));
        pa += 7;
        pd += 7;
        didsamp += 7;
#if defined DEBUG && DEBUG == 2
  packtype[1]++;
#endif
        continue;
      }

      /*
       * 3 10-bit samples in 1 int32_t
       */
      if ((pdmax - pd) >= 3 &&
        pa[0] < 0x00000200 && pa[1] < 0x00000200 &&
        pa[2] < 0x00000200) {
        *out++ = htonl(0x80000000 |
                 ((pd[0] & 0x000003ff) << 20) |
                 ((pd[1] & 0x000003ff) << 10) |
                  (pd[2] & 0x000003ff));
        pa += 3;
        pd += 3;
        didsamp += 3;
#if defined DEBUG && DEBUG == 2
  packtype[2]++;
#endif
        continue;
      }

      /*
       * 5 12-bit samples in 2 int32_ts
       */
      if ((pdmax - pd) >= 5 && (outmax - out) > 1 &&
        pa[0] < 0x00000800 && pa[1] < 0x00000800 &&
        pa[2] < 0x00000800 && pa[3] < 0x00000800 &&
        pa[4] < 0x00000800) {
        *out++ = htonl(0xd0000000 |
                       ((pd[0] & 0x00000fff) << 16) |
                       ((pd[1] & 0x00000fff) << 4) |
                       ((pd[2] & 0x00000fff) >> 8));
        *out++ =  htonl((pd[2]               << 24) |
                       ((pd[3] & 0x00000fff) << 12) |
                        (pd[4] & 0x00000fff));
        pa += 5;
        pd += 5;
        didsamp += 5;
#if defined DEBUG && DEBUG == 2
  packtype[3]++;
#endif
        continue;
      }

      /*
       * 4 15-bit samples in 2 int32_ts
       */
      if ((pdmax - pd) >= 4 && (outmax - out) > 1 &&
        pa[0] < 0x00004000 && pa[1] < 0x00004000 &&
        pa[2] < 0x00004000 && pa[3] < 0x00004000) {
        *out++ = htonl(0xe0000000 |
                       ((pd[0] & 0x00007fff) << 13) |
                       ((pd[1] & 0x00007fff) >> 2));
        *out++ =  htonl((pd[1]               << 30) |
                       ((pd[2] & 0x00007fff) << 15) |
                        (pd[3] & 0x00007fff));
        pa += 4;
        pd += 4;
        didsamp += 4;
#if defined DEBUG && DEBUG == 2
  packtype[4]++;
#endif
        continue;
      }

      /*
       * 1 28-bit sample in 1 int32_t
       */
      if (pa[0] < 0x10000000) {
        *out++ = htonl(0xf0000000 |
                  (pd[0] & 0x0fffffff));
        pa += 1;
        pd += 1;
        didsamp += 1;
#if defined DEBUG && DEBUG == 2
  packtype[5]++;
#endif
        continue;
      }

      /*
       * If we get here, the next sample is more than 28 bits.
       * Finish the block and let the next block be uncompressed.
       */
      break;
    }

#if defined DEBUG && DEBUG == 3
  (void)fprintf(stderr, "pack %d, diff %d: %d samps, %d remain, last = %d\n",
    pck++, dchoose, didsamp, insamp - didsamp, in[didsamp - 1]);
#endif

    ((uint16_t *)pout)[0] = htons((uint16_t)bufbytes);
    ((uint16_t *)pout)[1] = htons((uint16_t)didsamp);
    pout[1] = htonl(EC_MAKECHECK(in[didsamp - 1]));
    ((uint8_t  *)pout)[4] = (uint8_t)dchoose;
    insamp -= didsamp;

    /*
     * last block
     */
    if (insamp == 0) {
      if (block_flag == EC_SHORT_END) {
        ((uint16_t *)pout)[0] =
          htons((uint16_t)(sizeof(uint32_t) * (out - pout)));
        *outbytes += sizeof(uint32_t) * (out - pout);
        return EC_SUCCESS;
      }
      *outbytes += bufbytes;
      return EC_SUCCESS;
    }

    in += didsamp;
    out = outmax;
    *outbytes += bufbytes;
  }
  
  /*
   * should never get here
   */
  return EC_FAILED;
}
