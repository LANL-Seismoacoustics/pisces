void
t4tot8(buf, n)
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
	register float *f;
	
	d = (double *)buf;
	f = (float *)buf;
	d += n;
	f += n;
	for (; n > 9; n -= 10) {
		d -= 10;
		f -= 10;
		d[9] = (double)f[9];
		d[8] = (double)f[8];
		d[7] = (double)f[7];
		d[6] = (double)f[6];
		d[5] = (double)f[5];
		d[4] = (double)f[4];
		d[3] = (double)f[3];
		d[2] = (double)f[2];
		d[1] = (double)f[1];
		d[0] = (double)f[0];
	}
	for (; n > 0; n--) {
		*--d = (double)*--f;
	}
}

void
t8tot4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 8-byte boundary, correct alignment
	 *    is required.
	 *    note that t8 implicitly carries much more precision than t4.
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
	register float *f;
	
	d = (double *)buf;
	f = (float *)buf;
	for (; n > 9; n -= 10) {
		f[0] = (float)d[0];
		f[1] = (float)d[1];
		f[2] = (float)d[2];
		f[3] = (float)d[3];
		f[4] = (float)d[4];
		f[5] = (float)d[5];
		f[6] = (float)d[6];
		f[7] = (float)d[7];
		f[8] = (float)d[8];
		f[9] = (float)d[9];
		f += 10;
		d += 10;
	}
	for (; n > 0; n--) {
		*f++ = (float)*d++;
	}
}
