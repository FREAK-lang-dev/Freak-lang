; FREAK LLVM IR Generator (v3)

declare i32 @puts(i8*)
declare i32 @printf(i8*, ...)
declare i64 @strlen(i8*)
declare i64 @freak_llvm_word_from_int(i64)
declare i64 @freak_llvm_word_from_bool(i64)
declare i64 @freak_llvm_word_concat(i64, i64)
declare i64 @freak_llvm_word_eq(i64, i64)
declare i64 @freak_llvm_word_neq(i64, i64)
declare i64 @freak_llvm_word_length(i64)
declare i64 @freak_llvm_word_char_at(i64, i64)
declare i64 @freak_llvm_word_contains(i64, i64)
declare i64 @freak_llvm_word_starts_with(i64, i64)
declare i64 @freak_llvm_word_ends_with(i64, i64)
declare i64 @freak_llvm_word_to_upper(i64)
declare i64 @freak_llvm_word_to_lower(i64)
declare i64 @freak_llvm_word_trim(i64)
declare i64 @freak_llvm_word_replace(i64, i64, i64)
declare i64 @freak_llvm_word_to_int(i64)
declare void @freak_llvm_say(i64)
declare void @freak_llvm_print_str(i64)
declare void @freak_llvm_print_int(i64)
declare void @freak_llvm_print_newline()
declare i64 @freak_llvm_ask(i64)
declare i64 @freak_llvm_process_args_count()
declare i64 @freak_llvm_process_arg(i64)
declare void @freak_llvm_process_exit(i64)
declare i64 @freak_llvm_process_exec(i64)
declare i64 @freak_llvm_process_exec_capture(i64)
declare void @freak_llvm_panic(i64)
declare i64 @freak_llvm_shape_alloc(i64)
declare i64 @freak_llvm_shape_get(i64, i64)
declare void @freak_llvm_shape_set(i64, i64, i64)
declare void @freak_llvm_setup_args(i64, i64)
declare i64 @freak_llvm_word_from_num(i64)
declare void @freak_llvm_print_num(i64)
declare i64 @freak_llvm_int_to_num(i64)
declare i64 @freak_llvm_num_to_int(i64)
declare i64 @freak_llvm_ui_create_window(i64, i64, i64, i64)
declare void @freak_llvm_ui_destroy_window(i64)
declare i64 @freak_llvm_ui_poll_events(i64)
declare void @freak_llvm_ui_begin_frame(i64)
declare void @freak_llvm_ui_end_frame(i64)
declare i64 @freak_llvm_ui_event_kind(i64)
declare i64 @freak_llvm_ui_event_key(i64)
declare i64 @freak_llvm_ui_event_pressed(i64)
declare i64 @freak_llvm_ui_event_character(i64)
declare i64 @freak_llvm_ui_event_mouse_x(i64)
declare i64 @freak_llvm_ui_event_mouse_y(i64)
declare i64 @freak_llvm_ui_event_button(i64)
declare void @freak_llvm_ui_clear(i64, i64, i64, i64, i64)
declare void @freak_llvm_ui_fill_rect(i64, i64, i64, i64, i64, i64, i64, i64, i64)
declare void @freak_llvm_ui_stroke_rect(i64, i64, i64, i64, i64, i64, i64, i64, i64)
declare void @freak_llvm_ui_fill_circle(i64, i64, i64, i64, i64, i64, i64, i64)
declare void @freak_llvm_ui_draw_line(i64, i64, i64, i64, i64, i64, i64, i64, i64)
declare i64 @freak_llvm_ui_draw_text(i64, i64, i64, i64, i64, i64, i64, i64, i64, i64)
declare i64 @freak_llvm_ui_measure_text(i64, i64, i64, i64)
declare i64 @freak_llvm_math_sqrt(i64)
declare i64 @freak_llvm_math_pow(i64, i64)
declare i64 @freak_llvm_math_sin(i64)
declare i64 @freak_llvm_math_cos(i64)
declare i64 @freak_llvm_math_tan(i64)
declare i64 @freak_llvm_math_floor(i64)
declare i64 @freak_llvm_math_ceil(i64)
declare i64 @freak_llvm_parse_num(i64)
declare i64 @freak_llvm_format_num(i64)
declare i64 @freak_word_compare(i64, i64)
declare i64 @freak_llvm_array_new()
declare void @freak_llvm_array_push(i64, i64)
declare i64 @freak_llvm_array_get(i64, i64)
declare i64 @freak_llvm_array_len(i64)
declare void @freak_llvm_array_set(i64, i64, i64)
declare i64 @freak_llvm_tcp_connect(i64, i64)
declare i64 @freak_llvm_tcp_send(i64, i64)
declare i64 @freak_llvm_tcp_recv(i64, i64)
declare i64 @freak_llvm_tcp_recv_all(i64, i64)
declare void @freak_llvm_tcp_close(i64)

@g_json_types = global i64 0
@g_json_vals = global i64 0
@g_json_children = global i64 0
@g_json_keys = global i64 0
@g_json_count = global i64 0
@g_json_inited = global i64 0
@g_json_src = global i64 0
@g_json_pos = global i64 0
@g_json_len = global i64 0
@g_http_resp_statuses = global i64 0
@g_http_resp_bodies = global i64 0
@g_http_resp_headers_raw = global i64 0
@g_http_resp_count = global i64 0
@g_http_inited = global i64 0
@g_a = global i64 0
@g_b = global i64 0
@g_neg = global i64 0

declare i64 @freak_fopen(i64, i64)
declare i64 @freak_fclose(i64)
declare i64 @freak_fseek(i64, i64, i64)
declare i64 @freak_ftell(i64)
declare i64 @freak_fread(i64, i64, i64, i64)
declare i64 @freak_fwrite(i64, i64, i64, i64)
declare i64 @freak_calloc(i64, i64)
declare i64 @freak_remove(i64)

define i64 @freak_llvm_fs_read(i64 %arg_path_p) {
entry:
    %path_p = alloca i64
    store i64 %arg_path_p, i64* %path_p
    %t0 = load i64, i64* %path_p
    %t1 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.0, i64 0, i64 0
    %t2 = ptrtoint i8* %t1 to i64
    %t3 = call i64 @freak_fopen(i64 %t0, i64 %t2)
    %f_v4 = alloca i64
    store i64 %t3, i64* %f_v4
    %t5 = load i64, i64* %f_v4
    %t7 = icmp eq i64 %t5, 0
    %t6 = zext i1 %t7 to i64
    %t11 = icmp ne i64 %t6, 0
    br i1 %t11, label %if.then.8, label %if.end.10
if.then.8:
    %t12 = getelementptr inbounds [24 x i8], [24 x i8]* @.str.1, i64 0, i64 0
    %t13 = ptrtoint i8* %t12 to i64
    call void @freak_llvm_say(i64 %t13)
    call void @freak_llvm_process_exit(i64 1)
    br label %if.end.10
if.end.10:
    %t14 = load i64, i64* %f_v4
    %t15 = call i64 @freak_fseek(i64 %t14, i64 0, i64 2)
    %t16 = load i64, i64* %f_v4
    %t17 = call i64 @freak_ftell(i64 %t16)
    %sz_v18 = alloca i64
    store i64 %t17, i64* %sz_v18
    %t19 = load i64, i64* %f_v4
    %t20 = call i64 @freak_fseek(i64 %t19, i64 0, i64 0)
    %t21 = load i64, i64* %sz_v18
    %t22 = add i64 %t21, 1
    %t23 = call i64 @freak_calloc(i64 %t22, i64 1)
    %buf_v24 = alloca i64
    store i64 %t23, i64* %buf_v24
    %t25 = load i64, i64* %buf_v24
    %t26 = load i64, i64* %sz_v18
    %t27 = load i64, i64* %f_v4
    %t28 = call i64 @freak_fread(i64 %t25, i64 1, i64 %t26, i64 %t27)
    %t29 = load i64, i64* %f_v4
    %t30 = call i64 @freak_fclose(i64 %t29)
    %t31 = load i64, i64* %buf_v24
    ret i64 %t31
    ret i64 0
}

define void @freak_llvm_fs_write(i64 %arg_path_p, i64 %arg_content_p) {
entry:
    %path_p = alloca i64
    store i64 %arg_path_p, i64* %path_p
    %content_p = alloca i64
    store i64 %arg_content_p, i64* %content_p
    %t32 = load i64, i64* %path_p
    %t33 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.2, i64 0, i64 0
    %t34 = ptrtoint i8* %t33 to i64
    %t35 = call i64 @freak_fopen(i64 %t32, i64 %t34)
    %f_v36 = alloca i64
    store i64 %t35, i64* %f_v36
    %t37 = load i64, i64* %f_v36
    %t39 = icmp eq i64 %t37, 0
    %t38 = zext i1 %t39 to i64
    %t43 = icmp ne i64 %t38, 0
    br i1 %t43, label %if.then.40, label %if.end.42
if.then.40:
    %t44 = getelementptr inbounds [25 x i8], [25 x i8]* @.str.3, i64 0, i64 0
    %t45 = ptrtoint i8* %t44 to i64
    call void @freak_llvm_say(i64 %t45)
    call void @freak_llvm_process_exit(i64 1)
    br label %if.end.42
if.end.42:
    %t46 = load i64, i64* %content_p
    %t47 = call i64 @freak_llvm_word_length(i64 %t46)
    %len_v48 = alloca i64
    store i64 %t47, i64* %len_v48
    %t49 = load i64, i64* %content_p
    %t50 = load i64, i64* %len_v48
    %t51 = load i64, i64* %f_v36
    %t52 = call i64 @freak_fwrite(i64 %t49, i64 1, i64 %t50, i64 %t51)
    %t53 = load i64, i64* %f_v36
    %t54 = call i64 @freak_fclose(i64 %t53)
    ret void
}

define void @freak_llvm_fs_append(i64 %arg_path_p, i64 %arg_content_p) {
entry:
    %path_p = alloca i64
    store i64 %arg_path_p, i64* %path_p
    %content_p = alloca i64
    store i64 %arg_content_p, i64* %content_p
    %t55 = load i64, i64* %path_p
    %t56 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.4, i64 0, i64 0
    %t57 = ptrtoint i8* %t56 to i64
    %t58 = call i64 @freak_fopen(i64 %t55, i64 %t57)
    %f_v59 = alloca i64
    store i64 %t58, i64* %f_v59
    %t60 = load i64, i64* %f_v59
    %t62 = icmp eq i64 %t60, 0
    %t61 = zext i1 %t62 to i64
    %t66 = icmp ne i64 %t61, 0
    br i1 %t66, label %if.then.63, label %if.end.65
if.then.63:
    %t67 = getelementptr inbounds [26 x i8], [26 x i8]* @.str.5, i64 0, i64 0
    %t68 = ptrtoint i8* %t67 to i64
    call void @freak_llvm_say(i64 %t68)
    call void @freak_llvm_process_exit(i64 1)
    br label %if.end.65
if.end.65:
    %t69 = load i64, i64* %content_p
    %t70 = call i64 @freak_llvm_word_length(i64 %t69)
    %len_v71 = alloca i64
    store i64 %t70, i64* %len_v71
    %t72 = load i64, i64* %content_p
    %t73 = load i64, i64* %len_v71
    %t74 = load i64, i64* %f_v59
    %t75 = call i64 @freak_fwrite(i64 %t72, i64 1, i64 %t73, i64 %t74)
    %t76 = load i64, i64* %f_v59
    %t77 = call i64 @freak_fclose(i64 %t76)
    ret void
}

define i64 @freak_llvm_fs_exists(i64 %arg_path_p) {
entry:
    %path_p = alloca i64
    store i64 %arg_path_p, i64* %path_p
    %t78 = load i64, i64* %path_p
    %t79 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.6, i64 0, i64 0
    %t80 = ptrtoint i8* %t79 to i64
    %t81 = call i64 @freak_fopen(i64 %t78, i64 %t80)
    %f_v82 = alloca i64
    store i64 %t81, i64* %f_v82
    %t83 = load i64, i64* %f_v82
    %t85 = icmp eq i64 %t83, 0
    %t84 = zext i1 %t85 to i64
    %t89 = icmp ne i64 %t84, 0
    br i1 %t89, label %if.then.86, label %if.end.88
if.then.86:
    ret i64 0
    br label %if.end.88
if.end.88:
    %t90 = load i64, i64* %f_v82
    %t91 = call i64 @freak_fclose(i64 %t90)
    ret i64 1
    ret i64 0
}

define void @freak_llvm_fs_delete(i64 %arg_path_p) {
entry:
    %path_p = alloca i64
    store i64 %arg_path_p, i64* %path_p
    %t92 = load i64, i64* %path_p
    %t93 = call i64 @freak_remove(i64 %t92)
    ret void
}

define i64 @freak_std_abs(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t94 = load i64, i64* %x
    %t96 = icmp slt i64 %t94, 0
    %t95 = zext i1 %t96 to i64
    %t100 = icmp ne i64 %t95, 0
    br i1 %t100, label %if.then.97, label %if.end.99
if.then.97:
    %t101 = load i64, i64* %x
    %t102 = sub i64 0, %t101
    ret i64 %t102
    br label %if.end.99
if.end.99:
    %t103 = load i64, i64* %x
    ret i64 %t103
    ret i64 0
}

define i64 @freak_std_clamp(i64 %arg_x, i64 %arg_lo, i64 %arg_hi) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %lo = alloca i64
    store i64 %arg_lo, i64* %lo
    %hi = alloca i64
    store i64 %arg_hi, i64* %hi
    %t104 = load i64, i64* %x
    %t105 = load i64, i64* %lo
    %t107 = icmp slt i64 %t104, %t105
    %t106 = zext i1 %t107 to i64
    %t111 = icmp ne i64 %t106, 0
    br i1 %t111, label %if.then.108, label %if.end.110
if.then.108:
    %t112 = load i64, i64* %lo
    ret i64 %t112
    br label %if.end.110
if.end.110:
    %t113 = load i64, i64* %x
    %t114 = load i64, i64* %hi
    %t116 = icmp sgt i64 %t113, %t114
    %t115 = zext i1 %t116 to i64
    %t120 = icmp ne i64 %t115, 0
    br i1 %t120, label %if.then.117, label %if.end.119
if.then.117:
    %t121 = load i64, i64* %hi
    ret i64 %t121
    br label %if.end.119
if.end.119:
    %t122 = load i64, i64* %x
    ret i64 %t122
    ret i64 0
}

define i64 @freak_std_pow(i64 %arg_base, i64 %arg_exp) {
entry:
    %base = alloca i64
    store i64 %arg_base, i64* %base
    %exp = alloca i64
    store i64 %arg_exp, i64* %exp
    %t123 = load i64, i64* %exp
    %t125 = icmp slt i64 %t123, 0
    %t124 = zext i1 %t125 to i64
    %t129 = icmp ne i64 %t124, 0
    br i1 %t129, label %if.then.126, label %if.end.128
if.then.126:
    ret i64 0
    br label %if.end.128
if.end.128:
    %res_v130 = alloca i64
    store i64 1, i64* %res_v130
    %t131 = load i64, i64* %base
    store i64 %t131, i64* @g_b
    %t132 = load i64, i64* %exp
    %e_v133 = alloca i64
    store i64 %t132, i64* %e_v133
    br label %loop.cond.134
loop.cond.134:
    %t137 = load i64, i64* %e_v133
    %t139 = icmp sle i64 %t137, 0
    %t138 = zext i1 %t139 to i64
    %t140 = icmp eq i64 %t138, 0
    br i1 %t140, label %loop.body.135, label %loop.end.136
loop.body.135:
    %t141 = load i64, i64* %e_v133
    %t142 = sdiv i64 %t141, 2
    %half_v143 = alloca i64
    store i64 %t142, i64* %half_v143
    %t144 = load i64, i64* %half_v143
    %t145 = mul i64 %t144, 2
    %even_part_v146 = alloca i64
    store i64 %t145, i64* %even_part_v146
    %t147 = load i64, i64* %e_v133
    %t148 = load i64, i64* %even_part_v146
    %t149 = sub i64 %t147, %t148
    %odd_v150 = alloca i64
    store i64 %t149, i64* %odd_v150
    %t151 = load i64, i64* %odd_v150
    %t153 = icmp eq i64 %t151, 1
    %t152 = zext i1 %t153 to i64
    %t157 = icmp ne i64 %t152, 0
    br i1 %t157, label %if.then.154, label %if.end.156
if.then.154:
    %t158 = load i64, i64* %res_v130
    %t159 = load i64, i64* @g_b
    %t160 = mul i64 %t158, %t159
    store i64 %t160, i64* %res_v130
    br label %if.end.156
if.end.156:
    %t161 = load i64, i64* @g_b
    %t162 = load i64, i64* @g_b
    %t163 = mul i64 %t161, %t162
    store i64 %t163, i64* @g_b
    %t164 = load i64, i64* %e_v133
    %t165 = sdiv i64 %t164, 2
    store i64 %t165, i64* %e_v133
    br label %loop.cond.134
loop.end.136:
    %t166 = load i64, i64* %res_v130
    ret i64 %t166
    ret i64 0
}

define i64 @freak_std_max(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t167 = load i64, i64* @g_a
    %t168 = load i64, i64* @g_b
    %t170 = icmp sgt i64 %t167, %t168
    %t169 = zext i1 %t170 to i64
    %t174 = icmp ne i64 %t169, 0
    br i1 %t174, label %if.then.171, label %if.end.173
if.then.171:
    %t175 = load i64, i64* @g_a
    ret i64 %t175
    br label %if.end.173
if.end.173:
    %t176 = load i64, i64* @g_b
    ret i64 %t176
    ret i64 0
}

define i64 @freak_std_min(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t177 = load i64, i64* @g_a
    %t178 = load i64, i64* @g_b
    %t180 = icmp slt i64 %t177, %t178
    %t179 = zext i1 %t180 to i64
    %t184 = icmp ne i64 %t179, 0
    br i1 %t184, label %if.then.181, label %if.end.183
if.then.181:
    %t185 = load i64, i64* @g_a
    ret i64 %t185
    br label %if.end.183
if.end.183:
    %t186 = load i64, i64* @g_b
    ret i64 %t186
    ret i64 0
}

define i64 @freak_int_to_word(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t187 = load i64, i64* %n
    %t188 = call i64 @freak_llvm_word_from_int(i64 %t187)
    ret i64 %t188
    ret i64 0
}

define i64 @freak_std_sign(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t189 = load i64, i64* %x
    %t191 = icmp sgt i64 %t189, 0
    %t190 = zext i1 %t191 to i64
    %t195 = icmp ne i64 %t190, 0
    br i1 %t195, label %if.then.192, label %if.end.194
if.then.192:
    ret i64 1
    br label %if.end.194
if.end.194:
    %t196 = load i64, i64* %x
    %t198 = icmp slt i64 %t196, 0
    %t197 = zext i1 %t198 to i64
    %t202 = icmp ne i64 %t197, 0
    br i1 %t202, label %if.then.199, label %if.end.201
if.then.199:
    %t203 = sub i64 0, 1
    ret i64 %t203
    br label %if.end.201
if.end.201:
    ret i64 0
    ret i64 0
}

define i64 @freak_std_gcd(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t204 = load i64, i64* @g_a
    %t205 = call i64 @freak_std_abs(i64 %t204)
    %x_v206 = alloca i64
    store i64 %t205, i64* %x_v206
    %t207 = load i64, i64* @g_b
    %t208 = call i64 @freak_std_abs(i64 %t207)
    %y_v209 = alloca i64
    store i64 %t208, i64* %y_v209
    br label %loop.cond.210
loop.cond.210:
    %t213 = load i64, i64* %y_v209
    %t215 = icmp eq i64 %t213, 0
    %t214 = zext i1 %t215 to i64
    %t216 = icmp eq i64 %t214, 0
    br i1 %t216, label %loop.body.211, label %loop.end.212
loop.body.211:
    %t217 = load i64, i64* %y_v209
    %tmp_v218 = alloca i64
    store i64 %t217, i64* %tmp_v218
    %t219 = load i64, i64* %x_v206
    %t220 = load i64, i64* %x_v206
    %t221 = load i64, i64* %y_v209
    %t222 = sdiv i64 %t220, %t221
    %t223 = load i64, i64* %y_v209
    %t224 = mul i64 %t222, %t223
    %t225 = sub i64 %t219, %t224
    %rem_v226 = alloca i64
    store i64 %t225, i64* %rem_v226
    %t227 = load i64, i64* %tmp_v218
    store i64 %t227, i64* %x_v206
    %t228 = load i64, i64* %rem_v226
    store i64 %t228, i64* %y_v209
    br label %loop.cond.210
loop.end.212:
    %t229 = load i64, i64* %x_v206
    ret i64 %t229
    ret i64 0
}

define i64 @freak_std_lcm(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t230 = load i64, i64* @g_a
    %t232 = icmp eq i64 %t230, 0
    %t231 = zext i1 %t232 to i64
    %t233 = load i64, i64* @g_b
    %t235 = icmp eq i64 %t233, 0
    %t234 = zext i1 %t235 to i64
    %t237 = icmp ne i64 %t231, 0
    %t238 = icmp ne i64 %t234, 0
    %t239 = or i1 %t237, %t238
    %t236 = zext i1 %t239 to i64
    %t243 = icmp ne i64 %t236, 0
    br i1 %t243, label %if.then.240, label %if.end.242
if.then.240:
    ret i64 0
    br label %if.end.242
if.end.242:
    %t244 = load i64, i64* @g_a
    %t245 = load i64, i64* @g_b
    %t246 = call i64 @freak_std_gcd(i64 %t244, i64 %t245)
    %g_v247 = alloca i64
    store i64 %t246, i64* %g_v247
    %t248 = load i64, i64* @g_a
    %t249 = call i64 @freak_std_abs(i64 %t248)
    %aa_v250 = alloca i64
    store i64 %t249, i64* %aa_v250
    %t251 = load i64, i64* @g_b
    %t252 = call i64 @freak_std_abs(i64 %t251)
    %bb_v253 = alloca i64
    store i64 %t252, i64* %bb_v253
    %t254 = load i64, i64* %aa_v250
    %t255 = load i64, i64* %g_v247
    %t256 = sdiv i64 %t254, %t255
    %t257 = load i64, i64* %bb_v253
    %t258 = mul i64 %t256, %t257
    ret i64 %t258
    ret i64 0
}

define i64 @freak_std_factorial(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t259 = load i64, i64* %n
    %t261 = icmp sle i64 %t259, 1
    %t260 = zext i1 %t261 to i64
    %t265 = icmp ne i64 %t260, 0
    br i1 %t265, label %if.then.262, label %if.end.264
if.then.262:
    ret i64 1
    br label %if.end.264
if.end.264:
    %f_v266 = alloca i64
    store i64 1, i64* %f_v266
    %i_v267 = alloca i64
    store i64 2, i64* %i_v267
    br label %loop.cond.268
loop.cond.268:
    %t271 = load i64, i64* %i_v267
    %t272 = load i64, i64* %n
    %t274 = icmp sgt i64 %t271, %t272
    %t273 = zext i1 %t274 to i64
    %t275 = icmp eq i64 %t273, 0
    br i1 %t275, label %loop.body.269, label %loop.end.270
loop.body.269:
    %t276 = load i64, i64* %f_v266
    %t277 = load i64, i64* %i_v267
    %t278 = mul i64 %t276, %t277
    store i64 %t278, i64* %f_v266
    %t279 = load i64, i64* %i_v267
    %t280 = add i64 %t279, 1
    store i64 %t280, i64* %i_v267
    br label %loop.cond.268
loop.end.270:
    %t281 = load i64, i64* %f_v266
    ret i64 %t281
    ret i64 0
}

define i64 @freak_std_fibonacci(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t282 = load i64, i64* %n
    %t284 = icmp sle i64 %t282, 0
    %t283 = zext i1 %t284 to i64
    %t288 = icmp ne i64 %t283, 0
    br i1 %t288, label %if.then.285, label %if.end.287
if.then.285:
    ret i64 0
    br label %if.end.287
if.end.287:
    %t289 = load i64, i64* %n
    %t291 = icmp eq i64 %t289, 1
    %t290 = zext i1 %t291 to i64
    %t295 = icmp ne i64 %t290, 0
    br i1 %t295, label %if.then.292, label %if.end.294
if.then.292:
    ret i64 1
    br label %if.end.294
if.end.294:
    store i64 0, i64* @g_a
    store i64 1, i64* @g_b
    %i_v296 = alloca i64
    store i64 2, i64* %i_v296
    br label %loop.cond.297
loop.cond.297:
    %t300 = load i64, i64* %i_v296
    %t301 = load i64, i64* %n
    %t303 = icmp sgt i64 %t300, %t301
    %t302 = zext i1 %t303 to i64
    %t304 = icmp eq i64 %t302, 0
    br i1 %t304, label %loop.body.298, label %loop.end.299
loop.body.298:
    %t305 = load i64, i64* @g_a
    %t306 = load i64, i64* @g_b
    %t307 = add i64 %t305, %t306
    %tmp_v308 = alloca i64
    store i64 %t307, i64* %tmp_v308
    %t309 = load i64, i64* @g_b
    store i64 %t309, i64* @g_a
    %t310 = load i64, i64* %tmp_v308
    store i64 %t310, i64* @g_b
    %t311 = load i64, i64* %i_v296
    %t312 = add i64 %t311, 1
    store i64 %t312, i64* %i_v296
    br label %loop.cond.297
loop.end.299:
    %t313 = load i64, i64* @g_b
    ret i64 %t313
    ret i64 0
}

define i64 @freak_std_is_even(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t314 = load i64, i64* %x
    %t315 = sdiv i64 %t314, 2
    %half_v316 = alloca i64
    store i64 %t315, i64* %half_v316
    %t317 = load i64, i64* %half_v316
    %t318 = mul i64 %t317, 2
    %t319 = load i64, i64* %x
    %t321 = icmp eq i64 %t318, %t319
    %t320 = zext i1 %t321 to i64
    ret i64 %t320
    ret i64 0
}

define i64 @freak_std_is_odd(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t322 = load i64, i64* %x
    %t323 = call i64 @freak_std_is_even(i64 %t322)
    %t325 = icmp eq i64 %t323, 0
    %t324 = zext i1 %t325 to i64
    ret i64 %t324
    ret i64 0
}

define i64 @freak_string_repeat(i64 %arg_s, i64 %arg_count) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %count = alloca i64
    store i64 %arg_count, i64* %count
    %t326 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.7, i64 0, i64 0
    %t327 = ptrtoint i8* %t326 to i64
    %out_v328 = alloca i64
    store i64 %t327, i64* %out_v328
    %i_v329 = alloca i64
    store i64 0, i64* %i_v329
    %t335 = load i64, i64* %count
    %rep.334 = alloca i64
    store i64 0, i64* %rep.334
    br label %loop.cond.330
loop.cond.330:
    %t336 = load i64, i64* %rep.334
    %t337 = icmp slt i64 %t336, %t335
    br i1 %t337, label %loop.body.331, label %loop.end.332
loop.body.331:
    %t338 = load i64, i64* %out_v328
    %t339 = load i64, i64* %s
    %t340 = call i64 @freak_llvm_word_concat(i64 %t338, i64 %t339)
    store i64 %t340, i64* %out_v328
    %t341 = load i64, i64* %i_v329
    %t342 = add i64 %t341, 1
    store i64 %t342, i64* %i_v329
    br label %loop.inc.333
loop.inc.333:
    %t343 = load i64, i64* %rep.334
    %t344 = add i64 %t343, 1
    store i64 %t344, i64* %rep.334
    br label %loop.cond.330
loop.end.332:
    %t345 = load i64, i64* %out_v328
    ret i64 %t345
    ret i64 0
}

define i64 @freak_string_pad_left(i64 %arg_s, i64 %arg_width, i64 %arg_pad_char) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %width = alloca i64
    store i64 %arg_width, i64* %width
    %pad_char = alloca i64
    store i64 %arg_pad_char, i64* %pad_char
    %t346 = load i64, i64* %s
    %t347 = call i64 @freak_llvm_word_length(i64 %t346)
    %slen_v348 = alloca i64
    store i64 %t347, i64* %slen_v348
    %t349 = load i64, i64* %slen_v348
    %t350 = load i64, i64* %width
    %t352 = icmp sge i64 %t349, %t350
    %t351 = zext i1 %t352 to i64
    %t356 = icmp ne i64 %t351, 0
    br i1 %t356, label %if.then.353, label %if.end.355
if.then.353:
    %t357 = load i64, i64* %s
    ret i64 %t357
    br label %if.end.355
if.end.355:
    %t358 = load i64, i64* %width
    %t359 = load i64, i64* %slen_v348
    %t360 = sub i64 %t358, %t359
    %needed_v361 = alloca i64
    store i64 %t360, i64* %needed_v361
    %t362 = load i64, i64* %pad_char
    %t363 = load i64, i64* %needed_v361
    %t364 = call i64 @freak_string_repeat(i64 %t362, i64 %t363)
    %padding_v365 = alloca i64
    store i64 %t364, i64* %padding_v365
    %t366 = load i64, i64* %padding_v365
    %t367 = load i64, i64* %s
    %t368 = call i64 @freak_llvm_word_concat(i64 %t366, i64 %t367)
    ret i64 %t368
    ret i64 0
}

define i64 @freak_string_pad_right(i64 %arg_s, i64 %arg_width, i64 %arg_pad_char) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %width = alloca i64
    store i64 %arg_width, i64* %width
    %pad_char = alloca i64
    store i64 %arg_pad_char, i64* %pad_char
    %t369 = load i64, i64* %s
    %t370 = call i64 @freak_llvm_word_length(i64 %t369)
    %slen_v371 = alloca i64
    store i64 %t370, i64* %slen_v371
    %t372 = load i64, i64* %slen_v371
    %t373 = load i64, i64* %width
    %t375 = icmp sge i64 %t372, %t373
    %t374 = zext i1 %t375 to i64
    %t379 = icmp ne i64 %t374, 0
    br i1 %t379, label %if.then.376, label %if.end.378
if.then.376:
    %t380 = load i64, i64* %s
    ret i64 %t380
    br label %if.end.378
if.end.378:
    %t381 = load i64, i64* %width
    %t382 = load i64, i64* %slen_v371
    %t383 = sub i64 %t381, %t382
    %needed_v384 = alloca i64
    store i64 %t383, i64* %needed_v384
    %t385 = load i64, i64* %pad_char
    %t386 = load i64, i64* %needed_v384
    %t387 = call i64 @freak_string_repeat(i64 %t385, i64 %t386)
    %padding_v388 = alloca i64
    store i64 %t387, i64* %padding_v388
    %t389 = load i64, i64* %s
    %t390 = load i64, i64* %padding_v388
    %t391 = call i64 @freak_llvm_word_concat(i64 %t389, i64 %t390)
    ret i64 %t391
    ret i64 0
}

define i64 @freak_string_reverse(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t392 = load i64, i64* %s
    %t393 = call i64 @freak_llvm_word_length(i64 %t392)
    %slen_v394 = alloca i64
    store i64 %t393, i64* %slen_v394
    %t395 = load i64, i64* %slen_v394
    %t397 = icmp sle i64 %t395, 1
    %t396 = zext i1 %t397 to i64
    %t401 = icmp ne i64 %t396, 0
    br i1 %t401, label %if.then.398, label %if.end.400
if.then.398:
    %t402 = load i64, i64* %s
    ret i64 %t402
    br label %if.end.400
if.end.400:
    %t403 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.8, i64 0, i64 0
    %t404 = ptrtoint i8* %t403 to i64
    %out_v405 = alloca i64
    store i64 %t404, i64* %out_v405
    %t406 = load i64, i64* %slen_v394
    %t407 = sub i64 %t406, 1
    %i_v408 = alloca i64
    store i64 %t407, i64* %i_v408
    %t414 = load i64, i64* %slen_v394
    %rep.413 = alloca i64
    store i64 0, i64* %rep.413
    br label %loop.cond.409
loop.cond.409:
    %t415 = load i64, i64* %rep.413
    %t416 = icmp slt i64 %t415, %t414
    br i1 %t416, label %loop.body.410, label %loop.end.411
loop.body.410:
    %t417 = load i64, i64* %out_v405
    %t418 = load i64, i64* %s
    %t420 = load i64, i64* %i_v408
    %t419 = call i64 @freak_llvm_word_char_at(i64 %t418, i64 %t420)
    %t421 = call i64 @freak_llvm_word_concat(i64 %t417, i64 %t419)
    store i64 %t421, i64* %out_v405
    %t422 = load i64, i64* %i_v408
    %t423 = sub i64 %t422, 1
    store i64 %t423, i64* %i_v408
    br label %loop.inc.412
loop.inc.412:
    %t424 = load i64, i64* %rep.413
    %t425 = add i64 %t424, 1
    store i64 %t425, i64* %rep.413
    br label %loop.cond.409
loop.end.411:
    %t426 = load i64, i64* %out_v405
    ret i64 %t426
    ret i64 0
}

define i64 @freak_string_count(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t427 = load i64, i64* %haystack
    %t428 = call i64 @freak_llvm_word_length(i64 %t427)
    %hlen_v429 = alloca i64
    store i64 %t428, i64* %hlen_v429
    %t430 = load i64, i64* %needle
    %t431 = call i64 @freak_llvm_word_length(i64 %t430)
    %nlen_v432 = alloca i64
    store i64 %t431, i64* %nlen_v432
    %t433 = load i64, i64* %nlen_v432
    %t435 = icmp eq i64 %t433, 0
    %t434 = zext i1 %t435 to i64
    %t439 = icmp ne i64 %t434, 0
    br i1 %t439, label %if.then.436, label %if.end.438
if.then.436:
    ret i64 0
    br label %if.end.438
if.end.438:
    %t440 = load i64, i64* %nlen_v432
    %t441 = load i64, i64* %hlen_v429
    %t443 = icmp sgt i64 %t440, %t441
    %t442 = zext i1 %t443 to i64
    %t447 = icmp ne i64 %t442, 0
    br i1 %t447, label %if.then.444, label %if.end.446
if.then.444:
    ret i64 0
    br label %if.end.446
if.end.446:
    %count_v448 = alloca i64
    store i64 0, i64* %count_v448
    %i_v449 = alloca i64
    store i64 0, i64* %i_v449
    %t450 = load i64, i64* %hlen_v429
    %t451 = load i64, i64* %nlen_v432
    %t452 = sub i64 %t450, %t451
    %t453 = add i64 %t452, 1
    %limit_v454 = alloca i64
    store i64 %t453, i64* %limit_v454
    %t460 = load i64, i64* %limit_v454
    %rep.459 = alloca i64
    store i64 0, i64* %rep.459
    br label %loop.cond.455
loop.cond.455:
    %t461 = load i64, i64* %rep.459
    %t462 = icmp slt i64 %t461, %t460
    br i1 %t462, label %loop.body.456, label %loop.end.457
loop.body.456:
    %match_v463 = alloca i64
    store i64 1, i64* %match_v463
    %j_v464 = alloca i64
    store i64 0, i64* %j_v464
    %t470 = load i64, i64* %nlen_v432
    %rep.469 = alloca i64
    store i64 0, i64* %rep.469
    br label %loop.cond.465
loop.cond.465:
    %t471 = load i64, i64* %rep.469
    %t472 = icmp slt i64 %t471, %t470
    br i1 %t472, label %loop.body.466, label %loop.end.467
loop.body.466:
    %t473 = load i64, i64* %match_v463
    %t477 = icmp ne i64 %t473, 0
    br i1 %t477, label %if.then.474, label %if.end.476
if.then.474:
    %t478 = load i64, i64* %haystack
    %t480 = load i64, i64* %i_v449
    %t481 = load i64, i64* %j_v464
    %t482 = add i64 %t480, %t481
    %t479 = call i64 @freak_llvm_word_char_at(i64 %t478, i64 %t482)
    %t483 = load i64, i64* %needle
    %t485 = load i64, i64* %j_v464
    %t484 = call i64 @freak_llvm_word_char_at(i64 %t483, i64 %t485)
    %t486 = call i64 @freak_llvm_word_neq(i64 %t479, i64 %t484)
    %t490 = icmp ne i64 %t486, 0
    br i1 %t490, label %if.then.487, label %if.end.489
if.then.487:
    store i64 0, i64* %match_v463
    br label %if.end.489
if.end.489:
    br label %if.end.476
if.end.476:
    %t491 = load i64, i64* %j_v464
    %t492 = add i64 %t491, 1
    store i64 %t492, i64* %j_v464
    br label %loop.inc.468
loop.inc.468:
    %t493 = load i64, i64* %rep.469
    %t494 = add i64 %t493, 1
    store i64 %t494, i64* %rep.469
    br label %loop.cond.465
loop.end.467:
    %t495 = load i64, i64* %match_v463
    %t499 = icmp ne i64 %t495, 0
    br i1 %t499, label %if.then.496, label %if.end.498
if.then.496:
    %t500 = load i64, i64* %count_v448
    %t501 = add i64 %t500, 1
    store i64 %t501, i64* %count_v448
    br label %if.end.498
if.end.498:
    %t502 = load i64, i64* %i_v449
    %t503 = add i64 %t502, 1
    store i64 %t503, i64* %i_v449
    br label %loop.inc.458
loop.inc.458:
    %t504 = load i64, i64* %rep.459
    %t505 = add i64 %t504, 1
    store i64 %t505, i64* %rep.459
    br label %loop.cond.455
loop.end.457:
    %t506 = load i64, i64* %count_v448
    ret i64 %t506
    ret i64 0
}

define i64 @freak_string_split(i64 %arg_s, i64 %arg_delim) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %delim = alloca i64
    store i64 %arg_delim, i64* %delim
    %t507 = load i64, i64* %s
    %t508 = call i64 @freak_llvm_word_length(i64 %t507)
    %slen_v509 = alloca i64
    store i64 %t508, i64* %slen_v509
    %t510 = load i64, i64* %delim
    %t511 = call i64 @freak_llvm_word_length(i64 %t510)
    %dlen_v512 = alloca i64
    store i64 %t511, i64* %dlen_v512
    %t513 = load i64, i64* %dlen_v512
    %t515 = icmp eq i64 %t513, 0
    %t514 = zext i1 %t515 to i64
    %t519 = icmp ne i64 %t514, 0
    br i1 %t519, label %if.then.516, label %if.end.518
if.then.516:
    %t520 = load i64, i64* %s
    ret i64 %t520
    br label %if.end.518
if.end.518:
    %t521 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.9, i64 0, i64 0
    %t522 = ptrtoint i8* %t521 to i64
    %sp_out_v523 = alloca i64
    store i64 %t522, i64* %sp_out_v523
    %t524 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.10, i64 0, i64 0
    %t525 = ptrtoint i8* %t524 to i64
    %sp_cur_v526 = alloca i64
    store i64 %t525, i64* %sp_cur_v526
    %sp_i_v527 = alloca i64
    store i64 0, i64* %sp_i_v527
    %t533 = load i64, i64* %slen_v509
    %rep.532 = alloca i64
    store i64 0, i64* %rep.532
    br label %loop.cond.528
loop.cond.528:
    %t534 = load i64, i64* %rep.532
    %t535 = icmp slt i64 %t534, %t533
    br i1 %t535, label %loop.body.529, label %loop.end.530
loop.body.529:
    %sp_match_v536 = alloca i64
    store i64 1, i64* %sp_match_v536
    %t537 = load i64, i64* %sp_i_v527
    %t538 = load i64, i64* %dlen_v512
    %t539 = add i64 %t537, %t538
    %t540 = load i64, i64* %slen_v509
    %t542 = icmp sle i64 %t539, %t540
    %t541 = zext i1 %t542 to i64
    %t546 = icmp ne i64 %t541, 0
    br i1 %t546, label %if.then.543, label %if.else.544
if.then.543:
    %sp_j_v547 = alloca i64
    store i64 0, i64* %sp_j_v547
    %t553 = load i64, i64* %dlen_v512
    %rep.552 = alloca i64
    store i64 0, i64* %rep.552
    br label %loop.cond.548
loop.cond.548:
    %t554 = load i64, i64* %rep.552
    %t555 = icmp slt i64 %t554, %t553
    br i1 %t555, label %loop.body.549, label %loop.end.550
loop.body.549:
    %t556 = load i64, i64* %sp_match_v536
    %t560 = icmp ne i64 %t556, 0
    br i1 %t560, label %if.then.557, label %if.end.559
if.then.557:
    %t561 = load i64, i64* %s
    %t563 = load i64, i64* %sp_i_v527
    %t564 = load i64, i64* %sp_j_v547
    %t565 = add i64 %t563, %t564
    %t562 = call i64 @freak_llvm_word_char_at(i64 %t561, i64 %t565)
    %t566 = load i64, i64* %delim
    %t568 = load i64, i64* %sp_j_v547
    %t567 = call i64 @freak_llvm_word_char_at(i64 %t566, i64 %t568)
    %t569 = call i64 @freak_llvm_word_neq(i64 %t562, i64 %t567)
    %t573 = icmp ne i64 %t569, 0
    br i1 %t573, label %if.then.570, label %if.end.572
if.then.570:
    store i64 0, i64* %sp_match_v536
    br label %if.end.572
if.end.572:
    br label %if.end.559
if.end.559:
    %t574 = load i64, i64* %sp_j_v547
    %t575 = add i64 %t574, 1
    store i64 %t575, i64* %sp_j_v547
    br label %loop.inc.551
loop.inc.551:
    %t576 = load i64, i64* %rep.552
    %t577 = add i64 %t576, 1
    store i64 %t577, i64* %rep.552
    br label %loop.cond.548
loop.end.550:
    br label %if.end.545
if.else.544:
    store i64 0, i64* %sp_match_v536
    br label %if.end.545
if.end.545:
    %t578 = load i64, i64* %sp_match_v536
    %t582 = icmp ne i64 %t578, 0
    br i1 %t582, label %if.then.579, label %if.else.580
if.then.579:
    %t583 = load i64, i64* %sp_out_v523
    %t584 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.11, i64 0, i64 0
    %t585 = ptrtoint i8* %t584 to i64
    %t586 = call i64 @freak_llvm_word_eq(i64 %t583, i64 %t585)
    %t590 = icmp ne i64 %t586, 0
    br i1 %t590, label %if.then.587, label %if.else.588
if.then.587:
    %t591 = load i64, i64* %sp_cur_v526
    store i64 %t591, i64* %sp_out_v523
    br label %if.end.589
if.else.588:
    %t592 = load i64, i64* %sp_out_v523
    %t593 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.12, i64 0, i64 0
    %t594 = ptrtoint i8* %t593 to i64
    %t595 = call i64 @freak_llvm_word_concat(i64 %t592, i64 %t594)
    %t596 = load i64, i64* %sp_cur_v526
    %t597 = call i64 @freak_llvm_word_concat(i64 %t595, i64 %t596)
    store i64 %t597, i64* %sp_out_v523
    br label %if.end.589
if.end.589:
    %t598 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.13, i64 0, i64 0
    %t599 = ptrtoint i8* %t598 to i64
    store i64 %t599, i64* %sp_cur_v526
    %t600 = load i64, i64* %dlen_v512
    %t601 = load i64, i64* %sp_i_v527
    %t602 = add i64 %t601, %t600
    store i64 %t602, i64* %sp_i_v527
    br label %if.end.581
if.else.580:
    %t603 = load i64, i64* %sp_cur_v526
    %t604 = load i64, i64* %s
    %t606 = load i64, i64* %sp_i_v527
    %t605 = call i64 @freak_llvm_word_char_at(i64 %t604, i64 %t606)
    %t607 = call i64 @freak_llvm_word_concat(i64 %t603, i64 %t605)
    store i64 %t607, i64* %sp_cur_v526
    %t608 = load i64, i64* %sp_i_v527
    %t609 = add i64 %t608, 1
    store i64 %t609, i64* %sp_i_v527
    br label %if.end.581
if.end.581:
    br label %loop.inc.531
loop.inc.531:
    %t610 = load i64, i64* %rep.532
    %t611 = add i64 %t610, 1
    store i64 %t611, i64* %rep.532
    br label %loop.cond.528
loop.end.530:
    %t612 = load i64, i64* %sp_out_v523
    %t613 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.14, i64 0, i64 0
    %t614 = ptrtoint i8* %t613 to i64
    %t615 = call i64 @freak_llvm_word_eq(i64 %t612, i64 %t614)
    %t619 = icmp ne i64 %t615, 0
    br i1 %t619, label %if.then.616, label %if.else.617
if.then.616:
    %t620 = load i64, i64* %sp_cur_v526
    store i64 %t620, i64* %sp_out_v523
    br label %if.end.618
if.else.617:
    %t621 = load i64, i64* %sp_out_v523
    %t622 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.15, i64 0, i64 0
    %t623 = ptrtoint i8* %t622 to i64
    %t624 = call i64 @freak_llvm_word_concat(i64 %t621, i64 %t623)
    %t625 = load i64, i64* %sp_cur_v526
    %t626 = call i64 @freak_llvm_word_concat(i64 %t624, i64 %t625)
    store i64 %t626, i64* %sp_out_v523
    br label %if.end.618
if.end.618:
    %t627 = load i64, i64* %sp_out_v523
    ret i64 %t627
    ret i64 0
}

define i64 @freak_string_join(i64 %arg_parts, i64 %arg_separator) {
entry:
    %parts = alloca i64
    store i64 %arg_parts, i64* %parts
    %separator = alloca i64
    store i64 %arg_separator, i64* %separator
    %t628 = load i64, i64* %parts
    %t629 = call i64 @freak_llvm_word_length(i64 %t628)
    %plen_v630 = alloca i64
    store i64 %t629, i64* %plen_v630
    %t631 = load i64, i64* %plen_v630
    %t633 = icmp eq i64 %t631, 0
    %t632 = zext i1 %t633 to i64
    %t637 = icmp ne i64 %t632, 0
    br i1 %t637, label %if.then.634, label %if.end.636
if.then.634:
    %t638 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.16, i64 0, i64 0
    %t639 = ptrtoint i8* %t638 to i64
    ret i64 %t639
    br label %if.end.636
if.end.636:
    %t640 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.17, i64 0, i64 0
    %t641 = ptrtoint i8* %t640 to i64
    %jn_out_v642 = alloca i64
    store i64 %t641, i64* %jn_out_v642
    %t643 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.18, i64 0, i64 0
    %t644 = ptrtoint i8* %t643 to i64
    %jn_cur_v645 = alloca i64
    store i64 %t644, i64* %jn_cur_v645
    %jn_first_v646 = alloca i64
    store i64 1, i64* %jn_first_v646
    %jn_i_v647 = alloca i64
    store i64 0, i64* %jn_i_v647
    %t653 = load i64, i64* %plen_v630
    %rep.652 = alloca i64
    store i64 0, i64* %rep.652
    br label %loop.cond.648
loop.cond.648:
    %t654 = load i64, i64* %rep.652
    %t655 = icmp slt i64 %t654, %t653
    br i1 %t655, label %loop.body.649, label %loop.end.650
loop.body.649:
    %t656 = load i64, i64* %parts
    %t658 = load i64, i64* %jn_i_v647
    %t657 = call i64 @freak_llvm_word_char_at(i64 %t656, i64 %t658)
    %jn_c_v659 = alloca i64
    store i64 %t657, i64* %jn_c_v659
    %t660 = load i64, i64* %jn_c_v659
    %t661 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.19, i64 0, i64 0
    %t662 = ptrtoint i8* %t661 to i64
    %t663 = call i64 @freak_llvm_word_eq(i64 %t660, i64 %t662)
    %t667 = icmp ne i64 %t663, 0
    br i1 %t667, label %if.then.664, label %if.else.665
if.then.664:
    %t668 = load i64, i64* %jn_first_v646
    %t672 = icmp ne i64 %t668, 0
    br i1 %t672, label %if.then.669, label %if.else.670
if.then.669:
    %t673 = load i64, i64* %jn_cur_v645
    store i64 %t673, i64* %jn_out_v642
    store i64 0, i64* %jn_first_v646
    br label %if.end.671
if.else.670:
    %t674 = load i64, i64* %jn_out_v642
    %t675 = load i64, i64* %separator
    %t676 = call i64 @freak_llvm_word_concat(i64 %t674, i64 %t675)
    %t677 = load i64, i64* %jn_cur_v645
    %t678 = call i64 @freak_llvm_word_concat(i64 %t676, i64 %t677)
    store i64 %t678, i64* %jn_out_v642
    br label %if.end.671
if.end.671:
    %t679 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.20, i64 0, i64 0
    %t680 = ptrtoint i8* %t679 to i64
    store i64 %t680, i64* %jn_cur_v645
    br label %if.end.666
if.else.665:
    %t681 = load i64, i64* %jn_cur_v645
    %t682 = load i64, i64* %jn_c_v659
    %t683 = call i64 @freak_llvm_word_concat(i64 %t681, i64 %t682)
    store i64 %t683, i64* %jn_cur_v645
    br label %if.end.666
if.end.666:
    %t684 = load i64, i64* %jn_i_v647
    %t685 = add i64 %t684, 1
    store i64 %t685, i64* %jn_i_v647
    br label %loop.inc.651
loop.inc.651:
    %t686 = load i64, i64* %rep.652
    %t687 = add i64 %t686, 1
    store i64 %t687, i64* %rep.652
    br label %loop.cond.648
loop.end.650:
    %t688 = load i64, i64* %jn_first_v646
    %t692 = icmp ne i64 %t688, 0
    br i1 %t692, label %if.then.689, label %if.else.690
if.then.689:
    %t693 = load i64, i64* %jn_cur_v645
    store i64 %t693, i64* %jn_out_v642
    br label %if.end.691
if.else.690:
    %t694 = load i64, i64* %jn_out_v642
    %t695 = load i64, i64* %separator
    %t696 = call i64 @freak_llvm_word_concat(i64 %t694, i64 %t695)
    %t697 = load i64, i64* %jn_cur_v645
    %t698 = call i64 @freak_llvm_word_concat(i64 %t696, i64 %t697)
    store i64 %t698, i64* %jn_out_v642
    br label %if.end.691
if.end.691:
    %t699 = load i64, i64* %jn_out_v642
    ret i64 %t699
    ret i64 0
}

define i64 @freak_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t700 = load i64, i64* %c
    %t701 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.21, i64 0, i64 0
    %t702 = ptrtoint i8* %t701 to i64
    %t703 = call i64 @freak_llvm_word_eq(i64 %t700, i64 %t702)
    %t707 = icmp ne i64 %t703, 0
    br i1 %t707, label %if.then.704, label %if.end.706
if.then.704:
    ret i64 1
    br label %if.end.706
if.end.706:
    %t708 = load i64, i64* %c
    %t709 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.22, i64 0, i64 0
    %t710 = ptrtoint i8* %t709 to i64
    %t711 = call i64 @freak_llvm_word_eq(i64 %t708, i64 %t710)
    %t715 = icmp ne i64 %t711, 0
    br i1 %t715, label %if.then.712, label %if.end.714
if.then.712:
    ret i64 1
    br label %if.end.714
if.end.714:
    %t716 = load i64, i64* %c
    %t717 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.23, i64 0, i64 0
    %t718 = ptrtoint i8* %t717 to i64
    %t719 = call i64 @freak_llvm_word_eq(i64 %t716, i64 %t718)
    %t723 = icmp ne i64 %t719, 0
    br i1 %t723, label %if.then.720, label %if.end.722
if.then.720:
    ret i64 1
    br label %if.end.722
if.end.722:
    %t724 = load i64, i64* %c
    %t725 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.24, i64 0, i64 0
    %t726 = ptrtoint i8* %t725 to i64
    %t727 = call i64 @freak_llvm_word_eq(i64 %t724, i64 %t726)
    %t731 = icmp ne i64 %t727, 0
    br i1 %t731, label %if.then.728, label %if.end.730
if.then.728:
    ret i64 1
    br label %if.end.730
if.end.730:
    %t732 = load i64, i64* %c
    %t733 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.25, i64 0, i64 0
    %t734 = ptrtoint i8* %t733 to i64
    %t735 = call i64 @freak_llvm_word_eq(i64 %t732, i64 %t734)
    %t739 = icmp ne i64 %t735, 0
    br i1 %t739, label %if.then.736, label %if.end.738
if.then.736:
    ret i64 1
    br label %if.end.738
if.end.738:
    %t740 = load i64, i64* %c
    %t741 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.26, i64 0, i64 0
    %t742 = ptrtoint i8* %t741 to i64
    %t743 = call i64 @freak_llvm_word_eq(i64 %t740, i64 %t742)
    %t747 = icmp ne i64 %t743, 0
    br i1 %t747, label %if.then.744, label %if.end.746
if.then.744:
    ret i64 1
    br label %if.end.746
if.end.746:
    %t748 = load i64, i64* %c
    %t749 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.27, i64 0, i64 0
    %t750 = ptrtoint i8* %t749 to i64
    %t751 = call i64 @freak_llvm_word_eq(i64 %t748, i64 %t750)
    %t755 = icmp ne i64 %t751, 0
    br i1 %t755, label %if.then.752, label %if.end.754
if.then.752:
    ret i64 1
    br label %if.end.754
if.end.754:
    %t756 = load i64, i64* %c
    %t757 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.28, i64 0, i64 0
    %t758 = ptrtoint i8* %t757 to i64
    %t759 = call i64 @freak_llvm_word_eq(i64 %t756, i64 %t758)
    %t763 = icmp ne i64 %t759, 0
    br i1 %t763, label %if.then.760, label %if.end.762
if.then.760:
    ret i64 1
    br label %if.end.762
if.end.762:
    %t764 = load i64, i64* %c
    %t765 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.29, i64 0, i64 0
    %t766 = ptrtoint i8* %t765 to i64
    %t767 = call i64 @freak_llvm_word_eq(i64 %t764, i64 %t766)
    %t771 = icmp ne i64 %t767, 0
    br i1 %t771, label %if.then.768, label %if.end.770
if.then.768:
    ret i64 1
    br label %if.end.770
if.end.770:
    %t772 = load i64, i64* %c
    %t773 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.30, i64 0, i64 0
    %t774 = ptrtoint i8* %t773 to i64
    %t775 = call i64 @freak_llvm_word_eq(i64 %t772, i64 %t774)
    %t779 = icmp ne i64 %t775, 0
    br i1 %t779, label %if.then.776, label %if.end.778
if.then.776:
    ret i64 1
    br label %if.end.778
if.end.778:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_alpha(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t780 = load i64, i64* %c
    %t781 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.31, i64 0, i64 0
    %t782 = ptrtoint i8* %t781 to i64
    %t783 = call i64 @freak_llvm_word_eq(i64 %t780, i64 %t782)
    %t784 = load i64, i64* %c
    %t785 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.32, i64 0, i64 0
    %t786 = ptrtoint i8* %t785 to i64
    %t787 = call i64 @freak_llvm_word_eq(i64 %t784, i64 %t786)
    %t789 = icmp ne i64 %t783, 0
    %t790 = icmp ne i64 %t787, 0
    %t791 = or i1 %t789, %t790
    %t788 = zext i1 %t791 to i64
    %t792 = load i64, i64* %c
    %t793 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.33, i64 0, i64 0
    %t794 = ptrtoint i8* %t793 to i64
    %t795 = call i64 @freak_llvm_word_eq(i64 %t792, i64 %t794)
    %t797 = icmp ne i64 %t788, 0
    %t798 = icmp ne i64 %t795, 0
    %t799 = or i1 %t797, %t798
    %t796 = zext i1 %t799 to i64
    %t800 = load i64, i64* %c
    %t801 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.34, i64 0, i64 0
    %t802 = ptrtoint i8* %t801 to i64
    %t803 = call i64 @freak_llvm_word_eq(i64 %t800, i64 %t802)
    %t805 = icmp ne i64 %t796, 0
    %t806 = icmp ne i64 %t803, 0
    %t807 = or i1 %t805, %t806
    %t804 = zext i1 %t807 to i64
    %t808 = load i64, i64* %c
    %t809 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.35, i64 0, i64 0
    %t810 = ptrtoint i8* %t809 to i64
    %t811 = call i64 @freak_llvm_word_eq(i64 %t808, i64 %t810)
    %t813 = icmp ne i64 %t804, 0
    %t814 = icmp ne i64 %t811, 0
    %t815 = or i1 %t813, %t814
    %t812 = zext i1 %t815 to i64
    %t819 = icmp ne i64 %t812, 0
    br i1 %t819, label %if.then.816, label %if.end.818
if.then.816:
    ret i64 1
    br label %if.end.818
if.end.818:
    %t820 = load i64, i64* %c
    %t821 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.36, i64 0, i64 0
    %t822 = ptrtoint i8* %t821 to i64
    %t823 = call i64 @freak_llvm_word_eq(i64 %t820, i64 %t822)
    %t824 = load i64, i64* %c
    %t825 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.37, i64 0, i64 0
    %t826 = ptrtoint i8* %t825 to i64
    %t827 = call i64 @freak_llvm_word_eq(i64 %t824, i64 %t826)
    %t829 = icmp ne i64 %t823, 0
    %t830 = icmp ne i64 %t827, 0
    %t831 = or i1 %t829, %t830
    %t828 = zext i1 %t831 to i64
    %t832 = load i64, i64* %c
    %t833 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.38, i64 0, i64 0
    %t834 = ptrtoint i8* %t833 to i64
    %t835 = call i64 @freak_llvm_word_eq(i64 %t832, i64 %t834)
    %t837 = icmp ne i64 %t828, 0
    %t838 = icmp ne i64 %t835, 0
    %t839 = or i1 %t837, %t838
    %t836 = zext i1 %t839 to i64
    %t840 = load i64, i64* %c
    %t841 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.39, i64 0, i64 0
    %t842 = ptrtoint i8* %t841 to i64
    %t843 = call i64 @freak_llvm_word_eq(i64 %t840, i64 %t842)
    %t845 = icmp ne i64 %t836, 0
    %t846 = icmp ne i64 %t843, 0
    %t847 = or i1 %t845, %t846
    %t844 = zext i1 %t847 to i64
    %t848 = load i64, i64* %c
    %t849 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.40, i64 0, i64 0
    %t850 = ptrtoint i8* %t849 to i64
    %t851 = call i64 @freak_llvm_word_eq(i64 %t848, i64 %t850)
    %t853 = icmp ne i64 %t844, 0
    %t854 = icmp ne i64 %t851, 0
    %t855 = or i1 %t853, %t854
    %t852 = zext i1 %t855 to i64
    %t859 = icmp ne i64 %t852, 0
    br i1 %t859, label %if.then.856, label %if.end.858
if.then.856:
    ret i64 1
    br label %if.end.858
if.end.858:
    %t860 = load i64, i64* %c
    %t861 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.41, i64 0, i64 0
    %t862 = ptrtoint i8* %t861 to i64
    %t863 = call i64 @freak_llvm_word_eq(i64 %t860, i64 %t862)
    %t864 = load i64, i64* %c
    %t865 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.42, i64 0, i64 0
    %t866 = ptrtoint i8* %t865 to i64
    %t867 = call i64 @freak_llvm_word_eq(i64 %t864, i64 %t866)
    %t869 = icmp ne i64 %t863, 0
    %t870 = icmp ne i64 %t867, 0
    %t871 = or i1 %t869, %t870
    %t868 = zext i1 %t871 to i64
    %t872 = load i64, i64* %c
    %t873 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.43, i64 0, i64 0
    %t874 = ptrtoint i8* %t873 to i64
    %t875 = call i64 @freak_llvm_word_eq(i64 %t872, i64 %t874)
    %t877 = icmp ne i64 %t868, 0
    %t878 = icmp ne i64 %t875, 0
    %t879 = or i1 %t877, %t878
    %t876 = zext i1 %t879 to i64
    %t880 = load i64, i64* %c
    %t881 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.44, i64 0, i64 0
    %t882 = ptrtoint i8* %t881 to i64
    %t883 = call i64 @freak_llvm_word_eq(i64 %t880, i64 %t882)
    %t885 = icmp ne i64 %t876, 0
    %t886 = icmp ne i64 %t883, 0
    %t887 = or i1 %t885, %t886
    %t884 = zext i1 %t887 to i64
    %t888 = load i64, i64* %c
    %t889 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.45, i64 0, i64 0
    %t890 = ptrtoint i8* %t889 to i64
    %t891 = call i64 @freak_llvm_word_eq(i64 %t888, i64 %t890)
    %t893 = icmp ne i64 %t884, 0
    %t894 = icmp ne i64 %t891, 0
    %t895 = or i1 %t893, %t894
    %t892 = zext i1 %t895 to i64
    %t899 = icmp ne i64 %t892, 0
    br i1 %t899, label %if.then.896, label %if.end.898
if.then.896:
    ret i64 1
    br label %if.end.898
if.end.898:
    %t900 = load i64, i64* %c
    %t901 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.46, i64 0, i64 0
    %t902 = ptrtoint i8* %t901 to i64
    %t903 = call i64 @freak_llvm_word_eq(i64 %t900, i64 %t902)
    %t904 = load i64, i64* %c
    %t905 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.47, i64 0, i64 0
    %t906 = ptrtoint i8* %t905 to i64
    %t907 = call i64 @freak_llvm_word_eq(i64 %t904, i64 %t906)
    %t909 = icmp ne i64 %t903, 0
    %t910 = icmp ne i64 %t907, 0
    %t911 = or i1 %t909, %t910
    %t908 = zext i1 %t911 to i64
    %t912 = load i64, i64* %c
    %t913 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.48, i64 0, i64 0
    %t914 = ptrtoint i8* %t913 to i64
    %t915 = call i64 @freak_llvm_word_eq(i64 %t912, i64 %t914)
    %t917 = icmp ne i64 %t908, 0
    %t918 = icmp ne i64 %t915, 0
    %t919 = or i1 %t917, %t918
    %t916 = zext i1 %t919 to i64
    %t920 = load i64, i64* %c
    %t921 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.49, i64 0, i64 0
    %t922 = ptrtoint i8* %t921 to i64
    %t923 = call i64 @freak_llvm_word_eq(i64 %t920, i64 %t922)
    %t925 = icmp ne i64 %t916, 0
    %t926 = icmp ne i64 %t923, 0
    %t927 = or i1 %t925, %t926
    %t924 = zext i1 %t927 to i64
    %t928 = load i64, i64* %c
    %t929 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.50, i64 0, i64 0
    %t930 = ptrtoint i8* %t929 to i64
    %t931 = call i64 @freak_llvm_word_eq(i64 %t928, i64 %t930)
    %t933 = icmp ne i64 %t924, 0
    %t934 = icmp ne i64 %t931, 0
    %t935 = or i1 %t933, %t934
    %t932 = zext i1 %t935 to i64
    %t939 = icmp ne i64 %t932, 0
    br i1 %t939, label %if.then.936, label %if.end.938
if.then.936:
    ret i64 1
    br label %if.end.938
if.end.938:
    %t940 = load i64, i64* %c
    %t941 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.51, i64 0, i64 0
    %t942 = ptrtoint i8* %t941 to i64
    %t943 = call i64 @freak_llvm_word_eq(i64 %t940, i64 %t942)
    %t944 = load i64, i64* %c
    %t945 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.52, i64 0, i64 0
    %t946 = ptrtoint i8* %t945 to i64
    %t947 = call i64 @freak_llvm_word_eq(i64 %t944, i64 %t946)
    %t949 = icmp ne i64 %t943, 0
    %t950 = icmp ne i64 %t947, 0
    %t951 = or i1 %t949, %t950
    %t948 = zext i1 %t951 to i64
    %t952 = load i64, i64* %c
    %t953 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.53, i64 0, i64 0
    %t954 = ptrtoint i8* %t953 to i64
    %t955 = call i64 @freak_llvm_word_eq(i64 %t952, i64 %t954)
    %t957 = icmp ne i64 %t948, 0
    %t958 = icmp ne i64 %t955, 0
    %t959 = or i1 %t957, %t958
    %t956 = zext i1 %t959 to i64
    %t960 = load i64, i64* %c
    %t961 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.54, i64 0, i64 0
    %t962 = ptrtoint i8* %t961 to i64
    %t963 = call i64 @freak_llvm_word_eq(i64 %t960, i64 %t962)
    %t965 = icmp ne i64 %t956, 0
    %t966 = icmp ne i64 %t963, 0
    %t967 = or i1 %t965, %t966
    %t964 = zext i1 %t967 to i64
    %t968 = load i64, i64* %c
    %t969 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.55, i64 0, i64 0
    %t970 = ptrtoint i8* %t969 to i64
    %t971 = call i64 @freak_llvm_word_eq(i64 %t968, i64 %t970)
    %t973 = icmp ne i64 %t964, 0
    %t974 = icmp ne i64 %t971, 0
    %t975 = or i1 %t973, %t974
    %t972 = zext i1 %t975 to i64
    %t976 = load i64, i64* %c
    %t977 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.56, i64 0, i64 0
    %t978 = ptrtoint i8* %t977 to i64
    %t979 = call i64 @freak_llvm_word_eq(i64 %t976, i64 %t978)
    %t981 = icmp ne i64 %t972, 0
    %t982 = icmp ne i64 %t979, 0
    %t983 = or i1 %t981, %t982
    %t980 = zext i1 %t983 to i64
    %t987 = icmp ne i64 %t980, 0
    br i1 %t987, label %if.then.984, label %if.end.986
if.then.984:
    ret i64 1
    br label %if.end.986
if.end.986:
    %t988 = load i64, i64* %c
    %t989 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.57, i64 0, i64 0
    %t990 = ptrtoint i8* %t989 to i64
    %t991 = call i64 @freak_llvm_word_eq(i64 %t988, i64 %t990)
    %t992 = load i64, i64* %c
    %t993 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.58, i64 0, i64 0
    %t994 = ptrtoint i8* %t993 to i64
    %t995 = call i64 @freak_llvm_word_eq(i64 %t992, i64 %t994)
    %t997 = icmp ne i64 %t991, 0
    %t998 = icmp ne i64 %t995, 0
    %t999 = or i1 %t997, %t998
    %t996 = zext i1 %t999 to i64
    %t1000 = load i64, i64* %c
    %t1001 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.59, i64 0, i64 0
    %t1002 = ptrtoint i8* %t1001 to i64
    %t1003 = call i64 @freak_llvm_word_eq(i64 %t1000, i64 %t1002)
    %t1005 = icmp ne i64 %t996, 0
    %t1006 = icmp ne i64 %t1003, 0
    %t1007 = or i1 %t1005, %t1006
    %t1004 = zext i1 %t1007 to i64
    %t1008 = load i64, i64* %c
    %t1009 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.60, i64 0, i64 0
    %t1010 = ptrtoint i8* %t1009 to i64
    %t1011 = call i64 @freak_llvm_word_eq(i64 %t1008, i64 %t1010)
    %t1013 = icmp ne i64 %t1004, 0
    %t1014 = icmp ne i64 %t1011, 0
    %t1015 = or i1 %t1013, %t1014
    %t1012 = zext i1 %t1015 to i64
    %t1016 = load i64, i64* %c
    %t1017 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.61, i64 0, i64 0
    %t1018 = ptrtoint i8* %t1017 to i64
    %t1019 = call i64 @freak_llvm_word_eq(i64 %t1016, i64 %t1018)
    %t1021 = icmp ne i64 %t1012, 0
    %t1022 = icmp ne i64 %t1019, 0
    %t1023 = or i1 %t1021, %t1022
    %t1020 = zext i1 %t1023 to i64
    %t1027 = icmp ne i64 %t1020, 0
    br i1 %t1027, label %if.then.1024, label %if.end.1026
if.then.1024:
    ret i64 1
    br label %if.end.1026
if.end.1026:
    %t1028 = load i64, i64* %c
    %t1029 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.62, i64 0, i64 0
    %t1030 = ptrtoint i8* %t1029 to i64
    %t1031 = call i64 @freak_llvm_word_eq(i64 %t1028, i64 %t1030)
    %t1032 = load i64, i64* %c
    %t1033 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.63, i64 0, i64 0
    %t1034 = ptrtoint i8* %t1033 to i64
    %t1035 = call i64 @freak_llvm_word_eq(i64 %t1032, i64 %t1034)
    %t1037 = icmp ne i64 %t1031, 0
    %t1038 = icmp ne i64 %t1035, 0
    %t1039 = or i1 %t1037, %t1038
    %t1036 = zext i1 %t1039 to i64
    %t1040 = load i64, i64* %c
    %t1041 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.64, i64 0, i64 0
    %t1042 = ptrtoint i8* %t1041 to i64
    %t1043 = call i64 @freak_llvm_word_eq(i64 %t1040, i64 %t1042)
    %t1045 = icmp ne i64 %t1036, 0
    %t1046 = icmp ne i64 %t1043, 0
    %t1047 = or i1 %t1045, %t1046
    %t1044 = zext i1 %t1047 to i64
    %t1048 = load i64, i64* %c
    %t1049 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.65, i64 0, i64 0
    %t1050 = ptrtoint i8* %t1049 to i64
    %t1051 = call i64 @freak_llvm_word_eq(i64 %t1048, i64 %t1050)
    %t1053 = icmp ne i64 %t1044, 0
    %t1054 = icmp ne i64 %t1051, 0
    %t1055 = or i1 %t1053, %t1054
    %t1052 = zext i1 %t1055 to i64
    %t1056 = load i64, i64* %c
    %t1057 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.66, i64 0, i64 0
    %t1058 = ptrtoint i8* %t1057 to i64
    %t1059 = call i64 @freak_llvm_word_eq(i64 %t1056, i64 %t1058)
    %t1061 = icmp ne i64 %t1052, 0
    %t1062 = icmp ne i64 %t1059, 0
    %t1063 = or i1 %t1061, %t1062
    %t1060 = zext i1 %t1063 to i64
    %t1067 = icmp ne i64 %t1060, 0
    br i1 %t1067, label %if.then.1064, label %if.end.1066
if.then.1064:
    ret i64 1
    br label %if.end.1066
if.end.1066:
    %t1068 = load i64, i64* %c
    %t1069 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.67, i64 0, i64 0
    %t1070 = ptrtoint i8* %t1069 to i64
    %t1071 = call i64 @freak_llvm_word_eq(i64 %t1068, i64 %t1070)
    %t1072 = load i64, i64* %c
    %t1073 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.68, i64 0, i64 0
    %t1074 = ptrtoint i8* %t1073 to i64
    %t1075 = call i64 @freak_llvm_word_eq(i64 %t1072, i64 %t1074)
    %t1077 = icmp ne i64 %t1071, 0
    %t1078 = icmp ne i64 %t1075, 0
    %t1079 = or i1 %t1077, %t1078
    %t1076 = zext i1 %t1079 to i64
    %t1080 = load i64, i64* %c
    %t1081 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.69, i64 0, i64 0
    %t1082 = ptrtoint i8* %t1081 to i64
    %t1083 = call i64 @freak_llvm_word_eq(i64 %t1080, i64 %t1082)
    %t1085 = icmp ne i64 %t1076, 0
    %t1086 = icmp ne i64 %t1083, 0
    %t1087 = or i1 %t1085, %t1086
    %t1084 = zext i1 %t1087 to i64
    %t1088 = load i64, i64* %c
    %t1089 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.70, i64 0, i64 0
    %t1090 = ptrtoint i8* %t1089 to i64
    %t1091 = call i64 @freak_llvm_word_eq(i64 %t1088, i64 %t1090)
    %t1093 = icmp ne i64 %t1084, 0
    %t1094 = icmp ne i64 %t1091, 0
    %t1095 = or i1 %t1093, %t1094
    %t1092 = zext i1 %t1095 to i64
    %t1096 = load i64, i64* %c
    %t1097 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.71, i64 0, i64 0
    %t1098 = ptrtoint i8* %t1097 to i64
    %t1099 = call i64 @freak_llvm_word_eq(i64 %t1096, i64 %t1098)
    %t1101 = icmp ne i64 %t1092, 0
    %t1102 = icmp ne i64 %t1099, 0
    %t1103 = or i1 %t1101, %t1102
    %t1100 = zext i1 %t1103 to i64
    %t1107 = icmp ne i64 %t1100, 0
    br i1 %t1107, label %if.then.1104, label %if.end.1106
if.then.1104:
    ret i64 1
    br label %if.end.1106
if.end.1106:
    %t1108 = load i64, i64* %c
    %t1109 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.72, i64 0, i64 0
    %t1110 = ptrtoint i8* %t1109 to i64
    %t1111 = call i64 @freak_llvm_word_eq(i64 %t1108, i64 %t1110)
    %t1112 = load i64, i64* %c
    %t1113 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.73, i64 0, i64 0
    %t1114 = ptrtoint i8* %t1113 to i64
    %t1115 = call i64 @freak_llvm_word_eq(i64 %t1112, i64 %t1114)
    %t1117 = icmp ne i64 %t1111, 0
    %t1118 = icmp ne i64 %t1115, 0
    %t1119 = or i1 %t1117, %t1118
    %t1116 = zext i1 %t1119 to i64
    %t1120 = load i64, i64* %c
    %t1121 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.74, i64 0, i64 0
    %t1122 = ptrtoint i8* %t1121 to i64
    %t1123 = call i64 @freak_llvm_word_eq(i64 %t1120, i64 %t1122)
    %t1125 = icmp ne i64 %t1116, 0
    %t1126 = icmp ne i64 %t1123, 0
    %t1127 = or i1 %t1125, %t1126
    %t1124 = zext i1 %t1127 to i64
    %t1128 = load i64, i64* %c
    %t1129 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.75, i64 0, i64 0
    %t1130 = ptrtoint i8* %t1129 to i64
    %t1131 = call i64 @freak_llvm_word_eq(i64 %t1128, i64 %t1130)
    %t1133 = icmp ne i64 %t1124, 0
    %t1134 = icmp ne i64 %t1131, 0
    %t1135 = or i1 %t1133, %t1134
    %t1132 = zext i1 %t1135 to i64
    %t1136 = load i64, i64* %c
    %t1137 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.76, i64 0, i64 0
    %t1138 = ptrtoint i8* %t1137 to i64
    %t1139 = call i64 @freak_llvm_word_eq(i64 %t1136, i64 %t1138)
    %t1141 = icmp ne i64 %t1132, 0
    %t1142 = icmp ne i64 %t1139, 0
    %t1143 = or i1 %t1141, %t1142
    %t1140 = zext i1 %t1143 to i64
    %t1147 = icmp ne i64 %t1140, 0
    br i1 %t1147, label %if.then.1144, label %if.end.1146
if.then.1144:
    ret i64 1
    br label %if.end.1146
if.end.1146:
    %t1148 = load i64, i64* %c
    %t1149 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.77, i64 0, i64 0
    %t1150 = ptrtoint i8* %t1149 to i64
    %t1151 = call i64 @freak_llvm_word_eq(i64 %t1148, i64 %t1150)
    %t1152 = load i64, i64* %c
    %t1153 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.78, i64 0, i64 0
    %t1154 = ptrtoint i8* %t1153 to i64
    %t1155 = call i64 @freak_llvm_word_eq(i64 %t1152, i64 %t1154)
    %t1157 = icmp ne i64 %t1151, 0
    %t1158 = icmp ne i64 %t1155, 0
    %t1159 = or i1 %t1157, %t1158
    %t1156 = zext i1 %t1159 to i64
    %t1160 = load i64, i64* %c
    %t1161 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.79, i64 0, i64 0
    %t1162 = ptrtoint i8* %t1161 to i64
    %t1163 = call i64 @freak_llvm_word_eq(i64 %t1160, i64 %t1162)
    %t1165 = icmp ne i64 %t1156, 0
    %t1166 = icmp ne i64 %t1163, 0
    %t1167 = or i1 %t1165, %t1166
    %t1164 = zext i1 %t1167 to i64
    %t1168 = load i64, i64* %c
    %t1169 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.80, i64 0, i64 0
    %t1170 = ptrtoint i8* %t1169 to i64
    %t1171 = call i64 @freak_llvm_word_eq(i64 %t1168, i64 %t1170)
    %t1173 = icmp ne i64 %t1164, 0
    %t1174 = icmp ne i64 %t1171, 0
    %t1175 = or i1 %t1173, %t1174
    %t1172 = zext i1 %t1175 to i64
    %t1176 = load i64, i64* %c
    %t1177 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.81, i64 0, i64 0
    %t1178 = ptrtoint i8* %t1177 to i64
    %t1179 = call i64 @freak_llvm_word_eq(i64 %t1176, i64 %t1178)
    %t1181 = icmp ne i64 %t1172, 0
    %t1182 = icmp ne i64 %t1179, 0
    %t1183 = or i1 %t1181, %t1182
    %t1180 = zext i1 %t1183 to i64
    %t1184 = load i64, i64* %c
    %t1185 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.82, i64 0, i64 0
    %t1186 = ptrtoint i8* %t1185 to i64
    %t1187 = call i64 @freak_llvm_word_eq(i64 %t1184, i64 %t1186)
    %t1189 = icmp ne i64 %t1180, 0
    %t1190 = icmp ne i64 %t1187, 0
    %t1191 = or i1 %t1189, %t1190
    %t1188 = zext i1 %t1191 to i64
    %t1195 = icmp ne i64 %t1188, 0
    br i1 %t1195, label %if.then.1192, label %if.end.1194
if.then.1192:
    ret i64 1
    br label %if.end.1194
if.end.1194:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_whitespace(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1196 = load i64, i64* %c
    %t1197 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.83, i64 0, i64 0
    %t1198 = ptrtoint i8* %t1197 to i64
    %t1199 = call i64 @freak_llvm_word_eq(i64 %t1196, i64 %t1198)
    %t1203 = icmp ne i64 %t1199, 0
    br i1 %t1203, label %if.then.1200, label %if.end.1202
if.then.1200:
    ret i64 1
    br label %if.end.1202
if.end.1202:
    %t1204 = load i64, i64* %c
    %t1205 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.84, i64 0, i64 0
    %t1206 = ptrtoint i8* %t1205 to i64
    %t1207 = call i64 @freak_llvm_word_eq(i64 %t1204, i64 %t1206)
    %t1211 = icmp ne i64 %t1207, 0
    br i1 %t1211, label %if.then.1208, label %if.end.1210
if.then.1208:
    ret i64 1
    br label %if.end.1210
if.end.1210:
    %t1212 = load i64, i64* %c
    %t1213 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.85, i64 0, i64 0
    %t1214 = ptrtoint i8* %t1213 to i64
    %t1215 = call i64 @freak_llvm_word_eq(i64 %t1212, i64 %t1214)
    %t1219 = icmp ne i64 %t1215, 0
    br i1 %t1219, label %if.then.1216, label %if.end.1218
if.then.1216:
    ret i64 1
    br label %if.end.1218
if.end.1218:
    %t1220 = load i64, i64* %c
    %t1221 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.86, i64 0, i64 0
    %t1222 = ptrtoint i8* %t1221 to i64
    %t1223 = call i64 @freak_llvm_word_eq(i64 %t1220, i64 %t1222)
    %t1227 = icmp ne i64 %t1223, 0
    br i1 %t1227, label %if.then.1224, label %if.end.1226
if.then.1224:
    ret i64 1
    br label %if.end.1226
if.end.1226:
    ret i64 0
    ret i64 0
}

define i64 @freak_string_starts_with(i64 %arg_s, i64 %arg_prefix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %prefix = alloca i64
    store i64 %arg_prefix, i64* %prefix
    %t1228 = load i64, i64* %s
    %t1229 = call i64 @freak_llvm_word_length(i64 %t1228)
    %slen_v1230 = alloca i64
    store i64 %t1229, i64* %slen_v1230
    %t1231 = load i64, i64* %prefix
    %t1232 = call i64 @freak_llvm_word_length(i64 %t1231)
    %plen_v1233 = alloca i64
    store i64 %t1232, i64* %plen_v1233
    %t1234 = load i64, i64* %plen_v1233
    %t1235 = load i64, i64* %slen_v1230
    %t1237 = icmp sgt i64 %t1234, %t1235
    %t1236 = zext i1 %t1237 to i64
    %t1241 = icmp ne i64 %t1236, 0
    br i1 %t1241, label %if.then.1238, label %if.end.1240
if.then.1238:
    ret i64 0
    br label %if.end.1240
if.end.1240:
    %si_v1242 = alloca i64
    store i64 0, i64* %si_v1242
    %t1248 = load i64, i64* %plen_v1233
    %rep.1247 = alloca i64
    store i64 0, i64* %rep.1247
    br label %loop.cond.1243
loop.cond.1243:
    %t1249 = load i64, i64* %rep.1247
    %t1250 = icmp slt i64 %t1249, %t1248
    br i1 %t1250, label %loop.body.1244, label %loop.end.1245
loop.body.1244:
    %t1251 = load i64, i64* %s
    %t1253 = load i64, i64* %si_v1242
    %t1252 = call i64 @freak_llvm_word_char_at(i64 %t1251, i64 %t1253)
    %t1254 = load i64, i64* %prefix
    %t1256 = load i64, i64* %si_v1242
    %t1255 = call i64 @freak_llvm_word_char_at(i64 %t1254, i64 %t1256)
    %t1257 = call i64 @freak_llvm_word_neq(i64 %t1252, i64 %t1255)
    %t1261 = icmp ne i64 %t1257, 0
    br i1 %t1261, label %if.then.1258, label %if.end.1260
if.then.1258:
    ret i64 0
    br label %if.end.1260
if.end.1260:
    %t1262 = load i64, i64* %si_v1242
    %t1263 = add i64 %t1262, 1
    store i64 %t1263, i64* %si_v1242
    br label %loop.inc.1246
loop.inc.1246:
    %t1264 = load i64, i64* %rep.1247
    %t1265 = add i64 %t1264, 1
    store i64 %t1265, i64* %rep.1247
    br label %loop.cond.1243
loop.end.1245:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_ends_with(i64 %arg_s, i64 %arg_suffix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %suffix = alloca i64
    store i64 %arg_suffix, i64* %suffix
    %t1266 = load i64, i64* %s
    %t1267 = call i64 @freak_llvm_word_length(i64 %t1266)
    %slen_v1268 = alloca i64
    store i64 %t1267, i64* %slen_v1268
    %t1269 = load i64, i64* %suffix
    %t1270 = call i64 @freak_llvm_word_length(i64 %t1269)
    %xlen_v1271 = alloca i64
    store i64 %t1270, i64* %xlen_v1271
    %t1272 = load i64, i64* %xlen_v1271
    %t1273 = load i64, i64* %slen_v1268
    %t1275 = icmp sgt i64 %t1272, %t1273
    %t1274 = zext i1 %t1275 to i64
    %t1279 = icmp ne i64 %t1274, 0
    br i1 %t1279, label %if.then.1276, label %if.end.1278
if.then.1276:
    ret i64 0
    br label %if.end.1278
if.end.1278:
    %t1280 = load i64, i64* %slen_v1268
    %t1281 = load i64, i64* %xlen_v1271
    %t1282 = sub i64 %t1280, %t1281
    %offset_v1283 = alloca i64
    store i64 %t1282, i64* %offset_v1283
    %ei_v1284 = alloca i64
    store i64 0, i64* %ei_v1284
    %t1290 = load i64, i64* %xlen_v1271
    %rep.1289 = alloca i64
    store i64 0, i64* %rep.1289
    br label %loop.cond.1285
loop.cond.1285:
    %t1291 = load i64, i64* %rep.1289
    %t1292 = icmp slt i64 %t1291, %t1290
    br i1 %t1292, label %loop.body.1286, label %loop.end.1287
loop.body.1286:
    %t1293 = load i64, i64* %s
    %t1295 = load i64, i64* %offset_v1283
    %t1296 = load i64, i64* %ei_v1284
    %t1297 = add i64 %t1295, %t1296
    %t1294 = call i64 @freak_llvm_word_char_at(i64 %t1293, i64 %t1297)
    %t1298 = load i64, i64* %suffix
    %t1300 = load i64, i64* %ei_v1284
    %t1299 = call i64 @freak_llvm_word_char_at(i64 %t1298, i64 %t1300)
    %t1301 = call i64 @freak_llvm_word_neq(i64 %t1294, i64 %t1299)
    %t1305 = icmp ne i64 %t1301, 0
    br i1 %t1305, label %if.then.1302, label %if.end.1304
if.then.1302:
    ret i64 0
    br label %if.end.1304
if.end.1304:
    %t1306 = load i64, i64* %ei_v1284
    %t1307 = add i64 %t1306, 1
    store i64 %t1307, i64* %ei_v1284
    br label %loop.inc.1288
loop.inc.1288:
    %t1308 = load i64, i64* %rep.1289
    %t1309 = add i64 %t1308, 1
    store i64 %t1309, i64* %rep.1289
    br label %loop.cond.1285
loop.end.1287:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_contains(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1310 = load i64, i64* %haystack
    %t1311 = load i64, i64* %needle
    %t1312 = call i64 @freak_string_count(i64 %t1310, i64 %t1311)
    %t1314 = icmp sgt i64 %t1312, 0
    %t1313 = zext i1 %t1314 to i64
    ret i64 %t1313
    ret i64 0
}

define i64 @freak_string_trim(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1315 = load i64, i64* %s
    %t1316 = call i64 @freak_llvm_word_length(i64 %t1315)
    %slen_v1317 = alloca i64
    store i64 %t1316, i64* %slen_v1317
    %t1318 = load i64, i64* %slen_v1317
    %t1320 = icmp eq i64 %t1318, 0
    %t1319 = zext i1 %t1320 to i64
    %t1324 = icmp ne i64 %t1319, 0
    br i1 %t1324, label %if.then.1321, label %if.end.1323
if.then.1321:
    %t1325 = load i64, i64* %s
    ret i64 %t1325
    br label %if.end.1323
if.end.1323:
    %tstart_v1326 = alloca i64
    store i64 0, i64* %tstart_v1326
    br label %loop.cond.1327
loop.cond.1327:
    %t1330 = load i64, i64* %tstart_v1326
    %t1331 = load i64, i64* %slen_v1317
    %t1333 = icmp sge i64 %t1330, %t1331
    %t1332 = zext i1 %t1333 to i64
    %t1334 = icmp eq i64 %t1332, 0
    br i1 %t1334, label %loop.body.1328, label %loop.end.1329
loop.body.1328:
    %t1335 = load i64, i64* %s
    %t1337 = load i64, i64* %tstart_v1326
    %t1336 = call i64 @freak_llvm_word_char_at(i64 %t1335, i64 %t1337)
    %t1338 = call i64 @freak_is_whitespace(i64 %t1336)
    %t1340 = icmp eq i64 %t1338, 0
    %t1339 = zext i1 %t1340 to i64
    %t1344 = icmp ne i64 %t1339, 0
    br i1 %t1344, label %if.then.1341, label %if.end.1343
if.then.1341:
    %t1345 = load i64, i64* %s
    %t1346 = load i64, i64* %tstart_v1326
    %t1347 = call i64 @freak_string_trim_end(i64 %t1345, i64 %t1346)
    ret i64 %t1347
    br label %if.end.1343
if.end.1343:
    %t1348 = load i64, i64* %tstart_v1326
    %t1349 = add i64 %t1348, 1
    store i64 %t1349, i64* %tstart_v1326
    br label %loop.cond.1327
loop.end.1329:
    %t1350 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.87, i64 0, i64 0
    %t1351 = ptrtoint i8* %t1350 to i64
    ret i64 %t1351
    ret i64 0
}

define i64 @freak_string_trim_end(i64 %arg_s, i64 %arg_tstart) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %tstart = alloca i64
    store i64 %arg_tstart, i64* %tstart
    %t1352 = load i64, i64* %s
    %t1353 = call i64 @freak_llvm_word_length(i64 %t1352)
    %t1354 = sub i64 %t1353, 1
    %tend_v1355 = alloca i64
    store i64 %t1354, i64* %tend_v1355
    br label %loop.cond.1356
loop.cond.1356:
    %t1359 = load i64, i64* %tend_v1355
    %t1360 = load i64, i64* %tstart
    %t1362 = icmp slt i64 %t1359, %t1360
    %t1361 = zext i1 %t1362 to i64
    %t1363 = icmp eq i64 %t1361, 0
    br i1 %t1363, label %loop.body.1357, label %loop.end.1358
loop.body.1357:
    %t1364 = load i64, i64* %s
    %t1366 = load i64, i64* %tend_v1355
    %t1365 = call i64 @freak_llvm_word_char_at(i64 %t1364, i64 %t1366)
    %t1367 = call i64 @freak_is_whitespace(i64 %t1365)
    %t1369 = icmp eq i64 %t1367, 0
    %t1368 = zext i1 %t1369 to i64
    %t1373 = icmp ne i64 %t1368, 0
    br i1 %t1373, label %if.then.1370, label %if.end.1372
if.then.1370:
    %t1374 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.88, i64 0, i64 0
    %t1375 = ptrtoint i8* %t1374 to i64
    %tout_v1376 = alloca i64
    store i64 %t1375, i64* %tout_v1376
    %t1377 = load i64, i64* %tstart
    %ti_v1378 = alloca i64
    store i64 %t1377, i64* %ti_v1378
    br label %loop.cond.1379
loop.cond.1379:
    %t1382 = load i64, i64* %ti_v1378
    %t1383 = load i64, i64* %tend_v1355
    %t1385 = icmp sgt i64 %t1382, %t1383
    %t1384 = zext i1 %t1385 to i64
    %t1386 = icmp eq i64 %t1384, 0
    br i1 %t1386, label %loop.body.1380, label %loop.end.1381
loop.body.1380:
    %t1387 = load i64, i64* %tout_v1376
    %t1388 = load i64, i64* %s
    %t1390 = load i64, i64* %ti_v1378
    %t1389 = call i64 @freak_llvm_word_char_at(i64 %t1388, i64 %t1390)
    %t1391 = call i64 @freak_llvm_word_concat(i64 %t1387, i64 %t1389)
    store i64 %t1391, i64* %tout_v1376
    %t1392 = load i64, i64* %ti_v1378
    %t1393 = add i64 %t1392, 1
    store i64 %t1393, i64* %ti_v1378
    br label %loop.cond.1379
loop.end.1381:
    %t1394 = load i64, i64* %tout_v1376
    ret i64 %t1394
    br label %if.end.1372
if.end.1372:
    %t1395 = load i64, i64* %tend_v1355
    %t1396 = sub i64 %t1395, 1
    store i64 %t1396, i64* %tend_v1355
    br label %loop.cond.1356
loop.end.1358:
    %t1397 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.89, i64 0, i64 0
    %t1398 = ptrtoint i8* %t1397 to i64
    ret i64 %t1398
    ret i64 0
}

define i64 @freak_string_replace(i64 %arg_s, i64 %arg_old_str, i64 %arg_new_str) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %old_str = alloca i64
    store i64 %arg_old_str, i64* %old_str
    %new_str = alloca i64
    store i64 %arg_new_str, i64* %new_str
    %t1399 = load i64, i64* %s
    %t1400 = call i64 @freak_llvm_word_length(i64 %t1399)
    %slen_v1401 = alloca i64
    store i64 %t1400, i64* %slen_v1401
    %t1402 = load i64, i64* %old_str
    %t1403 = call i64 @freak_llvm_word_length(i64 %t1402)
    %olen_v1404 = alloca i64
    store i64 %t1403, i64* %olen_v1404
    %t1405 = load i64, i64* %olen_v1404
    %t1407 = icmp eq i64 %t1405, 0
    %t1406 = zext i1 %t1407 to i64
    %t1411 = icmp ne i64 %t1406, 0
    br i1 %t1411, label %if.then.1408, label %if.end.1410
if.then.1408:
    %t1412 = load i64, i64* %s
    ret i64 %t1412
    br label %if.end.1410
if.end.1410:
    %t1413 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.90, i64 0, i64 0
    %t1414 = ptrtoint i8* %t1413 to i64
    %rout_v1415 = alloca i64
    store i64 %t1414, i64* %rout_v1415
    %ri_v1416 = alloca i64
    store i64 0, i64* %ri_v1416
    br label %loop.cond.1417
loop.cond.1417:
    %t1420 = load i64, i64* %ri_v1416
    %t1421 = load i64, i64* %slen_v1401
    %t1423 = icmp sge i64 %t1420, %t1421
    %t1422 = zext i1 %t1423 to i64
    %t1424 = icmp eq i64 %t1422, 0
    br i1 %t1424, label %loop.body.1418, label %loop.end.1419
loop.body.1418:
    %rmatch_v1425 = alloca i64
    store i64 1, i64* %rmatch_v1425
    %t1426 = load i64, i64* %ri_v1416
    %t1427 = load i64, i64* %olen_v1404
    %t1428 = add i64 %t1426, %t1427
    %t1429 = load i64, i64* %slen_v1401
    %t1431 = icmp sle i64 %t1428, %t1429
    %t1430 = zext i1 %t1431 to i64
    %t1435 = icmp ne i64 %t1430, 0
    br i1 %t1435, label %if.then.1432, label %if.else.1433
if.then.1432:
    %rj_v1436 = alloca i64
    store i64 0, i64* %rj_v1436
    %t1442 = load i64, i64* %olen_v1404
    %rep.1441 = alloca i64
    store i64 0, i64* %rep.1441
    br label %loop.cond.1437
loop.cond.1437:
    %t1443 = load i64, i64* %rep.1441
    %t1444 = icmp slt i64 %t1443, %t1442
    br i1 %t1444, label %loop.body.1438, label %loop.end.1439
loop.body.1438:
    %t1445 = load i64, i64* %rmatch_v1425
    %t1449 = icmp ne i64 %t1445, 0
    br i1 %t1449, label %if.then.1446, label %if.end.1448
if.then.1446:
    %t1450 = load i64, i64* %s
    %t1452 = load i64, i64* %ri_v1416
    %t1453 = load i64, i64* %rj_v1436
    %t1454 = add i64 %t1452, %t1453
    %t1451 = call i64 @freak_llvm_word_char_at(i64 %t1450, i64 %t1454)
    %t1455 = load i64, i64* %old_str
    %t1457 = load i64, i64* %rj_v1436
    %t1456 = call i64 @freak_llvm_word_char_at(i64 %t1455, i64 %t1457)
    %t1458 = call i64 @freak_llvm_word_neq(i64 %t1451, i64 %t1456)
    %t1462 = icmp ne i64 %t1458, 0
    br i1 %t1462, label %if.then.1459, label %if.end.1461
if.then.1459:
    store i64 0, i64* %rmatch_v1425
    br label %if.end.1461
if.end.1461:
    br label %if.end.1448
if.end.1448:
    %t1463 = load i64, i64* %rj_v1436
    %t1464 = add i64 %t1463, 1
    store i64 %t1464, i64* %rj_v1436
    br label %loop.inc.1440
loop.inc.1440:
    %t1465 = load i64, i64* %rep.1441
    %t1466 = add i64 %t1465, 1
    store i64 %t1466, i64* %rep.1441
    br label %loop.cond.1437
loop.end.1439:
    br label %if.end.1434
if.else.1433:
    store i64 0, i64* %rmatch_v1425
    br label %if.end.1434
if.end.1434:
    %t1467 = load i64, i64* %rmatch_v1425
    %t1471 = icmp ne i64 %t1467, 0
    br i1 %t1471, label %if.then.1468, label %if.else.1469
if.then.1468:
    %t1472 = load i64, i64* %rout_v1415
    %t1473 = load i64, i64* %new_str
    %t1474 = call i64 @freak_llvm_word_concat(i64 %t1472, i64 %t1473)
    store i64 %t1474, i64* %rout_v1415
    %t1475 = load i64, i64* %olen_v1404
    %t1476 = load i64, i64* %ri_v1416
    %t1477 = add i64 %t1476, %t1475
    store i64 %t1477, i64* %ri_v1416
    br label %if.end.1470
if.else.1469:
    %t1478 = load i64, i64* %rout_v1415
    %t1479 = load i64, i64* %s
    %t1481 = load i64, i64* %ri_v1416
    %t1480 = call i64 @freak_llvm_word_char_at(i64 %t1479, i64 %t1481)
    %t1482 = call i64 @freak_llvm_word_concat(i64 %t1478, i64 %t1480)
    store i64 %t1482, i64* %rout_v1415
    %t1483 = load i64, i64* %ri_v1416
    %t1484 = add i64 %t1483, 1
    store i64 %t1484, i64* %ri_v1416
    br label %if.end.1470
if.end.1470:
    br label %loop.cond.1417
loop.end.1419:
    %t1485 = load i64, i64* %rout_v1415
    ret i64 %t1485
    ret i64 0
}

define i64 @freak_string_substring(i64 %arg_s, i64 %arg_start_idx, i64 %arg_end_idx) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start_idx = alloca i64
    store i64 %arg_start_idx, i64* %start_idx
    %end_idx = alloca i64
    store i64 %arg_end_idx, i64* %end_idx
    %t1486 = load i64, i64* %s
    %t1487 = call i64 @freak_llvm_word_length(i64 %t1486)
    %slen_v1488 = alloca i64
    store i64 %t1487, i64* %slen_v1488
    %t1489 = load i64, i64* %start_idx
    %ss_v1490 = alloca i64
    store i64 %t1489, i64* %ss_v1490
    %t1491 = load i64, i64* %end_idx
    %se_v1492 = alloca i64
    store i64 %t1491, i64* %se_v1492
    %t1493 = load i64, i64* %ss_v1490
    %t1495 = icmp slt i64 %t1493, 0
    %t1494 = zext i1 %t1495 to i64
    %t1499 = icmp ne i64 %t1494, 0
    br i1 %t1499, label %if.then.1496, label %if.end.1498
if.then.1496:
    store i64 0, i64* %ss_v1490
    br label %if.end.1498
if.end.1498:
    %t1500 = load i64, i64* %se_v1492
    %t1501 = load i64, i64* %slen_v1488
    %t1503 = icmp sgt i64 %t1500, %t1501
    %t1502 = zext i1 %t1503 to i64
    %t1507 = icmp ne i64 %t1502, 0
    br i1 %t1507, label %if.then.1504, label %if.end.1506
if.then.1504:
    %t1508 = load i64, i64* %slen_v1488
    store i64 %t1508, i64* %se_v1492
    br label %if.end.1506
if.end.1506:
    %t1509 = load i64, i64* %ss_v1490
    %t1510 = load i64, i64* %se_v1492
    %t1512 = icmp sge i64 %t1509, %t1510
    %t1511 = zext i1 %t1512 to i64
    %t1516 = icmp ne i64 %t1511, 0
    br i1 %t1516, label %if.then.1513, label %if.end.1515
if.then.1513:
    %t1517 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.91, i64 0, i64 0
    %t1518 = ptrtoint i8* %t1517 to i64
    ret i64 %t1518
    br label %if.end.1515
if.end.1515:
    %t1519 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.92, i64 0, i64 0
    %t1520 = ptrtoint i8* %t1519 to i64
    %sub_out_v1521 = alloca i64
    store i64 %t1520, i64* %sub_out_v1521
    %t1522 = load i64, i64* %ss_v1490
    %si_v1523 = alloca i64
    store i64 %t1522, i64* %si_v1523
    br label %loop.cond.1524
loop.cond.1524:
    %t1527 = load i64, i64* %si_v1523
    %t1528 = load i64, i64* %se_v1492
    %t1530 = icmp sge i64 %t1527, %t1528
    %t1529 = zext i1 %t1530 to i64
    %t1531 = icmp eq i64 %t1529, 0
    br i1 %t1531, label %loop.body.1525, label %loop.end.1526
loop.body.1525:
    %t1532 = load i64, i64* %sub_out_v1521
    %t1533 = load i64, i64* %s
    %t1535 = load i64, i64* %si_v1523
    %t1534 = call i64 @freak_llvm_word_char_at(i64 %t1533, i64 %t1535)
    %t1536 = call i64 @freak_llvm_word_concat(i64 %t1532, i64 %t1534)
    store i64 %t1536, i64* %sub_out_v1521
    %t1537 = load i64, i64* %si_v1523
    %t1538 = add i64 %t1537, 1
    store i64 %t1538, i64* %si_v1523
    br label %loop.cond.1524
loop.end.1526:
    %t1539 = load i64, i64* %sub_out_v1521
    ret i64 %t1539
    ret i64 0
}

define i64 @freak_string_index_of(i64 %arg_s, i64 %arg_needle) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1540 = load i64, i64* %s
    %t1541 = call i64 @freak_llvm_word_length(i64 %t1540)
    %slen_v1542 = alloca i64
    store i64 %t1541, i64* %slen_v1542
    %t1543 = load i64, i64* %needle
    %t1544 = call i64 @freak_llvm_word_length(i64 %t1543)
    %nlen_v1545 = alloca i64
    store i64 %t1544, i64* %nlen_v1545
    %t1546 = load i64, i64* %nlen_v1545
    %t1548 = icmp eq i64 %t1546, 0
    %t1547 = zext i1 %t1548 to i64
    %t1552 = icmp ne i64 %t1547, 0
    br i1 %t1552, label %if.then.1549, label %if.end.1551
if.then.1549:
    ret i64 0
    br label %if.end.1551
if.end.1551:
    %t1553 = load i64, i64* %nlen_v1545
    %t1554 = load i64, i64* %slen_v1542
    %t1556 = icmp sgt i64 %t1553, %t1554
    %t1555 = zext i1 %t1556 to i64
    %t1560 = icmp ne i64 %t1555, 0
    br i1 %t1560, label %if.then.1557, label %if.end.1559
if.then.1557:
    %t1561 = sub i64 0, 1
    ret i64 %t1561
    br label %if.end.1559
if.end.1559:
    %t1562 = load i64, i64* %slen_v1542
    %t1563 = load i64, i64* %nlen_v1545
    %t1564 = sub i64 %t1562, %t1563
    %t1565 = add i64 %t1564, 1
    %limit_v1566 = alloca i64
    store i64 %t1565, i64* %limit_v1566
    %fi_v1567 = alloca i64
    store i64 0, i64* %fi_v1567
    %t1573 = load i64, i64* %limit_v1566
    %rep.1572 = alloca i64
    store i64 0, i64* %rep.1572
    br label %loop.cond.1568
loop.cond.1568:
    %t1574 = load i64, i64* %rep.1572
    %t1575 = icmp slt i64 %t1574, %t1573
    br i1 %t1575, label %loop.body.1569, label %loop.end.1570
loop.body.1569:
    %fmatch_v1576 = alloca i64
    store i64 1, i64* %fmatch_v1576
    %fj_v1577 = alloca i64
    store i64 0, i64* %fj_v1577
    %t1583 = load i64, i64* %nlen_v1545
    %rep.1582 = alloca i64
    store i64 0, i64* %rep.1582
    br label %loop.cond.1578
loop.cond.1578:
    %t1584 = load i64, i64* %rep.1582
    %t1585 = icmp slt i64 %t1584, %t1583
    br i1 %t1585, label %loop.body.1579, label %loop.end.1580
loop.body.1579:
    %t1586 = load i64, i64* %fmatch_v1576
    %t1590 = icmp ne i64 %t1586, 0
    br i1 %t1590, label %if.then.1587, label %if.end.1589
if.then.1587:
    %t1591 = load i64, i64* %s
    %t1593 = load i64, i64* %fi_v1567
    %t1594 = load i64, i64* %fj_v1577
    %t1595 = add i64 %t1593, %t1594
    %t1592 = call i64 @freak_llvm_word_char_at(i64 %t1591, i64 %t1595)
    %t1596 = load i64, i64* %needle
    %t1598 = load i64, i64* %fj_v1577
    %t1597 = call i64 @freak_llvm_word_char_at(i64 %t1596, i64 %t1598)
    %t1599 = call i64 @freak_llvm_word_neq(i64 %t1592, i64 %t1597)
    %t1603 = icmp ne i64 %t1599, 0
    br i1 %t1603, label %if.then.1600, label %if.end.1602
if.then.1600:
    store i64 0, i64* %fmatch_v1576
    br label %if.end.1602
if.end.1602:
    br label %if.end.1589
if.end.1589:
    %t1604 = load i64, i64* %fj_v1577
    %t1605 = add i64 %t1604, 1
    store i64 %t1605, i64* %fj_v1577
    br label %loop.inc.1581
loop.inc.1581:
    %t1606 = load i64, i64* %rep.1582
    %t1607 = add i64 %t1606, 1
    store i64 %t1607, i64* %rep.1582
    br label %loop.cond.1578
loop.end.1580:
    %t1608 = load i64, i64* %fmatch_v1576
    %t1612 = icmp ne i64 %t1608, 0
    br i1 %t1612, label %if.then.1609, label %if.end.1611
if.then.1609:
    %t1613 = load i64, i64* %fi_v1567
    ret i64 %t1613
    br label %if.end.1611
if.end.1611:
    %t1614 = load i64, i64* %fi_v1567
    %t1615 = add i64 %t1614, 1
    store i64 %t1615, i64* %fi_v1567
    br label %loop.inc.1571
loop.inc.1571:
    %t1616 = load i64, i64* %rep.1572
    %t1617 = add i64 %t1616, 1
    store i64 %t1617, i64* %rep.1572
    br label %loop.cond.1568
loop.end.1570:
    %t1618 = sub i64 0, 1
    ret i64 %t1618
    ret i64 0
}

define i64 @freak_int_to_hex(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1619 = load i64, i64* %n
    %t1621 = icmp eq i64 %t1619, 0
    %t1620 = zext i1 %t1621 to i64
    %t1625 = icmp ne i64 %t1620, 0
    br i1 %t1625, label %if.then.1622, label %if.end.1624
if.then.1622:
    %t1626 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.93, i64 0, i64 0
    %t1627 = ptrtoint i8* %t1626 to i64
    ret i64 %t1627
    br label %if.end.1624
if.end.1624:
    %t1628 = getelementptr inbounds [17 x i8], [17 x i8]* @.str.94, i64 0, i64 0
    %t1629 = ptrtoint i8* %t1628 to i64
    %hex_chars_v1630 = alloca i64
    store i64 %t1629, i64* %hex_chars_v1630
    store i64 0, i64* @g_neg
    %t1631 = load i64, i64* %n
    %val_v1632 = alloca i64
    store i64 %t1631, i64* %val_v1632
    %t1633 = load i64, i64* %val_v1632
    %t1635 = icmp slt i64 %t1633, 0
    %t1634 = zext i1 %t1635 to i64
    %t1639 = icmp ne i64 %t1634, 0
    br i1 %t1639, label %if.then.1636, label %if.end.1638
if.then.1636:
    store i64 1, i64* @g_neg
    %t1640 = load i64, i64* %val_v1632
    %t1641 = sub i64 0, %t1640
    store i64 %t1641, i64* %val_v1632
    br label %if.end.1638
if.end.1638:
    %t1642 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.95, i64 0, i64 0
    %t1643 = ptrtoint i8* %t1642 to i64
    %hex_out_v1644 = alloca i64
    store i64 %t1643, i64* %hex_out_v1644
    br label %loop.cond.1645
loop.cond.1645:
    %t1648 = load i64, i64* %val_v1632
    %t1650 = icmp sle i64 %t1648, 0
    %t1649 = zext i1 %t1650 to i64
    %t1651 = icmp eq i64 %t1649, 0
    br i1 %t1651, label %loop.body.1646, label %loop.end.1647
loop.body.1646:
    %t1652 = load i64, i64* %val_v1632
    %t1653 = load i64, i64* %val_v1632
    %t1654 = sdiv i64 %t1653, 16
    %t1655 = mul i64 %t1654, 16
    %t1656 = sub i64 %t1652, %t1655
    %rem_v1657 = alloca i64
    store i64 %t1656, i64* %rem_v1657
    %t1658 = load i64, i64* %hex_chars_v1630
    %t1660 = load i64, i64* %rem_v1657
    %t1659 = call i64 @freak_llvm_word_char_at(i64 %t1658, i64 %t1660)
    %t1661 = load i64, i64* %hex_out_v1644
    %t1662 = call i64 @freak_llvm_word_concat(i64 %t1659, i64 %t1661)
    store i64 %t1662, i64* %hex_out_v1644
    %t1663 = load i64, i64* %val_v1632
    %t1664 = sdiv i64 %t1663, 16
    store i64 %t1664, i64* %val_v1632
    br label %loop.cond.1645
loop.end.1647:
    %t1665 = load i64, i64* @g_neg
    %t1669 = icmp ne i64 %t1665, 0
    br i1 %t1669, label %if.then.1666, label %if.end.1668
if.then.1666:
    %t1670 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.96, i64 0, i64 0
    %t1671 = ptrtoint i8* %t1670 to i64
    %t1672 = load i64, i64* %hex_out_v1644
    %t1673 = call i64 @freak_llvm_word_concat(i64 %t1671, i64 %t1672)
    store i64 %t1673, i64* %hex_out_v1644
    br label %if.end.1668
if.end.1668:
    %t1674 = load i64, i64* %hex_out_v1644
    ret i64 %t1674
    ret i64 0
}

define i64 @freak_int_to_bin(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1675 = load i64, i64* %n
    %t1677 = icmp eq i64 %t1675, 0
    %t1676 = zext i1 %t1677 to i64
    %t1681 = icmp ne i64 %t1676, 0
    br i1 %t1681, label %if.then.1678, label %if.end.1680
if.then.1678:
    %t1682 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.97, i64 0, i64 0
    %t1683 = ptrtoint i8* %t1682 to i64
    ret i64 %t1683
    br label %if.end.1680
if.end.1680:
    store i64 0, i64* @g_neg
    %t1684 = load i64, i64* %n
    %val_v1685 = alloca i64
    store i64 %t1684, i64* %val_v1685
    %t1686 = load i64, i64* %val_v1685
    %t1688 = icmp slt i64 %t1686, 0
    %t1687 = zext i1 %t1688 to i64
    %t1692 = icmp ne i64 %t1687, 0
    br i1 %t1692, label %if.then.1689, label %if.end.1691
if.then.1689:
    store i64 1, i64* @g_neg
    %t1693 = load i64, i64* %val_v1685
    %t1694 = sub i64 0, %t1693
    store i64 %t1694, i64* %val_v1685
    br label %if.end.1691
if.end.1691:
    %t1695 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.98, i64 0, i64 0
    %t1696 = ptrtoint i8* %t1695 to i64
    %bin_out_v1697 = alloca i64
    store i64 %t1696, i64* %bin_out_v1697
    br label %loop.cond.1698
loop.cond.1698:
    %t1701 = load i64, i64* %val_v1685
    %t1703 = icmp sle i64 %t1701, 0
    %t1702 = zext i1 %t1703 to i64
    %t1704 = icmp eq i64 %t1702, 0
    br i1 %t1704, label %loop.body.1699, label %loop.end.1700
loop.body.1699:
    %t1705 = load i64, i64* %val_v1685
    %t1706 = load i64, i64* %val_v1685
    %t1707 = sdiv i64 %t1706, 2
    %t1708 = mul i64 %t1707, 2
    %t1709 = sub i64 %t1705, %t1708
    %rem_v1710 = alloca i64
    store i64 %t1709, i64* %rem_v1710
    %t1711 = load i64, i64* %rem_v1710
    %t1713 = icmp eq i64 %t1711, 1
    %t1712 = zext i1 %t1713 to i64
    %t1717 = icmp ne i64 %t1712, 0
    br i1 %t1717, label %if.then.1714, label %if.else.1715
if.then.1714:
    %t1718 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.99, i64 0, i64 0
    %t1719 = ptrtoint i8* %t1718 to i64
    %t1720 = load i64, i64* %bin_out_v1697
    %t1721 = call i64 @freak_llvm_word_concat(i64 %t1719, i64 %t1720)
    store i64 %t1721, i64* %bin_out_v1697
    br label %if.end.1716
if.else.1715:
    %t1722 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.100, i64 0, i64 0
    %t1723 = ptrtoint i8* %t1722 to i64
    %t1724 = load i64, i64* %bin_out_v1697
    %t1725 = call i64 @freak_llvm_word_concat(i64 %t1723, i64 %t1724)
    store i64 %t1725, i64* %bin_out_v1697
    br label %if.end.1716
if.end.1716:
    %t1726 = load i64, i64* %val_v1685
    %t1727 = sdiv i64 %t1726, 2
    store i64 %t1727, i64* %val_v1685
    br label %loop.cond.1698
loop.end.1700:
    %t1728 = load i64, i64* @g_neg
    %t1732 = icmp ne i64 %t1728, 0
    br i1 %t1732, label %if.then.1729, label %if.end.1731
if.then.1729:
    %t1733 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.101, i64 0, i64 0
    %t1734 = ptrtoint i8* %t1733 to i64
    %t1735 = load i64, i64* %bin_out_v1697
    %t1736 = call i64 @freak_llvm_word_concat(i64 %t1734, i64 %t1735)
    store i64 %t1736, i64* %bin_out_v1697
    br label %if.end.1731
if.end.1731:
    %t1737 = load i64, i64* %bin_out_v1697
    ret i64 %t1737
    ret i64 0
}

define i64 @freak_int_to_oct(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1738 = load i64, i64* %n
    %t1740 = icmp eq i64 %t1738, 0
    %t1739 = zext i1 %t1740 to i64
    %t1744 = icmp ne i64 %t1739, 0
    br i1 %t1744, label %if.then.1741, label %if.end.1743
if.then.1741:
    %t1745 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.102, i64 0, i64 0
    %t1746 = ptrtoint i8* %t1745 to i64
    ret i64 %t1746
    br label %if.end.1743
if.end.1743:
    %t1747 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.103, i64 0, i64 0
    %t1748 = ptrtoint i8* %t1747 to i64
    %oct_chars_v1749 = alloca i64
    store i64 %t1748, i64* %oct_chars_v1749
    store i64 0, i64* @g_neg
    %t1750 = load i64, i64* %n
    %val_v1751 = alloca i64
    store i64 %t1750, i64* %val_v1751
    %t1752 = load i64, i64* %val_v1751
    %t1754 = icmp slt i64 %t1752, 0
    %t1753 = zext i1 %t1754 to i64
    %t1758 = icmp ne i64 %t1753, 0
    br i1 %t1758, label %if.then.1755, label %if.end.1757
if.then.1755:
    store i64 1, i64* @g_neg
    %t1759 = load i64, i64* %val_v1751
    %t1760 = sub i64 0, %t1759
    store i64 %t1760, i64* %val_v1751
    br label %if.end.1757
if.end.1757:
    %t1761 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.104, i64 0, i64 0
    %t1762 = ptrtoint i8* %t1761 to i64
    %oct_out_v1763 = alloca i64
    store i64 %t1762, i64* %oct_out_v1763
    br label %loop.cond.1764
loop.cond.1764:
    %t1767 = load i64, i64* %val_v1751
    %t1769 = icmp sle i64 %t1767, 0
    %t1768 = zext i1 %t1769 to i64
    %t1770 = icmp eq i64 %t1768, 0
    br i1 %t1770, label %loop.body.1765, label %loop.end.1766
loop.body.1765:
    %t1771 = load i64, i64* %val_v1751
    %t1772 = load i64, i64* %val_v1751
    %t1773 = sdiv i64 %t1772, 8
    %t1774 = mul i64 %t1773, 8
    %t1775 = sub i64 %t1771, %t1774
    %rem_v1776 = alloca i64
    store i64 %t1775, i64* %rem_v1776
    %t1777 = load i64, i64* %oct_chars_v1749
    %t1779 = load i64, i64* %rem_v1776
    %t1778 = call i64 @freak_llvm_word_char_at(i64 %t1777, i64 %t1779)
    %t1780 = load i64, i64* %oct_out_v1763
    %t1781 = call i64 @freak_llvm_word_concat(i64 %t1778, i64 %t1780)
    store i64 %t1781, i64* %oct_out_v1763
    %t1782 = load i64, i64* %val_v1751
    %t1783 = sdiv i64 %t1782, 8
    store i64 %t1783, i64* %val_v1751
    br label %loop.cond.1764
loop.end.1766:
    %t1784 = load i64, i64* @g_neg
    %t1788 = icmp ne i64 %t1784, 0
    br i1 %t1788, label %if.then.1785, label %if.end.1787
if.then.1785:
    %t1789 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.105, i64 0, i64 0
    %t1790 = ptrtoint i8* %t1789 to i64
    %t1791 = load i64, i64* %oct_out_v1763
    %t1792 = call i64 @freak_llvm_word_concat(i64 %t1790, i64 %t1791)
    store i64 %t1792, i64* %oct_out_v1763
    br label %if.end.1787
if.end.1787:
    %t1793 = load i64, i64* %oct_out_v1763
    ret i64 %t1793
    ret i64 0
}

define i64 @freak_char_to_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1794 = load i64, i64* %c
    %t1795 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.106, i64 0, i64 0
    %t1796 = ptrtoint i8* %t1795 to i64
    %t1797 = call i64 @freak_llvm_word_eq(i64 %t1794, i64 %t1796)
    %t1801 = icmp ne i64 %t1797, 0
    br i1 %t1801, label %if.then.1798, label %if.end.1800
if.then.1798:
    ret i64 0
    br label %if.end.1800
if.end.1800:
    %t1802 = load i64, i64* %c
    %t1803 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.107, i64 0, i64 0
    %t1804 = ptrtoint i8* %t1803 to i64
    %t1805 = call i64 @freak_llvm_word_eq(i64 %t1802, i64 %t1804)
    %t1809 = icmp ne i64 %t1805, 0
    br i1 %t1809, label %if.then.1806, label %if.end.1808
if.then.1806:
    ret i64 1
    br label %if.end.1808
if.end.1808:
    %t1810 = load i64, i64* %c
    %t1811 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.108, i64 0, i64 0
    %t1812 = ptrtoint i8* %t1811 to i64
    %t1813 = call i64 @freak_llvm_word_eq(i64 %t1810, i64 %t1812)
    %t1817 = icmp ne i64 %t1813, 0
    br i1 %t1817, label %if.then.1814, label %if.end.1816
if.then.1814:
    ret i64 2
    br label %if.end.1816
if.end.1816:
    %t1818 = load i64, i64* %c
    %t1819 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.109, i64 0, i64 0
    %t1820 = ptrtoint i8* %t1819 to i64
    %t1821 = call i64 @freak_llvm_word_eq(i64 %t1818, i64 %t1820)
    %t1825 = icmp ne i64 %t1821, 0
    br i1 %t1825, label %if.then.1822, label %if.end.1824
if.then.1822:
    ret i64 3
    br label %if.end.1824
if.end.1824:
    %t1826 = load i64, i64* %c
    %t1827 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.110, i64 0, i64 0
    %t1828 = ptrtoint i8* %t1827 to i64
    %t1829 = call i64 @freak_llvm_word_eq(i64 %t1826, i64 %t1828)
    %t1833 = icmp ne i64 %t1829, 0
    br i1 %t1833, label %if.then.1830, label %if.end.1832
if.then.1830:
    ret i64 4
    br label %if.end.1832
if.end.1832:
    %t1834 = load i64, i64* %c
    %t1835 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.111, i64 0, i64 0
    %t1836 = ptrtoint i8* %t1835 to i64
    %t1837 = call i64 @freak_llvm_word_eq(i64 %t1834, i64 %t1836)
    %t1841 = icmp ne i64 %t1837, 0
    br i1 %t1841, label %if.then.1838, label %if.end.1840
if.then.1838:
    ret i64 5
    br label %if.end.1840
if.end.1840:
    %t1842 = load i64, i64* %c
    %t1843 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.112, i64 0, i64 0
    %t1844 = ptrtoint i8* %t1843 to i64
    %t1845 = call i64 @freak_llvm_word_eq(i64 %t1842, i64 %t1844)
    %t1849 = icmp ne i64 %t1845, 0
    br i1 %t1849, label %if.then.1846, label %if.end.1848
if.then.1846:
    ret i64 6
    br label %if.end.1848
if.end.1848:
    %t1850 = load i64, i64* %c
    %t1851 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.113, i64 0, i64 0
    %t1852 = ptrtoint i8* %t1851 to i64
    %t1853 = call i64 @freak_llvm_word_eq(i64 %t1850, i64 %t1852)
    %t1857 = icmp ne i64 %t1853, 0
    br i1 %t1857, label %if.then.1854, label %if.end.1856
if.then.1854:
    ret i64 7
    br label %if.end.1856
if.end.1856:
    %t1858 = load i64, i64* %c
    %t1859 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.114, i64 0, i64 0
    %t1860 = ptrtoint i8* %t1859 to i64
    %t1861 = call i64 @freak_llvm_word_eq(i64 %t1858, i64 %t1860)
    %t1865 = icmp ne i64 %t1861, 0
    br i1 %t1865, label %if.then.1862, label %if.end.1864
if.then.1862:
    ret i64 8
    br label %if.end.1864
if.end.1864:
    %t1866 = load i64, i64* %c
    %t1867 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.115, i64 0, i64 0
    %t1868 = ptrtoint i8* %t1867 to i64
    %t1869 = call i64 @freak_llvm_word_eq(i64 %t1866, i64 %t1868)
    %t1873 = icmp ne i64 %t1869, 0
    br i1 %t1873, label %if.then.1870, label %if.end.1872
if.then.1870:
    ret i64 9
    br label %if.end.1872
if.end.1872:
    %t1874 = sub i64 0, 1
    ret i64 %t1874
    ret i64 0
}

define i64 @freak_word_to_int_safe(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1875 = load i64, i64* %s
    %t1876 = call i64 @freak_llvm_word_length(i64 %t1875)
    %slen_v1877 = alloca i64
    store i64 %t1876, i64* %slen_v1877
    %t1878 = load i64, i64* %slen_v1877
    %t1880 = icmp eq i64 %t1878, 0
    %t1879 = zext i1 %t1880 to i64
    %t1884 = icmp ne i64 %t1879, 0
    br i1 %t1884, label %if.then.1881, label %if.end.1883
if.then.1881:
    ret i64 0
    br label %if.end.1883
if.end.1883:
    store i64 0, i64* @g_neg
    %wi_v1885 = alloca i64
    store i64 0, i64* %wi_v1885
    %t1886 = load i64, i64* %s
    %t1887 = call i64 @freak_llvm_word_char_at(i64 %t1886, i64 0)
    %t1888 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.116, i64 0, i64 0
    %t1889 = ptrtoint i8* %t1888 to i64
    %t1890 = call i64 @freak_llvm_word_eq(i64 %t1887, i64 %t1889)
    %t1894 = icmp ne i64 %t1890, 0
    br i1 %t1894, label %if.then.1891, label %if.end.1893
if.then.1891:
    store i64 1, i64* @g_neg
    store i64 1, i64* %wi_v1885
    br label %if.end.1893
if.end.1893:
    %num_v1895 = alloca i64
    store i64 0, i64* %num_v1895
    br label %loop.cond.1896
loop.cond.1896:
    %t1899 = load i64, i64* %wi_v1885
    %t1900 = load i64, i64* %slen_v1877
    %t1902 = icmp sge i64 %t1899, %t1900
    %t1901 = zext i1 %t1902 to i64
    %t1903 = icmp eq i64 %t1901, 0
    br i1 %t1903, label %loop.body.1897, label %loop.end.1898
loop.body.1897:
    %t1904 = load i64, i64* %s
    %t1906 = load i64, i64* %wi_v1885
    %t1905 = call i64 @freak_llvm_word_char_at(i64 %t1904, i64 %t1906)
    %t1907 = call i64 @freak_char_to_digit(i64 %t1905)
    %d_v1908 = alloca i64
    store i64 %t1907, i64* %d_v1908
    %t1909 = load i64, i64* %d_v1908
    %t1911 = icmp slt i64 %t1909, 0
    %t1910 = zext i1 %t1911 to i64
    %t1915 = icmp ne i64 %t1910, 0
    br i1 %t1915, label %if.then.1912, label %if.end.1914
if.then.1912:
    ret i64 0
    br label %if.end.1914
if.end.1914:
    %t1916 = load i64, i64* %num_v1895
    %t1917 = mul i64 %t1916, 10
    %t1918 = load i64, i64* %d_v1908
    %t1919 = add i64 %t1917, %t1918
    store i64 %t1919, i64* %num_v1895
    %t1920 = load i64, i64* %wi_v1885
    %t1921 = add i64 %t1920, 1
    store i64 %t1921, i64* %wi_v1885
    br label %loop.cond.1896
loop.end.1898:
    %t1922 = load i64, i64* @g_neg
    %t1926 = icmp ne i64 %t1922, 0
    br i1 %t1926, label %if.then.1923, label %if.end.1925
if.then.1923:
    %t1927 = load i64, i64* %num_v1895
    %t1928 = sub i64 0, %t1927
    ret i64 %t1928
    br label %if.end.1925
if.end.1925:
    %t1929 = load i64, i64* %num_v1895
    ret i64 %t1929
    ret i64 0
}

define i64 @freak_bool_to_word(i64 %arg_b) {
entry:
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t1930 = load i64, i64* @g_b
    %t1934 = icmp ne i64 %t1930, 0
    br i1 %t1934, label %if.then.1931, label %if.end.1933
if.then.1931:
    %t1935 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.117, i64 0, i64 0
    %t1936 = ptrtoint i8* %t1935 to i64
    ret i64 %t1936
    br label %if.end.1933
if.end.1933:
    %t1937 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.118, i64 0, i64 0
    %t1938 = ptrtoint i8* %t1937 to i64
    ret i64 %t1938
    ret i64 0
}

define void @freak_array_sort_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t1939 = load i64, i64* %handle
    %t1940 = call i64 @freak_llvm_array_len(i64 %t1939)
    %alen_v1941 = alloca i64
    store i64 %t1940, i64* %alen_v1941
    %t1942 = load i64, i64* %alen_v1941
    %t1944 = icmp sle i64 %t1942, 1
    %t1943 = zext i1 %t1944 to i64
    %t1948 = icmp ne i64 %t1943, 0
    br i1 %t1948, label %if.then.1945, label %if.end.1947
if.then.1945:
    ret void
    br label %if.end.1947
if.end.1947:
    %si_v1949 = alloca i64
    store i64 1, i64* %si_v1949
    br label %loop.cond.1950
loop.cond.1950:
    %t1953 = load i64, i64* %si_v1949
    %t1954 = load i64, i64* %alen_v1941
    %t1956 = icmp sge i64 %t1953, %t1954
    %t1955 = zext i1 %t1956 to i64
    %t1957 = icmp eq i64 %t1955, 0
    br i1 %t1957, label %loop.body.1951, label %loop.end.1952
loop.body.1951:
    %t1958 = load i64, i64* %handle
    %t1959 = load i64, i64* %si_v1949
    %t1960 = call i64 @freak_llvm_array_get(i64 %t1958, i64 %t1959)
    %key_w_v1961 = alloca i64
    store i64 %t1960, i64* %key_w_v1961
    %t1962 = load i64, i64* %key_w_v1961
    %t1963 = call i64 @freak_llvm_word_to_int(i64 %t1962)
    %key_v1964 = alloca i64
    store i64 %t1963, i64* %key_v1964
    %t1965 = load i64, i64* %si_v1949
    %t1966 = sub i64 %t1965, 1
    %sj_v1967 = alloca i64
    store i64 %t1966, i64* %sj_v1967
    %sorted_v1968 = alloca i64
    store i64 0, i64* %sorted_v1968
    br label %loop.cond.1969
loop.cond.1969:
    %t1972 = load i64, i64* %sj_v1967
    %t1974 = icmp slt i64 %t1972, 0
    %t1973 = zext i1 %t1974 to i64
    %t1975 = load i64, i64* %sorted_v1968
    %t1977 = icmp ne i64 %t1973, 0
    %t1978 = icmp ne i64 %t1975, 0
    %t1979 = or i1 %t1977, %t1978
    %t1976 = zext i1 %t1979 to i64
    %t1980 = icmp eq i64 %t1976, 0
    br i1 %t1980, label %loop.body.1970, label %loop.end.1971
loop.body.1970:
    %t1981 = load i64, i64* %handle
    %t1982 = load i64, i64* %sj_v1967
    %t1983 = call i64 @freak_llvm_array_get(i64 %t1981, i64 %t1982)
    %cw_v1984 = alloca i64
    store i64 %t1983, i64* %cw_v1984
    %t1985 = load i64, i64* %cw_v1984
    %t1986 = call i64 @freak_llvm_word_to_int(i64 %t1985)
    %cv_v1987 = alloca i64
    store i64 %t1986, i64* %cv_v1987
    %t1988 = load i64, i64* %cv_v1987
    %t1989 = load i64, i64* %key_v1964
    %t1991 = icmp sgt i64 %t1988, %t1989
    %t1990 = zext i1 %t1991 to i64
    %t1995 = icmp ne i64 %t1990, 0
    br i1 %t1995, label %if.then.1992, label %if.else.1993
if.then.1992:
    %t1996 = load i64, i64* %handle
    %t1997 = load i64, i64* %sj_v1967
    %t1998 = add i64 %t1997, 1
    %t1999 = load i64, i64* %cw_v1984
    call void @freak_llvm_array_set(i64 %t1996, i64 %t1998, i64 %t1999)
    %t2000 = load i64, i64* %sj_v1967
    %t2001 = sub i64 %t2000, 1
    store i64 %t2001, i64* %sj_v1967
    br label %if.end.1994
if.else.1993:
    store i64 1, i64* %sorted_v1968
    br label %if.end.1994
if.end.1994:
    br label %loop.cond.1969
loop.end.1971:
    %t2002 = load i64, i64* %handle
    %t2003 = load i64, i64* %sj_v1967
    %t2004 = add i64 %t2003, 1
    %t2005 = load i64, i64* %key_v1964
    %t2006 = call i64 @freak_llvm_word_from_int(i64 %t2005)
    call void @freak_llvm_array_set(i64 %t2002, i64 %t2004, i64 %t2006)
    %t2007 = load i64, i64* %si_v1949
    %t2008 = add i64 %t2007, 1
    store i64 %t2008, i64* %si_v1949
    br label %loop.cond.1950
loop.end.1952:
    ret void
}

define void @freak_array_sort_word(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2009 = load i64, i64* %handle
    %t2010 = call i64 @freak_llvm_array_len(i64 %t2009)
    %alen_v2011 = alloca i64
    store i64 %t2010, i64* %alen_v2011
    %t2012 = load i64, i64* %alen_v2011
    %t2014 = icmp sle i64 %t2012, 1
    %t2013 = zext i1 %t2014 to i64
    %t2018 = icmp ne i64 %t2013, 0
    br i1 %t2018, label %if.then.2015, label %if.end.2017
if.then.2015:
    ret void
    br label %if.end.2017
if.end.2017:
    %si_v2019 = alloca i64
    store i64 1, i64* %si_v2019
    br label %loop.cond.2020
loop.cond.2020:
    %t2023 = load i64, i64* %si_v2019
    %t2024 = load i64, i64* %alen_v2011
    %t2026 = icmp sge i64 %t2023, %t2024
    %t2025 = zext i1 %t2026 to i64
    %t2027 = icmp eq i64 %t2025, 0
    br i1 %t2027, label %loop.body.2021, label %loop.end.2022
loop.body.2021:
    %t2028 = load i64, i64* %handle
    %t2029 = load i64, i64* %si_v2019
    %t2030 = call i64 @freak_llvm_array_get(i64 %t2028, i64 %t2029)
    %key_w_v2031 = alloca i64
    store i64 %t2030, i64* %key_w_v2031
    %t2032 = load i64, i64* %si_v2019
    %t2033 = sub i64 %t2032, 1
    %sj_v2034 = alloca i64
    store i64 %t2033, i64* %sj_v2034
    %sorted_v2035 = alloca i64
    store i64 0, i64* %sorted_v2035
    br label %loop.cond.2036
loop.cond.2036:
    %t2039 = load i64, i64* %sj_v2034
    %t2041 = icmp slt i64 %t2039, 0
    %t2040 = zext i1 %t2041 to i64
    %t2042 = load i64, i64* %sorted_v2035
    %t2044 = icmp ne i64 %t2040, 0
    %t2045 = icmp ne i64 %t2042, 0
    %t2046 = or i1 %t2044, %t2045
    %t2043 = zext i1 %t2046 to i64
    %t2047 = icmp eq i64 %t2043, 0
    br i1 %t2047, label %loop.body.2037, label %loop.end.2038
loop.body.2037:
    %t2048 = load i64, i64* %handle
    %t2049 = load i64, i64* %sj_v2034
    %t2050 = call i64 @freak_llvm_array_get(i64 %t2048, i64 %t2049)
    %cw_v2051 = alloca i64
    store i64 %t2050, i64* %cw_v2051
    %t2052 = load i64, i64* %cw_v2051
    %t2053 = load i64, i64* %key_w_v2031
    %t2054 = call i64 @freak_word_compare(i64 %t2052, i64 %t2053)
    %t2056 = icmp sgt i64 %t2054, 0
    %t2055 = zext i1 %t2056 to i64
    %t2060 = icmp ne i64 %t2055, 0
    br i1 %t2060, label %if.then.2057, label %if.else.2058
if.then.2057:
    %t2061 = load i64, i64* %handle
    %t2062 = load i64, i64* %sj_v2034
    %t2063 = add i64 %t2062, 1
    %t2064 = load i64, i64* %cw_v2051
    call void @freak_llvm_array_set(i64 %t2061, i64 %t2063, i64 %t2064)
    %t2065 = load i64, i64* %sj_v2034
    %t2066 = sub i64 %t2065, 1
    store i64 %t2066, i64* %sj_v2034
    br label %if.end.2059
if.else.2058:
    store i64 1, i64* %sorted_v2035
    br label %if.end.2059
if.end.2059:
    br label %loop.cond.2036
loop.end.2038:
    %t2067 = load i64, i64* %handle
    %t2068 = load i64, i64* %sj_v2034
    %t2069 = add i64 %t2068, 1
    %t2070 = load i64, i64* %key_w_v2031
    call void @freak_llvm_array_set(i64 %t2067, i64 %t2069, i64 %t2070)
    %t2071 = load i64, i64* %si_v2019
    %t2072 = add i64 %t2071, 1
    store i64 %t2072, i64* %si_v2019
    br label %loop.cond.2020
loop.end.2022:
    ret void
}

define i64 @freak_array_binary_search_int(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %lo_v2073 = alloca i64
    store i64 0, i64* %lo_v2073
    %t2074 = load i64, i64* %handle
    %t2075 = call i64 @freak_llvm_array_len(i64 %t2074)
    %t2076 = sub i64 %t2075, 1
    %hi_v2077 = alloca i64
    store i64 %t2076, i64* %hi_v2077
    br label %loop.cond.2078
loop.cond.2078:
    %t2081 = load i64, i64* %lo_v2073
    %t2082 = load i64, i64* %hi_v2077
    %t2084 = icmp sgt i64 %t2081, %t2082
    %t2083 = zext i1 %t2084 to i64
    %t2085 = icmp eq i64 %t2083, 0
    br i1 %t2085, label %loop.body.2079, label %loop.end.2080
loop.body.2079:
    %t2086 = load i64, i64* %hi_v2077
    %t2087 = load i64, i64* %lo_v2073
    %t2088 = sub i64 %t2086, %t2087
    %range_v2089 = alloca i64
    store i64 %t2088, i64* %range_v2089
    %t2090 = load i64, i64* %range_v2089
    %t2091 = sdiv i64 %t2090, 2
    %half_v2092 = alloca i64
    store i64 %t2091, i64* %half_v2092
    %t2093 = load i64, i64* %lo_v2073
    %t2094 = load i64, i64* %half_v2092
    %t2095 = add i64 %t2093, %t2094
    %mid_v2096 = alloca i64
    store i64 %t2095, i64* %mid_v2096
    %t2097 = load i64, i64* %handle
    %t2098 = load i64, i64* %mid_v2096
    %t2099 = call i64 @freak_llvm_array_get(i64 %t2097, i64 %t2098)
    %mw_v2100 = alloca i64
    store i64 %t2099, i64* %mw_v2100
    %t2101 = load i64, i64* %mw_v2100
    %t2102 = call i64 @freak_llvm_word_to_int(i64 %t2101)
    %mv_v2103 = alloca i64
    store i64 %t2102, i64* %mv_v2103
    %t2104 = load i64, i64* %mv_v2103
    %t2105 = load i64, i64* %target
    %t2107 = icmp eq i64 %t2104, %t2105
    %t2106 = zext i1 %t2107 to i64
    %t2111 = icmp ne i64 %t2106, 0
    br i1 %t2111, label %if.then.2108, label %if.end.2110
if.then.2108:
    %t2112 = load i64, i64* %mid_v2096
    ret i64 %t2112
    br label %if.end.2110
if.end.2110:
    %t2113 = load i64, i64* %mv_v2103
    %t2114 = load i64, i64* %target
    %t2116 = icmp slt i64 %t2113, %t2114
    %t2115 = zext i1 %t2116 to i64
    %t2120 = icmp ne i64 %t2115, 0
    br i1 %t2120, label %if.then.2117, label %if.else.2118
if.then.2117:
    %t2121 = load i64, i64* %mid_v2096
    %t2122 = add i64 %t2121, 1
    store i64 %t2122, i64* %lo_v2073
    br label %if.end.2119
if.else.2118:
    %t2123 = load i64, i64* %mid_v2096
    %t2124 = sub i64 %t2123, 1
    store i64 %t2124, i64* %hi_v2077
    br label %if.end.2119
if.end.2119:
    br label %loop.cond.2078
loop.end.2080:
    %t2125 = sub i64 0, 1
    ret i64 %t2125
    ret i64 0
}

define i64 @freak_array_find(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2126 = load i64, i64* %handle
    %t2127 = call i64 @freak_llvm_array_len(i64 %t2126)
    %alen_v2128 = alloca i64
    store i64 %t2127, i64* %alen_v2128
    %fi_v2129 = alloca i64
    store i64 0, i64* %fi_v2129
    %t2135 = load i64, i64* %alen_v2128
    %rep.2134 = alloca i64
    store i64 0, i64* %rep.2134
    br label %loop.cond.2130
loop.cond.2130:
    %t2136 = load i64, i64* %rep.2134
    %t2137 = icmp slt i64 %t2136, %t2135
    br i1 %t2137, label %loop.body.2131, label %loop.end.2132
loop.body.2131:
    %t2138 = load i64, i64* %handle
    %t2139 = load i64, i64* %fi_v2129
    %t2140 = call i64 @freak_llvm_array_get(i64 %t2138, i64 %t2139)
    %fw_v2141 = alloca i64
    store i64 %t2140, i64* %fw_v2141
    %t2142 = load i64, i64* %fw_v2141
    %t2143 = load i64, i64* %target
    %t2144 = call i64 @freak_llvm_word_eq(i64 %t2142, i64 %t2143)
    %t2148 = icmp ne i64 %t2144, 0
    br i1 %t2148, label %if.then.2145, label %if.end.2147
if.then.2145:
    %t2149 = load i64, i64* %fi_v2129
    ret i64 %t2149
    br label %if.end.2147
if.end.2147:
    %t2150 = load i64, i64* %fi_v2129
    %t2151 = add i64 %t2150, 1
    store i64 %t2151, i64* %fi_v2129
    br label %loop.inc.2133
loop.inc.2133:
    %t2152 = load i64, i64* %rep.2134
    %t2153 = add i64 %t2152, 1
    store i64 %t2153, i64* %rep.2134
    br label %loop.cond.2130
loop.end.2132:
    %t2154 = sub i64 0, 1
    ret i64 %t2154
    ret i64 0
}

define i64 @freak_array_contains(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2155 = load i64, i64* %handle
    %t2156 = load i64, i64* %target
    %t2157 = call i64 @freak_array_find(i64 %t2155, i64 %t2156)
    %t2159 = icmp sge i64 %t2157, 0
    %t2158 = zext i1 %t2159 to i64
    ret i64 %t2158
    ret i64 0
}

define void @freak_array_reverse(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2160 = load i64, i64* %handle
    %t2161 = call i64 @freak_llvm_array_len(i64 %t2160)
    %alen_v2162 = alloca i64
    store i64 %t2161, i64* %alen_v2162
    %t2163 = load i64, i64* %alen_v2162
    %t2165 = icmp sle i64 %t2163, 1
    %t2164 = zext i1 %t2165 to i64
    %t2169 = icmp ne i64 %t2164, 0
    br i1 %t2169, label %if.then.2166, label %if.end.2168
if.then.2166:
    ret void
    br label %if.end.2168
if.end.2168:
    %lo_v2170 = alloca i64
    store i64 0, i64* %lo_v2170
    %t2171 = load i64, i64* %alen_v2162
    %t2172 = sub i64 %t2171, 1
    %hi_v2173 = alloca i64
    store i64 %t2172, i64* %hi_v2173
    br label %loop.cond.2174
loop.cond.2174:
    %t2177 = load i64, i64* %lo_v2170
    %t2178 = load i64, i64* %hi_v2173
    %t2180 = icmp sge i64 %t2177, %t2178
    %t2179 = zext i1 %t2180 to i64
    %t2181 = icmp eq i64 %t2179, 0
    br i1 %t2181, label %loop.body.2175, label %loop.end.2176
loop.body.2175:
    %t2182 = load i64, i64* %handle
    %t2183 = load i64, i64* %lo_v2170
    %t2184 = call i64 @freak_llvm_array_get(i64 %t2182, i64 %t2183)
    %tmp_v2185 = alloca i64
    store i64 %t2184, i64* %tmp_v2185
    %t2186 = load i64, i64* %handle
    %t2187 = load i64, i64* %hi_v2173
    %t2188 = call i64 @freak_llvm_array_get(i64 %t2186, i64 %t2187)
    %hw_v2189 = alloca i64
    store i64 %t2188, i64* %hw_v2189
    %t2190 = load i64, i64* %handle
    %t2191 = load i64, i64* %lo_v2170
    %t2192 = load i64, i64* %hw_v2189
    call void @freak_llvm_array_set(i64 %t2190, i64 %t2191, i64 %t2192)
    %t2193 = load i64, i64* %handle
    %t2194 = load i64, i64* %hi_v2173
    %t2195 = load i64, i64* %tmp_v2185
    call void @freak_llvm_array_set(i64 %t2193, i64 %t2194, i64 %t2195)
    %t2196 = load i64, i64* %lo_v2170
    %t2197 = add i64 %t2196, 1
    store i64 %t2197, i64* %lo_v2170
    %t2198 = load i64, i64* %hi_v2173
    %t2199 = sub i64 %t2198, 1
    store i64 %t2199, i64* %hi_v2173
    br label %loop.cond.2174
loop.end.2176:
    ret void
}

define i64 @freak_array_copy(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2200 = call i64 @freak_llvm_array_new()
    %new_arr_v2201 = alloca i64
    store i64 %t2200, i64* %new_arr_v2201
    %t2202 = load i64, i64* %handle
    %t2203 = call i64 @freak_llvm_array_len(i64 %t2202)
    %alen_v2204 = alloca i64
    store i64 %t2203, i64* %alen_v2204
    %ci_v2205 = alloca i64
    store i64 0, i64* %ci_v2205
    %t2211 = load i64, i64* %alen_v2204
    %rep.2210 = alloca i64
    store i64 0, i64* %rep.2210
    br label %loop.cond.2206
loop.cond.2206:
    %t2212 = load i64, i64* %rep.2210
    %t2213 = icmp slt i64 %t2212, %t2211
    br i1 %t2213, label %loop.body.2207, label %loop.end.2208
loop.body.2207:
    %t2214 = load i64, i64* %handle
    %t2215 = load i64, i64* %ci_v2205
    %t2216 = call i64 @freak_llvm_array_get(i64 %t2214, i64 %t2215)
    %cw_v2217 = alloca i64
    store i64 %t2216, i64* %cw_v2217
    %t2218 = load i64, i64* %new_arr_v2201
    %t2219 = load i64, i64* %cw_v2217
    call void @freak_llvm_array_push(i64 %t2218, i64 %t2219)
    %t2220 = load i64, i64* %ci_v2205
    %t2221 = add i64 %t2220, 1
    store i64 %t2221, i64* %ci_v2205
    br label %loop.inc.2209
loop.inc.2209:
    %t2222 = load i64, i64* %rep.2210
    %t2223 = add i64 %t2222, 1
    store i64 %t2223, i64* %rep.2210
    br label %loop.cond.2206
loop.end.2208:
    %t2224 = load i64, i64* %new_arr_v2201
    ret i64 %t2224
    ret i64 0
}

define i64 @freak_array_join(i64 %arg_handle, i64 %arg_sep) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %sep = alloca i64
    store i64 %arg_sep, i64* %sep
    %t2225 = load i64, i64* %handle
    %t2226 = call i64 @freak_llvm_array_len(i64 %t2225)
    %alen_v2227 = alloca i64
    store i64 %t2226, i64* %alen_v2227
    %t2228 = load i64, i64* %alen_v2227
    %t2230 = icmp eq i64 %t2228, 0
    %t2229 = zext i1 %t2230 to i64
    %t2234 = icmp ne i64 %t2229, 0
    br i1 %t2234, label %if.then.2231, label %if.end.2233
if.then.2231:
    %t2235 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.119, i64 0, i64 0
    %t2236 = ptrtoint i8* %t2235 to i64
    ret i64 %t2236
    br label %if.end.2233
if.end.2233:
    %t2237 = load i64, i64* %handle
    %t2238 = call i64 @freak_llvm_array_get(i64 %t2237, i64 0)
    %aj_out_v2239 = alloca i64
    store i64 %t2238, i64* %aj_out_v2239
    %ji_v2240 = alloca i64
    store i64 1, i64* %ji_v2240
    br label %loop.cond.2241
loop.cond.2241:
    %t2244 = load i64, i64* %ji_v2240
    %t2245 = load i64, i64* %alen_v2227
    %t2247 = icmp sge i64 %t2244, %t2245
    %t2246 = zext i1 %t2247 to i64
    %t2248 = icmp eq i64 %t2246, 0
    br i1 %t2248, label %loop.body.2242, label %loop.end.2243
loop.body.2242:
    %t2249 = load i64, i64* %handle
    %t2250 = load i64, i64* %ji_v2240
    %t2251 = call i64 @freak_llvm_array_get(i64 %t2249, i64 %t2250)
    %jw_v2252 = alloca i64
    store i64 %t2251, i64* %jw_v2252
    %t2253 = load i64, i64* %aj_out_v2239
    %t2254 = load i64, i64* %sep
    %t2255 = call i64 @freak_llvm_word_concat(i64 %t2253, i64 %t2254)
    %t2256 = load i64, i64* %jw_v2252
    %t2257 = call i64 @freak_llvm_word_concat(i64 %t2255, i64 %t2256)
    store i64 %t2257, i64* %aj_out_v2239
    %t2258 = load i64, i64* %ji_v2240
    %t2259 = add i64 %t2258, 1
    store i64 %t2259, i64* %ji_v2240
    br label %loop.cond.2241
loop.end.2243:
    %t2260 = load i64, i64* %aj_out_v2239
    ret i64 %t2260
    ret i64 0
}

define i64 @freak_array_count(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2261 = load i64, i64* %handle
    %t2262 = call i64 @freak_llvm_array_len(i64 %t2261)
    %alen_v2263 = alloca i64
    store i64 %t2262, i64* %alen_v2263
    %cnt_v2264 = alloca i64
    store i64 0, i64* %cnt_v2264
    %ci_v2265 = alloca i64
    store i64 0, i64* %ci_v2265
    %t2271 = load i64, i64* %alen_v2263
    %rep.2270 = alloca i64
    store i64 0, i64* %rep.2270
    br label %loop.cond.2266
loop.cond.2266:
    %t2272 = load i64, i64* %rep.2270
    %t2273 = icmp slt i64 %t2272, %t2271
    br i1 %t2273, label %loop.body.2267, label %loop.end.2268
loop.body.2267:
    %t2274 = load i64, i64* %handle
    %t2275 = load i64, i64* %ci_v2265
    %t2276 = call i64 @freak_llvm_array_get(i64 %t2274, i64 %t2275)
    %cw_v2277 = alloca i64
    store i64 %t2276, i64* %cw_v2277
    %t2278 = load i64, i64* %cw_v2277
    %t2279 = load i64, i64* %target
    %t2280 = call i64 @freak_llvm_word_eq(i64 %t2278, i64 %t2279)
    %t2284 = icmp ne i64 %t2280, 0
    br i1 %t2284, label %if.then.2281, label %if.end.2283
if.then.2281:
    %t2285 = load i64, i64* %cnt_v2264
    %t2286 = add i64 %t2285, 1
    store i64 %t2286, i64* %cnt_v2264
    br label %if.end.2283
if.end.2283:
    %t2287 = load i64, i64* %ci_v2265
    %t2288 = add i64 %t2287, 1
    store i64 %t2288, i64* %ci_v2265
    br label %loop.inc.2269
loop.inc.2269:
    %t2289 = load i64, i64* %rep.2270
    %t2290 = add i64 %t2289, 1
    store i64 %t2290, i64* %rep.2270
    br label %loop.cond.2266
loop.end.2268:
    %t2291 = load i64, i64* %cnt_v2264
    ret i64 %t2291
    ret i64 0
}

define i64 @freak_array_unique(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2292 = load i64, i64* %handle
    %t2293 = call i64 @freak_llvm_array_len(i64 %t2292)
    %alen_v2294 = alloca i64
    store i64 %t2293, i64* %alen_v2294
    %t2295 = load i64, i64* %alen_v2294
    %t2297 = icmp sle i64 %t2295, 1
    %t2296 = zext i1 %t2297 to i64
    %t2301 = icmp ne i64 %t2296, 0
    br i1 %t2301, label %if.then.2298, label %if.end.2300
if.then.2298:
    %t2302 = load i64, i64* %alen_v2294
    ret i64 %t2302
    br label %if.end.2300
if.end.2300:
    %write_idx_v2303 = alloca i64
    store i64 1, i64* %write_idx_v2303
    %ri_v2304 = alloca i64
    store i64 1, i64* %ri_v2304
    br label %loop.cond.2305
loop.cond.2305:
    %t2308 = load i64, i64* %ri_v2304
    %t2309 = load i64, i64* %alen_v2294
    %t2311 = icmp sge i64 %t2308, %t2309
    %t2310 = zext i1 %t2311 to i64
    %t2312 = icmp eq i64 %t2310, 0
    br i1 %t2312, label %loop.body.2306, label %loop.end.2307
loop.body.2306:
    %t2313 = load i64, i64* %handle
    %t2314 = load i64, i64* %ri_v2304
    %t2315 = call i64 @freak_llvm_array_get(i64 %t2313, i64 %t2314)
    %cur_v2316 = alloca i64
    store i64 %t2315, i64* %cur_v2316
    %t2317 = load i64, i64* %handle
    %t2318 = load i64, i64* %ri_v2304
    %t2319 = sub i64 %t2318, 1
    %t2320 = call i64 @freak_llvm_array_get(i64 %t2317, i64 %t2319)
    %prev_v2321 = alloca i64
    store i64 %t2320, i64* %prev_v2321
    %t2322 = load i64, i64* %cur_v2316
    %t2323 = load i64, i64* %prev_v2321
    %t2324 = call i64 @freak_llvm_word_neq(i64 %t2322, i64 %t2323)
    %t2328 = icmp ne i64 %t2324, 0
    br i1 %t2328, label %if.then.2325, label %if.end.2327
if.then.2325:
    %t2329 = load i64, i64* %handle
    %t2330 = load i64, i64* %write_idx_v2303
    %t2331 = load i64, i64* %cur_v2316
    call void @freak_llvm_array_set(i64 %t2329, i64 %t2330, i64 %t2331)
    %t2332 = load i64, i64* %write_idx_v2303
    %t2333 = add i64 %t2332, 1
    store i64 %t2333, i64* %write_idx_v2303
    br label %if.end.2327
if.end.2327:
    %t2334 = load i64, i64* %ri_v2304
    %t2335 = add i64 %t2334, 1
    store i64 %t2335, i64* %ri_v2304
    br label %loop.cond.2305
loop.end.2307:
    %t2336 = load i64, i64* %write_idx_v2303
    ret i64 %t2336
    ret i64 0
}

define i64 @freak_array_sum_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2337 = load i64, i64* %handle
    %t2338 = call i64 @freak_llvm_array_len(i64 %t2337)
    %alen_v2339 = alloca i64
    store i64 %t2338, i64* %alen_v2339
    %total_v2340 = alloca i64
    store i64 0, i64* %total_v2340
    %si_v2341 = alloca i64
    store i64 0, i64* %si_v2341
    %t2347 = load i64, i64* %alen_v2339
    %rep.2346 = alloca i64
    store i64 0, i64* %rep.2346
    br label %loop.cond.2342
loop.cond.2342:
    %t2348 = load i64, i64* %rep.2346
    %t2349 = icmp slt i64 %t2348, %t2347
    br i1 %t2349, label %loop.body.2343, label %loop.end.2344
loop.body.2343:
    %t2350 = load i64, i64* %handle
    %t2351 = load i64, i64* %si_v2341
    %t2352 = call i64 @freak_llvm_array_get(i64 %t2350, i64 %t2351)
    %sw_v2353 = alloca i64
    store i64 %t2352, i64* %sw_v2353
    %t2354 = load i64, i64* %sw_v2353
    %t2355 = call i64 @freak_llvm_word_to_int(i64 %t2354)
    %t2356 = load i64, i64* %total_v2340
    %t2357 = add i64 %t2356, %t2355
    store i64 %t2357, i64* %total_v2340
    %t2358 = load i64, i64* %si_v2341
    %t2359 = add i64 %t2358, 1
    store i64 %t2359, i64* %si_v2341
    br label %loop.inc.2345
loop.inc.2345:
    %t2360 = load i64, i64* %rep.2346
    %t2361 = add i64 %t2360, 1
    store i64 %t2361, i64* %rep.2346
    br label %loop.cond.2342
loop.end.2344:
    %t2362 = load i64, i64* %total_v2340
    ret i64 %t2362
    ret i64 0
}

define i64 @freak_array_max_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2363 = load i64, i64* %handle
    %t2364 = call i64 @freak_llvm_array_len(i64 %t2363)
    %alen_v2365 = alloca i64
    store i64 %t2364, i64* %alen_v2365
    %t2366 = load i64, i64* %alen_v2365
    %t2368 = icmp eq i64 %t2366, 0
    %t2367 = zext i1 %t2368 to i64
    %t2372 = icmp ne i64 %t2367, 0
    br i1 %t2372, label %if.then.2369, label %if.end.2371
if.then.2369:
    ret i64 0
    br label %if.end.2371
if.end.2371:
    %t2373 = load i64, i64* %handle
    %t2374 = call i64 @freak_llvm_array_get(i64 %t2373, i64 0)
    %mw_v2375 = alloca i64
    store i64 %t2374, i64* %mw_v2375
    %t2376 = load i64, i64* %mw_v2375
    %t2377 = call i64 @freak_llvm_word_to_int(i64 %t2376)
    %mx_v2378 = alloca i64
    store i64 %t2377, i64* %mx_v2378
    %mi_v2379 = alloca i64
    store i64 1, i64* %mi_v2379
    br label %loop.cond.2380
loop.cond.2380:
    %t2383 = load i64, i64* %mi_v2379
    %t2384 = load i64, i64* %alen_v2365
    %t2386 = icmp sge i64 %t2383, %t2384
    %t2385 = zext i1 %t2386 to i64
    %t2387 = icmp eq i64 %t2385, 0
    br i1 %t2387, label %loop.body.2381, label %loop.end.2382
loop.body.2381:
    %t2388 = load i64, i64* %handle
    %t2389 = load i64, i64* %mi_v2379
    %t2390 = call i64 @freak_llvm_array_get(i64 %t2388, i64 %t2389)
    %cw_v2391 = alloca i64
    store i64 %t2390, i64* %cw_v2391
    %t2392 = load i64, i64* %cw_v2391
    %t2393 = call i64 @freak_llvm_word_to_int(i64 %t2392)
    %cv_v2394 = alloca i64
    store i64 %t2393, i64* %cv_v2394
    %t2395 = load i64, i64* %cv_v2394
    %t2396 = load i64, i64* %mx_v2378
    %t2398 = icmp sgt i64 %t2395, %t2396
    %t2397 = zext i1 %t2398 to i64
    %t2402 = icmp ne i64 %t2397, 0
    br i1 %t2402, label %if.then.2399, label %if.end.2401
if.then.2399:
    %t2403 = load i64, i64* %cv_v2394
    store i64 %t2403, i64* %mx_v2378
    br label %if.end.2401
if.end.2401:
    %t2404 = load i64, i64* %mi_v2379
    %t2405 = add i64 %t2404, 1
    store i64 %t2405, i64* %mi_v2379
    br label %loop.cond.2380
loop.end.2382:
    %t2406 = load i64, i64* %mx_v2378
    ret i64 %t2406
    ret i64 0
}

define i64 @freak_array_min_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2407 = load i64, i64* %handle
    %t2408 = call i64 @freak_llvm_array_len(i64 %t2407)
    %alen_v2409 = alloca i64
    store i64 %t2408, i64* %alen_v2409
    %t2410 = load i64, i64* %alen_v2409
    %t2412 = icmp eq i64 %t2410, 0
    %t2411 = zext i1 %t2412 to i64
    %t2416 = icmp ne i64 %t2411, 0
    br i1 %t2416, label %if.then.2413, label %if.end.2415
if.then.2413:
    ret i64 0
    br label %if.end.2415
if.end.2415:
    %t2417 = load i64, i64* %handle
    %t2418 = call i64 @freak_llvm_array_get(i64 %t2417, i64 0)
    %mw_v2419 = alloca i64
    store i64 %t2418, i64* %mw_v2419
    %t2420 = load i64, i64* %mw_v2419
    %t2421 = call i64 @freak_llvm_word_to_int(i64 %t2420)
    %mn_v2422 = alloca i64
    store i64 %t2421, i64* %mn_v2422
    %mi_v2423 = alloca i64
    store i64 1, i64* %mi_v2423
    br label %loop.cond.2424
loop.cond.2424:
    %t2427 = load i64, i64* %mi_v2423
    %t2428 = load i64, i64* %alen_v2409
    %t2430 = icmp sge i64 %t2427, %t2428
    %t2429 = zext i1 %t2430 to i64
    %t2431 = icmp eq i64 %t2429, 0
    br i1 %t2431, label %loop.body.2425, label %loop.end.2426
loop.body.2425:
    %t2432 = load i64, i64* %handle
    %t2433 = load i64, i64* %mi_v2423
    %t2434 = call i64 @freak_llvm_array_get(i64 %t2432, i64 %t2433)
    %cw_v2435 = alloca i64
    store i64 %t2434, i64* %cw_v2435
    %t2436 = load i64, i64* %cw_v2435
    %t2437 = call i64 @freak_llvm_word_to_int(i64 %t2436)
    %cv_v2438 = alloca i64
    store i64 %t2437, i64* %cv_v2438
    %t2439 = load i64, i64* %cv_v2438
    %t2440 = load i64, i64* %mn_v2422
    %t2442 = icmp slt i64 %t2439, %t2440
    %t2441 = zext i1 %t2442 to i64
    %t2446 = icmp ne i64 %t2441, 0
    br i1 %t2446, label %if.then.2443, label %if.end.2445
if.then.2443:
    %t2447 = load i64, i64* %cv_v2438
    store i64 %t2447, i64* %mn_v2422
    br label %if.end.2445
if.end.2445:
    %t2448 = load i64, i64* %mi_v2423
    %t2449 = add i64 %t2448, 1
    store i64 %t2449, i64* %mi_v2423
    br label %loop.cond.2424
loop.end.2426:
    %t2450 = load i64, i64* %mn_v2422
    ret i64 %t2450
    ret i64 0
}

define void @freak_json_init() {
entry:
    %t2451 = load i64, i64* @g_json_inited
    %t2453 = icmp eq i64 %t2451, 0
    %t2452 = zext i1 %t2453 to i64
    %t2457 = icmp ne i64 %t2452, 0
    br i1 %t2457, label %if.then.2454, label %if.end.2456
if.then.2454:
    %t2458 = call i64 @freak_llvm_array_new()
    store i64 %t2458, i64* @g_json_types
    %t2459 = call i64 @freak_llvm_array_new()
    store i64 %t2459, i64* @g_json_vals
    %t2460 = call i64 @freak_llvm_array_new()
    store i64 %t2460, i64* @g_json_children
    %t2461 = call i64 @freak_llvm_array_new()
    store i64 %t2461, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 1, i64* @g_json_inited
    br label %if.end.2456
if.end.2456:
    ret void
}

define i64 @freak_json_alloc(i64 %arg_jtype, i64 %arg_jval) {
entry:
    %jtype = alloca i64
    store i64 %arg_jtype, i64* %jtype
    %jval = alloca i64
    store i64 %arg_jval, i64* %jval
    %t2462 = load i64, i64* @g_json_count
    %idx_v2463 = alloca i64
    store i64 %t2462, i64* %idx_v2463
    %t2464 = load i64, i64* @g_json_types
    %t2465 = load i64, i64* %jtype
    call void @freak_llvm_array_push(i64 %t2464, i64 %t2465)
    %t2466 = load i64, i64* @g_json_vals
    %t2467 = load i64, i64* %jval
    call void @freak_llvm_array_push(i64 %t2466, i64 %t2467)
    %t2468 = load i64, i64* @g_json_children
    %t2469 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2468, i64 %t2469)
    %t2470 = load i64, i64* @g_json_keys
    %t2471 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2470, i64 %t2471)
    %t2472 = load i64, i64* @g_json_count
    %t2473 = add i64 %t2472, 1
    store i64 %t2473, i64* @g_json_count
    %t2474 = load i64, i64* %idx_v2463
    ret i64 %t2474
    ret i64 0
}

define i64 @freak_json_get_type(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2475 = load i64, i64* @g_json_types
    %t2476 = load i64, i64* %handle
    %t2477 = call i64 @freak_llvm_array_get(i64 %t2475, i64 %t2476)
    ret i64 %t2477
    ret i64 0
}

define i64 @freak_json_get_str(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2478 = load i64, i64* @g_json_vals
    %t2479 = load i64, i64* %handle
    %t2480 = call i64 @freak_llvm_array_get(i64 %t2478, i64 %t2479)
    ret i64 %t2480
    ret i64 0
}

define i64 @freak_json_get_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2481 = load i64, i64* @g_json_vals
    %t2482 = load i64, i64* %handle
    %t2483 = call i64 @freak_llvm_array_get(i64 %t2481, i64 %t2482)
    %v_v2484 = alloca i64
    store i64 %t2483, i64* %v_v2484
    %t2485 = load i64, i64* %v_v2484
    %t2486 = call i64 @freak_llvm_word_to_int(i64 %t2485)
    ret i64 %t2486
    ret i64 0
}

define i64 @freak_json_get_bool(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2487 = load i64, i64* @g_json_vals
    %t2488 = load i64, i64* %handle
    %t2489 = call i64 @freak_llvm_array_get(i64 %t2487, i64 %t2488)
    %v_v2490 = alloca i64
    store i64 %t2489, i64* %v_v2490
    %t2491 = load i64, i64* %v_v2490
    %t2492 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.120, i64 0, i64 0
    %t2493 = ptrtoint i8* %t2492 to i64
    %t2494 = call i64 @freak_llvm_word_eq(i64 %t2491, i64 %t2493)
    ret i64 %t2494
    ret i64 0
}

define i64 @freak_json_is_null(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2495 = load i64, i64* @g_json_types
    %t2496 = load i64, i64* %handle
    %t2497 = call i64 @freak_llvm_array_get(i64 %t2495, i64 %t2496)
    %t_v2498 = alloca i64
    store i64 %t2497, i64* %t_v2498
    %t2499 = load i64, i64* %t_v2498
    %t2500 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.121, i64 0, i64 0
    %t2501 = ptrtoint i8* %t2500 to i64
    %t2502 = call i64 @freak_llvm_word_eq(i64 %t2499, i64 %t2501)
    ret i64 %t2502
    ret i64 0
}

define i64 @freak_json_arr_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2503 = load i64, i64* @g_json_children
    %t2504 = load i64, i64* %handle
    %t2505 = call i64 @freak_llvm_array_get(i64 %t2503, i64 %t2504)
    %ch_v2506 = alloca i64
    store i64 %t2505, i64* %ch_v2506
    %t2507 = load i64, i64* %ch_v2506
    %t2508 = call i64 @freak_llvm_word_to_int(i64 %t2507)
    %ch_handle_v2509 = alloca i64
    store i64 %t2508, i64* %ch_handle_v2509
    %t2510 = load i64, i64* %ch_handle_v2509
    %t2511 = call i64 @freak_llvm_array_len(i64 %t2510)
    ret i64 %t2511
    ret i64 0
}

define i64 @freak_json_arr_get(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2512 = load i64, i64* @g_json_children
    %t2513 = load i64, i64* %handle
    %t2514 = call i64 @freak_llvm_array_get(i64 %t2512, i64 %t2513)
    %ch_v2515 = alloca i64
    store i64 %t2514, i64* %ch_v2515
    %t2516 = load i64, i64* %ch_v2515
    %t2517 = call i64 @freak_llvm_word_to_int(i64 %t2516)
    %ch_handle_v2518 = alloca i64
    store i64 %t2517, i64* %ch_handle_v2518
    %t2519 = load i64, i64* %ch_handle_v2518
    %t2520 = load i64, i64* %index
    %t2521 = call i64 @freak_llvm_array_get(i64 %t2519, i64 %t2520)
    %val_w_v2522 = alloca i64
    store i64 %t2521, i64* %val_w_v2522
    %t2523 = load i64, i64* %val_w_v2522
    %t2524 = call i64 @freak_llvm_word_to_int(i64 %t2523)
    ret i64 %t2524
    ret i64 0
}

define i64 @freak_json_obj_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2525 = load i64, i64* @g_json_keys
    %t2526 = load i64, i64* %handle
    %t2527 = call i64 @freak_llvm_array_get(i64 %t2525, i64 %t2526)
    %ks_v2528 = alloca i64
    store i64 %t2527, i64* %ks_v2528
    %t2529 = load i64, i64* %ks_v2528
    %t2530 = call i64 @freak_llvm_word_to_int(i64 %t2529)
    %ks_handle_v2531 = alloca i64
    store i64 %t2530, i64* %ks_handle_v2531
    %t2532 = load i64, i64* %ks_handle_v2531
    %t2533 = call i64 @freak_llvm_array_len(i64 %t2532)
    ret i64 %t2533
    ret i64 0
}

define i64 @freak_json_obj_get(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2534 = load i64, i64* @g_json_keys
    %t2535 = load i64, i64* %handle
    %t2536 = call i64 @freak_llvm_array_get(i64 %t2534, i64 %t2535)
    %ks_v2537 = alloca i64
    store i64 %t2536, i64* %ks_v2537
    %t2538 = load i64, i64* %ks_v2537
    %t2539 = call i64 @freak_llvm_word_to_int(i64 %t2538)
    %ks_handle_v2540 = alloca i64
    store i64 %t2539, i64* %ks_handle_v2540
    %t2541 = load i64, i64* @g_json_children
    %t2542 = load i64, i64* %handle
    %t2543 = call i64 @freak_llvm_array_get(i64 %t2541, i64 %t2542)
    %ch_v2544 = alloca i64
    store i64 %t2543, i64* %ch_v2544
    %t2545 = load i64, i64* %ch_v2544
    %t2546 = call i64 @freak_llvm_word_to_int(i64 %t2545)
    %ch_handle_v2547 = alloca i64
    store i64 %t2546, i64* %ch_handle_v2547
    %t2548 = load i64, i64* %ks_handle_v2540
    %t2549 = call i64 @freak_llvm_array_len(i64 %t2548)
    %klen_v2550 = alloca i64
    store i64 %t2549, i64* %klen_v2550
    %ki_v2551 = alloca i64
    store i64 0, i64* %ki_v2551
    %t2557 = load i64, i64* %klen_v2550
    %rep.2556 = alloca i64
    store i64 0, i64* %rep.2556
    br label %loop.cond.2552
loop.cond.2552:
    %t2558 = load i64, i64* %rep.2556
    %t2559 = icmp slt i64 %t2558, %t2557
    br i1 %t2559, label %loop.body.2553, label %loop.end.2554
loop.body.2553:
    %t2560 = load i64, i64* %ks_handle_v2540
    %t2561 = load i64, i64* %ki_v2551
    %t2562 = call i64 @freak_llvm_array_get(i64 %t2560, i64 %t2561)
    %k_v2563 = alloca i64
    store i64 %t2562, i64* %k_v2563
    %t2564 = load i64, i64* %k_v2563
    %t2565 = load i64, i64* %key
    %t2566 = call i64 @freak_llvm_word_eq(i64 %t2564, i64 %t2565)
    %t2570 = icmp ne i64 %t2566, 0
    br i1 %t2570, label %if.then.2567, label %if.end.2569
if.then.2567:
    %t2571 = load i64, i64* %ch_handle_v2547
    %t2572 = load i64, i64* %ki_v2551
    %t2573 = call i64 @freak_llvm_array_get(i64 %t2571, i64 %t2572)
    %v_v2574 = alloca i64
    store i64 %t2573, i64* %v_v2574
    %t2575 = load i64, i64* %v_v2574
    %t2576 = call i64 @freak_llvm_word_to_int(i64 %t2575)
    ret i64 %t2576
    br label %if.end.2569
if.end.2569:
    %t2577 = load i64, i64* %ki_v2551
    %t2578 = add i64 %t2577, 1
    store i64 %t2578, i64* %ki_v2551
    br label %loop.inc.2555
loop.inc.2555:
    %t2579 = load i64, i64* %rep.2556
    %t2580 = add i64 %t2579, 1
    store i64 %t2580, i64* %rep.2556
    br label %loop.cond.2552
loop.end.2554:
    %t2581 = sub i64 0, 1
    ret i64 %t2581
    ret i64 0
}

define i64 @freak_json_obj_has(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2582 = load i64, i64* %handle
    %t2583 = load i64, i64* %key
    %t2584 = call i64 @freak_json_obj_get(i64 %t2582, i64 %t2583)
    %t2586 = icmp sge i64 %t2584, 0
    %t2585 = zext i1 %t2586 to i64
    ret i64 %t2585
    ret i64 0
}

define i64 @freak_json_obj_key_at(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2587 = load i64, i64* @g_json_keys
    %t2588 = load i64, i64* %handle
    %t2589 = call i64 @freak_llvm_array_get(i64 %t2587, i64 %t2588)
    %ks_v2590 = alloca i64
    store i64 %t2589, i64* %ks_v2590
    %t2591 = load i64, i64* %ks_v2590
    %t2592 = call i64 @freak_llvm_word_to_int(i64 %t2591)
    %ks_handle_v2593 = alloca i64
    store i64 %t2592, i64* %ks_handle_v2593
    %t2594 = load i64, i64* %ks_handle_v2593
    %t2595 = load i64, i64* %index
    %t2596 = call i64 @freak_llvm_array_get(i64 %t2594, i64 %t2595)
    ret i64 %t2596
    ret i64 0
}

define i64 @freak_json_cur() {
entry:
    %t2597 = load i64, i64* @g_json_pos
    %t2598 = load i64, i64* @g_json_len
    %t2600 = icmp sge i64 %t2597, %t2598
    %t2599 = zext i1 %t2600 to i64
    %t2604 = icmp ne i64 %t2599, 0
    br i1 %t2604, label %if.then.2601, label %if.end.2603
if.then.2601:
    %t2605 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.122, i64 0, i64 0
    %t2606 = ptrtoint i8* %t2605 to i64
    ret i64 %t2606
    br label %if.end.2603
if.end.2603:
    %t2607 = load i64, i64* @g_json_src
    %t2609 = load i64, i64* @g_json_pos
    %t2608 = call i64 @freak_llvm_word_char_at(i64 %t2607, i64 %t2609)
    ret i64 %t2608
    ret i64 0
}

define i64 @freak_json_advance() {
entry:
    %t2610 = call i64 @freak_json_cur()
    %c_v2611 = alloca i64
    store i64 %t2610, i64* %c_v2611
    %t2612 = load i64, i64* @g_json_pos
    %t2613 = add i64 %t2612, 1
    store i64 %t2613, i64* @g_json_pos
    %t2614 = load i64, i64* %c_v2611
    ret i64 %t2614
    ret i64 0
}

define void @freak_json_skip_ws() {
entry:
    br label %loop.cond.2615
loop.cond.2615:
    %t2618 = load i64, i64* @g_json_pos
    %t2619 = load i64, i64* @g_json_len
    %t2621 = icmp sge i64 %t2618, %t2619
    %t2620 = zext i1 %t2621 to i64
    %t2622 = icmp eq i64 %t2620, 0
    br i1 %t2622, label %loop.body.2616, label %loop.end.2617
loop.body.2616:
    %t2623 = call i64 @freak_json_cur()
    %c_v2624 = alloca i64
    store i64 %t2623, i64* %c_v2624
    %t2625 = load i64, i64* %c_v2624
    %t2626 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.123, i64 0, i64 0
    %t2627 = ptrtoint i8* %t2626 to i64
    %t2628 = call i64 @freak_llvm_word_neq(i64 %t2625, i64 %t2627)
    %t2629 = load i64, i64* %c_v2624
    %t2630 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.124, i64 0, i64 0
    %t2631 = ptrtoint i8* %t2630 to i64
    %t2632 = call i64 @freak_llvm_word_neq(i64 %t2629, i64 %t2631)
    %t2634 = icmp ne i64 %t2628, 0
    %t2635 = icmp ne i64 %t2632, 0
    %t2636 = and i1 %t2634, %t2635
    %t2633 = zext i1 %t2636 to i64
    %t2637 = load i64, i64* %c_v2624
    %t2638 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.125, i64 0, i64 0
    %t2639 = ptrtoint i8* %t2638 to i64
    %t2640 = call i64 @freak_llvm_word_neq(i64 %t2637, i64 %t2639)
    %t2642 = icmp ne i64 %t2633, 0
    %t2643 = icmp ne i64 %t2640, 0
    %t2644 = and i1 %t2642, %t2643
    %t2641 = zext i1 %t2644 to i64
    %t2645 = load i64, i64* %c_v2624
    %t2646 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.126, i64 0, i64 0
    %t2647 = ptrtoint i8* %t2646 to i64
    %t2648 = call i64 @freak_llvm_word_neq(i64 %t2645, i64 %t2647)
    %t2650 = icmp ne i64 %t2641, 0
    %t2651 = icmp ne i64 %t2648, 0
    %t2652 = and i1 %t2650, %t2651
    %t2649 = zext i1 %t2652 to i64
    %t2656 = icmp ne i64 %t2649, 0
    br i1 %t2656, label %if.then.2653, label %if.end.2655
if.then.2653:
    ret void
    br label %if.end.2655
if.end.2655:
    %t2657 = load i64, i64* @g_json_pos
    %t2658 = add i64 %t2657, 1
    store i64 %t2658, i64* @g_json_pos
    br label %loop.cond.2615
loop.end.2617:
    ret void
}

define void @freak_json_expect(i64 %arg_ch) {
entry:
    %ch = alloca i64
    store i64 %arg_ch, i64* %ch
    %t2659 = call i64 @freak_json_advance()
    %c_v2660 = alloca i64
    store i64 %t2659, i64* %c_v2660
    %t2661 = load i64, i64* %c_v2660
    %t2662 = load i64, i64* %ch
    %t2663 = call i64 @freak_llvm_word_neq(i64 %t2661, i64 %t2662)
    %t2667 = icmp ne i64 %t2663, 0
    br i1 %t2667, label %if.then.2664, label %if.end.2666
if.then.2664:
    %t2668 = getelementptr inbounds [29 x i8], [29 x i8]* @.str.127, i64 0, i64 0
    %t2669 = ptrtoint i8* %t2668 to i64
    %t2670 = load i64, i64* %ch
    %t2671 = call i64 @freak_llvm_word_concat(i64 %t2669, i64 %t2670)
    %t2672 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.128, i64 0, i64 0
    %t2673 = ptrtoint i8* %t2672 to i64
    %t2674 = call i64 @freak_llvm_word_concat(i64 %t2671, i64 %t2673)
    %t2675 = load i64, i64* %c_v2660
    %t2676 = call i64 @freak_llvm_word_concat(i64 %t2674, i64 %t2675)
    %t2677 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.129, i64 0, i64 0
    %t2678 = ptrtoint i8* %t2677 to i64
    %t2679 = call i64 @freak_llvm_word_concat(i64 %t2676, i64 %t2678)
    call void @freak_llvm_say(i64 %t2679)
    br label %if.end.2666
if.end.2666:
    ret void
}

define i64 @freak_json_parse_string() {
entry:
    %t2680 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.130, i64 0, i64 0
    %t2681 = ptrtoint i8* %t2680 to i64
    call void @freak_json_expect(i64 %t2681)
    %t2682 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.131, i64 0, i64 0
    %t2683 = ptrtoint i8* %t2682 to i64
    %ps_out_v2684 = alloca i64
    store i64 %t2683, i64* %ps_out_v2684
    br label %loop.cond.2685
loop.cond.2685:
    %t2688 = load i64, i64* @g_json_pos
    %t2689 = load i64, i64* @g_json_len
    %t2691 = icmp sge i64 %t2688, %t2689
    %t2690 = zext i1 %t2691 to i64
    %t2692 = icmp eq i64 %t2690, 0
    br i1 %t2692, label %loop.body.2686, label %loop.end.2687
loop.body.2686:
    %t2693 = call i64 @freak_json_advance()
    %c_v2694 = alloca i64
    store i64 %t2693, i64* %c_v2694
    %t2695 = load i64, i64* %c_v2694
    %t2696 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.132, i64 0, i64 0
    %t2697 = ptrtoint i8* %t2696 to i64
    %t2698 = call i64 @freak_llvm_word_eq(i64 %t2695, i64 %t2697)
    %t2702 = icmp ne i64 %t2698, 0
    br i1 %t2702, label %if.then.2699, label %if.end.2701
if.then.2699:
    %t2703 = load i64, i64* %ps_out_v2684
    ret i64 %t2703
    br label %if.end.2701
if.end.2701:
    %t2704 = load i64, i64* %c_v2694
    %t2705 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.133, i64 0, i64 0
    %t2706 = ptrtoint i8* %t2705 to i64
    %t2707 = call i64 @freak_llvm_word_eq(i64 %t2704, i64 %t2706)
    %t2711 = icmp ne i64 %t2707, 0
    br i1 %t2711, label %if.then.2708, label %if.else.2709
if.then.2708:
    %t2712 = call i64 @freak_json_advance()
    %esc_v2713 = alloca i64
    store i64 %t2712, i64* %esc_v2713
    %t2714 = load i64, i64* %esc_v2713
    %t2715 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.134, i64 0, i64 0
    %t2716 = ptrtoint i8* %t2715 to i64
    %t2717 = call i64 @freak_llvm_word_eq(i64 %t2714, i64 %t2716)
    %t2721 = icmp ne i64 %t2717, 0
    br i1 %t2721, label %if.then.2718, label %if.else.2719
if.then.2718:
    %t2722 = load i64, i64* %ps_out_v2684
    %t2723 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.135, i64 0, i64 0
    %t2724 = ptrtoint i8* %t2723 to i64
    %t2725 = call i64 @freak_llvm_word_concat(i64 %t2722, i64 %t2724)
    store i64 %t2725, i64* %ps_out_v2684
    br label %if.end.2720
if.else.2719:
    %t2726 = load i64, i64* %esc_v2713
    %t2727 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.136, i64 0, i64 0
    %t2728 = ptrtoint i8* %t2727 to i64
    %t2729 = call i64 @freak_llvm_word_eq(i64 %t2726, i64 %t2728)
    %t2733 = icmp ne i64 %t2729, 0
    br i1 %t2733, label %if.then.2730, label %if.else.2731
if.then.2730:
    %t2734 = load i64, i64* %ps_out_v2684
    %t2735 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.137, i64 0, i64 0
    %t2736 = ptrtoint i8* %t2735 to i64
    %t2737 = call i64 @freak_llvm_word_concat(i64 %t2734, i64 %t2736)
    store i64 %t2737, i64* %ps_out_v2684
    br label %if.end.2732
if.else.2731:
    %t2738 = load i64, i64* %esc_v2713
    %t2739 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.138, i64 0, i64 0
    %t2740 = ptrtoint i8* %t2739 to i64
    %t2741 = call i64 @freak_llvm_word_eq(i64 %t2738, i64 %t2740)
    %t2745 = icmp ne i64 %t2741, 0
    br i1 %t2745, label %if.then.2742, label %if.else.2743
if.then.2742:
    %t2746 = load i64, i64* %ps_out_v2684
    %t2747 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.139, i64 0, i64 0
    %t2748 = ptrtoint i8* %t2747 to i64
    %t2749 = call i64 @freak_llvm_word_concat(i64 %t2746, i64 %t2748)
    store i64 %t2749, i64* %ps_out_v2684
    br label %if.end.2744
if.else.2743:
    %t2750 = load i64, i64* %esc_v2713
    %t2751 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.140, i64 0, i64 0
    %t2752 = ptrtoint i8* %t2751 to i64
    %t2753 = call i64 @freak_llvm_word_eq(i64 %t2750, i64 %t2752)
    %t2757 = icmp ne i64 %t2753, 0
    br i1 %t2757, label %if.then.2754, label %if.else.2755
if.then.2754:
    %t2758 = load i64, i64* %ps_out_v2684
    %t2759 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.141, i64 0, i64 0
    %t2760 = ptrtoint i8* %t2759 to i64
    %t2761 = call i64 @freak_llvm_word_concat(i64 %t2758, i64 %t2760)
    store i64 %t2761, i64* %ps_out_v2684
    br label %if.end.2756
if.else.2755:
    %t2762 = load i64, i64* %esc_v2713
    %t2763 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.142, i64 0, i64 0
    %t2764 = ptrtoint i8* %t2763 to i64
    %t2765 = call i64 @freak_llvm_word_eq(i64 %t2762, i64 %t2764)
    %t2769 = icmp ne i64 %t2765, 0
    br i1 %t2769, label %if.then.2766, label %if.else.2767
if.then.2766:
    %t2770 = load i64, i64* %ps_out_v2684
    %t2771 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.143, i64 0, i64 0
    %t2772 = ptrtoint i8* %t2771 to i64
    %t2773 = call i64 @freak_llvm_word_concat(i64 %t2770, i64 %t2772)
    store i64 %t2773, i64* %ps_out_v2684
    br label %if.end.2768
if.else.2767:
    %t2774 = load i64, i64* %esc_v2713
    %t2775 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.144, i64 0, i64 0
    %t2776 = ptrtoint i8* %t2775 to i64
    %t2777 = call i64 @freak_llvm_word_eq(i64 %t2774, i64 %t2776)
    %t2781 = icmp ne i64 %t2777, 0
    br i1 %t2781, label %if.then.2778, label %if.else.2779
if.then.2778:
    %t2782 = load i64, i64* %ps_out_v2684
    %t2783 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.145, i64 0, i64 0
    %t2784 = ptrtoint i8* %t2783 to i64
    %t2785 = call i64 @freak_llvm_word_concat(i64 %t2782, i64 %t2784)
    store i64 %t2785, i64* %ps_out_v2684
    br label %if.end.2780
if.else.2779:
    %t2786 = load i64, i64* %ps_out_v2684
    %t2787 = load i64, i64* %esc_v2713
    %t2788 = call i64 @freak_llvm_word_concat(i64 %t2786, i64 %t2787)
    store i64 %t2788, i64* %ps_out_v2684
    br label %if.end.2780
if.end.2780:
    br label %if.end.2768
if.end.2768:
    br label %if.end.2756
if.end.2756:
    br label %if.end.2744
if.end.2744:
    br label %if.end.2732
if.end.2732:
    br label %if.end.2720
if.end.2720:
    br label %if.end.2710
if.else.2709:
    %t2789 = load i64, i64* %ps_out_v2684
    %t2790 = load i64, i64* %c_v2694
    %t2791 = call i64 @freak_llvm_word_concat(i64 %t2789, i64 %t2790)
    store i64 %t2791, i64* %ps_out_v2684
    br label %if.end.2710
if.end.2710:
    br label %loop.cond.2685
loop.end.2687:
    %t2792 = load i64, i64* %ps_out_v2684
    ret i64 %t2792
    ret i64 0
}

define i64 @freak_json_parse_number() {
entry:
    %t2793 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.146, i64 0, i64 0
    %t2794 = ptrtoint i8* %t2793 to i64
    %pn_out_v2795 = alloca i64
    store i64 %t2794, i64* %pn_out_v2795
    %t2796 = call i64 @freak_json_cur()
    %c_v2797 = alloca i64
    store i64 %t2796, i64* %c_v2797
    %t2798 = load i64, i64* %c_v2797
    %t2799 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.147, i64 0, i64 0
    %t2800 = ptrtoint i8* %t2799 to i64
    %t2801 = call i64 @freak_llvm_word_eq(i64 %t2798, i64 %t2800)
    %t2805 = icmp ne i64 %t2801, 0
    br i1 %t2805, label %if.then.2802, label %if.end.2804
if.then.2802:
    %t2806 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.148, i64 0, i64 0
    %t2807 = ptrtoint i8* %t2806 to i64
    store i64 %t2807, i64* %pn_out_v2795
    %t2808 = load i64, i64* @g_json_pos
    %t2809 = add i64 %t2808, 1
    store i64 %t2809, i64* @g_json_pos
    br label %if.end.2804
if.end.2804:
    br label %loop.cond.2810
loop.cond.2810:
    %t2813 = load i64, i64* @g_json_pos
    %t2814 = load i64, i64* @g_json_len
    %t2816 = icmp sge i64 %t2813, %t2814
    %t2815 = zext i1 %t2816 to i64
    %t2817 = icmp eq i64 %t2815, 0
    br i1 %t2817, label %loop.body.2811, label %loop.end.2812
loop.body.2811:
    %t2818 = call i64 @freak_json_cur()
    store i64 %t2818, i64* %c_v2797
    %t2819 = load i64, i64* %c_v2797
    %t2820 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.149, i64 0, i64 0
    %t2821 = ptrtoint i8* %t2820 to i64
    %t2822 = call i64 @freak_llvm_word_eq(i64 %t2819, i64 %t2821)
    %t2823 = load i64, i64* %c_v2797
    %t2824 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.150, i64 0, i64 0
    %t2825 = ptrtoint i8* %t2824 to i64
    %t2826 = call i64 @freak_llvm_word_eq(i64 %t2823, i64 %t2825)
    %t2828 = icmp ne i64 %t2822, 0
    %t2829 = icmp ne i64 %t2826, 0
    %t2830 = or i1 %t2828, %t2829
    %t2827 = zext i1 %t2830 to i64
    %t2831 = load i64, i64* %c_v2797
    %t2832 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.151, i64 0, i64 0
    %t2833 = ptrtoint i8* %t2832 to i64
    %t2834 = call i64 @freak_llvm_word_eq(i64 %t2831, i64 %t2833)
    %t2836 = icmp ne i64 %t2827, 0
    %t2837 = icmp ne i64 %t2834, 0
    %t2838 = or i1 %t2836, %t2837
    %t2835 = zext i1 %t2838 to i64
    %t2839 = load i64, i64* %c_v2797
    %t2840 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.152, i64 0, i64 0
    %t2841 = ptrtoint i8* %t2840 to i64
    %t2842 = call i64 @freak_llvm_word_eq(i64 %t2839, i64 %t2841)
    %t2844 = icmp ne i64 %t2835, 0
    %t2845 = icmp ne i64 %t2842, 0
    %t2846 = or i1 %t2844, %t2845
    %t2843 = zext i1 %t2846 to i64
    %t2847 = load i64, i64* %c_v2797
    %t2848 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.153, i64 0, i64 0
    %t2849 = ptrtoint i8* %t2848 to i64
    %t2850 = call i64 @freak_llvm_word_eq(i64 %t2847, i64 %t2849)
    %t2852 = icmp ne i64 %t2843, 0
    %t2853 = icmp ne i64 %t2850, 0
    %t2854 = or i1 %t2852, %t2853
    %t2851 = zext i1 %t2854 to i64
    %t2855 = load i64, i64* %c_v2797
    %t2856 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.154, i64 0, i64 0
    %t2857 = ptrtoint i8* %t2856 to i64
    %t2858 = call i64 @freak_llvm_word_eq(i64 %t2855, i64 %t2857)
    %t2860 = icmp ne i64 %t2851, 0
    %t2861 = icmp ne i64 %t2858, 0
    %t2862 = or i1 %t2860, %t2861
    %t2859 = zext i1 %t2862 to i64
    %t2863 = load i64, i64* %c_v2797
    %t2864 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.155, i64 0, i64 0
    %t2865 = ptrtoint i8* %t2864 to i64
    %t2866 = call i64 @freak_llvm_word_eq(i64 %t2863, i64 %t2865)
    %t2868 = icmp ne i64 %t2859, 0
    %t2869 = icmp ne i64 %t2866, 0
    %t2870 = or i1 %t2868, %t2869
    %t2867 = zext i1 %t2870 to i64
    %t2871 = load i64, i64* %c_v2797
    %t2872 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.156, i64 0, i64 0
    %t2873 = ptrtoint i8* %t2872 to i64
    %t2874 = call i64 @freak_llvm_word_eq(i64 %t2871, i64 %t2873)
    %t2876 = icmp ne i64 %t2867, 0
    %t2877 = icmp ne i64 %t2874, 0
    %t2878 = or i1 %t2876, %t2877
    %t2875 = zext i1 %t2878 to i64
    %t2879 = load i64, i64* %c_v2797
    %t2880 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.157, i64 0, i64 0
    %t2881 = ptrtoint i8* %t2880 to i64
    %t2882 = call i64 @freak_llvm_word_eq(i64 %t2879, i64 %t2881)
    %t2884 = icmp ne i64 %t2875, 0
    %t2885 = icmp ne i64 %t2882, 0
    %t2886 = or i1 %t2884, %t2885
    %t2883 = zext i1 %t2886 to i64
    %t2887 = load i64, i64* %c_v2797
    %t2888 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.158, i64 0, i64 0
    %t2889 = ptrtoint i8* %t2888 to i64
    %t2890 = call i64 @freak_llvm_word_eq(i64 %t2887, i64 %t2889)
    %t2892 = icmp ne i64 %t2883, 0
    %t2893 = icmp ne i64 %t2890, 0
    %t2894 = or i1 %t2892, %t2893
    %t2891 = zext i1 %t2894 to i64
    %t2895 = load i64, i64* %c_v2797
    %t2896 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.159, i64 0, i64 0
    %t2897 = ptrtoint i8* %t2896 to i64
    %t2898 = call i64 @freak_llvm_word_eq(i64 %t2895, i64 %t2897)
    %t2900 = icmp ne i64 %t2891, 0
    %t2901 = icmp ne i64 %t2898, 0
    %t2902 = or i1 %t2900, %t2901
    %t2899 = zext i1 %t2902 to i64
    %t2906 = icmp ne i64 %t2899, 0
    br i1 %t2906, label %if.then.2903, label %if.else.2904
if.then.2903:
    %t2907 = load i64, i64* %pn_out_v2795
    %t2908 = load i64, i64* %c_v2797
    %t2909 = call i64 @freak_llvm_word_concat(i64 %t2907, i64 %t2908)
    store i64 %t2909, i64* %pn_out_v2795
    %t2910 = load i64, i64* @g_json_pos
    %t2911 = add i64 %t2910, 1
    store i64 %t2911, i64* @g_json_pos
    br label %if.end.2905
if.else.2904:
    %t2912 = load i64, i64* %pn_out_v2795
    ret i64 %t2912
    br label %if.end.2905
if.end.2905:
    br label %loop.cond.2810
loop.end.2812:
    %t2913 = load i64, i64* %pn_out_v2795
    ret i64 %t2913
    ret i64 0
}

define i64 @freak_json_try_keyword(i64 %arg_kw) {
entry:
    %kw = alloca i64
    store i64 %arg_kw, i64* %kw
    %t2914 = load i64, i64* %kw
    %t2915 = call i64 @freak_llvm_word_length(i64 %t2914)
    %kwlen_v2916 = alloca i64
    store i64 %t2915, i64* %kwlen_v2916
    %t2917 = load i64, i64* @g_json_pos
    %t2918 = load i64, i64* %kwlen_v2916
    %t2919 = add i64 %t2917, %t2918
    %t2920 = load i64, i64* @g_json_len
    %t2922 = icmp sgt i64 %t2919, %t2920
    %t2921 = zext i1 %t2922 to i64
    %t2926 = icmp ne i64 %t2921, 0
    br i1 %t2926, label %if.then.2923, label %if.end.2925
if.then.2923:
    ret i64 0
    br label %if.end.2925
if.end.2925:
    %ki_v2927 = alloca i64
    store i64 0, i64* %ki_v2927
    %t2933 = load i64, i64* %kwlen_v2916
    %rep.2932 = alloca i64
    store i64 0, i64* %rep.2932
    br label %loop.cond.2928
loop.cond.2928:
    %t2934 = load i64, i64* %rep.2932
    %t2935 = icmp slt i64 %t2934, %t2933
    br i1 %t2935, label %loop.body.2929, label %loop.end.2930
loop.body.2929:
    %t2936 = load i64, i64* @g_json_src
    %t2938 = load i64, i64* @g_json_pos
    %t2939 = load i64, i64* %ki_v2927
    %t2940 = add i64 %t2938, %t2939
    %t2937 = call i64 @freak_llvm_word_char_at(i64 %t2936, i64 %t2940)
    %t2941 = load i64, i64* %kw
    %t2943 = load i64, i64* %ki_v2927
    %t2942 = call i64 @freak_llvm_word_char_at(i64 %t2941, i64 %t2943)
    %t2944 = call i64 @freak_llvm_word_neq(i64 %t2937, i64 %t2942)
    %t2948 = icmp ne i64 %t2944, 0
    br i1 %t2948, label %if.then.2945, label %if.end.2947
if.then.2945:
    ret i64 0
    br label %if.end.2947
if.end.2947:
    %t2949 = load i64, i64* %ki_v2927
    %t2950 = add i64 %t2949, 1
    store i64 %t2950, i64* %ki_v2927
    br label %loop.inc.2931
loop.inc.2931:
    %t2951 = load i64, i64* %rep.2932
    %t2952 = add i64 %t2951, 1
    store i64 %t2952, i64* %rep.2932
    br label %loop.cond.2928
loop.end.2930:
    %t2953 = load i64, i64* %kwlen_v2916
    %t2954 = load i64, i64* @g_json_pos
    %t2955 = add i64 %t2954, %t2953
    store i64 %t2955, i64* @g_json_pos
    ret i64 1
    ret i64 0
}

define i64 @freak_json_parse_value() {
entry:
    call void @freak_json_skip_ws()
    %t2956 = call i64 @freak_json_cur()
    %c_v2957 = alloca i64
    store i64 %t2956, i64* %c_v2957
    %t2958 = load i64, i64* %c_v2957
    %t2959 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.160, i64 0, i64 0
    %t2960 = ptrtoint i8* %t2959 to i64
    %t2961 = call i64 @freak_llvm_word_eq(i64 %t2958, i64 %t2960)
    %t2965 = icmp ne i64 %t2961, 0
    br i1 %t2965, label %if.then.2962, label %if.end.2964
if.then.2962:
    %t2966 = call i64 @freak_json_parse_string()
    %sv_v2967 = alloca i64
    store i64 %t2966, i64* %sv_v2967
    %t2968 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.161, i64 0, i64 0
    %t2969 = ptrtoint i8* %t2968 to i64
    %t2970 = load i64, i64* %sv_v2967
    %t2971 = call i64 @freak_json_alloc(i64 %t2969, i64 %t2970)
    ret i64 %t2971
    br label %if.end.2964
if.end.2964:
    %t2972 = load i64, i64* %c_v2957
    %t2973 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.162, i64 0, i64 0
    %t2974 = ptrtoint i8* %t2973 to i64
    %t2975 = call i64 @freak_llvm_word_eq(i64 %t2972, i64 %t2974)
    %t2976 = load i64, i64* %c_v2957
    %t2977 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.163, i64 0, i64 0
    %t2978 = ptrtoint i8* %t2977 to i64
    %t2979 = call i64 @freak_llvm_word_eq(i64 %t2976, i64 %t2978)
    %t2981 = icmp ne i64 %t2975, 0
    %t2982 = icmp ne i64 %t2979, 0
    %t2983 = or i1 %t2981, %t2982
    %t2980 = zext i1 %t2983 to i64
    %t2984 = load i64, i64* %c_v2957
    %t2985 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.164, i64 0, i64 0
    %t2986 = ptrtoint i8* %t2985 to i64
    %t2987 = call i64 @freak_llvm_word_eq(i64 %t2984, i64 %t2986)
    %t2989 = icmp ne i64 %t2980, 0
    %t2990 = icmp ne i64 %t2987, 0
    %t2991 = or i1 %t2989, %t2990
    %t2988 = zext i1 %t2991 to i64
    %t2992 = load i64, i64* %c_v2957
    %t2993 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.165, i64 0, i64 0
    %t2994 = ptrtoint i8* %t2993 to i64
    %t2995 = call i64 @freak_llvm_word_eq(i64 %t2992, i64 %t2994)
    %t2997 = icmp ne i64 %t2988, 0
    %t2998 = icmp ne i64 %t2995, 0
    %t2999 = or i1 %t2997, %t2998
    %t2996 = zext i1 %t2999 to i64
    %t3000 = load i64, i64* %c_v2957
    %t3001 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.166, i64 0, i64 0
    %t3002 = ptrtoint i8* %t3001 to i64
    %t3003 = call i64 @freak_llvm_word_eq(i64 %t3000, i64 %t3002)
    %t3005 = icmp ne i64 %t2996, 0
    %t3006 = icmp ne i64 %t3003, 0
    %t3007 = or i1 %t3005, %t3006
    %t3004 = zext i1 %t3007 to i64
    %t3008 = load i64, i64* %c_v2957
    %t3009 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.167, i64 0, i64 0
    %t3010 = ptrtoint i8* %t3009 to i64
    %t3011 = call i64 @freak_llvm_word_eq(i64 %t3008, i64 %t3010)
    %t3013 = icmp ne i64 %t3004, 0
    %t3014 = icmp ne i64 %t3011, 0
    %t3015 = or i1 %t3013, %t3014
    %t3012 = zext i1 %t3015 to i64
    %t3016 = load i64, i64* %c_v2957
    %t3017 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.168, i64 0, i64 0
    %t3018 = ptrtoint i8* %t3017 to i64
    %t3019 = call i64 @freak_llvm_word_eq(i64 %t3016, i64 %t3018)
    %t3021 = icmp ne i64 %t3012, 0
    %t3022 = icmp ne i64 %t3019, 0
    %t3023 = or i1 %t3021, %t3022
    %t3020 = zext i1 %t3023 to i64
    %t3024 = load i64, i64* %c_v2957
    %t3025 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.169, i64 0, i64 0
    %t3026 = ptrtoint i8* %t3025 to i64
    %t3027 = call i64 @freak_llvm_word_eq(i64 %t3024, i64 %t3026)
    %t3029 = icmp ne i64 %t3020, 0
    %t3030 = icmp ne i64 %t3027, 0
    %t3031 = or i1 %t3029, %t3030
    %t3028 = zext i1 %t3031 to i64
    %t3032 = load i64, i64* %c_v2957
    %t3033 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.170, i64 0, i64 0
    %t3034 = ptrtoint i8* %t3033 to i64
    %t3035 = call i64 @freak_llvm_word_eq(i64 %t3032, i64 %t3034)
    %t3037 = icmp ne i64 %t3028, 0
    %t3038 = icmp ne i64 %t3035, 0
    %t3039 = or i1 %t3037, %t3038
    %t3036 = zext i1 %t3039 to i64
    %t3040 = load i64, i64* %c_v2957
    %t3041 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.171, i64 0, i64 0
    %t3042 = ptrtoint i8* %t3041 to i64
    %t3043 = call i64 @freak_llvm_word_eq(i64 %t3040, i64 %t3042)
    %t3045 = icmp ne i64 %t3036, 0
    %t3046 = icmp ne i64 %t3043, 0
    %t3047 = or i1 %t3045, %t3046
    %t3044 = zext i1 %t3047 to i64
    %t3048 = load i64, i64* %c_v2957
    %t3049 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.172, i64 0, i64 0
    %t3050 = ptrtoint i8* %t3049 to i64
    %t3051 = call i64 @freak_llvm_word_eq(i64 %t3048, i64 %t3050)
    %t3053 = icmp ne i64 %t3044, 0
    %t3054 = icmp ne i64 %t3051, 0
    %t3055 = or i1 %t3053, %t3054
    %t3052 = zext i1 %t3055 to i64
    %t3059 = icmp ne i64 %t3052, 0
    br i1 %t3059, label %if.then.3056, label %if.end.3058
if.then.3056:
    %t3060 = call i64 @freak_json_parse_number()
    %nv_v3061 = alloca i64
    store i64 %t3060, i64* %nv_v3061
    %t3062 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.173, i64 0, i64 0
    %t3063 = ptrtoint i8* %t3062 to i64
    %t3064 = load i64, i64* %nv_v3061
    %t3065 = call i64 @freak_json_alloc(i64 %t3063, i64 %t3064)
    ret i64 %t3065
    br label %if.end.3058
if.end.3058:
    %t3066 = load i64, i64* %c_v2957
    %t3067 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.174, i64 0, i64 0
    %t3068 = ptrtoint i8* %t3067 to i64
    %t3069 = call i64 @freak_llvm_word_eq(i64 %t3066, i64 %t3068)
    %t3073 = icmp ne i64 %t3069, 0
    br i1 %t3073, label %if.then.3070, label %if.end.3072
if.then.3070:
    %t3074 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.175, i64 0, i64 0
    %t3075 = ptrtoint i8* %t3074 to i64
    %t3076 = call i64 @freak_json_try_keyword(i64 %t3075)
    %t3080 = icmp ne i64 %t3076, 0
    br i1 %t3080, label %if.then.3077, label %if.end.3079
if.then.3077:
    %t3081 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.176, i64 0, i64 0
    %t3082 = ptrtoint i8* %t3081 to i64
    %t3083 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.177, i64 0, i64 0
    %t3084 = ptrtoint i8* %t3083 to i64
    %t3085 = call i64 @freak_json_alloc(i64 %t3082, i64 %t3084)
    ret i64 %t3085
    br label %if.end.3079
if.end.3079:
    br label %if.end.3072
if.end.3072:
    %t3086 = load i64, i64* %c_v2957
    %t3087 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.178, i64 0, i64 0
    %t3088 = ptrtoint i8* %t3087 to i64
    %t3089 = call i64 @freak_llvm_word_eq(i64 %t3086, i64 %t3088)
    %t3093 = icmp ne i64 %t3089, 0
    br i1 %t3093, label %if.then.3090, label %if.end.3092
if.then.3090:
    %t3094 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.179, i64 0, i64 0
    %t3095 = ptrtoint i8* %t3094 to i64
    %t3096 = call i64 @freak_json_try_keyword(i64 %t3095)
    %t3100 = icmp ne i64 %t3096, 0
    br i1 %t3100, label %if.then.3097, label %if.end.3099
if.then.3097:
    %t3101 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.180, i64 0, i64 0
    %t3102 = ptrtoint i8* %t3101 to i64
    %t3103 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.181, i64 0, i64 0
    %t3104 = ptrtoint i8* %t3103 to i64
    %t3105 = call i64 @freak_json_alloc(i64 %t3102, i64 %t3104)
    ret i64 %t3105
    br label %if.end.3099
if.end.3099:
    br label %if.end.3092
if.end.3092:
    %t3106 = load i64, i64* %c_v2957
    %t3107 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.182, i64 0, i64 0
    %t3108 = ptrtoint i8* %t3107 to i64
    %t3109 = call i64 @freak_llvm_word_eq(i64 %t3106, i64 %t3108)
    %t3113 = icmp ne i64 %t3109, 0
    br i1 %t3113, label %if.then.3110, label %if.end.3112
if.then.3110:
    %t3114 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.183, i64 0, i64 0
    %t3115 = ptrtoint i8* %t3114 to i64
    %t3116 = call i64 @freak_json_try_keyword(i64 %t3115)
    %t3120 = icmp ne i64 %t3116, 0
    br i1 %t3120, label %if.then.3117, label %if.end.3119
if.then.3117:
    %t3121 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.184, i64 0, i64 0
    %t3122 = ptrtoint i8* %t3121 to i64
    %t3123 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.185, i64 0, i64 0
    %t3124 = ptrtoint i8* %t3123 to i64
    %t3125 = call i64 @freak_json_alloc(i64 %t3122, i64 %t3124)
    ret i64 %t3125
    br label %if.end.3119
if.end.3119:
    br label %if.end.3112
if.end.3112:
    %t3126 = load i64, i64* %c_v2957
    %t3127 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.186, i64 0, i64 0
    %t3128 = ptrtoint i8* %t3127 to i64
    %t3129 = call i64 @freak_llvm_word_eq(i64 %t3126, i64 %t3128)
    %t3133 = icmp ne i64 %t3129, 0
    br i1 %t3133, label %if.then.3130, label %if.end.3132
if.then.3130:
    %t3134 = load i64, i64* @g_json_pos
    %t3135 = add i64 %t3134, 1
    store i64 %t3135, i64* @g_json_pos
    %t3136 = call i64 @freak_llvm_array_new()
    %arr_children_v3137 = alloca i64
    store i64 %t3136, i64* %arr_children_v3137
    %t3138 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.187, i64 0, i64 0
    %t3139 = ptrtoint i8* %t3138 to i64
    %t3140 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.188, i64 0, i64 0
    %t3141 = ptrtoint i8* %t3140 to i64
    %t3142 = call i64 @freak_json_alloc(i64 %t3139, i64 %t3141)
    %arr_handle_v3143 = alloca i64
    store i64 %t3142, i64* %arr_handle_v3143
    %t3144 = load i64, i64* @g_json_children
    %t3145 = load i64, i64* %arr_handle_v3143
    %t3146 = load i64, i64* %arr_children_v3137
    %t3147 = call i64 @freak_llvm_word_from_int(i64 %t3146)
    call void @freak_llvm_array_set(i64 %t3144, i64 %t3145, i64 %t3147)
    call void @freak_json_skip_ws()
    %t3148 = call i64 @freak_json_cur()
    %t3149 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.189, i64 0, i64 0
    %t3150 = ptrtoint i8* %t3149 to i64
    %t3151 = call i64 @freak_llvm_word_neq(i64 %t3148, i64 %t3150)
    %t3155 = icmp ne i64 %t3151, 0
    br i1 %t3155, label %if.then.3152, label %if.end.3154
if.then.3152:
    %t3156 = call i64 @freak_json_parse_value()
    %first_val_v3157 = alloca i64
    store i64 %t3156, i64* %first_val_v3157
    %t3158 = load i64, i64* %arr_children_v3137
    %t3159 = load i64, i64* %first_val_v3157
    %t3160 = call i64 @freak_llvm_word_from_int(i64 %t3159)
    call void @freak_llvm_array_push(i64 %t3158, i64 %t3160)
    call void @freak_json_skip_ws()
    br label %loop.cond.3161
loop.cond.3161:
    %t3164 = call i64 @freak_json_cur()
    %t3165 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.190, i64 0, i64 0
    %t3166 = ptrtoint i8* %t3165 to i64
    %t3167 = call i64 @freak_llvm_word_neq(i64 %t3164, i64 %t3166)
    %t3168 = icmp eq i64 %t3167, 0
    br i1 %t3168, label %loop.body.3162, label %loop.end.3163
loop.body.3162:
    %t3169 = load i64, i64* @g_json_pos
    %t3170 = add i64 %t3169, 1
    store i64 %t3170, i64* @g_json_pos
    %t3171 = call i64 @freak_json_parse_value()
    %next_val_v3172 = alloca i64
    store i64 %t3171, i64* %next_val_v3172
    %t3173 = load i64, i64* %arr_children_v3137
    %t3174 = load i64, i64* %next_val_v3172
    %t3175 = call i64 @freak_llvm_word_from_int(i64 %t3174)
    call void @freak_llvm_array_push(i64 %t3173, i64 %t3175)
    call void @freak_json_skip_ws()
    br label %loop.cond.3161
loop.end.3163:
    br label %if.end.3154
if.end.3154:
    %t3176 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.191, i64 0, i64 0
    %t3177 = ptrtoint i8* %t3176 to i64
    call void @freak_json_expect(i64 %t3177)
    %t3178 = load i64, i64* %arr_handle_v3143
    ret i64 %t3178
    br label %if.end.3132
if.end.3132:
    %t3179 = load i64, i64* %c_v2957
    %t3180 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.192, i64 0, i64 0
    %t3181 = ptrtoint i8* %t3180 to i64
    %t3182 = call i64 @freak_llvm_word_eq(i64 %t3179, i64 %t3181)
    %t3186 = icmp ne i64 %t3182, 0
    br i1 %t3186, label %if.then.3183, label %if.end.3185
if.then.3183:
    %t3187 = load i64, i64* @g_json_pos
    %t3188 = add i64 %t3187, 1
    store i64 %t3188, i64* @g_json_pos
    %t3189 = call i64 @freak_llvm_array_new()
    %obj_children_v3190 = alloca i64
    store i64 %t3189, i64* %obj_children_v3190
    %t3191 = call i64 @freak_llvm_array_new()
    %obj_keys_v3192 = alloca i64
    store i64 %t3191, i64* %obj_keys_v3192
    %t3193 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.193, i64 0, i64 0
    %t3194 = ptrtoint i8* %t3193 to i64
    %t3195 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.194, i64 0, i64 0
    %t3196 = ptrtoint i8* %t3195 to i64
    %t3197 = call i64 @freak_json_alloc(i64 %t3194, i64 %t3196)
    %obj_handle_v3198 = alloca i64
    store i64 %t3197, i64* %obj_handle_v3198
    %t3199 = load i64, i64* @g_json_children
    %t3200 = load i64, i64* %obj_handle_v3198
    %t3201 = load i64, i64* %obj_children_v3190
    %t3202 = call i64 @freak_llvm_word_from_int(i64 %t3201)
    call void @freak_llvm_array_set(i64 %t3199, i64 %t3200, i64 %t3202)
    %t3203 = load i64, i64* @g_json_keys
    %t3204 = load i64, i64* %obj_handle_v3198
    %t3205 = load i64, i64* %obj_keys_v3192
    %t3206 = call i64 @freak_llvm_word_from_int(i64 %t3205)
    call void @freak_llvm_array_set(i64 %t3203, i64 %t3204, i64 %t3206)
    call void @freak_json_skip_ws()
    %t3207 = call i64 @freak_json_cur()
    %t3208 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.195, i64 0, i64 0
    %t3209 = ptrtoint i8* %t3208 to i64
    %t3210 = call i64 @freak_llvm_word_neq(i64 %t3207, i64 %t3209)
    %t3214 = icmp ne i64 %t3210, 0
    br i1 %t3214, label %if.then.3211, label %if.end.3213
if.then.3211:
    %t3215 = call i64 @freak_json_parse_string()
    %k1_v3216 = alloca i64
    store i64 %t3215, i64* %k1_v3216
    call void @freak_json_skip_ws()
    %t3217 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.196, i64 0, i64 0
    %t3218 = ptrtoint i8* %t3217 to i64
    call void @freak_json_expect(i64 %t3218)
    %t3219 = call i64 @freak_json_parse_value()
    %v1_v3220 = alloca i64
    store i64 %t3219, i64* %v1_v3220
    %t3221 = load i64, i64* %obj_keys_v3192
    %t3222 = load i64, i64* %k1_v3216
    call void @freak_llvm_array_push(i64 %t3221, i64 %t3222)
    %t3223 = load i64, i64* %obj_children_v3190
    %t3224 = load i64, i64* %v1_v3220
    %t3225 = call i64 @freak_llvm_word_from_int(i64 %t3224)
    call void @freak_llvm_array_push(i64 %t3223, i64 %t3225)
    call void @freak_json_skip_ws()
    br label %loop.cond.3226
loop.cond.3226:
    %t3229 = call i64 @freak_json_cur()
    %t3230 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.197, i64 0, i64 0
    %t3231 = ptrtoint i8* %t3230 to i64
    %t3232 = call i64 @freak_llvm_word_neq(i64 %t3229, i64 %t3231)
    %t3233 = icmp eq i64 %t3232, 0
    br i1 %t3233, label %loop.body.3227, label %loop.end.3228
loop.body.3227:
    %t3234 = load i64, i64* @g_json_pos
    %t3235 = add i64 %t3234, 1
    store i64 %t3235, i64* @g_json_pos
    call void @freak_json_skip_ws()
    %t3236 = call i64 @freak_json_parse_string()
    %kn_v3237 = alloca i64
    store i64 %t3236, i64* %kn_v3237
    call void @freak_json_skip_ws()
    %t3238 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.198, i64 0, i64 0
    %t3239 = ptrtoint i8* %t3238 to i64
    call void @freak_json_expect(i64 %t3239)
    %t3240 = call i64 @freak_json_parse_value()
    %vn_v3241 = alloca i64
    store i64 %t3240, i64* %vn_v3241
    %t3242 = load i64, i64* %obj_keys_v3192
    %t3243 = load i64, i64* %kn_v3237
    call void @freak_llvm_array_push(i64 %t3242, i64 %t3243)
    %t3244 = load i64, i64* %obj_children_v3190
    %t3245 = load i64, i64* %vn_v3241
    %t3246 = call i64 @freak_llvm_word_from_int(i64 %t3245)
    call void @freak_llvm_array_push(i64 %t3244, i64 %t3246)
    call void @freak_json_skip_ws()
    br label %loop.cond.3226
loop.end.3228:
    br label %if.end.3213
if.end.3213:
    %t3247 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.199, i64 0, i64 0
    %t3248 = ptrtoint i8* %t3247 to i64
    call void @freak_json_expect(i64 %t3248)
    %t3249 = load i64, i64* %obj_handle_v3198
    ret i64 %t3249
    br label %if.end.3185
if.end.3185:
    %t3250 = getelementptr inbounds [31 x i8], [31 x i8]* @.str.200, i64 0, i64 0
    %t3251 = ptrtoint i8* %t3250 to i64
    %t3252 = load i64, i64* %c_v2957
    %t3253 = call i64 @freak_llvm_word_concat(i64 %t3251, i64 %t3252)
    %t3254 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.201, i64 0, i64 0
    %t3255 = ptrtoint i8* %t3254 to i64
    %t3256 = call i64 @freak_llvm_word_concat(i64 %t3253, i64 %t3255)
    call void @freak_llvm_say(i64 %t3256)
    %t3257 = sub i64 0, 1
    ret i64 %t3257
    ret i64 0
}

define i64 @freak_json_parse(i64 %arg_source) {
entry:
    %source = alloca i64
    store i64 %arg_source, i64* %source
    call void @freak_json_init()
    %t3258 = load i64, i64* %source
    store i64 %t3258, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    %t3259 = load i64, i64* %source
    %t3260 = call i64 @freak_llvm_word_length(i64 %t3259)
    store i64 %t3260, i64* @g_json_len
    %t3261 = call i64 @freak_json_parse_value()
    ret i64 %t3261
    ret i64 0
}

define i64 @freak_json_stringify(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t3262 = load i64, i64* %handle
    %t3264 = icmp slt i64 %t3262, 0
    %t3263 = zext i1 %t3264 to i64
    %t3268 = icmp ne i64 %t3263, 0
    br i1 %t3268, label %if.then.3265, label %if.end.3267
if.then.3265:
    %t3269 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.202, i64 0, i64 0
    %t3270 = ptrtoint i8* %t3269 to i64
    ret i64 %t3270
    br label %if.end.3267
if.end.3267:
    %t3271 = load i64, i64* @g_json_types
    %t3272 = load i64, i64* %handle
    %t3273 = call i64 @freak_llvm_array_get(i64 %t3271, i64 %t3272)
    %t_v3274 = alloca i64
    store i64 %t3273, i64* %t_v3274
    %t3275 = load i64, i64* %t_v3274
    %t3276 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.203, i64 0, i64 0
    %t3277 = ptrtoint i8* %t3276 to i64
    %t3278 = call i64 @freak_llvm_word_eq(i64 %t3275, i64 %t3277)
    %t3282 = icmp ne i64 %t3278, 0
    br i1 %t3282, label %if.then.3279, label %if.end.3281
if.then.3279:
    %t3283 = load i64, i64* @g_json_vals
    %t3284 = load i64, i64* %handle
    %t3285 = call i64 @freak_llvm_array_get(i64 %t3283, i64 %t3284)
    %sv_v3286 = alloca i64
    store i64 %t3285, i64* %sv_v3286
    %t3287 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.204, i64 0, i64 0
    %t3288 = ptrtoint i8* %t3287 to i64
    %t3289 = load i64, i64* %sv_v3286
    %t3290 = call i64 @freak_llvm_word_concat(i64 %t3288, i64 %t3289)
    %t3291 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.205, i64 0, i64 0
    %t3292 = ptrtoint i8* %t3291 to i64
    %t3293 = call i64 @freak_llvm_word_concat(i64 %t3290, i64 %t3292)
    ret i64 %t3293
    br label %if.end.3281
if.end.3281:
    %t3294 = load i64, i64* %t_v3274
    %t3295 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.206, i64 0, i64 0
    %t3296 = ptrtoint i8* %t3295 to i64
    %t3297 = call i64 @freak_llvm_word_eq(i64 %t3294, i64 %t3296)
    %t3301 = icmp ne i64 %t3297, 0
    br i1 %t3301, label %if.then.3298, label %if.end.3300
if.then.3298:
    %t3302 = load i64, i64* @g_json_vals
    %t3303 = load i64, i64* %handle
    %t3304 = call i64 @freak_llvm_array_get(i64 %t3302, i64 %t3303)
    ret i64 %t3304
    br label %if.end.3300
if.end.3300:
    %t3305 = load i64, i64* %t_v3274
    %t3306 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.207, i64 0, i64 0
    %t3307 = ptrtoint i8* %t3306 to i64
    %t3308 = call i64 @freak_llvm_word_eq(i64 %t3305, i64 %t3307)
    %t3312 = icmp ne i64 %t3308, 0
    br i1 %t3312, label %if.then.3309, label %if.end.3311
if.then.3309:
    %t3313 = load i64, i64* @g_json_vals
    %t3314 = load i64, i64* %handle
    %t3315 = call i64 @freak_llvm_array_get(i64 %t3313, i64 %t3314)
    ret i64 %t3315
    br label %if.end.3311
if.end.3311:
    %t3316 = load i64, i64* %t_v3274
    %t3317 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.208, i64 0, i64 0
    %t3318 = ptrtoint i8* %t3317 to i64
    %t3319 = call i64 @freak_llvm_word_eq(i64 %t3316, i64 %t3318)
    %t3323 = icmp ne i64 %t3319, 0
    br i1 %t3323, label %if.then.3320, label %if.end.3322
if.then.3320:
    %t3324 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.209, i64 0, i64 0
    %t3325 = ptrtoint i8* %t3324 to i64
    ret i64 %t3325
    br label %if.end.3322
if.end.3322:
    %t3326 = load i64, i64* %t_v3274
    %t3327 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.210, i64 0, i64 0
    %t3328 = ptrtoint i8* %t3327 to i64
    %t3329 = call i64 @freak_llvm_word_eq(i64 %t3326, i64 %t3328)
    %t3333 = icmp ne i64 %t3329, 0
    br i1 %t3333, label %if.then.3330, label %if.end.3332
if.then.3330:
    %t3334 = load i64, i64* %handle
    %t3335 = call i64 @freak_json_arr_len(i64 %t3334)
    %alen_v3336 = alloca i64
    store i64 %t3335, i64* %alen_v3336
    %t3337 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.211, i64 0, i64 0
    %t3338 = ptrtoint i8* %t3337 to i64
    %a_out_v3339 = alloca i64
    store i64 %t3338, i64* %a_out_v3339
    %ai_v3340 = alloca i64
    store i64 0, i64* %ai_v3340
    %t3346 = load i64, i64* %alen_v3336
    %rep.3345 = alloca i64
    store i64 0, i64* %rep.3345
    br label %loop.cond.3341
loop.cond.3341:
    %t3347 = load i64, i64* %rep.3345
    %t3348 = icmp slt i64 %t3347, %t3346
    br i1 %t3348, label %loop.body.3342, label %loop.end.3343
loop.body.3342:
    %t3349 = load i64, i64* %ai_v3340
    %t3351 = icmp sgt i64 %t3349, 0
    %t3350 = zext i1 %t3351 to i64
    %t3355 = icmp ne i64 %t3350, 0
    br i1 %t3355, label %if.then.3352, label %if.end.3354
if.then.3352:
    %t3356 = load i64, i64* %a_out_v3339
    %t3357 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.212, i64 0, i64 0
    %t3358 = ptrtoint i8* %t3357 to i64
    %t3359 = call i64 @freak_llvm_word_concat(i64 %t3356, i64 %t3358)
    store i64 %t3359, i64* %a_out_v3339
    br label %if.end.3354
if.end.3354:
    %t3360 = load i64, i64* %handle
    %t3361 = load i64, i64* %ai_v3340
    %t3362 = call i64 @freak_json_arr_get(i64 %t3360, i64 %t3361)
    %child_v3363 = alloca i64
    store i64 %t3362, i64* %child_v3363
    %t3364 = load i64, i64* %a_out_v3339
    %t3365 = load i64, i64* %child_v3363
    %t3366 = call i64 @freak_json_stringify(i64 %t3365)
    %t3367 = call i64 @freak_llvm_word_concat(i64 %t3364, i64 %t3366)
    store i64 %t3367, i64* %a_out_v3339
    %t3368 = load i64, i64* %ai_v3340
    %t3369 = add i64 %t3368, 1
    store i64 %t3369, i64* %ai_v3340
    br label %loop.inc.3344
loop.inc.3344:
    %t3370 = load i64, i64* %rep.3345
    %t3371 = add i64 %t3370, 1
    store i64 %t3371, i64* %rep.3345
    br label %loop.cond.3341
loop.end.3343:
    %t3372 = load i64, i64* %a_out_v3339
    %t3373 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.213, i64 0, i64 0
    %t3374 = ptrtoint i8* %t3373 to i64
    %t3375 = call i64 @freak_llvm_word_concat(i64 %t3372, i64 %t3374)
    ret i64 %t3375
    br label %if.end.3332
if.end.3332:
    %t3376 = load i64, i64* %t_v3274
    %t3377 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.214, i64 0, i64 0
    %t3378 = ptrtoint i8* %t3377 to i64
    %t3379 = call i64 @freak_llvm_word_eq(i64 %t3376, i64 %t3378)
    %t3383 = icmp ne i64 %t3379, 0
    br i1 %t3383, label %if.then.3380, label %if.end.3382
if.then.3380:
    %t3384 = load i64, i64* %handle
    %t3385 = call i64 @freak_json_obj_len(i64 %t3384)
    %olen_v3386 = alloca i64
    store i64 %t3385, i64* %olen_v3386
    %t3387 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.215, i64 0, i64 0
    %t3388 = ptrtoint i8* %t3387 to i64
    %o_out_v3389 = alloca i64
    store i64 %t3388, i64* %o_out_v3389
    %oi_v3390 = alloca i64
    store i64 0, i64* %oi_v3390
    %t3396 = load i64, i64* %olen_v3386
    %rep.3395 = alloca i64
    store i64 0, i64* %rep.3395
    br label %loop.cond.3391
loop.cond.3391:
    %t3397 = load i64, i64* %rep.3395
    %t3398 = icmp slt i64 %t3397, %t3396
    br i1 %t3398, label %loop.body.3392, label %loop.end.3393
loop.body.3392:
    %t3399 = load i64, i64* %oi_v3390
    %t3401 = icmp sgt i64 %t3399, 0
    %t3400 = zext i1 %t3401 to i64
    %t3405 = icmp ne i64 %t3400, 0
    br i1 %t3405, label %if.then.3402, label %if.end.3404
if.then.3402:
    %t3406 = load i64, i64* %o_out_v3389
    %t3407 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.216, i64 0, i64 0
    %t3408 = ptrtoint i8* %t3407 to i64
    %t3409 = call i64 @freak_llvm_word_concat(i64 %t3406, i64 %t3408)
    store i64 %t3409, i64* %o_out_v3389
    br label %if.end.3404
if.end.3404:
    %t3410 = load i64, i64* %handle
    %t3411 = load i64, i64* %oi_v3390
    %t3412 = call i64 @freak_json_obj_key_at(i64 %t3410, i64 %t3411)
    %okey_v3413 = alloca i64
    store i64 %t3412, i64* %okey_v3413
    %t3414 = load i64, i64* %handle
    %t3415 = load i64, i64* %oi_v3390
    %t3416 = call i64 @freak_json_arr_get(i64 %t3414, i64 %t3415)
    %ov_v3417 = alloca i64
    store i64 %t3416, i64* %ov_v3417
    %t3418 = load i64, i64* %o_out_v3389
    %t3419 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.217, i64 0, i64 0
    %t3420 = ptrtoint i8* %t3419 to i64
    %t3421 = call i64 @freak_llvm_word_concat(i64 %t3418, i64 %t3420)
    %t3422 = load i64, i64* %okey_v3413
    %t3423 = call i64 @freak_llvm_word_concat(i64 %t3421, i64 %t3422)
    %t3424 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.218, i64 0, i64 0
    %t3425 = ptrtoint i8* %t3424 to i64
    %t3426 = call i64 @freak_llvm_word_concat(i64 %t3423, i64 %t3425)
    %t3427 = load i64, i64* %ov_v3417
    %t3428 = call i64 @freak_json_stringify(i64 %t3427)
    %t3429 = call i64 @freak_llvm_word_concat(i64 %t3426, i64 %t3428)
    store i64 %t3429, i64* %o_out_v3389
    %t3430 = load i64, i64* %oi_v3390
    %t3431 = add i64 %t3430, 1
    store i64 %t3431, i64* %oi_v3390
    br label %loop.inc.3394
loop.inc.3394:
    %t3432 = load i64, i64* %rep.3395
    %t3433 = add i64 %t3432, 1
    store i64 %t3433, i64* %rep.3395
    br label %loop.cond.3391
loop.end.3393:
    %t3434 = load i64, i64* %o_out_v3389
    %t3435 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.219, i64 0, i64 0
    %t3436 = ptrtoint i8* %t3435 to i64
    %t3437 = call i64 @freak_llvm_word_concat(i64 %t3434, i64 %t3436)
    ret i64 %t3437
    br label %if.end.3382
if.end.3382:
    %t3438 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.220, i64 0, i64 0
    %t3439 = ptrtoint i8* %t3438 to i64
    ret i64 %t3439
    ret i64 0
}

define i64 @freak_ver_parse_num(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3440 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.221, i64 0, i64 0
    %t3441 = ptrtoint i8* %t3440 to i64
    %res_v3442 = alloca i64
    store i64 %t3441, i64* %res_v3442
    %t3443 = load i64, i64* %start
    %i_v3444 = alloca i64
    store i64 %t3443, i64* %i_v3444
    %t3445 = load i64, i64* %s
    %t3446 = call i64 @freak_llvm_word_length(i64 %t3445)
    %slen_v3447 = alloca i64
    store i64 %t3446, i64* %slen_v3447
    br label %loop.cond.3448
loop.cond.3448:
    %t3451 = load i64, i64* %i_v3444
    %t3452 = load i64, i64* %slen_v3447
    %t3454 = icmp sge i64 %t3451, %t3452
    %t3453 = zext i1 %t3454 to i64
    %t3455 = icmp eq i64 %t3453, 0
    br i1 %t3455, label %loop.body.3449, label %loop.end.3450
loop.body.3449:
    %t3456 = load i64, i64* %s
    %t3458 = load i64, i64* %i_v3444
    %t3457 = call i64 @freak_llvm_word_char_at(i64 %t3456, i64 %t3458)
    %c_v3459 = alloca i64
    store i64 %t3457, i64* %c_v3459
    %t3460 = load i64, i64* %c_v3459
    %t3461 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.222, i64 0, i64 0
    %t3462 = ptrtoint i8* %t3461 to i64
    %t3463 = call i64 @freak_llvm_word_eq(i64 %t3460, i64 %t3462)
    %t3464 = load i64, i64* %c_v3459
    %t3465 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.223, i64 0, i64 0
    %t3466 = ptrtoint i8* %t3465 to i64
    %t3467 = call i64 @freak_llvm_word_eq(i64 %t3464, i64 %t3466)
    %t3469 = icmp ne i64 %t3463, 0
    %t3470 = icmp ne i64 %t3467, 0
    %t3471 = or i1 %t3469, %t3470
    %t3468 = zext i1 %t3471 to i64
    %t3472 = load i64, i64* %c_v3459
    %t3473 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.224, i64 0, i64 0
    %t3474 = ptrtoint i8* %t3473 to i64
    %t3475 = call i64 @freak_llvm_word_eq(i64 %t3472, i64 %t3474)
    %t3477 = icmp ne i64 %t3468, 0
    %t3478 = icmp ne i64 %t3475, 0
    %t3479 = or i1 %t3477, %t3478
    %t3476 = zext i1 %t3479 to i64
    %t3483 = icmp ne i64 %t3476, 0
    br i1 %t3483, label %if.then.3480, label %if.end.3482
if.then.3480:
    %t3484 = load i64, i64* %i_v3444
    %t3485 = add i64 %t3484, 1
    %t3486 = call i64 @freak_llvm_word_from_int(i64 %t3485)
    %pos_str_v3487 = alloca i64
    store i64 %t3486, i64* %pos_str_v3487
    %t3488 = load i64, i64* %res_v3442
    %t3489 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.225, i64 0, i64 0
    %t3490 = ptrtoint i8* %t3489 to i64
    %t3491 = call i64 @freak_llvm_word_concat(i64 %t3488, i64 %t3490)
    %t3492 = load i64, i64* %pos_str_v3487
    %t3493 = call i64 @freak_llvm_word_concat(i64 %t3491, i64 %t3492)
    ret i64 %t3493
    br label %if.end.3482
if.end.3482:
    %t3494 = load i64, i64* %res_v3442
    %t3495 = load i64, i64* %c_v3459
    %t3496 = call i64 @freak_llvm_word_concat(i64 %t3494, i64 %t3495)
    store i64 %t3496, i64* %res_v3442
    %t3497 = load i64, i64* %i_v3444
    %t3498 = add i64 %t3497, 1
    store i64 %t3498, i64* %i_v3444
    br label %loop.cond.3448
loop.end.3450:
    %t3499 = load i64, i64* %i_v3444
    %t3500 = call i64 @freak_llvm_word_from_int(i64 %t3499)
    %pos_str2_v3501 = alloca i64
    store i64 %t3500, i64* %pos_str2_v3501
    %t3502 = load i64, i64* %res_v3442
    %t3503 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.226, i64 0, i64 0
    %t3504 = ptrtoint i8* %t3503 to i64
    %t3505 = call i64 @freak_llvm_word_concat(i64 %t3502, i64 %t3504)
    %t3506 = load i64, i64* %pos_str2_v3501
    %t3507 = call i64 @freak_llvm_word_concat(i64 %t3505, i64 %t3506)
    ret i64 %t3507
    ret i64 0
}

define i64 @freak_ver_parse_pre(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3508 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.227, i64 0, i64 0
    %t3509 = ptrtoint i8* %t3508 to i64
    %res_v3510 = alloca i64
    store i64 %t3509, i64* %res_v3510
    %t3511 = load i64, i64* %start
    %i_v3512 = alloca i64
    store i64 %t3511, i64* %i_v3512
    %t3513 = load i64, i64* %s
    %t3514 = call i64 @freak_llvm_word_length(i64 %t3513)
    %slen_v3515 = alloca i64
    store i64 %t3514, i64* %slen_v3515
    br label %loop.cond.3516
loop.cond.3516:
    %t3519 = load i64, i64* %i_v3512
    %t3520 = load i64, i64* %slen_v3515
    %t3522 = icmp sge i64 %t3519, %t3520
    %t3521 = zext i1 %t3522 to i64
    %t3523 = icmp eq i64 %t3521, 0
    br i1 %t3523, label %loop.body.3517, label %loop.end.3518
loop.body.3517:
    %t3524 = load i64, i64* %s
    %t3526 = load i64, i64* %i_v3512
    %t3525 = call i64 @freak_llvm_word_char_at(i64 %t3524, i64 %t3526)
    %c_v3527 = alloca i64
    store i64 %t3525, i64* %c_v3527
    %t3528 = load i64, i64* %c_v3527
    %t3529 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.228, i64 0, i64 0
    %t3530 = ptrtoint i8* %t3529 to i64
    %t3531 = call i64 @freak_llvm_word_eq(i64 %t3528, i64 %t3530)
    %t3535 = icmp ne i64 %t3531, 0
    br i1 %t3535, label %if.then.3532, label %if.end.3534
if.then.3532:
    %t3536 = load i64, i64* %res_v3510
    ret i64 %t3536
    br label %if.end.3534
if.end.3534:
    %t3537 = load i64, i64* %res_v3510
    %t3538 = load i64, i64* %c_v3527
    %t3539 = call i64 @freak_llvm_word_concat(i64 %t3537, i64 %t3538)
    store i64 %t3539, i64* %res_v3510
    %t3540 = load i64, i64* %i_v3512
    %t3541 = add i64 %t3540, 1
    store i64 %t3541, i64* %i_v3512
    br label %loop.cond.3516
loop.end.3518:
    %t3542 = load i64, i64* %res_v3510
    ret i64 %t3542
    ret i64 0
}

define i64 @freak_ver_parse_build(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3543 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.229, i64 0, i64 0
    %t3544 = ptrtoint i8* %t3543 to i64
    %res_v3545 = alloca i64
    store i64 %t3544, i64* %res_v3545
    %t3546 = load i64, i64* %start
    %i_v3547 = alloca i64
    store i64 %t3546, i64* %i_v3547
    %t3548 = load i64, i64* %s
    %t3549 = call i64 @freak_llvm_word_length(i64 %t3548)
    %slen_v3550 = alloca i64
    store i64 %t3549, i64* %slen_v3550
    br label %loop.cond.3551
loop.cond.3551:
    %t3554 = load i64, i64* %i_v3547
    %t3555 = load i64, i64* %slen_v3550
    %t3557 = icmp sge i64 %t3554, %t3555
    %t3556 = zext i1 %t3557 to i64
    %t3558 = icmp eq i64 %t3556, 0
    br i1 %t3558, label %loop.body.3552, label %loop.end.3553
loop.body.3552:
    %t3559 = load i64, i64* %res_v3545
    %t3560 = load i64, i64* %s
    %t3562 = load i64, i64* %i_v3547
    %t3561 = call i64 @freak_llvm_word_char_at(i64 %t3560, i64 %t3562)
    %t3563 = call i64 @freak_llvm_word_concat(i64 %t3559, i64 %t3561)
    store i64 %t3563, i64* %res_v3545
    %t3564 = load i64, i64* %i_v3547
    %t3565 = add i64 %t3564, 1
    store i64 %t3565, i64* %i_v3547
    br label %loop.cond.3551
loop.end.3553:
    %t3566 = load i64, i64* %res_v3545
    ret i64 %t3566
    ret i64 0
}

define i64 @freak_ver_get_val(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %t3567 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.230, i64 0, i64 0
    %t3568 = ptrtoint i8* %t3567 to i64
    %res_v3569 = alloca i64
    store i64 %t3568, i64* %res_v3569
    %i_v3570 = alloca i64
    store i64 0, i64* %i_v3570
    %t3571 = load i64, i64* %encoded
    %t3572 = call i64 @freak_llvm_word_length(i64 %t3571)
    %elen_v3573 = alloca i64
    store i64 %t3572, i64* %elen_v3573
    br label %loop.cond.3574
loop.cond.3574:
    %t3577 = load i64, i64* %i_v3570
    %t3578 = load i64, i64* %elen_v3573
    %t3580 = icmp sge i64 %t3577, %t3578
    %t3579 = zext i1 %t3580 to i64
    %t3581 = icmp eq i64 %t3579, 0
    br i1 %t3581, label %loop.body.3575, label %loop.end.3576
loop.body.3575:
    %t3582 = load i64, i64* %encoded
    %t3584 = load i64, i64* %i_v3570
    %t3583 = call i64 @freak_llvm_word_char_at(i64 %t3582, i64 %t3584)
    %c_v3585 = alloca i64
    store i64 %t3583, i64* %c_v3585
    %t3586 = load i64, i64* %c_v3585
    %t3587 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.231, i64 0, i64 0
    %t3588 = ptrtoint i8* %t3587 to i64
    %t3589 = call i64 @freak_llvm_word_eq(i64 %t3586, i64 %t3588)
    %t3593 = icmp ne i64 %t3589, 0
    br i1 %t3593, label %if.then.3590, label %if.end.3592
if.then.3590:
    %t3594 = load i64, i64* %res_v3569
    ret i64 %t3594
    br label %if.end.3592
if.end.3592:
    %t3595 = load i64, i64* %res_v3569
    %t3596 = load i64, i64* %c_v3585
    %t3597 = call i64 @freak_llvm_word_concat(i64 %t3595, i64 %t3596)
    store i64 %t3597, i64* %res_v3569
    %t3598 = load i64, i64* %i_v3570
    %t3599 = add i64 %t3598, 1
    store i64 %t3599, i64* %i_v3570
    br label %loop.cond.3574
loop.end.3576:
    %t3600 = load i64, i64* %res_v3569
    ret i64 %t3600
    ret i64 0
}

define i64 @freak_ver_get_pos(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %i_v3601 = alloca i64
    store i64 0, i64* %i_v3601
    %t3602 = load i64, i64* %encoded
    %t3603 = call i64 @freak_llvm_word_length(i64 %t3602)
    %elen_v3604 = alloca i64
    store i64 %t3603, i64* %elen_v3604
    br label %loop.cond.3605
loop.cond.3605:
    %t3608 = load i64, i64* %i_v3601
    %t3609 = load i64, i64* %elen_v3604
    %t3611 = icmp sge i64 %t3608, %t3609
    %t3610 = zext i1 %t3611 to i64
    %t3612 = icmp eq i64 %t3610, 0
    br i1 %t3612, label %loop.body.3606, label %loop.end.3607
loop.body.3606:
    %t3613 = load i64, i64* %encoded
    %t3615 = load i64, i64* %i_v3601
    %t3614 = call i64 @freak_llvm_word_char_at(i64 %t3613, i64 %t3615)
    %c_v3616 = alloca i64
    store i64 %t3614, i64* %c_v3616
    %t3617 = load i64, i64* %c_v3616
    %t3618 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.232, i64 0, i64 0
    %t3619 = ptrtoint i8* %t3618 to i64
    %t3620 = call i64 @freak_llvm_word_eq(i64 %t3617, i64 %t3619)
    %t3624 = icmp ne i64 %t3620, 0
    br i1 %t3624, label %if.then.3621, label %if.end.3623
if.then.3621:
    %t3625 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.233, i64 0, i64 0
    %t3626 = ptrtoint i8* %t3625 to i64
    %pos_str_v3627 = alloca i64
    store i64 %t3626, i64* %pos_str_v3627
    %t3628 = load i64, i64* %i_v3601
    %t3629 = add i64 %t3628, 1
    %j_v3630 = alloca i64
    store i64 %t3629, i64* %j_v3630
    br label %loop.cond.3631
loop.cond.3631:
    %t3634 = load i64, i64* %j_v3630
    %t3635 = load i64, i64* %elen_v3604
    %t3637 = icmp sge i64 %t3634, %t3635
    %t3636 = zext i1 %t3637 to i64
    %t3638 = icmp eq i64 %t3636, 0
    br i1 %t3638, label %loop.body.3632, label %loop.end.3633
loop.body.3632:
    %t3639 = load i64, i64* %pos_str_v3627
    %t3640 = load i64, i64* %encoded
    %t3642 = load i64, i64* %j_v3630
    %t3641 = call i64 @freak_llvm_word_char_at(i64 %t3640, i64 %t3642)
    %t3643 = call i64 @freak_llvm_word_concat(i64 %t3639, i64 %t3641)
    store i64 %t3643, i64* %pos_str_v3627
    %t3644 = load i64, i64* %j_v3630
    %t3645 = add i64 %t3644, 1
    store i64 %t3645, i64* %j_v3630
    br label %loop.cond.3631
loop.end.3633:
    %t3646 = load i64, i64* %pos_str_v3627
    %t3647 = call i64 @freak_llvm_word_to_int(i64 %t3646)
    ret i64 %t3647
    br label %if.end.3623
if.end.3623:
    %t3648 = load i64, i64* %i_v3601
    %t3649 = add i64 %t3648, 1
    store i64 %t3649, i64* %i_v3601
    br label %loop.cond.3605
loop.end.3607:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_parse(i64 %arg_version) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %t3650 = load i64, i64* %version
    %s_v3651 = alloca i64
    store i64 %t3650, i64* %s_v3651
    %t3652 = load i64, i64* %s_v3651
    %t3653 = call i64 @freak_llvm_word_length(i64 %t3652)
    %t3655 = icmp sgt i64 %t3653, 0
    %t3654 = zext i1 %t3655 to i64
    %t3659 = icmp ne i64 %t3654, 0
    br i1 %t3659, label %if.then.3656, label %if.end.3658
if.then.3656:
    %t3660 = load i64, i64* %s_v3651
    %t3661 = call i64 @freak_llvm_word_char_at(i64 %t3660, i64 0)
    %fc_v3662 = alloca i64
    store i64 %t3661, i64* %fc_v3662
    %t3663 = load i64, i64* %fc_v3662
    %t3664 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.234, i64 0, i64 0
    %t3665 = ptrtoint i8* %t3664 to i64
    %t3666 = call i64 @freak_llvm_word_eq(i64 %t3663, i64 %t3665)
    %t3667 = load i64, i64* %fc_v3662
    %t3668 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.235, i64 0, i64 0
    %t3669 = ptrtoint i8* %t3668 to i64
    %t3670 = call i64 @freak_llvm_word_eq(i64 %t3667, i64 %t3669)
    %t3672 = icmp ne i64 %t3666, 0
    %t3673 = icmp ne i64 %t3670, 0
    %t3674 = or i1 %t3672, %t3673
    %t3671 = zext i1 %t3674 to i64
    %t3678 = icmp ne i64 %t3671, 0
    br i1 %t3678, label %if.then.3675, label %if.end.3677
if.then.3675:
    %t3679 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.236, i64 0, i64 0
    %t3680 = ptrtoint i8* %t3679 to i64
    %ns_v3681 = alloca i64
    store i64 %t3680, i64* %ns_v3681
    %vi_v3682 = alloca i64
    store i64 1, i64* %vi_v3682
    br label %loop.cond.3683
loop.cond.3683:
    %t3686 = load i64, i64* %vi_v3682
    %t3687 = load i64, i64* %s_v3651
    %t3688 = call i64 @freak_llvm_word_length(i64 %t3687)
    %t3690 = icmp sge i64 %t3686, %t3688
    %t3689 = zext i1 %t3690 to i64
    %t3691 = icmp eq i64 %t3689, 0
    br i1 %t3691, label %loop.body.3684, label %loop.end.3685
loop.body.3684:
    %t3692 = load i64, i64* %ns_v3681
    %t3693 = load i64, i64* %s_v3651
    %t3695 = load i64, i64* %vi_v3682
    %t3694 = call i64 @freak_llvm_word_char_at(i64 %t3693, i64 %t3695)
    %t3696 = call i64 @freak_llvm_word_concat(i64 %t3692, i64 %t3694)
    store i64 %t3696, i64* %ns_v3681
    %t3697 = load i64, i64* %vi_v3682
    %t3698 = add i64 %t3697, 1
    store i64 %t3698, i64* %vi_v3682
    br label %loop.cond.3683
loop.end.3685:
    %t3699 = load i64, i64* %ns_v3681
    store i64 %t3699, i64* %s_v3651
    br label %if.end.3677
if.end.3677:
    br label %if.end.3658
if.end.3658:
    %t3700 = load i64, i64* %s_v3651
    %t3701 = call i64 @freak_ver_parse_num(i64 %t3700, i64 0)
    %r1_v3702 = alloca i64
    store i64 %t3701, i64* %r1_v3702
    %t3703 = load i64, i64* %r1_v3702
    %t3704 = call i64 @freak_ver_get_val(i64 %t3703)
    %major_v3705 = alloca i64
    store i64 %t3704, i64* %major_v3705
    %t3706 = load i64, i64* %r1_v3702
    %t3707 = call i64 @freak_ver_get_pos(i64 %t3706)
    %pos1_v3708 = alloca i64
    store i64 %t3707, i64* %pos1_v3708
    %t3709 = load i64, i64* %s_v3651
    %t3710 = load i64, i64* %pos1_v3708
    %t3711 = call i64 @freak_ver_parse_num(i64 %t3709, i64 %t3710)
    %r2_v3712 = alloca i64
    store i64 %t3711, i64* %r2_v3712
    %t3713 = load i64, i64* %r2_v3712
    %t3714 = call i64 @freak_ver_get_val(i64 %t3713)
    %minor_v3715 = alloca i64
    store i64 %t3714, i64* %minor_v3715
    %t3716 = load i64, i64* %r2_v3712
    %t3717 = call i64 @freak_ver_get_pos(i64 %t3716)
    %pos2_v3718 = alloca i64
    store i64 %t3717, i64* %pos2_v3718
    %t3719 = load i64, i64* %s_v3651
    %t3720 = load i64, i64* %pos2_v3718
    %t3721 = call i64 @freak_ver_parse_num(i64 %t3719, i64 %t3720)
    %r3_v3722 = alloca i64
    store i64 %t3721, i64* %r3_v3722
    %t3723 = load i64, i64* %r3_v3722
    %t3724 = call i64 @freak_ver_get_val(i64 %t3723)
    %patch_v3725 = alloca i64
    store i64 %t3724, i64* %patch_v3725
    %t3726 = load i64, i64* %r3_v3722
    %t3727 = call i64 @freak_ver_get_pos(i64 %t3726)
    %pos3_v3728 = alloca i64
    store i64 %t3727, i64* %pos3_v3728
    %t3729 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.237, i64 0, i64 0
    %t3730 = ptrtoint i8* %t3729 to i64
    %pre_v3731 = alloca i64
    store i64 %t3730, i64* %pre_v3731
    %t3732 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.238, i64 0, i64 0
    %t3733 = ptrtoint i8* %t3732 to i64
    %bld_v3734 = alloca i64
    store i64 %t3733, i64* %bld_v3734
    %t3735 = load i64, i64* %pos3_v3728
    %t3736 = load i64, i64* %s_v3651
    %t3737 = call i64 @freak_llvm_word_length(i64 %t3736)
    %t3739 = icmp sle i64 %t3735, %t3737
    %t3738 = zext i1 %t3739 to i64
    %t3743 = icmp ne i64 %t3738, 0
    br i1 %t3743, label %if.then.3740, label %if.end.3742
if.then.3740:
    %t3744 = load i64, i64* %pos3_v3728
    %t3746 = icmp sgt i64 %t3744, 0
    %t3745 = zext i1 %t3746 to i64
    %t3750 = icmp ne i64 %t3745, 0
    br i1 %t3750, label %if.then.3747, label %if.end.3749
if.then.3747:
    %t3751 = load i64, i64* %s_v3651
    %t3753 = load i64, i64* %pos3_v3728
    %t3754 = sub i64 %t3753, 1
    %t3752 = call i64 @freak_llvm_word_char_at(i64 %t3751, i64 %t3754)
    %delim_v3755 = alloca i64
    store i64 %t3752, i64* %delim_v3755
    %t3756 = load i64, i64* %delim_v3755
    %t3757 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.239, i64 0, i64 0
    %t3758 = ptrtoint i8* %t3757 to i64
    %t3759 = call i64 @freak_llvm_word_eq(i64 %t3756, i64 %t3758)
    %t3763 = icmp ne i64 %t3759, 0
    br i1 %t3763, label %if.then.3760, label %if.else.3761
if.then.3760:
    %t3764 = load i64, i64* %s_v3651
    %t3765 = load i64, i64* %pos3_v3728
    %t3766 = call i64 @freak_ver_parse_pre(i64 %t3764, i64 %t3765)
    store i64 %t3766, i64* %pre_v3731
    br label %if.end.3762
if.else.3761:
    %t3767 = load i64, i64* %delim_v3755
    %t3768 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.240, i64 0, i64 0
    %t3769 = ptrtoint i8* %t3768 to i64
    %t3770 = call i64 @freak_llvm_word_eq(i64 %t3767, i64 %t3769)
    %t3774 = icmp ne i64 %t3770, 0
    br i1 %t3774, label %if.then.3771, label %if.end.3773
if.then.3771:
    %t3775 = load i64, i64* %s_v3651
    %t3776 = load i64, i64* %pos3_v3728
    %t3777 = call i64 @freak_ver_parse_build(i64 %t3775, i64 %t3776)
    store i64 %t3777, i64* %bld_v3734
    br label %if.end.3773
if.end.3773:
    br label %if.end.3762
if.end.3762:
    br label %if.end.3749
if.end.3749:
    br label %if.end.3742
if.end.3742:
    %t3778 = load i64, i64* %pre_v3731
    %t3779 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.241, i64 0, i64 0
    %t3780 = ptrtoint i8* %t3779 to i64
    %t3781 = call i64 @freak_llvm_word_neq(i64 %t3778, i64 %t3780)
    %t3785 = icmp ne i64 %t3781, 0
    br i1 %t3785, label %if.then.3782, label %if.end.3784
if.then.3782:
    %pi_v3786 = alloca i64
    store i64 0, i64* %pi_v3786
    %t3787 = load i64, i64* %s_v3651
    %t3788 = call i64 @freak_llvm_word_length(i64 %t3787)
    %plen_v3789 = alloca i64
    store i64 %t3788, i64* %plen_v3789
    br label %loop.cond.3790
loop.cond.3790:
    %t3793 = load i64, i64* %pi_v3786
    %t3794 = load i64, i64* %plen_v3789
    %t3796 = icmp sge i64 %t3793, %t3794
    %t3795 = zext i1 %t3796 to i64
    %t3797 = icmp eq i64 %t3795, 0
    br i1 %t3797, label %loop.body.3791, label %loop.end.3792
loop.body.3791:
    %t3798 = load i64, i64* %s_v3651
    %t3800 = load i64, i64* %pi_v3786
    %t3799 = call i64 @freak_llvm_word_char_at(i64 %t3798, i64 %t3800)
    %t3801 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.242, i64 0, i64 0
    %t3802 = ptrtoint i8* %t3801 to i64
    %t3803 = call i64 @freak_llvm_word_eq(i64 %t3799, i64 %t3802)
    %t3807 = icmp ne i64 %t3803, 0
    br i1 %t3807, label %if.then.3804, label %if.end.3806
if.then.3804:
    %t3808 = load i64, i64* %s_v3651
    %t3809 = load i64, i64* %pi_v3786
    %t3810 = add i64 %t3809, 1
    %t3811 = call i64 @freak_ver_parse_build(i64 %t3808, i64 %t3810)
    store i64 %t3811, i64* %bld_v3734
    br label %if.end.3806
if.end.3806:
    %t3812 = load i64, i64* %pi_v3786
    %t3813 = add i64 %t3812, 1
    store i64 %t3813, i64* %pi_v3786
    br label %loop.cond.3790
loop.end.3792:
    br label %if.end.3784
if.end.3784:
    %t3814 = load i64, i64* %major_v3705
    %t3815 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.243, i64 0, i64 0
    %t3816 = ptrtoint i8* %t3815 to i64
    %t3817 = call i64 @freak_llvm_word_concat(i64 %t3814, i64 %t3816)
    %t3818 = load i64, i64* %minor_v3715
    %t3819 = call i64 @freak_llvm_word_concat(i64 %t3817, i64 %t3818)
    %t3820 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.244, i64 0, i64 0
    %t3821 = ptrtoint i8* %t3820 to i64
    %t3822 = call i64 @freak_llvm_word_concat(i64 %t3819, i64 %t3821)
    %t3823 = load i64, i64* %patch_v3725
    %t3824 = call i64 @freak_llvm_word_concat(i64 %t3822, i64 %t3823)
    %t3825 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.245, i64 0, i64 0
    %t3826 = ptrtoint i8* %t3825 to i64
    %t3827 = call i64 @freak_llvm_word_concat(i64 %t3824, i64 %t3826)
    %t3828 = load i64, i64* %pre_v3731
    %t3829 = call i64 @freak_llvm_word_concat(i64 %t3827, i64 %t3828)
    %t3830 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.246, i64 0, i64 0
    %t3831 = ptrtoint i8* %t3830 to i64
    %t3832 = call i64 @freak_llvm_word_concat(i64 %t3829, i64 %t3831)
    %t3833 = load i64, i64* %bld_v3734
    %t3834 = call i64 @freak_llvm_word_concat(i64 %t3832, i64 %t3833)
    ret i64 %t3834
    ret i64 0
}

define i64 @freak_ver_field(i64 %arg_parsed, i64 %arg_field_idx) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %field_idx = alloca i64
    store i64 %arg_field_idx, i64* %field_idx
    %t3835 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.247, i64 0, i64 0
    %t3836 = ptrtoint i8* %t3835 to i64
    %res_v3837 = alloca i64
    store i64 %t3836, i64* %res_v3837
    %current_field_v3838 = alloca i64
    store i64 0, i64* %current_field_v3838
    %i_v3839 = alloca i64
    store i64 0, i64* %i_v3839
    %t3840 = load i64, i64* %parsed
    %t3841 = call i64 @freak_llvm_word_length(i64 %t3840)
    %plen_v3842 = alloca i64
    store i64 %t3841, i64* %plen_v3842
    br label %loop.cond.3843
loop.cond.3843:
    %t3846 = load i64, i64* %i_v3839
    %t3847 = load i64, i64* %plen_v3842
    %t3849 = icmp sge i64 %t3846, %t3847
    %t3848 = zext i1 %t3849 to i64
    %t3850 = icmp eq i64 %t3848, 0
    br i1 %t3850, label %loop.body.3844, label %loop.end.3845
loop.body.3844:
    %t3851 = load i64, i64* %parsed
    %t3853 = load i64, i64* %i_v3839
    %t3852 = call i64 @freak_llvm_word_char_at(i64 %t3851, i64 %t3853)
    %c_v3854 = alloca i64
    store i64 %t3852, i64* %c_v3854
    %t3855 = load i64, i64* %c_v3854
    %t3856 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.248, i64 0, i64 0
    %t3857 = ptrtoint i8* %t3856 to i64
    %t3858 = call i64 @freak_llvm_word_eq(i64 %t3855, i64 %t3857)
    %t3862 = icmp ne i64 %t3858, 0
    br i1 %t3862, label %if.then.3859, label %if.else.3860
if.then.3859:
    %t3863 = load i64, i64* %current_field_v3838
    %t3864 = load i64, i64* %field_idx
    %t3866 = icmp eq i64 %t3863, %t3864
    %t3865 = zext i1 %t3866 to i64
    %t3870 = icmp ne i64 %t3865, 0
    br i1 %t3870, label %if.then.3867, label %if.end.3869
if.then.3867:
    %t3871 = load i64, i64* %res_v3837
    ret i64 %t3871
    br label %if.end.3869
if.end.3869:
    %t3872 = load i64, i64* %current_field_v3838
    %t3873 = add i64 %t3872, 1
    store i64 %t3873, i64* %current_field_v3838
    %t3874 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.249, i64 0, i64 0
    %t3875 = ptrtoint i8* %t3874 to i64
    store i64 %t3875, i64* %res_v3837
    br label %if.end.3861
if.else.3860:
    %t3876 = load i64, i64* %res_v3837
    %t3877 = load i64, i64* %c_v3854
    %t3878 = call i64 @freak_llvm_word_concat(i64 %t3876, i64 %t3877)
    store i64 %t3878, i64* %res_v3837
    br label %if.end.3861
if.end.3861:
    %t3879 = load i64, i64* %i_v3839
    %t3880 = add i64 %t3879, 1
    store i64 %t3880, i64* %i_v3839
    br label %loop.cond.3843
loop.end.3845:
    %t3881 = load i64, i64* %current_field_v3838
    %t3882 = load i64, i64* %field_idx
    %t3884 = icmp eq i64 %t3881, %t3882
    %t3883 = zext i1 %t3884 to i64
    %t3888 = icmp ne i64 %t3883, 0
    br i1 %t3888, label %if.then.3885, label %if.end.3887
if.then.3885:
    %t3889 = load i64, i64* %res_v3837
    ret i64 %t3889
    br label %if.end.3887
if.end.3887:
    %t3890 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.250, i64 0, i64 0
    %t3891 = ptrtoint i8* %t3890 to i64
    ret i64 %t3891
    ret i64 0
}

define i64 @freak_ver_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3892 = load i64, i64* %parsed
    %t3893 = call i64 @freak_ver_field(i64 %t3892, i64 0)
    %t3894 = call i64 @freak_llvm_word_to_int(i64 %t3893)
    ret i64 %t3894
    ret i64 0
}

define i64 @freak_ver_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3895 = load i64, i64* %parsed
    %t3896 = call i64 @freak_ver_field(i64 %t3895, i64 1)
    %t3897 = call i64 @freak_llvm_word_to_int(i64 %t3896)
    ret i64 %t3897
    ret i64 0
}

define i64 @freak_ver_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3898 = load i64, i64* %parsed
    %t3899 = call i64 @freak_ver_field(i64 %t3898, i64 2)
    %t3900 = call i64 @freak_llvm_word_to_int(i64 %t3899)
    ret i64 %t3900
    ret i64 0
}

define i64 @freak_ver_pre(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3901 = load i64, i64* %parsed
    %t3902 = call i64 @freak_ver_field(i64 %t3901, i64 3)
    ret i64 %t3902
    ret i64 0
}

define i64 @freak_ver_build(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3903 = load i64, i64* %parsed
    %t3904 = call i64 @freak_ver_field(i64 %t3903, i64 4)
    ret i64 %t3904
    ret i64 0
}

define i64 @freak_ver_to_string(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3905 = load i64, i64* %parsed
    %t3906 = call i64 @freak_ver_field(i64 %t3905, i64 0)
    %maj_v3907 = alloca i64
    store i64 %t3906, i64* %maj_v3907
    %t3908 = load i64, i64* %parsed
    %t3909 = call i64 @freak_ver_field(i64 %t3908, i64 1)
    %min_v3910 = alloca i64
    store i64 %t3909, i64* %min_v3910
    %t3911 = load i64, i64* %parsed
    %t3912 = call i64 @freak_ver_field(i64 %t3911, i64 2)
    %pat_v3913 = alloca i64
    store i64 %t3912, i64* %pat_v3913
    %t3914 = load i64, i64* %parsed
    %t3915 = call i64 @freak_ver_field(i64 %t3914, i64 3)
    %pre_v3916 = alloca i64
    store i64 %t3915, i64* %pre_v3916
    %t3917 = load i64, i64* %parsed
    %t3918 = call i64 @freak_ver_field(i64 %t3917, i64 4)
    %bld_v3919 = alloca i64
    store i64 %t3918, i64* %bld_v3919
    %t3920 = load i64, i64* %maj_v3907
    %t3921 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.251, i64 0, i64 0
    %t3922 = ptrtoint i8* %t3921 to i64
    %t3923 = call i64 @freak_llvm_word_concat(i64 %t3920, i64 %t3922)
    %t3924 = load i64, i64* %min_v3910
    %t3925 = call i64 @freak_llvm_word_concat(i64 %t3923, i64 %t3924)
    %t3926 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.252, i64 0, i64 0
    %t3927 = ptrtoint i8* %t3926 to i64
    %t3928 = call i64 @freak_llvm_word_concat(i64 %t3925, i64 %t3927)
    %t3929 = load i64, i64* %pat_v3913
    %t3930 = call i64 @freak_llvm_word_concat(i64 %t3928, i64 %t3929)
    %out_v3931 = alloca i64
    store i64 %t3930, i64* %out_v3931
    %t3932 = load i64, i64* %pre_v3916
    %t3933 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.253, i64 0, i64 0
    %t3934 = ptrtoint i8* %t3933 to i64
    %t3935 = call i64 @freak_llvm_word_neq(i64 %t3932, i64 %t3934)
    %t3939 = icmp ne i64 %t3935, 0
    br i1 %t3939, label %if.then.3936, label %if.end.3938
if.then.3936:
    %t3940 = load i64, i64* %out_v3931
    %t3941 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.254, i64 0, i64 0
    %t3942 = ptrtoint i8* %t3941 to i64
    %t3943 = call i64 @freak_llvm_word_concat(i64 %t3940, i64 %t3942)
    %t3944 = load i64, i64* %pre_v3916
    %t3945 = call i64 @freak_llvm_word_concat(i64 %t3943, i64 %t3944)
    store i64 %t3945, i64* %out_v3931
    br label %if.end.3938
if.end.3938:
    %t3946 = load i64, i64* %bld_v3919
    %t3947 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.255, i64 0, i64 0
    %t3948 = ptrtoint i8* %t3947 to i64
    %t3949 = call i64 @freak_llvm_word_neq(i64 %t3946, i64 %t3948)
    %t3953 = icmp ne i64 %t3949, 0
    br i1 %t3953, label %if.then.3950, label %if.end.3952
if.then.3950:
    %t3954 = load i64, i64* %out_v3931
    %t3955 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.256, i64 0, i64 0
    %t3956 = ptrtoint i8* %t3955 to i64
    %t3957 = call i64 @freak_llvm_word_concat(i64 %t3954, i64 %t3956)
    %t3958 = load i64, i64* %bld_v3919
    %t3959 = call i64 @freak_llvm_word_concat(i64 %t3957, i64 %t3958)
    store i64 %t3959, i64* %out_v3931
    br label %if.end.3952
if.end.3952:
    %t3960 = load i64, i64* %out_v3931
    ret i64 %t3960
    ret i64 0
}

define i64 @freak_ver_compare(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t3961 = load i64, i64* @g_a
    %t3962 = call i64 @freak_ver_major(i64 %t3961)
    %a_major_v3963 = alloca i64
    store i64 %t3962, i64* %a_major_v3963
    %t3964 = load i64, i64* @g_b
    %t3965 = call i64 @freak_ver_major(i64 %t3964)
    %b_major_v3966 = alloca i64
    store i64 %t3965, i64* %b_major_v3966
    %t3967 = load i64, i64* %a_major_v3963
    %t3968 = load i64, i64* %b_major_v3966
    %t3970 = icmp slt i64 %t3967, %t3968
    %t3969 = zext i1 %t3970 to i64
    %t3974 = icmp ne i64 %t3969, 0
    br i1 %t3974, label %if.then.3971, label %if.end.3973
if.then.3971:
    %t3975 = sub i64 0, 1
    ret i64 %t3975
    br label %if.end.3973
if.end.3973:
    %t3976 = load i64, i64* %a_major_v3963
    %t3977 = load i64, i64* %b_major_v3966
    %t3979 = icmp sgt i64 %t3976, %t3977
    %t3978 = zext i1 %t3979 to i64
    %t3983 = icmp ne i64 %t3978, 0
    br i1 %t3983, label %if.then.3980, label %if.end.3982
if.then.3980:
    ret i64 1
    br label %if.end.3982
if.end.3982:
    %t3984 = load i64, i64* @g_a
    %t3985 = call i64 @freak_ver_minor(i64 %t3984)
    %a_minor_v3986 = alloca i64
    store i64 %t3985, i64* %a_minor_v3986
    %t3987 = load i64, i64* @g_b
    %t3988 = call i64 @freak_ver_minor(i64 %t3987)
    %b_minor_v3989 = alloca i64
    store i64 %t3988, i64* %b_minor_v3989
    %t3990 = load i64, i64* %a_minor_v3986
    %t3991 = load i64, i64* %b_minor_v3989
    %t3993 = icmp slt i64 %t3990, %t3991
    %t3992 = zext i1 %t3993 to i64
    %t3997 = icmp ne i64 %t3992, 0
    br i1 %t3997, label %if.then.3994, label %if.end.3996
if.then.3994:
    %t3998 = sub i64 0, 1
    ret i64 %t3998
    br label %if.end.3996
if.end.3996:
    %t3999 = load i64, i64* %a_minor_v3986
    %t4000 = load i64, i64* %b_minor_v3989
    %t4002 = icmp sgt i64 %t3999, %t4000
    %t4001 = zext i1 %t4002 to i64
    %t4006 = icmp ne i64 %t4001, 0
    br i1 %t4006, label %if.then.4003, label %if.end.4005
if.then.4003:
    ret i64 1
    br label %if.end.4005
if.end.4005:
    %t4007 = load i64, i64* @g_a
    %t4008 = call i64 @freak_ver_patch(i64 %t4007)
    %a_patch_v4009 = alloca i64
    store i64 %t4008, i64* %a_patch_v4009
    %t4010 = load i64, i64* @g_b
    %t4011 = call i64 @freak_ver_patch(i64 %t4010)
    %b_patch_v4012 = alloca i64
    store i64 %t4011, i64* %b_patch_v4012
    %t4013 = load i64, i64* %a_patch_v4009
    %t4014 = load i64, i64* %b_patch_v4012
    %t4016 = icmp slt i64 %t4013, %t4014
    %t4015 = zext i1 %t4016 to i64
    %t4020 = icmp ne i64 %t4015, 0
    br i1 %t4020, label %if.then.4017, label %if.end.4019
if.then.4017:
    %t4021 = sub i64 0, 1
    ret i64 %t4021
    br label %if.end.4019
if.end.4019:
    %t4022 = load i64, i64* %a_patch_v4009
    %t4023 = load i64, i64* %b_patch_v4012
    %t4025 = icmp sgt i64 %t4022, %t4023
    %t4024 = zext i1 %t4025 to i64
    %t4029 = icmp ne i64 %t4024, 0
    br i1 %t4029, label %if.then.4026, label %if.end.4028
if.then.4026:
    ret i64 1
    br label %if.end.4028
if.end.4028:
    %t4030 = load i64, i64* @g_a
    %t4031 = call i64 @freak_ver_pre(i64 %t4030)
    %a_pre_v4032 = alloca i64
    store i64 %t4031, i64* %a_pre_v4032
    %t4033 = load i64, i64* @g_b
    %t4034 = call i64 @freak_ver_pre(i64 %t4033)
    %b_pre_v4035 = alloca i64
    store i64 %t4034, i64* %b_pre_v4035
    %t4036 = load i64, i64* %a_pre_v4032
    %t4037 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.257, i64 0, i64 0
    %t4038 = ptrtoint i8* %t4037 to i64
    %t4039 = call i64 @freak_llvm_word_eq(i64 %t4036, i64 %t4038)
    %t4040 = load i64, i64* %b_pre_v4035
    %t4041 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.258, i64 0, i64 0
    %t4042 = ptrtoint i8* %t4041 to i64
    %t4043 = call i64 @freak_llvm_word_neq(i64 %t4040, i64 %t4042)
    %t4045 = icmp ne i64 %t4039, 0
    %t4046 = icmp ne i64 %t4043, 0
    %t4047 = and i1 %t4045, %t4046
    %t4044 = zext i1 %t4047 to i64
    %t4051 = icmp ne i64 %t4044, 0
    br i1 %t4051, label %if.then.4048, label %if.end.4050
if.then.4048:
    ret i64 1
    br label %if.end.4050
if.end.4050:
    %t4052 = load i64, i64* %a_pre_v4032
    %t4053 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.259, i64 0, i64 0
    %t4054 = ptrtoint i8* %t4053 to i64
    %t4055 = call i64 @freak_llvm_word_neq(i64 %t4052, i64 %t4054)
    %t4056 = load i64, i64* %b_pre_v4035
    %t4057 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.260, i64 0, i64 0
    %t4058 = ptrtoint i8* %t4057 to i64
    %t4059 = call i64 @freak_llvm_word_eq(i64 %t4056, i64 %t4058)
    %t4061 = icmp ne i64 %t4055, 0
    %t4062 = icmp ne i64 %t4059, 0
    %t4063 = and i1 %t4061, %t4062
    %t4060 = zext i1 %t4063 to i64
    %t4067 = icmp ne i64 %t4060, 0
    br i1 %t4067, label %if.then.4064, label %if.end.4066
if.then.4064:
    %t4068 = sub i64 0, 1
    ret i64 %t4068
    br label %if.end.4066
if.end.4066:
    %t4069 = load i64, i64* %a_pre_v4032
    %t4070 = call i64 @freak_llvm_word_length(i64 %t4069)
    %cmp_len_v4071 = alloca i64
    store i64 %t4070, i64* %cmp_len_v4071
    %t4072 = load i64, i64* %b_pre_v4035
    %t4073 = call i64 @freak_llvm_word_length(i64 %t4072)
    %t4074 = load i64, i64* %cmp_len_v4071
    %t4076 = icmp slt i64 %t4073, %t4074
    %t4075 = zext i1 %t4076 to i64
    %t4080 = icmp ne i64 %t4075, 0
    br i1 %t4080, label %if.then.4077, label %if.end.4079
if.then.4077:
    %t4081 = load i64, i64* %b_pre_v4035
    %t4082 = call i64 @freak_llvm_word_length(i64 %t4081)
    store i64 %t4082, i64* %cmp_len_v4071
    br label %if.end.4079
if.end.4079:
    %ci_v4083 = alloca i64
    store i64 0, i64* %ci_v4083
    br label %loop.cond.4084
loop.cond.4084:
    %t4087 = load i64, i64* %ci_v4083
    %t4088 = load i64, i64* %cmp_len_v4071
    %t4090 = icmp sge i64 %t4087, %t4088
    %t4089 = zext i1 %t4090 to i64
    %t4091 = icmp eq i64 %t4089, 0
    br i1 %t4091, label %loop.body.4085, label %loop.end.4086
loop.body.4085:
    %t4092 = load i64, i64* %a_pre_v4032
    %t4094 = load i64, i64* %ci_v4083
    %t4093 = call i64 @freak_llvm_word_char_at(i64 %t4092, i64 %t4094)
    %ac_v4095 = alloca i64
    store i64 %t4093, i64* %ac_v4095
    %t4096 = load i64, i64* %b_pre_v4035
    %t4098 = load i64, i64* %ci_v4083
    %t4097 = call i64 @freak_llvm_word_char_at(i64 %t4096, i64 %t4098)
    %bc_v4099 = alloca i64
    store i64 %t4097, i64* %bc_v4099
    %t4100 = load i64, i64* %ac_v4095
    %t4101 = load i64, i64* %bc_v4099
    %t4102 = call i64 @freak_llvm_word_neq(i64 %t4100, i64 %t4101)
    %t4106 = icmp ne i64 %t4102, 0
    br i1 %t4106, label %if.then.4103, label %if.end.4105
if.then.4103:
    %t4107 = load i64, i64* %ac_v4095
    %t4108 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.261, i64 0, i64 0
    %t4109 = ptrtoint i8* %t4108 to i64
    %t4110 = call i64 @freak_llvm_word_eq(i64 %t4107, i64 %t4109)
    %t4111 = load i64, i64* %bc_v4099
    %t4112 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.262, i64 0, i64 0
    %t4113 = ptrtoint i8* %t4112 to i64
    %t4114 = call i64 @freak_llvm_word_eq(i64 %t4111, i64 %t4113)
    %t4116 = icmp ne i64 %t4110, 0
    %t4117 = icmp ne i64 %t4114, 0
    %t4118 = and i1 %t4116, %t4117
    %t4115 = zext i1 %t4118 to i64
    %t4122 = icmp ne i64 %t4115, 0
    br i1 %t4122, label %if.then.4119, label %if.end.4121
if.then.4119:
    %t4123 = sub i64 0, 1
    ret i64 %t4123
    br label %if.end.4121
if.end.4121:
    %t4124 = load i64, i64* %ac_v4095
    %t4125 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.263, i64 0, i64 0
    %t4126 = ptrtoint i8* %t4125 to i64
    %t4127 = call i64 @freak_llvm_word_eq(i64 %t4124, i64 %t4126)
    %t4128 = load i64, i64* %bc_v4099
    %t4129 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.264, i64 0, i64 0
    %t4130 = ptrtoint i8* %t4129 to i64
    %t4131 = call i64 @freak_llvm_word_eq(i64 %t4128, i64 %t4130)
    %t4133 = icmp ne i64 %t4127, 0
    %t4134 = icmp ne i64 %t4131, 0
    %t4135 = and i1 %t4133, %t4134
    %t4132 = zext i1 %t4135 to i64
    %t4139 = icmp ne i64 %t4132, 0
    br i1 %t4139, label %if.then.4136, label %if.end.4138
if.then.4136:
    ret i64 1
    br label %if.end.4138
if.end.4138:
    %t4140 = load i64, i64* %ac_v4095
    %t4141 = call i64 @freak_llvm_word_to_int(i64 %t4140)
    %ai_v4142 = alloca i64
    store i64 %t4141, i64* %ai_v4142
    %t4143 = load i64, i64* %bc_v4099
    %t4144 = call i64 @freak_llvm_word_to_int(i64 %t4143)
    %bi_v4145 = alloca i64
    store i64 %t4144, i64* %bi_v4145
    %t4146 = load i64, i64* %ai_v4142
    %t4147 = load i64, i64* %bi_v4145
    %t4149 = icmp slt i64 %t4146, %t4147
    %t4148 = zext i1 %t4149 to i64
    %t4153 = icmp ne i64 %t4148, 0
    br i1 %t4153, label %if.then.4150, label %if.end.4152
if.then.4150:
    %t4154 = sub i64 0, 1
    ret i64 %t4154
    br label %if.end.4152
if.end.4152:
    %t4155 = load i64, i64* %ai_v4142
    %t4156 = load i64, i64* %bi_v4145
    %t4158 = icmp sgt i64 %t4155, %t4156
    %t4157 = zext i1 %t4158 to i64
    %t4162 = icmp ne i64 %t4157, 0
    br i1 %t4162, label %if.then.4159, label %if.end.4161
if.then.4159:
    ret i64 1
    br label %if.end.4161
if.end.4161:
    br label %if.end.4105
if.end.4105:
    %t4163 = load i64, i64* %ci_v4083
    %t4164 = add i64 %t4163, 1
    store i64 %t4164, i64* %ci_v4083
    br label %loop.cond.4084
loop.end.4086:
    %t4165 = load i64, i64* %a_pre_v4032
    %t4166 = call i64 @freak_llvm_word_length(i64 %t4165)
    %t4167 = load i64, i64* %b_pre_v4035
    %t4168 = call i64 @freak_llvm_word_length(i64 %t4167)
    %t4170 = icmp slt i64 %t4166, %t4168
    %t4169 = zext i1 %t4170 to i64
    %t4174 = icmp ne i64 %t4169, 0
    br i1 %t4174, label %if.then.4171, label %if.end.4173
if.then.4171:
    %t4175 = sub i64 0, 1
    ret i64 %t4175
    br label %if.end.4173
if.end.4173:
    %t4176 = load i64, i64* %a_pre_v4032
    %t4177 = call i64 @freak_llvm_word_length(i64 %t4176)
    %t4178 = load i64, i64* %b_pre_v4035
    %t4179 = call i64 @freak_llvm_word_length(i64 %t4178)
    %t4181 = icmp sgt i64 %t4177, %t4179
    %t4180 = zext i1 %t4181 to i64
    %t4185 = icmp ne i64 %t4180, 0
    br i1 %t4185, label %if.then.4182, label %if.end.4184
if.then.4182:
    ret i64 1
    br label %if.end.4184
if.end.4184:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_eq(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4186 = load i64, i64* @g_a
    %t4187 = load i64, i64* @g_b
    %t4188 = call i64 @freak_ver_compare(i64 %t4186, i64 %t4187)
    %t4190 = icmp eq i64 %t4188, 0
    %t4189 = zext i1 %t4190 to i64
    ret i64 %t4189
    ret i64 0
}

define i64 @freak_ver_lt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4191 = load i64, i64* @g_a
    %t4192 = load i64, i64* @g_b
    %t4193 = call i64 @freak_ver_compare(i64 %t4191, i64 %t4192)
    %t4195 = icmp slt i64 %t4193, 0
    %t4194 = zext i1 %t4195 to i64
    ret i64 %t4194
    ret i64 0
}

define i64 @freak_ver_gt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4196 = load i64, i64* @g_a
    %t4197 = load i64, i64* @g_b
    %t4198 = call i64 @freak_ver_compare(i64 %t4196, i64 %t4197)
    %t4200 = icmp sgt i64 %t4198, 0
    %t4199 = zext i1 %t4200 to i64
    ret i64 %t4199
    ret i64 0
}

define i64 @freak_ver_lte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4201 = load i64, i64* @g_a
    %t4202 = load i64, i64* @g_b
    %t4203 = call i64 @freak_ver_compare(i64 %t4201, i64 %t4202)
    %t4205 = icmp sle i64 %t4203, 0
    %t4204 = zext i1 %t4205 to i64
    ret i64 %t4204
    ret i64 0
}

define i64 @freak_ver_gte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4206 = load i64, i64* @g_a
    %t4207 = load i64, i64* @g_b
    %t4208 = call i64 @freak_ver_compare(i64 %t4206, i64 %t4207)
    %t4210 = icmp sge i64 %t4208, 0
    %t4209 = zext i1 %t4210 to i64
    ret i64 %t4209
    ret i64 0
}

define i64 @freak_ver_bump_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4211 = load i64, i64* %parsed
    %t4212 = call i64 @freak_ver_major(i64 %t4211)
    %t4213 = add i64 %t4212, 1
    %maj_v4214 = alloca i64
    store i64 %t4213, i64* %maj_v4214
    %t4215 = load i64, i64* %maj_v4214
    %t4216 = call i64 @freak_llvm_word_from_int(i64 %t4215)
    %t4217 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.265, i64 0, i64 0
    %t4218 = ptrtoint i8* %t4217 to i64
    %t4219 = call i64 @freak_llvm_word_concat(i64 %t4216, i64 %t4218)
    ret i64 %t4219
    ret i64 0
}

define i64 @freak_ver_bump_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4220 = load i64, i64* %parsed
    %t4221 = call i64 @freak_ver_major(i64 %t4220)
    %maj_v4222 = alloca i64
    store i64 %t4221, i64* %maj_v4222
    %t4223 = load i64, i64* %parsed
    %t4224 = call i64 @freak_ver_minor(i64 %t4223)
    %t4225 = add i64 %t4224, 1
    %min_v4226 = alloca i64
    store i64 %t4225, i64* %min_v4226
    %t4227 = load i64, i64* %maj_v4222
    %t4228 = call i64 @freak_llvm_word_from_int(i64 %t4227)
    %t4229 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.266, i64 0, i64 0
    %t4230 = ptrtoint i8* %t4229 to i64
    %t4231 = call i64 @freak_llvm_word_concat(i64 %t4228, i64 %t4230)
    %t4232 = load i64, i64* %min_v4226
    %t4233 = call i64 @freak_llvm_word_from_int(i64 %t4232)
    %t4234 = call i64 @freak_llvm_word_concat(i64 %t4231, i64 %t4233)
    %t4235 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.267, i64 0, i64 0
    %t4236 = ptrtoint i8* %t4235 to i64
    %t4237 = call i64 @freak_llvm_word_concat(i64 %t4234, i64 %t4236)
    ret i64 %t4237
    ret i64 0
}

define i64 @freak_ver_bump_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4238 = load i64, i64* %parsed
    %t4239 = call i64 @freak_ver_major(i64 %t4238)
    %maj_v4240 = alloca i64
    store i64 %t4239, i64* %maj_v4240
    %t4241 = load i64, i64* %parsed
    %t4242 = call i64 @freak_ver_minor(i64 %t4241)
    %min_v4243 = alloca i64
    store i64 %t4242, i64* %min_v4243
    %t4244 = load i64, i64* %parsed
    %t4245 = call i64 @freak_ver_patch(i64 %t4244)
    %t4246 = add i64 %t4245, 1
    %pat_v4247 = alloca i64
    store i64 %t4246, i64* %pat_v4247
    %t4248 = load i64, i64* %maj_v4240
    %t4249 = call i64 @freak_llvm_word_from_int(i64 %t4248)
    %t4250 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.268, i64 0, i64 0
    %t4251 = ptrtoint i8* %t4250 to i64
    %t4252 = call i64 @freak_llvm_word_concat(i64 %t4249, i64 %t4251)
    %t4253 = load i64, i64* %min_v4243
    %t4254 = call i64 @freak_llvm_word_from_int(i64 %t4253)
    %t4255 = call i64 @freak_llvm_word_concat(i64 %t4252, i64 %t4254)
    %t4256 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.269, i64 0, i64 0
    %t4257 = ptrtoint i8* %t4256 to i64
    %t4258 = call i64 @freak_llvm_word_concat(i64 %t4255, i64 %t4257)
    %t4259 = load i64, i64* %pat_v4247
    %t4260 = call i64 @freak_llvm_word_from_int(i64 %t4259)
    %t4261 = call i64 @freak_llvm_word_concat(i64 %t4258, i64 %t4260)
    %t4262 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.270, i64 0, i64 0
    %t4263 = ptrtoint i8* %t4262 to i64
    %t4264 = call i64 @freak_llvm_word_concat(i64 %t4261, i64 %t4263)
    ret i64 %t4264
    ret i64 0
}

define i64 @freak_ver_strip_prefix(i64 %arg_constraint, i64 %arg_prefix_len) {
entry:
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %prefix_len = alloca i64
    store i64 %arg_prefix_len, i64* %prefix_len
    %t4265 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.271, i64 0, i64 0
    %t4266 = ptrtoint i8* %t4265 to i64
    %stripped_v4267 = alloca i64
    store i64 %t4266, i64* %stripped_v4267
    %t4268 = load i64, i64* %prefix_len
    %si_v4269 = alloca i64
    store i64 %t4268, i64* %si_v4269
    br label %loop.cond.4270
loop.cond.4270:
    %t4273 = load i64, i64* %si_v4269
    %t4274 = load i64, i64* %constraint
    %t4275 = call i64 @freak_llvm_word_length(i64 %t4274)
    %t4277 = icmp sge i64 %t4273, %t4275
    %t4276 = zext i1 %t4277 to i64
    %t4278 = icmp eq i64 %t4276, 0
    br i1 %t4278, label %loop.body.4271, label %loop.end.4272
loop.body.4271:
    %t4279 = load i64, i64* %stripped_v4267
    %t4280 = load i64, i64* %constraint
    %t4282 = load i64, i64* %si_v4269
    %t4281 = call i64 @freak_llvm_word_char_at(i64 %t4280, i64 %t4282)
    %t4283 = call i64 @freak_llvm_word_concat(i64 %t4279, i64 %t4281)
    store i64 %t4283, i64* %stripped_v4267
    %t4284 = load i64, i64* %si_v4269
    %t4285 = add i64 %t4284, 1
    store i64 %t4285, i64* %si_v4269
    br label %loop.cond.4270
loop.end.4272:
    %t4286 = load i64, i64* %stripped_v4267
    ret i64 %t4286
    ret i64 0
}

define i64 @freak_ver_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t4287 = load i64, i64* %c
    %t4288 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.272, i64 0, i64 0
    %t4289 = ptrtoint i8* %t4288 to i64
    %t4290 = call i64 @freak_llvm_word_eq(i64 %t4287, i64 %t4289)
    %t4294 = icmp ne i64 %t4290, 0
    br i1 %t4294, label %if.then.4291, label %if.end.4293
if.then.4291:
    ret i64 1
    br label %if.end.4293
if.end.4293:
    %t4295 = load i64, i64* %c
    %t4296 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.273, i64 0, i64 0
    %t4297 = ptrtoint i8* %t4296 to i64
    %t4298 = call i64 @freak_llvm_word_eq(i64 %t4295, i64 %t4297)
    %t4302 = icmp ne i64 %t4298, 0
    br i1 %t4302, label %if.then.4299, label %if.end.4301
if.then.4299:
    ret i64 1
    br label %if.end.4301
if.end.4301:
    %t4303 = load i64, i64* %c
    %t4304 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.274, i64 0, i64 0
    %t4305 = ptrtoint i8* %t4304 to i64
    %t4306 = call i64 @freak_llvm_word_eq(i64 %t4303, i64 %t4305)
    %t4310 = icmp ne i64 %t4306, 0
    br i1 %t4310, label %if.then.4307, label %if.end.4309
if.then.4307:
    ret i64 1
    br label %if.end.4309
if.end.4309:
    %t4311 = load i64, i64* %c
    %t4312 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.275, i64 0, i64 0
    %t4313 = ptrtoint i8* %t4312 to i64
    %t4314 = call i64 @freak_llvm_word_eq(i64 %t4311, i64 %t4313)
    %t4318 = icmp ne i64 %t4314, 0
    br i1 %t4318, label %if.then.4315, label %if.end.4317
if.then.4315:
    ret i64 1
    br label %if.end.4317
if.end.4317:
    %t4319 = load i64, i64* %c
    %t4320 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.276, i64 0, i64 0
    %t4321 = ptrtoint i8* %t4320 to i64
    %t4322 = call i64 @freak_llvm_word_eq(i64 %t4319, i64 %t4321)
    %t4326 = icmp ne i64 %t4322, 0
    br i1 %t4326, label %if.then.4323, label %if.end.4325
if.then.4323:
    ret i64 1
    br label %if.end.4325
if.end.4325:
    %t4327 = load i64, i64* %c
    %t4328 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.277, i64 0, i64 0
    %t4329 = ptrtoint i8* %t4328 to i64
    %t4330 = call i64 @freak_llvm_word_eq(i64 %t4327, i64 %t4329)
    %t4334 = icmp ne i64 %t4330, 0
    br i1 %t4334, label %if.then.4331, label %if.end.4333
if.then.4331:
    ret i64 1
    br label %if.end.4333
if.end.4333:
    %t4335 = load i64, i64* %c
    %t4336 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.278, i64 0, i64 0
    %t4337 = ptrtoint i8* %t4336 to i64
    %t4338 = call i64 @freak_llvm_word_eq(i64 %t4335, i64 %t4337)
    %t4342 = icmp ne i64 %t4338, 0
    br i1 %t4342, label %if.then.4339, label %if.end.4341
if.then.4339:
    ret i64 1
    br label %if.end.4341
if.end.4341:
    %t4343 = load i64, i64* %c
    %t4344 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.279, i64 0, i64 0
    %t4345 = ptrtoint i8* %t4344 to i64
    %t4346 = call i64 @freak_llvm_word_eq(i64 %t4343, i64 %t4345)
    %t4350 = icmp ne i64 %t4346, 0
    br i1 %t4350, label %if.then.4347, label %if.end.4349
if.then.4347:
    ret i64 1
    br label %if.end.4349
if.end.4349:
    %t4351 = load i64, i64* %c
    %t4352 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.280, i64 0, i64 0
    %t4353 = ptrtoint i8* %t4352 to i64
    %t4354 = call i64 @freak_llvm_word_eq(i64 %t4351, i64 %t4353)
    %t4358 = icmp ne i64 %t4354, 0
    br i1 %t4358, label %if.then.4355, label %if.end.4357
if.then.4355:
    ret i64 1
    br label %if.end.4357
if.end.4357:
    %t4359 = load i64, i64* %c
    %t4360 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.281, i64 0, i64 0
    %t4361 = ptrtoint i8* %t4360 to i64
    %t4362 = call i64 @freak_llvm_word_eq(i64 %t4359, i64 %t4361)
    %t4366 = icmp ne i64 %t4362, 0
    br i1 %t4366, label %if.then.4363, label %if.end.4365
if.then.4363:
    ret i64 1
    br label %if.end.4365
if.end.4365:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_satisfies_single(i64 %arg_v, i64 %arg_constraint) {
entry:
    %v = alloca i64
    store i64 %arg_v, i64* %v
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4367 = load i64, i64* %constraint
    %t4368 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.282, i64 0, i64 0
    %t4369 = ptrtoint i8* %t4368 to i64
    %t4370 = call i64 @freak_llvm_word_eq(i64 %t4367, i64 %t4369)
    %t4371 = load i64, i64* %constraint
    %t4372 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.283, i64 0, i64 0
    %t4373 = ptrtoint i8* %t4372 to i64
    %t4374 = call i64 @freak_llvm_word_eq(i64 %t4371, i64 %t4373)
    %t4376 = icmp ne i64 %t4370, 0
    %t4377 = icmp ne i64 %t4374, 0
    %t4378 = or i1 %t4376, %t4377
    %t4375 = zext i1 %t4378 to i64
    %t4382 = icmp ne i64 %t4375, 0
    br i1 %t4382, label %if.then.4379, label %if.end.4381
if.then.4379:
    ret i64 1
    br label %if.end.4381
if.end.4381:
    %t4383 = load i64, i64* %constraint
    %t4385 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.284, i64 0, i64 0
    %t4386 = ptrtoint i8* %t4385 to i64
    %t4384 = call i64 @freak_llvm_word_starts_with(i64 %t4383, i64 %t4386)
    %t4390 = icmp ne i64 %t4384, 0
    br i1 %t4390, label %if.then.4387, label %if.end.4389
if.then.4387:
    %t4391 = load i64, i64* %constraint
    %t4392 = call i64 @freak_ver_strip_prefix(i64 %t4391, i64 1)
    %t4393 = call i64 @freak_ver_parse(i64 %t4392)
    %c_v4394 = alloca i64
    store i64 %t4393, i64* %c_v4394
    %t4395 = load i64, i64* %v
    %t4396 = call i64 @freak_ver_major(i64 %t4395)
    %t4397 = load i64, i64* %c_v4394
    %t4398 = call i64 @freak_ver_major(i64 %t4397)
    %t4400 = icmp ne i64 %t4396, %t4398
    %t4399 = zext i1 %t4400 to i64
    %t4404 = icmp ne i64 %t4399, 0
    br i1 %t4404, label %if.then.4401, label %if.end.4403
if.then.4401:
    ret i64 0
    br label %if.end.4403
if.end.4403:
    %t4405 = load i64, i64* %v
    %t4406 = load i64, i64* %c_v4394
    %t4407 = call i64 @freak_ver_gte(i64 %t4405, i64 %t4406)
    ret i64 %t4407
    br label %if.end.4389
if.end.4389:
    %t4408 = load i64, i64* %constraint
    %t4410 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.285, i64 0, i64 0
    %t4411 = ptrtoint i8* %t4410 to i64
    %t4409 = call i64 @freak_llvm_word_starts_with(i64 %t4408, i64 %t4411)
    %t4415 = icmp ne i64 %t4409, 0
    br i1 %t4415, label %if.then.4412, label %if.end.4414
if.then.4412:
    %t4416 = load i64, i64* %constraint
    %t4417 = call i64 @freak_ver_strip_prefix(i64 %t4416, i64 1)
    %t4418 = call i64 @freak_ver_parse(i64 %t4417)
    %t_v4419 = alloca i64
    store i64 %t4418, i64* %t_v4419
    %t4420 = load i64, i64* %v
    %t4421 = call i64 @freak_ver_major(i64 %t4420)
    %t4422 = load i64, i64* %t_v4419
    %t4423 = call i64 @freak_ver_major(i64 %t4422)
    %t4425 = icmp ne i64 %t4421, %t4423
    %t4424 = zext i1 %t4425 to i64
    %t4429 = icmp ne i64 %t4424, 0
    br i1 %t4429, label %if.then.4426, label %if.end.4428
if.then.4426:
    ret i64 0
    br label %if.end.4428
if.end.4428:
    %t4430 = load i64, i64* %v
    %t4431 = call i64 @freak_ver_minor(i64 %t4430)
    %t4432 = load i64, i64* %t_v4419
    %t4433 = call i64 @freak_ver_minor(i64 %t4432)
    %t4435 = icmp ne i64 %t4431, %t4433
    %t4434 = zext i1 %t4435 to i64
    %t4439 = icmp ne i64 %t4434, 0
    br i1 %t4439, label %if.then.4436, label %if.end.4438
if.then.4436:
    ret i64 0
    br label %if.end.4438
if.end.4438:
    %t4440 = load i64, i64* %v
    %t4441 = load i64, i64* %t_v4419
    %t4442 = call i64 @freak_ver_gte(i64 %t4440, i64 %t4441)
    ret i64 %t4442
    br label %if.end.4414
if.end.4414:
    %t4443 = load i64, i64* %constraint
    %t4445 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.286, i64 0, i64 0
    %t4446 = ptrtoint i8* %t4445 to i64
    %t4444 = call i64 @freak_llvm_word_starts_with(i64 %t4443, i64 %t4446)
    %t4450 = icmp ne i64 %t4444, 0
    br i1 %t4450, label %if.then.4447, label %if.end.4449
if.then.4447:
    %t4451 = load i64, i64* %v
    %t4452 = load i64, i64* %constraint
    %t4453 = call i64 @freak_ver_strip_prefix(i64 %t4452, i64 2)
    %t4454 = call i64 @freak_ver_parse(i64 %t4453)
    %t4455 = call i64 @freak_ver_gte(i64 %t4451, i64 %t4454)
    ret i64 %t4455
    br label %if.end.4449
if.end.4449:
    %t4456 = load i64, i64* %constraint
    %t4458 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.287, i64 0, i64 0
    %t4459 = ptrtoint i8* %t4458 to i64
    %t4457 = call i64 @freak_llvm_word_starts_with(i64 %t4456, i64 %t4459)
    %t4463 = icmp ne i64 %t4457, 0
    br i1 %t4463, label %if.then.4460, label %if.end.4462
if.then.4460:
    %t4464 = load i64, i64* %v
    %t4465 = load i64, i64* %constraint
    %t4466 = call i64 @freak_ver_strip_prefix(i64 %t4465, i64 2)
    %t4467 = call i64 @freak_ver_parse(i64 %t4466)
    %t4468 = call i64 @freak_ver_lte(i64 %t4464, i64 %t4467)
    ret i64 %t4468
    br label %if.end.4462
if.end.4462:
    %t4469 = load i64, i64* %constraint
    %t4471 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.288, i64 0, i64 0
    %t4472 = ptrtoint i8* %t4471 to i64
    %t4470 = call i64 @freak_llvm_word_starts_with(i64 %t4469, i64 %t4472)
    %t4476 = icmp ne i64 %t4470, 0
    br i1 %t4476, label %if.then.4473, label %if.end.4475
if.then.4473:
    %t4477 = load i64, i64* %v
    %t4478 = load i64, i64* %constraint
    %t4479 = call i64 @freak_ver_strip_prefix(i64 %t4478, i64 1)
    %t4480 = call i64 @freak_ver_parse(i64 %t4479)
    %t4481 = call i64 @freak_ver_gt(i64 %t4477, i64 %t4480)
    ret i64 %t4481
    br label %if.end.4475
if.end.4475:
    %t4482 = load i64, i64* %constraint
    %t4484 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.289, i64 0, i64 0
    %t4485 = ptrtoint i8* %t4484 to i64
    %t4483 = call i64 @freak_llvm_word_starts_with(i64 %t4482, i64 %t4485)
    %t4489 = icmp ne i64 %t4483, 0
    br i1 %t4489, label %if.then.4486, label %if.end.4488
if.then.4486:
    %t4490 = load i64, i64* %v
    %t4491 = load i64, i64* %constraint
    %t4492 = call i64 @freak_ver_strip_prefix(i64 %t4491, i64 1)
    %t4493 = call i64 @freak_ver_parse(i64 %t4492)
    %t4494 = call i64 @freak_ver_lt(i64 %t4490, i64 %t4493)
    ret i64 %t4494
    br label %if.end.4488
if.end.4488:
    %t4495 = load i64, i64* %constraint
    %t4497 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.290, i64 0, i64 0
    %t4498 = ptrtoint i8* %t4497 to i64
    %t4496 = call i64 @freak_llvm_word_starts_with(i64 %t4495, i64 %t4498)
    %t4502 = icmp ne i64 %t4496, 0
    br i1 %t4502, label %if.then.4499, label %if.end.4501
if.then.4499:
    %t4503 = load i64, i64* %v
    %t4504 = load i64, i64* %constraint
    %t4505 = call i64 @freak_ver_strip_prefix(i64 %t4504, i64 1)
    %t4506 = call i64 @freak_ver_parse(i64 %t4505)
    %t4507 = call i64 @freak_ver_eq(i64 %t4503, i64 %t4506)
    ret i64 %t4507
    br label %if.end.4501
if.end.4501:
    %t4508 = load i64, i64* %constraint
    %t4509 = call i64 @freak_llvm_word_length(i64 %t4508)
    %t4511 = icmp sgt i64 %t4509, 0
    %t4510 = zext i1 %t4511 to i64
    %t4515 = icmp ne i64 %t4510, 0
    br i1 %t4515, label %if.then.4512, label %if.end.4514
if.then.4512:
    %t4516 = load i64, i64* %constraint
    %t4517 = call i64 @freak_llvm_word_char_at(i64 %t4516, i64 0)
    %fc_v4518 = alloca i64
    store i64 %t4517, i64* %fc_v4518
    %t4519 = load i64, i64* %fc_v4518
    %t4520 = call i64 @freak_ver_is_digit(i64 %t4519)
    %t4524 = icmp ne i64 %t4520, 0
    br i1 %t4524, label %if.then.4521, label %if.end.4523
if.then.4521:
    %t4525 = load i64, i64* %constraint
    %t4526 = call i64 @freak_ver_parse(i64 %t4525)
    %c_v4527 = alloca i64
    store i64 %t4526, i64* %c_v4527
    %t4528 = load i64, i64* %v
    %t4529 = call i64 @freak_ver_major(i64 %t4528)
    %t4530 = load i64, i64* %c_v4527
    %t4531 = call i64 @freak_ver_major(i64 %t4530)
    %t4533 = icmp ne i64 %t4529, %t4531
    %t4532 = zext i1 %t4533 to i64
    %t4537 = icmp ne i64 %t4532, 0
    br i1 %t4537, label %if.then.4534, label %if.end.4536
if.then.4534:
    ret i64 0
    br label %if.end.4536
if.end.4536:
    %t4538 = load i64, i64* %v
    %t4539 = load i64, i64* %c_v4527
    %t4540 = call i64 @freak_ver_gte(i64 %t4538, i64 %t4539)
    ret i64 %t4540
    br label %if.end.4523
if.end.4523:
    br label %if.end.4514
if.end.4514:
    %t4541 = load i64, i64* %v
    %t4542 = load i64, i64* %constraint
    %t4543 = call i64 @freak_ver_parse(i64 %t4542)
    %t4544 = call i64 @freak_ver_eq(i64 %t4541, i64 %t4543)
    ret i64 %t4544
    ret i64 0
}

define i64 @freak_ver_satisfies(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4545 = load i64, i64* %version
    %t4546 = call i64 @freak_ver_parse(i64 %t4545)
    %v_v4547 = alloca i64
    store i64 %t4546, i64* %v_v4547
    %t4548 = load i64, i64* %constraint
    %t4549 = call i64 @freak_llvm_word_length(i64 %t4548)
    %clen_v4550 = alloca i64
    store i64 %t4549, i64* %clen_v4550
    %t4551 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.291, i64 0, i64 0
    %t4552 = ptrtoint i8* %t4551 to i64
    %current_v4553 = alloca i64
    store i64 %t4552, i64* %current_v4553
    %i_v4554 = alloca i64
    store i64 0, i64* %i_v4554
    br label %loop.cond.4555
loop.cond.4555:
    %t4558 = load i64, i64* %i_v4554
    %t4559 = load i64, i64* %clen_v4550
    %t4561 = icmp sge i64 %t4558, %t4559
    %t4560 = zext i1 %t4561 to i64
    %t4562 = icmp eq i64 %t4560, 0
    br i1 %t4562, label %loop.body.4556, label %loop.end.4557
loop.body.4556:
    %t4563 = load i64, i64* %constraint
    %t4565 = load i64, i64* %i_v4554
    %t4564 = call i64 @freak_llvm_word_char_at(i64 %t4563, i64 %t4565)
    %ch_v4566 = alloca i64
    store i64 %t4564, i64* %ch_v4566
    %t4567 = load i64, i64* %ch_v4566
    %t4568 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.292, i64 0, i64 0
    %t4569 = ptrtoint i8* %t4568 to i64
    %t4570 = call i64 @freak_llvm_word_eq(i64 %t4567, i64 %t4569)
    %t4574 = icmp ne i64 %t4570, 0
    br i1 %t4574, label %if.then.4571, label %if.else.4572
if.then.4571:
    %t4575 = load i64, i64* %current_v4553
    %t4576 = call i64 @freak_llvm_word_length(i64 %t4575)
    %t4578 = icmp sgt i64 %t4576, 0
    %t4577 = zext i1 %t4578 to i64
    %t4582 = icmp ne i64 %t4577, 0
    br i1 %t4582, label %if.then.4579, label %if.end.4581
if.then.4579:
    %t4583 = load i64, i64* %v_v4547
    %t4584 = load i64, i64* %current_v4553
    %t4585 = call i64 @freak_ver_satisfies_single(i64 %t4583, i64 %t4584)
    %t4587 = icmp eq i64 %t4585, 0
    %t4586 = zext i1 %t4587 to i64
    %t4591 = icmp ne i64 %t4586, 0
    br i1 %t4591, label %if.then.4588, label %if.end.4590
if.then.4588:
    ret i64 0
    br label %if.end.4590
if.end.4590:
    %t4592 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.293, i64 0, i64 0
    %t4593 = ptrtoint i8* %t4592 to i64
    store i64 %t4593, i64* %current_v4553
    br label %if.end.4581
if.end.4581:
    br label %if.end.4573
if.else.4572:
    %t4594 = load i64, i64* %current_v4553
    %t4595 = load i64, i64* %ch_v4566
    %t4596 = call i64 @freak_llvm_word_concat(i64 %t4594, i64 %t4595)
    store i64 %t4596, i64* %current_v4553
    br label %if.end.4573
if.end.4573:
    %t4597 = load i64, i64* %i_v4554
    %t4598 = add i64 %t4597, 1
    store i64 %t4598, i64* %i_v4554
    br label %loop.cond.4555
loop.end.4557:
    %t4599 = load i64, i64* %current_v4553
    %t4600 = call i64 @freak_llvm_word_length(i64 %t4599)
    %t4602 = icmp sgt i64 %t4600, 0
    %t4601 = zext i1 %t4602 to i64
    %t4606 = icmp ne i64 %t4601, 0
    br i1 %t4606, label %if.then.4603, label %if.end.4605
if.then.4603:
    %t4607 = load i64, i64* %v_v4547
    %t4608 = load i64, i64* %current_v4553
    %t4609 = call i64 @freak_ver_satisfies_single(i64 %t4607, i64 %t4608)
    %t4611 = icmp eq i64 %t4609, 0
    %t4610 = zext i1 %t4611 to i64
    %t4615 = icmp ne i64 %t4610, 0
    br i1 %t4615, label %if.then.4612, label %if.end.4614
if.then.4612:
    ret i64 0
    br label %if.end.4614
if.end.4614:
    br label %if.end.4605
if.end.4605:
    ret i64 1
    ret i64 0
}

define i64 @freak_version_matches_constraint(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4616 = load i64, i64* %version
    %t4617 = load i64, i64* %constraint
    %t4618 = call i64 @freak_ver_satisfies(i64 %t4616, i64 %t4617)
    ret i64 %t4618
    ret i64 0
}

define void @freak_http_init() {
entry:
    %t4619 = load i64, i64* @g_http_inited
    %t4621 = icmp eq i64 %t4619, 0
    %t4620 = zext i1 %t4621 to i64
    %t4625 = icmp ne i64 %t4620, 0
    br i1 %t4625, label %if.then.4622, label %if.end.4624
if.then.4622:
    %t4626 = call i64 @freak_llvm_array_new()
    store i64 %t4626, i64* @g_http_resp_statuses
    %t4627 = call i64 @freak_llvm_array_new()
    store i64 %t4627, i64* @g_http_resp_bodies
    %t4628 = call i64 @freak_llvm_array_new()
    store i64 %t4628, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 1, i64* @g_http_inited
    br label %if.end.4624
if.end.4624:
    ret void
}

define i64 @freak_http_alloc_resp(i64 %arg_status, i64 %arg_body, i64 %arg_headers) {
entry:
    %status = alloca i64
    store i64 %arg_status, i64* %status
    %body = alloca i64
    store i64 %arg_body, i64* %body
    %headers = alloca i64
    store i64 %arg_headers, i64* %headers
    %t4629 = load i64, i64* @g_http_resp_count
    %idx_v4630 = alloca i64
    store i64 %t4629, i64* %idx_v4630
    %t4631 = load i64, i64* @g_http_resp_statuses
    %t4632 = load i64, i64* %status
    %t4633 = call i64 @freak_llvm_word_from_int(i64 %t4632)
    call void @freak_llvm_array_push(i64 %t4631, i64 %t4633)
    %t4634 = load i64, i64* @g_http_resp_bodies
    %t4635 = load i64, i64* %body
    call void @freak_llvm_array_push(i64 %t4634, i64 %t4635)
    %t4636 = load i64, i64* @g_http_resp_headers_raw
    %t4637 = load i64, i64* %headers
    call void @freak_llvm_array_push(i64 %t4636, i64 %t4637)
    %t4638 = load i64, i64* @g_http_resp_count
    %t4639 = add i64 %t4638, 1
    store i64 %t4639, i64* @g_http_resp_count
    %t4640 = load i64, i64* %idx_v4630
    ret i64 %t4640
    ret i64 0
}

define i64 @freak_http_resp_status(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4641 = load i64, i64* @g_http_resp_statuses
    %t4642 = load i64, i64* %handle
    %t4643 = call i64 @freak_llvm_array_get(i64 %t4641, i64 %t4642)
    %v_v4644 = alloca i64
    store i64 %t4643, i64* %v_v4644
    %t4645 = load i64, i64* %v_v4644
    %t4646 = call i64 @freak_llvm_word_to_int(i64 %t4645)
    ret i64 %t4646
    ret i64 0
}

define i64 @freak_http_resp_body(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4647 = load i64, i64* @g_http_resp_bodies
    %t4648 = load i64, i64* %handle
    %t4649 = call i64 @freak_llvm_array_get(i64 %t4647, i64 %t4648)
    ret i64 %t4649
    ret i64 0
}

define i64 @freak_http_resp_headers(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4650 = load i64, i64* @g_http_resp_headers_raw
    %t4651 = load i64, i64* %handle
    %t4652 = call i64 @freak_llvm_array_get(i64 %t4650, i64 %t4651)
    ret i64 %t4652
    ret i64 0
}

define i64 @freak_http_parse_status(i64 %arg_line) {
entry:
    %line = alloca i64
    store i64 %arg_line, i64* %line
    %t4653 = load i64, i64* %line
    %t4654 = call i64 @freak_llvm_word_length(i64 %t4653)
    %slen_v4655 = alloca i64
    store i64 %t4654, i64* %slen_v4655
    %si_v4656 = alloca i64
    store i64 0, i64* %si_v4656
    %t4662 = load i64, i64* %slen_v4655
    %rep.4661 = alloca i64
    store i64 0, i64* %rep.4661
    br label %loop.cond.4657
loop.cond.4657:
    %t4663 = load i64, i64* %rep.4661
    %t4664 = icmp slt i64 %t4663, %t4662
    br i1 %t4664, label %loop.body.4658, label %loop.end.4659
loop.body.4658:
    %t4665 = load i64, i64* %line
    %t4667 = load i64, i64* %si_v4656
    %t4666 = call i64 @freak_llvm_word_char_at(i64 %t4665, i64 %t4667)
    %t4668 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.294, i64 0, i64 0
    %t4669 = ptrtoint i8* %t4668 to i64
    %t4670 = call i64 @freak_llvm_word_eq(i64 %t4666, i64 %t4669)
    %t4674 = icmp ne i64 %t4670, 0
    br i1 %t4674, label %if.then.4671, label %if.end.4673
if.then.4671:
    %t4675 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.295, i64 0, i64 0
    %t4676 = ptrtoint i8* %t4675 to i64
    %code_str_v4677 = alloca i64
    store i64 %t4676, i64* %code_str_v4677
    %t4678 = load i64, i64* %si_v4656
    %t4679 = add i64 %t4678, 1
    %ci_v4680 = alloca i64
    store i64 %t4679, i64* %ci_v4680
    %rep.4685 = alloca i64
    store i64 0, i64* %rep.4685
    br label %loop.cond.4681
loop.cond.4681:
    %t4686 = load i64, i64* %rep.4685
    %t4687 = icmp slt i64 %t4686, 3
    br i1 %t4687, label %loop.body.4682, label %loop.end.4683
loop.body.4682:
    %t4688 = load i64, i64* %ci_v4680
    %t4689 = load i64, i64* %slen_v4655
    %t4691 = icmp slt i64 %t4688, %t4689
    %t4690 = zext i1 %t4691 to i64
    %t4695 = icmp ne i64 %t4690, 0
    br i1 %t4695, label %if.then.4692, label %if.end.4694
if.then.4692:
    %t4696 = load i64, i64* %code_str_v4677
    %t4697 = load i64, i64* %line
    %t4699 = load i64, i64* %ci_v4680
    %t4698 = call i64 @freak_llvm_word_char_at(i64 %t4697, i64 %t4699)
    %t4700 = call i64 @freak_llvm_word_concat(i64 %t4696, i64 %t4698)
    store i64 %t4700, i64* %code_str_v4677
    %t4701 = load i64, i64* %ci_v4680
    %t4702 = add i64 %t4701, 1
    store i64 %t4702, i64* %ci_v4680
    br label %if.end.4694
if.end.4694:
    br label %loop.inc.4684
loop.inc.4684:
    %t4703 = load i64, i64* %rep.4685
    %t4704 = add i64 %t4703, 1
    store i64 %t4704, i64* %rep.4685
    br label %loop.cond.4681
loop.end.4683:
    %t4705 = load i64, i64* %code_str_v4677
    %t4706 = call i64 @freak_llvm_word_to_int(i64 %t4705)
    ret i64 %t4706
    br label %if.end.4673
if.end.4673:
    %t4707 = load i64, i64* %si_v4656
    %t4708 = add i64 %t4707, 1
    store i64 %t4708, i64* %si_v4656
    br label %loop.inc.4660
loop.inc.4660:
    %t4709 = load i64, i64* %rep.4661
    %t4710 = add i64 %t4709, 1
    store i64 %t4710, i64* %rep.4661
    br label %loop.cond.4657
loop.end.4659:
    ret i64 0
    ret i64 0
}

define i64 @freak_http_split_response(i64 %arg_raw) {
entry:
    %raw = alloca i64
    store i64 %arg_raw, i64* %raw
    %t4711 = load i64, i64* %raw
    %t4712 = call i64 @freak_llvm_word_length(i64 %t4711)
    %rlen_v4713 = alloca i64
    store i64 %t4712, i64* %rlen_v4713
    %ri_v4714 = alloca i64
    store i64 0, i64* %ri_v4714
    %t4715 = sub i64 0, 1
    %header_end_v4716 = alloca i64
    store i64 %t4715, i64* %header_end_v4716
    %t4717 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.296, i64 0, i64 0
    %t4718 = ptrtoint i8* %t4717 to i64
    %prev3_v4719 = alloca i64
    store i64 %t4718, i64* %prev3_v4719
    %t4720 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.297, i64 0, i64 0
    %t4721 = ptrtoint i8* %t4720 to i64
    %prev2_v4722 = alloca i64
    store i64 %t4721, i64* %prev2_v4722
    %t4723 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.298, i64 0, i64 0
    %t4724 = ptrtoint i8* %t4723 to i64
    %prev1_v4725 = alloca i64
    store i64 %t4724, i64* %prev1_v4725
    %t4731 = load i64, i64* %rlen_v4713
    %rep.4730 = alloca i64
    store i64 0, i64* %rep.4730
    br label %loop.cond.4726
loop.cond.4726:
    %t4732 = load i64, i64* %rep.4730
    %t4733 = icmp slt i64 %t4732, %t4731
    br i1 %t4733, label %loop.body.4727, label %loop.end.4728
loop.body.4727:
    %t4734 = load i64, i64* %raw
    %t4736 = load i64, i64* %ri_v4714
    %t4735 = call i64 @freak_llvm_word_char_at(i64 %t4734, i64 %t4736)
    %ch_v4737 = alloca i64
    store i64 %t4735, i64* %ch_v4737
    %t4738 = load i64, i64* %prev2_v4722
    %t4739 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.299, i64 0, i64 0
    %t4740 = ptrtoint i8* %t4739 to i64
    %t4741 = call i64 @freak_llvm_word_eq(i64 %t4738, i64 %t4740)
    %t4742 = load i64, i64* %prev1_v4725
    %t4743 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.300, i64 0, i64 0
    %t4744 = ptrtoint i8* %t4743 to i64
    %t4745 = call i64 @freak_llvm_word_eq(i64 %t4742, i64 %t4744)
    %t4747 = icmp ne i64 %t4741, 0
    %t4748 = icmp ne i64 %t4745, 0
    %t4749 = and i1 %t4747, %t4748
    %t4746 = zext i1 %t4749 to i64
    %t4750 = load i64, i64* %ch_v4737
    %t4751 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.301, i64 0, i64 0
    %t4752 = ptrtoint i8* %t4751 to i64
    %t4753 = call i64 @freak_llvm_word_eq(i64 %t4750, i64 %t4752)
    %t4755 = icmp ne i64 %t4746, 0
    %t4756 = icmp ne i64 %t4753, 0
    %t4757 = and i1 %t4755, %t4756
    %t4754 = zext i1 %t4757 to i64
    %t4761 = icmp ne i64 %t4754, 0
    br i1 %t4761, label %if.then.4758, label %if.end.4760
if.then.4758:
    %t4762 = load i64, i64* %ri_v4714
    %t4763 = add i64 %t4762, 1
    store i64 %t4763, i64* %header_end_v4716
    br label %if.end.4760
if.end.4760:
    %t4764 = load i64, i64* %prev3_v4719
    %t4765 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.302, i64 0, i64 0
    %t4766 = ptrtoint i8* %t4765 to i64
    %t4767 = call i64 @freak_llvm_word_eq(i64 %t4764, i64 %t4766)
    %t4768 = load i64, i64* %prev2_v4722
    %t4769 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.303, i64 0, i64 0
    %t4770 = ptrtoint i8* %t4769 to i64
    %t4771 = call i64 @freak_llvm_word_eq(i64 %t4768, i64 %t4770)
    %t4773 = icmp ne i64 %t4767, 0
    %t4774 = icmp ne i64 %t4771, 0
    %t4775 = and i1 %t4773, %t4774
    %t4772 = zext i1 %t4775 to i64
    %t4776 = load i64, i64* %prev1_v4725
    %t4777 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.304, i64 0, i64 0
    %t4778 = ptrtoint i8* %t4777 to i64
    %t4779 = call i64 @freak_llvm_word_eq(i64 %t4776, i64 %t4778)
    %t4781 = icmp ne i64 %t4772, 0
    %t4782 = icmp ne i64 %t4779, 0
    %t4783 = and i1 %t4781, %t4782
    %t4780 = zext i1 %t4783 to i64
    %t4784 = load i64, i64* %ch_v4737
    %t4785 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.305, i64 0, i64 0
    %t4786 = ptrtoint i8* %t4785 to i64
    %t4787 = call i64 @freak_llvm_word_eq(i64 %t4784, i64 %t4786)
    %t4789 = icmp ne i64 %t4780, 0
    %t4790 = icmp ne i64 %t4787, 0
    %t4791 = and i1 %t4789, %t4790
    %t4788 = zext i1 %t4791 to i64
    %t4795 = icmp ne i64 %t4788, 0
    br i1 %t4795, label %if.then.4792, label %if.end.4794
if.then.4792:
    %t4796 = load i64, i64* %ri_v4714
    %t4797 = add i64 %t4796, 1
    store i64 %t4797, i64* %header_end_v4716
    br label %if.end.4794
if.end.4794:
    %t4798 = load i64, i64* %prev2_v4722
    store i64 %t4798, i64* %prev3_v4719
    %t4799 = load i64, i64* %prev1_v4725
    store i64 %t4799, i64* %prev2_v4722
    %t4800 = load i64, i64* %ch_v4737
    store i64 %t4800, i64* %prev1_v4725
    %t4801 = load i64, i64* %ri_v4714
    %t4802 = add i64 %t4801, 1
    store i64 %t4802, i64* %ri_v4714
    br label %loop.inc.4729
loop.inc.4729:
    %t4803 = load i64, i64* %rep.4730
    %t4804 = add i64 %t4803, 1
    store i64 %t4804, i64* %rep.4730
    br label %loop.cond.4726
loop.end.4728:
    %t4805 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.306, i64 0, i64 0
    %t4806 = ptrtoint i8* %t4805 to i64
    %status_line_v4807 = alloca i64
    store i64 %t4806, i64* %status_line_v4807
    %li_v4808 = alloca i64
    store i64 0, i64* %li_v4808
    %t4814 = load i64, i64* %rlen_v4713
    %rep.4813 = alloca i64
    store i64 0, i64* %rep.4813
    br label %loop.cond.4809
loop.cond.4809:
    %t4815 = load i64, i64* %rep.4813
    %t4816 = icmp slt i64 %t4815, %t4814
    br i1 %t4816, label %loop.body.4810, label %loop.end.4811
loop.body.4810:
    %t4817 = load i64, i64* %raw
    %t4819 = load i64, i64* %li_v4808
    %t4818 = call i64 @freak_llvm_word_char_at(i64 %t4817, i64 %t4819)
    %lc_v4820 = alloca i64
    store i64 %t4818, i64* %lc_v4820
    %t4821 = load i64, i64* %lc_v4820
    %t4822 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.307, i64 0, i64 0
    %t4823 = ptrtoint i8* %t4822 to i64
    %t4824 = call i64 @freak_llvm_word_eq(i64 %t4821, i64 %t4823)
    %t4825 = load i64, i64* %lc_v4820
    %t4826 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.308, i64 0, i64 0
    %t4827 = ptrtoint i8* %t4826 to i64
    %t4828 = call i64 @freak_llvm_word_eq(i64 %t4825, i64 %t4827)
    %t4830 = icmp ne i64 %t4824, 0
    %t4831 = icmp ne i64 %t4828, 0
    %t4832 = or i1 %t4830, %t4831
    %t4829 = zext i1 %t4832 to i64
    %t4836 = icmp ne i64 %t4829, 0
    br i1 %t4836, label %if.then.4833, label %if.else.4834
if.then.4833:
    %t4837 = load i64, i64* %rlen_v4713
    store i64 %t4837, i64* %li_v4808
    br label %if.end.4835
if.else.4834:
    %t4838 = load i64, i64* %status_line_v4807
    %t4839 = load i64, i64* %lc_v4820
    %t4840 = call i64 @freak_llvm_word_concat(i64 %t4838, i64 %t4839)
    store i64 %t4840, i64* %status_line_v4807
    br label %if.end.4835
if.end.4835:
    %t4841 = load i64, i64* %li_v4808
    %t4842 = add i64 %t4841, 1
    store i64 %t4842, i64* %li_v4808
    br label %loop.inc.4812
loop.inc.4812:
    %t4843 = load i64, i64* %rep.4813
    %t4844 = add i64 %t4843, 1
    store i64 %t4844, i64* %rep.4813
    br label %loop.cond.4809
loop.end.4811:
    %t4845 = load i64, i64* %status_line_v4807
    %t4846 = call i64 @freak_http_parse_status(i64 %t4845)
    %status_v4847 = alloca i64
    store i64 %t4846, i64* %status_v4847
    %t4848 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.309, i64 0, i64 0
    %t4849 = ptrtoint i8* %t4848 to i64
    %headers_v4850 = alloca i64
    store i64 %t4849, i64* %headers_v4850
    %t4851 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.310, i64 0, i64 0
    %t4852 = ptrtoint i8* %t4851 to i64
    %body_v4853 = alloca i64
    store i64 %t4852, i64* %body_v4853
    %t4854 = load i64, i64* %header_end_v4716
    %t4856 = icmp sgt i64 %t4854, 0
    %t4855 = zext i1 %t4856 to i64
    %t4860 = icmp ne i64 %t4855, 0
    br i1 %t4860, label %if.then.4857, label %if.else.4858
if.then.4857:
    %hi_v4861 = alloca i64
    store i64 0, i64* %hi_v4861
    %t4867 = load i64, i64* %header_end_v4716
    %rep.4866 = alloca i64
    store i64 0, i64* %rep.4866
    br label %loop.cond.4862
loop.cond.4862:
    %t4868 = load i64, i64* %rep.4866
    %t4869 = icmp slt i64 %t4868, %t4867
    br i1 %t4869, label %loop.body.4863, label %loop.end.4864
loop.body.4863:
    %t4870 = load i64, i64* %hi_v4861
    %t4871 = load i64, i64* %rlen_v4713
    %t4873 = icmp slt i64 %t4870, %t4871
    %t4872 = zext i1 %t4873 to i64
    %t4877 = icmp ne i64 %t4872, 0
    br i1 %t4877, label %if.then.4874, label %if.end.4876
if.then.4874:
    %t4878 = load i64, i64* %headers_v4850
    %t4879 = load i64, i64* %raw
    %t4881 = load i64, i64* %hi_v4861
    %t4880 = call i64 @freak_llvm_word_char_at(i64 %t4879, i64 %t4881)
    %t4882 = call i64 @freak_llvm_word_concat(i64 %t4878, i64 %t4880)
    store i64 %t4882, i64* %headers_v4850
    br label %if.end.4876
if.end.4876:
    %t4883 = load i64, i64* %hi_v4861
    %t4884 = add i64 %t4883, 1
    store i64 %t4884, i64* %hi_v4861
    br label %loop.inc.4865
loop.inc.4865:
    %t4885 = load i64, i64* %rep.4866
    %t4886 = add i64 %t4885, 1
    store i64 %t4886, i64* %rep.4866
    br label %loop.cond.4862
loop.end.4864:
    %t4887 = load i64, i64* %header_end_v4716
    %bi_v4888 = alloca i64
    store i64 %t4887, i64* %bi_v4888
    %t4894 = load i64, i64* %rlen_v4713
    %rep.4893 = alloca i64
    store i64 0, i64* %rep.4893
    br label %loop.cond.4889
loop.cond.4889:
    %t4895 = load i64, i64* %rep.4893
    %t4896 = icmp slt i64 %t4895, %t4894
    br i1 %t4896, label %loop.body.4890, label %loop.end.4891
loop.body.4890:
    %t4897 = load i64, i64* %bi_v4888
    %t4898 = load i64, i64* %rlen_v4713
    %t4900 = icmp slt i64 %t4897, %t4898
    %t4899 = zext i1 %t4900 to i64
    %t4904 = icmp ne i64 %t4899, 0
    br i1 %t4904, label %if.then.4901, label %if.end.4903
if.then.4901:
    %t4905 = load i64, i64* %body_v4853
    %t4906 = load i64, i64* %raw
    %t4908 = load i64, i64* %bi_v4888
    %t4907 = call i64 @freak_llvm_word_char_at(i64 %t4906, i64 %t4908)
    %t4909 = call i64 @freak_llvm_word_concat(i64 %t4905, i64 %t4907)
    store i64 %t4909, i64* %body_v4853
    br label %if.end.4903
if.end.4903:
    %t4910 = load i64, i64* %bi_v4888
    %t4911 = add i64 %t4910, 1
    store i64 %t4911, i64* %bi_v4888
    br label %loop.inc.4892
loop.inc.4892:
    %t4912 = load i64, i64* %rep.4893
    %t4913 = add i64 %t4912, 1
    store i64 %t4913, i64* %rep.4893
    br label %loop.cond.4889
loop.end.4891:
    br label %if.end.4859
if.else.4858:
    %t4914 = load i64, i64* %raw
    store i64 %t4914, i64* %headers_v4850
    br label %if.end.4859
if.end.4859:
    %t4915 = load i64, i64* %status_v4847
    %t4916 = load i64, i64* %body_v4853
    %t4917 = load i64, i64* %headers_v4850
    %t4918 = call i64 @freak_http_alloc_resp(i64 %t4915, i64 %t4916, i64 %t4917)
    ret i64 %t4918
    ret i64 0
}

define i64 @freak_http_get(i64 %arg_host, i64 %arg_path, i64 %arg_port) {
entry:
    %host = alloca i64
    store i64 %arg_host, i64* %host
    %path = alloca i64
    store i64 %arg_path, i64* %path
    %port = alloca i64
    store i64 %arg_port, i64* %port
    call void @freak_http_init()
    %t4919 = load i64, i64* %host
    %t4920 = load i64, i64* %port
    %t4921 = call i64 @freak_llvm_tcp_connect(i64 %t4919, i64 %t4920)
    %fd_v4922 = alloca i64
    store i64 %t4921, i64* %fd_v4922
    %t4923 = load i64, i64* %fd_v4922
    %t4925 = icmp slt i64 %t4923, 0
    %t4924 = zext i1 %t4925 to i64
    %t4929 = icmp ne i64 %t4924, 0
    br i1 %t4929, label %if.then.4926, label %if.end.4928
if.then.4926:
    %t4930 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.311, i64 0, i64 0
    %t4931 = ptrtoint i8* %t4930 to i64
    %t4932 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.312, i64 0, i64 0
    %t4933 = ptrtoint i8* %t4932 to i64
    %t4934 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4931, i64 %t4933)
    ret i64 %t4934
    br label %if.end.4928
if.end.4928:
    %t4935 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.313, i64 0, i64 0
    %t4936 = ptrtoint i8* %t4935 to i64
    %t4937 = load i64, i64* %path
    %t4938 = call i64 @freak_llvm_word_concat(i64 %t4936, i64 %t4937)
    %t4939 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.314, i64 0, i64 0
    %t4940 = ptrtoint i8* %t4939 to i64
    %t4941 = call i64 @freak_llvm_word_concat(i64 %t4938, i64 %t4940)
    %t4942 = load i64, i64* %host
    %t4943 = call i64 @freak_llvm_word_concat(i64 %t4941, i64 %t4942)
    %t4944 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.315, i64 0, i64 0
    %t4945 = ptrtoint i8* %t4944 to i64
    %t4946 = call i64 @freak_llvm_word_concat(i64 %t4943, i64 %t4945)
    %req_v4947 = alloca i64
    store i64 %t4946, i64* %req_v4947
    %t4948 = load i64, i64* %fd_v4922
    %t4949 = load i64, i64* %req_v4947
    %t4950 = call i64 @freak_llvm_tcp_send(i64 %t4948, i64 %t4949)
    %t4951 = load i64, i64* %fd_v4922
    %t4952 = call i64 @freak_llvm_tcp_recv_all(i64 %t4951, i64 65536)
    %raw_v4953 = alloca i64
    store i64 %t4952, i64* %raw_v4953
    %t4954 = load i64, i64* %fd_v4922
    call void @freak_llvm_tcp_close(i64 %t4954)
    %t4955 = load i64, i64* %raw_v4953
    %t4956 = call i64 @freak_http_split_response(i64 %t4955)
    ret i64 %t4956
    ret i64 0
}

define i64 @freak_http_post(i64 %arg_host, i64 %arg_path, i64 %arg_port, i64 %arg_content_type, i64 %arg_body) {
entry:
    %host = alloca i64
    store i64 %arg_host, i64* %host
    %path = alloca i64
    store i64 %arg_path, i64* %path
    %port = alloca i64
    store i64 %arg_port, i64* %port
    %content_type = alloca i64
    store i64 %arg_content_type, i64* %content_type
    %body = alloca i64
    store i64 %arg_body, i64* %body
    call void @freak_http_init()
    %t4957 = load i64, i64* %host
    %t4958 = load i64, i64* %port
    %t4959 = call i64 @freak_llvm_tcp_connect(i64 %t4957, i64 %t4958)
    %fd_v4960 = alloca i64
    store i64 %t4959, i64* %fd_v4960
    %t4961 = load i64, i64* %fd_v4960
    %t4963 = icmp slt i64 %t4961, 0
    %t4962 = zext i1 %t4963 to i64
    %t4967 = icmp ne i64 %t4962, 0
    br i1 %t4967, label %if.then.4964, label %if.end.4966
if.then.4964:
    %t4968 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.316, i64 0, i64 0
    %t4969 = ptrtoint i8* %t4968 to i64
    %t4970 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.317, i64 0, i64 0
    %t4971 = ptrtoint i8* %t4970 to i64
    %t4972 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4969, i64 %t4971)
    ret i64 %t4972
    br label %if.end.4966
if.end.4966:
    %t4973 = load i64, i64* %body
    %t4974 = call i64 @freak_llvm_word_length(i64 %t4973)
    %t4975 = call i64 @freak_llvm_word_from_int(i64 %t4974)
    %body_len_v4976 = alloca i64
    store i64 %t4975, i64* %body_len_v4976
    %t4977 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.318, i64 0, i64 0
    %t4978 = ptrtoint i8* %t4977 to i64
    %t4979 = load i64, i64* %path
    %t4980 = call i64 @freak_llvm_word_concat(i64 %t4978, i64 %t4979)
    %t4981 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.319, i64 0, i64 0
    %t4982 = ptrtoint i8* %t4981 to i64
    %t4983 = call i64 @freak_llvm_word_concat(i64 %t4980, i64 %t4982)
    %t4984 = load i64, i64* %host
    %t4985 = call i64 @freak_llvm_word_concat(i64 %t4983, i64 %t4984)
    %t4986 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.320, i64 0, i64 0
    %t4987 = ptrtoint i8* %t4986 to i64
    %t4988 = call i64 @freak_llvm_word_concat(i64 %t4985, i64 %t4987)
    %t4989 = load i64, i64* %content_type
    %t4990 = call i64 @freak_llvm_word_concat(i64 %t4988, i64 %t4989)
    %t4991 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.321, i64 0, i64 0
    %t4992 = ptrtoint i8* %t4991 to i64
    %t4993 = call i64 @freak_llvm_word_concat(i64 %t4990, i64 %t4992)
    %t4994 = load i64, i64* %body_len_v4976
    %t4995 = call i64 @freak_llvm_word_concat(i64 %t4993, i64 %t4994)
    %t4996 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.322, i64 0, i64 0
    %t4997 = ptrtoint i8* %t4996 to i64
    %t4998 = call i64 @freak_llvm_word_concat(i64 %t4995, i64 %t4997)
    %t4999 = load i64, i64* %body
    %t5000 = call i64 @freak_llvm_word_concat(i64 %t4998, i64 %t4999)
    %req_v5001 = alloca i64
    store i64 %t5000, i64* %req_v5001
    %t5002 = load i64, i64* %fd_v4960
    %t5003 = load i64, i64* %req_v5001
    %t5004 = call i64 @freak_llvm_tcp_send(i64 %t5002, i64 %t5003)
    %t5005 = load i64, i64* %fd_v4960
    %t5006 = call i64 @freak_llvm_tcp_recv_all(i64 %t5005, i64 65536)
    %raw_v5007 = alloca i64
    store i64 %t5006, i64* %raw_v5007
    %t5008 = load i64, i64* %fd_v4960
    call void @freak_llvm_tcp_close(i64 %t5008)
    %t5009 = load i64, i64* %raw_v5007
    %t5010 = call i64 @freak_http_split_response(i64 %t5009)
    ret i64 %t5010
    ret i64 0
}

define i64 @freak_http_put(i64 %arg_host, i64 %arg_path, i64 %arg_port, i64 %arg_content_type, i64 %arg_body) {
entry:
    %host = alloca i64
    store i64 %arg_host, i64* %host
    %path = alloca i64
    store i64 %arg_path, i64* %path
    %port = alloca i64
    store i64 %arg_port, i64* %port
    %content_type = alloca i64
    store i64 %arg_content_type, i64* %content_type
    %body = alloca i64
    store i64 %arg_body, i64* %body
    call void @freak_http_init()
    %t5011 = load i64, i64* %host
    %t5012 = load i64, i64* %port
    %t5013 = call i64 @freak_llvm_tcp_connect(i64 %t5011, i64 %t5012)
    %fd_v5014 = alloca i64
    store i64 %t5013, i64* %fd_v5014
    %t5015 = load i64, i64* %fd_v5014
    %t5017 = icmp slt i64 %t5015, 0
    %t5016 = zext i1 %t5017 to i64
    %t5021 = icmp ne i64 %t5016, 0
    br i1 %t5021, label %if.then.5018, label %if.end.5020
if.then.5018:
    %t5022 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.323, i64 0, i64 0
    %t5023 = ptrtoint i8* %t5022 to i64
    %t5024 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.324, i64 0, i64 0
    %t5025 = ptrtoint i8* %t5024 to i64
    %t5026 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5023, i64 %t5025)
    ret i64 %t5026
    br label %if.end.5020
if.end.5020:
    %t5027 = load i64, i64* %body
    %t5028 = call i64 @freak_llvm_word_length(i64 %t5027)
    %t5029 = call i64 @freak_llvm_word_from_int(i64 %t5028)
    %body_len_v5030 = alloca i64
    store i64 %t5029, i64* %body_len_v5030
    %t5031 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.325, i64 0, i64 0
    %t5032 = ptrtoint i8* %t5031 to i64
    %t5033 = load i64, i64* %path
    %t5034 = call i64 @freak_llvm_word_concat(i64 %t5032, i64 %t5033)
    %t5035 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.326, i64 0, i64 0
    %t5036 = ptrtoint i8* %t5035 to i64
    %t5037 = call i64 @freak_llvm_word_concat(i64 %t5034, i64 %t5036)
    %t5038 = load i64, i64* %host
    %t5039 = call i64 @freak_llvm_word_concat(i64 %t5037, i64 %t5038)
    %t5040 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.327, i64 0, i64 0
    %t5041 = ptrtoint i8* %t5040 to i64
    %t5042 = call i64 @freak_llvm_word_concat(i64 %t5039, i64 %t5041)
    %t5043 = load i64, i64* %content_type
    %t5044 = call i64 @freak_llvm_word_concat(i64 %t5042, i64 %t5043)
    %t5045 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.328, i64 0, i64 0
    %t5046 = ptrtoint i8* %t5045 to i64
    %t5047 = call i64 @freak_llvm_word_concat(i64 %t5044, i64 %t5046)
    %t5048 = load i64, i64* %body_len_v5030
    %t5049 = call i64 @freak_llvm_word_concat(i64 %t5047, i64 %t5048)
    %t5050 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.329, i64 0, i64 0
    %t5051 = ptrtoint i8* %t5050 to i64
    %t5052 = call i64 @freak_llvm_word_concat(i64 %t5049, i64 %t5051)
    %t5053 = load i64, i64* %body
    %t5054 = call i64 @freak_llvm_word_concat(i64 %t5052, i64 %t5053)
    %req_v5055 = alloca i64
    store i64 %t5054, i64* %req_v5055
    %t5056 = load i64, i64* %fd_v5014
    %t5057 = load i64, i64* %req_v5055
    %t5058 = call i64 @freak_llvm_tcp_send(i64 %t5056, i64 %t5057)
    %t5059 = load i64, i64* %fd_v5014
    %t5060 = call i64 @freak_llvm_tcp_recv_all(i64 %t5059, i64 65536)
    %raw_v5061 = alloca i64
    store i64 %t5060, i64* %raw_v5061
    %t5062 = load i64, i64* %fd_v5014
    call void @freak_llvm_tcp_close(i64 %t5062)
    %t5063 = load i64, i64* %raw_v5061
    %t5064 = call i64 @freak_http_split_response(i64 %t5063)
    ret i64 %t5064
    ret i64 0
}

define i64 @freak_http_delete(i64 %arg_host, i64 %arg_path, i64 %arg_port) {
entry:
    %host = alloca i64
    store i64 %arg_host, i64* %host
    %path = alloca i64
    store i64 %arg_path, i64* %path
    %port = alloca i64
    store i64 %arg_port, i64* %port
    call void @freak_http_init()
    %t5065 = load i64, i64* %host
    %t5066 = load i64, i64* %port
    %t5067 = call i64 @freak_llvm_tcp_connect(i64 %t5065, i64 %t5066)
    %fd_v5068 = alloca i64
    store i64 %t5067, i64* %fd_v5068
    %t5069 = load i64, i64* %fd_v5068
    %t5071 = icmp slt i64 %t5069, 0
    %t5070 = zext i1 %t5071 to i64
    %t5075 = icmp ne i64 %t5070, 0
    br i1 %t5075, label %if.then.5072, label %if.end.5074
if.then.5072:
    %t5076 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.330, i64 0, i64 0
    %t5077 = ptrtoint i8* %t5076 to i64
    %t5078 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.331, i64 0, i64 0
    %t5079 = ptrtoint i8* %t5078 to i64
    %t5080 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5077, i64 %t5079)
    ret i64 %t5080
    br label %if.end.5074
if.end.5074:
    %t5081 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.332, i64 0, i64 0
    %t5082 = ptrtoint i8* %t5081 to i64
    %t5083 = load i64, i64* %path
    %t5084 = call i64 @freak_llvm_word_concat(i64 %t5082, i64 %t5083)
    %t5085 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.333, i64 0, i64 0
    %t5086 = ptrtoint i8* %t5085 to i64
    %t5087 = call i64 @freak_llvm_word_concat(i64 %t5084, i64 %t5086)
    %t5088 = load i64, i64* %host
    %t5089 = call i64 @freak_llvm_word_concat(i64 %t5087, i64 %t5088)
    %t5090 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.334, i64 0, i64 0
    %t5091 = ptrtoint i8* %t5090 to i64
    %t5092 = call i64 @freak_llvm_word_concat(i64 %t5089, i64 %t5091)
    %req_v5093 = alloca i64
    store i64 %t5092, i64* %req_v5093
    %t5094 = load i64, i64* %fd_v5068
    %t5095 = load i64, i64* %req_v5093
    %t5096 = call i64 @freak_llvm_tcp_send(i64 %t5094, i64 %t5095)
    %t5097 = load i64, i64* %fd_v5068
    %t5098 = call i64 @freak_llvm_tcp_recv_all(i64 %t5097, i64 65536)
    %raw_v5099 = alloca i64
    store i64 %t5098, i64* %raw_v5099
    %t5100 = load i64, i64* %fd_v5068
    call void @freak_llvm_tcp_close(i64 %t5100)
    %t5101 = load i64, i64* %raw_v5099
    %t5102 = call i64 @freak_http_split_response(i64 %t5101)
    ret i64 %t5102
    ret i64 0
}

define void @freak_main() {
entry:
    store i64 0, i64* @g_json_types
    store i64 0, i64* @g_json_vals
    store i64 0, i64* @g_json_children
    store i64 0, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 0, i64* @g_json_inited
    %t5103 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.335, i64 0, i64 0
    %t5104 = ptrtoint i8* %t5103 to i64
    store i64 %t5104, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    store i64 0, i64* @g_json_len
    store i64 0, i64* @g_http_resp_statuses
    store i64 0, i64* @g_http_resp_bodies
    store i64 0, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 0, i64* @g_http_inited
    store i64 10, i64* @g_a
    store i64 3, i64* @g_b
    %t5105 = load i64, i64* @g_a
    %t5106 = load i64, i64* @g_b
    %t5107 = add i64 %t5105, %t5106
    %t5108 = call i64 @freak_llvm_word_from_int(i64 %t5107)
    call void @freak_llvm_say(i64 %t5108)
    %t5109 = load i64, i64* @g_a
    %t5110 = load i64, i64* @g_b
    %t5111 = sub i64 %t5109, %t5110
    %t5112 = call i64 @freak_llvm_word_from_int(i64 %t5111)
    call void @freak_llvm_say(i64 %t5112)
    %t5113 = load i64, i64* @g_a
    %t5114 = load i64, i64* @g_b
    %t5115 = mul i64 %t5113, %t5114
    %t5116 = call i64 @freak_llvm_word_from_int(i64 %t5115)
    call void @freak_llvm_say(i64 %t5116)
    %t5117 = load i64, i64* @g_a
    %t5118 = load i64, i64* @g_b
    %t5119 = sdiv i64 %t5117, %t5118
    %t5120 = call i64 @freak_llvm_word_from_int(i64 %t5119)
    call void @freak_llvm_say(i64 %t5120)
    %t5121 = load i64, i64* @g_a
    %t5122 = load i64, i64* @g_b
    %t5123 = srem i64 %t5121, %t5122
    %t5124 = call i64 @freak_llvm_word_from_int(i64 %t5123)
    call void @freak_llvm_say(i64 %t5124)
    %t5125 = sub i64 0, 7
    store i64 %t5125, i64* @g_neg
    %t5126 = load i64, i64* @g_neg
    %t5127 = call i64 @freak_llvm_word_from_int(i64 %t5126)
    call void @freak_llvm_say(i64 %t5127)
    ret void
}

define i32 @main(i32 %argc, i8** %argv) {
entry:
    %argc_ext = sext i32 %argc to i64
    %argv_ptr = ptrtoint i8** %argv to i64
    call void @freak_llvm_setup_args(i64 %argc_ext, i64 %argv_ptr)
    call void @freak_main()
    ret i32 0
}

; String Literals
@.str.0 = private unnamed_addr constant [3 x i8] c"rb\00", align 1
@.str.1 = private unnamed_addr constant [24 x i8] c"FREAK: cannot read file\00", align 1
@.str.2 = private unnamed_addr constant [3 x i8] c"wb\00", align 1
@.str.3 = private unnamed_addr constant [25 x i8] c"FREAK: cannot write file\00", align 1
@.str.4 = private unnamed_addr constant [3 x i8] c"ab\00", align 1
@.str.5 = private unnamed_addr constant [26 x i8] c"FREAK: cannot append file\00", align 1
@.str.6 = private unnamed_addr constant [3 x i8] c"rb\00", align 1
@.str.7 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.8 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.9 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.10 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.11 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.12 = private unnamed_addr constant [2 x i8] c"|\00", align 1
@.str.13 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.14 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.15 = private unnamed_addr constant [2 x i8] c"|\00", align 1
@.str.16 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.17 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.18 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.19 = private unnamed_addr constant [2 x i8] c"|\00", align 1
@.str.20 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.21 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.22 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.23 = private unnamed_addr constant [2 x i8] c"2\00", align 1
@.str.24 = private unnamed_addr constant [2 x i8] c"3\00", align 1
@.str.25 = private unnamed_addr constant [2 x i8] c"4\00", align 1
@.str.26 = private unnamed_addr constant [2 x i8] c"5\00", align 1
@.str.27 = private unnamed_addr constant [2 x i8] c"6\00", align 1
@.str.28 = private unnamed_addr constant [2 x i8] c"7\00", align 1
@.str.29 = private unnamed_addr constant [2 x i8] c"8\00", align 1
@.str.30 = private unnamed_addr constant [2 x i8] c"9\00", align 1
@.str.31 = private unnamed_addr constant [2 x i8] c"a\00", align 1
@.str.32 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.33 = private unnamed_addr constant [2 x i8] c"c\00", align 1
@.str.34 = private unnamed_addr constant [2 x i8] c"d\00", align 1
@.str.35 = private unnamed_addr constant [2 x i8] c"e\00", align 1
@.str.36 = private unnamed_addr constant [2 x i8] c"f\00", align 1
@.str.37 = private unnamed_addr constant [2 x i8] c"g\00", align 1
@.str.38 = private unnamed_addr constant [2 x i8] c"h\00", align 1
@.str.39 = private unnamed_addr constant [2 x i8] c"i\00", align 1
@.str.40 = private unnamed_addr constant [2 x i8] c"j\00", align 1
@.str.41 = private unnamed_addr constant [2 x i8] c"k\00", align 1
@.str.42 = private unnamed_addr constant [2 x i8] c"l\00", align 1
@.str.43 = private unnamed_addr constant [2 x i8] c"m\00", align 1
@.str.44 = private unnamed_addr constant [2 x i8] c"n\00", align 1
@.str.45 = private unnamed_addr constant [2 x i8] c"o\00", align 1
@.str.46 = private unnamed_addr constant [2 x i8] c"p\00", align 1
@.str.47 = private unnamed_addr constant [2 x i8] c"q\00", align 1
@.str.48 = private unnamed_addr constant [2 x i8] c"r\00", align 1
@.str.49 = private unnamed_addr constant [2 x i8] c"s\00", align 1
@.str.50 = private unnamed_addr constant [2 x i8] c"t\00", align 1
@.str.51 = private unnamed_addr constant [2 x i8] c"u\00", align 1
@.str.52 = private unnamed_addr constant [2 x i8] c"v\00", align 1
@.str.53 = private unnamed_addr constant [2 x i8] c"w\00", align 1
@.str.54 = private unnamed_addr constant [2 x i8] c"x\00", align 1
@.str.55 = private unnamed_addr constant [2 x i8] c"y\00", align 1
@.str.56 = private unnamed_addr constant [2 x i8] c"z\00", align 1
@.str.57 = private unnamed_addr constant [2 x i8] c"A\00", align 1
@.str.58 = private unnamed_addr constant [2 x i8] c"B\00", align 1
@.str.59 = private unnamed_addr constant [2 x i8] c"C\00", align 1
@.str.60 = private unnamed_addr constant [2 x i8] c"D\00", align 1
@.str.61 = private unnamed_addr constant [2 x i8] c"E\00", align 1
@.str.62 = private unnamed_addr constant [2 x i8] c"F\00", align 1
@.str.63 = private unnamed_addr constant [2 x i8] c"G\00", align 1
@.str.64 = private unnamed_addr constant [2 x i8] c"H\00", align 1
@.str.65 = private unnamed_addr constant [2 x i8] c"I\00", align 1
@.str.66 = private unnamed_addr constant [2 x i8] c"J\00", align 1
@.str.67 = private unnamed_addr constant [2 x i8] c"K\00", align 1
@.str.68 = private unnamed_addr constant [2 x i8] c"L\00", align 1
@.str.69 = private unnamed_addr constant [2 x i8] c"M\00", align 1
@.str.70 = private unnamed_addr constant [2 x i8] c"N\00", align 1
@.str.71 = private unnamed_addr constant [2 x i8] c"O\00", align 1
@.str.72 = private unnamed_addr constant [2 x i8] c"P\00", align 1
@.str.73 = private unnamed_addr constant [2 x i8] c"Q\00", align 1
@.str.74 = private unnamed_addr constant [2 x i8] c"R\00", align 1
@.str.75 = private unnamed_addr constant [2 x i8] c"S\00", align 1
@.str.76 = private unnamed_addr constant [2 x i8] c"T\00", align 1
@.str.77 = private unnamed_addr constant [2 x i8] c"U\00", align 1
@.str.78 = private unnamed_addr constant [2 x i8] c"V\00", align 1
@.str.79 = private unnamed_addr constant [2 x i8] c"W\00", align 1
@.str.80 = private unnamed_addr constant [2 x i8] c"X\00", align 1
@.str.81 = private unnamed_addr constant [2 x i8] c"Y\00", align 1
@.str.82 = private unnamed_addr constant [2 x i8] c"Z\00", align 1
@.str.83 = private unnamed_addr constant [2 x i8] c" \00", align 1
@.str.84 = private unnamed_addr constant [2 x i8] c"\09\00", align 1
@.str.85 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.86 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.87 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.88 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.89 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.90 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.91 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.92 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.93 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.94 = private unnamed_addr constant [17 x i8] c"0123456789abcdef\00", align 1
@.str.95 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.96 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.97 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.98 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.99 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.100 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.101 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.102 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.103 = private unnamed_addr constant [9 x i8] c"01234567\00", align 1
@.str.104 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.105 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.106 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.107 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.108 = private unnamed_addr constant [2 x i8] c"2\00", align 1
@.str.109 = private unnamed_addr constant [2 x i8] c"3\00", align 1
@.str.110 = private unnamed_addr constant [2 x i8] c"4\00", align 1
@.str.111 = private unnamed_addr constant [2 x i8] c"5\00", align 1
@.str.112 = private unnamed_addr constant [2 x i8] c"6\00", align 1
@.str.113 = private unnamed_addr constant [2 x i8] c"7\00", align 1
@.str.114 = private unnamed_addr constant [2 x i8] c"8\00", align 1
@.str.115 = private unnamed_addr constant [2 x i8] c"9\00", align 1
@.str.116 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.117 = private unnamed_addr constant [5 x i8] c"true\00", align 1
@.str.118 = private unnamed_addr constant [6 x i8] c"false\00", align 1
@.str.119 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.120 = private unnamed_addr constant [5 x i8] c"true\00", align 1
@.str.121 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.122 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.123 = private unnamed_addr constant [2 x i8] c" \00", align 1
@.str.124 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.125 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.126 = private unnamed_addr constant [2 x i8] c"\09\00", align 1
@.str.127 = private unnamed_addr constant [29 x i8] c"JSON parse error: expected '\00", align 1
@.str.128 = private unnamed_addr constant [8 x i8] c"' got '\00", align 1
@.str.129 = private unnamed_addr constant [2 x i8] c"'\00", align 1
@.str.130 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.131 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.132 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.133 = private unnamed_addr constant [2 x i8] c"\5C\00", align 1
@.str.134 = private unnamed_addr constant [2 x i8] c"n\00", align 1
@.str.135 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.136 = private unnamed_addr constant [2 x i8] c"t\00", align 1
@.str.137 = private unnamed_addr constant [2 x i8] c"\09\00", align 1
@.str.138 = private unnamed_addr constant [2 x i8] c"r\00", align 1
@.str.139 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.140 = private unnamed_addr constant [2 x i8] c"\5C\00", align 1
@.str.141 = private unnamed_addr constant [2 x i8] c"\5C\00", align 1
@.str.142 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.143 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.144 = private unnamed_addr constant [2 x i8] c"/\00", align 1
@.str.145 = private unnamed_addr constant [2 x i8] c"/\00", align 1
@.str.146 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.147 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.148 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.149 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.150 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.151 = private unnamed_addr constant [2 x i8] c"2\00", align 1
@.str.152 = private unnamed_addr constant [2 x i8] c"3\00", align 1
@.str.153 = private unnamed_addr constant [2 x i8] c"4\00", align 1
@.str.154 = private unnamed_addr constant [2 x i8] c"5\00", align 1
@.str.155 = private unnamed_addr constant [2 x i8] c"6\00", align 1
@.str.156 = private unnamed_addr constant [2 x i8] c"7\00", align 1
@.str.157 = private unnamed_addr constant [2 x i8] c"8\00", align 1
@.str.158 = private unnamed_addr constant [2 x i8] c"9\00", align 1
@.str.159 = private unnamed_addr constant [2 x i8] c".\00", align 1
@.str.160 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.161 = private unnamed_addr constant [2 x i8] c"s\00", align 1
@.str.162 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.163 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.164 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.165 = private unnamed_addr constant [2 x i8] c"2\00", align 1
@.str.166 = private unnamed_addr constant [2 x i8] c"3\00", align 1
@.str.167 = private unnamed_addr constant [2 x i8] c"4\00", align 1
@.str.168 = private unnamed_addr constant [2 x i8] c"5\00", align 1
@.str.169 = private unnamed_addr constant [2 x i8] c"6\00", align 1
@.str.170 = private unnamed_addr constant [2 x i8] c"7\00", align 1
@.str.171 = private unnamed_addr constant [2 x i8] c"8\00", align 1
@.str.172 = private unnamed_addr constant [2 x i8] c"9\00", align 1
@.str.173 = private unnamed_addr constant [2 x i8] c"n\00", align 1
@.str.174 = private unnamed_addr constant [2 x i8] c"t\00", align 1
@.str.175 = private unnamed_addr constant [5 x i8] c"true\00", align 1
@.str.176 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.177 = private unnamed_addr constant [5 x i8] c"true\00", align 1
@.str.178 = private unnamed_addr constant [2 x i8] c"f\00", align 1
@.str.179 = private unnamed_addr constant [6 x i8] c"false\00", align 1
@.str.180 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.181 = private unnamed_addr constant [6 x i8] c"false\00", align 1
@.str.182 = private unnamed_addr constant [2 x i8] c"n\00", align 1
@.str.183 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.184 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.185 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.186 = private unnamed_addr constant [2 x i8] c"[\00", align 1
@.str.187 = private unnamed_addr constant [2 x i8] c"a\00", align 1
@.str.188 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.189 = private unnamed_addr constant [2 x i8] c"]\00", align 1
@.str.190 = private unnamed_addr constant [2 x i8] c",\00", align 1
@.str.191 = private unnamed_addr constant [2 x i8] c"]\00", align 1
@.str.192 = private unnamed_addr constant [2 x i8] c"{\00", align 1
@.str.193 = private unnamed_addr constant [2 x i8] c"o\00", align 1
@.str.194 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.195 = private unnamed_addr constant [2 x i8] c"}\00", align 1
@.str.196 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.197 = private unnamed_addr constant [2 x i8] c",\00", align 1
@.str.198 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.199 = private unnamed_addr constant [2 x i8] c"}\00", align 1
@.str.200 = private unnamed_addr constant [31 x i8] c"JSON parse error: unexpected '\00", align 1
@.str.201 = private unnamed_addr constant [2 x i8] c"'\00", align 1
@.str.202 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.203 = private unnamed_addr constant [2 x i8] c"s\00", align 1
@.str.204 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.205 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.206 = private unnamed_addr constant [2 x i8] c"n\00", align 1
@.str.207 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.208 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.209 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.210 = private unnamed_addr constant [2 x i8] c"a\00", align 1
@.str.211 = private unnamed_addr constant [2 x i8] c"[\00", align 1
@.str.212 = private unnamed_addr constant [2 x i8] c",\00", align 1
@.str.213 = private unnamed_addr constant [2 x i8] c"]\00", align 1
@.str.214 = private unnamed_addr constant [2 x i8] c"o\00", align 1
@.str.215 = private unnamed_addr constant [2 x i8] c"{\00", align 1
@.str.216 = private unnamed_addr constant [2 x i8] c",\00", align 1
@.str.217 = private unnamed_addr constant [2 x i8] c"\22\00", align 1
@.str.218 = private unnamed_addr constant [3 x i8] c"\22:\00", align 1
@.str.219 = private unnamed_addr constant [2 x i8] c"}\00", align 1
@.str.220 = private unnamed_addr constant [5 x i8] c"null\00", align 1
@.str.221 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.222 = private unnamed_addr constant [2 x i8] c".\00", align 1
@.str.223 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.224 = private unnamed_addr constant [2 x i8] c"+\00", align 1
@.str.225 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.226 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.227 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.228 = private unnamed_addr constant [2 x i8] c"+\00", align 1
@.str.229 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.230 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.231 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.232 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.233 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.234 = private unnamed_addr constant [2 x i8] c"v\00", align 1
@.str.235 = private unnamed_addr constant [2 x i8] c"V\00", align 1
@.str.236 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.237 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.238 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.239 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.240 = private unnamed_addr constant [2 x i8] c"+\00", align 1
@.str.241 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.242 = private unnamed_addr constant [2 x i8] c"+\00", align 1
@.str.243 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.244 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.245 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.246 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.247 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.248 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.249 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.250 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.251 = private unnamed_addr constant [2 x i8] c".\00", align 1
@.str.252 = private unnamed_addr constant [2 x i8] c".\00", align 1
@.str.253 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.254 = private unnamed_addr constant [2 x i8] c"-\00", align 1
@.str.255 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.256 = private unnamed_addr constant [2 x i8] c"+\00", align 1
@.str.257 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.258 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.259 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.260 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.261 = private unnamed_addr constant [2 x i8] c"a\00", align 1
@.str.262 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.263 = private unnamed_addr constant [2 x i8] c"b\00", align 1
@.str.264 = private unnamed_addr constant [2 x i8] c"a\00", align 1
@.str.265 = private unnamed_addr constant [7 x i8] c":0:0::\00", align 1
@.str.266 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.267 = private unnamed_addr constant [5 x i8] c":0::\00", align 1
@.str.268 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.269 = private unnamed_addr constant [2 x i8] c":\00", align 1
@.str.270 = private unnamed_addr constant [3 x i8] c"::\00", align 1
@.str.271 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.272 = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.273 = private unnamed_addr constant [2 x i8] c"1\00", align 1
@.str.274 = private unnamed_addr constant [2 x i8] c"2\00", align 1
@.str.275 = private unnamed_addr constant [2 x i8] c"3\00", align 1
@.str.276 = private unnamed_addr constant [2 x i8] c"4\00", align 1
@.str.277 = private unnamed_addr constant [2 x i8] c"5\00", align 1
@.str.278 = private unnamed_addr constant [2 x i8] c"6\00", align 1
@.str.279 = private unnamed_addr constant [2 x i8] c"7\00", align 1
@.str.280 = private unnamed_addr constant [2 x i8] c"8\00", align 1
@.str.281 = private unnamed_addr constant [2 x i8] c"9\00", align 1
@.str.282 = private unnamed_addr constant [2 x i8] c"*\00", align 1
@.str.283 = private unnamed_addr constant [7 x i8] c"latest\00", align 1
@.str.284 = private unnamed_addr constant [2 x i8] c"^\00", align 1
@.str.285 = private unnamed_addr constant [2 x i8] c"~\00", align 1
@.str.286 = private unnamed_addr constant [3 x i8] c">=\00", align 1
@.str.287 = private unnamed_addr constant [3 x i8] c"<=\00", align 1
@.str.288 = private unnamed_addr constant [2 x i8] c">\00", align 1
@.str.289 = private unnamed_addr constant [2 x i8] c"<\00", align 1
@.str.290 = private unnamed_addr constant [2 x i8] c"=\00", align 1
@.str.291 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.292 = private unnamed_addr constant [2 x i8] c" \00", align 1
@.str.293 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.294 = private unnamed_addr constant [2 x i8] c" \00", align 1
@.str.295 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.296 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.297 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.298 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.299 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.300 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.301 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.302 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.303 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.304 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.305 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.306 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.307 = private unnamed_addr constant [2 x i8] c"\0D\00", align 1
@.str.308 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.309 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.310 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.311 = private unnamed_addr constant [18 x i8] c"Connection failed\00", align 1
@.str.312 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.313 = private unnamed_addr constant [5 x i8] c"GET \00", align 1
@.str.314 = private unnamed_addr constant [18 x i8] c" HTTP/1.1\0D\0AHost: \00", align 1
@.str.315 = private unnamed_addr constant [47 x i8] c"\0D\0AConnection: close\0D\0AUser-Agent: FREAK/0.8\0D\0A\0D\0A\00", align 1
@.str.316 = private unnamed_addr constant [18 x i8] c"Connection failed\00", align 1
@.str.317 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.318 = private unnamed_addr constant [6 x i8] c"POST \00", align 1
@.str.319 = private unnamed_addr constant [18 x i8] c" HTTP/1.1\0D\0AHost: \00", align 1
@.str.320 = private unnamed_addr constant [59 x i8] c"\0D\0AConnection: close\0D\0AUser-Agent: FREAK/0.8\0D\0AContent-Type: \00", align 1
@.str.321 = private unnamed_addr constant [19 x i8] c"\0D\0AContent-Length: \00", align 1
@.str.322 = private unnamed_addr constant [5 x i8] c"\0D\0A\0D\0A\00", align 1
@.str.323 = private unnamed_addr constant [18 x i8] c"Connection failed\00", align 1
@.str.324 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.325 = private unnamed_addr constant [5 x i8] c"PUT \00", align 1
@.str.326 = private unnamed_addr constant [18 x i8] c" HTTP/1.1\0D\0AHost: \00", align 1
@.str.327 = private unnamed_addr constant [59 x i8] c"\0D\0AConnection: close\0D\0AUser-Agent: FREAK/0.8\0D\0AContent-Type: \00", align 1
@.str.328 = private unnamed_addr constant [19 x i8] c"\0D\0AContent-Length: \00", align 1
@.str.329 = private unnamed_addr constant [5 x i8] c"\0D\0A\0D\0A\00", align 1
@.str.330 = private unnamed_addr constant [18 x i8] c"Connection failed\00", align 1
@.str.331 = private unnamed_addr constant [1 x i8] c"\00", align 1
@.str.332 = private unnamed_addr constant [8 x i8] c"DELETE \00", align 1
@.str.333 = private unnamed_addr constant [18 x i8] c" HTTP/1.1\0D\0AHost: \00", align 1
@.str.334 = private unnamed_addr constant [47 x i8] c"\0D\0AConnection: close\0D\0AUser-Agent: FREAK/0.8\0D\0A\0D\0A\00", align 1
@.str.335 = private unnamed_addr constant [1 x i8] c"\00", align 1

