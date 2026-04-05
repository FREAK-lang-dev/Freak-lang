#include "freak_runtime.h"
void freak_init_arrays(void);
int64_t freak_alloc_expr(freak_word kind, freak_word val, freak_word left, freak_word right);
int64_t freak_alloc_stmt(freak_word kind, freak_word name, freak_word expr_id, freak_word body_id, freak_word else_body, freak_word extra, freak_word params, freak_word returns);
void freak_register_shape(freak_word name, freak_word fields);
bool freak_is_shape_name(freak_word name);
freak_word freak_get_shape_fields(freak_word name);
int64_t freak_get_shape_field_count(freak_word shape_name);
int64_t freak_get_shape_field_index(freak_word shape_name, freak_word field_name);
void freak_emit(freak_word s);
void freak_emit_line(freak_word s);
void freak_emt_set_var_type(freak_word name, freak_word vtype);
freak_word freak_emt_get_var_type(freak_word name);
void freak_emt_register_word_task(freak_word name);
bool freak_emt_is_word_task(freak_word name);
void freak_emt_register_extern(freak_word name, freak_word ret);
bool freak_emt_is_extern(freak_word name);
freak_word freak_emt_get_extern_ret(freak_word name);
bool freak_is_ast_word(freak_word id);
freak_word freak_get_source_line(int64_t n);
freak_word freak_diag_make_caret(int64_t col);
freak_word freak_friendly_tok(freak_word ttype, freak_word tval);
void freak_diag_error(freak_word msg, freak_word hint);
freak_word freak_lex_cur_ch(void);
freak_word freak_lex_ch_at(int64_t offset);
freak_word freak_lex_advance(void);
void freak_push_token(freak_word kind, freak_word val);
void freak_lex_skip_ws(void);
bool freak_is_numeric(freak_word c);
bool freak_is_alphabetic(freak_word c);
bool freak_is_alnum_ext(freak_word c);
void freak_lex_number(void);
bool freak_try_consume_word(freak_word target);
void freak_lex_ident(void);
void freak_lex_string(void);
void freak_lex_operators(void);
void freak_tokenize(freak_word source);
freak_word freak_cur_tok_type(void);
freak_word freak_cur_tok_val(void);
void freak_advance_tok(void);
bool freak_match_tok(freak_word type, freak_word val);
void freak_expect_tok(freak_word type, freak_word val);
int64_t freak_parse_primary(void);
int64_t freak_parse_postfix(void);
int64_t freak_parse_unary(void);
int64_t freak_parse_mul(void);
int64_t freak_parse_add(void);
int64_t freak_parse_comparison(void);
int64_t freak_parse_and(void);
int64_t freak_parse_expr(void);
freak_word freak_parse_block(void);
int64_t freak_parse_stmt(void);
freak_word freak_parse_params(void);
int64_t freak_parse_shape(void);
int64_t freak_parse_impl(void);
int64_t freak_parse_when(void);
int64_t freak_parse_extern(void);
int64_t freak_parse_task_def(void);
void freak_parse_program(void);
void freak_check_program(void);
freak_word freak_c_safe_ident(freak_word s);
void freak_emit_args(freak_word args);
freak_word freak_c_map_call(freak_word val);
void freak_emit_expr(freak_word id);
void freak_emit_c_string(freak_word val);
void freak_emit_c_call(freak_word val, freak_word left);
void freak_emit_c_method(freak_word val, freak_word left, freak_word right);
void freak_emit_c_field(freak_word val, freak_word left);
void freak_emit_c_binop(freak_word val, freak_word left, freak_word right);
void freak_emit_c_unaryop(freak_word val, freak_word left);
void freak_emit_block(freak_word block);
void freak_emit_stmt(freak_word eid);
void freak_emit_stmt_pilot(freak_word eid);
void freak_emit_stmt_when(freak_word eid);
freak_word freak_translate_params(freak_word p);
freak_word freak_c_ret_type(freak_word returns_w);
void freak_emit_task(freak_word eid);
void freak_register_param_types(freak_word params_w);
void freak_emit_global_decl(freak_word eid);
void freak_emit_global_init(freak_word eid);
void freak_emit_fwd_decl(freak_word eid);
void freak_emit_extern_decl(freak_word eid);
void freak_emit_c_program(void);
void freak_llvm_emit(freak_word s);
void freak_llvm_emit_line(freak_word s);
freak_word freak_next_reg(void);
freak_word freak_llvm_escape_str(freak_word s);
freak_word freak_register_string_literal(freak_word val);
freak_word freak_llvm_c_safe_ident(freak_word s);
void freak_llvm_set_var_type(freak_word name, freak_word vtype);
freak_word freak_llvm_get_var_type(freak_word name);
void freak_llvm_register_task(freak_word name, freak_word ret_type);
freak_word freak_llvm_get_task_ret_type(freak_word name);
bool freak_llvm_is_global(freak_word vname);
void freak_llvm_reg_var(freak_word freak_name, freak_word llvm_name);
freak_word freak_llvm_get_llvm_name(freak_word freak_name);
freak_word freak_llvm_var_ptr(freak_word vname);
bool freak_llvm_is_runtime_func(freak_word fname);
freak_word freak_llvm_infer_expr_type(freak_word expr_id);
freak_word freak_llvm_infer_field_type(freak_word field_name);
freak_word freak_llvm_infer_call_type(freak_word val);
freak_word freak_llvm_i64_to_double(freak_word i64_reg);
freak_word freak_llvm_double_to_i64(freak_word dbl_reg);
bool freak_llvm_is_num_expr(freak_word expr_id);
freak_word freak_llvm_map_call_name(freak_word val);
bool freak_llvm_is_void_call(freak_word val);
freak_word freak_llvm_emit_args(freak_word args);
freak_word freak_llvm_emit_expr(freak_word id);
freak_word freak_llvm_emit_call(freak_word val, freak_word left);
freak_word freak_llvm_emit_shape_ctor(freak_word val, freak_word left);
freak_word freak_llvm_emit_binop(freak_word val, freak_word left, freak_word right, freak_word id);
freak_word freak_llvm_emit_add(freak_word l_reg, freak_word r_reg, freak_word res_reg, freak_word left, freak_word right, freak_word id, bool is_num_op);
freak_word freak_llvm_emit_arith(freak_word l_reg, freak_word r_reg, freak_word res_reg, bool is_num_op, freak_word int_op, freak_word float_op);
freak_word freak_llvm_emit_cmp(freak_word l_reg, freak_word r_reg, freak_word res_reg, freak_word left, bool is_num_op, freak_word int_cmp, freak_word float_cmp);
freak_word freak_llvm_emit_icmp(freak_word l_reg, freak_word r_reg, freak_word res_reg, bool is_num_op, freak_word int_cmp, freak_word float_cmp);
freak_word freak_llvm_emit_unaryop(freak_word val, freak_word left);
freak_word freak_llvm_emit_method(freak_word val, freak_word left, freak_word right);
freak_word freak_llvm_emit_field(freak_word val, freak_word left);
void freak_llvm_emit_block(freak_word block);
void freak_llvm_emit_stmt(freak_word eid);
void freak_llvm_emit_stmt_pilot(freak_word eid);
void freak_llvm_emit_stmt_if(freak_word eid);
void freak_llvm_emit_stmt_repeat(freak_word eid);
void freak_llvm_emit_stmt_training_arc(freak_word eid);
void freak_llvm_emit_stmt_assign(freak_word eid);
void freak_llvm_emit_stmt_when(freak_word eid);
bool freak_llvm_str_has_interp(freak_word val);
void freak_llvm_emit_say_interp(freak_word val);
freak_word freak_llvm_translate_params(freak_word p);
void freak_llvm_allocate_params(freak_word p);
void freak_llvm_emit_task(freak_word eid);
void freak_llvm_emit_runtime_decls(void);
void freak_emit_llvm_program(void);
void freak_freakc_v3_main(void);
freak_word FREAKC_VERSION = FREAK_WORD_EMPTY;
freak_word FREAKC_CODENAME = FREAK_WORD_EMPTY;
freak_word TOK_EOF = FREAK_WORD_EMPTY;
freak_word TOK_IDENT = FREAK_WORD_EMPTY;
freak_word TOK_NUM = FREAK_WORD_EMPTY;
freak_word TOK_STR = FREAK_WORD_EMPTY;
freak_word TOK_BOOL = FREAK_WORD_EMPTY;
freak_word TOK_PUNCT = FREAK_WORD_EMPTY;
freak_word TOK_KW = FREAK_WORD_EMPTY;
int64_t tok_types = 0;
int64_t tok_vals = 0;
int64_t tok_lines = 0;
int64_t tok_cols = 0;
int64_t tokens_count = 0;
freak_word EXPR_INT = FREAK_WORD_EMPTY;
freak_word EXPR_FLOAT = FREAK_WORD_EMPTY;
freak_word EXPR_STR = FREAK_WORD_EMPTY;
freak_word EXPR_BOOL = FREAK_WORD_EMPTY;
freak_word EXPR_IDENT = FREAK_WORD_EMPTY;
freak_word EXPR_BINOP = FREAK_WORD_EMPTY;
freak_word EXPR_UNARYOP = FREAK_WORD_EMPTY;
freak_word EXPR_CALL = FREAK_WORD_EMPTY;
freak_word EXPR_METHOD = FREAK_WORD_EMPTY;
freak_word EXPR_FIELD = FREAK_WORD_EMPTY;
freak_word EXPR_INDEX = FREAK_WORD_EMPTY;
int64_t ast_expr_kinds = 0;
int64_t ast_expr_vals = 0;
int64_t ast_expr_lefts = 0;
int64_t ast_expr_rights = 0;
freak_word STMT_PILOT = FREAK_WORD_EMPTY;
freak_word STMT_SAY = FREAK_WORD_EMPTY;
freak_word STMT_TASK = FREAK_WORD_EMPTY;
freak_word STMT_GIVE_BACK = FREAK_WORD_EMPTY;
freak_word STMT_IF = FREAK_WORD_EMPTY;
freak_word STMT_ASSIGN = FREAK_WORD_EMPTY;
freak_word STMT_EXPR = FREAK_WORD_EMPTY;
freak_word STMT_REPEAT = FREAK_WORD_EMPTY;
freak_word STMT_TRAINING_ARC = FREAK_WORD_EMPTY;
freak_word STMT_WHEN = FREAK_WORD_EMPTY;
freak_word STMT_BLOCK = FREAK_WORD_EMPTY;
freak_word STMT_SHAPE = FREAK_WORD_EMPTY;
freak_word STMT_BREAK = FREAK_WORD_EMPTY;
freak_word STMT_CONTINUE = FREAK_WORD_EMPTY;
freak_word STMT_EVENTUALLY = FREAK_WORD_EMPTY;
freak_word STMT_EXTERN = FREAK_WORD_EMPTY;
int64_t ast_stmt_kinds = 0;
int64_t ast_stmt_names = 0;
int64_t ast_stmt_exprs = 0;
int64_t ast_stmt_bodies = 0;
int64_t ast_stmt_else_bodies = 0;
int64_t ast_stmt_extras = 0;
int64_t ast_task_params = 0;
int64_t ast_task_returns = 0;
int64_t ast_top_stmts = 0;
int64_t shape_registry_names = 0;
int64_t shape_registry_fields = 0;
int64_t shape_registry_count = 0;
freak_word lex_source = FREAK_WORD_EMPTY;
int64_t lex_len = 0;
int64_t lex_pos = 0;
int64_t lex_line = 0;
int64_t lex_col = 0;
int64_t cur_tok_line = 0;
int64_t cur_tok_col = 0;
int64_t parse_idx = 0;
int64_t tok_total = 0;
int64_t parse_error_count = 0;
int64_t error_count = 0;
int64_t next_expr_id = 0;
int64_t next_stmt_id = 0;
freak_word out_file = FREAK_WORD_EMPTY;
freak_word emit_target = FREAK_WORD_EMPTY;
int64_t emt_var_names = 0;
int64_t emt_var_types = 0;
int64_t emt_var_count = 0;
int64_t emt_word_tasks = 0;
int64_t emt_word_task_count = 0;
int64_t emt_extern_names = 0;
int64_t emt_extern_rets = 0;
int64_t emt_extern_count = 0;
int64_t llvm_line_count = 0;
int64_t temp_reg_counter = 0;
freak_word string_literals = FREAK_WORD_EMPTY;
int64_t string_literals_count = 0;
freak_word llvm_var_names = FREAK_WORD_EMPTY;
freak_word llvm_var_types = FREAK_WORD_EMPTY;
freak_word llvm_task_reg_names = FREAK_WORD_EMPTY;
freak_word llvm_task_reg_types = FREAK_WORD_EMPTY;
int64_t llvm_task_reg_count = 0;
bool llvm_cur_func_is_void = false;
freak_word llvm_declared_funcs = FREAK_WORD_EMPTY;
freak_word llvm_loop_end_label = FREAK_WORD_EMPTY;
freak_word llvm_loop_cond_label = FREAK_WORD_EMPTY;
freak_word llvm_global_names = FREAK_WORD_EMPTY;
freak_word llvm_var_reg_map = FREAK_WORD_EMPTY;
freak_word input_file = FREAK_WORD_EMPTY;
freak_word opt_level = FREAK_WORD_EMPTY;
freak_word cross_target = FREAK_WORD_EMPTY;
void freak_init_arrays(void) {
tok_types = freak_array_new();
tok_vals = freak_array_new();
tok_lines = freak_array_new();
tok_cols = freak_array_new();
ast_expr_kinds = freak_array_new();
ast_expr_vals = freak_array_new();
ast_expr_lefts = freak_array_new();
ast_expr_rights = freak_array_new();
ast_stmt_kinds = freak_array_new();
ast_stmt_names = freak_array_new();
ast_stmt_exprs = freak_array_new();
ast_stmt_bodies = freak_array_new();
ast_stmt_else_bodies = freak_array_new();
ast_stmt_extras = freak_array_new();
ast_task_params = freak_array_new();
ast_task_returns = freak_array_new();
ast_top_stmts = freak_array_new();
shape_registry_names = freak_array_new();
shape_registry_fields = freak_array_new();
emt_var_names = freak_array_new();
emt_var_types = freak_array_new();
emt_word_tasks = freak_array_new();
emt_extern_names = freak_array_new();
emt_extern_rets = freak_array_new();
}
int64_t freak_alloc_expr(freak_word kind, freak_word val, freak_word left, freak_word right) {
int64_t id = next_expr_id;
next_expr_id += 1;
freak_array_push(ast_expr_kinds, kind);
freak_array_push(ast_expr_vals, val);
freak_array_push(ast_expr_lefts, left);
freak_array_push(ast_expr_rights, right);
return id;
}
int64_t freak_alloc_stmt(freak_word kind, freak_word name, freak_word expr_id, freak_word body_id, freak_word else_body, freak_word extra, freak_word params, freak_word returns) {
int64_t id = next_stmt_id;
next_stmt_id += 1;
freak_array_push(ast_stmt_kinds, kind);
freak_array_push(ast_stmt_names, name);
freak_array_push(ast_stmt_exprs, expr_id);
freak_array_push(ast_stmt_bodies, body_id);
freak_array_push(ast_stmt_else_bodies, else_body);
freak_array_push(ast_stmt_extras, extra);
freak_array_push(ast_task_params, params);
freak_array_push(ast_task_returns, returns);
return id;
}
void freak_register_shape(freak_word name, freak_word fields) {
freak_array_push(shape_registry_names, name);
freak_array_push(shape_registry_fields, fields);
shape_registry_count += 1;
}
bool freak_is_shape_name(freak_word name) {
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
if (freak_word_eq(freak_array_get(shape_registry_names, si), name)) {
return true;
}
si += 1;
}
return false;
}
freak_word freak_get_shape_fields(freak_word name) {
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
if (freak_word_eq(freak_array_get(shape_registry_names, si), name)) {
return freak_array_get(shape_registry_fields, si);
}
si += 1;
}
return freak_word_lit("");
}
int64_t freak_get_shape_field_count(freak_word shape_name) {
freak_word fields = freak_get_shape_fields(shape_name);
if ((freak_word_length(fields) == 0)) {
return 0;
}
int64_t count = 1;
int64_t i = 0;
int64_t slen = freak_word_length(fields);
for (int64_t __rep = 0; __rep < slen; __rep++) {
if (freak_word_eq(freak_word_char_at(fields, i), freak_word_lit(","))) {
count += 1;
}
i += 1;
}
return count;
}
int64_t freak_get_shape_field_index(freak_word shape_name, freak_word field_name) {
freak_word fields = freak_get_shape_fields(shape_name);
if ((freak_word_length(fields) == 0)) {
return (0 - 1);
}
int64_t idx = 0;
freak_word cur_name = freak_word_lit("");
bool in_type = false;
int64_t slen = freak_word_length(fields);
int64_t i = 0;
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(fields, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if (freak_word_eq(cur_name, field_name)) {
return idx;
}
idx += 1;
cur_name = freak_word_lit("");
in_type = false;
}
else {
if (freak_word_eq(c, freak_word_lit(":"))) {
in_type = true;
}
else {
if ((!in_type)) {
cur_name = freak_word_concat(cur_name, c);
}
}
}
i += 1;
}
if (freak_word_eq(cur_name, field_name)) {
return idx;
}
return (0 - 1);
}
void freak_emit(freak_word s) {
freak_fs_append(out_file, s);
}
void freak_emit_line(freak_word s) {
freak_fs_append(out_file, freak_word_concat(s, freak_word_lit("\n")));
}
void freak_emt_set_var_type(freak_word name, freak_word vtype) {
int64_t i = 0;
for (int64_t __rep = 0; __rep < emt_var_count; __rep++) {
if (freak_word_eq(freak_array_get(emt_var_names, i), name)) {
freak_array_set(emt_var_types, i, vtype);
return ;
}
i += 1;
}
freak_array_push(emt_var_names, name);
freak_array_push(emt_var_types, vtype);
emt_var_count += 1;
}
freak_word freak_emt_get_var_type(freak_word name) {
int64_t i = 0;
for (int64_t __rep = 0; __rep < emt_var_count; __rep++) {
if (freak_word_eq(freak_array_get(emt_var_names, i), name)) {
return freak_array_get(emt_var_types, i);
}
i += 1;
}
return freak_word_lit("i");
}
void freak_emt_register_word_task(freak_word name) {
freak_array_push(emt_word_tasks, name);
emt_word_task_count += 1;
}
bool freak_emt_is_word_task(freak_word name) {
int64_t i = 0;
for (int64_t __rep = 0; __rep < emt_word_task_count; __rep++) {
if (freak_word_eq(freak_array_get(emt_word_tasks, i), name)) {
return true;
}
i += 1;
}
return false;
}
void freak_emt_register_extern(freak_word name, freak_word ret) {
freak_array_push(emt_extern_names, name);
freak_array_push(emt_extern_rets, ret);
emt_extern_count += 1;
}
bool freak_emt_is_extern(freak_word name) {
int64_t i = 0;
for (int64_t __rep = 0; __rep < emt_extern_count; __rep++) {
if (freak_word_eq(freak_array_get(emt_extern_names, i), name)) {
return true;
}
i += 1;
}
return false;
}
freak_word freak_emt_get_extern_ret(freak_word name) {
int64_t i = 0;
for (int64_t __rep = 0; __rep < emt_extern_count; __rep++) {
if (freak_word_eq(freak_array_get(emt_extern_names, i), name)) {
return freak_array_get(emt_extern_rets, i);
}
i += 1;
}
return freak_word_lit("");
}
bool freak_is_ast_word(freak_word id) {
int64_t i = freak_word_to_int(id);
freak_word kind = freak_array_get(ast_expr_kinds, i);
if (freak_word_eq(kind, EXPR_STR)) {
return true;
}
if (freak_word_eq(kind, EXPR_METHOD)) {
freak_word mname = freak_array_get(ast_expr_vals, i);
if (freak_word_eq(mname, freak_word_lit("length"))) {
return false;
}
if (freak_word_eq(mname, freak_word_lit("to_int"))) {
return false;
}
if (freak_word_eq(mname, freak_word_lit("starts_with"))) {
return false;
}
if (freak_word_eq(mname, freak_word_lit("ends_with"))) {
return false;
}
if (freak_word_eq(mname, freak_word_lit("contains"))) {
return false;
}
return true;
}
if (freak_word_eq(kind, EXPR_CALL)) {
freak_word cname = freak_array_get(ast_expr_vals, i);
if (freak_word_eq(cname, freak_word_lit("word_from_int"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("word_from_bool"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("ask"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("fs::read"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("process::arg"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("process::exec_capture"))) {
return true;
}
if (freak_word_eq(cname, freak_word_lit("format_num"))) {
return true;
}
if (freak_emt_is_word_task(cname)) {
return true;
}
freak_word eret = freak_emt_get_extern_ret(cname);
if (freak_word_eq(eret, freak_word_lit("word"))) {
return true;
}
return false;
}
if (freak_word_eq(kind, EXPR_IDENT)) {
freak_word vname = freak_array_get(ast_expr_vals, i);
freak_word vt = freak_emt_get_var_type(vname);
if (freak_word_eq(vt, freak_word_lit("w"))) {
return true;
}
return false;
}
if (freak_word_eq(kind, EXPR_BINOP)) {
freak_word op = freak_array_get(ast_expr_vals, i);
if (freak_word_eq(op, freak_word_lit("+"))) {
freak_word lft = freak_array_get(ast_expr_lefts, i);
if (freak_is_ast_word(lft)) {
return true;
}
}
return false;
}
if (freak_word_eq(kind, EXPR_FIELD)) {
return false;
}
return false;
}
freak_word freak_get_source_line(int64_t n) {
if ((n <= 0)) {
return freak_word_lit("");
}
int64_t cur_line = 1;
int64_t i = 0;
int64_t slen = freak_word_length(lex_source);
freak_word line_text = freak_word_lit("");
bool found_line = false;
while (!((i >= slen))) {
if (((cur_line == n) && (!found_line))) {
found_line = true;
}
if (found_line) {
freak_word ch = freak_word_char_at(lex_source, i);
if ((freak_word_eq(ch, freak_word_lit("\n")) || freak_word_eq(ch, freak_word_lit("\r")))) {
return line_text;
}
line_text = freak_word_concat(line_text, ch);
}
else {
if (freak_word_eq(freak_word_char_at(lex_source, i), freak_word_lit("\n"))) {
cur_line += 1;
}
}
i += 1;
}
return line_text;
}
freak_word freak_diag_make_caret(int64_t col) {
freak_word s = freak_word_lit("");
int64_t i = 1;
while (!((i >= col))) {
s = freak_word_concat(s, freak_word_lit(" "));
i += 1;
}
return freak_word_concat(s, freak_word_lit("^"));
}
freak_word freak_friendly_tok(freak_word ttype, freak_word tval) {
if ((freak_word_eq(ttype, TOK_EOF) || freak_word_eq(ttype, freak_word_lit("")))) {
return freak_word_lit("end of file");
}
if (freak_word_eq(ttype, TOK_IDENT)) {
return freak_word_concat(freak_word_concat(freak_word_lit("'"), tval), freak_word_lit("'"));
}
if (freak_word_eq(ttype, TOK_NUM)) {
return freak_word_concat(freak_word_concat(freak_word_lit("number '"), tval), freak_word_lit("'"));
}
if (freak_word_eq(ttype, TOK_STR)) {
return freak_word_lit("string literal");
}
if (freak_word_eq(ttype, TOK_BOOL)) {
return freak_word_concat(freak_word_concat(freak_word_lit("'"), tval), freak_word_lit("'"));
}
if (freak_word_eq(ttype, TOK_KW)) {
return freak_word_concat(freak_word_concat(freak_word_lit("'"), tval), freak_word_lit("'"));
}
if (freak_word_eq(ttype, TOK_PUNCT)) {
return freak_word_concat(freak_word_concat(freak_word_lit("'"), tval), freak_word_lit("'"));
}
return freak_word_concat(freak_word_concat(freak_word_lit("'"), tval), freak_word_lit("'"));
}
void freak_diag_error(freak_word msg, freak_word hint) {
error_count += 1;
parse_error_count += 1;
int64_t tidx = parse_idx;
if ((tokens_count == 0)) {
freak_say(freak_word_concat(freak_word_lit("\x1b[1;31merror\x1b[0m: "), msg));
freak_say(freak_word_concat(freak_word_lit(" --> "), input_file));
freak_say(freak_word_lit(""));
return ;
}
if ((tidx >= tokens_count)) {
tidx = (tokens_count - 1);
}
if ((tidx < 0)) {
tidx = 0;
}
int64_t line_n = freak_word_to_int(freak_array_get(tok_lines, tidx));
int64_t col_n = freak_word_to_int(freak_array_get(tok_cols, tidx));
freak_word src_line = freak_get_source_line(line_n);
freak_word line_str = freak_word_from_int(line_n);
freak_word col_str = freak_word_from_int(col_n);
freak_say(freak_word_concat(freak_word_lit("\x1b[1;31merror\x1b[0m: "), msg));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" --> "), input_file), freak_word_lit(":")), line_str), freak_word_lit(":")), col_str));
freak_say(freak_word_lit("  |"));
freak_say(freak_word_concat(freak_word_concat(line_str, freak_word_lit(" | ")), src_line));
freak_word caret = freak_word_concat(freak_word_lit("  | "), freak_diag_make_caret(col_n));
if ((!freak_word_eq(hint, freak_word_lit("")))) {
caret = freak_word_concat(freak_word_concat(caret, freak_word_lit(" ")), hint);
}
freak_say(freak_word_concat(freak_word_concat(freak_word_lit("\x1b[1;31m"), caret), freak_word_lit("\x1b[0m")));
freak_say(freak_word_lit(""));
}
freak_word freak_lex_cur_ch(void) {
if ((lex_pos >= lex_len)) {
return freak_word_lit("");
}
return freak_word_char_at(lex_source, lex_pos);
}
freak_word freak_lex_ch_at(int64_t offset) {
if (((lex_pos + offset) >= lex_len)) {
return freak_word_lit("");
}
return freak_word_char_at(lex_source, (lex_pos + offset));
}
freak_word freak_lex_advance(void) {
if ((lex_pos >= lex_len)) {
return freak_word_lit("");
}
freak_word c = freak_word_char_at(lex_source, lex_pos);
lex_pos += 1;
if (freak_word_eq(c, freak_word_lit("\n"))) {
lex_line += 1;
lex_col = 1;
}
else {
lex_col += 1;
}
return c;
}
void freak_push_token(freak_word kind, freak_word val) {
freak_array_push(tok_types, kind);
freak_array_push(tok_vals, val);
freak_array_push(tok_lines, freak_word_from_int(cur_tok_line));
freak_array_push(tok_cols, freak_word_from_int(cur_tok_col));
tokens_count += 1;
}
void freak_lex_skip_ws(void) {
bool fin = false;
while (!(fin)) {
freak_word c = freak_lex_cur_ch();
if ((((freak_word_eq(c, freak_word_lit(" ")) || freak_word_eq(c, freak_word_lit("\n"))) || freak_word_eq(c, freak_word_lit("\r"))) || freak_word_eq(c, freak_word_lit("\t")))) {
freak_lex_advance();
}
else {
if (freak_word_eq(c, freak_word_lit("-"))) {
if (freak_word_eq(freak_lex_ch_at(1), freak_word_lit("-"))) {
freak_lex_advance();
freak_lex_advance();
bool cline_fin = false;
while (!(cline_fin)) {
freak_word cc = freak_lex_cur_ch();
if ((freak_word_eq(cc, freak_word_lit("")) || freak_word_eq(cc, freak_word_lit("\n")))) {
cline_fin = true;
}
else {
freak_lex_advance();
}
}
}
else {
fin = true;
}
}
else {
fin = true;
}
}
}
}
bool freak_is_numeric(freak_word c) {
if (((((freak_word_eq(c, freak_word_lit("0")) || freak_word_eq(c, freak_word_lit("1"))) || freak_word_eq(c, freak_word_lit("2"))) || freak_word_eq(c, freak_word_lit("3"))) || freak_word_eq(c, freak_word_lit("4")))) {
return true;
}
if (((((freak_word_eq(c, freak_word_lit("5")) || freak_word_eq(c, freak_word_lit("6"))) || freak_word_eq(c, freak_word_lit("7"))) || freak_word_eq(c, freak_word_lit("8"))) || freak_word_eq(c, freak_word_lit("9")))) {
return true;
}
return false;
}
bool freak_is_alphabetic(freak_word c) {
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
if (((((freak_word_eq(c, freak_word_lit("P")) || freak_word_eq(c, freak_word_lit("Q"))) || freak_word_eq(c, freak_word_lit("R"))) || freak_word_eq(c, freak_word_lit("S"))) || freak_word_eq(c, freak_word_lit("T")))) {
return true;
}
if ((((((freak_word_eq(c, freak_word_lit("U")) || freak_word_eq(c, freak_word_lit("V"))) || freak_word_eq(c, freak_word_lit("W"))) || freak_word_eq(c, freak_word_lit("X"))) || freak_word_eq(c, freak_word_lit("Y"))) || freak_word_eq(c, freak_word_lit("Z")))) {
return true;
}
return false;
}
bool freak_is_alnum_ext(freak_word c) {
if (freak_is_alphabetic(c)) {
return true;
}
if (freak_is_numeric(c)) {
return true;
}
return false;
}
void freak_lex_number(void) {
freak_word res = freak_word_lit("");
bool fin = false;
while (!(fin)) {
freak_word c = freak_lex_cur_ch();
if ((freak_is_numeric(c) || freak_word_eq(c, freak_word_lit(".")))) {
res = freak_word_concat(res, c);
freak_lex_advance();
}
else {
fin = true;
}
}
freak_push_token(TOK_NUM, res);
}
bool freak_try_consume_word(freak_word target) {
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
}
else {
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
void freak_lex_ident(void) {
freak_word res = freak_word_lit("");
bool fin = false;
while (!(fin)) {
freak_word c = freak_lex_cur_ch();
if (freak_is_alnum_ext(c)) {
res = freak_word_concat(res, c);
freak_lex_advance();
}
else {
fin = true;
}
}
freak_word lower = freak_word_to_lower(res);
if (freak_word_eq(lower, freak_word_lit("give"))) {
if (freak_try_consume_word(freak_word_lit("back"))) {
freak_push_token(TOK_KW, freak_word_lit("give back"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("or"))) {
if (freak_try_consume_word(freak_word_lit("else"))) {
freak_push_token(TOK_KW, freak_word_lit("or else"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("trust"))) {
if (freak_try_consume_word(freak_word_lit("me"))) {
freak_push_token(TOK_KW, freak_word_lit("trust me"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("for"))) {
if (freak_try_consume_word(freak_word_lit("each"))) {
freak_push_token(TOK_KW, freak_word_lit("for each"));
return ;
}
if (freak_try_consume_word(freak_word_lit("science"))) {
freak_push_token(TOK_KW, freak_word_lit("for science"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("training"))) {
if (freak_try_consume_word(freak_word_lit("arc"))) {
freak_push_token(TOK_KW, freak_word_lit("training arc"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("bringing"))) {
if (freak_try_consume_word(freak_word_lit("back"))) {
freak_push_token(TOK_KW, freak_word_lit("bringing back"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("only"))) {
if (freak_try_consume_word(freak_word_lit("on"))) {
freak_push_token(TOK_KW, freak_word_lit("only on"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("plus"))) {
if (freak_try_consume_word(freak_word_lit("ultra"))) {
freak_push_token(TOK_KW, freak_word_lit("PLUS ULTRA"));
return ;
}
}
if (freak_word_eq(lower, freak_word_lit("final"))) {
if (freak_try_consume_word(freak_word_lit("form"))) {
freak_push_token(TOK_KW, freak_word_lit("FINAL FORM"));
return ;
}
}
if ((((((((((((((((((((((((((((((((((((((((((((((((freak_word_eq(lower, freak_word_lit("pilot")) || freak_word_eq(lower, freak_word_lit("fixed"))) || freak_word_eq(lower, freak_word_lit("task"))) || freak_word_eq(lower, freak_word_lit("say"))) || freak_word_eq(lower, freak_word_lit("shape"))) || freak_word_eq(lower, freak_word_lit("impl"))) || freak_word_eq(lower, freak_word_lit("doctrine"))) || freak_word_eq(lower, freak_word_lit("launch"))) || freak_word_eq(lower, freak_word_lit("use"))) || freak_word_eq(lower, freak_word_lit("as"))) || freak_word_eq(lower, freak_word_lit("in"))) || freak_word_eq(lower, freak_word_lit("lend"))) || freak_word_eq(lower, freak_word_lit("mut"))) || freak_word_eq(lower, freak_word_lit("move"))) || freak_word_eq(lower, freak_word_lit("copy"))) || freak_word_eq(lower, freak_word_lit("break"))) || freak_word_eq(lower, freak_word_lit("continue"))) || freak_word_eq(lower, freak_word_lit("if"))) || freak_word_eq(lower, freak_word_lit("else"))) || freak_word_eq(lower, freak_word_lit("when"))) || freak_word_eq(lower, freak_word_lit("repeat"))) || freak_word_eq(lower, freak_word_lit("times"))) || freak_word_eq(lower, freak_word_lit("until"))) || freak_word_eq(lower, freak_word_lit("done"))) || freak_word_eq(lower, freak_word_lit("for"))) || freak_word_eq(lower, freak_word_lit("each"))) || freak_word_eq(lower, freak_word_lit("check"))) || freak_word_eq(lower, freak_word_lit("result"))) || freak_word_eq(lower, freak_word_lit("got"))) || freak_word_eq(lower, freak_word_lit("nobody"))) || freak_word_eq(lower, freak_word_lit("some"))) || freak_word_eq(lower, freak_word_lit("ok"))) || freak_word_eq(lower, freak_word_lit("err"))) || freak_word_eq(lower, freak_word_lit("sessions"))) || freak_word_eq(lower, freak_word_lit("max"))) || freak_word_eq(lower, freak_word_lit("foreshadow"))) || freak_word_eq(lower, freak_word_lit("payoff"))) || freak_word_eq(lower, freak_word_lit("route"))) || freak_word_eq(lower, freak_word_lit("sadly"))) || freak_word_eq(lower, freak_word_lit("deus_ex_machina"))) || freak_word_eq(lower, freak_word_lit("isekai"))) || freak_word_eq(lower, freak_word_lit("eventually"))) || freak_word_eq(lower, freak_word_lit("and"))) || freak_word_eq(lower, freak_word_lit("or"))) || freak_word_eq(lower, freak_word_lit("not"))) || freak_word_eq(lower, freak_word_lit("nakama"))) || freak_word_eq(lower, freak_word_lit("tsundere"))) || freak_word_eq(lower, freak_word_lit("extern")))) {
freak_push_token(TOK_KW, res);
}
else {
if ((((((freak_word_eq(lower, freak_word_lit("true")) || freak_word_eq(lower, freak_word_lit("false"))) || freak_word_eq(lower, freak_word_lit("yes"))) || freak_word_eq(lower, freak_word_lit("no"))) || freak_word_eq(lower, freak_word_lit("hai"))) || freak_word_eq(lower, freak_word_lit("iie")))) {
freak_push_token(TOK_BOOL, res);
}
else {
freak_push_token(TOK_IDENT, res);
}
}
}
void freak_lex_string(void) {
freak_lex_advance();
freak_word res = freak_word_lit("");
bool fin = false;
while (!(fin)) {
freak_word c = freak_lex_advance();
if (freak_word_eq(c, freak_word_lit("\""))) {
fin = true;
}
else {
if (freak_word_eq(c, freak_word_lit(""))) {
fin = true;
}
else {
if (freak_word_eq(c, freak_word_lit("\\"))) {
freak_word esc = freak_lex_advance();
if (freak_word_eq(esc, freak_word_lit("n"))) {
res = freak_word_concat(res, freak_word_lit("\n"));
}
else {
if (freak_word_eq(esc, freak_word_lit("r"))) {
res = freak_word_concat(res, freak_word_lit("\r"));
}
else {
if (freak_word_eq(esc, freak_word_lit("t"))) {
res = freak_word_concat(res, freak_word_lit("\t"));
}
else {
if (freak_word_eq(esc, freak_word_lit("x"))) {
freak_word hex_hi = freak_lex_advance();
freak_word hex_lo = freak_lex_advance();
res = freak_word_concat(freak_word_concat(freak_word_concat(res, freak_word_lit("\\x")), hex_hi), hex_lo);
}
else {
res = freak_word_concat(res, esc);
}
}
}
}
}
else {
if (freak_word_eq(c, freak_word_lit("|"))) {
res = freak_word_concat(res, freak_word_lit("<<PIPE>>"));
}
else {
res = freak_word_concat(res, c);
}
}
}
}
}
freak_push_token(TOK_STR, res);
}
void freak_lex_operators(void) {
freak_word c = freak_lex_cur_ch();
freak_word op = c;
freak_lex_advance();
freak_word next_c = freak_lex_cur_ch();
bool is_double = false;
if ((freak_word_eq(op, freak_word_lit("=")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("!")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("<")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit(">")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("+")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("-")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("*")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("/")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("%")) && freak_word_eq(next_c, freak_word_lit("=")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("-")) && freak_word_eq(next_c, freak_word_lit(">")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("=")) && freak_word_eq(next_c, freak_word_lit(">")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("*")) && freak_word_eq(next_c, freak_word_lit("*")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("|")) && freak_word_eq(next_c, freak_word_lit(">")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit("|")) && freak_word_eq(next_c, freak_word_lit("|")))) {
is_double = true;
}
if ((freak_word_eq(op, freak_word_lit(":")) && freak_word_eq(next_c, freak_word_lit(":")))) {
is_double = true;
}
if (is_double) {
op = freak_word_concat(op, next_c);
freak_lex_advance();
}
freak_push_token(TOK_PUNCT, op);
}
void freak_tokenize(freak_word source) {
lex_source = source;
lex_len = freak_word_length(source);
freak_say(freak_word_concat(freak_word_lit("Source length: "), freak_word_from_int(lex_len)));
lex_pos = 0;
lex_line = 1;
lex_col = 1;
tokens_count = 0;
bool fin = false;
while (!(fin)) {
freak_lex_skip_ws();
cur_tok_line = lex_line;
cur_tok_col = lex_col;
if ((lex_pos >= lex_len)) {
fin = true;
}
else {
freak_word c = freak_lex_cur_ch();
if (freak_is_numeric(c)) {
freak_lex_number();
}
else {
if (freak_is_alphabetic(c)) {
freak_lex_ident();
}
else {
if (freak_word_eq(c, freak_word_lit("\""))) {
freak_lex_string();
}
else {
if (((((((((((((freak_word_eq(c, freak_word_lit("=")) || freak_word_eq(c, freak_word_lit("+"))) || freak_word_eq(c, freak_word_lit("-"))) || freak_word_eq(c, freak_word_lit("*"))) || freak_word_eq(c, freak_word_lit("/"))) || freak_word_eq(c, freak_word_lit("<"))) || freak_word_eq(c, freak_word_lit(">"))) || freak_word_eq(c, freak_word_lit("!"))) || freak_word_eq(c, freak_word_lit(":"))) || freak_word_eq(c, freak_word_lit("|"))) || freak_word_eq(c, freak_word_lit("%"))) || freak_word_eq(c, freak_word_lit("@"))) || freak_word_eq(c, freak_word_lit("?")))) {
freak_lex_operators();
}
else {
if ((((((((freak_word_eq(c, freak_word_lit("{")) || freak_word_eq(c, freak_word_lit("}"))) || freak_word_eq(c, freak_word_lit("("))) || freak_word_eq(c, freak_word_lit(")"))) || freak_word_eq(c, freak_word_lit("["))) || freak_word_eq(c, freak_word_lit("]"))) || freak_word_eq(c, freak_word_lit(","))) || freak_word_eq(c, freak_word_lit(".")))) {
freak_push_token(TOK_PUNCT, c);
freak_lex_advance();
}
else {
freak_push_token(TOK_PUNCT, c);
freak_lex_advance();
}
}
}
}
}
}
}
freak_push_token(TOK_EOF, freak_word_lit(""));
}
freak_word freak_cur_tok_type(void) {
return freak_array_get(tok_types, parse_idx);
}
freak_word freak_cur_tok_val(void) {
return freak_array_get(tok_vals, parse_idx);
}
void freak_advance_tok(void) {
parse_idx += 1;
}
bool freak_match_tok(freak_word type, freak_word val) {
if (freak_word_eq(freak_cur_tok_type(), type)) {
if ((freak_word_eq(val, freak_word_lit("")) || freak_word_eq(freak_cur_tok_val(), val))) {
freak_advance_tok();
return true;
}
}
return false;
}
void freak_expect_tok(freak_word type, freak_word val) {
if ((!freak_match_tok(type, val))) {
freak_word expected = freak_word_lit("");
if ((freak_word_eq(type, TOK_IDENT) && freak_word_eq(val, freak_word_lit("")))) {
expected = freak_word_lit("an identifier");
}
if (freak_word_eq(type, TOK_PUNCT)) {
expected = freak_word_concat(freak_word_concat(freak_word_lit("'"), val), freak_word_lit("'"));
}
if (freak_word_eq(type, TOK_KW)) {
expected = freak_word_concat(freak_word_concat(freak_word_lit("keyword '"), val), freak_word_lit("'"));
}
if (freak_word_eq(expected, freak_word_lit(""))) {
expected = freak_word_concat(freak_word_concat(freak_word_lit("'"), val), freak_word_lit("'"));
}
freak_word found_tok = freak_friendly_tok(freak_cur_tok_type(), freak_cur_tok_val());
freak_diag_error(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("expected "), expected), freak_word_lit(", found ")), found_tok), freak_word_lit(""));
if (((!freak_word_eq(freak_cur_tok_type(), TOK_EOF)) && (!freak_word_eq(freak_cur_tok_type(), freak_word_lit(""))))) {
freak_advance_tok();
}
}
}
int64_t freak_parse_primary(void) {
freak_word ttype = freak_cur_tok_type();
freak_word tval = freak_cur_tok_val();
if ((freak_word_eq(ttype, TOK_EOF) || freak_word_eq(ttype, freak_word_lit("")))) {
return (0 - 1);
}
if (freak_word_eq(ttype, TOK_NUM)) {
freak_advance_tok();
bool is_float = false;
int64_t nci = 0;
int64_t nclen = freak_word_length(tval);
for (int64_t __rep = 0; __rep < nclen; __rep++) {
if (freak_word_eq(freak_word_char_at(tval, nci), freak_word_lit("."))) {
is_float = true;
}
nci += 1;
}
if (is_float) {
return freak_alloc_expr(EXPR_FLOAT, tval, freak_word_lit(""), freak_word_lit(""));
}
return freak_alloc_expr(EXPR_INT, tval, freak_word_lit(""), freak_word_lit(""));
}
if (freak_word_eq(ttype, TOK_STR)) {
freak_advance_tok();
return freak_alloc_expr(EXPR_STR, tval, freak_word_lit(""), freak_word_lit(""));
}
if (freak_word_eq(ttype, TOK_BOOL)) {
freak_advance_tok();
return freak_alloc_expr(EXPR_BOOL, tval, freak_word_lit(""), freak_word_lit(""));
}
if (freak_word_eq(ttype, TOK_IDENT)) {
freak_advance_tok();
if (freak_match_tok(TOK_PUNCT, freak_word_lit("::"))) {
freak_word nttype = freak_cur_tok_type();
freak_word ntval = freak_cur_tok_val();
if (freak_word_eq(nttype, TOK_IDENT)) {
tval = freak_word_concat(freak_word_concat(tval, freak_word_lit("::")), ntval);
freak_advance_tok();
}
else {
freak_say(freak_word_lit("Expected identifier after ::"));
}
}
if ((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit("{")))) {
if (freak_is_shape_name(tval)) {
freak_advance_tok();
freak_word val_ids = freak_word_lit("");
bool cfin = false;
bool cis_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
cfin = true;
}
while (!(cfin)) {
freak_word fname = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit(":"));
int64_t fval_id = freak_parse_expr();
if (cis_first) {
val_ids = freak_word_from_int(fval_id);
cis_first = false;
}
else {
val_ids = freak_word_concat(freak_word_concat(val_ids, freak_word_lit(",")), freak_word_from_int(fval_id));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
cfin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
return freak_alloc_expr(EXPR_CALL, freak_word_concat(freak_word_lit("shape::ctor::"), tval), val_ids, freak_word_lit(""));
}
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("("))) {
freak_word args = freak_word_lit("");
bool fin = false;
bool is_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
fin = true;
}
while (!(fin)) {
int64_t arg_id = freak_parse_expr();
if (is_first) {
args = freak_word_from_int(arg_id);
is_first = false;
}
else {
args = freak_word_concat(freak_word_concat(args, freak_word_lit(",")), freak_word_from_int(arg_id));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
fin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
return freak_alloc_expr(EXPR_CALL, tval, args, freak_word_lit(""));
}
return freak_alloc_expr(EXPR_IDENT, tval, freak_word_lit(""), freak_word_lit(""));
}
if ((freak_word_eq(ttype, TOK_PUNCT) && freak_word_eq(tval, freak_word_lit("(")))) {
freak_advance_tok();
int64_t inner = freak_parse_expr();
freak_expect_tok(TOK_PUNCT, freak_word_lit(")"));
return inner;
}
freak_diag_error(freak_word_concat(freak_word_concat(freak_word_lit("unexpected "), freak_friendly_tok(ttype, tval)), freak_word_lit(" — this token cannot start an expression")), freak_word_lit(""));
if (((!freak_word_eq(ttype, TOK_EOF)) && (!freak_word_eq(ttype, freak_word_lit(""))))) {
freak_advance_tok();
}
return (0 - 1);
}
int64_t freak_parse_postfix(void) {
int64_t left = freak_parse_primary();
bool fin = false;
while (!(fin)) {
if (freak_match_tok(TOK_PUNCT, freak_word_lit("."))) {
freak_word mname = freak_cur_tok_val();
freak_expect_tok(TOK_IDENT, freak_word_lit(""));
if ((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit("(")))) {
freak_advance_tok();
freak_word args = freak_word_lit("");
bool argfin = false;
bool is_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
argfin = true;
}
while (!(argfin)) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_EOF) || freak_word_eq(freak_cur_tok_type(), freak_word_lit("")))) {
argfin = true;
}
else {
int64_t arg_id = freak_parse_expr();
if (is_first) {
args = freak_word_from_int(arg_id);
is_first = false;
}
else {
args = freak_word_concat(freak_word_concat(args, freak_word_lit(",")), freak_word_from_int(arg_id));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
argfin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
}
left = freak_alloc_expr(EXPR_METHOD, mname, freak_word_from_int(left), args);
}
else {
left = freak_alloc_expr(EXPR_FIELD, mname, freak_word_from_int(left), freak_word_lit(""));
}
}
else {
if (freak_match_tok(TOK_PUNCT, freak_word_lit("["))) {
int64_t idx_expr = freak_parse_expr();
freak_expect_tok(TOK_PUNCT, freak_word_lit("]"));
left = freak_alloc_expr(EXPR_INDEX, freak_word_lit(""), freak_word_from_int(left), freak_word_from_int(idx_expr));
}
else {
if (freak_match_tok(TOK_PUNCT, freak_word_lit("|>"))) {
freak_word fname = freak_cur_tok_val();
freak_advance_tok();
freak_word pipe_args = freak_word_from_int(left);
if (freak_match_tok(TOK_PUNCT, freak_word_lit("("))) {
if ((!freak_match_tok(TOK_PUNCT, freak_word_lit(")")))) {
bool pfin = false;
while (!(pfin)) {
int64_t parg_id = freak_parse_expr();
pipe_args = freak_word_concat(freak_word_concat(pipe_args, freak_word_lit(",")), freak_word_from_int(parg_id));
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
pfin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
}
}
left = freak_alloc_expr(EXPR_CALL, fname, pipe_args, freak_word_lit(""));
}
else {
fin = true;
}
}
}
}
return left;
}
int64_t freak_parse_unary(void) {
if (freak_match_tok(TOK_KW, freak_word_lit("not"))) {
int64_t op = freak_parse_unary();
return freak_alloc_expr(EXPR_UNARYOP, freak_word_lit("not"), freak_word_from_int(op), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("-"))) {
int64_t op = freak_parse_unary();
return freak_alloc_expr(EXPR_UNARYOP, freak_word_lit("-"), freak_word_from_int(op), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("PLUS ULTRA"))) {
int64_t op = freak_parse_unary();
return freak_alloc_expr(EXPR_UNARYOP, freak_word_lit("PLUS ULTRA"), freak_word_from_int(op), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("FINAL FORM"))) {
int64_t op = freak_parse_unary();
return freak_alloc_expr(EXPR_UNARYOP, freak_word_lit("FINAL FORM"), freak_word_from_int(op), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("TSUNDERE"))) {
int64_t op = freak_parse_unary();
return freak_alloc_expr(EXPR_UNARYOP, freak_word_lit("TSUNDERE"), freak_word_from_int(op), freak_word_lit(""));
}
return freak_parse_postfix();
}
int64_t freak_parse_mul(void) {
int64_t left = freak_parse_unary();
bool fin = false;
while (!(fin)) {
freak_word tval = freak_cur_tok_val();
if (((freak_word_eq(tval, freak_word_lit("*")) || freak_word_eq(tval, freak_word_lit("/"))) || freak_word_eq(tval, freak_word_lit("%")))) {
freak_advance_tok();
int64_t right = freak_parse_unary();
left = freak_alloc_expr(EXPR_BINOP, tval, freak_word_from_int(left), freak_word_from_int(right));
}
else {
fin = true;
}
}
return left;
}
int64_t freak_parse_add(void) {
int64_t left = freak_parse_mul();
bool fin = false;
while (!(fin)) {
freak_word tval = freak_cur_tok_val();
if (((freak_word_eq(tval, freak_word_lit("+")) || freak_word_eq(tval, freak_word_lit("-"))) || freak_word_eq(tval, freak_word_lit("NAKAMA")))) {
freak_advance_tok();
int64_t right = freak_parse_mul();
left = freak_alloc_expr(EXPR_BINOP, tval, freak_word_from_int(left), freak_word_from_int(right));
}
else {
fin = true;
}
}
return left;
}
int64_t freak_parse_comparison(void) {
int64_t left = freak_parse_add();
bool fin = false;
while (!(fin)) {
freak_word tval = freak_cur_tok_val();
if ((((((freak_word_eq(tval, freak_word_lit("==")) || freak_word_eq(tval, freak_word_lit("!="))) || freak_word_eq(tval, freak_word_lit("<"))) || freak_word_eq(tval, freak_word_lit(">"))) || freak_word_eq(tval, freak_word_lit("<="))) || freak_word_eq(tval, freak_word_lit(">=")))) {
freak_advance_tok();
int64_t right = freak_parse_add();
left = freak_alloc_expr(EXPR_BINOP, tval, freak_word_from_int(left), freak_word_from_int(right));
}
else {
fin = true;
}
}
return left;
}
int64_t freak_parse_and(void) {
int64_t left = freak_parse_comparison();
bool fin = false;
while (!(fin)) {
freak_word tval = freak_cur_tok_val();
if (freak_word_eq(tval, freak_word_lit("and"))) {
freak_advance_tok();
int64_t right = freak_parse_comparison();
left = freak_alloc_expr(EXPR_BINOP, freak_word_lit("and"), freak_word_from_int(left), freak_word_from_int(right));
}
else {
fin = true;
}
}
return left;
}
int64_t freak_parse_expr(void) {
int64_t left = freak_parse_and();
bool fin = false;
while (!(fin)) {
freak_word tval = freak_cur_tok_val();
if (freak_word_eq(tval, freak_word_lit("or"))) {
freak_advance_tok();
int64_t right = freak_parse_and();
left = freak_alloc_expr(EXPR_BINOP, freak_word_lit("or"), freak_word_from_int(left), freak_word_from_int(right));
}
else {
fin = true;
}
}
return left;
}
freak_word freak_parse_block(void) {
freak_expect_tok(TOK_PUNCT, freak_word_lit("{"));
freak_word block = freak_word_lit("");
bool fin = false;
bool is_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
fin = true;
}
while (!(fin)) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_EOF) || freak_word_eq(freak_cur_tok_type(), freak_word_lit("")))) {
freak_diag_error(freak_word_lit("unexpected end of file — missing '}'"), freak_word_lit("block opened here"));
fin = true;
}
else {
int64_t stmt_id = freak_parse_stmt();
if (is_first) {
block = freak_word_from_int(stmt_id);
is_first = false;
}
else {
block = freak_word_concat(freak_word_concat(block, freak_word_lit(",")), freak_word_from_int(stmt_id));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
fin = true;
}
}
}
return block;
}
int64_t freak_parse_stmt(void) {
freak_word ttype = freak_cur_tok_type();
freak_word tval = freak_cur_tok_val();
if ((freak_word_eq(ttype, TOK_PUNCT) && freak_word_eq(tval, freak_word_lit("@")))) {
freak_advance_tok();
freak_advance_tok();
ttype = freak_cur_tok_type();
tval = freak_cur_tok_val();
}
if (freak_match_tok(TOK_KW, freak_word_lit("say"))) {
int64_t expr_id = freak_parse_expr();
return freak_alloc_stmt(STMT_SAY, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("shape"))) {
return freak_parse_shape();
}
if (freak_match_tok(TOK_KW, freak_word_lit("impl"))) {
return freak_parse_impl();
}
if (freak_match_tok(TOK_KW, freak_word_lit("eventually"))) {
freak_word ev_body = freak_parse_block();
return freak_alloc_stmt(STMT_EVENTUALLY, freak_word_lit(""), freak_word_lit(""), ev_body, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("pilot"))) {
freak_word name = freak_cur_tok_val();
freak_advance_tok();
freak_word type_ann = freak_word_lit("");
if ((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit(":")))) {
freak_advance_tok();
type_ann = freak_cur_tok_val();
freak_advance_tok();
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("="));
int64_t expr_id = freak_parse_expr();
return freak_alloc_stmt(STMT_PILOT, name, freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), type_ann, freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("give back"))) {
int64_t expr_id = (0 - 1);
if (((!freak_word_eq(freak_cur_tok_type(), TOK_PUNCT)) || (!freak_word_eq(freak_cur_tok_val(), freak_word_lit("}"))))) {
expr_id = freak_parse_expr();
}
return freak_alloc_stmt(STMT_GIVE_BACK, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("break"))) {
return freak_alloc_stmt(STMT_BREAK, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("continue"))) {
return freak_alloc_stmt(STMT_CONTINUE, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("if"))) {
int64_t expr_id = freak_parse_expr();
freak_word body_id = freak_parse_block();
freak_word else_body = freak_word_lit("");
if (freak_match_tok(TOK_KW, freak_word_lit("else"))) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_KW) && freak_word_eq(freak_cur_tok_val(), freak_word_lit("if")))) {
int64_t elif_id = freak_parse_stmt();
else_body = freak_word_from_int(elif_id);
}
else {
else_body = freak_parse_block();
}
}
return freak_alloc_stmt(STMT_IF, freak_word_lit(""), freak_word_from_int(expr_id), body_id, else_body, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("repeat"))) {
if (freak_match_tok(TOK_KW, freak_word_lit("until"))) {
int64_t expr_id = freak_parse_expr();
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_REPEAT, freak_word_lit("until"), freak_word_from_int(expr_id), body_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
int64_t expr_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("times"));
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_REPEAT, freak_word_lit("times"), freak_word_from_int(expr_id), body_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("training arc"))) {
freak_expect_tok(TOK_KW, freak_word_lit("until"));
int64_t cond_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("max"));
int64_t max_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("sessions"));
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_TRAINING_ARC, freak_word_lit(""), freak_word_from_int(cond_id), body_id, freak_word_lit(""), freak_word_from_int(max_id), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_KW, freak_word_lit("when"))) {
return freak_parse_when();
}
if (freak_match_tok(TOK_KW, freak_word_lit("extern"))) {
return freak_parse_extern();
}
if (freak_match_tok(TOK_KW, freak_word_lit("task"))) {
return freak_parse_task_def();
}
if ((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit("{")))) {
freak_word block_id = freak_parse_block();
return freak_alloc_stmt(STMT_BLOCK, freak_word_lit(""), freak_word_lit(""), block_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
int64_t expr_id = freak_parse_expr();
if (freak_match_tok(TOK_PUNCT, freak_word_lit("="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("+="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("+="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("-="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("-="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("*="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("*="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("/="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("/="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("%="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("%="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
return freak_alloc_stmt(STMT_EXPR, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
freak_word freak_parse_params(void) {
freak_word params = freak_word_lit("");
bool fin = false;
bool is_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
fin = true;
}
while (!(fin)) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_EOF) || freak_word_eq(freak_cur_tok_type(), freak_word_lit("")))) {
freak_diag_error(freak_word_lit("unexpected end of file inside parameter list"), freak_word_lit(""));
fin = true;
}
else {
freak_word pname = freak_cur_tok_val();
freak_advance_tok();
if (freak_word_eq(pname, freak_word_lit("self"))) {
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
fin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
if (is_first) {
params = freak_word_lit("self:word");
is_first = false;
}
else {
params = freak_word_concat(params, freak_word_lit(",self:word"));
}
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(":"));
freak_word ptype = freak_cur_tok_val();
freak_advance_tok();
freak_word pstr = freak_word_concat(freak_word_concat(pname, freak_word_lit(":")), ptype);
if (is_first) {
params = pstr;
is_first = false;
}
else {
params = freak_word_concat(freak_word_concat(params, freak_word_lit(",")), pstr);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
fin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
}
}
return params;
}
int64_t freak_parse_shape(void) {
freak_word shape_name = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit("{"));
freak_word fields = freak_word_lit("");
bool sfin = false;
bool sis_first = true;
while (!(sfin)) {
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
sfin = true;
}
else {
freak_word fname = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit(":"));
freak_word ftype = freak_cur_tok_val();
freak_advance_tok();
if (sis_first) {
fields = freak_word_concat(freak_word_concat(fname, freak_word_lit(":")), ftype);
sis_first = false;
}
else {
fields = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(fields, freak_word_lit(",")), fname), freak_word_lit(":")), ftype);
}
}
}
freak_register_shape(shape_name, fields);
return freak_alloc_stmt(STMT_SHAPE, shape_name, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), fields, freak_word_lit(""), freak_word_lit(""));
}
int64_t freak_parse_impl(void) {
freak_word impl_name = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit("{"));
while (!((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit("}"))))) {
if (freak_match_tok(TOK_KW, freak_word_lit("task"))) {
freak_word mname = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit("("));
freak_word params = freak_parse_params();
freak_word ret_type = freak_word_lit("void");
if (freak_match_tok(TOK_PUNCT, freak_word_lit("->"))) {
ret_type = freak_cur_tok_val();
freak_advance_tok();
}
freak_word body_id = freak_parse_block();
freak_word full_name = freak_word_concat(freak_word_concat(impl_name, freak_word_lit("_")), mname);
int64_t sid = freak_alloc_stmt(STMT_TASK, full_name, freak_word_lit(""), body_id, freak_word_lit(""), freak_word_lit(""), params, ret_type);
freak_array_push(ast_top_stmts, freak_word_from_int(sid));
}
else {
freak_advance_tok();
}
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("}"));
return freak_alloc_stmt(STMT_BLOCK, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
int64_t freak_parse_when(void) {
int64_t target_id = freak_parse_expr();
freak_expect_tok(TOK_PUNCT, freak_word_lit("{"));
freak_word cases_str = freak_word_lit("");
bool fin = false;
bool is_first = true;
while (!(fin)) {
if (freak_match_tok(TOK_PUNCT, freak_word_lit("}"))) {
fin = true;
}
else {
int64_t case_expr = (0 - 1);
if (freak_match_tok(TOK_IDENT, freak_word_lit("_"))) {
case_expr = (0 - 1);
}
else {
case_expr = freak_parse_expr();
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("->"));
int64_t stmt_id = freak_parse_stmt();
freak_word case_str = freak_word_concat(freak_word_concat(freak_word_from_int(case_expr), freak_word_lit(":")), freak_word_from_int(stmt_id));
if (is_first) {
cases_str = case_str;
is_first = false;
}
else {
cases_str = freak_word_concat(freak_word_concat(cases_str, freak_word_lit(",")), case_str);
}
}
}
return freak_alloc_stmt(STMT_WHEN, freak_word_lit(""), freak_word_from_int(target_id), cases_str, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""));
}
int64_t freak_parse_extern(void) {
freak_expect_tok(TOK_KW, freak_word_lit("task"));
freak_word ename = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit("("));
freak_word eparams = freak_word_lit("");
bool efin = false;
bool eis_first = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
efin = true;
}
while (!(efin)) {
freak_word epname = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit(":"));
freak_word eptype = freak_cur_tok_val();
freak_advance_tok();
freak_word epstr = freak_word_concat(freak_word_concat(epname, freak_word_lit(":")), eptype);
if (eis_first) {
eparams = epstr;
eis_first = false;
}
else {
eparams = freak_word_concat(freak_word_concat(eparams, freak_word_lit(",")), epstr);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit(")"))) {
efin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("->"));
freak_word eret_type = freak_cur_tok_val();
freak_advance_tok();
return freak_alloc_stmt(STMT_EXTERN, ename, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), eparams, eret_type);
}
int64_t freak_parse_task_def(void) {
freak_word name = freak_cur_tok_val();
freak_advance_tok();
freak_expect_tok(TOK_PUNCT, freak_word_lit("("));
freak_word params = freak_parse_params();
freak_word ret_type = freak_word_lit("void");
if (freak_match_tok(TOK_PUNCT, freak_word_lit("->"))) {
ret_type = freak_cur_tok_val();
freak_advance_tok();
}
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_TASK, name, freak_word_lit(""), body_id, freak_word_lit(""), freak_word_lit(""), params, ret_type);
}
void freak_parse_program(void) {
parse_idx = 0;
tok_total = tokens_count;
parse_error_count = 0;
bool pfin = false;
while (!(pfin)) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_EOF) || freak_word_eq(freak_cur_tok_type(), freak_word_lit("")))) {
pfin = true;
}
else {
if ((parse_error_count > 100)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_lit("\x1b[1;31merror\x1b[0m: too many errors, giving up (>100 syntax errors in "), input_file), freak_word_lit(")")));
pfin = true;
}
else {
int64_t stmt_id = freak_parse_stmt();
freak_array_push(ast_top_stmts, freak_word_from_int(stmt_id));
}
}
}
}
void freak_check_program(void) {
}
freak_word freak_c_safe_ident(freak_word s) {
freak_word res = freak_word_lit("");
int64_t slen = freak_word_length(s);
int64_t i = 0;
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(s, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
if (((i + 1) < slen)) {
if (freak_word_eq(freak_word_char_at(s, (i + 1)), freak_word_lit(":"))) {
res = freak_word_concat(res, freak_word_lit("_"));
i += 1;
}
else {
res = freak_word_concat(res, c);
}
}
else {
res = freak_word_concat(res, c);
}
}
else {
res = freak_word_concat(res, c);
}
i += 1;
}
return res;
}
void freak_emit_args(freak_word args) {
int64_t i = 0;
int64_t slen = freak_word_length(args);
freak_word cur_id = freak_word_lit("");
bool first = true;
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(args, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((!first)) {
freak_emit(freak_word_lit(", "));
}
freak_emit_expr(cur_id);
cur_id = freak_word_lit("");
first = false;
}
else {
cur_id = freak_word_concat(cur_id, c);
}
i += 1;
}
if ((!freak_word_eq(cur_id, freak_word_lit("")))) {
if ((!first)) {
freak_emit(freak_word_lit(", "));
}
freak_emit_expr(cur_id);
}
}
freak_word freak_c_map_call(freak_word val) {
if (freak_word_eq(val, freak_word_lit("say"))) {
return freak_word_lit("freak_say");
}
if (freak_word_eq(val, freak_word_lit("ask"))) {
return freak_word_lit("freak_ask");
}
if (freak_word_eq(val, freak_word_lit("word_from_int"))) {
return freak_word_lit("freak_word_from_int");
}
if (freak_word_eq(val, freak_word_lit("word_from_bool"))) {
return freak_word_lit("freak_word_from_bool");
}
if (freak_word_eq(val, freak_word_lit("word_to_int"))) {
return freak_word_lit("freak_word_to_int");
}
if (freak_word_eq(val, freak_word_lit("array_new"))) {
return freak_word_lit("freak_array_new");
}
if (freak_word_eq(val, freak_word_lit("array_push"))) {
return freak_word_lit("freak_array_push");
}
if (freak_word_eq(val, freak_word_lit("array_get"))) {
return freak_word_lit("freak_array_get");
}
if (freak_word_eq(val, freak_word_lit("array_set"))) {
return freak_word_lit("freak_array_set");
}
if (freak_word_eq(val, freak_word_lit("array_len"))) {
return freak_word_lit("freak_array_len");
}
if (freak_word_eq(val, freak_word_lit("process::args"))) {
return freak_word_lit("freak_process_args");
}
if (freak_word_eq(val, freak_word_lit("process::exit"))) {
return freak_word_lit("freak_process_exit");
}
if (freak_word_eq(val, freak_word_lit("process::exec"))) {
return freak_word_lit("freak_process_exec");
}
if (freak_word_eq(val, freak_word_lit("process::exec_capture"))) {
return freak_word_lit("freak_process_exec_capture");
}
if (freak_word_eq(val, freak_word_lit("process::env"))) {
return freak_word_lit("freak_process_env");
}
if (freak_word_eq(val, freak_word_lit("process::arg"))) {
return freak_word_lit("freak_process_arg");
}
if (freak_word_eq(val, freak_word_lit("process::args_count"))) {
return freak_word_lit("freak_process_args_count");
}
if (freak_word_eq(val, freak_word_lit("fs::read"))) {
return freak_word_lit("freak_fs_read");
}
if (freak_word_eq(val, freak_word_lit("fs::write"))) {
return freak_word_lit("freak_fs_write");
}
if (freak_word_eq(val, freak_word_lit("fs::append"))) {
return freak_word_lit("freak_fs_append");
}
if (freak_word_eq(val, freak_word_lit("fs::exists"))) {
return freak_word_lit("freak_fs_exists");
}
if (freak_word_eq(val, freak_word_lit("fs::delete"))) {
return freak_word_lit("freak_fs_delete");
}
if (freak_word_eq(val, freak_word_lit("fs::list_dir"))) {
return freak_word_lit("freak_fs_list_dir");
}
if (freak_word_eq(val, freak_word_lit("math::sqrt"))) {
return freak_word_lit("freak_math_sqrt");
}
if (freak_word_eq(val, freak_word_lit("math::pow"))) {
return freak_word_lit("freak_math_pow");
}
if (freak_word_eq(val, freak_word_lit("math::sin"))) {
return freak_word_lit("freak_math_sin");
}
if (freak_word_eq(val, freak_word_lit("math::cos"))) {
return freak_word_lit("freak_math_cos");
}
if (freak_word_eq(val, freak_word_lit("math::tan"))) {
return freak_word_lit("freak_math_tan");
}
if (freak_word_eq(val, freak_word_lit("math::floor"))) {
return freak_word_lit("freak_math_floor");
}
if (freak_word_eq(val, freak_word_lit("math::ceil"))) {
return freak_word_lit("freak_math_ceil");
}
if (freak_word_eq(val, freak_word_lit("parse_num"))) {
return freak_word_lit("freak_parse_num");
}
if (freak_word_eq(val, freak_word_lit("format_num"))) {
return freak_word_lit("freak_format_num");
}
if (freak_word_eq(val, freak_word_lit("ui::create_window"))) {
return freak_word_lit("freak_ui_create_window_word");
}
if (freak_word_eq(val, freak_word_lit("ui::destroy_window"))) {
return freak_word_lit("freak_ui_destroy_window");
}
if (freak_word_eq(val, freak_word_lit("ui::begin_frame"))) {
return freak_word_lit("freak_ui_begin_frame");
}
if (freak_word_eq(val, freak_word_lit("ui::end_frame"))) {
return freak_word_lit("freak_ui_end_frame");
}
if (freak_word_eq(val, freak_word_lit("ui::poll_events"))) {
return freak_word_lit("freak_ui_poll_events");
}
if (freak_word_eq(val, freak_word_lit("ui::clear"))) {
return freak_word_lit("freak_ui_clear");
}
if (freak_word_eq(val, freak_word_lit("ui::event_kind"))) {
return freak_word_lit("freak_ui_event_kind");
}
if (freak_word_eq(val, freak_word_lit("ui::event_key"))) {
return freak_word_lit("freak_ui_event_key");
}
if (freak_word_eq(val, freak_word_lit("ui::event_pressed"))) {
return freak_word_lit("freak_ui_event_pressed");
}
if (freak_word_eq(val, freak_word_lit("ui::event_character"))) {
return freak_word_lit("freak_ui_event_character");
}
if (freak_word_eq(val, freak_word_lit("ui::event_mouse_x"))) {
return freak_word_lit("freak_ui_event_mouse_x");
}
if (freak_word_eq(val, freak_word_lit("ui::event_mouse_y"))) {
return freak_word_lit("freak_ui_event_mouse_y");
}
if (freak_word_eq(val, freak_word_lit("ui::event_button"))) {
return freak_word_lit("freak_ui_event_button");
}
if (freak_word_eq(val, freak_word_lit("ui::fill_rect"))) {
return freak_word_lit("freak_ui_fill_rect");
}
if (freak_word_eq(val, freak_word_lit("ui::stroke_rect"))) {
return freak_word_lit("freak_ui_stroke_rect");
}
if (freak_word_eq(val, freak_word_lit("ui::fill_circle"))) {
return freak_word_lit("freak_ui_fill_circle");
}
if (freak_word_eq(val, freak_word_lit("ui::draw_line"))) {
return freak_word_lit("freak_ui_draw_line");
}
if (freak_word_eq(val, freak_word_lit("ui::draw_text"))) {
return freak_word_lit("freak_ui_draw_text_word");
}
if (freak_word_eq(val, freak_word_lit("ui::measure_text"))) {
return freak_word_lit("freak_ui_measure_text_word");
}
if (freak_word_eq(val, freak_word_lit("tcp::connect"))) {
return freak_word_lit("freak_tcp_connect");
}
if (freak_word_eq(val, freak_word_lit("tcp::send"))) {
return freak_word_lit("freak_tcp_send");
}
if (freak_word_eq(val, freak_word_lit("tcp::recv"))) {
return freak_word_lit("freak_tcp_recv");
}
if (freak_word_eq(val, freak_word_lit("tcp::recv_all"))) {
return freak_word_lit("freak_tcp_recv_all");
}
if (freak_word_eq(val, freak_word_lit("tcp::close"))) {
return freak_word_lit("freak_tcp_close");
}
return freak_word_lit("");
}
void freak_emit_expr(freak_word id) {
int64_t i = freak_word_to_int(id);
freak_word kind = freak_array_get(ast_expr_kinds, i);
freak_word val = freak_array_get(ast_expr_vals, i);
freak_word left = freak_array_get(ast_expr_lefts, i);
freak_word right = freak_array_get(ast_expr_rights, i);
if (freak_word_eq(kind, EXPR_INT)) {
freak_emit(val);
return ;
}
if (freak_word_eq(kind, EXPR_FLOAT)) {
freak_emit(val);
return ;
}
if (freak_word_eq(kind, EXPR_BOOL)) {
if (((freak_word_eq(val, freak_word_lit("true")) || freak_word_eq(val, freak_word_lit("yes"))) || freak_word_eq(val, freak_word_lit("hai")))) {
freak_emit(freak_word_lit("true"));
}
else {
freak_emit(freak_word_lit("false"));
}
return ;
}
if (freak_word_eq(kind, EXPR_IDENT)) {
freak_emit(val);
return ;
}
if (freak_word_eq(kind, EXPR_STR)) {
freak_emit_c_string(val);
return ;
}
if (freak_word_eq(kind, EXPR_CALL)) {
freak_emit_c_call(val, left);
return ;
}
if (freak_word_eq(kind, EXPR_METHOD)) {
freak_emit_c_method(val, left, right);
return ;
}
if (freak_word_eq(kind, EXPR_FIELD)) {
freak_emit_c_field(val, left);
return ;
}
if (freak_word_eq(kind, EXPR_INDEX)) {
if (freak_is_ast_word(left)) {
freak_emit(freak_word_lit("freak_word_char_at("));
freak_emit_expr(left);
freak_emit(freak_word_lit(", "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
}
else {
freak_emit_expr(left);
freak_emit(freak_word_lit(".data["));
freak_emit_expr(right);
freak_emit(freak_word_lit("]"));
}
return ;
}
if (freak_word_eq(kind, EXPR_BINOP)) {
freak_emit_c_binop(val, left, right);
return ;
}
if (freak_word_eq(kind, EXPR_UNARYOP)) {
freak_emit_c_unaryop(val, left);
return ;
}
freak_emit(freak_word_lit("/* Unknown Expr */"));
}
void freak_emit_c_string(freak_word val) {
freak_word tmp = freak_word_lit("freak_word_lit(\"");
freak_word str_val = freak_word_replace(val, freak_word_lit("<<PIPE>>"), freak_word_lit("|"));
int64_t si = 0;
int64_t sslen = freak_word_length(str_val);
while (!((si >= sslen))) {
freak_word sc = freak_word_char_at(str_val, si);
if ((freak_word_eq(sc, freak_word_lit("\\")) && ((si + 3) < sslen))) {
freak_word snx = freak_word_char_at(str_val, (si + 1));
if (freak_word_eq(snx, freak_word_lit("x"))) {
tmp = freak_word_concat(freak_word_concat(freak_word_concat(tmp, freak_word_lit("\\x")), freak_word_char_at(str_val, (si + 2))), freak_word_char_at(str_val, (si + 3)));
si += 4;
}
else {
tmp = freak_word_concat(tmp, freak_word_lit("\\\\"));
si += 1;
}
}
else {
if (freak_word_eq(sc, freak_word_lit("\n"))) {
tmp = freak_word_concat(tmp, freak_word_lit("\\n"));
si += 1;
}
else {
if (freak_word_eq(sc, freak_word_lit("\r"))) {
tmp = freak_word_concat(tmp, freak_word_lit("\\r"));
si += 1;
}
else {
if (freak_word_eq(sc, freak_word_lit("\t"))) {
tmp = freak_word_concat(tmp, freak_word_lit("\\t"));
si += 1;
}
else {
if (freak_word_eq(sc, freak_word_lit("\\"))) {
tmp = freak_word_concat(tmp, freak_word_lit("\\\\"));
si += 1;
}
else {
if (freak_word_eq(sc, freak_word_lit("\""))) {
tmp = freak_word_concat(tmp, freak_word_lit("\\\""));
si += 1;
}
else {
tmp = freak_word_concat(tmp, sc);
si += 1;
}
}
}
}
}
}
}
freak_emit(freak_word_concat(tmp, freak_word_lit("\")")));
}
void freak_emit_c_call(freak_word val, freak_word left) {
if (freak_word_starts_with(val, freak_word_lit("shape::ctor::"))) {
freak_word sname = freak_word_replace(val, freak_word_lit("shape::ctor::"), freak_word_lit(""));
int64_t field_count = freak_get_shape_field_count(sname);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit("freak_shape_alloc("), freak_word_from_int(field_count)), freak_word_lit(", ")));
if ((!freak_word_eq(left, freak_word_lit("")))) {
freak_emit_args(left);
}
freak_emit(freak_word_lit(")"));
return ;
}
freak_word mapped = freak_c_map_call(val);
if ((!freak_word_eq(mapped, freak_word_lit("")))) {
freak_emit(freak_word_concat(mapped, freak_word_lit("(")));
if ((!freak_word_eq(left, freak_word_lit("")))) {
freak_emit_args(left);
}
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_emt_is_extern(val)) {
freak_emit(freak_word_concat(freak_c_safe_ident(val), freak_word_lit("(")));
if ((!freak_word_eq(left, freak_word_lit("")))) {
freak_emit_args(left);
}
freak_emit(freak_word_lit(")"));
return ;
}
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit("freak_"), freak_c_safe_ident(val)), freak_word_lit("(")));
if ((!freak_word_eq(left, freak_word_lit("")))) {
freak_emit_args(left);
}
freak_emit(freak_word_lit(")"));
}
void freak_emit_c_method(freak_word val, freak_word left, freak_word right) {
if (freak_word_eq(val, freak_word_lit("length"))) {
freak_emit(freak_word_lit("freak_word_length("));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("to_int"))) {
freak_emit(freak_word_lit("freak_word_to_int("));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit("freak_word_"), val), freak_word_lit("(")));
freak_emit_expr(left);
if ((!freak_word_eq(right, freak_word_lit("")))) {
freak_emit(freak_word_lit(", "));
freak_emit_args(right);
}
freak_emit(freak_word_lit(")"));
}
void freak_emit_c_field(freak_word val, freak_word left) {
int64_t fidx = (0 - 1);
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
int64_t tmpidx = freak_get_shape_field_index(freak_array_get(shape_registry_names, si), val);
if ((tmpidx >= 0)) {
fidx = tmpidx;
}
si += 1;
}
if ((fidx < 0)) {
fidx = 0;
}
freak_emit(freak_word_lit("freak_llvm_shape_get("));
freak_emit_expr(left);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(", "), freak_word_from_int(fidx)), freak_word_lit(")")));
}
void freak_emit_c_binop(freak_word val, freak_word left, freak_word right) {
if (freak_word_eq(val, freak_word_lit("+"))) {
if ((freak_is_ast_word(left) || freak_is_ast_word(right))) {
freak_emit(freak_word_lit("freak_word_concat("));
freak_emit_expr(left);
freak_emit(freak_word_lit(", "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
return ;
}
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" + "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
return ;
}
if ((freak_word_eq(val, freak_word_lit("==")) || freak_word_eq(val, freak_word_lit("!=")))) {
if ((freak_is_ast_word(left) || freak_is_ast_word(right))) {
if (freak_word_eq(val, freak_word_lit("!="))) {
freak_emit(freak_word_lit("(!"));
}
freak_emit(freak_word_lit("freak_word_eq("));
freak_emit_expr(left);
freak_emit(freak_word_lit(", "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
if (freak_word_eq(val, freak_word_lit("!="))) {
freak_emit(freak_word_lit(")"));
}
return ;
}
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(" "), val), freak_word_lit(" ")));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("and"))) {
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" && "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("or"))) {
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" || "));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("NAKAMA"))) {
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" + "));
freak_emit_expr(right);
freak_emit(freak_word_lit(" + ("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" * "));
freak_emit_expr(right);
freak_emit(freak_word_lit(" / 10))"));
return ;
}
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(" "), val), freak_word_lit(" ")));
freak_emit_expr(right);
freak_emit(freak_word_lit(")"));
}
void freak_emit_c_unaryop(freak_word val, freak_word left) {
if (freak_word_eq(val, freak_word_lit("not"))) {
freak_emit(freak_word_lit("(!"));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("-"))) {
freak_emit(freak_word_lit("(-"));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("PLUS ULTRA"))) {
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" * 2)"));
return ;
}
if (freak_word_eq(val, freak_word_lit("FINAL FORM"))) {
freak_emit(freak_word_lit("("));
freak_emit_expr(left);
freak_emit(freak_word_lit(" * "));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
if (freak_word_eq(val, freak_word_lit("TSUNDERE"))) {
freak_emit(freak_word_lit("(-"));
freak_emit_expr(left);
freak_emit(freak_word_lit(")"));
return ;
}
}
void freak_emit_block(freak_word block) {
int64_t i = 0;
int64_t slen = freak_word_length(block);
freak_word cur_id = freak_word_lit("");
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(block, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((!freak_word_eq(cur_id, freak_word_lit("")))) {
freak_emit_stmt(cur_id);
}
cur_id = freak_word_lit("");
}
else {
cur_id = freak_word_concat(cur_id, c);
}
i += 1;
}
if ((!freak_word_eq(cur_id, freak_word_lit("")))) {
freak_emit_stmt(cur_id);
}
}
void freak_emit_stmt(freak_word eid) {
if ((freak_word_length(eid) == 0)) {
return ;
}
int64_t i = freak_word_to_int(eid);
freak_word kind = freak_array_get(ast_stmt_kinds, i);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
if (freak_word_eq(kind, STMT_PILOT)) {
freak_emit_stmt_pilot(eid);
return ;
}
if (freak_word_eq(kind, STMT_SAY)) {
freak_emit(freak_word_lit("freak_say("));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(");"));
return ;
}
if (freak_word_eq(kind, STMT_EXPR)) {
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(";"));
return ;
}
if (freak_word_eq(kind, STMT_GIVE_BACK)) {
freak_emit(freak_word_lit("return "));
if (((freak_word_length(expr_id_w) > 0) && (!freak_word_starts_with(expr_id_w, freak_word_lit("-"))))) {
freak_emit_expr(expr_id_w);
}
freak_emit_line(freak_word_lit(";"));
return ;
}
if (freak_word_eq(kind, STMT_IF)) {
freak_emit(freak_word_lit("if ("));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(") {"));
freak_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_emit_line(freak_word_lit("}"));
freak_word else_body_w = freak_array_get(ast_stmt_else_bodies, i);
if ((!freak_word_eq(else_body_w, freak_word_lit("")))) {
freak_emit_line(freak_word_lit("else {"));
freak_emit_block(else_body_w);
freak_emit_line(freak_word_lit("}"));
}
return ;
}
if (freak_word_eq(kind, STMT_REPEAT)) {
if (freak_word_eq(name_w, freak_word_lit("until"))) {
freak_emit(freak_word_lit("while (!("));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(")) {"));
freak_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_emit_line(freak_word_lit("}"));
}
else {
freak_emit(freak_word_lit("for (int64_t __rep = 0; __rep < "));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit("; __rep++) {"));
freak_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_emit_line(freak_word_lit("}"));
}
return ;
}
if (freak_word_eq(kind, STMT_TRAINING_ARC)) {
freak_word max_id_w = freak_array_get(ast_stmt_extras, i);
freak_emit(freak_word_lit("for (int64_t __arc = 0; __arc < "));
freak_emit_expr(max_id_w);
freak_emit_line(freak_word_lit("; __arc++) {"));
freak_emit(freak_word_lit("    if ("));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(") { break; }"));
freak_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_emit_line(freak_word_lit("}"));
return ;
}
if (freak_word_eq(kind, STMT_WHEN)) {
freak_emit_stmt_when(eid);
return ;
}
if (freak_word_eq(kind, STMT_BLOCK)) {
freak_emit_line(freak_word_lit("{"));
freak_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_emit_line(freak_word_lit("}"));
return ;
}
if (freak_word_eq(kind, STMT_ASSIGN)) {
freak_word op_w = name_w;
freak_word rhs_w = freak_array_get(ast_stmt_bodies, i);
freak_emit_expr(expr_id_w);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(" "), op_w), freak_word_lit(" ")));
freak_emit_expr(rhs_w);
freak_emit_line(freak_word_lit(";"));
return ;
}
if (freak_word_eq(kind, STMT_SHAPE)) {
freak_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("/* shape "), name_w), freak_word_lit(" */")));
return ;
}
if (freak_word_eq(kind, STMT_BREAK)) {
freak_emit_line(freak_word_lit("break;"));
return ;
}
if (freak_word_eq(kind, STMT_CONTINUE)) {
freak_emit_line(freak_word_lit("continue;"));
return ;
}
if (freak_word_eq(kind, STMT_EVENTUALLY)) {
freak_emit_line(freak_word_lit("/* eventually */"));
freak_word ev_body_w = freak_array_get(ast_stmt_bodies, i);
if ((freak_word_length(ev_body_w) > 0)) {
freak_emit_block(ev_body_w);
}
return ;
}
}
void freak_emit_stmt_pilot(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
int64_t e_idx = freak_word_to_int(expr_id_w);
freak_word e_kind = freak_array_get(ast_expr_kinds, e_idx);
freak_word type_ann_w = freak_array_get(ast_stmt_extras, i);
freak_word ctype = freak_word_lit("int64_t ");
freak_word vtype = freak_word_lit("i");
if (freak_word_eq(type_ann_w, freak_word_lit("word"))) {
ctype = freak_word_lit("freak_word ");
vtype = freak_word_lit("w");
}
if (freak_word_eq(type_ann_w, freak_word_lit("bool"))) {
ctype = freak_word_lit("bool ");
vtype = freak_word_lit("b");
}
if (freak_word_eq(type_ann_w, freak_word_lit("num"))) {
ctype = freak_word_lit("double ");
vtype = freak_word_lit("d");
}
if (freak_word_eq(type_ann_w, freak_word_lit("int"))) {
ctype = freak_word_lit("int64_t ");
vtype = freak_word_lit("i");
}
if (freak_word_eq(type_ann_w, freak_word_lit(""))) {
if (freak_is_ast_word(expr_id_w)) {
ctype = freak_word_lit("freak_word ");
vtype = freak_word_lit("w");
}
if (freak_word_eq(e_kind, EXPR_BOOL)) {
ctype = freak_word_lit("bool ");
vtype = freak_word_lit("b");
}
if (freak_word_eq(e_kind, EXPR_FLOAT)) {
ctype = freak_word_lit("double ");
vtype = freak_word_lit("d");
}
}
freak_emt_set_var_type(name_w, vtype);
freak_emit(freak_word_concat(freak_word_concat(ctype, name_w), freak_word_lit(" = ")));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(";"));
}
void freak_emit_stmt_when(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word target_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word cases_str = freak_array_get(ast_stmt_bodies, i);
freak_emit(freak_word_lit("{ int64_t __target = "));
freak_emit_expr(target_id_w);
freak_emit_line(freak_word_lit(";"));
int64_t cases_len = freak_word_length(cases_str);
int64_t ci = 0;
freak_word cur_case = freak_word_lit("");
bool is_first = true;
bool case_fin = false;
while (!(case_fin)) {
freak_word cc = freak_word_char_at(cases_str, ci);
if ((freak_word_eq(cc, freak_word_lit(",")) || (ci >= cases_len))) {
if ((!freak_word_eq(cur_case, freak_word_lit("")))) {
freak_word c_expr = freak_word_lit("");
freak_word c_stmt = freak_word_lit("");
bool in_expr = true;
int64_t c_len = freak_word_length(cur_case);
int64_t cj = 0;
for (int64_t __rep = 0; __rep < c_len; __rep++) {
freak_word p = freak_word_char_at(cur_case, cj);
if (freak_word_eq(p, freak_word_lit(":"))) {
in_expr = false;
}
else {
if (in_expr) {
c_expr = freak_word_concat(c_expr, p);
}
else {
c_stmt = freak_word_concat(c_stmt, p);
}
}
cj += 1;
}
if (freak_word_eq(c_expr, freak_word_lit("-1"))) {
if ((!is_first)) {
freak_emit(freak_word_lit("else "));
}
freak_emit_line(freak_word_lit("{"));
freak_emit_stmt(c_stmt);
freak_emit_line(freak_word_lit("}"));
}
else {
if ((!is_first)) {
freak_emit(freak_word_lit("else "));
}
freak_emit(freak_word_lit("if (__target == "));
freak_emit_expr(c_expr);
freak_emit_line(freak_word_lit(") {"));
freak_emit_stmt(c_stmt);
freak_emit_line(freak_word_lit("}"));
}
is_first = false;
}
cur_case = freak_word_lit("");
if ((ci >= cases_len)) {
case_fin = true;
}
}
else {
cur_case = freak_word_concat(cur_case, cc);
}
ci += 1;
}
freak_emit_line(freak_word_lit("}"));
}
freak_word freak_translate_params(freak_word p) {
freak_word res = freak_word_lit("");
freak_word cur_name = freak_word_lit("");
freak_word cur_type = freak_word_lit("");
bool in_type = false;
int64_t i = 0;
int64_t slen = freak_word_length(p);
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(p, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
in_type = true;
}
else {
if (freak_word_eq(c, freak_word_lit(","))) {
freak_word ctype = freak_word_lit("int64_t");
if (freak_word_eq(cur_type, freak_word_lit("word"))) {
ctype = freak_word_lit("freak_word");
}
if (freak_word_eq(cur_type, freak_word_lit("bool"))) {
ctype = freak_word_lit("bool");
}
if (freak_word_eq(cur_type, freak_word_lit("num"))) {
ctype = freak_word_lit("double");
}
if ((!freak_word_eq(res, freak_word_lit("")))) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(freak_word_concat(res, ctype), freak_word_lit(" ")), cur_name);
cur_name = freak_word_lit("");
cur_type = freak_word_lit("");
in_type = false;
}
else {
if (in_type) {
cur_type = freak_word_concat(cur_type, c);
}
else {
cur_name = freak_word_concat(cur_name, c);
}
}
}
i += 1;
}
if ((!freak_word_eq(cur_name, freak_word_lit("")))) {
freak_word ctype = freak_word_lit("int64_t");
if (freak_word_eq(cur_type, freak_word_lit("word"))) {
ctype = freak_word_lit("freak_word");
}
if (freak_word_eq(cur_type, freak_word_lit("bool"))) {
ctype = freak_word_lit("bool");
}
if (freak_word_eq(cur_type, freak_word_lit("num"))) {
ctype = freak_word_lit("double");
}
if ((!freak_word_eq(res, freak_word_lit("")))) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(freak_word_concat(res, ctype), freak_word_lit(" ")), cur_name);
}
return res;
}
freak_word freak_c_ret_type(freak_word returns_w) {
if (freak_word_eq(returns_w, freak_word_lit("int"))) {
return freak_word_lit("int64_t");
}
if (freak_word_eq(returns_w, freak_word_lit("word"))) {
return freak_word_lit("freak_word");
}
if (freak_word_eq(returns_w, freak_word_lit("bool"))) {
return freak_word_lit("bool");
}
if (freak_word_eq(returns_w, freak_word_lit("num"))) {
return freak_word_lit("double");
}
return freak_word_lit("void");
}
void freak_emit_task(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word body_id_w = freak_array_get(ast_stmt_bodies, i);
freak_word params_w = freak_array_get(ast_task_params, i);
freak_word returns_w = freak_array_get(ast_task_returns, i);
freak_word c_ret = freak_c_ret_type(returns_w);
freak_word c_params = freak_word_lit("void");
if ((!freak_word_eq(params_w, freak_word_lit("")))) {
c_params = freak_translate_params(params_w);
freak_register_param_types(params_w);
}
freak_emit(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(c_ret, freak_word_lit(" freak_")), name_w), freak_word_lit("(")), c_params));
freak_emit_line(freak_word_lit(") {"));
freak_emit_block(body_id_w);
freak_emit_line(freak_word_lit("}"));
}
void freak_register_param_types(freak_word params_w) {
int64_t pi = 0;
int64_t pslen = freak_word_length(params_w);
freak_word pname = freak_word_lit("");
freak_word ptype = freak_word_lit("");
bool in_ptype = false;
for (int64_t __rep = 0; __rep < pslen; __rep++) {
freak_word pc = freak_word_char_at(params_w, pi);
if (freak_word_eq(pc, freak_word_lit(":"))) {
in_ptype = true;
}
else {
if (freak_word_eq(pc, freak_word_lit(","))) {
if (freak_word_eq(ptype, freak_word_lit("word"))) {
freak_emt_set_var_type(pname, freak_word_lit("w"));
}
else {
if (freak_word_eq(ptype, freak_word_lit("bool"))) {
freak_emt_set_var_type(pname, freak_word_lit("b"));
}
else {
if (freak_word_eq(ptype, freak_word_lit("num"))) {
freak_emt_set_var_type(pname, freak_word_lit("d"));
}
else {
freak_emt_set_var_type(pname, freak_word_lit("i"));
}
}
}
pname = freak_word_lit("");
ptype = freak_word_lit("");
in_ptype = false;
}
else {
if (in_ptype) {
ptype = freak_word_concat(ptype, pc);
}
else {
pname = freak_word_concat(pname, pc);
}
}
}
pi += 1;
}
if ((!freak_word_eq(pname, freak_word_lit("")))) {
if (freak_word_eq(ptype, freak_word_lit("word"))) {
freak_emt_set_var_type(pname, freak_word_lit("w"));
}
else {
if (freak_word_eq(ptype, freak_word_lit("bool"))) {
freak_emt_set_var_type(pname, freak_word_lit("b"));
}
else {
if (freak_word_eq(ptype, freak_word_lit("num"))) {
freak_emt_set_var_type(pname, freak_word_lit("d"));
}
else {
freak_emt_set_var_type(pname, freak_word_lit("i"));
}
}
}
}
}
void freak_emit_global_decl(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
int64_t e_idx = freak_word_to_int(expr_id_w);
freak_word e_kind = freak_array_get(ast_expr_kinds, e_idx);
freak_word type_ann_w = freak_array_get(ast_stmt_extras, i);
freak_word ctype = freak_word_lit("int64_t ");
freak_word defval = freak_word_lit(" = 0");
freak_word vtype = freak_word_lit("i");
if (freak_word_eq(type_ann_w, freak_word_lit("word"))) {
ctype = freak_word_lit("freak_word ");
defval = freak_word_lit(" = FREAK_WORD_EMPTY");
vtype = freak_word_lit("w");
}
if (freak_word_eq(type_ann_w, freak_word_lit("bool"))) {
ctype = freak_word_lit("bool ");
defval = freak_word_lit(" = false");
vtype = freak_word_lit("b");
}
if (freak_word_eq(type_ann_w, freak_word_lit("num"))) {
ctype = freak_word_lit("double ");
defval = freak_word_lit(" = 0.0");
vtype = freak_word_lit("d");
}
if (freak_word_eq(type_ann_w, freak_word_lit(""))) {
if (freak_is_ast_word(expr_id_w)) {
ctype = freak_word_lit("freak_word ");
defval = freak_word_lit(" = FREAK_WORD_EMPTY");
vtype = freak_word_lit("w");
}
if (freak_word_eq(e_kind, EXPR_BOOL)) {
ctype = freak_word_lit("bool ");
defval = freak_word_lit(" = false");
vtype = freak_word_lit("b");
}
if (freak_word_eq(e_kind, EXPR_FLOAT)) {
ctype = freak_word_lit("double ");
defval = freak_word_lit(" = 0.0");
vtype = freak_word_lit("d");
}
}
freak_emt_set_var_type(name_w, vtype);
freak_emit(freak_word_concat(freak_word_concat(ctype, name_w), defval));
freak_emit_line(freak_word_lit(";"));
}
void freak_emit_global_init(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_emit(freak_word_concat(name_w, freak_word_lit(" = ")));
freak_emit_expr(expr_id_w);
freak_emit_line(freak_word_lit(";"));
}
void freak_emit_fwd_decl(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word params_w = freak_array_get(ast_task_params, i);
freak_word returns_w = freak_array_get(ast_task_returns, i);
if (freak_word_eq(returns_w, freak_word_lit("word"))) {
freak_emt_register_word_task(name_w);
}
freak_word c_ret = freak_c_ret_type(returns_w);
freak_word c_params = freak_word_lit("void");
if ((!freak_word_eq(params_w, freak_word_lit("")))) {
c_params = freak_translate_params(params_w);
}
freak_emit(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(c_ret, freak_word_lit(" freak_")), name_w), freak_word_lit("(")), c_params));
freak_emit_line(freak_word_lit(");"));
}
void freak_emit_extern_decl(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word params_w = freak_array_get(ast_task_params, i);
freak_word returns_w = freak_array_get(ast_task_returns, i);
freak_emt_register_extern(name_w, returns_w);
freak_word c_ret = freak_c_ret_type(returns_w);
freak_word c_params = freak_word_lit("void");
if ((!freak_word_eq(params_w, freak_word_lit("")))) {
c_params = freak_translate_params(params_w);
}
freak_emit(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("extern "), c_ret), freak_word_lit(" ")), name_w), freak_word_lit("(")), c_params));
freak_emit_line(freak_word_lit(");"));
}
void freak_emit_c_program(void) {
freak_emit_line(freak_word_lit("#include \"freak_runtime.h\""));
int64_t top_count = freak_array_len(ast_top_stmts);
int64_t i = 0;
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_TASK)) {
freak_emit_fwd_decl(cur_id);
}
if (freak_word_eq(kind, STMT_EXTERN)) {
freak_emit_extern_decl(cur_id);
}
i += 1;
}
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_PILOT)) {
freak_emit_global_decl(cur_id);
}
i += 1;
}
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_TASK)) {
freak_emit_task(cur_id);
}
i += 1;
}
bool has_user_main = false;
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_TASK)) {
freak_word tname = freak_array_get(ast_stmt_names, freak_word_to_int(cur_id));
if (freak_word_eq(tname, freak_word_lit("main"))) {
has_user_main = true;
}
}
i += 1;
}
if (has_user_main) {
freak_emit_line(freak_word_lit("void freak_init_globals(void) {"));
}
if ((!has_user_main)) {
freak_emit_line(freak_word_lit("void freak_main(void) {"));
}
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_PILOT)) {
freak_emit_global_init(cur_id);
}
i += 1;
}
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (((((!freak_word_eq(kind, STMT_TASK)) && (!freak_word_eq(kind, STMT_SHAPE))) && (!freak_word_eq(kind, STMT_PILOT))) && (!freak_word_eq(kind, STMT_EXTERN)))) {
freak_emit_stmt(cur_id);
}
i += 1;
}
freak_emit_line(freak_word_lit("}"));
freak_emit_line(freak_word_lit("int main(int argc, char** argv) {"));
freak_emit_line(freak_word_lit("    freak_argc = argc;"));
freak_emit_line(freak_word_lit("    freak_argv = argv;"));
if (has_user_main) {
freak_emit_line(freak_word_lit("    freak_init_globals();"));
freak_emit_line(freak_word_lit("    freak_main();"));
}
if ((!has_user_main)) {
freak_emit_line(freak_word_lit("    freak_main();"));
}
freak_emit_line(freak_word_lit("    return 0;"));
freak_emit_line(freak_word_lit("}"));
}
void freak_llvm_emit(freak_word s) {
freak_fs_append(out_file, s);
}
void freak_llvm_emit_line(freak_word s) {
freak_fs_append(out_file, freak_word_concat(s, freak_word_lit("\n")));
}
freak_word freak_next_reg(void) {
freak_word r = freak_word_concat(freak_word_lit("%t"), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
return r;
}
freak_word freak_llvm_escape_str(freak_word s) {
freak_word esc_out = freak_word_lit("");
int64_t esc_len = freak_word_length(s);
int64_t esc_i = 0;
while (!((esc_i >= esc_len))) {
freak_word ch = freak_word_char_at(s, esc_i);
if ((freak_word_eq(ch, freak_word_lit("\\")) && ((esc_i + 3) < esc_len))) {
freak_word nx = freak_word_char_at(s, (esc_i + 1));
if (freak_word_eq(nx, freak_word_lit("x"))) {
freak_word h1 = freak_word_char_at(s, (esc_i + 2));
freak_word h2 = freak_word_char_at(s, (esc_i + 3));
esc_out = freak_word_concat(freak_word_concat(freak_word_concat(esc_out, freak_word_lit("\\")), h1), h2);
esc_i += 4;
}
else {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\5C"));
esc_i += 1;
}
}
else {
if (freak_word_eq(ch, freak_word_lit("\""))) {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\22"));
esc_i += 1;
}
else {
if (freak_word_eq(ch, freak_word_lit("\\"))) {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\5C"));
esc_i += 1;
}
else {
if (freak_word_eq(ch, freak_word_lit("\n"))) {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\0A"));
esc_i += 1;
}
else {
if (freak_word_eq(ch, freak_word_lit("\r"))) {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\0D"));
esc_i += 1;
}
else {
if (freak_word_eq(ch, freak_word_lit("\t"))) {
esc_out = freak_word_concat(esc_out, freak_word_lit("\\09"));
esc_i += 1;
}
else {
esc_out = freak_word_concat(esc_out, ch);
esc_i += 1;
}
}
}
}
}
}
}
return esc_out;
}
freak_word freak_register_string_literal(freak_word val) {
freak_word id = freak_word_concat(freak_word_lit("@.str."), freak_word_from_int(string_literals_count));
string_literals_count += 1;
freak_word real_val = freak_word_replace(val, freak_word_lit("<<PIPE>>"), freak_word_lit("|"));
int64_t len = freak_word_length(real_val);
int64_t adj_i = 0;
while (!((adj_i >= len))) {
freak_word adj_ch = freak_word_char_at(real_val, adj_i);
if ((freak_word_eq(adj_ch, freak_word_lit("\\")) && ((adj_i + 3) < len))) {
freak_word adj_nx = freak_word_char_at(real_val, (adj_i + 1));
if (freak_word_eq(adj_nx, freak_word_lit("x"))) {
len -= 3;
adj_i += 4;
}
else {
adj_i += 1;
}
}
else {
adj_i += 1;
}
}
int64_t null_term_len = (len + 1);
freak_word escaped = freak_llvm_escape_str(real_val);
freak_word decl = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(id, freak_word_lit(" = private unnamed_addr constant [")), freak_word_from_int(null_term_len)), freak_word_lit(" x i8] c\"")), escaped), freak_word_lit("\\00\", align 1\n"));
string_literals = freak_word_concat(string_literals, decl);
return id;
}
freak_word freak_llvm_c_safe_ident(freak_word s) {
freak_word res = freak_word_lit("");
int64_t slen = freak_word_length(s);
int64_t i = 0;
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(s, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
if (((i + 1) < slen)) {
if (freak_word_eq(freak_word_char_at(s, (i + 1)), freak_word_lit(":"))) {
res = freak_word_concat(res, freak_word_lit("_"));
i += 1;
}
else {
res = freak_word_concat(res, c);
}
}
else {
res = freak_word_concat(res, c);
}
}
else {
res = freak_word_concat(res, c);
}
i += 1;
}
return res;
}
void freak_llvm_set_var_type(freak_word name, freak_word vtype) {
llvm_var_names = freak_word_concat(freak_word_concat(llvm_var_names, name), freak_word_lit("|"));
llvm_var_types = freak_word_concat(freak_word_concat(llvm_var_types, vtype), freak_word_lit("|"));
}
freak_word freak_llvm_get_var_type(freak_word name) {
int64_t nlen = freak_word_length(llvm_var_names);
int64_t i = 0;
freak_word cur_name = freak_word_lit("");
int64_t idx = 0;
while (!((i >= nlen))) {
freak_word c = freak_word_char_at(llvm_var_names, i);
if (freak_word_eq(c, freak_word_lit("|"))) {
if (freak_word_eq(cur_name, name)) {
int64_t ti = 0;
freak_word cur_type = freak_word_lit("");
int64_t tidx = 0;
int64_t tlen = freak_word_length(llvm_var_types);
while (!((ti >= tlen))) {
freak_word tc = freak_word_char_at(llvm_var_types, ti);
if (freak_word_eq(tc, freak_word_lit("|"))) {
if ((tidx == idx)) {
return cur_type;
}
tidx += 1;
cur_type = freak_word_lit("");
}
else {
cur_type = freak_word_concat(cur_type, tc);
}
ti += 1;
}
}
idx += 1;
cur_name = freak_word_lit("");
}
else {
cur_name = freak_word_concat(cur_name, c);
}
i += 1;
}
return freak_word_lit("i");
}
void freak_llvm_register_task(freak_word name, freak_word ret_type) {
freak_word t = freak_word_lit("i");
if (freak_word_eq(ret_type, freak_word_lit("word"))) {
t = freak_word_lit("w");
}
if (freak_word_eq(ret_type, freak_word_lit("bool"))) {
t = freak_word_lit("b");
}
if (freak_word_eq(ret_type, freak_word_lit("num"))) {
t = freak_word_lit("n");
}
if (freak_word_eq(ret_type, freak_word_lit("int"))) {
t = freak_word_lit("i");
}
if (freak_word_eq(ret_type, freak_word_lit("void"))) {
t = freak_word_lit("v");
}
llvm_task_reg_names = freak_word_concat(freak_word_concat(llvm_task_reg_names, name), freak_word_lit("|"));
llvm_task_reg_types = freak_word_concat(freak_word_concat(llvm_task_reg_types, t), freak_word_lit("|"));
llvm_task_reg_count += 1;
}
freak_word freak_llvm_get_task_ret_type(freak_word name) {
int64_t nlen = freak_word_length(llvm_task_reg_names);
int64_t i = 0;
freak_word cur_name = freak_word_lit("");
int64_t idx = 0;
while (!((i >= nlen))) {
freak_word c = freak_word_char_at(llvm_task_reg_names, i);
if (freak_word_eq(c, freak_word_lit("|"))) {
if (freak_word_eq(cur_name, name)) {
int64_t ti = 0;
freak_word cur_type = freak_word_lit("");
int64_t tidx = 0;
int64_t tlen = freak_word_length(llvm_task_reg_types);
while (!((ti >= tlen))) {
freak_word tc = freak_word_char_at(llvm_task_reg_types, ti);
if (freak_word_eq(tc, freak_word_lit("|"))) {
if ((tidx == idx)) {
return cur_type;
}
tidx += 1;
cur_type = freak_word_lit("");
}
else {
cur_type = freak_word_concat(cur_type, tc);
}
ti += 1;
}
}
idx += 1;
cur_name = freak_word_lit("");
}
else {
cur_name = freak_word_concat(cur_name, c);
}
i += 1;
}
return freak_word_lit("");
}
bool freak_llvm_is_global(freak_word vname) {
freak_word needle = freak_word_concat(freak_word_concat(freak_word_lit("|"), vname), freak_word_lit("|"));
return freak_word_contains(llvm_global_names, needle);
}
void freak_llvm_reg_var(freak_word freak_name, freak_word llvm_name) {
llvm_var_reg_map = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(llvm_var_reg_map, freak_name), freak_word_lit(":")), llvm_name), freak_word_lit("|"));
}
freak_word freak_llvm_get_llvm_name(freak_word freak_name) {
int64_t mlen = freak_word_length(llvm_var_reg_map);
int64_t i = (mlen - 1);
freak_word cur_llvm = freak_word_lit("");
freak_word cur_freak = freak_word_lit("");
bool in_llvm = true;
while (!((i < 0))) {
freak_word ch = freak_word_char_at(llvm_var_reg_map, i);
if (freak_word_eq(ch, freak_word_lit("|"))) {
if ((freak_word_eq(cur_freak, freak_name) && (freak_word_length(cur_llvm) > 0))) {
return cur_llvm;
}
cur_llvm = freak_word_lit("");
cur_freak = freak_word_lit("");
in_llvm = true;
}
else {
if (freak_word_eq(ch, freak_word_lit(":"))) {
in_llvm = false;
}
else {
if (in_llvm) {
cur_llvm = freak_word_concat(ch, cur_llvm);
}
else {
cur_freak = freak_word_concat(ch, cur_freak);
}
}
}
i -= 1;
}
if ((freak_word_eq(cur_freak, freak_name) && (freak_word_length(cur_llvm) > 0))) {
return cur_llvm;
}
return freak_word_lit("");
}
freak_word freak_llvm_var_ptr(freak_word vname) {
if (freak_llvm_is_global(vname)) {
return freak_word_concat(freak_word_lit("@g_"), vname);
}
freak_word unique = freak_llvm_get_llvm_name(vname);
if ((!freak_word_eq(unique, freak_word_lit("")))) {
return freak_word_concat(freak_word_lit("%"), unique);
}
return freak_word_concat(freak_word_lit("%"), vname);
}
bool freak_llvm_is_runtime_func(freak_word fname) {
freak_word needle = freak_word_concat(freak_word_concat(freak_word_lit("|"), fname), freak_word_lit("|"));
return freak_word_contains(llvm_declared_funcs, needle);
}
freak_word freak_llvm_infer_expr_type(freak_word expr_id) {
if ((freak_word_length(expr_id) == 0)) {
return freak_word_lit("i");
}
int64_t i = freak_word_to_int(expr_id);
freak_word kind = freak_array_get(ast_expr_kinds, i);
freak_word val = freak_array_get(ast_expr_vals, i);
if (freak_word_eq(kind, EXPR_STR)) {
return freak_word_lit("w");
}
if (freak_word_eq(kind, EXPR_INT)) {
return freak_word_lit("i");
}
if (freak_word_eq(kind, EXPR_FLOAT)) {
return freak_word_lit("n");
}
if (freak_word_eq(kind, EXPR_BOOL)) {
return freak_word_lit("b");
}
if (freak_word_eq(kind, EXPR_IDENT)) {
return freak_llvm_get_var_type(val);
}
if (freak_word_eq(kind, EXPR_METHOD)) {
if (((((freak_word_eq(val, freak_word_lit("trim")) || freak_word_eq(val, freak_word_lit("to_upper"))) || freak_word_eq(val, freak_word_lit("to_lower"))) || freak_word_eq(val, freak_word_lit("replace"))) || freak_word_eq(val, freak_word_lit("char_at")))) {
return freak_word_lit("w");
}
if (((((freak_word_eq(val, freak_word_lit("length")) || freak_word_eq(val, freak_word_lit("to_int"))) || freak_word_eq(val, freak_word_lit("contains"))) || freak_word_eq(val, freak_word_lit("starts_with"))) || freak_word_eq(val, freak_word_lit("ends_with")))) {
return freak_word_lit("i");
}
int64_t mi = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
freak_word msname = freak_word_concat(freak_word_lit(""), freak_array_get(shape_registry_names, mi));
freak_word impl_ret = freak_llvm_get_task_ret_type(freak_word_concat(freak_word_concat(msname, freak_word_lit("_")), val));
if ((freak_word_length(impl_ret) > 0)) {
return impl_ret;
}
mi += 1;
}
}
if (freak_word_eq(kind, EXPR_FIELD)) {
return freak_llvm_infer_field_type(val);
}
if (freak_word_eq(kind, EXPR_BINOP)) {
freak_word left = freak_array_get(ast_expr_lefts, i);
freak_word right = freak_array_get(ast_expr_rights, i);
freak_word lt = freak_llvm_infer_expr_type(left);
freak_word rt = freak_llvm_infer_expr_type(right);
if (freak_word_eq(val, freak_word_lit("+"))) {
if ((freak_word_starts_with(lt, freak_word_lit("w")) || freak_word_starts_with(rt, freak_word_lit("w")))) {
return freak_word_lit("w");
}
}
if ((freak_word_starts_with(lt, freak_word_lit("n")) || freak_word_starts_with(rt, freak_word_lit("n")))) {
if (((((freak_word_eq(val, freak_word_lit("+")) || freak_word_eq(val, freak_word_lit("-"))) || freak_word_eq(val, freak_word_lit("*"))) || freak_word_eq(val, freak_word_lit("/"))) || freak_word_eq(val, freak_word_lit("%")))) {
return freak_word_lit("n");
}
}
}
if (freak_word_eq(kind, EXPR_CALL)) {
return freak_llvm_infer_call_type(val);
}
return freak_word_lit("i");
}
freak_word freak_llvm_infer_field_type(freak_word field_name) {
int64_t fi = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
freak_word fields = freak_word_concat(freak_word_lit(""), freak_array_get(shape_registry_fields, fi));
int64_t flen = freak_word_length(fields);
int64_t fj = 0;
freak_word fname = freak_word_lit("");
freak_word ftype = freak_word_lit("");
bool in_ftype = false;
for (int64_t __rep = 0; __rep < flen; __rep++) {
freak_word ftc = freak_word_concat(freak_word_lit(""), freak_word_char_at(fields, fj));
if (freak_word_eq(ftc, freak_word_lit(","))) {
if (freak_word_eq(fname, field_name)) {
if ((freak_word_eq(ftype, freak_word_lit("num")) || freak_word_eq(ftype, freak_word_lit("float")))) {
return freak_word_lit("n");
}
if (freak_word_eq(ftype, freak_word_lit("word"))) {
return freak_word_lit("w");
}
if (freak_word_eq(ftype, freak_word_lit("bool"))) {
return freak_word_lit("b");
}
return freak_word_lit("i");
}
fname = freak_word_lit("");
ftype = freak_word_lit("");
in_ftype = false;
}
else {
if (freak_word_eq(ftc, freak_word_lit(":"))) {
in_ftype = true;
}
else {
if (in_ftype) {
ftype = freak_word_concat(ftype, ftc);
}
else {
fname = freak_word_concat(fname, ftc);
}
}
}
fj += 1;
}
if (freak_word_eq(fname, field_name)) {
if ((freak_word_eq(ftype, freak_word_lit("num")) || freak_word_eq(ftype, freak_word_lit("float")))) {
return freak_word_lit("n");
}
if (freak_word_eq(ftype, freak_word_lit("word"))) {
return freak_word_lit("w");
}
if (freak_word_eq(ftype, freak_word_lit("bool"))) {
return freak_word_lit("b");
}
return freak_word_lit("i");
}
fi += 1;
}
return freak_word_lit("i");
}
freak_word freak_llvm_infer_call_type(freak_word val) {
if (((freak_word_eq(val, freak_word_lit("fs::read")) || freak_word_eq(val, freak_word_lit("fs::list_dir"))) || freak_word_eq(val, freak_word_lit("process::arg")))) {
return freak_word_lit("w");
}
if ((freak_word_eq(val, freak_word_lit("process::exec_capture")) || freak_word_eq(val, freak_word_lit("ask")))) {
return freak_word_lit("w");
}
if ((((freak_word_eq(val, freak_word_lit("word_from_int")) || freak_word_eq(val, freak_word_lit("word_from_bool"))) || freak_word_eq(val, freak_word_lit("word_concat"))) || freak_word_eq(val, freak_word_lit("format_num")))) {
return freak_word_lit("w");
}
if (freak_word_eq(val, freak_word_lit("array_get"))) {
return freak_word_lit("w");
}
if ((freak_word_eq(val, freak_word_lit("array_new")) || freak_word_eq(val, freak_word_lit("array_len")))) {
return freak_word_lit("i");
}
if (freak_word_starts_with(val, freak_word_lit("shape::ctor::"))) {
return freak_word_lit("i");
}
freak_word task_ret = freak_llvm_get_task_ret_type(val);
if ((freak_word_length(task_ret) > 0)) {
return task_ret;
}
return freak_word_lit("i");
}
freak_word freak_llvm_i64_to_double(freak_word i64_reg) {
freak_word dbl = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), dbl), freak_word_lit(" = bitcast i64 ")), i64_reg), freak_word_lit(" to double")));
return dbl;
}
freak_word freak_llvm_double_to_i64(freak_word dbl_reg) {
freak_word i64r = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), i64r), freak_word_lit(" = bitcast double ")), dbl_reg), freak_word_lit(" to i64")));
return i64r;
}
bool freak_llvm_is_num_expr(freak_word expr_id) {
freak_word t = freak_llvm_infer_expr_type(expr_id);
if (freak_word_starts_with(t, freak_word_lit("n"))) {
return true;
}
return false;
}
freak_word freak_llvm_map_call_name(freak_word val) {
if (freak_word_eq(val, freak_word_lit("say"))) {
return freak_word_lit("@freak_llvm_say");
}
if (freak_word_eq(val, freak_word_lit("ask"))) {
return freak_word_lit("@freak_llvm_ask");
}
if (freak_word_eq(val, freak_word_lit("word_from_int"))) {
return freak_word_lit("@freak_llvm_word_from_int");
}
if (freak_word_eq(val, freak_word_lit("word_from_bool"))) {
return freak_word_lit("@freak_llvm_word_from_bool");
}
if (freak_word_eq(val, freak_word_lit("word_to_int"))) {
return freak_word_lit("@freak_llvm_word_to_int");
}
if (freak_word_eq(val, freak_word_lit("fs::read"))) {
return freak_word_lit("@freak_llvm_fs_read");
}
if (freak_word_eq(val, freak_word_lit("fs::write"))) {
return freak_word_lit("@freak_llvm_fs_write");
}
if (freak_word_eq(val, freak_word_lit("fs::append"))) {
return freak_word_lit("@freak_llvm_fs_append");
}
if (freak_word_eq(val, freak_word_lit("fs::exists"))) {
return freak_word_lit("@freak_llvm_fs_exists");
}
if (freak_word_eq(val, freak_word_lit("fs::delete"))) {
return freak_word_lit("@freak_llvm_fs_delete");
}
if (freak_word_eq(val, freak_word_lit("process::args_count"))) {
return freak_word_lit("@freak_llvm_process_args_count");
}
if (freak_word_eq(val, freak_word_lit("process::arg"))) {
return freak_word_lit("@freak_llvm_process_arg");
}
if (freak_word_eq(val, freak_word_lit("process::exit"))) {
return freak_word_lit("@freak_llvm_process_exit");
}
if (freak_word_eq(val, freak_word_lit("process::exec"))) {
return freak_word_lit("@freak_llvm_process_exec");
}
if (freak_word_eq(val, freak_word_lit("process::exec_capture"))) {
return freak_word_lit("@freak_llvm_process_exec_capture");
}
if (freak_word_eq(val, freak_word_lit("panic"))) {
return freak_word_lit("@freak_llvm_panic");
}
if (freak_word_eq(val, freak_word_lit("array_new"))) {
return freak_word_lit("@freak_llvm_array_new");
}
if (freak_word_eq(val, freak_word_lit("array_push"))) {
return freak_word_lit("@freak_llvm_array_push");
}
if (freak_word_eq(val, freak_word_lit("array_get"))) {
return freak_word_lit("@freak_llvm_array_get");
}
if (freak_word_eq(val, freak_word_lit("array_set"))) {
return freak_word_lit("@freak_llvm_array_set");
}
if (freak_word_eq(val, freak_word_lit("array_len"))) {
return freak_word_lit("@freak_llvm_array_len");
}
if (freak_word_eq(val, freak_word_lit("ui::create_window"))) {
return freak_word_lit("@freak_llvm_ui_create_window");
}
if (freak_word_eq(val, freak_word_lit("ui::destroy_window"))) {
return freak_word_lit("@freak_llvm_ui_destroy_window");
}
if (freak_word_eq(val, freak_word_lit("ui::poll_events"))) {
return freak_word_lit("@freak_llvm_ui_poll_events");
}
if (freak_word_eq(val, freak_word_lit("ui::begin_frame"))) {
return freak_word_lit("@freak_llvm_ui_begin_frame");
}
if (freak_word_eq(val, freak_word_lit("ui::end_frame"))) {
return freak_word_lit("@freak_llvm_ui_end_frame");
}
if (freak_word_eq(val, freak_word_lit("ui::event_kind"))) {
return freak_word_lit("@freak_llvm_ui_event_kind");
}
if (freak_word_eq(val, freak_word_lit("ui::event_key"))) {
return freak_word_lit("@freak_llvm_ui_event_key");
}
if (freak_word_eq(val, freak_word_lit("ui::event_pressed"))) {
return freak_word_lit("@freak_llvm_ui_event_pressed");
}
if (freak_word_eq(val, freak_word_lit("ui::event_character"))) {
return freak_word_lit("@freak_llvm_ui_event_character");
}
if (freak_word_eq(val, freak_word_lit("ui::event_mouse_x"))) {
return freak_word_lit("@freak_llvm_ui_event_mouse_x");
}
if (freak_word_eq(val, freak_word_lit("ui::event_mouse_y"))) {
return freak_word_lit("@freak_llvm_ui_event_mouse_y");
}
if (freak_word_eq(val, freak_word_lit("ui::event_button"))) {
return freak_word_lit("@freak_llvm_ui_event_button");
}
if (freak_word_eq(val, freak_word_lit("ui::clear"))) {
return freak_word_lit("@freak_llvm_ui_clear");
}
if (freak_word_eq(val, freak_word_lit("ui::fill_rect"))) {
return freak_word_lit("@freak_llvm_ui_fill_rect");
}
if (freak_word_eq(val, freak_word_lit("ui::stroke_rect"))) {
return freak_word_lit("@freak_llvm_ui_stroke_rect");
}
if (freak_word_eq(val, freak_word_lit("ui::fill_circle"))) {
return freak_word_lit("@freak_llvm_ui_fill_circle");
}
if (freak_word_eq(val, freak_word_lit("ui::draw_line"))) {
return freak_word_lit("@freak_llvm_ui_draw_line");
}
if (freak_word_eq(val, freak_word_lit("ui::draw_text"))) {
return freak_word_lit("@freak_llvm_ui_draw_text");
}
if (freak_word_eq(val, freak_word_lit("ui::measure_text"))) {
return freak_word_lit("@freak_llvm_ui_measure_text");
}
if (freak_word_eq(val, freak_word_lit("math::sqrt"))) {
return freak_word_lit("@freak_llvm_math_sqrt");
}
if (freak_word_eq(val, freak_word_lit("math::pow"))) {
return freak_word_lit("@freak_llvm_math_pow");
}
if (freak_word_eq(val, freak_word_lit("math::sin"))) {
return freak_word_lit("@freak_llvm_math_sin");
}
if (freak_word_eq(val, freak_word_lit("math::cos"))) {
return freak_word_lit("@freak_llvm_math_cos");
}
if (freak_word_eq(val, freak_word_lit("math::tan"))) {
return freak_word_lit("@freak_llvm_math_tan");
}
if (freak_word_eq(val, freak_word_lit("math::floor"))) {
return freak_word_lit("@freak_llvm_math_floor");
}
if (freak_word_eq(val, freak_word_lit("math::ceil"))) {
return freak_word_lit("@freak_llvm_math_ceil");
}
if (freak_word_eq(val, freak_word_lit("parse_num"))) {
return freak_word_lit("@freak_llvm_parse_num");
}
if (freak_word_eq(val, freak_word_lit("format_num"))) {
return freak_word_lit("@freak_llvm_format_num");
}
if (freak_word_eq(val, freak_word_lit("shape::alloc"))) {
return freak_word_lit("@freak_llvm_shape_alloc");
}
if (freak_word_eq(val, freak_word_lit("shape::get"))) {
return freak_word_lit("@freak_llvm_shape_get");
}
if (freak_word_eq(val, freak_word_lit("shape::set"))) {
return freak_word_lit("@freak_llvm_shape_set");
}
if ((freak_word_eq(val, freak_word_lit("tcp::connect")) || freak_word_eq(val, freak_word_lit("tcp_connect")))) {
return freak_word_lit("@freak_llvm_tcp_connect");
}
if ((freak_word_eq(val, freak_word_lit("tcp::send")) || freak_word_eq(val, freak_word_lit("tcp_send")))) {
return freak_word_lit("@freak_llvm_tcp_send");
}
if ((freak_word_eq(val, freak_word_lit("tcp::recv")) || freak_word_eq(val, freak_word_lit("tcp_recv")))) {
return freak_word_lit("@freak_llvm_tcp_recv");
}
if ((freak_word_eq(val, freak_word_lit("tcp::recv_all")) || freak_word_eq(val, freak_word_lit("tcp_recv_all")))) {
return freak_word_lit("@freak_llvm_tcp_recv_all");
}
if ((freak_word_eq(val, freak_word_lit("tcp::close")) || freak_word_eq(val, freak_word_lit("tcp_close")))) {
return freak_word_lit("@freak_llvm_tcp_close");
}
return freak_word_lit("");
}
bool freak_llvm_is_void_call(freak_word val) {
if ((freak_word_eq(val, freak_word_lit("say")) || freak_word_eq(val, freak_word_lit("panic")))) {
return true;
}
if (((freak_word_eq(val, freak_word_lit("fs::write")) || freak_word_eq(val, freak_word_lit("fs::append"))) || freak_word_eq(val, freak_word_lit("fs::delete")))) {
return true;
}
if (freak_word_eq(val, freak_word_lit("process::exit"))) {
return true;
}
if ((freak_word_eq(val, freak_word_lit("array_push")) || freak_word_eq(val, freak_word_lit("array_set")))) {
return true;
}
if (freak_word_eq(val, freak_word_lit("shape::set"))) {
return true;
}
if ((freak_word_eq(val, freak_word_lit("tcp::close")) || freak_word_eq(val, freak_word_lit("tcp_close")))) {
return true;
}
if (((freak_word_eq(val, freak_word_lit("ui::destroy_window")) || freak_word_eq(val, freak_word_lit("ui::begin_frame"))) || freak_word_eq(val, freak_word_lit("ui::end_frame")))) {
return true;
}
if (((freak_word_eq(val, freak_word_lit("ui::clear")) || freak_word_eq(val, freak_word_lit("ui::fill_rect"))) || freak_word_eq(val, freak_word_lit("ui::stroke_rect")))) {
return true;
}
if ((freak_word_eq(val, freak_word_lit("ui::fill_circle")) || freak_word_eq(val, freak_word_lit("ui::draw_line")))) {
return true;
}
return false;
}
freak_word freak_llvm_emit_args(freak_word args) {
freak_word res = freak_word_lit("");
int64_t i = 0;
int64_t slen = freak_word_length(args);
freak_word cur_id = freak_word_lit("");
bool first = true;
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(args, i);
if (freak_word_eq(c, freak_word_lit(","))) {
freak_word reg = freak_llvm_emit_expr(cur_id);
if ((!first)) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(res, freak_word_lit("i64 ")), reg);
cur_id = freak_word_lit("");
first = false;
}
else {
cur_id = freak_word_concat(cur_id, c);
}
i += 1;
}
if ((freak_word_length(cur_id) > 0)) {
freak_word reg = freak_llvm_emit_expr(cur_id);
if ((!first)) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(res, freak_word_lit("i64 ")), reg);
}
return res;
}
freak_word freak_llvm_emit_expr(freak_word id) {
int64_t i = freak_word_to_int(id);
freak_word kind = freak_array_get(ast_expr_kinds, i);
freak_word val = freak_array_get(ast_expr_vals, i);
freak_word left = freak_array_get(ast_expr_lefts, i);
freak_word right = freak_array_get(ast_expr_rights, i);
if (freak_word_eq(kind, EXPR_INT)) {
return val;
}
if (freak_word_eq(kind, EXPR_BOOL)) {
if (((freak_word_eq(val, freak_word_lit("true")) || freak_word_eq(val, freak_word_lit("yes"))) || freak_word_eq(val, freak_word_lit("hai")))) {
return freak_word_lit("1");
}
return freak_word_lit("0");
}
if (freak_word_eq(kind, EXPR_FLOAT)) {
freak_word dbl_reg = freak_next_reg();
freak_word cast_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), dbl_reg), freak_word_lit(" = fadd double 0.0, ")), val));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cast_reg), freak_word_lit(" = bitcast double ")), dbl_reg), freak_word_lit(" to i64")));
return cast_reg;
}
if (freak_word_eq(kind, EXPR_STR)) {
freak_word str_id = freak_register_string_literal(val);
int64_t len = (freak_word_length(freak_word_replace(val, freak_word_lit("<<PIPE>>"), freak_word_lit("|"))) + 1);
freak_word get_ptr = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), get_ptr), freak_word_lit(" = getelementptr inbounds [")), freak_word_from_int(len)), freak_word_lit(" x i8], [")), freak_word_from_int(len)), freak_word_lit(" x i8]* ")), str_id), freak_word_lit(", i64 0, i64 0")));
freak_word cast_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cast_reg), freak_word_lit(" = ptrtoint i8* ")), get_ptr), freak_word_lit(" to i64")));
return cast_reg;
}
if (freak_word_eq(kind, EXPR_IDENT)) {
freak_word res_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = load i64, i64* ")), freak_llvm_var_ptr(val)));
return res_reg;
}
if (freak_word_eq(kind, EXPR_CALL)) {
return freak_llvm_emit_call(val, left);
}
if (freak_word_eq(kind, EXPR_BINOP)) {
return freak_llvm_emit_binop(val, left, right, id);
}
if (freak_word_eq(kind, EXPR_UNARYOP)) {
return freak_llvm_emit_unaryop(val, left);
}
if (freak_word_eq(kind, EXPR_METHOD)) {
return freak_llvm_emit_method(val, left, right);
}
if (freak_word_eq(kind, EXPR_FIELD)) {
return freak_llvm_emit_field(val, left);
}
if (freak_word_eq(kind, EXPR_INDEX)) {
freak_word obj_reg = freak_llvm_emit_expr(left);
freak_word idx_reg = freak_llvm_emit_expr(right);
freak_word res_reg = freak_next_reg();
freak_word ptr_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), ptr_reg), freak_word_lit(" = inttoptr i64 ")), obj_reg), freak_word_lit(" to i8*")));
freak_word gep_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), gep_reg), freak_word_lit(" = getelementptr inbounds i8, i8* ")), ptr_reg), freak_word_lit(", i64 ")), idx_reg));
freak_word char_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), char_reg), freak_word_lit(" = load i8, i8* ")), gep_reg));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i8 ")), char_reg), freak_word_lit(" to i64")));
return res_reg;
}
return freak_word_lit("0");
}
freak_word freak_llvm_emit_call(freak_word val, freak_word left) {
freak_word arg_str = freak_word_lit("");
if ((freak_word_length(left) > 0)) {
arg_str = freak_llvm_emit_args(left);
}
if (freak_word_starts_with(val, freak_word_lit("shape::ctor::"))) {
return freak_llvm_emit_shape_ctor(val, left);
}
freak_word func_name = freak_llvm_map_call_name(val);
if (freak_word_eq(func_name, freak_word_lit(""))) {
if (freak_emt_is_extern(val)) {
func_name = freak_word_concat(freak_word_lit("@"), freak_llvm_c_safe_ident(val));
}
else {
func_name = freak_word_concat(freak_word_lit("@freak_"), freak_llvm_c_safe_ident(val));
}
}
int64_t is_void = freak_llvm_is_void_call(val);
if ((!is_void)) {
freak_word call_ret = freak_llvm_get_task_ret_type(val);
if (freak_word_eq(call_ret, freak_word_lit("v"))) {
is_void = true;
}
}
if (is_void) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void "), func_name), freak_word_lit("(")), arg_str), freak_word_lit(")")));
return freak_word_lit("0");
}
freak_word res_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 ")), func_name), freak_word_lit("(")), arg_str), freak_word_lit(")")));
return res_reg;
}
freak_word freak_llvm_emit_shape_ctor(freak_word val, freak_word left) {
freak_word sname = freak_word_lit("");
int64_t vi = 13;
int64_t vlen = freak_word_length(val);
for (int64_t __rep = 0; __rep < vlen; __rep++) {
if ((vi < vlen)) {
sname = freak_word_concat(sname, freak_word_char_at(val, vi));
}
vi += 1;
}
int64_t fcount = freak_get_shape_field_count(sname);
freak_word alloc_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), alloc_reg), freak_word_lit(" = call i64 @freak_llvm_shape_alloc(i64 ")), freak_word_from_int(fcount)), freak_word_lit(")")));
if ((freak_word_length(left) > 0)) {
int64_t fi = 0;
int64_t ci = 0;
int64_t cslen = freak_word_length(left);
freak_word cur = freak_word_lit("");
for (int64_t __rep = 0; __rep < cslen; __rep++) {
freak_word cc = freak_word_char_at(left, ci);
if (freak_word_eq(cc, freak_word_lit(","))) {
if ((freak_word_length(cur) > 0)) {
freak_word fval_reg = freak_llvm_emit_expr(cur);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_shape_set(i64 "), alloc_reg), freak_word_lit(", i64 ")), freak_word_from_int(fi)), freak_word_lit(", i64 ")), fval_reg), freak_word_lit(")")));
fi += 1;
}
cur = freak_word_lit("");
}
else {
cur = freak_word_concat(cur, cc);
}
ci += 1;
}
if ((freak_word_length(cur) > 0)) {
freak_word fval_reg = freak_llvm_emit_expr(cur);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_shape_set(i64 "), alloc_reg), freak_word_lit(", i64 ")), freak_word_from_int(fi)), freak_word_lit(", i64 ")), fval_reg), freak_word_lit(")")));
}
}
return alloc_reg;
}
freak_word freak_llvm_emit_binop(freak_word val, freak_word left, freak_word right, freak_word id) {
freak_word l_reg = freak_llvm_emit_expr(left);
freak_word r_reg = freak_llvm_emit_expr(right);
freak_word res_reg = freak_next_reg();
int64_t is_num_op = (freak_llvm_is_num_expr(left) || freak_llvm_is_num_expr(right));
if (freak_word_eq(val, freak_word_lit("+"))) {
return freak_llvm_emit_add(l_reg, r_reg, res_reg, left, right, id, is_num_op);
}
if (freak_word_eq(val, freak_word_lit("-"))) {
return freak_llvm_emit_arith(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("sub"), freak_word_lit("fsub"));
}
if (freak_word_eq(val, freak_word_lit("*"))) {
return freak_llvm_emit_arith(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("mul"), freak_word_lit("fmul"));
}
if (freak_word_eq(val, freak_word_lit("/"))) {
return freak_llvm_emit_arith(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("sdiv"), freak_word_lit("fdiv"));
}
if (freak_word_eq(val, freak_word_lit("%"))) {
return freak_llvm_emit_arith(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("srem"), freak_word_lit("frem"));
}
if (freak_word_eq(val, freak_word_lit("=="))) {
return freak_llvm_emit_cmp(l_reg, r_reg, res_reg, left, is_num_op, freak_word_lit("eq"), freak_word_lit("oeq"));
}
if (freak_word_eq(val, freak_word_lit("!="))) {
return freak_llvm_emit_cmp(l_reg, r_reg, res_reg, left, is_num_op, freak_word_lit("ne"), freak_word_lit("une"));
}
if (freak_word_eq(val, freak_word_lit("<"))) {
return freak_llvm_emit_icmp(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("slt"), freak_word_lit("olt"));
}
if (freak_word_eq(val, freak_word_lit(">"))) {
return freak_llvm_emit_icmp(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("sgt"), freak_word_lit("ogt"));
}
if (freak_word_eq(val, freak_word_lit("<="))) {
return freak_llvm_emit_icmp(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("sle"), freak_word_lit("ole"));
}
if (freak_word_eq(val, freak_word_lit(">="))) {
return freak_llvm_emit_icmp(l_reg, r_reg, res_reg, is_num_op, freak_word_lit("sge"), freak_word_lit("oge"));
}
if (freak_word_eq(val, freak_word_lit("and"))) {
freak_word cmp_l = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_l), freak_word_lit(" = icmp ne i64 ")), l_reg), freak_word_lit(", 0")));
freak_word cmp_r = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_r), freak_word_lit(" = icmp ne i64 ")), r_reg), freak_word_lit(", 0")));
freak_word and_res = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), and_res), freak_word_lit(" = and i1 ")), cmp_l), freak_word_lit(", ")), cmp_r));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i1 ")), and_res), freak_word_lit(" to i64")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("or"))) {
freak_word cmp_l = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_l), freak_word_lit(" = icmp ne i64 ")), l_reg), freak_word_lit(", 0")));
freak_word cmp_r = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_r), freak_word_lit(" = icmp ne i64 ")), r_reg), freak_word_lit(", 0")));
freak_word or_res = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), or_res), freak_word_lit(" = or i1 ")), cmp_l), freak_word_lit(", ")), cmp_r));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i1 ")), or_res), freak_word_lit(" to i64")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("NAKAMA"))) {
freak_word t1 = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), t1), freak_word_lit(" = add i64 ")), l_reg), freak_word_lit(", ")), r_reg));
freak_word t2 = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), t2), freak_word_lit(" = mul i64 ")), l_reg), freak_word_lit(", ")), r_reg));
freak_word t3 = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), t3), freak_word_lit(" = sdiv i64 ")), t2), freak_word_lit(", 10")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = add i64 ")), t1), freak_word_lit(", ")), t3));
return res_reg;
}
return res_reg;
}
freak_word freak_llvm_emit_add(freak_word l_reg, freak_word r_reg, freak_word res_reg, freak_word left, freak_word right, freak_word id, bool is_num_op) {
freak_word vtype = freak_llvm_infer_expr_type(id);
if (freak_word_starts_with(vtype, freak_word_lit("w"))) {
freak_word lt = freak_llvm_infer_expr_type(left);
freak_word rt = freak_llvm_infer_expr_type(right);
freak_word lw = l_reg;
freak_word rw = r_reg;
if ((!freak_word_starts_with(lt, freak_word_lit("w")))) {
lw = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), lw), freak_word_lit(" = call i64 @freak_llvm_word_from_int(i64 ")), l_reg), freak_word_lit(")")));
}
if ((!freak_word_starts_with(rt, freak_word_lit("w")))) {
rw = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), rw), freak_word_lit(" = call i64 @freak_llvm_word_from_int(i64 ")), r_reg), freak_word_lit(")")));
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_concat(i64 ")), lw), freak_word_lit(", i64 ")), rw), freak_word_lit(")")));
return res_reg;
}
if (is_num_op) {
freak_word ld = freak_llvm_i64_to_double(l_reg);
freak_word rd = freak_llvm_i64_to_double(r_reg);
freak_word dres = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), dres), freak_word_lit(" = fadd double ")), ld), freak_word_lit(", ")), rd));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = bitcast double ")), dres), freak_word_lit(" to i64")));
return res_reg;
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = add i64 ")), l_reg), freak_word_lit(", ")), r_reg));
return res_reg;
}
freak_word freak_llvm_emit_arith(freak_word l_reg, freak_word r_reg, freak_word res_reg, bool is_num_op, freak_word int_op, freak_word float_op) {
if (is_num_op) {
freak_word ld = freak_llvm_i64_to_double(l_reg);
freak_word rd = freak_llvm_i64_to_double(r_reg);
freak_word dres = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), dres), freak_word_lit(" = ")), float_op), freak_word_lit(" double ")), ld), freak_word_lit(", ")), rd));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = bitcast double ")), dres), freak_word_lit(" to i64")));
return res_reg;
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = ")), int_op), freak_word_lit(" i64 ")), l_reg), freak_word_lit(", ")), r_reg));
return res_reg;
}
freak_word freak_llvm_emit_cmp(freak_word l_reg, freak_word r_reg, freak_word res_reg, freak_word left, bool is_num_op, freak_word int_cmp, freak_word float_cmp) {
freak_word ltype = freak_llvm_infer_expr_type(left);
if (freak_word_starts_with(ltype, freak_word_lit("w"))) {
if (freak_word_eq(int_cmp, freak_word_lit("eq"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_eq(i64 ")), l_reg), freak_word_lit(", i64 ")), r_reg), freak_word_lit(")")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_neq(i64 ")), l_reg), freak_word_lit(", i64 ")), r_reg), freak_word_lit(")")));
}
return res_reg;
}
return freak_llvm_emit_icmp(l_reg, r_reg, res_reg, is_num_op, int_cmp, float_cmp);
}
freak_word freak_llvm_emit_icmp(freak_word l_reg, freak_word r_reg, freak_word res_reg, bool is_num_op, freak_word int_cmp, freak_word float_cmp) {
if (is_num_op) {
freak_word ld = freak_llvm_i64_to_double(l_reg);
freak_word rd = freak_llvm_i64_to_double(r_reg);
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = fcmp ")), float_cmp), freak_word_lit(" double ")), ld), freak_word_lit(", ")), rd));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i1 ")), cmp_reg), freak_word_lit(" to i64")));
return res_reg;
}
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = icmp ")), int_cmp), freak_word_lit(" i64 ")), l_reg), freak_word_lit(", ")), r_reg));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i1 ")), cmp_reg), freak_word_lit(" to i64")));
return res_reg;
}
freak_word freak_llvm_emit_unaryop(freak_word val, freak_word left) {
freak_word op_reg = freak_llvm_emit_expr(left);
freak_word res_reg = freak_next_reg();
if (freak_word_eq(val, freak_word_lit("not"))) {
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = icmp eq i64 ")), op_reg), freak_word_lit(", 0")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = zext i1 ")), cmp_reg), freak_word_lit(" to i64")));
}
if (freak_word_eq(val, freak_word_lit("-"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = sub i64 0, ")), op_reg));
}
if (freak_word_eq(val, freak_word_lit("PLUS ULTRA"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = mul i64 ")), op_reg), freak_word_lit(", 2")));
}
if (freak_word_eq(val, freak_word_lit("FINAL FORM"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = mul i64 ")), op_reg), freak_word_lit(", ")), op_reg));
}
if (freak_word_eq(val, freak_word_lit("TSUNDERE"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = sub i64 0, ")), op_reg));
}
return res_reg;
}
freak_word freak_llvm_emit_method(freak_word val, freak_word left, freak_word right) {
freak_word obj_reg = freak_llvm_emit_expr(left);
freak_word res_reg = freak_next_reg();
if (freak_word_eq(val, freak_word_lit("length"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_length(i64 ")), obj_reg), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("char_at"))) {
freak_word a = freak_llvm_emit_expr(right);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_char_at(i64 ")), obj_reg), freak_word_lit(", i64 ")), a), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("contains"))) {
freak_word a = freak_llvm_emit_expr(right);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_contains(i64 ")), obj_reg), freak_word_lit(", i64 ")), a), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("starts_with"))) {
freak_word a = freak_llvm_emit_expr(right);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_starts_with(i64 ")), obj_reg), freak_word_lit(", i64 ")), a), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("ends_with"))) {
freak_word a = freak_llvm_emit_expr(right);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_ends_with(i64 ")), obj_reg), freak_word_lit(", i64 ")), a), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("to_upper"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_to_upper(i64 ")), obj_reg), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("to_lower"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_to_lower(i64 ")), obj_reg), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("trim"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_trim(i64 ")), obj_reg), freak_word_lit(")")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("replace"))) {
freak_word a = freak_llvm_emit_expr(right);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_replace(i64 ")), obj_reg), freak_word_lit(", i64 ")), a), freak_word_lit(", i64 0)")));
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("to_int"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_to_int(i64 ")), obj_reg), freak_word_lit(")")));
return res_reg;
}
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
freak_word sname = freak_word_concat(freak_word_lit(""), freak_array_get(shape_registry_names, si));
freak_word call_ret = freak_llvm_get_task_ret_type(freak_word_concat(freak_word_concat(sname, freak_word_lit("_")), val));
if ((freak_word_length(call_ret) > 0)) {
freak_word impl_fname = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("freak_"), sname), freak_word_lit("_")), val);
if (freak_word_eq(call_ret, freak_word_lit("v"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @"), impl_fname), freak_word_lit("(i64 ")), obj_reg), freak_word_lit(")")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = add i64 0, 0")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @")), impl_fname), freak_word_lit("(i64 ")), obj_reg), freak_word_lit(")")));
}
return res_reg;
}
si += 1;
}
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    ; unsupported method "), val));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = add i64 0, 0")));
return res_reg;
}
freak_word freak_llvm_emit_field(freak_word val, freak_word left) {
freak_word obj_reg = freak_llvm_emit_expr(left);
int64_t fidx = (0 - 1);
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
int64_t tmpidx = freak_get_shape_field_index(freak_array_get(shape_registry_names, si), val);
if ((tmpidx >= 0)) {
fidx = tmpidx;
}
si += 1;
}
if ((fidx < 0)) {
fidx = 0;
}
freak_word res_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_shape_get(i64 ")), obj_reg), freak_word_lit(", i64 ")), freak_word_from_int(fidx)), freak_word_lit(")")));
return res_reg;
}
void freak_llvm_emit_block(freak_word block) {
int64_t i = 0;
int64_t slen = freak_word_length(block);
freak_word cur_id = freak_word_lit("");
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(block, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((freak_word_length(cur_id) > 0)) {
freak_llvm_emit_stmt(cur_id);
}
cur_id = freak_word_lit("");
}
else {
cur_id = freak_word_concat(cur_id, c);
}
i += 1;
}
if ((freak_word_length(cur_id) > 0)) {
freak_llvm_emit_stmt(cur_id);
}
}
void freak_llvm_emit_stmt(freak_word eid) {
if ((freak_word_length(eid) == 0)) {
return ;
}
int64_t i = freak_word_to_int(eid);
freak_word kind = freak_array_get(ast_stmt_kinds, i);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
if (freak_word_eq(kind, STMT_PILOT)) {
freak_llvm_emit_stmt_pilot(eid);
return ;
}
if (freak_word_eq(kind, STMT_SAY)) {
freak_word say_kind = freak_array_get(ast_expr_kinds, freak_word_to_int(expr_id_w));
freak_word say_val = freak_array_get(ast_expr_vals, freak_word_to_int(expr_id_w));
if ((freak_word_eq(say_kind, EXPR_STR) && freak_llvm_str_has_interp(say_val))) {
freak_llvm_emit_say_interp(say_val);
}
else {
freak_word reg = freak_llvm_emit_expr(expr_id_w);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_say(i64 "), reg), freak_word_lit(")")));
}
return ;
}
if (freak_word_eq(kind, STMT_EXPR)) {
freak_llvm_emit_expr(expr_id_w);
return ;
}
if (freak_word_eq(kind, STMT_GIVE_BACK)) {
if (llvm_cur_func_is_void) {
freak_llvm_emit_line(freak_word_lit("    ret void"));
}
else {
if (((freak_word_length(expr_id_w) > 0) && (!freak_word_starts_with(expr_id_w, freak_word_lit("-"))))) {
freak_word reg = freak_llvm_emit_expr(expr_id_w);
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    ret i64 "), reg));
}
else {
freak_llvm_emit_line(freak_word_lit("    ret i64 0"));
}
}
return ;
}
if (freak_word_eq(kind, STMT_IF)) {
freak_llvm_emit_stmt_if(eid);
return ;
}
if (freak_word_eq(kind, STMT_REPEAT)) {
freak_llvm_emit_stmt_repeat(eid);
return ;
}
if (freak_word_eq(kind, STMT_TRAINING_ARC)) {
freak_llvm_emit_stmt_training_arc(eid);
return ;
}
if (freak_word_eq(kind, STMT_WHEN)) {
freak_llvm_emit_stmt_when(eid);
return ;
}
if (freak_word_eq(kind, STMT_BLOCK)) {
freak_llvm_emit_block(freak_array_get(ast_stmt_bodies, i));
return ;
}
if (freak_word_eq(kind, STMT_ASSIGN)) {
freak_llvm_emit_stmt_assign(eid);
return ;
}
if (freak_word_eq(kind, STMT_BREAK)) {
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), llvm_loop_end_label));
freak_word dead = freak_word_concat(freak_word_lit("break.dead."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_llvm_emit_line(freak_word_concat(dead, freak_word_lit(":")));
return ;
}
if (freak_word_eq(kind, STMT_CONTINUE)) {
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), llvm_loop_cond_label));
freak_word dead = freak_word_concat(freak_word_lit("cont.dead."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_llvm_emit_line(freak_word_concat(dead, freak_word_lit(":")));
return ;
}
if (freak_word_eq(kind, STMT_SHAPE)) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    ; shape "), name_w), freak_word_lit(" defined")));
return ;
}
if (freak_word_eq(kind, STMT_EVENTUALLY)) {
freak_llvm_emit_line(freak_word_lit("    ; eventually block"));
freak_word ev_body = freak_array_get(ast_stmt_bodies, i);
if ((freak_word_length(ev_body) > 0)) {
freak_llvm_emit_block(ev_body);
}
return ;
}
}
void freak_llvm_emit_stmt_pilot(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word type_ann = freak_array_get(ast_stmt_extras, i);
freak_word vtype = freak_word_lit("");
if (freak_word_eq(type_ann, freak_word_lit("word"))) {
vtype = freak_word_lit("w");
}
if (freak_word_eq(type_ann, freak_word_lit("num"))) {
vtype = freak_word_lit("n");
}
if (freak_word_eq(type_ann, freak_word_lit("bool"))) {
vtype = freak_word_lit("b");
}
if (freak_word_eq(type_ann, freak_word_lit("int"))) {
vtype = freak_word_lit("i");
}
if (freak_word_eq(vtype, freak_word_lit(""))) {
vtype = freak_llvm_infer_expr_type(expr_id_w);
}
freak_llvm_set_var_type(name_w, vtype);
freak_word reg = freak_llvm_emit_expr(expr_id_w);
if (freak_llvm_is_global(name_w)) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), reg), freak_word_lit(", i64* @g_")), name_w));
}
else {
freak_word uniq = freak_word_concat(freak_word_concat(name_w, freak_word_lit("_v")), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_llvm_reg_var(name_w, uniq);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    %"), uniq), freak_word_lit(" = alloca i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), reg), freak_word_lit(", i64* %")), uniq));
}
}
void freak_llvm_emit_stmt_if(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word cond_reg = freak_llvm_emit_expr(expr_id_w);
freak_word l_then = freak_word_concat(freak_word_lit("if.then."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_else = freak_word_concat(freak_word_lit("if.else."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_end = freak_word_concat(freak_word_lit("if.end."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = icmp ne i64 ")), cond_reg), freak_word_lit(", 0")));
freak_word else_body_w = freak_array_get(ast_stmt_else_bodies, i);
if ((freak_word_length(else_body_w) > 0)) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), cmp_reg), freak_word_lit(", label %")), l_then), freak_word_lit(", label %")), l_else));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), cmp_reg), freak_word_lit(", label %")), l_then), freak_word_lit(", label %")), l_end));
}
freak_llvm_emit_line(freak_word_concat(l_then, freak_word_lit(":")));
freak_llvm_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_end));
if ((freak_word_length(else_body_w) > 0)) {
freak_llvm_emit_line(freak_word_concat(l_else, freak_word_lit(":")));
freak_llvm_emit_block(else_body_w);
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_end));
}
freak_llvm_emit_line(freak_word_concat(l_end, freak_word_lit(":")));
}
void freak_llvm_emit_stmt_repeat(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word l_cond = freak_word_concat(freak_word_lit("loop.cond."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_body = freak_word_concat(freak_word_lit("loop.body."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_end = freak_word_concat(freak_word_lit("loop.end."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word save_end = llvm_loop_end_label;
freak_word save_cond = llvm_loop_cond_label;
llvm_loop_end_label = l_end;
if (freak_word_eq(name_w, freak_word_lit("until"))) {
llvm_loop_cond_label = l_cond;
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
freak_llvm_emit_line(freak_word_concat(l_cond, freak_word_lit(":")));
freak_word cond_reg = freak_llvm_emit_expr(expr_id_w);
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = icmp eq i64 ")), cond_reg), freak_word_lit(", 0")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), cmp_reg), freak_word_lit(", label %")), l_body), freak_word_lit(", label %")), l_end));
freak_llvm_emit_line(freak_word_concat(l_body, freak_word_lit(":")));
freak_llvm_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
}
else {
freak_word l_inc = freak_word_concat(freak_word_lit("loop.inc."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word rep_var = freak_word_concat(freak_word_lit("rep."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
llvm_loop_cond_label = l_inc;
freak_word count_reg = freak_llvm_emit_expr(expr_id_w);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    %"), rep_var), freak_word_lit(" = alloca i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    store i64 0, i64* %"), rep_var));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
freak_llvm_emit_line(freak_word_concat(l_cond, freak_word_lit(":")));
freak_word curr_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), curr_val), freak_word_lit(" = load i64, i64* %")), rep_var));
freak_word cmp_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_reg), freak_word_lit(" = icmp slt i64 ")), curr_val), freak_word_lit(", ")), count_reg));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), cmp_reg), freak_word_lit(", label %")), l_body), freak_word_lit(", label %")), l_end));
freak_llvm_emit_line(freak_word_concat(l_body, freak_word_lit(":")));
freak_llvm_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_inc));
freak_llvm_emit_line(freak_word_concat(l_inc, freak_word_lit(":")));
freak_word next_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), next_val), freak_word_lit(" = load i64, i64* %")), rep_var));
freak_word inc_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), inc_val), freak_word_lit(" = add i64 ")), next_val), freak_word_lit(", 1")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), inc_val), freak_word_lit(", i64* %")), rep_var));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
}
freak_llvm_emit_line(freak_word_concat(l_end, freak_word_lit(":")));
llvm_loop_end_label = save_end;
llvm_loop_cond_label = save_cond;
}
void freak_llvm_emit_stmt_training_arc(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word l_cond = freak_word_concat(freak_word_lit("loop.cond."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_body = freak_word_concat(freak_word_lit("loop.body."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_end = freak_word_concat(freak_word_lit("loop.end."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word l_inc = freak_word_concat(freak_word_lit("loop.inc."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word rep_var = freak_word_concat(freak_word_lit("rep."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word max_reg = freak_llvm_emit_expr(freak_array_get(ast_stmt_extras, i));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    %"), rep_var), freak_word_lit(" = alloca i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    store i64 0, i64* %"), rep_var));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
freak_llvm_emit_line(freak_word_concat(l_cond, freak_word_lit(":")));
freak_word curr_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), curr_val), freak_word_lit(" = load i64, i64* %")), rep_var));
freak_word cmp_max = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_max), freak_word_lit(" = icmp slt i64 ")), curr_val), freak_word_lit(", ")), max_reg));
freak_word cond_reg = freak_llvm_emit_expr(expr_id_w);
freak_word cmp_cond = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_cond), freak_word_lit(" = icmp eq i64 ")), cond_reg), freak_word_lit(", 0")));
freak_word loop_continue = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), loop_continue), freak_word_lit(" = and i1 ")), cmp_max), freak_word_lit(", ")), cmp_cond));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), loop_continue), freak_word_lit(", label %")), l_body), freak_word_lit(", label %")), l_end));
freak_word save_end = llvm_loop_end_label;
freak_word save_cond = llvm_loop_cond_label;
llvm_loop_end_label = l_end;
llvm_loop_cond_label = l_inc;
freak_llvm_emit_line(freak_word_concat(l_body, freak_word_lit(":")));
freak_llvm_emit_block(freak_array_get(ast_stmt_bodies, i));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_inc));
freak_llvm_emit_line(freak_word_concat(l_inc, freak_word_lit(":")));
freak_word next_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), next_val), freak_word_lit(" = load i64, i64* %")), rep_var));
freak_word inc_val = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), inc_val), freak_word_lit(" = add i64 ")), next_val), freak_word_lit(", 1")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), inc_val), freak_word_lit(", i64* %")), rep_var));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_cond));
freak_llvm_emit_line(freak_word_concat(l_end, freak_word_lit(":")));
llvm_loop_end_label = save_end;
llvm_loop_cond_label = save_cond;
}
void freak_llvm_emit_stmt_assign(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word rhs_w = freak_array_get(ast_stmt_bodies, i);
freak_word var_name_expr = freak_array_get(ast_expr_vals, freak_word_to_int(expr_id_w));
freak_word reg = freak_llvm_emit_expr(rhs_w);
freak_word var_ptr = freak_llvm_var_ptr(var_name_expr);
if (freak_word_eq(name_w, freak_word_lit("="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), reg), freak_word_lit(", i64* ")), var_ptr));
return ;
}
freak_word load_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), load_reg), freak_word_lit(" = load i64, i64* ")), var_ptr));
freak_word op_reg = freak_next_reg();
if (freak_word_eq(name_w, freak_word_lit("+="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = add i64 ")), load_reg), freak_word_lit(", ")), reg));
}
if (freak_word_eq(name_w, freak_word_lit("-="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = sub i64 ")), load_reg), freak_word_lit(", ")), reg));
}
if (freak_word_eq(name_w, freak_word_lit("*="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = mul i64 ")), load_reg), freak_word_lit(", ")), reg));
}
if (freak_word_eq(name_w, freak_word_lit("/="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = sdiv i64 ")), load_reg), freak_word_lit(", ")), reg));
}
if (freak_word_eq(name_w, freak_word_lit("%="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = srem i64 ")), load_reg), freak_word_lit(", ")), reg));
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 "), op_reg), freak_word_lit(", i64* ")), var_ptr));
}
void freak_llvm_emit_stmt_when(freak_word eid) {
int64_t i = freak_word_to_int(eid);
freak_word expr_id_w = freak_array_get(ast_stmt_exprs, i);
freak_word target_reg = freak_llvm_emit_expr(expr_id_w);
freak_word cases_str = freak_array_get(ast_stmt_bodies, i);
freak_word l_end = freak_word_concat(freak_word_lit("when.end."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word current_block = freak_word_concat(freak_word_lit("when.case."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), current_block));
int64_t cases_len = freak_word_length(cases_str);
int64_t ci = 0;
freak_word cur_case = freak_word_lit("");
bool case_fin = false;
while (!(case_fin)) {
freak_word cc = freak_word_char_at(cases_str, ci);
if ((freak_word_eq(cc, freak_word_lit(",")) || (ci >= cases_len))) {
if ((freak_word_length(cur_case) > 0)) {
freak_llvm_emit_line(freak_word_concat(current_block, freak_word_lit(":")));
freak_word c_expr = freak_word_lit("");
freak_word c_stmt = freak_word_lit("");
bool in_expr = true;
int64_t c_len = freak_word_length(cur_case);
int64_t cj = 0;
for (int64_t __rep = 0; __rep < c_len; __rep++) {
freak_word p = freak_word_char_at(cur_case, cj);
if (freak_word_eq(p, freak_word_lit(":"))) {
in_expr = false;
}
else {
if (in_expr) {
c_expr = freak_word_concat(c_expr, p);
}
else {
c_stmt = freak_word_concat(c_stmt, p);
}
}
cj += 1;
}
freak_word next_block = freak_word_concat(freak_word_lit("when.case."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
freak_word do_block = freak_word_concat(freak_word_lit("when.do."), freak_word_from_int(temp_reg_counter));
temp_reg_counter += 1;
if (freak_word_eq(c_expr, freak_word_lit("-1"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), do_block));
}
else {
freak_word cmp_val = freak_llvm_emit_expr(c_expr);
freak_word cmp_res = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cmp_res), freak_word_lit(" = icmp eq i64 ")), target_reg), freak_word_lit(", ")), cmp_val));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    br i1 "), cmp_res), freak_word_lit(", label %")), do_block), freak_word_lit(", label %")), next_block));
}
freak_llvm_emit_line(freak_word_concat(do_block, freak_word_lit(":")));
freak_llvm_emit_stmt(c_stmt);
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_end));
current_block = next_block;
}
cur_case = freak_word_lit("");
if ((ci >= cases_len)) {
case_fin = true;
}
}
else {
cur_case = freak_word_concat(cur_case, cc);
}
ci += 1;
}
freak_llvm_emit_line(freak_word_concat(current_block, freak_word_lit(":")));
freak_llvm_emit_line(freak_word_concat(freak_word_lit("    br label %"), l_end));
freak_llvm_emit_line(freak_word_concat(l_end, freak_word_lit(":")));
}
bool freak_llvm_str_has_interp(freak_word val) {
int64_t slen = freak_word_length(val);
int64_t i = 0;
for (int64_t __rep = 0; __rep < slen; __rep++) {
if (freak_word_eq(freak_word_char_at(val, i), freak_word_lit("{"))) {
return true;
}
i += 1;
}
return false;
}
void freak_llvm_emit_say_interp(freak_word val) {
int64_t slen = freak_word_length(val);
int64_t i = 0;
freak_word buf = freak_word_lit("");
freak_word vname = freak_word_lit("");
bool in_var = false;
while (!((i >= slen))) {
freak_word c = freak_word_char_at(val, i);
if (in_var) {
if (freak_word_eq(c, freak_word_lit("}"))) {
freak_word var_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), var_reg), freak_word_lit(" = load i64, i64* ")), freak_llvm_var_ptr(vname)));
freak_word var_type = freak_llvm_get_var_type(vname);
if (freak_word_starts_with(var_type, freak_word_lit("w"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_print_str(i64 "), var_reg), freak_word_lit(")")));
}
else {
if (freak_word_starts_with(var_type, freak_word_lit("n"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_print_num(i64 "), var_reg), freak_word_lit(")")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_print_int(i64 "), var_reg), freak_word_lit(")")));
}
}
vname = freak_word_lit("");
in_var = false;
}
else {
vname = freak_word_concat(vname, c);
}
}
else {
if (freak_word_eq(c, freak_word_lit("{"))) {
if ((freak_word_length(buf) > 0)) {
freak_word lit_id = freak_register_string_literal(buf);
int64_t lit_len = (freak_word_length(buf) + 1);
freak_word gep = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), gep), freak_word_lit(" = getelementptr inbounds [")), freak_word_from_int(lit_len)), freak_word_lit(" x i8], [")), freak_word_from_int(lit_len)), freak_word_lit(" x i8]* ")), lit_id), freak_word_lit(", i64 0, i64 0")));
freak_word ptr = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), ptr), freak_word_lit(" = ptrtoint i8* ")), gep), freak_word_lit(" to i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_print_str(i64 "), ptr), freak_word_lit(")")));
buf = freak_word_lit("");
}
in_var = true;
}
else {
buf = freak_word_concat(buf, c);
}
}
i += 1;
}
if ((freak_word_length(buf) > 0)) {
freak_word lit_id = freak_register_string_literal(buf);
int64_t lit_len = (freak_word_length(buf) + 1);
freak_word gep = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), gep), freak_word_lit(" = getelementptr inbounds [")), freak_word_from_int(lit_len)), freak_word_lit(" x i8], [")), freak_word_from_int(lit_len)), freak_word_lit(" x i8]* ")), lit_id), freak_word_lit(", i64 0, i64 0")));
freak_word ptr = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), ptr), freak_word_lit(" = ptrtoint i8* ")), gep), freak_word_lit(" to i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_print_str(i64 "), ptr), freak_word_lit(")")));
}
freak_llvm_emit_line(freak_word_lit("    call void @freak_llvm_print_newline()"));
}
freak_word freak_llvm_translate_params(freak_word p) {
freak_word res = freak_word_lit("");
freak_word cur_name = freak_word_lit("");
bool in_type = false;
int64_t i = 0;
int64_t slen = freak_word_length(p);
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(p, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
in_type = true;
}
else {
if (freak_word_eq(c, freak_word_lit(","))) {
if ((freak_word_length(res) > 0)) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(res, freak_word_lit("i64 %arg_")), cur_name);
cur_name = freak_word_lit("");
in_type = false;
}
else {
if ((!in_type)) {
cur_name = freak_word_concat(cur_name, c);
}
}
}
i += 1;
}
if ((freak_word_length(cur_name) > 0)) {
if ((freak_word_length(res) > 0)) {
res = freak_word_concat(res, freak_word_lit(", "));
}
res = freak_word_concat(freak_word_concat(res, freak_word_lit("i64 %arg_")), cur_name);
}
return res;
}
void freak_llvm_allocate_params(freak_word p) {
freak_word cur_name = freak_word_lit("");
freak_word cur_type = freak_word_lit("");
bool in_type = false;
int64_t i = 0;
int64_t slen = freak_word_length(p);
for (int64_t __rep = 0; __rep < slen; __rep++) {
freak_word c = freak_word_char_at(p, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
in_type = true;
}
else {
if (freak_word_eq(c, freak_word_lit(","))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    %"), cur_name), freak_word_lit(" = alloca i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 %arg_"), cur_name), freak_word_lit(", i64* %")), cur_name));
freak_word pt = freak_word_lit("i");
if (freak_word_eq(cur_type, freak_word_lit("word"))) {
pt = freak_word_lit("w");
}
if (freak_word_eq(cur_type, freak_word_lit("num"))) {
pt = freak_word_lit("n");
}
if (freak_word_eq(cur_type, freak_word_lit("bool"))) {
pt = freak_word_lit("b");
}
freak_llvm_set_var_type(cur_name, pt);
cur_name = freak_word_lit("");
cur_type = freak_word_lit("");
in_type = false;
}
else {
if (in_type) {
cur_type = freak_word_concat(cur_type, c);
}
else {
cur_name = freak_word_concat(cur_name, c);
}
}
}
i += 1;
}
if ((freak_word_length(cur_name) > 0)) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    %"), cur_name), freak_word_lit(" = alloca i64")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    store i64 %arg_"), cur_name), freak_word_lit(", i64* %")), cur_name));
freak_word pt = freak_word_lit("i");
if (freak_word_eq(cur_type, freak_word_lit("word"))) {
pt = freak_word_lit("w");
}
if (freak_word_eq(cur_type, freak_word_lit("num"))) {
pt = freak_word_lit("n");
}
if (freak_word_eq(cur_type, freak_word_lit("bool"))) {
pt = freak_word_lit("b");
}
freak_llvm_set_var_type(cur_name, pt);
}
}
void freak_llvm_emit_task(freak_word eid) {
llvm_var_names = freak_word_lit("");
llvm_var_types = freak_word_lit("");
llvm_var_reg_map = freak_word_lit("");
int64_t i = freak_word_to_int(eid);
freak_word name_w = freak_array_get(ast_stmt_names, i);
freak_word body_id_w = freak_array_get(ast_stmt_bodies, i);
freak_word params_w = freak_array_get(ast_task_params, i);
freak_word returns_w = freak_array_get(ast_task_returns, i);
freak_word ret_type = freak_word_lit("i64");
bool is_void = false;
if ((freak_word_eq(returns_w, freak_word_lit("void")) || freak_word_eq(returns_w, freak_word_lit("")))) {
ret_type = freak_word_lit("void");
is_void = true;
}
llvm_cur_func_is_void = is_void;
freak_word p_str = freak_word_lit("");
if ((freak_word_length(params_w) > 0)) {
p_str = freak_llvm_translate_params(params_w);
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("define "), ret_type), freak_word_lit(" @freak_")), name_w), freak_word_lit("(")), p_str), freak_word_lit(") {")));
freak_llvm_emit_line(freak_word_lit("entry:"));
if ((freak_word_length(params_w) > 0)) {
freak_llvm_allocate_params(params_w);
}
freak_llvm_emit_block(body_id_w);
if (is_void) {
freak_llvm_emit_line(freak_word_lit("    ret void"));
}
else {
freak_llvm_emit_line(freak_word_lit("    ret i64 0"));
}
freak_llvm_emit_line(freak_word_lit("}"));
freak_llvm_emit_line(freak_word_lit(""));
}
void freak_llvm_emit_runtime_decls(void) {
freak_llvm_emit_line(freak_word_lit("declare i32 @puts(i8*)"));
freak_llvm_emit_line(freak_word_lit("declare i32 @printf(i8*, ...)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @strlen(i8*)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_from_int(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_from_bool(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_concat(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_eq(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_neq(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_length(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_char_at(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_contains(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_starts_with(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_ends_with(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_to_upper(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_to_lower(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_trim(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_replace(i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_to_int(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_say(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_print_str(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_print_int(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_print_newline()"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ask(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_process_args_count()"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_process_arg(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_process_exit(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_process_exec(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_process_exec_capture(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_panic(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_shape_alloc(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_shape_get(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_shape_set(i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_setup_args(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_from_num(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_print_num(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_int_to_num(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_num_to_int(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_create_window(i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_destroy_window(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_poll_events(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_begin_frame(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_end_frame(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_kind(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_key(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_pressed(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_character(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_mouse_x(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_mouse_y(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_button(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_clear(i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_fill_rect(i64, i64, i64, i64, i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_stroke_rect(i64, i64, i64, i64, i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_fill_circle(i64, i64, i64, i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_ui_draw_line(i64, i64, i64, i64, i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_draw_text(i64, i64, i64, i64, i64, i64, i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_measure_text(i64, i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_sqrt(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_pow(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_sin(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_cos(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_tan(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_floor(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_math_ceil(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_parse_num(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_format_num(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_word_compare(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_array_new()"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_array_push(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_array_get(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_array_len(i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_array_set(i64, i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_tcp_connect(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_tcp_send(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_tcp_recv(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_tcp_recv_all(i64, i64)"));
freak_llvm_emit_line(freak_word_lit("declare void @freak_llvm_tcp_close(i64)"));
llvm_declared_funcs = freak_word_lit("|puts|printf|strlen|freak_llvm_word_from_int|freak_llvm_word_from_bool|freak_llvm_word_concat|freak_llvm_word_eq|freak_llvm_word_neq|freak_llvm_word_length|freak_llvm_word_char_at|freak_llvm_word_contains|freak_llvm_word_starts_with|freak_llvm_word_ends_with|freak_llvm_word_to_upper|freak_llvm_word_to_lower|freak_llvm_word_trim|freak_llvm_word_replace|freak_llvm_word_to_int|freak_llvm_say|freak_llvm_print_str|freak_llvm_print_int|freak_llvm_print_newline|freak_llvm_ask|freak_llvm_process_args_count|freak_llvm_process_arg|freak_llvm_process_exit|freak_llvm_process_exec|freak_llvm_process_exec_capture|freak_llvm_panic|freak_llvm_shape_alloc|freak_llvm_shape_get|freak_llvm_shape_set|freak_llvm_setup_args|freak_llvm_word_from_num|freak_llvm_print_num|freak_llvm_int_to_num|freak_llvm_num_to_int|freak_llvm_ui_create_window|freak_llvm_ui_destroy_window|freak_llvm_ui_poll_events|freak_llvm_ui_begin_frame|freak_llvm_ui_end_frame|freak_llvm_ui_event_kind|freak_llvm_ui_event_key|freak_llvm_ui_event_pressed|freak_llvm_ui_event_character|freak_llvm_ui_event_mouse_x|freak_llvm_ui_event_mouse_y|freak_llvm_ui_event_button|freak_llvm_ui_clear|freak_llvm_ui_fill_rect|freak_llvm_ui_stroke_rect|freak_llvm_ui_fill_circle|freak_llvm_ui_draw_line|freak_llvm_ui_draw_text|freak_llvm_ui_measure_text|freak_llvm_math_sqrt|freak_llvm_math_pow|freak_llvm_math_sin|freak_llvm_math_cos|freak_llvm_math_tan|freak_llvm_math_floor|freak_llvm_math_ceil|freak_llvm_parse_num|freak_llvm_format_num|freak_llvm_array_new|freak_llvm_array_push|freak_llvm_array_get|freak_llvm_array_len|freak_llvm_array_set|freak_word_compare|freak_llvm_tcp_connect|freak_llvm_tcp_send|freak_llvm_tcp_recv|freak_llvm_tcp_recv_all|freak_llvm_tcp_close|freak_llvm_time_now_ms|");
}
void freak_emit_llvm_program(void) {
temp_reg_counter = 0;
string_literals = freak_word_lit("");
string_literals_count = 0;
freak_fs_write(out_file, freak_word_lit(""));
freak_llvm_emit_line(freak_word_lit("; FREAK LLVM IR Generator (v3)"));
freak_llvm_emit_line(freak_word_lit(""));
freak_llvm_emit_runtime_decls();
freak_llvm_emit_line(freak_word_lit(""));
int64_t top_count = freak_array_len(ast_top_stmts);
int64_t prescan_i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word pid = freak_array_get(ast_top_stmts, prescan_i);
freak_word pk = freak_array_get(ast_stmt_kinds, freak_word_to_int(pid));
if (freak_word_eq(pk, STMT_TASK)) {
freak_word pn = freak_array_get(ast_stmt_names, freak_word_to_int(pid));
freak_word pr = freak_array_get(ast_task_returns, freak_word_to_int(pid));
freak_llvm_register_task(pn, pr);
}
if (freak_word_eq(pk, STMT_EXTERN)) {
freak_word en = freak_array_get(ast_stmt_names, freak_word_to_int(pid));
freak_word er = freak_array_get(ast_task_returns, freak_word_to_int(pid));
freak_llvm_register_task(en, er);
freak_emt_register_extern(en, er);
}
prescan_i += 1;
}
llvm_global_names = freak_word_lit("");
int64_t glob_i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word gid = freak_array_get(ast_top_stmts, glob_i);
freak_word gk = freak_array_get(ast_stmt_kinds, freak_word_to_int(gid));
if (freak_word_eq(gk, STMT_PILOT)) {
freak_word gn = freak_array_get(ast_stmt_names, freak_word_to_int(gid));
llvm_global_names = freak_word_concat(freak_word_concat(freak_word_concat(llvm_global_names, freak_word_lit("|")), gn), freak_word_lit("|"));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("@g_"), gn), freak_word_lit(" = global i64 0")));
}
glob_i += 1;
}
freak_llvm_emit_line(freak_word_lit(""));
int64_t ext_i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word eid = freak_array_get(ast_top_stmts, ext_i);
freak_word ek = freak_array_get(ast_stmt_kinds, freak_word_to_int(eid));
if (freak_word_eq(ek, STMT_EXTERN)) {
freak_word enm = freak_array_get(ast_stmt_names, freak_word_to_int(eid));
freak_word ert = freak_array_get(ast_task_returns, freak_word_to_int(eid));
freak_word epm = freak_array_get(ast_task_params, freak_word_to_int(eid));
freak_word llvm_ret = freak_word_lit("i64");
if (freak_word_eq(ert, freak_word_lit("void"))) {
llvm_ret = freak_word_lit("void");
}
freak_word llvm_params = freak_word_lit("");
if ((!freak_word_eq(epm, freak_word_lit("")))) {
int64_t plen = freak_word_length(epm);
int64_t pi = 0;
int64_t pcount = 1;
for (int64_t __rep = 0; __rep < plen; __rep++) {
if (freak_word_eq(freak_word_char_at(epm, pi), freak_word_lit(","))) {
pcount += 1;
}
pi += 1;
}
int64_t pj = 0;
for (int64_t __rep = 0; __rep < pcount; __rep++) {
if ((pj > 0)) {
llvm_params = freak_word_concat(llvm_params, freak_word_lit(", "));
}
llvm_params = freak_word_concat(llvm_params, freak_word_lit("i64"));
pj += 1;
}
}
if ((!freak_llvm_is_runtime_func(enm))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("declare "), llvm_ret), freak_word_lit(" @")), enm), freak_word_lit("(")), llvm_params), freak_word_lit(")")));
}
}
ext_i += 1;
}
freak_llvm_emit_line(freak_word_lit(""));
int64_t i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_TASK)) {
freak_llvm_emit_task(cur_id);
}
i += 1;
}
bool has_main_task = false;
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_TASK)) {
freak_word tname = freak_array_get(ast_stmt_names, freak_word_to_int(cur_id));
if (freak_word_eq(tname, freak_word_lit("main"))) {
has_main_task = true;
}
}
i += 1;
}
if (has_main_task) {
llvm_var_names = freak_word_lit("");
llvm_var_types = freak_word_lit("");
llvm_var_reg_map = freak_word_lit("");
llvm_cur_func_is_void = true;
freak_llvm_emit_line(freak_word_lit("define void @freak_init_globals() {"));
freak_llvm_emit_line(freak_word_lit("entry:"));
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (freak_word_eq(kind, STMT_PILOT)) {
freak_llvm_emit_stmt(cur_id);
}
i += 1;
}
freak_llvm_emit_line(freak_word_lit("    ret void"));
freak_llvm_emit_line(freak_word_lit("}"));
freak_llvm_emit_line(freak_word_lit(""));
}
if ((!has_main_task)) {
llvm_var_names = freak_word_lit("");
llvm_var_types = freak_word_lit("");
llvm_var_reg_map = freak_word_lit("");
llvm_cur_func_is_void = true;
freak_llvm_emit_line(freak_word_lit("define void @freak_main() {"));
freak_llvm_emit_line(freak_word_lit("entry:"));
i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
freak_word cur_id = freak_array_get(ast_top_stmts, i);
freak_word kind = freak_array_get(ast_stmt_kinds, freak_word_to_int(cur_id));
if (((!freak_word_eq(kind, STMT_TASK)) && (!freak_word_eq(kind, STMT_EXTERN)))) {
freak_llvm_emit_stmt(cur_id);
}
i += 1;
}
freak_llvm_emit_line(freak_word_lit("    ret void"));
freak_llvm_emit_line(freak_word_lit("}"));
}
freak_llvm_emit_line(freak_word_lit(""));
freak_llvm_emit_line(freak_word_lit("define i32 @main(i32 %argc, i8** %argv) {"));
freak_llvm_emit_line(freak_word_lit("entry:"));
freak_llvm_emit_line(freak_word_lit("    %argc_ext = sext i32 %argc to i64"));
freak_llvm_emit_line(freak_word_lit("    %argv_ptr = ptrtoint i8** %argv to i64"));
freak_llvm_emit_line(freak_word_lit("    call void @freak_llvm_setup_args(i64 %argc_ext, i64 %argv_ptr)"));
if (has_main_task) {
freak_llvm_emit_line(freak_word_lit("    call void @freak_init_globals()"));
freak_llvm_emit_line(freak_word_lit("    call void @freak_main()"));
}
if ((!has_main_task)) {
freak_llvm_emit_line(freak_word_lit("    call void @freak_main()"));
}
freak_llvm_emit_line(freak_word_lit("    ret i32 0"));
freak_llvm_emit_line(freak_word_lit("}"));
freak_llvm_emit_line(freak_word_lit(""));
freak_llvm_emit_line(freak_word_lit("; String Literals"));
freak_llvm_emit_line(string_literals);
}
void freak_freakc_v3_main(void) {
int64_t args_cnt = freak_process_args_count();
if ((args_cnt >= 2)) {
freak_word first_arg = freak_process_arg(1);
if ((freak_word_eq(first_arg, freak_word_lit("--version")) || freak_word_eq(first_arg, freak_word_lit("-V")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("freakc "), FREAKC_VERSION), freak_word_lit(" (")), FREAKC_CODENAME), freak_word_lit(")")));
return ;
}
if ((freak_word_eq(first_arg, freak_word_lit("--help")) || freak_word_eq(first_arg, freak_word_lit("-h")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("FREAK Compiler "), FREAKC_VERSION), freak_word_lit(" (")), FREAKC_CODENAME), freak_word_lit(")")));
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
return ;
}
}
if ((args_cnt < 2)) {
freak_say(freak_word_lit("Usage: freakc <file.fk> [--c] [--llvm] [--opt=N] [--target=TRIPLE]"));
freak_say(freak_word_lit("       freakc --version | --help"));
return ;
}
input_file = freak_process_arg(1);
int64_t fi = 2;
while (!((fi >= args_cnt))) {
freak_word flag = freak_process_arg(fi);
if (freak_word_eq(flag, freak_word_lit("--c"))) {
emit_target = freak_word_lit("c");
}
if (freak_word_eq(flag, freak_word_lit("--llvm"))) {
emit_target = freak_word_lit("llvm");
}
if (freak_word_starts_with(flag, freak_word_lit("--opt="))) {
opt_level = freak_word_char_at(flag, 6);
}
if (freak_word_starts_with(flag, freak_word_lit("--target="))) {
int64_t ti = 9;
freak_word tval = freak_word_lit("");
while (!((ti >= freak_word_length(flag)))) {
tval = freak_word_concat(tval, freak_word_char_at(flag, ti));
ti += 1;
}
cross_target = tval;
}
fi += 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("FREAK v3 Compiling: "), input_file), freak_word_lit(" (Target: ")), emit_target), freak_word_lit(")")));
freak_word src = freak_fs_read(input_file);
if (freak_word_eq(src, freak_word_lit(""))) {
freak_say(freak_word_lit("Error: Could not read file."));
return ;
}
error_count = 0;
freak_init_arrays();
freak_say(freak_word_lit("[1/4] Lexing..."));
freak_tokenize(src);
freak_say(freak_word_lit("[2/4] Parsing..."));
freak_parse_program();
if ((error_count > 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_lit("\x1b[1;31maborting: "), freak_word_from_int(error_count)), freak_word_lit(" error(s) found\x1b[0m")));
freak_process_exit(1);
}
freak_say(freak_word_lit("[3/4] Type Checking..."));
freak_check_program();
freak_say(freak_word_lit("[4/4] Emitting..."));
if (freak_word_eq(emit_target, freak_word_lit("llvm"))) {
out_file = freak_word_concat(input_file, freak_word_lit(".ll"));
freak_emit_llvm_program();
freak_say(freak_word_concat(freak_word_lit("Generated LLVM IR at "), out_file));
}
else {
out_file = freak_word_concat(input_file, freak_word_lit(".c"));
freak_fs_write(out_file, freak_word_lit(""));
freak_emit_c_program();
freak_say(freak_word_concat(freak_word_lit("Generated C code at "), out_file));
}
freak_say(freak_word_lit("Done."));
}
void freak_main(void) {
FREAKC_VERSION = freak_word_lit("0.13.0");
FREAKC_CODENAME = freak_word_lit("Shiranui");
TOK_EOF = freak_word_lit("0");
TOK_IDENT = freak_word_lit("1");
TOK_NUM = freak_word_lit("2");
TOK_STR = freak_word_lit("3");
TOK_BOOL = freak_word_lit("4");
TOK_PUNCT = freak_word_lit("5");
TOK_KW = freak_word_lit("6");
tok_types = 0;
tok_vals = 0;
tok_lines = 0;
tok_cols = 0;
tokens_count = 0;
EXPR_INT = freak_word_lit("1");
EXPR_FLOAT = freak_word_lit("2");
EXPR_STR = freak_word_lit("3");
EXPR_BOOL = freak_word_lit("4");
EXPR_IDENT = freak_word_lit("5");
EXPR_BINOP = freak_word_lit("6");
EXPR_UNARYOP = freak_word_lit("7");
EXPR_CALL = freak_word_lit("8");
EXPR_METHOD = freak_word_lit("9");
EXPR_FIELD = freak_word_lit("10");
EXPR_INDEX = freak_word_lit("11");
ast_expr_kinds = 0;
ast_expr_vals = 0;
ast_expr_lefts = 0;
ast_expr_rights = 0;
STMT_PILOT = freak_word_lit("1");
STMT_SAY = freak_word_lit("2");
STMT_TASK = freak_word_lit("3");
STMT_GIVE_BACK = freak_word_lit("4");
STMT_IF = freak_word_lit("5");
STMT_ASSIGN = freak_word_lit("6");
STMT_EXPR = freak_word_lit("7");
STMT_REPEAT = freak_word_lit("8");
STMT_TRAINING_ARC = freak_word_lit("9");
STMT_WHEN = freak_word_lit("10");
STMT_BLOCK = freak_word_lit("11");
STMT_SHAPE = freak_word_lit("12");
STMT_BREAK = freak_word_lit("13");
STMT_CONTINUE = freak_word_lit("14");
STMT_EVENTUALLY = freak_word_lit("15");
STMT_EXTERN = freak_word_lit("16");
ast_stmt_kinds = 0;
ast_stmt_names = 0;
ast_stmt_exprs = 0;
ast_stmt_bodies = 0;
ast_stmt_else_bodies = 0;
ast_stmt_extras = 0;
ast_task_params = 0;
ast_task_returns = 0;
ast_top_stmts = 0;
shape_registry_names = 0;
shape_registry_fields = 0;
shape_registry_count = 0;
lex_source = freak_word_lit("");
lex_len = 0;
lex_pos = 0;
lex_line = 1;
lex_col = 1;
cur_tok_line = 1;
cur_tok_col = 1;
parse_idx = 1;
tok_total = 0;
parse_error_count = 0;
error_count = 0;
next_expr_id = 0;
next_stmt_id = 0;
out_file = freak_word_lit("");
emit_target = freak_word_lit("llvm");
emt_var_names = 0;
emt_var_types = 0;
emt_var_count = 0;
emt_word_tasks = 0;
emt_word_task_count = 0;
emt_extern_names = 0;
emt_extern_rets = 0;
emt_extern_count = 0;
llvm_line_count = 0;
temp_reg_counter = 0;
string_literals = freak_word_lit("");
string_literals_count = 0;
llvm_var_names = freak_word_lit("");
llvm_var_types = freak_word_lit("");
llvm_task_reg_names = freak_word_lit("");
llvm_task_reg_types = freak_word_lit("");
llvm_task_reg_count = 0;
llvm_cur_func_is_void = false;
llvm_declared_funcs = freak_word_lit("");
llvm_loop_end_label = freak_word_lit("");
llvm_loop_cond_label = freak_word_lit("");
llvm_global_names = freak_word_lit("");
llvm_var_reg_map = freak_word_lit("");
input_file = freak_word_lit("");
opt_level = freak_word_lit("2");
cross_target = freak_word_lit("");
freak_freakc_v3_main();
}
int main(int argc, char** argv) {
    freak_argc = argc;
    freak_argv = argv;
    freak_main();
    return 0;
}
