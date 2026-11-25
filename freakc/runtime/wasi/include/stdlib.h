#pragma once
#include "freak_pal.h"
/* The allocator keeps its C names: generated code calls realloc/free and
   programs may declare extern [C] malloc/free themselves. */
void *malloc(size_t);
void *calloc(size_t, size_t);
void *realloc(void *, size_t);
void free(void *);
#define abort freak_pal_abort
#define exit freak_pal_exit
#define _Exit freak_pal__Exit
#define atexit freak_pal_atexit
#define strtoll freak_pal_strtoll
#define strtod freak_pal_strtod
#define atoll freak_pal_atoll
#define getenv freak_pal_getenv
_Noreturn void abort(void);
_Noreturn void exit(int);
_Noreturn void _Exit(int);
int atexit(void (*)(void));
long long strtoll(const char *, char **, int);
double strtod(const char *, char **);
long long atoll(const char *);
char *getenv(const char *);
#define EXIT_SUCCESS 0
#define EXIT_FAILURE 1
