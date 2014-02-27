void
s2tos4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 4-byte boundary, correct alignment
	 *    is required.
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    it steps down from the end, converting to longs as it goes.
	 *    loop unrolled ten times for speed.
	 *    note - on most machines, the direct addressing is more efficient
	 *    than incrementing or decrementing the pointer at each sample.
	 *    On sparc, unrolling and then using direct addressing improves
	 *    efficiency by about a factor of 2.
	 */
	register long *l;
	register short *s;
	
	l = (long *)buf + n;
	s = (short *)buf + n;
	for (; n > 9; n -= 10) {
		l -= 10;
		s -= 10;
		l[9] = s[9];
		l[8] = s[8];
		l[7] = s[7];
		l[6] = s[6];
		l[5] = s[5];
		l[4] = s[4];
		l[3] = s[3];
		l[2] = s[2];
		l[1] = s[1];
		l[0] = s[0];
	}
	for (; n > 0; n--) {
		*--l = *--s;
	}
}

void
s4tos2(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    buf is assumed to start on an 4-byte boundary, correct alignment
	 *    is required.
	 *    note that s4 implicitly carries much more precision than s2.
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    just copies 2 lsb.  Tough luck if the number exceeds short.
	 *    note - on most machines, the direct addressing is more efficient
	 *    than incrementing or decrementing the pointer at each sample.
	 *    On sparc, unrolling and then using direct addressing improves
	 *    efficiency by about a factor of 2.
	 */
	register char *p4;
	register char *p2;
	
	p4 = (char *)buf;
	p2 = (char *)buf;
	for (; n > 4; n -= 5) {
		p2[0] = p4[ 2];
		p2[1] = p4[ 3];
		p2[2] = p4[ 6];
		p2[3] = p4[ 7];
		p2[4] = p4[10];
		p2[5] = p4[11];
		p2[6] = p4[14];
		p2[7] = p4[15];
		p2[8] = p4[18];
		p2[9] = p4[19];
		p2 += 10;
		p4 += 20;
	}
	for (; n > 0; n--) {
		p2[0] = p4[ 2];
		p2[1] = p4[ 3];
		p2 += 2;
		p4 += 4;
	}
}
