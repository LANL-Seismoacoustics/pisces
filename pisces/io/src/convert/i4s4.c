void
i4tos4(buf, n)
void *buf;
register int n;
{
	/*
	 * note:
	 *    the i4 -> s4 operation is the same as s4 -> i4
	 *
	 * args:
	 *    buf is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    changes byte order from 0 1 2 3 to 3 2 1 0.
	 *    unroll and use direct addressing for efficiency.
	 */
	register char *u;
	register char temp;
	
	u = (char *)buf;

	for (; n > 4; n -= 5) {
		temp  = u[ 0];
		u[ 0] = u[ 3];
		u[ 3] = temp;
		temp  = u[ 1];
		u[ 1] = u[ 2];
		u[ 2] = temp;

		temp  = u[ 4];
		u[ 4] = u[ 7];
		u[ 7] = temp;
		temp  = u[ 5];
		u[ 5] = u[ 6];
		u[ 6] = temp;

		temp  = u[ 8];
		u[ 8] = u[11];
		u[11] = temp;
		temp  = u[ 9];
		u[ 9] = u[10];
		u[10] = temp;

		temp  = u[12];
		u[12] = u[15];
		u[15] = temp;
		temp  = u[13];
		u[13] = u[14];
		u[14] = temp;

		temp  = u[16];
		u[16] = u[19];
		u[19] = temp;
		temp  = u[17];
		u[17] = u[18];
		u[18] = temp;

		u += 20;
	}
	for (; n > 0; n--) {
		temp  = u[ 0];
		u[ 0] = u[ 3];
		u[ 3] = temp;
		temp  = u[ 1];
		u[ 1] = u[ 2];
		u[ 2] = temp;

		u += 4;
	}
}

void
s4toi4(buf, n)
void *buf;
int n;
{
	i4tos4(buf, n);
}
