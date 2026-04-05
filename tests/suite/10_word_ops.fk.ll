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
@g_s = global i64 0
@g_a = global i64 0
@g_b = global i64 0

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
    %t339 = load i64, i64* @g_s
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
    %t346 = load i64, i64* @g_s
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
    %t357 = load i64, i64* @g_s
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
    %t367 = load i64, i64* @g_s
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
    %t369 = load i64, i64* @g_s
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
    %t380 = load i64, i64* @g_s
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
    %t389 = load i64, i64* @g_s
    %t390 = load i64, i64* %padding_v388
    %t391 = call i64 @freak_llvm_word_concat(i64 %t389, i64 %t390)
    ret i64 %t391
    ret i64 0
}

define i64 @freak_string_reverse(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t392 = load i64, i64* @g_s
    %t393 = call i64 @freak_llvm_word_length(i64 %t392)
    %slen_v394 = alloca i64
    store i64 %t393, i64* %slen_v394
    %t395 = load i64, i64* %slen_v394
    %t397 = icmp sle i64 %t395, 1
    %t396 = zext i1 %t397 to i64
    %t401 = icmp ne i64 %t396, 0
    br i1 %t401, label %if.then.398, label %if.end.400
if.then.398:
    %t402 = load i64, i64* @g_s
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
    %t418 = load i64, i64* @g_s
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
    %t507 = load i64, i64* @g_s
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
    %t520 = load i64, i64* @g_s
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
    %t561 = load i64, i64* @g_s
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
    %t604 = load i64, i64* @g_s
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
    %t1228 = load i64, i64* @g_s
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
    %t1251 = load i64, i64* @g_s
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
    %t1266 = load i64, i64* @g_s
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
    %t1293 = load i64, i64* @g_s
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
    %t1315 = load i64, i64* @g_s
    %t1316 = call i64 @freak_llvm_word_length(i64 %t1315)
    %slen_v1317 = alloca i64
    store i64 %t1316, i64* %slen_v1317
    %t1318 = load i64, i64* %slen_v1317
    %t1320 = icmp eq i64 %t1318, 0
    %t1319 = zext i1 %t1320 to i64
    %t1324 = icmp ne i64 %t1319, 0
    br i1 %t1324, label %if.then.1321, label %if.end.1323
if.then.1321:
    %t1325 = load i64, i64* @g_s
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
    %t1335 = load i64, i64* @g_s
    %t1337 = load i64, i64* %tstart_v1326
    %t1336 = call i64 @freak_llvm_word_char_at(i64 %t1335, i64 %t1337)
    %t1338 = call i64 @freak_is_whitespace(i64 %t1336)
    %t1340 = icmp eq i64 %t1338, 0
    %t1339 = zext i1 %t1340 to i64
    %t1344 = icmp ne i64 %t1339, 0
    br i1 %t1344, label %if.then.1341, label %if.end.1343
if.then.1341:
    %t1345 = load i64, i64* @g_s
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
    %t1352 = load i64, i64* @g_s
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
    %t1364 = load i64, i64* @g_s
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
    %t1388 = load i64, i64* @g_s
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
    %t1399 = load i64, i64* @g_s
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
    %t1412 = load i64, i64* @g_s
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
    %t1450 = load i64, i64* @g_s
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
    %t1479 = load i64, i64* @g_s
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
    %t1486 = load i64, i64* @g_s
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
    %t1533 = load i64, i64* @g_s
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
    %t1540 = load i64, i64* @g_s
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
    %t1591 = load i64, i64* @g_s
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
    %neg_v1631 = alloca i64
    store i64 0, i64* %neg_v1631
    %t1632 = load i64, i64* %n
    %val_v1633 = alloca i64
    store i64 %t1632, i64* %val_v1633
    %t1634 = load i64, i64* %val_v1633
    %t1636 = icmp slt i64 %t1634, 0
    %t1635 = zext i1 %t1636 to i64
    %t1640 = icmp ne i64 %t1635, 0
    br i1 %t1640, label %if.then.1637, label %if.end.1639
if.then.1637:
    store i64 1, i64* %neg_v1631
    %t1641 = load i64, i64* %val_v1633
    %t1642 = sub i64 0, %t1641
    store i64 %t1642, i64* %val_v1633
    br label %if.end.1639
if.end.1639:
    %t1643 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.95, i64 0, i64 0
    %t1644 = ptrtoint i8* %t1643 to i64
    %hex_out_v1645 = alloca i64
    store i64 %t1644, i64* %hex_out_v1645
    br label %loop.cond.1646
loop.cond.1646:
    %t1649 = load i64, i64* %val_v1633
    %t1651 = icmp sle i64 %t1649, 0
    %t1650 = zext i1 %t1651 to i64
    %t1652 = icmp eq i64 %t1650, 0
    br i1 %t1652, label %loop.body.1647, label %loop.end.1648
loop.body.1647:
    %t1653 = load i64, i64* %val_v1633
    %t1654 = load i64, i64* %val_v1633
    %t1655 = sdiv i64 %t1654, 16
    %t1656 = mul i64 %t1655, 16
    %t1657 = sub i64 %t1653, %t1656
    %rem_v1658 = alloca i64
    store i64 %t1657, i64* %rem_v1658
    %t1659 = load i64, i64* %hex_chars_v1630
    %t1661 = load i64, i64* %rem_v1658
    %t1660 = call i64 @freak_llvm_word_char_at(i64 %t1659, i64 %t1661)
    %t1662 = load i64, i64* %hex_out_v1645
    %t1663 = call i64 @freak_llvm_word_concat(i64 %t1660, i64 %t1662)
    store i64 %t1663, i64* %hex_out_v1645
    %t1664 = load i64, i64* %val_v1633
    %t1665 = sdiv i64 %t1664, 16
    store i64 %t1665, i64* %val_v1633
    br label %loop.cond.1646
loop.end.1648:
    %t1666 = load i64, i64* %neg_v1631
    %t1670 = icmp ne i64 %t1666, 0
    br i1 %t1670, label %if.then.1667, label %if.end.1669
if.then.1667:
    %t1671 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.96, i64 0, i64 0
    %t1672 = ptrtoint i8* %t1671 to i64
    %t1673 = load i64, i64* %hex_out_v1645
    %t1674 = call i64 @freak_llvm_word_concat(i64 %t1672, i64 %t1673)
    store i64 %t1674, i64* %hex_out_v1645
    br label %if.end.1669
if.end.1669:
    %t1675 = load i64, i64* %hex_out_v1645
    ret i64 %t1675
    ret i64 0
}

define i64 @freak_int_to_bin(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1676 = load i64, i64* %n
    %t1678 = icmp eq i64 %t1676, 0
    %t1677 = zext i1 %t1678 to i64
    %t1682 = icmp ne i64 %t1677, 0
    br i1 %t1682, label %if.then.1679, label %if.end.1681
if.then.1679:
    %t1683 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.97, i64 0, i64 0
    %t1684 = ptrtoint i8* %t1683 to i64
    ret i64 %t1684
    br label %if.end.1681
if.end.1681:
    %neg_v1685 = alloca i64
    store i64 0, i64* %neg_v1685
    %t1686 = load i64, i64* %n
    %val_v1687 = alloca i64
    store i64 %t1686, i64* %val_v1687
    %t1688 = load i64, i64* %val_v1687
    %t1690 = icmp slt i64 %t1688, 0
    %t1689 = zext i1 %t1690 to i64
    %t1694 = icmp ne i64 %t1689, 0
    br i1 %t1694, label %if.then.1691, label %if.end.1693
if.then.1691:
    store i64 1, i64* %neg_v1685
    %t1695 = load i64, i64* %val_v1687
    %t1696 = sub i64 0, %t1695
    store i64 %t1696, i64* %val_v1687
    br label %if.end.1693
if.end.1693:
    %t1697 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.98, i64 0, i64 0
    %t1698 = ptrtoint i8* %t1697 to i64
    %bin_out_v1699 = alloca i64
    store i64 %t1698, i64* %bin_out_v1699
    br label %loop.cond.1700
loop.cond.1700:
    %t1703 = load i64, i64* %val_v1687
    %t1705 = icmp sle i64 %t1703, 0
    %t1704 = zext i1 %t1705 to i64
    %t1706 = icmp eq i64 %t1704, 0
    br i1 %t1706, label %loop.body.1701, label %loop.end.1702
loop.body.1701:
    %t1707 = load i64, i64* %val_v1687
    %t1708 = load i64, i64* %val_v1687
    %t1709 = sdiv i64 %t1708, 2
    %t1710 = mul i64 %t1709, 2
    %t1711 = sub i64 %t1707, %t1710
    %rem_v1712 = alloca i64
    store i64 %t1711, i64* %rem_v1712
    %t1713 = load i64, i64* %rem_v1712
    %t1715 = icmp eq i64 %t1713, 1
    %t1714 = zext i1 %t1715 to i64
    %t1719 = icmp ne i64 %t1714, 0
    br i1 %t1719, label %if.then.1716, label %if.else.1717
if.then.1716:
    %t1720 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.99, i64 0, i64 0
    %t1721 = ptrtoint i8* %t1720 to i64
    %t1722 = load i64, i64* %bin_out_v1699
    %t1723 = call i64 @freak_llvm_word_concat(i64 %t1721, i64 %t1722)
    store i64 %t1723, i64* %bin_out_v1699
    br label %if.end.1718
if.else.1717:
    %t1724 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.100, i64 0, i64 0
    %t1725 = ptrtoint i8* %t1724 to i64
    %t1726 = load i64, i64* %bin_out_v1699
    %t1727 = call i64 @freak_llvm_word_concat(i64 %t1725, i64 %t1726)
    store i64 %t1727, i64* %bin_out_v1699
    br label %if.end.1718
if.end.1718:
    %t1728 = load i64, i64* %val_v1687
    %t1729 = sdiv i64 %t1728, 2
    store i64 %t1729, i64* %val_v1687
    br label %loop.cond.1700
loop.end.1702:
    %t1730 = load i64, i64* %neg_v1685
    %t1734 = icmp ne i64 %t1730, 0
    br i1 %t1734, label %if.then.1731, label %if.end.1733
if.then.1731:
    %t1735 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.101, i64 0, i64 0
    %t1736 = ptrtoint i8* %t1735 to i64
    %t1737 = load i64, i64* %bin_out_v1699
    %t1738 = call i64 @freak_llvm_word_concat(i64 %t1736, i64 %t1737)
    store i64 %t1738, i64* %bin_out_v1699
    br label %if.end.1733
if.end.1733:
    %t1739 = load i64, i64* %bin_out_v1699
    ret i64 %t1739
    ret i64 0
}

define i64 @freak_int_to_oct(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1740 = load i64, i64* %n
    %t1742 = icmp eq i64 %t1740, 0
    %t1741 = zext i1 %t1742 to i64
    %t1746 = icmp ne i64 %t1741, 0
    br i1 %t1746, label %if.then.1743, label %if.end.1745
if.then.1743:
    %t1747 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.102, i64 0, i64 0
    %t1748 = ptrtoint i8* %t1747 to i64
    ret i64 %t1748
    br label %if.end.1745
if.end.1745:
    %t1749 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.103, i64 0, i64 0
    %t1750 = ptrtoint i8* %t1749 to i64
    %oct_chars_v1751 = alloca i64
    store i64 %t1750, i64* %oct_chars_v1751
    %neg_v1752 = alloca i64
    store i64 0, i64* %neg_v1752
    %t1753 = load i64, i64* %n
    %val_v1754 = alloca i64
    store i64 %t1753, i64* %val_v1754
    %t1755 = load i64, i64* %val_v1754
    %t1757 = icmp slt i64 %t1755, 0
    %t1756 = zext i1 %t1757 to i64
    %t1761 = icmp ne i64 %t1756, 0
    br i1 %t1761, label %if.then.1758, label %if.end.1760
if.then.1758:
    store i64 1, i64* %neg_v1752
    %t1762 = load i64, i64* %val_v1754
    %t1763 = sub i64 0, %t1762
    store i64 %t1763, i64* %val_v1754
    br label %if.end.1760
if.end.1760:
    %t1764 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.104, i64 0, i64 0
    %t1765 = ptrtoint i8* %t1764 to i64
    %oct_out_v1766 = alloca i64
    store i64 %t1765, i64* %oct_out_v1766
    br label %loop.cond.1767
loop.cond.1767:
    %t1770 = load i64, i64* %val_v1754
    %t1772 = icmp sle i64 %t1770, 0
    %t1771 = zext i1 %t1772 to i64
    %t1773 = icmp eq i64 %t1771, 0
    br i1 %t1773, label %loop.body.1768, label %loop.end.1769
loop.body.1768:
    %t1774 = load i64, i64* %val_v1754
    %t1775 = load i64, i64* %val_v1754
    %t1776 = sdiv i64 %t1775, 8
    %t1777 = mul i64 %t1776, 8
    %t1778 = sub i64 %t1774, %t1777
    %rem_v1779 = alloca i64
    store i64 %t1778, i64* %rem_v1779
    %t1780 = load i64, i64* %oct_chars_v1751
    %t1782 = load i64, i64* %rem_v1779
    %t1781 = call i64 @freak_llvm_word_char_at(i64 %t1780, i64 %t1782)
    %t1783 = load i64, i64* %oct_out_v1766
    %t1784 = call i64 @freak_llvm_word_concat(i64 %t1781, i64 %t1783)
    store i64 %t1784, i64* %oct_out_v1766
    %t1785 = load i64, i64* %val_v1754
    %t1786 = sdiv i64 %t1785, 8
    store i64 %t1786, i64* %val_v1754
    br label %loop.cond.1767
loop.end.1769:
    %t1787 = load i64, i64* %neg_v1752
    %t1791 = icmp ne i64 %t1787, 0
    br i1 %t1791, label %if.then.1788, label %if.end.1790
if.then.1788:
    %t1792 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.105, i64 0, i64 0
    %t1793 = ptrtoint i8* %t1792 to i64
    %t1794 = load i64, i64* %oct_out_v1766
    %t1795 = call i64 @freak_llvm_word_concat(i64 %t1793, i64 %t1794)
    store i64 %t1795, i64* %oct_out_v1766
    br label %if.end.1790
if.end.1790:
    %t1796 = load i64, i64* %oct_out_v1766
    ret i64 %t1796
    ret i64 0
}

define i64 @freak_char_to_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1797 = load i64, i64* %c
    %t1798 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.106, i64 0, i64 0
    %t1799 = ptrtoint i8* %t1798 to i64
    %t1800 = call i64 @freak_llvm_word_eq(i64 %t1797, i64 %t1799)
    %t1804 = icmp ne i64 %t1800, 0
    br i1 %t1804, label %if.then.1801, label %if.end.1803
if.then.1801:
    ret i64 0
    br label %if.end.1803
if.end.1803:
    %t1805 = load i64, i64* %c
    %t1806 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.107, i64 0, i64 0
    %t1807 = ptrtoint i8* %t1806 to i64
    %t1808 = call i64 @freak_llvm_word_eq(i64 %t1805, i64 %t1807)
    %t1812 = icmp ne i64 %t1808, 0
    br i1 %t1812, label %if.then.1809, label %if.end.1811
if.then.1809:
    ret i64 1
    br label %if.end.1811
if.end.1811:
    %t1813 = load i64, i64* %c
    %t1814 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.108, i64 0, i64 0
    %t1815 = ptrtoint i8* %t1814 to i64
    %t1816 = call i64 @freak_llvm_word_eq(i64 %t1813, i64 %t1815)
    %t1820 = icmp ne i64 %t1816, 0
    br i1 %t1820, label %if.then.1817, label %if.end.1819
if.then.1817:
    ret i64 2
    br label %if.end.1819
if.end.1819:
    %t1821 = load i64, i64* %c
    %t1822 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.109, i64 0, i64 0
    %t1823 = ptrtoint i8* %t1822 to i64
    %t1824 = call i64 @freak_llvm_word_eq(i64 %t1821, i64 %t1823)
    %t1828 = icmp ne i64 %t1824, 0
    br i1 %t1828, label %if.then.1825, label %if.end.1827
if.then.1825:
    ret i64 3
    br label %if.end.1827
if.end.1827:
    %t1829 = load i64, i64* %c
    %t1830 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.110, i64 0, i64 0
    %t1831 = ptrtoint i8* %t1830 to i64
    %t1832 = call i64 @freak_llvm_word_eq(i64 %t1829, i64 %t1831)
    %t1836 = icmp ne i64 %t1832, 0
    br i1 %t1836, label %if.then.1833, label %if.end.1835
if.then.1833:
    ret i64 4
    br label %if.end.1835
if.end.1835:
    %t1837 = load i64, i64* %c
    %t1838 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.111, i64 0, i64 0
    %t1839 = ptrtoint i8* %t1838 to i64
    %t1840 = call i64 @freak_llvm_word_eq(i64 %t1837, i64 %t1839)
    %t1844 = icmp ne i64 %t1840, 0
    br i1 %t1844, label %if.then.1841, label %if.end.1843
if.then.1841:
    ret i64 5
    br label %if.end.1843
if.end.1843:
    %t1845 = load i64, i64* %c
    %t1846 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.112, i64 0, i64 0
    %t1847 = ptrtoint i8* %t1846 to i64
    %t1848 = call i64 @freak_llvm_word_eq(i64 %t1845, i64 %t1847)
    %t1852 = icmp ne i64 %t1848, 0
    br i1 %t1852, label %if.then.1849, label %if.end.1851
if.then.1849:
    ret i64 6
    br label %if.end.1851
if.end.1851:
    %t1853 = load i64, i64* %c
    %t1854 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.113, i64 0, i64 0
    %t1855 = ptrtoint i8* %t1854 to i64
    %t1856 = call i64 @freak_llvm_word_eq(i64 %t1853, i64 %t1855)
    %t1860 = icmp ne i64 %t1856, 0
    br i1 %t1860, label %if.then.1857, label %if.end.1859
if.then.1857:
    ret i64 7
    br label %if.end.1859
if.end.1859:
    %t1861 = load i64, i64* %c
    %t1862 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.114, i64 0, i64 0
    %t1863 = ptrtoint i8* %t1862 to i64
    %t1864 = call i64 @freak_llvm_word_eq(i64 %t1861, i64 %t1863)
    %t1868 = icmp ne i64 %t1864, 0
    br i1 %t1868, label %if.then.1865, label %if.end.1867
if.then.1865:
    ret i64 8
    br label %if.end.1867
if.end.1867:
    %t1869 = load i64, i64* %c
    %t1870 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.115, i64 0, i64 0
    %t1871 = ptrtoint i8* %t1870 to i64
    %t1872 = call i64 @freak_llvm_word_eq(i64 %t1869, i64 %t1871)
    %t1876 = icmp ne i64 %t1872, 0
    br i1 %t1876, label %if.then.1873, label %if.end.1875
if.then.1873:
    ret i64 9
    br label %if.end.1875
if.end.1875:
    %t1877 = sub i64 0, 1
    ret i64 %t1877
    ret i64 0
}

define i64 @freak_word_to_int_safe(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1878 = load i64, i64* @g_s
    %t1879 = call i64 @freak_llvm_word_length(i64 %t1878)
    %slen_v1880 = alloca i64
    store i64 %t1879, i64* %slen_v1880
    %t1881 = load i64, i64* %slen_v1880
    %t1883 = icmp eq i64 %t1881, 0
    %t1882 = zext i1 %t1883 to i64
    %t1887 = icmp ne i64 %t1882, 0
    br i1 %t1887, label %if.then.1884, label %if.end.1886
if.then.1884:
    ret i64 0
    br label %if.end.1886
if.end.1886:
    %neg_v1888 = alloca i64
    store i64 0, i64* %neg_v1888
    %wi_v1889 = alloca i64
    store i64 0, i64* %wi_v1889
    %t1890 = load i64, i64* @g_s
    %t1891 = call i64 @freak_llvm_word_char_at(i64 %t1890, i64 0)
    %t1892 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.116, i64 0, i64 0
    %t1893 = ptrtoint i8* %t1892 to i64
    %t1894 = call i64 @freak_llvm_word_eq(i64 %t1891, i64 %t1893)
    %t1898 = icmp ne i64 %t1894, 0
    br i1 %t1898, label %if.then.1895, label %if.end.1897
if.then.1895:
    store i64 1, i64* %neg_v1888
    store i64 1, i64* %wi_v1889
    br label %if.end.1897
if.end.1897:
    %num_v1899 = alloca i64
    store i64 0, i64* %num_v1899
    br label %loop.cond.1900
loop.cond.1900:
    %t1903 = load i64, i64* %wi_v1889
    %t1904 = load i64, i64* %slen_v1880
    %t1906 = icmp sge i64 %t1903, %t1904
    %t1905 = zext i1 %t1906 to i64
    %t1907 = icmp eq i64 %t1905, 0
    br i1 %t1907, label %loop.body.1901, label %loop.end.1902
loop.body.1901:
    %t1908 = load i64, i64* @g_s
    %t1910 = load i64, i64* %wi_v1889
    %t1909 = call i64 @freak_llvm_word_char_at(i64 %t1908, i64 %t1910)
    %t1911 = call i64 @freak_char_to_digit(i64 %t1909)
    %d_v1912 = alloca i64
    store i64 %t1911, i64* %d_v1912
    %t1913 = load i64, i64* %d_v1912
    %t1915 = icmp slt i64 %t1913, 0
    %t1914 = zext i1 %t1915 to i64
    %t1919 = icmp ne i64 %t1914, 0
    br i1 %t1919, label %if.then.1916, label %if.end.1918
if.then.1916:
    ret i64 0
    br label %if.end.1918
if.end.1918:
    %t1920 = load i64, i64* %num_v1899
    %t1921 = mul i64 %t1920, 10
    %t1922 = load i64, i64* %d_v1912
    %t1923 = add i64 %t1921, %t1922
    store i64 %t1923, i64* %num_v1899
    %t1924 = load i64, i64* %wi_v1889
    %t1925 = add i64 %t1924, 1
    store i64 %t1925, i64* %wi_v1889
    br label %loop.cond.1900
loop.end.1902:
    %t1926 = load i64, i64* %neg_v1888
    %t1930 = icmp ne i64 %t1926, 0
    br i1 %t1930, label %if.then.1927, label %if.end.1929
if.then.1927:
    %t1931 = load i64, i64* %num_v1899
    %t1932 = sub i64 0, %t1931
    ret i64 %t1932
    br label %if.end.1929
if.end.1929:
    %t1933 = load i64, i64* %num_v1899
    ret i64 %t1933
    ret i64 0
}

define i64 @freak_bool_to_word(i64 %arg_b) {
entry:
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t1934 = load i64, i64* @g_b
    %t1938 = icmp ne i64 %t1934, 0
    br i1 %t1938, label %if.then.1935, label %if.end.1937
if.then.1935:
    %t1939 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.117, i64 0, i64 0
    %t1940 = ptrtoint i8* %t1939 to i64
    ret i64 %t1940
    br label %if.end.1937
if.end.1937:
    %t1941 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.118, i64 0, i64 0
    %t1942 = ptrtoint i8* %t1941 to i64
    ret i64 %t1942
    ret i64 0
}

define void @freak_array_sort_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t1943 = load i64, i64* %handle
    %t1944 = call i64 @freak_llvm_array_len(i64 %t1943)
    %alen_v1945 = alloca i64
    store i64 %t1944, i64* %alen_v1945
    %t1946 = load i64, i64* %alen_v1945
    %t1948 = icmp sle i64 %t1946, 1
    %t1947 = zext i1 %t1948 to i64
    %t1952 = icmp ne i64 %t1947, 0
    br i1 %t1952, label %if.then.1949, label %if.end.1951
if.then.1949:
    ret void
    br label %if.end.1951
if.end.1951:
    %si_v1953 = alloca i64
    store i64 1, i64* %si_v1953
    br label %loop.cond.1954
loop.cond.1954:
    %t1957 = load i64, i64* %si_v1953
    %t1958 = load i64, i64* %alen_v1945
    %t1960 = icmp sge i64 %t1957, %t1958
    %t1959 = zext i1 %t1960 to i64
    %t1961 = icmp eq i64 %t1959, 0
    br i1 %t1961, label %loop.body.1955, label %loop.end.1956
loop.body.1955:
    %t1962 = load i64, i64* %handle
    %t1963 = load i64, i64* %si_v1953
    %t1964 = call i64 @freak_llvm_array_get(i64 %t1962, i64 %t1963)
    %key_w_v1965 = alloca i64
    store i64 %t1964, i64* %key_w_v1965
    %t1966 = load i64, i64* %key_w_v1965
    %t1967 = call i64 @freak_llvm_word_to_int(i64 %t1966)
    %key_v1968 = alloca i64
    store i64 %t1967, i64* %key_v1968
    %t1969 = load i64, i64* %si_v1953
    %t1970 = sub i64 %t1969, 1
    %sj_v1971 = alloca i64
    store i64 %t1970, i64* %sj_v1971
    %sorted_v1972 = alloca i64
    store i64 0, i64* %sorted_v1972
    br label %loop.cond.1973
loop.cond.1973:
    %t1976 = load i64, i64* %sj_v1971
    %t1978 = icmp slt i64 %t1976, 0
    %t1977 = zext i1 %t1978 to i64
    %t1979 = load i64, i64* %sorted_v1972
    %t1981 = icmp ne i64 %t1977, 0
    %t1982 = icmp ne i64 %t1979, 0
    %t1983 = or i1 %t1981, %t1982
    %t1980 = zext i1 %t1983 to i64
    %t1984 = icmp eq i64 %t1980, 0
    br i1 %t1984, label %loop.body.1974, label %loop.end.1975
loop.body.1974:
    %t1985 = load i64, i64* %handle
    %t1986 = load i64, i64* %sj_v1971
    %t1987 = call i64 @freak_llvm_array_get(i64 %t1985, i64 %t1986)
    %cw_v1988 = alloca i64
    store i64 %t1987, i64* %cw_v1988
    %t1989 = load i64, i64* %cw_v1988
    %t1990 = call i64 @freak_llvm_word_to_int(i64 %t1989)
    %cv_v1991 = alloca i64
    store i64 %t1990, i64* %cv_v1991
    %t1992 = load i64, i64* %cv_v1991
    %t1993 = load i64, i64* %key_v1968
    %t1995 = icmp sgt i64 %t1992, %t1993
    %t1994 = zext i1 %t1995 to i64
    %t1999 = icmp ne i64 %t1994, 0
    br i1 %t1999, label %if.then.1996, label %if.else.1997
if.then.1996:
    %t2000 = load i64, i64* %handle
    %t2001 = load i64, i64* %sj_v1971
    %t2002 = add i64 %t2001, 1
    %t2003 = load i64, i64* %cw_v1988
    call void @freak_llvm_array_set(i64 %t2000, i64 %t2002, i64 %t2003)
    %t2004 = load i64, i64* %sj_v1971
    %t2005 = sub i64 %t2004, 1
    store i64 %t2005, i64* %sj_v1971
    br label %if.end.1998
if.else.1997:
    store i64 1, i64* %sorted_v1972
    br label %if.end.1998
if.end.1998:
    br label %loop.cond.1973
loop.end.1975:
    %t2006 = load i64, i64* %handle
    %t2007 = load i64, i64* %sj_v1971
    %t2008 = add i64 %t2007, 1
    %t2009 = load i64, i64* %key_v1968
    %t2010 = call i64 @freak_llvm_word_from_int(i64 %t2009)
    call void @freak_llvm_array_set(i64 %t2006, i64 %t2008, i64 %t2010)
    %t2011 = load i64, i64* %si_v1953
    %t2012 = add i64 %t2011, 1
    store i64 %t2012, i64* %si_v1953
    br label %loop.cond.1954
loop.end.1956:
    ret void
}

define void @freak_array_sort_word(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2013 = load i64, i64* %handle
    %t2014 = call i64 @freak_llvm_array_len(i64 %t2013)
    %alen_v2015 = alloca i64
    store i64 %t2014, i64* %alen_v2015
    %t2016 = load i64, i64* %alen_v2015
    %t2018 = icmp sle i64 %t2016, 1
    %t2017 = zext i1 %t2018 to i64
    %t2022 = icmp ne i64 %t2017, 0
    br i1 %t2022, label %if.then.2019, label %if.end.2021
if.then.2019:
    ret void
    br label %if.end.2021
if.end.2021:
    %si_v2023 = alloca i64
    store i64 1, i64* %si_v2023
    br label %loop.cond.2024
loop.cond.2024:
    %t2027 = load i64, i64* %si_v2023
    %t2028 = load i64, i64* %alen_v2015
    %t2030 = icmp sge i64 %t2027, %t2028
    %t2029 = zext i1 %t2030 to i64
    %t2031 = icmp eq i64 %t2029, 0
    br i1 %t2031, label %loop.body.2025, label %loop.end.2026
loop.body.2025:
    %t2032 = load i64, i64* %handle
    %t2033 = load i64, i64* %si_v2023
    %t2034 = call i64 @freak_llvm_array_get(i64 %t2032, i64 %t2033)
    %key_w_v2035 = alloca i64
    store i64 %t2034, i64* %key_w_v2035
    %t2036 = load i64, i64* %si_v2023
    %t2037 = sub i64 %t2036, 1
    %sj_v2038 = alloca i64
    store i64 %t2037, i64* %sj_v2038
    %sorted_v2039 = alloca i64
    store i64 0, i64* %sorted_v2039
    br label %loop.cond.2040
loop.cond.2040:
    %t2043 = load i64, i64* %sj_v2038
    %t2045 = icmp slt i64 %t2043, 0
    %t2044 = zext i1 %t2045 to i64
    %t2046 = load i64, i64* %sorted_v2039
    %t2048 = icmp ne i64 %t2044, 0
    %t2049 = icmp ne i64 %t2046, 0
    %t2050 = or i1 %t2048, %t2049
    %t2047 = zext i1 %t2050 to i64
    %t2051 = icmp eq i64 %t2047, 0
    br i1 %t2051, label %loop.body.2041, label %loop.end.2042
loop.body.2041:
    %t2052 = load i64, i64* %handle
    %t2053 = load i64, i64* %sj_v2038
    %t2054 = call i64 @freak_llvm_array_get(i64 %t2052, i64 %t2053)
    %cw_v2055 = alloca i64
    store i64 %t2054, i64* %cw_v2055
    %t2056 = load i64, i64* %cw_v2055
    %t2057 = load i64, i64* %key_w_v2035
    %t2058 = call i64 @freak_word_compare(i64 %t2056, i64 %t2057)
    %t2060 = icmp sgt i64 %t2058, 0
    %t2059 = zext i1 %t2060 to i64
    %t2064 = icmp ne i64 %t2059, 0
    br i1 %t2064, label %if.then.2061, label %if.else.2062
if.then.2061:
    %t2065 = load i64, i64* %handle
    %t2066 = load i64, i64* %sj_v2038
    %t2067 = add i64 %t2066, 1
    %t2068 = load i64, i64* %cw_v2055
    call void @freak_llvm_array_set(i64 %t2065, i64 %t2067, i64 %t2068)
    %t2069 = load i64, i64* %sj_v2038
    %t2070 = sub i64 %t2069, 1
    store i64 %t2070, i64* %sj_v2038
    br label %if.end.2063
if.else.2062:
    store i64 1, i64* %sorted_v2039
    br label %if.end.2063
if.end.2063:
    br label %loop.cond.2040
loop.end.2042:
    %t2071 = load i64, i64* %handle
    %t2072 = load i64, i64* %sj_v2038
    %t2073 = add i64 %t2072, 1
    %t2074 = load i64, i64* %key_w_v2035
    call void @freak_llvm_array_set(i64 %t2071, i64 %t2073, i64 %t2074)
    %t2075 = load i64, i64* %si_v2023
    %t2076 = add i64 %t2075, 1
    store i64 %t2076, i64* %si_v2023
    br label %loop.cond.2024
loop.end.2026:
    ret void
}

define i64 @freak_array_binary_search_int(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %lo_v2077 = alloca i64
    store i64 0, i64* %lo_v2077
    %t2078 = load i64, i64* %handle
    %t2079 = call i64 @freak_llvm_array_len(i64 %t2078)
    %t2080 = sub i64 %t2079, 1
    %hi_v2081 = alloca i64
    store i64 %t2080, i64* %hi_v2081
    br label %loop.cond.2082
loop.cond.2082:
    %t2085 = load i64, i64* %lo_v2077
    %t2086 = load i64, i64* %hi_v2081
    %t2088 = icmp sgt i64 %t2085, %t2086
    %t2087 = zext i1 %t2088 to i64
    %t2089 = icmp eq i64 %t2087, 0
    br i1 %t2089, label %loop.body.2083, label %loop.end.2084
loop.body.2083:
    %t2090 = load i64, i64* %hi_v2081
    %t2091 = load i64, i64* %lo_v2077
    %t2092 = sub i64 %t2090, %t2091
    %range_v2093 = alloca i64
    store i64 %t2092, i64* %range_v2093
    %t2094 = load i64, i64* %range_v2093
    %t2095 = sdiv i64 %t2094, 2
    %half_v2096 = alloca i64
    store i64 %t2095, i64* %half_v2096
    %t2097 = load i64, i64* %lo_v2077
    %t2098 = load i64, i64* %half_v2096
    %t2099 = add i64 %t2097, %t2098
    %mid_v2100 = alloca i64
    store i64 %t2099, i64* %mid_v2100
    %t2101 = load i64, i64* %handle
    %t2102 = load i64, i64* %mid_v2100
    %t2103 = call i64 @freak_llvm_array_get(i64 %t2101, i64 %t2102)
    %mw_v2104 = alloca i64
    store i64 %t2103, i64* %mw_v2104
    %t2105 = load i64, i64* %mw_v2104
    %t2106 = call i64 @freak_llvm_word_to_int(i64 %t2105)
    %mv_v2107 = alloca i64
    store i64 %t2106, i64* %mv_v2107
    %t2108 = load i64, i64* %mv_v2107
    %t2109 = load i64, i64* %target
    %t2111 = icmp eq i64 %t2108, %t2109
    %t2110 = zext i1 %t2111 to i64
    %t2115 = icmp ne i64 %t2110, 0
    br i1 %t2115, label %if.then.2112, label %if.end.2114
if.then.2112:
    %t2116 = load i64, i64* %mid_v2100
    ret i64 %t2116
    br label %if.end.2114
if.end.2114:
    %t2117 = load i64, i64* %mv_v2107
    %t2118 = load i64, i64* %target
    %t2120 = icmp slt i64 %t2117, %t2118
    %t2119 = zext i1 %t2120 to i64
    %t2124 = icmp ne i64 %t2119, 0
    br i1 %t2124, label %if.then.2121, label %if.else.2122
if.then.2121:
    %t2125 = load i64, i64* %mid_v2100
    %t2126 = add i64 %t2125, 1
    store i64 %t2126, i64* %lo_v2077
    br label %if.end.2123
if.else.2122:
    %t2127 = load i64, i64* %mid_v2100
    %t2128 = sub i64 %t2127, 1
    store i64 %t2128, i64* %hi_v2081
    br label %if.end.2123
if.end.2123:
    br label %loop.cond.2082
loop.end.2084:
    %t2129 = sub i64 0, 1
    ret i64 %t2129
    ret i64 0
}

define i64 @freak_array_find(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2130 = load i64, i64* %handle
    %t2131 = call i64 @freak_llvm_array_len(i64 %t2130)
    %alen_v2132 = alloca i64
    store i64 %t2131, i64* %alen_v2132
    %fi_v2133 = alloca i64
    store i64 0, i64* %fi_v2133
    %t2139 = load i64, i64* %alen_v2132
    %rep.2138 = alloca i64
    store i64 0, i64* %rep.2138
    br label %loop.cond.2134
loop.cond.2134:
    %t2140 = load i64, i64* %rep.2138
    %t2141 = icmp slt i64 %t2140, %t2139
    br i1 %t2141, label %loop.body.2135, label %loop.end.2136
loop.body.2135:
    %t2142 = load i64, i64* %handle
    %t2143 = load i64, i64* %fi_v2133
    %t2144 = call i64 @freak_llvm_array_get(i64 %t2142, i64 %t2143)
    %fw_v2145 = alloca i64
    store i64 %t2144, i64* %fw_v2145
    %t2146 = load i64, i64* %fw_v2145
    %t2147 = load i64, i64* %target
    %t2148 = call i64 @freak_llvm_word_eq(i64 %t2146, i64 %t2147)
    %t2152 = icmp ne i64 %t2148, 0
    br i1 %t2152, label %if.then.2149, label %if.end.2151
if.then.2149:
    %t2153 = load i64, i64* %fi_v2133
    ret i64 %t2153
    br label %if.end.2151
if.end.2151:
    %t2154 = load i64, i64* %fi_v2133
    %t2155 = add i64 %t2154, 1
    store i64 %t2155, i64* %fi_v2133
    br label %loop.inc.2137
loop.inc.2137:
    %t2156 = load i64, i64* %rep.2138
    %t2157 = add i64 %t2156, 1
    store i64 %t2157, i64* %rep.2138
    br label %loop.cond.2134
loop.end.2136:
    %t2158 = sub i64 0, 1
    ret i64 %t2158
    ret i64 0
}

define i64 @freak_array_contains(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2159 = load i64, i64* %handle
    %t2160 = load i64, i64* %target
    %t2161 = call i64 @freak_array_find(i64 %t2159, i64 %t2160)
    %t2163 = icmp sge i64 %t2161, 0
    %t2162 = zext i1 %t2163 to i64
    ret i64 %t2162
    ret i64 0
}

define void @freak_array_reverse(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2164 = load i64, i64* %handle
    %t2165 = call i64 @freak_llvm_array_len(i64 %t2164)
    %alen_v2166 = alloca i64
    store i64 %t2165, i64* %alen_v2166
    %t2167 = load i64, i64* %alen_v2166
    %t2169 = icmp sle i64 %t2167, 1
    %t2168 = zext i1 %t2169 to i64
    %t2173 = icmp ne i64 %t2168, 0
    br i1 %t2173, label %if.then.2170, label %if.end.2172
if.then.2170:
    ret void
    br label %if.end.2172
if.end.2172:
    %lo_v2174 = alloca i64
    store i64 0, i64* %lo_v2174
    %t2175 = load i64, i64* %alen_v2166
    %t2176 = sub i64 %t2175, 1
    %hi_v2177 = alloca i64
    store i64 %t2176, i64* %hi_v2177
    br label %loop.cond.2178
loop.cond.2178:
    %t2181 = load i64, i64* %lo_v2174
    %t2182 = load i64, i64* %hi_v2177
    %t2184 = icmp sge i64 %t2181, %t2182
    %t2183 = zext i1 %t2184 to i64
    %t2185 = icmp eq i64 %t2183, 0
    br i1 %t2185, label %loop.body.2179, label %loop.end.2180
loop.body.2179:
    %t2186 = load i64, i64* %handle
    %t2187 = load i64, i64* %lo_v2174
    %t2188 = call i64 @freak_llvm_array_get(i64 %t2186, i64 %t2187)
    %tmp_v2189 = alloca i64
    store i64 %t2188, i64* %tmp_v2189
    %t2190 = load i64, i64* %handle
    %t2191 = load i64, i64* %hi_v2177
    %t2192 = call i64 @freak_llvm_array_get(i64 %t2190, i64 %t2191)
    %hw_v2193 = alloca i64
    store i64 %t2192, i64* %hw_v2193
    %t2194 = load i64, i64* %handle
    %t2195 = load i64, i64* %lo_v2174
    %t2196 = load i64, i64* %hw_v2193
    call void @freak_llvm_array_set(i64 %t2194, i64 %t2195, i64 %t2196)
    %t2197 = load i64, i64* %handle
    %t2198 = load i64, i64* %hi_v2177
    %t2199 = load i64, i64* %tmp_v2189
    call void @freak_llvm_array_set(i64 %t2197, i64 %t2198, i64 %t2199)
    %t2200 = load i64, i64* %lo_v2174
    %t2201 = add i64 %t2200, 1
    store i64 %t2201, i64* %lo_v2174
    %t2202 = load i64, i64* %hi_v2177
    %t2203 = sub i64 %t2202, 1
    store i64 %t2203, i64* %hi_v2177
    br label %loop.cond.2178
loop.end.2180:
    ret void
}

define i64 @freak_array_copy(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2204 = call i64 @freak_llvm_array_new()
    %new_arr_v2205 = alloca i64
    store i64 %t2204, i64* %new_arr_v2205
    %t2206 = load i64, i64* %handle
    %t2207 = call i64 @freak_llvm_array_len(i64 %t2206)
    %alen_v2208 = alloca i64
    store i64 %t2207, i64* %alen_v2208
    %ci_v2209 = alloca i64
    store i64 0, i64* %ci_v2209
    %t2215 = load i64, i64* %alen_v2208
    %rep.2214 = alloca i64
    store i64 0, i64* %rep.2214
    br label %loop.cond.2210
loop.cond.2210:
    %t2216 = load i64, i64* %rep.2214
    %t2217 = icmp slt i64 %t2216, %t2215
    br i1 %t2217, label %loop.body.2211, label %loop.end.2212
loop.body.2211:
    %t2218 = load i64, i64* %handle
    %t2219 = load i64, i64* %ci_v2209
    %t2220 = call i64 @freak_llvm_array_get(i64 %t2218, i64 %t2219)
    %cw_v2221 = alloca i64
    store i64 %t2220, i64* %cw_v2221
    %t2222 = load i64, i64* %new_arr_v2205
    %t2223 = load i64, i64* %cw_v2221
    call void @freak_llvm_array_push(i64 %t2222, i64 %t2223)
    %t2224 = load i64, i64* %ci_v2209
    %t2225 = add i64 %t2224, 1
    store i64 %t2225, i64* %ci_v2209
    br label %loop.inc.2213
loop.inc.2213:
    %t2226 = load i64, i64* %rep.2214
    %t2227 = add i64 %t2226, 1
    store i64 %t2227, i64* %rep.2214
    br label %loop.cond.2210
loop.end.2212:
    %t2228 = load i64, i64* %new_arr_v2205
    ret i64 %t2228
    ret i64 0
}

define i64 @freak_array_join(i64 %arg_handle, i64 %arg_sep) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %sep = alloca i64
    store i64 %arg_sep, i64* %sep
    %t2229 = load i64, i64* %handle
    %t2230 = call i64 @freak_llvm_array_len(i64 %t2229)
    %alen_v2231 = alloca i64
    store i64 %t2230, i64* %alen_v2231
    %t2232 = load i64, i64* %alen_v2231
    %t2234 = icmp eq i64 %t2232, 0
    %t2233 = zext i1 %t2234 to i64
    %t2238 = icmp ne i64 %t2233, 0
    br i1 %t2238, label %if.then.2235, label %if.end.2237
if.then.2235:
    %t2239 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.119, i64 0, i64 0
    %t2240 = ptrtoint i8* %t2239 to i64
    ret i64 %t2240
    br label %if.end.2237
if.end.2237:
    %t2241 = load i64, i64* %handle
    %t2242 = call i64 @freak_llvm_array_get(i64 %t2241, i64 0)
    %aj_out_v2243 = alloca i64
    store i64 %t2242, i64* %aj_out_v2243
    %ji_v2244 = alloca i64
    store i64 1, i64* %ji_v2244
    br label %loop.cond.2245
loop.cond.2245:
    %t2248 = load i64, i64* %ji_v2244
    %t2249 = load i64, i64* %alen_v2231
    %t2251 = icmp sge i64 %t2248, %t2249
    %t2250 = zext i1 %t2251 to i64
    %t2252 = icmp eq i64 %t2250, 0
    br i1 %t2252, label %loop.body.2246, label %loop.end.2247
loop.body.2246:
    %t2253 = load i64, i64* %handle
    %t2254 = load i64, i64* %ji_v2244
    %t2255 = call i64 @freak_llvm_array_get(i64 %t2253, i64 %t2254)
    %jw_v2256 = alloca i64
    store i64 %t2255, i64* %jw_v2256
    %t2257 = load i64, i64* %aj_out_v2243
    %t2258 = load i64, i64* %sep
    %t2259 = call i64 @freak_llvm_word_concat(i64 %t2257, i64 %t2258)
    %t2260 = load i64, i64* %jw_v2256
    %t2261 = call i64 @freak_llvm_word_concat(i64 %t2259, i64 %t2260)
    store i64 %t2261, i64* %aj_out_v2243
    %t2262 = load i64, i64* %ji_v2244
    %t2263 = add i64 %t2262, 1
    store i64 %t2263, i64* %ji_v2244
    br label %loop.cond.2245
loop.end.2247:
    %t2264 = load i64, i64* %aj_out_v2243
    ret i64 %t2264
    ret i64 0
}

define i64 @freak_array_count(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2265 = load i64, i64* %handle
    %t2266 = call i64 @freak_llvm_array_len(i64 %t2265)
    %alen_v2267 = alloca i64
    store i64 %t2266, i64* %alen_v2267
    %cnt_v2268 = alloca i64
    store i64 0, i64* %cnt_v2268
    %ci_v2269 = alloca i64
    store i64 0, i64* %ci_v2269
    %t2275 = load i64, i64* %alen_v2267
    %rep.2274 = alloca i64
    store i64 0, i64* %rep.2274
    br label %loop.cond.2270
loop.cond.2270:
    %t2276 = load i64, i64* %rep.2274
    %t2277 = icmp slt i64 %t2276, %t2275
    br i1 %t2277, label %loop.body.2271, label %loop.end.2272
loop.body.2271:
    %t2278 = load i64, i64* %handle
    %t2279 = load i64, i64* %ci_v2269
    %t2280 = call i64 @freak_llvm_array_get(i64 %t2278, i64 %t2279)
    %cw_v2281 = alloca i64
    store i64 %t2280, i64* %cw_v2281
    %t2282 = load i64, i64* %cw_v2281
    %t2283 = load i64, i64* %target
    %t2284 = call i64 @freak_llvm_word_eq(i64 %t2282, i64 %t2283)
    %t2288 = icmp ne i64 %t2284, 0
    br i1 %t2288, label %if.then.2285, label %if.end.2287
if.then.2285:
    %t2289 = load i64, i64* %cnt_v2268
    %t2290 = add i64 %t2289, 1
    store i64 %t2290, i64* %cnt_v2268
    br label %if.end.2287
if.end.2287:
    %t2291 = load i64, i64* %ci_v2269
    %t2292 = add i64 %t2291, 1
    store i64 %t2292, i64* %ci_v2269
    br label %loop.inc.2273
loop.inc.2273:
    %t2293 = load i64, i64* %rep.2274
    %t2294 = add i64 %t2293, 1
    store i64 %t2294, i64* %rep.2274
    br label %loop.cond.2270
loop.end.2272:
    %t2295 = load i64, i64* %cnt_v2268
    ret i64 %t2295
    ret i64 0
}

define i64 @freak_array_unique(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2296 = load i64, i64* %handle
    %t2297 = call i64 @freak_llvm_array_len(i64 %t2296)
    %alen_v2298 = alloca i64
    store i64 %t2297, i64* %alen_v2298
    %t2299 = load i64, i64* %alen_v2298
    %t2301 = icmp sle i64 %t2299, 1
    %t2300 = zext i1 %t2301 to i64
    %t2305 = icmp ne i64 %t2300, 0
    br i1 %t2305, label %if.then.2302, label %if.end.2304
if.then.2302:
    %t2306 = load i64, i64* %alen_v2298
    ret i64 %t2306
    br label %if.end.2304
if.end.2304:
    %write_idx_v2307 = alloca i64
    store i64 1, i64* %write_idx_v2307
    %ri_v2308 = alloca i64
    store i64 1, i64* %ri_v2308
    br label %loop.cond.2309
loop.cond.2309:
    %t2312 = load i64, i64* %ri_v2308
    %t2313 = load i64, i64* %alen_v2298
    %t2315 = icmp sge i64 %t2312, %t2313
    %t2314 = zext i1 %t2315 to i64
    %t2316 = icmp eq i64 %t2314, 0
    br i1 %t2316, label %loop.body.2310, label %loop.end.2311
loop.body.2310:
    %t2317 = load i64, i64* %handle
    %t2318 = load i64, i64* %ri_v2308
    %t2319 = call i64 @freak_llvm_array_get(i64 %t2317, i64 %t2318)
    %cur_v2320 = alloca i64
    store i64 %t2319, i64* %cur_v2320
    %t2321 = load i64, i64* %handle
    %t2322 = load i64, i64* %ri_v2308
    %t2323 = sub i64 %t2322, 1
    %t2324 = call i64 @freak_llvm_array_get(i64 %t2321, i64 %t2323)
    %prev_v2325 = alloca i64
    store i64 %t2324, i64* %prev_v2325
    %t2326 = load i64, i64* %cur_v2320
    %t2327 = load i64, i64* %prev_v2325
    %t2328 = call i64 @freak_llvm_word_neq(i64 %t2326, i64 %t2327)
    %t2332 = icmp ne i64 %t2328, 0
    br i1 %t2332, label %if.then.2329, label %if.end.2331
if.then.2329:
    %t2333 = load i64, i64* %handle
    %t2334 = load i64, i64* %write_idx_v2307
    %t2335 = load i64, i64* %cur_v2320
    call void @freak_llvm_array_set(i64 %t2333, i64 %t2334, i64 %t2335)
    %t2336 = load i64, i64* %write_idx_v2307
    %t2337 = add i64 %t2336, 1
    store i64 %t2337, i64* %write_idx_v2307
    br label %if.end.2331
if.end.2331:
    %t2338 = load i64, i64* %ri_v2308
    %t2339 = add i64 %t2338, 1
    store i64 %t2339, i64* %ri_v2308
    br label %loop.cond.2309
loop.end.2311:
    %t2340 = load i64, i64* %write_idx_v2307
    ret i64 %t2340
    ret i64 0
}

define i64 @freak_array_sum_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2341 = load i64, i64* %handle
    %t2342 = call i64 @freak_llvm_array_len(i64 %t2341)
    %alen_v2343 = alloca i64
    store i64 %t2342, i64* %alen_v2343
    %total_v2344 = alloca i64
    store i64 0, i64* %total_v2344
    %si_v2345 = alloca i64
    store i64 0, i64* %si_v2345
    %t2351 = load i64, i64* %alen_v2343
    %rep.2350 = alloca i64
    store i64 0, i64* %rep.2350
    br label %loop.cond.2346
loop.cond.2346:
    %t2352 = load i64, i64* %rep.2350
    %t2353 = icmp slt i64 %t2352, %t2351
    br i1 %t2353, label %loop.body.2347, label %loop.end.2348
loop.body.2347:
    %t2354 = load i64, i64* %handle
    %t2355 = load i64, i64* %si_v2345
    %t2356 = call i64 @freak_llvm_array_get(i64 %t2354, i64 %t2355)
    %sw_v2357 = alloca i64
    store i64 %t2356, i64* %sw_v2357
    %t2358 = load i64, i64* %sw_v2357
    %t2359 = call i64 @freak_llvm_word_to_int(i64 %t2358)
    %t2360 = load i64, i64* %total_v2344
    %t2361 = add i64 %t2360, %t2359
    store i64 %t2361, i64* %total_v2344
    %t2362 = load i64, i64* %si_v2345
    %t2363 = add i64 %t2362, 1
    store i64 %t2363, i64* %si_v2345
    br label %loop.inc.2349
loop.inc.2349:
    %t2364 = load i64, i64* %rep.2350
    %t2365 = add i64 %t2364, 1
    store i64 %t2365, i64* %rep.2350
    br label %loop.cond.2346
loop.end.2348:
    %t2366 = load i64, i64* %total_v2344
    ret i64 %t2366
    ret i64 0
}

define i64 @freak_array_max_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2367 = load i64, i64* %handle
    %t2368 = call i64 @freak_llvm_array_len(i64 %t2367)
    %alen_v2369 = alloca i64
    store i64 %t2368, i64* %alen_v2369
    %t2370 = load i64, i64* %alen_v2369
    %t2372 = icmp eq i64 %t2370, 0
    %t2371 = zext i1 %t2372 to i64
    %t2376 = icmp ne i64 %t2371, 0
    br i1 %t2376, label %if.then.2373, label %if.end.2375
if.then.2373:
    ret i64 0
    br label %if.end.2375
if.end.2375:
    %t2377 = load i64, i64* %handle
    %t2378 = call i64 @freak_llvm_array_get(i64 %t2377, i64 0)
    %mw_v2379 = alloca i64
    store i64 %t2378, i64* %mw_v2379
    %t2380 = load i64, i64* %mw_v2379
    %t2381 = call i64 @freak_llvm_word_to_int(i64 %t2380)
    %mx_v2382 = alloca i64
    store i64 %t2381, i64* %mx_v2382
    %mi_v2383 = alloca i64
    store i64 1, i64* %mi_v2383
    br label %loop.cond.2384
loop.cond.2384:
    %t2387 = load i64, i64* %mi_v2383
    %t2388 = load i64, i64* %alen_v2369
    %t2390 = icmp sge i64 %t2387, %t2388
    %t2389 = zext i1 %t2390 to i64
    %t2391 = icmp eq i64 %t2389, 0
    br i1 %t2391, label %loop.body.2385, label %loop.end.2386
loop.body.2385:
    %t2392 = load i64, i64* %handle
    %t2393 = load i64, i64* %mi_v2383
    %t2394 = call i64 @freak_llvm_array_get(i64 %t2392, i64 %t2393)
    %cw_v2395 = alloca i64
    store i64 %t2394, i64* %cw_v2395
    %t2396 = load i64, i64* %cw_v2395
    %t2397 = call i64 @freak_llvm_word_to_int(i64 %t2396)
    %cv_v2398 = alloca i64
    store i64 %t2397, i64* %cv_v2398
    %t2399 = load i64, i64* %cv_v2398
    %t2400 = load i64, i64* %mx_v2382
    %t2402 = icmp sgt i64 %t2399, %t2400
    %t2401 = zext i1 %t2402 to i64
    %t2406 = icmp ne i64 %t2401, 0
    br i1 %t2406, label %if.then.2403, label %if.end.2405
if.then.2403:
    %t2407 = load i64, i64* %cv_v2398
    store i64 %t2407, i64* %mx_v2382
    br label %if.end.2405
if.end.2405:
    %t2408 = load i64, i64* %mi_v2383
    %t2409 = add i64 %t2408, 1
    store i64 %t2409, i64* %mi_v2383
    br label %loop.cond.2384
loop.end.2386:
    %t2410 = load i64, i64* %mx_v2382
    ret i64 %t2410
    ret i64 0
}

define i64 @freak_array_min_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2411 = load i64, i64* %handle
    %t2412 = call i64 @freak_llvm_array_len(i64 %t2411)
    %alen_v2413 = alloca i64
    store i64 %t2412, i64* %alen_v2413
    %t2414 = load i64, i64* %alen_v2413
    %t2416 = icmp eq i64 %t2414, 0
    %t2415 = zext i1 %t2416 to i64
    %t2420 = icmp ne i64 %t2415, 0
    br i1 %t2420, label %if.then.2417, label %if.end.2419
if.then.2417:
    ret i64 0
    br label %if.end.2419
if.end.2419:
    %t2421 = load i64, i64* %handle
    %t2422 = call i64 @freak_llvm_array_get(i64 %t2421, i64 0)
    %mw_v2423 = alloca i64
    store i64 %t2422, i64* %mw_v2423
    %t2424 = load i64, i64* %mw_v2423
    %t2425 = call i64 @freak_llvm_word_to_int(i64 %t2424)
    %mn_v2426 = alloca i64
    store i64 %t2425, i64* %mn_v2426
    %mi_v2427 = alloca i64
    store i64 1, i64* %mi_v2427
    br label %loop.cond.2428
loop.cond.2428:
    %t2431 = load i64, i64* %mi_v2427
    %t2432 = load i64, i64* %alen_v2413
    %t2434 = icmp sge i64 %t2431, %t2432
    %t2433 = zext i1 %t2434 to i64
    %t2435 = icmp eq i64 %t2433, 0
    br i1 %t2435, label %loop.body.2429, label %loop.end.2430
loop.body.2429:
    %t2436 = load i64, i64* %handle
    %t2437 = load i64, i64* %mi_v2427
    %t2438 = call i64 @freak_llvm_array_get(i64 %t2436, i64 %t2437)
    %cw_v2439 = alloca i64
    store i64 %t2438, i64* %cw_v2439
    %t2440 = load i64, i64* %cw_v2439
    %t2441 = call i64 @freak_llvm_word_to_int(i64 %t2440)
    %cv_v2442 = alloca i64
    store i64 %t2441, i64* %cv_v2442
    %t2443 = load i64, i64* %cv_v2442
    %t2444 = load i64, i64* %mn_v2426
    %t2446 = icmp slt i64 %t2443, %t2444
    %t2445 = zext i1 %t2446 to i64
    %t2450 = icmp ne i64 %t2445, 0
    br i1 %t2450, label %if.then.2447, label %if.end.2449
if.then.2447:
    %t2451 = load i64, i64* %cv_v2442
    store i64 %t2451, i64* %mn_v2426
    br label %if.end.2449
if.end.2449:
    %t2452 = load i64, i64* %mi_v2427
    %t2453 = add i64 %t2452, 1
    store i64 %t2453, i64* %mi_v2427
    br label %loop.cond.2428
loop.end.2430:
    %t2454 = load i64, i64* %mn_v2426
    ret i64 %t2454
    ret i64 0
}

define void @freak_json_init() {
entry:
    %t2455 = load i64, i64* @g_json_inited
    %t2457 = icmp eq i64 %t2455, 0
    %t2456 = zext i1 %t2457 to i64
    %t2461 = icmp ne i64 %t2456, 0
    br i1 %t2461, label %if.then.2458, label %if.end.2460
if.then.2458:
    %t2462 = call i64 @freak_llvm_array_new()
    store i64 %t2462, i64* @g_json_types
    %t2463 = call i64 @freak_llvm_array_new()
    store i64 %t2463, i64* @g_json_vals
    %t2464 = call i64 @freak_llvm_array_new()
    store i64 %t2464, i64* @g_json_children
    %t2465 = call i64 @freak_llvm_array_new()
    store i64 %t2465, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 1, i64* @g_json_inited
    br label %if.end.2460
if.end.2460:
    ret void
}

define i64 @freak_json_alloc(i64 %arg_jtype, i64 %arg_jval) {
entry:
    %jtype = alloca i64
    store i64 %arg_jtype, i64* %jtype
    %jval = alloca i64
    store i64 %arg_jval, i64* %jval
    %t2466 = load i64, i64* @g_json_count
    %idx_v2467 = alloca i64
    store i64 %t2466, i64* %idx_v2467
    %t2468 = load i64, i64* @g_json_types
    %t2469 = load i64, i64* %jtype
    call void @freak_llvm_array_push(i64 %t2468, i64 %t2469)
    %t2470 = load i64, i64* @g_json_vals
    %t2471 = load i64, i64* %jval
    call void @freak_llvm_array_push(i64 %t2470, i64 %t2471)
    %t2472 = load i64, i64* @g_json_children
    %t2473 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2472, i64 %t2473)
    %t2474 = load i64, i64* @g_json_keys
    %t2475 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2474, i64 %t2475)
    %t2476 = load i64, i64* @g_json_count
    %t2477 = add i64 %t2476, 1
    store i64 %t2477, i64* @g_json_count
    %t2478 = load i64, i64* %idx_v2467
    ret i64 %t2478
    ret i64 0
}

define i64 @freak_json_get_type(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2479 = load i64, i64* @g_json_types
    %t2480 = load i64, i64* %handle
    %t2481 = call i64 @freak_llvm_array_get(i64 %t2479, i64 %t2480)
    ret i64 %t2481
    ret i64 0
}

define i64 @freak_json_get_str(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2482 = load i64, i64* @g_json_vals
    %t2483 = load i64, i64* %handle
    %t2484 = call i64 @freak_llvm_array_get(i64 %t2482, i64 %t2483)
    ret i64 %t2484
    ret i64 0
}

define i64 @freak_json_get_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2485 = load i64, i64* @g_json_vals
    %t2486 = load i64, i64* %handle
    %t2487 = call i64 @freak_llvm_array_get(i64 %t2485, i64 %t2486)
    %v_v2488 = alloca i64
    store i64 %t2487, i64* %v_v2488
    %t2489 = load i64, i64* %v_v2488
    %t2490 = call i64 @freak_llvm_word_to_int(i64 %t2489)
    ret i64 %t2490
    ret i64 0
}

define i64 @freak_json_get_bool(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2491 = load i64, i64* @g_json_vals
    %t2492 = load i64, i64* %handle
    %t2493 = call i64 @freak_llvm_array_get(i64 %t2491, i64 %t2492)
    %v_v2494 = alloca i64
    store i64 %t2493, i64* %v_v2494
    %t2495 = load i64, i64* %v_v2494
    %t2496 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.120, i64 0, i64 0
    %t2497 = ptrtoint i8* %t2496 to i64
    %t2498 = call i64 @freak_llvm_word_eq(i64 %t2495, i64 %t2497)
    ret i64 %t2498
    ret i64 0
}

define i64 @freak_json_is_null(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2499 = load i64, i64* @g_json_types
    %t2500 = load i64, i64* %handle
    %t2501 = call i64 @freak_llvm_array_get(i64 %t2499, i64 %t2500)
    %t_v2502 = alloca i64
    store i64 %t2501, i64* %t_v2502
    %t2503 = load i64, i64* %t_v2502
    %t2504 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.121, i64 0, i64 0
    %t2505 = ptrtoint i8* %t2504 to i64
    %t2506 = call i64 @freak_llvm_word_eq(i64 %t2503, i64 %t2505)
    ret i64 %t2506
    ret i64 0
}

define i64 @freak_json_arr_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2507 = load i64, i64* @g_json_children
    %t2508 = load i64, i64* %handle
    %t2509 = call i64 @freak_llvm_array_get(i64 %t2507, i64 %t2508)
    %ch_v2510 = alloca i64
    store i64 %t2509, i64* %ch_v2510
    %t2511 = load i64, i64* %ch_v2510
    %t2512 = call i64 @freak_llvm_word_to_int(i64 %t2511)
    %ch_handle_v2513 = alloca i64
    store i64 %t2512, i64* %ch_handle_v2513
    %t2514 = load i64, i64* %ch_handle_v2513
    %t2515 = call i64 @freak_llvm_array_len(i64 %t2514)
    ret i64 %t2515
    ret i64 0
}

define i64 @freak_json_arr_get(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2516 = load i64, i64* @g_json_children
    %t2517 = load i64, i64* %handle
    %t2518 = call i64 @freak_llvm_array_get(i64 %t2516, i64 %t2517)
    %ch_v2519 = alloca i64
    store i64 %t2518, i64* %ch_v2519
    %t2520 = load i64, i64* %ch_v2519
    %t2521 = call i64 @freak_llvm_word_to_int(i64 %t2520)
    %ch_handle_v2522 = alloca i64
    store i64 %t2521, i64* %ch_handle_v2522
    %t2523 = load i64, i64* %ch_handle_v2522
    %t2524 = load i64, i64* %index
    %t2525 = call i64 @freak_llvm_array_get(i64 %t2523, i64 %t2524)
    %val_w_v2526 = alloca i64
    store i64 %t2525, i64* %val_w_v2526
    %t2527 = load i64, i64* %val_w_v2526
    %t2528 = call i64 @freak_llvm_word_to_int(i64 %t2527)
    ret i64 %t2528
    ret i64 0
}

define i64 @freak_json_obj_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2529 = load i64, i64* @g_json_keys
    %t2530 = load i64, i64* %handle
    %t2531 = call i64 @freak_llvm_array_get(i64 %t2529, i64 %t2530)
    %ks_v2532 = alloca i64
    store i64 %t2531, i64* %ks_v2532
    %t2533 = load i64, i64* %ks_v2532
    %t2534 = call i64 @freak_llvm_word_to_int(i64 %t2533)
    %ks_handle_v2535 = alloca i64
    store i64 %t2534, i64* %ks_handle_v2535
    %t2536 = load i64, i64* %ks_handle_v2535
    %t2537 = call i64 @freak_llvm_array_len(i64 %t2536)
    ret i64 %t2537
    ret i64 0
}

define i64 @freak_json_obj_get(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2538 = load i64, i64* @g_json_keys
    %t2539 = load i64, i64* %handle
    %t2540 = call i64 @freak_llvm_array_get(i64 %t2538, i64 %t2539)
    %ks_v2541 = alloca i64
    store i64 %t2540, i64* %ks_v2541
    %t2542 = load i64, i64* %ks_v2541
    %t2543 = call i64 @freak_llvm_word_to_int(i64 %t2542)
    %ks_handle_v2544 = alloca i64
    store i64 %t2543, i64* %ks_handle_v2544
    %t2545 = load i64, i64* @g_json_children
    %t2546 = load i64, i64* %handle
    %t2547 = call i64 @freak_llvm_array_get(i64 %t2545, i64 %t2546)
    %ch_v2548 = alloca i64
    store i64 %t2547, i64* %ch_v2548
    %t2549 = load i64, i64* %ch_v2548
    %t2550 = call i64 @freak_llvm_word_to_int(i64 %t2549)
    %ch_handle_v2551 = alloca i64
    store i64 %t2550, i64* %ch_handle_v2551
    %t2552 = load i64, i64* %ks_handle_v2544
    %t2553 = call i64 @freak_llvm_array_len(i64 %t2552)
    %klen_v2554 = alloca i64
    store i64 %t2553, i64* %klen_v2554
    %ki_v2555 = alloca i64
    store i64 0, i64* %ki_v2555
    %t2561 = load i64, i64* %klen_v2554
    %rep.2560 = alloca i64
    store i64 0, i64* %rep.2560
    br label %loop.cond.2556
loop.cond.2556:
    %t2562 = load i64, i64* %rep.2560
    %t2563 = icmp slt i64 %t2562, %t2561
    br i1 %t2563, label %loop.body.2557, label %loop.end.2558
loop.body.2557:
    %t2564 = load i64, i64* %ks_handle_v2544
    %t2565 = load i64, i64* %ki_v2555
    %t2566 = call i64 @freak_llvm_array_get(i64 %t2564, i64 %t2565)
    %k_v2567 = alloca i64
    store i64 %t2566, i64* %k_v2567
    %t2568 = load i64, i64* %k_v2567
    %t2569 = load i64, i64* %key
    %t2570 = call i64 @freak_llvm_word_eq(i64 %t2568, i64 %t2569)
    %t2574 = icmp ne i64 %t2570, 0
    br i1 %t2574, label %if.then.2571, label %if.end.2573
if.then.2571:
    %t2575 = load i64, i64* %ch_handle_v2551
    %t2576 = load i64, i64* %ki_v2555
    %t2577 = call i64 @freak_llvm_array_get(i64 %t2575, i64 %t2576)
    %v_v2578 = alloca i64
    store i64 %t2577, i64* %v_v2578
    %t2579 = load i64, i64* %v_v2578
    %t2580 = call i64 @freak_llvm_word_to_int(i64 %t2579)
    ret i64 %t2580
    br label %if.end.2573
if.end.2573:
    %t2581 = load i64, i64* %ki_v2555
    %t2582 = add i64 %t2581, 1
    store i64 %t2582, i64* %ki_v2555
    br label %loop.inc.2559
loop.inc.2559:
    %t2583 = load i64, i64* %rep.2560
    %t2584 = add i64 %t2583, 1
    store i64 %t2584, i64* %rep.2560
    br label %loop.cond.2556
loop.end.2558:
    %t2585 = sub i64 0, 1
    ret i64 %t2585
    ret i64 0
}

define i64 @freak_json_obj_has(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2586 = load i64, i64* %handle
    %t2587 = load i64, i64* %key
    %t2588 = call i64 @freak_json_obj_get(i64 %t2586, i64 %t2587)
    %t2590 = icmp sge i64 %t2588, 0
    %t2589 = zext i1 %t2590 to i64
    ret i64 %t2589
    ret i64 0
}

define i64 @freak_json_obj_key_at(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2591 = load i64, i64* @g_json_keys
    %t2592 = load i64, i64* %handle
    %t2593 = call i64 @freak_llvm_array_get(i64 %t2591, i64 %t2592)
    %ks_v2594 = alloca i64
    store i64 %t2593, i64* %ks_v2594
    %t2595 = load i64, i64* %ks_v2594
    %t2596 = call i64 @freak_llvm_word_to_int(i64 %t2595)
    %ks_handle_v2597 = alloca i64
    store i64 %t2596, i64* %ks_handle_v2597
    %t2598 = load i64, i64* %ks_handle_v2597
    %t2599 = load i64, i64* %index
    %t2600 = call i64 @freak_llvm_array_get(i64 %t2598, i64 %t2599)
    ret i64 %t2600
    ret i64 0
}

define i64 @freak_json_cur() {
entry:
    %t2601 = load i64, i64* @g_json_pos
    %t2602 = load i64, i64* @g_json_len
    %t2604 = icmp sge i64 %t2601, %t2602
    %t2603 = zext i1 %t2604 to i64
    %t2608 = icmp ne i64 %t2603, 0
    br i1 %t2608, label %if.then.2605, label %if.end.2607
if.then.2605:
    %t2609 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.122, i64 0, i64 0
    %t2610 = ptrtoint i8* %t2609 to i64
    ret i64 %t2610
    br label %if.end.2607
if.end.2607:
    %t2611 = load i64, i64* @g_json_src
    %t2613 = load i64, i64* @g_json_pos
    %t2612 = call i64 @freak_llvm_word_char_at(i64 %t2611, i64 %t2613)
    ret i64 %t2612
    ret i64 0
}

define i64 @freak_json_advance() {
entry:
    %t2614 = call i64 @freak_json_cur()
    %c_v2615 = alloca i64
    store i64 %t2614, i64* %c_v2615
    %t2616 = load i64, i64* @g_json_pos
    %t2617 = add i64 %t2616, 1
    store i64 %t2617, i64* @g_json_pos
    %t2618 = load i64, i64* %c_v2615
    ret i64 %t2618
    ret i64 0
}

define void @freak_json_skip_ws() {
entry:
    br label %loop.cond.2619
loop.cond.2619:
    %t2622 = load i64, i64* @g_json_pos
    %t2623 = load i64, i64* @g_json_len
    %t2625 = icmp sge i64 %t2622, %t2623
    %t2624 = zext i1 %t2625 to i64
    %t2626 = icmp eq i64 %t2624, 0
    br i1 %t2626, label %loop.body.2620, label %loop.end.2621
loop.body.2620:
    %t2627 = call i64 @freak_json_cur()
    %c_v2628 = alloca i64
    store i64 %t2627, i64* %c_v2628
    %t2629 = load i64, i64* %c_v2628
    %t2630 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.123, i64 0, i64 0
    %t2631 = ptrtoint i8* %t2630 to i64
    %t2632 = call i64 @freak_llvm_word_neq(i64 %t2629, i64 %t2631)
    %t2633 = load i64, i64* %c_v2628
    %t2634 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.124, i64 0, i64 0
    %t2635 = ptrtoint i8* %t2634 to i64
    %t2636 = call i64 @freak_llvm_word_neq(i64 %t2633, i64 %t2635)
    %t2638 = icmp ne i64 %t2632, 0
    %t2639 = icmp ne i64 %t2636, 0
    %t2640 = and i1 %t2638, %t2639
    %t2637 = zext i1 %t2640 to i64
    %t2641 = load i64, i64* %c_v2628
    %t2642 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.125, i64 0, i64 0
    %t2643 = ptrtoint i8* %t2642 to i64
    %t2644 = call i64 @freak_llvm_word_neq(i64 %t2641, i64 %t2643)
    %t2646 = icmp ne i64 %t2637, 0
    %t2647 = icmp ne i64 %t2644, 0
    %t2648 = and i1 %t2646, %t2647
    %t2645 = zext i1 %t2648 to i64
    %t2649 = load i64, i64* %c_v2628
    %t2650 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.126, i64 0, i64 0
    %t2651 = ptrtoint i8* %t2650 to i64
    %t2652 = call i64 @freak_llvm_word_neq(i64 %t2649, i64 %t2651)
    %t2654 = icmp ne i64 %t2645, 0
    %t2655 = icmp ne i64 %t2652, 0
    %t2656 = and i1 %t2654, %t2655
    %t2653 = zext i1 %t2656 to i64
    %t2660 = icmp ne i64 %t2653, 0
    br i1 %t2660, label %if.then.2657, label %if.end.2659
if.then.2657:
    ret void
    br label %if.end.2659
if.end.2659:
    %t2661 = load i64, i64* @g_json_pos
    %t2662 = add i64 %t2661, 1
    store i64 %t2662, i64* @g_json_pos
    br label %loop.cond.2619
loop.end.2621:
    ret void
}

define void @freak_json_expect(i64 %arg_ch) {
entry:
    %ch = alloca i64
    store i64 %arg_ch, i64* %ch
    %t2663 = call i64 @freak_json_advance()
    %c_v2664 = alloca i64
    store i64 %t2663, i64* %c_v2664
    %t2665 = load i64, i64* %c_v2664
    %t2666 = load i64, i64* %ch
    %t2667 = call i64 @freak_llvm_word_neq(i64 %t2665, i64 %t2666)
    %t2671 = icmp ne i64 %t2667, 0
    br i1 %t2671, label %if.then.2668, label %if.end.2670
if.then.2668:
    %t2672 = getelementptr inbounds [29 x i8], [29 x i8]* @.str.127, i64 0, i64 0
    %t2673 = ptrtoint i8* %t2672 to i64
    %t2674 = load i64, i64* %ch
    %t2675 = call i64 @freak_llvm_word_concat(i64 %t2673, i64 %t2674)
    %t2676 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.128, i64 0, i64 0
    %t2677 = ptrtoint i8* %t2676 to i64
    %t2678 = call i64 @freak_llvm_word_concat(i64 %t2675, i64 %t2677)
    %t2679 = load i64, i64* %c_v2664
    %t2680 = call i64 @freak_llvm_word_concat(i64 %t2678, i64 %t2679)
    %t2681 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.129, i64 0, i64 0
    %t2682 = ptrtoint i8* %t2681 to i64
    %t2683 = call i64 @freak_llvm_word_concat(i64 %t2680, i64 %t2682)
    call void @freak_llvm_say(i64 %t2683)
    br label %if.end.2670
if.end.2670:
    ret void
}

define i64 @freak_json_parse_string() {
entry:
    %t2684 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.130, i64 0, i64 0
    %t2685 = ptrtoint i8* %t2684 to i64
    call void @freak_json_expect(i64 %t2685)
    %t2686 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.131, i64 0, i64 0
    %t2687 = ptrtoint i8* %t2686 to i64
    %ps_out_v2688 = alloca i64
    store i64 %t2687, i64* %ps_out_v2688
    br label %loop.cond.2689
loop.cond.2689:
    %t2692 = load i64, i64* @g_json_pos
    %t2693 = load i64, i64* @g_json_len
    %t2695 = icmp sge i64 %t2692, %t2693
    %t2694 = zext i1 %t2695 to i64
    %t2696 = icmp eq i64 %t2694, 0
    br i1 %t2696, label %loop.body.2690, label %loop.end.2691
loop.body.2690:
    %t2697 = call i64 @freak_json_advance()
    %c_v2698 = alloca i64
    store i64 %t2697, i64* %c_v2698
    %t2699 = load i64, i64* %c_v2698
    %t2700 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.132, i64 0, i64 0
    %t2701 = ptrtoint i8* %t2700 to i64
    %t2702 = call i64 @freak_llvm_word_eq(i64 %t2699, i64 %t2701)
    %t2706 = icmp ne i64 %t2702, 0
    br i1 %t2706, label %if.then.2703, label %if.end.2705
if.then.2703:
    %t2707 = load i64, i64* %ps_out_v2688
    ret i64 %t2707
    br label %if.end.2705
if.end.2705:
    %t2708 = load i64, i64* %c_v2698
    %t2709 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.133, i64 0, i64 0
    %t2710 = ptrtoint i8* %t2709 to i64
    %t2711 = call i64 @freak_llvm_word_eq(i64 %t2708, i64 %t2710)
    %t2715 = icmp ne i64 %t2711, 0
    br i1 %t2715, label %if.then.2712, label %if.else.2713
if.then.2712:
    %t2716 = call i64 @freak_json_advance()
    %esc_v2717 = alloca i64
    store i64 %t2716, i64* %esc_v2717
    %t2718 = load i64, i64* %esc_v2717
    %t2719 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.134, i64 0, i64 0
    %t2720 = ptrtoint i8* %t2719 to i64
    %t2721 = call i64 @freak_llvm_word_eq(i64 %t2718, i64 %t2720)
    %t2725 = icmp ne i64 %t2721, 0
    br i1 %t2725, label %if.then.2722, label %if.else.2723
if.then.2722:
    %t2726 = load i64, i64* %ps_out_v2688
    %t2727 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.135, i64 0, i64 0
    %t2728 = ptrtoint i8* %t2727 to i64
    %t2729 = call i64 @freak_llvm_word_concat(i64 %t2726, i64 %t2728)
    store i64 %t2729, i64* %ps_out_v2688
    br label %if.end.2724
if.else.2723:
    %t2730 = load i64, i64* %esc_v2717
    %t2731 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.136, i64 0, i64 0
    %t2732 = ptrtoint i8* %t2731 to i64
    %t2733 = call i64 @freak_llvm_word_eq(i64 %t2730, i64 %t2732)
    %t2737 = icmp ne i64 %t2733, 0
    br i1 %t2737, label %if.then.2734, label %if.else.2735
if.then.2734:
    %t2738 = load i64, i64* %ps_out_v2688
    %t2739 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.137, i64 0, i64 0
    %t2740 = ptrtoint i8* %t2739 to i64
    %t2741 = call i64 @freak_llvm_word_concat(i64 %t2738, i64 %t2740)
    store i64 %t2741, i64* %ps_out_v2688
    br label %if.end.2736
if.else.2735:
    %t2742 = load i64, i64* %esc_v2717
    %t2743 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.138, i64 0, i64 0
    %t2744 = ptrtoint i8* %t2743 to i64
    %t2745 = call i64 @freak_llvm_word_eq(i64 %t2742, i64 %t2744)
    %t2749 = icmp ne i64 %t2745, 0
    br i1 %t2749, label %if.then.2746, label %if.else.2747
if.then.2746:
    %t2750 = load i64, i64* %ps_out_v2688
    %t2751 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.139, i64 0, i64 0
    %t2752 = ptrtoint i8* %t2751 to i64
    %t2753 = call i64 @freak_llvm_word_concat(i64 %t2750, i64 %t2752)
    store i64 %t2753, i64* %ps_out_v2688
    br label %if.end.2748
if.else.2747:
    %t2754 = load i64, i64* %esc_v2717
    %t2755 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.140, i64 0, i64 0
    %t2756 = ptrtoint i8* %t2755 to i64
    %t2757 = call i64 @freak_llvm_word_eq(i64 %t2754, i64 %t2756)
    %t2761 = icmp ne i64 %t2757, 0
    br i1 %t2761, label %if.then.2758, label %if.else.2759
if.then.2758:
    %t2762 = load i64, i64* %ps_out_v2688
    %t2763 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.141, i64 0, i64 0
    %t2764 = ptrtoint i8* %t2763 to i64
    %t2765 = call i64 @freak_llvm_word_concat(i64 %t2762, i64 %t2764)
    store i64 %t2765, i64* %ps_out_v2688
    br label %if.end.2760
if.else.2759:
    %t2766 = load i64, i64* %esc_v2717
    %t2767 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.142, i64 0, i64 0
    %t2768 = ptrtoint i8* %t2767 to i64
    %t2769 = call i64 @freak_llvm_word_eq(i64 %t2766, i64 %t2768)
    %t2773 = icmp ne i64 %t2769, 0
    br i1 %t2773, label %if.then.2770, label %if.else.2771
if.then.2770:
    %t2774 = load i64, i64* %ps_out_v2688
    %t2775 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.143, i64 0, i64 0
    %t2776 = ptrtoint i8* %t2775 to i64
    %t2777 = call i64 @freak_llvm_word_concat(i64 %t2774, i64 %t2776)
    store i64 %t2777, i64* %ps_out_v2688
    br label %if.end.2772
if.else.2771:
    %t2778 = load i64, i64* %esc_v2717
    %t2779 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.144, i64 0, i64 0
    %t2780 = ptrtoint i8* %t2779 to i64
    %t2781 = call i64 @freak_llvm_word_eq(i64 %t2778, i64 %t2780)
    %t2785 = icmp ne i64 %t2781, 0
    br i1 %t2785, label %if.then.2782, label %if.else.2783
if.then.2782:
    %t2786 = load i64, i64* %ps_out_v2688
    %t2787 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.145, i64 0, i64 0
    %t2788 = ptrtoint i8* %t2787 to i64
    %t2789 = call i64 @freak_llvm_word_concat(i64 %t2786, i64 %t2788)
    store i64 %t2789, i64* %ps_out_v2688
    br label %if.end.2784
if.else.2783:
    %t2790 = load i64, i64* %ps_out_v2688
    %t2791 = load i64, i64* %esc_v2717
    %t2792 = call i64 @freak_llvm_word_concat(i64 %t2790, i64 %t2791)
    store i64 %t2792, i64* %ps_out_v2688
    br label %if.end.2784
if.end.2784:
    br label %if.end.2772
if.end.2772:
    br label %if.end.2760
if.end.2760:
    br label %if.end.2748
if.end.2748:
    br label %if.end.2736
if.end.2736:
    br label %if.end.2724
if.end.2724:
    br label %if.end.2714
if.else.2713:
    %t2793 = load i64, i64* %ps_out_v2688
    %t2794 = load i64, i64* %c_v2698
    %t2795 = call i64 @freak_llvm_word_concat(i64 %t2793, i64 %t2794)
    store i64 %t2795, i64* %ps_out_v2688
    br label %if.end.2714
if.end.2714:
    br label %loop.cond.2689
loop.end.2691:
    %t2796 = load i64, i64* %ps_out_v2688
    ret i64 %t2796
    ret i64 0
}

define i64 @freak_json_parse_number() {
entry:
    %t2797 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.146, i64 0, i64 0
    %t2798 = ptrtoint i8* %t2797 to i64
    %pn_out_v2799 = alloca i64
    store i64 %t2798, i64* %pn_out_v2799
    %t2800 = call i64 @freak_json_cur()
    %c_v2801 = alloca i64
    store i64 %t2800, i64* %c_v2801
    %t2802 = load i64, i64* %c_v2801
    %t2803 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.147, i64 0, i64 0
    %t2804 = ptrtoint i8* %t2803 to i64
    %t2805 = call i64 @freak_llvm_word_eq(i64 %t2802, i64 %t2804)
    %t2809 = icmp ne i64 %t2805, 0
    br i1 %t2809, label %if.then.2806, label %if.end.2808
if.then.2806:
    %t2810 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.148, i64 0, i64 0
    %t2811 = ptrtoint i8* %t2810 to i64
    store i64 %t2811, i64* %pn_out_v2799
    %t2812 = load i64, i64* @g_json_pos
    %t2813 = add i64 %t2812, 1
    store i64 %t2813, i64* @g_json_pos
    br label %if.end.2808
if.end.2808:
    br label %loop.cond.2814
loop.cond.2814:
    %t2817 = load i64, i64* @g_json_pos
    %t2818 = load i64, i64* @g_json_len
    %t2820 = icmp sge i64 %t2817, %t2818
    %t2819 = zext i1 %t2820 to i64
    %t2821 = icmp eq i64 %t2819, 0
    br i1 %t2821, label %loop.body.2815, label %loop.end.2816
loop.body.2815:
    %t2822 = call i64 @freak_json_cur()
    store i64 %t2822, i64* %c_v2801
    %t2823 = load i64, i64* %c_v2801
    %t2824 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.149, i64 0, i64 0
    %t2825 = ptrtoint i8* %t2824 to i64
    %t2826 = call i64 @freak_llvm_word_eq(i64 %t2823, i64 %t2825)
    %t2827 = load i64, i64* %c_v2801
    %t2828 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.150, i64 0, i64 0
    %t2829 = ptrtoint i8* %t2828 to i64
    %t2830 = call i64 @freak_llvm_word_eq(i64 %t2827, i64 %t2829)
    %t2832 = icmp ne i64 %t2826, 0
    %t2833 = icmp ne i64 %t2830, 0
    %t2834 = or i1 %t2832, %t2833
    %t2831 = zext i1 %t2834 to i64
    %t2835 = load i64, i64* %c_v2801
    %t2836 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.151, i64 0, i64 0
    %t2837 = ptrtoint i8* %t2836 to i64
    %t2838 = call i64 @freak_llvm_word_eq(i64 %t2835, i64 %t2837)
    %t2840 = icmp ne i64 %t2831, 0
    %t2841 = icmp ne i64 %t2838, 0
    %t2842 = or i1 %t2840, %t2841
    %t2839 = zext i1 %t2842 to i64
    %t2843 = load i64, i64* %c_v2801
    %t2844 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.152, i64 0, i64 0
    %t2845 = ptrtoint i8* %t2844 to i64
    %t2846 = call i64 @freak_llvm_word_eq(i64 %t2843, i64 %t2845)
    %t2848 = icmp ne i64 %t2839, 0
    %t2849 = icmp ne i64 %t2846, 0
    %t2850 = or i1 %t2848, %t2849
    %t2847 = zext i1 %t2850 to i64
    %t2851 = load i64, i64* %c_v2801
    %t2852 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.153, i64 0, i64 0
    %t2853 = ptrtoint i8* %t2852 to i64
    %t2854 = call i64 @freak_llvm_word_eq(i64 %t2851, i64 %t2853)
    %t2856 = icmp ne i64 %t2847, 0
    %t2857 = icmp ne i64 %t2854, 0
    %t2858 = or i1 %t2856, %t2857
    %t2855 = zext i1 %t2858 to i64
    %t2859 = load i64, i64* %c_v2801
    %t2860 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.154, i64 0, i64 0
    %t2861 = ptrtoint i8* %t2860 to i64
    %t2862 = call i64 @freak_llvm_word_eq(i64 %t2859, i64 %t2861)
    %t2864 = icmp ne i64 %t2855, 0
    %t2865 = icmp ne i64 %t2862, 0
    %t2866 = or i1 %t2864, %t2865
    %t2863 = zext i1 %t2866 to i64
    %t2867 = load i64, i64* %c_v2801
    %t2868 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.155, i64 0, i64 0
    %t2869 = ptrtoint i8* %t2868 to i64
    %t2870 = call i64 @freak_llvm_word_eq(i64 %t2867, i64 %t2869)
    %t2872 = icmp ne i64 %t2863, 0
    %t2873 = icmp ne i64 %t2870, 0
    %t2874 = or i1 %t2872, %t2873
    %t2871 = zext i1 %t2874 to i64
    %t2875 = load i64, i64* %c_v2801
    %t2876 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.156, i64 0, i64 0
    %t2877 = ptrtoint i8* %t2876 to i64
    %t2878 = call i64 @freak_llvm_word_eq(i64 %t2875, i64 %t2877)
    %t2880 = icmp ne i64 %t2871, 0
    %t2881 = icmp ne i64 %t2878, 0
    %t2882 = or i1 %t2880, %t2881
    %t2879 = zext i1 %t2882 to i64
    %t2883 = load i64, i64* %c_v2801
    %t2884 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.157, i64 0, i64 0
    %t2885 = ptrtoint i8* %t2884 to i64
    %t2886 = call i64 @freak_llvm_word_eq(i64 %t2883, i64 %t2885)
    %t2888 = icmp ne i64 %t2879, 0
    %t2889 = icmp ne i64 %t2886, 0
    %t2890 = or i1 %t2888, %t2889
    %t2887 = zext i1 %t2890 to i64
    %t2891 = load i64, i64* %c_v2801
    %t2892 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.158, i64 0, i64 0
    %t2893 = ptrtoint i8* %t2892 to i64
    %t2894 = call i64 @freak_llvm_word_eq(i64 %t2891, i64 %t2893)
    %t2896 = icmp ne i64 %t2887, 0
    %t2897 = icmp ne i64 %t2894, 0
    %t2898 = or i1 %t2896, %t2897
    %t2895 = zext i1 %t2898 to i64
    %t2899 = load i64, i64* %c_v2801
    %t2900 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.159, i64 0, i64 0
    %t2901 = ptrtoint i8* %t2900 to i64
    %t2902 = call i64 @freak_llvm_word_eq(i64 %t2899, i64 %t2901)
    %t2904 = icmp ne i64 %t2895, 0
    %t2905 = icmp ne i64 %t2902, 0
    %t2906 = or i1 %t2904, %t2905
    %t2903 = zext i1 %t2906 to i64
    %t2910 = icmp ne i64 %t2903, 0
    br i1 %t2910, label %if.then.2907, label %if.else.2908
if.then.2907:
    %t2911 = load i64, i64* %pn_out_v2799
    %t2912 = load i64, i64* %c_v2801
    %t2913 = call i64 @freak_llvm_word_concat(i64 %t2911, i64 %t2912)
    store i64 %t2913, i64* %pn_out_v2799
    %t2914 = load i64, i64* @g_json_pos
    %t2915 = add i64 %t2914, 1
    store i64 %t2915, i64* @g_json_pos
    br label %if.end.2909
if.else.2908:
    %t2916 = load i64, i64* %pn_out_v2799
    ret i64 %t2916
    br label %if.end.2909
if.end.2909:
    br label %loop.cond.2814
loop.end.2816:
    %t2917 = load i64, i64* %pn_out_v2799
    ret i64 %t2917
    ret i64 0
}

define i64 @freak_json_try_keyword(i64 %arg_kw) {
entry:
    %kw = alloca i64
    store i64 %arg_kw, i64* %kw
    %t2918 = load i64, i64* %kw
    %t2919 = call i64 @freak_llvm_word_length(i64 %t2918)
    %kwlen_v2920 = alloca i64
    store i64 %t2919, i64* %kwlen_v2920
    %t2921 = load i64, i64* @g_json_pos
    %t2922 = load i64, i64* %kwlen_v2920
    %t2923 = add i64 %t2921, %t2922
    %t2924 = load i64, i64* @g_json_len
    %t2926 = icmp sgt i64 %t2923, %t2924
    %t2925 = zext i1 %t2926 to i64
    %t2930 = icmp ne i64 %t2925, 0
    br i1 %t2930, label %if.then.2927, label %if.end.2929
if.then.2927:
    ret i64 0
    br label %if.end.2929
if.end.2929:
    %ki_v2931 = alloca i64
    store i64 0, i64* %ki_v2931
    %t2937 = load i64, i64* %kwlen_v2920
    %rep.2936 = alloca i64
    store i64 0, i64* %rep.2936
    br label %loop.cond.2932
loop.cond.2932:
    %t2938 = load i64, i64* %rep.2936
    %t2939 = icmp slt i64 %t2938, %t2937
    br i1 %t2939, label %loop.body.2933, label %loop.end.2934
loop.body.2933:
    %t2940 = load i64, i64* @g_json_src
    %t2942 = load i64, i64* @g_json_pos
    %t2943 = load i64, i64* %ki_v2931
    %t2944 = add i64 %t2942, %t2943
    %t2941 = call i64 @freak_llvm_word_char_at(i64 %t2940, i64 %t2944)
    %t2945 = load i64, i64* %kw
    %t2947 = load i64, i64* %ki_v2931
    %t2946 = call i64 @freak_llvm_word_char_at(i64 %t2945, i64 %t2947)
    %t2948 = call i64 @freak_llvm_word_neq(i64 %t2941, i64 %t2946)
    %t2952 = icmp ne i64 %t2948, 0
    br i1 %t2952, label %if.then.2949, label %if.end.2951
if.then.2949:
    ret i64 0
    br label %if.end.2951
if.end.2951:
    %t2953 = load i64, i64* %ki_v2931
    %t2954 = add i64 %t2953, 1
    store i64 %t2954, i64* %ki_v2931
    br label %loop.inc.2935
loop.inc.2935:
    %t2955 = load i64, i64* %rep.2936
    %t2956 = add i64 %t2955, 1
    store i64 %t2956, i64* %rep.2936
    br label %loop.cond.2932
loop.end.2934:
    %t2957 = load i64, i64* %kwlen_v2920
    %t2958 = load i64, i64* @g_json_pos
    %t2959 = add i64 %t2958, %t2957
    store i64 %t2959, i64* @g_json_pos
    ret i64 1
    ret i64 0
}

define i64 @freak_json_parse_value() {
entry:
    call void @freak_json_skip_ws()
    %t2960 = call i64 @freak_json_cur()
    %c_v2961 = alloca i64
    store i64 %t2960, i64* %c_v2961
    %t2962 = load i64, i64* %c_v2961
    %t2963 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.160, i64 0, i64 0
    %t2964 = ptrtoint i8* %t2963 to i64
    %t2965 = call i64 @freak_llvm_word_eq(i64 %t2962, i64 %t2964)
    %t2969 = icmp ne i64 %t2965, 0
    br i1 %t2969, label %if.then.2966, label %if.end.2968
if.then.2966:
    %t2970 = call i64 @freak_json_parse_string()
    %sv_v2971 = alloca i64
    store i64 %t2970, i64* %sv_v2971
    %t2972 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.161, i64 0, i64 0
    %t2973 = ptrtoint i8* %t2972 to i64
    %t2974 = load i64, i64* %sv_v2971
    %t2975 = call i64 @freak_json_alloc(i64 %t2973, i64 %t2974)
    ret i64 %t2975
    br label %if.end.2968
if.end.2968:
    %t2976 = load i64, i64* %c_v2961
    %t2977 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.162, i64 0, i64 0
    %t2978 = ptrtoint i8* %t2977 to i64
    %t2979 = call i64 @freak_llvm_word_eq(i64 %t2976, i64 %t2978)
    %t2980 = load i64, i64* %c_v2961
    %t2981 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.163, i64 0, i64 0
    %t2982 = ptrtoint i8* %t2981 to i64
    %t2983 = call i64 @freak_llvm_word_eq(i64 %t2980, i64 %t2982)
    %t2985 = icmp ne i64 %t2979, 0
    %t2986 = icmp ne i64 %t2983, 0
    %t2987 = or i1 %t2985, %t2986
    %t2984 = zext i1 %t2987 to i64
    %t2988 = load i64, i64* %c_v2961
    %t2989 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.164, i64 0, i64 0
    %t2990 = ptrtoint i8* %t2989 to i64
    %t2991 = call i64 @freak_llvm_word_eq(i64 %t2988, i64 %t2990)
    %t2993 = icmp ne i64 %t2984, 0
    %t2994 = icmp ne i64 %t2991, 0
    %t2995 = or i1 %t2993, %t2994
    %t2992 = zext i1 %t2995 to i64
    %t2996 = load i64, i64* %c_v2961
    %t2997 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.165, i64 0, i64 0
    %t2998 = ptrtoint i8* %t2997 to i64
    %t2999 = call i64 @freak_llvm_word_eq(i64 %t2996, i64 %t2998)
    %t3001 = icmp ne i64 %t2992, 0
    %t3002 = icmp ne i64 %t2999, 0
    %t3003 = or i1 %t3001, %t3002
    %t3000 = zext i1 %t3003 to i64
    %t3004 = load i64, i64* %c_v2961
    %t3005 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.166, i64 0, i64 0
    %t3006 = ptrtoint i8* %t3005 to i64
    %t3007 = call i64 @freak_llvm_word_eq(i64 %t3004, i64 %t3006)
    %t3009 = icmp ne i64 %t3000, 0
    %t3010 = icmp ne i64 %t3007, 0
    %t3011 = or i1 %t3009, %t3010
    %t3008 = zext i1 %t3011 to i64
    %t3012 = load i64, i64* %c_v2961
    %t3013 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.167, i64 0, i64 0
    %t3014 = ptrtoint i8* %t3013 to i64
    %t3015 = call i64 @freak_llvm_word_eq(i64 %t3012, i64 %t3014)
    %t3017 = icmp ne i64 %t3008, 0
    %t3018 = icmp ne i64 %t3015, 0
    %t3019 = or i1 %t3017, %t3018
    %t3016 = zext i1 %t3019 to i64
    %t3020 = load i64, i64* %c_v2961
    %t3021 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.168, i64 0, i64 0
    %t3022 = ptrtoint i8* %t3021 to i64
    %t3023 = call i64 @freak_llvm_word_eq(i64 %t3020, i64 %t3022)
    %t3025 = icmp ne i64 %t3016, 0
    %t3026 = icmp ne i64 %t3023, 0
    %t3027 = or i1 %t3025, %t3026
    %t3024 = zext i1 %t3027 to i64
    %t3028 = load i64, i64* %c_v2961
    %t3029 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.169, i64 0, i64 0
    %t3030 = ptrtoint i8* %t3029 to i64
    %t3031 = call i64 @freak_llvm_word_eq(i64 %t3028, i64 %t3030)
    %t3033 = icmp ne i64 %t3024, 0
    %t3034 = icmp ne i64 %t3031, 0
    %t3035 = or i1 %t3033, %t3034
    %t3032 = zext i1 %t3035 to i64
    %t3036 = load i64, i64* %c_v2961
    %t3037 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.170, i64 0, i64 0
    %t3038 = ptrtoint i8* %t3037 to i64
    %t3039 = call i64 @freak_llvm_word_eq(i64 %t3036, i64 %t3038)
    %t3041 = icmp ne i64 %t3032, 0
    %t3042 = icmp ne i64 %t3039, 0
    %t3043 = or i1 %t3041, %t3042
    %t3040 = zext i1 %t3043 to i64
    %t3044 = load i64, i64* %c_v2961
    %t3045 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.171, i64 0, i64 0
    %t3046 = ptrtoint i8* %t3045 to i64
    %t3047 = call i64 @freak_llvm_word_eq(i64 %t3044, i64 %t3046)
    %t3049 = icmp ne i64 %t3040, 0
    %t3050 = icmp ne i64 %t3047, 0
    %t3051 = or i1 %t3049, %t3050
    %t3048 = zext i1 %t3051 to i64
    %t3052 = load i64, i64* %c_v2961
    %t3053 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.172, i64 0, i64 0
    %t3054 = ptrtoint i8* %t3053 to i64
    %t3055 = call i64 @freak_llvm_word_eq(i64 %t3052, i64 %t3054)
    %t3057 = icmp ne i64 %t3048, 0
    %t3058 = icmp ne i64 %t3055, 0
    %t3059 = or i1 %t3057, %t3058
    %t3056 = zext i1 %t3059 to i64
    %t3063 = icmp ne i64 %t3056, 0
    br i1 %t3063, label %if.then.3060, label %if.end.3062
if.then.3060:
    %t3064 = call i64 @freak_json_parse_number()
    %nv_v3065 = alloca i64
    store i64 %t3064, i64* %nv_v3065
    %t3066 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.173, i64 0, i64 0
    %t3067 = ptrtoint i8* %t3066 to i64
    %t3068 = load i64, i64* %nv_v3065
    %t3069 = call i64 @freak_json_alloc(i64 %t3067, i64 %t3068)
    ret i64 %t3069
    br label %if.end.3062
if.end.3062:
    %t3070 = load i64, i64* %c_v2961
    %t3071 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.174, i64 0, i64 0
    %t3072 = ptrtoint i8* %t3071 to i64
    %t3073 = call i64 @freak_llvm_word_eq(i64 %t3070, i64 %t3072)
    %t3077 = icmp ne i64 %t3073, 0
    br i1 %t3077, label %if.then.3074, label %if.end.3076
if.then.3074:
    %t3078 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.175, i64 0, i64 0
    %t3079 = ptrtoint i8* %t3078 to i64
    %t3080 = call i64 @freak_json_try_keyword(i64 %t3079)
    %t3084 = icmp ne i64 %t3080, 0
    br i1 %t3084, label %if.then.3081, label %if.end.3083
if.then.3081:
    %t3085 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.176, i64 0, i64 0
    %t3086 = ptrtoint i8* %t3085 to i64
    %t3087 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.177, i64 0, i64 0
    %t3088 = ptrtoint i8* %t3087 to i64
    %t3089 = call i64 @freak_json_alloc(i64 %t3086, i64 %t3088)
    ret i64 %t3089
    br label %if.end.3083
if.end.3083:
    br label %if.end.3076
if.end.3076:
    %t3090 = load i64, i64* %c_v2961
    %t3091 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.178, i64 0, i64 0
    %t3092 = ptrtoint i8* %t3091 to i64
    %t3093 = call i64 @freak_llvm_word_eq(i64 %t3090, i64 %t3092)
    %t3097 = icmp ne i64 %t3093, 0
    br i1 %t3097, label %if.then.3094, label %if.end.3096
if.then.3094:
    %t3098 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.179, i64 0, i64 0
    %t3099 = ptrtoint i8* %t3098 to i64
    %t3100 = call i64 @freak_json_try_keyword(i64 %t3099)
    %t3104 = icmp ne i64 %t3100, 0
    br i1 %t3104, label %if.then.3101, label %if.end.3103
if.then.3101:
    %t3105 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.180, i64 0, i64 0
    %t3106 = ptrtoint i8* %t3105 to i64
    %t3107 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.181, i64 0, i64 0
    %t3108 = ptrtoint i8* %t3107 to i64
    %t3109 = call i64 @freak_json_alloc(i64 %t3106, i64 %t3108)
    ret i64 %t3109
    br label %if.end.3103
if.end.3103:
    br label %if.end.3096
if.end.3096:
    %t3110 = load i64, i64* %c_v2961
    %t3111 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.182, i64 0, i64 0
    %t3112 = ptrtoint i8* %t3111 to i64
    %t3113 = call i64 @freak_llvm_word_eq(i64 %t3110, i64 %t3112)
    %t3117 = icmp ne i64 %t3113, 0
    br i1 %t3117, label %if.then.3114, label %if.end.3116
if.then.3114:
    %t3118 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.183, i64 0, i64 0
    %t3119 = ptrtoint i8* %t3118 to i64
    %t3120 = call i64 @freak_json_try_keyword(i64 %t3119)
    %t3124 = icmp ne i64 %t3120, 0
    br i1 %t3124, label %if.then.3121, label %if.end.3123
if.then.3121:
    %t3125 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.184, i64 0, i64 0
    %t3126 = ptrtoint i8* %t3125 to i64
    %t3127 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.185, i64 0, i64 0
    %t3128 = ptrtoint i8* %t3127 to i64
    %t3129 = call i64 @freak_json_alloc(i64 %t3126, i64 %t3128)
    ret i64 %t3129
    br label %if.end.3123
if.end.3123:
    br label %if.end.3116
if.end.3116:
    %t3130 = load i64, i64* %c_v2961
    %t3131 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.186, i64 0, i64 0
    %t3132 = ptrtoint i8* %t3131 to i64
    %t3133 = call i64 @freak_llvm_word_eq(i64 %t3130, i64 %t3132)
    %t3137 = icmp ne i64 %t3133, 0
    br i1 %t3137, label %if.then.3134, label %if.end.3136
if.then.3134:
    %t3138 = load i64, i64* @g_json_pos
    %t3139 = add i64 %t3138, 1
    store i64 %t3139, i64* @g_json_pos
    %t3140 = call i64 @freak_llvm_array_new()
    %arr_children_v3141 = alloca i64
    store i64 %t3140, i64* %arr_children_v3141
    %t3142 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.187, i64 0, i64 0
    %t3143 = ptrtoint i8* %t3142 to i64
    %t3144 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.188, i64 0, i64 0
    %t3145 = ptrtoint i8* %t3144 to i64
    %t3146 = call i64 @freak_json_alloc(i64 %t3143, i64 %t3145)
    %arr_handle_v3147 = alloca i64
    store i64 %t3146, i64* %arr_handle_v3147
    %t3148 = load i64, i64* @g_json_children
    %t3149 = load i64, i64* %arr_handle_v3147
    %t3150 = load i64, i64* %arr_children_v3141
    %t3151 = call i64 @freak_llvm_word_from_int(i64 %t3150)
    call void @freak_llvm_array_set(i64 %t3148, i64 %t3149, i64 %t3151)
    call void @freak_json_skip_ws()
    %t3152 = call i64 @freak_json_cur()
    %t3153 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.189, i64 0, i64 0
    %t3154 = ptrtoint i8* %t3153 to i64
    %t3155 = call i64 @freak_llvm_word_neq(i64 %t3152, i64 %t3154)
    %t3159 = icmp ne i64 %t3155, 0
    br i1 %t3159, label %if.then.3156, label %if.end.3158
if.then.3156:
    %t3160 = call i64 @freak_json_parse_value()
    %first_val_v3161 = alloca i64
    store i64 %t3160, i64* %first_val_v3161
    %t3162 = load i64, i64* %arr_children_v3141
    %t3163 = load i64, i64* %first_val_v3161
    %t3164 = call i64 @freak_llvm_word_from_int(i64 %t3163)
    call void @freak_llvm_array_push(i64 %t3162, i64 %t3164)
    call void @freak_json_skip_ws()
    br label %loop.cond.3165
loop.cond.3165:
    %t3168 = call i64 @freak_json_cur()
    %t3169 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.190, i64 0, i64 0
    %t3170 = ptrtoint i8* %t3169 to i64
    %t3171 = call i64 @freak_llvm_word_neq(i64 %t3168, i64 %t3170)
    %t3172 = icmp eq i64 %t3171, 0
    br i1 %t3172, label %loop.body.3166, label %loop.end.3167
loop.body.3166:
    %t3173 = load i64, i64* @g_json_pos
    %t3174 = add i64 %t3173, 1
    store i64 %t3174, i64* @g_json_pos
    %t3175 = call i64 @freak_json_parse_value()
    %next_val_v3176 = alloca i64
    store i64 %t3175, i64* %next_val_v3176
    %t3177 = load i64, i64* %arr_children_v3141
    %t3178 = load i64, i64* %next_val_v3176
    %t3179 = call i64 @freak_llvm_word_from_int(i64 %t3178)
    call void @freak_llvm_array_push(i64 %t3177, i64 %t3179)
    call void @freak_json_skip_ws()
    br label %loop.cond.3165
loop.end.3167:
    br label %if.end.3158
if.end.3158:
    %t3180 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.191, i64 0, i64 0
    %t3181 = ptrtoint i8* %t3180 to i64
    call void @freak_json_expect(i64 %t3181)
    %t3182 = load i64, i64* %arr_handle_v3147
    ret i64 %t3182
    br label %if.end.3136
if.end.3136:
    %t3183 = load i64, i64* %c_v2961
    %t3184 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.192, i64 0, i64 0
    %t3185 = ptrtoint i8* %t3184 to i64
    %t3186 = call i64 @freak_llvm_word_eq(i64 %t3183, i64 %t3185)
    %t3190 = icmp ne i64 %t3186, 0
    br i1 %t3190, label %if.then.3187, label %if.end.3189
if.then.3187:
    %t3191 = load i64, i64* @g_json_pos
    %t3192 = add i64 %t3191, 1
    store i64 %t3192, i64* @g_json_pos
    %t3193 = call i64 @freak_llvm_array_new()
    %obj_children_v3194 = alloca i64
    store i64 %t3193, i64* %obj_children_v3194
    %t3195 = call i64 @freak_llvm_array_new()
    %obj_keys_v3196 = alloca i64
    store i64 %t3195, i64* %obj_keys_v3196
    %t3197 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.193, i64 0, i64 0
    %t3198 = ptrtoint i8* %t3197 to i64
    %t3199 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.194, i64 0, i64 0
    %t3200 = ptrtoint i8* %t3199 to i64
    %t3201 = call i64 @freak_json_alloc(i64 %t3198, i64 %t3200)
    %obj_handle_v3202 = alloca i64
    store i64 %t3201, i64* %obj_handle_v3202
    %t3203 = load i64, i64* @g_json_children
    %t3204 = load i64, i64* %obj_handle_v3202
    %t3205 = load i64, i64* %obj_children_v3194
    %t3206 = call i64 @freak_llvm_word_from_int(i64 %t3205)
    call void @freak_llvm_array_set(i64 %t3203, i64 %t3204, i64 %t3206)
    %t3207 = load i64, i64* @g_json_keys
    %t3208 = load i64, i64* %obj_handle_v3202
    %t3209 = load i64, i64* %obj_keys_v3196
    %t3210 = call i64 @freak_llvm_word_from_int(i64 %t3209)
    call void @freak_llvm_array_set(i64 %t3207, i64 %t3208, i64 %t3210)
    call void @freak_json_skip_ws()
    %t3211 = call i64 @freak_json_cur()
    %t3212 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.195, i64 0, i64 0
    %t3213 = ptrtoint i8* %t3212 to i64
    %t3214 = call i64 @freak_llvm_word_neq(i64 %t3211, i64 %t3213)
    %t3218 = icmp ne i64 %t3214, 0
    br i1 %t3218, label %if.then.3215, label %if.end.3217
if.then.3215:
    %t3219 = call i64 @freak_json_parse_string()
    %k1_v3220 = alloca i64
    store i64 %t3219, i64* %k1_v3220
    call void @freak_json_skip_ws()
    %t3221 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.196, i64 0, i64 0
    %t3222 = ptrtoint i8* %t3221 to i64
    call void @freak_json_expect(i64 %t3222)
    %t3223 = call i64 @freak_json_parse_value()
    %v1_v3224 = alloca i64
    store i64 %t3223, i64* %v1_v3224
    %t3225 = load i64, i64* %obj_keys_v3196
    %t3226 = load i64, i64* %k1_v3220
    call void @freak_llvm_array_push(i64 %t3225, i64 %t3226)
    %t3227 = load i64, i64* %obj_children_v3194
    %t3228 = load i64, i64* %v1_v3224
    %t3229 = call i64 @freak_llvm_word_from_int(i64 %t3228)
    call void @freak_llvm_array_push(i64 %t3227, i64 %t3229)
    call void @freak_json_skip_ws()
    br label %loop.cond.3230
loop.cond.3230:
    %t3233 = call i64 @freak_json_cur()
    %t3234 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.197, i64 0, i64 0
    %t3235 = ptrtoint i8* %t3234 to i64
    %t3236 = call i64 @freak_llvm_word_neq(i64 %t3233, i64 %t3235)
    %t3237 = icmp eq i64 %t3236, 0
    br i1 %t3237, label %loop.body.3231, label %loop.end.3232
loop.body.3231:
    %t3238 = load i64, i64* @g_json_pos
    %t3239 = add i64 %t3238, 1
    store i64 %t3239, i64* @g_json_pos
    call void @freak_json_skip_ws()
    %t3240 = call i64 @freak_json_parse_string()
    %kn_v3241 = alloca i64
    store i64 %t3240, i64* %kn_v3241
    call void @freak_json_skip_ws()
    %t3242 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.198, i64 0, i64 0
    %t3243 = ptrtoint i8* %t3242 to i64
    call void @freak_json_expect(i64 %t3243)
    %t3244 = call i64 @freak_json_parse_value()
    %vn_v3245 = alloca i64
    store i64 %t3244, i64* %vn_v3245
    %t3246 = load i64, i64* %obj_keys_v3196
    %t3247 = load i64, i64* %kn_v3241
    call void @freak_llvm_array_push(i64 %t3246, i64 %t3247)
    %t3248 = load i64, i64* %obj_children_v3194
    %t3249 = load i64, i64* %vn_v3245
    %t3250 = call i64 @freak_llvm_word_from_int(i64 %t3249)
    call void @freak_llvm_array_push(i64 %t3248, i64 %t3250)
    call void @freak_json_skip_ws()
    br label %loop.cond.3230
loop.end.3232:
    br label %if.end.3217
if.end.3217:
    %t3251 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.199, i64 0, i64 0
    %t3252 = ptrtoint i8* %t3251 to i64
    call void @freak_json_expect(i64 %t3252)
    %t3253 = load i64, i64* %obj_handle_v3202
    ret i64 %t3253
    br label %if.end.3189
if.end.3189:
    %t3254 = getelementptr inbounds [31 x i8], [31 x i8]* @.str.200, i64 0, i64 0
    %t3255 = ptrtoint i8* %t3254 to i64
    %t3256 = load i64, i64* %c_v2961
    %t3257 = call i64 @freak_llvm_word_concat(i64 %t3255, i64 %t3256)
    %t3258 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.201, i64 0, i64 0
    %t3259 = ptrtoint i8* %t3258 to i64
    %t3260 = call i64 @freak_llvm_word_concat(i64 %t3257, i64 %t3259)
    call void @freak_llvm_say(i64 %t3260)
    %t3261 = sub i64 0, 1
    ret i64 %t3261
    ret i64 0
}

define i64 @freak_json_parse(i64 %arg_source) {
entry:
    %source = alloca i64
    store i64 %arg_source, i64* %source
    call void @freak_json_init()
    %t3262 = load i64, i64* %source
    store i64 %t3262, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    %t3263 = load i64, i64* %source
    %t3264 = call i64 @freak_llvm_word_length(i64 %t3263)
    store i64 %t3264, i64* @g_json_len
    %t3265 = call i64 @freak_json_parse_value()
    ret i64 %t3265
    ret i64 0
}

define i64 @freak_json_stringify(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t3266 = load i64, i64* %handle
    %t3268 = icmp slt i64 %t3266, 0
    %t3267 = zext i1 %t3268 to i64
    %t3272 = icmp ne i64 %t3267, 0
    br i1 %t3272, label %if.then.3269, label %if.end.3271
if.then.3269:
    %t3273 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.202, i64 0, i64 0
    %t3274 = ptrtoint i8* %t3273 to i64
    ret i64 %t3274
    br label %if.end.3271
if.end.3271:
    %t3275 = load i64, i64* @g_json_types
    %t3276 = load i64, i64* %handle
    %t3277 = call i64 @freak_llvm_array_get(i64 %t3275, i64 %t3276)
    %t_v3278 = alloca i64
    store i64 %t3277, i64* %t_v3278
    %t3279 = load i64, i64* %t_v3278
    %t3280 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.203, i64 0, i64 0
    %t3281 = ptrtoint i8* %t3280 to i64
    %t3282 = call i64 @freak_llvm_word_eq(i64 %t3279, i64 %t3281)
    %t3286 = icmp ne i64 %t3282, 0
    br i1 %t3286, label %if.then.3283, label %if.end.3285
if.then.3283:
    %t3287 = load i64, i64* @g_json_vals
    %t3288 = load i64, i64* %handle
    %t3289 = call i64 @freak_llvm_array_get(i64 %t3287, i64 %t3288)
    %sv_v3290 = alloca i64
    store i64 %t3289, i64* %sv_v3290
    %t3291 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.204, i64 0, i64 0
    %t3292 = ptrtoint i8* %t3291 to i64
    %t3293 = load i64, i64* %sv_v3290
    %t3294 = call i64 @freak_llvm_word_concat(i64 %t3292, i64 %t3293)
    %t3295 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.205, i64 0, i64 0
    %t3296 = ptrtoint i8* %t3295 to i64
    %t3297 = call i64 @freak_llvm_word_concat(i64 %t3294, i64 %t3296)
    ret i64 %t3297
    br label %if.end.3285
if.end.3285:
    %t3298 = load i64, i64* %t_v3278
    %t3299 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.206, i64 0, i64 0
    %t3300 = ptrtoint i8* %t3299 to i64
    %t3301 = call i64 @freak_llvm_word_eq(i64 %t3298, i64 %t3300)
    %t3305 = icmp ne i64 %t3301, 0
    br i1 %t3305, label %if.then.3302, label %if.end.3304
if.then.3302:
    %t3306 = load i64, i64* @g_json_vals
    %t3307 = load i64, i64* %handle
    %t3308 = call i64 @freak_llvm_array_get(i64 %t3306, i64 %t3307)
    ret i64 %t3308
    br label %if.end.3304
if.end.3304:
    %t3309 = load i64, i64* %t_v3278
    %t3310 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.207, i64 0, i64 0
    %t3311 = ptrtoint i8* %t3310 to i64
    %t3312 = call i64 @freak_llvm_word_eq(i64 %t3309, i64 %t3311)
    %t3316 = icmp ne i64 %t3312, 0
    br i1 %t3316, label %if.then.3313, label %if.end.3315
if.then.3313:
    %t3317 = load i64, i64* @g_json_vals
    %t3318 = load i64, i64* %handle
    %t3319 = call i64 @freak_llvm_array_get(i64 %t3317, i64 %t3318)
    ret i64 %t3319
    br label %if.end.3315
if.end.3315:
    %t3320 = load i64, i64* %t_v3278
    %t3321 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.208, i64 0, i64 0
    %t3322 = ptrtoint i8* %t3321 to i64
    %t3323 = call i64 @freak_llvm_word_eq(i64 %t3320, i64 %t3322)
    %t3327 = icmp ne i64 %t3323, 0
    br i1 %t3327, label %if.then.3324, label %if.end.3326
if.then.3324:
    %t3328 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.209, i64 0, i64 0
    %t3329 = ptrtoint i8* %t3328 to i64
    ret i64 %t3329
    br label %if.end.3326
if.end.3326:
    %t3330 = load i64, i64* %t_v3278
    %t3331 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.210, i64 0, i64 0
    %t3332 = ptrtoint i8* %t3331 to i64
    %t3333 = call i64 @freak_llvm_word_eq(i64 %t3330, i64 %t3332)
    %t3337 = icmp ne i64 %t3333, 0
    br i1 %t3337, label %if.then.3334, label %if.end.3336
if.then.3334:
    %t3338 = load i64, i64* %handle
    %t3339 = call i64 @freak_json_arr_len(i64 %t3338)
    %alen_v3340 = alloca i64
    store i64 %t3339, i64* %alen_v3340
    %t3341 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.211, i64 0, i64 0
    %t3342 = ptrtoint i8* %t3341 to i64
    %a_out_v3343 = alloca i64
    store i64 %t3342, i64* %a_out_v3343
    %ai_v3344 = alloca i64
    store i64 0, i64* %ai_v3344
    %t3350 = load i64, i64* %alen_v3340
    %rep.3349 = alloca i64
    store i64 0, i64* %rep.3349
    br label %loop.cond.3345
loop.cond.3345:
    %t3351 = load i64, i64* %rep.3349
    %t3352 = icmp slt i64 %t3351, %t3350
    br i1 %t3352, label %loop.body.3346, label %loop.end.3347
loop.body.3346:
    %t3353 = load i64, i64* %ai_v3344
    %t3355 = icmp sgt i64 %t3353, 0
    %t3354 = zext i1 %t3355 to i64
    %t3359 = icmp ne i64 %t3354, 0
    br i1 %t3359, label %if.then.3356, label %if.end.3358
if.then.3356:
    %t3360 = load i64, i64* %a_out_v3343
    %t3361 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.212, i64 0, i64 0
    %t3362 = ptrtoint i8* %t3361 to i64
    %t3363 = call i64 @freak_llvm_word_concat(i64 %t3360, i64 %t3362)
    store i64 %t3363, i64* %a_out_v3343
    br label %if.end.3358
if.end.3358:
    %t3364 = load i64, i64* %handle
    %t3365 = load i64, i64* %ai_v3344
    %t3366 = call i64 @freak_json_arr_get(i64 %t3364, i64 %t3365)
    %child_v3367 = alloca i64
    store i64 %t3366, i64* %child_v3367
    %t3368 = load i64, i64* %a_out_v3343
    %t3369 = load i64, i64* %child_v3367
    %t3370 = call i64 @freak_json_stringify(i64 %t3369)
    %t3371 = call i64 @freak_llvm_word_concat(i64 %t3368, i64 %t3370)
    store i64 %t3371, i64* %a_out_v3343
    %t3372 = load i64, i64* %ai_v3344
    %t3373 = add i64 %t3372, 1
    store i64 %t3373, i64* %ai_v3344
    br label %loop.inc.3348
loop.inc.3348:
    %t3374 = load i64, i64* %rep.3349
    %t3375 = add i64 %t3374, 1
    store i64 %t3375, i64* %rep.3349
    br label %loop.cond.3345
loop.end.3347:
    %t3376 = load i64, i64* %a_out_v3343
    %t3377 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.213, i64 0, i64 0
    %t3378 = ptrtoint i8* %t3377 to i64
    %t3379 = call i64 @freak_llvm_word_concat(i64 %t3376, i64 %t3378)
    ret i64 %t3379
    br label %if.end.3336
if.end.3336:
    %t3380 = load i64, i64* %t_v3278
    %t3381 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.214, i64 0, i64 0
    %t3382 = ptrtoint i8* %t3381 to i64
    %t3383 = call i64 @freak_llvm_word_eq(i64 %t3380, i64 %t3382)
    %t3387 = icmp ne i64 %t3383, 0
    br i1 %t3387, label %if.then.3384, label %if.end.3386
if.then.3384:
    %t3388 = load i64, i64* %handle
    %t3389 = call i64 @freak_json_obj_len(i64 %t3388)
    %olen_v3390 = alloca i64
    store i64 %t3389, i64* %olen_v3390
    %t3391 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.215, i64 0, i64 0
    %t3392 = ptrtoint i8* %t3391 to i64
    %o_out_v3393 = alloca i64
    store i64 %t3392, i64* %o_out_v3393
    %oi_v3394 = alloca i64
    store i64 0, i64* %oi_v3394
    %t3400 = load i64, i64* %olen_v3390
    %rep.3399 = alloca i64
    store i64 0, i64* %rep.3399
    br label %loop.cond.3395
loop.cond.3395:
    %t3401 = load i64, i64* %rep.3399
    %t3402 = icmp slt i64 %t3401, %t3400
    br i1 %t3402, label %loop.body.3396, label %loop.end.3397
loop.body.3396:
    %t3403 = load i64, i64* %oi_v3394
    %t3405 = icmp sgt i64 %t3403, 0
    %t3404 = zext i1 %t3405 to i64
    %t3409 = icmp ne i64 %t3404, 0
    br i1 %t3409, label %if.then.3406, label %if.end.3408
if.then.3406:
    %t3410 = load i64, i64* %o_out_v3393
    %t3411 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.216, i64 0, i64 0
    %t3412 = ptrtoint i8* %t3411 to i64
    %t3413 = call i64 @freak_llvm_word_concat(i64 %t3410, i64 %t3412)
    store i64 %t3413, i64* %o_out_v3393
    br label %if.end.3408
if.end.3408:
    %t3414 = load i64, i64* %handle
    %t3415 = load i64, i64* %oi_v3394
    %t3416 = call i64 @freak_json_obj_key_at(i64 %t3414, i64 %t3415)
    %okey_v3417 = alloca i64
    store i64 %t3416, i64* %okey_v3417
    %t3418 = load i64, i64* %handle
    %t3419 = load i64, i64* %oi_v3394
    %t3420 = call i64 @freak_json_arr_get(i64 %t3418, i64 %t3419)
    %ov_v3421 = alloca i64
    store i64 %t3420, i64* %ov_v3421
    %t3422 = load i64, i64* %o_out_v3393
    %t3423 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.217, i64 0, i64 0
    %t3424 = ptrtoint i8* %t3423 to i64
    %t3425 = call i64 @freak_llvm_word_concat(i64 %t3422, i64 %t3424)
    %t3426 = load i64, i64* %okey_v3417
    %t3427 = call i64 @freak_llvm_word_concat(i64 %t3425, i64 %t3426)
    %t3428 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.218, i64 0, i64 0
    %t3429 = ptrtoint i8* %t3428 to i64
    %t3430 = call i64 @freak_llvm_word_concat(i64 %t3427, i64 %t3429)
    %t3431 = load i64, i64* %ov_v3421
    %t3432 = call i64 @freak_json_stringify(i64 %t3431)
    %t3433 = call i64 @freak_llvm_word_concat(i64 %t3430, i64 %t3432)
    store i64 %t3433, i64* %o_out_v3393
    %t3434 = load i64, i64* %oi_v3394
    %t3435 = add i64 %t3434, 1
    store i64 %t3435, i64* %oi_v3394
    br label %loop.inc.3398
loop.inc.3398:
    %t3436 = load i64, i64* %rep.3399
    %t3437 = add i64 %t3436, 1
    store i64 %t3437, i64* %rep.3399
    br label %loop.cond.3395
loop.end.3397:
    %t3438 = load i64, i64* %o_out_v3393
    %t3439 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.219, i64 0, i64 0
    %t3440 = ptrtoint i8* %t3439 to i64
    %t3441 = call i64 @freak_llvm_word_concat(i64 %t3438, i64 %t3440)
    ret i64 %t3441
    br label %if.end.3386
if.end.3386:
    %t3442 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.220, i64 0, i64 0
    %t3443 = ptrtoint i8* %t3442 to i64
    ret i64 %t3443
    ret i64 0
}

define i64 @freak_ver_parse_num(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3444 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.221, i64 0, i64 0
    %t3445 = ptrtoint i8* %t3444 to i64
    %res_v3446 = alloca i64
    store i64 %t3445, i64* %res_v3446
    %t3447 = load i64, i64* %start
    %i_v3448 = alloca i64
    store i64 %t3447, i64* %i_v3448
    %t3449 = load i64, i64* @g_s
    %t3450 = call i64 @freak_llvm_word_length(i64 %t3449)
    %slen_v3451 = alloca i64
    store i64 %t3450, i64* %slen_v3451
    br label %loop.cond.3452
loop.cond.3452:
    %t3455 = load i64, i64* %i_v3448
    %t3456 = load i64, i64* %slen_v3451
    %t3458 = icmp sge i64 %t3455, %t3456
    %t3457 = zext i1 %t3458 to i64
    %t3459 = icmp eq i64 %t3457, 0
    br i1 %t3459, label %loop.body.3453, label %loop.end.3454
loop.body.3453:
    %t3460 = load i64, i64* @g_s
    %t3462 = load i64, i64* %i_v3448
    %t3461 = call i64 @freak_llvm_word_char_at(i64 %t3460, i64 %t3462)
    %c_v3463 = alloca i64
    store i64 %t3461, i64* %c_v3463
    %t3464 = load i64, i64* %c_v3463
    %t3465 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.222, i64 0, i64 0
    %t3466 = ptrtoint i8* %t3465 to i64
    %t3467 = call i64 @freak_llvm_word_eq(i64 %t3464, i64 %t3466)
    %t3468 = load i64, i64* %c_v3463
    %t3469 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.223, i64 0, i64 0
    %t3470 = ptrtoint i8* %t3469 to i64
    %t3471 = call i64 @freak_llvm_word_eq(i64 %t3468, i64 %t3470)
    %t3473 = icmp ne i64 %t3467, 0
    %t3474 = icmp ne i64 %t3471, 0
    %t3475 = or i1 %t3473, %t3474
    %t3472 = zext i1 %t3475 to i64
    %t3476 = load i64, i64* %c_v3463
    %t3477 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.224, i64 0, i64 0
    %t3478 = ptrtoint i8* %t3477 to i64
    %t3479 = call i64 @freak_llvm_word_eq(i64 %t3476, i64 %t3478)
    %t3481 = icmp ne i64 %t3472, 0
    %t3482 = icmp ne i64 %t3479, 0
    %t3483 = or i1 %t3481, %t3482
    %t3480 = zext i1 %t3483 to i64
    %t3487 = icmp ne i64 %t3480, 0
    br i1 %t3487, label %if.then.3484, label %if.end.3486
if.then.3484:
    %t3488 = load i64, i64* %i_v3448
    %t3489 = add i64 %t3488, 1
    %t3490 = call i64 @freak_llvm_word_from_int(i64 %t3489)
    %pos_str_v3491 = alloca i64
    store i64 %t3490, i64* %pos_str_v3491
    %t3492 = load i64, i64* %res_v3446
    %t3493 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.225, i64 0, i64 0
    %t3494 = ptrtoint i8* %t3493 to i64
    %t3495 = call i64 @freak_llvm_word_concat(i64 %t3492, i64 %t3494)
    %t3496 = load i64, i64* %pos_str_v3491
    %t3497 = call i64 @freak_llvm_word_concat(i64 %t3495, i64 %t3496)
    ret i64 %t3497
    br label %if.end.3486
if.end.3486:
    %t3498 = load i64, i64* %res_v3446
    %t3499 = load i64, i64* %c_v3463
    %t3500 = call i64 @freak_llvm_word_concat(i64 %t3498, i64 %t3499)
    store i64 %t3500, i64* %res_v3446
    %t3501 = load i64, i64* %i_v3448
    %t3502 = add i64 %t3501, 1
    store i64 %t3502, i64* %i_v3448
    br label %loop.cond.3452
loop.end.3454:
    %t3503 = load i64, i64* %i_v3448
    %t3504 = call i64 @freak_llvm_word_from_int(i64 %t3503)
    %pos_str2_v3505 = alloca i64
    store i64 %t3504, i64* %pos_str2_v3505
    %t3506 = load i64, i64* %res_v3446
    %t3507 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.226, i64 0, i64 0
    %t3508 = ptrtoint i8* %t3507 to i64
    %t3509 = call i64 @freak_llvm_word_concat(i64 %t3506, i64 %t3508)
    %t3510 = load i64, i64* %pos_str2_v3505
    %t3511 = call i64 @freak_llvm_word_concat(i64 %t3509, i64 %t3510)
    ret i64 %t3511
    ret i64 0
}

define i64 @freak_ver_parse_pre(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3512 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.227, i64 0, i64 0
    %t3513 = ptrtoint i8* %t3512 to i64
    %res_v3514 = alloca i64
    store i64 %t3513, i64* %res_v3514
    %t3515 = load i64, i64* %start
    %i_v3516 = alloca i64
    store i64 %t3515, i64* %i_v3516
    %t3517 = load i64, i64* @g_s
    %t3518 = call i64 @freak_llvm_word_length(i64 %t3517)
    %slen_v3519 = alloca i64
    store i64 %t3518, i64* %slen_v3519
    br label %loop.cond.3520
loop.cond.3520:
    %t3523 = load i64, i64* %i_v3516
    %t3524 = load i64, i64* %slen_v3519
    %t3526 = icmp sge i64 %t3523, %t3524
    %t3525 = zext i1 %t3526 to i64
    %t3527 = icmp eq i64 %t3525, 0
    br i1 %t3527, label %loop.body.3521, label %loop.end.3522
loop.body.3521:
    %t3528 = load i64, i64* @g_s
    %t3530 = load i64, i64* %i_v3516
    %t3529 = call i64 @freak_llvm_word_char_at(i64 %t3528, i64 %t3530)
    %c_v3531 = alloca i64
    store i64 %t3529, i64* %c_v3531
    %t3532 = load i64, i64* %c_v3531
    %t3533 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.228, i64 0, i64 0
    %t3534 = ptrtoint i8* %t3533 to i64
    %t3535 = call i64 @freak_llvm_word_eq(i64 %t3532, i64 %t3534)
    %t3539 = icmp ne i64 %t3535, 0
    br i1 %t3539, label %if.then.3536, label %if.end.3538
if.then.3536:
    %t3540 = load i64, i64* %res_v3514
    ret i64 %t3540
    br label %if.end.3538
if.end.3538:
    %t3541 = load i64, i64* %res_v3514
    %t3542 = load i64, i64* %c_v3531
    %t3543 = call i64 @freak_llvm_word_concat(i64 %t3541, i64 %t3542)
    store i64 %t3543, i64* %res_v3514
    %t3544 = load i64, i64* %i_v3516
    %t3545 = add i64 %t3544, 1
    store i64 %t3545, i64* %i_v3516
    br label %loop.cond.3520
loop.end.3522:
    %t3546 = load i64, i64* %res_v3514
    ret i64 %t3546
    ret i64 0
}

define i64 @freak_ver_parse_build(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3547 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.229, i64 0, i64 0
    %t3548 = ptrtoint i8* %t3547 to i64
    %res_v3549 = alloca i64
    store i64 %t3548, i64* %res_v3549
    %t3550 = load i64, i64* %start
    %i_v3551 = alloca i64
    store i64 %t3550, i64* %i_v3551
    %t3552 = load i64, i64* @g_s
    %t3553 = call i64 @freak_llvm_word_length(i64 %t3552)
    %slen_v3554 = alloca i64
    store i64 %t3553, i64* %slen_v3554
    br label %loop.cond.3555
loop.cond.3555:
    %t3558 = load i64, i64* %i_v3551
    %t3559 = load i64, i64* %slen_v3554
    %t3561 = icmp sge i64 %t3558, %t3559
    %t3560 = zext i1 %t3561 to i64
    %t3562 = icmp eq i64 %t3560, 0
    br i1 %t3562, label %loop.body.3556, label %loop.end.3557
loop.body.3556:
    %t3563 = load i64, i64* %res_v3549
    %t3564 = load i64, i64* @g_s
    %t3566 = load i64, i64* %i_v3551
    %t3565 = call i64 @freak_llvm_word_char_at(i64 %t3564, i64 %t3566)
    %t3567 = call i64 @freak_llvm_word_concat(i64 %t3563, i64 %t3565)
    store i64 %t3567, i64* %res_v3549
    %t3568 = load i64, i64* %i_v3551
    %t3569 = add i64 %t3568, 1
    store i64 %t3569, i64* %i_v3551
    br label %loop.cond.3555
loop.end.3557:
    %t3570 = load i64, i64* %res_v3549
    ret i64 %t3570
    ret i64 0
}

define i64 @freak_ver_get_val(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %t3571 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.230, i64 0, i64 0
    %t3572 = ptrtoint i8* %t3571 to i64
    %res_v3573 = alloca i64
    store i64 %t3572, i64* %res_v3573
    %i_v3574 = alloca i64
    store i64 0, i64* %i_v3574
    %t3575 = load i64, i64* %encoded
    %t3576 = call i64 @freak_llvm_word_length(i64 %t3575)
    %elen_v3577 = alloca i64
    store i64 %t3576, i64* %elen_v3577
    br label %loop.cond.3578
loop.cond.3578:
    %t3581 = load i64, i64* %i_v3574
    %t3582 = load i64, i64* %elen_v3577
    %t3584 = icmp sge i64 %t3581, %t3582
    %t3583 = zext i1 %t3584 to i64
    %t3585 = icmp eq i64 %t3583, 0
    br i1 %t3585, label %loop.body.3579, label %loop.end.3580
loop.body.3579:
    %t3586 = load i64, i64* %encoded
    %t3588 = load i64, i64* %i_v3574
    %t3587 = call i64 @freak_llvm_word_char_at(i64 %t3586, i64 %t3588)
    %c_v3589 = alloca i64
    store i64 %t3587, i64* %c_v3589
    %t3590 = load i64, i64* %c_v3589
    %t3591 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.231, i64 0, i64 0
    %t3592 = ptrtoint i8* %t3591 to i64
    %t3593 = call i64 @freak_llvm_word_eq(i64 %t3590, i64 %t3592)
    %t3597 = icmp ne i64 %t3593, 0
    br i1 %t3597, label %if.then.3594, label %if.end.3596
if.then.3594:
    %t3598 = load i64, i64* %res_v3573
    ret i64 %t3598
    br label %if.end.3596
if.end.3596:
    %t3599 = load i64, i64* %res_v3573
    %t3600 = load i64, i64* %c_v3589
    %t3601 = call i64 @freak_llvm_word_concat(i64 %t3599, i64 %t3600)
    store i64 %t3601, i64* %res_v3573
    %t3602 = load i64, i64* %i_v3574
    %t3603 = add i64 %t3602, 1
    store i64 %t3603, i64* %i_v3574
    br label %loop.cond.3578
loop.end.3580:
    %t3604 = load i64, i64* %res_v3573
    ret i64 %t3604
    ret i64 0
}

define i64 @freak_ver_get_pos(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %i_v3605 = alloca i64
    store i64 0, i64* %i_v3605
    %t3606 = load i64, i64* %encoded
    %t3607 = call i64 @freak_llvm_word_length(i64 %t3606)
    %elen_v3608 = alloca i64
    store i64 %t3607, i64* %elen_v3608
    br label %loop.cond.3609
loop.cond.3609:
    %t3612 = load i64, i64* %i_v3605
    %t3613 = load i64, i64* %elen_v3608
    %t3615 = icmp sge i64 %t3612, %t3613
    %t3614 = zext i1 %t3615 to i64
    %t3616 = icmp eq i64 %t3614, 0
    br i1 %t3616, label %loop.body.3610, label %loop.end.3611
loop.body.3610:
    %t3617 = load i64, i64* %encoded
    %t3619 = load i64, i64* %i_v3605
    %t3618 = call i64 @freak_llvm_word_char_at(i64 %t3617, i64 %t3619)
    %c_v3620 = alloca i64
    store i64 %t3618, i64* %c_v3620
    %t3621 = load i64, i64* %c_v3620
    %t3622 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.232, i64 0, i64 0
    %t3623 = ptrtoint i8* %t3622 to i64
    %t3624 = call i64 @freak_llvm_word_eq(i64 %t3621, i64 %t3623)
    %t3628 = icmp ne i64 %t3624, 0
    br i1 %t3628, label %if.then.3625, label %if.end.3627
if.then.3625:
    %t3629 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.233, i64 0, i64 0
    %t3630 = ptrtoint i8* %t3629 to i64
    %pos_str_v3631 = alloca i64
    store i64 %t3630, i64* %pos_str_v3631
    %t3632 = load i64, i64* %i_v3605
    %t3633 = add i64 %t3632, 1
    %j_v3634 = alloca i64
    store i64 %t3633, i64* %j_v3634
    br label %loop.cond.3635
loop.cond.3635:
    %t3638 = load i64, i64* %j_v3634
    %t3639 = load i64, i64* %elen_v3608
    %t3641 = icmp sge i64 %t3638, %t3639
    %t3640 = zext i1 %t3641 to i64
    %t3642 = icmp eq i64 %t3640, 0
    br i1 %t3642, label %loop.body.3636, label %loop.end.3637
loop.body.3636:
    %t3643 = load i64, i64* %pos_str_v3631
    %t3644 = load i64, i64* %encoded
    %t3646 = load i64, i64* %j_v3634
    %t3645 = call i64 @freak_llvm_word_char_at(i64 %t3644, i64 %t3646)
    %t3647 = call i64 @freak_llvm_word_concat(i64 %t3643, i64 %t3645)
    store i64 %t3647, i64* %pos_str_v3631
    %t3648 = load i64, i64* %j_v3634
    %t3649 = add i64 %t3648, 1
    store i64 %t3649, i64* %j_v3634
    br label %loop.cond.3635
loop.end.3637:
    %t3650 = load i64, i64* %pos_str_v3631
    %t3651 = call i64 @freak_llvm_word_to_int(i64 %t3650)
    ret i64 %t3651
    br label %if.end.3627
if.end.3627:
    %t3652 = load i64, i64* %i_v3605
    %t3653 = add i64 %t3652, 1
    store i64 %t3653, i64* %i_v3605
    br label %loop.cond.3609
loop.end.3611:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_parse(i64 %arg_version) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %t3654 = load i64, i64* %version
    store i64 %t3654, i64* @g_s
    %t3655 = load i64, i64* @g_s
    %t3656 = call i64 @freak_llvm_word_length(i64 %t3655)
    %t3658 = icmp sgt i64 %t3656, 0
    %t3657 = zext i1 %t3658 to i64
    %t3662 = icmp ne i64 %t3657, 0
    br i1 %t3662, label %if.then.3659, label %if.end.3661
if.then.3659:
    %t3663 = load i64, i64* @g_s
    %t3664 = call i64 @freak_llvm_word_char_at(i64 %t3663, i64 0)
    %fc_v3665 = alloca i64
    store i64 %t3664, i64* %fc_v3665
    %t3666 = load i64, i64* %fc_v3665
    %t3667 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.234, i64 0, i64 0
    %t3668 = ptrtoint i8* %t3667 to i64
    %t3669 = call i64 @freak_llvm_word_eq(i64 %t3666, i64 %t3668)
    %t3670 = load i64, i64* %fc_v3665
    %t3671 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.235, i64 0, i64 0
    %t3672 = ptrtoint i8* %t3671 to i64
    %t3673 = call i64 @freak_llvm_word_eq(i64 %t3670, i64 %t3672)
    %t3675 = icmp ne i64 %t3669, 0
    %t3676 = icmp ne i64 %t3673, 0
    %t3677 = or i1 %t3675, %t3676
    %t3674 = zext i1 %t3677 to i64
    %t3681 = icmp ne i64 %t3674, 0
    br i1 %t3681, label %if.then.3678, label %if.end.3680
if.then.3678:
    %t3682 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.236, i64 0, i64 0
    %t3683 = ptrtoint i8* %t3682 to i64
    %ns_v3684 = alloca i64
    store i64 %t3683, i64* %ns_v3684
    %vi_v3685 = alloca i64
    store i64 1, i64* %vi_v3685
    br label %loop.cond.3686
loop.cond.3686:
    %t3689 = load i64, i64* %vi_v3685
    %t3690 = load i64, i64* @g_s
    %t3691 = call i64 @freak_llvm_word_length(i64 %t3690)
    %t3693 = icmp sge i64 %t3689, %t3691
    %t3692 = zext i1 %t3693 to i64
    %t3694 = icmp eq i64 %t3692, 0
    br i1 %t3694, label %loop.body.3687, label %loop.end.3688
loop.body.3687:
    %t3695 = load i64, i64* %ns_v3684
    %t3696 = load i64, i64* @g_s
    %t3698 = load i64, i64* %vi_v3685
    %t3697 = call i64 @freak_llvm_word_char_at(i64 %t3696, i64 %t3698)
    %t3699 = call i64 @freak_llvm_word_concat(i64 %t3695, i64 %t3697)
    store i64 %t3699, i64* %ns_v3684
    %t3700 = load i64, i64* %vi_v3685
    %t3701 = add i64 %t3700, 1
    store i64 %t3701, i64* %vi_v3685
    br label %loop.cond.3686
loop.end.3688:
    %t3702 = load i64, i64* %ns_v3684
    store i64 %t3702, i64* @g_s
    br label %if.end.3680
if.end.3680:
    br label %if.end.3661
if.end.3661:
    %t3703 = load i64, i64* @g_s
    %t3704 = call i64 @freak_ver_parse_num(i64 %t3703, i64 0)
    %r1_v3705 = alloca i64
    store i64 %t3704, i64* %r1_v3705
    %t3706 = load i64, i64* %r1_v3705
    %t3707 = call i64 @freak_ver_get_val(i64 %t3706)
    %major_v3708 = alloca i64
    store i64 %t3707, i64* %major_v3708
    %t3709 = load i64, i64* %r1_v3705
    %t3710 = call i64 @freak_ver_get_pos(i64 %t3709)
    %pos1_v3711 = alloca i64
    store i64 %t3710, i64* %pos1_v3711
    %t3712 = load i64, i64* @g_s
    %t3713 = load i64, i64* %pos1_v3711
    %t3714 = call i64 @freak_ver_parse_num(i64 %t3712, i64 %t3713)
    %r2_v3715 = alloca i64
    store i64 %t3714, i64* %r2_v3715
    %t3716 = load i64, i64* %r2_v3715
    %t3717 = call i64 @freak_ver_get_val(i64 %t3716)
    %minor_v3718 = alloca i64
    store i64 %t3717, i64* %minor_v3718
    %t3719 = load i64, i64* %r2_v3715
    %t3720 = call i64 @freak_ver_get_pos(i64 %t3719)
    %pos2_v3721 = alloca i64
    store i64 %t3720, i64* %pos2_v3721
    %t3722 = load i64, i64* @g_s
    %t3723 = load i64, i64* %pos2_v3721
    %t3724 = call i64 @freak_ver_parse_num(i64 %t3722, i64 %t3723)
    %r3_v3725 = alloca i64
    store i64 %t3724, i64* %r3_v3725
    %t3726 = load i64, i64* %r3_v3725
    %t3727 = call i64 @freak_ver_get_val(i64 %t3726)
    %patch_v3728 = alloca i64
    store i64 %t3727, i64* %patch_v3728
    %t3729 = load i64, i64* %r3_v3725
    %t3730 = call i64 @freak_ver_get_pos(i64 %t3729)
    %pos3_v3731 = alloca i64
    store i64 %t3730, i64* %pos3_v3731
    %t3732 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.237, i64 0, i64 0
    %t3733 = ptrtoint i8* %t3732 to i64
    %pre_v3734 = alloca i64
    store i64 %t3733, i64* %pre_v3734
    %t3735 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.238, i64 0, i64 0
    %t3736 = ptrtoint i8* %t3735 to i64
    %bld_v3737 = alloca i64
    store i64 %t3736, i64* %bld_v3737
    %t3738 = load i64, i64* %pos3_v3731
    %t3739 = load i64, i64* @g_s
    %t3740 = call i64 @freak_llvm_word_length(i64 %t3739)
    %t3742 = icmp sle i64 %t3738, %t3740
    %t3741 = zext i1 %t3742 to i64
    %t3746 = icmp ne i64 %t3741, 0
    br i1 %t3746, label %if.then.3743, label %if.end.3745
if.then.3743:
    %t3747 = load i64, i64* %pos3_v3731
    %t3749 = icmp sgt i64 %t3747, 0
    %t3748 = zext i1 %t3749 to i64
    %t3753 = icmp ne i64 %t3748, 0
    br i1 %t3753, label %if.then.3750, label %if.end.3752
if.then.3750:
    %t3754 = load i64, i64* @g_s
    %t3756 = load i64, i64* %pos3_v3731
    %t3757 = sub i64 %t3756, 1
    %t3755 = call i64 @freak_llvm_word_char_at(i64 %t3754, i64 %t3757)
    %delim_v3758 = alloca i64
    store i64 %t3755, i64* %delim_v3758
    %t3759 = load i64, i64* %delim_v3758
    %t3760 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.239, i64 0, i64 0
    %t3761 = ptrtoint i8* %t3760 to i64
    %t3762 = call i64 @freak_llvm_word_eq(i64 %t3759, i64 %t3761)
    %t3766 = icmp ne i64 %t3762, 0
    br i1 %t3766, label %if.then.3763, label %if.else.3764
if.then.3763:
    %t3767 = load i64, i64* @g_s
    %t3768 = load i64, i64* %pos3_v3731
    %t3769 = call i64 @freak_ver_parse_pre(i64 %t3767, i64 %t3768)
    store i64 %t3769, i64* %pre_v3734
    br label %if.end.3765
if.else.3764:
    %t3770 = load i64, i64* %delim_v3758
    %t3771 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.240, i64 0, i64 0
    %t3772 = ptrtoint i8* %t3771 to i64
    %t3773 = call i64 @freak_llvm_word_eq(i64 %t3770, i64 %t3772)
    %t3777 = icmp ne i64 %t3773, 0
    br i1 %t3777, label %if.then.3774, label %if.end.3776
if.then.3774:
    %t3778 = load i64, i64* @g_s
    %t3779 = load i64, i64* %pos3_v3731
    %t3780 = call i64 @freak_ver_parse_build(i64 %t3778, i64 %t3779)
    store i64 %t3780, i64* %bld_v3737
    br label %if.end.3776
if.end.3776:
    br label %if.end.3765
if.end.3765:
    br label %if.end.3752
if.end.3752:
    br label %if.end.3745
if.end.3745:
    %t3781 = load i64, i64* %pre_v3734
    %t3782 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.241, i64 0, i64 0
    %t3783 = ptrtoint i8* %t3782 to i64
    %t3784 = call i64 @freak_llvm_word_neq(i64 %t3781, i64 %t3783)
    %t3788 = icmp ne i64 %t3784, 0
    br i1 %t3788, label %if.then.3785, label %if.end.3787
if.then.3785:
    %pi_v3789 = alloca i64
    store i64 0, i64* %pi_v3789
    %t3790 = load i64, i64* @g_s
    %t3791 = call i64 @freak_llvm_word_length(i64 %t3790)
    %plen_v3792 = alloca i64
    store i64 %t3791, i64* %plen_v3792
    br label %loop.cond.3793
loop.cond.3793:
    %t3796 = load i64, i64* %pi_v3789
    %t3797 = load i64, i64* %plen_v3792
    %t3799 = icmp sge i64 %t3796, %t3797
    %t3798 = zext i1 %t3799 to i64
    %t3800 = icmp eq i64 %t3798, 0
    br i1 %t3800, label %loop.body.3794, label %loop.end.3795
loop.body.3794:
    %t3801 = load i64, i64* @g_s
    %t3803 = load i64, i64* %pi_v3789
    %t3802 = call i64 @freak_llvm_word_char_at(i64 %t3801, i64 %t3803)
    %t3804 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.242, i64 0, i64 0
    %t3805 = ptrtoint i8* %t3804 to i64
    %t3806 = call i64 @freak_llvm_word_eq(i64 %t3802, i64 %t3805)
    %t3810 = icmp ne i64 %t3806, 0
    br i1 %t3810, label %if.then.3807, label %if.end.3809
if.then.3807:
    %t3811 = load i64, i64* @g_s
    %t3812 = load i64, i64* %pi_v3789
    %t3813 = add i64 %t3812, 1
    %t3814 = call i64 @freak_ver_parse_build(i64 %t3811, i64 %t3813)
    store i64 %t3814, i64* %bld_v3737
    br label %if.end.3809
if.end.3809:
    %t3815 = load i64, i64* %pi_v3789
    %t3816 = add i64 %t3815, 1
    store i64 %t3816, i64* %pi_v3789
    br label %loop.cond.3793
loop.end.3795:
    br label %if.end.3787
if.end.3787:
    %t3817 = load i64, i64* %major_v3708
    %t3818 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.243, i64 0, i64 0
    %t3819 = ptrtoint i8* %t3818 to i64
    %t3820 = call i64 @freak_llvm_word_concat(i64 %t3817, i64 %t3819)
    %t3821 = load i64, i64* %minor_v3718
    %t3822 = call i64 @freak_llvm_word_concat(i64 %t3820, i64 %t3821)
    %t3823 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.244, i64 0, i64 0
    %t3824 = ptrtoint i8* %t3823 to i64
    %t3825 = call i64 @freak_llvm_word_concat(i64 %t3822, i64 %t3824)
    %t3826 = load i64, i64* %patch_v3728
    %t3827 = call i64 @freak_llvm_word_concat(i64 %t3825, i64 %t3826)
    %t3828 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.245, i64 0, i64 0
    %t3829 = ptrtoint i8* %t3828 to i64
    %t3830 = call i64 @freak_llvm_word_concat(i64 %t3827, i64 %t3829)
    %t3831 = load i64, i64* %pre_v3734
    %t3832 = call i64 @freak_llvm_word_concat(i64 %t3830, i64 %t3831)
    %t3833 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.246, i64 0, i64 0
    %t3834 = ptrtoint i8* %t3833 to i64
    %t3835 = call i64 @freak_llvm_word_concat(i64 %t3832, i64 %t3834)
    %t3836 = load i64, i64* %bld_v3737
    %t3837 = call i64 @freak_llvm_word_concat(i64 %t3835, i64 %t3836)
    ret i64 %t3837
    ret i64 0
}

define i64 @freak_ver_field(i64 %arg_parsed, i64 %arg_field_idx) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %field_idx = alloca i64
    store i64 %arg_field_idx, i64* %field_idx
    %t3838 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.247, i64 0, i64 0
    %t3839 = ptrtoint i8* %t3838 to i64
    %res_v3840 = alloca i64
    store i64 %t3839, i64* %res_v3840
    %current_field_v3841 = alloca i64
    store i64 0, i64* %current_field_v3841
    %i_v3842 = alloca i64
    store i64 0, i64* %i_v3842
    %t3843 = load i64, i64* %parsed
    %t3844 = call i64 @freak_llvm_word_length(i64 %t3843)
    %plen_v3845 = alloca i64
    store i64 %t3844, i64* %plen_v3845
    br label %loop.cond.3846
loop.cond.3846:
    %t3849 = load i64, i64* %i_v3842
    %t3850 = load i64, i64* %plen_v3845
    %t3852 = icmp sge i64 %t3849, %t3850
    %t3851 = zext i1 %t3852 to i64
    %t3853 = icmp eq i64 %t3851, 0
    br i1 %t3853, label %loop.body.3847, label %loop.end.3848
loop.body.3847:
    %t3854 = load i64, i64* %parsed
    %t3856 = load i64, i64* %i_v3842
    %t3855 = call i64 @freak_llvm_word_char_at(i64 %t3854, i64 %t3856)
    %c_v3857 = alloca i64
    store i64 %t3855, i64* %c_v3857
    %t3858 = load i64, i64* %c_v3857
    %t3859 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.248, i64 0, i64 0
    %t3860 = ptrtoint i8* %t3859 to i64
    %t3861 = call i64 @freak_llvm_word_eq(i64 %t3858, i64 %t3860)
    %t3865 = icmp ne i64 %t3861, 0
    br i1 %t3865, label %if.then.3862, label %if.else.3863
if.then.3862:
    %t3866 = load i64, i64* %current_field_v3841
    %t3867 = load i64, i64* %field_idx
    %t3869 = icmp eq i64 %t3866, %t3867
    %t3868 = zext i1 %t3869 to i64
    %t3873 = icmp ne i64 %t3868, 0
    br i1 %t3873, label %if.then.3870, label %if.end.3872
if.then.3870:
    %t3874 = load i64, i64* %res_v3840
    ret i64 %t3874
    br label %if.end.3872
if.end.3872:
    %t3875 = load i64, i64* %current_field_v3841
    %t3876 = add i64 %t3875, 1
    store i64 %t3876, i64* %current_field_v3841
    %t3877 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.249, i64 0, i64 0
    %t3878 = ptrtoint i8* %t3877 to i64
    store i64 %t3878, i64* %res_v3840
    br label %if.end.3864
if.else.3863:
    %t3879 = load i64, i64* %res_v3840
    %t3880 = load i64, i64* %c_v3857
    %t3881 = call i64 @freak_llvm_word_concat(i64 %t3879, i64 %t3880)
    store i64 %t3881, i64* %res_v3840
    br label %if.end.3864
if.end.3864:
    %t3882 = load i64, i64* %i_v3842
    %t3883 = add i64 %t3882, 1
    store i64 %t3883, i64* %i_v3842
    br label %loop.cond.3846
loop.end.3848:
    %t3884 = load i64, i64* %current_field_v3841
    %t3885 = load i64, i64* %field_idx
    %t3887 = icmp eq i64 %t3884, %t3885
    %t3886 = zext i1 %t3887 to i64
    %t3891 = icmp ne i64 %t3886, 0
    br i1 %t3891, label %if.then.3888, label %if.end.3890
if.then.3888:
    %t3892 = load i64, i64* %res_v3840
    ret i64 %t3892
    br label %if.end.3890
if.end.3890:
    %t3893 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.250, i64 0, i64 0
    %t3894 = ptrtoint i8* %t3893 to i64
    ret i64 %t3894
    ret i64 0
}

define i64 @freak_ver_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3895 = load i64, i64* %parsed
    %t3896 = call i64 @freak_ver_field(i64 %t3895, i64 0)
    %t3897 = call i64 @freak_llvm_word_to_int(i64 %t3896)
    ret i64 %t3897
    ret i64 0
}

define i64 @freak_ver_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3898 = load i64, i64* %parsed
    %t3899 = call i64 @freak_ver_field(i64 %t3898, i64 1)
    %t3900 = call i64 @freak_llvm_word_to_int(i64 %t3899)
    ret i64 %t3900
    ret i64 0
}

define i64 @freak_ver_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3901 = load i64, i64* %parsed
    %t3902 = call i64 @freak_ver_field(i64 %t3901, i64 2)
    %t3903 = call i64 @freak_llvm_word_to_int(i64 %t3902)
    ret i64 %t3903
    ret i64 0
}

define i64 @freak_ver_pre(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3904 = load i64, i64* %parsed
    %t3905 = call i64 @freak_ver_field(i64 %t3904, i64 3)
    ret i64 %t3905
    ret i64 0
}

define i64 @freak_ver_build(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3906 = load i64, i64* %parsed
    %t3907 = call i64 @freak_ver_field(i64 %t3906, i64 4)
    ret i64 %t3907
    ret i64 0
}

define i64 @freak_ver_to_string(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3908 = load i64, i64* %parsed
    %t3909 = call i64 @freak_ver_field(i64 %t3908, i64 0)
    %maj_v3910 = alloca i64
    store i64 %t3909, i64* %maj_v3910
    %t3911 = load i64, i64* %parsed
    %t3912 = call i64 @freak_ver_field(i64 %t3911, i64 1)
    %min_v3913 = alloca i64
    store i64 %t3912, i64* %min_v3913
    %t3914 = load i64, i64* %parsed
    %t3915 = call i64 @freak_ver_field(i64 %t3914, i64 2)
    %pat_v3916 = alloca i64
    store i64 %t3915, i64* %pat_v3916
    %t3917 = load i64, i64* %parsed
    %t3918 = call i64 @freak_ver_field(i64 %t3917, i64 3)
    %pre_v3919 = alloca i64
    store i64 %t3918, i64* %pre_v3919
    %t3920 = load i64, i64* %parsed
    %t3921 = call i64 @freak_ver_field(i64 %t3920, i64 4)
    %bld_v3922 = alloca i64
    store i64 %t3921, i64* %bld_v3922
    %t3923 = load i64, i64* %maj_v3910
    %t3924 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.251, i64 0, i64 0
    %t3925 = ptrtoint i8* %t3924 to i64
    %t3926 = call i64 @freak_llvm_word_concat(i64 %t3923, i64 %t3925)
    %t3927 = load i64, i64* %min_v3913
    %t3928 = call i64 @freak_llvm_word_concat(i64 %t3926, i64 %t3927)
    %t3929 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.252, i64 0, i64 0
    %t3930 = ptrtoint i8* %t3929 to i64
    %t3931 = call i64 @freak_llvm_word_concat(i64 %t3928, i64 %t3930)
    %t3932 = load i64, i64* %pat_v3916
    %t3933 = call i64 @freak_llvm_word_concat(i64 %t3931, i64 %t3932)
    %out_v3934 = alloca i64
    store i64 %t3933, i64* %out_v3934
    %t3935 = load i64, i64* %pre_v3919
    %t3936 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.253, i64 0, i64 0
    %t3937 = ptrtoint i8* %t3936 to i64
    %t3938 = call i64 @freak_llvm_word_neq(i64 %t3935, i64 %t3937)
    %t3942 = icmp ne i64 %t3938, 0
    br i1 %t3942, label %if.then.3939, label %if.end.3941
if.then.3939:
    %t3943 = load i64, i64* %out_v3934
    %t3944 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.254, i64 0, i64 0
    %t3945 = ptrtoint i8* %t3944 to i64
    %t3946 = call i64 @freak_llvm_word_concat(i64 %t3943, i64 %t3945)
    %t3947 = load i64, i64* %pre_v3919
    %t3948 = call i64 @freak_llvm_word_concat(i64 %t3946, i64 %t3947)
    store i64 %t3948, i64* %out_v3934
    br label %if.end.3941
if.end.3941:
    %t3949 = load i64, i64* %bld_v3922
    %t3950 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.255, i64 0, i64 0
    %t3951 = ptrtoint i8* %t3950 to i64
    %t3952 = call i64 @freak_llvm_word_neq(i64 %t3949, i64 %t3951)
    %t3956 = icmp ne i64 %t3952, 0
    br i1 %t3956, label %if.then.3953, label %if.end.3955
if.then.3953:
    %t3957 = load i64, i64* %out_v3934
    %t3958 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.256, i64 0, i64 0
    %t3959 = ptrtoint i8* %t3958 to i64
    %t3960 = call i64 @freak_llvm_word_concat(i64 %t3957, i64 %t3959)
    %t3961 = load i64, i64* %bld_v3922
    %t3962 = call i64 @freak_llvm_word_concat(i64 %t3960, i64 %t3961)
    store i64 %t3962, i64* %out_v3934
    br label %if.end.3955
if.end.3955:
    %t3963 = load i64, i64* %out_v3934
    ret i64 %t3963
    ret i64 0
}

define i64 @freak_ver_compare(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t3964 = load i64, i64* @g_a
    %t3965 = call i64 @freak_ver_major(i64 %t3964)
    %a_major_v3966 = alloca i64
    store i64 %t3965, i64* %a_major_v3966
    %t3967 = load i64, i64* @g_b
    %t3968 = call i64 @freak_ver_major(i64 %t3967)
    %b_major_v3969 = alloca i64
    store i64 %t3968, i64* %b_major_v3969
    %t3970 = load i64, i64* %a_major_v3966
    %t3971 = load i64, i64* %b_major_v3969
    %t3973 = icmp slt i64 %t3970, %t3971
    %t3972 = zext i1 %t3973 to i64
    %t3977 = icmp ne i64 %t3972, 0
    br i1 %t3977, label %if.then.3974, label %if.end.3976
if.then.3974:
    %t3978 = sub i64 0, 1
    ret i64 %t3978
    br label %if.end.3976
if.end.3976:
    %t3979 = load i64, i64* %a_major_v3966
    %t3980 = load i64, i64* %b_major_v3969
    %t3982 = icmp sgt i64 %t3979, %t3980
    %t3981 = zext i1 %t3982 to i64
    %t3986 = icmp ne i64 %t3981, 0
    br i1 %t3986, label %if.then.3983, label %if.end.3985
if.then.3983:
    ret i64 1
    br label %if.end.3985
if.end.3985:
    %t3987 = load i64, i64* @g_a
    %t3988 = call i64 @freak_ver_minor(i64 %t3987)
    %a_minor_v3989 = alloca i64
    store i64 %t3988, i64* %a_minor_v3989
    %t3990 = load i64, i64* @g_b
    %t3991 = call i64 @freak_ver_minor(i64 %t3990)
    %b_minor_v3992 = alloca i64
    store i64 %t3991, i64* %b_minor_v3992
    %t3993 = load i64, i64* %a_minor_v3989
    %t3994 = load i64, i64* %b_minor_v3992
    %t3996 = icmp slt i64 %t3993, %t3994
    %t3995 = zext i1 %t3996 to i64
    %t4000 = icmp ne i64 %t3995, 0
    br i1 %t4000, label %if.then.3997, label %if.end.3999
if.then.3997:
    %t4001 = sub i64 0, 1
    ret i64 %t4001
    br label %if.end.3999
if.end.3999:
    %t4002 = load i64, i64* %a_minor_v3989
    %t4003 = load i64, i64* %b_minor_v3992
    %t4005 = icmp sgt i64 %t4002, %t4003
    %t4004 = zext i1 %t4005 to i64
    %t4009 = icmp ne i64 %t4004, 0
    br i1 %t4009, label %if.then.4006, label %if.end.4008
if.then.4006:
    ret i64 1
    br label %if.end.4008
if.end.4008:
    %t4010 = load i64, i64* @g_a
    %t4011 = call i64 @freak_ver_patch(i64 %t4010)
    %a_patch_v4012 = alloca i64
    store i64 %t4011, i64* %a_patch_v4012
    %t4013 = load i64, i64* @g_b
    %t4014 = call i64 @freak_ver_patch(i64 %t4013)
    %b_patch_v4015 = alloca i64
    store i64 %t4014, i64* %b_patch_v4015
    %t4016 = load i64, i64* %a_patch_v4012
    %t4017 = load i64, i64* %b_patch_v4015
    %t4019 = icmp slt i64 %t4016, %t4017
    %t4018 = zext i1 %t4019 to i64
    %t4023 = icmp ne i64 %t4018, 0
    br i1 %t4023, label %if.then.4020, label %if.end.4022
if.then.4020:
    %t4024 = sub i64 0, 1
    ret i64 %t4024
    br label %if.end.4022
if.end.4022:
    %t4025 = load i64, i64* %a_patch_v4012
    %t4026 = load i64, i64* %b_patch_v4015
    %t4028 = icmp sgt i64 %t4025, %t4026
    %t4027 = zext i1 %t4028 to i64
    %t4032 = icmp ne i64 %t4027, 0
    br i1 %t4032, label %if.then.4029, label %if.end.4031
if.then.4029:
    ret i64 1
    br label %if.end.4031
if.end.4031:
    %t4033 = load i64, i64* @g_a
    %t4034 = call i64 @freak_ver_pre(i64 %t4033)
    %a_pre_v4035 = alloca i64
    store i64 %t4034, i64* %a_pre_v4035
    %t4036 = load i64, i64* @g_b
    %t4037 = call i64 @freak_ver_pre(i64 %t4036)
    %b_pre_v4038 = alloca i64
    store i64 %t4037, i64* %b_pre_v4038
    %t4039 = load i64, i64* %a_pre_v4035
    %t4040 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.257, i64 0, i64 0
    %t4041 = ptrtoint i8* %t4040 to i64
    %t4042 = call i64 @freak_llvm_word_eq(i64 %t4039, i64 %t4041)
    %t4043 = load i64, i64* %b_pre_v4038
    %t4044 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.258, i64 0, i64 0
    %t4045 = ptrtoint i8* %t4044 to i64
    %t4046 = call i64 @freak_llvm_word_neq(i64 %t4043, i64 %t4045)
    %t4048 = icmp ne i64 %t4042, 0
    %t4049 = icmp ne i64 %t4046, 0
    %t4050 = and i1 %t4048, %t4049
    %t4047 = zext i1 %t4050 to i64
    %t4054 = icmp ne i64 %t4047, 0
    br i1 %t4054, label %if.then.4051, label %if.end.4053
if.then.4051:
    ret i64 1
    br label %if.end.4053
if.end.4053:
    %t4055 = load i64, i64* %a_pre_v4035
    %t4056 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.259, i64 0, i64 0
    %t4057 = ptrtoint i8* %t4056 to i64
    %t4058 = call i64 @freak_llvm_word_neq(i64 %t4055, i64 %t4057)
    %t4059 = load i64, i64* %b_pre_v4038
    %t4060 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.260, i64 0, i64 0
    %t4061 = ptrtoint i8* %t4060 to i64
    %t4062 = call i64 @freak_llvm_word_eq(i64 %t4059, i64 %t4061)
    %t4064 = icmp ne i64 %t4058, 0
    %t4065 = icmp ne i64 %t4062, 0
    %t4066 = and i1 %t4064, %t4065
    %t4063 = zext i1 %t4066 to i64
    %t4070 = icmp ne i64 %t4063, 0
    br i1 %t4070, label %if.then.4067, label %if.end.4069
if.then.4067:
    %t4071 = sub i64 0, 1
    ret i64 %t4071
    br label %if.end.4069
if.end.4069:
    %t4072 = load i64, i64* %a_pre_v4035
    %t4073 = call i64 @freak_llvm_word_length(i64 %t4072)
    %cmp_len_v4074 = alloca i64
    store i64 %t4073, i64* %cmp_len_v4074
    %t4075 = load i64, i64* %b_pre_v4038
    %t4076 = call i64 @freak_llvm_word_length(i64 %t4075)
    %t4077 = load i64, i64* %cmp_len_v4074
    %t4079 = icmp slt i64 %t4076, %t4077
    %t4078 = zext i1 %t4079 to i64
    %t4083 = icmp ne i64 %t4078, 0
    br i1 %t4083, label %if.then.4080, label %if.end.4082
if.then.4080:
    %t4084 = load i64, i64* %b_pre_v4038
    %t4085 = call i64 @freak_llvm_word_length(i64 %t4084)
    store i64 %t4085, i64* %cmp_len_v4074
    br label %if.end.4082
if.end.4082:
    %ci_v4086 = alloca i64
    store i64 0, i64* %ci_v4086
    br label %loop.cond.4087
loop.cond.4087:
    %t4090 = load i64, i64* %ci_v4086
    %t4091 = load i64, i64* %cmp_len_v4074
    %t4093 = icmp sge i64 %t4090, %t4091
    %t4092 = zext i1 %t4093 to i64
    %t4094 = icmp eq i64 %t4092, 0
    br i1 %t4094, label %loop.body.4088, label %loop.end.4089
loop.body.4088:
    %t4095 = load i64, i64* %a_pre_v4035
    %t4097 = load i64, i64* %ci_v4086
    %t4096 = call i64 @freak_llvm_word_char_at(i64 %t4095, i64 %t4097)
    %ac_v4098 = alloca i64
    store i64 %t4096, i64* %ac_v4098
    %t4099 = load i64, i64* %b_pre_v4038
    %t4101 = load i64, i64* %ci_v4086
    %t4100 = call i64 @freak_llvm_word_char_at(i64 %t4099, i64 %t4101)
    %bc_v4102 = alloca i64
    store i64 %t4100, i64* %bc_v4102
    %t4103 = load i64, i64* %ac_v4098
    %t4104 = load i64, i64* %bc_v4102
    %t4105 = call i64 @freak_llvm_word_neq(i64 %t4103, i64 %t4104)
    %t4109 = icmp ne i64 %t4105, 0
    br i1 %t4109, label %if.then.4106, label %if.end.4108
if.then.4106:
    %t4110 = load i64, i64* %ac_v4098
    %t4111 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.261, i64 0, i64 0
    %t4112 = ptrtoint i8* %t4111 to i64
    %t4113 = call i64 @freak_llvm_word_eq(i64 %t4110, i64 %t4112)
    %t4114 = load i64, i64* %bc_v4102
    %t4115 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.262, i64 0, i64 0
    %t4116 = ptrtoint i8* %t4115 to i64
    %t4117 = call i64 @freak_llvm_word_eq(i64 %t4114, i64 %t4116)
    %t4119 = icmp ne i64 %t4113, 0
    %t4120 = icmp ne i64 %t4117, 0
    %t4121 = and i1 %t4119, %t4120
    %t4118 = zext i1 %t4121 to i64
    %t4125 = icmp ne i64 %t4118, 0
    br i1 %t4125, label %if.then.4122, label %if.end.4124
if.then.4122:
    %t4126 = sub i64 0, 1
    ret i64 %t4126
    br label %if.end.4124
if.end.4124:
    %t4127 = load i64, i64* %ac_v4098
    %t4128 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.263, i64 0, i64 0
    %t4129 = ptrtoint i8* %t4128 to i64
    %t4130 = call i64 @freak_llvm_word_eq(i64 %t4127, i64 %t4129)
    %t4131 = load i64, i64* %bc_v4102
    %t4132 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.264, i64 0, i64 0
    %t4133 = ptrtoint i8* %t4132 to i64
    %t4134 = call i64 @freak_llvm_word_eq(i64 %t4131, i64 %t4133)
    %t4136 = icmp ne i64 %t4130, 0
    %t4137 = icmp ne i64 %t4134, 0
    %t4138 = and i1 %t4136, %t4137
    %t4135 = zext i1 %t4138 to i64
    %t4142 = icmp ne i64 %t4135, 0
    br i1 %t4142, label %if.then.4139, label %if.end.4141
if.then.4139:
    ret i64 1
    br label %if.end.4141
if.end.4141:
    %t4143 = load i64, i64* %ac_v4098
    %t4144 = call i64 @freak_llvm_word_to_int(i64 %t4143)
    %ai_v4145 = alloca i64
    store i64 %t4144, i64* %ai_v4145
    %t4146 = load i64, i64* %bc_v4102
    %t4147 = call i64 @freak_llvm_word_to_int(i64 %t4146)
    %bi_v4148 = alloca i64
    store i64 %t4147, i64* %bi_v4148
    %t4149 = load i64, i64* %ai_v4145
    %t4150 = load i64, i64* %bi_v4148
    %t4152 = icmp slt i64 %t4149, %t4150
    %t4151 = zext i1 %t4152 to i64
    %t4156 = icmp ne i64 %t4151, 0
    br i1 %t4156, label %if.then.4153, label %if.end.4155
if.then.4153:
    %t4157 = sub i64 0, 1
    ret i64 %t4157
    br label %if.end.4155
if.end.4155:
    %t4158 = load i64, i64* %ai_v4145
    %t4159 = load i64, i64* %bi_v4148
    %t4161 = icmp sgt i64 %t4158, %t4159
    %t4160 = zext i1 %t4161 to i64
    %t4165 = icmp ne i64 %t4160, 0
    br i1 %t4165, label %if.then.4162, label %if.end.4164
if.then.4162:
    ret i64 1
    br label %if.end.4164
if.end.4164:
    br label %if.end.4108
if.end.4108:
    %t4166 = load i64, i64* %ci_v4086
    %t4167 = add i64 %t4166, 1
    store i64 %t4167, i64* %ci_v4086
    br label %loop.cond.4087
loop.end.4089:
    %t4168 = load i64, i64* %a_pre_v4035
    %t4169 = call i64 @freak_llvm_word_length(i64 %t4168)
    %t4170 = load i64, i64* %b_pre_v4038
    %t4171 = call i64 @freak_llvm_word_length(i64 %t4170)
    %t4173 = icmp slt i64 %t4169, %t4171
    %t4172 = zext i1 %t4173 to i64
    %t4177 = icmp ne i64 %t4172, 0
    br i1 %t4177, label %if.then.4174, label %if.end.4176
if.then.4174:
    %t4178 = sub i64 0, 1
    ret i64 %t4178
    br label %if.end.4176
if.end.4176:
    %t4179 = load i64, i64* %a_pre_v4035
    %t4180 = call i64 @freak_llvm_word_length(i64 %t4179)
    %t4181 = load i64, i64* %b_pre_v4038
    %t4182 = call i64 @freak_llvm_word_length(i64 %t4181)
    %t4184 = icmp sgt i64 %t4180, %t4182
    %t4183 = zext i1 %t4184 to i64
    %t4188 = icmp ne i64 %t4183, 0
    br i1 %t4188, label %if.then.4185, label %if.end.4187
if.then.4185:
    ret i64 1
    br label %if.end.4187
if.end.4187:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_eq(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4189 = load i64, i64* @g_a
    %t4190 = load i64, i64* @g_b
    %t4191 = call i64 @freak_ver_compare(i64 %t4189, i64 %t4190)
    %t4193 = icmp eq i64 %t4191, 0
    %t4192 = zext i1 %t4193 to i64
    ret i64 %t4192
    ret i64 0
}

define i64 @freak_ver_lt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4194 = load i64, i64* @g_a
    %t4195 = load i64, i64* @g_b
    %t4196 = call i64 @freak_ver_compare(i64 %t4194, i64 %t4195)
    %t4198 = icmp slt i64 %t4196, 0
    %t4197 = zext i1 %t4198 to i64
    ret i64 %t4197
    ret i64 0
}

define i64 @freak_ver_gt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4199 = load i64, i64* @g_a
    %t4200 = load i64, i64* @g_b
    %t4201 = call i64 @freak_ver_compare(i64 %t4199, i64 %t4200)
    %t4203 = icmp sgt i64 %t4201, 0
    %t4202 = zext i1 %t4203 to i64
    ret i64 %t4202
    ret i64 0
}

define i64 @freak_ver_lte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4204 = load i64, i64* @g_a
    %t4205 = load i64, i64* @g_b
    %t4206 = call i64 @freak_ver_compare(i64 %t4204, i64 %t4205)
    %t4208 = icmp sle i64 %t4206, 0
    %t4207 = zext i1 %t4208 to i64
    ret i64 %t4207
    ret i64 0
}

define i64 @freak_ver_gte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4209 = load i64, i64* @g_a
    %t4210 = load i64, i64* @g_b
    %t4211 = call i64 @freak_ver_compare(i64 %t4209, i64 %t4210)
    %t4213 = icmp sge i64 %t4211, 0
    %t4212 = zext i1 %t4213 to i64
    ret i64 %t4212
    ret i64 0
}

define i64 @freak_ver_bump_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4214 = load i64, i64* %parsed
    %t4215 = call i64 @freak_ver_major(i64 %t4214)
    %t4216 = add i64 %t4215, 1
    %maj_v4217 = alloca i64
    store i64 %t4216, i64* %maj_v4217
    %t4218 = load i64, i64* %maj_v4217
    %t4219 = call i64 @freak_llvm_word_from_int(i64 %t4218)
    %t4220 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.265, i64 0, i64 0
    %t4221 = ptrtoint i8* %t4220 to i64
    %t4222 = call i64 @freak_llvm_word_concat(i64 %t4219, i64 %t4221)
    ret i64 %t4222
    ret i64 0
}

define i64 @freak_ver_bump_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4223 = load i64, i64* %parsed
    %t4224 = call i64 @freak_ver_major(i64 %t4223)
    %maj_v4225 = alloca i64
    store i64 %t4224, i64* %maj_v4225
    %t4226 = load i64, i64* %parsed
    %t4227 = call i64 @freak_ver_minor(i64 %t4226)
    %t4228 = add i64 %t4227, 1
    %min_v4229 = alloca i64
    store i64 %t4228, i64* %min_v4229
    %t4230 = load i64, i64* %maj_v4225
    %t4231 = call i64 @freak_llvm_word_from_int(i64 %t4230)
    %t4232 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.266, i64 0, i64 0
    %t4233 = ptrtoint i8* %t4232 to i64
    %t4234 = call i64 @freak_llvm_word_concat(i64 %t4231, i64 %t4233)
    %t4235 = load i64, i64* %min_v4229
    %t4236 = call i64 @freak_llvm_word_from_int(i64 %t4235)
    %t4237 = call i64 @freak_llvm_word_concat(i64 %t4234, i64 %t4236)
    %t4238 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.267, i64 0, i64 0
    %t4239 = ptrtoint i8* %t4238 to i64
    %t4240 = call i64 @freak_llvm_word_concat(i64 %t4237, i64 %t4239)
    ret i64 %t4240
    ret i64 0
}

define i64 @freak_ver_bump_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4241 = load i64, i64* %parsed
    %t4242 = call i64 @freak_ver_major(i64 %t4241)
    %maj_v4243 = alloca i64
    store i64 %t4242, i64* %maj_v4243
    %t4244 = load i64, i64* %parsed
    %t4245 = call i64 @freak_ver_minor(i64 %t4244)
    %min_v4246 = alloca i64
    store i64 %t4245, i64* %min_v4246
    %t4247 = load i64, i64* %parsed
    %t4248 = call i64 @freak_ver_patch(i64 %t4247)
    %t4249 = add i64 %t4248, 1
    %pat_v4250 = alloca i64
    store i64 %t4249, i64* %pat_v4250
    %t4251 = load i64, i64* %maj_v4243
    %t4252 = call i64 @freak_llvm_word_from_int(i64 %t4251)
    %t4253 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.268, i64 0, i64 0
    %t4254 = ptrtoint i8* %t4253 to i64
    %t4255 = call i64 @freak_llvm_word_concat(i64 %t4252, i64 %t4254)
    %t4256 = load i64, i64* %min_v4246
    %t4257 = call i64 @freak_llvm_word_from_int(i64 %t4256)
    %t4258 = call i64 @freak_llvm_word_concat(i64 %t4255, i64 %t4257)
    %t4259 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.269, i64 0, i64 0
    %t4260 = ptrtoint i8* %t4259 to i64
    %t4261 = call i64 @freak_llvm_word_concat(i64 %t4258, i64 %t4260)
    %t4262 = load i64, i64* %pat_v4250
    %t4263 = call i64 @freak_llvm_word_from_int(i64 %t4262)
    %t4264 = call i64 @freak_llvm_word_concat(i64 %t4261, i64 %t4263)
    %t4265 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.270, i64 0, i64 0
    %t4266 = ptrtoint i8* %t4265 to i64
    %t4267 = call i64 @freak_llvm_word_concat(i64 %t4264, i64 %t4266)
    ret i64 %t4267
    ret i64 0
}

define i64 @freak_ver_strip_prefix(i64 %arg_constraint, i64 %arg_prefix_len) {
entry:
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %prefix_len = alloca i64
    store i64 %arg_prefix_len, i64* %prefix_len
    %t4268 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.271, i64 0, i64 0
    %t4269 = ptrtoint i8* %t4268 to i64
    %stripped_v4270 = alloca i64
    store i64 %t4269, i64* %stripped_v4270
    %t4271 = load i64, i64* %prefix_len
    %si_v4272 = alloca i64
    store i64 %t4271, i64* %si_v4272
    br label %loop.cond.4273
loop.cond.4273:
    %t4276 = load i64, i64* %si_v4272
    %t4277 = load i64, i64* %constraint
    %t4278 = call i64 @freak_llvm_word_length(i64 %t4277)
    %t4280 = icmp sge i64 %t4276, %t4278
    %t4279 = zext i1 %t4280 to i64
    %t4281 = icmp eq i64 %t4279, 0
    br i1 %t4281, label %loop.body.4274, label %loop.end.4275
loop.body.4274:
    %t4282 = load i64, i64* %stripped_v4270
    %t4283 = load i64, i64* %constraint
    %t4285 = load i64, i64* %si_v4272
    %t4284 = call i64 @freak_llvm_word_char_at(i64 %t4283, i64 %t4285)
    %t4286 = call i64 @freak_llvm_word_concat(i64 %t4282, i64 %t4284)
    store i64 %t4286, i64* %stripped_v4270
    %t4287 = load i64, i64* %si_v4272
    %t4288 = add i64 %t4287, 1
    store i64 %t4288, i64* %si_v4272
    br label %loop.cond.4273
loop.end.4275:
    %t4289 = load i64, i64* %stripped_v4270
    ret i64 %t4289
    ret i64 0
}

define i64 @freak_ver_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t4290 = load i64, i64* %c
    %t4291 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.272, i64 0, i64 0
    %t4292 = ptrtoint i8* %t4291 to i64
    %t4293 = call i64 @freak_llvm_word_eq(i64 %t4290, i64 %t4292)
    %t4297 = icmp ne i64 %t4293, 0
    br i1 %t4297, label %if.then.4294, label %if.end.4296
if.then.4294:
    ret i64 1
    br label %if.end.4296
if.end.4296:
    %t4298 = load i64, i64* %c
    %t4299 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.273, i64 0, i64 0
    %t4300 = ptrtoint i8* %t4299 to i64
    %t4301 = call i64 @freak_llvm_word_eq(i64 %t4298, i64 %t4300)
    %t4305 = icmp ne i64 %t4301, 0
    br i1 %t4305, label %if.then.4302, label %if.end.4304
if.then.4302:
    ret i64 1
    br label %if.end.4304
if.end.4304:
    %t4306 = load i64, i64* %c
    %t4307 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.274, i64 0, i64 0
    %t4308 = ptrtoint i8* %t4307 to i64
    %t4309 = call i64 @freak_llvm_word_eq(i64 %t4306, i64 %t4308)
    %t4313 = icmp ne i64 %t4309, 0
    br i1 %t4313, label %if.then.4310, label %if.end.4312
if.then.4310:
    ret i64 1
    br label %if.end.4312
if.end.4312:
    %t4314 = load i64, i64* %c
    %t4315 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.275, i64 0, i64 0
    %t4316 = ptrtoint i8* %t4315 to i64
    %t4317 = call i64 @freak_llvm_word_eq(i64 %t4314, i64 %t4316)
    %t4321 = icmp ne i64 %t4317, 0
    br i1 %t4321, label %if.then.4318, label %if.end.4320
if.then.4318:
    ret i64 1
    br label %if.end.4320
if.end.4320:
    %t4322 = load i64, i64* %c
    %t4323 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.276, i64 0, i64 0
    %t4324 = ptrtoint i8* %t4323 to i64
    %t4325 = call i64 @freak_llvm_word_eq(i64 %t4322, i64 %t4324)
    %t4329 = icmp ne i64 %t4325, 0
    br i1 %t4329, label %if.then.4326, label %if.end.4328
if.then.4326:
    ret i64 1
    br label %if.end.4328
if.end.4328:
    %t4330 = load i64, i64* %c
    %t4331 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.277, i64 0, i64 0
    %t4332 = ptrtoint i8* %t4331 to i64
    %t4333 = call i64 @freak_llvm_word_eq(i64 %t4330, i64 %t4332)
    %t4337 = icmp ne i64 %t4333, 0
    br i1 %t4337, label %if.then.4334, label %if.end.4336
if.then.4334:
    ret i64 1
    br label %if.end.4336
if.end.4336:
    %t4338 = load i64, i64* %c
    %t4339 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.278, i64 0, i64 0
    %t4340 = ptrtoint i8* %t4339 to i64
    %t4341 = call i64 @freak_llvm_word_eq(i64 %t4338, i64 %t4340)
    %t4345 = icmp ne i64 %t4341, 0
    br i1 %t4345, label %if.then.4342, label %if.end.4344
if.then.4342:
    ret i64 1
    br label %if.end.4344
if.end.4344:
    %t4346 = load i64, i64* %c
    %t4347 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.279, i64 0, i64 0
    %t4348 = ptrtoint i8* %t4347 to i64
    %t4349 = call i64 @freak_llvm_word_eq(i64 %t4346, i64 %t4348)
    %t4353 = icmp ne i64 %t4349, 0
    br i1 %t4353, label %if.then.4350, label %if.end.4352
if.then.4350:
    ret i64 1
    br label %if.end.4352
if.end.4352:
    %t4354 = load i64, i64* %c
    %t4355 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.280, i64 0, i64 0
    %t4356 = ptrtoint i8* %t4355 to i64
    %t4357 = call i64 @freak_llvm_word_eq(i64 %t4354, i64 %t4356)
    %t4361 = icmp ne i64 %t4357, 0
    br i1 %t4361, label %if.then.4358, label %if.end.4360
if.then.4358:
    ret i64 1
    br label %if.end.4360
if.end.4360:
    %t4362 = load i64, i64* %c
    %t4363 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.281, i64 0, i64 0
    %t4364 = ptrtoint i8* %t4363 to i64
    %t4365 = call i64 @freak_llvm_word_eq(i64 %t4362, i64 %t4364)
    %t4369 = icmp ne i64 %t4365, 0
    br i1 %t4369, label %if.then.4366, label %if.end.4368
if.then.4366:
    ret i64 1
    br label %if.end.4368
if.end.4368:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_satisfies_single(i64 %arg_v, i64 %arg_constraint) {
entry:
    %v = alloca i64
    store i64 %arg_v, i64* %v
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4370 = load i64, i64* %constraint
    %t4371 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.282, i64 0, i64 0
    %t4372 = ptrtoint i8* %t4371 to i64
    %t4373 = call i64 @freak_llvm_word_eq(i64 %t4370, i64 %t4372)
    %t4374 = load i64, i64* %constraint
    %t4375 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.283, i64 0, i64 0
    %t4376 = ptrtoint i8* %t4375 to i64
    %t4377 = call i64 @freak_llvm_word_eq(i64 %t4374, i64 %t4376)
    %t4379 = icmp ne i64 %t4373, 0
    %t4380 = icmp ne i64 %t4377, 0
    %t4381 = or i1 %t4379, %t4380
    %t4378 = zext i1 %t4381 to i64
    %t4385 = icmp ne i64 %t4378, 0
    br i1 %t4385, label %if.then.4382, label %if.end.4384
if.then.4382:
    ret i64 1
    br label %if.end.4384
if.end.4384:
    %t4386 = load i64, i64* %constraint
    %t4388 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.284, i64 0, i64 0
    %t4389 = ptrtoint i8* %t4388 to i64
    %t4387 = call i64 @freak_llvm_word_starts_with(i64 %t4386, i64 %t4389)
    %t4393 = icmp ne i64 %t4387, 0
    br i1 %t4393, label %if.then.4390, label %if.end.4392
if.then.4390:
    %t4394 = load i64, i64* %constraint
    %t4395 = call i64 @freak_ver_strip_prefix(i64 %t4394, i64 1)
    %t4396 = call i64 @freak_ver_parse(i64 %t4395)
    %c_v4397 = alloca i64
    store i64 %t4396, i64* %c_v4397
    %t4398 = load i64, i64* %v
    %t4399 = call i64 @freak_ver_major(i64 %t4398)
    %t4400 = load i64, i64* %c_v4397
    %t4401 = call i64 @freak_ver_major(i64 %t4400)
    %t4403 = icmp ne i64 %t4399, %t4401
    %t4402 = zext i1 %t4403 to i64
    %t4407 = icmp ne i64 %t4402, 0
    br i1 %t4407, label %if.then.4404, label %if.end.4406
if.then.4404:
    ret i64 0
    br label %if.end.4406
if.end.4406:
    %t4408 = load i64, i64* %v
    %t4409 = load i64, i64* %c_v4397
    %t4410 = call i64 @freak_ver_gte(i64 %t4408, i64 %t4409)
    ret i64 %t4410
    br label %if.end.4392
if.end.4392:
    %t4411 = load i64, i64* %constraint
    %t4413 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.285, i64 0, i64 0
    %t4414 = ptrtoint i8* %t4413 to i64
    %t4412 = call i64 @freak_llvm_word_starts_with(i64 %t4411, i64 %t4414)
    %t4418 = icmp ne i64 %t4412, 0
    br i1 %t4418, label %if.then.4415, label %if.end.4417
if.then.4415:
    %t4419 = load i64, i64* %constraint
    %t4420 = call i64 @freak_ver_strip_prefix(i64 %t4419, i64 1)
    %t4421 = call i64 @freak_ver_parse(i64 %t4420)
    %t_v4422 = alloca i64
    store i64 %t4421, i64* %t_v4422
    %t4423 = load i64, i64* %v
    %t4424 = call i64 @freak_ver_major(i64 %t4423)
    %t4425 = load i64, i64* %t_v4422
    %t4426 = call i64 @freak_ver_major(i64 %t4425)
    %t4428 = icmp ne i64 %t4424, %t4426
    %t4427 = zext i1 %t4428 to i64
    %t4432 = icmp ne i64 %t4427, 0
    br i1 %t4432, label %if.then.4429, label %if.end.4431
if.then.4429:
    ret i64 0
    br label %if.end.4431
if.end.4431:
    %t4433 = load i64, i64* %v
    %t4434 = call i64 @freak_ver_minor(i64 %t4433)
    %t4435 = load i64, i64* %t_v4422
    %t4436 = call i64 @freak_ver_minor(i64 %t4435)
    %t4438 = icmp ne i64 %t4434, %t4436
    %t4437 = zext i1 %t4438 to i64
    %t4442 = icmp ne i64 %t4437, 0
    br i1 %t4442, label %if.then.4439, label %if.end.4441
if.then.4439:
    ret i64 0
    br label %if.end.4441
if.end.4441:
    %t4443 = load i64, i64* %v
    %t4444 = load i64, i64* %t_v4422
    %t4445 = call i64 @freak_ver_gte(i64 %t4443, i64 %t4444)
    ret i64 %t4445
    br label %if.end.4417
if.end.4417:
    %t4446 = load i64, i64* %constraint
    %t4448 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.286, i64 0, i64 0
    %t4449 = ptrtoint i8* %t4448 to i64
    %t4447 = call i64 @freak_llvm_word_starts_with(i64 %t4446, i64 %t4449)
    %t4453 = icmp ne i64 %t4447, 0
    br i1 %t4453, label %if.then.4450, label %if.end.4452
if.then.4450:
    %t4454 = load i64, i64* %v
    %t4455 = load i64, i64* %constraint
    %t4456 = call i64 @freak_ver_strip_prefix(i64 %t4455, i64 2)
    %t4457 = call i64 @freak_ver_parse(i64 %t4456)
    %t4458 = call i64 @freak_ver_gte(i64 %t4454, i64 %t4457)
    ret i64 %t4458
    br label %if.end.4452
if.end.4452:
    %t4459 = load i64, i64* %constraint
    %t4461 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.287, i64 0, i64 0
    %t4462 = ptrtoint i8* %t4461 to i64
    %t4460 = call i64 @freak_llvm_word_starts_with(i64 %t4459, i64 %t4462)
    %t4466 = icmp ne i64 %t4460, 0
    br i1 %t4466, label %if.then.4463, label %if.end.4465
if.then.4463:
    %t4467 = load i64, i64* %v
    %t4468 = load i64, i64* %constraint
    %t4469 = call i64 @freak_ver_strip_prefix(i64 %t4468, i64 2)
    %t4470 = call i64 @freak_ver_parse(i64 %t4469)
    %t4471 = call i64 @freak_ver_lte(i64 %t4467, i64 %t4470)
    ret i64 %t4471
    br label %if.end.4465
if.end.4465:
    %t4472 = load i64, i64* %constraint
    %t4474 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.288, i64 0, i64 0
    %t4475 = ptrtoint i8* %t4474 to i64
    %t4473 = call i64 @freak_llvm_word_starts_with(i64 %t4472, i64 %t4475)
    %t4479 = icmp ne i64 %t4473, 0
    br i1 %t4479, label %if.then.4476, label %if.end.4478
if.then.4476:
    %t4480 = load i64, i64* %v
    %t4481 = load i64, i64* %constraint
    %t4482 = call i64 @freak_ver_strip_prefix(i64 %t4481, i64 1)
    %t4483 = call i64 @freak_ver_parse(i64 %t4482)
    %t4484 = call i64 @freak_ver_gt(i64 %t4480, i64 %t4483)
    ret i64 %t4484
    br label %if.end.4478
if.end.4478:
    %t4485 = load i64, i64* %constraint
    %t4487 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.289, i64 0, i64 0
    %t4488 = ptrtoint i8* %t4487 to i64
    %t4486 = call i64 @freak_llvm_word_starts_with(i64 %t4485, i64 %t4488)
    %t4492 = icmp ne i64 %t4486, 0
    br i1 %t4492, label %if.then.4489, label %if.end.4491
if.then.4489:
    %t4493 = load i64, i64* %v
    %t4494 = load i64, i64* %constraint
    %t4495 = call i64 @freak_ver_strip_prefix(i64 %t4494, i64 1)
    %t4496 = call i64 @freak_ver_parse(i64 %t4495)
    %t4497 = call i64 @freak_ver_lt(i64 %t4493, i64 %t4496)
    ret i64 %t4497
    br label %if.end.4491
if.end.4491:
    %t4498 = load i64, i64* %constraint
    %t4500 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.290, i64 0, i64 0
    %t4501 = ptrtoint i8* %t4500 to i64
    %t4499 = call i64 @freak_llvm_word_starts_with(i64 %t4498, i64 %t4501)
    %t4505 = icmp ne i64 %t4499, 0
    br i1 %t4505, label %if.then.4502, label %if.end.4504
if.then.4502:
    %t4506 = load i64, i64* %v
    %t4507 = load i64, i64* %constraint
    %t4508 = call i64 @freak_ver_strip_prefix(i64 %t4507, i64 1)
    %t4509 = call i64 @freak_ver_parse(i64 %t4508)
    %t4510 = call i64 @freak_ver_eq(i64 %t4506, i64 %t4509)
    ret i64 %t4510
    br label %if.end.4504
if.end.4504:
    %t4511 = load i64, i64* %constraint
    %t4512 = call i64 @freak_llvm_word_length(i64 %t4511)
    %t4514 = icmp sgt i64 %t4512, 0
    %t4513 = zext i1 %t4514 to i64
    %t4518 = icmp ne i64 %t4513, 0
    br i1 %t4518, label %if.then.4515, label %if.end.4517
if.then.4515:
    %t4519 = load i64, i64* %constraint
    %t4520 = call i64 @freak_llvm_word_char_at(i64 %t4519, i64 0)
    %fc_v4521 = alloca i64
    store i64 %t4520, i64* %fc_v4521
    %t4522 = load i64, i64* %fc_v4521
    %t4523 = call i64 @freak_ver_is_digit(i64 %t4522)
    %t4527 = icmp ne i64 %t4523, 0
    br i1 %t4527, label %if.then.4524, label %if.end.4526
if.then.4524:
    %t4528 = load i64, i64* %constraint
    %t4529 = call i64 @freak_ver_parse(i64 %t4528)
    %c_v4530 = alloca i64
    store i64 %t4529, i64* %c_v4530
    %t4531 = load i64, i64* %v
    %t4532 = call i64 @freak_ver_major(i64 %t4531)
    %t4533 = load i64, i64* %c_v4530
    %t4534 = call i64 @freak_ver_major(i64 %t4533)
    %t4536 = icmp ne i64 %t4532, %t4534
    %t4535 = zext i1 %t4536 to i64
    %t4540 = icmp ne i64 %t4535, 0
    br i1 %t4540, label %if.then.4537, label %if.end.4539
if.then.4537:
    ret i64 0
    br label %if.end.4539
if.end.4539:
    %t4541 = load i64, i64* %v
    %t4542 = load i64, i64* %c_v4530
    %t4543 = call i64 @freak_ver_gte(i64 %t4541, i64 %t4542)
    ret i64 %t4543
    br label %if.end.4526
if.end.4526:
    br label %if.end.4517
if.end.4517:
    %t4544 = load i64, i64* %v
    %t4545 = load i64, i64* %constraint
    %t4546 = call i64 @freak_ver_parse(i64 %t4545)
    %t4547 = call i64 @freak_ver_eq(i64 %t4544, i64 %t4546)
    ret i64 %t4547
    ret i64 0
}

define i64 @freak_ver_satisfies(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4548 = load i64, i64* %version
    %t4549 = call i64 @freak_ver_parse(i64 %t4548)
    %v_v4550 = alloca i64
    store i64 %t4549, i64* %v_v4550
    %t4551 = load i64, i64* %constraint
    %t4552 = call i64 @freak_llvm_word_length(i64 %t4551)
    %clen_v4553 = alloca i64
    store i64 %t4552, i64* %clen_v4553
    %t4554 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.291, i64 0, i64 0
    %t4555 = ptrtoint i8* %t4554 to i64
    %current_v4556 = alloca i64
    store i64 %t4555, i64* %current_v4556
    %i_v4557 = alloca i64
    store i64 0, i64* %i_v4557
    br label %loop.cond.4558
loop.cond.4558:
    %t4561 = load i64, i64* %i_v4557
    %t4562 = load i64, i64* %clen_v4553
    %t4564 = icmp sge i64 %t4561, %t4562
    %t4563 = zext i1 %t4564 to i64
    %t4565 = icmp eq i64 %t4563, 0
    br i1 %t4565, label %loop.body.4559, label %loop.end.4560
loop.body.4559:
    %t4566 = load i64, i64* %constraint
    %t4568 = load i64, i64* %i_v4557
    %t4567 = call i64 @freak_llvm_word_char_at(i64 %t4566, i64 %t4568)
    %ch_v4569 = alloca i64
    store i64 %t4567, i64* %ch_v4569
    %t4570 = load i64, i64* %ch_v4569
    %t4571 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.292, i64 0, i64 0
    %t4572 = ptrtoint i8* %t4571 to i64
    %t4573 = call i64 @freak_llvm_word_eq(i64 %t4570, i64 %t4572)
    %t4577 = icmp ne i64 %t4573, 0
    br i1 %t4577, label %if.then.4574, label %if.else.4575
if.then.4574:
    %t4578 = load i64, i64* %current_v4556
    %t4579 = call i64 @freak_llvm_word_length(i64 %t4578)
    %t4581 = icmp sgt i64 %t4579, 0
    %t4580 = zext i1 %t4581 to i64
    %t4585 = icmp ne i64 %t4580, 0
    br i1 %t4585, label %if.then.4582, label %if.end.4584
if.then.4582:
    %t4586 = load i64, i64* %v_v4550
    %t4587 = load i64, i64* %current_v4556
    %t4588 = call i64 @freak_ver_satisfies_single(i64 %t4586, i64 %t4587)
    %t4590 = icmp eq i64 %t4588, 0
    %t4589 = zext i1 %t4590 to i64
    %t4594 = icmp ne i64 %t4589, 0
    br i1 %t4594, label %if.then.4591, label %if.end.4593
if.then.4591:
    ret i64 0
    br label %if.end.4593
if.end.4593:
    %t4595 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.293, i64 0, i64 0
    %t4596 = ptrtoint i8* %t4595 to i64
    store i64 %t4596, i64* %current_v4556
    br label %if.end.4584
if.end.4584:
    br label %if.end.4576
if.else.4575:
    %t4597 = load i64, i64* %current_v4556
    %t4598 = load i64, i64* %ch_v4569
    %t4599 = call i64 @freak_llvm_word_concat(i64 %t4597, i64 %t4598)
    store i64 %t4599, i64* %current_v4556
    br label %if.end.4576
if.end.4576:
    %t4600 = load i64, i64* %i_v4557
    %t4601 = add i64 %t4600, 1
    store i64 %t4601, i64* %i_v4557
    br label %loop.cond.4558
loop.end.4560:
    %t4602 = load i64, i64* %current_v4556
    %t4603 = call i64 @freak_llvm_word_length(i64 %t4602)
    %t4605 = icmp sgt i64 %t4603, 0
    %t4604 = zext i1 %t4605 to i64
    %t4609 = icmp ne i64 %t4604, 0
    br i1 %t4609, label %if.then.4606, label %if.end.4608
if.then.4606:
    %t4610 = load i64, i64* %v_v4550
    %t4611 = load i64, i64* %current_v4556
    %t4612 = call i64 @freak_ver_satisfies_single(i64 %t4610, i64 %t4611)
    %t4614 = icmp eq i64 %t4612, 0
    %t4613 = zext i1 %t4614 to i64
    %t4618 = icmp ne i64 %t4613, 0
    br i1 %t4618, label %if.then.4615, label %if.end.4617
if.then.4615:
    ret i64 0
    br label %if.end.4617
if.end.4617:
    br label %if.end.4608
if.end.4608:
    ret i64 1
    ret i64 0
}

define i64 @freak_version_matches_constraint(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4619 = load i64, i64* %version
    %t4620 = load i64, i64* %constraint
    %t4621 = call i64 @freak_ver_satisfies(i64 %t4619, i64 %t4620)
    ret i64 %t4621
    ret i64 0
}

define void @freak_http_init() {
entry:
    %t4622 = load i64, i64* @g_http_inited
    %t4624 = icmp eq i64 %t4622, 0
    %t4623 = zext i1 %t4624 to i64
    %t4628 = icmp ne i64 %t4623, 0
    br i1 %t4628, label %if.then.4625, label %if.end.4627
if.then.4625:
    %t4629 = call i64 @freak_llvm_array_new()
    store i64 %t4629, i64* @g_http_resp_statuses
    %t4630 = call i64 @freak_llvm_array_new()
    store i64 %t4630, i64* @g_http_resp_bodies
    %t4631 = call i64 @freak_llvm_array_new()
    store i64 %t4631, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 1, i64* @g_http_inited
    br label %if.end.4627
if.end.4627:
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
    %t4632 = load i64, i64* @g_http_resp_count
    %idx_v4633 = alloca i64
    store i64 %t4632, i64* %idx_v4633
    %t4634 = load i64, i64* @g_http_resp_statuses
    %t4635 = load i64, i64* %status
    %t4636 = call i64 @freak_llvm_word_from_int(i64 %t4635)
    call void @freak_llvm_array_push(i64 %t4634, i64 %t4636)
    %t4637 = load i64, i64* @g_http_resp_bodies
    %t4638 = load i64, i64* %body
    call void @freak_llvm_array_push(i64 %t4637, i64 %t4638)
    %t4639 = load i64, i64* @g_http_resp_headers_raw
    %t4640 = load i64, i64* %headers
    call void @freak_llvm_array_push(i64 %t4639, i64 %t4640)
    %t4641 = load i64, i64* @g_http_resp_count
    %t4642 = add i64 %t4641, 1
    store i64 %t4642, i64* @g_http_resp_count
    %t4643 = load i64, i64* %idx_v4633
    ret i64 %t4643
    ret i64 0
}

define i64 @freak_http_resp_status(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4644 = load i64, i64* @g_http_resp_statuses
    %t4645 = load i64, i64* %handle
    %t4646 = call i64 @freak_llvm_array_get(i64 %t4644, i64 %t4645)
    %v_v4647 = alloca i64
    store i64 %t4646, i64* %v_v4647
    %t4648 = load i64, i64* %v_v4647
    %t4649 = call i64 @freak_llvm_word_to_int(i64 %t4648)
    ret i64 %t4649
    ret i64 0
}

define i64 @freak_http_resp_body(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4650 = load i64, i64* @g_http_resp_bodies
    %t4651 = load i64, i64* %handle
    %t4652 = call i64 @freak_llvm_array_get(i64 %t4650, i64 %t4651)
    ret i64 %t4652
    ret i64 0
}

define i64 @freak_http_resp_headers(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4653 = load i64, i64* @g_http_resp_headers_raw
    %t4654 = load i64, i64* %handle
    %t4655 = call i64 @freak_llvm_array_get(i64 %t4653, i64 %t4654)
    ret i64 %t4655
    ret i64 0
}

define i64 @freak_http_parse_status(i64 %arg_line) {
entry:
    %line = alloca i64
    store i64 %arg_line, i64* %line
    %t4656 = load i64, i64* %line
    %t4657 = call i64 @freak_llvm_word_length(i64 %t4656)
    %slen_v4658 = alloca i64
    store i64 %t4657, i64* %slen_v4658
    %si_v4659 = alloca i64
    store i64 0, i64* %si_v4659
    %t4665 = load i64, i64* %slen_v4658
    %rep.4664 = alloca i64
    store i64 0, i64* %rep.4664
    br label %loop.cond.4660
loop.cond.4660:
    %t4666 = load i64, i64* %rep.4664
    %t4667 = icmp slt i64 %t4666, %t4665
    br i1 %t4667, label %loop.body.4661, label %loop.end.4662
loop.body.4661:
    %t4668 = load i64, i64* %line
    %t4670 = load i64, i64* %si_v4659
    %t4669 = call i64 @freak_llvm_word_char_at(i64 %t4668, i64 %t4670)
    %t4671 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.294, i64 0, i64 0
    %t4672 = ptrtoint i8* %t4671 to i64
    %t4673 = call i64 @freak_llvm_word_eq(i64 %t4669, i64 %t4672)
    %t4677 = icmp ne i64 %t4673, 0
    br i1 %t4677, label %if.then.4674, label %if.end.4676
if.then.4674:
    %t4678 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.295, i64 0, i64 0
    %t4679 = ptrtoint i8* %t4678 to i64
    %code_str_v4680 = alloca i64
    store i64 %t4679, i64* %code_str_v4680
    %t4681 = load i64, i64* %si_v4659
    %t4682 = add i64 %t4681, 1
    %ci_v4683 = alloca i64
    store i64 %t4682, i64* %ci_v4683
    %rep.4688 = alloca i64
    store i64 0, i64* %rep.4688
    br label %loop.cond.4684
loop.cond.4684:
    %t4689 = load i64, i64* %rep.4688
    %t4690 = icmp slt i64 %t4689, 3
    br i1 %t4690, label %loop.body.4685, label %loop.end.4686
loop.body.4685:
    %t4691 = load i64, i64* %ci_v4683
    %t4692 = load i64, i64* %slen_v4658
    %t4694 = icmp slt i64 %t4691, %t4692
    %t4693 = zext i1 %t4694 to i64
    %t4698 = icmp ne i64 %t4693, 0
    br i1 %t4698, label %if.then.4695, label %if.end.4697
if.then.4695:
    %t4699 = load i64, i64* %code_str_v4680
    %t4700 = load i64, i64* %line
    %t4702 = load i64, i64* %ci_v4683
    %t4701 = call i64 @freak_llvm_word_char_at(i64 %t4700, i64 %t4702)
    %t4703 = call i64 @freak_llvm_word_concat(i64 %t4699, i64 %t4701)
    store i64 %t4703, i64* %code_str_v4680
    %t4704 = load i64, i64* %ci_v4683
    %t4705 = add i64 %t4704, 1
    store i64 %t4705, i64* %ci_v4683
    br label %if.end.4697
if.end.4697:
    br label %loop.inc.4687
loop.inc.4687:
    %t4706 = load i64, i64* %rep.4688
    %t4707 = add i64 %t4706, 1
    store i64 %t4707, i64* %rep.4688
    br label %loop.cond.4684
loop.end.4686:
    %t4708 = load i64, i64* %code_str_v4680
    %t4709 = call i64 @freak_llvm_word_to_int(i64 %t4708)
    ret i64 %t4709
    br label %if.end.4676
if.end.4676:
    %t4710 = load i64, i64* %si_v4659
    %t4711 = add i64 %t4710, 1
    store i64 %t4711, i64* %si_v4659
    br label %loop.inc.4663
loop.inc.4663:
    %t4712 = load i64, i64* %rep.4664
    %t4713 = add i64 %t4712, 1
    store i64 %t4713, i64* %rep.4664
    br label %loop.cond.4660
loop.end.4662:
    ret i64 0
    ret i64 0
}

define i64 @freak_http_split_response(i64 %arg_raw) {
entry:
    %raw = alloca i64
    store i64 %arg_raw, i64* %raw
    %t4714 = load i64, i64* %raw
    %t4715 = call i64 @freak_llvm_word_length(i64 %t4714)
    %rlen_v4716 = alloca i64
    store i64 %t4715, i64* %rlen_v4716
    %ri_v4717 = alloca i64
    store i64 0, i64* %ri_v4717
    %t4718 = sub i64 0, 1
    %header_end_v4719 = alloca i64
    store i64 %t4718, i64* %header_end_v4719
    %t4720 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.296, i64 0, i64 0
    %t4721 = ptrtoint i8* %t4720 to i64
    %prev3_v4722 = alloca i64
    store i64 %t4721, i64* %prev3_v4722
    %t4723 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.297, i64 0, i64 0
    %t4724 = ptrtoint i8* %t4723 to i64
    %prev2_v4725 = alloca i64
    store i64 %t4724, i64* %prev2_v4725
    %t4726 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.298, i64 0, i64 0
    %t4727 = ptrtoint i8* %t4726 to i64
    %prev1_v4728 = alloca i64
    store i64 %t4727, i64* %prev1_v4728
    %t4734 = load i64, i64* %rlen_v4716
    %rep.4733 = alloca i64
    store i64 0, i64* %rep.4733
    br label %loop.cond.4729
loop.cond.4729:
    %t4735 = load i64, i64* %rep.4733
    %t4736 = icmp slt i64 %t4735, %t4734
    br i1 %t4736, label %loop.body.4730, label %loop.end.4731
loop.body.4730:
    %t4737 = load i64, i64* %raw
    %t4739 = load i64, i64* %ri_v4717
    %t4738 = call i64 @freak_llvm_word_char_at(i64 %t4737, i64 %t4739)
    %ch_v4740 = alloca i64
    store i64 %t4738, i64* %ch_v4740
    %t4741 = load i64, i64* %prev2_v4725
    %t4742 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.299, i64 0, i64 0
    %t4743 = ptrtoint i8* %t4742 to i64
    %t4744 = call i64 @freak_llvm_word_eq(i64 %t4741, i64 %t4743)
    %t4745 = load i64, i64* %prev1_v4728
    %t4746 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.300, i64 0, i64 0
    %t4747 = ptrtoint i8* %t4746 to i64
    %t4748 = call i64 @freak_llvm_word_eq(i64 %t4745, i64 %t4747)
    %t4750 = icmp ne i64 %t4744, 0
    %t4751 = icmp ne i64 %t4748, 0
    %t4752 = and i1 %t4750, %t4751
    %t4749 = zext i1 %t4752 to i64
    %t4753 = load i64, i64* %ch_v4740
    %t4754 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.301, i64 0, i64 0
    %t4755 = ptrtoint i8* %t4754 to i64
    %t4756 = call i64 @freak_llvm_word_eq(i64 %t4753, i64 %t4755)
    %t4758 = icmp ne i64 %t4749, 0
    %t4759 = icmp ne i64 %t4756, 0
    %t4760 = and i1 %t4758, %t4759
    %t4757 = zext i1 %t4760 to i64
    %t4764 = icmp ne i64 %t4757, 0
    br i1 %t4764, label %if.then.4761, label %if.end.4763
if.then.4761:
    %t4765 = load i64, i64* %ri_v4717
    %t4766 = add i64 %t4765, 1
    store i64 %t4766, i64* %header_end_v4719
    br label %if.end.4763
if.end.4763:
    %t4767 = load i64, i64* %prev3_v4722
    %t4768 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.302, i64 0, i64 0
    %t4769 = ptrtoint i8* %t4768 to i64
    %t4770 = call i64 @freak_llvm_word_eq(i64 %t4767, i64 %t4769)
    %t4771 = load i64, i64* %prev2_v4725
    %t4772 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.303, i64 0, i64 0
    %t4773 = ptrtoint i8* %t4772 to i64
    %t4774 = call i64 @freak_llvm_word_eq(i64 %t4771, i64 %t4773)
    %t4776 = icmp ne i64 %t4770, 0
    %t4777 = icmp ne i64 %t4774, 0
    %t4778 = and i1 %t4776, %t4777
    %t4775 = zext i1 %t4778 to i64
    %t4779 = load i64, i64* %prev1_v4728
    %t4780 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.304, i64 0, i64 0
    %t4781 = ptrtoint i8* %t4780 to i64
    %t4782 = call i64 @freak_llvm_word_eq(i64 %t4779, i64 %t4781)
    %t4784 = icmp ne i64 %t4775, 0
    %t4785 = icmp ne i64 %t4782, 0
    %t4786 = and i1 %t4784, %t4785
    %t4783 = zext i1 %t4786 to i64
    %t4787 = load i64, i64* %ch_v4740
    %t4788 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.305, i64 0, i64 0
    %t4789 = ptrtoint i8* %t4788 to i64
    %t4790 = call i64 @freak_llvm_word_eq(i64 %t4787, i64 %t4789)
    %t4792 = icmp ne i64 %t4783, 0
    %t4793 = icmp ne i64 %t4790, 0
    %t4794 = and i1 %t4792, %t4793
    %t4791 = zext i1 %t4794 to i64
    %t4798 = icmp ne i64 %t4791, 0
    br i1 %t4798, label %if.then.4795, label %if.end.4797
if.then.4795:
    %t4799 = load i64, i64* %ri_v4717
    %t4800 = add i64 %t4799, 1
    store i64 %t4800, i64* %header_end_v4719
    br label %if.end.4797
if.end.4797:
    %t4801 = load i64, i64* %prev2_v4725
    store i64 %t4801, i64* %prev3_v4722
    %t4802 = load i64, i64* %prev1_v4728
    store i64 %t4802, i64* %prev2_v4725
    %t4803 = load i64, i64* %ch_v4740
    store i64 %t4803, i64* %prev1_v4728
    %t4804 = load i64, i64* %ri_v4717
    %t4805 = add i64 %t4804, 1
    store i64 %t4805, i64* %ri_v4717
    br label %loop.inc.4732
loop.inc.4732:
    %t4806 = load i64, i64* %rep.4733
    %t4807 = add i64 %t4806, 1
    store i64 %t4807, i64* %rep.4733
    br label %loop.cond.4729
loop.end.4731:
    %t4808 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.306, i64 0, i64 0
    %t4809 = ptrtoint i8* %t4808 to i64
    %status_line_v4810 = alloca i64
    store i64 %t4809, i64* %status_line_v4810
    %li_v4811 = alloca i64
    store i64 0, i64* %li_v4811
    %t4817 = load i64, i64* %rlen_v4716
    %rep.4816 = alloca i64
    store i64 0, i64* %rep.4816
    br label %loop.cond.4812
loop.cond.4812:
    %t4818 = load i64, i64* %rep.4816
    %t4819 = icmp slt i64 %t4818, %t4817
    br i1 %t4819, label %loop.body.4813, label %loop.end.4814
loop.body.4813:
    %t4820 = load i64, i64* %raw
    %t4822 = load i64, i64* %li_v4811
    %t4821 = call i64 @freak_llvm_word_char_at(i64 %t4820, i64 %t4822)
    %lc_v4823 = alloca i64
    store i64 %t4821, i64* %lc_v4823
    %t4824 = load i64, i64* %lc_v4823
    %t4825 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.307, i64 0, i64 0
    %t4826 = ptrtoint i8* %t4825 to i64
    %t4827 = call i64 @freak_llvm_word_eq(i64 %t4824, i64 %t4826)
    %t4828 = load i64, i64* %lc_v4823
    %t4829 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.308, i64 0, i64 0
    %t4830 = ptrtoint i8* %t4829 to i64
    %t4831 = call i64 @freak_llvm_word_eq(i64 %t4828, i64 %t4830)
    %t4833 = icmp ne i64 %t4827, 0
    %t4834 = icmp ne i64 %t4831, 0
    %t4835 = or i1 %t4833, %t4834
    %t4832 = zext i1 %t4835 to i64
    %t4839 = icmp ne i64 %t4832, 0
    br i1 %t4839, label %if.then.4836, label %if.else.4837
if.then.4836:
    %t4840 = load i64, i64* %rlen_v4716
    store i64 %t4840, i64* %li_v4811
    br label %if.end.4838
if.else.4837:
    %t4841 = load i64, i64* %status_line_v4810
    %t4842 = load i64, i64* %lc_v4823
    %t4843 = call i64 @freak_llvm_word_concat(i64 %t4841, i64 %t4842)
    store i64 %t4843, i64* %status_line_v4810
    br label %if.end.4838
if.end.4838:
    %t4844 = load i64, i64* %li_v4811
    %t4845 = add i64 %t4844, 1
    store i64 %t4845, i64* %li_v4811
    br label %loop.inc.4815
loop.inc.4815:
    %t4846 = load i64, i64* %rep.4816
    %t4847 = add i64 %t4846, 1
    store i64 %t4847, i64* %rep.4816
    br label %loop.cond.4812
loop.end.4814:
    %t4848 = load i64, i64* %status_line_v4810
    %t4849 = call i64 @freak_http_parse_status(i64 %t4848)
    %status_v4850 = alloca i64
    store i64 %t4849, i64* %status_v4850
    %t4851 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.309, i64 0, i64 0
    %t4852 = ptrtoint i8* %t4851 to i64
    %headers_v4853 = alloca i64
    store i64 %t4852, i64* %headers_v4853
    %t4854 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.310, i64 0, i64 0
    %t4855 = ptrtoint i8* %t4854 to i64
    %body_v4856 = alloca i64
    store i64 %t4855, i64* %body_v4856
    %t4857 = load i64, i64* %header_end_v4719
    %t4859 = icmp sgt i64 %t4857, 0
    %t4858 = zext i1 %t4859 to i64
    %t4863 = icmp ne i64 %t4858, 0
    br i1 %t4863, label %if.then.4860, label %if.else.4861
if.then.4860:
    %hi_v4864 = alloca i64
    store i64 0, i64* %hi_v4864
    %t4870 = load i64, i64* %header_end_v4719
    %rep.4869 = alloca i64
    store i64 0, i64* %rep.4869
    br label %loop.cond.4865
loop.cond.4865:
    %t4871 = load i64, i64* %rep.4869
    %t4872 = icmp slt i64 %t4871, %t4870
    br i1 %t4872, label %loop.body.4866, label %loop.end.4867
loop.body.4866:
    %t4873 = load i64, i64* %hi_v4864
    %t4874 = load i64, i64* %rlen_v4716
    %t4876 = icmp slt i64 %t4873, %t4874
    %t4875 = zext i1 %t4876 to i64
    %t4880 = icmp ne i64 %t4875, 0
    br i1 %t4880, label %if.then.4877, label %if.end.4879
if.then.4877:
    %t4881 = load i64, i64* %headers_v4853
    %t4882 = load i64, i64* %raw
    %t4884 = load i64, i64* %hi_v4864
    %t4883 = call i64 @freak_llvm_word_char_at(i64 %t4882, i64 %t4884)
    %t4885 = call i64 @freak_llvm_word_concat(i64 %t4881, i64 %t4883)
    store i64 %t4885, i64* %headers_v4853
    br label %if.end.4879
if.end.4879:
    %t4886 = load i64, i64* %hi_v4864
    %t4887 = add i64 %t4886, 1
    store i64 %t4887, i64* %hi_v4864
    br label %loop.inc.4868
loop.inc.4868:
    %t4888 = load i64, i64* %rep.4869
    %t4889 = add i64 %t4888, 1
    store i64 %t4889, i64* %rep.4869
    br label %loop.cond.4865
loop.end.4867:
    %t4890 = load i64, i64* %header_end_v4719
    %bi_v4891 = alloca i64
    store i64 %t4890, i64* %bi_v4891
    %t4897 = load i64, i64* %rlen_v4716
    %rep.4896 = alloca i64
    store i64 0, i64* %rep.4896
    br label %loop.cond.4892
loop.cond.4892:
    %t4898 = load i64, i64* %rep.4896
    %t4899 = icmp slt i64 %t4898, %t4897
    br i1 %t4899, label %loop.body.4893, label %loop.end.4894
loop.body.4893:
    %t4900 = load i64, i64* %bi_v4891
    %t4901 = load i64, i64* %rlen_v4716
    %t4903 = icmp slt i64 %t4900, %t4901
    %t4902 = zext i1 %t4903 to i64
    %t4907 = icmp ne i64 %t4902, 0
    br i1 %t4907, label %if.then.4904, label %if.end.4906
if.then.4904:
    %t4908 = load i64, i64* %body_v4856
    %t4909 = load i64, i64* %raw
    %t4911 = load i64, i64* %bi_v4891
    %t4910 = call i64 @freak_llvm_word_char_at(i64 %t4909, i64 %t4911)
    %t4912 = call i64 @freak_llvm_word_concat(i64 %t4908, i64 %t4910)
    store i64 %t4912, i64* %body_v4856
    br label %if.end.4906
if.end.4906:
    %t4913 = load i64, i64* %bi_v4891
    %t4914 = add i64 %t4913, 1
    store i64 %t4914, i64* %bi_v4891
    br label %loop.inc.4895
loop.inc.4895:
    %t4915 = load i64, i64* %rep.4896
    %t4916 = add i64 %t4915, 1
    store i64 %t4916, i64* %rep.4896
    br label %loop.cond.4892
loop.end.4894:
    br label %if.end.4862
if.else.4861:
    %t4917 = load i64, i64* %raw
    store i64 %t4917, i64* %headers_v4853
    br label %if.end.4862
if.end.4862:
    %t4918 = load i64, i64* %status_v4850
    %t4919 = load i64, i64* %body_v4856
    %t4920 = load i64, i64* %headers_v4853
    %t4921 = call i64 @freak_http_alloc_resp(i64 %t4918, i64 %t4919, i64 %t4920)
    ret i64 %t4921
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
    %t4922 = load i64, i64* %host
    %t4923 = load i64, i64* %port
    %t4924 = call i64 @freak_llvm_tcp_connect(i64 %t4922, i64 %t4923)
    %fd_v4925 = alloca i64
    store i64 %t4924, i64* %fd_v4925
    %t4926 = load i64, i64* %fd_v4925
    %t4928 = icmp slt i64 %t4926, 0
    %t4927 = zext i1 %t4928 to i64
    %t4932 = icmp ne i64 %t4927, 0
    br i1 %t4932, label %if.then.4929, label %if.end.4931
if.then.4929:
    %t4933 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.311, i64 0, i64 0
    %t4934 = ptrtoint i8* %t4933 to i64
    %t4935 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.312, i64 0, i64 0
    %t4936 = ptrtoint i8* %t4935 to i64
    %t4937 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4934, i64 %t4936)
    ret i64 %t4937
    br label %if.end.4931
if.end.4931:
    %t4938 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.313, i64 0, i64 0
    %t4939 = ptrtoint i8* %t4938 to i64
    %t4940 = load i64, i64* %path
    %t4941 = call i64 @freak_llvm_word_concat(i64 %t4939, i64 %t4940)
    %t4942 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.314, i64 0, i64 0
    %t4943 = ptrtoint i8* %t4942 to i64
    %t4944 = call i64 @freak_llvm_word_concat(i64 %t4941, i64 %t4943)
    %t4945 = load i64, i64* %host
    %t4946 = call i64 @freak_llvm_word_concat(i64 %t4944, i64 %t4945)
    %t4947 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.315, i64 0, i64 0
    %t4948 = ptrtoint i8* %t4947 to i64
    %t4949 = call i64 @freak_llvm_word_concat(i64 %t4946, i64 %t4948)
    %req_v4950 = alloca i64
    store i64 %t4949, i64* %req_v4950
    %t4951 = load i64, i64* %fd_v4925
    %t4952 = load i64, i64* %req_v4950
    %t4953 = call i64 @freak_llvm_tcp_send(i64 %t4951, i64 %t4952)
    %t4954 = load i64, i64* %fd_v4925
    %t4955 = call i64 @freak_llvm_tcp_recv_all(i64 %t4954, i64 65536)
    %raw_v4956 = alloca i64
    store i64 %t4955, i64* %raw_v4956
    %t4957 = load i64, i64* %fd_v4925
    call void @freak_llvm_tcp_close(i64 %t4957)
    %t4958 = load i64, i64* %raw_v4956
    %t4959 = call i64 @freak_http_split_response(i64 %t4958)
    ret i64 %t4959
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
    %t4960 = load i64, i64* %host
    %t4961 = load i64, i64* %port
    %t4962 = call i64 @freak_llvm_tcp_connect(i64 %t4960, i64 %t4961)
    %fd_v4963 = alloca i64
    store i64 %t4962, i64* %fd_v4963
    %t4964 = load i64, i64* %fd_v4963
    %t4966 = icmp slt i64 %t4964, 0
    %t4965 = zext i1 %t4966 to i64
    %t4970 = icmp ne i64 %t4965, 0
    br i1 %t4970, label %if.then.4967, label %if.end.4969
if.then.4967:
    %t4971 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.316, i64 0, i64 0
    %t4972 = ptrtoint i8* %t4971 to i64
    %t4973 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.317, i64 0, i64 0
    %t4974 = ptrtoint i8* %t4973 to i64
    %t4975 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4972, i64 %t4974)
    ret i64 %t4975
    br label %if.end.4969
if.end.4969:
    %t4976 = load i64, i64* %body
    %t4977 = call i64 @freak_llvm_word_length(i64 %t4976)
    %t4978 = call i64 @freak_llvm_word_from_int(i64 %t4977)
    %body_len_v4979 = alloca i64
    store i64 %t4978, i64* %body_len_v4979
    %t4980 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.318, i64 0, i64 0
    %t4981 = ptrtoint i8* %t4980 to i64
    %t4982 = load i64, i64* %path
    %t4983 = call i64 @freak_llvm_word_concat(i64 %t4981, i64 %t4982)
    %t4984 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.319, i64 0, i64 0
    %t4985 = ptrtoint i8* %t4984 to i64
    %t4986 = call i64 @freak_llvm_word_concat(i64 %t4983, i64 %t4985)
    %t4987 = load i64, i64* %host
    %t4988 = call i64 @freak_llvm_word_concat(i64 %t4986, i64 %t4987)
    %t4989 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.320, i64 0, i64 0
    %t4990 = ptrtoint i8* %t4989 to i64
    %t4991 = call i64 @freak_llvm_word_concat(i64 %t4988, i64 %t4990)
    %t4992 = load i64, i64* %content_type
    %t4993 = call i64 @freak_llvm_word_concat(i64 %t4991, i64 %t4992)
    %t4994 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.321, i64 0, i64 0
    %t4995 = ptrtoint i8* %t4994 to i64
    %t4996 = call i64 @freak_llvm_word_concat(i64 %t4993, i64 %t4995)
    %t4997 = load i64, i64* %body_len_v4979
    %t4998 = call i64 @freak_llvm_word_concat(i64 %t4996, i64 %t4997)
    %t4999 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.322, i64 0, i64 0
    %t5000 = ptrtoint i8* %t4999 to i64
    %t5001 = call i64 @freak_llvm_word_concat(i64 %t4998, i64 %t5000)
    %t5002 = load i64, i64* %body
    %t5003 = call i64 @freak_llvm_word_concat(i64 %t5001, i64 %t5002)
    %req_v5004 = alloca i64
    store i64 %t5003, i64* %req_v5004
    %t5005 = load i64, i64* %fd_v4963
    %t5006 = load i64, i64* %req_v5004
    %t5007 = call i64 @freak_llvm_tcp_send(i64 %t5005, i64 %t5006)
    %t5008 = load i64, i64* %fd_v4963
    %t5009 = call i64 @freak_llvm_tcp_recv_all(i64 %t5008, i64 65536)
    %raw_v5010 = alloca i64
    store i64 %t5009, i64* %raw_v5010
    %t5011 = load i64, i64* %fd_v4963
    call void @freak_llvm_tcp_close(i64 %t5011)
    %t5012 = load i64, i64* %raw_v5010
    %t5013 = call i64 @freak_http_split_response(i64 %t5012)
    ret i64 %t5013
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
    %t5014 = load i64, i64* %host
    %t5015 = load i64, i64* %port
    %t5016 = call i64 @freak_llvm_tcp_connect(i64 %t5014, i64 %t5015)
    %fd_v5017 = alloca i64
    store i64 %t5016, i64* %fd_v5017
    %t5018 = load i64, i64* %fd_v5017
    %t5020 = icmp slt i64 %t5018, 0
    %t5019 = zext i1 %t5020 to i64
    %t5024 = icmp ne i64 %t5019, 0
    br i1 %t5024, label %if.then.5021, label %if.end.5023
if.then.5021:
    %t5025 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.323, i64 0, i64 0
    %t5026 = ptrtoint i8* %t5025 to i64
    %t5027 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.324, i64 0, i64 0
    %t5028 = ptrtoint i8* %t5027 to i64
    %t5029 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5026, i64 %t5028)
    ret i64 %t5029
    br label %if.end.5023
if.end.5023:
    %t5030 = load i64, i64* %body
    %t5031 = call i64 @freak_llvm_word_length(i64 %t5030)
    %t5032 = call i64 @freak_llvm_word_from_int(i64 %t5031)
    %body_len_v5033 = alloca i64
    store i64 %t5032, i64* %body_len_v5033
    %t5034 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.325, i64 0, i64 0
    %t5035 = ptrtoint i8* %t5034 to i64
    %t5036 = load i64, i64* %path
    %t5037 = call i64 @freak_llvm_word_concat(i64 %t5035, i64 %t5036)
    %t5038 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.326, i64 0, i64 0
    %t5039 = ptrtoint i8* %t5038 to i64
    %t5040 = call i64 @freak_llvm_word_concat(i64 %t5037, i64 %t5039)
    %t5041 = load i64, i64* %host
    %t5042 = call i64 @freak_llvm_word_concat(i64 %t5040, i64 %t5041)
    %t5043 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.327, i64 0, i64 0
    %t5044 = ptrtoint i8* %t5043 to i64
    %t5045 = call i64 @freak_llvm_word_concat(i64 %t5042, i64 %t5044)
    %t5046 = load i64, i64* %content_type
    %t5047 = call i64 @freak_llvm_word_concat(i64 %t5045, i64 %t5046)
    %t5048 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.328, i64 0, i64 0
    %t5049 = ptrtoint i8* %t5048 to i64
    %t5050 = call i64 @freak_llvm_word_concat(i64 %t5047, i64 %t5049)
    %t5051 = load i64, i64* %body_len_v5033
    %t5052 = call i64 @freak_llvm_word_concat(i64 %t5050, i64 %t5051)
    %t5053 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.329, i64 0, i64 0
    %t5054 = ptrtoint i8* %t5053 to i64
    %t5055 = call i64 @freak_llvm_word_concat(i64 %t5052, i64 %t5054)
    %t5056 = load i64, i64* %body
    %t5057 = call i64 @freak_llvm_word_concat(i64 %t5055, i64 %t5056)
    %req_v5058 = alloca i64
    store i64 %t5057, i64* %req_v5058
    %t5059 = load i64, i64* %fd_v5017
    %t5060 = load i64, i64* %req_v5058
    %t5061 = call i64 @freak_llvm_tcp_send(i64 %t5059, i64 %t5060)
    %t5062 = load i64, i64* %fd_v5017
    %t5063 = call i64 @freak_llvm_tcp_recv_all(i64 %t5062, i64 65536)
    %raw_v5064 = alloca i64
    store i64 %t5063, i64* %raw_v5064
    %t5065 = load i64, i64* %fd_v5017
    call void @freak_llvm_tcp_close(i64 %t5065)
    %t5066 = load i64, i64* %raw_v5064
    %t5067 = call i64 @freak_http_split_response(i64 %t5066)
    ret i64 %t5067
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
    %t5068 = load i64, i64* %host
    %t5069 = load i64, i64* %port
    %t5070 = call i64 @freak_llvm_tcp_connect(i64 %t5068, i64 %t5069)
    %fd_v5071 = alloca i64
    store i64 %t5070, i64* %fd_v5071
    %t5072 = load i64, i64* %fd_v5071
    %t5074 = icmp slt i64 %t5072, 0
    %t5073 = zext i1 %t5074 to i64
    %t5078 = icmp ne i64 %t5073, 0
    br i1 %t5078, label %if.then.5075, label %if.end.5077
if.then.5075:
    %t5079 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.330, i64 0, i64 0
    %t5080 = ptrtoint i8* %t5079 to i64
    %t5081 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.331, i64 0, i64 0
    %t5082 = ptrtoint i8* %t5081 to i64
    %t5083 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5080, i64 %t5082)
    ret i64 %t5083
    br label %if.end.5077
if.end.5077:
    %t5084 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.332, i64 0, i64 0
    %t5085 = ptrtoint i8* %t5084 to i64
    %t5086 = load i64, i64* %path
    %t5087 = call i64 @freak_llvm_word_concat(i64 %t5085, i64 %t5086)
    %t5088 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.333, i64 0, i64 0
    %t5089 = ptrtoint i8* %t5088 to i64
    %t5090 = call i64 @freak_llvm_word_concat(i64 %t5087, i64 %t5089)
    %t5091 = load i64, i64* %host
    %t5092 = call i64 @freak_llvm_word_concat(i64 %t5090, i64 %t5091)
    %t5093 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.334, i64 0, i64 0
    %t5094 = ptrtoint i8* %t5093 to i64
    %t5095 = call i64 @freak_llvm_word_concat(i64 %t5092, i64 %t5094)
    %req_v5096 = alloca i64
    store i64 %t5095, i64* %req_v5096
    %t5097 = load i64, i64* %fd_v5071
    %t5098 = load i64, i64* %req_v5096
    %t5099 = call i64 @freak_llvm_tcp_send(i64 %t5097, i64 %t5098)
    %t5100 = load i64, i64* %fd_v5071
    %t5101 = call i64 @freak_llvm_tcp_recv_all(i64 %t5100, i64 65536)
    %raw_v5102 = alloca i64
    store i64 %t5101, i64* %raw_v5102
    %t5103 = load i64, i64* %fd_v5071
    call void @freak_llvm_tcp_close(i64 %t5103)
    %t5104 = load i64, i64* %raw_v5102
    %t5105 = call i64 @freak_http_split_response(i64 %t5104)
    ret i64 %t5105
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
    %t5106 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.335, i64 0, i64 0
    %t5107 = ptrtoint i8* %t5106 to i64
    store i64 %t5107, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    store i64 0, i64* @g_json_len
    store i64 0, i64* @g_http_resp_statuses
    store i64 0, i64* @g_http_resp_bodies
    store i64 0, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 0, i64* @g_http_inited
    %t5108 = getelementptr inbounds [14 x i8], [14 x i8]* @.str.336, i64 0, i64 0
    %t5109 = ptrtoint i8* %t5108 to i64
    store i64 %t5109, i64* @g_s
    %t5110 = load i64, i64* @g_s
    %t5111 = call i64 @freak_llvm_word_length(i64 %t5110)
    %t5112 = call i64 @freak_llvm_word_from_int(i64 %t5111)
    call void @freak_llvm_say(i64 %t5112)
    %t5113 = load i64, i64* @g_s
    %t5114 = call i64 @freak_llvm_word_char_at(i64 %t5113, i64 0)
    call void @freak_llvm_say(i64 %t5114)
    %t5115 = load i64, i64* @g_s
    %t5116 = call i64 @freak_llvm_word_char_at(i64 %t5115, i64 7)
    call void @freak_llvm_say(i64 %t5116)
    %t5117 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.337, i64 0, i64 0
    %t5118 = ptrtoint i8* %t5117 to i64
    store i64 %t5118, i64* @g_a
    %t5119 = getelementptr inbounds [4 x i8], [4 x i8]* @.str.338, i64 0, i64 0
    %t5120 = ptrtoint i8* %t5119 to i64
    store i64 %t5120, i64* @g_b
    %t5121 = load i64, i64* @g_a
    %t5122 = load i64, i64* @g_b
    %t5123 = call i64 @freak_llvm_word_concat(i64 %t5121, i64 %t5122)
    call void @freak_llvm_say(i64 %t5123)
    %t5124 = call i64 @freak_llvm_word_from_int(i64 2025)
    call void @freak_llvm_say(i64 %t5124)
    %t5125 = call i64 @freak_llvm_word_from_bool(i64 1)
    call void @freak_llvm_say(i64 %t5125)
    %t5126 = call i64 @freak_llvm_word_from_bool(i64 0)
    call void @freak_llvm_say(i64 %t5126)
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
@.str.336 = private unnamed_addr constant [14 x i8] c"Hello, FREAK!\00", align 1
@.str.337 = private unnamed_addr constant [5 x i8] c"Muv-\00", align 1
@.str.338 = private unnamed_addr constant [4 x i8] c"Luv\00", align 1

