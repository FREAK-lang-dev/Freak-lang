#include "freak_runtime.h"
#include <string.h>

/* --- Global variables --- */
freak_word FREAKC_VERSION = { 0 };
freak_word FREAKC_CODENAME = { 0 };
freak_word input_file = { 0 };
freak_word emit_target = { 0 };
freak_word opt_level = { 0 };
freak_word cross_target = { 0 };

/* --- Forward declarations --- */
static void freak_freakc_v2_main(void);

/* --- Function definitions --- */
static void freak_freakc_v2_main(void) {
    int64_t args_cnt = ((int64_t)freak_argc);
    if ((args_cnt >= ((int64_t)2))) {
        freak_word cli_first_arg = freak_word_lit(freak_argv[((int64_t)1)]);
        if ((freak_word_eq(cli_first_arg, freak_word_lit("--version")) || freak_word_eq(cli_first_arg, freak_word_lit("-V")))) {
            freak_word ver_str = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("freakc "), FREAKC_VERSION), freak_word_lit(" (")), FREAKC_CODENAME), freak_word_lit(")"));
            freak_say(ver_str);
            return;
        }
        if ((freak_word_eq(cli_first_arg, freak_word_lit("--help")) || freak_word_eq(cli_first_arg, freak_word_lit("-h")))) {
            freak_word help_hdr = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("FREAK Compiler "), FREAKC_VERSION), freak_word_lit(" (")), FREAKC_CODENAME), freak_word_lit(")"));
            freak_say(help_hdr);
            freak_say(freak_word_lit(""));
            freak_say(freak_word_lit("Usage: freakc <file.fk> [options]"));
            freak_say(freak_word_lit(""));
            freak_say(freak_word_lit("Options:"));
            freak_say(freak_word_lit("  --llvm             Use LLVM IR backend (default)"));
            freak_say(freak_word_lit("  --c                Use C backend"));
            freak_say(freak_word_lit("  --opt=N            Optimization level 0-3 (default: 2)"));
            freak_say(freak_word_lit("  --target=TRIPLE    Cross-compile target triple"));
            freak_say(freak_word_lit("  --version, -V      Show version"));
            freak_say(freak_word_lit("  --help, -h         Show this help"));
            return;
        }
    }
    if ((args_cnt < ((int64_t)2))) {
        freak_say(freak_word_lit("Usage: freakc <file.fk> [--c] [--llvm] [--opt=N] [--target=TRIPLE]"));
        freak_say(freak_word_lit("       freakc --version | --help"));
        return;
    }
    input_file = freak_word_lit(freak_argv[((int64_t)1)]);
    int64_t fi = ((int64_t)2);
    while (!((fi >= args_cnt))) {
        freak_word flag = freak_word_lit(freak_argv[fi]);
        if (freak_word_eq(flag, freak_word_lit("--c"))) {
            emit_target = freak_word_lit("c");
        } else if (freak_word_eq(flag, freak_word_lit("--llvm"))) {
            emit_target = freak_word_lit("llvm");
        } else if (freak_word_starts_with(flag, freak_word_lit("--opt="))) {
            opt_level = freak_word_char_at(flag, ((int64_t)6));
        } else if (freak_word_starts_with(flag, freak_word_lit("--target="))) {
            int64_t ti = ((int64_t)9);
            freak_word tval = freak_word_lit("");
            while (!((ti >= freak_word_length(flag)))) {
                tval = freak_word_concat(tval, freak_word_char_at(flag, ti));
                ti += ((int64_t)1);
            }
            cross_target = tval;
        }
        fi += ((int64_t)1);
    }
    freak_word msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("FREAK v2 Compiling: "), input_file), freak_word_lit(" (Target: ")), emit_target), freak_word_lit(")"));
    freak_say(msg);
    freak_word src = freak_fs_read(input_file);
    if (freak_word_eq(src, freak_word_lit(""))) {
        freak_say(freak_word_lit("Error: Could not read file."));
        return;
    }
    freak_init_arrays();
    freak_say(freak_word_lit("[1/4] Lexing..."));
    freak_tokenize(src);
    freak_say(freak_word_lit("[2/4] Parsing..."));
    freak_parse_program();
    freak_say(freak_word_lit("[3/4] Type Checking..."));
    freak_check_program();
    freak_say(freak_word_lit("[4/4] Emitting..."));
    if (freak_word_eq(emit_target, freak_word_lit("llvm"))) {
        freak_word out_file = freak_word_concat(input_file, freak_word_lit(".ll"));
        llvm_out_file = out_file;
        freak_fs_write(out_file, freak_word_lit(""));
        freak_emit_llvm_program();
        llvm_out_file = freak_word_lit("");
        freak_word msg2 = freak_word_concat(freak_word_lit("Generated LLVM IR at "), out_file);
        freak_say(msg2);
    } else {
        freak_emit_program();
        freak_word out_file = freak_word_concat(input_file, freak_word_lit(".c"));
        freak_fs_write(out_file, out_buf);
        freak_word msg3 = freak_word_concat(freak_word_lit("Generated C code at "), out_file);
        freak_say(msg3);
    }
}


int freak_main(int argc, char** argv) {
    FREAKC_VERSION = freak_word_lit("0.9.0");
    FREAKC_CODENAME = freak_word_lit("Alternative-4");
    input_file = freak_word_lit("");
    emit_target = freak_word_lit("llvm");
    opt_level = freak_word_lit("2");
    cross_target = freak_word_lit("");
    freak_freakc_v2_main();
    return 0;
}

int main(int argc, char** argv) {
    freak_argc = argc;
    freak_argv = argv;
    (void)argc; (void)argv;
    return freak_main(argc, argv);
}
