#pragma once
#include "freak_pal.h"
typedef struct FILE FILE;
#define stdout freak_pal_stdout
#define stderr freak_pal_stderr
#define stdin freak_pal_stdin
extern FILE *freak_pal_stdout, *freak_pal_stderr, *freak_pal_stdin;
#define EOF (-1)
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2
#define fprintf freak_pal_fprintf
#define printf freak_pal_printf
#define snprintf freak_pal_snprintf
#define vsnprintf freak_pal_vsnprintf
#define vfprintf freak_pal_vfprintf
#define fputs freak_pal_fputs
#define fputc freak_pal_fputc
#define putc freak_pal_fputc
#define putchar freak_pal_putchar
#define puts freak_pal_puts
#define fwrite freak_pal_fwrite
#define fflush freak_pal_fflush
#define fdopen freak_pal_fdopen
#define fopen freak_pal_fopen
#define fread freak_pal_fread
#define fclose freak_pal_fclose
#define ferror freak_pal_ferror
#define feof freak_pal_feof
#define fseek freak_pal_fseek
#define ftell freak_pal_ftell
#define fgetc freak_pal_fgetc
#define getc freak_pal_fgetc
int fprintf(FILE *, const char *, ...);
int printf(const char *, ...);
int snprintf(char *, size_t, const char *, ...);
int vsnprintf(char *, size_t, const char *, va_list);
int vfprintf(FILE *, const char *, va_list);
int fputs(const char *, FILE *);
int fputc(int, FILE *);
int putchar(int);
int puts(const char *);
size_t fwrite(const void *, size_t, size_t, FILE *);
int fflush(FILE *);
FILE *fdopen(int, const char *);
FILE *fopen(const char *, const char *);
size_t fread(void *, size_t, size_t, FILE *);
int fclose(FILE *);
int ferror(FILE *);
int feof(FILE *);
int fseek(FILE *, long, int);
long ftell(FILE *);
int fgetc(FILE *);
