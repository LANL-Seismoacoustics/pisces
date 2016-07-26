#ifndef CONVERT_H
#define CONVERT_H

/*
 * known translation routines
 */
#ifdef __STDC__
typedef void ConvFunc(void *buf, int n);
ConvFunc a2tot4;
ConvFunc a2tot8;
ConvFunc b4tot4;
ConvFunc t4tob4;
ConvFunc f4tof8;
ConvFunc f4tot4;
ConvFunc f4tot4x;
ConvFunc f4tot8;
ConvFunc f8tof4;
ConvFunc f8tot4;
ConvFunc f8tot8;
ConvFunc f8Dtot8;
ConvFunc g2tos4;
ConvFunc i2tos2;
ConvFunc i2tos4;
ConvFunc i4tos4;
ConvFunc s2toi2;
ConvFunc s2tos4;
ConvFunc s2tot8;
ConvFunc s3tos4;
ConvFunc s4tog2;
ConvFunc s4toi2;
ConvFunc s4toi4;
ConvFunc s4tos2;
ConvFunc s4tos3;
ConvFunc s4tot4;
ConvFunc s4tot8;
ConvFunc t4toa2;
ConvFunc t4tof4;
ConvFunc t4tof4x;
ConvFunc t4tof8;
ConvFunc t4tos4;
ConvFunc t4tot8;
ConvFunc t8toa2;
ConvFunc t8tof4;
ConvFunc t8tof8;
ConvFunc t8tos2;
ConvFunc t8tos4;
ConvFunc t8tot4;
#else
void a2tot4();
void a2tot8();
void b4tot4();
void t4tob4();
void f4tof8();
void f4tot4();
void f4tot4x();
void f4tot8();
void f8tof4();
void f8tot4();
void f8tot8();
void f8Dtot8();
void g2tos4();
void i2tos2();
void i2tos4();
void i4tos4();
void s2toi2();
void s2tos4();
void s2tot8();

void s4tog2();
void s4toi2();
void s4toi4();
void s4tos2();

void s4tot4();
void s4tot8();
void t4toa2();
void t4tof4();
void t4tof4x();
void t4tof8();
void t4tos4();
void t4tot8();
void t8toa2();
void t8tof4();
void t8tof8();
void t8tos2();
void t8tos4();
void t8tot4();
    //Support for different OS
    #ifdef _WIN32
        _declspec(dllexport) void s3tos4();
        _declspec(dllexport) void s4tos3();
    #else
        void s3tos4();
        void s4tos3();
    #endif
#endif

/*
  * The _declspec(dllexport) statement explicitly tells the compiler to send a function to the .dll.
  * This is done so that when PythonXX.lib is updated it knows how to find the appropriate functions
  * when referencing the .pyd.
  */

#ifdef __STDC__

    // Support for different OS
    #ifdef _WIN32
        _declspec(dllexport) int convdata(void *buf, int n, char *intype, char *outtype);
    #else
        int convdata(void *buf, int n, char *intype, char *outtype);
    #endif

    int convfunc(char *intype, char *outtype, int *inlen, int *outlen, ConvFunc **func, int *nfunc);
    int convlen(char *typ);

#else
    #ifdef _WIN32
        _declspec(dllexport) int convdata();
    #else
        int convdata();
    #endif

    int convfunc();
    int convlen();
#endif

/*
 * return values
 */
#define CONV_SUCCESS 0
#define CONV_UNKNOWN -1

#endif CONVERT_H
