/*
 * FREAK V3.5 IRBuilder bridge (freak_ib2_*).
 *
 * emit_llvm.fk lowers a program once; its ir_* sinks either print textual
 * IR or call the functions below, which build the same module in memory
 * through the LLVM C API and emit an object file in process. Clang is then
 * only the linker.
 *
 * Operands arrive as the names the text sink would print ("%t3",
 * "%binding.local.7", "@g_x", "@.str.2", "42", "1.5e+00", "true"). Locals
 * and blocks live in per-function tables; "@" names resolve against the
 * module. Every FREAK value is an i64 (words, shapes and lists are handles;
 * num is double bits), so the bridge only needs i1/i32/i64/double/ptr.
 *
 * The first error wins: it is recorded, later calls become no-ops, and
 * freak_ib2_finish() reports failure so the CLI can fall back to the
 * shadow .ll that the text sink wrote alongside.
 *
 * Built only for release CLIs that link LLVM (define FREAK_IB2_LINKED when
 * compiling freak_runtime.c so its stubs step aside).
 */
#include "freak_runtime.h"

#include <llvm-c/Analysis.h>
#include <llvm-c/BitWriter.h>
#include <llvm-c/Core.h>
#include <llvm-c/DebugInfo.h>
#include <llvm-c/Target.h>
#include <llvm-c/TargetMachine.h>
#include <llvm-c/Transforms/PassBuilder.h>

#ifdef FREAK_IB2_DYNAMIC
#include "ib_llvm_dynamic.h"
#endif

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* State                                                              */
/* ------------------------------------------------------------------ */

typedef struct ib2_entry {
    char *key;
    void *value;
    struct ib2_entry *next;
} ib2_entry;

typedef struct {
    ib2_entry **buckets;
    size_t bucket_count;
    size_t count;
} ib2_table;

static struct {
    int open;
    char error[2048];
    LLVMContextRef context;
    LLVMModuleRef module;
    LLVMBuilderRef builder;
    LLVMDIBuilderRef di;
    LLVMMetadataRef di_file;
    LLVMMetadataRef di_unit;
    LLVMMetadataRef di_routine_type;
    LLVMMetadataRef di_scope;
    int64_t line;
    LLVMTypeRef i1, i8, i32, i64, f64, ptr, void_type, overflow_pair;
    LLVMValueRef function;
    int function_returns; /* 0 void, 1 i64, 2 i32 main */
    ib2_table values;
    ib2_table blocks;
    unsigned prof_kind;
    LLVMValueRef cold_weights;
    unsigned dead_blocks;
} ib2;

static uint64_t ib2_hash(const char *s) {
    uint64_t h = 1469598103934665603ULL;
    while (*s) { h ^= (unsigned char)*s++; h *= 1099511628211ULL; }
    return h;
}

static void ib2_table_clear(ib2_table *t) {
    if (!t->buckets) return;
    for (size_t i = 0; i < t->bucket_count; i++) {
        ib2_entry *e = t->buckets[i];
        while (e) { ib2_entry *n = e->next; free(e->key); free(e); e = n; }
        t->buckets[i] = NULL;
    }
    t->count = 0;
}

static void ib2_table_free(ib2_table *t) {
    ib2_table_clear(t);
    free(t->buckets);
    t->buckets = NULL;
    t->bucket_count = 0;
}

static void *ib2_table_get(ib2_table *t, const char *key) {
    if (!t->buckets) return NULL;
    ib2_entry *e = t->buckets[ib2_hash(key) & (t->bucket_count - 1)];
    for (; e; e = e->next) if (strcmp(e->key, key) == 0) return e->value;
    return NULL;
}

static void ib2_table_grow(ib2_table *t) {
    size_t next = t->bucket_count ? t->bucket_count * 2 : 1024;
    ib2_entry **buckets = calloc(next, sizeof(*buckets));
    if (!buckets) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    for (size_t i = 0; i < t->bucket_count; i++) {
        ib2_entry *e = t->buckets[i];
        while (e) {
            ib2_entry *n = e->next;
            size_t slot = ib2_hash(e->key) & (next - 1);
            e->next = buckets[slot];
            buckets[slot] = e;
            e = n;
        }
    }
    free(t->buckets);
    t->buckets = buckets;
    t->bucket_count = next;
}

static void ib2_table_put(ib2_table *t, const char *key, void *value) {
    if (t->count * 2 >= t->bucket_count) ib2_table_grow(t);
    size_t slot = ib2_hash(key) & (t->bucket_count - 1);
    for (ib2_entry *e = t->buckets[slot]; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { e->value = value; return; }
    }
    ib2_entry *e = malloc(sizeof(*e));
    size_t len = strlen(key);
    e->key = malloc(len + 1);
    if (!e || !e->key) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    memcpy(e->key, key, len + 1);
    e->value = value;
    e->next = t->buckets[slot];
    t->buckets[slot] = e;
    t->count++;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

/* FREAK words are not NUL-terminated: copy into rotating scratch buffers. */
static char *ib2_cstr(freak_word w) {
    static char *slots[8];
    static size_t sizes[8];
    static int next;
    int i = next;
    next = (next + 1) & 7;
    size_t need = w.length + 1;
    if (sizes[i] < need) {
        size_t size = need < 256 ? 256 : need * 2;
        char *grown = realloc(slots[i], size);
        if (!grown) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
        slots[i] = grown;
        sizes[i] = size;
    }
    if (w.length) memcpy(slots[i], w.data, w.length);
    slots[i][w.length] = '\0';
    return slots[i];
}

static int ib2_failed(void) { return ib2.error[0] != '\0' || !ib2.open; }

static void ib2_fail(const char *fmt, ...) {
    if (ib2.error[0]) return;
    va_list args;
    va_start(args, fmt);
    vsnprintf(ib2.error, sizeof(ib2.error), fmt, args);
    va_end(args);
}

/* "%t3" -> "t3", "@g_x" -> "g_x". */
static const char *ib2_bare(const char *name) {
    return (name[0] == '%' || name[0] == '@') ? name + 1 : name;
}

static LLVMValueRef ib2_global_value(const char *name) {
    const char *bare = ib2_bare(name);
    LLVMValueRef v = LLVMGetNamedGlobal(ib2.module, bare);
    if (!v) v = LLVMGetNamedFunction(ib2.module, bare);
    return v;
}

static int ib2_parse_int(const char *s, long long *out) {
    if (!*s) return 0;
    char *end = NULL;
    long long v = strtoll(s, &end, 10);
    if (*end) return 0;
    *out = v;
    return 1;
}

static int ib2_parse_double(const char *s, double *out) {
    if (!*s) return 0;
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
        /* LLVM hex double literal: the IEEE bit pattern. */
        char *end = NULL;
        unsigned long long bits = strtoull(s + 2, &end, 16);
        if (*end) return 0;
        memcpy(out, &bits, sizeof(*out));
        return 1;
    }
    char *end = NULL;
    double v = strtod(s, &end);
    if (*end) return 0;
    *out = v;
    return 1;
}

/* Resolve an operand in a context that expects `type`. */
static LLVMValueRef ib2_value(const char *name, LLVMTypeRef type) {
    if (ib2_failed()) return NULL;
    if (name[0] == '%') {
        LLVMValueRef v = ib2_table_get(&ib2.values, name);
        if (!v) ib2_fail("IRBuilder: use of undefined value %s", name);
        return v;
    }
    if (name[0] == '@') {
        LLVMValueRef v = ib2_global_value(name);
        if (!v) ib2_fail("IRBuilder: use of undefined global %s", name);
        return v;
    }
    if (strncmp(name, "getelementptr inbounds (", 24) == 0) {
        /* `getelementptr inbounds ([N x i8], [N x i8]* @g, i64 0, i64 0)`:
         * with opaque pointers that is @g itself. */
        const char *at = strstr(name, "* @");
        if (at && strstr(at, ", i64 0, i64 0)")) {
            char global[512];
            size_t n = 0;
            at += 2;
            while (at[n] && at[n] != ',' && n + 1 < sizeof(global)) { global[n] = at[n]; n++; }
            global[n] = '\0';
            LLVMValueRef v = ib2_global_value(global);
            if (!v) ib2_fail("IRBuilder: use of undefined global %s", global);
            return v;
        }
    }
    if (strcmp(name, "undef") == 0) return LLVMGetUndef(type);
    if (strcmp(name, "poison") == 0) return LLVMGetPoison(type);
    if (strcmp(name, "null") == 0) return LLVMConstNull(type);
    if (type == ib2.i1) {
        if (strcmp(name, "true") == 0) return LLVMConstInt(ib2.i1, 1, 0);
        if (strcmp(name, "false") == 0) return LLVMConstInt(ib2.i1, 0, 0);
    }
    if (type == ib2.f64) {
        double d;
        if (ib2_parse_double(name, &d)) return LLVMConstReal(ib2.f64, d);
    } else {
        long long n;
        if (strcmp(name, "true") == 0) return LLVMConstInt(type, 1, 0);
        if (strcmp(name, "false") == 0) return LLVMConstInt(type, 0, 0);
        if (ib2_parse_int(name, &n)) return LLVMConstInt(type, (unsigned long long)n, 1);
    }
    ib2_fail("IRBuilder: cannot read operand '%s'", name);
    return NULL;
}

static void ib2_define(const char *name, LLVMValueRef v) {
    if (!v || ib2_failed()) return;
    if (name[0] != '%') { ib2_fail("IRBuilder: result name '%s' is not a local", name); return; }
    if (ib2_table_get(&ib2.values, name)) { ib2_fail("IRBuilder: %s defined twice", name); return; }
    ib2_table_put(&ib2.values, name, v);
}

static LLVMBasicBlockRef ib2_block(const char *label) {
    const char *bare = ib2_bare(label);
    LLVMBasicBlockRef bb = ib2_table_get(&ib2.blocks, bare);
    if (!bb) {
        bb = LLVMCreateBasicBlockInContext(ib2.context, bare);
        ib2_table_put(&ib2.blocks, bare, bb);
    }
    return bb;
}

/* Position for a new instruction. Text IR may keep emitting after a
 * terminator (code after `give back`); LLVM's parser starts an unnamed
 * block there, so the bridge does the same. */
static int ib2_ready(void) {
    if (ib2_failed()) return 0;
    if (!ib2.function) { ib2_fail("IRBuilder: instruction outside a function"); return 0; }
    LLVMBasicBlockRef bb = LLVMGetInsertBlock(ib2.builder);
    if (!bb) { ib2_fail("IRBuilder: instruction before the first label"); return 0; }
    if (LLVMGetBasicBlockTerminator(bb)) {
        char name[48];
        snprintf(name, sizeof(name), "dead.%u", ib2.dead_blocks++);
        LLVMBasicBlockRef dead = LLVMAppendBasicBlockInContext(ib2.context, ib2.function, name);
        LLVMPositionBuilderAtEnd(ib2.builder, dead);
    }
    return 1;
}

static void ib2_apply_line(void) {
    if (!ib2.di_scope || ib2.line <= 0) {
        LLVMSetCurrentDebugLocation2(ib2.builder, NULL);
        return;
    }
    LLVMMetadataRef loc = LLVMDIBuilderCreateDebugLocation(
        ib2.context, (unsigned)ib2.line, 0, ib2.di_scope, NULL);
    LLVMSetCurrentDebugLocation2(ib2.builder, loc);
}

static LLVMValueRef ib2_function(const char *symbol, LLVMTypeRef type) {
    const char *bare = ib2_bare(symbol);
    LLVMValueRef fn = LLVMGetNamedFunction(ib2.module, bare);
    if (!fn) fn = LLVMAddFunction(ib2.module, bare, type);
    return fn;
}

static LLVMTypeRef ib2_i64_function_type(int returns_void, int64_t parameters) {
    LLVMTypeRef params[64];
    LLVMTypeRef *list = params;
    LLVMTypeRef *heap = NULL;
    if (parameters > 64) {
        heap = malloc(sizeof(LLVMTypeRef) * (size_t)parameters);
        list = heap;
    }
    for (int64_t i = 0; i < parameters; i++) list[i] = ib2.i64;
    LLVMTypeRef type = LLVMFunctionType(returns_void ? ib2.void_type : ib2.i64,
                                        list, (unsigned)parameters, 0);
    free(heap);
    return type;
}

static void ib2_add_fn_attribute(LLVMValueRef fn, const char *name) {
    unsigned kind = LLVMGetEnumAttributeKindForName(name, strlen(name));
    LLVMAddAttributeAtIndex(fn, LLVMAttributeFunctionIndex,
                            LLVMCreateEnumAttribute(ib2.context, kind, 0));
}

static LLVMValueRef ib2_private_string(const char *name, const char *bytes, size_t length, int align) {
    LLVMValueRef existing = LLVMGetNamedGlobal(ib2.module, name);
    if (existing) return existing;
    LLVMValueRef init = LLVMConstStringInContext2(ib2.context, bytes, length, 0);
    LLVMValueRef g = LLVMAddGlobal(ib2.module, LLVMTypeOf(init), name);
    LLVMSetInitializer(g, init);
    LLVMSetLinkage(g, LLVMPrivateLinkage);
    LLVMSetGlobalConstant(g, 1);
    LLVMSetUnnamedAddress(g, LLVMGlobalUnnamedAddr);
    if (align) LLVMSetAlignment(g, (unsigned)align);
    return g;
}

/* ------------------------------------------------------------------ */
/* Session                                                            */
/* ------------------------------------------------------------------ */

static void ib2_dispose(void) {
    ib2_table_free(&ib2.values);
    ib2_table_free(&ib2.blocks);
    if (ib2.di) LLVMDisposeDIBuilder(ib2.di);
    if (ib2.builder) LLVMDisposeBuilder(ib2.builder);
    if (ib2.module) LLVMDisposeModule(ib2.module);
    if (ib2.context) LLVMContextDispose(ib2.context);
    ib2.di = NULL;
    ib2.builder = NULL;
    ib2.module = NULL;
    ib2.context = NULL;
    ib2.function = NULL;
    ib2.di_scope = NULL;
    ib2.open = 0;
}

static int ib2_loaded = 0;

/* Static builds carry LLVM inside freak; Windows binds LLVM-C.dll from the
 * installed runtime directory on first use. */
int64_t freak_ib2_bind(freak_word library) {
#ifdef FREAK_IB2_DYNAMIC
    if (ib2_loaded) return ib2_loaded > 0;
    ib2_loaded = freak_ib2_dynamic_bind(ib2_cstr(library)) ? 1 : -1;
    return ib2_loaded > 0;
#else
    (void)library;
    ib2_loaded = 1;
    return 1;
#endif
}

int64_t freak_ib2_available(void) {
#ifdef FREAK_IB2_DYNAMIC
    return ib2_loaded > 0;
#else
    return 1;
#endif
}

freak_word freak_ib2_version(void) {
    static char text[32];
    unsigned major = 0, minor = 0, patch = 0;
    if (!freak_ib2_available()) return freak_word_lit("");
    LLVMGetVersion(&major, &minor, &patch);
    snprintf(text, sizeof(text), "%u.%u.%u", major, minor, patch);
    return freak_word_lit(text);
}

freak_word freak_ib2_error(void) {
    static char copy[sizeof(ib2.error)];
    memcpy(copy, ib2.error, sizeof(copy));
    return freak_word_lit(copy);
}

int64_t freak_ib2_open(freak_word module_name, freak_word source_file, freak_word source_dir) {
    ib2_dispose();
    ib2.error[0] = '\0';
    ib2.context = LLVMContextCreate();
    ib2.module = LLVMModuleCreateWithNameInContext(ib2_cstr(module_name), ib2.context);
    ib2.builder = LLVMCreateBuilderInContext(ib2.context);
    ib2.i1 = LLVMInt1TypeInContext(ib2.context);
    ib2.i8 = LLVMInt8TypeInContext(ib2.context);
    ib2.i32 = LLVMInt32TypeInContext(ib2.context);
    ib2.i64 = LLVMInt64TypeInContext(ib2.context);
    ib2.f64 = LLVMDoubleTypeInContext(ib2.context);
    ib2.ptr = LLVMPointerTypeInContext(ib2.context, 0);
    ib2.void_type = LLVMVoidTypeInContext(ib2.context);
    LLVMTypeRef pair[2] = { ib2.i64, ib2.i1 };
    ib2.overflow_pair = LLVMStructTypeInContext(ib2.context, pair, 2, 0);
    ib2.prof_kind = LLVMGetMDKindIDInContext(ib2.context, "prof", 4);
    LLVMMetadataRef weights[3] = {
        LLVMMDStringInContext2(ib2.context, "branch_weights", 14),
        LLVMValueAsMetadata(LLVMConstInt(ib2.i32, 1, 0)),
        LLVMValueAsMetadata(LLVMConstInt(ib2.i32, 1048575, 0)),
    };
    ib2.cold_weights = LLVMMetadataAsValue(ib2.context, LLVMMDNodeInContext2(ib2.context, weights, 3));

    const char *file = ib2_cstr(source_file);
    const char *dir = ib2_cstr(source_dir);
    ib2.di = LLVMCreateDIBuilder(ib2.module);
    ib2.di_file = LLVMDIBuilderCreateFile(ib2.di, file, strlen(file), dir, strlen(dir));
    ib2.di_unit = LLVMDIBuilderCreateCompileUnit(
        ib2.di, LLVMDWARFSourceLanguageC, ib2.di_file, "FREAK v3", 8, 0, "", 0, 0, "", 0,
        LLVMDWARFEmissionLineTablesOnly, 0, 1, 0, "", 0, "", 0);
    ib2.di_routine_type = LLVMDIBuilderCreateSubroutineType(ib2.di, ib2.di_file, NULL, 0, LLVMDIFlagZero);
    LLVMAddModuleFlag(ib2.module, LLVMModuleFlagBehaviorWarning, "Dwarf Version", 13,
                      LLVMValueAsMetadata(LLVMConstInt(ib2.i32, 4, 0)));
    LLVMAddModuleFlag(ib2.module, LLVMModuleFlagBehaviorWarning, "Debug Info Version", 18,
                      LLVMValueAsMetadata(LLVMConstInt(ib2.i32, LLVMDebugMetadataVersion(), 0)));
    ib2.function = NULL;
    ib2.di_scope = NULL;
    ib2.line = 0;
    ib2.dead_blocks = 0;
    ib2.open = 1;
    return 1;
}

int64_t freak_ib2_close(void) {
    ib2_dispose();
    return 1;
}

/* ------------------------------------------------------------------ */
/* Module-level declarations                                          */
/* ------------------------------------------------------------------ */

int64_t freak_ib2_declare(freak_word name, int64_t returns_void, int64_t parameters) {
    if (ib2_failed()) return 0;
    ib2_function(ib2_cstr(name), ib2_i64_function_type((int)returns_void, parameters));
    return 1;
}

int64_t freak_ib2_declare_support(int64_t kind) {
    if (ib2_failed()) return 0;
    if (kind == 1) {
        LLVMTypeRef fail_params[2] = { ib2.ptr, ib2.ptr };
        LLVMValueRef fail = ib2_function("__freak_int_fail",
            LLVMFunctionType(ib2.void_type, fail_params, 2, 0));
        ib2_add_fn_attribute(fail, "cold");
        ib2_add_fn_attribute(fail, "noreturn");
        static const char *messages[][2] = {
            { "__freak_int_overflow", "overflow" },
            { "__freak_int_division_by_zero", "division by zero" },
            { "__freak_int_addition", "addition" },
            { "__freak_int_subtraction", "subtraction" },
            { "__freak_int_multiplication", "multiplication" },
            { "__freak_int_division", "division" },
            { "__freak_int_remainder", "remainder" },
            { "__freak_int_negation", "negation" },
        };
        for (size_t i = 0; i < sizeof(messages) / sizeof(messages[0]); i++) {
            ib2_private_string(messages[i][0], messages[i][1], strlen(messages[i][1]), 0);
        }
        return 1;
    }
    if (kind == 2) {
        LLVMTypeRef one_ptr[1] = { ib2.ptr };
        ib2_function("puts", LLVMFunctionType(ib2.i32, one_ptr, 1, 0));
        ib2_function("printf", LLVMFunctionType(ib2.i32, one_ptr, 1, 1));
        ib2_function("strlen", LLVMFunctionType(ib2.i64, one_ptr, 1, 0));
        return 1;
    }
    if (kind == 3) {
        LLVMTypeRef one_i64[1] = { ib2.i64 };
        LLVMTypeRef helper_type = LLVMFunctionType(ib2.void_type, one_i64, 1, 0);
        LLVMValueRef release = ib2_function("freak_llvm_fs_result_release", helper_type);
        LLVMValueRef helper = ib2_function("__freak_drop_result", helper_type);
        LLVMSetLinkage(helper, LLVMInternalLinkage);
        LLVMValueRef ticket = LLVMGetParam(helper, 0);
        LLVMSetValueName2(ticket, "ticket", 6);
        LLVMBasicBlockRef entry = LLVMAppendBasicBlockInContext(ib2.context, helper, "entry");
        LLVMBasicBlockRef do_release = LLVMAppendBasicBlockInContext(ib2.context, helper, "release");
        LLVMBasicBlockRef done = LLVMAppendBasicBlockInContext(ib2.context, helper, "done");
        LLVMSetCurrentDebugLocation2(ib2.builder, NULL);
        LLVMPositionBuilderAtEnd(ib2.builder, entry);
        LLVMValueRef live = LLVMBuildICmp(ib2.builder, LLVMIntNE, ticket, LLVMConstInt(ib2.i64, 0, 0), "live");
        LLVMBuildCondBr(ib2.builder, live, do_release, done);
        LLVMPositionBuilderAtEnd(ib2.builder, do_release);
        LLVMValueRef args[1] = { ticket };
        LLVMBuildCall2(ib2.builder, helper_type, release, args, 1, "");
        LLVMBuildBr(ib2.builder, done);
        LLVMPositionBuilderAtEnd(ib2.builder, done);
        LLVMBuildRetVoid(ib2.builder);
        LLVMClearInsertionPosition(ib2.builder);
        return 1;
    }
    ib2_fail("IRBuilder: unknown support kind %lld", (long long)kind);
    return 0;
}

int64_t freak_ib2_global(freak_word name) {
    if (ib2_failed()) return 0;
    const char *bare = ib2_bare(ib2_cstr(name));
    if (LLVMGetNamedGlobal(ib2.module, bare)) return 1;
    LLVMValueRef g = LLVMAddGlobal(ib2.module, ib2.i64, bare);
    LLVMSetInitializer(g, LLVMConstInt(ib2.i64, 0, 0));
    return 1;
}

/* `text` is the body of an LLVM c"..." literal: \HH escapes, otherwise raw. */
int64_t freak_ib2_string(freak_word name, freak_word text) {
    if (ib2_failed()) return 0;
    const char *bare = ib2_bare(ib2_cstr(name));
    const unsigned char *src = (const unsigned char *)text.data;
    size_t n = text.length;
    char *bytes = malloc(n + 1);
    if (!bytes) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    size_t out = 0;
    for (size_t i = 0; i < n; i++) {
        if (src[i] == '\\' && i + 2 < n) {
            char hex[3] = { (char)src[i + 1], (char)src[i + 2], 0 };
            char *end = NULL;
            long v = strtol(hex, &end, 16);
            if (end == hex + 2) { bytes[out++] = (char)v; i += 2; continue; }
        }
        bytes[out++] = (char)src[i];
    }
    ib2_private_string(bare, bytes, out, 1);
    free(bytes);
    return 1;
}

/* ------------------------------------------------------------------ */
/* Functions and blocks                                               */
/* ------------------------------------------------------------------ */

int64_t freak_ib2_begin_function(freak_word symbol, int64_t returns, int64_t parameters,
                                 freak_word debug_name, int64_t line) {
    if (ib2_failed()) return 0;
    const char *sym = ib2_bare(ib2_cstr(symbol));
    const char *dbg_name = ib2_cstr(debug_name);
    LLVMTypeRef type;
    if (returns == 2) {
        LLVMTypeRef params[2] = { ib2.i32, ib2.ptr };
        type = LLVMFunctionType(ib2.i32, params, 2, 0);
    } else {
        type = ib2_i64_function_type(returns == 0, parameters);
    }
    LLVMValueRef fn = LLVMGetNamedFunction(ib2.module, sym);
    if (fn) {
        if (LLVMCountBasicBlocks(fn) > 0) { ib2_fail("IRBuilder: @%s defined twice", sym); return 0; }
        if (LLVMGlobalGetValueType(fn) != type) {
            ib2_fail("IRBuilder: @%s defined with a different signature than its uses", sym);
            return 0;
        }
    } else {
        fn = LLVMAddFunction(ib2.module, sym, type);
    }
    ib2_table_clear(&ib2.values);
    ib2_table_clear(&ib2.blocks);
    ib2.function = fn;
    ib2.function_returns = (int)returns;
    ib2.dead_blocks = 0;
    if (returns == 2) {
        LLVMValueRef argc = LLVMGetParam(fn, 0);
        LLVMValueRef argv = LLVMGetParam(fn, 1);
        LLVMSetValueName2(argc, "argc", 4);
        LLVMSetValueName2(argv, "argv", 4);
        ib2_table_put(&ib2.values, "%argc", argc);
        ib2_table_put(&ib2.values, "%argv", argv);
    } else {
        for (int64_t i = 0; i < parameters; i++) {
            char name[64];
            snprintf(name, sizeof(name), "%%parameter.input.%lld", (long long)i);
            LLVMValueRef p = LLVMGetParam(fn, (unsigned)i);
            LLVMSetValueName2(p, name + 1, strlen(name + 1));
            ib2_table_put(&ib2.values, name, p);
        }
    }
    if (line <= 0) line = 1;
    ib2.di_scope = LLVMDIBuilderCreateFunction(
        ib2.di, ib2.di_file, dbg_name, strlen(dbg_name), "", 0, ib2.di_file, (unsigned)line,
        ib2.di_routine_type, 0, 1, (unsigned)line, LLVMDIFlagZero, 0);
    LLVMSetSubprogram(fn, ib2.di_scope);
    ib2.line = line;
    LLVMClearInsertionPosition(ib2.builder);
    return 1;
}

int64_t freak_ib2_end_function(void) {
    if (ib2_failed()) return 0;
    if (!ib2.function) { ib2_fail("IRBuilder: end of function without a function"); return 0; }
    /* Every referenced label must have been placed. */
    for (size_t i = 0; i < ib2.blocks.bucket_count; i++) {
        for (ib2_entry *e = ib2.blocks.buckets[i]; e; e = e->next) {
            LLVMBasicBlockRef bb = e->value;
            if (LLVMGetBasicBlockParent(bb) == NULL) {
                ib2_fail("IRBuilder: label %%%s used but never placed in @%s", e->key,
                         LLVMGetValueName(ib2.function));
                return 0;
            }
        }
    }
    if (ib2.di_scope) LLVMDIBuilderFinalizeSubprogram(ib2.di, ib2.di_scope);
    ib2.function = NULL;
    ib2.di_scope = NULL;
    ib2.line = 0;
    LLVMClearInsertionPosition(ib2.builder);
    LLVMSetCurrentDebugLocation2(ib2.builder, NULL);
    return 1;
}

int64_t freak_ib2_label(freak_word name) {
    if (ib2_failed()) return 0;
    if (!ib2.function) { ib2_fail("IRBuilder: label outside a function"); return 0; }
    LLVMBasicBlockRef bb = ib2_block(ib2_cstr(name));
    if (LLVMGetBasicBlockParent(bb) != NULL) {
        ib2_fail("IRBuilder: label %s placed twice", LLVMGetBasicBlockName(bb));
        return 0;
    }
    LLVMAppendExistingBasicBlock(ib2.function, bb);
    LLVMPositionBuilderAtEnd(ib2.builder, bb);
    ib2_apply_line();
    return 1;
}

int64_t freak_ib2_set_line(int64_t line) {
    if (ib2_failed()) return 0;
    if (!ib2.di_scope) return 1;
    if (line <= 0) line = 1;
    if (line != ib2.line) {
        ib2.line = line;
        ib2_apply_line();
    }
    return 1;
}

/* ------------------------------------------------------------------ */
/* Instructions                                                       */
/* ------------------------------------------------------------------ */

static void ib2_before_instruction(void) {
    /* A label resets the location; keep it current for every instruction. */
    if (ib2.di_scope && !LLVMGetCurrentDebugLocation2(ib2.builder)) ib2_apply_line();
}

int64_t freak_ib2_call(freak_word dest, freak_word callee, freak_word arguments, int64_t returns_void) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *name = ib2_cstr(callee);
    const char *list = ib2_cstr(arguments);
    char *copy = strdup(list);
    if (!copy) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    size_t count = 0;
    for (const char *c = copy; *c; c++) if (*c == '|') count++;
    LLVMValueRef stack_args[16];
    LLVMValueRef *args = count > 16 ? malloc(sizeof(LLVMValueRef) * count) : stack_args;
    LLVMValueRef fn = ib2_global_value(name);
    LLVMTypeRef type;
    if (fn) {
        type = LLVMGlobalGetValueType(fn);
    } else {
        type = ib2_i64_function_type((int)returns_void, (int64_t)count);
        fn = LLVMAddFunction(ib2.module, ib2_bare(name), type);
    }
    unsigned declared = LLVMCountParamTypes(type);
    LLVMTypeRef param_types[64];
    LLVMTypeRef *ptypes = declared > 64 ? malloc(sizeof(LLVMTypeRef) * declared) : param_types;
    LLVMGetParamTypes(type, ptypes);
    size_t index = 0;
    char *start = copy;
    for (char *c = copy; *c; c++) {
        if (*c != '|') continue;
        *c = '\0';
        LLVMTypeRef want = index < declared ? ptypes[index] : ib2.i64;
        args[index++] = ib2_value(start, want);
        start = c + 1;
    }
    if (!LLVMIsFunctionVarArg(type) && declared != count) {
        ib2_fail("IRBuilder: call to %s passes %zu arguments, it takes %u", name, count, declared);
    }
    const char *result = ib2_cstr(dest);
    if (!ib2_failed()) {
        int is_void = LLVMGetReturnType(type) == ib2.void_type;
        LLVMValueRef call = LLVMBuildCall2(ib2.builder, type, fn, args, (unsigned)count,
                                           is_void ? "" : ib2_bare(result));
        if (!is_void && result[0]) ib2_define(result, call);
        else if (result[0] && is_void) ib2_fail("IRBuilder: %s takes the result of void %s", result, name);
    }
    if (args != stack_args) free(args);
    if (ptypes != param_types) free(ptypes);
    free(copy);
    return ib2_failed() ? 0 : 1;
}

int64_t freak_ib2_load(freak_word dest, freak_word pointer) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    LLVMValueRef p = ib2_value(ib2_cstr(pointer), ib2.ptr);
    if (ib2_failed()) return 0;
    ib2_define(result, LLVMBuildLoad2(ib2.builder, ib2.i64, p, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_store(freak_word value, freak_word pointer) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMValueRef v = ib2_value(ib2_cstr(value), ib2.i64);
    LLVMValueRef p = ib2_value(ib2_cstr(pointer), ib2.ptr);
    if (ib2_failed()) return 0;
    LLVMBuildStore(ib2.builder, v, p);
    return 1;
}

int64_t freak_ib2_alloca(freak_word dest) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    ib2_define(result, LLVMBuildAlloca(ib2.builder, ib2.i64, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_int(freak_word dest, freak_word operation, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *op = ib2_cstr(operation);
    LLVMValueRef l = ib2_value(ib2_cstr(left), ib2.i64);
    LLVMValueRef r = ib2_value(ib2_cstr(right), ib2.i64);
    if (ib2_failed()) return 0;
    LLVMOpcode code;
    if (strcmp(op, "add") == 0) code = LLVMAdd;
    else if (strcmp(op, "sub") == 0) code = LLVMSub;
    else if (strcmp(op, "mul") == 0) code = LLVMMul;
    else if (strcmp(op, "sdiv") == 0) code = LLVMSDiv;
    else if (strcmp(op, "srem") == 0) code = LLVMSRem;
    else if (strcmp(op, "udiv") == 0) code = LLVMUDiv;
    else if (strcmp(op, "urem") == 0) code = LLVMURem;
    else if (strcmp(op, "and") == 0) code = LLVMAnd;
    else if (strcmp(op, "or") == 0) code = LLVMOr;
    else if (strcmp(op, "xor") == 0) code = LLVMXor;
    else if (strcmp(op, "shl") == 0) code = LLVMShl;
    else if (strcmp(op, "ashr") == 0) code = LLVMAShr;
    else if (strcmp(op, "lshr") == 0) code = LLVMLShr;
    else { ib2_fail("IRBuilder: unknown integer operation '%s'", op); return 0; }
    ib2_define(result, LLVMBuildBinOp(ib2.builder, code, l, r, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_icmp(freak_word dest, freak_word predicate, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *p = ib2_cstr(predicate);
    LLVMValueRef l = ib2_value(ib2_cstr(left), ib2.i64);
    LLVMValueRef r = ib2_value(ib2_cstr(right), ib2.i64);
    if (ib2_failed()) return 0;
    LLVMIntPredicate pred;
    if (strcmp(p, "eq") == 0) pred = LLVMIntEQ;
    else if (strcmp(p, "ne") == 0) pred = LLVMIntNE;
    else if (strcmp(p, "slt") == 0) pred = LLVMIntSLT;
    else if (strcmp(p, "sle") == 0) pred = LLVMIntSLE;
    else if (strcmp(p, "sgt") == 0) pred = LLVMIntSGT;
    else if (strcmp(p, "sge") == 0) pred = LLVMIntSGE;
    else if (strcmp(p, "ult") == 0) pred = LLVMIntULT;
    else if (strcmp(p, "ule") == 0) pred = LLVMIntULE;
    else if (strcmp(p, "ugt") == 0) pred = LLVMIntUGT;
    else if (strcmp(p, "uge") == 0) pred = LLVMIntUGE;
    else { ib2_fail("IRBuilder: unknown icmp predicate '%s'", p); return 0; }
    ib2_define(result, LLVMBuildICmp(ib2.builder, pred, l, r, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_fcmp(freak_word dest, freak_word predicate, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *p = ib2_cstr(predicate);
    LLVMValueRef l = ib2_value(ib2_cstr(left), ib2.f64);
    LLVMValueRef r = ib2_value(ib2_cstr(right), ib2.f64);
    if (ib2_failed()) return 0;
    static const struct { const char *name; LLVMRealPredicate pred; } table[] = {
        { "false", LLVMRealPredicateFalse }, { "oeq", LLVMRealOEQ }, { "ogt", LLVMRealOGT },
        { "oge", LLVMRealOGE }, { "olt", LLVMRealOLT }, { "ole", LLVMRealOLE },
        { "one", LLVMRealONE }, { "ord", LLVMRealORD }, { "uno", LLVMRealUNO },
        { "ueq", LLVMRealUEQ }, { "ugt", LLVMRealUGT }, { "uge", LLVMRealUGE },
        { "ult", LLVMRealULT }, { "ule", LLVMRealULE }, { "une", LLVMRealUNE },
        { "true", LLVMRealPredicateTrue },
    };
    for (size_t i = 0; i < sizeof(table) / sizeof(table[0]); i++) {
        if (strcmp(p, table[i].name) == 0) {
            ib2_define(result, LLVMBuildFCmp(ib2.builder, table[i].pred, l, r, ib2_bare(result)));
            return 1;
        }
    }
    ib2_fail("IRBuilder: unknown fcmp predicate '%s'", p);
    return 0;
}

int64_t freak_ib2_float(freak_word dest, freak_word operation, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *op = ib2_cstr(operation);
    LLVMValueRef l = ib2_value(ib2_cstr(left), ib2.f64);
    LLVMValueRef r = ib2_value(ib2_cstr(right), ib2.f64);
    if (ib2_failed()) return 0;
    LLVMOpcode code;
    if (strcmp(op, "fadd") == 0) code = LLVMFAdd;
    else if (strcmp(op, "fsub") == 0) code = LLVMFSub;
    else if (strcmp(op, "fmul") == 0) code = LLVMFMul;
    else if (strcmp(op, "fdiv") == 0) code = LLVMFDiv;
    else if (strcmp(op, "frem") == 0) code = LLVMFRem;
    else { ib2_fail("IRBuilder: unknown float operation '%s'", op); return 0; }
    ib2_define(result, LLVMBuildBinOp(ib2.builder, code, l, r, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_cast(freak_word dest, freak_word kind, freak_word value) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *k = ib2_cstr(kind);
    const char *name = ib2_bare(result);
    const char *operand = ib2_cstr(value);
    LLVMValueRef v;
    LLVMValueRef out = NULL;
    if (strcmp(k, "zext1") == 0) {
        v = ib2_value(operand, ib2.i1);
        if (v) out = LLVMBuildZExt(ib2.builder, v, ib2.i64, name);
    } else if (strcmp(k, "i2d") == 0) {
        v = ib2_value(operand, ib2.i64);
        if (v) out = LLVMBuildBitCast(ib2.builder, v, ib2.f64, name);
    } else if (strcmp(k, "d2i") == 0) {
        v = ib2_value(operand, ib2.f64);
        if (v) out = LLVMBuildBitCast(ib2.builder, v, ib2.i64, name);
    } else if (strcmp(k, "sitofp") == 0) {
        v = ib2_value(operand, ib2.i64);
        if (v) out = LLVMBuildSIToFP(ib2.builder, v, ib2.f64, name);
    } else if (strcmp(k, "ptrtoint") == 0) {
        v = ib2_value(operand, ib2.ptr);
        if (v) out = LLVMBuildPtrToInt(ib2.builder, v, ib2.i64, name);
    } else if (strcmp(k, "sext32") == 0) {
        v = ib2_value(operand, ib2.i32);
        if (v) out = LLVMBuildSExt(ib2.builder, v, ib2.i64, name);
    } else {
        ib2_fail("IRBuilder: unknown cast '%s'", k);
        return 0;
    }
    if (ib2_failed()) return 0;
    ib2_define(result, out);
    return 1;
}

int64_t freak_ib2_and1(freak_word dest, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    LLVMValueRef l = ib2_value(ib2_cstr(left), ib2.i1);
    LLVMValueRef r = ib2_value(ib2_cstr(right), ib2.i1);
    if (ib2_failed()) return 0;
    ib2_define(result, LLVMBuildAnd(ib2.builder, l, r, ib2_bare(result)));
    return 1;
}

/* With opaque pointers `gep [N x i8], @s, 0, 0` is @s itself. */
int64_t freak_ib2_string_pointer(freak_word dest, freak_word global_name) {
    if (!ib2_ready()) return 0;
    const char *result = ib2_cstr(dest);
    LLVMValueRef g = ib2_value(ib2_cstr(global_name), ib2.ptr);
    if (ib2_failed()) return 0;
    ib2_define(result, g);
    return 1;
}

int64_t freak_ib2_br(freak_word label) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMBuildBr(ib2.builder, ib2_block(ib2_cstr(label)));
    return 1;
}

int64_t freak_ib2_cond_br(freak_word condition, freak_word then_label, freak_word else_label, int64_t cold) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMValueRef c = ib2_value(ib2_cstr(condition), ib2.i1);
    if (ib2_failed()) return 0;
    LLVMBasicBlockRef t = ib2_block(ib2_cstr(then_label));
    LLVMBasicBlockRef e = ib2_block(ib2_cstr(else_label));
    LLVMValueRef br = LLVMBuildCondBr(ib2.builder, c, t, e);
    if (cold) LLVMSetMetadata(br, ib2.prof_kind, ib2.cold_weights);
    return 1;
}

int64_t freak_ib2_phi2(freak_word dest, freak_word first, freak_word first_block,
                       freak_word second, freak_word second_block) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    LLVMValueRef values[2] = {
        ib2_value(ib2_cstr(first), ib2.i64),
        ib2_value(ib2_cstr(second), ib2.i64),
    };
    if (ib2_failed()) return 0;
    LLVMBasicBlockRef blocks[2] = { ib2_block(ib2_cstr(first_block)), ib2_block(ib2_cstr(second_block)) };
    LLVMValueRef phi = LLVMBuildPhi(ib2.builder, ib2.i64, ib2_bare(result));
    LLVMAddIncoming(phi, values, blocks, 2);
    ib2_define(result, phi);
    return 1;
}

int64_t freak_ib2_overflow(freak_word dest, freak_word operation, freak_word left, freak_word right) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *op = ib2_cstr(operation);
    char intrinsic[48];
    snprintf(intrinsic, sizeof(intrinsic), "llvm.s%s.with.overflow", op);
    unsigned id = LLVMLookupIntrinsicID(intrinsic, strlen(intrinsic));
    if (!id) { ib2_fail("IRBuilder: unknown overflow operation '%s'", op); return 0; }
    LLVMTypeRef overloads[1] = { ib2.i64 };
    LLVMValueRef fn = LLVMGetIntrinsicDeclaration(ib2.module, id, overloads, 1);
    LLVMTypeRef type = LLVMIntrinsicGetType(ib2.context, id, overloads, 1);
    LLVMValueRef args[2] = {
        ib2_value(ib2_cstr(left), ib2.i64),
        ib2_value(ib2_cstr(right), ib2.i64),
    };
    if (ib2_failed()) return 0;
    ib2_define(result, LLVMBuildCall2(ib2.builder, type, fn, args, 2, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_extract(freak_word dest, freak_word pair, int64_t index) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    LLVMValueRef p = ib2_value(ib2_cstr(pair), ib2.overflow_pair);
    if (ib2_failed()) return 0;
    ib2_define(result, LLVMBuildExtractValue(ib2.builder, p, (unsigned)index, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_ret(freak_word value) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMValueRef v = ib2_value(ib2_cstr(value), ib2.i64);
    if (ib2_failed()) return 0;
    LLVMBuildRet(ib2.builder, v);
    return 1;
}

int64_t freak_ib2_ret_void(void) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMBuildRetVoid(ib2.builder);
    return 1;
}

int64_t freak_ib2_ret_i32(freak_word value) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *v = ib2_cstr(value);
    if (!v[0]) {
        LLVMBuildRet(ib2.builder, LLVMConstInt(ib2.i32, 0, 0));
        return 1;
    }
    LLVMValueRef wide = ib2_value(v, ib2.i64);
    if (ib2_failed()) return 0;
    LLVMBuildRet(ib2.builder, LLVMBuildTrunc(ib2.builder, wide, ib2.i32, "exit.code"));
    return 1;
}

int64_t freak_ib2_unreachable(void) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMBuildUnreachable(ib2.builder);
    return 1;
}

/* ------------------------------------------------------------------ */
/* Typed operations (native FFI: C widths instead of the i64 carrier)  */
/* ------------------------------------------------------------------ */

/* "i32", "i8 signext", "i1 zeroext", "double", "i8*", "void". Sets *attr to
 * 1 for signext, 2 for zeroext, 0 otherwise; returns NULL on a bad name. */
static LLVMTypeRef ib2_type_named(const char *text, int *attr) {
    char name[32];
    size_t n = 0;
    while (text[n] && text[n] != ' ' && n + 1 < sizeof(name)) { name[n] = text[n]; n++; }
    name[n] = '\0';
    if (attr) {
        const char *rest = text + n;
        while (*rest == ' ') rest++;
        *attr = 0;
        if (strncmp(rest, "signext", 7) == 0) *attr = 1;
        else if (strncmp(rest, "zeroext", 7) == 0) *attr = 2;
    }
    if (strcmp(name, "i1") == 0) return ib2.i1;
    if (strcmp(name, "i8") == 0) return ib2.i8;
    if (strcmp(name, "i16") == 0) return LLVMInt16TypeInContext(ib2.context);
    if (strcmp(name, "i32") == 0) return ib2.i32;
    if (strcmp(name, "i64") == 0) return ib2.i64;
    if (strcmp(name, "float") == 0) return LLVMFloatTypeInContext(ib2.context);
    if (strcmp(name, "double") == 0) return ib2.f64;
    if (strcmp(name, "void") == 0) return ib2.void_type;
    if (name[n ? n - 1 : 0] == '*' || strcmp(name, "ptr") == 0) return ib2.ptr;
    ib2_fail("IRBuilder: unknown type '%s'", text);
    return NULL;
}

static LLVMAttributeRef ib2_ext_attribute(int attr) {
    const char *name = attr == 1 ? "signext" : "zeroext";
    unsigned kind = LLVMGetEnumAttributeKindForName(name, strlen(name));
    return LLVMCreateEnumAttribute(ib2.context, kind, 0);
}

/* Splits a "|"-terminated list in place; returns the item count. */
static size_t ib2_split(char *copy, char **items, size_t cap) {
    size_t count = 0;
    char *start = copy;
    for (char *c = copy; *c; c++) {
        if (*c != '|') continue;
        *c = '\0';
        if (count < cap) items[count] = start;
        count++;
        start = c + 1;
    }
    return count;
}

#define IB2_MAX_TYPED 64

typedef struct {
    LLVMTypeRef type;
    LLVMTypeRef params[IB2_MAX_TYPED];
    int attrs[IB2_MAX_TYPED];
    char *names[IB2_MAX_TYPED];
    size_t count;
    char *copy;
} ib2_signature;

/* `params` items are "TYPE[ ATTR][ NAME]". */
static int ib2_signature_parse(ib2_signature *sig, const char *ret, const char *params, int named) {
    memset(sig, 0, sizeof(*sig));
    sig->copy = strdup(params);
    if (!sig->copy) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    char *items[IB2_MAX_TYPED];
    sig->count = ib2_split(sig->copy, items, IB2_MAX_TYPED);
    if (sig->count > IB2_MAX_TYPED) { ib2_fail("IRBuilder: more than %d C parameters", IB2_MAX_TYPED); return 0; }
    for (size_t i = 0; i < sig->count; i++) {
        /* TYPE, then an optional signext/zeroext, then the value or name
         * (which may itself contain spaces: a constant GEP expression). */
        char *item = items[i];
        char *rest = item;
        while (*rest && *rest != ' ') rest++;
        if (*rest) *rest++ = '\0';
        while (*rest == ' ') rest++;
        sig->attrs[i] = 0;
        if (strncmp(rest, "signext", 7) == 0 && (rest[7] == ' ' || !rest[7])) { sig->attrs[i] = 1; rest += 7; }
        else if (strncmp(rest, "zeroext", 7) == 0 && (rest[7] == ' ' || !rest[7])) { sig->attrs[i] = 2; rest += 7; }
        while (*rest == ' ') rest++;
        sig->params[i] = ib2_type_named(item, NULL);
        sig->names[i] = NULL;
        if (named) {
            if (!*rest) { ib2_fail("IRBuilder: typed operand without a value"); return 0; }
            sig->names[i] = rest;
        }
    }
    LLVMTypeRef r = ib2_type_named(ret, NULL);
    if (ib2_failed()) return 0;
    sig->type = LLVMFunctionType(r, sig->params, (unsigned)sig->count, 0);
    return 1;
}

int64_t freak_ib2_declare_typed(freak_word symbol, freak_word ret, freak_word params) {
    if (ib2_failed()) return 0;
    const char *bare = ib2_bare(ib2_cstr(symbol));
    if (LLVMGetNamedFunction(ib2.module, bare)) return 1;
    ib2_signature sig;
    if (!ib2_signature_parse(&sig, ib2_cstr(ret), ib2_cstr(params), 0)) { free(sig.copy); return 0; }
    LLVMValueRef fn = LLVMAddFunction(ib2.module, bare, sig.type);
    for (size_t i = 0; i < sig.count; i++) {
        if (sig.attrs[i]) LLVMAddAttributeAtIndex(fn, (unsigned)i + 1, ib2_ext_attribute(sig.attrs[i]));
    }
    free(sig.copy);
    return 1;
}

/* An internal `ptr` global initialized to null (a load= symbol cache). */
int64_t freak_ib2_global_pointer(freak_word name) {
    if (ib2_failed()) return 0;
    const char *bare = ib2_bare(ib2_cstr(name));
    if (LLVMGetNamedGlobal(ib2.module, bare)) return 1;
    LLVMValueRef g = LLVMAddGlobal(ib2.module, ib2.ptr, bare);
    LLVMSetInitializer(g, LLVMConstNull(ib2.ptr));
    LLVMSetLinkage(g, LLVMInternalLinkage);
    return 1;
}

/* `define internal RET @symbol(TYPE ATTR %name, ...)`, no debug scope. */
int64_t freak_ib2_begin_function_typed(freak_word symbol, freak_word ret, freak_word params) {
    if (ib2_failed()) return 0;
    const char *sym = ib2_bare(ib2_cstr(symbol));
    ib2_signature sig;
    if (!ib2_signature_parse(&sig, ib2_cstr(ret), ib2_cstr(params), 1)) { free(sig.copy); return 0; }
    LLVMValueRef fn = LLVMGetNamedFunction(ib2.module, sym);
    if (fn) { ib2_fail("IRBuilder: @%s defined twice", sym); free(sig.copy); return 0; }
    fn = LLVMAddFunction(ib2.module, sym, sig.type);
    LLVMSetLinkage(fn, LLVMInternalLinkage);
    ib2_table_clear(&ib2.values);
    ib2_table_clear(&ib2.blocks);
    ib2.function = fn;
    ib2.function_returns = 3;
    ib2.dead_blocks = 0;
    for (size_t i = 0; i < sig.count; i++) {
        LLVMValueRef p = LLVMGetParam(fn, (unsigned)i);
        const char *name = sig.names[i];
        LLVMSetValueName2(p, ib2_bare(name), strlen(ib2_bare(name)));
        ib2_table_put(&ib2.values, name, p);
        if (sig.attrs[i]) LLVMAddAttributeAtIndex(fn, (unsigned)i + 1, ib2_ext_attribute(sig.attrs[i]));
    }
    free(sig.copy);
    ib2.di_scope = NULL;
    ib2.line = 0;
    LLVMClearInsertionPosition(ib2.builder);
    LLVMSetCurrentDebugLocation2(ib2.builder, NULL);
    return 1;
}

/* `call RET CALLEE(TYPE ATTR VALUE, ...)`; CALLEE is @symbol or a local
 * function pointer. The call carries its own function type. */
int64_t freak_ib2_call_typed(freak_word dest, freak_word callee, freak_word ret, freak_word arguments) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *name = ib2_cstr(callee);
    ib2_signature sig;
    if (!ib2_signature_parse(&sig, ib2_cstr(ret), ib2_cstr(arguments), 1)) { free(sig.copy); return 0; }
    LLVMValueRef fn;
    if (name[0] == '%') {
        fn = ib2_value(name, ib2.ptr);
    } else {
        fn = ib2_global_value(name);
        if (!fn) {
            fn = LLVMAddFunction(ib2.module, ib2_bare(name), sig.type);
            for (size_t i = 0; i < sig.count; i++) {
                if (sig.attrs[i]) LLVMAddAttributeAtIndex(fn, (unsigned)i + 1, ib2_ext_attribute(sig.attrs[i]));
            }
        }
    }
    LLVMValueRef args[IB2_MAX_TYPED];
    for (size_t i = 0; i < sig.count; i++) args[i] = ib2_value(sig.names[i], sig.params[i]);
    const char *result = ib2_cstr(dest);
    if (!ib2_failed()) {
        int is_void = LLVMGetReturnType(sig.type) == ib2.void_type;
        LLVMValueRef call = LLVMBuildCall2(ib2.builder, sig.type, fn, args, (unsigned)sig.count,
                                           is_void ? "" : ib2_bare(result));
        for (size_t i = 0; i < sig.count; i++) {
            if (sig.attrs[i]) LLVMAddCallSiteAttribute(call, (unsigned)i + 1, ib2_ext_attribute(sig.attrs[i]));
        }
        if (!is_void && result[0]) ib2_define(result, call);
        else if (result[0] && is_void) ib2_fail("IRBuilder: %s takes the result of void %s", result, name);
    }
    free(sig.copy);
    return ib2_failed() ? 0 : 1;
}

/* `DEST = OP FROM VALUE to TO` for trunc/sext/zext/fptrunc/fpext/inttoptr/
 * ptrtoint/bitcast. */
int64_t freak_ib2_convert(freak_word dest, freak_word operation, freak_word from, freak_word value, freak_word to) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    const char *result = ib2_cstr(dest);
    const char *op = ib2_cstr(operation);
    LLVMTypeRef src = ib2_type_named(ib2_cstr(from), NULL);
    LLVMTypeRef dst = ib2_type_named(ib2_cstr(to), NULL);
    if (ib2_failed()) return 0;
    LLVMValueRef v = ib2_value(ib2_cstr(value), src);
    if (ib2_failed()) return 0;
    LLVMOpcode code;
    if (strcmp(op, "trunc") == 0) code = LLVMTrunc;
    else if (strcmp(op, "sext") == 0) code = LLVMSExt;
    else if (strcmp(op, "zext") == 0) code = LLVMZExt;
    else if (strcmp(op, "fptrunc") == 0) code = LLVMFPTrunc;
    else if (strcmp(op, "fpext") == 0) code = LLVMFPExt;
    else if (strcmp(op, "inttoptr") == 0) code = LLVMIntToPtr;
    else if (strcmp(op, "ptrtoint") == 0) code = LLVMPtrToInt;
    else if (strcmp(op, "bitcast") == 0) code = LLVMBitCast;
    else { ib2_fail("IRBuilder: unknown conversion '%s'", op); return 0; }
    ib2_define(result, LLVMBuildCast(ib2.builder, code, v, dst, ib2_bare(result)));
    return 1;
}

int64_t freak_ib2_ret_typed(freak_word type, freak_word value) {
    if (!ib2_ready()) return 0;
    ib2_before_instruction();
    LLVMTypeRef t = ib2_type_named(ib2_cstr(type), NULL);
    if (ib2_failed()) return 0;
    if (t == ib2.void_type) { LLVMBuildRetVoid(ib2.builder); return 1; }
    LLVMValueRef v = ib2_value(ib2_cstr(value), t);
    if (ib2_failed()) return 0;
    LLVMBuildRet(ib2.builder, v);
    return 1;
}

/* Portable strtok_r(list, "|") (the Windows CRT has no strtok_r). */
static char *ib2_next_item(char **cursor) {
    char *start = *cursor;
    while (*start == '|') start++;
    if (!*start) { *cursor = start; return NULL; }
    char *end = strchr(start, '|');
    if (end) { *end = '\0'; *cursor = end + 1; }
    else *cursor = start + strlen(start);
    return start;
}

/* edges: "edge;reason;operation|..." with message names using '_' for ' '. */
int64_t freak_ib2_integer_failure(freak_word edges) {
    if (ib2_failed()) return 0;
    if (!ib2.function) { ib2_fail("IRBuilder: integer failure block outside a function"); return 0; }
    char *list = strdup(ib2_cstr(edges));
    if (!list) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    LLVMBasicBlockRef fail_block = ib2_block("integer.fail");
    if (LLVMGetBasicBlockParent(fail_block) != NULL) { free(list); ib2_fail("IRBuilder: integer.fail placed twice"); return 0; }
    LLVMAppendExistingBasicBlock(ib2.function, fail_block);
    LLVMPositionBuilderAtEnd(ib2.builder, fail_block);
    ib2_apply_line();
    LLVMValueRef reason = LLVMBuildPhi(ib2.builder, ib2.ptr, "integer.reason");
    LLVMValueRef operation = LLVMBuildPhi(ib2.builder, ib2.ptr, "integer.operation");
    char *cursor = list;
    for (char *item = ib2_next_item(&cursor); item; item = ib2_next_item(&cursor)) {
        char *a = strchr(item, ';');
        char *b = a ? strchr(a + 1, ';') : NULL;
        if (!a || !b) { ib2_fail("IRBuilder: malformed integer failure edge '%s'", item); break; }
        *a = '\0';
        *b = '\0';
        char reason_name[128], operation_name[128];
        snprintf(reason_name, sizeof(reason_name), "__freak_int_%s", a + 1);
        snprintf(operation_name, sizeof(operation_name), "__freak_int_%s", b + 1);
        LLVMValueRef rv = LLVMGetNamedGlobal(ib2.module, reason_name);
        LLVMValueRef ov = LLVMGetNamedGlobal(ib2.module, operation_name);
        if (!rv || !ov) { ib2_fail("IRBuilder: missing integer failure message for '%s'", item); break; }
        LLVMBasicBlockRef from = ib2_block(item);
        LLVMAddIncoming(reason, &rv, &from, 1);
        LLVMAddIncoming(operation, &ov, &from, 1);
    }
    free(list);
    if (ib2_failed()) return 0;
    LLVMValueRef fail_fn = LLVMGetNamedFunction(ib2.module, "__freak_int_fail");
    if (!fail_fn) { ib2_fail("IRBuilder: __freak_int_fail is not declared"); return 0; }
    LLVMValueRef args[2] = { reason, operation };
    LLVMBuildCall2(ib2.builder, LLVMGlobalGetValueType(fail_fn), fail_fn, args, 2, "");
    LLVMBuildUnreachable(ib2.builder);
    return 1;
}

/* ------------------------------------------------------------------ */
/* Finish: verify, optimize, emit                                      */
/* ------------------------------------------------------------------ */

static int ib2_targets_ready;

static void ib2_init_targets(void) {
    if (ib2_targets_ready) return;
    LLVMInitializeX86TargetInfo();
    LLVMInitializeX86Target();
    LLVMInitializeX86TargetMC();
    LLVMInitializeX86AsmPrinter();
    LLVMInitializeAArch64TargetInfo();
    LLVMInitializeAArch64Target();
    LLVMInitializeAArch64TargetMC();
    LLVMInitializeAArch64AsmPrinter();
    ib2_targets_ready = 1;
}

/* kind 0 = object file, 1 = textual IR, 2 = bitcode. */
int64_t freak_ib2_finish(freak_word output, int64_t kind, freak_word triple, int64_t optimization) {
    if (ib2_failed()) { if (!ib2.error[0]) ib2_fail("IRBuilder: no open module"); ib2_dispose(); return 0; }
    const char *out_path = ib2_cstr(output);
    char *path = strdup(out_path);
    /* triple is "triple;cpu;features;reloc" as probed from clang -###, or a
     * bare triple, or empty for LLVM's default. */
    char *spec = strdup(ib2_cstr(triple));
    if (!path || !spec) { fprintf(stderr, "freak: out of memory in IRBuilder bridge\n"); exit(70); }
    char *fields[4] = { spec, "", "", "" };
    {
        int f = 1;
        for (char *c = spec; *c && f < 4; c++) {
            if (*c == ';') { *c = '\0'; fields[f++] = c + 1; }
        }
    }
    int default_triple = fields[0][0] == '\0';
    char *target_triple = default_triple ? LLVMGetDefaultTargetTriple() : fields[0];
    const char *cpu = fields[1][0] ? fields[1] : "generic";
    const char *features = fields[2];
    const char *reloc_name = fields[3];
    int ok = 0;
    LLVMTargetMachineRef tm = NULL;
    LLVMDIBuilderFinalize(ib2.di);

    char *message = NULL;
    if (LLVMVerifyModule(ib2.module, LLVMReturnStatusAction, &message)) {
        ib2_fail("IRBuilder: module failed verification: %s", message ? message : "(no detail)");
        goto done;
    }
    if (message) { LLVMDisposeMessage(message); message = NULL; }

    ib2_init_targets();
    LLVMTargetRef target = NULL;
    if (LLVMGetTargetFromTriple(target_triple, &target, &message)) {
        ib2_fail("IRBuilder: no LLVM target for %s: %s", target_triple, message ? message : "");
        goto done;
    }
    if (message) { LLVMDisposeMessage(message); message = NULL; }
    if (optimization < 0) optimization = 0;
    if (optimization > 3) optimization = 3;
    LLVMCodeGenOptLevel level = optimization == 0 ? LLVMCodeGenLevelNone
                              : optimization == 1 ? LLVMCodeGenLevelLess
                              : optimization == 2 ? LLVMCodeGenLevelDefault
                              : LLVMCodeGenLevelAggressive;
    int is_windows = strstr(target_triple, "windows") != NULL || strstr(target_triple, "mingw") != NULL;
    LLVMRelocMode reloc = is_windows ? LLVMRelocDefault : LLVMRelocPIC;
    if (strcmp(reloc_name, "pic") == 0) reloc = LLVMRelocPIC;
    else if (strcmp(reloc_name, "static") == 0) reloc = LLVMRelocStatic;
    else if (strcmp(reloc_name, "dynamic-no-pic") == 0) reloc = LLVMRelocDynamicNoPic;
    tm = LLVMCreateTargetMachine(target, target_triple, cpu, features, level, reloc, LLVMCodeModelDefault);
    if (!tm) { ib2_fail("IRBuilder: cannot create a target machine for %s", target_triple); goto done; }
    LLVMSetTarget(ib2.module, target_triple);
    LLVMTargetDataRef layout = LLVMCreateTargetDataLayout(tm);
    LLVMSetModuleDataLayout(ib2.module, layout);
    LLVMDisposeTargetData(layout);

    if (optimization > 0) {
        char pipeline[32];
        snprintf(pipeline, sizeof(pipeline), "default<O%lld>", (long long)optimization);
        LLVMPassBuilderOptionsRef options = LLVMCreatePassBuilderOptions();
        LLVMErrorRef err = LLVMRunPasses(ib2.module, pipeline, tm, options);
        LLVMDisposePassBuilderOptions(options);
        if (err) {
            char *text = LLVMGetErrorMessage(err);
            ib2_fail("IRBuilder: optimization failed: %s", text);
            LLVMDisposeErrorMessage(text);
            goto done;
        }
    }

    if (kind == 1) {
        if (LLVMPrintModuleToFile(ib2.module, path, &message)) {
            ib2_fail("IRBuilder: cannot write %s: %s", path, message ? message : "");
            goto done;
        }
    } else if (kind == 2) {
        if (LLVMWriteBitcodeToFile(ib2.module, path) != 0) {
            ib2_fail("IRBuilder: cannot write %s", path);
            goto done;
        }
    } else {
        if (LLVMTargetMachineEmitToFile(tm, ib2.module, path, LLVMObjectFile, &message)) {
            ib2_fail("IRBuilder: cannot emit %s: %s", path, message ? message : "");
            goto done;
        }
    }
    ok = 1;

done:
    if (message) LLVMDisposeMessage(message);
    if (tm) LLVMDisposeTargetMachine(tm);
    if (default_triple) LLVMDisposeMessage(target_triple);
    free(spec);
    free(path);
    ib2_dispose();
    return ok;
}
