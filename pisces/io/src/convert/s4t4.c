void
s4tot4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    a loss of precision is possible, since s4 theoretically provides
	 *    32 significant bits, and t4 only 23.
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    it just converts the long to a float, then replaces the existing
	 *    value in place.  Loop is unrolled a factor of 10 for speed.
	 */
	register float *f;
	register long *l;
	
	f = (float *)buf;
	l = (long *)buf;

	for (; n > 9; n -= 10) {
		f[0] = (float)l[0];
		f[1] = (float)l[1];
		f[2] = (float)l[2];
		f[3] = (float)l[3];
		f[4] = (float)l[4];
		f[5] = (float)l[5];
		f[6] = (float)l[6];
		f[7] = (float)l[7];
		f[8] = (float)l[8];
		f[9] = (float)l[9];
		f += 10;
		l += 10;
	}
	for (; n > 0; n--) {
		*f++ = (float)*l++;
	}
}

void
t4tos4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    does not check for overflow - floats must be in range for
	 *    longs.
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    it just converts the float to a long, then replaces the existing
	 *    value in place.  Loop is unrolled a factor of 10 for speed.
	 */
	register float *f;
	register long *l;
	
	f = (float *)buf;
	l = (long *)buf;

	for (; n > 9; n -= 10) {
		l[0] = (long)f[0];
		l[1] = (long)f[1];
		l[2] = (long)f[2];
		l[3] = (long)f[3];
		l[4] = (long)f[4];
		l[5] = (long)f[5];
		l[6] = (long)f[6];
		l[7] = (long)f[7];
		l[8] = (long)f[8];
		l[9] = (long)f[9];
		f += 10;
		l += 10;
	}
	for (; n > 0; n--) {
		*l++ = (long)*f++;
	}
}
