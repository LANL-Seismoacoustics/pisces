void
s2tot8(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 8-byte boundary, correct alignment
	 *    is required.
	 *
	 * args:
	 *    buf is the 8-byte aligned buffer of length at least 8 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    it steps down from the end, converting to doubles as it goes.
	 *    loop unrolled ten times for speed.
	 *    note - on most machines, the direct addressing is more efficient
	 *    than incrementing or decrementing the pointer at each sample.
	 *    On sparc, unrolling and then using direct addressing improves
	 *    efficiency by about a factor of 2.
	 */
	register double *d;
	register short *s;
	
	d = (double *)buf;
	s = (short *)buf;
	d += n;
	s += n;
	for (; n > 9; n -= 10) {
		d -= 10;
		s -= 10;
		d[9] = (double)s[9];
		d[8] = (double)s[8];
		d[7] = (double)s[7];
		d[6] = (double)s[6];
		d[5] = (double)s[5];
		d[4] = (double)s[4];
		d[3] = (double)s[3];
		d[2] = (double)s[2];
		d[1] = (double)s[1];
		d[0] = (double)s[0];
	}
	for (; n > 0; n--) {
		*--d = (double)*--s;
	}
}

void
t8tos2(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 8-byte boundary, correct alignment
	 *    is required.
	 *    note that t8 implicitly carries much more precision than s2.
	 *
	 * args:
	 *    buf is the 8-byte aligned buffer of length at least 8 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    note - on most machines, the direct addressing is more efficient
	 *    than incrementing or decrementing the pointer at each sample.
	 *    On sparc, unrolling and then using direct addressing improves
	 *    efficiency by about a factor of 2.
	 */
	register double *d;
	register short *s;
	
	d = (double *)buf;
	s = (short *)buf;
	for (; n > 9; n -= 10) {
		s[0] = (short)d[0];
		s[1] = (short)d[1];
		s[2] = (short)d[2];
		s[3] = (short)d[3];
		s[4] = (short)d[4];
		s[5] = (short)d[5];
		s[6] = (short)d[6];
		s[7] = (short)d[7];
		s[8] = (short)d[8];
		s[9] = (short)d[9];
		s += 10;
		d += 10;
	}
	for (; n > 0; n--) {
		*s++ = (short)*d++;
	}
}
