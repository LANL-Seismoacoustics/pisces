void
s3tos4(byte, n)
void *byte;
register int n;
{
	/*
	 * note:
	 *    to use this routine, it is assumed byte is allocated
	 *    long enough and has the correct alignment
	 *
	 * args:
	 *    byte is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * how:
	 *    it copies the 2 lsb of the 3-byte to the 2 lsb of the 4-byte,
	 *    then can just copy the last byte into what correctly-aligned short
	 *    also, unroll and use direct addressing since it is more efficient.
	 */
	register char *p4;
	register char *p3;
	register short *s;
	
	s = (short *)byte;
	p4 = (char *)byte;
	p3 = (char *)byte;
	s += 2 * n;
	p4 += 4 * n;
	p3 += 3 * n;
	for (; n > 3; n -= 4) {
		s -= 8;
		p4 -= 16;
		p3 -= 12;
		p4[15] = p3[11];
		p4[14] = p3[10];
		s[6]   = p3[ 9];
		p4[11] = p3[ 8];
		p4[10] = p3[ 7];
		s[4]   = p3[ 6];
		p4[ 7] = p3[ 5];
		p4[ 6] = p3[ 4];
		s[2]   = p3[ 3];
		p4[ 3] = p3[ 2];
		p4[ 2] = p3[ 1];
		s[0]   = p3[ 0];
	}
	for (; n > 0; n--) {
		s -= 2;
		p4 -= 4;
		p3 -= 3;
		p4[ 3] = p3[ 2];
		p4[ 2] = p3[ 1];
		s[0]   = p3[ 0];
	}

	/* 
	 * what it looks like without direct addressing
	s = (short *)byte;
	s += 2 * n - 2;
	p4 = (char *)byte + 4 * n - 1;
	p3 = (char *)byte + 3 * n - 1;
	for (; n > 0; n--) {
		*p4-- = *p3--;
		*p4-- = *p3--;
		p4--;
		*p4-- = *p3--;
		*s >>= 8;
		s -= 2;
	}
	 */
}

void
s4tos3(byte, n)
void *byte;
register int n;
{
	/*
	 * NOTE - to use this routine, it is assumed that no value
	 * in the original 4-byte array exceeds 3 significant bytes of data
	 *
	 * args:
	 *    byte is the 4-byte aligned buffer of length at least 4 * n bytes
	 *    n is the number of values to be converted in place
	 *
	 * How:
	 *    it copies 3 lsb of the 4-byte to the 3-byte
	 *    also, unroll and use direct addressing since it is more efficient.
	 */
	register char *p4;
	register char *p3;
	
	p4 = (char *)byte;
	p3 = (char *)byte;
	for (; n > 3; n -= 4) {
		p3[ 0] = p4[ 1];
		p3[ 1] = p4[ 2];
		p3[ 2] = p4[ 3];
		p3[ 3] = p4[ 5];
		p3[ 4] = p4[ 6];
		p3[ 5] = p4[ 7];
		p3[ 6] = p4[ 9];
		p3[ 7] = p4[10];
		p3[ 8] = p4[11];
		p3[ 9] = p4[13];
		p3[10] = p4[14];
		p3[11] = p4[15];
		p4 += 16;
		p3 += 12;
	}
	for (; n > 0; n--) {
		p3[ 0] = p4[ 1];
		p3[ 1] = p4[ 2];
		p3[ 2] = p4[ 3];
		p4 += 4;
		p3 += 3;
	}

	/* 
	 * what it looks like without direct addressing
	p4 = byte + 1;
	p3 = byte;
	for (; n > 0; n--) {
		*p3++ = *p4++;
		*p3++ = *p4++;
		*p3++ = *p4++;
		p4++;
	}
	 */
}
