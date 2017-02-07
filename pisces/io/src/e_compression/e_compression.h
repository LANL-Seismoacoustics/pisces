#ifndef EC_H

#define EC_H

//Support for different OS - Note: stdint.h is provided in msvs 2013 (12.0) and later.
#ifdef _WIN32
typedef unsigned __int8 uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
typedef unsigned __int64 uint64_t;

typedef __int32 int32_t;
typedef __int64 int64_t;

#else
#include <stdint.h>
#endif

/*
 * Future enhancements could include tests and branches to account for
 * variations in architecture.  However, the raw compressed data must
 * be 2's complement, big-endian, and sign in most significant bit.
 */

/*
 * return codes
 */
#define EC_SUCCESS      0
#define EC_FAILED       1
#define EC_LENGTH_ERROR 2
#define EC_SAMP_ERROR   3
#define EC_DIFF_ERROR   4
#define EC_CHECK_ERROR  5
#define EC_ARG_ERROR    6
#define EC_TYPE_ERROR   7
#define EC_MEMORY_ERROR 8

#ifndef EC_C
static char mess0[] = "operation succeeded";
static char mess1[] = "operation failed";
static char mess2[] = "number of bytes in data incorrect";
static char mess3[] = "number of samples in data incorrect";
static char mess4[] = "error in number of differences";
static char mess5[] = "check value (last sample in block) incorrect";
static char mess6[] = "error in arguments to function";
static char mess7[] = "datatype incorrect";
static char mess8[] = "memory allocation error";
static char *e_messages[] =
  {mess0, mess1, mess2, mess3, mess4, mess5, mess6, mess7, mess8};
#endif

/*
 * flags to determine handling of last block
 */
#define EC_FULL_END  0
#define EC_SHORT_END 1

/*
 * The largest compressed buffer size for e* or E* format is 16K bytes.
 * The maximum compression using e style compression is about 1 byte per sample.
 * Therefore, the maximum working buffer size would be about 16K 32bit ints.
 * (Best compression is 4 7-bit samples in 4 bytes, but there are still
 * the 8 bytes per block overhead).
 */
#define EC_MAX_BUFFER 16384

/*
 * The maximum number of differences allowed.
 * The time series is differenced at most this many times before
 * applying the bit-wise compression.
 */
#define EC_MAX_NDIFF 4

/*
 * functions
 */

 /*
  * The _declspec(dllexport) statement explicitly tells the compiler to send a function to the .dll.
  * This is done so that when PythonXX.lib is updated it knows how to find the appropriate functions
  * when referencing the .pyd.
  */
#ifdef _WIN32
    _declspec(dllexport) int32_t e_decomp(uint32_t *in, int32_t *out, int32_t is, int32_t ib, int32_t o0, int32_t os);
    _declspec(dllexport) int32_t e_comp(int32_t *in, uint32_t *out, int32_t is, int32_t *ob, char dt[], int32_t flag);
    _declspec(dllexport) int32_t e_decomp_inplace(int32_t *in, int32_t is, int32_t ib, int32_t o0, int32_t os);
    _declspec(dllexport) int32_t e_comp_inplace(int32_t *in, int32_t is, int32_t *ob, char dt[], int32_t flag);
#else
    int32_t e_decomp(uint32_t *in, int32_t *out, int32_t is, int32_t ib, int32_t o0, int32_t os);
    int32_t e_comp(int32_t *in, uint32_t *out, int32_t is, int32_t *ob, char dt[], int32_t flag);
    int32_t e_decomp_inplace(int32_t *in, int32_t is, int32_t ib, int32_t o0, int32_t os);
    int32_t e_comp_inplace(int32_t *in, int32_t is, int32_t *ob, char dt[], int32_t flag);
#endif


int32_t block_e_decomp(uint32_t *in, int32_t *out, int32_t *nsamp, int32_t *nbyte);

#endif EC_H
