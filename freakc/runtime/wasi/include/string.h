#pragma once
#include "freak_pal.h"
void *memcpy(void *, const void *, size_t);
void *memmove(void *, const void *, size_t);
void *memset(void *, int, size_t);
int memcmp(const void *, const void *, size_t);
#define strlen freak_pal_strlen
#define strcmp freak_pal_strcmp
#define strncmp freak_pal_strncmp
#define strdup freak_pal_strdup
#define memchr freak_pal_memchr
#define strerror freak_pal_strerror
size_t strlen(const char *);
int strcmp(const char *, const char *);
int strncmp(const char *, const char *, size_t);
char *strdup(const char *);
void *memchr(const void *, int, size_t);
char *strerror(int);
