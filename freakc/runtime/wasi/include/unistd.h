#pragma once
#include "freak_pal.h"
typedef long ssize_t;
#define read freak_pal_read
#define close freak_pal_close
ssize_t read(int, void *, size_t);
int close(int);
