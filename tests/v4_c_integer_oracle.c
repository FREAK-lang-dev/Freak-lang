/* Header-free scalar storage/signature oracle. This deliberately uses actual
   C int/unsigned int/long/unsigned long, not fixed-width substitute typedefs. */
#ifndef FREAK_ORACLE_LONG_BYTES
#error "pass the registered target's expected C long byte width explicitly"
#endif
_Static_assert(__CHAR_BIT__ == 8, "registered target byte width");
_Static_assert(sizeof(void *) == 8, "registered target pointer width");
_Static_assert(sizeof(int) == 4 && sizeof(unsigned int) == 4, "C int size");
_Static_assert(_Alignof(int) == 4 && _Alignof(unsigned int) == 4, "C int alignment");
_Static_assert(sizeof(long) == FREAK_ORACLE_LONG_BYTES, "C long size");
_Static_assert(sizeof(unsigned long) == FREAK_ORACLE_LONG_BYTES, "C unsigned long size");
_Static_assert(_Alignof(long) == FREAK_ORACLE_LONG_BYTES, "C long alignment");
_Static_assert(_Alignof(unsigned long) == FREAK_ORACLE_LONG_BYTES, "C unsigned long alignment");

#define ORACLE_INTEGER(key, type) \
    const unsigned long long oracle_size_##key = sizeof(type); \
    const unsigned long long oracle_align_##key = _Alignof(type); \
    const unsigned long long oracle_signed_##key = ((type)-1 < (type)0); \
    type oracle_identity_##key(type value) { return value; } \
    type oracle_direct_##key(type value) { return oracle_identity_##key(value); } \
    type oracle_indirect_##key(type (*callback)(type), type value) { return callback(value); }

ORACLE_INTEGER(c_int, int)
ORACLE_INTEGER(c_uint, unsigned int)
ORACLE_INTEGER(c_long, long)
ORACLE_INTEGER(c_ulong, unsigned long)
