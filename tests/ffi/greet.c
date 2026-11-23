/* Test library for tests/v3_ffi.py: a plain C shared library that FREAK
 * binds through extern [C, link="greet"] and extern [C, load="greet"]. */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#ifdef _WIN32
#define GREET_API __declspec(dllexport)
#else
#define GREET_API __attribute__((visibility("default")))
#endif

static int greet_counter;

GREET_API int greet_add(int a, int b) { return a + b; }
GREET_API int greet_negate(int a) { return -a; }
GREET_API unsigned char greet_wrap(unsigned char x) { return (unsigned char)(x + 1); }
GREET_API short greet_twice(short x) { return (short)(x * 2); }
GREET_API ptrdiff_t greet_big(ptrdiff_t a) { return a * (ptrdiff_t)1000000000; }
GREET_API double greet_scale(double x, int factor) { return x * factor; }
GREET_API float greet_halve(float x) { return x / 2.0f; }
GREET_API _Bool greet_is_even(int x) { return x % 2 == 0; }
GREET_API _Bool greet_not(_Bool x) { return !x; }
GREET_API size_t greet_strlen(const char *s) { return strlen(s); }
GREET_API const char *greet_hello(void) { return "hello from C"; }
GREET_API void greet_squares(int *out, int n) { for (int i = 0; i < n; i++) out[i] = i * i; }
GREET_API void greet_bump(void) { greet_counter++; }
GREET_API int greet_count(void) { return greet_counter; }
GREET_API int greet_shout(char *s) {
    int changed = 0;
    for (; *s; s++) if (*s >= 'a' && *s <= 'z') { *s = (char)(*s - 32); changed++; }
    return changed;
}
GREET_API long greet_long(long x) { return x - 1; }
