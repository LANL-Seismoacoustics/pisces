void
i2tos2(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    the i2 -> s2 operation is the same as s2 -> i2
	 *
	 * args:
	 *    buf is the 2-byte aligned buffer of length at least 2 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    changes byte order from 0 1 2 3 to 1 0 3 2.
	 *    unroll and use direct addressing for efficiency.
	 */
	register char *u;
	register char temp;
	
	u = (char *)buf;

	for (; n > 9; n -= 10) {
		temp  = u[ 0];
		u[ 0] = u[ 1];
		u[ 1] = temp;
		temp  = u[ 2];
		u[ 2] = u[ 3];
		u[ 3] = temp;
		temp  = u[ 4];
		u[ 4] = u[ 5];
		u[ 5] = temp;
		temp  = u[ 6];
		u[ 6] = u[ 7];
		u[ 7] = temp;
		temp  = u[ 8];
		u[ 8] = u[ 9];
		u[ 9] = temp;
		temp  = u[10];
		u[10] = u[11];
		u[11] = temp;
		temp  = u[12];
		u[12] = u[13];
		u[13] = temp;
		temp  = u[14];
		u[14] = u[15];
		u[15] = temp;
		temp  = u[16];
		u[16] = u[17];
		u[17] = temp;
		temp  = u[18];
		u[18] = u[19];
		u[19] = temp;
		u += 20;
	}
	for (; n > 0; n--) {
		temp  = u[ 0];
		u[ 0] = u[ 1];
		u[ 1] = temp;
		u += 2;
	}
}

void
s2toi2(buf, n)
void *buf;
int n;
{
	i2tos2(buf, n);
}
