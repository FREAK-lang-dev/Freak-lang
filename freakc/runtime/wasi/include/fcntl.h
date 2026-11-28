#pragma once
#include "freak_pal.h"
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2
#define O_BINARY 0
#define O_CLOEXEC 0
#define O_NONBLOCK 0
#define open freak_pal_open
int open(const char *, int, ...);
