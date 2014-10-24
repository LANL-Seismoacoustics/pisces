#include "convert.h"

/*
	Floating Point conversion, VAX to IEEE:

VAX representation (when stored on an IEEE machine):
	 0           6 7            14 15 16            23 24     31
	|  mantissa   |  exponent     | s|    mantissa              |

The least significant mantissa bit is bit 23, the most significant is bit 0.
A VAX float is constructed by 
                        s                  (exponent - 128)
		    (-1)  * 0.1mantissa * 2

Remember, this is binary so the '1' before the mantissa is in the 'halves'
place (immediately after the binary point).  The mantissa is completely
justified, ie: the exponent has been manipulated until the number is
correctly represented by   0.1... * 2 ** (exponent - 128).  For completely
justified binary mantissas, there is always a bit on in the halves places,
so it can be dropped (assumed).

IEEE representation:
	 0               8 9                                      31
	|s|   exponent    | <------------- mantissa --------------> |

The least significant mantissa bit is bit 31, the most significant is bit 9.
A VAX float is constructed by 
                        s                 (exponent - 127)
		    (-1)  * 1.mantissa * 2

The main difference here is the form of the mantissa (justification now
occurs in the one's place), and the excess valuation of the exponent.
Combined, this is a factor of 4, which is correctly represented by
adding 2 to the VAX exponent to get the IEEE exponent, leaving the
mantissa unchanged.  This works except for small numbers (exponents
of 1 or 2, that is 2**-127 and 2**-126), and for zero (which must
remain unchanged).
   case 0:
case 0 is an exponent of zero.  This is special to both VAX
and IEEE representations.  If all bytes in the number are
zero, the number is a floating point zero.  All other numbers
with exponent zero are RESERVED OPERANDS.  On the VAX, these
are error designations.  Under IEEE, they are values of special
meaning including:  Infinity, NotANumber, and Inexact.
These subroutines assume no knowledge of special designations,
and therefore turn all zero-exponent values to true zero.
   case 1:
   case 2:
These are values properly represented on the VAX which are too
small to properly represent under IEEE (Underflow). They
could be set to 'Inexact' (the proper IEEE designation),
but it would cause more problems than it would fix

The converse is true going from IEEE to VAX, large numbers correctly
represented under IEEE will fail (Overflow) on the VAX.

Double precision has a longer mantissa (4 more bytes tacked on from
bit 32 to bit 63).  The VAX mantissa remains byte-reversed (LSB at bit
55).  The exponent can change length.  The VAX has two double precision
representations: 8-bit exponent and 11-bit exponent.  IEEE has only one:
11-bit.  The extra 3 bits are placed where the most significant 3 bits
of the mantissa were, the mantissa is shifted over appropriately.
*/

void
t8tof8(buf, n)                   /* This routine works on vax 'G' format */
void *buf;
register int n;
{
	register unsigned char *u;
	register unsigned char temp;
	union {
		unsigned short s;
		unsigned char c[2];
	} exp_test;

	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		exp_test.c[0] = u[0];
		exp_test.c[1] = u[1];

		if ((exp_test.s & (unsigned short)0x7ff0) >
			(unsigned short)0x7fe0) {
			/*
			 * This takes care of the overflow cases
			 */
			u[0] = 0xff;
			u[1] = 0x7f;
			u[2] = 0xff;
			u[3] = 0xff;
			u[4] = 0xff;
			u[5] = 0xff;
			u[6] = 0xff;
			u[7] = 0xff;
			u += 8;
			continue;
		}
		exp_test.s += (short)0x0020;

		u[0] = exp_test.c[1];
		u[1] = exp_test.c[0];

		/*
		 * finish swapping the mantissa
		 */
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		temp = u[4];
		u[4] = u[5];
		u[5] = temp;
		temp = u[6];
		u[6] = u[7];
		u[7] = temp;
		u += 8;
	}
}

void
f8tot8(buf, n)                   /* This routine works on vax 'G' format */
void *buf;
register int n;
{
	register unsigned char *u;
	register unsigned char temp;
	union {
		unsigned short s;
		unsigned char c[2];
	} exp_test;

	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		exp_test.c[0] = u[1];
		exp_test.c[1] = u[0];

		if ((exp_test.s & (unsigned short)0x7ff0) <
			(unsigned short)0x0030) {
			/*
			 * This takes care of the three special cases
			 * 0, 0x0010, 0x0020
			 */
			u[0] = 0;
			u[1] = 0;
			u[2] = 0;
			u[3] = 0;
			u[4] = 0;
			u[5] = 0;
			u[6] = 0;
			u[7] = 0;
			u += 8;
			continue;
		}

		exp_test.s -= (short)0x0020;
		u[0] = exp_test.c[0];
		u[1] = exp_test.c[1];

		/*
		 * finish swapping the mantissa
		 */
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		temp = u[4];
		u[4] = u[5];
		u[5] = temp;
		temp = u[6];
		u[6] = u[7];
		u[7] = temp;
		u += 8;
	}
}

void
f8Dtot8(buf, n)                   /* This routine works on vax 'D' format */
void *buf;
register int n;
/*
 * There is no way to do this fast
 */
{
	register unsigned char *u;
	register unsigned char save;
	union {
		unsigned long l;
		unsigned char c[4];
	} exp_test;

	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		exp_test.c[0] = u[1];
		exp_test.c[1] = u[0];
		exp_test.c[2] = u[3];
		exp_test.c[3] = u[2];

		if ((exp_test.l & 0x7f800000) < 0x01800000) {
			/*
			 * This takes care of the three special cases
			 * 0, 0x00800000, 0x01000000
			 * (could turn them into inexacts, but that
			 * causes problems, too)
			 */
			u[0] = 0;
			u[1] = 0;
			u[2] = 0;
			u[3] = 0;
			u[4] = 0;
			u[5] = 0;
			u[6] = 0;
			u[7] = 0;
			u += 8;
			continue;
		}

		/*
		 * allow for factor of four
		 */
		exp_test.l -= 0x01000000;

		/*
		 * shift exponent, but keep sign bit in the same place
		 */
		exp_test.l = ((exp_test.l & 0x7fffffff) >> 3) |
			      (exp_test.l & 0x80000000);

		/*
		 * correct exponent bias from 127 to 1023
		 */
		exp_test.l += 0x38000000;

		/*
		 * save mantissa bits about to be axed
		 */
		save = u[2] << 5;

		u[0] = exp_test.c[0];
		u[1] = exp_test.c[1];
		u[2] = exp_test.c[2];
		u[3] = exp_test.c[3];

		/*
		 * reconstruct the rest, losing 3 bits precision
		 */
		exp_test.c[0] = u[5];
		exp_test.c[1] = u[4];
		exp_test.c[2] = u[7];
		exp_test.c[3] = u[6];
		exp_test.l >>= 3;
		u[4] = exp_test.c[0] | save;
		u[5] = exp_test.c[1];
		u[6] = exp_test.c[2];
		u[7] = exp_test.c[3];
	}
}

void
t4tof4(buf, n)                /* fast, but sloppy */
void *buf;
int n;
{
	register unsigned char temp;
	register unsigned char *u;

	/*
	 * for a slightly faster, sloppier routine, remove the '& 0x7f'
	 * (would assume there are no values "-0", which cannot be guaranteed)
	 */
	
	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		temp = ((*u & 0x7f) ? ++(*u) : *u);
		u[0] = u[1];
		u[1] = temp;
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		u += 4;
	}
}

void
f4tot4(buf, n)                /* fast, but sloppy */
void *buf;
int n;
{
	register unsigned char temp;
	register unsigned char *u;

	/*
	 * for a slightly faster, sloppier routine, remove the '& 0x7f'
	 * (would assume there are no values "-0", which cannot be guaranteed)
	 */
	
	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		temp = u[0];
		u[0] = ((u[1] & 0x7f) ? --(u[1]) : u[1]);
		u[1] = temp;
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		u += 4;
	}
}

void
t4tof4x(buf, n)               /* slower, but correct */
void *buf;
int n;
{
	register unsigned char temp;
	register unsigned char *u;

	u = (unsigned char *)buf;

	for (; n > 0; n--) {
		temp = u[0] << 1;
		temp |= (u[1] & (unsigned char)0x80) >> (unsigned char)7;
		if (!temp) {
			/*
			 * set anything like zero or inexact
			 * to exactly zero
			 */
			u[0] = 0;
			u[1] = 0;
			u[2] = 0;
			u[3] = 0;
			u += 4;
			continue;
		}
		if (temp > 0xfd) {
			/*
			 * set overflow to infinity
			 */
			u[0] = 0xff;
			u[1] = 0x7f;
			u[2] = 0xff;
			u[3] = 0xff;
			u += 4;
			continue;
		}

		temp = ++(u[0]);
		u[0] = u[1];
		u[1] = temp;
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		u += 4;
	}
}

void
f4tot4x(buf, n)                /* slower, but correct */
void *buf;
int n;
{
	register unsigned char temp;
	register unsigned char *u;

	u = (unsigned char *)buf;

	/*
	 * strictly speaking, 0xffffffff and 0xff7fffff should
	 * convert to infinity, not valid values as below
	 * (they end up as 0xfeffffff and 0x7effffff)
	 */
	for (; n > 0; n--) {
		if ((u[1] & (unsigned char)0x7f) < (unsigned char)0x02 &&
			!(u[0] & (unsigned char)0x80)) {
			/*
			 * set anything like zero or inexact
			 * to exactly zero
			 */
			u[0] = 0;
			u[1] = 0;
			u[2] = 0;
			u[3] = 0;
			u += 4;
			continue;
		}
		temp = u[0];
		u[0] = --(u[1]);
		u[1] = temp;
		temp = u[2];
		u[2] = u[3];
		u[3] = temp;
		u += 4;
	}
}

void
f4tot8(buf, n)
void *buf;
int n;
{
	f4tot4(buf, n);
	t4tot8(buf, n);
}

void
f8tot4(buf, n)
void *buf;
int n;
{
	f8tot8(buf, n);
	t8tot4(buf, n);
}

void
t4tof8(buf, n)
void *buf;
int n;
{
	t4tot8(buf, n);
	t8tof8(buf, n);
}

void
t8tof4(buf, n)
void *buf;
int n;
{
	t8tot4(buf, n);
	t4tof4(buf, n);
}
