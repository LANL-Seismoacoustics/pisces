AR = ar cq
RM = rm -f
RM_CMD = $(RM) mapfile *.CKP *.ln *.BAK *.bak *.o core errs ,* *~ *.a .emacs_* tags TAGS make.log MakeOut *.O
CC = gcc
CFLAGS = -Wall -fPIC -shared -dynamiclib -lm -I. -arch i386 -arch x86_64 -g -O

LIBNAME = convert
SRCS = a2t4.c b4t4.c convdata.c f4f8t4t8.c g2s4.c i2s2.c i2s4.c i4s4.c \
	s2s4.c s2t8.c s3s4.c s4t4.c s4t8.c t4t8.c
SHARED_HEADERS = convert.h
HEADERS = convert.h
OBJS = $(SRCS:%.c=%.o)

all:: $(LIBRARY)

%.o: %.c
	$(CC) -c $(CFLAGS) $*.c -o $*.o

lib$(LIBNAME).a: $(OBJS) $(HEADERS)
	$(RM) $@
	$(AR) $@ $(OBJS)

LIBRARY = lib$(LIBNAME).a

clean::
	$(RM_CMD) "#"*
