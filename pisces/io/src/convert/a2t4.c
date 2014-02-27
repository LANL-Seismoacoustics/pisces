#include "convert.h"

/* 
 *  a2tot4 converts aftac gain-ranged format to ieee longs
 */

void
a2tot4(buf, n)
void *buf;
register int n;
{
	register float *f;
	register long *l;
	register unsigned short *s;
	register unsigned short *u;

	f = (float *)buf;
	l = (long *)buf;
	s = (unsigned short *)buf;
	u = (unsigned short *)buf;
	f += n;
	l += n;
	s += n;
	u += 2 * n;
	for (; n > 1; n--) {
		f--;
		l--;
		s--;
		u -= 2;

		*u = *s << 3;
		u[1] = (short)0;
		*l >>= (long)5 + (long)((*s & (unsigned short)0xe000) >>
			(unsigned short)12);
		*f = (float)*l / (float)8.0;
	}

	/*
	 * first sample requires more care (to save exponent bits in place)
	 */
	f--;
	l--;
	s--;
	u -= 2;

	n = 5 + (int)((*s & (unsigned short)0xe000) >> (unsigned short)12);
	*u <<= 3;
	u[1] = (short)0;
	*l >>= n;
	*f = (float)*l / (float)8.0;
}

/* 
 *  t4toa2 converts from ieee integer to aftac gain ranged format
 */

void
t4toa2(buf, n)
void *buf;
register int n;
{
#ifdef OLDWAY
	register float *f;
	register long *l;
	register unsigned short *s;
	register unsigned short *u;

	f = (float *)buf;
	l = (long *)buf;
	s = (unsigned short *)buf;
	u = (unsigned short *)buf;

	for (; n > 0; n--, f++, l++, s++, u += 2) {
		/*
		 * check for range, set to max if out of range
		 * (range is -2^23 to 2^23 - 1)
		 */
		if (*f > 8388607) {*s = 0xefff; continue;}
		if (*f < -8388608) {*s = 0xffff; continue;}

		*l = (long)(*f * (float)8.0);
		*l <<= 5;

		/*
		 * find gain, process, then continue
		 * gain goes 2 bits at a time.  If three adjacent bits
		 * are the same, then sign is preserved when two bits
		 * are removed.  Otherwise, no further gain possible
		 */
		if ((*u & 0xe000) != 0xe000 && (*u & 0xe000) != 0) {
			*u >>= 3;
			*s = *u;
			continue;
		}
		if ((*u & 0xf800) != 0xf800 && (*u & 0xf800) != 0) {
			*l <<= 2;
			*u >>= 3;
			*u |= 0x2000;
			*s = *u;
			continue;
		}
		if ((*u & 0xfe00) != 0xfe00 && (*u & 0xfe00) != 0) {
			*l <<= 4;
			*u >>= 3;
			*u |= 0x4000;
			*s = *u;
			continue;
		}
		if ((*u & 0xff80) != 0xff80 && (*u & 0xff80) != 0) {
			*l <<= 6;
			*u >>= 3;
			*u |= 0x6000;
			*s = *u;
			continue;
		}
		if ((*u & 0xffe0) != 0xffe0 && (*u & 0xffe0) != 0) {
			*l <<= 8;
			*u >>= 3;
			*u |= 0x8000;
			*s = *u;
			continue;
		}
		if ((*u & 0xfff8) != 0xfff8 && (*u & 0xfff8) != 0) {
			*l <<= 10;
			*u >>= 3;
			*u |= 0xa000;
			*s = *u;
			continue;
		}
		if ((*u & 0xfffe) != 0xfffe && (*u & 0xfffe) != 0) {
			*l <<= 12;
			*u >>= 3;
			*u |= 0xc000;
			*s = *u;
			continue;
		}
		*l <<= 14;
		*u >>= 3;
		*u |= 0xe000;
		*s = *u;
	}
#else
	register float *f;
	register long *l;
	register short *s;
	register short *u;
	register unsigned short test = 0xfffe;

	f = (float *)buf;
	l = (long *)buf;
	s = (short *)buf;
	u = (short *)buf;

	for (; n > 0; n--, f++, l++, s++, u += 2) {
		/*
		 * check for range, set to max if out of range
		 * (range is -2^23 to 2^23 - 1)
		 */
		if (*f > 8388607) {*s = 0xefff; continue;}
		if (*f < -8388608) {*s = 0xffff; continue;}

		*l = (long)(*f * (float)8.0);
		*l <<= 5;

		/*
		 * trick - sign-extended shift the first halfword such
		 * that the halfword must be 0 (0x0000) or -1 (0xffff)
		 * at that gain range.  Add 1, then verify that all but
		 * the last bit are zero (1, 0x0001 or 0, 0x0000)
		 * should be a fast test.
		 */
		if (!(((*u >> (short)1) + (short)1) & test)) {
			*l <<= 11;
			*s = (*u & (short)0x1fff) | (short)0xe000;
			continue;
		}
		if (!(((*u >> (short)3) + (short)1) & test)) {
			*l <<= 9;
			*s = (*u & (short)0x1fff) | (short)0xc000;
			continue;
		}
		if (!(((*u >> (short)5) + (short)1) & test)) {
			*l <<= 7;
			*s = (*u & (short)0x1fff) | (short)0xa000;
			continue;
		}
		if (!(((*u >> (short)7) + (short)1) & test)) {
			*l <<= 5;
			*s = (*u & (short)0x1fff) | (short)0x8000;
			continue;
		}
		if (!(((*u >> (short)9) + (short)1) & test)) {
			*l <<= 3;
			*s = (*u & (short)0x1fff) | (short)0x6000;
			continue;
		}
		if (!(((*u >> (short)11) + (short)1) & test)) {
			*l <<= 1;
			*s = (*u & (short)0x1fff) | (short)0x4000;
			continue;
		}
		if (!(((*u >> (short)13) + (short)1) & test)) {
			*l >>= 1;
			*s = (*u & (short)0x1fff) | (short)0x2000;
			continue;
		}
		*u >>= 3;
		*s = *u & (short)0x1fff;
	}
#endif
}

void
a2tot8(buf, n)
void *buf;
int n;
{
	a2tot4(buf, n);
	t4tot8(buf, n);
}

void
t8toa2(buf, n)
void *buf;
int n;
{
	t8tot4(buf, n);
	t4toa2(buf, n);
}
