#include "freak_runtime.h"
#include <string.h>

/* --- Global variables --- */
freak_word lex_source = { 0 };
int64_t lex_len = 0;
int64_t lex_pos = 0;
int64_t lex_line = 0;
int64_t lex_col = 0;
int64_t cur_tok_line = 0;
int64_t cur_tok_col = 0;

/* --- Forward declarations --- */
static freak_word freak_lex_cur_ch(void);
static freak_word freak_lex_ch_at(int64_t offset);
static freak_word freak_lex_advance(void);
static void freak_push_token(freak_word kind, freak_word val);
static void freak_lex_skip_ws(void);
static bool freak_is_numeric(freak_word c);
static bool freak_is_alphabetic(freak_word c);
static bool freak_is_alnum_ext(freak_word c);
static void freak_lex_number(void);
static bool freak_try_consume_word(freak_word target);
static void freak_lex_ident(void);
static void freak_lex_string(void);
static void freak_tokenize(freak_word source);

/* --- Function definitions --- */
static freak_word freak_lex_cur_ch(void) {
    if ((lex_pos >= lex_len)) {
        return freak_word_lit("");
    }
    return freak_word_char_at(lex_source, lex_pos);
}

static freak_word freak_lex_ch_at(int64_t offset) {
    if (((lex_pos + offset) >= lex_len)) {
        return freak_word_lit("");
    }
    return freak_word_char_at(lex_source, (lex_pos + offset));
}

static freak_word freak_lex_advance(void) {
    if ((lex_pos >= lex_len)) {
        return freak_word_lit("");
    }
    freak_word c = freak_word_char_at(lex_source, lex_pos);
    lex_pos += ((int64_t)1);
    if (freak_word_eq(c, freak_word_lit("\n"))) {
        lex_line += ((int64_t)1);
        lex_col = ((int64_t)1);
    } else {
        lex_col += ((int64_t)1);
    }
    return c;
}

static void freak_push_token(freak_word kind, freak_word val) {
    tok_types = freak_push_item(tok_types, kind, tokens_count);
    tok_vals = freak_push_item(tok_vals, val, tokens_count);
    tok_lines = freak_push_item(tok_lines, freak_word_from_int(cur_tok_line), tokens_count);
    tok_cols = freak_push_item(tok_cols, freak_word_from_int(cur_tok_col), tokens_count);
    tokens_count += ((int64_t)1);
}

static void freak_lex_skip_ws(void) {
    bool fin = false;
    while (!(fin)) {
        freak_word c = freak_lex_cur_ch();
        if ((((freak_word_eq(c, freak_word_lit(" ")) || freak_word_eq(c, freak_word_lit("\n"))) || freak_word_eq(c, freak_word_lit("\r"))) || freak_word_eq(c, freak_word_lit("\t")))) {
            freak_lex_advance();
        } else if (freak_word_eq(c, freak_word_lit("-"))) {
            if (freak_word_eq(freak_lex_ch_at(((int64_t)1)), freak_word_lit("-"))) {
                freak_lex_advance();
                freak_lex_advance();
                bool cline_fin = false;
                while (!(cline_fin)) {
                    freak_word cc = freak_lex_cur_ch();
                    if ((freak_word_eq(cc, freak_word_lit("")) || freak_word_eq(cc, freak_word_lit("\n")))) {
                        cline_fin = true;
                    } else {
                        freak_lex_advance();
                    }
                }
            } else {
                fin = true;
            }
        } else {
            fin = true;
        }
    }
}

static bool freak_is_numeric(freak_word c) {
    if (((((freak_word_eq(c, freak_word_lit("0")) || freak_word_eq(c, freak_word_lit("1"))) || freak_word_eq(c, freak_word_lit("2"))) || freak_word_eq(c, freak_word_lit("3"))) || freak_word_eq(c, freak_word_lit("4")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("5")) || freak_word_eq(c, freak_word_lit("6"))) || freak_word_eq(c, freak_word_lit("7"))) || freak_word_eq(c, freak_word_lit("8"))) || freak_word_eq(c, freak_word_lit("9")))) {
        return true;
    }
    return false;
}

static bool freak_is_alphabetic(freak_word c) {
    if (freak_word_eq(c, freak_word_lit("_"))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("a")) || freak_word_eq(c, freak_word_lit("b"))) || freak_word_eq(c, freak_word_lit("c"))) || freak_word_eq(c, freak_word_lit("d"))) || freak_word_eq(c, freak_word_lit("e")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("f")) || freak_word_eq(c, freak_word_lit("g"))) || freak_word_eq(c, freak_word_lit("h"))) || freak_word_eq(c, freak_word_lit("i"))) || freak_word_eq(c, freak_word_lit("j")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("k")) || freak_word_eq(c, freak_word_lit("l"))) || freak_word_eq(c, freak_word_lit("m"))) || freak_word_eq(c, freak_word_lit("n"))) || freak_word_eq(c, freak_word_lit("o")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("p")) || freak_word_eq(c, freak_word_lit("q"))) || freak_word_eq(c, freak_word_lit("r"))) || freak_word_eq(c, freak_word_lit("s"))) || freak_word_eq(c, freak_word_lit("t")))) {
        return true;
    }
    if ((((((freak_word_eq(c, freak_word_lit("u")) || freak_word_eq(c, freak_word_lit("v"))) || freak_word_eq(c, freak_word_lit("w"))) || freak_word_eq(c, freak_word_lit("x"))) || freak_word_eq(c, freak_word_lit("y"))) || freak_word_eq(c, freak_word_lit("z")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("A")) || freak_word_eq(c, freak_word_lit("B"))) || freak_word_eq(c, freak_word_lit("C"))) || freak_word_eq(c, freak_word_lit("D"))) || freak_word_eq(c, freak_word_lit("E")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("F")) || freak_word_eq(c, freak_word_lit("G"))) || freak_word_eq(c, freak_word_lit("H"))) || freak_word_eq(c, freak_word_lit("I"))) || freak_word_eq(c, freak_word_lit("J")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("K")) || freak_word_eq(c, freak_word_lit("L"))) || freak_word_eq(c, freak_word_lit("M"))) || freak_word_eq(c, freak_word_lit("N"))) || freak_word_eq(c, freak_word_lit("O")))) {
        return true;
    }
    if (((((freak_word_eq(c, freak_word_lit("P")) || freak_word_eq(c, freak_word_lit("Q"))) || freak_word_eq(c, freak_word_lit("r"))) || freak_word_eq(c, freak_word_lit("S"))) || freak_word_eq(c, freak_word_lit("T")))) {
        return true;
    }
    if ((((((freak_word_eq(c, freak_word_lit("U")) || freak_word_eq(c, freak_word_lit("V"))) || freak_word_eq(c, freak_word_lit("W"))) || freak_word_eq(c, freak_word_lit("X"))) || freak_word_eq(c, freak_word_lit("Y"))) || freak_word_eq(c, freak_word_lit("Z")))) {
        return true;
    }
    return false;
}

static bool freak_is_alnum_ext(freak_word c) {
    if (freak_is_alphabetic(c)) {
        return true;
    }
    if (freak_is_numeric(c)) {
        return true;
    }
    return false;
}

static void freak_lex_number(void) {
    freak_word res = freak_word_lit("");
    bool fin = false;
    while (!(fin)) {
        freak_word c = freak_lex_cur_ch();
        if ((freak_is_numeric(c) || freak_word_eq(c, freak_word_lit(".")))) {
            res = freak_word_concat(res, c);
            freak_lex_advance();
        } else {
            fin = true;
        }
    }
    freak_push_token(TOK_NUM, res);
}

static bool freak_try_consume_word(freak_word target) {
    int64_t s_pos = lex_pos;
    int64_t s_line = lex_line;
    int64_t s_col = lex_col;
    freak_lex_skip_ws();
    freak_word res = freak_word_lit("");
    bool fin = false;
    while (!(fin)) {
        freak_word c = freak_lex_cur_ch();
        if (freak_is_alnum_ext(c)) {
            res = freak_word_concat(res, c);
            freak_lex_advance();
        } else {
            fin = true;
        }
    }
    if (freak_word_eq(freak_word_to_lower(res), freak_word_to_lower(target))) {
        return true;
    }
    lex_pos = s_pos;
    lex_line = s_line;
    lex_col = s_col;
    return false;
}

static void freak_lex_ident(void) {
    freak_word res = freak_word_lit("");
    bool fin = false;
    while (!(fin)) {
        freak_word c = freak_lex_cur_ch();
        if (freak_is_alnum_ext(c)) {
            res = freak_word_concat(res, c);
            freak_lex_advance();
        } else {
            fin = true;
        }
    }
    freak_word lower = freak_word_to_lower(res);
    if (freak_word_eq(lower, freak_word_lit("give"))) {
        if (freak_try_consume_word(freak_word_lit("back"))) {
            freak_push_token(TOK_KW, freak_word_lit("give back"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("or"))) {
        if (freak_try_consume_word(freak_word_lit("else"))) {
            freak_push_token(TOK_KW, freak_word_lit("or else"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("trust"))) {
        if (freak_try_consume_word(freak_word_lit("me"))) {
            freak_push_token(TOK_KW, freak_word_lit("trust me"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("for"))) {
        if (freak_try_consume_word(freak_word_lit("each"))) {
            freak_push_token(TOK_KW, freak_word_lit("for each"));
            return;
        }
        if (freak_try_consume_word(freak_word_lit("science"))) {
            freak_push_token(TOK_KW, freak_word_lit("for science"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("training"))) {
        if (freak_try_consume_word(freak_word_lit("arc"))) {
            freak_push_token(TOK_KW, freak_word_lit("training arc"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("on"))) {
        int64_t s_pos = lex_pos;
        int64_t s_line = lex_line;
        int64_t s_col = lex_col;
        if (freak_try_consume_word(freak_word_lit("my"))) {
            if (freak_try_consume_word(freak_word_lit("honor"))) {
                if (freak_try_consume_word(freak_word_lit("as"))) {
                    freak_push_token(TOK_KW, freak_word_lit("on my honor as"));
                    return;
                }
            }
        }
        lex_pos = s_pos;
        lex_line = s_line;
        lex_col = s_col;
    }
    if (freak_word_eq(lower, freak_word_lit("knowing"))) {
        int64_t s_pos = lex_pos;
        int64_t s_line = lex_line;
        int64_t s_col = lex_col;
        if (freak_try_consume_word(freak_word_lit("this"))) {
            if (freak_try_consume_word(freak_word_lit("will"))) {
                if (freak_try_consume_word(freak_word_lit("hurt"))) {
                    freak_push_token(TOK_KW, freak_word_lit("knowing this will hurt"));
                    return;
                }
            }
        }
        lex_pos = s_pos;
        lex_line = s_line;
        lex_col = s_col;
    }
    if (freak_word_eq(lower, freak_word_lit("plus"))) {
        if (freak_try_consume_word(freak_word_lit("ultra"))) {
            freak_push_token(TOK_KW, freak_word_lit("PLUS ULTRA"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("final"))) {
        if (freak_try_consume_word(freak_word_lit("form"))) {
            freak_push_token(TOK_KW, freak_word_lit("FINAL FORM"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("bringing"))) {
        if (freak_try_consume_word(freak_word_lit("back"))) {
            freak_push_token(TOK_KW, freak_word_lit("bringing back"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("only"))) {
        if (freak_try_consume_word(freak_word_lit("on"))) {
            freak_push_token(TOK_KW, freak_word_lit("only on"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("prob"))) {
        if (freak_try_consume_word(freak_word_lit("when"))) {
            freak_push_token(TOK_KW, freak_word_lit("prob when"));
            return;
        }
    }
    if (freak_word_eq(lower, freak_word_lit("declare"))) {
        if (freak_try_consume_word(freak_word_lit("was"))) {
            freak_push_token(TOK_KW, freak_word_lit("declare was"));
            return;
        }
    }
    if (((((((((((((((((((((((((((((((((((((((((((((((freak_word_eq(lower, freak_word_lit("pilot")) || freak_word_eq(lower, freak_word_lit("fixed"))) || freak_word_eq(lower, freak_word_lit("task"))) || freak_word_eq(lower, freak_word_lit("say"))) || freak_word_eq(lower, freak_word_lit("shape"))) || freak_word_eq(lower, freak_word_lit("impl"))) || freak_word_eq(lower, freak_word_lit("doctrine"))) || freak_word_eq(lower, freak_word_lit("launch"))) || freak_word_eq(lower, freak_word_lit("use"))) || freak_word_eq(lower, freak_word_lit("as"))) || freak_word_eq(lower, freak_word_lit("in"))) || freak_word_eq(lower, freak_word_lit("lend"))) || freak_word_eq(lower, freak_word_lit("mut"))) || freak_word_eq(lower, freak_word_lit("move"))) || freak_word_eq(lower, freak_word_lit("copy"))) || freak_word_eq(lower, freak_word_lit("break"))) || freak_word_eq(lower, freak_word_lit("continue"))) || freak_word_eq(lower, freak_word_lit("if"))) || freak_word_eq(lower, freak_word_lit("else"))) || freak_word_eq(lower, freak_word_lit("when"))) || freak_word_eq(lower, freak_word_lit("repeat"))) || freak_word_eq(lower, freak_word_lit("times"))) || freak_word_eq(lower, freak_word_lit("until"))) || freak_word_eq(lower, freak_word_lit("done"))) || freak_word_eq(lower, freak_word_lit("for"))) || freak_word_eq(lower, freak_word_lit("each"))) || freak_word_eq(lower, freak_word_lit("check"))) || freak_word_eq(lower, freak_word_lit("result"))) || freak_word_eq(lower, freak_word_lit("got"))) || freak_word_eq(lower, freak_word_lit("nobody"))) || freak_word_eq(lower, freak_word_lit("some"))) || freak_word_eq(lower, freak_word_lit("ok"))) || freak_word_eq(lower, freak_word_lit("err"))) || freak_word_eq(lower, freak_word_lit("sessions"))) || freak_word_eq(lower, freak_word_lit("max"))) || freak_word_eq(lower, freak_word_lit("foreshadow"))) || freak_word_eq(lower, freak_word_lit("payoff"))) || freak_word_eq(lower, freak_word_lit("route"))) || freak_word_eq(lower, freak_word_lit("sadly"))) || freak_word_eq(lower, freak_word_lit("deus_ex_machina"))) || freak_word_eq(lower, freak_word_lit("isekai"))) || freak_word_eq(lower, freak_word_lit("eventually"))) || freak_word_eq(lower, freak_word_lit("and"))) || freak_word_eq(lower, freak_word_lit("or"))) || freak_word_eq(lower, freak_word_lit("not"))) || freak_word_eq(lower, freak_word_lit("NAKAMA"))) || freak_word_eq(lower, freak_word_lit("TSUNDERE")))) {
        freak_push_token(TOK_KW, res);
    } else if ((((((freak_word_eq(lower, freak_word_lit("true")) || freak_word_eq(lower, freak_word_lit("false"))) || freak_word_eq(lower, freak_word_lit("yes"))) || freak_word_eq(lower, freak_word_lit("no"))) || freak_word_eq(lower, freak_word_lit("hai"))) || freak_word_eq(lower, freak_word_lit("iie")))) {
        freak_push_token(TOK_BOOL, res);
    } else {
        freak_push_token(TOK_IDENT, res);
    }
}

static void freak_lex_string(void) {
    freak_lex_advance();
    freak_word res = freak_word_lit("");
    bool fin = false;
    while (!(fin)) {
        freak_word c = freak_lex_advance();
        if (freak_word_eq(c, freak_word_lit("\""))) {
            fin = true;
        } else if (freak_word_eq(c, freak_word_lit(""))) {
            fin = true;
        } else if (freak_word_eq(c, freak_word_lit("\\"))) {
            freak_word esc = freak_lex_advance();
            if (freak_word_eq(esc, freak_word_lit("n"))) {
                res = freak_word_concat(res, freak_word_lit("\n"));
            } else if (freak_word_eq(esc, freak_word_lit("t"))) {
                res = freak_word_concat(res, freak_word_lit("\t"));
            } else {
                res = freak_word_concat(res, esc);
            }
        } else {
            res = freak_word_concat(res, c);
        }
    }
    freak_push_token(TOK_STR, res);
}

static void freak_tokenize(freak_word source) {
    lex_source = source;
    lex_len = freak_word_length(source);
    freak_word len_msg = freak_word_lit("Source length: ");
    len_msg = freak_word_concat(len_msg, freak_word_from_int(freak_word_from_int(lex_len)));
    freak_say(len_msg);
    lex_pos = ((int64_t)0);
    lex_line = ((int64_t)1);
    lex_col = ((int64_t)1);
    tok_types = freak_word_lit("");
    tok_vals = freak_word_lit("");
    tok_lines = freak_word_lit("");
    tok_cols = freak_word_lit("");
    bool fin = false;
    while (!(fin)) {
        freak_lex_skip_ws();
        cur_tok_line = lex_line;
        cur_tok_col = lex_col;
        if ((lex_pos >= lex_len)) {
            fin = true;
        } else {
            freak_word c = freak_lex_cur_ch();
            if (freak_is_numeric(c)) {
                freak_lex_number();
            } else if (freak_is_alphabetic(c)) {
                freak_lex_ident();
            } else if (freak_word_eq(c, freak_word_lit("\""))) {
                freak_lex_string();
            } else if (((((((((((((freak_word_eq(c, freak_word_lit("=")) || freak_word_eq(c, freak_word_lit("+"))) || freak_word_eq(c, freak_word_lit("-"))) || freak_word_eq(c, freak_word_lit("*"))) || freak_word_eq(c, freak_word_lit("/"))) || freak_word_eq(c, freak_word_lit("<"))) || freak_word_eq(c, freak_word_lit(">"))) || freak_word_eq(c, freak_word_lit("!"))) || freak_word_eq(c, freak_word_lit(":"))) || freak_word_eq(c, freak_word_lit("|"))) || freak_word_eq(c, freak_word_lit("%"))) || freak_word_eq(c, freak_word_lit("@"))) || freak_word_eq(c, freak_word_lit("?")))) {
                freak_word op = c;
                freak_lex_advance();
                freak_word next_c = freak_lex_cur_ch();
                bool double_ = false;
                if ((freak_word_eq(op, freak_word_lit("=")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("!")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("<")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit(">")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("+")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("-")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("*")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("/")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("%")) && freak_word_eq(next_c, freak_word_lit("=")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("-")) && freak_word_eq(next_c, freak_word_lit(">")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("=")) && freak_word_eq(next_c, freak_word_lit(">")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("*")) && freak_word_eq(next_c, freak_word_lit("*")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("|")) && freak_word_eq(next_c, freak_word_lit(">")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit("|")) && freak_word_eq(next_c, freak_word_lit("|")))) {
                    double_ = true;
                } else if ((freak_word_eq(op, freak_word_lit(":")) && freak_word_eq(next_c, freak_word_lit(":")))) {
                    double_ = true;
                }
                if (double_) {
                    op = freak_word_concat(op, next_c);
                    freak_lex_advance();
                }
                freak_push_token(TOK_PUNCT, op);
            } else if ((((((((freak_word_eq(c, freak_word_lit("{")) || freak_word_eq(c, freak_word_lit("}"))) || freak_word_eq(c, freak_word_lit("("))) || freak_word_eq(c, freak_word_lit(")"))) || freak_word_eq(c, freak_word_lit("["))) || freak_word_eq(c, freak_word_lit("]"))) || freak_word_eq(c, freak_word_lit(","))) || freak_word_eq(c, freak_word_lit(".")))) {
                freak_push_token(TOK_PUNCT, c);
                freak_lex_advance();
            } else {
                freak_push_token(TOK_PUNCT, c);
                freak_lex_advance();
            }
        }
    }
    freak_push_token(TOK_EOF, freak_word_lit(""));
}


int freak_main(int argc, char** argv) {
    lex_source = freak_word_lit("");
    lex_len = ((int64_t)0);
    lex_pos = ((int64_t)0);
    lex_line = ((int64_t)1);
    lex_col = ((int64_t)1);
    cur_tok_line = ((int64_t)1);
    cur_tok_col = ((int64_t)1);
    return 0;
}

int main(int argc, char** argv) {
    freak_argc = argc;
    freak_argv = argv;
    (void)argc; (void)argv;
    return freak_main(argc, argv);
}
