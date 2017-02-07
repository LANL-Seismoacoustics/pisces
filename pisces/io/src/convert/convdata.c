#include "convert.h"

/*
 * translation routines used below:
a2tot8	f4tot4	f4tot4x	f4tot8	f8tot8	g2tos4	i2tos2	i2tos4	i4tos4	s2toi2
s2tos4	s2tot8	s3tos4	s4tog2	s4toi2	s4toi4	s4tos2	s4tos3	s4tot4	s4tot8
t4tof4	t4tof4x	t4tos4	t4tot8	t8toa2	t8tof4	t8tof8	t8tos2	t8tos4	t8tot4
 */

/*
 * known fixed-width types
 * (datatypes are hex values for char[4]'s - see "man ascii" to fill in)
 */
#define NDATATYPE 11

#define A2 0x61320000		/* "a2" */
#define F4 0x66340000		/* "f4" */
#define F8 0x66380000		/* "f8" */
#define G2 0x67320000		/* "g2" */
#define I2 0x69320000		/* "i2" */
#define I4 0x69340000		/* "i4" */
#define S2 0x73320000		/* "s2" */
#define S3 0x73330000		/* "s3" */
#define S4 0x73340000		/* "s4" */
#define T4 0x74340000		/* "t4" */
#define T8 0x74380000		/* "t8" */

struct typeinfo {
	long name;
	int len;
	int have_s4;
	int have_t8;
#ifdef __STDC__
	ConvFunc *from_s4_func;
	ConvFunc *to_s4_func;
	ConvFunc *from_t8_func;
	ConvFunc *to_t8_func;
#else
	void (*from_s4_func)();
	void (*to_s4_func)();
	void (*from_t8_func)();
	void (*to_t8_func)();
#endif
} datatype[NDATATYPE] = {
	{A2, 2, 0, 1,      0,      0, t8toa2, a2tot8},
	{F4, 4, 0, 1,      0,      0, t8tof4, f4tot8},
	{F8, 8, 0, 1,      0,      0, t8tof8, f8tot8},
	{G2, 2, 1, 0, s4tog2, g2tos4,      0,      0},
	{I2, 2, 1, 0, s4toi2, i2tos4,      0,      0},
	{I4, 4, 1, 0, s4toi4, i4tos4,      0,      0},
	{S2, 2, 1, 1, s4tos2, s2tos4, t8tos2, s2tot8},
	{S3, 3, 1, 0, s4tos3, s3tos4,      0,      0},
	{S4, 4, 0, 1,      0,      0, t8tos4, s4tot8},
	{T4, 4, 1, 1, s4tot4, t4tos4, t8tot4, t4tot8},
	{T8, 8, 1, 0, s4tot8, t8tos4,      0,      0}
};

/* Python C extensions for Windows expects the symbol initModuleName when building the library.
* This declaration gives msvc compiler this symbol to compile correctly.
* Note : This not the documented way to build C extensions for Windows. It is typically expected to
* use wrapper methods. What this does is prevents a statement such as 'import libconvert' in Python.
* Instead, the only way to load the library is through a ctypes.CDLL call. Which in this case, is all that
* is needed, as seen in readwaveform.py.
*/
#ifdef _WIN32
void initlibconvert() {}
#endif

/* note that at least one of have_s4 and have_t8 must be set */

int convdata(buf, n, intype, outtype)
void *buf;
int n;
char *intype, *outtype;
{
	union {long l; char c[4];} typeu;
	struct typeinfo *in_info, *out_info;
	int i;

	typeu.c[2] = typeu.c[3] = 0;
	typeu.c[0] = intype[0];
	typeu.c[1] = intype[1];
	for (i = 0; i < NDATATYPE; i++) {
		if (datatype[i].name == typeu.l) break;
	}
	if (i == NDATATYPE) {
		/*
		 * unknown datatype
		 */
		return CONV_UNKNOWN;
	}
	in_info = &(datatype[i]);
	typeu.c[2] = typeu.c[3] = 0;
	typeu.c[0] = outtype[0];
	typeu.c[1] = outtype[1];
	for (i = 0; i < NDATATYPE; i++) {
		if (datatype[i].name == typeu.l) break;
	}
	if (i == NDATATYPE) {
		/*
		 * unknown datatype
		 */
		return CONV_UNKNOWN;
	}
	out_info = &(datatype[i]);

	if (in_info == out_info) {
		return CONV_SUCCESS;
	}

	/*
	 * if we can use s4 as the intermediate type, do so
	 * most s4 conversions exist.  Do intype->s4, s4->outtype
	 * or two stage as required.  If s4 conversion not available,
	 * or conversion type requires t8, go to t8 conversions
	 *
	 * catch the special cases of i2->s2 or s2->i2 and
	 * f4->t4 or t4->f4 first, since they are simpler than the others
	 * (use "x" versions of f4t4, since they are better for special cases)
	 */
	if (in_info->name == I2 && out_info->name == S2) {
		i2tos2(buf, n);
		return CONV_SUCCESS;
	}
	if (in_info->name == S2 && out_info->name == I2) {
		s2toi2(buf, n);
		return CONV_SUCCESS;
	}
	if (in_info->name == F4 && out_info->name == T4) {
		f4tot4x(buf, n);
		return CONV_SUCCESS;
	}
	if (in_info->name == T4 && out_info->name == F4) {
		t4tof4x(buf, n);
		return CONV_SUCCESS;
	}

	if (in_info->name == S4) {
		(*out_info->from_s4_func)(buf, n);
		return CONV_SUCCESS;
	}
	if (out_info->name == S4) {
		(*in_info->to_s4_func)(buf, n);
		return CONV_SUCCESS;
	}
	if (out_info->have_s4 && in_info->have_s4) {
		(*in_info->to_s4_func)(buf, n);
		(*out_info->from_s4_func)(buf, n);
		return CONV_SUCCESS;
	}

	/*
	 * have to use t8 as intermediate type
	 */
	if (in_info->name == T8) {
		if (out_info->have_t8)
			(*out_info->from_t8_func)(buf, n);
		else {
			t8tos4(buf,n);
			(*out_info->from_s4_func)(buf, n);
		}
		return CONV_SUCCESS;
	}
	if (out_info->name == T8) {
		if (in_info->have_t8)
			(*in_info->to_t8_func)(buf, n);
		else {
			(*in_info->to_s4_func)(buf, n);
			s4tot8(buf,n);
		}
		return CONV_SUCCESS;
	}
	if (in_info->have_t8)
		(*in_info->to_t8_func)(buf, n);
	else {
		(*in_info->to_s4_func)(buf, n);
		s4tot8(buf,n);
	}
	if (out_info->have_t8)
		(*out_info->from_t8_func)(buf, n);
	else {
		t8tos4(buf,n);
		(*out_info->from_s4_func)(buf, n);
	}
	return CONV_SUCCESS;
}

int convfunc(intype, outtype, inlen, outlen, func, nfunc)
char *intype, *outtype;
int *inlen, *outlen;
#ifdef __STDC__
ConvFunc **func;
#else
void (**func)();
#endif
int *nfunc;
{
	union {long l; char c[4];} typeu;
	struct typeinfo *in_info, *out_info;
	int i;

	typeu.c[2] = typeu.c[3] = 0;
	typeu.c[0] = intype[0];
	typeu.c[1] = intype[1];
	for (i = 0; i < NDATATYPE; i++) {
		if (datatype[i].name == typeu.l) break;
	}
	if (i == NDATATYPE) {
		/*
		 * unknown datatype
		 */
		*inlen = *outlen = 0;
		*nfunc = 0;
		return CONV_UNKNOWN;
	}
	in_info = &(datatype[i]);
	*inlen = in_info->len;
	typeu.c[2] = typeu.c[3] = 0;
	typeu.c[0] = outtype[0];
	typeu.c[1] = outtype[1];
	for (i = 0; i < NDATATYPE; i++) {
		if (datatype[i].name == typeu.l) break;
	}
	if (i == NDATATYPE) {
		/*
		 * unknown datatype
		 */
		*inlen = *outlen = 0;
		*nfunc = 0;
		return CONV_UNKNOWN;
	}
	out_info = &(datatype[i]);
	*outlen = out_info->len;

	if (in_info == out_info) {
		*inlen = *outlen = out_info->len;
		*nfunc = 0;
		return CONV_SUCCESS;
	}

	/*
	 * if we can use s4 as the intermediate type, do so
	 * most s4 conversions exist.  Do intype->s4, s4->outtype
	 * or two stage as required.  If s4 conversion not available,
	 * or conversion type requires t8, go to t8 conversions
	 *
	 * catch the special cases of i2->s2 or s2->i2 and
	 * f4->t4 or t4->f4 first, since they are simpler than the others
	 * (use "x" versions of f4t4, since they are better for special cases)
	 */
	if (in_info->name == I2 && out_info->name == S2) {
		func[0] = i2tos2;
		*nfunc = 1;
		return CONV_SUCCESS;
	}
	if (in_info->name == S2 && out_info->name == I2) {
		func[0] = s2toi2;
		*nfunc = 1;
		return CONV_SUCCESS;
	}
	if (in_info->name == F4 && out_info->name == T4) {
		func[0] = f4tot4;
		*nfunc = 1;
		return CONV_SUCCESS;
	}
	if (in_info->name == T4 && out_info->name == F4) {
		func[0] = t4tof4;
		*nfunc = 1;
		return CONV_SUCCESS;
	}

	if (in_info->name == S4) {
		func[0] = out_info->from_s4_func;
		*nfunc = 1;
		return CONV_SUCCESS;
	}
	if (out_info->name == S4) {
		func[0] = in_info->to_s4_func;
		*nfunc = 1;
		return CONV_SUCCESS;
	}
	if (out_info->have_s4 && in_info->have_s4) {
		func[0] = in_info->to_s4_func;
		func[1] = out_info->from_s4_func;
		*nfunc = 2;
		return CONV_SUCCESS;
	}

	/*
	 * have to use t8 as intermediate type
	 */
	if (in_info->name == T8) {
		if (out_info->have_t8) {
			func[0] = out_info->from_t8_func;
			*nfunc = 1;
		}
		else {
			func[0] = t8tos4;
			func[1] = out_info->from_s4_func;
			*nfunc = 2;
		}
		return CONV_SUCCESS;
	}
	if (out_info->name == T8) {
		if (in_info->have_t8) {
			func[0] = in_info->to_t8_func;
			*nfunc = 1;
		}
		else {
			func[0] = in_info->to_s4_func;
			func[1] = s4tot8;
			*nfunc = 2;
		}
		return CONV_SUCCESS;
	}
	if (in_info->have_t8) {
		func[0] = in_info->to_t8_func;
		*nfunc = 1;
	}
	else {
		func[0] = in_info->to_s4_func;
		func[1] = s4tot8;
		*nfunc = 2;
	}
	if (out_info->have_t8) {
		func[(*nfunc)++] = out_info->from_t8_func;
	}
	else {
		func[(*nfunc)++] = t8tos4;
		func[(*nfunc)++] = out_info->from_s4_func;
	}
	return CONV_SUCCESS;
}

int convlen(typ)
char *typ;
{
	union {long l; char c[4];} typeu;
	struct typeinfo *inf;
	int i;

	typeu.c[2] = typeu.c[3] = 0;
	typeu.c[0] = typ[0];
	typeu.c[1] = typ[1];
	for (i = 0; i < NDATATYPE; i++) {
		if (datatype[i].name == typeu.l) break;
	}
	if (i == NDATATYPE) {
		/*
		 * unknown datatype
		 */
		return -1;
	}
	inf = &(datatype[i]);
	return inf->len;
}
