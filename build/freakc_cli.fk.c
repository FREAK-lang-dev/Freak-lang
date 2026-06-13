#include "freak_runtime.h"
freak_word freak_ver_parse_num(freak_word s, int64_t start);
freak_word freak_ver_parse_pre(freak_word s, int64_t start);
freak_word freak_ver_parse_build(freak_word s, int64_t start);
freak_word freak_ver_get_val(freak_word encoded);
int64_t freak_ver_get_pos(freak_word encoded);
freak_word freak_ver_parse(freak_word version);
freak_word freak_ver_field(freak_word parsed, int64_t field_idx);
int64_t freak_ver_major(freak_word parsed);
int64_t freak_ver_minor(freak_word parsed);
int64_t freak_ver_patch(freak_word parsed);
freak_word freak_ver_pre(freak_word parsed);
freak_word freak_ver_build(freak_word parsed);
freak_word freak_ver_to_string(freak_word parsed);
int64_t freak_ver_compare(freak_word a, freak_word b);
bool freak_ver_eq(freak_word a, freak_word b);
bool freak_ver_lt(freak_word a, freak_word b);
bool freak_ver_gt(freak_word a, freak_word b);
bool freak_ver_lte(freak_word a, freak_word b);
bool freak_ver_gte(freak_word a, freak_word b);
freak_word freak_ver_bump_major(freak_word parsed);
freak_word freak_ver_bump_minor(freak_word parsed);
freak_word freak_ver_bump_patch(freak_word parsed);
freak_word freak_ver_strip_prefix(freak_word constraint, int64_t prefix_len);
bool freak_ver_is_digit(freak_word c);
bool freak_ver_satisfies_single(freak_word v, freak_word constraint);
bool freak_ver_satisfies(freak_word version, freak_word constraint);
bool freak_version_matches_constraint(freak_word version, freak_word constraint);
void freak_init_arrays(void);
int64_t freak_alloc_expr(freak_word kind, freak_word val, freak_word left, freak_word right);
int64_t freak_alloc_stmt(freak_word kind, freak_word name, freak_word expr_id, freak_word body_id, freak_word else_body, freak_word extra, freak_word params, freak_word returns, freak_word line_no);
void freak_register_shape(freak_word name, freak_word fields);
bool freak_is_shape_name(freak_word name);
freak_word freak_get_shape_fields(freak_word name);
int64_t freak_get_shape_field_count(freak_word shape_name);
int64_t freak_get_shape_field_index(freak_word shape_name, freak_word field_name);
void freak_emit(freak_word s);
void freak_emit_line(freak_word s);
void freak_adjust_token_lines(int64_t offset);
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
freak_word freak_current_source_line(void);
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
bool freak_bc_is_copy_type(freak_word type_ann);
freak_word freak_bc_classify_rhs(int64_t expr_id);
freak_word freak_bc_classify_binding(freak_word type_ann, int64_t expr_id);
void freak_bc_push_sym(freak_word name, freak_word kind, freak_word is_mut, int64_t line);
int64_t freak_bc_lookup_idx(freak_word name);
void freak_bc_pop_to_depth(int64_t target_depth);
void freak_bc_enter_scope(void);
void freak_bc_leave_scope(void);
void freak_bc_diag(freak_word msg, freak_word name, int64_t line);
void freak_bc_err_use_after_move(freak_word name, int64_t line);
void freak_bc_err_assign_immut(freak_word name, int64_t line);
void freak_bc_walk_expr(int64_t expr_id, bool consume, int64_t use_line);
void freak_bc_walk_call_args(freak_word args, int64_t use_line);
void freak_bc_walk_stmt(int64_t stmt_id);
void freak_bc_walk_block(freak_word block_str);
void freak_bc_register_task_params(freak_word params, int64_t line);
void freak_bc_run_program(void);
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
freak_word freak_llvm_dbg_escape(freak_word s);
int64_t freak_llvm_dbg_append(freak_word defn);
void freak_llvm_dbg_init(void);
int64_t freak_llvm_dbg_emit_subprogram(freak_word name, int64_t line_no);
int64_t freak_llvm_dbg_emit_location(int64_t line_no);
void freak_llvm_dbg_set_stmt_line(freak_word eid);
freak_word freak_llvm_dbg_begin_func(freak_word name, int64_t line_no);
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
freak_word freak_cli_rgb(int64_t r, int64_t g, int64_t b);
freak_word freak_cli_box_line(int64_t width);
freak_word freak_cli_box_top(int64_t width);
freak_word freak_cli_box_bot(int64_t width);
freak_word freak_cli_box_mid(freak_word content, int64_t width);
freak_word freak_cli_box_sep(int64_t width);
freak_word freak_cli_random_quote(int64_t seed);
freak_word freak_cli_fail_quote(int64_t seed);
void freak_cli_show_version(void);
void freak_cli_show_banner(void);
void freak_cli_show_help(void);
void freak_toml_clear(void);
void freak_toml_set(freak_word key, freak_word val);
freak_word freak_toml_get(freak_word key);
bool freak_toml_has(freak_word key);
void freak_toml_remove_prefix(freak_word prefix);
freak_word freak_toml_get_line(freak_word content, int64_t start);
int64_t freak_toml_line_end(freak_word content, int64_t start);
freak_word freak_toml_trim(freak_word s);
void freak_toml_parse(freak_word content);
freak_word freak_toml_extract_section(freak_word line);
void freak_toml_parse_kv(freak_word line, freak_word section);
freak_word freak_toml_unquote(freak_word s);
void freak_toml_parse_inline_table(freak_word s, freak_word prefix);
void freak_toml_parse_inline_pair(freak_word pair, freak_word prefix);
void freak_toml_write_file(freak_word path);
freak_word freak_toml_extract_dep_name(freak_word key);
bool freak_toml_arr_contains(int64_t arr, int64_t count, freak_word item);
freak_word freak_toml_dep_get_version(freak_word dep_name);
freak_word freak_toml_dep_get_git(freak_word dep_name);
bool freak_toml_dep_is_short_syntax(freak_word dep_name);
void freak_toml_load(freak_word path);
int64_t freak_toml_dep_names_arr(void);
int64_t freak_toml_dep_count(void);
void freak_lock_clear(void);
void freak_lock_add_entry(freak_word name, freak_word version, freak_word source, freak_word sha256);
void freak_lock_remove_entry(freak_word name);
freak_word freak_lock_get_version(freak_word name);
freak_word freak_lock_get_source(freak_word name);
bool freak_lock_has(freak_word name);
void freak_lock_write(freak_word path);
void freak_lock_parse(freak_word content);
freak_word freak_lock_parse_key(freak_word line);
freak_word freak_lock_parse_val(freak_word line);
freak_word freak_lock_get_sha256(freak_word name);
bool freak_lock_load(freak_word path);
void freak_cli_step_start(void);
void freak_cli_step_done(freak_word label);
int64_t freak_cli_count_lines(freak_word s);
freak_word freak_cli_strip_resolved_use_lines(freak_word source);
freak_word freak_cli_transpile(freak_word src_file, freak_word source, freak_word target);
bool freak_cli_has_runtime(freak_word dir);
freak_word freak_cli_find_runtime_dir(void);
freak_word freak_cli_strip_fk(freak_word path);
bool freak_cli_is_windows(void);
bool freak_cli_has_precompiled_runtime(freak_word runtime_dir);
freak_word freak_cli_build_binary(freak_word transpiled_file, freak_word src_file, freak_word target, freak_word opt, freak_word cross);
freak_word freak_cli_find_std_dir(void);
freak_word freak_cli_load_std(freak_word source, freak_word target);
freak_word freak_cli_build(freak_word src_file, freak_word target, freak_word opt, freak_word cross);
void freak_cli_run(freak_word src_file, freak_word target, freak_word opt, freak_word cross);
freak_word freak_hangar_arg(int64_t idx);
int64_t freak_hangar_init(freak_word project_dir);
int64_t freak_hangar_add(freak_word project_dir, freak_word pkg_name, freak_word repo, freak_word ver);
int64_t freak_hangar_remove(freak_word project_dir, freak_word pkg_name);
void freak_resolve_clear(void);
int64_t freak_resolve_find(freak_word name);
bool freak_resolve_add(freak_word name, freak_word version, freak_word source, freak_word constraint, freak_word requested_by);
bool freak_resolve_collect_transitive(freak_word project_dir, freak_word pkg_name, int64_t depth);
int64_t freak_hangar_install(freak_word project_dir);
int64_t freak_hangar_update(freak_word project_dir, freak_word pkg_name);
freak_word freak_hangar_get_index_path(freak_word name);
freak_word freak_hangar_resolve_from_registry(freak_word name, freak_word constraint);
int64_t freak_hangar_install_one(freak_word project_dir, freak_word pkg_name, freak_word repo, freak_word ver);
void freak_hangar_create_stub(freak_word pkg_dir, freak_word pkg_name);
int64_t freak_hangar_version_cmd(freak_word project_dir, freak_word bump);
int64_t freak_hangar_download_file(freak_word url, freak_word dest, bool is_win);
void freak_hangar_mkdir(freak_word path, bool is_win);
int64_t freak_hangar_install_freak(void);
int64_t freak_hangar_outdated(freak_word project_dir);
freak_word freak_hangar_basename(freak_word path);
freak_word freak_hangar_rm_cmd(freak_word path);
freak_word freak_hangar_extract_json_field(freak_word json, freak_word field);
freak_word freak_hangar_compute_sha256(freak_word path);
freak_word freak_hangar_compute_dir_sha256(freak_word pkg_dir);
bool freak_hangar_verify_package(freak_word pkg_name, freak_word pkg_dir, freak_word expected_sha256);
int64_t freak_hangar_audit(freak_word project_dir, bool fix_mode);
int64_t freak_hangar_login(void);
int64_t freak_hangar_publish(freak_word project_dir, bool dry_run);
freak_word freak_hangar_extract_colon(freak_word s, int64_t idx);
void freak_hangar_dispatch(int64_t args_cnt);
int64_t freak_cli_install_clang(freak_word os_tag);
void freak_cli_doctor(bool fix_mode);
int64_t freak_cli_audit_dispatch(freak_word subcmd, int64_t args_cnt);
freak_word freak_cli_learn_quote_arg(freak_word arg);
int64_t freak_cli_learn_dispatch(int64_t args_cnt);
freak_word freak_cli_parse_flags(int64_t start_idx, int64_t args_cnt);
freak_word freak_cli_extract_flag(freak_word flags, int64_t idx);
void freak_cli_flex(void);
void freak_cli_init(freak_word project_name);
void freak_hangar_standalone_main(void);
void freak_freakc_cli_main(void);
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
freak_word EXPR_ARRAY_LIT = FREAK_WORD_EMPTY;
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
int64_t ast_stmt_lines = 0;
int64_t ast_top_stmts = 0;
int64_t ast_pilot_is_mut = 0;
bool strict_borrow = false;
int64_t bc_sym_names = 0;
int64_t bc_sym_kinds = 0;
int64_t bc_sym_is_mut = 0;
int64_t bc_sym_state = 0;
int64_t bc_sym_scopes = 0;
int64_t bc_sym_lines = 0;
int64_t bc_sym_count = 0;
int64_t bc_scope_depth = 0;
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
freak_word llvm_dbg_md = FREAK_WORD_EMPTY;
int64_t llvm_dbg_next_id = 0;
int64_t llvm_dbg_file_id = 0;
int64_t llvm_dbg_cu_id = 0;
int64_t llvm_dbg_empty_id = 0;
int64_t llvm_dbg_subroutine_type_id = 0;
int64_t llvm_dbg_current_scope_id = 0;
int64_t llvm_dbg_current_line = 0;
freak_word llvm_dbg_current_dir = FREAK_WORD_EMPTY;
freak_word llvm_dbg_current_file = FREAK_WORD_EMPTY;
freak_word input_file = FREAK_WORD_EMPTY;
freak_word opt_level = FREAK_WORD_EMPTY;
freak_word cross_target = FREAK_WORD_EMPTY;
int64_t source_line_offset = 0;
freak_word CLI_VERSION = FREAK_WORD_EMPTY;
freak_word CLI_CODENAME = FREAK_WORD_EMPTY;
freak_word C_RESET = FREAK_WORD_EMPTY;
freak_word C_BOLD = FREAK_WORD_EMPTY;
freak_word C_DIM = FREAK_WORD_EMPTY;
freak_word C_ITALIC = FREAK_WORD_EMPTY;
freak_word C_ULINE = FREAK_WORD_EMPTY;
freak_word C_BLINK = FREAK_WORD_EMPTY;
freak_word C_STRIKE = FREAK_WORD_EMPTY;
freak_word C_RED = FREAK_WORD_EMPTY;
freak_word C_GREEN = FREAK_WORD_EMPTY;
freak_word C_YELLOW = FREAK_WORD_EMPTY;
freak_word C_BLUE = FREAK_WORD_EMPTY;
freak_word C_MAGENTA = FREAK_WORD_EMPTY;
freak_word C_CYAN = FREAK_WORD_EMPTY;
freak_word C_WHITE = FREAK_WORD_EMPTY;
freak_word C_BRED = FREAK_WORD_EMPTY;
freak_word C_BGREEN = FREAK_WORD_EMPTY;
freak_word C_BYELLOW = FREAK_WORD_EMPTY;
freak_word C_BBLUE = FREAK_WORD_EMPTY;
freak_word C_BMAGENTA = FREAK_WORD_EMPTY;
freak_word C_BCYAN = FREAK_WORD_EMPTY;
freak_word C_BWHITE = FREAK_WORD_EMPTY;
freak_word C_G1 = FREAK_WORD_EMPTY;
freak_word C_G2 = FREAK_WORD_EMPTY;
freak_word C_G3 = FREAK_WORD_EMPTY;
freak_word C_G4 = FREAK_WORD_EMPTY;
freak_word C_G5 = FREAK_WORD_EMPTY;
freak_word C_G6 = FREAK_WORD_EMPTY;
freak_word C_BG_DARK = FREAK_WORD_EMPTY;
freak_word BOX_TL = FREAK_WORD_EMPTY;
freak_word BOX_TR = FREAK_WORD_EMPTY;
freak_word BOX_BL = FREAK_WORD_EMPTY;
freak_word BOX_BR = FREAK_WORD_EMPTY;
freak_word BOX_H = FREAK_WORD_EMPTY;
freak_word BOX_V = FREAK_WORD_EMPTY;
freak_word BOX_VR = FREAK_WORD_EMPTY;
freak_word BOX_VL = FREAK_WORD_EMPTY;
freak_word SYM_CHECK = FREAK_WORD_EMPTY;
freak_word SYM_CROSS = FREAK_WORD_EMPTY;
freak_word SYM_SPARK = FREAK_WORD_EMPTY;
freak_word SYM_BOLT = FREAK_WORD_EMPTY;
freak_word SYM_GEAR = FREAK_WORD_EMPTY;
freak_word SYM_ARROW = FREAK_WORD_EMPTY;
freak_word SYM_DOT = FREAK_WORD_EMPTY;
freak_word SYM_RING = FREAK_WORD_EMPTY;
freak_word SYM_STAR = FREAK_WORD_EMPTY;
freak_word SYM_SKULL = FREAK_WORD_EMPTY;
freak_word SYM_ROCKET = FREAK_WORD_EMPTY;
freak_word SYM_FIRE = FREAK_WORD_EMPTY;
int64_t toml_keys_arr = 0;
int64_t toml_vals_arr = 0;
int64_t toml_count = 0;
int64_t lock_pkg_names = 0;
int64_t lock_pkg_versions = 0;
int64_t lock_pkg_sources = 0;
int64_t lock_pkg_sha256s = 0;
int64_t lock_pkg_count = 0;
int64_t cli_build_start_ms = 0;
int64_t cli_step_ms = 0;
freak_word HANGAR_DEFAULT_REGISTRY = FREAK_WORD_EMPTY;
int64_t hangar_arg_offset = 0;
int64_t resolve_names = 0;
int64_t resolve_versions = 0;
int64_t resolve_sources = 0;
int64_t resolve_constraints = 0;
int64_t resolve_requested_by = 0;
int64_t resolve_count = 0;
freak_word freak_ver_parse_num(freak_word s, int64_t start) {
freak_word res = freak_word_lit("");
int64_t i = start;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
freak_word c = freak_word_char_at(s, i);
if (((freak_word_eq(c, freak_word_lit(".")) || freak_word_eq(c, freak_word_lit("-"))) || freak_word_eq(c, freak_word_lit("+")))) {
freak_word pos_str = freak_word_from_int((i + 1));
return freak_word_concat(freak_word_concat(res, freak_word_lit(":")), pos_str);
}
res = freak_word_concat(res, c);
i += 1;
}
freak_word pos_str2 = freak_word_from_int(i);
return freak_word_concat(freak_word_concat(res, freak_word_lit(":")), pos_str2);
}
freak_word freak_ver_parse_pre(freak_word s, int64_t start) {
freak_word res = freak_word_lit("");
int64_t i = start;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
freak_word c = freak_word_char_at(s, i);
if (freak_word_eq(c, freak_word_lit("+"))) {
return res;
}
res = freak_word_concat(res, c);
i += 1;
}
return res;
}
freak_word freak_ver_parse_build(freak_word s, int64_t start) {
freak_word res = freak_word_lit("");
int64_t i = start;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
res = freak_word_concat(res, freak_word_char_at(s, i));
i += 1;
}
return res;
}
freak_word freak_ver_get_val(freak_word encoded) {
freak_word res = freak_word_lit("");
int64_t i = 0;
int64_t elen = freak_word_length(encoded);
while (!((i >= elen))) {
freak_word c = freak_word_char_at(encoded, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
return res;
}
res = freak_word_concat(res, c);
i += 1;
}
return res;
}
int64_t freak_ver_get_pos(freak_word encoded) {
int64_t i = 0;
int64_t elen = freak_word_length(encoded);
while (!((i >= elen))) {
freak_word c = freak_word_char_at(encoded, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
freak_word pos_str = freak_word_lit("");
int64_t j = (i + 1);
while (!((j >= elen))) {
pos_str = freak_word_concat(pos_str, freak_word_char_at(encoded, j));
j += 1;
}
return freak_word_to_int(pos_str);
}
i += 1;
}
return 0;
}
freak_word freak_ver_parse(freak_word version) {
freak_word s = version;
if ((freak_word_length(s) > 0)) {
freak_word fc = freak_word_char_at(s, 0);
if ((freak_word_eq(fc, freak_word_lit("v")) || freak_word_eq(fc, freak_word_lit("V")))) {
freak_word ns = freak_word_lit("");
int64_t vi = 1;
while (!((vi >= freak_word_length(s)))) {
ns = freak_word_concat(ns, freak_word_char_at(s, vi));
vi += 1;
}
s = ns;
}
}
freak_word r1 = freak_ver_parse_num(s, 0);
freak_word major = freak_ver_get_val(r1);
int64_t pos1 = freak_ver_get_pos(r1);
freak_word r2 = freak_ver_parse_num(s, pos1);
freak_word minor = freak_ver_get_val(r2);
int64_t pos2 = freak_ver_get_pos(r2);
freak_word r3 = freak_ver_parse_num(s, pos2);
freak_word patch = freak_ver_get_val(r3);
int64_t pos3 = freak_ver_get_pos(r3);
freak_word pre = freak_word_lit("");
freak_word bld = freak_word_lit("");
if ((pos3 <= freak_word_length(s))) {
if ((pos3 > 0)) {
freak_word delim = freak_word_char_at(s, (pos3 - 1));
if (freak_word_eq(delim, freak_word_lit("-"))) {
pre = freak_ver_parse_pre(s, pos3);
}
else {
if (freak_word_eq(delim, freak_word_lit("+"))) {
bld = freak_ver_parse_build(s, pos3);
}
}
}
}
if ((!freak_word_eq(pre, freak_word_lit("")))) {
int64_t pi = 0;
int64_t plen = freak_word_length(s);
while (!((pi >= plen))) {
if (freak_word_eq(freak_word_char_at(s, pi), freak_word_lit("+"))) {
bld = freak_ver_parse_build(s, (pi + 1));
}
pi += 1;
}
}
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(major, freak_word_lit(":")), minor), freak_word_lit(":")), patch), freak_word_lit(":")), pre), freak_word_lit(":")), bld);
}
freak_word freak_ver_field(freak_word parsed, int64_t field_idx) {
freak_word res = freak_word_lit("");
int64_t current_field = 0;
int64_t i = 0;
int64_t plen = freak_word_length(parsed);
while (!((i >= plen))) {
freak_word c = freak_word_char_at(parsed, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
if ((current_field == field_idx)) {
return res;
}
current_field += 1;
res = freak_word_lit("");
}
else {
res = freak_word_concat(res, c);
}
i += 1;
}
if ((current_field == field_idx)) {
return res;
}
return freak_word_lit("");
}
int64_t freak_ver_major(freak_word parsed) {
return freak_word_to_int(freak_ver_field(parsed, 0));
}
int64_t freak_ver_minor(freak_word parsed) {
return freak_word_to_int(freak_ver_field(parsed, 1));
}
int64_t freak_ver_patch(freak_word parsed) {
return freak_word_to_int(freak_ver_field(parsed, 2));
}
freak_word freak_ver_pre(freak_word parsed) {
return freak_ver_field(parsed, 3);
}
freak_word freak_ver_build(freak_word parsed) {
return freak_ver_field(parsed, 4);
}
freak_word freak_ver_to_string(freak_word parsed) {
freak_word maj = freak_ver_field(parsed, 0);
freak_word min = freak_ver_field(parsed, 1);
freak_word pat = freak_ver_field(parsed, 2);
freak_word pre = freak_ver_field(parsed, 3);
freak_word bld = freak_ver_field(parsed, 4);
freak_word out = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(maj, freak_word_lit(".")), min), freak_word_lit(".")), pat);
if ((!freak_word_eq(pre, freak_word_lit("")))) {
out = freak_word_concat(freak_word_concat(out, freak_word_lit("-")), pre);
}
if ((!freak_word_eq(bld, freak_word_lit("")))) {
out = freak_word_concat(freak_word_concat(out, freak_word_lit("+")), bld);
}
return out;
}
int64_t freak_ver_compare(freak_word a, freak_word b) {
int64_t a_major = freak_ver_major(a);
int64_t b_major = freak_ver_major(b);
if ((a_major < b_major)) {
return (0 - 1);
}
if ((a_major > b_major)) {
return 1;
}
int64_t a_minor = freak_ver_minor(a);
int64_t b_minor = freak_ver_minor(b);
if ((a_minor < b_minor)) {
return (0 - 1);
}
if ((a_minor > b_minor)) {
return 1;
}
int64_t a_patch = freak_ver_patch(a);
int64_t b_patch = freak_ver_patch(b);
if ((a_patch < b_patch)) {
return (0 - 1);
}
if ((a_patch > b_patch)) {
return 1;
}
freak_word a_pre = freak_ver_pre(a);
freak_word b_pre = freak_ver_pre(b);
if ((freak_word_eq(a_pre, freak_word_lit("")) && (!freak_word_eq(b_pre, freak_word_lit(""))))) {
return 1;
}
if (((!freak_word_eq(a_pre, freak_word_lit(""))) && freak_word_eq(b_pre, freak_word_lit("")))) {
return (0 - 1);
}
int64_t cmp_len = freak_word_length(a_pre);
if ((freak_word_length(b_pre) < cmp_len)) {
cmp_len = freak_word_length(b_pre);
}
int64_t ci = 0;
while (!((ci >= cmp_len))) {
freak_word ac = freak_word_char_at(a_pre, ci);
freak_word bc = freak_word_char_at(b_pre, ci);
if ((!freak_word_eq(ac, bc))) {
if ((freak_word_eq(ac, freak_word_lit("a")) && freak_word_eq(bc, freak_word_lit("b")))) {
return (0 - 1);
}
if ((freak_word_eq(ac, freak_word_lit("b")) && freak_word_eq(bc, freak_word_lit("a")))) {
return 1;
}
int64_t ai = freak_word_to_int(ac);
int64_t bi = freak_word_to_int(bc);
if ((ai < bi)) {
return (0 - 1);
}
if ((ai > bi)) {
return 1;
}
}
ci += 1;
}
if ((freak_word_length(a_pre) < freak_word_length(b_pre))) {
return (0 - 1);
}
if ((freak_word_length(a_pre) > freak_word_length(b_pre))) {
return 1;
}
return 0;
}
bool freak_ver_eq(freak_word a, freak_word b) {
return (freak_ver_compare(a, b) == 0);
}
bool freak_ver_lt(freak_word a, freak_word b) {
return (freak_ver_compare(a, b) < 0);
}
bool freak_ver_gt(freak_word a, freak_word b) {
return (freak_ver_compare(a, b) > 0);
}
bool freak_ver_lte(freak_word a, freak_word b) {
return (freak_ver_compare(a, b) <= 0);
}
bool freak_ver_gte(freak_word a, freak_word b) {
return (freak_ver_compare(a, b) >= 0);
}
freak_word freak_ver_bump_major(freak_word parsed) {
int64_t maj = (freak_ver_major(parsed) + 1);
return freak_word_concat(freak_word_from_int(maj), freak_word_lit(":0:0::"));
}
freak_word freak_ver_bump_minor(freak_word parsed) {
int64_t maj = freak_ver_major(parsed);
int64_t min = (freak_ver_minor(parsed) + 1);
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_from_int(maj), freak_word_lit(":")), freak_word_from_int(min)), freak_word_lit(":0::"));
}
freak_word freak_ver_bump_patch(freak_word parsed) {
int64_t maj = freak_ver_major(parsed);
int64_t min = freak_ver_minor(parsed);
int64_t pat = (freak_ver_patch(parsed) + 1);
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_from_int(maj), freak_word_lit(":")), freak_word_from_int(min)), freak_word_lit(":")), freak_word_from_int(pat)), freak_word_lit("::"));
}
freak_word freak_ver_strip_prefix(freak_word constraint, int64_t prefix_len) {
freak_word stripped = freak_word_lit("");
int64_t si = prefix_len;
while (!((si >= freak_word_length(constraint)))) {
stripped = freak_word_concat(stripped, freak_word_char_at(constraint, si));
si += 1;
}
return stripped;
}
bool freak_ver_is_digit(freak_word c) {
if (freak_word_eq(c, freak_word_lit("0"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("1"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("2"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("3"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("4"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("5"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("6"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("7"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("8"))) {
return true;
}
if (freak_word_eq(c, freak_word_lit("9"))) {
return true;
}
return false;
}
bool freak_ver_satisfies_single(freak_word v, freak_word constraint) {
if ((freak_word_eq(constraint, freak_word_lit("*")) || freak_word_eq(constraint, freak_word_lit("latest")))) {
return true;
}
if (freak_word_starts_with(constraint, freak_word_lit("^"))) {
freak_word c = freak_ver_parse(freak_ver_strip_prefix(constraint, 1));
if ((freak_ver_major(v) != freak_ver_major(c))) {
return false;
}
return freak_ver_gte(v, c);
}
if (freak_word_starts_with(constraint, freak_word_lit("~"))) {
freak_word t = freak_ver_parse(freak_ver_strip_prefix(constraint, 1));
if ((freak_ver_major(v) != freak_ver_major(t))) {
return false;
}
if ((freak_ver_minor(v) != freak_ver_minor(t))) {
return false;
}
return freak_ver_gte(v, t);
}
if (freak_word_starts_with(constraint, freak_word_lit(">="))) {
return freak_ver_gte(v, freak_ver_parse(freak_ver_strip_prefix(constraint, 2)));
}
if (freak_word_starts_with(constraint, freak_word_lit("<="))) {
return freak_ver_lte(v, freak_ver_parse(freak_ver_strip_prefix(constraint, 2)));
}
if (freak_word_starts_with(constraint, freak_word_lit(">"))) {
return freak_ver_gt(v, freak_ver_parse(freak_ver_strip_prefix(constraint, 1)));
}
if (freak_word_starts_with(constraint, freak_word_lit("<"))) {
return freak_ver_lt(v, freak_ver_parse(freak_ver_strip_prefix(constraint, 1)));
}
if (freak_word_starts_with(constraint, freak_word_lit("="))) {
return freak_ver_eq(v, freak_ver_parse(freak_ver_strip_prefix(constraint, 1)));
}
if ((freak_word_length(constraint) > 0)) {
freak_word fc = freak_word_char_at(constraint, 0);
if (freak_ver_is_digit(fc)) {
freak_word c = freak_ver_parse(constraint);
if ((freak_ver_major(v) != freak_ver_major(c))) {
return false;
}
return freak_ver_gte(v, c);
}
}
return freak_ver_eq(v, freak_ver_parse(constraint));
}
bool freak_ver_satisfies(freak_word version, freak_word constraint) {
freak_word v = freak_ver_parse(version);
int64_t clen = freak_word_length(constraint);
freak_word current = freak_word_lit("");
int64_t i = 0;
while (!((i >= clen))) {
freak_word ch = freak_word_char_at(constraint, i);
if (freak_word_eq(ch, freak_word_lit(" "))) {
if ((freak_word_length(current) > 0)) {
if ((freak_ver_satisfies_single(v, current) == false)) {
return false;
}
current = freak_word_lit("");
}
}
else {
current = freak_word_concat(current, ch);
}
i += 1;
}
if ((freak_word_length(current) > 0)) {
if ((freak_ver_satisfies_single(v, current) == false)) {
return false;
}
}
return true;
}
bool freak_version_matches_constraint(freak_word version, freak_word constraint) {
return freak_ver_satisfies(version, constraint);
}
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
ast_stmt_lines = freak_array_new();
ast_top_stmts = freak_array_new();
ast_pilot_is_mut = freak_array_new();
bc_sym_names = freak_array_new();
bc_sym_kinds = freak_array_new();
bc_sym_is_mut = freak_array_new();
bc_sym_state = freak_array_new();
bc_sym_scopes = freak_array_new();
bc_sym_lines = freak_array_new();
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
int64_t freak_alloc_stmt(freak_word kind, freak_word name, freak_word expr_id, freak_word body_id, freak_word else_body, freak_word extra, freak_word params, freak_word returns, freak_word line_no) {
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
freak_array_push(ast_stmt_lines, line_no);
freak_array_push(ast_pilot_is_mut, freak_word_lit("0"));
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
void freak_adjust_token_lines(int64_t offset) {
if ((offset <= 0)) {
return ;
}
int64_t i = 0;
while (!((i >= tokens_count))) {
int64_t line_no = freak_word_to_int(freak_array_get(tok_lines, i));
if ((line_no > offset)) {
freak_array_set(tok_lines, i, freak_word_from_int((line_no - offset)));
}
else {
freak_array_set(tok_lines, i, freak_word_lit("1"));
}
i += 1;
}
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
res = freak_word_concat(res, freak_word_lit("|"));
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
freak_word freak_current_source_line(void) {
if (((parse_idx < 0) || (parse_idx >= tokens_count))) {
return freak_word_lit("1");
}
int64_t line_no = freak_word_to_int(freak_array_get(tok_lines, parse_idx));
if ((line_no <= 0)) {
line_no = 1;
}
return freak_word_from_int(line_no);
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
if ((freak_word_eq(ttype, TOK_PUNCT) && freak_word_eq(tval, freak_word_lit("[")))) {
freak_advance_tok();
freak_word elem_ids = freak_word_lit("");
bool afin = false;
bool afirst = true;
if (freak_match_tok(TOK_PUNCT, freak_word_lit("]"))) {
afin = true;
}
while (!(afin)) {
if ((freak_word_eq(freak_cur_tok_type(), TOK_EOF) || freak_word_eq(freak_cur_tok_type(), freak_word_lit("")))) {
afin = true;
}
else {
int64_t e_id = freak_parse_expr();
if (afirst) {
elem_ids = freak_word_from_int(e_id);
afirst = false;
}
else {
elem_ids = freak_word_concat(freak_word_concat(elem_ids, freak_word_lit(",")), freak_word_from_int(e_id));
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("]"))) {
afin = true;
}
else {
freak_expect_tok(TOK_PUNCT, freak_word_lit(","));
}
}
}
return freak_alloc_expr(EXPR_ARRAY_LIT, freak_word_lit(""), elem_ids, freak_word_lit(""));
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
freak_word stmt_line = freak_current_source_line();
if (freak_match_tok(TOK_KW, freak_word_lit("say"))) {
int64_t expr_id = freak_parse_expr();
return freak_alloc_stmt(STMT_SAY, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("shape"))) {
return freak_parse_shape();
}
if (freak_match_tok(TOK_KW, freak_word_lit("impl"))) {
return freak_parse_impl();
}
if (freak_match_tok(TOK_KW, freak_word_lit("eventually"))) {
freak_word ev_body = freak_parse_block();
return freak_alloc_stmt(STMT_EVENTUALLY, freak_word_lit(""), freak_word_lit(""), ev_body, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("fixed"))) {
if ((!freak_match_tok(TOK_KW, freak_word_lit("pilot")))) {
freak_diag_error(freak_word_lit("expected 'pilot' after 'fixed'"), freak_word_lit(""));
}
freak_word fname = freak_cur_tok_val();
freak_advance_tok();
freak_word ftype_ann = freak_word_lit("");
if ((freak_word_eq(freak_cur_tok_type(), TOK_PUNCT) && freak_word_eq(freak_cur_tok_val(), freak_word_lit(":")))) {
freak_advance_tok();
ftype_ann = freak_cur_tok_val();
freak_advance_tok();
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("="));
int64_t fexpr_id = freak_parse_expr();
return freak_alloc_stmt(STMT_PILOT, fname, freak_word_from_int(fexpr_id), freak_word_lit(""), freak_word_lit(""), ftype_ann, freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("pilot"))) {
bool is_mut = false;
if (freak_match_tok(TOK_KW, freak_word_lit("mut"))) {
is_mut = true;
}
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
int64_t stmt_id = freak_alloc_stmt(STMT_PILOT, name, freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), type_ann, freak_word_lit(""), freak_word_lit(""), stmt_line);
if (is_mut) {
freak_array_set(ast_pilot_is_mut, stmt_id, freak_word_lit("1"));
}
return stmt_id;
}
if (freak_match_tok(TOK_KW, freak_word_lit("give back"))) {
int64_t expr_id = (0 - 1);
if (((!freak_word_eq(freak_cur_tok_type(), TOK_PUNCT)) || (!freak_word_eq(freak_cur_tok_val(), freak_word_lit("}"))))) {
expr_id = freak_parse_expr();
}
return freak_alloc_stmt(STMT_GIVE_BACK, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("break"))) {
return freak_alloc_stmt(STMT_BREAK, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("continue"))) {
return freak_alloc_stmt(STMT_CONTINUE, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
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
return freak_alloc_stmt(STMT_IF, freak_word_lit(""), freak_word_from_int(expr_id), body_id, else_body, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("repeat"))) {
if (freak_match_tok(TOK_KW, freak_word_lit("until"))) {
int64_t expr_id = freak_parse_expr();
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_REPEAT, freak_word_lit("until"), freak_word_from_int(expr_id), body_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
int64_t expr_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("times"));
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_REPEAT, freak_word_lit("times"), freak_word_from_int(expr_id), body_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_KW, freak_word_lit("training arc"))) {
freak_expect_tok(TOK_KW, freak_word_lit("until"));
int64_t cond_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("max"));
int64_t max_id = freak_parse_expr();
freak_expect_tok(TOK_KW, freak_word_lit("sessions"));
freak_word body_id = freak_parse_block();
return freak_alloc_stmt(STMT_TRAINING_ARC, freak_word_lit(""), freak_word_from_int(cond_id), body_id, freak_word_lit(""), freak_word_from_int(max_id), freak_word_lit(""), freak_word_lit(""), stmt_line);
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
return freak_alloc_stmt(STMT_BLOCK, freak_word_lit(""), freak_word_lit(""), block_id, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
int64_t expr_id = freak_parse_expr();
if (freak_match_tok(TOK_PUNCT, freak_word_lit("="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("+="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("+="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("-="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("-="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("*="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("*="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("/="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("/="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
if (freak_match_tok(TOK_PUNCT, freak_word_lit("%="))) {
int64_t rhs = freak_parse_expr();
return freak_alloc_stmt(STMT_ASSIGN, freak_word_lit("%="), freak_word_from_int(expr_id), freak_word_from_int(rhs), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
return freak_alloc_stmt(STMT_EXPR, freak_word_lit(""), freak_word_from_int(expr_id), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
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
return freak_alloc_stmt(STMT_SHAPE, shape_name, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), fields, freak_word_lit(""), freak_word_lit(""), freak_word_lit("1"));
}
int64_t freak_parse_impl(void) {
freak_word impl_name = freak_cur_tok_val();
freak_word stmt_line = freak_current_source_line();
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
int64_t sid = freak_alloc_stmt(STMT_TASK, full_name, freak_word_lit(""), body_id, freak_word_lit(""), freak_word_lit(""), params, ret_type, stmt_line);
freak_array_push(ast_top_stmts, freak_word_from_int(sid));
}
else {
freak_advance_tok();
}
}
freak_expect_tok(TOK_PUNCT, freak_word_lit("}"));
return freak_alloc_stmt(STMT_BLOCK, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit("1"));
}
int64_t freak_parse_when(void) {
freak_word stmt_line = freak_current_source_line();
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
return freak_alloc_stmt(STMT_WHEN, freak_word_lit(""), freak_word_from_int(target_id), cases_str, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), stmt_line);
}
int64_t freak_parse_extern(void) {
freak_word stmt_line = freak_current_source_line();
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
return freak_alloc_stmt(STMT_EXTERN, ename, freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), freak_word_lit(""), eparams, eret_type, stmt_line);
}
int64_t freak_parse_task_def(void) {
freak_word stmt_line = freak_current_source_line();
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
return freak_alloc_stmt(STMT_TASK, name, freak_word_lit(""), body_id, freak_word_lit(""), freak_word_lit(""), params, ret_type, stmt_line);
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
if (strict_borrow) {
freak_bc_run_program();
}
}
bool freak_bc_is_copy_type(freak_word type_ann) {
if (freak_word_eq(type_ann, freak_word_lit("int"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("uint"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("num"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("tiny"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("bool"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("char"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("float"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("float32"))) {
return true;
}
if (freak_word_eq(type_ann, freak_word_lit("big"))) {
return true;
}
return false;
}
freak_word freak_bc_classify_rhs(int64_t expr_id) {
if ((expr_id < 0)) {
return freak_word_lit("owned");
}
freak_word k = freak_array_get(ast_expr_kinds, expr_id);
if (freak_word_eq(k, EXPR_INT)) {
return freak_word_lit("copy");
}
if (freak_word_eq(k, EXPR_FLOAT)) {
return freak_word_lit("copy");
}
if (freak_word_eq(k, EXPR_BOOL)) {
return freak_word_lit("copy");
}
return freak_word_lit("owned");
}
freak_word freak_bc_classify_binding(freak_word type_ann, int64_t expr_id) {
if ((!freak_word_eq(type_ann, freak_word_lit("")))) {
if (freak_bc_is_copy_type(type_ann)) {
return freak_word_lit("copy");
}
return freak_word_lit("owned");
}
return freak_bc_classify_rhs(expr_id);
}
void freak_bc_push_sym(freak_word name, freak_word kind, freak_word is_mut, int64_t line) {
int64_t phys_len = freak_array_len(bc_sym_names);
if ((bc_sym_count < phys_len)) {
freak_array_set(bc_sym_names, bc_sym_count, name);
freak_array_set(bc_sym_kinds, bc_sym_count, kind);
freak_array_set(bc_sym_is_mut, bc_sym_count, is_mut);
freak_array_set(bc_sym_state, bc_sym_count, freak_word_lit("live"));
freak_array_set(bc_sym_scopes, bc_sym_count, freak_word_from_int(bc_scope_depth));
freak_array_set(bc_sym_lines, bc_sym_count, freak_word_from_int(line));
}
else {
freak_array_push(bc_sym_names, name);
freak_array_push(bc_sym_kinds, kind);
freak_array_push(bc_sym_is_mut, is_mut);
freak_array_push(bc_sym_state, freak_word_lit("live"));
freak_array_push(bc_sym_scopes, freak_word_from_int(bc_scope_depth));
freak_array_push(bc_sym_lines, freak_word_from_int(line));
}
bc_sym_count += 1;
}
int64_t freak_bc_lookup_idx(freak_word name) {
int64_t j = (bc_sym_count - 1);
while (!((j < 0))) {
if (freak_word_eq(freak_array_get(bc_sym_names, j), name)) {
return j;
}
j -= 1;
}
return (0 - 1);
}
void freak_bc_pop_to_depth(int64_t target_depth) {
while (!((bc_sym_count == 0))) {
int64_t top = (bc_sym_count - 1);
int64_t d = freak_word_to_int(freak_array_get(bc_sym_scopes, top));
if ((d <= target_depth)) {
return ;
}
bc_sym_count -= 1;
}
}
void freak_bc_enter_scope(void) {
bc_scope_depth += 1;
}
void freak_bc_leave_scope(void) {
int64_t prev = (bc_scope_depth - 1);
freak_bc_pop_to_depth(prev);
bc_scope_depth = prev;
}
void freak_bc_diag(freak_word msg, freak_word name, int64_t line) {
error_count += 1;
freak_word loc = freak_word_lit("");
if ((line > 0)) {
loc = freak_word_concat(freak_word_concat(freak_word_lit(" (line "), freak_word_from_int(line)), freak_word_lit(")"));
}
freak_word at_name = freak_word_lit("");
if ((!freak_word_eq(name, freak_word_lit("")))) {
at_name = freak_word_concat(freak_word_concat(freak_word_lit(" '"), name), freak_word_lit("'"));
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("\x1b[1;31mborrowck\x1b[0m: "), msg), at_name), loc));
}
void freak_bc_err_use_after_move(freak_word name, int64_t line) {
freak_bc_diag(freak_word_lit("Shirogane. You gave this away. It no longer belongs to you."), name, line);
}
void freak_bc_err_assign_immut(freak_word name, int64_t line) {
freak_bc_diag(freak_word_lit("This binding was sworn to silence. It cannot be reassigned."), name, line);
}
void freak_bc_walk_expr(int64_t expr_id, bool consume, int64_t use_line) {
if ((expr_id < 0)) {
return ;
}
freak_word k = freak_array_get(ast_expr_kinds, expr_id);
if ((((freak_word_eq(k, EXPR_INT) || freak_word_eq(k, EXPR_FLOAT)) || freak_word_eq(k, EXPR_STR)) || freak_word_eq(k, EXPR_BOOL))) {
return ;
}
if (freak_word_eq(k, EXPR_IDENT)) {
freak_word name = freak_array_get(ast_expr_vals, expr_id);
int64_t idx = freak_bc_lookup_idx(name);
if ((idx < 0)) {
return ;
}
freak_word state = freak_array_get(bc_sym_state, idx);
freak_word kind = freak_array_get(bc_sym_kinds, idx);
if (freak_word_eq(state, freak_word_lit("moved"))) {
freak_bc_err_use_after_move(name, use_line);
return ;
}
if ((consume && freak_word_eq(kind, freak_word_lit("owned")))) {
freak_array_set(bc_sym_state, idx, freak_word_lit("moved"));
}
return ;
}
if (freak_word_eq(k, EXPR_BINOP)) {
freak_word lft = freak_array_get(ast_expr_lefts, expr_id);
freak_word rht = freak_array_get(ast_expr_rights, expr_id);
freak_bc_walk_expr(freak_word_to_int(lft), false, use_line);
freak_bc_walk_expr(freak_word_to_int(rht), false, use_line);
return ;
}
if (freak_word_eq(k, EXPR_UNARYOP)) {
freak_word inner = freak_array_get(ast_expr_lefts, expr_id);
freak_bc_walk_expr(freak_word_to_int(inner), false, use_line);
return ;
}
if (freak_word_eq(k, EXPR_CALL)) {
freak_word args = freak_array_get(ast_expr_lefts, expr_id);
freak_bc_walk_call_args(args, use_line);
return ;
}
if (freak_word_eq(k, EXPR_METHOD)) {
freak_word recv = freak_array_get(ast_expr_lefts, expr_id);
freak_word margs = freak_array_get(ast_expr_rights, expr_id);
freak_bc_walk_expr(freak_word_to_int(recv), false, use_line);
freak_bc_walk_call_args(margs, use_line);
return ;
}
if (freak_word_eq(k, EXPR_FIELD)) {
freak_word base = freak_array_get(ast_expr_lefts, expr_id);
freak_bc_walk_expr(freak_word_to_int(base), false, use_line);
return ;
}
if (freak_word_eq(k, EXPR_INDEX)) {
freak_word base = freak_array_get(ast_expr_lefts, expr_id);
freak_word idxe = freak_array_get(ast_expr_rights, expr_id);
freak_bc_walk_expr(freak_word_to_int(base), false, use_line);
freak_bc_walk_expr(freak_word_to_int(idxe), false, use_line);
return ;
}
}
void freak_bc_walk_call_args(freak_word args, int64_t use_line) {
if (freak_word_eq(args, freak_word_lit(""))) {
return ;
}
freak_word cur = freak_word_lit("");
int64_t i = 0;
int64_t n = freak_word_length(args);
for (int64_t __rep = 0; __rep < n; __rep++) {
freak_word c = freak_word_char_at(args, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((!freak_word_eq(cur, freak_word_lit("")))) {
freak_bc_walk_expr(freak_word_to_int(cur), true, use_line);
}
cur = freak_word_lit("");
}
else {
cur = freak_word_concat(cur, c);
}
i += 1;
}
if ((!freak_word_eq(cur, freak_word_lit("")))) {
freak_bc_walk_expr(freak_word_to_int(cur), true, use_line);
}
}
void freak_bc_walk_stmt(int64_t stmt_id) {
if ((stmt_id < 0)) {
return ;
}
freak_word kind = freak_array_get(ast_stmt_kinds, stmt_id);
int64_t line = freak_word_to_int(freak_array_get(ast_stmt_lines, stmt_id));
if ((source_line_offset > 0)) {
if ((line <= 1)) {
return ;
}
}
if (freak_word_eq(kind, STMT_PILOT)) {
freak_word name = freak_array_get(ast_stmt_names, stmt_id);
freak_word expr_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_word type_ann = freak_array_get(ast_stmt_extras, stmt_id);
int64_t expr_id = freak_word_to_int(expr_w);
freak_bc_walk_expr(expr_id, true, line);
freak_word k = freak_bc_classify_binding(type_ann, expr_id);
freak_word is_mut = freak_array_get(ast_pilot_is_mut, stmt_id);
freak_bc_push_sym(name, k, is_mut, line);
return ;
}
if (freak_word_eq(kind, STMT_ASSIGN)) {
freak_word op = freak_array_get(ast_stmt_names, stmt_id);
freak_word lhs_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_word rhs_w = freak_array_get(ast_stmt_bodies, stmt_id);
int64_t lhs = freak_word_to_int(lhs_w);
int64_t rhs = freak_word_to_int(rhs_w);
freak_bc_walk_expr(rhs, true, line);
freak_word lk = freak_array_get(ast_expr_kinds, lhs);
if (freak_word_eq(lk, EXPR_IDENT)) {
freak_word lname = freak_array_get(ast_expr_vals, lhs);
int64_t idx = freak_bc_lookup_idx(lname);
if ((idx >= 0)) {
freak_word is_mut = freak_array_get(bc_sym_is_mut, idx);
if ((!freak_word_eq(is_mut, freak_word_lit("1")))) {
freak_bc_err_assign_immut(lname, line);
}
freak_array_set(bc_sym_state, idx, freak_word_lit("live"));
}
}
else {
freak_bc_walk_expr(lhs, false, line);
}
return ;
}
if (freak_word_eq(kind, STMT_SAY)) {
freak_word expr_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_bc_walk_expr(freak_word_to_int(expr_w), false, line);
return ;
}
if (freak_word_eq(kind, STMT_GIVE_BACK)) {
freak_word expr_w = freak_array_get(ast_stmt_exprs, stmt_id);
int64_t eid = freak_word_to_int(expr_w);
if ((eid >= 0)) {
freak_bc_walk_expr(eid, true, line);
}
return ;
}
if (freak_word_eq(kind, STMT_EXPR)) {
freak_word expr_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_bc_walk_expr(freak_word_to_int(expr_w), false, line);
return ;
}
if (freak_word_eq(kind, STMT_IF)) {
freak_word cond_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_word then_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_word else_w = freak_array_get(ast_stmt_else_bodies, stmt_id);
freak_bc_walk_expr(freak_word_to_int(cond_w), false, line);
freak_bc_enter_scope();
freak_bc_walk_block(then_w);
freak_bc_leave_scope();
if ((!freak_word_eq(else_w, freak_word_lit("")))) {
freak_bc_enter_scope();
freak_bc_walk_block(else_w);
freak_bc_leave_scope();
}
return ;
}
if (freak_word_eq(kind, STMT_REPEAT)) {
freak_word cond_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_word body_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_bc_walk_expr(freak_word_to_int(cond_w), false, line);
freak_bc_enter_scope();
freak_bc_walk_block(body_w);
freak_bc_leave_scope();
return ;
}
if (freak_word_eq(kind, STMT_TRAINING_ARC)) {
freak_word cond_w = freak_array_get(ast_stmt_exprs, stmt_id);
freak_word body_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_bc_walk_expr(freak_word_to_int(cond_w), false, line);
freak_bc_enter_scope();
freak_bc_walk_block(body_w);
freak_bc_leave_scope();
return ;
}
if (freak_word_eq(kind, STMT_BLOCK)) {
freak_word body_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_bc_enter_scope();
freak_bc_walk_block(body_w);
freak_bc_leave_scope();
return ;
}
if (freak_word_eq(kind, STMT_EVENTUALLY)) {
freak_word body_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_bc_enter_scope();
freak_bc_walk_block(body_w);
freak_bc_leave_scope();
return ;
}
if (freak_word_eq(kind, STMT_TASK)) {
freak_word body_w = freak_array_get(ast_stmt_bodies, stmt_id);
freak_word params = freak_array_get(ast_task_params, stmt_id);
freak_bc_enter_scope();
freak_bc_register_task_params(params, line);
freak_bc_walk_block(body_w);
freak_bc_leave_scope();
return ;
}
if (freak_word_eq(kind, STMT_SHAPE)) {
return ;
}
if (freak_word_eq(kind, STMT_BREAK)) {
return ;
}
if (freak_word_eq(kind, STMT_CONTINUE)) {
return ;
}
if (freak_word_eq(kind, STMT_EXTERN)) {
return ;
}
if (freak_word_eq(kind, STMT_WHEN)) {
return ;
}
}
void freak_bc_walk_block(freak_word block_str) {
if (freak_word_eq(block_str, freak_word_lit(""))) {
return ;
}
freak_word cur = freak_word_lit("");
int64_t i = 0;
int64_t n = freak_word_length(block_str);
for (int64_t __rep = 0; __rep < n; __rep++) {
freak_word c = freak_word_char_at(block_str, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((!freak_word_eq(cur, freak_word_lit("")))) {
freak_bc_walk_stmt(freak_word_to_int(cur));
}
cur = freak_word_lit("");
}
else {
cur = freak_word_concat(cur, c);
}
i += 1;
}
if ((!freak_word_eq(cur, freak_word_lit("")))) {
freak_bc_walk_stmt(freak_word_to_int(cur));
}
}
void freak_bc_register_task_params(freak_word params, int64_t line) {
if (freak_word_eq(params, freak_word_lit(""))) {
return ;
}
freak_word cur_name = freak_word_lit("");
freak_word cur_type = freak_word_lit("");
bool in_type = false;
int64_t i = 0;
int64_t n = freak_word_length(params);
for (int64_t __rep = 0; __rep < n; __rep++) {
freak_word c = freak_word_char_at(params, i);
if (freak_word_eq(c, freak_word_lit(","))) {
if ((!freak_word_eq(cur_name, freak_word_lit("")))) {
freak_word k = freak_word_lit("owned");
if (freak_bc_is_copy_type(cur_type)) {
k = freak_word_lit("copy");
}
freak_bc_push_sym(cur_name, k, freak_word_lit("1"), line);
}
cur_name = freak_word_lit("");
cur_type = freak_word_lit("");
in_type = false;
}
else {
if (freak_word_eq(c, freak_word_lit(":"))) {
in_type = true;
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
freak_word k2 = freak_word_lit("owned");
if (freak_bc_is_copy_type(cur_type)) {
k2 = freak_word_lit("copy");
}
freak_bc_push_sym(cur_name, k2, freak_word_lit("1"), line);
}
}
void freak_bc_run_program(void) {
bc_sym_count = 0;
bc_scope_depth = 0;
int64_t top_count = freak_array_len(ast_top_stmts);
int64_t i = 0;
for (int64_t __rep = 0; __rep < top_count; __rep++) {
int64_t stmt_id = freak_word_to_int(freak_array_get(ast_top_stmts, i));
freak_bc_walk_stmt(stmt_id);
i += 1;
}
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
if (freak_word_eq(kind, EXPR_ARRAY_LIT)) {
freak_emit(freak_word_lit("({ int64_t __arr = freak_llvm_array_new(); "));
int64_t ali = 0;
int64_t alen2 = freak_word_length(left);
freak_word cur_eid_c = freak_word_lit("");
for (int64_t __rep = 0; __rep < alen2; __rep++) {
freak_word acc = freak_word_char_at(left, ali);
if (freak_word_eq(acc, freak_word_lit(","))) {
if ((freak_word_length(cur_eid_c) > 0)) {
freak_emit(freak_word_lit("freak_llvm_array_push(__arr, "));
freak_emit_expr(cur_eid_c);
freak_emit(freak_word_lit("); "));
cur_eid_c = freak_word_lit("");
}
}
else {
cur_eid_c = freak_word_concat(cur_eid_c, acc);
}
ali += 1;
}
if ((freak_word_length(cur_eid_c) > 0)) {
freak_emit(freak_word_lit("freak_llvm_array_push(__arr, "));
freak_emit_expr(cur_eid_c);
freak_emit(freak_word_lit("); "));
}
freak_emit(freak_word_lit("__arr; })"));
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
freak_word str_val = freak_word_replace(val, freak_word_lit("|"), freak_word_lit("|"));
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
int64_t lhs_idx = freak_word_to_int(expr_id_w);
freak_word lhs_kind = freak_array_get(ast_expr_kinds, lhs_idx);
if (freak_word_eq(lhs_kind, EXPR_FIELD)) {
freak_word field_name = freak_array_get(ast_expr_vals, lhs_idx);
freak_word recv_id = freak_array_get(ast_expr_lefts, lhs_idx);
int64_t fidx = (0 - 1);
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
int64_t tmpidx = freak_get_shape_field_index(freak_array_get(shape_registry_names, si), field_name);
if ((tmpidx >= 0)) {
fidx = tmpidx;
}
si += 1;
}
if ((fidx < 0)) {
fidx = 0;
}
freak_word fidx_w = freak_word_from_int(fidx);
if (freak_word_eq(op_w, freak_word_lit("="))) {
freak_emit(freak_word_lit("freak_llvm_shape_set("));
freak_emit_expr(recv_id);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(", "), fidx_w), freak_word_lit(", ")));
freak_emit_expr(rhs_w);
freak_emit_line(freak_word_lit(");"));
return ;
}
freak_word bin_op = freak_word_lit("+");
if (freak_word_eq(op_w, freak_word_lit("-="))) {
bin_op = freak_word_lit("-");
}
if (freak_word_eq(op_w, freak_word_lit("*="))) {
bin_op = freak_word_lit("*");
}
if (freak_word_eq(op_w, freak_word_lit("/="))) {
bin_op = freak_word_lit("/");
}
if (freak_word_eq(op_w, freak_word_lit("%="))) {
bin_op = freak_word_lit("%");
}
freak_emit(freak_word_lit("freak_llvm_shape_set("));
freak_emit_expr(recv_id);
freak_emit(freak_word_concat(freak_word_concat(freak_word_lit(", "), fidx_w), freak_word_lit(", freak_llvm_shape_get(")));
freak_emit_expr(recv_id);
freak_emit(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(", "), fidx_w), freak_word_lit(") ")), bin_op), freak_word_lit(" ")));
freak_emit_expr(rhs_w);
freak_emit_line(freak_word_lit(");"));
return ;
}
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
freak_emit_line(freak_word_lit("    freak_enable_ansi();"));
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
freak_word out = s;
if (((llvm_dbg_current_scope_id > 0) && (llvm_dbg_current_line > 0))) {
if ((freak_word_starts_with(s, freak_word_lit("    ")) && (!freak_word_starts_with(s, freak_word_lit("    ;"))))) {
int64_t loc_id = freak_llvm_dbg_emit_location(llvm_dbg_current_line);
out = freak_word_concat(freak_word_concat(s, freak_word_lit(", !dbg !")), freak_word_from_int(loc_id));
}
}
freak_fs_append(out_file, freak_word_concat(out, freak_word_lit("\n")));
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
freak_word freak_llvm_dbg_escape(freak_word s) {
freak_word out = freak_word_lit("");
int64_t i = 0;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
freak_word ch = freak_word_char_at(s, i);
if (freak_word_eq(ch, freak_word_lit("\\"))) {
out = freak_word_concat(out, freak_word_lit("\\5C"));
}
else {
if (freak_word_eq(ch, freak_word_lit("\""))) {
out = freak_word_concat(out, freak_word_lit("\\22"));
}
else {
out = freak_word_concat(out, ch);
}
}
i += 1;
}
return out;
}
int64_t freak_llvm_dbg_append(freak_word defn) {
int64_t id = llvm_dbg_next_id;
llvm_dbg_next_id += 1;
llvm_dbg_md = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(llvm_dbg_md, freak_word_lit("!")), freak_word_from_int(id)), freak_word_lit(" = ")), defn), freak_word_lit("\n"));
return id;
}
void freak_llvm_dbg_init(void) {
llvm_dbg_md = freak_word_lit("");
llvm_dbg_next_id = 0;
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
llvm_dbg_current_dir = freak_word_lit(".");
llvm_dbg_current_file = input_file;
int64_t slash = (-1);
int64_t i = 0;
int64_t plen = freak_word_length(input_file);
while (!((i >= plen))) {
freak_word ch = freak_word_char_at(input_file, i);
if ((freak_word_eq(ch, freak_word_lit("/")) || freak_word_eq(ch, freak_word_lit("\\")))) {
slash = i;
}
i += 1;
}
if ((slash >= 0)) {
freak_word base = freak_word_lit("");
i = (slash + 1);
while (!((i >= plen))) {
base = freak_word_concat(base, freak_word_char_at(input_file, i));
i += 1;
}
if ((!freak_word_eq(base, freak_word_lit("")))) {
llvm_dbg_current_file = base;
}
freak_word dir = freak_word_lit("");
i = 0;
while (!((i >= slash))) {
dir = freak_word_concat(dir, freak_word_char_at(input_file, i));
i += 1;
}
if ((!freak_word_eq(dir, freak_word_lit("")))) {
llvm_dbg_current_dir = dir;
}
}
freak_word file_name = freak_llvm_dbg_escape(llvm_dbg_current_file);
freak_word dir_name = freak_llvm_dbg_escape(llvm_dbg_current_dir);
llvm_dbg_file_id = freak_llvm_dbg_append(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("!DIFile(filename: \""), file_name), freak_word_lit("\", directory: \"")), dir_name), freak_word_lit("\")")));
llvm_dbg_cu_id = freak_llvm_dbg_append(freak_word_concat(freak_word_concat(freak_word_lit("distinct !DICompileUnit(language: DW_LANG_C, file: !"), freak_word_from_int(llvm_dbg_file_id)), freak_word_lit(", producer: \"FREAK v3\", isOptimized: false, runtimeVersion: 0, emissionKind: LineTablesOnly)")));
llvm_dbg_empty_id = freak_llvm_dbg_append(freak_word_lit("!{}"));
llvm_dbg_subroutine_type_id = freak_llvm_dbg_append(freak_word_concat(freak_word_concat(freak_word_lit("!DISubroutineType(types: !"), freak_word_from_int(llvm_dbg_empty_id)), freak_word_lit(")")));
}
int64_t freak_llvm_dbg_emit_subprogram(freak_word name, int64_t line_no) {
if ((line_no <= 0)) {
line_no = 1;
}
return freak_llvm_dbg_append(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("distinct !DISubprogram(name: \""), freak_llvm_dbg_escape(name)), freak_word_lit("\", scope: !")), freak_word_from_int(llvm_dbg_file_id)), freak_word_lit(", file: !")), freak_word_from_int(llvm_dbg_file_id)), freak_word_lit(", line: ")), freak_word_from_int(line_no)), freak_word_lit(", type: !")), freak_word_from_int(llvm_dbg_subroutine_type_id)), freak_word_lit(", scopeLine: ")), freak_word_from_int(line_no)), freak_word_lit(", spFlags: DISPFlagDefinition, unit: !")), freak_word_from_int(llvm_dbg_cu_id)), freak_word_lit(", retainedNodes: !")), freak_word_from_int(llvm_dbg_empty_id)), freak_word_lit(")")));
}
int64_t freak_llvm_dbg_emit_location(int64_t line_no) {
if ((line_no <= 0)) {
line_no = 1;
}
return freak_llvm_dbg_append(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("!DILocation(line: "), freak_word_from_int(line_no)), freak_word_lit(", column: 1, scope: !")), freak_word_from_int(llvm_dbg_current_scope_id)), freak_word_lit(")")));
}
void freak_llvm_dbg_set_stmt_line(freak_word eid) {
int64_t line_no = 1;
if ((freak_word_length(eid) > 0)) {
int64_t idx = freak_word_to_int(eid);
line_no = freak_word_to_int(freak_array_get(ast_stmt_lines, idx));
if ((line_no <= 0)) {
line_no = 1;
}
}
llvm_dbg_current_line = line_no;
}
freak_word freak_llvm_dbg_begin_func(freak_word name, int64_t line_no) {
int64_t sp_id = freak_llvm_dbg_emit_subprogram(name, line_no);
llvm_dbg_current_scope_id = sp_id;
llvm_dbg_current_line = line_no;
return freak_word_concat(freak_word_lit(" !dbg !"), freak_word_from_int(sp_id));
}
freak_word freak_register_string_literal(freak_word val) {
freak_word id = freak_word_concat(freak_word_lit("@.str."), freak_word_from_int(string_literals_count));
string_literals_count += 1;
freak_word real_val = freak_word_replace(val, freak_word_lit("|"), freak_word_lit("|"));
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
return freak_word_concat(freak_word_lit("@g_"), vname);
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
if (freak_word_eq(val, freak_word_lit("to_word"))) {
return freak_word_lit("w");
}
if (freak_word_eq(val, freak_word_lit("to_num"))) {
return freak_word_lit("n");
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
if (freak_word_eq(val, freak_word_lit("char_to_word"))) {
return freak_word_lit("@freak_llvm_char_to_word");
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
if (freak_word_eq(val, freak_word_lit("time::now_ms"))) {
return freak_word_lit("@freak_llvm_time_now_ms");
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
if (freak_word_eq(val, freak_word_lit("ui::event_repeat"))) {
return freak_word_lit("@freak_llvm_ui_event_repeat");
}
if (freak_word_eq(val, freak_word_lit("ui::event_scroll_dy"))) {
return freak_word_lit("@freak_llvm_ui_event_scroll_dy");
}
if (freak_word_eq(val, freak_word_lit("ui::event_width"))) {
return freak_word_lit("@freak_llvm_ui_event_width");
}
if (freak_word_eq(val, freak_word_lit("ui::event_height"))) {
return freak_word_lit("@freak_llvm_ui_event_height");
}
if (freak_word_eq(val, freak_word_lit("ui::event_gained"))) {
return freak_word_lit("@freak_llvm_ui_event_gained");
}
if (freak_word_eq(val, freak_word_lit("ui::get_width"))) {
return freak_word_lit("@freak_llvm_ui_get_width");
}
if (freak_word_eq(val, freak_word_lit("ui::get_height"))) {
return freak_word_lit("@freak_llvm_ui_get_height");
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
int64_t len = (freak_word_length(freak_word_replace(val, freak_word_lit("|"), freak_word_lit("|"))) + 1);
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
if (freak_word_eq(kind, EXPR_ARRAY_LIT)) {
freak_word arr_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    "), arr_reg), freak_word_lit(" = call i64 @freak_llvm_array_new()")));
int64_t ai = 0;
int64_t alen = freak_word_length(left);
freak_word cur_eid = freak_word_lit("");
for (int64_t __rep = 0; __rep < alen; __rep++) {
freak_word ac = freak_word_char_at(left, ai);
if (freak_word_eq(ac, freak_word_lit(","))) {
if ((freak_word_length(cur_eid) > 0)) {
freak_word er = freak_llvm_emit_expr(cur_eid);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_array_push(i64 "), arr_reg), freak_word_lit(", i64 ")), er), freak_word_lit(")")));
cur_eid = freak_word_lit("");
}
}
else {
cur_eid = freak_word_concat(cur_eid, ac);
}
ai += 1;
}
if ((freak_word_length(cur_eid) > 0)) {
freak_word er2 = freak_llvm_emit_expr(cur_eid);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_array_push(i64 "), arr_reg), freak_word_lit(", i64 ")), er2), freak_word_lit(")")));
}
return arr_reg;
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
freak_word recv_ty = freak_llvm_infer_expr_type(left);
if (freak_word_eq(val, freak_word_lit("to_int"))) {
if (freak_word_starts_with(recv_ty, freak_word_lit("n"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_num_to_int(i64 ")), obj_reg), freak_word_lit(")")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_to_int(i64 ")), obj_reg), freak_word_lit(")")));
}
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("to_num"))) {
if (freak_word_starts_with(recv_ty, freak_word_lit("w"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_parse_num(i64 ")), obj_reg), freak_word_lit(")")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_int_to_num(i64 ")), obj_reg), freak_word_lit(")")));
}
return res_reg;
}
if (freak_word_eq(val, freak_word_lit("to_word"))) {
if (freak_word_starts_with(recv_ty, freak_word_lit("n"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_from_num(i64 ")), obj_reg), freak_word_lit(")")));
}
else {
if (freak_word_starts_with(recv_ty, freak_word_lit("b"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_from_bool(i64 ")), obj_reg), freak_word_lit(")")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @freak_llvm_word_from_int(i64 ")), obj_reg), freak_word_lit(")")));
}
}
return res_reg;
}
freak_word extra_args = freak_word_lit("");
if ((freak_word_length(right) > 0)) {
extra_args = freak_word_concat(freak_word_lit(", "), freak_llvm_emit_args(right));
}
freak_word best_sname = freak_word_lit("");
freak_word best_ret = freak_word_lit("");
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
freak_word sname = freak_word_concat(freak_word_lit(""), freak_array_get(shape_registry_names, si));
freak_word call_ret = freak_llvm_get_task_ret_type(freak_word_concat(freak_word_concat(sname, freak_word_lit("_")), val));
if ((freak_word_length(call_ret) > 0)) {
best_sname = sname;
best_ret = call_ret;
}
si += 1;
}
if ((freak_word_length(best_sname) > 0)) {
freak_word impl_fname = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("freak_"), best_sname), freak_word_lit("_")), val);
if (freak_word_eq(best_ret, freak_word_lit("v"))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @"), impl_fname), freak_word_lit("(i64 ")), obj_reg), extra_args), freak_word_lit(")")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = add i64 0, 0")));
}
else {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), res_reg), freak_word_lit(" = call i64 @")), impl_fname), freak_word_lit("(i64 ")), obj_reg), extra_args), freak_word_lit(")")));
}
return res_reg;
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
freak_llvm_dbg_set_stmt_line(eid);
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
int64_t lhs_idx = freak_word_to_int(expr_id_w);
freak_word lhs_kind = freak_array_get(ast_expr_kinds, lhs_idx);
if (freak_word_eq(lhs_kind, EXPR_FIELD)) {
freak_word field_name = freak_array_get(ast_expr_vals, lhs_idx);
freak_word recv_id = freak_array_get(ast_expr_lefts, lhs_idx);
freak_word recv_reg = freak_llvm_emit_expr(recv_id);
int64_t fidx = (0 - 1);
int64_t si = 0;
for (int64_t __rep = 0; __rep < shape_registry_count; __rep++) {
int64_t tmpidx = freak_get_shape_field_index(freak_array_get(shape_registry_names, si), field_name);
if ((tmpidx >= 0)) {
fidx = tmpidx;
}
si += 1;
}
if ((fidx < 0)) {
fidx = 0;
}
freak_word rhs_reg = freak_llvm_emit_expr(rhs_w);
freak_word fidx_w = freak_word_from_int(fidx);
if (freak_word_eq(name_w, freak_word_lit("="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_shape_set(i64 "), recv_reg), freak_word_lit(", i64 ")), fidx_w), freak_word_lit(", i64 ")), rhs_reg), freak_word_lit(")")));
return ;
}
freak_word cur_reg = freak_next_reg();
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), cur_reg), freak_word_lit(" = call i64 @freak_llvm_shape_get(i64 ")), recv_reg), freak_word_lit(", i64 ")), fidx_w), freak_word_lit(")")));
freak_word op_reg = freak_next_reg();
if (freak_word_eq(name_w, freak_word_lit("+="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = add i64 ")), cur_reg), freak_word_lit(", ")), rhs_reg));
}
if (freak_word_eq(name_w, freak_word_lit("-="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = sub i64 ")), cur_reg), freak_word_lit(", ")), rhs_reg));
}
if (freak_word_eq(name_w, freak_word_lit("*="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = mul i64 ")), cur_reg), freak_word_lit(", ")), rhs_reg));
}
if (freak_word_eq(name_w, freak_word_lit("/="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = sdiv i64 ")), cur_reg), freak_word_lit(", ")), rhs_reg));
}
if (freak_word_eq(name_w, freak_word_lit("%="))) {
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), op_reg), freak_word_lit(" = srem i64 ")), cur_reg), freak_word_lit(", ")), rhs_reg));
}
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    call void @freak_llvm_shape_set(i64 "), recv_reg), freak_word_lit(", i64 ")), fidx_w), freak_word_lit(", i64 ")), op_reg), freak_word_lit(")")));
return ;
}
freak_word var_name_expr = freak_array_get(ast_expr_vals, lhs_idx);
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
freak_llvm_reg_var(cur_name, cur_name);
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
freak_llvm_reg_var(cur_name, cur_name);
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
int64_t line_no = freak_word_to_int(freak_array_get(ast_stmt_lines, i));
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
freak_word dbg_attr = freak_llvm_dbg_begin_func(name_w, line_no);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("define "), ret_type), freak_word_lit(" @freak_")), name_w), freak_word_lit("(")), p_str), freak_word_lit(")")), dbg_attr), freak_word_lit(" {")));
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
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
}
void freak_llvm_emit_runtime_decls(void) {
freak_llvm_emit_line(freak_word_lit("declare i32 @puts(i8*)"));
freak_llvm_emit_line(freak_word_lit("declare i32 @printf(i8*, ...)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @strlen(i8*)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_from_int(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_word_from_bool(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_char_to_word(i64)"));
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
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_time_now_ms()"));
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
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_repeat(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_scroll_dy(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_width(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_height(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_event_gained(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_get_width(i64)"));
freak_llvm_emit_line(freak_word_lit("declare i64 @freak_llvm_ui_get_height(i64)"));
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
freak_llvm_dbg_init();
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
freak_word init_dbg = freak_llvm_dbg_begin_func(freak_word_lit("freak_init_globals"), 1);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("define void @freak_init_globals()"), init_dbg), freak_word_lit(" {")));
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
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
}
if ((!has_main_task)) {
llvm_var_names = freak_word_lit("");
llvm_var_types = freak_word_lit("");
llvm_var_reg_map = freak_word_lit("");
llvm_cur_func_is_void = true;
freak_word main_dbg = freak_llvm_dbg_begin_func(freak_word_lit("freak_main"), 1);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("define void @freak_main()"), main_dbg), freak_word_lit(" {")));
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
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
}
freak_llvm_emit_line(freak_word_lit(""));
freak_word cmain_dbg = freak_llvm_dbg_begin_func(freak_word_lit("main"), 1);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("define i32 @main(i32 %argc, i8** %argv)"), cmain_dbg), freak_word_lit(" {")));
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
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
freak_llvm_emit_line(freak_word_lit(""));
freak_llvm_emit_line(freak_word_lit("; String Literals"));
freak_llvm_emit_line(string_literals);
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_lit("!llvm.dbg.cu = !{!"), freak_word_from_int(llvm_dbg_cu_id)), freak_word_lit("}")));
freak_llvm_emit_line(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("!llvm.module.flags = !{!"), freak_word_from_int(freak_llvm_dbg_append(freak_word_lit("!{i32 7, !\"Dwarf Version\", i32 4}")))), freak_word_lit(", !")), freak_word_from_int(freak_llvm_dbg_append(freak_word_lit("!{i32 2, !\"Debug Info Version\", i32 3}")))), freak_word_lit("}")));
freak_llvm_emit_line(llvm_dbg_md);
}
freak_word freak_cli_rgb(int64_t r, int64_t g, int64_t b) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("\x1b[38;2;"), freak_word_from_int(r)), freak_word_lit(";")), freak_word_from_int(g)), freak_word_lit(";")), freak_word_from_int(b)), freak_word_lit("m"));
}
freak_word freak_cli_box_line(int64_t width) {
freak_word line = freak_word_lit("");
int64_t i = 0;
while (!((i >= width))) {
line = freak_word_concat(line, BOX_H);
i += 1;
}
return line;
}
freak_word freak_cli_box_top(int64_t width) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), BOX_TL), freak_cli_box_line(width)), BOX_TR), C_RESET);
}
freak_word freak_cli_box_bot(int64_t width) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), BOX_BL), freak_cli_box_line(width)), BOX_BR), C_RESET);
}
freak_word freak_cli_box_mid(freak_word content, int64_t width) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), BOX_V), C_RESET), freak_word_lit(" ")), content);
}
freak_word freak_cli_box_sep(int64_t width) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), BOX_VR), freak_cli_box_line(width)), BOX_VL), C_RESET);
}
freak_word freak_cli_random_quote(int64_t seed) {
int64_t idx = (seed % 12);
if ((idx == 0)) {
return freak_word_lit("\"This is the choice of Steins;Gate.\"");
}
if ((idx == 1)) {
return freak_word_lit("\"People die when they are killed.\"");
}
if ((idx == 2)) {
return freak_word_lit("\"You can't change the past, but you can change the future.\"");
}
if ((idx == 3)) {
return freak_word_lit("\"The only ones who should kill are those prepared to be killed.\"");
}
if ((idx == 4)) {
return freak_word_lit("\"If you don't take risks, you can't create a future.\"");
}
if ((idx == 5)) {
return freak_word_lit("\"A lesson without pain is meaningless.\"");
}
if ((idx == 6)) {
return freak_word_lit("\"It was always going to end this way.\"");
}
if ((idx == 7)) {
return freak_word_lit("\"I am the bone of my sword.\"");
}
if ((idx == 8)) {
return freak_word_lit("\"Believe in the me that believes in you!\"");
}
if ((idx == 9)) {
return freak_word_lit("\"There is no way to take back a move once played.\"");
}
if ((idx == 10)) {
return freak_word_lit("\"The world is not beautiful; and that is why it is beautiful.\"");
}
return freak_word_lit("\"Even if I die, I can be replaced.\" -- Rei Ayanami");
}
freak_word freak_cli_fail_quote(int64_t seed) {
int64_t idx = (seed % 8);
if ((idx == 0)) {
return freak_word_lit("\"I mustn't run away. I mustn't run away.\"");
}
if ((idx == 1)) {
return freak_word_lit("\"How many times must I tell you? This is reality.\"");
}
if ((idx == 2)) {
return freak_word_lit("\"Omae wa mou shindeiru.\"");
}
if ((idx == 3)) {
return freak_word_lit("\"You thought it would compile? Too bad, it was me, Dio!\"");
}
if ((idx == 4)) {
return freak_word_lit("\"This pain... it's still not enough.\"");
}
if ((idx == 5)) {
return freak_word_lit("\"The cruelest thing is a held-out hope.\"");
}
if ((idx == 6)) {
return freak_word_lit("\"No one can escape the fate chosen for them.\"");
}
return freak_word_lit("\"I'll accept any curse. I don't care.\" -- Homura");
}
void freak_cli_show_version(void) {
freak_word ver = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_G1, freak_word_lit("freak")), C_RESET), freak_word_lit(" ")), C_BWHITE), CLI_VERSION), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("(")), CLI_CODENAME), freak_word_lit(")")), C_RESET);
freak_say(ver);
}
void freak_cli_show_banner(void) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G2), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97 ")), C_G3), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G4), freak_word_lit(" \xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97 ")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97  ")), C_G6), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d")), C_G2), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G3), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d")), C_G4), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91 ")), C_G6), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x9d")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97  ")), C_G2), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x9d")), C_G3), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97  ")), C_G4), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x9d ")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G2), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d  ")), C_G3), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G4), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d  ")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x95\x90\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x94\xe2\x95\x90\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G3), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91     ")), C_G4), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91  \xe2\x96\x88\xe2\x96\x88\xe2\x95\x91")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_G5), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91  \xe2\x96\x88\xe2\x96\x88\xe2\x95\x91")), C_G6), freak_word_lit("\xe2\x96\x88\xe2\x96\x88\xe2\x95\x91  \xe2\x96\x88\xe2\x96\x88\xe2\x95\x97")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G4), freak_word_lit("\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d     ")), C_G5), freak_word_lit("\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d  \xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d")), C_G5), freak_word_lit("\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d")), C_G5), freak_word_lit("\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d  \xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d")), C_G6), freak_word_lit("\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d  \xe2\x95\x9a\xe2\x95\x90\xe2\x95\x9d")), C_RESET));
freak_say(freak_word_lit(""));
freak_word tag = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("v")), CLI_VERSION), C_RESET), freak_word_lit(" ")), C_G1), CLI_CODENAME), C_RESET), C_DIM), freak_word_lit(" ")), BOX_V), freak_word_lit(" self-hosting compiler ")), BOX_V), freak_word_lit(" LLVM backend")), C_RESET);
freak_say(tag);
freak_say(freak_word_lit(""));
}
void freak_cli_show_help(void) {
freak_cli_show_banner();
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(C_BWHITE, freak_word_lit(" COMMANDS")), C_RESET), 45));
freak_say(freak_cli_box_sep(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("build")), C_RESET), freak_word_lit("     <file.fk> [opts]  ")), C_DIM), freak_word_lit("Compile to binary")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G2), freak_word_lit("run")), C_RESET), freak_word_lit("       <file.fk> [opts]  ")), C_DIM), freak_word_lit("Build & execute")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G3), freak_word_lit("check")), C_RESET), freak_word_lit("     <file.fk>         ")), C_DIM), freak_word_lit("Type-check only")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G4), freak_word_lit("transpile")), C_RESET), freak_word_lit(" <file.fk> [opts]  ")), C_DIM), freak_word_lit("Emit .c or .ll")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G5), freak_word_lit("hangar")), C_RESET), freak_word_lit("    <cmd>              ")), C_DIM), freak_word_lit("Package manager")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G6), freak_word_lit("doctor")), C_RESET), freak_word_lit("    [--fix]              ")), C_DIM), freak_word_lit("Check setup, auto-fix")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("learn")), C_RESET), freak_word_lit("     [cmd]              ")), C_DIM), freak_word_lit("FREAK Academy")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("test")), C_RESET), freak_word_lit("                          ")), C_DIM), freak_word_lit("Run regression suite")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G2), freak_word_lit("audit-*")), C_RESET), freak_word_lit("                       ")), C_DIM), freak_word_lit("audit-conformance/science/trust/miracles")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), freak_word_lit("upgrade")), C_RESET), freak_word_lit("                      ")), C_DIM), freak_word_lit("Download latest FREAK")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BCYAN), freak_word_lit("version")), C_RESET), freak_word_lit("                      ")), C_DIM), freak_word_lit("Show version")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BCYAN), freak_word_lit("help")), C_RESET), freak_word_lit("                         ")), C_DIM), freak_word_lit("This screen")), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(C_BWHITE, freak_word_lit(" OPTIONS")), C_RESET), 45));
freak_say(freak_cli_box_sep(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("--llvm")), C_RESET), freak_word_lit("            ")), C_DIM), freak_word_lit("LLVM IR backend (default)")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("--c")), C_RESET), freak_word_lit("               ")), C_DIM), freak_word_lit("C backend")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("--opt=N")), C_RESET), freak_word_lit("           ")), C_DIM), freak_word_lit("Optimization 0-3 (default: 2)")), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("--target=TRIPLE")), C_RESET), freak_word_lit("   ")), C_DIM), freak_word_lit("Cross-compile target")), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("EXAMPLES")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("  $ ")), C_RESET), C_BWHITE), freak_word_lit("freak build")), C_RESET), freak_word_lit(" hello.fk")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("  $ ")), C_RESET), C_BWHITE), freak_word_lit("freak run")), C_RESET), freak_word_lit(" hello.fk ")), C_BYELLOW), freak_word_lit("--c --opt=3")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("  $ ")), C_RESET), C_BWHITE), freak_word_lit("freak build")), C_RESET), freak_word_lit(" game.fk ")), C_BYELLOW), freak_word_lit("--target=x86_64-linux-gnu")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("  $ ")), C_RESET), C_BWHITE), freak_word_lit("freak hangar")), C_RESET), freak_word_lit(" init my-project")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("  $ ")), C_RESET), C_BWHITE), freak_word_lit("freak learn")), C_RESET), freak_word_lit(" list")));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_cli_random_quote(42)), C_RESET));
freak_say(freak_word_lit(""));
}
void freak_toml_clear(void) {
toml_keys_arr = freak_array_new();
toml_vals_arr = freak_array_new();
toml_count = 0;
}
void freak_toml_set(freak_word key, freak_word val) {
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
if (freak_word_eq(k, key)) {
freak_array_set(toml_vals_arr, i, val);
return ;
}
i += 1;
}
freak_array_push(toml_keys_arr, key);
freak_array_push(toml_vals_arr, val);
toml_count += 1;
}
freak_word freak_toml_get(freak_word key) {
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
if (freak_word_eq(k, key)) {
return freak_array_get(toml_vals_arr, i);
}
i += 1;
}
return freak_word_lit("");
}
bool freak_toml_has(freak_word key) {
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
if (freak_word_eq(k, key)) {
return true;
}
i += 1;
}
return false;
}
void freak_toml_remove_prefix(freak_word prefix) {
int64_t new_keys = freak_array_new();
int64_t new_vals = freak_array_new();
int64_t new_count = 0;
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
freak_word v = freak_array_get(toml_vals_arr, i);
if ((freak_word_starts_with(k, prefix) == false)) {
freak_array_push(new_keys, k);
freak_array_push(new_vals, v);
new_count += 1;
}
i += 1;
}
toml_keys_arr = new_keys;
toml_vals_arr = new_vals;
toml_count = new_count;
}
freak_word freak_toml_get_line(freak_word content, int64_t start) {
freak_word line = freak_word_lit("");
int64_t i = start;
int64_t clen = freak_word_length(content);
while (!((i >= clen))) {
freak_word c = freak_word_char_at(content, i);
if (freak_word_eq(c, freak_word_lit("\n"))) {
return line;
}
line = freak_word_concat(line, c);
i += 1;
}
return line;
}
int64_t freak_toml_line_end(freak_word content, int64_t start) {
int64_t i = start;
int64_t clen = freak_word_length(content);
while (!((i >= clen))) {
freak_word c = freak_word_char_at(content, i);
i += 1;
if (freak_word_eq(c, freak_word_lit("\n"))) {
return i;
}
}
return clen;
}
freak_word freak_toml_trim(freak_word s) {
return freak_word_trim(s);
}
void freak_toml_parse(freak_word content) {
freak_toml_clear();
freak_word section = freak_word_lit("");
int64_t pos = 0;
int64_t clen = freak_word_length(content);
while (!((pos >= clen))) {
freak_word line = freak_toml_get_line(content, pos);
pos = freak_toml_line_end(content, pos);
freak_word trimmed = freak_toml_trim(line);
if (freak_word_eq(trimmed, freak_word_lit(""))) {
}
else {
if (freak_word_starts_with(trimmed, freak_word_lit("#"))) {
}
else {
if (freak_word_starts_with(trimmed, freak_word_lit("["))) {
section = freak_toml_extract_section(trimmed);
}
else {
if (freak_word_contains(trimmed, freak_word_lit("="))) {
freak_toml_parse_kv(trimmed, section);
}
}
}
}
}
}
freak_word freak_toml_extract_section(freak_word line) {
freak_word name = freak_word_lit("");
int64_t i = 1;
int64_t llen = freak_word_length(line);
while (!((i >= llen))) {
freak_word c = freak_word_char_at(line, i);
if (freak_word_eq(c, freak_word_lit("]"))) {
return name;
}
if ((!freak_word_eq(c, freak_word_lit(" ")))) {
name = freak_word_concat(name, c);
}
i += 1;
}
return name;
}
void freak_toml_parse_kv(freak_word line, freak_word section) {
int64_t eq_pos = (0 - 1);
int64_t i = 0;
int64_t llen = freak_word_length(line);
bool in_quotes = false;
while (!((i >= llen))) {
freak_word c = freak_word_char_at(line, i);
if (freak_word_eq(c, freak_word_lit("\""))) {
in_quotes = (in_quotes == false);
}
if (((freak_word_eq(c, freak_word_lit("=")) && (in_quotes == false)) && (eq_pos < 0))) {
eq_pos = i;
}
i += 1;
}
if ((eq_pos < 0)) {
return ;
}
freak_word raw_key = freak_word_lit("");
int64_t ki = 0;
while (!((ki >= eq_pos))) {
freak_word kc = freak_word_char_at(line, ki);
if (((!freak_word_eq(kc, freak_word_lit(" "))) && (!freak_word_eq(kc, freak_word_lit("\t"))))) {
raw_key = freak_word_concat(raw_key, kc);
}
ki += 1;
}
freak_word raw_val = freak_word_lit("");
int64_t vi = (eq_pos + 1);
while (!((vi >= llen))) {
raw_val = freak_word_concat(raw_val, freak_word_char_at(line, vi));
vi += 1;
}
raw_val = freak_toml_trim(raw_val);
freak_word full_key = freak_word_lit("");
if ((!freak_word_eq(section, freak_word_lit("")))) {
full_key = freak_word_concat(freak_word_concat(section, freak_word_lit(".")), raw_key);
}
else {
full_key = raw_key;
}
if (freak_word_starts_with(raw_val, freak_word_lit("\""))) {
freak_word str_val = freak_toml_unquote(raw_val);
if (freak_word_eq(section, freak_word_lit("dependencies"))) {
freak_toml_set(freak_word_concat(full_key, freak_word_lit(".version")), str_val);
}
else {
freak_toml_set(full_key, str_val);
}
}
else {
if (freak_word_starts_with(raw_val, freak_word_lit("{"))) {
freak_toml_parse_inline_table(raw_val, full_key);
}
else {
freak_toml_set(full_key, raw_val);
}
}
}
freak_word freak_toml_unquote(freak_word s) {
int64_t slen = freak_word_length(s);
if ((slen < 2)) {
return s;
}
freak_word out = freak_word_lit("");
int64_t i = 1;
int64_t end_pos = (slen - 1);
while (!((i >= end_pos))) {
out = freak_word_concat(out, freak_word_char_at(s, i));
i += 1;
}
return out;
}
void freak_toml_parse_inline_table(freak_word s, freak_word prefix) {
freak_word inner = freak_word_lit("");
int64_t i = 1;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
freak_word c = freak_word_char_at(s, i);
if (freak_word_eq(c, freak_word_lit("}"))) {
i = slen;
}
if ((!freak_word_eq(c, freak_word_lit("}")))) {
inner = freak_word_concat(inner, c);
}
i += 1;
}
freak_word pair = freak_word_lit("");
int64_t pi = 0;
int64_t ilen = freak_word_length(inner);
while (!((pi >= ilen))) {
freak_word pc = freak_word_char_at(inner, pi);
if (freak_word_eq(pc, freak_word_lit(","))) {
freak_toml_parse_inline_pair(pair, prefix);
pair = freak_word_lit("");
}
else {
pair = freak_word_concat(pair, pc);
}
pi += 1;
}
if ((!freak_word_eq(pair, freak_word_lit("")))) {
freak_toml_parse_inline_pair(pair, prefix);
}
}
void freak_toml_parse_inline_pair(freak_word pair, freak_word prefix) {
freak_word trimmed = freak_toml_trim(pair);
if (freak_word_eq(trimmed, freak_word_lit(""))) {
return ;
}
int64_t eq = (0 - 1);
int64_t i = 0;
int64_t plen = freak_word_length(trimmed);
while (!((i >= plen))) {
freak_word c = freak_word_char_at(trimmed, i);
if ((freak_word_eq(c, freak_word_lit("=")) && (eq < 0))) {
eq = i;
}
i += 1;
}
if ((eq < 0)) {
return ;
}
freak_word subkey = freak_word_lit("");
int64_t ki = 0;
while (!((ki >= eq))) {
freak_word kc = freak_word_char_at(trimmed, ki);
if (((!freak_word_eq(kc, freak_word_lit(" "))) && (!freak_word_eq(kc, freak_word_lit("\t"))))) {
subkey = freak_word_concat(subkey, kc);
}
ki += 1;
}
freak_word raw_val = freak_word_lit("");
int64_t vi = (eq + 1);
while (!((vi >= plen))) {
raw_val = freak_word_concat(raw_val, freak_word_char_at(trimmed, vi));
vi += 1;
}
raw_val = freak_toml_trim(raw_val);
freak_word full_key = freak_word_concat(freak_word_concat(prefix, freak_word_lit(".")), subkey);
if (freak_word_starts_with(raw_val, freak_word_lit("\""))) {
freak_word uv = freak_toml_unquote(raw_val);
freak_toml_set(full_key, uv);
}
else {
freak_toml_set(full_key, raw_val);
}
}
void freak_toml_write_file(freak_word path) {
freak_word out = freak_word_lit("");
if ((freak_toml_has(freak_word_lit("project.name")) || freak_toml_has(freak_word_lit("project.version")))) {
out = freak_word_concat(out, freak_word_lit("[project]\n"));
freak_word pname = freak_toml_get(freak_word_lit("project.name"));
if ((!freak_word_eq(pname, freak_word_lit("")))) {
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("name = \"")), pname), freak_word_lit("\"\n"));
}
freak_word pver = freak_toml_get(freak_word_lit("project.version"));
if ((!freak_word_eq(pver, freak_word_lit("")))) {
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("version = \"")), pver), freak_word_lit("\"\n"));
}
out = freak_word_concat(out, freak_word_lit("\n"));
}
int64_t dep_names = freak_array_new();
int64_t dep_names_count = 0;
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
if (freak_word_starts_with(k, freak_word_lit("dependencies."))) {
freak_word dname = freak_toml_extract_dep_name(k);
if ((!freak_word_eq(dname, freak_word_lit("")))) {
if ((freak_toml_arr_contains(dep_names, dep_names_count, dname) == false)) {
freak_array_push(dep_names, dname);
dep_names_count += 1;
}
}
}
i += 1;
}
if ((dep_names_count > 0)) {
out = freak_word_concat(out, freak_word_lit("[dependencies]\n"));
int64_t di = 0;
while (!((di >= dep_names_count))) {
freak_word dn = freak_array_get(dep_names, di);
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dn), freak_word_lit(".git"));
freak_word ver_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dn), freak_word_lit(".version"));
freak_word git_val = freak_toml_get(git_key);
freak_word ver_val = freak_toml_get(ver_key);
if ((freak_word_eq(git_val, freak_word_lit("")) && (!freak_word_eq(ver_val, freak_word_lit(""))))) {
freak_word ln_short = freak_word_concat(freak_word_concat(freak_word_concat(dn, freak_word_lit(" = \"")), ver_val), freak_word_lit("\"\n"));
out = freak_word_concat(out, ln_short);
}
else {
freak_word ln = freak_word_concat(dn, freak_word_lit(" = { "));
bool has_f = false;
if ((!freak_word_eq(git_val, freak_word_lit("")))) {
ln = freak_word_concat(freak_word_concat(freak_word_concat(ln, freak_word_lit("git = \"")), git_val), freak_word_lit("\""));
has_f = true;
}
if ((!freak_word_eq(ver_val, freak_word_lit("")))) {
if (has_f) {
ln = freak_word_concat(ln, freak_word_lit(", "));
}
ln = freak_word_concat(freak_word_concat(freak_word_concat(ln, freak_word_lit("version = \"")), ver_val), freak_word_lit("\""));
}
ln = freak_word_concat(ln, freak_word_lit(" }\n"));
out = freak_word_concat(out, ln);
}
di += 1;
}
out = freak_word_concat(out, freak_word_lit("\n"));
}
freak_fs_write(path, out);
}
freak_word freak_toml_extract_dep_name(freak_word key) {
int64_t prefix_len = 13;
freak_word rest = freak_word_lit("");
int64_t i = prefix_len;
int64_t klen = freak_word_length(key);
while (!((i >= klen))) {
freak_word c = freak_word_char_at(key, i);
if (freak_word_eq(c, freak_word_lit("."))) {
return rest;
}
rest = freak_word_concat(rest, c);
i += 1;
}
return rest;
}
bool freak_toml_arr_contains(int64_t arr, int64_t count, freak_word item) {
int64_t i = 0;
while (!((i >= count))) {
freak_word v = freak_array_get(arr, i);
if (freak_word_eq(v, item)) {
return true;
}
i += 1;
}
return false;
}
freak_word freak_toml_dep_get_version(freak_word dep_name) {
freak_word ver_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dep_name), freak_word_lit(".version"));
return freak_toml_get(ver_key);
}
freak_word freak_toml_dep_get_git(freak_word dep_name) {
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dep_name), freak_word_lit(".git"));
return freak_toml_get(git_key);
}
bool freak_toml_dep_is_short_syntax(freak_word dep_name) {
freak_word git_val = freak_toml_dep_get_git(dep_name);
freak_word ver_val = freak_toml_dep_get_version(dep_name);
return (freak_word_eq(git_val, freak_word_lit("")) && (!freak_word_eq(ver_val, freak_word_lit(""))));
}
void freak_toml_load(freak_word path) {
freak_word content = freak_fs_read(path);
freak_toml_parse(content);
}
int64_t freak_toml_dep_names_arr(void) {
int64_t deps = freak_array_new();
int64_t i = 0;
while (!((i >= toml_count))) {
freak_word k = freak_array_get(toml_keys_arr, i);
if (freak_word_starts_with(k, freak_word_lit("dependencies."))) {
freak_word dn = freak_toml_extract_dep_name(k);
if ((!freak_word_eq(dn, freak_word_lit("")))) {
if ((freak_toml_arr_contains(deps, freak_array_len(deps), dn) == false)) {
freak_array_push(deps, dn);
}
}
}
i += 1;
}
return deps;
}
int64_t freak_toml_dep_count(void) {
int64_t deps = freak_toml_dep_names_arr();
return freak_array_len(deps);
}
void freak_lock_clear(void) {
lock_pkg_names = freak_array_new();
lock_pkg_versions = freak_array_new();
lock_pkg_sources = freak_array_new();
lock_pkg_sha256s = freak_array_new();
lock_pkg_count = 0;
}
void freak_lock_add_entry(freak_word name, freak_word version, freak_word source, freak_word sha256) {
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word existing = freak_array_get(lock_pkg_names, i);
if (freak_word_eq(existing, name)) {
freak_array_set(lock_pkg_versions, i, version);
freak_array_set(lock_pkg_sources, i, source);
freak_array_set(lock_pkg_sha256s, i, sha256);
return ;
}
i += 1;
}
freak_array_push(lock_pkg_names, name);
freak_array_push(lock_pkg_versions, version);
freak_array_push(lock_pkg_sources, source);
freak_array_push(lock_pkg_sha256s, sha256);
lock_pkg_count += 1;
}
void freak_lock_remove_entry(freak_word name) {
int64_t new_names = freak_array_new();
int64_t new_versions = freak_array_new();
int64_t new_sources = freak_array_new();
int64_t new_sha256s = freak_array_new();
int64_t new_count = 0;
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word n = freak_array_get(lock_pkg_names, i);
if ((!freak_word_eq(n, name))) {
freak_array_push(new_names, freak_array_get(lock_pkg_names, i));
freak_array_push(new_versions, freak_array_get(lock_pkg_versions, i));
freak_array_push(new_sources, freak_array_get(lock_pkg_sources, i));
freak_array_push(new_sha256s, freak_array_get(lock_pkg_sha256s, i));
new_count += 1;
}
i += 1;
}
lock_pkg_names = new_names;
lock_pkg_versions = new_versions;
lock_pkg_sources = new_sources;
lock_pkg_sha256s = new_sha256s;
lock_pkg_count = new_count;
}
freak_word freak_lock_get_version(freak_word name) {
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word n = freak_array_get(lock_pkg_names, i);
if (freak_word_eq(n, name)) {
return freak_array_get(lock_pkg_versions, i);
}
i += 1;
}
return freak_word_lit("");
}
freak_word freak_lock_get_source(freak_word name) {
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word n = freak_array_get(lock_pkg_names, i);
if (freak_word_eq(n, name)) {
return freak_array_get(lock_pkg_sources, i);
}
i += 1;
}
return freak_word_lit("");
}
bool freak_lock_has(freak_word name) {
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word n = freak_array_get(lock_pkg_names, i);
if (freak_word_eq(n, name)) {
return true;
}
i += 1;
}
return false;
}
void freak_lock_write(freak_word path) {
freak_word out = freak_word_lit("# This file is auto-generated by Hangar. Do not edit manually.\n");
out = freak_word_concat(out, freak_word_lit("# Commit this file to version control for reproducible builds.\n\n"));
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word name = freak_array_get(lock_pkg_names, i);
freak_word version = freak_array_get(lock_pkg_versions, i);
freak_word source = freak_array_get(lock_pkg_sources, i);
freak_word sha256 = freak_array_get(lock_pkg_sha256s, i);
out = freak_word_concat(out, freak_word_lit("[[package]]\n"));
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("name    = \"")), name), freak_word_lit("\"\n"));
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("version = \"")), version), freak_word_lit("\"\n"));
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("source  = \"")), source), freak_word_lit("\"\n"));
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("sha256  = \"")), sha256), freak_word_lit("\"\n"));
out = freak_word_concat(out, freak_word_lit("\n"));
i += 1;
}
freak_fs_write(path, out);
}
void freak_lock_parse(freak_word content) {
freak_lock_clear();
int64_t pos = 0;
int64_t clen = freak_word_length(content);
freak_word cur_name = freak_word_lit("");
freak_word cur_version = freak_word_lit("");
freak_word cur_source = freak_word_lit("");
freak_word cur_sha256 = freak_word_lit("");
bool in_package = false;
while (!((pos >= clen))) {
freak_word line = freak_toml_get_line(content, pos);
pos = freak_toml_line_end(content, pos);
freak_word trimmed = freak_word_trim(line);
if (freak_word_eq(trimmed, freak_word_lit(""))) {
if ((in_package && (!freak_word_eq(cur_name, freak_word_lit(""))))) {
freak_lock_add_entry(cur_name, cur_version, cur_source, cur_sha256);
cur_name = freak_word_lit("");
cur_version = freak_word_lit("");
cur_source = freak_word_lit("");
cur_sha256 = freak_word_lit("");
in_package = false;
}
}
else {
if (freak_word_starts_with(trimmed, freak_word_lit("#"))) {
}
else {
if (freak_word_eq(trimmed, freak_word_lit("[[package]]"))) {
if ((in_package && (!freak_word_eq(cur_name, freak_word_lit(""))))) {
freak_lock_add_entry(cur_name, cur_version, cur_source, cur_sha256);
}
cur_name = freak_word_lit("");
cur_version = freak_word_lit("");
cur_source = freak_word_lit("");
cur_sha256 = freak_word_lit("");
in_package = true;
}
else {
if ((in_package && freak_word_contains(trimmed, freak_word_lit("=")))) {
freak_word kv_key = freak_lock_parse_key(trimmed);
freak_word kv_val = freak_lock_parse_val(trimmed);
if (freak_word_eq(kv_key, freak_word_lit("name"))) {
cur_name = kv_val;
}
else {
if (freak_word_eq(kv_key, freak_word_lit("version"))) {
cur_version = kv_val;
}
else {
if (freak_word_eq(kv_key, freak_word_lit("source"))) {
cur_source = kv_val;
}
else {
if (freak_word_eq(kv_key, freak_word_lit("sha256"))) {
cur_sha256 = kv_val;
}
}
}
}
}
}
}
}
}
if ((in_package && (!freak_word_eq(cur_name, freak_word_lit(""))))) {
freak_lock_add_entry(cur_name, cur_version, cur_source, cur_sha256);
}
}
freak_word freak_lock_parse_key(freak_word line) {
freak_word key = freak_word_lit("");
int64_t i = 0;
int64_t llen = freak_word_length(line);
while (!((i >= llen))) {
freak_word c = freak_word_char_at(line, i);
if (((freak_word_eq(c, freak_word_lit(" ")) || freak_word_eq(c, freak_word_lit("\t"))) || freak_word_eq(c, freak_word_lit("=")))) {
if ((!freak_word_eq(key, freak_word_lit("")))) {
return key;
}
}
else {
key = freak_word_concat(key, c);
}
i += 1;
}
return key;
}
freak_word freak_lock_parse_val(freak_word line) {
bool found_eq = false;
int64_t i = 0;
int64_t llen = freak_word_length(line);
while (!((i >= llen))) {
freak_word c = freak_word_char_at(line, i);
if (freak_word_eq(c, freak_word_lit("="))) {
found_eq = true;
}
else {
if ((found_eq && freak_word_eq(c, freak_word_lit("\"")))) {
freak_word val = freak_word_lit("");
i += 1;
while (!((i >= llen))) {
freak_word vc = freak_word_char_at(line, i);
if (freak_word_eq(vc, freak_word_lit("\""))) {
return val;
}
val = freak_word_concat(val, vc);
i += 1;
}
return val;
}
}
i += 1;
}
return freak_word_lit("");
}
freak_word freak_lock_get_sha256(freak_word name) {
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word n = freak_array_get(lock_pkg_names, i);
if (freak_word_eq(n, name)) {
return freak_array_get(lock_pkg_sha256s, i);
}
i += 1;
}
return freak_word_lit("");
}
bool freak_lock_load(freak_word path) {
if ((freak_fs_exists(path) == false)) {
return false;
}
freak_word content = freak_fs_read(path);
if (freak_word_eq(content, freak_word_lit(""))) {
return false;
}
freak_lock_parse(content);
return true;
}
void freak_cli_step_start(void) {
cli_step_ms = freak_time_now_ms();
}
void freak_cli_step_done(freak_word label) {
int64_t elapsed = (freak_time_now_ms() - cli_step_ms);
freak_word elapsed_str = freak_word_from_int(elapsed);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit("  ")), label), C_DIM), freak_word_lit(" (")), elapsed_str), freak_word_lit("ms)")), C_RESET));
}
int64_t freak_cli_count_lines(freak_word s) {
if (freak_word_eq(s, freak_word_lit(""))) {
return 0;
}
int64_t count = 1;
int64_t i = 0;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
if (freak_word_eq(freak_word_char_at(s, i), freak_word_lit("\n"))) {
count += 1;
}
i += 1;
}
return count;
}
freak_word freak_cli_strip_resolved_use_lines(freak_word source) {
freak_word out = freak_word_lit("");
freak_word line = freak_word_lit("");
int64_t i = 0;
int64_t slen = freak_word_length(source);
bool in_use_block = false;
while (!((i >= slen))) {
freak_word ch = freak_word_char_at(source, i);
if (freak_word_eq(ch, freak_word_lit("\n"))) {
freak_word trimmed = freak_word_trim(line);
if (in_use_block) {
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("-- [resolved cont] ")), trimmed), freak_word_lit("\n"));
if (freak_word_contains(trimmed, freak_word_lit("}"))) {
in_use_block = false;
}
}
else {
if (freak_word_starts_with(trimmed, freak_word_lit("use "))) {
out = freak_word_concat(freak_word_concat(freak_word_concat(out, freak_word_lit("-- [resolved] ")), trimmed), freak_word_lit("\n"));
if ((freak_word_contains(trimmed, freak_word_lit("{")) && (!freak_word_contains(trimmed, freak_word_lit("}"))))) {
in_use_block = true;
}
}
else {
out = freak_word_concat(freak_word_concat(out, line), freak_word_lit("\n"));
}
}
line = freak_word_lit("");
}
else {
if ((!freak_word_eq(ch, freak_word_lit("\r")))) {
line = freak_word_concat(line, ch);
}
}
i += 1;
}
if ((!freak_word_eq(line, freak_word_lit("")))) {
freak_word trimmed_last = freak_word_trim(line);
if ((in_use_block || freak_word_starts_with(trimmed_last, freak_word_lit("use ")))) {
out = freak_word_concat(freak_word_concat(out, freak_word_lit("-- [resolved] ")), trimmed_last);
}
else {
out = freak_word_concat(out, line);
}
}
return out;
}
freak_word freak_cli_transpile(freak_word src_file, freak_word source, freak_word target) {
input_file = src_file;
freak_init_arrays();
freak_cli_step_start();
freak_tokenize(source);
freak_adjust_token_lines(source_line_offset);
freak_cli_step_done(freak_word_lit("Lexing"));
freak_cli_step_start();
freak_parse_program();
freak_cli_step_done(freak_word_lit("Parsing"));
freak_cli_step_start();
freak_check_program();
if (strict_borrow) {
freak_cli_step_done(freak_word_lit("Borrow checking"));
if ((error_count > 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ")), freak_word_from_int(error_count)), freak_word_lit(" borrow-check error(s)")), C_RESET));
return freak_word_lit("");
}
}
else {
freak_cli_step_done(freak_word_lit("Type checking"));
}
freak_cli_step_start();
if (freak_word_eq(target, freak_word_lit("llvm"))) {
freak_word out_ll = freak_word_concat(src_file, freak_word_lit(".ll"));
out_file = out_ll;
freak_fs_write(out_ll, freak_word_lit(""));
freak_emit_llvm_program();
out_file = freak_word_lit("");
freak_cli_step_done(freak_word_lit("Emit LLVM IR"));
return out_ll;
}
else {
freak_word out_c = freak_word_concat(src_file, freak_word_lit(".c"));
out_file = out_c;
freak_fs_write(out_c, freak_word_lit(""));
freak_emit_c_program();
out_file = freak_word_lit("");
freak_cli_step_done(freak_word_lit("Emit C"));
return out_c;
}
}
bool freak_cli_has_runtime(freak_word dir) {
freak_word c_path = freak_word_concat(dir, freak_word_lit("/freak_runtime.c"));
freak_word o_path = freak_word_concat(dir, freak_word_lit("/freak_runtime.o"));
if (freak_fs_exists(c_path)) {
return true;
}
if (freak_fs_exists(o_path)) {
return true;
}
return false;
}
freak_word freak_cli_find_runtime_dir(void) {
if (freak_cli_has_runtime(freak_word_lit("freakc/runtime"))) {
return freak_word_lit("freakc/runtime");
}
freak_word home_dir = freak_process_env(freak_word_lit("HOME"));
if ((!freak_word_eq(home_dir, freak_word_lit("")))) {
freak_word home_rt = freak_word_concat(home_dir, freak_word_lit("/.freak/runtime"));
if (freak_cli_has_runtime(home_rt)) {
return home_rt;
}
}
freak_word appdata_dir = freak_process_env(freak_word_lit("APPDATA"));
if ((!freak_word_eq(appdata_dir, freak_word_lit("")))) {
freak_word appdata_rt = freak_word_concat(appdata_dir, freak_word_lit("/freak/runtime"));
if (freak_cli_has_runtime(appdata_rt)) {
return appdata_rt;
}
}
freak_word freak_home = freak_process_env(freak_word_lit("FREAK_HOME"));
if ((!freak_word_eq(freak_home, freak_word_lit("")))) {
freak_word fh_rt = freak_word_concat(freak_home, freak_word_lit("/runtime"));
if (freak_cli_has_runtime(fh_rt)) {
return fh_rt;
}
}
if (freak_fs_exists(freak_word_lit("freak_runtime.c"))) {
return freak_word_lit(".");
}
if (freak_fs_exists(freak_word_lit("freak_runtime.o"))) {
return freak_word_lit(".");
}
return freak_word_lit("");
}
freak_word freak_cli_strip_fk(freak_word path) {
if (freak_word_ends_with(path, freak_word_lit(".fk"))) {
int64_t oi = 0;
freak_word oname = freak_word_lit("");
int64_t olen = (freak_word_length(path) - 3);
while (!((oi >= olen))) {
oname = freak_word_concat(oname, freak_word_char_at(path, oi));
oi += 1;
}
return oname;
}
return path;
}
bool freak_cli_is_windows(void) {
freak_word windir = freak_process_env(freak_word_lit("WINDIR"));
if ((!freak_word_eq(windir, freak_word_lit("")))) {
return true;
}
return false;
}
bool freak_cli_has_precompiled_runtime(freak_word runtime_dir) {
freak_word rt_obj = freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.obj"));
freak_word llvm_obj = freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime.obj"));
if (freak_fs_exists(rt_obj)) {
if (freak_fs_exists(llvm_obj)) {
return true;
}
}
freak_word rt_o = freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.o"));
freak_word llvm_o = freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime.o"));
if (freak_fs_exists(rt_o)) {
if (freak_fs_exists(llvm_o)) {
return true;
}
}
return false;
}
freak_word freak_cli_build_binary(freak_word transpiled_file, freak_word src_file, freak_word target, freak_word opt, freak_word cross) {
freak_word runtime_dir = freak_cli_find_runtime_dir();
if (freak_word_eq(runtime_dir, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  RUNTIME NOT FOUND")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  The runtime is needed to compile FREAK programs.")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Searched in:")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    freakc/runtime/           "), C_DIM), freak_word_lit("(dev/repo)")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    ~/.freak/runtime/         "), C_DIM), freak_word_lit("(install.sh)")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    %APPDATA%\\freak\\runtime\\  "), C_DIM), freak_word_lit("(install.ps1)")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    $FREAK_HOME/runtime/      "), C_DIM), freak_word_lit("(custom)")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Fix: Re-run the install script, or run '")), C_RESET), freak_word_lit("freak doctor")), C_DIM), freak_word_lit("'.")), C_RESET));
return freak_word_lit("");
}
freak_word out_bin = freak_cli_strip_fk(src_file);
if (freak_cli_is_windows()) {
out_bin = freak_word_concat(out_bin, freak_word_lit(".exe"));
}
int64_t is_win = freak_cli_is_windows();
bool use_bundle = false;
if (freak_word_eq(target, freak_word_lit("llvm"))) {
if ((freak_cli_has_precompiled_runtime(runtime_dir) && (!is_win))) {
use_bundle = true;
}
}
if (use_bundle) {
freak_word obj_ext = freak_word_lit(".obj");
if ((!is_win)) {
obj_ext = freak_word_lit(".o");
}
freak_word user_obj = freak_word_concat(freak_cli_strip_fk(src_file), obj_ext);
freak_word cc_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("clang -c -g -o "), user_obj), freak_word_lit(" ")), transpiled_file), freak_word_lit(" -O")), opt), freak_word_lit(" -w"));
if ((!freak_word_eq(cross, freak_word_lit("")))) {
cc_cmd = freak_word_concat(freak_word_concat(cc_cmd, freak_word_lit(" --target=")), cross);
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), SYM_GEAR), freak_word_lit("  Compiling IR...")), C_RESET));
int64_t cc_exit = freak_process_exec(cc_cmd);
if ((cc_exit != 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  MISSION FAILED")), C_RESET), C_RED), freak_word_lit(" -- IR compilation error")), C_RESET));
return freak_word_lit("");
}
freak_word rt_obj = freak_word_concat(freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime")), obj_ext);
freak_word llvm_rt_obj = freak_word_concat(freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime")), obj_ext);
freak_word ui_obj = freak_word_concat(freak_word_concat(runtime_dir, freak_word_lit("/freak_ui_win32")), obj_ext);
if (is_win) {
freak_word link_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("lld-link /FORCE:MULTIPLE "), user_obj), freak_word_lit(" ")), llvm_rt_obj), freak_word_lit(" ")), rt_obj);
if (freak_fs_exists(ui_obj)) {
link_cmd = freak_word_concat(freak_word_concat(link_cmd, freak_word_lit(" ")), ui_obj);
}
link_cmd = freak_word_concat(freak_word_concat(freak_word_concat(link_cmd, freak_word_lit(" /out:")), out_bin), freak_word_lit(" /subsystem:console"));
freak_word pdb_out = freak_word_concat(freak_cli_strip_fk(src_file), freak_word_lit(".pdb"));
link_cmd = freak_word_concat(freak_word_concat(link_cmd, freak_word_lit(" /debug /pdb:")), pdb_out);
link_cmd = freak_word_concat(link_cmd, freak_word_lit(" libcmt.lib user32.lib gdi32.lib msimg32.lib ws2_32.lib"));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), SYM_GEAR), freak_word_lit("  Linking...")), C_RESET));
int64_t link_exit = freak_process_exec(link_cmd);
if ((link_exit != 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  MISSION FAILED")), C_RESET), C_RED), freak_word_lit(" -- link error")), C_RESET));
return freak_word_lit("");
}
}
if ((!is_win)) {
freak_word link_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("ld.lld --allow-multiple-definition -o "), out_bin), freak_word_lit(" ")), user_obj), freak_word_lit(" ")), llvm_rt_obj), freak_word_lit(" ")), rt_obj);
if (freak_fs_exists(ui_obj)) {
link_cmd = freak_word_concat(freak_word_concat(link_cmd, freak_word_lit(" ")), ui_obj);
}
link_cmd = freak_word_concat(link_cmd, freak_word_lit(" -lc -lm"));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), SYM_GEAR), freak_word_lit("  Linking...")), C_RESET));
int64_t link_exit = freak_process_exec(link_cmd);
if ((link_exit != 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  MISSION FAILED")), C_RESET), C_RED), freak_word_lit(" -- link error")), C_RESET));
return freak_word_lit("");
}
}
return out_bin;
}
freak_word runtime_file = freak_word_lit("");
if (freak_word_eq(target, freak_word_lit("llvm"))) {
freak_word llvm_rt_c = freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime.c"));
freak_word rt_c = freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.c"));
runtime_file = freak_word_concat(freak_word_concat(llvm_rt_c, freak_word_lit(" ")), rt_c);
}
else {
runtime_file = freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.c"));
}
freak_word cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("clang -g -o "), out_bin), freak_word_lit(" ")), transpiled_file), freak_word_lit(" ")), runtime_file);
cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(cmd, freak_word_lit(" -I")), runtime_dir), freak_word_lit(" -O")), opt), freak_word_lit(" -w -D_CRT_SECURE_NO_WARNINGS"));
if ((!is_win)) {
cmd = freak_word_concat(cmd, freak_word_lit(" -lm"));
}
if (is_win) {
cmd = freak_word_concat(cmd, freak_word_lit(" -lws2_32"));
}
freak_word ui_c = freak_word_concat(runtime_dir, freak_word_lit("/ui/win32_backend.c"));
if (is_win) {
if (freak_fs_exists(ui_c)) {
cmd = freak_word_concat(freak_word_concat(freak_word_concat(cmd, freak_word_lit(" ")), ui_c), freak_word_lit(" -DFREAK_HAS_UI -luser32 -lgdi32 -lmsimg32"));
}
}
if ((!freak_word_eq(cross, freak_word_lit("")))) {
cmd = freak_word_concat(freak_word_concat(cmd, freak_word_lit(" --target=")), cross);
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), SYM_GEAR), freak_word_lit("  Compiling native binary...")), C_RESET));
int64_t exit_code = freak_process_exec(cmd);
if ((exit_code != 0)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  MISSION FAILED")), C_RESET), C_RED), freak_word_lit(" -- clang compilation error")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Make sure clang is installed and in your PATH:")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    Windows: "), C_CYAN), freak_word_lit("choco install llvm")), C_RESET), freak_word_lit("  or  ")), C_CYAN), freak_word_lit("winget install LLVM.LLVM")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    macOS:   "), C_CYAN), freak_word_lit("xcode-select --install")), C_RESET), freak_word_lit("  or  ")), C_CYAN), freak_word_lit("brew install llvm")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    Linux:   "), C_CYAN), freak_word_lit("sudo apt install clang")), C_RESET), freak_word_lit("  or  ")), C_CYAN), freak_word_lit("sudo dnf install clang")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Run '")), C_RESET), freak_word_lit("freak doctor")), C_DIM), freak_word_lit("' to diagnose your setup.")), C_RESET));
return freak_word_lit("");
}
return out_bin;
}
freak_word freak_cli_find_std_dir(void) {
if (freak_fs_exists(freak_word_lit("std/math.fk"))) {
return freak_word_lit("std");
}
freak_word home_dir = freak_process_env(freak_word_lit("HOME"));
if ((!freak_word_eq(home_dir, freak_word_lit("")))) {
freak_word home_std = freak_word_concat(home_dir, freak_word_lit("/.freak/std"));
if (freak_fs_exists(freak_word_concat(home_std, freak_word_lit("/math.fk")))) {
return home_std;
}
}
freak_word appdata_dir = freak_process_env(freak_word_lit("APPDATA"));
if ((!freak_word_eq(appdata_dir, freak_word_lit("")))) {
freak_word app_std = freak_word_concat(appdata_dir, freak_word_lit("/freak/std"));
if (freak_fs_exists(freak_word_concat(app_std, freak_word_lit("/math.fk")))) {
return app_std;
}
}
freak_word freak_home = freak_process_env(freak_word_lit("FREAK_HOME"));
if ((!freak_word_eq(freak_home, freak_word_lit("")))) {
freak_word fh_std = freak_word_concat(freak_home, freak_word_lit("/std"));
if (freak_fs_exists(freak_word_concat(fh_std, freak_word_lit("/math.fk")))) {
return fh_std;
}
}
return freak_word_lit("");
}
freak_word freak_cli_load_std(freak_word source, freak_word target) {
freak_word std_dir = freak_cli_find_std_dir();
if (freak_word_eq(std_dir, freak_word_lit(""))) {
return freak_word_lit("");
}
freak_word std_src = freak_word_lit("");
freak_word math_path = freak_word_concat(std_dir, freak_word_lit("/math.fk"));
if (freak_fs_exists(math_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(math_path)), freak_word_lit("\n"));
}
freak_word string_path = freak_word_concat(std_dir, freak_word_lit("/string.fk"));
if (freak_fs_exists(string_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(string_path)), freak_word_lit("\n"));
}
freak_word convert_path = freak_word_concat(std_dir, freak_word_lit("/convert.fk"));
if (freak_fs_exists(convert_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(convert_path)), freak_word_lit("\n"));
}
freak_word algo_path = freak_word_concat(std_dir, freak_word_lit("/algorithm.fk"));
if (freak_fs_exists(algo_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(algo_path)), freak_word_lit("\n"));
}
bool need_math3d = false;
if (freak_word_contains(source, freak_word_lit("use std::math3d"))) {
need_math3d = true;
}
if (freak_word_contains(source, freak_word_lit("use std::math3d::{"))) {
need_math3d = true;
}
freak_word math3d_path = freak_word_concat(std_dir, freak_word_lit("/math3d.fk"));
if ((need_math3d && freak_fs_exists(math3d_path))) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(math3d_path)), freak_word_lit("\n"));
}
bool need_zip = false;
if (freak_word_contains(source, freak_word_lit("use std::zip"))) {
need_zip = true;
}
if (freak_word_contains(source, freak_word_lit("use std::zip::{"))) {
need_zip = true;
}
freak_word zip_path = freak_word_concat(std_dir, freak_word_lit("/zip.fk"));
if ((need_zip && freak_fs_exists(zip_path))) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(zip_path)), freak_word_lit("\n"));
}
freak_word json_path = freak_word_concat(std_dir, freak_word_lit("/json.fk"));
if (freak_fs_exists(json_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(json_path)), freak_word_lit("\n"));
}
freak_word version_path = freak_word_concat(std_dir, freak_word_lit("/version.fk"));
if (freak_fs_exists(version_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(version_path)), freak_word_lit("\n"));
}
bool need_ui = false;
if (freak_word_contains(source, freak_word_lit("use std::ui"))) {
need_ui = true;
}
freak_word ui_path = freak_word_concat(std_dir, freak_word_lit("/ui/window.fk"));
if ((need_ui && freak_fs_exists(ui_path))) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(ui_path)), freak_word_lit("\n"));
}
bool need_cockpit = false;
if (freak_word_contains(source, freak_word_lit("use cockpit"))) {
need_cockpit = true;
}
if (need_cockpit) {
freak_word cockpit_root = freak_word_lit("packages/cockpit/src");
if (freak_fs_exists(freak_word_concat(cockpit_root, freak_word_lit("/containers.fk")))) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(freak_word_concat(cockpit_root, freak_word_lit("/containers.fk")))), freak_word_lit("\n"));
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(freak_word_concat(cockpit_root, freak_word_lit("/theme.fk")))), freak_word_lit("\n"));
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(freak_word_concat(cockpit_root, freak_word_lit("/layout.fk")))), freak_word_lit("\n"));
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(freak_word_concat(cockpit_root, freak_word_lit("/widgets.fk")))), freak_word_lit("\n"));
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(freak_word_concat(cockpit_root, freak_word_lit("/ui.fk")))), freak_word_lit("\n"));
}
}
if (freak_word_eq(target, freak_word_lit("llvm"))) {
freak_word http_path = freak_word_concat(std_dir, freak_word_lit("/http.fk"));
if (freak_fs_exists(http_path)) {
std_src = freak_word_concat(freak_word_concat(std_src, freak_fs_read(http_path)), freak_word_lit("\n"));
}
}
if (freak_word_eq(target, freak_word_lit("llvm"))) {
freak_word rt_path = freak_word_concat(std_dir, freak_word_lit("/runtime.fk"));
if (freak_fs_exists(rt_path)) {
std_src = freak_word_concat(freak_word_concat(freak_fs_read(rt_path), freak_word_lit("\n")), std_src);
}
}
return std_src;
}
freak_word freak_cli_build(freak_word src_file, freak_word target, freak_word opt, freak_word cross) {
cli_build_start_ms = freak_time_now_ms();
freak_word source = freak_fs_read(src_file);
if (freak_word_eq(source, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" Could not read file: ")), C_BWHITE), src_file), C_RESET));
return freak_word_lit("");
}
freak_word backend_label = freak_word_lit("LLVM IR");
if (freak_word_eq(target, freak_word_lit("c"))) {
backend_label = freak_word_lit("C");
}
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G1), SYM_BOLT), freak_word_lit(" FREAK")), C_RESET), freak_word_lit("  ")), C_BWHITE), src_file), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_DIM), freak_word_lit("  Backend: ")), C_RESET), C_BCYAN), backend_label), C_RESET), C_DIM), freak_word_lit("  Opt: -O")), opt), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
freak_word std_source = freak_cli_load_std(source, target);
source_line_offset = 0;
if ((!freak_word_eq(std_source, freak_word_lit("")))) {
std_source = freak_cli_strip_resolved_use_lines(std_source);
source_line_offset = freak_cli_count_lines(std_source);
source = freak_cli_strip_resolved_use_lines(source);
source = freak_word_concat(std_source, source);
}
freak_word transpiled = freak_cli_transpile(src_file, source, target);
if (freak_word_eq(transpiled, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_SKULL), freak_word_lit(" BUILD FAILED")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_cli_fail_quote(freak_time_now_ms())), C_RESET));
freak_say(freak_word_lit(""));
return freak_word_lit("");
}
freak_cli_step_start();
freak_word binary = freak_cli_build_binary(transpiled, src_file, target, opt, cross);
if (freak_word_eq(binary, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_SKULL), freak_word_lit(" BUILD FAILED")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_cli_fail_quote(freak_time_now_ms())), C_RESET));
freak_say(freak_word_lit(""));
return freak_word_lit("");
}
freak_cli_step_done(freak_word_lit("Native binary"));
int64_t total_ms = (freak_time_now_ms() - cli_build_start_ms);
freak_word total_str = freak_word_from_int(total_ms);
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_BGREEN), SYM_SPARK), freak_word_lit(" BUILD SUCCESSFUL")), C_RESET), 45));
freak_say(freak_cli_box_sep(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Binary: ")), C_RESET), C_BWHITE), binary), C_RESET), 45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Time:   ")), C_RESET), C_BCYAN), total_str), freak_word_lit("ms")), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_cli_random_quote(total_ms)), C_RESET));
freak_say(freak_word_lit(""));
return binary;
}
void freak_cli_run(freak_word src_file, freak_word target, freak_word opt, freak_word cross) {
freak_word binary = freak_cli_build(src_file, target, opt, cross);
if (freak_word_eq(binary, freak_word_lit(""))) {
return ;
}
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G5), SYM_ARROW), freak_word_lit(" RUNNING")), C_RESET), freak_word_lit("  ")), C_BWHITE), binary), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
freak_word run_cmd = freak_word_replace(binary, freak_word_lit("/"), freak_word_lit("\\"));
int64_t run_start = freak_time_now_ms();
int64_t run_code = freak_process_exec(run_cmd);
int64_t run_elapsed = (freak_time_now_ms() - run_start);
freak_say(freak_word_lit(""));
if ((run_code != 0)) {
freak_word rc_str = freak_word_from_int(run_code);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), SYM_BOLT), freak_word_lit(" EXIT")), C_RESET), C_DIM), freak_word_lit(" code ")), rc_str), freak_word_lit(" (")), freak_word_from_int(run_elapsed)), freak_word_lit("ms)")), C_RESET));
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_CHECK), freak_word_lit(" DONE")), C_RESET), C_DIM), freak_word_lit(" (")), freak_word_from_int(run_elapsed)), freak_word_lit("ms)")), C_RESET));
}
freak_say(freak_word_lit(""));
}
freak_word freak_hangar_arg(int64_t idx) {
return freak_process_arg((idx - hangar_arg_offset));
}
int64_t freak_hangar_init(freak_word project_dir) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if (freak_fs_exists(manifest)) {
freak_word msg = freak_word_concat(freak_word_lit("  hangar.toml already exists in "), project_dir);
freak_say(msg);
return 1;
}
if ((freak_fs_exists(project_dir) == false)) {
freak_fs_make_dir(project_dir);
}
freak_word project_name = freak_hangar_basename(project_dir);
freak_toml_clear();
freak_toml_set(freak_word_lit("project.name"), project_name);
freak_toml_set(freak_word_lit("project.version"), freak_word_lit("0.1.0"));
freak_toml_write_file(manifest);
freak_word src_dir = freak_word_concat(project_dir, freak_word_lit("/src"));
freak_word src_main = freak_word_concat(src_dir, freak_word_lit("/main.fk"));
if ((freak_fs_exists(src_dir) == false)) {
freak_fs_make_dir(src_dir);
}
if ((freak_fs_exists(src_main) == false)) {
freak_word main_content = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("-- "), project_name), freak_word_lit(" -- a FREAK project\n\nsay \"Hello from ")), project_name), freak_word_lit("!\"\n"));
freak_fs_write(src_main, main_content);
}
freak_word modules_dir = freak_word_concat(project_dir, freak_word_lit("/hangar_modules"));
if ((freak_fs_exists(modules_dir) == false)) {
freak_fs_make_dir(modules_dir);
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  INITIALIZED")), C_RESET), freak_word_lit(" ")), C_BWHITE), project_name), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("    hangar.toml")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("    src/main.fk")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("    hangar_modules/")), C_RESET));
freak_say(freak_word_lit(""));
freak_word next_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Next: ")), C_RESET), freak_word_lit("cd ")), project_dir), freak_word_lit(" && freak run src/main.fk"));
freak_say(next_msg);
freak_say(freak_word_lit(""));
return 0;
}
int64_t freak_hangar_add(freak_word project_dir, freak_word pkg_name, freak_word repo, freak_word ver) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
if (freak_word_eq(repo, freak_word_lit(""))) {
freak_word ver_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".version"));
freak_toml_set(ver_key, ver);
freak_toml_write_file(manifest);
freak_word msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  + ")), C_RESET), C_BWHITE), pkg_name), C_RESET), C_DIM), freak_word_lit(" (")), ver), freak_word_lit(")")), C_RESET);
freak_say(msg);
return 0;
}
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".git"));
freak_word ver_key2 = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".version"));
freak_toml_set(git_key, repo);
freak_toml_set(ver_key2, ver);
freak_toml_write_file(manifest);
freak_word msg2 = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  + ")), C_RESET), C_BWHITE), pkg_name), C_RESET), C_DIM), freak_word_lit(" (")), repo), freak_word_lit(" @ ")), ver), freak_word_lit(")")), C_RESET);
freak_say(msg2);
int64_t install_res = freak_hangar_install_one(project_dir, pkg_name, repo, ver);
if ((install_res == 0)) {
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
freak_lock_load(lockfile);
freak_word lock_source = freak_word_concat(freak_word_lit("git+"), repo);
if (freak_word_eq(repo, freak_word_lit(""))) {
lock_source = freak_word_lit("local");
}
freak_lock_add_entry(pkg_name, ver, lock_source, freak_word_lit(""));
freak_lock_write(lockfile);
}
return install_res;
}
int64_t freak_hangar_remove(freak_word project_dir, freak_word pkg_name) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".git"));
freak_word ver_only_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".version"));
if (((freak_toml_has(git_key) == false) && (freak_toml_has(ver_only_key) == false))) {
freak_word msg = freak_word_concat(freak_word_concat(freak_word_lit("  Package '"), pkg_name), freak_word_lit("' is not in hangar.toml"));
freak_say(msg);
return 1;
}
freak_word prefix = freak_word_concat(freak_word_lit("dependencies."), pkg_name);
freak_toml_remove_prefix(prefix);
freak_toml_write_file(manifest);
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
if (freak_fs_exists(lockfile)) {
freak_lock_load(lockfile);
freak_lock_remove_entry(pkg_name);
freak_lock_write(lockfile);
}
freak_word pkg_dir = freak_word_concat(freak_word_concat(project_dir, freak_word_lit("/hangar_modules/")), pkg_name);
if (freak_fs_exists(pkg_dir)) {
freak_word rm_cmd = freak_hangar_rm_cmd(pkg_dir);
freak_process_exec(rm_cmd);
}
freak_word msg2 = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  - ")), C_RESET), C_BWHITE), pkg_name), C_RESET);
freak_say(msg2);
return 0;
}
void freak_resolve_clear(void) {
resolve_names = freak_array_new();
resolve_versions = freak_array_new();
resolve_sources = freak_array_new();
resolve_constraints = freak_array_new();
resolve_requested_by = freak_array_new();
resolve_count = 0;
}
int64_t freak_resolve_find(freak_word name) {
int64_t i = 0;
while (!((i >= resolve_count))) {
freak_word n = freak_array_get(resolve_names, i);
if (freak_word_eq(n, name)) {
return i;
}
i += 1;
}
return (-1);
}
bool freak_resolve_add(freak_word name, freak_word version, freak_word source, freak_word constraint, freak_word requested_by) {
int64_t idx = freak_resolve_find(name);
if ((idx >= 0)) {
freak_word existing_ver = freak_array_get(resolve_versions, idx);
if ((((!freak_word_eq(constraint, freak_word_lit("latest"))) && (!freak_word_eq(constraint, freak_word_lit("*")))) && (!freak_word_eq(constraint, freak_word_lit(""))))) {
if ((freak_version_matches_constraint(existing_ver, constraint) == false)) {
freak_word existing_by = freak_array_get(resolve_requested_by, idx);
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  [YUUKO] Resolution failed.")), C_RESET), freak_word_lit(" Two dependencies want incompatible versions of ")), C_BWHITE), name), C_RESET), freak_word_lit(":")));
freak_word conflict_msg1 = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BCYAN), existing_by), C_RESET), freak_word_lit("  requires  ")), name), freak_word_lit(" ")), freak_array_get(resolve_constraints, idx));
freak_word conflict_msg2 = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BCYAN), requested_by), C_RESET), freak_word_lit("  requires  ")), name), freak_word_lit(" ")), constraint);
freak_say(conflict_msg1);
freak_say(conflict_msg2);
freak_say(freak_word_lit("        These ranges do not overlap."));
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("        Suggestion: update one of the constraints to allow a compatible version.")), C_RESET));
freak_say(freak_word_lit(""));
return false;
}
}
return true;
}
freak_array_push(resolve_names, name);
freak_array_push(resolve_versions, version);
freak_array_push(resolve_sources, source);
freak_array_push(resolve_constraints, constraint);
freak_array_push(resolve_requested_by, requested_by);
resolve_count += 1;
return true;
}
bool freak_resolve_collect_transitive(freak_word project_dir, freak_word pkg_name, int64_t depth) {
if ((depth > 10)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  WARNING")), C_RESET), freak_word_lit(" Dependency depth limit reached for ")), pkg_name));
return true;
}
freak_word pkg_dir = freak_word_concat(freak_word_concat(project_dir, freak_word_lit("/hangar_modules/")), pkg_name);
freak_word pkg_manifest = freak_word_concat(pkg_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(pkg_manifest) == false)) {
return true;
}
freak_word sub_content = freak_fs_read(pkg_manifest);
if (freak_word_eq(sub_content, freak_word_lit(""))) {
return true;
}
int64_t pos = 0;
int64_t clen = freak_word_length(sub_content);
bool in_deps = false;
while (!((pos >= clen))) {
freak_word line = freak_toml_get_line(sub_content, pos);
pos = freak_toml_line_end(sub_content, pos);
freak_word trimmed = freak_word_trim(line);
if (freak_word_eq(trimmed, freak_word_lit("[dependencies]"))) {
in_deps = true;
}
else {
if ((freak_word_starts_with(trimmed, freak_word_lit("[")) && (!freak_word_eq(trimmed, freak_word_lit("[dependencies]"))))) {
in_deps = false;
}
else {
if (((in_deps && (!freak_word_eq(trimmed, freak_word_lit("")))) && (freak_word_starts_with(trimmed, freak_word_lit("#")) == false))) {
freak_word dep_name = freak_word_lit("");
int64_t di = 0;
int64_t tlen = freak_word_length(trimmed);
while (!((di >= tlen))) {
freak_word c = freak_word_char_at(trimmed, di);
if (((freak_word_eq(c, freak_word_lit(" ")) || freak_word_eq(c, freak_word_lit("="))) || freak_word_eq(c, freak_word_lit("\t")))) {
if ((!freak_word_eq(dep_name, freak_word_lit("")))) {
freak_word dep_constraint = freak_word_lit("latest");
if (freak_word_contains(trimmed, freak_word_lit("\""))) {
int64_t qi = 0;
bool found_eq = false;
while (!((qi >= tlen))) {
freak_word qc = freak_word_char_at(trimmed, qi);
if (freak_word_eq(qc, freak_word_lit("="))) {
found_eq = true;
}
if ((found_eq && freak_word_eq(qc, freak_word_lit("\"")))) {
qi += 1;
freak_word qval = freak_word_lit("");
while (!((qi >= tlen))) {
freak_word qvc = freak_word_char_at(trimmed, qi);
if (freak_word_eq(qvc, freak_word_lit("\""))) {
dep_constraint = qval;
qi = tlen;
}
else {
qval = freak_word_concat(qval, qvc);
}
qi += 1;
}
}
qi += 1;
}
}
freak_word resolved_ver = dep_constraint;
freak_word resolved_src = freak_word_lit("");
if (((!freak_word_eq(dep_constraint, freak_word_lit("latest"))) && (!freak_word_eq(dep_constraint, freak_word_lit("*"))))) {
freak_word reg_result = freak_hangar_resolve_from_registry(dep_name, dep_constraint);
if ((!freak_word_eq(reg_result, freak_word_lit("")))) {
resolved_ver = freak_hangar_extract_colon(reg_result, 0);
resolved_src = freak_hangar_extract_colon(reg_result, 1);
}
}
int64_t is_ok = freak_resolve_add(dep_name, resolved_ver, resolved_src, dep_constraint, pkg_name);
if ((is_ok == false)) {
return false;
}
di = tlen;
}
}
else {
dep_name = freak_word_concat(dep_name, c);
}
di += 1;
}
}
}
}
}
return true;
}
int64_t freak_hangar_install(freak_word project_dir) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
int64_t dep_cnt = freak_toml_dep_count();
if ((dep_cnt == 0)) {
freak_say(freak_word_lit("  No dependencies to install."));
return 0;
}
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
int64_t has_lockfile = freak_lock_load(lockfile);
if (has_lockfile) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Using versions from hangar.lock")));
}
freak_resolve_clear();
int64_t dep_arr = freak_toml_dep_names_arr();
int64_t di = 0;
bool conflicts = false;
while (!((di >= dep_cnt))) {
freak_word dname = freak_array_get(dep_arr, di);
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dname), freak_word_lit(".git"));
freak_word ver_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dname), freak_word_lit(".version"));
freak_word git_val = freak_toml_get(git_key);
freak_word ver_val = freak_toml_get(ver_key);
if (freak_word_eq(ver_val, freak_word_lit(""))) {
ver_val = freak_word_lit("latest");
}
freak_word use_ver = ver_val;
if ((has_lockfile && freak_lock_has(dname))) {
use_ver = freak_lock_get_version(dname);
}
int64_t is_ok = freak_resolve_add(dname, use_ver, git_val, ver_val, freak_word_lit("your project"));
if ((is_ok == false)) {
conflicts = true;
}
di += 1;
}
if (conflicts) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  RESOLUTION FAILED")), C_RESET), freak_word_lit(" — fix the conflicts above before installing.")));
return 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Resolved ")), freak_word_from_int(resolve_count)), freak_word_lit(" package(s)")));
if ((has_lockfile == false)) {
freak_lock_clear();
}
int64_t errors = 0;
int64_t ri = 0;
while (!((ri >= resolve_count))) {
freak_word rname = freak_array_get(resolve_names, ri);
freak_word rver = freak_array_get(resolve_versions, ri);
freak_word rsrc = freak_array_get(resolve_sources, ri);
if ((has_lockfile && freak_lock_has(rname))) {
freak_word locked_ver = freak_lock_get_version(rname);
freak_word lock_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Locked: ")), C_BWHITE), rname), C_RESET), C_DIM), freak_word_lit(" @ ")), locked_ver), C_RESET);
freak_say(lock_msg);
rver = locked_ver;
}
int64_t ires = freak_hangar_install_one(project_dir, rname, rsrc, rver);
if ((ires != 0)) {
errors += 1;
}
int64_t trans_ok = freak_resolve_collect_transitive(project_dir, rname, 0);
if ((trans_ok == false)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  TRANSITIVE CONFLICT")), C_RESET), freak_word_lit(" — stopping installation.")));
return 1;
}
ri += 1;
}
while (!((ri >= resolve_count))) {
freak_word tname = freak_array_get(resolve_names, ri);
freak_word tver = freak_array_get(resolve_versions, ri);
freak_word tsrc = freak_array_get(resolve_sources, ri);
freak_word tmsg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Transitive: ")), C_BWHITE), tname), C_RESET);
freak_say(tmsg);
int64_t tres = freak_hangar_install_one(project_dir, tname, tsrc, tver);
if ((tres != 0)) {
errors += 1;
}
ri += 1;
}
freak_lock_write(lockfile);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Lockfile written: hangar.lock")));
if ((errors > 0)) {
freak_word err_str = freak_word_from_int(errors);
freak_word errmsg = freak_word_concat(freak_word_concat(freak_word_lit("  "), err_str), freak_word_lit(" package(s) failed to install."));
freak_say(errmsg);
return 1;
}
freak_word cnt_str = freak_word_from_int(resolve_count);
freak_word ok_msg = freak_word_concat(freak_word_concat(freak_word_lit("  All "), cnt_str), freak_word_lit(" package(s) installed."));
freak_say(ok_msg);
return 0;
}
int64_t freak_hangar_update(freak_word project_dir, freak_word pkg_name) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
int64_t dep_cnt = freak_toml_dep_count();
if ((dep_cnt == 0)) {
freak_say(freak_word_lit("  No dependencies to update."));
return 0;
}
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
if ((!freak_word_eq(pkg_name, freak_word_lit("")))) {
freak_word git_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".git"));
freak_word ver_key = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), pkg_name), freak_word_lit(".version"));
freak_word git_val = freak_toml_get(git_key);
freak_word ver_val = freak_toml_get(ver_key);
if (freak_word_eq(ver_val, freak_word_lit(""))) {
ver_val = freak_word_lit("latest");
}
if (((freak_toml_has(git_key) == false) && (freak_toml_has(ver_key) == false))) {
freak_word not_found = freak_word_concat(freak_word_concat(freak_word_lit("  Package '"), pkg_name), freak_word_lit("' is not in hangar.toml"));
freak_say(not_found);
return 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Updating ")), C_BWHITE), pkg_name), C_RESET), freak_word_lit("...")));
freak_lock_load(lockfile);
freak_lock_remove_entry(pkg_name);
int64_t ires = freak_hangar_install_one(project_dir, pkg_name, git_val, ver_val);
if ((ires == 0)) {
freak_word lock_source = freak_word_concat(freak_word_lit("git+"), git_val);
if (freak_word_eq(git_val, freak_word_lit(""))) {
lock_source = freak_word_lit("local");
}
freak_lock_add_entry(pkg_name, ver_val, lock_source, freak_word_lit(""));
}
freak_lock_write(lockfile);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Lockfile updated: hangar.lock")));
return ires;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Re-resolving all dependencies...")));
freak_lock_clear();
int64_t dep_arr = freak_toml_dep_names_arr();
int64_t errors = 0;
int64_t di = 0;
while (!((di >= dep_cnt))) {
freak_word dname = freak_array_get(dep_arr, di);
freak_word git_key2 = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dname), freak_word_lit(".git"));
freak_word ver_key2 = freak_word_concat(freak_word_concat(freak_word_lit("dependencies."), dname), freak_word_lit(".version"));
freak_word git_val2 = freak_toml_get(git_key2);
freak_word ver_val2 = freak_toml_get(ver_key2);
if (freak_word_eq(ver_val2, freak_word_lit(""))) {
ver_val2 = freak_word_lit("latest");
}
int64_t ires2 = freak_hangar_install_one(project_dir, dname, git_val2, ver_val2);
if ((ires2 != 0)) {
errors += 1;
}
else {
freak_word lock_source2 = freak_word_concat(freak_word_lit("git+"), git_val2);
if (freak_word_eq(git_val2, freak_word_lit(""))) {
lock_source2 = freak_word_lit("local");
}
freak_lock_add_entry(dname, ver_val2, lock_source2, freak_word_lit(""));
}
di += 1;
}
freak_lock_write(lockfile);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Lockfile updated: hangar.lock")));
if ((errors > 0)) {
freak_word err_str = freak_word_from_int(errors);
freak_word errmsg = freak_word_concat(freak_word_concat(freak_word_lit("  "), err_str), freak_word_lit(" package(s) failed to update."));
freak_say(errmsg);
return 1;
}
freak_word cnt_str = freak_word_from_int(dep_cnt);
freak_word ok_msg = freak_word_concat(freak_word_concat(freak_word_lit("  All "), cnt_str), freak_word_lit(" package(s) updated."));
freak_say(ok_msg);
return 0;
}
freak_word freak_hangar_get_index_path(freak_word name) {
if ((freak_word_length(name) < 2)) {
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("/"), name), freak_word_lit("/")), name);
}
freak_word p1 = freak_word_to_lower(freak_word_char_at(name, 0));
freak_word p2 = freak_word_to_lower(freak_word_char_at(name, 1));
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("/"), p1), freak_word_lit("/")), p2), freak_word_lit("/")), name);
}
freak_word freak_hangar_resolve_from_registry(freak_word name, freak_word constraint) {
freak_word registry = freak_toml_get(freak_word_lit("registries.default"));
if (freak_word_eq(registry, freak_word_lit(""))) {
registry = HANGAR_DEFAULT_REGISTRY;
}
freak_word index_url = freak_word_concat(registry, freak_hangar_get_index_path(name));
freak_word fetch_cmd = freak_word_concat(freak_word_lit("curl -sL "), index_url);
freak_word index_content = freak_process_exec_capture(fetch_cmd);
if ((freak_word_eq(index_content, freak_word_lit("")) || freak_word_contains(index_content, freak_word_lit("404")))) {
return freak_word_lit("");
}
int64_t pos = 0;
int64_t clen = freak_word_length(index_content);
freak_word best_ver = freak_word_lit("");
freak_word best_repo = freak_word_lit("");
while (!((pos >= clen))) {
freak_word line = freak_toml_get_line(index_content, pos);
pos = freak_toml_line_end(index_content, pos);
if ((!freak_word_eq(freak_word_trim(line), freak_word_lit("")))) {
freak_word v = freak_hangar_extract_json_field(line, freak_word_lit("vers"));
freak_word r = freak_hangar_extract_json_field(line, freak_word_lit("repo"));
if (freak_version_matches_constraint(v, constraint)) {
if ((freak_word_eq(best_ver, freak_word_lit("")) || freak_ver_gt(freak_ver_parse(v), freak_ver_parse(best_ver)))) {
best_ver = v;
best_repo = r;
}
}
}
}
if ((!freak_word_eq(best_ver, freak_word_lit("")))) {
return freak_word_concat(freak_word_concat(best_ver, freak_word_lit(":")), best_repo);
}
return freak_word_lit("");
}
int64_t freak_hangar_install_one(freak_word project_dir, freak_word pkg_name, freak_word repo, freak_word ver) {
freak_word modules_dir = freak_word_concat(project_dir, freak_word_lit("/hangar_modules"));
if ((freak_fs_exists(modules_dir) == false)) {
freak_fs_make_dir(modules_dir);
}
freak_word pkg_dir = freak_word_concat(freak_word_concat(modules_dir, freak_word_lit("/")), pkg_name);
freak_word actual_repo = repo;
freak_word actual_ver = ver;
if (freak_word_eq(actual_repo, freak_word_lit(""))) {
freak_word resolved = freak_hangar_resolve_from_registry(pkg_name, ver);
if (freak_word_eq(resolved, freak_word_lit(""))) {
freak_word msg = freak_word_concat(freak_word_concat(freak_word_lit("  Package '"), pkg_name), freak_word_lit("' not found in registry and no git repo specified."));
freak_say(msg);
return 1;
}
actual_ver = freak_hangar_extract_colon(resolved, 0);
actual_repo = freak_hangar_extract_colon(resolved, 1);
freak_word res_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Resolved ")), C_BWHITE), pkg_name), C_RESET), C_DIM), freak_word_lit(" to ")), actual_ver), freak_word_lit(" (")), actual_repo), freak_word_lit(")")), C_RESET);
freak_say(res_msg);
}
freak_word fetch_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Fetching ")), C_BWHITE), pkg_name), C_RESET), C_DIM), freak_word_lit(" from ")), actual_repo), freak_word_lit("...")), C_RESET);
freak_say(fetch_msg);
if (freak_fs_exists(pkg_dir)) {
freak_word rm_cmd = freak_hangar_rm_cmd(pkg_dir);
freak_process_exec(rm_cmd);
}
freak_word git_url = freak_word_lit("");
if (freak_word_starts_with(actual_repo, freak_word_lit("https://"))) {
git_url = actual_repo;
}
else {
git_url = freak_word_concat(freak_word_concat(freak_word_lit("https://github.com/"), actual_repo), freak_word_lit(".git"));
}
freak_word clone_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("git clone --depth 1 --quiet "), git_url), freak_word_lit(" ")), pkg_dir);
if (((!freak_word_eq(actual_ver, freak_word_lit("latest"))) && (!freak_word_eq(actual_ver, freak_word_lit("*"))))) {
clone_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("git clone --depth 1 --quiet --branch v"), actual_ver), freak_word_lit(" ")), git_url), freak_word_lit(" ")), pkg_dir);
}
int64_t clone_res = freak_process_exec(clone_cmd);
if ((clone_res != 0)) {
if (((!freak_word_eq(actual_ver, freak_word_lit("latest"))) && (!freak_word_eq(actual_ver, freak_word_lit("*"))))) {
freak_word clone2 = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("git clone --depth 1 --quiet --branch "), actual_ver), freak_word_lit(" ")), git_url), freak_word_lit(" ")), pkg_dir);
int64_t clone2_res = freak_process_exec(clone2);
if ((clone2_res != 0)) {
freak_word fail_msg = freak_word_concat(freak_word_concat(freak_word_lit("  Could not fetch "), pkg_name), freak_word_lit(". Creating stub..."));
freak_say(fail_msg);
freak_hangar_create_stub(pkg_dir, pkg_name);
return 0;
}
}
else {
freak_word fail_msg2 = freak_word_concat(freak_word_concat(freak_word_lit("  Could not fetch "), pkg_name), freak_word_lit(". Creating stub..."));
freak_say(fail_msg2);
freak_hangar_create_stub(pkg_dir, pkg_name);
return 0;
}
}
freak_word git_dir = freak_word_concat(pkg_dir, freak_word_lit("/.git"));
if (freak_fs_exists(git_dir)) {
freak_word rm_git = freak_hangar_rm_cmd(git_dir);
freak_process_exec(rm_git);
}
freak_word pkg_sha = freak_hangar_compute_dir_sha256(pkg_dir);
if ((!freak_word_eq(pkg_sha, freak_word_lit("")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("SHA-256: ")), freak_word_substring(pkg_sha, 0, 16)), freak_word_lit("...")));
}
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
freak_lock_load(lockfile);
freak_word lock_source = actual_repo;
freak_lock_add_entry(pkg_name, actual_ver, lock_source, pkg_sha);
freak_lock_write(lockfile);
freak_word ok_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  INSTALLED")), C_RESET), freak_word_lit(" ")), C_BWHITE), pkg_name), C_RESET), C_DIM), freak_word_lit(" -> hangar_modules/")), pkg_name), freak_word_lit("/")), C_RESET);
freak_say(ok_msg);
return 0;
}
void freak_hangar_create_stub(freak_word pkg_dir, freak_word pkg_name) {
freak_fs_make_dir(pkg_dir);
freak_word stub_path = freak_word_concat(freak_word_concat(freak_word_concat(pkg_dir, freak_word_lit("/")), pkg_name), freak_word_lit(".fk"));
freak_word stub_content = freak_word_concat(freak_word_concat(freak_word_lit("-- "), pkg_name), freak_word_lit(" (stub module -- install with 'hangar install')\n-- This stub was created because the package could not be downloaded.\n\n"));
freak_fs_write(stub_path, stub_content);
freak_word msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Created stub: hangar_modules/"), pkg_name), freak_word_lit("/")), pkg_name), freak_word_lit(".fk"));
freak_say(msg);
}
int64_t freak_hangar_version_cmd(freak_word project_dir, freak_word bump) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
freak_word pname = freak_toml_get(freak_word_lit("project.name"));
freak_word current = freak_toml_get(freak_word_lit("project.version"));
if (freak_word_eq(pname, freak_word_lit(""))) {
pname = freak_word_lit("unknown");
}
if (freak_word_eq(current, freak_word_lit(""))) {
current = freak_word_lit("0.0.0");
}
if (freak_word_eq(bump, freak_word_lit(""))) {
freak_word show_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), pname), C_RESET), freak_word_lit(" ")), C_BMAGENTA), freak_word_lit("v")), current), C_RESET);
freak_say(show_msg);
return 0;
}
freak_word parsed = freak_ver_parse(current);
int64_t maj = freak_ver_major(parsed);
int64_t min = freak_ver_minor(parsed);
int64_t pat = freak_ver_patch(parsed);
freak_word new_ver = freak_word_lit("");
if (freak_word_eq(bump, freak_word_lit("major"))) {
new_ver = freak_word_concat(freak_word_from_int((maj + 1)), freak_word_lit(".0.0"));
}
else {
if (freak_word_eq(bump, freak_word_lit("minor"))) {
freak_word new_min = freak_word_from_int((min + 1));
new_ver = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_from_int(maj), freak_word_lit(".")), new_min), freak_word_lit(".0"));
}
else {
if (freak_word_eq(bump, freak_word_lit("patch"))) {
freak_word new_pat = freak_word_from_int((pat + 1));
new_ver = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_from_int(maj), freak_word_lit(".")), freak_word_from_int(min)), freak_word_lit(".")), new_pat);
}
else {
new_ver = bump;
}
}
}
freak_toml_set(freak_word_lit("project.version"), new_ver);
freak_toml_write_file(manifest);
freak_word done_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), pname), C_RESET), freak_word_lit(" ")), C_DIM), current), C_RESET), freak_word_lit(" -> ")), C_BMAGENTA), new_ver), C_RESET);
freak_say(done_msg);
return 0;
}
int64_t freak_hangar_download_file(freak_word url, freak_word dest, bool is_win) {
if (is_win) {
freak_word ps_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("powershell -NoProfile -NonInteractive -Command \"(New-Object Net.WebClient).DownloadFile('"), url), freak_word_lit("', '")), dest), freak_word_lit("')\""));
int64_t ps_res = freak_process_exec(ps_cmd);
if ((ps_res == 0)) {
return 0;
}
freak_word curl_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("curl -fsSL -o \""), dest), freak_word_lit("\" \"")), url), freak_word_lit("\""));
return freak_process_exec(curl_cmd);
}
else {
freak_word curl_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("curl -fsSL -o \""), dest), freak_word_lit("\" \"")), url), freak_word_lit("\""));
return freak_process_exec(curl_cmd);
}
}
void freak_hangar_mkdir(freak_word path, bool is_win) {
if (is_win) {
freak_word cmd = freak_word_concat(freak_word_concat(freak_word_lit("powershell -NoProfile -NonInteractive -Command \"New-Item -Force -ItemType Directory -Path '"), path), freak_word_lit("' | Out-Null\""));
freak_process_exec(cmd);
}
else {
freak_process_exec(freak_word_concat(freak_word_concat(freak_word_lit("mkdir -p \""), path), freak_word_lit("\"")));
}
}
int64_t freak_hangar_install_freak(void) {
freak_say(freak_word_lit("  Detecting platform..."));
freak_word os_tag = freak_word_lit("");
freak_word ext = freak_word_lit("");
freak_word windir_env = freak_process_env(freak_word_lit("WINDIR"));
if ((!freak_word_eq(windir_env, freak_word_lit("")))) {
os_tag = freak_word_lit("windows");
ext = freak_word_lit(".exe");
}
else {
freak_word uname_out = freak_process_exec_capture(freak_word_lit("uname -s 2>/dev/null"));
if (freak_word_contains(uname_out, freak_word_lit("Linux"))) {
os_tag = freak_word_lit("linux");
}
else {
if (freak_word_contains(uname_out, freak_word_lit("Darwin"))) {
os_tag = freak_word_lit("macos");
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" Unsupported OS.")));
freak_say(freak_word_lit("  Download manually: https://github.com/FREAK-lang-dev/Freak-lang/releases"));
return 1;
}
}
}
int64_t is_win = freak_word_eq(os_tag, freak_word_lit("windows"));
freak_word arch_tag = freak_word_lit("x64");
if ((!is_win)) {
freak_word arch_out = freak_process_exec_capture(freak_word_lit("uname -m 2>/dev/null"));
if ((freak_word_contains(arch_out, freak_word_lit("aarch64")) || freak_word_contains(arch_out, freak_word_lit("arm64")))) {
arch_tag = freak_word_lit("arm64");
}
}
freak_word platform = freak_word_concat(freak_word_concat(os_tag, freak_word_lit("-")), arch_tag);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Platform: "), C_BWHITE), platform), C_RESET));
freak_word freak_home = freak_word_lit("");
if (is_win) {
freak_word appdata = freak_process_env(freak_word_lit("APPDATA"));
if (freak_word_eq(appdata, freak_word_lit(""))) {
freak_word userprofile = freak_process_env(freak_word_lit("USERPROFILE"));
appdata = freak_word_concat(userprofile, freak_word_lit("/AppData/Roaming"));
}
freak_home = freak_word_concat(appdata, freak_word_lit("/freak"));
}
else {
freak_word home_dir = freak_process_env(freak_word_lit("HOME"));
freak_home = freak_word_concat(home_dir, freak_word_lit("/.freak"));
}
freak_word bin_dir = freak_word_concat(freak_home, freak_word_lit("/bin"));
freak_word runtime_dir = freak_word_concat(freak_home, freak_word_lit("/runtime"));
freak_word std_dir = freak_word_concat(freak_home, freak_word_lit("/std"));
freak_word binary_path = freak_word_concat(freak_word_concat(bin_dir, freak_word_lit("/freak")), ext);
freak_word hangar_path = freak_word_concat(freak_word_concat(bin_dir, freak_word_lit("/hangar")), ext);
freak_say(freak_word_lit("  Checking latest version..."));
freak_word api_resp = freak_word_lit("");
if (is_win) {
freak_word ps_api = freak_word_lit("powershell -NoProfile -NonInteractive -Command \"(New-Object Net.WebClient).DownloadString('https://api.github.com/repos/FREAK-lang-dev/Freak-lang/releases/latest')\"");
api_resp = freak_process_exec_capture(ps_api);
if (freak_word_eq(api_resp, freak_word_lit(""))) {
api_resp = freak_process_exec_capture(freak_word_lit("curl -fsSL \"https://api.github.com/repos/FREAK-lang-dev/Freak-lang/releases/latest\""));
}
}
else {
api_resp = freak_process_exec_capture(freak_word_lit("curl -fsSL \"https://api.github.com/repos/FREAK-lang-dev/Freak-lang/releases/latest\""));
}
freak_word version = freak_hangar_extract_json_field(api_resp, freak_word_lit("tag_name"));
if (freak_word_eq(version, freak_word_lit(""))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" Could not fetch latest release.")));
freak_say(freak_word_lit("  Check your internet connection and try again."));
freak_say(freak_word_lit("  Manual download: https://github.com/FREAK-lang-dev/Freak-lang/releases"));
return 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Latest: "), C_BGREEN), version), C_RESET));
freak_say(freak_word_lit("  Creating directories..."));
freak_hangar_mkdir(bin_dir, is_win);
freak_hangar_mkdir(runtime_dir, is_win);
freak_hangar_mkdir(std_dir, is_win);
freak_word artifact = freak_word_concat(freak_word_concat(freak_word_lit("freak-"), platform), ext);
freak_word base_url = freak_word_concat(freak_word_lit("https://github.com/FREAK-lang-dev/Freak-lang/releases/download/"), version);
freak_word freak_url = freak_word_concat(freak_word_concat(base_url, freak_word_lit("/")), artifact);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Downloading "), C_BWHITE), artifact), C_RESET), freak_word_lit("...")));
int64_t dl_res = freak_hangar_download_file(freak_url, binary_path, is_win);
if ((dl_res != 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" Download failed.")));
freak_say(freak_word_concat(freak_word_lit("  URL tried: "), freak_url));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Try: "), C_DIM), freak_word_lit("curl -fsSL -o freak")), ext), freak_word_lit(" \"")), freak_url), freak_word_lit("\"")), C_RESET));
return 1;
}
if ((!is_win)) {
freak_process_exec(freak_word_concat(freak_word_concat(freak_word_lit("chmod +x \""), binary_path), freak_word_lit("\"")));
}
freak_word hangar_artifact = freak_word_concat(freak_word_concat(freak_word_lit("hangar-"), platform), ext);
freak_word hangar_url = freak_word_concat(freak_word_concat(base_url, freak_word_lit("/")), hangar_artifact);
int64_t hg_res = freak_hangar_download_file(hangar_url, hangar_path, is_win);
if ((hg_res == 0)) {
if ((!is_win)) {
freak_process_exec(freak_word_concat(freak_word_concat(freak_word_lit("chmod +x \""), hangar_path), freak_word_lit("\"")));
}
}
freak_say(freak_word_lit("  Downloading runtime..."));
freak_word raw_base = freak_word_concat(freak_word_lit("https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/"), version);
freak_word rt_o_ext = freak_word_lit(".o");
if (is_win) {
rt_o_ext = freak_word_lit(".obj");
}
freak_word rt_o_url = freak_word_concat(freak_word_concat(raw_base, freak_word_lit("/freakc/runtime/freak_runtime")), rt_o_ext);
freak_word llvm_o_url = freak_word_concat(freak_word_concat(raw_base, freak_word_lit("/freakc/runtime/freak_llvm_runtime")), rt_o_ext);
freak_hangar_download_file(rt_o_url, freak_word_concat(freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime")), rt_o_ext), is_win);
freak_hangar_download_file(llvm_o_url, freak_word_concat(freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime")), rt_o_ext), is_win);
freak_hangar_download_file(freak_word_concat(raw_base, freak_word_lit("/freakc/runtime/freak_runtime.c")), freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.c")), is_win);
freak_hangar_download_file(freak_word_concat(raw_base, freak_word_lit("/freakc/runtime/freak_runtime.h")), freak_word_concat(runtime_dir, freak_word_lit("/freak_runtime.h")), is_win);
freak_hangar_download_file(freak_word_concat(raw_base, freak_word_lit("/freakc/runtime/freak_llvm_runtime.c")), freak_word_concat(runtime_dir, freak_word_lit("/freak_llvm_runtime.c")), is_win);
freak_say(freak_word_lit("  Downloading standard library..."));
int64_t std_files = freak_array_new();
freak_array_push(std_files, freak_word_lit("math.fk"));
freak_array_push(std_files, freak_word_lit("math3d.fk"));
freak_array_push(std_files, freak_word_lit("zip.fk"));
freak_array_push(std_files, freak_word_lit("string.fk"));
freak_array_push(std_files, freak_word_lit("convert.fk"));
freak_array_push(std_files, freak_word_lit("algorithm.fk"));
freak_array_push(std_files, freak_word_lit("json.fk"));
freak_array_push(std_files, freak_word_lit("http.fk"));
freak_array_push(std_files, freak_word_lit("version.fk"));
freak_array_push(std_files, freak_word_lit("runtime.fk"));
int64_t si = 0;
for (int64_t __rep = 0; __rep < 8; __rep++) {
freak_word sf = freak_array_get(std_files, si);
freak_hangar_download_file(freak_word_concat(freak_word_concat(raw_base, freak_word_lit("/std/")), sf), freak_word_concat(freak_word_concat(std_dir, freak_word_lit("/")), sf), is_win);
si += 1;
}
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_BGREEN), SYM_SPARK), freak_word_lit(" FREAK ")), version), freak_word_lit(" installed!")), C_RESET), 48));
freak_say(freak_cli_box_sep(48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Compiler: ")), C_RESET), binary_path), 48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Runtime:  ")), C_RESET), runtime_dir), 48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Stdlib:   ")), C_RESET), std_dir), 48));
freak_say(freak_cli_box_sep(48));
if (is_win) {
freak_say(freak_cli_box_mid(freak_word_lit("  Add to PATH (PowerShell):"), 48));
freak_word ps_path_cmd = freak_word_concat(freak_word_concat(freak_word_lit("$env:PATH += ';' + '"), bin_dir), freak_word_lit("'"));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_CYAN), ps_path_cmd), C_RESET), 48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Or: "), C_DIM), freak_word_lit("setx PATH \"%PATH%;")), bin_dir), freak_word_lit("\"")), C_RESET), 48));
}
else {
freak_say(freak_cli_box_mid(freak_word_lit("  Add to PATH:"), 48));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_CYAN), freak_word_lit("export PATH=\"")), bin_dir), freak_word_lit(":$PATH\"")), C_RESET), 48));
}
freak_say(freak_cli_box_bot(48));
freak_say(freak_word_lit(""));
int64_t clang_test = freak_process_exec(freak_word_lit("clang --version"));
if ((clang_test != 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), SYM_BOLT), freak_word_lit(" clang not found")), C_RESET), freak_word_lit(" — needed to compile .fk programs.")));
if (is_win) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Install with: "), C_CYAN), freak_word_lit("winget install LLVM.LLVM")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("           or: "), C_CYAN), freak_word_lit("choco install llvm")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Then reopen terminal and run: "), C_BWHITE), freak_word_lit("freak doctor")), C_RESET));
}
else {
if (freak_word_eq(os_tag, freak_word_lit("linux"))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Install with: "), C_CYAN), freak_word_lit("sudo apt install clang lld")), C_RESET), freak_word_lit("  (Debian/Ubuntu)")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("            or: "), C_CYAN), freak_word_lit("sudo dnf install clang lld")), C_RESET), freak_word_lit("  (Fedora/RHEL)")));
}
else {
if (freak_word_eq(os_tag, freak_word_lit("macos"))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Install with: "), C_CYAN), freak_word_lit("xcode-select --install")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("            or: "), C_CYAN), freak_word_lit("brew install llvm")), C_RESET));
}
}
}
freak_say(freak_word_lit(""));
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_CHECK), freak_word_lit(" clang found")), C_RESET), freak_word_lit(" — ready to compile!")));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Try: ")), C_RESET), C_BWHITE), freak_word_lit("freak build hello.fk")), C_RESET));
freak_say(freak_word_lit(""));
}
return 0;
}
int64_t freak_hangar_outdated(freak_word project_dir) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Run 'hangar init' first."));
return 1;
}
freak_toml_load(manifest);
int64_t dep_cnt = freak_toml_dep_count();
if ((dep_cnt == 0)) {
freak_say(freak_word_lit("  No dependencies to check."));
return 0;
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BMAGENTA, freak_word_lit("  OUTDATED")), C_RESET), C_DIM), freak_word_lit(" -- checking installed packages")), C_RESET));
freak_say(freak_word_lit(""));
int64_t dep_arr = freak_toml_dep_names_arr();
int64_t found_outdated = 0;
int64_t di = 0;
while (!((di >= dep_cnt))) {
freak_word dname = freak_array_get(dep_arr, di);
freak_word ver_val = freak_toml_dep_get_version(dname);
freak_word pkg_manifest = freak_word_concat(freak_word_concat(freak_word_concat(project_dir, freak_word_lit("/hangar_modules/")), dname), freak_word_lit("/hangar.toml"));
freak_word installed_ver = freak_word_lit("");
if (freak_fs_exists(pkg_manifest)) {
int64_t saved_keys = toml_keys_arr;
int64_t saved_vals = toml_vals_arr;
int64_t saved_count = toml_count;
freak_toml_load(pkg_manifest);
installed_ver = freak_toml_get(freak_word_lit("project.version"));
toml_keys_arr = saved_keys;
toml_vals_arr = saved_vals;
toml_count = saved_count;
}
if (freak_word_eq(installed_ver, freak_word_lit(""))) {
installed_ver = freak_word_lit("unknown");
}
freak_word constraint_str = ver_val;
if (freak_word_eq(constraint_str, freak_word_lit(""))) {
constraint_str = freak_word_lit("latest");
}
freak_word status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), dname), C_RESET);
status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(status_line, C_DIM), freak_word_lit("  installed: ")), C_RESET), installed_ver);
status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(status_line, C_DIM), freak_word_lit("  constraint: ")), C_RESET), constraint_str);
if (((((!freak_word_eq(installed_ver, freak_word_lit("unknown"))) && (!freak_word_eq(ver_val, freak_word_lit("")))) && (!freak_word_eq(ver_val, freak_word_lit("latest")))) && (!freak_word_eq(ver_val, freak_word_lit("*"))))) {
int64_t satisfies = freak_ver_satisfies(installed_ver, ver_val);
if ((satisfies == false)) {
status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(status_line, freak_word_lit("  ")), C_BYELLOW), freak_word_lit("UPDATE AVAILABLE")), C_RESET);
found_outdated += 1;
}
else {
status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(status_line, freak_word_lit("  ")), C_BGREEN), freak_word_lit("OK")), C_RESET);
}
}
else {
status_line = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(status_line, freak_word_lit("  ")), C_DIM), freak_word_lit("skip (no constraint)")), C_RESET);
}
freak_say(status_line);
di += 1;
}
freak_say(freak_word_lit(""));
if ((found_outdated > 0)) {
freak_word cnt_str = freak_word_from_int(found_outdated);
freak_word summary = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  ")), cnt_str), freak_word_lit(" package(s) may need updating.")), C_RESET);
freak_say(summary);
}
else {
freak_say(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  All packages satisfy their constraints.")), C_RESET));
}
freak_say(freak_word_lit(""));
return 0;
}
freak_word freak_hangar_basename(freak_word path) {
freak_word last = freak_word_lit("");
int64_t i = 0;
int64_t plen = freak_word_length(path);
while (!((i >= plen))) {
freak_word c = freak_word_char_at(path, i);
if ((freak_word_eq(c, freak_word_lit("/")) || freak_word_eq(c, freak_word_lit("\\")))) {
last = freak_word_lit("");
}
else {
last = freak_word_concat(last, c);
}
i += 1;
}
if ((freak_word_eq(last, freak_word_lit("")) || freak_word_eq(last, freak_word_lit(".")))) {
last = freak_word_lit("my-project");
}
return last;
}
freak_word freak_hangar_rm_cmd(freak_word path) {
freak_word win_check = freak_process_exec_capture(freak_word_lit("echo %OS%"));
if (freak_word_contains(win_check, freak_word_lit("Windows"))) {
freak_word win_path = freak_word_replace(path, freak_word_lit("/"), freak_word_lit("\\"));
return freak_word_concat(freak_word_concat(freak_word_lit("rmdir /s /q \""), win_path), freak_word_lit("\""));
}
else {
return freak_word_concat(freak_word_concat(freak_word_lit("rm -rf \""), path), freak_word_lit("\""));
}
}
freak_word freak_hangar_extract_json_field(freak_word json, freak_word field) {
freak_word search = freak_word_concat(freak_word_concat(freak_word_lit("\""), field), freak_word_lit("\""));
int64_t jlen = freak_word_length(json);
int64_t slen = freak_word_length(search);
int64_t i = 0;
while (!((i >= jlen))) {
bool match = true;
int64_t si = 0;
while (!((si >= slen))) {
if (((i + si) >= jlen)) {
match = false;
}
if (match) {
freak_word jc = freak_word_char_at(json, (i + si));
freak_word sc = freak_word_char_at(search, si);
if ((!freak_word_eq(jc, sc))) {
match = false;
}
}
si += 1;
}
if (match) {
int64_t vi = (i + slen);
while (!((vi >= jlen))) {
freak_word vc = freak_word_char_at(json, vi);
if ((((!freak_word_eq(vc, freak_word_lit(":"))) && (!freak_word_eq(vc, freak_word_lit(" ")))) && (!freak_word_eq(vc, freak_word_lit("\t"))))) {
if (freak_word_eq(vc, freak_word_lit("\""))) {
vi += 1;
freak_word val = freak_word_lit("");
while (!((vi >= jlen))) {
freak_word vv = freak_word_char_at(json, vi);
if (freak_word_eq(vv, freak_word_lit("\""))) {
return val;
}
val = freak_word_concat(val, vv);
vi += 1;
}
}
}
vi += 1;
}
}
i += 1;
}
return freak_word_lit("");
}
freak_word freak_hangar_compute_sha256(freak_word path) {
freak_word win_check = freak_process_exec_capture(freak_word_lit("echo %OS%"));
freak_word cmd = freak_word_lit("");
if (freak_word_contains(win_check, freak_word_lit("Windows"))) {
cmd = freak_word_concat(freak_word_concat(freak_word_lit("certutil -hashfile \""), path), freak_word_lit("\" SHA256"));
}
else {
cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("sha256sum \""), path), freak_word_lit("\" 2>/dev/null || shasum -a 256 \"")), path), freak_word_lit("\""));
}
freak_word output = freak_process_exec_capture(cmd);
if (freak_word_eq(output, freak_word_lit(""))) {
return freak_word_lit("");
}
if (freak_word_contains(win_check, freak_word_lit("Windows"))) {
int64_t pos = 0;
int64_t olen = freak_word_length(output);
int64_t line_num = 0;
while (!((pos >= olen))) {
freak_word line = freak_toml_get_line(output, pos);
pos = freak_toml_line_end(output, pos);
line_num += 1;
if ((line_num == 2)) {
return freak_word_replace(freak_word_trim(line), freak_word_lit(" "), freak_word_lit(""));
}
}
}
else {
freak_word hash = freak_word_lit("");
int64_t i = 0;
int64_t olen = freak_word_length(output);
while (!(((i >= 64) || (i >= olen)))) {
freak_word c = freak_word_char_at(output, i);
if (((!freak_word_eq(c, freak_word_lit(" "))) && (!freak_word_eq(c, freak_word_lit("\t"))))) {
hash = freak_word_concat(hash, c);
}
i += 1;
}
return hash;
}
return freak_word_lit("");
}
freak_word freak_hangar_compute_dir_sha256(freak_word pkg_dir) {
freak_word tmp_tar = freak_word_concat(pkg_dir, freak_word_lit(".tmp.tar.gz"));
freak_word win_check = freak_process_exec_capture(freak_word_lit("echo %OS%"));
freak_word tar_cmd = freak_word_lit("");
if (freak_word_contains(win_check, freak_word_lit("Windows"))) {
tar_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("tar -czf \""), tmp_tar), freak_word_lit("\" -C \"")), pkg_dir), freak_word_lit("\" ."));
}
else {
tar_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("tar -czf \""), tmp_tar), freak_word_lit("\" -C \"")), pkg_dir), freak_word_lit("\" ."));
}
int64_t tar_res = freak_process_exec(tar_cmd);
if ((tar_res != 0)) {
return freak_word_lit("");
}
freak_word hash = freak_hangar_compute_sha256(tmp_tar);
freak_fs_delete(tmp_tar);
return hash;
}
bool freak_hangar_verify_package(freak_word pkg_name, freak_word pkg_dir, freak_word expected_sha256) {
if (freak_word_eq(expected_sha256, freak_word_lit(""))) {
return true;
}
freak_word actual = freak_hangar_compute_dir_sha256(pkg_dir);
if (freak_word_eq(actual, freak_word_lit(""))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  WARNING")), C_RESET), freak_word_lit(" Could not compute hash for ")), pkg_name));
return true;
}
if (freak_word_eq(actual, expected_sha256)) {
return true;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  INTEGRITY FAILURE")), C_RESET), freak_word_lit(" ")), pkg_name));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("    expected: ")), C_RESET), expected_sha256));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("    actual:   ")), C_RESET), actual));
return false;
}
}
int64_t freak_hangar_audit(freak_word project_dir, bool fix_mode) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_BMAGENTA, freak_word_lit("  HANGAR AUDIT")), C_RESET));
freak_say(freak_word_lit(""));
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found."));
return 1;
}
freak_toml_load(manifest);
freak_word lockfile = freak_word_concat(project_dir, freak_word_lit("/hangar.lock"));
int64_t has_lock = freak_lock_load(lockfile);
if ((has_lock == false)) {
freak_say(freak_word_lit("  No hangar.lock found. Run 'hangar install' first."));
return 1;
}
freak_word modules_dir = freak_word_concat(project_dir, freak_word_lit("/hangar_modules"));
int64_t issues = 0;
int64_t verified = 0;
int64_t i = 0;
while (!((i >= lock_pkg_count))) {
freak_word name = freak_array_get(lock_pkg_names, i);
freak_word version = freak_array_get(lock_pkg_versions, i);
freak_word sha256 = freak_array_get(lock_pkg_sha256s, i);
freak_word pkg_dir = freak_word_concat(freak_word_concat(modules_dir, freak_word_lit("/")), name);
if ((freak_fs_exists(pkg_dir) == false)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  MISSING")), C_RESET), freak_word_lit(" ")), name), freak_word_lit(" v")), version), freak_word_lit(" (not installed)")));
issues += 1;
if (fix_mode) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Reinstalling ")), name), freak_word_lit("...")));
freak_word source = freak_array_get(lock_pkg_sources, i);
freak_hangar_install_one(project_dir, name, source, version);
}
}
else {
if ((!freak_word_eq(sha256, freak_word_lit("")))) {
int64_t valid = freak_hangar_verify_package(name, pkg_dir, sha256);
if (valid) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  OK")), C_RESET), freak_word_lit(" ")), name), freak_word_lit(" v")), version));
verified += 1;
}
else {
issues += 1;
if (fix_mode) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Reinstalling ")), name), freak_word_lit("...")));
freak_word source2 = freak_array_get(lock_pkg_sources, i);
freak_hangar_install_one(project_dir, name, source2, version);
freak_word new_hash = freak_hangar_compute_dir_sha256(pkg_dir);
if ((!freak_word_eq(new_hash, freak_word_lit("")))) {
freak_array_set(lock_pkg_sha256s, i, new_hash);
}
}
}
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  UNVERIFIED")), C_RESET), freak_word_lit(" ")), name), freak_word_lit(" v")), version), freak_word_lit(" (no checksum in lockfile)")));
if (fix_mode) {
freak_word new_hash2 = freak_hangar_compute_dir_sha256(pkg_dir);
if ((!freak_word_eq(new_hash2, freak_word_lit("")))) {
freak_array_set(lock_pkg_sha256s, i, new_hash2);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Computed SHA-256: ")), freak_word_substring(new_hash2, 0, 16)), freak_word_lit("...")));
verified += 1;
}
}
}
}
i += 1;
}
if (fix_mode) {
freak_lock_write(lockfile);
}
freak_say(freak_word_lit(""));
if ((issues == 0)) {
freak_word ok_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  ALL CLEAR")), C_RESET), freak_word_lit(" ")), freak_word_from_int(verified)), freak_word_lit(" packages verified"));
freak_say(ok_msg);
}
else {
freak_word issue_msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  ")), freak_word_from_int(issues)), freak_word_lit(" issue(s) found")), C_RESET);
freak_say(issue_msg);
if ((fix_mode == false)) {
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  Run 'hangar audit --fix' to auto-repair.")), C_RESET));
}
}
freak_say(freak_word_lit(""));
return issues;
}
int64_t freak_hangar_login(void) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_BMAGENTA, freak_word_lit("  HANGAR LOGIN")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_lit("  Please enter your Hangar API token:"));
freak_word token = freak_process_input();
if (freak_word_eq(token, freak_word_lit(""))) {
freak_say(freak_word_lit("  Login cancelled."));
return 1;
}
freak_word home_dir = freak_process_env(freak_word_lit("HOME"));
if (freak_word_eq(home_dir, freak_word_lit(""))) {
home_dir = freak_word_concat(freak_process_env(freak_word_lit("APPDATA")), freak_word_lit("/freak"));
}
freak_word hangar_dir = freak_word_concat(home_dir, freak_word_lit("/.hangar"));
if ((freak_fs_exists(hangar_dir) == false)) {
freak_fs_make_dir(hangar_dir);
}
freak_word creds_path = freak_word_concat(hangar_dir, freak_word_lit("/credentials"));
freak_fs_write(creds_path, token);
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  SUCCESS")), C_RESET), freak_word_lit(" Token stored in ")), creds_path));
freak_say(freak_word_lit(""));
return 0;
}
int64_t freak_hangar_publish(freak_word project_dir, bool dry_run) {
freak_word manifest = freak_word_concat(project_dir, freak_word_lit("/hangar.toml"));
if ((freak_fs_exists(manifest) == false)) {
freak_say(freak_word_lit("  No hangar.toml found. Cannot publish."));
return 1;
}
freak_toml_load(manifest);
freak_word pname = freak_toml_get(freak_word_lit("project.name"));
freak_word pver = freak_toml_get(freak_word_lit("project.version"));
if ((freak_word_eq(pname, freak_word_lit("")) || freak_word_eq(pver, freak_word_lit("")))) {
freak_say(freak_word_lit("  Invalid hangar.toml: name and version are required."));
return 1;
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BMAGENTA, freak_word_lit("  HANGAR PUBLISH")), C_RESET), freak_word_lit(" ")), C_BWHITE), pname), C_RESET), freak_word_lit(" v")), pver));
freak_say(freak_word_lit(""));
if (dry_run) {
freak_say(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  [DRY RUN] Would include:")), C_RESET));
freak_say(freak_word_lit("    hangar.toml"));
freak_say(freak_word_lit("    src/"));
if (freak_fs_exists(freak_word_concat(project_dir, freak_word_lit("/README.md")))) {
freak_say(freak_word_lit("    README.md"));
}
if (freak_fs_exists(freak_word_concat(project_dir, freak_word_lit("/LICENSE")))) {
freak_say(freak_word_lit("    LICENSE"));
}
freak_say(freak_word_lit(""));
freak_say(freak_word_lit("  Dry run complete. No files uploaded."));
return 0;
}
freak_word tarball = freak_word_concat(freak_word_concat(freak_word_concat(pname, freak_word_lit("-")), pver), freak_word_lit(".tar.gz"));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Packaging ")), tarball), freak_word_lit("...")));
freak_word include_list = freak_word_lit("hangar.toml src");
if (freak_fs_exists(freak_word_concat(project_dir, freak_word_lit("/README.md")))) {
include_list = freak_word_concat(include_list, freak_word_lit(" README.md"));
}
if (freak_fs_exists(freak_word_concat(project_dir, freak_word_lit("/LICENSE")))) {
include_list = freak_word_concat(include_list, freak_word_lit(" LICENSE"));
}
freak_word tar_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("tar -czf "), tarball), freak_word_lit(" ")), include_list);
int64_t tar_res = freak_process_exec(tar_cmd);
if ((tar_res != 0)) {
freak_say(freak_word_lit("  Failed to create tarball. Make sure 'tar' is in your PATH."));
return 1;
}
freak_word home_dir = freak_process_env(freak_word_lit("HOME"));
if (freak_word_eq(home_dir, freak_word_lit(""))) {
home_dir = freak_word_concat(freak_process_env(freak_word_lit("APPDATA")), freak_word_lit("/freak"));
}
freak_word creds_path = freak_word_concat(home_dir, freak_word_lit("/.hangar/credentials"));
if ((freak_fs_exists(creds_path) == false)) {
freak_say(freak_word_concat(freak_word_concat(C_BYELLOW, freak_word_lit("  NOT LOGGED IN")), C_RESET));
freak_say(freak_word_lit("  Run 'hangar login' first."));
return 1;
}
freak_word token = freak_fs_read(creds_path);
freak_word registry = freak_toml_get(freak_word_lit("registries.default"));
if (freak_word_eq(registry, freak_word_lit(""))) {
registry = HANGAR_DEFAULT_REGISTRY;
}
freak_word api_url = freak_word_lit("https://api.hangar.dev/api/v1/publish");
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_DIM, freak_word_lit("  >> ")), C_RESET), freak_word_lit("Uploading to ")), api_url), freak_word_lit("...")));
freak_word curl_cmd = freak_word_concat(freak_word_concat(freak_word_lit("curl -s -X POST -H \"Authorization: Bearer "), token), freak_word_lit("\" "));
curl_cmd = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(curl_cmd, freak_word_lit("-F \"package=@")), tarball), freak_word_lit("\" ")), api_url);
int64_t curl_res = freak_process_exec(curl_cmd);
freak_word rm_cmd = freak_hangar_rm_cmd(tarball);
freak_fs_delete(tarball);
if ((curl_res == 0)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BGREEN, freak_word_lit("  PUBLISHED")), C_RESET), freak_word_lit(" ")), C_BWHITE), pname), C_RESET), freak_word_lit(" v")), pver));
freak_say(freak_word_lit(""));
return 0;
}
else {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_BRED, freak_word_lit("  UPLOAD FAILED")), C_RESET));
return 1;
}
}
freak_word freak_hangar_extract_colon(freak_word s, int64_t idx) {
freak_word res = freak_word_lit("");
int64_t cur_idx = 0;
int64_t i = 0;
int64_t slen = freak_word_length(s);
while (!((i >= slen))) {
freak_word c = freak_word_char_at(s, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
if ((cur_idx == idx)) {
return res;
}
cur_idx += 1;
res = freak_word_lit("");
}
else {
res = freak_word_concat(res, c);
}
i += 1;
}
if ((cur_idx == idx)) {
return res;
}
return freak_word_lit("");
}
void freak_hangar_dispatch(int64_t args_cnt) {
if ((args_cnt < 3)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BMAGENTA, freak_word_lit("  HANGAR")), C_RESET), C_DIM), freak_word_lit(" -- FREAK package manager")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(C_BWHITE, freak_word_lit("  COMMANDS")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    init")), C_RESET), freak_word_lit("                         ")), C_DIM), freak_word_lit("Create new project")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    add")), C_RESET), freak_word_lit(" <name> [constraint]       ")), C_DIM), freak_word_lit("Add dependency with version")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    add")), C_RESET), freak_word_lit(" <name> <repo> [version]  ")), C_DIM), freak_word_lit("Add dependency with git repo")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    remove")), C_RESET), freak_word_lit(" <name>                ")), C_DIM), freak_word_lit("Remove dependency")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    install")), C_RESET), freak_word_lit("                      ")), C_DIM), freak_word_lit("Install all dependencies")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    install freak")), C_RESET), freak_word_lit("                ")), C_DIM), freak_word_lit("Install FREAK compiler")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    update")), C_RESET), freak_word_lit(" [package]              ")), C_DIM), freak_word_lit("Re-resolve and update lockfile")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    outdated")), C_RESET), freak_word_lit("                     ")), C_DIM), freak_word_lit("Check for outdated packages")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    version")), C_RESET), freak_word_lit("                      ")), C_DIM), freak_word_lit("Show project version")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    version")), C_RESET), freak_word_lit(" patch|minor|major    ")), C_DIM), freak_word_lit("Bump version")), C_RESET));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    audit")), C_RESET), freak_word_lit("                        ")), C_DIM), freak_word_lit("Verify package integrity")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    audit")), C_RESET), freak_word_lit(" --fix                 ")), C_DIM), freak_word_lit("Fix integrity issues")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    login")), C_RESET), freak_word_lit("                        ")), C_DIM), freak_word_lit("Authenticate with registry")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(C_BCYAN, freak_word_lit("    publish")), C_RESET), freak_word_lit(" [--dry-run]          ")), C_DIM), freak_word_lit("Publish to registry")), C_RESET));
freak_say(freak_word_lit(""));
return ;
}
freak_word subcmd = freak_hangar_arg(2);
freak_word project_dir = freak_word_lit(".");
if (freak_word_eq(subcmd, freak_word_lit("init"))) {
if ((args_cnt >= 4)) {
project_dir = freak_hangar_arg(3);
}
freak_hangar_init(project_dir);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("add"))) {
if ((args_cnt < 4)) {
freak_say(freak_word_lit("Usage: hangar add <name> [constraint]"));
freak_say(freak_word_lit("       hangar add <name> <repo> [version]"));
return ;
}
freak_word pkg = freak_hangar_arg(3);
if ((args_cnt == 4)) {
freak_hangar_add(project_dir, pkg, freak_word_lit(""), freak_word_lit("latest"));
}
else {
if ((args_cnt == 5)) {
freak_word arg4 = freak_hangar_arg(4);
if (((((freak_word_starts_with(arg4, freak_word_lit("^")) || freak_word_starts_with(arg4, freak_word_lit("~"))) || freak_word_starts_with(arg4, freak_word_lit("="))) || freak_word_starts_with(arg4, freak_word_lit(">"))) || freak_word_starts_with(arg4, freak_word_lit("<")))) {
freak_hangar_add(project_dir, pkg, freak_word_lit(""), arg4);
}
else {
freak_hangar_add(project_dir, pkg, arg4, freak_word_lit("latest"));
}
}
else {
freak_word repo = freak_hangar_arg(4);
freak_word ver = freak_word_lit("latest");
if ((args_cnt >= 6)) {
ver = freak_hangar_arg(5);
}
freak_hangar_add(project_dir, pkg, repo, ver);
}
}
}
else {
if (freak_word_eq(subcmd, freak_word_lit("remove"))) {
if ((args_cnt < 4)) {
freak_say(freak_word_lit("Usage: hangar remove <name>"));
return ;
}
freak_word pkg2 = freak_hangar_arg(3);
freak_hangar_remove(project_dir, pkg2);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("install"))) {
if ((args_cnt >= 4)) {
freak_word install_target = freak_hangar_arg(3);
if (freak_word_eq(install_target, freak_word_lit("freak"))) {
freak_hangar_install_freak();
return ;
}
}
freak_hangar_install(project_dir);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("update"))) {
freak_word update_pkg = freak_word_lit("");
if ((args_cnt >= 4)) {
update_pkg = freak_hangar_arg(3);
}
freak_hangar_update(project_dir, update_pkg);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("outdated"))) {
freak_hangar_outdated(project_dir);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("version"))) {
freak_word bump = freak_word_lit("");
if ((args_cnt >= 4)) {
bump = freak_hangar_arg(3);
}
freak_hangar_version_cmd(project_dir, bump);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("audit"))) {
bool fix_mode = false;
if ((args_cnt >= 4)) {
freak_word arg3 = freak_hangar_arg(3);
if (freak_word_eq(arg3, freak_word_lit("--fix"))) {
fix_mode = true;
}
}
freak_hangar_audit(project_dir, fix_mode);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("login"))) {
freak_hangar_login();
}
else {
if (freak_word_eq(subcmd, freak_word_lit("publish"))) {
bool dry_run = false;
if ((args_cnt >= 4)) {
freak_word arg3 = freak_hangar_arg(3);
if (freak_word_eq(arg3, freak_word_lit("--dry-run"))) {
dry_run = true;
}
}
freak_hangar_publish(project_dir, dry_run);
}
else {
freak_word msg = freak_word_concat(freak_word_lit("Unknown hangar command: "), subcmd);
freak_say(msg);
freak_say(freak_word_lit("Run 'hangar' for usage."));
}
}
}
}
}
}
}
}
}
}
}
int64_t freak_cli_install_clang(freak_word os_tag) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Attempting to install clang...")), C_RESET));
if (freak_word_eq(os_tag, freak_word_lit("windows"))) {
int64_t wg_res = freak_process_exec(freak_word_lit("winget install LLVM.LLVM --silent --accept-package-agreements --accept-source-agreements"));
if ((wg_res == 0)) {
return 0;
}
int64_t choco_res = freak_process_exec(freak_word_lit("choco install llvm -y"));
if ((choco_res == 0)) {
return 0;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("  Auto-install failed. Install manually:")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_CYAN), freak_word_lit("winget install LLVM.LLVM")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_CYAN), freak_word_lit("choco install llvm")), C_RESET));
freak_say(freak_word_lit("    https://github.com/llvm/llvm-project/releases"));
return 1;
}
else {
if (freak_word_eq(os_tag, freak_word_lit("linux"))) {
int64_t apt_res = freak_process_exec(freak_word_lit("sudo apt-get install -y clang lld"));
if ((apt_res == 0)) {
return 0;
}
int64_t dnf_res = freak_process_exec(freak_word_lit("sudo dnf install -y clang lld"));
if ((dnf_res == 0)) {
return 0;
}
int64_t pacman_res = freak_process_exec(freak_word_lit("sudo pacman -S --noconfirm clang lld"));
if ((pacman_res == 0)) {
return 0;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BYELLOW), freak_word_lit("  Could not auto-install. Try:")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_CYAN), freak_word_lit("sudo apt install clang lld")), C_RESET), freak_word_lit("  (Debian/Ubuntu)")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_CYAN), freak_word_lit("sudo dnf install clang lld")), C_RESET), freak_word_lit("  (Fedora)")));
return 1;
}
else {
if (freak_word_eq(os_tag, freak_word_lit("macos"))) {
int64_t brew_res = freak_process_exec(freak_word_lit("brew install llvm"));
if ((brew_res == 0)) {
return 0;
}
freak_process_exec(freak_word_lit("xcode-select --install"));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("If prompted, complete the Xcode CLT install then rerun 'freak doctor'")), C_RESET));
return 0;
}
}
}
return 1;
}
void freak_cli_doctor(bool fix_mode) {
freak_word os_tag = freak_word_lit("unix");
bool is_win = false;
freak_word windir_env = freak_process_env(freak_word_lit("WINDIR"));
if ((!freak_word_eq(windir_env, freak_word_lit("")))) {
os_tag = freak_word_lit("windows");
is_win = true;
}
else {
freak_word uname_out = freak_process_exec_capture(freak_word_lit("uname -s 2>/dev/null"));
if (freak_word_contains(uname_out, freak_word_lit("Darwin"))) {
os_tag = freak_word_lit("macos");
}
else {
os_tag = freak_word_lit("linux");
}
}
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(50));
if (fix_mode) {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G1), SYM_GEAR), freak_word_lit(" FREAK DOCTOR")), C_RESET), C_DIM), freak_word_lit(" --fix  repairing...")), C_RESET), 50));
}
else {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G1), SYM_GEAR), freak_word_lit(" FREAK DOCTOR")), C_RESET), C_DIM), freak_word_lit("  diagnosing your setup...")), C_RESET), 50));
}
freak_say(freak_cli_box_bot(50));
freak_say(freak_word_lit(""));
bool all_ok = true;
int64_t checks_passed = 0;
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("[1/5]")), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("Checking")), C_RESET), freak_word_lit(" clang")));
int64_t clang_exit = freak_process_exec(freak_word_lit("clang --version"));
if ((clang_exit == 0)) {
freak_word clang_ver = freak_process_exec_capture(freak_word_lit("clang --version"));
freak_word cv_line = freak_word_lit("");
int64_t cvi = 0;
bool cv_done = false;
while (!(cv_done)) {
if ((cvi >= freak_word_length(clang_ver))) {
cv_done = true;
}
else {
freak_word cch = freak_word_char_at(clang_ver, cvi);
if ((freak_word_eq(cch, freak_word_lit("\n")) || freak_word_eq(cch, freak_word_lit("\r")))) {
cv_done = true;
}
else {
cv_line = freak_word_concat(cv_line, cch);
}
}
cvi += 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" ")), C_DIM), cv_line), C_RESET));
checks_passed += 1;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" clang ")), C_RED), freak_word_lit("not found")), C_RESET));
all_ok = false;
if (fix_mode) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Attempting auto-install...")), C_RESET));
int64_t clang_fix = freak_cli_install_clang(os_tag);
if ((clang_fix == 0)) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" clang installed!")));
checks_passed += 1;
all_ok = true;
}
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Fix: ")), C_RESET), freak_word_lit("run ")), C_BWHITE), freak_word_lit("freak doctor --fix")), C_RESET));
if (is_win) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("         or: "), C_CYAN), freak_word_lit("winget install LLVM.LLVM")), C_RESET));
}
else {
if (freak_word_eq(os_tag, freak_word_lit("linux"))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("         or: "), C_CYAN), freak_word_lit("sudo apt install clang lld")), C_RESET));
}
else {
if (freak_word_eq(os_tag, freak_word_lit("macos"))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("         or: "), C_CYAN), freak_word_lit("xcode-select --install")), C_RESET));
}
}
}
}
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("[2/5]")), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("Checking")), C_RESET), freak_word_lit(" lld linker")));
bool lld_found = false;
if (is_win) {
int64_t lld_exit = freak_process_exec(freak_word_lit("where lld-link"));
if ((lld_exit == 0)) {
lld_found = true;
}
}
else {
int64_t lld_exit = freak_process_exec(freak_word_lit("ld.lld --version"));
if ((lld_exit == 0)) {
lld_found = true;
}
}
if (lld_found) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" lld found ")), C_DIM), freak_word_lit("(bundle mode available)")), C_RESET));
checks_passed += 1;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BYELLOW), SYM_RING), C_RESET), freak_word_lit(" lld not found ")), C_DIM), freak_word_lit("(optional — clang can link too)")), C_RESET));
checks_passed += 1;
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("[3/5]")), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("Checking")), C_RESET), freak_word_lit(" runtime")));
freak_word rt_dir = freak_cli_find_runtime_dir();
if ((!freak_word_eq(rt_dir, freak_word_lit("")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" ")), C_DIM), rt_dir), C_RESET));
bool has_obj = false;
if (is_win) {
has_obj = freak_fs_exists(freak_word_concat(rt_dir, freak_word_lit("/freak_runtime.obj")));
}
else {
has_obj = freak_fs_exists(freak_word_concat(rt_dir, freak_word_lit("/freak_runtime.o")));
}
if (has_obj) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), C_DIM), freak_word_lit(" pre-compiled objects (fast bundle mode)")), C_RESET));
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BYELLOW), SYM_RING), C_RESET), C_DIM), freak_word_lit(" no pre-compiled objects (source fallback active)")), C_RESET));
}
if (freak_fs_exists(freak_word_concat(rt_dir, freak_word_lit("/freak_llvm_runtime.c")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), C_DIM), freak_word_lit(" LLVM runtime available")), C_RESET));
}
checks_passed += 1;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" runtime directory not found")));
all_ok = false;
if (fix_mode) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Downloading runtime...")), C_RESET));
freak_hangar_install_freak();
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Fix: ")), C_RESET), freak_word_lit("run ")), C_BWHITE), freak_word_lit("freak upgrade")), C_RESET), freak_word_lit(" or re-run install script")));
}
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("[4/5]")), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("Checking")), C_RESET), freak_word_lit(" standard library")));
freak_word std_dir = freak_cli_find_std_dir();
if ((!freak_word_eq(std_dir, freak_word_lit("")))) {
int64_t mod_count = 0;
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/math.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/math3d.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/zip.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/string.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/convert.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/algorithm.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/json.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/http.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/version.fk")))) {
mod_count += 1;
}
if (freak_fs_exists(freak_word_concat(std_dir, freak_word_lit("/runtime.fk")))) {
mod_count += 1;
}
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" ")), freak_word_from_int(mod_count)), freak_word_lit("/10 modules in ")), C_DIM), std_dir), C_RESET));
checks_passed += 1;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" standard library not found")));
all_ok = false;
if (fix_mode) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Re-run upgrade to download std...")), C_RESET));
freak_hangar_install_freak();
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_DIM), freak_word_lit("Fix: ")), C_RESET), freak_word_lit("run ")), C_BWHITE), freak_word_lit("freak upgrade")), C_RESET));
}
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("[5/5]")), C_RESET), freak_word_lit(" ")), C_DIM), freak_word_lit("Checking")), C_RESET), freak_word_lit(" compile pipeline")));
if (((clang_exit == 0) && (!freak_word_eq(rt_dir, freak_word_lit(""))))) {
freak_word test_src = freak_word_lit("say \"FREAK doctor test\"");
freak_word test_path = freak_word_lit("_freak_doctor_test.fk");
freak_fs_write(test_path, test_src);
freak_word transpiled = freak_cli_transpile(test_path, test_src, freak_word_lit("llvm"));
if ((!freak_word_eq(transpiled, freak_word_lit("")))) {
freak_word bin = freak_cli_build_binary(transpiled, test_path, freak_word_lit("llvm"), freak_word_lit("2"), freak_word_lit(""));
if ((!freak_word_eq(bin, freak_word_lit("")))) {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" full pipeline works")));
freak_fs_delete(bin);
checks_passed += 1;
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" clang compilation error (see above)")));
all_ok = false;
}
freak_fs_delete(transpiled);
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BRED), SYM_CROSS), C_RESET), freak_word_lit(" transpilation error")));
all_ok = false;
}
freak_fs_delete(test_path);
}
else {
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("        "), C_BYELLOW), SYM_RING), C_RESET), C_DIM), freak_word_lit(" skipped (fix missing clang/runtime first)")), C_RESET));
}
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(50));
if (all_ok) {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_BGREEN), SYM_SPARK), freak_word_lit(" ALL SYSTEMS GO")), C_RESET), freak_word_lit("  ")), C_DIM), freak_word_from_int(checks_passed)), freak_word_lit("/5 passed")), C_RESET), 50));
freak_say(freak_cli_box_sep(50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Get started:")), C_RESET), freak_word_lit("  freak build hello.fk")), 50));
}
else {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_BRED), SYM_CROSS), freak_word_lit(" ISSUES FOUND")), C_RESET), freak_word_lit("  ")), C_DIM), freak_word_from_int(checks_passed)), freak_word_lit("/5 passed")), C_RESET), 50));
freak_say(freak_cli_box_sep(50));
if (fix_mode) {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Run "), C_BWHITE), freak_word_lit("freak doctor")), C_RESET), freak_word_lit(" to verify fixes")), 50));
}
else {
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  Run "), C_BWHITE), freak_word_lit("freak doctor --fix")), C_RESET), freak_word_lit(" to auto-repair")), 50));
}
}
freak_say(freak_cli_box_bot(50));
freak_say(freak_word_lit(""));
}
int64_t freak_cli_audit_dispatch(freak_word subcmd, int64_t args_cnt) {
freak_word cmd = freak_word_concat(freak_word_lit("python -m freakc "), subcmd);
int64_t ai = 2;
while (!((ai >= args_cnt))) {
freak_word extra = freak_process_arg(ai);
cmd = freak_word_concat(freak_word_concat(cmd, freak_word_lit(" ")), extra);
ai += 1;
}
int64_t exit_code = freak_process_exec(cmd);
if ((exit_code != 0)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Note: audit commands currently shell out to the Python CLI.")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("If Python is missing, install Python 3.10+ and try again.")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("(Native FREAK port of the auditor lands in V4.)")), C_RESET));
}
return exit_code;
}
freak_word freak_cli_learn_quote_arg(freak_word arg) {
return freak_word_concat(freak_word_concat(freak_word_lit("\""), freak_word_replace(arg, freak_word_lit("\""), freak_word_lit("\\\""))), freak_word_lit("\""));
}
int64_t freak_cli_learn_dispatch(int64_t args_cnt) {
freak_word cmd = freak_word_lit("python -m freakc learn");
int64_t ai = 2;
while (!((ai >= args_cnt))) {
freak_word extra = freak_process_arg(ai);
cmd = freak_word_concat(freak_word_concat(cmd, freak_word_lit(" ")), freak_cli_learn_quote_arg(extra));
ai += 1;
}
int64_t exit_code = freak_process_exec(cmd);
if ((exit_code != 0)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Note: `freak learn` currently shells out to the Python Academy CLI.")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("If Python is missing, install Python 3.10+ and try again.")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("(The FREAK-native Academy rewrite lands after the V4 query surface is ready.)")), C_RESET));
}
return exit_code;
}
freak_word freak_cli_parse_flags(int64_t start_idx, int64_t args_cnt) {
freak_word target = freak_word_lit("llvm");
freak_word opt = freak_word_lit("2");
freak_word cross = freak_word_lit("");
strict_borrow = false;
int64_t fi = start_idx;
while (!((fi >= args_cnt))) {
freak_word flag = freak_process_arg(fi);
if (freak_word_eq(flag, freak_word_lit("--c"))) {
target = freak_word_lit("c");
}
else {
if (freak_word_eq(flag, freak_word_lit("--llvm"))) {
target = freak_word_lit("llvm");
}
else {
if (freak_word_eq(flag, freak_word_lit("--strict-borrow"))) {
strict_borrow = true;
}
else {
if (freak_word_starts_with(flag, freak_word_lit("--opt="))) {
opt = freak_word_char_at(flag, 6);
}
else {
if (freak_word_starts_with(flag, freak_word_lit("--target="))) {
int64_t ti = 9;
freak_word tval = freak_word_lit("");
while (!((ti >= freak_word_length(flag)))) {
tval = freak_word_concat(tval, freak_word_char_at(flag, ti));
ti += 1;
}
cross = tval;
}
}
}
}
}
fi += 1;
}
return freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(target, freak_word_lit(":")), opt), freak_word_lit(":")), cross);
}
freak_word freak_cli_extract_flag(freak_word flags, int64_t idx) {
freak_word res = freak_word_lit("");
int64_t current = 0;
int64_t i = 0;
int64_t flen = freak_word_length(flags);
while (!((i >= flen))) {
freak_word c = freak_word_char_at(flags, i);
if (freak_word_eq(c, freak_word_lit(":"))) {
if ((current == idx)) {
return res;
}
current += 1;
res = freak_word_lit("");
}
else {
res = freak_word_concat(res, c);
}
i += 1;
}
if ((current == idx)) {
return res;
}
return freak_word_lit("");
}
void freak_cli_flex(void) {
freak_cli_show_banner();
freak_say(freak_cli_box_top(50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G1), SYM_FIRE), freak_word_lit(" FREAK FLEXING")), C_RESET), 50));
freak_say(freak_cli_box_sep(50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Language")), C_RESET), freak_word_lit("        FREAK ")), C_DIM), freak_word_lit("(.fk)")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Version")), C_RESET), freak_word_lit("         ")), CLI_VERSION), freak_word_lit(" ")), C_DIM), CLI_CODENAME), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Self-hosting")), C_RESET), freak_word_lit("    ")), C_BGREEN), SYM_CHECK), freak_word_lit(" YES")), C_RESET), C_DIM), freak_word_lit(" (compiler compiles itself)")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Backends")), C_RESET), freak_word_lit("        ")), C_BCYAN), freak_word_lit("LLVM IR")), C_RESET), freak_word_lit(" + ")), C_BYELLOW), freak_word_lit("C")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Cross-compile")), C_RESET), freak_word_lit("   ")), C_BGREEN), SYM_CHECK), freak_word_lit(" YES")), C_RESET), C_DIM), freak_word_lit(" (--target=TRIPLE)")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Package mgr")), C_RESET), freak_word_lit("     ")), C_BGREEN), SYM_CHECK), freak_word_lit(" Hangar")), C_RESET), C_DIM), freak_word_lit(" (built-in)")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("GUI framework")), C_RESET), freak_word_lit("   ")), C_BGREEN), SYM_CHECK), freak_word_lit(" freak-ui")), C_RESET), C_DIM), freak_word_lit(" (immediate mode)")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Platforms")), C_RESET), freak_word_lit("       ")), C_BCYAN), freak_word_lit("Windows")), C_RESET), freak_word_lit(" / ")), C_BGREEN), freak_word_lit("Linux")), C_RESET), freak_word_lit(" / ")), C_BWHITE), freak_word_lit("macOS")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Std library")), C_RESET), freak_word_lit("     ")), C_DIM), freak_word_lit("math, string, json, http, fs...")), C_RESET), 50));
freak_say(freak_cli_box_sep(50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Aesthetic")), C_RESET), freak_word_lit("       ")), C_G1), freak_word_lit("A")), C_G2), freak_word_lit("n")), C_G3), freak_word_lit("i")), C_G4), freak_word_lit("m")), C_G5), freak_word_lit("e")), C_G6), freak_word_lit("-")), C_G1), freak_word_lit("c")), C_G2), freak_word_lit("o")), C_G3), freak_word_lit("r")), C_G4), freak_word_lit("e")), C_RESET), 50));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BWHITE), freak_word_lit("Vibe")), C_RESET), freak_word_lit("            ")), C_BMAGENTA), freak_word_lit("MAXIMUM")), C_RESET), 50));
freak_say(freak_cli_box_bot(50));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_word_lit("\"My compiler compiles itself. Does yours?\"")), C_RESET));
freak_say(freak_word_lit(""));
}
void freak_cli_init(freak_word project_name) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G1), SYM_SPARK), freak_word_lit(" Creating project: ")), C_RESET), C_BWHITE), project_name), C_RESET));
freak_say(freak_word_lit(""));
freak_word mkdir_cmd = freak_word_concat(freak_word_lit("mkdir "), project_name);
freak_process_exec(mkdir_cmd);
freak_word main_content = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("-- "), project_name), freak_word_lit("\n-- Created with FREAK ")), CLI_VERSION), freak_word_lit("\n\nsay \"Hello from ")), project_name), freak_word_lit("!\"\n"));
freak_fs_write(freak_word_concat(project_name, freak_word_lit("/main.fk")), main_content);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" ")), project_name), freak_word_lit("/main.fk")));
freak_word toml_content = freak_word_concat(freak_word_concat(freak_word_lit("[project]\nname = \""), project_name), freak_word_lit("\"\nversion = \"0.1.0\"\n\n[dependencies]\n"));
freak_fs_write(freak_word_concat(project_name, freak_word_lit("/hangar.toml")), toml_content);
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_CHECK), C_RESET), freak_word_lit(" ")), project_name), freak_word_lit("/hangar.toml")));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Get started:")), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_BWHITE), freak_word_lit("cd ")), project_name), C_RESET));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("    "), C_BWHITE), freak_word_lit("freak run main.fk")), C_RESET));
freak_say(freak_word_lit(""));
}
void freak_hangar_standalone_main(void) {
int64_t args_cnt = freak_process_args_count();
hangar_arg_offset = 1;
freak_hangar_dispatch((args_cnt + 1));
}
void freak_freakc_cli_main(void) {
int64_t args_cnt = freak_process_args_count();
freak_word argv0 = freak_process_arg(0);
if ((freak_word_ends_with(argv0, freak_word_lit("hangar")) || freak_word_ends_with(argv0, freak_word_lit("hangar.exe")))) {
freak_hangar_standalone_main();
return ;
}
if ((args_cnt < 2)) {
freak_cli_show_help();
return ;
}
freak_word subcmd = freak_process_arg(1);
if ((freak_word_eq(subcmd, freak_word_lit("--version")) || freak_word_eq(subcmd, freak_word_lit("-V")))) {
freak_cli_show_version();
return ;
}
if (((freak_word_eq(subcmd, freak_word_lit("--help")) || freak_word_eq(subcmd, freak_word_lit("-h"))) || freak_word_eq(subcmd, freak_word_lit("help")))) {
freak_cli_show_help();
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("version"))) {
freak_cli_show_version();
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("flex"))) {
freak_cli_flex();
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("init"))) {
if ((args_cnt < 3)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" init requires a project name.")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Usage: ")), C_RESET), freak_word_lit("freak init <project-name>")));
freak_say(freak_word_lit(""));
return ;
}
freak_cli_init(freak_process_arg(2));
return ;
}
if ((((freak_word_eq(subcmd, freak_word_lit("build")) || freak_word_eq(subcmd, freak_word_lit("run"))) || freak_word_eq(subcmd, freak_word_lit("check"))) || freak_word_eq(subcmd, freak_word_lit("transpile")))) {
if ((args_cnt < 3)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" ")), subcmd), freak_word_lit(" requires a file argument.")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Usage: ")), C_RESET), freak_word_lit("freak ")), subcmd), freak_word_lit(" <file.fk> [options]")));
freak_say(freak_word_lit(""));
return ;
}
freak_word src_file = freak_process_arg(2);
freak_word flags = freak_cli_parse_flags(3, args_cnt);
freak_word target = freak_cli_extract_flag(flags, 0);
freak_word opt = freak_cli_extract_flag(flags, 1);
freak_word cross = freak_cli_extract_flag(flags, 2);
if (freak_word_eq(subcmd, freak_word_lit("build"))) {
freak_word binary = freak_cli_build(src_file, target, opt, cross);
if (freak_word_eq(binary, freak_word_lit(""))) {
freak_process_exit(1);
}
}
else {
if (freak_word_eq(subcmd, freak_word_lit("run"))) {
freak_cli_run(src_file, target, opt, cross);
}
else {
if (freak_word_eq(subcmd, freak_word_lit("check"))) {
freak_word source = freak_fs_read(src_file);
if (freak_word_eq(source, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" Could not read file: ")), C_BWHITE), src_file), C_RESET));
freak_say(freak_word_lit(""));
freak_process_exit(1);
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_G3), SYM_GEAR), freak_word_lit(" CHECKING")), C_RESET), freak_word_lit(" ")), C_BWHITE), src_file), C_RESET));
freak_say(freak_word_lit(""));
freak_init_arrays();
freak_cli_step_start();
freak_tokenize(source);
freak_cli_step_done(freak_word_lit("Lexing"));
freak_cli_step_start();
freak_parse_program();
freak_cli_step_done(freak_word_lit("Parsing"));
freak_cli_step_start();
freak_check_program();
freak_cli_step_done(freak_word_lit("Type checking"));
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BGREEN), SYM_SPARK), freak_word_lit(" PASSED")), C_RESET), C_DIM), freak_word_lit(" -- no type errors found")), C_RESET));
freak_say(freak_word_lit(""));
}
else {
if (freak_word_eq(subcmd, freak_word_lit("transpile"))) {
freak_word source = freak_fs_read(src_file);
if (freak_word_eq(source, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" Could not read file: ")), src_file));
freak_say(freak_word_lit(""));
freak_process_exit(1);
}
freak_word transpiled = freak_cli_transpile(src_file, source, target);
if (freak_word_eq(transpiled, freak_word_lit(""))) {
freak_process_exit(1);
}
}
}
}
}
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("upgrade"))) {
freak_say(freak_word_lit(""));
freak_say(freak_cli_box_top(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit(" "), C_G1), SYM_ROCKET), freak_word_lit(" FREAK UPGRADE")), C_RESET), 45));
freak_say(freak_cli_box_sep(45));
freak_say(freak_cli_box_mid(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Current: ")), C_RESET), C_BWHITE), CLI_VERSION), C_RESET), freak_word_lit(" ")), C_DIM), CLI_CODENAME), C_RESET), 45));
freak_say(freak_cli_box_bot(45));
freak_say(freak_word_lit(""));
int64_t upgrade_res = freak_hangar_install_freak();
if ((upgrade_res == 0)) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), C_ITALIC), freak_cli_random_quote(freak_time_now_ms())), C_RESET));
freak_say(freak_word_lit(""));
}
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("doctor"))) {
bool fix_mode = false;
if ((args_cnt >= 3)) {
if (freak_word_eq(freak_process_arg(2), freak_word_lit("--fix"))) {
fix_mode = true;
}
}
freak_cli_doctor(fix_mode);
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("hangar"))) {
freak_hangar_dispatch(args_cnt);
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("learn"))) {
int64_t learn_exit = freak_cli_learn_dispatch(args_cnt);
if ((learn_exit != 0)) {
freak_process_exit(learn_exit);
}
return ;
}
if (((((freak_word_eq(subcmd, freak_word_lit("audit-science")) || freak_word_eq(subcmd, freak_word_lit("audit-trust"))) || freak_word_eq(subcmd, freak_word_lit("audit-miracles"))) || freak_word_eq(subcmd, freak_word_lit("foreshadow-audit"))) || freak_word_eq(subcmd, freak_word_lit("audit-conformance")))) {
int64_t audit_exit = freak_cli_audit_dispatch(subcmd, args_cnt);
if ((audit_exit != 0)) {
freak_process_exit(audit_exit);
}
return ;
}
if (freak_word_eq(subcmd, freak_word_lit("test"))) {
int64_t test_exit = freak_process_exec(freak_word_lit("python tests/suite/run_tests.py"));
if ((test_exit != 0)) {
freak_process_exit(test_exit);
}
return ;
}
if (freak_word_ends_with(subcmd, freak_word_lit(".fk"))) {
freak_word flags = freak_cli_parse_flags(2, args_cnt);
freak_word target = freak_cli_extract_flag(flags, 0);
freak_word source = freak_fs_read(subcmd);
if (freak_word_eq(source, freak_word_lit(""))) {
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" Could not read file: ")), subcmd));
freak_say(freak_word_lit(""));
freak_process_exit(1);
}
freak_word msg = freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("FREAK v2 Compiling: "), subcmd), freak_word_lit(" (Target: ")), target), freak_word_lit(")"));
freak_say(msg);
freak_word transpiled = freak_cli_transpile(subcmd, source, target);
if (freak_word_eq(transpiled, freak_word_lit(""))) {
freak_process_exit(1);
}
return ;
}
freak_say(freak_word_lit(""));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_BRED), SYM_CROSS), freak_word_lit(" ERROR")), C_RESET), freak_word_lit(" Unknown command '")), C_BWHITE), subcmd), C_RESET), freak_word_lit("'")));
freak_say(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_concat(freak_word_lit("  "), C_DIM), freak_word_lit("Run '")), C_RESET), freak_word_lit("freak help")), C_DIM), freak_word_lit("' for usage.")), C_RESET));
freak_say(freak_word_lit(""));
}
void freak_main(void) {
FREAKC_VERSION = freak_word_lit("0.13.3");
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
EXPR_ARRAY_LIT = freak_word_lit("12");
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
ast_stmt_lines = 0;
ast_top_stmts = 0;
ast_pilot_is_mut = 0;
strict_borrow = false;
bc_sym_names = 0;
bc_sym_kinds = 0;
bc_sym_is_mut = 0;
bc_sym_state = 0;
bc_sym_scopes = 0;
bc_sym_lines = 0;
bc_sym_count = 0;
bc_scope_depth = 0;
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
llvm_dbg_md = freak_word_lit("");
llvm_dbg_next_id = 0;
llvm_dbg_file_id = 0;
llvm_dbg_cu_id = 0;
llvm_dbg_empty_id = 0;
llvm_dbg_subroutine_type_id = 0;
llvm_dbg_current_scope_id = 0;
llvm_dbg_current_line = 0;
llvm_dbg_current_dir = freak_word_lit(".");
llvm_dbg_current_file = freak_word_lit("");
input_file = freak_word_lit("");
opt_level = freak_word_lit("2");
cross_target = freak_word_lit("");
source_line_offset = 0;
CLI_VERSION = freak_word_lit("0.13.3");
CLI_CODENAME = freak_word_lit("Shiranui");
C_RESET = freak_word_lit("\x1b[0m");
C_BOLD = freak_word_lit("\x1b[1m");
C_DIM = freak_word_lit("\x1b[2m");
C_ITALIC = freak_word_lit("\x1b[3m");
C_ULINE = freak_word_lit("\x1b[4m");
C_BLINK = freak_word_lit("\x1b[5m");
C_STRIKE = freak_word_lit("\x1b[9m");
C_RED = freak_word_lit("\x1b[31m");
C_GREEN = freak_word_lit("\x1b[32m");
C_YELLOW = freak_word_lit("\x1b[33m");
C_BLUE = freak_word_lit("\x1b[34m");
C_MAGENTA = freak_word_lit("\x1b[35m");
C_CYAN = freak_word_lit("\x1b[36m");
C_WHITE = freak_word_lit("\x1b[37m");
C_BRED = freak_word_lit("\x1b[1;31m");
C_BGREEN = freak_word_lit("\x1b[1;32m");
C_BYELLOW = freak_word_lit("\x1b[1;33m");
C_BBLUE = freak_word_lit("\x1b[1;34m");
C_BMAGENTA = freak_word_lit("\x1b[1;35m");
C_BCYAN = freak_word_lit("\x1b[1;36m");
C_BWHITE = freak_word_lit("\x1b[1;37m");
C_G1 = freak_word_lit("\x1b[38;2;255;100;200m");
C_G2 = freak_word_lit("\x1b[38;2;220;80;220m");
C_G3 = freak_word_lit("\x1b[38;2;180;70;240m");
C_G4 = freak_word_lit("\x1b[38;2;140;80;255m");
C_G5 = freak_word_lit("\x1b[38;2;100;120;255m");
C_G6 = freak_word_lit("\x1b[38;2;60;180;255m");
C_BG_DARK = freak_word_lit("\x1b[48;2;20;20;30m");
BOX_TL = freak_word_lit("\xe2\x95\xad");
BOX_TR = freak_word_lit("\xe2\x95\xae");
BOX_BL = freak_word_lit("\xe2\x95\xb0");
BOX_BR = freak_word_lit("\xe2\x95\xaf");
BOX_H = freak_word_lit("\xe2\x94\x80");
BOX_V = freak_word_lit("\xe2\x94\x82");
BOX_VR = freak_word_lit("\xe2\x94\x9c");
BOX_VL = freak_word_lit("\xe2\x94\xa4");
SYM_CHECK = freak_word_lit("\xe2\x9c\x93");
SYM_CROSS = freak_word_lit("\xe2\x9c\x97");
SYM_SPARK = freak_word_lit("\xe2\x9c\xa8");
SYM_BOLT = freak_word_lit("\xe2\x9a\xa1");
SYM_GEAR = freak_word_lit("\xe2\x9a\x99");
SYM_ARROW = freak_word_lit("\xe2\x96\xb8");
SYM_DOT = freak_word_lit("\xe2\x97\x8f");
SYM_RING = freak_word_lit("\xe2\x97\x8b");
SYM_STAR = freak_word_lit("\xe2\x98\x85");
SYM_SKULL = freak_word_lit("\xe2\x98\xa0");
SYM_ROCKET = freak_word_lit("\xf0\x9f\x9a\x80");
SYM_FIRE = freak_word_lit("\xf0\x9f\x94\xa5");
toml_keys_arr = 0;
toml_vals_arr = 0;
toml_count = 0;
lock_pkg_names = 0;
lock_pkg_versions = 0;
lock_pkg_sources = 0;
lock_pkg_sha256s = 0;
lock_pkg_count = 0;
cli_build_start_ms = 0;
cli_step_ms = 0;
HANGAR_DEFAULT_REGISTRY = freak_word_lit("https://index.hangar.dev");
hangar_arg_offset = 0;
resolve_names = 0;
resolve_versions = 0;
resolve_sources = 0;
resolve_constraints = 0;
resolve_requested_by = 0;
resolve_count = 0;
freak_freakc_cli_main();
}
int main(int argc, char** argv) {
    freak_argc = argc;
    freak_argv = argv;
    freak_enable_ansi();
    freak_main();
    return 0;
}
