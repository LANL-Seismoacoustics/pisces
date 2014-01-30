#include "convert.h"

/*
	Floating Point conversion, IBM big-endian to IEEE big-endian

IBM big-endian representation (when stored on an IEEE machine):
	 0           7 8                                          31
	|s| exponent  | <------------- mantissa -------------->     |

An IBM float is constructed by 
                        s                  (exponent - 64)
		    (-1)  * 0.mantissa * 16

Remember, this is binary so the first bit of the mantissa is in the 'halves'
place (immediately after the binary point).  The mantissa is completely
justified, ie: the exponent has been manipulated until the number is
correctly represented by   0.xxx * 16 ** (exponent - 64).

IEEE representation:
	 0               8 9                                      31
	|s|   exponent    | <------------- mantissa --------------> |

The least significant mantissa bit is bit 31, the most significant is bit 9.
A IEEE float is constructed by 
                        s                 (exponent - 127)
		    (-1)  * 1.mantissa * 2

The main difference here is the form of the mantissa (IEEE drops the
leading 1 - it's implied), the use of a binary rather than the
hexadecimal exponent used by IBM, and the excess valuation of the exponent.

Note that the exponent can be much greater for IBM than for IEEE.
Essentially, IBM can have an exponent of 2^-256 to 2^+252, while
IEEE goes from 2^-127 to 2^128.  Clearly, there is a large range
of IBM single-precision that can only be represented as IEEE double
precision.  In this routine, we will assume that the range of IEEE
is not exceeded.  No attempt will be amde to deal with IEEE
NaN, Inexact or Overflow.

The procedure to follow is this:
1) shift the IBM exponent left 2 bits.  This multiplies by 4 and
   account for the difference between the hexadecimal and binary exponents.
2) subtract 129 from the exponent.  This accounts for the power-of-2
   difference in the exponent bias (IBM uses 64 in hex, which is 256
   in binary, IEEE uses 127).
3) shift the mantissa left until the left-most bit is 1.  Then shift once
   more (dropping the leading 1).  For each shift, subtract 1 from the
   exponent.
*/

void
b4tot4(void *buf, int n)
{
  register unsigned long tmpsign, tmpexp;
  register unsigned long *u = (unsigned long *)buf;

  /* makes several assumptions, particularly regarding exponent overflow */

  for (; n > 0; n--) {
    /* special case for 0 */
    if (! *u) {
      u++;
      continue;
    }

    /* save sign */
    tmpsign = *u & 0x80000000;

    /* extract exponent, correct bias */
    tmpexp = ((*u & 0x7f000000) >> 22) - 129;

    /* extract mantissa, shift leading 1 off */
    *u &= 0x00ffffff;
    *u <<= 8;
    while (!(*u & 0x80000000)) {
      *u <<= 1;
      tmpexp -= 1;
    }
    *u <<= 1;
    tmpexp -= 1;

    /* construct final value */
    *u >>= 9;
    *u |= (tmpexp << 23) | tmpsign;

    u++;
  }
}

void
t4tob4(void *buf, int n)
{
  register unsigned long tmpsign, tmpexp;
  register unsigned long *u = (unsigned long *)buf;

  /* makes several assumptions */

  for (; n > 0; n--) {
    /* special case for 0 */
    if (! *u) {
      u++;
      continue;
    }

    /* save sign */
    tmpsign = *u & 0x80000000;

    /* extract exponent, correct bias */
    tmpexp = ((*u & 0x7f800000) >> 23) + 129;

    /* extract mantissa, add leading 1 */
    *u &= 0x007fffff;
    *u |= 0x00800000;
/*
    *u >>= 1;
*/
    tmpexp += 1;

    switch (tmpexp & 0x00000003) {
    case 0:
/*
      if (!(tmpexp & 0x00000004)) {
        tmpexp += 4;
        *u >>= 4;
      }
      if (!(tmpexp & 0x00000004)) {
        tmpexp += 4;
        *u >>= 4;
      }
*/
      break;
    case 1:
      tmpexp += 3;
      *u >>= 3;
      break;
    case 2:
      tmpexp += 2;
      *u >>= 2;
      break;
    case 3:
      tmpexp++;
      *u >>= 1;
      break;
    }

    /* construct final value */
    *u |= (tmpexp << 22) | tmpsign;

    u++;
  }
}
