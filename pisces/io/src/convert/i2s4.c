void
i2tos4(buf, n)
void *buf;
register int n;
{
	/*
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    swaps byte order, then right shifts.  (Right shift is faster
	 *    than the system's conversion from short to long, provided the
	 *    bytes to be shifted are already in the right place).
	 *    unroll and use direct addressing for efficiency.
	 */
	register char *p4;
	register char *p2;
	register long *l;
	
	l = (long *)buf;
	p2 = (char *)buf;
	p4 = (char *)buf;
	p2 += 2 * n;
	p4 += 4 * n;

	for (; n > 9; n -= 10) {
		l -= 10;
		p2 -= 20;
		p4 -= 40;
		p4[37] = p2[18];
		p4[36] = p2[19];
		l[9] >>= 16;
		p4[33] = p2[16];
		p4[32] = p2[17];
		l[8] >>= 16;
		p4[29] = p2[14];
		p4[28] = p2[15];
		l[7] >>= 16;
		p4[25] = p2[12];
		p4[24] = p2[13];
		l[6] >>= 16;
		p4[21] = p2[10];
		p4[20] = p2[11];
		l[5] >>= 16;
		p4[17] = p2[ 8];
		p4[16] = p2[ 9];
		l[4] >>= 16;
		p4[13] = p2[ 6];
		p4[12] = p2[ 7];
		l[3] >>= 16;
		p4[ 9] = p2[ 4];
		p4[ 8] = p2[ 5];
		l[2] >>= 16;
		p4[ 5] = p2[ 2];
		p4[ 4] = p2[ 3];
		l[1] >>= 16;
		p4[ 1] = p2[ 0];
		p4[ 0] = p2[ 1];
		l[0] >>= 16;
	}
	for (; n > 0; n--) {
		p4 -= 4;
		p2 -= 2;
		p4[ 1] = p2[ 0];
		p4[ 0] = p2[ 1];
		*--l >>= 16;
	}
}

void
s4toi2(buf, n)
void *buf;
int n;
{
	/*
	 * note:
	 *    s4 has implicitly greater precision than i2.  This routine
	 *    does not check this before conversion.
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    swaps byte order, then right shifts.  (Right shift is faster
	 *    than the system's conversion from short to long, provided the
	 *    bytes to be shifted are already in the right place).
	 *    unroll and use direct addressing for efficiency.
	 */
	register char *p2;
	register char *p4;
	
	p2 = (char *)buf;
	p4 = (char *)buf;

	for (; n > 9; n -= 10) {
		p2[ 0] = p4[ 1];
		p2[ 1] = p4[ 0];
		p2[ 2] = p4[ 5];
		p2[ 3] = p4[ 4];
		p2[ 4] = p4[ 9];
		p2[ 5] = p4[ 8];
		p2[ 6] = p4[13];
		p2[ 7] = p4[12];
		p2[ 8] = p4[17];
		p2[ 9] = p4[16];
		p2[10] = p4[21];
		p2[11] = p4[20];
		p2[12] = p4[25];
		p2[13] = p4[24];
		p2[14] = p4[29];
		p2[15] = p4[28];
		p2[16] = p4[33];
		p2[17] = p4[32];
		p2[18] = p4[37];
		p2[19] = p4[36];
		p2 += 20;
		p4 += 40;
	}
	for (; n > 0; n--) {
		p2[ 0] = p4[ 1];
		p2[ 1] = p4[ 0];
		p4 += 4;
		p2 += 2;
	}
}
