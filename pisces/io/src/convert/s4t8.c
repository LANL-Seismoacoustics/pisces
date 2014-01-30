void
s4tot8(buf, n)
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
	register long *l;
	
	d = (double *)buf;
	l = (long *)buf;
	d += n;
	l += n;
	for (; n > 9; n -= 10) {
		d -= 10;
		l -= 10;
		d[9] = (double)l[9];
		d[8] = (double)l[8];
		d[7] = (double)l[7];
		d[6] = (double)l[6];
		d[5] = (double)l[5];
		d[4] = (double)l[4];
		d[3] = (double)l[3];
		d[2] = (double)l[2];
		d[1] = (double)l[1];
		d[0] = (double)l[0];
	}
	for (; n > 0; n--) {
		*--d = (double)*--l;
	}
}

void
t8tos4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 8-byte boundary, correct alignment
	 *    is required.
	 *    note that t8 implicitly carries much more precision than s4.
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
	register long *l;
	
	d = (double *)buf;
	l = (long *)buf;
	for (; n > 9; n -= 10) {
		l[0] = (long)d[0];
		l[1] = (long)d[1];
		l[2] = (long)d[2];
		l[3] = (long)d[3];
		l[4] = (long)d[4];
		l[5] = (long)d[5];
		l[6] = (long)d[6];
		l[7] = (long)d[7];
		l[8] = (long)d[8];
		l[9] = (long)d[9];
		l += 10;
		d += 10;
	}
	for (; n > 0; n--) {
		*l++ = (long)*d++;
	}
}
