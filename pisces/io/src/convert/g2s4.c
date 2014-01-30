/*
 * interpret gain bits:
 *
 * gain		mult	bit shift
 *  00		   1		0
 *  01		   4		2
 *  10		  16		4
 *  11		 128		7
 */
static unsigned short gain[4] = {0, 2, 4, 7};

void
g2tos4(buf, n)
void *buf;
register int n;
{
	register unsigned short *s;
	register long *l;
	register unsigned short u3fff = (unsigned short)0x3fff;
	register unsigned short u1fff = (unsigned short)0x1fff;
	register unsigned short uc000 = (unsigned short)0xc000;

	s = (unsigned short *)buf;
	l = (long *) buf;
	s += n;
	l += n;

	for (; n > 9; n -= 10) {
		s -= 10;
		l -= 10;
		l[9] = ((s[9] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[9] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[8] = ((s[8] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[8] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[7] = ((s[7] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[7] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[6] = ((s[6] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[6] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[5] = ((s[5] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[5] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[4] = ((s[4] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[4] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[3] = ((s[3] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[3] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[2] = ((s[2] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[2] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[1] = ((s[1] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[1] & (unsigned short)0xc000)
			>> (unsigned short)14];
		l[0] = ((s[0] & (unsigned short)0x3fff) -(unsigned short)0x1fff)
			<< gain[(s[0] & (unsigned short)0xc000)
			>> (unsigned short)14];
	}
	for (; n > 0; n--) {
		s--;
		l--;
		*l = ((*s & (unsigned short)0x3fff) - (unsigned short)0x1fff)
			<< gain[(*s & (unsigned short)0xc000)
			>>  (unsigned short)14];
	}
}

void
s4tog2(buf, n)
void *buf;
register int n;
{
	register unsigned short *s;
	register long *l;
	register long temp;

	s = (unsigned short *)buf;
	l = (long *) buf;

	/*
	 * bias is 8191, but round rather than truncate, so for
	 * bias before shift, set bias bits, then 0111... as needed
	 */
	for (; n > 4; n -= 5) {
		     if ((temp = (l[0] + 0x00001fff) & 0x7fffffff) < 0x00004000)
			s[0] =  temp;
		else if ((temp = (l[0] + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			s[0] = (temp >> 2) | 0x4000;
		else if ((temp = (l[0] + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			s[0] = (temp >> 4) | 0x8000;
		else if ((temp = (l[0] + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			s[0] = (temp >> 7) | 0xc000;
		else    s[1] = 0xffff;
		     if ((temp = (l[1] + 0x00001fff) & 0x7fffffff) < 0x00004000)
			s[1] =  temp;
		else if ((temp = (l[1] + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			s[1] = (temp >> 2) | 0x4000;
		else if ((temp = (l[1] + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			s[1] = (temp >> 4) | 0x8000;
		else if ((temp = (l[1] + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			s[1] = (temp >> 7) | 0xc000;
		else    s[1] = 0xffff;
		     if ((temp = (l[2] + 0x00001fff) & 0x7fffffff) < 0x00004000)
			s[2] =  temp;
		else if ((temp = (l[2] + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			s[2] = (temp >> 2) | 0x4000;
		else if ((temp = (l[2] + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			s[2] = (temp >> 4) | 0x8000;
		else if ((temp = (l[2] + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			s[2] = (temp >> 7) | 0xc000;
		else    s[2] = 0xffff;
		     if ((temp = (l[3] + 0x00001fff) & 0x7fffffff) < 0x00004000)
			s[3] =  temp;
		else if ((temp = (l[3] + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			s[3] = (temp >> 2) | 0x4000;
		else if ((temp = (l[3] + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			s[3] = (temp >> 4) | 0x8000;
		else if ((temp = (l[3] + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			s[3] = (temp >> 7) | 0xc000;
		else    s[3] = 0xffff;
		     if ((temp = (l[4] + 0x00001fff) & 0x7fffffff) < 0x00004000)
			s[4] =  temp;
		else if ((temp = (l[4] + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			s[4] = (temp >> 2) | 0x4000;
		else if ((temp = (l[4] + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			s[4] = (temp >> 4) | 0x8000;
		else if ((temp = (l[4] + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			s[4] = (temp >> 7) | 0xc000;
		else    s[4] = 0xffff;
		s += 5;
		l += 5;
	}
	for (; n > 0; n--) {
		/*
		 * more efficient version of old nmrd method
		temp = ((*l < 0) ? -*l : *l);
		     if (temp < 0x00002000)
			*s = (( *l       + 0x1fff) & 0x3fff);
		else if (temp < 0x00008000)
			*s = (((*l >> 2) + 0x1fff) & 0x3fff) | 0x4000;
		else if (temp < 0x00020000)
			*s = (((*l >> 4) + 0x1fff) & 0x3fff) | 0x8000;
		else if (temp < 0x00100000)
			*s = (((*l >> 7) + 0x1fff) & 0x3fff) | 0xc000;
		else    *s = 0xffff;
		 */
		/*
		 * my method - better accounts for range of mantissa,
		 * preserves precision better for 1 in 2^14 values
		 * costs an average of 1 op more than above.
		 */
		     if ((temp = (*l + 0x00001fff) & 0x7fffffff) < 0x00004000)
			*s =  temp;
		else if ((temp = (*l + 0x00007ffd) & 0x7fffffff) < 0x00010000)
			*s = (temp >> 2) | 0x4000;
		else if ((temp = (*l + 0x0001fff7) & 0x7fffffff) < 0x00040000)
			*s = (temp >> 4) | 0x8000;
		else if ((temp = (*l + 0x000fffbf) & 0x7fffffff) < 0x00200000)
			*s = (temp >> 7) | 0xc000;
		else    *s = 0xffff;
		s++;
		l++;
	}
}
