#pragma once
#include "../freak_pal.h"
struct stat { int64_t st_size; unsigned st_mode; };
#define S_IFMT 0170000
#define S_IFREG 0100000
#define S_IFDIR 0040000
#define S_ISREG(m) (((m) & S_IFMT) == S_IFREG)
#define S_ISDIR(m) (((m) & S_IFMT) == S_IFDIR)
#define fstat freak_pal_fstat
int fstat(int, struct stat *);
