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
@g_x = global i64 0
@g_day = global i64 0
@g_active = global i64 0

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
    %t94 = load i64, i64* @g_x
    %t96 = icmp slt i64 %t94, 0
    %t95 = zext i1 %t96 to i64
    %t100 = icmp ne i64 %t95, 0
    br i1 %t100, label %if.then.97, label %if.end.99
if.then.97:
    %t101 = load i64, i64* @g_x
    %t102 = sub i64 0, %t101
    ret i64 %t102
    br label %if.end.99
if.end.99:
    %t103 = load i64, i64* @g_x
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
    %t104 = load i64, i64* @g_x
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
    %t113 = load i64, i64* @g_x
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
    %t122 = load i64, i64* @g_x
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
    %b_v132 = alloca i64
    store i64 %t131, i64* %b_v132
    %t133 = load i64, i64* %exp
    %e_v134 = alloca i64
    store i64 %t133, i64* %e_v134
    br label %loop.cond.135
loop.cond.135:
    %t138 = load i64, i64* %e_v134
    %t140 = icmp sle i64 %t138, 0
    %t139 = zext i1 %t140 to i64
    %t141 = icmp eq i64 %t139, 0
    br i1 %t141, label %loop.body.136, label %loop.end.137
loop.body.136:
    %t142 = load i64, i64* %e_v134
    %t143 = sdiv i64 %t142, 2
    %half_v144 = alloca i64
    store i64 %t143, i64* %half_v144
    %t145 = load i64, i64* %half_v144
    %t146 = mul i64 %t145, 2
    %even_part_v147 = alloca i64
    store i64 %t146, i64* %even_part_v147
    %t148 = load i64, i64* %e_v134
    %t149 = load i64, i64* %even_part_v147
    %t150 = sub i64 %t148, %t149
    %odd_v151 = alloca i64
    store i64 %t150, i64* %odd_v151
    %t152 = load i64, i64* %odd_v151
    %t154 = icmp eq i64 %t152, 1
    %t153 = zext i1 %t154 to i64
    %t158 = icmp ne i64 %t153, 0
    br i1 %t158, label %if.then.155, label %if.end.157
if.then.155:
    %t159 = load i64, i64* %res_v130
    %t160 = load i64, i64* %b_v132
    %t161 = mul i64 %t159, %t160
    store i64 %t161, i64* %res_v130
    br label %if.end.157
if.end.157:
    %t162 = load i64, i64* %b_v132
    %t163 = load i64, i64* %b_v132
    %t164 = mul i64 %t162, %t163
    store i64 %t164, i64* %b_v132
    %t165 = load i64, i64* %e_v134
    %t166 = sdiv i64 %t165, 2
    store i64 %t166, i64* %e_v134
    br label %loop.cond.135
loop.end.137:
    %t167 = load i64, i64* %res_v130
    ret i64 %t167
    ret i64 0
}

define i64 @freak_std_max(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t168 = load i64, i64* %a
    %t169 = load i64, i64* %b
    %t171 = icmp sgt i64 %t168, %t169
    %t170 = zext i1 %t171 to i64
    %t175 = icmp ne i64 %t170, 0
    br i1 %t175, label %if.then.172, label %if.end.174
if.then.172:
    %t176 = load i64, i64* %a
    ret i64 %t176
    br label %if.end.174
if.end.174:
    %t177 = load i64, i64* %b
    ret i64 %t177
    ret i64 0
}

define i64 @freak_std_min(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t178 = load i64, i64* %a
    %t179 = load i64, i64* %b
    %t181 = icmp slt i64 %t178, %t179
    %t180 = zext i1 %t181 to i64
    %t185 = icmp ne i64 %t180, 0
    br i1 %t185, label %if.then.182, label %if.end.184
if.then.182:
    %t186 = load i64, i64* %a
    ret i64 %t186
    br label %if.end.184
if.end.184:
    %t187 = load i64, i64* %b
    ret i64 %t187
    ret i64 0
}

define i64 @freak_int_to_word(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t188 = load i64, i64* %n
    %t189 = call i64 @freak_llvm_word_from_int(i64 %t188)
    ret i64 %t189
    ret i64 0
}

define i64 @freak_std_sign(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t190 = load i64, i64* @g_x
    %t192 = icmp sgt i64 %t190, 0
    %t191 = zext i1 %t192 to i64
    %t196 = icmp ne i64 %t191, 0
    br i1 %t196, label %if.then.193, label %if.end.195
if.then.193:
    ret i64 1
    br label %if.end.195
if.end.195:
    %t197 = load i64, i64* @g_x
    %t199 = icmp slt i64 %t197, 0
    %t198 = zext i1 %t199 to i64
    %t203 = icmp ne i64 %t198, 0
    br i1 %t203, label %if.then.200, label %if.end.202
if.then.200:
    %t204 = sub i64 0, 1
    ret i64 %t204
    br label %if.end.202
if.end.202:
    ret i64 0
    ret i64 0
}

define i64 @freak_std_gcd(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t205 = load i64, i64* %a
    %t206 = call i64 @freak_std_abs(i64 %t205)
    store i64 %t206, i64* @g_x
    %t207 = load i64, i64* %b
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
    %t219 = load i64, i64* @g_x
    %t220 = load i64, i64* @g_x
    %t221 = load i64, i64* %y_v209
    %t222 = sdiv i64 %t220, %t221
    %t223 = load i64, i64* %y_v209
    %t224 = mul i64 %t222, %t223
    %t225 = sub i64 %t219, %t224
    %rem_v226 = alloca i64
    store i64 %t225, i64* %rem_v226
    %t227 = load i64, i64* %tmp_v218
    store i64 %t227, i64* @g_x
    %t228 = load i64, i64* %rem_v226
    store i64 %t228, i64* %y_v209
    br label %loop.cond.210
loop.end.212:
    %t229 = load i64, i64* @g_x
    ret i64 %t229
    ret i64 0
}

define i64 @freak_std_lcm(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t230 = load i64, i64* %a
    %t232 = icmp eq i64 %t230, 0
    %t231 = zext i1 %t232 to i64
    %t233 = load i64, i64* %b
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
    %t244 = load i64, i64* %a
    %t245 = load i64, i64* %b
    %t246 = call i64 @freak_std_gcd(i64 %t244, i64 %t245)
    %g_v247 = alloca i64
    store i64 %t246, i64* %g_v247
    %t248 = load i64, i64* %a
    %t249 = call i64 @freak_std_abs(i64 %t248)
    %aa_v250 = alloca i64
    store i64 %t249, i64* %aa_v250
    %t251 = load i64, i64* %b
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
    %a_v296 = alloca i64
    store i64 0, i64* %a_v296
    %b_v297 = alloca i64
    store i64 1, i64* %b_v297
    %i_v298 = alloca i64
    store i64 2, i64* %i_v298
    br label %loop.cond.299
loop.cond.299:
    %t302 = load i64, i64* %i_v298
    %t303 = load i64, i64* %n
    %t305 = icmp sgt i64 %t302, %t303
    %t304 = zext i1 %t305 to i64
    %t306 = icmp eq i64 %t304, 0
    br i1 %t306, label %loop.body.300, label %loop.end.301
loop.body.300:
    %t307 = load i64, i64* %a_v296
    %t308 = load i64, i64* %b_v297
    %t309 = add i64 %t307, %t308
    %tmp_v310 = alloca i64
    store i64 %t309, i64* %tmp_v310
    %t311 = load i64, i64* %b_v297
    store i64 %t311, i64* %a_v296
    %t312 = load i64, i64* %tmp_v310
    store i64 %t312, i64* %b_v297
    %t313 = load i64, i64* %i_v298
    %t314 = add i64 %t313, 1
    store i64 %t314, i64* %i_v298
    br label %loop.cond.299
loop.end.301:
    %t315 = load i64, i64* %b_v297
    ret i64 %t315
    ret i64 0
}

define i64 @freak_std_is_even(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t316 = load i64, i64* @g_x
    %t317 = sdiv i64 %t316, 2
    %half_v318 = alloca i64
    store i64 %t317, i64* %half_v318
    %t319 = load i64, i64* %half_v318
    %t320 = mul i64 %t319, 2
    %t321 = load i64, i64* @g_x
    %t323 = icmp eq i64 %t320, %t321
    %t322 = zext i1 %t323 to i64
    ret i64 %t322
    ret i64 0
}

define i64 @freak_std_is_odd(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t324 = load i64, i64* @g_x
    %t325 = call i64 @freak_std_is_even(i64 %t324)
    %t327 = icmp eq i64 %t325, 0
    %t326 = zext i1 %t327 to i64
    ret i64 %t326
    ret i64 0
}

define i64 @freak_string_repeat(i64 %arg_s, i64 %arg_count) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %count = alloca i64
    store i64 %arg_count, i64* %count
    %t328 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.7, i64 0, i64 0
    %t329 = ptrtoint i8* %t328 to i64
    %out_v330 = alloca i64
    store i64 %t329, i64* %out_v330
    %i_v331 = alloca i64
    store i64 0, i64* %i_v331
    %t337 = load i64, i64* %count
    %rep.336 = alloca i64
    store i64 0, i64* %rep.336
    br label %loop.cond.332
loop.cond.332:
    %t338 = load i64, i64* %rep.336
    %t339 = icmp slt i64 %t338, %t337
    br i1 %t339, label %loop.body.333, label %loop.end.334
loop.body.333:
    %t340 = load i64, i64* %out_v330
    %t341 = load i64, i64* %s
    %t342 = call i64 @freak_llvm_word_concat(i64 %t340, i64 %t341)
    store i64 %t342, i64* %out_v330
    %t343 = load i64, i64* %i_v331
    %t344 = add i64 %t343, 1
    store i64 %t344, i64* %i_v331
    br label %loop.inc.335
loop.inc.335:
    %t345 = load i64, i64* %rep.336
    %t346 = add i64 %t345, 1
    store i64 %t346, i64* %rep.336
    br label %loop.cond.332
loop.end.334:
    %t347 = load i64, i64* %out_v330
    ret i64 %t347
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
    %t348 = load i64, i64* %s
    %t349 = call i64 @freak_llvm_word_length(i64 %t348)
    %slen_v350 = alloca i64
    store i64 %t349, i64* %slen_v350
    %t351 = load i64, i64* %slen_v350
    %t352 = load i64, i64* %width
    %t354 = icmp sge i64 %t351, %t352
    %t353 = zext i1 %t354 to i64
    %t358 = icmp ne i64 %t353, 0
    br i1 %t358, label %if.then.355, label %if.end.357
if.then.355:
    %t359 = load i64, i64* %s
    ret i64 %t359
    br label %if.end.357
if.end.357:
    %t360 = load i64, i64* %width
    %t361 = load i64, i64* %slen_v350
    %t362 = sub i64 %t360, %t361
    %needed_v363 = alloca i64
    store i64 %t362, i64* %needed_v363
    %t364 = load i64, i64* %pad_char
    %t365 = load i64, i64* %needed_v363
    %t366 = call i64 @freak_string_repeat(i64 %t364, i64 %t365)
    %padding_v367 = alloca i64
    store i64 %t366, i64* %padding_v367
    %t368 = load i64, i64* %padding_v367
    %t369 = load i64, i64* %s
    %t370 = call i64 @freak_llvm_word_concat(i64 %t368, i64 %t369)
    ret i64 %t370
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
    %t371 = load i64, i64* %s
    %t372 = call i64 @freak_llvm_word_length(i64 %t371)
    %slen_v373 = alloca i64
    store i64 %t372, i64* %slen_v373
    %t374 = load i64, i64* %slen_v373
    %t375 = load i64, i64* %width
    %t377 = icmp sge i64 %t374, %t375
    %t376 = zext i1 %t377 to i64
    %t381 = icmp ne i64 %t376, 0
    br i1 %t381, label %if.then.378, label %if.end.380
if.then.378:
    %t382 = load i64, i64* %s
    ret i64 %t382
    br label %if.end.380
if.end.380:
    %t383 = load i64, i64* %width
    %t384 = load i64, i64* %slen_v373
    %t385 = sub i64 %t383, %t384
    %needed_v386 = alloca i64
    store i64 %t385, i64* %needed_v386
    %t387 = load i64, i64* %pad_char
    %t388 = load i64, i64* %needed_v386
    %t389 = call i64 @freak_string_repeat(i64 %t387, i64 %t388)
    %padding_v390 = alloca i64
    store i64 %t389, i64* %padding_v390
    %t391 = load i64, i64* %s
    %t392 = load i64, i64* %padding_v390
    %t393 = call i64 @freak_llvm_word_concat(i64 %t391, i64 %t392)
    ret i64 %t393
    ret i64 0
}

define i64 @freak_string_reverse(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t394 = load i64, i64* %s
    %t395 = call i64 @freak_llvm_word_length(i64 %t394)
    %slen_v396 = alloca i64
    store i64 %t395, i64* %slen_v396
    %t397 = load i64, i64* %slen_v396
    %t399 = icmp sle i64 %t397, 1
    %t398 = zext i1 %t399 to i64
    %t403 = icmp ne i64 %t398, 0
    br i1 %t403, label %if.then.400, label %if.end.402
if.then.400:
    %t404 = load i64, i64* %s
    ret i64 %t404
    br label %if.end.402
if.end.402:
    %t405 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.8, i64 0, i64 0
    %t406 = ptrtoint i8* %t405 to i64
    %out_v407 = alloca i64
    store i64 %t406, i64* %out_v407
    %t408 = load i64, i64* %slen_v396
    %t409 = sub i64 %t408, 1
    %i_v410 = alloca i64
    store i64 %t409, i64* %i_v410
    %t416 = load i64, i64* %slen_v396
    %rep.415 = alloca i64
    store i64 0, i64* %rep.415
    br label %loop.cond.411
loop.cond.411:
    %t417 = load i64, i64* %rep.415
    %t418 = icmp slt i64 %t417, %t416
    br i1 %t418, label %loop.body.412, label %loop.end.413
loop.body.412:
    %t419 = load i64, i64* %out_v407
    %t420 = load i64, i64* %s
    %t422 = load i64, i64* %i_v410
    %t421 = call i64 @freak_llvm_word_char_at(i64 %t420, i64 %t422)
    %t423 = call i64 @freak_llvm_word_concat(i64 %t419, i64 %t421)
    store i64 %t423, i64* %out_v407
    %t424 = load i64, i64* %i_v410
    %t425 = sub i64 %t424, 1
    store i64 %t425, i64* %i_v410
    br label %loop.inc.414
loop.inc.414:
    %t426 = load i64, i64* %rep.415
    %t427 = add i64 %t426, 1
    store i64 %t427, i64* %rep.415
    br label %loop.cond.411
loop.end.413:
    %t428 = load i64, i64* %out_v407
    ret i64 %t428
    ret i64 0
}

define i64 @freak_string_count(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t429 = load i64, i64* %haystack
    %t430 = call i64 @freak_llvm_word_length(i64 %t429)
    %hlen_v431 = alloca i64
    store i64 %t430, i64* %hlen_v431
    %t432 = load i64, i64* %needle
    %t433 = call i64 @freak_llvm_word_length(i64 %t432)
    %nlen_v434 = alloca i64
    store i64 %t433, i64* %nlen_v434
    %t435 = load i64, i64* %nlen_v434
    %t437 = icmp eq i64 %t435, 0
    %t436 = zext i1 %t437 to i64
    %t441 = icmp ne i64 %t436, 0
    br i1 %t441, label %if.then.438, label %if.end.440
if.then.438:
    ret i64 0
    br label %if.end.440
if.end.440:
    %t442 = load i64, i64* %nlen_v434
    %t443 = load i64, i64* %hlen_v431
    %t445 = icmp sgt i64 %t442, %t443
    %t444 = zext i1 %t445 to i64
    %t449 = icmp ne i64 %t444, 0
    br i1 %t449, label %if.then.446, label %if.end.448
if.then.446:
    ret i64 0
    br label %if.end.448
if.end.448:
    %count_v450 = alloca i64
    store i64 0, i64* %count_v450
    %i_v451 = alloca i64
    store i64 0, i64* %i_v451
    %t452 = load i64, i64* %hlen_v431
    %t453 = load i64, i64* %nlen_v434
    %t454 = sub i64 %t452, %t453
    %t455 = add i64 %t454, 1
    %limit_v456 = alloca i64
    store i64 %t455, i64* %limit_v456
    %t462 = load i64, i64* %limit_v456
    %rep.461 = alloca i64
    store i64 0, i64* %rep.461
    br label %loop.cond.457
loop.cond.457:
    %t463 = load i64, i64* %rep.461
    %t464 = icmp slt i64 %t463, %t462
    br i1 %t464, label %loop.body.458, label %loop.end.459
loop.body.458:
    %match_v465 = alloca i64
    store i64 1, i64* %match_v465
    %j_v466 = alloca i64
    store i64 0, i64* %j_v466
    %t472 = load i64, i64* %nlen_v434
    %rep.471 = alloca i64
    store i64 0, i64* %rep.471
    br label %loop.cond.467
loop.cond.467:
    %t473 = load i64, i64* %rep.471
    %t474 = icmp slt i64 %t473, %t472
    br i1 %t474, label %loop.body.468, label %loop.end.469
loop.body.468:
    %t475 = load i64, i64* %match_v465
    %t479 = icmp ne i64 %t475, 0
    br i1 %t479, label %if.then.476, label %if.end.478
if.then.476:
    %t480 = load i64, i64* %haystack
    %t482 = load i64, i64* %i_v451
    %t483 = load i64, i64* %j_v466
    %t484 = add i64 %t482, %t483
    %t481 = call i64 @freak_llvm_word_char_at(i64 %t480, i64 %t484)
    %t485 = load i64, i64* %needle
    %t487 = load i64, i64* %j_v466
    %t486 = call i64 @freak_llvm_word_char_at(i64 %t485, i64 %t487)
    %t488 = call i64 @freak_llvm_word_neq(i64 %t481, i64 %t486)
    %t492 = icmp ne i64 %t488, 0
    br i1 %t492, label %if.then.489, label %if.end.491
if.then.489:
    store i64 0, i64* %match_v465
    br label %if.end.491
if.end.491:
    br label %if.end.478
if.end.478:
    %t493 = load i64, i64* %j_v466
    %t494 = add i64 %t493, 1
    store i64 %t494, i64* %j_v466
    br label %loop.inc.470
loop.inc.470:
    %t495 = load i64, i64* %rep.471
    %t496 = add i64 %t495, 1
    store i64 %t496, i64* %rep.471
    br label %loop.cond.467
loop.end.469:
    %t497 = load i64, i64* %match_v465
    %t501 = icmp ne i64 %t497, 0
    br i1 %t501, label %if.then.498, label %if.end.500
if.then.498:
    %t502 = load i64, i64* %count_v450
    %t503 = add i64 %t502, 1
    store i64 %t503, i64* %count_v450
    br label %if.end.500
if.end.500:
    %t504 = load i64, i64* %i_v451
    %t505 = add i64 %t504, 1
    store i64 %t505, i64* %i_v451
    br label %loop.inc.460
loop.inc.460:
    %t506 = load i64, i64* %rep.461
    %t507 = add i64 %t506, 1
    store i64 %t507, i64* %rep.461
    br label %loop.cond.457
loop.end.459:
    %t508 = load i64, i64* %count_v450
    ret i64 %t508
    ret i64 0
}

define i64 @freak_string_split(i64 %arg_s, i64 %arg_delim) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %delim = alloca i64
    store i64 %arg_delim, i64* %delim
    %t509 = load i64, i64* %s
    %t510 = call i64 @freak_llvm_word_length(i64 %t509)
    %slen_v511 = alloca i64
    store i64 %t510, i64* %slen_v511
    %t512 = load i64, i64* %delim
    %t513 = call i64 @freak_llvm_word_length(i64 %t512)
    %dlen_v514 = alloca i64
    store i64 %t513, i64* %dlen_v514
    %t515 = load i64, i64* %dlen_v514
    %t517 = icmp eq i64 %t515, 0
    %t516 = zext i1 %t517 to i64
    %t521 = icmp ne i64 %t516, 0
    br i1 %t521, label %if.then.518, label %if.end.520
if.then.518:
    %t522 = load i64, i64* %s
    ret i64 %t522
    br label %if.end.520
if.end.520:
    %t523 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.9, i64 0, i64 0
    %t524 = ptrtoint i8* %t523 to i64
    %sp_out_v525 = alloca i64
    store i64 %t524, i64* %sp_out_v525
    %t526 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.10, i64 0, i64 0
    %t527 = ptrtoint i8* %t526 to i64
    %sp_cur_v528 = alloca i64
    store i64 %t527, i64* %sp_cur_v528
    %sp_i_v529 = alloca i64
    store i64 0, i64* %sp_i_v529
    %t535 = load i64, i64* %slen_v511
    %rep.534 = alloca i64
    store i64 0, i64* %rep.534
    br label %loop.cond.530
loop.cond.530:
    %t536 = load i64, i64* %rep.534
    %t537 = icmp slt i64 %t536, %t535
    br i1 %t537, label %loop.body.531, label %loop.end.532
loop.body.531:
    %sp_match_v538 = alloca i64
    store i64 1, i64* %sp_match_v538
    %t539 = load i64, i64* %sp_i_v529
    %t540 = load i64, i64* %dlen_v514
    %t541 = add i64 %t539, %t540
    %t542 = load i64, i64* %slen_v511
    %t544 = icmp sle i64 %t541, %t542
    %t543 = zext i1 %t544 to i64
    %t548 = icmp ne i64 %t543, 0
    br i1 %t548, label %if.then.545, label %if.else.546
if.then.545:
    %sp_j_v549 = alloca i64
    store i64 0, i64* %sp_j_v549
    %t555 = load i64, i64* %dlen_v514
    %rep.554 = alloca i64
    store i64 0, i64* %rep.554
    br label %loop.cond.550
loop.cond.550:
    %t556 = load i64, i64* %rep.554
    %t557 = icmp slt i64 %t556, %t555
    br i1 %t557, label %loop.body.551, label %loop.end.552
loop.body.551:
    %t558 = load i64, i64* %sp_match_v538
    %t562 = icmp ne i64 %t558, 0
    br i1 %t562, label %if.then.559, label %if.end.561
if.then.559:
    %t563 = load i64, i64* %s
    %t565 = load i64, i64* %sp_i_v529
    %t566 = load i64, i64* %sp_j_v549
    %t567 = add i64 %t565, %t566
    %t564 = call i64 @freak_llvm_word_char_at(i64 %t563, i64 %t567)
    %t568 = load i64, i64* %delim
    %t570 = load i64, i64* %sp_j_v549
    %t569 = call i64 @freak_llvm_word_char_at(i64 %t568, i64 %t570)
    %t571 = call i64 @freak_llvm_word_neq(i64 %t564, i64 %t569)
    %t575 = icmp ne i64 %t571, 0
    br i1 %t575, label %if.then.572, label %if.end.574
if.then.572:
    store i64 0, i64* %sp_match_v538
    br label %if.end.574
if.end.574:
    br label %if.end.561
if.end.561:
    %t576 = load i64, i64* %sp_j_v549
    %t577 = add i64 %t576, 1
    store i64 %t577, i64* %sp_j_v549
    br label %loop.inc.553
loop.inc.553:
    %t578 = load i64, i64* %rep.554
    %t579 = add i64 %t578, 1
    store i64 %t579, i64* %rep.554
    br label %loop.cond.550
loop.end.552:
    br label %if.end.547
if.else.546:
    store i64 0, i64* %sp_match_v538
    br label %if.end.547
if.end.547:
    %t580 = load i64, i64* %sp_match_v538
    %t584 = icmp ne i64 %t580, 0
    br i1 %t584, label %if.then.581, label %if.else.582
if.then.581:
    %t585 = load i64, i64* %sp_out_v525
    %t586 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.11, i64 0, i64 0
    %t587 = ptrtoint i8* %t586 to i64
    %t588 = call i64 @freak_llvm_word_eq(i64 %t585, i64 %t587)
    %t592 = icmp ne i64 %t588, 0
    br i1 %t592, label %if.then.589, label %if.else.590
if.then.589:
    %t593 = load i64, i64* %sp_cur_v528
    store i64 %t593, i64* %sp_out_v525
    br label %if.end.591
if.else.590:
    %t594 = load i64, i64* %sp_out_v525
    %t595 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.12, i64 0, i64 0
    %t596 = ptrtoint i8* %t595 to i64
    %t597 = call i64 @freak_llvm_word_concat(i64 %t594, i64 %t596)
    %t598 = load i64, i64* %sp_cur_v528
    %t599 = call i64 @freak_llvm_word_concat(i64 %t597, i64 %t598)
    store i64 %t599, i64* %sp_out_v525
    br label %if.end.591
if.end.591:
    %t600 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.13, i64 0, i64 0
    %t601 = ptrtoint i8* %t600 to i64
    store i64 %t601, i64* %sp_cur_v528
    %t602 = load i64, i64* %dlen_v514
    %t603 = load i64, i64* %sp_i_v529
    %t604 = add i64 %t603, %t602
    store i64 %t604, i64* %sp_i_v529
    br label %if.end.583
if.else.582:
    %t605 = load i64, i64* %sp_cur_v528
    %t606 = load i64, i64* %s
    %t608 = load i64, i64* %sp_i_v529
    %t607 = call i64 @freak_llvm_word_char_at(i64 %t606, i64 %t608)
    %t609 = call i64 @freak_llvm_word_concat(i64 %t605, i64 %t607)
    store i64 %t609, i64* %sp_cur_v528
    %t610 = load i64, i64* %sp_i_v529
    %t611 = add i64 %t610, 1
    store i64 %t611, i64* %sp_i_v529
    br label %if.end.583
if.end.583:
    br label %loop.inc.533
loop.inc.533:
    %t612 = load i64, i64* %rep.534
    %t613 = add i64 %t612, 1
    store i64 %t613, i64* %rep.534
    br label %loop.cond.530
loop.end.532:
    %t614 = load i64, i64* %sp_out_v525
    %t615 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.14, i64 0, i64 0
    %t616 = ptrtoint i8* %t615 to i64
    %t617 = call i64 @freak_llvm_word_eq(i64 %t614, i64 %t616)
    %t621 = icmp ne i64 %t617, 0
    br i1 %t621, label %if.then.618, label %if.else.619
if.then.618:
    %t622 = load i64, i64* %sp_cur_v528
    store i64 %t622, i64* %sp_out_v525
    br label %if.end.620
if.else.619:
    %t623 = load i64, i64* %sp_out_v525
    %t624 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.15, i64 0, i64 0
    %t625 = ptrtoint i8* %t624 to i64
    %t626 = call i64 @freak_llvm_word_concat(i64 %t623, i64 %t625)
    %t627 = load i64, i64* %sp_cur_v528
    %t628 = call i64 @freak_llvm_word_concat(i64 %t626, i64 %t627)
    store i64 %t628, i64* %sp_out_v525
    br label %if.end.620
if.end.620:
    %t629 = load i64, i64* %sp_out_v525
    ret i64 %t629
    ret i64 0
}

define i64 @freak_string_join(i64 %arg_parts, i64 %arg_separator) {
entry:
    %parts = alloca i64
    store i64 %arg_parts, i64* %parts
    %separator = alloca i64
    store i64 %arg_separator, i64* %separator
    %t630 = load i64, i64* %parts
    %t631 = call i64 @freak_llvm_word_length(i64 %t630)
    %plen_v632 = alloca i64
    store i64 %t631, i64* %plen_v632
    %t633 = load i64, i64* %plen_v632
    %t635 = icmp eq i64 %t633, 0
    %t634 = zext i1 %t635 to i64
    %t639 = icmp ne i64 %t634, 0
    br i1 %t639, label %if.then.636, label %if.end.638
if.then.636:
    %t640 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.16, i64 0, i64 0
    %t641 = ptrtoint i8* %t640 to i64
    ret i64 %t641
    br label %if.end.638
if.end.638:
    %t642 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.17, i64 0, i64 0
    %t643 = ptrtoint i8* %t642 to i64
    %jn_out_v644 = alloca i64
    store i64 %t643, i64* %jn_out_v644
    %t645 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.18, i64 0, i64 0
    %t646 = ptrtoint i8* %t645 to i64
    %jn_cur_v647 = alloca i64
    store i64 %t646, i64* %jn_cur_v647
    %jn_first_v648 = alloca i64
    store i64 1, i64* %jn_first_v648
    %jn_i_v649 = alloca i64
    store i64 0, i64* %jn_i_v649
    %t655 = load i64, i64* %plen_v632
    %rep.654 = alloca i64
    store i64 0, i64* %rep.654
    br label %loop.cond.650
loop.cond.650:
    %t656 = load i64, i64* %rep.654
    %t657 = icmp slt i64 %t656, %t655
    br i1 %t657, label %loop.body.651, label %loop.end.652
loop.body.651:
    %t658 = load i64, i64* %parts
    %t660 = load i64, i64* %jn_i_v649
    %t659 = call i64 @freak_llvm_word_char_at(i64 %t658, i64 %t660)
    %jn_c_v661 = alloca i64
    store i64 %t659, i64* %jn_c_v661
    %t662 = load i64, i64* %jn_c_v661
    %t663 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.19, i64 0, i64 0
    %t664 = ptrtoint i8* %t663 to i64
    %t665 = call i64 @freak_llvm_word_eq(i64 %t662, i64 %t664)
    %t669 = icmp ne i64 %t665, 0
    br i1 %t669, label %if.then.666, label %if.else.667
if.then.666:
    %t670 = load i64, i64* %jn_first_v648
    %t674 = icmp ne i64 %t670, 0
    br i1 %t674, label %if.then.671, label %if.else.672
if.then.671:
    %t675 = load i64, i64* %jn_cur_v647
    store i64 %t675, i64* %jn_out_v644
    store i64 0, i64* %jn_first_v648
    br label %if.end.673
if.else.672:
    %t676 = load i64, i64* %jn_out_v644
    %t677 = load i64, i64* %separator
    %t678 = call i64 @freak_llvm_word_concat(i64 %t676, i64 %t677)
    %t679 = load i64, i64* %jn_cur_v647
    %t680 = call i64 @freak_llvm_word_concat(i64 %t678, i64 %t679)
    store i64 %t680, i64* %jn_out_v644
    br label %if.end.673
if.end.673:
    %t681 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.20, i64 0, i64 0
    %t682 = ptrtoint i8* %t681 to i64
    store i64 %t682, i64* %jn_cur_v647
    br label %if.end.668
if.else.667:
    %t683 = load i64, i64* %jn_cur_v647
    %t684 = load i64, i64* %jn_c_v661
    %t685 = call i64 @freak_llvm_word_concat(i64 %t683, i64 %t684)
    store i64 %t685, i64* %jn_cur_v647
    br label %if.end.668
if.end.668:
    %t686 = load i64, i64* %jn_i_v649
    %t687 = add i64 %t686, 1
    store i64 %t687, i64* %jn_i_v649
    br label %loop.inc.653
loop.inc.653:
    %t688 = load i64, i64* %rep.654
    %t689 = add i64 %t688, 1
    store i64 %t689, i64* %rep.654
    br label %loop.cond.650
loop.end.652:
    %t690 = load i64, i64* %jn_first_v648
    %t694 = icmp ne i64 %t690, 0
    br i1 %t694, label %if.then.691, label %if.else.692
if.then.691:
    %t695 = load i64, i64* %jn_cur_v647
    store i64 %t695, i64* %jn_out_v644
    br label %if.end.693
if.else.692:
    %t696 = load i64, i64* %jn_out_v644
    %t697 = load i64, i64* %separator
    %t698 = call i64 @freak_llvm_word_concat(i64 %t696, i64 %t697)
    %t699 = load i64, i64* %jn_cur_v647
    %t700 = call i64 @freak_llvm_word_concat(i64 %t698, i64 %t699)
    store i64 %t700, i64* %jn_out_v644
    br label %if.end.693
if.end.693:
    %t701 = load i64, i64* %jn_out_v644
    ret i64 %t701
    ret i64 0
}

define i64 @freak_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t702 = load i64, i64* %c
    %t703 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.21, i64 0, i64 0
    %t704 = ptrtoint i8* %t703 to i64
    %t705 = call i64 @freak_llvm_word_eq(i64 %t702, i64 %t704)
    %t709 = icmp ne i64 %t705, 0
    br i1 %t709, label %if.then.706, label %if.end.708
if.then.706:
    ret i64 1
    br label %if.end.708
if.end.708:
    %t710 = load i64, i64* %c
    %t711 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.22, i64 0, i64 0
    %t712 = ptrtoint i8* %t711 to i64
    %t713 = call i64 @freak_llvm_word_eq(i64 %t710, i64 %t712)
    %t717 = icmp ne i64 %t713, 0
    br i1 %t717, label %if.then.714, label %if.end.716
if.then.714:
    ret i64 1
    br label %if.end.716
if.end.716:
    %t718 = load i64, i64* %c
    %t719 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.23, i64 0, i64 0
    %t720 = ptrtoint i8* %t719 to i64
    %t721 = call i64 @freak_llvm_word_eq(i64 %t718, i64 %t720)
    %t725 = icmp ne i64 %t721, 0
    br i1 %t725, label %if.then.722, label %if.end.724
if.then.722:
    ret i64 1
    br label %if.end.724
if.end.724:
    %t726 = load i64, i64* %c
    %t727 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.24, i64 0, i64 0
    %t728 = ptrtoint i8* %t727 to i64
    %t729 = call i64 @freak_llvm_word_eq(i64 %t726, i64 %t728)
    %t733 = icmp ne i64 %t729, 0
    br i1 %t733, label %if.then.730, label %if.end.732
if.then.730:
    ret i64 1
    br label %if.end.732
if.end.732:
    %t734 = load i64, i64* %c
    %t735 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.25, i64 0, i64 0
    %t736 = ptrtoint i8* %t735 to i64
    %t737 = call i64 @freak_llvm_word_eq(i64 %t734, i64 %t736)
    %t741 = icmp ne i64 %t737, 0
    br i1 %t741, label %if.then.738, label %if.end.740
if.then.738:
    ret i64 1
    br label %if.end.740
if.end.740:
    %t742 = load i64, i64* %c
    %t743 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.26, i64 0, i64 0
    %t744 = ptrtoint i8* %t743 to i64
    %t745 = call i64 @freak_llvm_word_eq(i64 %t742, i64 %t744)
    %t749 = icmp ne i64 %t745, 0
    br i1 %t749, label %if.then.746, label %if.end.748
if.then.746:
    ret i64 1
    br label %if.end.748
if.end.748:
    %t750 = load i64, i64* %c
    %t751 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.27, i64 0, i64 0
    %t752 = ptrtoint i8* %t751 to i64
    %t753 = call i64 @freak_llvm_word_eq(i64 %t750, i64 %t752)
    %t757 = icmp ne i64 %t753, 0
    br i1 %t757, label %if.then.754, label %if.end.756
if.then.754:
    ret i64 1
    br label %if.end.756
if.end.756:
    %t758 = load i64, i64* %c
    %t759 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.28, i64 0, i64 0
    %t760 = ptrtoint i8* %t759 to i64
    %t761 = call i64 @freak_llvm_word_eq(i64 %t758, i64 %t760)
    %t765 = icmp ne i64 %t761, 0
    br i1 %t765, label %if.then.762, label %if.end.764
if.then.762:
    ret i64 1
    br label %if.end.764
if.end.764:
    %t766 = load i64, i64* %c
    %t767 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.29, i64 0, i64 0
    %t768 = ptrtoint i8* %t767 to i64
    %t769 = call i64 @freak_llvm_word_eq(i64 %t766, i64 %t768)
    %t773 = icmp ne i64 %t769, 0
    br i1 %t773, label %if.then.770, label %if.end.772
if.then.770:
    ret i64 1
    br label %if.end.772
if.end.772:
    %t774 = load i64, i64* %c
    %t775 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.30, i64 0, i64 0
    %t776 = ptrtoint i8* %t775 to i64
    %t777 = call i64 @freak_llvm_word_eq(i64 %t774, i64 %t776)
    %t781 = icmp ne i64 %t777, 0
    br i1 %t781, label %if.then.778, label %if.end.780
if.then.778:
    ret i64 1
    br label %if.end.780
if.end.780:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_alpha(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t782 = load i64, i64* %c
    %t783 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.31, i64 0, i64 0
    %t784 = ptrtoint i8* %t783 to i64
    %t785 = call i64 @freak_llvm_word_eq(i64 %t782, i64 %t784)
    %t786 = load i64, i64* %c
    %t787 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.32, i64 0, i64 0
    %t788 = ptrtoint i8* %t787 to i64
    %t789 = call i64 @freak_llvm_word_eq(i64 %t786, i64 %t788)
    %t791 = icmp ne i64 %t785, 0
    %t792 = icmp ne i64 %t789, 0
    %t793 = or i1 %t791, %t792
    %t790 = zext i1 %t793 to i64
    %t794 = load i64, i64* %c
    %t795 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.33, i64 0, i64 0
    %t796 = ptrtoint i8* %t795 to i64
    %t797 = call i64 @freak_llvm_word_eq(i64 %t794, i64 %t796)
    %t799 = icmp ne i64 %t790, 0
    %t800 = icmp ne i64 %t797, 0
    %t801 = or i1 %t799, %t800
    %t798 = zext i1 %t801 to i64
    %t802 = load i64, i64* %c
    %t803 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.34, i64 0, i64 0
    %t804 = ptrtoint i8* %t803 to i64
    %t805 = call i64 @freak_llvm_word_eq(i64 %t802, i64 %t804)
    %t807 = icmp ne i64 %t798, 0
    %t808 = icmp ne i64 %t805, 0
    %t809 = or i1 %t807, %t808
    %t806 = zext i1 %t809 to i64
    %t810 = load i64, i64* %c
    %t811 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.35, i64 0, i64 0
    %t812 = ptrtoint i8* %t811 to i64
    %t813 = call i64 @freak_llvm_word_eq(i64 %t810, i64 %t812)
    %t815 = icmp ne i64 %t806, 0
    %t816 = icmp ne i64 %t813, 0
    %t817 = or i1 %t815, %t816
    %t814 = zext i1 %t817 to i64
    %t821 = icmp ne i64 %t814, 0
    br i1 %t821, label %if.then.818, label %if.end.820
if.then.818:
    ret i64 1
    br label %if.end.820
if.end.820:
    %t822 = load i64, i64* %c
    %t823 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.36, i64 0, i64 0
    %t824 = ptrtoint i8* %t823 to i64
    %t825 = call i64 @freak_llvm_word_eq(i64 %t822, i64 %t824)
    %t826 = load i64, i64* %c
    %t827 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.37, i64 0, i64 0
    %t828 = ptrtoint i8* %t827 to i64
    %t829 = call i64 @freak_llvm_word_eq(i64 %t826, i64 %t828)
    %t831 = icmp ne i64 %t825, 0
    %t832 = icmp ne i64 %t829, 0
    %t833 = or i1 %t831, %t832
    %t830 = zext i1 %t833 to i64
    %t834 = load i64, i64* %c
    %t835 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.38, i64 0, i64 0
    %t836 = ptrtoint i8* %t835 to i64
    %t837 = call i64 @freak_llvm_word_eq(i64 %t834, i64 %t836)
    %t839 = icmp ne i64 %t830, 0
    %t840 = icmp ne i64 %t837, 0
    %t841 = or i1 %t839, %t840
    %t838 = zext i1 %t841 to i64
    %t842 = load i64, i64* %c
    %t843 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.39, i64 0, i64 0
    %t844 = ptrtoint i8* %t843 to i64
    %t845 = call i64 @freak_llvm_word_eq(i64 %t842, i64 %t844)
    %t847 = icmp ne i64 %t838, 0
    %t848 = icmp ne i64 %t845, 0
    %t849 = or i1 %t847, %t848
    %t846 = zext i1 %t849 to i64
    %t850 = load i64, i64* %c
    %t851 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.40, i64 0, i64 0
    %t852 = ptrtoint i8* %t851 to i64
    %t853 = call i64 @freak_llvm_word_eq(i64 %t850, i64 %t852)
    %t855 = icmp ne i64 %t846, 0
    %t856 = icmp ne i64 %t853, 0
    %t857 = or i1 %t855, %t856
    %t854 = zext i1 %t857 to i64
    %t861 = icmp ne i64 %t854, 0
    br i1 %t861, label %if.then.858, label %if.end.860
if.then.858:
    ret i64 1
    br label %if.end.860
if.end.860:
    %t862 = load i64, i64* %c
    %t863 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.41, i64 0, i64 0
    %t864 = ptrtoint i8* %t863 to i64
    %t865 = call i64 @freak_llvm_word_eq(i64 %t862, i64 %t864)
    %t866 = load i64, i64* %c
    %t867 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.42, i64 0, i64 0
    %t868 = ptrtoint i8* %t867 to i64
    %t869 = call i64 @freak_llvm_word_eq(i64 %t866, i64 %t868)
    %t871 = icmp ne i64 %t865, 0
    %t872 = icmp ne i64 %t869, 0
    %t873 = or i1 %t871, %t872
    %t870 = zext i1 %t873 to i64
    %t874 = load i64, i64* %c
    %t875 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.43, i64 0, i64 0
    %t876 = ptrtoint i8* %t875 to i64
    %t877 = call i64 @freak_llvm_word_eq(i64 %t874, i64 %t876)
    %t879 = icmp ne i64 %t870, 0
    %t880 = icmp ne i64 %t877, 0
    %t881 = or i1 %t879, %t880
    %t878 = zext i1 %t881 to i64
    %t882 = load i64, i64* %c
    %t883 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.44, i64 0, i64 0
    %t884 = ptrtoint i8* %t883 to i64
    %t885 = call i64 @freak_llvm_word_eq(i64 %t882, i64 %t884)
    %t887 = icmp ne i64 %t878, 0
    %t888 = icmp ne i64 %t885, 0
    %t889 = or i1 %t887, %t888
    %t886 = zext i1 %t889 to i64
    %t890 = load i64, i64* %c
    %t891 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.45, i64 0, i64 0
    %t892 = ptrtoint i8* %t891 to i64
    %t893 = call i64 @freak_llvm_word_eq(i64 %t890, i64 %t892)
    %t895 = icmp ne i64 %t886, 0
    %t896 = icmp ne i64 %t893, 0
    %t897 = or i1 %t895, %t896
    %t894 = zext i1 %t897 to i64
    %t901 = icmp ne i64 %t894, 0
    br i1 %t901, label %if.then.898, label %if.end.900
if.then.898:
    ret i64 1
    br label %if.end.900
if.end.900:
    %t902 = load i64, i64* %c
    %t903 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.46, i64 0, i64 0
    %t904 = ptrtoint i8* %t903 to i64
    %t905 = call i64 @freak_llvm_word_eq(i64 %t902, i64 %t904)
    %t906 = load i64, i64* %c
    %t907 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.47, i64 0, i64 0
    %t908 = ptrtoint i8* %t907 to i64
    %t909 = call i64 @freak_llvm_word_eq(i64 %t906, i64 %t908)
    %t911 = icmp ne i64 %t905, 0
    %t912 = icmp ne i64 %t909, 0
    %t913 = or i1 %t911, %t912
    %t910 = zext i1 %t913 to i64
    %t914 = load i64, i64* %c
    %t915 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.48, i64 0, i64 0
    %t916 = ptrtoint i8* %t915 to i64
    %t917 = call i64 @freak_llvm_word_eq(i64 %t914, i64 %t916)
    %t919 = icmp ne i64 %t910, 0
    %t920 = icmp ne i64 %t917, 0
    %t921 = or i1 %t919, %t920
    %t918 = zext i1 %t921 to i64
    %t922 = load i64, i64* %c
    %t923 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.49, i64 0, i64 0
    %t924 = ptrtoint i8* %t923 to i64
    %t925 = call i64 @freak_llvm_word_eq(i64 %t922, i64 %t924)
    %t927 = icmp ne i64 %t918, 0
    %t928 = icmp ne i64 %t925, 0
    %t929 = or i1 %t927, %t928
    %t926 = zext i1 %t929 to i64
    %t930 = load i64, i64* %c
    %t931 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.50, i64 0, i64 0
    %t932 = ptrtoint i8* %t931 to i64
    %t933 = call i64 @freak_llvm_word_eq(i64 %t930, i64 %t932)
    %t935 = icmp ne i64 %t926, 0
    %t936 = icmp ne i64 %t933, 0
    %t937 = or i1 %t935, %t936
    %t934 = zext i1 %t937 to i64
    %t941 = icmp ne i64 %t934, 0
    br i1 %t941, label %if.then.938, label %if.end.940
if.then.938:
    ret i64 1
    br label %if.end.940
if.end.940:
    %t942 = load i64, i64* %c
    %t943 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.51, i64 0, i64 0
    %t944 = ptrtoint i8* %t943 to i64
    %t945 = call i64 @freak_llvm_word_eq(i64 %t942, i64 %t944)
    %t946 = load i64, i64* %c
    %t947 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.52, i64 0, i64 0
    %t948 = ptrtoint i8* %t947 to i64
    %t949 = call i64 @freak_llvm_word_eq(i64 %t946, i64 %t948)
    %t951 = icmp ne i64 %t945, 0
    %t952 = icmp ne i64 %t949, 0
    %t953 = or i1 %t951, %t952
    %t950 = zext i1 %t953 to i64
    %t954 = load i64, i64* %c
    %t955 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.53, i64 0, i64 0
    %t956 = ptrtoint i8* %t955 to i64
    %t957 = call i64 @freak_llvm_word_eq(i64 %t954, i64 %t956)
    %t959 = icmp ne i64 %t950, 0
    %t960 = icmp ne i64 %t957, 0
    %t961 = or i1 %t959, %t960
    %t958 = zext i1 %t961 to i64
    %t962 = load i64, i64* %c
    %t963 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.54, i64 0, i64 0
    %t964 = ptrtoint i8* %t963 to i64
    %t965 = call i64 @freak_llvm_word_eq(i64 %t962, i64 %t964)
    %t967 = icmp ne i64 %t958, 0
    %t968 = icmp ne i64 %t965, 0
    %t969 = or i1 %t967, %t968
    %t966 = zext i1 %t969 to i64
    %t970 = load i64, i64* %c
    %t971 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.55, i64 0, i64 0
    %t972 = ptrtoint i8* %t971 to i64
    %t973 = call i64 @freak_llvm_word_eq(i64 %t970, i64 %t972)
    %t975 = icmp ne i64 %t966, 0
    %t976 = icmp ne i64 %t973, 0
    %t977 = or i1 %t975, %t976
    %t974 = zext i1 %t977 to i64
    %t978 = load i64, i64* %c
    %t979 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.56, i64 0, i64 0
    %t980 = ptrtoint i8* %t979 to i64
    %t981 = call i64 @freak_llvm_word_eq(i64 %t978, i64 %t980)
    %t983 = icmp ne i64 %t974, 0
    %t984 = icmp ne i64 %t981, 0
    %t985 = or i1 %t983, %t984
    %t982 = zext i1 %t985 to i64
    %t989 = icmp ne i64 %t982, 0
    br i1 %t989, label %if.then.986, label %if.end.988
if.then.986:
    ret i64 1
    br label %if.end.988
if.end.988:
    %t990 = load i64, i64* %c
    %t991 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.57, i64 0, i64 0
    %t992 = ptrtoint i8* %t991 to i64
    %t993 = call i64 @freak_llvm_word_eq(i64 %t990, i64 %t992)
    %t994 = load i64, i64* %c
    %t995 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.58, i64 0, i64 0
    %t996 = ptrtoint i8* %t995 to i64
    %t997 = call i64 @freak_llvm_word_eq(i64 %t994, i64 %t996)
    %t999 = icmp ne i64 %t993, 0
    %t1000 = icmp ne i64 %t997, 0
    %t1001 = or i1 %t999, %t1000
    %t998 = zext i1 %t1001 to i64
    %t1002 = load i64, i64* %c
    %t1003 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.59, i64 0, i64 0
    %t1004 = ptrtoint i8* %t1003 to i64
    %t1005 = call i64 @freak_llvm_word_eq(i64 %t1002, i64 %t1004)
    %t1007 = icmp ne i64 %t998, 0
    %t1008 = icmp ne i64 %t1005, 0
    %t1009 = or i1 %t1007, %t1008
    %t1006 = zext i1 %t1009 to i64
    %t1010 = load i64, i64* %c
    %t1011 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.60, i64 0, i64 0
    %t1012 = ptrtoint i8* %t1011 to i64
    %t1013 = call i64 @freak_llvm_word_eq(i64 %t1010, i64 %t1012)
    %t1015 = icmp ne i64 %t1006, 0
    %t1016 = icmp ne i64 %t1013, 0
    %t1017 = or i1 %t1015, %t1016
    %t1014 = zext i1 %t1017 to i64
    %t1018 = load i64, i64* %c
    %t1019 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.61, i64 0, i64 0
    %t1020 = ptrtoint i8* %t1019 to i64
    %t1021 = call i64 @freak_llvm_word_eq(i64 %t1018, i64 %t1020)
    %t1023 = icmp ne i64 %t1014, 0
    %t1024 = icmp ne i64 %t1021, 0
    %t1025 = or i1 %t1023, %t1024
    %t1022 = zext i1 %t1025 to i64
    %t1029 = icmp ne i64 %t1022, 0
    br i1 %t1029, label %if.then.1026, label %if.end.1028
if.then.1026:
    ret i64 1
    br label %if.end.1028
if.end.1028:
    %t1030 = load i64, i64* %c
    %t1031 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.62, i64 0, i64 0
    %t1032 = ptrtoint i8* %t1031 to i64
    %t1033 = call i64 @freak_llvm_word_eq(i64 %t1030, i64 %t1032)
    %t1034 = load i64, i64* %c
    %t1035 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.63, i64 0, i64 0
    %t1036 = ptrtoint i8* %t1035 to i64
    %t1037 = call i64 @freak_llvm_word_eq(i64 %t1034, i64 %t1036)
    %t1039 = icmp ne i64 %t1033, 0
    %t1040 = icmp ne i64 %t1037, 0
    %t1041 = or i1 %t1039, %t1040
    %t1038 = zext i1 %t1041 to i64
    %t1042 = load i64, i64* %c
    %t1043 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.64, i64 0, i64 0
    %t1044 = ptrtoint i8* %t1043 to i64
    %t1045 = call i64 @freak_llvm_word_eq(i64 %t1042, i64 %t1044)
    %t1047 = icmp ne i64 %t1038, 0
    %t1048 = icmp ne i64 %t1045, 0
    %t1049 = or i1 %t1047, %t1048
    %t1046 = zext i1 %t1049 to i64
    %t1050 = load i64, i64* %c
    %t1051 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.65, i64 0, i64 0
    %t1052 = ptrtoint i8* %t1051 to i64
    %t1053 = call i64 @freak_llvm_word_eq(i64 %t1050, i64 %t1052)
    %t1055 = icmp ne i64 %t1046, 0
    %t1056 = icmp ne i64 %t1053, 0
    %t1057 = or i1 %t1055, %t1056
    %t1054 = zext i1 %t1057 to i64
    %t1058 = load i64, i64* %c
    %t1059 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.66, i64 0, i64 0
    %t1060 = ptrtoint i8* %t1059 to i64
    %t1061 = call i64 @freak_llvm_word_eq(i64 %t1058, i64 %t1060)
    %t1063 = icmp ne i64 %t1054, 0
    %t1064 = icmp ne i64 %t1061, 0
    %t1065 = or i1 %t1063, %t1064
    %t1062 = zext i1 %t1065 to i64
    %t1069 = icmp ne i64 %t1062, 0
    br i1 %t1069, label %if.then.1066, label %if.end.1068
if.then.1066:
    ret i64 1
    br label %if.end.1068
if.end.1068:
    %t1070 = load i64, i64* %c
    %t1071 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.67, i64 0, i64 0
    %t1072 = ptrtoint i8* %t1071 to i64
    %t1073 = call i64 @freak_llvm_word_eq(i64 %t1070, i64 %t1072)
    %t1074 = load i64, i64* %c
    %t1075 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.68, i64 0, i64 0
    %t1076 = ptrtoint i8* %t1075 to i64
    %t1077 = call i64 @freak_llvm_word_eq(i64 %t1074, i64 %t1076)
    %t1079 = icmp ne i64 %t1073, 0
    %t1080 = icmp ne i64 %t1077, 0
    %t1081 = or i1 %t1079, %t1080
    %t1078 = zext i1 %t1081 to i64
    %t1082 = load i64, i64* %c
    %t1083 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.69, i64 0, i64 0
    %t1084 = ptrtoint i8* %t1083 to i64
    %t1085 = call i64 @freak_llvm_word_eq(i64 %t1082, i64 %t1084)
    %t1087 = icmp ne i64 %t1078, 0
    %t1088 = icmp ne i64 %t1085, 0
    %t1089 = or i1 %t1087, %t1088
    %t1086 = zext i1 %t1089 to i64
    %t1090 = load i64, i64* %c
    %t1091 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.70, i64 0, i64 0
    %t1092 = ptrtoint i8* %t1091 to i64
    %t1093 = call i64 @freak_llvm_word_eq(i64 %t1090, i64 %t1092)
    %t1095 = icmp ne i64 %t1086, 0
    %t1096 = icmp ne i64 %t1093, 0
    %t1097 = or i1 %t1095, %t1096
    %t1094 = zext i1 %t1097 to i64
    %t1098 = load i64, i64* %c
    %t1099 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.71, i64 0, i64 0
    %t1100 = ptrtoint i8* %t1099 to i64
    %t1101 = call i64 @freak_llvm_word_eq(i64 %t1098, i64 %t1100)
    %t1103 = icmp ne i64 %t1094, 0
    %t1104 = icmp ne i64 %t1101, 0
    %t1105 = or i1 %t1103, %t1104
    %t1102 = zext i1 %t1105 to i64
    %t1109 = icmp ne i64 %t1102, 0
    br i1 %t1109, label %if.then.1106, label %if.end.1108
if.then.1106:
    ret i64 1
    br label %if.end.1108
if.end.1108:
    %t1110 = load i64, i64* %c
    %t1111 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.72, i64 0, i64 0
    %t1112 = ptrtoint i8* %t1111 to i64
    %t1113 = call i64 @freak_llvm_word_eq(i64 %t1110, i64 %t1112)
    %t1114 = load i64, i64* %c
    %t1115 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.73, i64 0, i64 0
    %t1116 = ptrtoint i8* %t1115 to i64
    %t1117 = call i64 @freak_llvm_word_eq(i64 %t1114, i64 %t1116)
    %t1119 = icmp ne i64 %t1113, 0
    %t1120 = icmp ne i64 %t1117, 0
    %t1121 = or i1 %t1119, %t1120
    %t1118 = zext i1 %t1121 to i64
    %t1122 = load i64, i64* %c
    %t1123 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.74, i64 0, i64 0
    %t1124 = ptrtoint i8* %t1123 to i64
    %t1125 = call i64 @freak_llvm_word_eq(i64 %t1122, i64 %t1124)
    %t1127 = icmp ne i64 %t1118, 0
    %t1128 = icmp ne i64 %t1125, 0
    %t1129 = or i1 %t1127, %t1128
    %t1126 = zext i1 %t1129 to i64
    %t1130 = load i64, i64* %c
    %t1131 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.75, i64 0, i64 0
    %t1132 = ptrtoint i8* %t1131 to i64
    %t1133 = call i64 @freak_llvm_word_eq(i64 %t1130, i64 %t1132)
    %t1135 = icmp ne i64 %t1126, 0
    %t1136 = icmp ne i64 %t1133, 0
    %t1137 = or i1 %t1135, %t1136
    %t1134 = zext i1 %t1137 to i64
    %t1138 = load i64, i64* %c
    %t1139 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.76, i64 0, i64 0
    %t1140 = ptrtoint i8* %t1139 to i64
    %t1141 = call i64 @freak_llvm_word_eq(i64 %t1138, i64 %t1140)
    %t1143 = icmp ne i64 %t1134, 0
    %t1144 = icmp ne i64 %t1141, 0
    %t1145 = or i1 %t1143, %t1144
    %t1142 = zext i1 %t1145 to i64
    %t1149 = icmp ne i64 %t1142, 0
    br i1 %t1149, label %if.then.1146, label %if.end.1148
if.then.1146:
    ret i64 1
    br label %if.end.1148
if.end.1148:
    %t1150 = load i64, i64* %c
    %t1151 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.77, i64 0, i64 0
    %t1152 = ptrtoint i8* %t1151 to i64
    %t1153 = call i64 @freak_llvm_word_eq(i64 %t1150, i64 %t1152)
    %t1154 = load i64, i64* %c
    %t1155 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.78, i64 0, i64 0
    %t1156 = ptrtoint i8* %t1155 to i64
    %t1157 = call i64 @freak_llvm_word_eq(i64 %t1154, i64 %t1156)
    %t1159 = icmp ne i64 %t1153, 0
    %t1160 = icmp ne i64 %t1157, 0
    %t1161 = or i1 %t1159, %t1160
    %t1158 = zext i1 %t1161 to i64
    %t1162 = load i64, i64* %c
    %t1163 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.79, i64 0, i64 0
    %t1164 = ptrtoint i8* %t1163 to i64
    %t1165 = call i64 @freak_llvm_word_eq(i64 %t1162, i64 %t1164)
    %t1167 = icmp ne i64 %t1158, 0
    %t1168 = icmp ne i64 %t1165, 0
    %t1169 = or i1 %t1167, %t1168
    %t1166 = zext i1 %t1169 to i64
    %t1170 = load i64, i64* %c
    %t1171 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.80, i64 0, i64 0
    %t1172 = ptrtoint i8* %t1171 to i64
    %t1173 = call i64 @freak_llvm_word_eq(i64 %t1170, i64 %t1172)
    %t1175 = icmp ne i64 %t1166, 0
    %t1176 = icmp ne i64 %t1173, 0
    %t1177 = or i1 %t1175, %t1176
    %t1174 = zext i1 %t1177 to i64
    %t1178 = load i64, i64* %c
    %t1179 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.81, i64 0, i64 0
    %t1180 = ptrtoint i8* %t1179 to i64
    %t1181 = call i64 @freak_llvm_word_eq(i64 %t1178, i64 %t1180)
    %t1183 = icmp ne i64 %t1174, 0
    %t1184 = icmp ne i64 %t1181, 0
    %t1185 = or i1 %t1183, %t1184
    %t1182 = zext i1 %t1185 to i64
    %t1186 = load i64, i64* %c
    %t1187 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.82, i64 0, i64 0
    %t1188 = ptrtoint i8* %t1187 to i64
    %t1189 = call i64 @freak_llvm_word_eq(i64 %t1186, i64 %t1188)
    %t1191 = icmp ne i64 %t1182, 0
    %t1192 = icmp ne i64 %t1189, 0
    %t1193 = or i1 %t1191, %t1192
    %t1190 = zext i1 %t1193 to i64
    %t1197 = icmp ne i64 %t1190, 0
    br i1 %t1197, label %if.then.1194, label %if.end.1196
if.then.1194:
    ret i64 1
    br label %if.end.1196
if.end.1196:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_whitespace(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1198 = load i64, i64* %c
    %t1199 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.83, i64 0, i64 0
    %t1200 = ptrtoint i8* %t1199 to i64
    %t1201 = call i64 @freak_llvm_word_eq(i64 %t1198, i64 %t1200)
    %t1205 = icmp ne i64 %t1201, 0
    br i1 %t1205, label %if.then.1202, label %if.end.1204
if.then.1202:
    ret i64 1
    br label %if.end.1204
if.end.1204:
    %t1206 = load i64, i64* %c
    %t1207 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.84, i64 0, i64 0
    %t1208 = ptrtoint i8* %t1207 to i64
    %t1209 = call i64 @freak_llvm_word_eq(i64 %t1206, i64 %t1208)
    %t1213 = icmp ne i64 %t1209, 0
    br i1 %t1213, label %if.then.1210, label %if.end.1212
if.then.1210:
    ret i64 1
    br label %if.end.1212
if.end.1212:
    %t1214 = load i64, i64* %c
    %t1215 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.85, i64 0, i64 0
    %t1216 = ptrtoint i8* %t1215 to i64
    %t1217 = call i64 @freak_llvm_word_eq(i64 %t1214, i64 %t1216)
    %t1221 = icmp ne i64 %t1217, 0
    br i1 %t1221, label %if.then.1218, label %if.end.1220
if.then.1218:
    ret i64 1
    br label %if.end.1220
if.end.1220:
    %t1222 = load i64, i64* %c
    %t1223 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.86, i64 0, i64 0
    %t1224 = ptrtoint i8* %t1223 to i64
    %t1225 = call i64 @freak_llvm_word_eq(i64 %t1222, i64 %t1224)
    %t1229 = icmp ne i64 %t1225, 0
    br i1 %t1229, label %if.then.1226, label %if.end.1228
if.then.1226:
    ret i64 1
    br label %if.end.1228
if.end.1228:
    ret i64 0
    ret i64 0
}

define i64 @freak_string_starts_with(i64 %arg_s, i64 %arg_prefix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %prefix = alloca i64
    store i64 %arg_prefix, i64* %prefix
    %t1230 = load i64, i64* %s
    %t1231 = call i64 @freak_llvm_word_length(i64 %t1230)
    %slen_v1232 = alloca i64
    store i64 %t1231, i64* %slen_v1232
    %t1233 = load i64, i64* %prefix
    %t1234 = call i64 @freak_llvm_word_length(i64 %t1233)
    %plen_v1235 = alloca i64
    store i64 %t1234, i64* %plen_v1235
    %t1236 = load i64, i64* %plen_v1235
    %t1237 = load i64, i64* %slen_v1232
    %t1239 = icmp sgt i64 %t1236, %t1237
    %t1238 = zext i1 %t1239 to i64
    %t1243 = icmp ne i64 %t1238, 0
    br i1 %t1243, label %if.then.1240, label %if.end.1242
if.then.1240:
    ret i64 0
    br label %if.end.1242
if.end.1242:
    %si_v1244 = alloca i64
    store i64 0, i64* %si_v1244
    %t1250 = load i64, i64* %plen_v1235
    %rep.1249 = alloca i64
    store i64 0, i64* %rep.1249
    br label %loop.cond.1245
loop.cond.1245:
    %t1251 = load i64, i64* %rep.1249
    %t1252 = icmp slt i64 %t1251, %t1250
    br i1 %t1252, label %loop.body.1246, label %loop.end.1247
loop.body.1246:
    %t1253 = load i64, i64* %s
    %t1255 = load i64, i64* %si_v1244
    %t1254 = call i64 @freak_llvm_word_char_at(i64 %t1253, i64 %t1255)
    %t1256 = load i64, i64* %prefix
    %t1258 = load i64, i64* %si_v1244
    %t1257 = call i64 @freak_llvm_word_char_at(i64 %t1256, i64 %t1258)
    %t1259 = call i64 @freak_llvm_word_neq(i64 %t1254, i64 %t1257)
    %t1263 = icmp ne i64 %t1259, 0
    br i1 %t1263, label %if.then.1260, label %if.end.1262
if.then.1260:
    ret i64 0
    br label %if.end.1262
if.end.1262:
    %t1264 = load i64, i64* %si_v1244
    %t1265 = add i64 %t1264, 1
    store i64 %t1265, i64* %si_v1244
    br label %loop.inc.1248
loop.inc.1248:
    %t1266 = load i64, i64* %rep.1249
    %t1267 = add i64 %t1266, 1
    store i64 %t1267, i64* %rep.1249
    br label %loop.cond.1245
loop.end.1247:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_ends_with(i64 %arg_s, i64 %arg_suffix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %suffix = alloca i64
    store i64 %arg_suffix, i64* %suffix
    %t1268 = load i64, i64* %s
    %t1269 = call i64 @freak_llvm_word_length(i64 %t1268)
    %slen_v1270 = alloca i64
    store i64 %t1269, i64* %slen_v1270
    %t1271 = load i64, i64* %suffix
    %t1272 = call i64 @freak_llvm_word_length(i64 %t1271)
    %xlen_v1273 = alloca i64
    store i64 %t1272, i64* %xlen_v1273
    %t1274 = load i64, i64* %xlen_v1273
    %t1275 = load i64, i64* %slen_v1270
    %t1277 = icmp sgt i64 %t1274, %t1275
    %t1276 = zext i1 %t1277 to i64
    %t1281 = icmp ne i64 %t1276, 0
    br i1 %t1281, label %if.then.1278, label %if.end.1280
if.then.1278:
    ret i64 0
    br label %if.end.1280
if.end.1280:
    %t1282 = load i64, i64* %slen_v1270
    %t1283 = load i64, i64* %xlen_v1273
    %t1284 = sub i64 %t1282, %t1283
    %offset_v1285 = alloca i64
    store i64 %t1284, i64* %offset_v1285
    %ei_v1286 = alloca i64
    store i64 0, i64* %ei_v1286
    %t1292 = load i64, i64* %xlen_v1273
    %rep.1291 = alloca i64
    store i64 0, i64* %rep.1291
    br label %loop.cond.1287
loop.cond.1287:
    %t1293 = load i64, i64* %rep.1291
    %t1294 = icmp slt i64 %t1293, %t1292
    br i1 %t1294, label %loop.body.1288, label %loop.end.1289
loop.body.1288:
    %t1295 = load i64, i64* %s
    %t1297 = load i64, i64* %offset_v1285
    %t1298 = load i64, i64* %ei_v1286
    %t1299 = add i64 %t1297, %t1298
    %t1296 = call i64 @freak_llvm_word_char_at(i64 %t1295, i64 %t1299)
    %t1300 = load i64, i64* %suffix
    %t1302 = load i64, i64* %ei_v1286
    %t1301 = call i64 @freak_llvm_word_char_at(i64 %t1300, i64 %t1302)
    %t1303 = call i64 @freak_llvm_word_neq(i64 %t1296, i64 %t1301)
    %t1307 = icmp ne i64 %t1303, 0
    br i1 %t1307, label %if.then.1304, label %if.end.1306
if.then.1304:
    ret i64 0
    br label %if.end.1306
if.end.1306:
    %t1308 = load i64, i64* %ei_v1286
    %t1309 = add i64 %t1308, 1
    store i64 %t1309, i64* %ei_v1286
    br label %loop.inc.1290
loop.inc.1290:
    %t1310 = load i64, i64* %rep.1291
    %t1311 = add i64 %t1310, 1
    store i64 %t1311, i64* %rep.1291
    br label %loop.cond.1287
loop.end.1289:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_contains(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1312 = load i64, i64* %haystack
    %t1313 = load i64, i64* %needle
    %t1314 = call i64 @freak_string_count(i64 %t1312, i64 %t1313)
    %t1316 = icmp sgt i64 %t1314, 0
    %t1315 = zext i1 %t1316 to i64
    ret i64 %t1315
    ret i64 0
}

define i64 @freak_string_trim(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1317 = load i64, i64* %s
    %t1318 = call i64 @freak_llvm_word_length(i64 %t1317)
    %slen_v1319 = alloca i64
    store i64 %t1318, i64* %slen_v1319
    %t1320 = load i64, i64* %slen_v1319
    %t1322 = icmp eq i64 %t1320, 0
    %t1321 = zext i1 %t1322 to i64
    %t1326 = icmp ne i64 %t1321, 0
    br i1 %t1326, label %if.then.1323, label %if.end.1325
if.then.1323:
    %t1327 = load i64, i64* %s
    ret i64 %t1327
    br label %if.end.1325
if.end.1325:
    %tstart_v1328 = alloca i64
    store i64 0, i64* %tstart_v1328
    br label %loop.cond.1329
loop.cond.1329:
    %t1332 = load i64, i64* %tstart_v1328
    %t1333 = load i64, i64* %slen_v1319
    %t1335 = icmp sge i64 %t1332, %t1333
    %t1334 = zext i1 %t1335 to i64
    %t1336 = icmp eq i64 %t1334, 0
    br i1 %t1336, label %loop.body.1330, label %loop.end.1331
loop.body.1330:
    %t1337 = load i64, i64* %s
    %t1339 = load i64, i64* %tstart_v1328
    %t1338 = call i64 @freak_llvm_word_char_at(i64 %t1337, i64 %t1339)
    %t1340 = call i64 @freak_is_whitespace(i64 %t1338)
    %t1342 = icmp eq i64 %t1340, 0
    %t1341 = zext i1 %t1342 to i64
    %t1346 = icmp ne i64 %t1341, 0
    br i1 %t1346, label %if.then.1343, label %if.end.1345
if.then.1343:
    %t1347 = load i64, i64* %s
    %t1348 = load i64, i64* %tstart_v1328
    %t1349 = call i64 @freak_string_trim_end(i64 %t1347, i64 %t1348)
    ret i64 %t1349
    br label %if.end.1345
if.end.1345:
    %t1350 = load i64, i64* %tstart_v1328
    %t1351 = add i64 %t1350, 1
    store i64 %t1351, i64* %tstart_v1328
    br label %loop.cond.1329
loop.end.1331:
    %t1352 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.87, i64 0, i64 0
    %t1353 = ptrtoint i8* %t1352 to i64
    ret i64 %t1353
    ret i64 0
}

define i64 @freak_string_trim_end(i64 %arg_s, i64 %arg_tstart) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %tstart = alloca i64
    store i64 %arg_tstart, i64* %tstart
    %t1354 = load i64, i64* %s
    %t1355 = call i64 @freak_llvm_word_length(i64 %t1354)
    %t1356 = sub i64 %t1355, 1
    %tend_v1357 = alloca i64
    store i64 %t1356, i64* %tend_v1357
    br label %loop.cond.1358
loop.cond.1358:
    %t1361 = load i64, i64* %tend_v1357
    %t1362 = load i64, i64* %tstart
    %t1364 = icmp slt i64 %t1361, %t1362
    %t1363 = zext i1 %t1364 to i64
    %t1365 = icmp eq i64 %t1363, 0
    br i1 %t1365, label %loop.body.1359, label %loop.end.1360
loop.body.1359:
    %t1366 = load i64, i64* %s
    %t1368 = load i64, i64* %tend_v1357
    %t1367 = call i64 @freak_llvm_word_char_at(i64 %t1366, i64 %t1368)
    %t1369 = call i64 @freak_is_whitespace(i64 %t1367)
    %t1371 = icmp eq i64 %t1369, 0
    %t1370 = zext i1 %t1371 to i64
    %t1375 = icmp ne i64 %t1370, 0
    br i1 %t1375, label %if.then.1372, label %if.end.1374
if.then.1372:
    %t1376 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.88, i64 0, i64 0
    %t1377 = ptrtoint i8* %t1376 to i64
    %tout_v1378 = alloca i64
    store i64 %t1377, i64* %tout_v1378
    %t1379 = load i64, i64* %tstart
    %ti_v1380 = alloca i64
    store i64 %t1379, i64* %ti_v1380
    br label %loop.cond.1381
loop.cond.1381:
    %t1384 = load i64, i64* %ti_v1380
    %t1385 = load i64, i64* %tend_v1357
    %t1387 = icmp sgt i64 %t1384, %t1385
    %t1386 = zext i1 %t1387 to i64
    %t1388 = icmp eq i64 %t1386, 0
    br i1 %t1388, label %loop.body.1382, label %loop.end.1383
loop.body.1382:
    %t1389 = load i64, i64* %tout_v1378
    %t1390 = load i64, i64* %s
    %t1392 = load i64, i64* %ti_v1380
    %t1391 = call i64 @freak_llvm_word_char_at(i64 %t1390, i64 %t1392)
    %t1393 = call i64 @freak_llvm_word_concat(i64 %t1389, i64 %t1391)
    store i64 %t1393, i64* %tout_v1378
    %t1394 = load i64, i64* %ti_v1380
    %t1395 = add i64 %t1394, 1
    store i64 %t1395, i64* %ti_v1380
    br label %loop.cond.1381
loop.end.1383:
    %t1396 = load i64, i64* %tout_v1378
    ret i64 %t1396
    br label %if.end.1374
if.end.1374:
    %t1397 = load i64, i64* %tend_v1357
    %t1398 = sub i64 %t1397, 1
    store i64 %t1398, i64* %tend_v1357
    br label %loop.cond.1358
loop.end.1360:
    %t1399 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.89, i64 0, i64 0
    %t1400 = ptrtoint i8* %t1399 to i64
    ret i64 %t1400
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
    %t1401 = load i64, i64* %s
    %t1402 = call i64 @freak_llvm_word_length(i64 %t1401)
    %slen_v1403 = alloca i64
    store i64 %t1402, i64* %slen_v1403
    %t1404 = load i64, i64* %old_str
    %t1405 = call i64 @freak_llvm_word_length(i64 %t1404)
    %olen_v1406 = alloca i64
    store i64 %t1405, i64* %olen_v1406
    %t1407 = load i64, i64* %olen_v1406
    %t1409 = icmp eq i64 %t1407, 0
    %t1408 = zext i1 %t1409 to i64
    %t1413 = icmp ne i64 %t1408, 0
    br i1 %t1413, label %if.then.1410, label %if.end.1412
if.then.1410:
    %t1414 = load i64, i64* %s
    ret i64 %t1414
    br label %if.end.1412
if.end.1412:
    %t1415 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.90, i64 0, i64 0
    %t1416 = ptrtoint i8* %t1415 to i64
    %rout_v1417 = alloca i64
    store i64 %t1416, i64* %rout_v1417
    %ri_v1418 = alloca i64
    store i64 0, i64* %ri_v1418
    br label %loop.cond.1419
loop.cond.1419:
    %t1422 = load i64, i64* %ri_v1418
    %t1423 = load i64, i64* %slen_v1403
    %t1425 = icmp sge i64 %t1422, %t1423
    %t1424 = zext i1 %t1425 to i64
    %t1426 = icmp eq i64 %t1424, 0
    br i1 %t1426, label %loop.body.1420, label %loop.end.1421
loop.body.1420:
    %rmatch_v1427 = alloca i64
    store i64 1, i64* %rmatch_v1427
    %t1428 = load i64, i64* %ri_v1418
    %t1429 = load i64, i64* %olen_v1406
    %t1430 = add i64 %t1428, %t1429
    %t1431 = load i64, i64* %slen_v1403
    %t1433 = icmp sle i64 %t1430, %t1431
    %t1432 = zext i1 %t1433 to i64
    %t1437 = icmp ne i64 %t1432, 0
    br i1 %t1437, label %if.then.1434, label %if.else.1435
if.then.1434:
    %rj_v1438 = alloca i64
    store i64 0, i64* %rj_v1438
    %t1444 = load i64, i64* %olen_v1406
    %rep.1443 = alloca i64
    store i64 0, i64* %rep.1443
    br label %loop.cond.1439
loop.cond.1439:
    %t1445 = load i64, i64* %rep.1443
    %t1446 = icmp slt i64 %t1445, %t1444
    br i1 %t1446, label %loop.body.1440, label %loop.end.1441
loop.body.1440:
    %t1447 = load i64, i64* %rmatch_v1427
    %t1451 = icmp ne i64 %t1447, 0
    br i1 %t1451, label %if.then.1448, label %if.end.1450
if.then.1448:
    %t1452 = load i64, i64* %s
    %t1454 = load i64, i64* %ri_v1418
    %t1455 = load i64, i64* %rj_v1438
    %t1456 = add i64 %t1454, %t1455
    %t1453 = call i64 @freak_llvm_word_char_at(i64 %t1452, i64 %t1456)
    %t1457 = load i64, i64* %old_str
    %t1459 = load i64, i64* %rj_v1438
    %t1458 = call i64 @freak_llvm_word_char_at(i64 %t1457, i64 %t1459)
    %t1460 = call i64 @freak_llvm_word_neq(i64 %t1453, i64 %t1458)
    %t1464 = icmp ne i64 %t1460, 0
    br i1 %t1464, label %if.then.1461, label %if.end.1463
if.then.1461:
    store i64 0, i64* %rmatch_v1427
    br label %if.end.1463
if.end.1463:
    br label %if.end.1450
if.end.1450:
    %t1465 = load i64, i64* %rj_v1438
    %t1466 = add i64 %t1465, 1
    store i64 %t1466, i64* %rj_v1438
    br label %loop.inc.1442
loop.inc.1442:
    %t1467 = load i64, i64* %rep.1443
    %t1468 = add i64 %t1467, 1
    store i64 %t1468, i64* %rep.1443
    br label %loop.cond.1439
loop.end.1441:
    br label %if.end.1436
if.else.1435:
    store i64 0, i64* %rmatch_v1427
    br label %if.end.1436
if.end.1436:
    %t1469 = load i64, i64* %rmatch_v1427
    %t1473 = icmp ne i64 %t1469, 0
    br i1 %t1473, label %if.then.1470, label %if.else.1471
if.then.1470:
    %t1474 = load i64, i64* %rout_v1417
    %t1475 = load i64, i64* %new_str
    %t1476 = call i64 @freak_llvm_word_concat(i64 %t1474, i64 %t1475)
    store i64 %t1476, i64* %rout_v1417
    %t1477 = load i64, i64* %olen_v1406
    %t1478 = load i64, i64* %ri_v1418
    %t1479 = add i64 %t1478, %t1477
    store i64 %t1479, i64* %ri_v1418
    br label %if.end.1472
if.else.1471:
    %t1480 = load i64, i64* %rout_v1417
    %t1481 = load i64, i64* %s
    %t1483 = load i64, i64* %ri_v1418
    %t1482 = call i64 @freak_llvm_word_char_at(i64 %t1481, i64 %t1483)
    %t1484 = call i64 @freak_llvm_word_concat(i64 %t1480, i64 %t1482)
    store i64 %t1484, i64* %rout_v1417
    %t1485 = load i64, i64* %ri_v1418
    %t1486 = add i64 %t1485, 1
    store i64 %t1486, i64* %ri_v1418
    br label %if.end.1472
if.end.1472:
    br label %loop.cond.1419
loop.end.1421:
    %t1487 = load i64, i64* %rout_v1417
    ret i64 %t1487
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
    %t1488 = load i64, i64* %s
    %t1489 = call i64 @freak_llvm_word_length(i64 %t1488)
    %slen_v1490 = alloca i64
    store i64 %t1489, i64* %slen_v1490
    %t1491 = load i64, i64* %start_idx
    %ss_v1492 = alloca i64
    store i64 %t1491, i64* %ss_v1492
    %t1493 = load i64, i64* %end_idx
    %se_v1494 = alloca i64
    store i64 %t1493, i64* %se_v1494
    %t1495 = load i64, i64* %ss_v1492
    %t1497 = icmp slt i64 %t1495, 0
    %t1496 = zext i1 %t1497 to i64
    %t1501 = icmp ne i64 %t1496, 0
    br i1 %t1501, label %if.then.1498, label %if.end.1500
if.then.1498:
    store i64 0, i64* %ss_v1492
    br label %if.end.1500
if.end.1500:
    %t1502 = load i64, i64* %se_v1494
    %t1503 = load i64, i64* %slen_v1490
    %t1505 = icmp sgt i64 %t1502, %t1503
    %t1504 = zext i1 %t1505 to i64
    %t1509 = icmp ne i64 %t1504, 0
    br i1 %t1509, label %if.then.1506, label %if.end.1508
if.then.1506:
    %t1510 = load i64, i64* %slen_v1490
    store i64 %t1510, i64* %se_v1494
    br label %if.end.1508
if.end.1508:
    %t1511 = load i64, i64* %ss_v1492
    %t1512 = load i64, i64* %se_v1494
    %t1514 = icmp sge i64 %t1511, %t1512
    %t1513 = zext i1 %t1514 to i64
    %t1518 = icmp ne i64 %t1513, 0
    br i1 %t1518, label %if.then.1515, label %if.end.1517
if.then.1515:
    %t1519 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.91, i64 0, i64 0
    %t1520 = ptrtoint i8* %t1519 to i64
    ret i64 %t1520
    br label %if.end.1517
if.end.1517:
    %t1521 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.92, i64 0, i64 0
    %t1522 = ptrtoint i8* %t1521 to i64
    %sub_out_v1523 = alloca i64
    store i64 %t1522, i64* %sub_out_v1523
    %t1524 = load i64, i64* %ss_v1492
    %si_v1525 = alloca i64
    store i64 %t1524, i64* %si_v1525
    br label %loop.cond.1526
loop.cond.1526:
    %t1529 = load i64, i64* %si_v1525
    %t1530 = load i64, i64* %se_v1494
    %t1532 = icmp sge i64 %t1529, %t1530
    %t1531 = zext i1 %t1532 to i64
    %t1533 = icmp eq i64 %t1531, 0
    br i1 %t1533, label %loop.body.1527, label %loop.end.1528
loop.body.1527:
    %t1534 = load i64, i64* %sub_out_v1523
    %t1535 = load i64, i64* %s
    %t1537 = load i64, i64* %si_v1525
    %t1536 = call i64 @freak_llvm_word_char_at(i64 %t1535, i64 %t1537)
    %t1538 = call i64 @freak_llvm_word_concat(i64 %t1534, i64 %t1536)
    store i64 %t1538, i64* %sub_out_v1523
    %t1539 = load i64, i64* %si_v1525
    %t1540 = add i64 %t1539, 1
    store i64 %t1540, i64* %si_v1525
    br label %loop.cond.1526
loop.end.1528:
    %t1541 = load i64, i64* %sub_out_v1523
    ret i64 %t1541
    ret i64 0
}

define i64 @freak_string_index_of(i64 %arg_s, i64 %arg_needle) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1542 = load i64, i64* %s
    %t1543 = call i64 @freak_llvm_word_length(i64 %t1542)
    %slen_v1544 = alloca i64
    store i64 %t1543, i64* %slen_v1544
    %t1545 = load i64, i64* %needle
    %t1546 = call i64 @freak_llvm_word_length(i64 %t1545)
    %nlen_v1547 = alloca i64
    store i64 %t1546, i64* %nlen_v1547
    %t1548 = load i64, i64* %nlen_v1547
    %t1550 = icmp eq i64 %t1548, 0
    %t1549 = zext i1 %t1550 to i64
    %t1554 = icmp ne i64 %t1549, 0
    br i1 %t1554, label %if.then.1551, label %if.end.1553
if.then.1551:
    ret i64 0
    br label %if.end.1553
if.end.1553:
    %t1555 = load i64, i64* %nlen_v1547
    %t1556 = load i64, i64* %slen_v1544
    %t1558 = icmp sgt i64 %t1555, %t1556
    %t1557 = zext i1 %t1558 to i64
    %t1562 = icmp ne i64 %t1557, 0
    br i1 %t1562, label %if.then.1559, label %if.end.1561
if.then.1559:
    %t1563 = sub i64 0, 1
    ret i64 %t1563
    br label %if.end.1561
if.end.1561:
    %t1564 = load i64, i64* %slen_v1544
    %t1565 = load i64, i64* %nlen_v1547
    %t1566 = sub i64 %t1564, %t1565
    %t1567 = add i64 %t1566, 1
    %limit_v1568 = alloca i64
    store i64 %t1567, i64* %limit_v1568
    %fi_v1569 = alloca i64
    store i64 0, i64* %fi_v1569
    %t1575 = load i64, i64* %limit_v1568
    %rep.1574 = alloca i64
    store i64 0, i64* %rep.1574
    br label %loop.cond.1570
loop.cond.1570:
    %t1576 = load i64, i64* %rep.1574
    %t1577 = icmp slt i64 %t1576, %t1575
    br i1 %t1577, label %loop.body.1571, label %loop.end.1572
loop.body.1571:
    %fmatch_v1578 = alloca i64
    store i64 1, i64* %fmatch_v1578
    %fj_v1579 = alloca i64
    store i64 0, i64* %fj_v1579
    %t1585 = load i64, i64* %nlen_v1547
    %rep.1584 = alloca i64
    store i64 0, i64* %rep.1584
    br label %loop.cond.1580
loop.cond.1580:
    %t1586 = load i64, i64* %rep.1584
    %t1587 = icmp slt i64 %t1586, %t1585
    br i1 %t1587, label %loop.body.1581, label %loop.end.1582
loop.body.1581:
    %t1588 = load i64, i64* %fmatch_v1578
    %t1592 = icmp ne i64 %t1588, 0
    br i1 %t1592, label %if.then.1589, label %if.end.1591
if.then.1589:
    %t1593 = load i64, i64* %s
    %t1595 = load i64, i64* %fi_v1569
    %t1596 = load i64, i64* %fj_v1579
    %t1597 = add i64 %t1595, %t1596
    %t1594 = call i64 @freak_llvm_word_char_at(i64 %t1593, i64 %t1597)
    %t1598 = load i64, i64* %needle
    %t1600 = load i64, i64* %fj_v1579
    %t1599 = call i64 @freak_llvm_word_char_at(i64 %t1598, i64 %t1600)
    %t1601 = call i64 @freak_llvm_word_neq(i64 %t1594, i64 %t1599)
    %t1605 = icmp ne i64 %t1601, 0
    br i1 %t1605, label %if.then.1602, label %if.end.1604
if.then.1602:
    store i64 0, i64* %fmatch_v1578
    br label %if.end.1604
if.end.1604:
    br label %if.end.1591
if.end.1591:
    %t1606 = load i64, i64* %fj_v1579
    %t1607 = add i64 %t1606, 1
    store i64 %t1607, i64* %fj_v1579
    br label %loop.inc.1583
loop.inc.1583:
    %t1608 = load i64, i64* %rep.1584
    %t1609 = add i64 %t1608, 1
    store i64 %t1609, i64* %rep.1584
    br label %loop.cond.1580
loop.end.1582:
    %t1610 = load i64, i64* %fmatch_v1578
    %t1614 = icmp ne i64 %t1610, 0
    br i1 %t1614, label %if.then.1611, label %if.end.1613
if.then.1611:
    %t1615 = load i64, i64* %fi_v1569
    ret i64 %t1615
    br label %if.end.1613
if.end.1613:
    %t1616 = load i64, i64* %fi_v1569
    %t1617 = add i64 %t1616, 1
    store i64 %t1617, i64* %fi_v1569
    br label %loop.inc.1573
loop.inc.1573:
    %t1618 = load i64, i64* %rep.1574
    %t1619 = add i64 %t1618, 1
    store i64 %t1619, i64* %rep.1574
    br label %loop.cond.1570
loop.end.1572:
    %t1620 = sub i64 0, 1
    ret i64 %t1620
    ret i64 0
}

define i64 @freak_int_to_hex(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1621 = load i64, i64* %n
    %t1623 = icmp eq i64 %t1621, 0
    %t1622 = zext i1 %t1623 to i64
    %t1627 = icmp ne i64 %t1622, 0
    br i1 %t1627, label %if.then.1624, label %if.end.1626
if.then.1624:
    %t1628 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.93, i64 0, i64 0
    %t1629 = ptrtoint i8* %t1628 to i64
    ret i64 %t1629
    br label %if.end.1626
if.end.1626:
    %t1630 = getelementptr inbounds [17 x i8], [17 x i8]* @.str.94, i64 0, i64 0
    %t1631 = ptrtoint i8* %t1630 to i64
    %hex_chars_v1632 = alloca i64
    store i64 %t1631, i64* %hex_chars_v1632
    %neg_v1633 = alloca i64
    store i64 0, i64* %neg_v1633
    %t1634 = load i64, i64* %n
    %val_v1635 = alloca i64
    store i64 %t1634, i64* %val_v1635
    %t1636 = load i64, i64* %val_v1635
    %t1638 = icmp slt i64 %t1636, 0
    %t1637 = zext i1 %t1638 to i64
    %t1642 = icmp ne i64 %t1637, 0
    br i1 %t1642, label %if.then.1639, label %if.end.1641
if.then.1639:
    store i64 1, i64* %neg_v1633
    %t1643 = load i64, i64* %val_v1635
    %t1644 = sub i64 0, %t1643
    store i64 %t1644, i64* %val_v1635
    br label %if.end.1641
if.end.1641:
    %t1645 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.95, i64 0, i64 0
    %t1646 = ptrtoint i8* %t1645 to i64
    %hex_out_v1647 = alloca i64
    store i64 %t1646, i64* %hex_out_v1647
    br label %loop.cond.1648
loop.cond.1648:
    %t1651 = load i64, i64* %val_v1635
    %t1653 = icmp sle i64 %t1651, 0
    %t1652 = zext i1 %t1653 to i64
    %t1654 = icmp eq i64 %t1652, 0
    br i1 %t1654, label %loop.body.1649, label %loop.end.1650
loop.body.1649:
    %t1655 = load i64, i64* %val_v1635
    %t1656 = load i64, i64* %val_v1635
    %t1657 = sdiv i64 %t1656, 16
    %t1658 = mul i64 %t1657, 16
    %t1659 = sub i64 %t1655, %t1658
    %rem_v1660 = alloca i64
    store i64 %t1659, i64* %rem_v1660
    %t1661 = load i64, i64* %hex_chars_v1632
    %t1663 = load i64, i64* %rem_v1660
    %t1662 = call i64 @freak_llvm_word_char_at(i64 %t1661, i64 %t1663)
    %t1664 = load i64, i64* %hex_out_v1647
    %t1665 = call i64 @freak_llvm_word_concat(i64 %t1662, i64 %t1664)
    store i64 %t1665, i64* %hex_out_v1647
    %t1666 = load i64, i64* %val_v1635
    %t1667 = sdiv i64 %t1666, 16
    store i64 %t1667, i64* %val_v1635
    br label %loop.cond.1648
loop.end.1650:
    %t1668 = load i64, i64* %neg_v1633
    %t1672 = icmp ne i64 %t1668, 0
    br i1 %t1672, label %if.then.1669, label %if.end.1671
if.then.1669:
    %t1673 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.96, i64 0, i64 0
    %t1674 = ptrtoint i8* %t1673 to i64
    %t1675 = load i64, i64* %hex_out_v1647
    %t1676 = call i64 @freak_llvm_word_concat(i64 %t1674, i64 %t1675)
    store i64 %t1676, i64* %hex_out_v1647
    br label %if.end.1671
if.end.1671:
    %t1677 = load i64, i64* %hex_out_v1647
    ret i64 %t1677
    ret i64 0
}

define i64 @freak_int_to_bin(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1678 = load i64, i64* %n
    %t1680 = icmp eq i64 %t1678, 0
    %t1679 = zext i1 %t1680 to i64
    %t1684 = icmp ne i64 %t1679, 0
    br i1 %t1684, label %if.then.1681, label %if.end.1683
if.then.1681:
    %t1685 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.97, i64 0, i64 0
    %t1686 = ptrtoint i8* %t1685 to i64
    ret i64 %t1686
    br label %if.end.1683
if.end.1683:
    %neg_v1687 = alloca i64
    store i64 0, i64* %neg_v1687
    %t1688 = load i64, i64* %n
    %val_v1689 = alloca i64
    store i64 %t1688, i64* %val_v1689
    %t1690 = load i64, i64* %val_v1689
    %t1692 = icmp slt i64 %t1690, 0
    %t1691 = zext i1 %t1692 to i64
    %t1696 = icmp ne i64 %t1691, 0
    br i1 %t1696, label %if.then.1693, label %if.end.1695
if.then.1693:
    store i64 1, i64* %neg_v1687
    %t1697 = load i64, i64* %val_v1689
    %t1698 = sub i64 0, %t1697
    store i64 %t1698, i64* %val_v1689
    br label %if.end.1695
if.end.1695:
    %t1699 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.98, i64 0, i64 0
    %t1700 = ptrtoint i8* %t1699 to i64
    %bin_out_v1701 = alloca i64
    store i64 %t1700, i64* %bin_out_v1701
    br label %loop.cond.1702
loop.cond.1702:
    %t1705 = load i64, i64* %val_v1689
    %t1707 = icmp sle i64 %t1705, 0
    %t1706 = zext i1 %t1707 to i64
    %t1708 = icmp eq i64 %t1706, 0
    br i1 %t1708, label %loop.body.1703, label %loop.end.1704
loop.body.1703:
    %t1709 = load i64, i64* %val_v1689
    %t1710 = load i64, i64* %val_v1689
    %t1711 = sdiv i64 %t1710, 2
    %t1712 = mul i64 %t1711, 2
    %t1713 = sub i64 %t1709, %t1712
    %rem_v1714 = alloca i64
    store i64 %t1713, i64* %rem_v1714
    %t1715 = load i64, i64* %rem_v1714
    %t1717 = icmp eq i64 %t1715, 1
    %t1716 = zext i1 %t1717 to i64
    %t1721 = icmp ne i64 %t1716, 0
    br i1 %t1721, label %if.then.1718, label %if.else.1719
if.then.1718:
    %t1722 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.99, i64 0, i64 0
    %t1723 = ptrtoint i8* %t1722 to i64
    %t1724 = load i64, i64* %bin_out_v1701
    %t1725 = call i64 @freak_llvm_word_concat(i64 %t1723, i64 %t1724)
    store i64 %t1725, i64* %bin_out_v1701
    br label %if.end.1720
if.else.1719:
    %t1726 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.100, i64 0, i64 0
    %t1727 = ptrtoint i8* %t1726 to i64
    %t1728 = load i64, i64* %bin_out_v1701
    %t1729 = call i64 @freak_llvm_word_concat(i64 %t1727, i64 %t1728)
    store i64 %t1729, i64* %bin_out_v1701
    br label %if.end.1720
if.end.1720:
    %t1730 = load i64, i64* %val_v1689
    %t1731 = sdiv i64 %t1730, 2
    store i64 %t1731, i64* %val_v1689
    br label %loop.cond.1702
loop.end.1704:
    %t1732 = load i64, i64* %neg_v1687
    %t1736 = icmp ne i64 %t1732, 0
    br i1 %t1736, label %if.then.1733, label %if.end.1735
if.then.1733:
    %t1737 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.101, i64 0, i64 0
    %t1738 = ptrtoint i8* %t1737 to i64
    %t1739 = load i64, i64* %bin_out_v1701
    %t1740 = call i64 @freak_llvm_word_concat(i64 %t1738, i64 %t1739)
    store i64 %t1740, i64* %bin_out_v1701
    br label %if.end.1735
if.end.1735:
    %t1741 = load i64, i64* %bin_out_v1701
    ret i64 %t1741
    ret i64 0
}

define i64 @freak_int_to_oct(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1742 = load i64, i64* %n
    %t1744 = icmp eq i64 %t1742, 0
    %t1743 = zext i1 %t1744 to i64
    %t1748 = icmp ne i64 %t1743, 0
    br i1 %t1748, label %if.then.1745, label %if.end.1747
if.then.1745:
    %t1749 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.102, i64 0, i64 0
    %t1750 = ptrtoint i8* %t1749 to i64
    ret i64 %t1750
    br label %if.end.1747
if.end.1747:
    %t1751 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.103, i64 0, i64 0
    %t1752 = ptrtoint i8* %t1751 to i64
    %oct_chars_v1753 = alloca i64
    store i64 %t1752, i64* %oct_chars_v1753
    %neg_v1754 = alloca i64
    store i64 0, i64* %neg_v1754
    %t1755 = load i64, i64* %n
    %val_v1756 = alloca i64
    store i64 %t1755, i64* %val_v1756
    %t1757 = load i64, i64* %val_v1756
    %t1759 = icmp slt i64 %t1757, 0
    %t1758 = zext i1 %t1759 to i64
    %t1763 = icmp ne i64 %t1758, 0
    br i1 %t1763, label %if.then.1760, label %if.end.1762
if.then.1760:
    store i64 1, i64* %neg_v1754
    %t1764 = load i64, i64* %val_v1756
    %t1765 = sub i64 0, %t1764
    store i64 %t1765, i64* %val_v1756
    br label %if.end.1762
if.end.1762:
    %t1766 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.104, i64 0, i64 0
    %t1767 = ptrtoint i8* %t1766 to i64
    %oct_out_v1768 = alloca i64
    store i64 %t1767, i64* %oct_out_v1768
    br label %loop.cond.1769
loop.cond.1769:
    %t1772 = load i64, i64* %val_v1756
    %t1774 = icmp sle i64 %t1772, 0
    %t1773 = zext i1 %t1774 to i64
    %t1775 = icmp eq i64 %t1773, 0
    br i1 %t1775, label %loop.body.1770, label %loop.end.1771
loop.body.1770:
    %t1776 = load i64, i64* %val_v1756
    %t1777 = load i64, i64* %val_v1756
    %t1778 = sdiv i64 %t1777, 8
    %t1779 = mul i64 %t1778, 8
    %t1780 = sub i64 %t1776, %t1779
    %rem_v1781 = alloca i64
    store i64 %t1780, i64* %rem_v1781
    %t1782 = load i64, i64* %oct_chars_v1753
    %t1784 = load i64, i64* %rem_v1781
    %t1783 = call i64 @freak_llvm_word_char_at(i64 %t1782, i64 %t1784)
    %t1785 = load i64, i64* %oct_out_v1768
    %t1786 = call i64 @freak_llvm_word_concat(i64 %t1783, i64 %t1785)
    store i64 %t1786, i64* %oct_out_v1768
    %t1787 = load i64, i64* %val_v1756
    %t1788 = sdiv i64 %t1787, 8
    store i64 %t1788, i64* %val_v1756
    br label %loop.cond.1769
loop.end.1771:
    %t1789 = load i64, i64* %neg_v1754
    %t1793 = icmp ne i64 %t1789, 0
    br i1 %t1793, label %if.then.1790, label %if.end.1792
if.then.1790:
    %t1794 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.105, i64 0, i64 0
    %t1795 = ptrtoint i8* %t1794 to i64
    %t1796 = load i64, i64* %oct_out_v1768
    %t1797 = call i64 @freak_llvm_word_concat(i64 %t1795, i64 %t1796)
    store i64 %t1797, i64* %oct_out_v1768
    br label %if.end.1792
if.end.1792:
    %t1798 = load i64, i64* %oct_out_v1768
    ret i64 %t1798
    ret i64 0
}

define i64 @freak_char_to_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1799 = load i64, i64* %c
    %t1800 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.106, i64 0, i64 0
    %t1801 = ptrtoint i8* %t1800 to i64
    %t1802 = call i64 @freak_llvm_word_eq(i64 %t1799, i64 %t1801)
    %t1806 = icmp ne i64 %t1802, 0
    br i1 %t1806, label %if.then.1803, label %if.end.1805
if.then.1803:
    ret i64 0
    br label %if.end.1805
if.end.1805:
    %t1807 = load i64, i64* %c
    %t1808 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.107, i64 0, i64 0
    %t1809 = ptrtoint i8* %t1808 to i64
    %t1810 = call i64 @freak_llvm_word_eq(i64 %t1807, i64 %t1809)
    %t1814 = icmp ne i64 %t1810, 0
    br i1 %t1814, label %if.then.1811, label %if.end.1813
if.then.1811:
    ret i64 1
    br label %if.end.1813
if.end.1813:
    %t1815 = load i64, i64* %c
    %t1816 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.108, i64 0, i64 0
    %t1817 = ptrtoint i8* %t1816 to i64
    %t1818 = call i64 @freak_llvm_word_eq(i64 %t1815, i64 %t1817)
    %t1822 = icmp ne i64 %t1818, 0
    br i1 %t1822, label %if.then.1819, label %if.end.1821
if.then.1819:
    ret i64 2
    br label %if.end.1821
if.end.1821:
    %t1823 = load i64, i64* %c
    %t1824 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.109, i64 0, i64 0
    %t1825 = ptrtoint i8* %t1824 to i64
    %t1826 = call i64 @freak_llvm_word_eq(i64 %t1823, i64 %t1825)
    %t1830 = icmp ne i64 %t1826, 0
    br i1 %t1830, label %if.then.1827, label %if.end.1829
if.then.1827:
    ret i64 3
    br label %if.end.1829
if.end.1829:
    %t1831 = load i64, i64* %c
    %t1832 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.110, i64 0, i64 0
    %t1833 = ptrtoint i8* %t1832 to i64
    %t1834 = call i64 @freak_llvm_word_eq(i64 %t1831, i64 %t1833)
    %t1838 = icmp ne i64 %t1834, 0
    br i1 %t1838, label %if.then.1835, label %if.end.1837
if.then.1835:
    ret i64 4
    br label %if.end.1837
if.end.1837:
    %t1839 = load i64, i64* %c
    %t1840 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.111, i64 0, i64 0
    %t1841 = ptrtoint i8* %t1840 to i64
    %t1842 = call i64 @freak_llvm_word_eq(i64 %t1839, i64 %t1841)
    %t1846 = icmp ne i64 %t1842, 0
    br i1 %t1846, label %if.then.1843, label %if.end.1845
if.then.1843:
    ret i64 5
    br label %if.end.1845
if.end.1845:
    %t1847 = load i64, i64* %c
    %t1848 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.112, i64 0, i64 0
    %t1849 = ptrtoint i8* %t1848 to i64
    %t1850 = call i64 @freak_llvm_word_eq(i64 %t1847, i64 %t1849)
    %t1854 = icmp ne i64 %t1850, 0
    br i1 %t1854, label %if.then.1851, label %if.end.1853
if.then.1851:
    ret i64 6
    br label %if.end.1853
if.end.1853:
    %t1855 = load i64, i64* %c
    %t1856 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.113, i64 0, i64 0
    %t1857 = ptrtoint i8* %t1856 to i64
    %t1858 = call i64 @freak_llvm_word_eq(i64 %t1855, i64 %t1857)
    %t1862 = icmp ne i64 %t1858, 0
    br i1 %t1862, label %if.then.1859, label %if.end.1861
if.then.1859:
    ret i64 7
    br label %if.end.1861
if.end.1861:
    %t1863 = load i64, i64* %c
    %t1864 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.114, i64 0, i64 0
    %t1865 = ptrtoint i8* %t1864 to i64
    %t1866 = call i64 @freak_llvm_word_eq(i64 %t1863, i64 %t1865)
    %t1870 = icmp ne i64 %t1866, 0
    br i1 %t1870, label %if.then.1867, label %if.end.1869
if.then.1867:
    ret i64 8
    br label %if.end.1869
if.end.1869:
    %t1871 = load i64, i64* %c
    %t1872 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.115, i64 0, i64 0
    %t1873 = ptrtoint i8* %t1872 to i64
    %t1874 = call i64 @freak_llvm_word_eq(i64 %t1871, i64 %t1873)
    %t1878 = icmp ne i64 %t1874, 0
    br i1 %t1878, label %if.then.1875, label %if.end.1877
if.then.1875:
    ret i64 9
    br label %if.end.1877
if.end.1877:
    %t1879 = sub i64 0, 1
    ret i64 %t1879
    ret i64 0
}

define i64 @freak_word_to_int_safe(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1880 = load i64, i64* %s
    %t1881 = call i64 @freak_llvm_word_length(i64 %t1880)
    %slen_v1882 = alloca i64
    store i64 %t1881, i64* %slen_v1882
    %t1883 = load i64, i64* %slen_v1882
    %t1885 = icmp eq i64 %t1883, 0
    %t1884 = zext i1 %t1885 to i64
    %t1889 = icmp ne i64 %t1884, 0
    br i1 %t1889, label %if.then.1886, label %if.end.1888
if.then.1886:
    ret i64 0
    br label %if.end.1888
if.end.1888:
    %neg_v1890 = alloca i64
    store i64 0, i64* %neg_v1890
    %wi_v1891 = alloca i64
    store i64 0, i64* %wi_v1891
    %t1892 = load i64, i64* %s
    %t1893 = call i64 @freak_llvm_word_char_at(i64 %t1892, i64 0)
    %t1894 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.116, i64 0, i64 0
    %t1895 = ptrtoint i8* %t1894 to i64
    %t1896 = call i64 @freak_llvm_word_eq(i64 %t1893, i64 %t1895)
    %t1900 = icmp ne i64 %t1896, 0
    br i1 %t1900, label %if.then.1897, label %if.end.1899
if.then.1897:
    store i64 1, i64* %neg_v1890
    store i64 1, i64* %wi_v1891
    br label %if.end.1899
if.end.1899:
    %num_v1901 = alloca i64
    store i64 0, i64* %num_v1901
    br label %loop.cond.1902
loop.cond.1902:
    %t1905 = load i64, i64* %wi_v1891
    %t1906 = load i64, i64* %slen_v1882
    %t1908 = icmp sge i64 %t1905, %t1906
    %t1907 = zext i1 %t1908 to i64
    %t1909 = icmp eq i64 %t1907, 0
    br i1 %t1909, label %loop.body.1903, label %loop.end.1904
loop.body.1903:
    %t1910 = load i64, i64* %s
    %t1912 = load i64, i64* %wi_v1891
    %t1911 = call i64 @freak_llvm_word_char_at(i64 %t1910, i64 %t1912)
    %t1913 = call i64 @freak_char_to_digit(i64 %t1911)
    %d_v1914 = alloca i64
    store i64 %t1913, i64* %d_v1914
    %t1915 = load i64, i64* %d_v1914
    %t1917 = icmp slt i64 %t1915, 0
    %t1916 = zext i1 %t1917 to i64
    %t1921 = icmp ne i64 %t1916, 0
    br i1 %t1921, label %if.then.1918, label %if.end.1920
if.then.1918:
    ret i64 0
    br label %if.end.1920
if.end.1920:
    %t1922 = load i64, i64* %num_v1901
    %t1923 = mul i64 %t1922, 10
    %t1924 = load i64, i64* %d_v1914
    %t1925 = add i64 %t1923, %t1924
    store i64 %t1925, i64* %num_v1901
    %t1926 = load i64, i64* %wi_v1891
    %t1927 = add i64 %t1926, 1
    store i64 %t1927, i64* %wi_v1891
    br label %loop.cond.1902
loop.end.1904:
    %t1928 = load i64, i64* %neg_v1890
    %t1932 = icmp ne i64 %t1928, 0
    br i1 %t1932, label %if.then.1929, label %if.end.1931
if.then.1929:
    %t1933 = load i64, i64* %num_v1901
    %t1934 = sub i64 0, %t1933
    ret i64 %t1934
    br label %if.end.1931
if.end.1931:
    %t1935 = load i64, i64* %num_v1901
    ret i64 %t1935
    ret i64 0
}

define i64 @freak_bool_to_word(i64 %arg_b) {
entry:
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t1936 = load i64, i64* %b
    %t1940 = icmp ne i64 %t1936, 0
    br i1 %t1940, label %if.then.1937, label %if.end.1939
if.then.1937:
    %t1941 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.117, i64 0, i64 0
    %t1942 = ptrtoint i8* %t1941 to i64
    ret i64 %t1942
    br label %if.end.1939
if.end.1939:
    %t1943 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.118, i64 0, i64 0
    %t1944 = ptrtoint i8* %t1943 to i64
    ret i64 %t1944
    ret i64 0
}

define void @freak_array_sort_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t1945 = load i64, i64* %handle
    %t1946 = call i64 @freak_llvm_array_len(i64 %t1945)
    %alen_v1947 = alloca i64
    store i64 %t1946, i64* %alen_v1947
    %t1948 = load i64, i64* %alen_v1947
    %t1950 = icmp sle i64 %t1948, 1
    %t1949 = zext i1 %t1950 to i64
    %t1954 = icmp ne i64 %t1949, 0
    br i1 %t1954, label %if.then.1951, label %if.end.1953
if.then.1951:
    ret void
    br label %if.end.1953
if.end.1953:
    %si_v1955 = alloca i64
    store i64 1, i64* %si_v1955
    br label %loop.cond.1956
loop.cond.1956:
    %t1959 = load i64, i64* %si_v1955
    %t1960 = load i64, i64* %alen_v1947
    %t1962 = icmp sge i64 %t1959, %t1960
    %t1961 = zext i1 %t1962 to i64
    %t1963 = icmp eq i64 %t1961, 0
    br i1 %t1963, label %loop.body.1957, label %loop.end.1958
loop.body.1957:
    %t1964 = load i64, i64* %handle
    %t1965 = load i64, i64* %si_v1955
    %t1966 = call i64 @freak_llvm_array_get(i64 %t1964, i64 %t1965)
    %key_w_v1967 = alloca i64
    store i64 %t1966, i64* %key_w_v1967
    %t1968 = load i64, i64* %key_w_v1967
    %t1969 = call i64 @freak_llvm_word_to_int(i64 %t1968)
    %key_v1970 = alloca i64
    store i64 %t1969, i64* %key_v1970
    %t1971 = load i64, i64* %si_v1955
    %t1972 = sub i64 %t1971, 1
    %sj_v1973 = alloca i64
    store i64 %t1972, i64* %sj_v1973
    %sorted_v1974 = alloca i64
    store i64 0, i64* %sorted_v1974
    br label %loop.cond.1975
loop.cond.1975:
    %t1978 = load i64, i64* %sj_v1973
    %t1980 = icmp slt i64 %t1978, 0
    %t1979 = zext i1 %t1980 to i64
    %t1981 = load i64, i64* %sorted_v1974
    %t1983 = icmp ne i64 %t1979, 0
    %t1984 = icmp ne i64 %t1981, 0
    %t1985 = or i1 %t1983, %t1984
    %t1982 = zext i1 %t1985 to i64
    %t1986 = icmp eq i64 %t1982, 0
    br i1 %t1986, label %loop.body.1976, label %loop.end.1977
loop.body.1976:
    %t1987 = load i64, i64* %handle
    %t1988 = load i64, i64* %sj_v1973
    %t1989 = call i64 @freak_llvm_array_get(i64 %t1987, i64 %t1988)
    %cw_v1990 = alloca i64
    store i64 %t1989, i64* %cw_v1990
    %t1991 = load i64, i64* %cw_v1990
    %t1992 = call i64 @freak_llvm_word_to_int(i64 %t1991)
    %cv_v1993 = alloca i64
    store i64 %t1992, i64* %cv_v1993
    %t1994 = load i64, i64* %cv_v1993
    %t1995 = load i64, i64* %key_v1970
    %t1997 = icmp sgt i64 %t1994, %t1995
    %t1996 = zext i1 %t1997 to i64
    %t2001 = icmp ne i64 %t1996, 0
    br i1 %t2001, label %if.then.1998, label %if.else.1999
if.then.1998:
    %t2002 = load i64, i64* %handle
    %t2003 = load i64, i64* %sj_v1973
    %t2004 = add i64 %t2003, 1
    %t2005 = load i64, i64* %cw_v1990
    call void @freak_llvm_array_set(i64 %t2002, i64 %t2004, i64 %t2005)
    %t2006 = load i64, i64* %sj_v1973
    %t2007 = sub i64 %t2006, 1
    store i64 %t2007, i64* %sj_v1973
    br label %if.end.2000
if.else.1999:
    store i64 1, i64* %sorted_v1974
    br label %if.end.2000
if.end.2000:
    br label %loop.cond.1975
loop.end.1977:
    %t2008 = load i64, i64* %handle
    %t2009 = load i64, i64* %sj_v1973
    %t2010 = add i64 %t2009, 1
    %t2011 = load i64, i64* %key_v1970
    %t2012 = call i64 @freak_llvm_word_from_int(i64 %t2011)
    call void @freak_llvm_array_set(i64 %t2008, i64 %t2010, i64 %t2012)
    %t2013 = load i64, i64* %si_v1955
    %t2014 = add i64 %t2013, 1
    store i64 %t2014, i64* %si_v1955
    br label %loop.cond.1956
loop.end.1958:
    ret void
}

define void @freak_array_sort_word(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2015 = load i64, i64* %handle
    %t2016 = call i64 @freak_llvm_array_len(i64 %t2015)
    %alen_v2017 = alloca i64
    store i64 %t2016, i64* %alen_v2017
    %t2018 = load i64, i64* %alen_v2017
    %t2020 = icmp sle i64 %t2018, 1
    %t2019 = zext i1 %t2020 to i64
    %t2024 = icmp ne i64 %t2019, 0
    br i1 %t2024, label %if.then.2021, label %if.end.2023
if.then.2021:
    ret void
    br label %if.end.2023
if.end.2023:
    %si_v2025 = alloca i64
    store i64 1, i64* %si_v2025
    br label %loop.cond.2026
loop.cond.2026:
    %t2029 = load i64, i64* %si_v2025
    %t2030 = load i64, i64* %alen_v2017
    %t2032 = icmp sge i64 %t2029, %t2030
    %t2031 = zext i1 %t2032 to i64
    %t2033 = icmp eq i64 %t2031, 0
    br i1 %t2033, label %loop.body.2027, label %loop.end.2028
loop.body.2027:
    %t2034 = load i64, i64* %handle
    %t2035 = load i64, i64* %si_v2025
    %t2036 = call i64 @freak_llvm_array_get(i64 %t2034, i64 %t2035)
    %key_w_v2037 = alloca i64
    store i64 %t2036, i64* %key_w_v2037
    %t2038 = load i64, i64* %si_v2025
    %t2039 = sub i64 %t2038, 1
    %sj_v2040 = alloca i64
    store i64 %t2039, i64* %sj_v2040
    %sorted_v2041 = alloca i64
    store i64 0, i64* %sorted_v2041
    br label %loop.cond.2042
loop.cond.2042:
    %t2045 = load i64, i64* %sj_v2040
    %t2047 = icmp slt i64 %t2045, 0
    %t2046 = zext i1 %t2047 to i64
    %t2048 = load i64, i64* %sorted_v2041
    %t2050 = icmp ne i64 %t2046, 0
    %t2051 = icmp ne i64 %t2048, 0
    %t2052 = or i1 %t2050, %t2051
    %t2049 = zext i1 %t2052 to i64
    %t2053 = icmp eq i64 %t2049, 0
    br i1 %t2053, label %loop.body.2043, label %loop.end.2044
loop.body.2043:
    %t2054 = load i64, i64* %handle
    %t2055 = load i64, i64* %sj_v2040
    %t2056 = call i64 @freak_llvm_array_get(i64 %t2054, i64 %t2055)
    %cw_v2057 = alloca i64
    store i64 %t2056, i64* %cw_v2057
    %t2058 = load i64, i64* %cw_v2057
    %t2059 = load i64, i64* %key_w_v2037
    %t2060 = call i64 @freak_word_compare(i64 %t2058, i64 %t2059)
    %t2062 = icmp sgt i64 %t2060, 0
    %t2061 = zext i1 %t2062 to i64
    %t2066 = icmp ne i64 %t2061, 0
    br i1 %t2066, label %if.then.2063, label %if.else.2064
if.then.2063:
    %t2067 = load i64, i64* %handle
    %t2068 = load i64, i64* %sj_v2040
    %t2069 = add i64 %t2068, 1
    %t2070 = load i64, i64* %cw_v2057
    call void @freak_llvm_array_set(i64 %t2067, i64 %t2069, i64 %t2070)
    %t2071 = load i64, i64* %sj_v2040
    %t2072 = sub i64 %t2071, 1
    store i64 %t2072, i64* %sj_v2040
    br label %if.end.2065
if.else.2064:
    store i64 1, i64* %sorted_v2041
    br label %if.end.2065
if.end.2065:
    br label %loop.cond.2042
loop.end.2044:
    %t2073 = load i64, i64* %handle
    %t2074 = load i64, i64* %sj_v2040
    %t2075 = add i64 %t2074, 1
    %t2076 = load i64, i64* %key_w_v2037
    call void @freak_llvm_array_set(i64 %t2073, i64 %t2075, i64 %t2076)
    %t2077 = load i64, i64* %si_v2025
    %t2078 = add i64 %t2077, 1
    store i64 %t2078, i64* %si_v2025
    br label %loop.cond.2026
loop.end.2028:
    ret void
}

define i64 @freak_array_binary_search_int(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %lo_v2079 = alloca i64
    store i64 0, i64* %lo_v2079
    %t2080 = load i64, i64* %handle
    %t2081 = call i64 @freak_llvm_array_len(i64 %t2080)
    %t2082 = sub i64 %t2081, 1
    %hi_v2083 = alloca i64
    store i64 %t2082, i64* %hi_v2083
    br label %loop.cond.2084
loop.cond.2084:
    %t2087 = load i64, i64* %lo_v2079
    %t2088 = load i64, i64* %hi_v2083
    %t2090 = icmp sgt i64 %t2087, %t2088
    %t2089 = zext i1 %t2090 to i64
    %t2091 = icmp eq i64 %t2089, 0
    br i1 %t2091, label %loop.body.2085, label %loop.end.2086
loop.body.2085:
    %t2092 = load i64, i64* %hi_v2083
    %t2093 = load i64, i64* %lo_v2079
    %t2094 = sub i64 %t2092, %t2093
    %range_v2095 = alloca i64
    store i64 %t2094, i64* %range_v2095
    %t2096 = load i64, i64* %range_v2095
    %t2097 = sdiv i64 %t2096, 2
    %half_v2098 = alloca i64
    store i64 %t2097, i64* %half_v2098
    %t2099 = load i64, i64* %lo_v2079
    %t2100 = load i64, i64* %half_v2098
    %t2101 = add i64 %t2099, %t2100
    %mid_v2102 = alloca i64
    store i64 %t2101, i64* %mid_v2102
    %t2103 = load i64, i64* %handle
    %t2104 = load i64, i64* %mid_v2102
    %t2105 = call i64 @freak_llvm_array_get(i64 %t2103, i64 %t2104)
    %mw_v2106 = alloca i64
    store i64 %t2105, i64* %mw_v2106
    %t2107 = load i64, i64* %mw_v2106
    %t2108 = call i64 @freak_llvm_word_to_int(i64 %t2107)
    %mv_v2109 = alloca i64
    store i64 %t2108, i64* %mv_v2109
    %t2110 = load i64, i64* %mv_v2109
    %t2111 = load i64, i64* %target
    %t2113 = icmp eq i64 %t2110, %t2111
    %t2112 = zext i1 %t2113 to i64
    %t2117 = icmp ne i64 %t2112, 0
    br i1 %t2117, label %if.then.2114, label %if.end.2116
if.then.2114:
    %t2118 = load i64, i64* %mid_v2102
    ret i64 %t2118
    br label %if.end.2116
if.end.2116:
    %t2119 = load i64, i64* %mv_v2109
    %t2120 = load i64, i64* %target
    %t2122 = icmp slt i64 %t2119, %t2120
    %t2121 = zext i1 %t2122 to i64
    %t2126 = icmp ne i64 %t2121, 0
    br i1 %t2126, label %if.then.2123, label %if.else.2124
if.then.2123:
    %t2127 = load i64, i64* %mid_v2102
    %t2128 = add i64 %t2127, 1
    store i64 %t2128, i64* %lo_v2079
    br label %if.end.2125
if.else.2124:
    %t2129 = load i64, i64* %mid_v2102
    %t2130 = sub i64 %t2129, 1
    store i64 %t2130, i64* %hi_v2083
    br label %if.end.2125
if.end.2125:
    br label %loop.cond.2084
loop.end.2086:
    %t2131 = sub i64 0, 1
    ret i64 %t2131
    ret i64 0
}

define i64 @freak_array_find(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2132 = load i64, i64* %handle
    %t2133 = call i64 @freak_llvm_array_len(i64 %t2132)
    %alen_v2134 = alloca i64
    store i64 %t2133, i64* %alen_v2134
    %fi_v2135 = alloca i64
    store i64 0, i64* %fi_v2135
    %t2141 = load i64, i64* %alen_v2134
    %rep.2140 = alloca i64
    store i64 0, i64* %rep.2140
    br label %loop.cond.2136
loop.cond.2136:
    %t2142 = load i64, i64* %rep.2140
    %t2143 = icmp slt i64 %t2142, %t2141
    br i1 %t2143, label %loop.body.2137, label %loop.end.2138
loop.body.2137:
    %t2144 = load i64, i64* %handle
    %t2145 = load i64, i64* %fi_v2135
    %t2146 = call i64 @freak_llvm_array_get(i64 %t2144, i64 %t2145)
    %fw_v2147 = alloca i64
    store i64 %t2146, i64* %fw_v2147
    %t2148 = load i64, i64* %fw_v2147
    %t2149 = load i64, i64* %target
    %t2150 = call i64 @freak_llvm_word_eq(i64 %t2148, i64 %t2149)
    %t2154 = icmp ne i64 %t2150, 0
    br i1 %t2154, label %if.then.2151, label %if.end.2153
if.then.2151:
    %t2155 = load i64, i64* %fi_v2135
    ret i64 %t2155
    br label %if.end.2153
if.end.2153:
    %t2156 = load i64, i64* %fi_v2135
    %t2157 = add i64 %t2156, 1
    store i64 %t2157, i64* %fi_v2135
    br label %loop.inc.2139
loop.inc.2139:
    %t2158 = load i64, i64* %rep.2140
    %t2159 = add i64 %t2158, 1
    store i64 %t2159, i64* %rep.2140
    br label %loop.cond.2136
loop.end.2138:
    %t2160 = sub i64 0, 1
    ret i64 %t2160
    ret i64 0
}

define i64 @freak_array_contains(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2161 = load i64, i64* %handle
    %t2162 = load i64, i64* %target
    %t2163 = call i64 @freak_array_find(i64 %t2161, i64 %t2162)
    %t2165 = icmp sge i64 %t2163, 0
    %t2164 = zext i1 %t2165 to i64
    ret i64 %t2164
    ret i64 0
}

define void @freak_array_reverse(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2166 = load i64, i64* %handle
    %t2167 = call i64 @freak_llvm_array_len(i64 %t2166)
    %alen_v2168 = alloca i64
    store i64 %t2167, i64* %alen_v2168
    %t2169 = load i64, i64* %alen_v2168
    %t2171 = icmp sle i64 %t2169, 1
    %t2170 = zext i1 %t2171 to i64
    %t2175 = icmp ne i64 %t2170, 0
    br i1 %t2175, label %if.then.2172, label %if.end.2174
if.then.2172:
    ret void
    br label %if.end.2174
if.end.2174:
    %lo_v2176 = alloca i64
    store i64 0, i64* %lo_v2176
    %t2177 = load i64, i64* %alen_v2168
    %t2178 = sub i64 %t2177, 1
    %hi_v2179 = alloca i64
    store i64 %t2178, i64* %hi_v2179
    br label %loop.cond.2180
loop.cond.2180:
    %t2183 = load i64, i64* %lo_v2176
    %t2184 = load i64, i64* %hi_v2179
    %t2186 = icmp sge i64 %t2183, %t2184
    %t2185 = zext i1 %t2186 to i64
    %t2187 = icmp eq i64 %t2185, 0
    br i1 %t2187, label %loop.body.2181, label %loop.end.2182
loop.body.2181:
    %t2188 = load i64, i64* %handle
    %t2189 = load i64, i64* %lo_v2176
    %t2190 = call i64 @freak_llvm_array_get(i64 %t2188, i64 %t2189)
    %tmp_v2191 = alloca i64
    store i64 %t2190, i64* %tmp_v2191
    %t2192 = load i64, i64* %handle
    %t2193 = load i64, i64* %hi_v2179
    %t2194 = call i64 @freak_llvm_array_get(i64 %t2192, i64 %t2193)
    %hw_v2195 = alloca i64
    store i64 %t2194, i64* %hw_v2195
    %t2196 = load i64, i64* %handle
    %t2197 = load i64, i64* %lo_v2176
    %t2198 = load i64, i64* %hw_v2195
    call void @freak_llvm_array_set(i64 %t2196, i64 %t2197, i64 %t2198)
    %t2199 = load i64, i64* %handle
    %t2200 = load i64, i64* %hi_v2179
    %t2201 = load i64, i64* %tmp_v2191
    call void @freak_llvm_array_set(i64 %t2199, i64 %t2200, i64 %t2201)
    %t2202 = load i64, i64* %lo_v2176
    %t2203 = add i64 %t2202, 1
    store i64 %t2203, i64* %lo_v2176
    %t2204 = load i64, i64* %hi_v2179
    %t2205 = sub i64 %t2204, 1
    store i64 %t2205, i64* %hi_v2179
    br label %loop.cond.2180
loop.end.2182:
    ret void
}

define i64 @freak_array_copy(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2206 = call i64 @freak_llvm_array_new()
    %new_arr_v2207 = alloca i64
    store i64 %t2206, i64* %new_arr_v2207
    %t2208 = load i64, i64* %handle
    %t2209 = call i64 @freak_llvm_array_len(i64 %t2208)
    %alen_v2210 = alloca i64
    store i64 %t2209, i64* %alen_v2210
    %ci_v2211 = alloca i64
    store i64 0, i64* %ci_v2211
    %t2217 = load i64, i64* %alen_v2210
    %rep.2216 = alloca i64
    store i64 0, i64* %rep.2216
    br label %loop.cond.2212
loop.cond.2212:
    %t2218 = load i64, i64* %rep.2216
    %t2219 = icmp slt i64 %t2218, %t2217
    br i1 %t2219, label %loop.body.2213, label %loop.end.2214
loop.body.2213:
    %t2220 = load i64, i64* %handle
    %t2221 = load i64, i64* %ci_v2211
    %t2222 = call i64 @freak_llvm_array_get(i64 %t2220, i64 %t2221)
    %cw_v2223 = alloca i64
    store i64 %t2222, i64* %cw_v2223
    %t2224 = load i64, i64* %new_arr_v2207
    %t2225 = load i64, i64* %cw_v2223
    call void @freak_llvm_array_push(i64 %t2224, i64 %t2225)
    %t2226 = load i64, i64* %ci_v2211
    %t2227 = add i64 %t2226, 1
    store i64 %t2227, i64* %ci_v2211
    br label %loop.inc.2215
loop.inc.2215:
    %t2228 = load i64, i64* %rep.2216
    %t2229 = add i64 %t2228, 1
    store i64 %t2229, i64* %rep.2216
    br label %loop.cond.2212
loop.end.2214:
    %t2230 = load i64, i64* %new_arr_v2207
    ret i64 %t2230
    ret i64 0
}

define i64 @freak_array_join(i64 %arg_handle, i64 %arg_sep) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %sep = alloca i64
    store i64 %arg_sep, i64* %sep
    %t2231 = load i64, i64* %handle
    %t2232 = call i64 @freak_llvm_array_len(i64 %t2231)
    %alen_v2233 = alloca i64
    store i64 %t2232, i64* %alen_v2233
    %t2234 = load i64, i64* %alen_v2233
    %t2236 = icmp eq i64 %t2234, 0
    %t2235 = zext i1 %t2236 to i64
    %t2240 = icmp ne i64 %t2235, 0
    br i1 %t2240, label %if.then.2237, label %if.end.2239
if.then.2237:
    %t2241 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.119, i64 0, i64 0
    %t2242 = ptrtoint i8* %t2241 to i64
    ret i64 %t2242
    br label %if.end.2239
if.end.2239:
    %t2243 = load i64, i64* %handle
    %t2244 = call i64 @freak_llvm_array_get(i64 %t2243, i64 0)
    %aj_out_v2245 = alloca i64
    store i64 %t2244, i64* %aj_out_v2245
    %ji_v2246 = alloca i64
    store i64 1, i64* %ji_v2246
    br label %loop.cond.2247
loop.cond.2247:
    %t2250 = load i64, i64* %ji_v2246
    %t2251 = load i64, i64* %alen_v2233
    %t2253 = icmp sge i64 %t2250, %t2251
    %t2252 = zext i1 %t2253 to i64
    %t2254 = icmp eq i64 %t2252, 0
    br i1 %t2254, label %loop.body.2248, label %loop.end.2249
loop.body.2248:
    %t2255 = load i64, i64* %handle
    %t2256 = load i64, i64* %ji_v2246
    %t2257 = call i64 @freak_llvm_array_get(i64 %t2255, i64 %t2256)
    %jw_v2258 = alloca i64
    store i64 %t2257, i64* %jw_v2258
    %t2259 = load i64, i64* %aj_out_v2245
    %t2260 = load i64, i64* %sep
    %t2261 = call i64 @freak_llvm_word_concat(i64 %t2259, i64 %t2260)
    %t2262 = load i64, i64* %jw_v2258
    %t2263 = call i64 @freak_llvm_word_concat(i64 %t2261, i64 %t2262)
    store i64 %t2263, i64* %aj_out_v2245
    %t2264 = load i64, i64* %ji_v2246
    %t2265 = add i64 %t2264, 1
    store i64 %t2265, i64* %ji_v2246
    br label %loop.cond.2247
loop.end.2249:
    %t2266 = load i64, i64* %aj_out_v2245
    ret i64 %t2266
    ret i64 0
}

define i64 @freak_array_count(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2267 = load i64, i64* %handle
    %t2268 = call i64 @freak_llvm_array_len(i64 %t2267)
    %alen_v2269 = alloca i64
    store i64 %t2268, i64* %alen_v2269
    %cnt_v2270 = alloca i64
    store i64 0, i64* %cnt_v2270
    %ci_v2271 = alloca i64
    store i64 0, i64* %ci_v2271
    %t2277 = load i64, i64* %alen_v2269
    %rep.2276 = alloca i64
    store i64 0, i64* %rep.2276
    br label %loop.cond.2272
loop.cond.2272:
    %t2278 = load i64, i64* %rep.2276
    %t2279 = icmp slt i64 %t2278, %t2277
    br i1 %t2279, label %loop.body.2273, label %loop.end.2274
loop.body.2273:
    %t2280 = load i64, i64* %handle
    %t2281 = load i64, i64* %ci_v2271
    %t2282 = call i64 @freak_llvm_array_get(i64 %t2280, i64 %t2281)
    %cw_v2283 = alloca i64
    store i64 %t2282, i64* %cw_v2283
    %t2284 = load i64, i64* %cw_v2283
    %t2285 = load i64, i64* %target
    %t2286 = call i64 @freak_llvm_word_eq(i64 %t2284, i64 %t2285)
    %t2290 = icmp ne i64 %t2286, 0
    br i1 %t2290, label %if.then.2287, label %if.end.2289
if.then.2287:
    %t2291 = load i64, i64* %cnt_v2270
    %t2292 = add i64 %t2291, 1
    store i64 %t2292, i64* %cnt_v2270
    br label %if.end.2289
if.end.2289:
    %t2293 = load i64, i64* %ci_v2271
    %t2294 = add i64 %t2293, 1
    store i64 %t2294, i64* %ci_v2271
    br label %loop.inc.2275
loop.inc.2275:
    %t2295 = load i64, i64* %rep.2276
    %t2296 = add i64 %t2295, 1
    store i64 %t2296, i64* %rep.2276
    br label %loop.cond.2272
loop.end.2274:
    %t2297 = load i64, i64* %cnt_v2270
    ret i64 %t2297
    ret i64 0
}

define i64 @freak_array_unique(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2298 = load i64, i64* %handle
    %t2299 = call i64 @freak_llvm_array_len(i64 %t2298)
    %alen_v2300 = alloca i64
    store i64 %t2299, i64* %alen_v2300
    %t2301 = load i64, i64* %alen_v2300
    %t2303 = icmp sle i64 %t2301, 1
    %t2302 = zext i1 %t2303 to i64
    %t2307 = icmp ne i64 %t2302, 0
    br i1 %t2307, label %if.then.2304, label %if.end.2306
if.then.2304:
    %t2308 = load i64, i64* %alen_v2300
    ret i64 %t2308
    br label %if.end.2306
if.end.2306:
    %write_idx_v2309 = alloca i64
    store i64 1, i64* %write_idx_v2309
    %ri_v2310 = alloca i64
    store i64 1, i64* %ri_v2310
    br label %loop.cond.2311
loop.cond.2311:
    %t2314 = load i64, i64* %ri_v2310
    %t2315 = load i64, i64* %alen_v2300
    %t2317 = icmp sge i64 %t2314, %t2315
    %t2316 = zext i1 %t2317 to i64
    %t2318 = icmp eq i64 %t2316, 0
    br i1 %t2318, label %loop.body.2312, label %loop.end.2313
loop.body.2312:
    %t2319 = load i64, i64* %handle
    %t2320 = load i64, i64* %ri_v2310
    %t2321 = call i64 @freak_llvm_array_get(i64 %t2319, i64 %t2320)
    %cur_v2322 = alloca i64
    store i64 %t2321, i64* %cur_v2322
    %t2323 = load i64, i64* %handle
    %t2324 = load i64, i64* %ri_v2310
    %t2325 = sub i64 %t2324, 1
    %t2326 = call i64 @freak_llvm_array_get(i64 %t2323, i64 %t2325)
    %prev_v2327 = alloca i64
    store i64 %t2326, i64* %prev_v2327
    %t2328 = load i64, i64* %cur_v2322
    %t2329 = load i64, i64* %prev_v2327
    %t2330 = call i64 @freak_llvm_word_neq(i64 %t2328, i64 %t2329)
    %t2334 = icmp ne i64 %t2330, 0
    br i1 %t2334, label %if.then.2331, label %if.end.2333
if.then.2331:
    %t2335 = load i64, i64* %handle
    %t2336 = load i64, i64* %write_idx_v2309
    %t2337 = load i64, i64* %cur_v2322
    call void @freak_llvm_array_set(i64 %t2335, i64 %t2336, i64 %t2337)
    %t2338 = load i64, i64* %write_idx_v2309
    %t2339 = add i64 %t2338, 1
    store i64 %t2339, i64* %write_idx_v2309
    br label %if.end.2333
if.end.2333:
    %t2340 = load i64, i64* %ri_v2310
    %t2341 = add i64 %t2340, 1
    store i64 %t2341, i64* %ri_v2310
    br label %loop.cond.2311
loop.end.2313:
    %t2342 = load i64, i64* %write_idx_v2309
    ret i64 %t2342
    ret i64 0
}

define i64 @freak_array_sum_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2343 = load i64, i64* %handle
    %t2344 = call i64 @freak_llvm_array_len(i64 %t2343)
    %alen_v2345 = alloca i64
    store i64 %t2344, i64* %alen_v2345
    %total_v2346 = alloca i64
    store i64 0, i64* %total_v2346
    %si_v2347 = alloca i64
    store i64 0, i64* %si_v2347
    %t2353 = load i64, i64* %alen_v2345
    %rep.2352 = alloca i64
    store i64 0, i64* %rep.2352
    br label %loop.cond.2348
loop.cond.2348:
    %t2354 = load i64, i64* %rep.2352
    %t2355 = icmp slt i64 %t2354, %t2353
    br i1 %t2355, label %loop.body.2349, label %loop.end.2350
loop.body.2349:
    %t2356 = load i64, i64* %handle
    %t2357 = load i64, i64* %si_v2347
    %t2358 = call i64 @freak_llvm_array_get(i64 %t2356, i64 %t2357)
    %sw_v2359 = alloca i64
    store i64 %t2358, i64* %sw_v2359
    %t2360 = load i64, i64* %sw_v2359
    %t2361 = call i64 @freak_llvm_word_to_int(i64 %t2360)
    %t2362 = load i64, i64* %total_v2346
    %t2363 = add i64 %t2362, %t2361
    store i64 %t2363, i64* %total_v2346
    %t2364 = load i64, i64* %si_v2347
    %t2365 = add i64 %t2364, 1
    store i64 %t2365, i64* %si_v2347
    br label %loop.inc.2351
loop.inc.2351:
    %t2366 = load i64, i64* %rep.2352
    %t2367 = add i64 %t2366, 1
    store i64 %t2367, i64* %rep.2352
    br label %loop.cond.2348
loop.end.2350:
    %t2368 = load i64, i64* %total_v2346
    ret i64 %t2368
    ret i64 0
}

define i64 @freak_array_max_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2369 = load i64, i64* %handle
    %t2370 = call i64 @freak_llvm_array_len(i64 %t2369)
    %alen_v2371 = alloca i64
    store i64 %t2370, i64* %alen_v2371
    %t2372 = load i64, i64* %alen_v2371
    %t2374 = icmp eq i64 %t2372, 0
    %t2373 = zext i1 %t2374 to i64
    %t2378 = icmp ne i64 %t2373, 0
    br i1 %t2378, label %if.then.2375, label %if.end.2377
if.then.2375:
    ret i64 0
    br label %if.end.2377
if.end.2377:
    %t2379 = load i64, i64* %handle
    %t2380 = call i64 @freak_llvm_array_get(i64 %t2379, i64 0)
    %mw_v2381 = alloca i64
    store i64 %t2380, i64* %mw_v2381
    %t2382 = load i64, i64* %mw_v2381
    %t2383 = call i64 @freak_llvm_word_to_int(i64 %t2382)
    %mx_v2384 = alloca i64
    store i64 %t2383, i64* %mx_v2384
    %mi_v2385 = alloca i64
    store i64 1, i64* %mi_v2385
    br label %loop.cond.2386
loop.cond.2386:
    %t2389 = load i64, i64* %mi_v2385
    %t2390 = load i64, i64* %alen_v2371
    %t2392 = icmp sge i64 %t2389, %t2390
    %t2391 = zext i1 %t2392 to i64
    %t2393 = icmp eq i64 %t2391, 0
    br i1 %t2393, label %loop.body.2387, label %loop.end.2388
loop.body.2387:
    %t2394 = load i64, i64* %handle
    %t2395 = load i64, i64* %mi_v2385
    %t2396 = call i64 @freak_llvm_array_get(i64 %t2394, i64 %t2395)
    %cw_v2397 = alloca i64
    store i64 %t2396, i64* %cw_v2397
    %t2398 = load i64, i64* %cw_v2397
    %t2399 = call i64 @freak_llvm_word_to_int(i64 %t2398)
    %cv_v2400 = alloca i64
    store i64 %t2399, i64* %cv_v2400
    %t2401 = load i64, i64* %cv_v2400
    %t2402 = load i64, i64* %mx_v2384
    %t2404 = icmp sgt i64 %t2401, %t2402
    %t2403 = zext i1 %t2404 to i64
    %t2408 = icmp ne i64 %t2403, 0
    br i1 %t2408, label %if.then.2405, label %if.end.2407
if.then.2405:
    %t2409 = load i64, i64* %cv_v2400
    store i64 %t2409, i64* %mx_v2384
    br label %if.end.2407
if.end.2407:
    %t2410 = load i64, i64* %mi_v2385
    %t2411 = add i64 %t2410, 1
    store i64 %t2411, i64* %mi_v2385
    br label %loop.cond.2386
loop.end.2388:
    %t2412 = load i64, i64* %mx_v2384
    ret i64 %t2412
    ret i64 0
}

define i64 @freak_array_min_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2413 = load i64, i64* %handle
    %t2414 = call i64 @freak_llvm_array_len(i64 %t2413)
    %alen_v2415 = alloca i64
    store i64 %t2414, i64* %alen_v2415
    %t2416 = load i64, i64* %alen_v2415
    %t2418 = icmp eq i64 %t2416, 0
    %t2417 = zext i1 %t2418 to i64
    %t2422 = icmp ne i64 %t2417, 0
    br i1 %t2422, label %if.then.2419, label %if.end.2421
if.then.2419:
    ret i64 0
    br label %if.end.2421
if.end.2421:
    %t2423 = load i64, i64* %handle
    %t2424 = call i64 @freak_llvm_array_get(i64 %t2423, i64 0)
    %mw_v2425 = alloca i64
    store i64 %t2424, i64* %mw_v2425
    %t2426 = load i64, i64* %mw_v2425
    %t2427 = call i64 @freak_llvm_word_to_int(i64 %t2426)
    %mn_v2428 = alloca i64
    store i64 %t2427, i64* %mn_v2428
    %mi_v2429 = alloca i64
    store i64 1, i64* %mi_v2429
    br label %loop.cond.2430
loop.cond.2430:
    %t2433 = load i64, i64* %mi_v2429
    %t2434 = load i64, i64* %alen_v2415
    %t2436 = icmp sge i64 %t2433, %t2434
    %t2435 = zext i1 %t2436 to i64
    %t2437 = icmp eq i64 %t2435, 0
    br i1 %t2437, label %loop.body.2431, label %loop.end.2432
loop.body.2431:
    %t2438 = load i64, i64* %handle
    %t2439 = load i64, i64* %mi_v2429
    %t2440 = call i64 @freak_llvm_array_get(i64 %t2438, i64 %t2439)
    %cw_v2441 = alloca i64
    store i64 %t2440, i64* %cw_v2441
    %t2442 = load i64, i64* %cw_v2441
    %t2443 = call i64 @freak_llvm_word_to_int(i64 %t2442)
    %cv_v2444 = alloca i64
    store i64 %t2443, i64* %cv_v2444
    %t2445 = load i64, i64* %cv_v2444
    %t2446 = load i64, i64* %mn_v2428
    %t2448 = icmp slt i64 %t2445, %t2446
    %t2447 = zext i1 %t2448 to i64
    %t2452 = icmp ne i64 %t2447, 0
    br i1 %t2452, label %if.then.2449, label %if.end.2451
if.then.2449:
    %t2453 = load i64, i64* %cv_v2444
    store i64 %t2453, i64* %mn_v2428
    br label %if.end.2451
if.end.2451:
    %t2454 = load i64, i64* %mi_v2429
    %t2455 = add i64 %t2454, 1
    store i64 %t2455, i64* %mi_v2429
    br label %loop.cond.2430
loop.end.2432:
    %t2456 = load i64, i64* %mn_v2428
    ret i64 %t2456
    ret i64 0
}

define void @freak_json_init() {
entry:
    %t2457 = load i64, i64* @g_json_inited
    %t2459 = icmp eq i64 %t2457, 0
    %t2458 = zext i1 %t2459 to i64
    %t2463 = icmp ne i64 %t2458, 0
    br i1 %t2463, label %if.then.2460, label %if.end.2462
if.then.2460:
    %t2464 = call i64 @freak_llvm_array_new()
    store i64 %t2464, i64* @g_json_types
    %t2465 = call i64 @freak_llvm_array_new()
    store i64 %t2465, i64* @g_json_vals
    %t2466 = call i64 @freak_llvm_array_new()
    store i64 %t2466, i64* @g_json_children
    %t2467 = call i64 @freak_llvm_array_new()
    store i64 %t2467, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 1, i64* @g_json_inited
    br label %if.end.2462
if.end.2462:
    ret void
}

define i64 @freak_json_alloc(i64 %arg_jtype, i64 %arg_jval) {
entry:
    %jtype = alloca i64
    store i64 %arg_jtype, i64* %jtype
    %jval = alloca i64
    store i64 %arg_jval, i64* %jval
    %t2468 = load i64, i64* @g_json_count
    %idx_v2469 = alloca i64
    store i64 %t2468, i64* %idx_v2469
    %t2470 = load i64, i64* @g_json_types
    %t2471 = load i64, i64* %jtype
    call void @freak_llvm_array_push(i64 %t2470, i64 %t2471)
    %t2472 = load i64, i64* @g_json_vals
    %t2473 = load i64, i64* %jval
    call void @freak_llvm_array_push(i64 %t2472, i64 %t2473)
    %t2474 = load i64, i64* @g_json_children
    %t2475 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2474, i64 %t2475)
    %t2476 = load i64, i64* @g_json_keys
    %t2477 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2476, i64 %t2477)
    %t2478 = load i64, i64* @g_json_count
    %t2479 = add i64 %t2478, 1
    store i64 %t2479, i64* @g_json_count
    %t2480 = load i64, i64* %idx_v2469
    ret i64 %t2480
    ret i64 0
}

define i64 @freak_json_get_type(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2481 = load i64, i64* @g_json_types
    %t2482 = load i64, i64* %handle
    %t2483 = call i64 @freak_llvm_array_get(i64 %t2481, i64 %t2482)
    ret i64 %t2483
    ret i64 0
}

define i64 @freak_json_get_str(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2484 = load i64, i64* @g_json_vals
    %t2485 = load i64, i64* %handle
    %t2486 = call i64 @freak_llvm_array_get(i64 %t2484, i64 %t2485)
    ret i64 %t2486
    ret i64 0
}

define i64 @freak_json_get_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2487 = load i64, i64* @g_json_vals
    %t2488 = load i64, i64* %handle
    %t2489 = call i64 @freak_llvm_array_get(i64 %t2487, i64 %t2488)
    %v_v2490 = alloca i64
    store i64 %t2489, i64* %v_v2490
    %t2491 = load i64, i64* %v_v2490
    %t2492 = call i64 @freak_llvm_word_to_int(i64 %t2491)
    ret i64 %t2492
    ret i64 0
}

define i64 @freak_json_get_bool(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2493 = load i64, i64* @g_json_vals
    %t2494 = load i64, i64* %handle
    %t2495 = call i64 @freak_llvm_array_get(i64 %t2493, i64 %t2494)
    %v_v2496 = alloca i64
    store i64 %t2495, i64* %v_v2496
    %t2497 = load i64, i64* %v_v2496
    %t2498 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.120, i64 0, i64 0
    %t2499 = ptrtoint i8* %t2498 to i64
    %t2500 = call i64 @freak_llvm_word_eq(i64 %t2497, i64 %t2499)
    ret i64 %t2500
    ret i64 0
}

define i64 @freak_json_is_null(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2501 = load i64, i64* @g_json_types
    %t2502 = load i64, i64* %handle
    %t2503 = call i64 @freak_llvm_array_get(i64 %t2501, i64 %t2502)
    %t_v2504 = alloca i64
    store i64 %t2503, i64* %t_v2504
    %t2505 = load i64, i64* %t_v2504
    %t2506 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.121, i64 0, i64 0
    %t2507 = ptrtoint i8* %t2506 to i64
    %t2508 = call i64 @freak_llvm_word_eq(i64 %t2505, i64 %t2507)
    ret i64 %t2508
    ret i64 0
}

define i64 @freak_json_arr_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2509 = load i64, i64* @g_json_children
    %t2510 = load i64, i64* %handle
    %t2511 = call i64 @freak_llvm_array_get(i64 %t2509, i64 %t2510)
    %ch_v2512 = alloca i64
    store i64 %t2511, i64* %ch_v2512
    %t2513 = load i64, i64* %ch_v2512
    %t2514 = call i64 @freak_llvm_word_to_int(i64 %t2513)
    %ch_handle_v2515 = alloca i64
    store i64 %t2514, i64* %ch_handle_v2515
    %t2516 = load i64, i64* %ch_handle_v2515
    %t2517 = call i64 @freak_llvm_array_len(i64 %t2516)
    ret i64 %t2517
    ret i64 0
}

define i64 @freak_json_arr_get(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2518 = load i64, i64* @g_json_children
    %t2519 = load i64, i64* %handle
    %t2520 = call i64 @freak_llvm_array_get(i64 %t2518, i64 %t2519)
    %ch_v2521 = alloca i64
    store i64 %t2520, i64* %ch_v2521
    %t2522 = load i64, i64* %ch_v2521
    %t2523 = call i64 @freak_llvm_word_to_int(i64 %t2522)
    %ch_handle_v2524 = alloca i64
    store i64 %t2523, i64* %ch_handle_v2524
    %t2525 = load i64, i64* %ch_handle_v2524
    %t2526 = load i64, i64* %index
    %t2527 = call i64 @freak_llvm_array_get(i64 %t2525, i64 %t2526)
    %val_w_v2528 = alloca i64
    store i64 %t2527, i64* %val_w_v2528
    %t2529 = load i64, i64* %val_w_v2528
    %t2530 = call i64 @freak_llvm_word_to_int(i64 %t2529)
    ret i64 %t2530
    ret i64 0
}

define i64 @freak_json_obj_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2531 = load i64, i64* @g_json_keys
    %t2532 = load i64, i64* %handle
    %t2533 = call i64 @freak_llvm_array_get(i64 %t2531, i64 %t2532)
    %ks_v2534 = alloca i64
    store i64 %t2533, i64* %ks_v2534
    %t2535 = load i64, i64* %ks_v2534
    %t2536 = call i64 @freak_llvm_word_to_int(i64 %t2535)
    %ks_handle_v2537 = alloca i64
    store i64 %t2536, i64* %ks_handle_v2537
    %t2538 = load i64, i64* %ks_handle_v2537
    %t2539 = call i64 @freak_llvm_array_len(i64 %t2538)
    ret i64 %t2539
    ret i64 0
}

define i64 @freak_json_obj_get(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2540 = load i64, i64* @g_json_keys
    %t2541 = load i64, i64* %handle
    %t2542 = call i64 @freak_llvm_array_get(i64 %t2540, i64 %t2541)
    %ks_v2543 = alloca i64
    store i64 %t2542, i64* %ks_v2543
    %t2544 = load i64, i64* %ks_v2543
    %t2545 = call i64 @freak_llvm_word_to_int(i64 %t2544)
    %ks_handle_v2546 = alloca i64
    store i64 %t2545, i64* %ks_handle_v2546
    %t2547 = load i64, i64* @g_json_children
    %t2548 = load i64, i64* %handle
    %t2549 = call i64 @freak_llvm_array_get(i64 %t2547, i64 %t2548)
    %ch_v2550 = alloca i64
    store i64 %t2549, i64* %ch_v2550
    %t2551 = load i64, i64* %ch_v2550
    %t2552 = call i64 @freak_llvm_word_to_int(i64 %t2551)
    %ch_handle_v2553 = alloca i64
    store i64 %t2552, i64* %ch_handle_v2553
    %t2554 = load i64, i64* %ks_handle_v2546
    %t2555 = call i64 @freak_llvm_array_len(i64 %t2554)
    %klen_v2556 = alloca i64
    store i64 %t2555, i64* %klen_v2556
    %ki_v2557 = alloca i64
    store i64 0, i64* %ki_v2557
    %t2563 = load i64, i64* %klen_v2556
    %rep.2562 = alloca i64
    store i64 0, i64* %rep.2562
    br label %loop.cond.2558
loop.cond.2558:
    %t2564 = load i64, i64* %rep.2562
    %t2565 = icmp slt i64 %t2564, %t2563
    br i1 %t2565, label %loop.body.2559, label %loop.end.2560
loop.body.2559:
    %t2566 = load i64, i64* %ks_handle_v2546
    %t2567 = load i64, i64* %ki_v2557
    %t2568 = call i64 @freak_llvm_array_get(i64 %t2566, i64 %t2567)
    %k_v2569 = alloca i64
    store i64 %t2568, i64* %k_v2569
    %t2570 = load i64, i64* %k_v2569
    %t2571 = load i64, i64* %key
    %t2572 = call i64 @freak_llvm_word_eq(i64 %t2570, i64 %t2571)
    %t2576 = icmp ne i64 %t2572, 0
    br i1 %t2576, label %if.then.2573, label %if.end.2575
if.then.2573:
    %t2577 = load i64, i64* %ch_handle_v2553
    %t2578 = load i64, i64* %ki_v2557
    %t2579 = call i64 @freak_llvm_array_get(i64 %t2577, i64 %t2578)
    %v_v2580 = alloca i64
    store i64 %t2579, i64* %v_v2580
    %t2581 = load i64, i64* %v_v2580
    %t2582 = call i64 @freak_llvm_word_to_int(i64 %t2581)
    ret i64 %t2582
    br label %if.end.2575
if.end.2575:
    %t2583 = load i64, i64* %ki_v2557
    %t2584 = add i64 %t2583, 1
    store i64 %t2584, i64* %ki_v2557
    br label %loop.inc.2561
loop.inc.2561:
    %t2585 = load i64, i64* %rep.2562
    %t2586 = add i64 %t2585, 1
    store i64 %t2586, i64* %rep.2562
    br label %loop.cond.2558
loop.end.2560:
    %t2587 = sub i64 0, 1
    ret i64 %t2587
    ret i64 0
}

define i64 @freak_json_obj_has(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2588 = load i64, i64* %handle
    %t2589 = load i64, i64* %key
    %t2590 = call i64 @freak_json_obj_get(i64 %t2588, i64 %t2589)
    %t2592 = icmp sge i64 %t2590, 0
    %t2591 = zext i1 %t2592 to i64
    ret i64 %t2591
    ret i64 0
}

define i64 @freak_json_obj_key_at(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2593 = load i64, i64* @g_json_keys
    %t2594 = load i64, i64* %handle
    %t2595 = call i64 @freak_llvm_array_get(i64 %t2593, i64 %t2594)
    %ks_v2596 = alloca i64
    store i64 %t2595, i64* %ks_v2596
    %t2597 = load i64, i64* %ks_v2596
    %t2598 = call i64 @freak_llvm_word_to_int(i64 %t2597)
    %ks_handle_v2599 = alloca i64
    store i64 %t2598, i64* %ks_handle_v2599
    %t2600 = load i64, i64* %ks_handle_v2599
    %t2601 = load i64, i64* %index
    %t2602 = call i64 @freak_llvm_array_get(i64 %t2600, i64 %t2601)
    ret i64 %t2602
    ret i64 0
}

define i64 @freak_json_cur() {
entry:
    %t2603 = load i64, i64* @g_json_pos
    %t2604 = load i64, i64* @g_json_len
    %t2606 = icmp sge i64 %t2603, %t2604
    %t2605 = zext i1 %t2606 to i64
    %t2610 = icmp ne i64 %t2605, 0
    br i1 %t2610, label %if.then.2607, label %if.end.2609
if.then.2607:
    %t2611 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.122, i64 0, i64 0
    %t2612 = ptrtoint i8* %t2611 to i64
    ret i64 %t2612
    br label %if.end.2609
if.end.2609:
    %t2613 = load i64, i64* @g_json_src
    %t2615 = load i64, i64* @g_json_pos
    %t2614 = call i64 @freak_llvm_word_char_at(i64 %t2613, i64 %t2615)
    ret i64 %t2614
    ret i64 0
}

define i64 @freak_json_advance() {
entry:
    %t2616 = call i64 @freak_json_cur()
    %c_v2617 = alloca i64
    store i64 %t2616, i64* %c_v2617
    %t2618 = load i64, i64* @g_json_pos
    %t2619 = add i64 %t2618, 1
    store i64 %t2619, i64* @g_json_pos
    %t2620 = load i64, i64* %c_v2617
    ret i64 %t2620
    ret i64 0
}

define void @freak_json_skip_ws() {
entry:
    br label %loop.cond.2621
loop.cond.2621:
    %t2624 = load i64, i64* @g_json_pos
    %t2625 = load i64, i64* @g_json_len
    %t2627 = icmp sge i64 %t2624, %t2625
    %t2626 = zext i1 %t2627 to i64
    %t2628 = icmp eq i64 %t2626, 0
    br i1 %t2628, label %loop.body.2622, label %loop.end.2623
loop.body.2622:
    %t2629 = call i64 @freak_json_cur()
    %c_v2630 = alloca i64
    store i64 %t2629, i64* %c_v2630
    %t2631 = load i64, i64* %c_v2630
    %t2632 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.123, i64 0, i64 0
    %t2633 = ptrtoint i8* %t2632 to i64
    %t2634 = call i64 @freak_llvm_word_neq(i64 %t2631, i64 %t2633)
    %t2635 = load i64, i64* %c_v2630
    %t2636 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.124, i64 0, i64 0
    %t2637 = ptrtoint i8* %t2636 to i64
    %t2638 = call i64 @freak_llvm_word_neq(i64 %t2635, i64 %t2637)
    %t2640 = icmp ne i64 %t2634, 0
    %t2641 = icmp ne i64 %t2638, 0
    %t2642 = and i1 %t2640, %t2641
    %t2639 = zext i1 %t2642 to i64
    %t2643 = load i64, i64* %c_v2630
    %t2644 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.125, i64 0, i64 0
    %t2645 = ptrtoint i8* %t2644 to i64
    %t2646 = call i64 @freak_llvm_word_neq(i64 %t2643, i64 %t2645)
    %t2648 = icmp ne i64 %t2639, 0
    %t2649 = icmp ne i64 %t2646, 0
    %t2650 = and i1 %t2648, %t2649
    %t2647 = zext i1 %t2650 to i64
    %t2651 = load i64, i64* %c_v2630
    %t2652 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.126, i64 0, i64 0
    %t2653 = ptrtoint i8* %t2652 to i64
    %t2654 = call i64 @freak_llvm_word_neq(i64 %t2651, i64 %t2653)
    %t2656 = icmp ne i64 %t2647, 0
    %t2657 = icmp ne i64 %t2654, 0
    %t2658 = and i1 %t2656, %t2657
    %t2655 = zext i1 %t2658 to i64
    %t2662 = icmp ne i64 %t2655, 0
    br i1 %t2662, label %if.then.2659, label %if.end.2661
if.then.2659:
    ret void
    br label %if.end.2661
if.end.2661:
    %t2663 = load i64, i64* @g_json_pos
    %t2664 = add i64 %t2663, 1
    store i64 %t2664, i64* @g_json_pos
    br label %loop.cond.2621
loop.end.2623:
    ret void
}

define void @freak_json_expect(i64 %arg_ch) {
entry:
    %ch = alloca i64
    store i64 %arg_ch, i64* %ch
    %t2665 = call i64 @freak_json_advance()
    %c_v2666 = alloca i64
    store i64 %t2665, i64* %c_v2666
    %t2667 = load i64, i64* %c_v2666
    %t2668 = load i64, i64* %ch
    %t2669 = call i64 @freak_llvm_word_neq(i64 %t2667, i64 %t2668)
    %t2673 = icmp ne i64 %t2669, 0
    br i1 %t2673, label %if.then.2670, label %if.end.2672
if.then.2670:
    %t2674 = getelementptr inbounds [29 x i8], [29 x i8]* @.str.127, i64 0, i64 0
    %t2675 = ptrtoint i8* %t2674 to i64
    %t2676 = load i64, i64* %ch
    %t2677 = call i64 @freak_llvm_word_concat(i64 %t2675, i64 %t2676)
    %t2678 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.128, i64 0, i64 0
    %t2679 = ptrtoint i8* %t2678 to i64
    %t2680 = call i64 @freak_llvm_word_concat(i64 %t2677, i64 %t2679)
    %t2681 = load i64, i64* %c_v2666
    %t2682 = call i64 @freak_llvm_word_concat(i64 %t2680, i64 %t2681)
    %t2683 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.129, i64 0, i64 0
    %t2684 = ptrtoint i8* %t2683 to i64
    %t2685 = call i64 @freak_llvm_word_concat(i64 %t2682, i64 %t2684)
    call void @freak_llvm_say(i64 %t2685)
    br label %if.end.2672
if.end.2672:
    ret void
}

define i64 @freak_json_parse_string() {
entry:
    %t2686 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.130, i64 0, i64 0
    %t2687 = ptrtoint i8* %t2686 to i64
    call void @freak_json_expect(i64 %t2687)
    %t2688 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.131, i64 0, i64 0
    %t2689 = ptrtoint i8* %t2688 to i64
    %ps_out_v2690 = alloca i64
    store i64 %t2689, i64* %ps_out_v2690
    br label %loop.cond.2691
loop.cond.2691:
    %t2694 = load i64, i64* @g_json_pos
    %t2695 = load i64, i64* @g_json_len
    %t2697 = icmp sge i64 %t2694, %t2695
    %t2696 = zext i1 %t2697 to i64
    %t2698 = icmp eq i64 %t2696, 0
    br i1 %t2698, label %loop.body.2692, label %loop.end.2693
loop.body.2692:
    %t2699 = call i64 @freak_json_advance()
    %c_v2700 = alloca i64
    store i64 %t2699, i64* %c_v2700
    %t2701 = load i64, i64* %c_v2700
    %t2702 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.132, i64 0, i64 0
    %t2703 = ptrtoint i8* %t2702 to i64
    %t2704 = call i64 @freak_llvm_word_eq(i64 %t2701, i64 %t2703)
    %t2708 = icmp ne i64 %t2704, 0
    br i1 %t2708, label %if.then.2705, label %if.end.2707
if.then.2705:
    %t2709 = load i64, i64* %ps_out_v2690
    ret i64 %t2709
    br label %if.end.2707
if.end.2707:
    %t2710 = load i64, i64* %c_v2700
    %t2711 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.133, i64 0, i64 0
    %t2712 = ptrtoint i8* %t2711 to i64
    %t2713 = call i64 @freak_llvm_word_eq(i64 %t2710, i64 %t2712)
    %t2717 = icmp ne i64 %t2713, 0
    br i1 %t2717, label %if.then.2714, label %if.else.2715
if.then.2714:
    %t2718 = call i64 @freak_json_advance()
    %esc_v2719 = alloca i64
    store i64 %t2718, i64* %esc_v2719
    %t2720 = load i64, i64* %esc_v2719
    %t2721 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.134, i64 0, i64 0
    %t2722 = ptrtoint i8* %t2721 to i64
    %t2723 = call i64 @freak_llvm_word_eq(i64 %t2720, i64 %t2722)
    %t2727 = icmp ne i64 %t2723, 0
    br i1 %t2727, label %if.then.2724, label %if.else.2725
if.then.2724:
    %t2728 = load i64, i64* %ps_out_v2690
    %t2729 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.135, i64 0, i64 0
    %t2730 = ptrtoint i8* %t2729 to i64
    %t2731 = call i64 @freak_llvm_word_concat(i64 %t2728, i64 %t2730)
    store i64 %t2731, i64* %ps_out_v2690
    br label %if.end.2726
if.else.2725:
    %t2732 = load i64, i64* %esc_v2719
    %t2733 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.136, i64 0, i64 0
    %t2734 = ptrtoint i8* %t2733 to i64
    %t2735 = call i64 @freak_llvm_word_eq(i64 %t2732, i64 %t2734)
    %t2739 = icmp ne i64 %t2735, 0
    br i1 %t2739, label %if.then.2736, label %if.else.2737
if.then.2736:
    %t2740 = load i64, i64* %ps_out_v2690
    %t2741 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.137, i64 0, i64 0
    %t2742 = ptrtoint i8* %t2741 to i64
    %t2743 = call i64 @freak_llvm_word_concat(i64 %t2740, i64 %t2742)
    store i64 %t2743, i64* %ps_out_v2690
    br label %if.end.2738
if.else.2737:
    %t2744 = load i64, i64* %esc_v2719
    %t2745 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.138, i64 0, i64 0
    %t2746 = ptrtoint i8* %t2745 to i64
    %t2747 = call i64 @freak_llvm_word_eq(i64 %t2744, i64 %t2746)
    %t2751 = icmp ne i64 %t2747, 0
    br i1 %t2751, label %if.then.2748, label %if.else.2749
if.then.2748:
    %t2752 = load i64, i64* %ps_out_v2690
    %t2753 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.139, i64 0, i64 0
    %t2754 = ptrtoint i8* %t2753 to i64
    %t2755 = call i64 @freak_llvm_word_concat(i64 %t2752, i64 %t2754)
    store i64 %t2755, i64* %ps_out_v2690
    br label %if.end.2750
if.else.2749:
    %t2756 = load i64, i64* %esc_v2719
    %t2757 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.140, i64 0, i64 0
    %t2758 = ptrtoint i8* %t2757 to i64
    %t2759 = call i64 @freak_llvm_word_eq(i64 %t2756, i64 %t2758)
    %t2763 = icmp ne i64 %t2759, 0
    br i1 %t2763, label %if.then.2760, label %if.else.2761
if.then.2760:
    %t2764 = load i64, i64* %ps_out_v2690
    %t2765 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.141, i64 0, i64 0
    %t2766 = ptrtoint i8* %t2765 to i64
    %t2767 = call i64 @freak_llvm_word_concat(i64 %t2764, i64 %t2766)
    store i64 %t2767, i64* %ps_out_v2690
    br label %if.end.2762
if.else.2761:
    %t2768 = load i64, i64* %esc_v2719
    %t2769 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.142, i64 0, i64 0
    %t2770 = ptrtoint i8* %t2769 to i64
    %t2771 = call i64 @freak_llvm_word_eq(i64 %t2768, i64 %t2770)
    %t2775 = icmp ne i64 %t2771, 0
    br i1 %t2775, label %if.then.2772, label %if.else.2773
if.then.2772:
    %t2776 = load i64, i64* %ps_out_v2690
    %t2777 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.143, i64 0, i64 0
    %t2778 = ptrtoint i8* %t2777 to i64
    %t2779 = call i64 @freak_llvm_word_concat(i64 %t2776, i64 %t2778)
    store i64 %t2779, i64* %ps_out_v2690
    br label %if.end.2774
if.else.2773:
    %t2780 = load i64, i64* %esc_v2719
    %t2781 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.144, i64 0, i64 0
    %t2782 = ptrtoint i8* %t2781 to i64
    %t2783 = call i64 @freak_llvm_word_eq(i64 %t2780, i64 %t2782)
    %t2787 = icmp ne i64 %t2783, 0
    br i1 %t2787, label %if.then.2784, label %if.else.2785
if.then.2784:
    %t2788 = load i64, i64* %ps_out_v2690
    %t2789 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.145, i64 0, i64 0
    %t2790 = ptrtoint i8* %t2789 to i64
    %t2791 = call i64 @freak_llvm_word_concat(i64 %t2788, i64 %t2790)
    store i64 %t2791, i64* %ps_out_v2690
    br label %if.end.2786
if.else.2785:
    %t2792 = load i64, i64* %ps_out_v2690
    %t2793 = load i64, i64* %esc_v2719
    %t2794 = call i64 @freak_llvm_word_concat(i64 %t2792, i64 %t2793)
    store i64 %t2794, i64* %ps_out_v2690
    br label %if.end.2786
if.end.2786:
    br label %if.end.2774
if.end.2774:
    br label %if.end.2762
if.end.2762:
    br label %if.end.2750
if.end.2750:
    br label %if.end.2738
if.end.2738:
    br label %if.end.2726
if.end.2726:
    br label %if.end.2716
if.else.2715:
    %t2795 = load i64, i64* %ps_out_v2690
    %t2796 = load i64, i64* %c_v2700
    %t2797 = call i64 @freak_llvm_word_concat(i64 %t2795, i64 %t2796)
    store i64 %t2797, i64* %ps_out_v2690
    br label %if.end.2716
if.end.2716:
    br label %loop.cond.2691
loop.end.2693:
    %t2798 = load i64, i64* %ps_out_v2690
    ret i64 %t2798
    ret i64 0
}

define i64 @freak_json_parse_number() {
entry:
    %t2799 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.146, i64 0, i64 0
    %t2800 = ptrtoint i8* %t2799 to i64
    %pn_out_v2801 = alloca i64
    store i64 %t2800, i64* %pn_out_v2801
    %t2802 = call i64 @freak_json_cur()
    %c_v2803 = alloca i64
    store i64 %t2802, i64* %c_v2803
    %t2804 = load i64, i64* %c_v2803
    %t2805 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.147, i64 0, i64 0
    %t2806 = ptrtoint i8* %t2805 to i64
    %t2807 = call i64 @freak_llvm_word_eq(i64 %t2804, i64 %t2806)
    %t2811 = icmp ne i64 %t2807, 0
    br i1 %t2811, label %if.then.2808, label %if.end.2810
if.then.2808:
    %t2812 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.148, i64 0, i64 0
    %t2813 = ptrtoint i8* %t2812 to i64
    store i64 %t2813, i64* %pn_out_v2801
    %t2814 = load i64, i64* @g_json_pos
    %t2815 = add i64 %t2814, 1
    store i64 %t2815, i64* @g_json_pos
    br label %if.end.2810
if.end.2810:
    br label %loop.cond.2816
loop.cond.2816:
    %t2819 = load i64, i64* @g_json_pos
    %t2820 = load i64, i64* @g_json_len
    %t2822 = icmp sge i64 %t2819, %t2820
    %t2821 = zext i1 %t2822 to i64
    %t2823 = icmp eq i64 %t2821, 0
    br i1 %t2823, label %loop.body.2817, label %loop.end.2818
loop.body.2817:
    %t2824 = call i64 @freak_json_cur()
    store i64 %t2824, i64* %c_v2803
    %t2825 = load i64, i64* %c_v2803
    %t2826 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.149, i64 0, i64 0
    %t2827 = ptrtoint i8* %t2826 to i64
    %t2828 = call i64 @freak_llvm_word_eq(i64 %t2825, i64 %t2827)
    %t2829 = load i64, i64* %c_v2803
    %t2830 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.150, i64 0, i64 0
    %t2831 = ptrtoint i8* %t2830 to i64
    %t2832 = call i64 @freak_llvm_word_eq(i64 %t2829, i64 %t2831)
    %t2834 = icmp ne i64 %t2828, 0
    %t2835 = icmp ne i64 %t2832, 0
    %t2836 = or i1 %t2834, %t2835
    %t2833 = zext i1 %t2836 to i64
    %t2837 = load i64, i64* %c_v2803
    %t2838 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.151, i64 0, i64 0
    %t2839 = ptrtoint i8* %t2838 to i64
    %t2840 = call i64 @freak_llvm_word_eq(i64 %t2837, i64 %t2839)
    %t2842 = icmp ne i64 %t2833, 0
    %t2843 = icmp ne i64 %t2840, 0
    %t2844 = or i1 %t2842, %t2843
    %t2841 = zext i1 %t2844 to i64
    %t2845 = load i64, i64* %c_v2803
    %t2846 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.152, i64 0, i64 0
    %t2847 = ptrtoint i8* %t2846 to i64
    %t2848 = call i64 @freak_llvm_word_eq(i64 %t2845, i64 %t2847)
    %t2850 = icmp ne i64 %t2841, 0
    %t2851 = icmp ne i64 %t2848, 0
    %t2852 = or i1 %t2850, %t2851
    %t2849 = zext i1 %t2852 to i64
    %t2853 = load i64, i64* %c_v2803
    %t2854 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.153, i64 0, i64 0
    %t2855 = ptrtoint i8* %t2854 to i64
    %t2856 = call i64 @freak_llvm_word_eq(i64 %t2853, i64 %t2855)
    %t2858 = icmp ne i64 %t2849, 0
    %t2859 = icmp ne i64 %t2856, 0
    %t2860 = or i1 %t2858, %t2859
    %t2857 = zext i1 %t2860 to i64
    %t2861 = load i64, i64* %c_v2803
    %t2862 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.154, i64 0, i64 0
    %t2863 = ptrtoint i8* %t2862 to i64
    %t2864 = call i64 @freak_llvm_word_eq(i64 %t2861, i64 %t2863)
    %t2866 = icmp ne i64 %t2857, 0
    %t2867 = icmp ne i64 %t2864, 0
    %t2868 = or i1 %t2866, %t2867
    %t2865 = zext i1 %t2868 to i64
    %t2869 = load i64, i64* %c_v2803
    %t2870 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.155, i64 0, i64 0
    %t2871 = ptrtoint i8* %t2870 to i64
    %t2872 = call i64 @freak_llvm_word_eq(i64 %t2869, i64 %t2871)
    %t2874 = icmp ne i64 %t2865, 0
    %t2875 = icmp ne i64 %t2872, 0
    %t2876 = or i1 %t2874, %t2875
    %t2873 = zext i1 %t2876 to i64
    %t2877 = load i64, i64* %c_v2803
    %t2878 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.156, i64 0, i64 0
    %t2879 = ptrtoint i8* %t2878 to i64
    %t2880 = call i64 @freak_llvm_word_eq(i64 %t2877, i64 %t2879)
    %t2882 = icmp ne i64 %t2873, 0
    %t2883 = icmp ne i64 %t2880, 0
    %t2884 = or i1 %t2882, %t2883
    %t2881 = zext i1 %t2884 to i64
    %t2885 = load i64, i64* %c_v2803
    %t2886 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.157, i64 0, i64 0
    %t2887 = ptrtoint i8* %t2886 to i64
    %t2888 = call i64 @freak_llvm_word_eq(i64 %t2885, i64 %t2887)
    %t2890 = icmp ne i64 %t2881, 0
    %t2891 = icmp ne i64 %t2888, 0
    %t2892 = or i1 %t2890, %t2891
    %t2889 = zext i1 %t2892 to i64
    %t2893 = load i64, i64* %c_v2803
    %t2894 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.158, i64 0, i64 0
    %t2895 = ptrtoint i8* %t2894 to i64
    %t2896 = call i64 @freak_llvm_word_eq(i64 %t2893, i64 %t2895)
    %t2898 = icmp ne i64 %t2889, 0
    %t2899 = icmp ne i64 %t2896, 0
    %t2900 = or i1 %t2898, %t2899
    %t2897 = zext i1 %t2900 to i64
    %t2901 = load i64, i64* %c_v2803
    %t2902 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.159, i64 0, i64 0
    %t2903 = ptrtoint i8* %t2902 to i64
    %t2904 = call i64 @freak_llvm_word_eq(i64 %t2901, i64 %t2903)
    %t2906 = icmp ne i64 %t2897, 0
    %t2907 = icmp ne i64 %t2904, 0
    %t2908 = or i1 %t2906, %t2907
    %t2905 = zext i1 %t2908 to i64
    %t2912 = icmp ne i64 %t2905, 0
    br i1 %t2912, label %if.then.2909, label %if.else.2910
if.then.2909:
    %t2913 = load i64, i64* %pn_out_v2801
    %t2914 = load i64, i64* %c_v2803
    %t2915 = call i64 @freak_llvm_word_concat(i64 %t2913, i64 %t2914)
    store i64 %t2915, i64* %pn_out_v2801
    %t2916 = load i64, i64* @g_json_pos
    %t2917 = add i64 %t2916, 1
    store i64 %t2917, i64* @g_json_pos
    br label %if.end.2911
if.else.2910:
    %t2918 = load i64, i64* %pn_out_v2801
    ret i64 %t2918
    br label %if.end.2911
if.end.2911:
    br label %loop.cond.2816
loop.end.2818:
    %t2919 = load i64, i64* %pn_out_v2801
    ret i64 %t2919
    ret i64 0
}

define i64 @freak_json_try_keyword(i64 %arg_kw) {
entry:
    %kw = alloca i64
    store i64 %arg_kw, i64* %kw
    %t2920 = load i64, i64* %kw
    %t2921 = call i64 @freak_llvm_word_length(i64 %t2920)
    %kwlen_v2922 = alloca i64
    store i64 %t2921, i64* %kwlen_v2922
    %t2923 = load i64, i64* @g_json_pos
    %t2924 = load i64, i64* %kwlen_v2922
    %t2925 = add i64 %t2923, %t2924
    %t2926 = load i64, i64* @g_json_len
    %t2928 = icmp sgt i64 %t2925, %t2926
    %t2927 = zext i1 %t2928 to i64
    %t2932 = icmp ne i64 %t2927, 0
    br i1 %t2932, label %if.then.2929, label %if.end.2931
if.then.2929:
    ret i64 0
    br label %if.end.2931
if.end.2931:
    %ki_v2933 = alloca i64
    store i64 0, i64* %ki_v2933
    %t2939 = load i64, i64* %kwlen_v2922
    %rep.2938 = alloca i64
    store i64 0, i64* %rep.2938
    br label %loop.cond.2934
loop.cond.2934:
    %t2940 = load i64, i64* %rep.2938
    %t2941 = icmp slt i64 %t2940, %t2939
    br i1 %t2941, label %loop.body.2935, label %loop.end.2936
loop.body.2935:
    %t2942 = load i64, i64* @g_json_src
    %t2944 = load i64, i64* @g_json_pos
    %t2945 = load i64, i64* %ki_v2933
    %t2946 = add i64 %t2944, %t2945
    %t2943 = call i64 @freak_llvm_word_char_at(i64 %t2942, i64 %t2946)
    %t2947 = load i64, i64* %kw
    %t2949 = load i64, i64* %ki_v2933
    %t2948 = call i64 @freak_llvm_word_char_at(i64 %t2947, i64 %t2949)
    %t2950 = call i64 @freak_llvm_word_neq(i64 %t2943, i64 %t2948)
    %t2954 = icmp ne i64 %t2950, 0
    br i1 %t2954, label %if.then.2951, label %if.end.2953
if.then.2951:
    ret i64 0
    br label %if.end.2953
if.end.2953:
    %t2955 = load i64, i64* %ki_v2933
    %t2956 = add i64 %t2955, 1
    store i64 %t2956, i64* %ki_v2933
    br label %loop.inc.2937
loop.inc.2937:
    %t2957 = load i64, i64* %rep.2938
    %t2958 = add i64 %t2957, 1
    store i64 %t2958, i64* %rep.2938
    br label %loop.cond.2934
loop.end.2936:
    %t2959 = load i64, i64* %kwlen_v2922
    %t2960 = load i64, i64* @g_json_pos
    %t2961 = add i64 %t2960, %t2959
    store i64 %t2961, i64* @g_json_pos
    ret i64 1
    ret i64 0
}

define i64 @freak_json_parse_value() {
entry:
    call void @freak_json_skip_ws()
    %t2962 = call i64 @freak_json_cur()
    %c_v2963 = alloca i64
    store i64 %t2962, i64* %c_v2963
    %t2964 = load i64, i64* %c_v2963
    %t2965 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.160, i64 0, i64 0
    %t2966 = ptrtoint i8* %t2965 to i64
    %t2967 = call i64 @freak_llvm_word_eq(i64 %t2964, i64 %t2966)
    %t2971 = icmp ne i64 %t2967, 0
    br i1 %t2971, label %if.then.2968, label %if.end.2970
if.then.2968:
    %t2972 = call i64 @freak_json_parse_string()
    %sv_v2973 = alloca i64
    store i64 %t2972, i64* %sv_v2973
    %t2974 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.161, i64 0, i64 0
    %t2975 = ptrtoint i8* %t2974 to i64
    %t2976 = load i64, i64* %sv_v2973
    %t2977 = call i64 @freak_json_alloc(i64 %t2975, i64 %t2976)
    ret i64 %t2977
    br label %if.end.2970
if.end.2970:
    %t2978 = load i64, i64* %c_v2963
    %t2979 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.162, i64 0, i64 0
    %t2980 = ptrtoint i8* %t2979 to i64
    %t2981 = call i64 @freak_llvm_word_eq(i64 %t2978, i64 %t2980)
    %t2982 = load i64, i64* %c_v2963
    %t2983 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.163, i64 0, i64 0
    %t2984 = ptrtoint i8* %t2983 to i64
    %t2985 = call i64 @freak_llvm_word_eq(i64 %t2982, i64 %t2984)
    %t2987 = icmp ne i64 %t2981, 0
    %t2988 = icmp ne i64 %t2985, 0
    %t2989 = or i1 %t2987, %t2988
    %t2986 = zext i1 %t2989 to i64
    %t2990 = load i64, i64* %c_v2963
    %t2991 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.164, i64 0, i64 0
    %t2992 = ptrtoint i8* %t2991 to i64
    %t2993 = call i64 @freak_llvm_word_eq(i64 %t2990, i64 %t2992)
    %t2995 = icmp ne i64 %t2986, 0
    %t2996 = icmp ne i64 %t2993, 0
    %t2997 = or i1 %t2995, %t2996
    %t2994 = zext i1 %t2997 to i64
    %t2998 = load i64, i64* %c_v2963
    %t2999 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.165, i64 0, i64 0
    %t3000 = ptrtoint i8* %t2999 to i64
    %t3001 = call i64 @freak_llvm_word_eq(i64 %t2998, i64 %t3000)
    %t3003 = icmp ne i64 %t2994, 0
    %t3004 = icmp ne i64 %t3001, 0
    %t3005 = or i1 %t3003, %t3004
    %t3002 = zext i1 %t3005 to i64
    %t3006 = load i64, i64* %c_v2963
    %t3007 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.166, i64 0, i64 0
    %t3008 = ptrtoint i8* %t3007 to i64
    %t3009 = call i64 @freak_llvm_word_eq(i64 %t3006, i64 %t3008)
    %t3011 = icmp ne i64 %t3002, 0
    %t3012 = icmp ne i64 %t3009, 0
    %t3013 = or i1 %t3011, %t3012
    %t3010 = zext i1 %t3013 to i64
    %t3014 = load i64, i64* %c_v2963
    %t3015 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.167, i64 0, i64 0
    %t3016 = ptrtoint i8* %t3015 to i64
    %t3017 = call i64 @freak_llvm_word_eq(i64 %t3014, i64 %t3016)
    %t3019 = icmp ne i64 %t3010, 0
    %t3020 = icmp ne i64 %t3017, 0
    %t3021 = or i1 %t3019, %t3020
    %t3018 = zext i1 %t3021 to i64
    %t3022 = load i64, i64* %c_v2963
    %t3023 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.168, i64 0, i64 0
    %t3024 = ptrtoint i8* %t3023 to i64
    %t3025 = call i64 @freak_llvm_word_eq(i64 %t3022, i64 %t3024)
    %t3027 = icmp ne i64 %t3018, 0
    %t3028 = icmp ne i64 %t3025, 0
    %t3029 = or i1 %t3027, %t3028
    %t3026 = zext i1 %t3029 to i64
    %t3030 = load i64, i64* %c_v2963
    %t3031 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.169, i64 0, i64 0
    %t3032 = ptrtoint i8* %t3031 to i64
    %t3033 = call i64 @freak_llvm_word_eq(i64 %t3030, i64 %t3032)
    %t3035 = icmp ne i64 %t3026, 0
    %t3036 = icmp ne i64 %t3033, 0
    %t3037 = or i1 %t3035, %t3036
    %t3034 = zext i1 %t3037 to i64
    %t3038 = load i64, i64* %c_v2963
    %t3039 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.170, i64 0, i64 0
    %t3040 = ptrtoint i8* %t3039 to i64
    %t3041 = call i64 @freak_llvm_word_eq(i64 %t3038, i64 %t3040)
    %t3043 = icmp ne i64 %t3034, 0
    %t3044 = icmp ne i64 %t3041, 0
    %t3045 = or i1 %t3043, %t3044
    %t3042 = zext i1 %t3045 to i64
    %t3046 = load i64, i64* %c_v2963
    %t3047 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.171, i64 0, i64 0
    %t3048 = ptrtoint i8* %t3047 to i64
    %t3049 = call i64 @freak_llvm_word_eq(i64 %t3046, i64 %t3048)
    %t3051 = icmp ne i64 %t3042, 0
    %t3052 = icmp ne i64 %t3049, 0
    %t3053 = or i1 %t3051, %t3052
    %t3050 = zext i1 %t3053 to i64
    %t3054 = load i64, i64* %c_v2963
    %t3055 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.172, i64 0, i64 0
    %t3056 = ptrtoint i8* %t3055 to i64
    %t3057 = call i64 @freak_llvm_word_eq(i64 %t3054, i64 %t3056)
    %t3059 = icmp ne i64 %t3050, 0
    %t3060 = icmp ne i64 %t3057, 0
    %t3061 = or i1 %t3059, %t3060
    %t3058 = zext i1 %t3061 to i64
    %t3065 = icmp ne i64 %t3058, 0
    br i1 %t3065, label %if.then.3062, label %if.end.3064
if.then.3062:
    %t3066 = call i64 @freak_json_parse_number()
    %nv_v3067 = alloca i64
    store i64 %t3066, i64* %nv_v3067
    %t3068 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.173, i64 0, i64 0
    %t3069 = ptrtoint i8* %t3068 to i64
    %t3070 = load i64, i64* %nv_v3067
    %t3071 = call i64 @freak_json_alloc(i64 %t3069, i64 %t3070)
    ret i64 %t3071
    br label %if.end.3064
if.end.3064:
    %t3072 = load i64, i64* %c_v2963
    %t3073 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.174, i64 0, i64 0
    %t3074 = ptrtoint i8* %t3073 to i64
    %t3075 = call i64 @freak_llvm_word_eq(i64 %t3072, i64 %t3074)
    %t3079 = icmp ne i64 %t3075, 0
    br i1 %t3079, label %if.then.3076, label %if.end.3078
if.then.3076:
    %t3080 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.175, i64 0, i64 0
    %t3081 = ptrtoint i8* %t3080 to i64
    %t3082 = call i64 @freak_json_try_keyword(i64 %t3081)
    %t3086 = icmp ne i64 %t3082, 0
    br i1 %t3086, label %if.then.3083, label %if.end.3085
if.then.3083:
    %t3087 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.176, i64 0, i64 0
    %t3088 = ptrtoint i8* %t3087 to i64
    %t3089 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.177, i64 0, i64 0
    %t3090 = ptrtoint i8* %t3089 to i64
    %t3091 = call i64 @freak_json_alloc(i64 %t3088, i64 %t3090)
    ret i64 %t3091
    br label %if.end.3085
if.end.3085:
    br label %if.end.3078
if.end.3078:
    %t3092 = load i64, i64* %c_v2963
    %t3093 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.178, i64 0, i64 0
    %t3094 = ptrtoint i8* %t3093 to i64
    %t3095 = call i64 @freak_llvm_word_eq(i64 %t3092, i64 %t3094)
    %t3099 = icmp ne i64 %t3095, 0
    br i1 %t3099, label %if.then.3096, label %if.end.3098
if.then.3096:
    %t3100 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.179, i64 0, i64 0
    %t3101 = ptrtoint i8* %t3100 to i64
    %t3102 = call i64 @freak_json_try_keyword(i64 %t3101)
    %t3106 = icmp ne i64 %t3102, 0
    br i1 %t3106, label %if.then.3103, label %if.end.3105
if.then.3103:
    %t3107 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.180, i64 0, i64 0
    %t3108 = ptrtoint i8* %t3107 to i64
    %t3109 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.181, i64 0, i64 0
    %t3110 = ptrtoint i8* %t3109 to i64
    %t3111 = call i64 @freak_json_alloc(i64 %t3108, i64 %t3110)
    ret i64 %t3111
    br label %if.end.3105
if.end.3105:
    br label %if.end.3098
if.end.3098:
    %t3112 = load i64, i64* %c_v2963
    %t3113 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.182, i64 0, i64 0
    %t3114 = ptrtoint i8* %t3113 to i64
    %t3115 = call i64 @freak_llvm_word_eq(i64 %t3112, i64 %t3114)
    %t3119 = icmp ne i64 %t3115, 0
    br i1 %t3119, label %if.then.3116, label %if.end.3118
if.then.3116:
    %t3120 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.183, i64 0, i64 0
    %t3121 = ptrtoint i8* %t3120 to i64
    %t3122 = call i64 @freak_json_try_keyword(i64 %t3121)
    %t3126 = icmp ne i64 %t3122, 0
    br i1 %t3126, label %if.then.3123, label %if.end.3125
if.then.3123:
    %t3127 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.184, i64 0, i64 0
    %t3128 = ptrtoint i8* %t3127 to i64
    %t3129 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.185, i64 0, i64 0
    %t3130 = ptrtoint i8* %t3129 to i64
    %t3131 = call i64 @freak_json_alloc(i64 %t3128, i64 %t3130)
    ret i64 %t3131
    br label %if.end.3125
if.end.3125:
    br label %if.end.3118
if.end.3118:
    %t3132 = load i64, i64* %c_v2963
    %t3133 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.186, i64 0, i64 0
    %t3134 = ptrtoint i8* %t3133 to i64
    %t3135 = call i64 @freak_llvm_word_eq(i64 %t3132, i64 %t3134)
    %t3139 = icmp ne i64 %t3135, 0
    br i1 %t3139, label %if.then.3136, label %if.end.3138
if.then.3136:
    %t3140 = load i64, i64* @g_json_pos
    %t3141 = add i64 %t3140, 1
    store i64 %t3141, i64* @g_json_pos
    %t3142 = call i64 @freak_llvm_array_new()
    %arr_children_v3143 = alloca i64
    store i64 %t3142, i64* %arr_children_v3143
    %t3144 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.187, i64 0, i64 0
    %t3145 = ptrtoint i8* %t3144 to i64
    %t3146 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.188, i64 0, i64 0
    %t3147 = ptrtoint i8* %t3146 to i64
    %t3148 = call i64 @freak_json_alloc(i64 %t3145, i64 %t3147)
    %arr_handle_v3149 = alloca i64
    store i64 %t3148, i64* %arr_handle_v3149
    %t3150 = load i64, i64* @g_json_children
    %t3151 = load i64, i64* %arr_handle_v3149
    %t3152 = load i64, i64* %arr_children_v3143
    %t3153 = call i64 @freak_llvm_word_from_int(i64 %t3152)
    call void @freak_llvm_array_set(i64 %t3150, i64 %t3151, i64 %t3153)
    call void @freak_json_skip_ws()
    %t3154 = call i64 @freak_json_cur()
    %t3155 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.189, i64 0, i64 0
    %t3156 = ptrtoint i8* %t3155 to i64
    %t3157 = call i64 @freak_llvm_word_neq(i64 %t3154, i64 %t3156)
    %t3161 = icmp ne i64 %t3157, 0
    br i1 %t3161, label %if.then.3158, label %if.end.3160
if.then.3158:
    %t3162 = call i64 @freak_json_parse_value()
    %first_val_v3163 = alloca i64
    store i64 %t3162, i64* %first_val_v3163
    %t3164 = load i64, i64* %arr_children_v3143
    %t3165 = load i64, i64* %first_val_v3163
    %t3166 = call i64 @freak_llvm_word_from_int(i64 %t3165)
    call void @freak_llvm_array_push(i64 %t3164, i64 %t3166)
    call void @freak_json_skip_ws()
    br label %loop.cond.3167
loop.cond.3167:
    %t3170 = call i64 @freak_json_cur()
    %t3171 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.190, i64 0, i64 0
    %t3172 = ptrtoint i8* %t3171 to i64
    %t3173 = call i64 @freak_llvm_word_neq(i64 %t3170, i64 %t3172)
    %t3174 = icmp eq i64 %t3173, 0
    br i1 %t3174, label %loop.body.3168, label %loop.end.3169
loop.body.3168:
    %t3175 = load i64, i64* @g_json_pos
    %t3176 = add i64 %t3175, 1
    store i64 %t3176, i64* @g_json_pos
    %t3177 = call i64 @freak_json_parse_value()
    %next_val_v3178 = alloca i64
    store i64 %t3177, i64* %next_val_v3178
    %t3179 = load i64, i64* %arr_children_v3143
    %t3180 = load i64, i64* %next_val_v3178
    %t3181 = call i64 @freak_llvm_word_from_int(i64 %t3180)
    call void @freak_llvm_array_push(i64 %t3179, i64 %t3181)
    call void @freak_json_skip_ws()
    br label %loop.cond.3167
loop.end.3169:
    br label %if.end.3160
if.end.3160:
    %t3182 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.191, i64 0, i64 0
    %t3183 = ptrtoint i8* %t3182 to i64
    call void @freak_json_expect(i64 %t3183)
    %t3184 = load i64, i64* %arr_handle_v3149
    ret i64 %t3184
    br label %if.end.3138
if.end.3138:
    %t3185 = load i64, i64* %c_v2963
    %t3186 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.192, i64 0, i64 0
    %t3187 = ptrtoint i8* %t3186 to i64
    %t3188 = call i64 @freak_llvm_word_eq(i64 %t3185, i64 %t3187)
    %t3192 = icmp ne i64 %t3188, 0
    br i1 %t3192, label %if.then.3189, label %if.end.3191
if.then.3189:
    %t3193 = load i64, i64* @g_json_pos
    %t3194 = add i64 %t3193, 1
    store i64 %t3194, i64* @g_json_pos
    %t3195 = call i64 @freak_llvm_array_new()
    %obj_children_v3196 = alloca i64
    store i64 %t3195, i64* %obj_children_v3196
    %t3197 = call i64 @freak_llvm_array_new()
    %obj_keys_v3198 = alloca i64
    store i64 %t3197, i64* %obj_keys_v3198
    %t3199 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.193, i64 0, i64 0
    %t3200 = ptrtoint i8* %t3199 to i64
    %t3201 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.194, i64 0, i64 0
    %t3202 = ptrtoint i8* %t3201 to i64
    %t3203 = call i64 @freak_json_alloc(i64 %t3200, i64 %t3202)
    %obj_handle_v3204 = alloca i64
    store i64 %t3203, i64* %obj_handle_v3204
    %t3205 = load i64, i64* @g_json_children
    %t3206 = load i64, i64* %obj_handle_v3204
    %t3207 = load i64, i64* %obj_children_v3196
    %t3208 = call i64 @freak_llvm_word_from_int(i64 %t3207)
    call void @freak_llvm_array_set(i64 %t3205, i64 %t3206, i64 %t3208)
    %t3209 = load i64, i64* @g_json_keys
    %t3210 = load i64, i64* %obj_handle_v3204
    %t3211 = load i64, i64* %obj_keys_v3198
    %t3212 = call i64 @freak_llvm_word_from_int(i64 %t3211)
    call void @freak_llvm_array_set(i64 %t3209, i64 %t3210, i64 %t3212)
    call void @freak_json_skip_ws()
    %t3213 = call i64 @freak_json_cur()
    %t3214 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.195, i64 0, i64 0
    %t3215 = ptrtoint i8* %t3214 to i64
    %t3216 = call i64 @freak_llvm_word_neq(i64 %t3213, i64 %t3215)
    %t3220 = icmp ne i64 %t3216, 0
    br i1 %t3220, label %if.then.3217, label %if.end.3219
if.then.3217:
    %t3221 = call i64 @freak_json_parse_string()
    %k1_v3222 = alloca i64
    store i64 %t3221, i64* %k1_v3222
    call void @freak_json_skip_ws()
    %t3223 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.196, i64 0, i64 0
    %t3224 = ptrtoint i8* %t3223 to i64
    call void @freak_json_expect(i64 %t3224)
    %t3225 = call i64 @freak_json_parse_value()
    %v1_v3226 = alloca i64
    store i64 %t3225, i64* %v1_v3226
    %t3227 = load i64, i64* %obj_keys_v3198
    %t3228 = load i64, i64* %k1_v3222
    call void @freak_llvm_array_push(i64 %t3227, i64 %t3228)
    %t3229 = load i64, i64* %obj_children_v3196
    %t3230 = load i64, i64* %v1_v3226
    %t3231 = call i64 @freak_llvm_word_from_int(i64 %t3230)
    call void @freak_llvm_array_push(i64 %t3229, i64 %t3231)
    call void @freak_json_skip_ws()
    br label %loop.cond.3232
loop.cond.3232:
    %t3235 = call i64 @freak_json_cur()
    %t3236 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.197, i64 0, i64 0
    %t3237 = ptrtoint i8* %t3236 to i64
    %t3238 = call i64 @freak_llvm_word_neq(i64 %t3235, i64 %t3237)
    %t3239 = icmp eq i64 %t3238, 0
    br i1 %t3239, label %loop.body.3233, label %loop.end.3234
loop.body.3233:
    %t3240 = load i64, i64* @g_json_pos
    %t3241 = add i64 %t3240, 1
    store i64 %t3241, i64* @g_json_pos
    call void @freak_json_skip_ws()
    %t3242 = call i64 @freak_json_parse_string()
    %kn_v3243 = alloca i64
    store i64 %t3242, i64* %kn_v3243
    call void @freak_json_skip_ws()
    %t3244 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.198, i64 0, i64 0
    %t3245 = ptrtoint i8* %t3244 to i64
    call void @freak_json_expect(i64 %t3245)
    %t3246 = call i64 @freak_json_parse_value()
    %vn_v3247 = alloca i64
    store i64 %t3246, i64* %vn_v3247
    %t3248 = load i64, i64* %obj_keys_v3198
    %t3249 = load i64, i64* %kn_v3243
    call void @freak_llvm_array_push(i64 %t3248, i64 %t3249)
    %t3250 = load i64, i64* %obj_children_v3196
    %t3251 = load i64, i64* %vn_v3247
    %t3252 = call i64 @freak_llvm_word_from_int(i64 %t3251)
    call void @freak_llvm_array_push(i64 %t3250, i64 %t3252)
    call void @freak_json_skip_ws()
    br label %loop.cond.3232
loop.end.3234:
    br label %if.end.3219
if.end.3219:
    %t3253 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.199, i64 0, i64 0
    %t3254 = ptrtoint i8* %t3253 to i64
    call void @freak_json_expect(i64 %t3254)
    %t3255 = load i64, i64* %obj_handle_v3204
    ret i64 %t3255
    br label %if.end.3191
if.end.3191:
    %t3256 = getelementptr inbounds [31 x i8], [31 x i8]* @.str.200, i64 0, i64 0
    %t3257 = ptrtoint i8* %t3256 to i64
    %t3258 = load i64, i64* %c_v2963
    %t3259 = call i64 @freak_llvm_word_concat(i64 %t3257, i64 %t3258)
    %t3260 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.201, i64 0, i64 0
    %t3261 = ptrtoint i8* %t3260 to i64
    %t3262 = call i64 @freak_llvm_word_concat(i64 %t3259, i64 %t3261)
    call void @freak_llvm_say(i64 %t3262)
    %t3263 = sub i64 0, 1
    ret i64 %t3263
    ret i64 0
}

define i64 @freak_json_parse(i64 %arg_source) {
entry:
    %source = alloca i64
    store i64 %arg_source, i64* %source
    call void @freak_json_init()
    %t3264 = load i64, i64* %source
    store i64 %t3264, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    %t3265 = load i64, i64* %source
    %t3266 = call i64 @freak_llvm_word_length(i64 %t3265)
    store i64 %t3266, i64* @g_json_len
    %t3267 = call i64 @freak_json_parse_value()
    ret i64 %t3267
    ret i64 0
}

define i64 @freak_json_stringify(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t3268 = load i64, i64* %handle
    %t3270 = icmp slt i64 %t3268, 0
    %t3269 = zext i1 %t3270 to i64
    %t3274 = icmp ne i64 %t3269, 0
    br i1 %t3274, label %if.then.3271, label %if.end.3273
if.then.3271:
    %t3275 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.202, i64 0, i64 0
    %t3276 = ptrtoint i8* %t3275 to i64
    ret i64 %t3276
    br label %if.end.3273
if.end.3273:
    %t3277 = load i64, i64* @g_json_types
    %t3278 = load i64, i64* %handle
    %t3279 = call i64 @freak_llvm_array_get(i64 %t3277, i64 %t3278)
    %t_v3280 = alloca i64
    store i64 %t3279, i64* %t_v3280
    %t3281 = load i64, i64* %t_v3280
    %t3282 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.203, i64 0, i64 0
    %t3283 = ptrtoint i8* %t3282 to i64
    %t3284 = call i64 @freak_llvm_word_eq(i64 %t3281, i64 %t3283)
    %t3288 = icmp ne i64 %t3284, 0
    br i1 %t3288, label %if.then.3285, label %if.end.3287
if.then.3285:
    %t3289 = load i64, i64* @g_json_vals
    %t3290 = load i64, i64* %handle
    %t3291 = call i64 @freak_llvm_array_get(i64 %t3289, i64 %t3290)
    %sv_v3292 = alloca i64
    store i64 %t3291, i64* %sv_v3292
    %t3293 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.204, i64 0, i64 0
    %t3294 = ptrtoint i8* %t3293 to i64
    %t3295 = load i64, i64* %sv_v3292
    %t3296 = call i64 @freak_llvm_word_concat(i64 %t3294, i64 %t3295)
    %t3297 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.205, i64 0, i64 0
    %t3298 = ptrtoint i8* %t3297 to i64
    %t3299 = call i64 @freak_llvm_word_concat(i64 %t3296, i64 %t3298)
    ret i64 %t3299
    br label %if.end.3287
if.end.3287:
    %t3300 = load i64, i64* %t_v3280
    %t3301 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.206, i64 0, i64 0
    %t3302 = ptrtoint i8* %t3301 to i64
    %t3303 = call i64 @freak_llvm_word_eq(i64 %t3300, i64 %t3302)
    %t3307 = icmp ne i64 %t3303, 0
    br i1 %t3307, label %if.then.3304, label %if.end.3306
if.then.3304:
    %t3308 = load i64, i64* @g_json_vals
    %t3309 = load i64, i64* %handle
    %t3310 = call i64 @freak_llvm_array_get(i64 %t3308, i64 %t3309)
    ret i64 %t3310
    br label %if.end.3306
if.end.3306:
    %t3311 = load i64, i64* %t_v3280
    %t3312 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.207, i64 0, i64 0
    %t3313 = ptrtoint i8* %t3312 to i64
    %t3314 = call i64 @freak_llvm_word_eq(i64 %t3311, i64 %t3313)
    %t3318 = icmp ne i64 %t3314, 0
    br i1 %t3318, label %if.then.3315, label %if.end.3317
if.then.3315:
    %t3319 = load i64, i64* @g_json_vals
    %t3320 = load i64, i64* %handle
    %t3321 = call i64 @freak_llvm_array_get(i64 %t3319, i64 %t3320)
    ret i64 %t3321
    br label %if.end.3317
if.end.3317:
    %t3322 = load i64, i64* %t_v3280
    %t3323 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.208, i64 0, i64 0
    %t3324 = ptrtoint i8* %t3323 to i64
    %t3325 = call i64 @freak_llvm_word_eq(i64 %t3322, i64 %t3324)
    %t3329 = icmp ne i64 %t3325, 0
    br i1 %t3329, label %if.then.3326, label %if.end.3328
if.then.3326:
    %t3330 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.209, i64 0, i64 0
    %t3331 = ptrtoint i8* %t3330 to i64
    ret i64 %t3331
    br label %if.end.3328
if.end.3328:
    %t3332 = load i64, i64* %t_v3280
    %t3333 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.210, i64 0, i64 0
    %t3334 = ptrtoint i8* %t3333 to i64
    %t3335 = call i64 @freak_llvm_word_eq(i64 %t3332, i64 %t3334)
    %t3339 = icmp ne i64 %t3335, 0
    br i1 %t3339, label %if.then.3336, label %if.end.3338
if.then.3336:
    %t3340 = load i64, i64* %handle
    %t3341 = call i64 @freak_json_arr_len(i64 %t3340)
    %alen_v3342 = alloca i64
    store i64 %t3341, i64* %alen_v3342
    %t3343 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.211, i64 0, i64 0
    %t3344 = ptrtoint i8* %t3343 to i64
    %a_out_v3345 = alloca i64
    store i64 %t3344, i64* %a_out_v3345
    %ai_v3346 = alloca i64
    store i64 0, i64* %ai_v3346
    %t3352 = load i64, i64* %alen_v3342
    %rep.3351 = alloca i64
    store i64 0, i64* %rep.3351
    br label %loop.cond.3347
loop.cond.3347:
    %t3353 = load i64, i64* %rep.3351
    %t3354 = icmp slt i64 %t3353, %t3352
    br i1 %t3354, label %loop.body.3348, label %loop.end.3349
loop.body.3348:
    %t3355 = load i64, i64* %ai_v3346
    %t3357 = icmp sgt i64 %t3355, 0
    %t3356 = zext i1 %t3357 to i64
    %t3361 = icmp ne i64 %t3356, 0
    br i1 %t3361, label %if.then.3358, label %if.end.3360
if.then.3358:
    %t3362 = load i64, i64* %a_out_v3345
    %t3363 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.212, i64 0, i64 0
    %t3364 = ptrtoint i8* %t3363 to i64
    %t3365 = call i64 @freak_llvm_word_concat(i64 %t3362, i64 %t3364)
    store i64 %t3365, i64* %a_out_v3345
    br label %if.end.3360
if.end.3360:
    %t3366 = load i64, i64* %handle
    %t3367 = load i64, i64* %ai_v3346
    %t3368 = call i64 @freak_json_arr_get(i64 %t3366, i64 %t3367)
    %child_v3369 = alloca i64
    store i64 %t3368, i64* %child_v3369
    %t3370 = load i64, i64* %a_out_v3345
    %t3371 = load i64, i64* %child_v3369
    %t3372 = call i64 @freak_json_stringify(i64 %t3371)
    %t3373 = call i64 @freak_llvm_word_concat(i64 %t3370, i64 %t3372)
    store i64 %t3373, i64* %a_out_v3345
    %t3374 = load i64, i64* %ai_v3346
    %t3375 = add i64 %t3374, 1
    store i64 %t3375, i64* %ai_v3346
    br label %loop.inc.3350
loop.inc.3350:
    %t3376 = load i64, i64* %rep.3351
    %t3377 = add i64 %t3376, 1
    store i64 %t3377, i64* %rep.3351
    br label %loop.cond.3347
loop.end.3349:
    %t3378 = load i64, i64* %a_out_v3345
    %t3379 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.213, i64 0, i64 0
    %t3380 = ptrtoint i8* %t3379 to i64
    %t3381 = call i64 @freak_llvm_word_concat(i64 %t3378, i64 %t3380)
    ret i64 %t3381
    br label %if.end.3338
if.end.3338:
    %t3382 = load i64, i64* %t_v3280
    %t3383 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.214, i64 0, i64 0
    %t3384 = ptrtoint i8* %t3383 to i64
    %t3385 = call i64 @freak_llvm_word_eq(i64 %t3382, i64 %t3384)
    %t3389 = icmp ne i64 %t3385, 0
    br i1 %t3389, label %if.then.3386, label %if.end.3388
if.then.3386:
    %t3390 = load i64, i64* %handle
    %t3391 = call i64 @freak_json_obj_len(i64 %t3390)
    %olen_v3392 = alloca i64
    store i64 %t3391, i64* %olen_v3392
    %t3393 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.215, i64 0, i64 0
    %t3394 = ptrtoint i8* %t3393 to i64
    %o_out_v3395 = alloca i64
    store i64 %t3394, i64* %o_out_v3395
    %oi_v3396 = alloca i64
    store i64 0, i64* %oi_v3396
    %t3402 = load i64, i64* %olen_v3392
    %rep.3401 = alloca i64
    store i64 0, i64* %rep.3401
    br label %loop.cond.3397
loop.cond.3397:
    %t3403 = load i64, i64* %rep.3401
    %t3404 = icmp slt i64 %t3403, %t3402
    br i1 %t3404, label %loop.body.3398, label %loop.end.3399
loop.body.3398:
    %t3405 = load i64, i64* %oi_v3396
    %t3407 = icmp sgt i64 %t3405, 0
    %t3406 = zext i1 %t3407 to i64
    %t3411 = icmp ne i64 %t3406, 0
    br i1 %t3411, label %if.then.3408, label %if.end.3410
if.then.3408:
    %t3412 = load i64, i64* %o_out_v3395
    %t3413 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.216, i64 0, i64 0
    %t3414 = ptrtoint i8* %t3413 to i64
    %t3415 = call i64 @freak_llvm_word_concat(i64 %t3412, i64 %t3414)
    store i64 %t3415, i64* %o_out_v3395
    br label %if.end.3410
if.end.3410:
    %t3416 = load i64, i64* %handle
    %t3417 = load i64, i64* %oi_v3396
    %t3418 = call i64 @freak_json_obj_key_at(i64 %t3416, i64 %t3417)
    %okey_v3419 = alloca i64
    store i64 %t3418, i64* %okey_v3419
    %t3420 = load i64, i64* %handle
    %t3421 = load i64, i64* %oi_v3396
    %t3422 = call i64 @freak_json_arr_get(i64 %t3420, i64 %t3421)
    %ov_v3423 = alloca i64
    store i64 %t3422, i64* %ov_v3423
    %t3424 = load i64, i64* %o_out_v3395
    %t3425 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.217, i64 0, i64 0
    %t3426 = ptrtoint i8* %t3425 to i64
    %t3427 = call i64 @freak_llvm_word_concat(i64 %t3424, i64 %t3426)
    %t3428 = load i64, i64* %okey_v3419
    %t3429 = call i64 @freak_llvm_word_concat(i64 %t3427, i64 %t3428)
    %t3430 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.218, i64 0, i64 0
    %t3431 = ptrtoint i8* %t3430 to i64
    %t3432 = call i64 @freak_llvm_word_concat(i64 %t3429, i64 %t3431)
    %t3433 = load i64, i64* %ov_v3423
    %t3434 = call i64 @freak_json_stringify(i64 %t3433)
    %t3435 = call i64 @freak_llvm_word_concat(i64 %t3432, i64 %t3434)
    store i64 %t3435, i64* %o_out_v3395
    %t3436 = load i64, i64* %oi_v3396
    %t3437 = add i64 %t3436, 1
    store i64 %t3437, i64* %oi_v3396
    br label %loop.inc.3400
loop.inc.3400:
    %t3438 = load i64, i64* %rep.3401
    %t3439 = add i64 %t3438, 1
    store i64 %t3439, i64* %rep.3401
    br label %loop.cond.3397
loop.end.3399:
    %t3440 = load i64, i64* %o_out_v3395
    %t3441 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.219, i64 0, i64 0
    %t3442 = ptrtoint i8* %t3441 to i64
    %t3443 = call i64 @freak_llvm_word_concat(i64 %t3440, i64 %t3442)
    ret i64 %t3443
    br label %if.end.3388
if.end.3388:
    %t3444 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.220, i64 0, i64 0
    %t3445 = ptrtoint i8* %t3444 to i64
    ret i64 %t3445
    ret i64 0
}

define i64 @freak_ver_parse_num(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3446 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.221, i64 0, i64 0
    %t3447 = ptrtoint i8* %t3446 to i64
    %res_v3448 = alloca i64
    store i64 %t3447, i64* %res_v3448
    %t3449 = load i64, i64* %start
    %i_v3450 = alloca i64
    store i64 %t3449, i64* %i_v3450
    %t3451 = load i64, i64* %s
    %t3452 = call i64 @freak_llvm_word_length(i64 %t3451)
    %slen_v3453 = alloca i64
    store i64 %t3452, i64* %slen_v3453
    br label %loop.cond.3454
loop.cond.3454:
    %t3457 = load i64, i64* %i_v3450
    %t3458 = load i64, i64* %slen_v3453
    %t3460 = icmp sge i64 %t3457, %t3458
    %t3459 = zext i1 %t3460 to i64
    %t3461 = icmp eq i64 %t3459, 0
    br i1 %t3461, label %loop.body.3455, label %loop.end.3456
loop.body.3455:
    %t3462 = load i64, i64* %s
    %t3464 = load i64, i64* %i_v3450
    %t3463 = call i64 @freak_llvm_word_char_at(i64 %t3462, i64 %t3464)
    %c_v3465 = alloca i64
    store i64 %t3463, i64* %c_v3465
    %t3466 = load i64, i64* %c_v3465
    %t3467 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.222, i64 0, i64 0
    %t3468 = ptrtoint i8* %t3467 to i64
    %t3469 = call i64 @freak_llvm_word_eq(i64 %t3466, i64 %t3468)
    %t3470 = load i64, i64* %c_v3465
    %t3471 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.223, i64 0, i64 0
    %t3472 = ptrtoint i8* %t3471 to i64
    %t3473 = call i64 @freak_llvm_word_eq(i64 %t3470, i64 %t3472)
    %t3475 = icmp ne i64 %t3469, 0
    %t3476 = icmp ne i64 %t3473, 0
    %t3477 = or i1 %t3475, %t3476
    %t3474 = zext i1 %t3477 to i64
    %t3478 = load i64, i64* %c_v3465
    %t3479 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.224, i64 0, i64 0
    %t3480 = ptrtoint i8* %t3479 to i64
    %t3481 = call i64 @freak_llvm_word_eq(i64 %t3478, i64 %t3480)
    %t3483 = icmp ne i64 %t3474, 0
    %t3484 = icmp ne i64 %t3481, 0
    %t3485 = or i1 %t3483, %t3484
    %t3482 = zext i1 %t3485 to i64
    %t3489 = icmp ne i64 %t3482, 0
    br i1 %t3489, label %if.then.3486, label %if.end.3488
if.then.3486:
    %t3490 = load i64, i64* %i_v3450
    %t3491 = add i64 %t3490, 1
    %t3492 = call i64 @freak_llvm_word_from_int(i64 %t3491)
    %pos_str_v3493 = alloca i64
    store i64 %t3492, i64* %pos_str_v3493
    %t3494 = load i64, i64* %res_v3448
    %t3495 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.225, i64 0, i64 0
    %t3496 = ptrtoint i8* %t3495 to i64
    %t3497 = call i64 @freak_llvm_word_concat(i64 %t3494, i64 %t3496)
    %t3498 = load i64, i64* %pos_str_v3493
    %t3499 = call i64 @freak_llvm_word_concat(i64 %t3497, i64 %t3498)
    ret i64 %t3499
    br label %if.end.3488
if.end.3488:
    %t3500 = load i64, i64* %res_v3448
    %t3501 = load i64, i64* %c_v3465
    %t3502 = call i64 @freak_llvm_word_concat(i64 %t3500, i64 %t3501)
    store i64 %t3502, i64* %res_v3448
    %t3503 = load i64, i64* %i_v3450
    %t3504 = add i64 %t3503, 1
    store i64 %t3504, i64* %i_v3450
    br label %loop.cond.3454
loop.end.3456:
    %t3505 = load i64, i64* %i_v3450
    %t3506 = call i64 @freak_llvm_word_from_int(i64 %t3505)
    %pos_str2_v3507 = alloca i64
    store i64 %t3506, i64* %pos_str2_v3507
    %t3508 = load i64, i64* %res_v3448
    %t3509 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.226, i64 0, i64 0
    %t3510 = ptrtoint i8* %t3509 to i64
    %t3511 = call i64 @freak_llvm_word_concat(i64 %t3508, i64 %t3510)
    %t3512 = load i64, i64* %pos_str2_v3507
    %t3513 = call i64 @freak_llvm_word_concat(i64 %t3511, i64 %t3512)
    ret i64 %t3513
    ret i64 0
}

define i64 @freak_ver_parse_pre(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3514 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.227, i64 0, i64 0
    %t3515 = ptrtoint i8* %t3514 to i64
    %res_v3516 = alloca i64
    store i64 %t3515, i64* %res_v3516
    %t3517 = load i64, i64* %start
    %i_v3518 = alloca i64
    store i64 %t3517, i64* %i_v3518
    %t3519 = load i64, i64* %s
    %t3520 = call i64 @freak_llvm_word_length(i64 %t3519)
    %slen_v3521 = alloca i64
    store i64 %t3520, i64* %slen_v3521
    br label %loop.cond.3522
loop.cond.3522:
    %t3525 = load i64, i64* %i_v3518
    %t3526 = load i64, i64* %slen_v3521
    %t3528 = icmp sge i64 %t3525, %t3526
    %t3527 = zext i1 %t3528 to i64
    %t3529 = icmp eq i64 %t3527, 0
    br i1 %t3529, label %loop.body.3523, label %loop.end.3524
loop.body.3523:
    %t3530 = load i64, i64* %s
    %t3532 = load i64, i64* %i_v3518
    %t3531 = call i64 @freak_llvm_word_char_at(i64 %t3530, i64 %t3532)
    %c_v3533 = alloca i64
    store i64 %t3531, i64* %c_v3533
    %t3534 = load i64, i64* %c_v3533
    %t3535 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.228, i64 0, i64 0
    %t3536 = ptrtoint i8* %t3535 to i64
    %t3537 = call i64 @freak_llvm_word_eq(i64 %t3534, i64 %t3536)
    %t3541 = icmp ne i64 %t3537, 0
    br i1 %t3541, label %if.then.3538, label %if.end.3540
if.then.3538:
    %t3542 = load i64, i64* %res_v3516
    ret i64 %t3542
    br label %if.end.3540
if.end.3540:
    %t3543 = load i64, i64* %res_v3516
    %t3544 = load i64, i64* %c_v3533
    %t3545 = call i64 @freak_llvm_word_concat(i64 %t3543, i64 %t3544)
    store i64 %t3545, i64* %res_v3516
    %t3546 = load i64, i64* %i_v3518
    %t3547 = add i64 %t3546, 1
    store i64 %t3547, i64* %i_v3518
    br label %loop.cond.3522
loop.end.3524:
    %t3548 = load i64, i64* %res_v3516
    ret i64 %t3548
    ret i64 0
}

define i64 @freak_ver_parse_build(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3549 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.229, i64 0, i64 0
    %t3550 = ptrtoint i8* %t3549 to i64
    %res_v3551 = alloca i64
    store i64 %t3550, i64* %res_v3551
    %t3552 = load i64, i64* %start
    %i_v3553 = alloca i64
    store i64 %t3552, i64* %i_v3553
    %t3554 = load i64, i64* %s
    %t3555 = call i64 @freak_llvm_word_length(i64 %t3554)
    %slen_v3556 = alloca i64
    store i64 %t3555, i64* %slen_v3556
    br label %loop.cond.3557
loop.cond.3557:
    %t3560 = load i64, i64* %i_v3553
    %t3561 = load i64, i64* %slen_v3556
    %t3563 = icmp sge i64 %t3560, %t3561
    %t3562 = zext i1 %t3563 to i64
    %t3564 = icmp eq i64 %t3562, 0
    br i1 %t3564, label %loop.body.3558, label %loop.end.3559
loop.body.3558:
    %t3565 = load i64, i64* %res_v3551
    %t3566 = load i64, i64* %s
    %t3568 = load i64, i64* %i_v3553
    %t3567 = call i64 @freak_llvm_word_char_at(i64 %t3566, i64 %t3568)
    %t3569 = call i64 @freak_llvm_word_concat(i64 %t3565, i64 %t3567)
    store i64 %t3569, i64* %res_v3551
    %t3570 = load i64, i64* %i_v3553
    %t3571 = add i64 %t3570, 1
    store i64 %t3571, i64* %i_v3553
    br label %loop.cond.3557
loop.end.3559:
    %t3572 = load i64, i64* %res_v3551
    ret i64 %t3572
    ret i64 0
}

define i64 @freak_ver_get_val(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %t3573 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.230, i64 0, i64 0
    %t3574 = ptrtoint i8* %t3573 to i64
    %res_v3575 = alloca i64
    store i64 %t3574, i64* %res_v3575
    %i_v3576 = alloca i64
    store i64 0, i64* %i_v3576
    %t3577 = load i64, i64* %encoded
    %t3578 = call i64 @freak_llvm_word_length(i64 %t3577)
    %elen_v3579 = alloca i64
    store i64 %t3578, i64* %elen_v3579
    br label %loop.cond.3580
loop.cond.3580:
    %t3583 = load i64, i64* %i_v3576
    %t3584 = load i64, i64* %elen_v3579
    %t3586 = icmp sge i64 %t3583, %t3584
    %t3585 = zext i1 %t3586 to i64
    %t3587 = icmp eq i64 %t3585, 0
    br i1 %t3587, label %loop.body.3581, label %loop.end.3582
loop.body.3581:
    %t3588 = load i64, i64* %encoded
    %t3590 = load i64, i64* %i_v3576
    %t3589 = call i64 @freak_llvm_word_char_at(i64 %t3588, i64 %t3590)
    %c_v3591 = alloca i64
    store i64 %t3589, i64* %c_v3591
    %t3592 = load i64, i64* %c_v3591
    %t3593 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.231, i64 0, i64 0
    %t3594 = ptrtoint i8* %t3593 to i64
    %t3595 = call i64 @freak_llvm_word_eq(i64 %t3592, i64 %t3594)
    %t3599 = icmp ne i64 %t3595, 0
    br i1 %t3599, label %if.then.3596, label %if.end.3598
if.then.3596:
    %t3600 = load i64, i64* %res_v3575
    ret i64 %t3600
    br label %if.end.3598
if.end.3598:
    %t3601 = load i64, i64* %res_v3575
    %t3602 = load i64, i64* %c_v3591
    %t3603 = call i64 @freak_llvm_word_concat(i64 %t3601, i64 %t3602)
    store i64 %t3603, i64* %res_v3575
    %t3604 = load i64, i64* %i_v3576
    %t3605 = add i64 %t3604, 1
    store i64 %t3605, i64* %i_v3576
    br label %loop.cond.3580
loop.end.3582:
    %t3606 = load i64, i64* %res_v3575
    ret i64 %t3606
    ret i64 0
}

define i64 @freak_ver_get_pos(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %i_v3607 = alloca i64
    store i64 0, i64* %i_v3607
    %t3608 = load i64, i64* %encoded
    %t3609 = call i64 @freak_llvm_word_length(i64 %t3608)
    %elen_v3610 = alloca i64
    store i64 %t3609, i64* %elen_v3610
    br label %loop.cond.3611
loop.cond.3611:
    %t3614 = load i64, i64* %i_v3607
    %t3615 = load i64, i64* %elen_v3610
    %t3617 = icmp sge i64 %t3614, %t3615
    %t3616 = zext i1 %t3617 to i64
    %t3618 = icmp eq i64 %t3616, 0
    br i1 %t3618, label %loop.body.3612, label %loop.end.3613
loop.body.3612:
    %t3619 = load i64, i64* %encoded
    %t3621 = load i64, i64* %i_v3607
    %t3620 = call i64 @freak_llvm_word_char_at(i64 %t3619, i64 %t3621)
    %c_v3622 = alloca i64
    store i64 %t3620, i64* %c_v3622
    %t3623 = load i64, i64* %c_v3622
    %t3624 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.232, i64 0, i64 0
    %t3625 = ptrtoint i8* %t3624 to i64
    %t3626 = call i64 @freak_llvm_word_eq(i64 %t3623, i64 %t3625)
    %t3630 = icmp ne i64 %t3626, 0
    br i1 %t3630, label %if.then.3627, label %if.end.3629
if.then.3627:
    %t3631 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.233, i64 0, i64 0
    %t3632 = ptrtoint i8* %t3631 to i64
    %pos_str_v3633 = alloca i64
    store i64 %t3632, i64* %pos_str_v3633
    %t3634 = load i64, i64* %i_v3607
    %t3635 = add i64 %t3634, 1
    %j_v3636 = alloca i64
    store i64 %t3635, i64* %j_v3636
    br label %loop.cond.3637
loop.cond.3637:
    %t3640 = load i64, i64* %j_v3636
    %t3641 = load i64, i64* %elen_v3610
    %t3643 = icmp sge i64 %t3640, %t3641
    %t3642 = zext i1 %t3643 to i64
    %t3644 = icmp eq i64 %t3642, 0
    br i1 %t3644, label %loop.body.3638, label %loop.end.3639
loop.body.3638:
    %t3645 = load i64, i64* %pos_str_v3633
    %t3646 = load i64, i64* %encoded
    %t3648 = load i64, i64* %j_v3636
    %t3647 = call i64 @freak_llvm_word_char_at(i64 %t3646, i64 %t3648)
    %t3649 = call i64 @freak_llvm_word_concat(i64 %t3645, i64 %t3647)
    store i64 %t3649, i64* %pos_str_v3633
    %t3650 = load i64, i64* %j_v3636
    %t3651 = add i64 %t3650, 1
    store i64 %t3651, i64* %j_v3636
    br label %loop.cond.3637
loop.end.3639:
    %t3652 = load i64, i64* %pos_str_v3633
    %t3653 = call i64 @freak_llvm_word_to_int(i64 %t3652)
    ret i64 %t3653
    br label %if.end.3629
if.end.3629:
    %t3654 = load i64, i64* %i_v3607
    %t3655 = add i64 %t3654, 1
    store i64 %t3655, i64* %i_v3607
    br label %loop.cond.3611
loop.end.3613:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_parse(i64 %arg_version) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %t3656 = load i64, i64* %version
    %s_v3657 = alloca i64
    store i64 %t3656, i64* %s_v3657
    %t3658 = load i64, i64* %s_v3657
    %t3659 = call i64 @freak_llvm_word_length(i64 %t3658)
    %t3661 = icmp sgt i64 %t3659, 0
    %t3660 = zext i1 %t3661 to i64
    %t3665 = icmp ne i64 %t3660, 0
    br i1 %t3665, label %if.then.3662, label %if.end.3664
if.then.3662:
    %t3666 = load i64, i64* %s_v3657
    %t3667 = call i64 @freak_llvm_word_char_at(i64 %t3666, i64 0)
    %fc_v3668 = alloca i64
    store i64 %t3667, i64* %fc_v3668
    %t3669 = load i64, i64* %fc_v3668
    %t3670 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.234, i64 0, i64 0
    %t3671 = ptrtoint i8* %t3670 to i64
    %t3672 = call i64 @freak_llvm_word_eq(i64 %t3669, i64 %t3671)
    %t3673 = load i64, i64* %fc_v3668
    %t3674 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.235, i64 0, i64 0
    %t3675 = ptrtoint i8* %t3674 to i64
    %t3676 = call i64 @freak_llvm_word_eq(i64 %t3673, i64 %t3675)
    %t3678 = icmp ne i64 %t3672, 0
    %t3679 = icmp ne i64 %t3676, 0
    %t3680 = or i1 %t3678, %t3679
    %t3677 = zext i1 %t3680 to i64
    %t3684 = icmp ne i64 %t3677, 0
    br i1 %t3684, label %if.then.3681, label %if.end.3683
if.then.3681:
    %t3685 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.236, i64 0, i64 0
    %t3686 = ptrtoint i8* %t3685 to i64
    %ns_v3687 = alloca i64
    store i64 %t3686, i64* %ns_v3687
    %vi_v3688 = alloca i64
    store i64 1, i64* %vi_v3688
    br label %loop.cond.3689
loop.cond.3689:
    %t3692 = load i64, i64* %vi_v3688
    %t3693 = load i64, i64* %s_v3657
    %t3694 = call i64 @freak_llvm_word_length(i64 %t3693)
    %t3696 = icmp sge i64 %t3692, %t3694
    %t3695 = zext i1 %t3696 to i64
    %t3697 = icmp eq i64 %t3695, 0
    br i1 %t3697, label %loop.body.3690, label %loop.end.3691
loop.body.3690:
    %t3698 = load i64, i64* %ns_v3687
    %t3699 = load i64, i64* %s_v3657
    %t3701 = load i64, i64* %vi_v3688
    %t3700 = call i64 @freak_llvm_word_char_at(i64 %t3699, i64 %t3701)
    %t3702 = call i64 @freak_llvm_word_concat(i64 %t3698, i64 %t3700)
    store i64 %t3702, i64* %ns_v3687
    %t3703 = load i64, i64* %vi_v3688
    %t3704 = add i64 %t3703, 1
    store i64 %t3704, i64* %vi_v3688
    br label %loop.cond.3689
loop.end.3691:
    %t3705 = load i64, i64* %ns_v3687
    store i64 %t3705, i64* %s_v3657
    br label %if.end.3683
if.end.3683:
    br label %if.end.3664
if.end.3664:
    %t3706 = load i64, i64* %s_v3657
    %t3707 = call i64 @freak_ver_parse_num(i64 %t3706, i64 0)
    %r1_v3708 = alloca i64
    store i64 %t3707, i64* %r1_v3708
    %t3709 = load i64, i64* %r1_v3708
    %t3710 = call i64 @freak_ver_get_val(i64 %t3709)
    %major_v3711 = alloca i64
    store i64 %t3710, i64* %major_v3711
    %t3712 = load i64, i64* %r1_v3708
    %t3713 = call i64 @freak_ver_get_pos(i64 %t3712)
    %pos1_v3714 = alloca i64
    store i64 %t3713, i64* %pos1_v3714
    %t3715 = load i64, i64* %s_v3657
    %t3716 = load i64, i64* %pos1_v3714
    %t3717 = call i64 @freak_ver_parse_num(i64 %t3715, i64 %t3716)
    %r2_v3718 = alloca i64
    store i64 %t3717, i64* %r2_v3718
    %t3719 = load i64, i64* %r2_v3718
    %t3720 = call i64 @freak_ver_get_val(i64 %t3719)
    %minor_v3721 = alloca i64
    store i64 %t3720, i64* %minor_v3721
    %t3722 = load i64, i64* %r2_v3718
    %t3723 = call i64 @freak_ver_get_pos(i64 %t3722)
    %pos2_v3724 = alloca i64
    store i64 %t3723, i64* %pos2_v3724
    %t3725 = load i64, i64* %s_v3657
    %t3726 = load i64, i64* %pos2_v3724
    %t3727 = call i64 @freak_ver_parse_num(i64 %t3725, i64 %t3726)
    %r3_v3728 = alloca i64
    store i64 %t3727, i64* %r3_v3728
    %t3729 = load i64, i64* %r3_v3728
    %t3730 = call i64 @freak_ver_get_val(i64 %t3729)
    %patch_v3731 = alloca i64
    store i64 %t3730, i64* %patch_v3731
    %t3732 = load i64, i64* %r3_v3728
    %t3733 = call i64 @freak_ver_get_pos(i64 %t3732)
    %pos3_v3734 = alloca i64
    store i64 %t3733, i64* %pos3_v3734
    %t3735 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.237, i64 0, i64 0
    %t3736 = ptrtoint i8* %t3735 to i64
    %pre_v3737 = alloca i64
    store i64 %t3736, i64* %pre_v3737
    %t3738 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.238, i64 0, i64 0
    %t3739 = ptrtoint i8* %t3738 to i64
    %bld_v3740 = alloca i64
    store i64 %t3739, i64* %bld_v3740
    %t3741 = load i64, i64* %pos3_v3734
    %t3742 = load i64, i64* %s_v3657
    %t3743 = call i64 @freak_llvm_word_length(i64 %t3742)
    %t3745 = icmp sle i64 %t3741, %t3743
    %t3744 = zext i1 %t3745 to i64
    %t3749 = icmp ne i64 %t3744, 0
    br i1 %t3749, label %if.then.3746, label %if.end.3748
if.then.3746:
    %t3750 = load i64, i64* %pos3_v3734
    %t3752 = icmp sgt i64 %t3750, 0
    %t3751 = zext i1 %t3752 to i64
    %t3756 = icmp ne i64 %t3751, 0
    br i1 %t3756, label %if.then.3753, label %if.end.3755
if.then.3753:
    %t3757 = load i64, i64* %s_v3657
    %t3759 = load i64, i64* %pos3_v3734
    %t3760 = sub i64 %t3759, 1
    %t3758 = call i64 @freak_llvm_word_char_at(i64 %t3757, i64 %t3760)
    %delim_v3761 = alloca i64
    store i64 %t3758, i64* %delim_v3761
    %t3762 = load i64, i64* %delim_v3761
    %t3763 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.239, i64 0, i64 0
    %t3764 = ptrtoint i8* %t3763 to i64
    %t3765 = call i64 @freak_llvm_word_eq(i64 %t3762, i64 %t3764)
    %t3769 = icmp ne i64 %t3765, 0
    br i1 %t3769, label %if.then.3766, label %if.else.3767
if.then.3766:
    %t3770 = load i64, i64* %s_v3657
    %t3771 = load i64, i64* %pos3_v3734
    %t3772 = call i64 @freak_ver_parse_pre(i64 %t3770, i64 %t3771)
    store i64 %t3772, i64* %pre_v3737
    br label %if.end.3768
if.else.3767:
    %t3773 = load i64, i64* %delim_v3761
    %t3774 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.240, i64 0, i64 0
    %t3775 = ptrtoint i8* %t3774 to i64
    %t3776 = call i64 @freak_llvm_word_eq(i64 %t3773, i64 %t3775)
    %t3780 = icmp ne i64 %t3776, 0
    br i1 %t3780, label %if.then.3777, label %if.end.3779
if.then.3777:
    %t3781 = load i64, i64* %s_v3657
    %t3782 = load i64, i64* %pos3_v3734
    %t3783 = call i64 @freak_ver_parse_build(i64 %t3781, i64 %t3782)
    store i64 %t3783, i64* %bld_v3740
    br label %if.end.3779
if.end.3779:
    br label %if.end.3768
if.end.3768:
    br label %if.end.3755
if.end.3755:
    br label %if.end.3748
if.end.3748:
    %t3784 = load i64, i64* %pre_v3737
    %t3785 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.241, i64 0, i64 0
    %t3786 = ptrtoint i8* %t3785 to i64
    %t3787 = call i64 @freak_llvm_word_neq(i64 %t3784, i64 %t3786)
    %t3791 = icmp ne i64 %t3787, 0
    br i1 %t3791, label %if.then.3788, label %if.end.3790
if.then.3788:
    %pi_v3792 = alloca i64
    store i64 0, i64* %pi_v3792
    %t3793 = load i64, i64* %s_v3657
    %t3794 = call i64 @freak_llvm_word_length(i64 %t3793)
    %plen_v3795 = alloca i64
    store i64 %t3794, i64* %plen_v3795
    br label %loop.cond.3796
loop.cond.3796:
    %t3799 = load i64, i64* %pi_v3792
    %t3800 = load i64, i64* %plen_v3795
    %t3802 = icmp sge i64 %t3799, %t3800
    %t3801 = zext i1 %t3802 to i64
    %t3803 = icmp eq i64 %t3801, 0
    br i1 %t3803, label %loop.body.3797, label %loop.end.3798
loop.body.3797:
    %t3804 = load i64, i64* %s_v3657
    %t3806 = load i64, i64* %pi_v3792
    %t3805 = call i64 @freak_llvm_word_char_at(i64 %t3804, i64 %t3806)
    %t3807 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.242, i64 0, i64 0
    %t3808 = ptrtoint i8* %t3807 to i64
    %t3809 = call i64 @freak_llvm_word_eq(i64 %t3805, i64 %t3808)
    %t3813 = icmp ne i64 %t3809, 0
    br i1 %t3813, label %if.then.3810, label %if.end.3812
if.then.3810:
    %t3814 = load i64, i64* %s_v3657
    %t3815 = load i64, i64* %pi_v3792
    %t3816 = add i64 %t3815, 1
    %t3817 = call i64 @freak_ver_parse_build(i64 %t3814, i64 %t3816)
    store i64 %t3817, i64* %bld_v3740
    br label %if.end.3812
if.end.3812:
    %t3818 = load i64, i64* %pi_v3792
    %t3819 = add i64 %t3818, 1
    store i64 %t3819, i64* %pi_v3792
    br label %loop.cond.3796
loop.end.3798:
    br label %if.end.3790
if.end.3790:
    %t3820 = load i64, i64* %major_v3711
    %t3821 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.243, i64 0, i64 0
    %t3822 = ptrtoint i8* %t3821 to i64
    %t3823 = call i64 @freak_llvm_word_concat(i64 %t3820, i64 %t3822)
    %t3824 = load i64, i64* %minor_v3721
    %t3825 = call i64 @freak_llvm_word_concat(i64 %t3823, i64 %t3824)
    %t3826 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.244, i64 0, i64 0
    %t3827 = ptrtoint i8* %t3826 to i64
    %t3828 = call i64 @freak_llvm_word_concat(i64 %t3825, i64 %t3827)
    %t3829 = load i64, i64* %patch_v3731
    %t3830 = call i64 @freak_llvm_word_concat(i64 %t3828, i64 %t3829)
    %t3831 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.245, i64 0, i64 0
    %t3832 = ptrtoint i8* %t3831 to i64
    %t3833 = call i64 @freak_llvm_word_concat(i64 %t3830, i64 %t3832)
    %t3834 = load i64, i64* %pre_v3737
    %t3835 = call i64 @freak_llvm_word_concat(i64 %t3833, i64 %t3834)
    %t3836 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.246, i64 0, i64 0
    %t3837 = ptrtoint i8* %t3836 to i64
    %t3838 = call i64 @freak_llvm_word_concat(i64 %t3835, i64 %t3837)
    %t3839 = load i64, i64* %bld_v3740
    %t3840 = call i64 @freak_llvm_word_concat(i64 %t3838, i64 %t3839)
    ret i64 %t3840
    ret i64 0
}

define i64 @freak_ver_field(i64 %arg_parsed, i64 %arg_field_idx) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %field_idx = alloca i64
    store i64 %arg_field_idx, i64* %field_idx
    %t3841 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.247, i64 0, i64 0
    %t3842 = ptrtoint i8* %t3841 to i64
    %res_v3843 = alloca i64
    store i64 %t3842, i64* %res_v3843
    %current_field_v3844 = alloca i64
    store i64 0, i64* %current_field_v3844
    %i_v3845 = alloca i64
    store i64 0, i64* %i_v3845
    %t3846 = load i64, i64* %parsed
    %t3847 = call i64 @freak_llvm_word_length(i64 %t3846)
    %plen_v3848 = alloca i64
    store i64 %t3847, i64* %plen_v3848
    br label %loop.cond.3849
loop.cond.3849:
    %t3852 = load i64, i64* %i_v3845
    %t3853 = load i64, i64* %plen_v3848
    %t3855 = icmp sge i64 %t3852, %t3853
    %t3854 = zext i1 %t3855 to i64
    %t3856 = icmp eq i64 %t3854, 0
    br i1 %t3856, label %loop.body.3850, label %loop.end.3851
loop.body.3850:
    %t3857 = load i64, i64* %parsed
    %t3859 = load i64, i64* %i_v3845
    %t3858 = call i64 @freak_llvm_word_char_at(i64 %t3857, i64 %t3859)
    %c_v3860 = alloca i64
    store i64 %t3858, i64* %c_v3860
    %t3861 = load i64, i64* %c_v3860
    %t3862 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.248, i64 0, i64 0
    %t3863 = ptrtoint i8* %t3862 to i64
    %t3864 = call i64 @freak_llvm_word_eq(i64 %t3861, i64 %t3863)
    %t3868 = icmp ne i64 %t3864, 0
    br i1 %t3868, label %if.then.3865, label %if.else.3866
if.then.3865:
    %t3869 = load i64, i64* %current_field_v3844
    %t3870 = load i64, i64* %field_idx
    %t3872 = icmp eq i64 %t3869, %t3870
    %t3871 = zext i1 %t3872 to i64
    %t3876 = icmp ne i64 %t3871, 0
    br i1 %t3876, label %if.then.3873, label %if.end.3875
if.then.3873:
    %t3877 = load i64, i64* %res_v3843
    ret i64 %t3877
    br label %if.end.3875
if.end.3875:
    %t3878 = load i64, i64* %current_field_v3844
    %t3879 = add i64 %t3878, 1
    store i64 %t3879, i64* %current_field_v3844
    %t3880 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.249, i64 0, i64 0
    %t3881 = ptrtoint i8* %t3880 to i64
    store i64 %t3881, i64* %res_v3843
    br label %if.end.3867
if.else.3866:
    %t3882 = load i64, i64* %res_v3843
    %t3883 = load i64, i64* %c_v3860
    %t3884 = call i64 @freak_llvm_word_concat(i64 %t3882, i64 %t3883)
    store i64 %t3884, i64* %res_v3843
    br label %if.end.3867
if.end.3867:
    %t3885 = load i64, i64* %i_v3845
    %t3886 = add i64 %t3885, 1
    store i64 %t3886, i64* %i_v3845
    br label %loop.cond.3849
loop.end.3851:
    %t3887 = load i64, i64* %current_field_v3844
    %t3888 = load i64, i64* %field_idx
    %t3890 = icmp eq i64 %t3887, %t3888
    %t3889 = zext i1 %t3890 to i64
    %t3894 = icmp ne i64 %t3889, 0
    br i1 %t3894, label %if.then.3891, label %if.end.3893
if.then.3891:
    %t3895 = load i64, i64* %res_v3843
    ret i64 %t3895
    br label %if.end.3893
if.end.3893:
    %t3896 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.250, i64 0, i64 0
    %t3897 = ptrtoint i8* %t3896 to i64
    ret i64 %t3897
    ret i64 0
}

define i64 @freak_ver_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3898 = load i64, i64* %parsed
    %t3899 = call i64 @freak_ver_field(i64 %t3898, i64 0)
    %t3900 = call i64 @freak_llvm_word_to_int(i64 %t3899)
    ret i64 %t3900
    ret i64 0
}

define i64 @freak_ver_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3901 = load i64, i64* %parsed
    %t3902 = call i64 @freak_ver_field(i64 %t3901, i64 1)
    %t3903 = call i64 @freak_llvm_word_to_int(i64 %t3902)
    ret i64 %t3903
    ret i64 0
}

define i64 @freak_ver_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3904 = load i64, i64* %parsed
    %t3905 = call i64 @freak_ver_field(i64 %t3904, i64 2)
    %t3906 = call i64 @freak_llvm_word_to_int(i64 %t3905)
    ret i64 %t3906
    ret i64 0
}

define i64 @freak_ver_pre(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3907 = load i64, i64* %parsed
    %t3908 = call i64 @freak_ver_field(i64 %t3907, i64 3)
    ret i64 %t3908
    ret i64 0
}

define i64 @freak_ver_build(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3909 = load i64, i64* %parsed
    %t3910 = call i64 @freak_ver_field(i64 %t3909, i64 4)
    ret i64 %t3910
    ret i64 0
}

define i64 @freak_ver_to_string(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3911 = load i64, i64* %parsed
    %t3912 = call i64 @freak_ver_field(i64 %t3911, i64 0)
    %maj_v3913 = alloca i64
    store i64 %t3912, i64* %maj_v3913
    %t3914 = load i64, i64* %parsed
    %t3915 = call i64 @freak_ver_field(i64 %t3914, i64 1)
    %min_v3916 = alloca i64
    store i64 %t3915, i64* %min_v3916
    %t3917 = load i64, i64* %parsed
    %t3918 = call i64 @freak_ver_field(i64 %t3917, i64 2)
    %pat_v3919 = alloca i64
    store i64 %t3918, i64* %pat_v3919
    %t3920 = load i64, i64* %parsed
    %t3921 = call i64 @freak_ver_field(i64 %t3920, i64 3)
    %pre_v3922 = alloca i64
    store i64 %t3921, i64* %pre_v3922
    %t3923 = load i64, i64* %parsed
    %t3924 = call i64 @freak_ver_field(i64 %t3923, i64 4)
    %bld_v3925 = alloca i64
    store i64 %t3924, i64* %bld_v3925
    %t3926 = load i64, i64* %maj_v3913
    %t3927 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.251, i64 0, i64 0
    %t3928 = ptrtoint i8* %t3927 to i64
    %t3929 = call i64 @freak_llvm_word_concat(i64 %t3926, i64 %t3928)
    %t3930 = load i64, i64* %min_v3916
    %t3931 = call i64 @freak_llvm_word_concat(i64 %t3929, i64 %t3930)
    %t3932 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.252, i64 0, i64 0
    %t3933 = ptrtoint i8* %t3932 to i64
    %t3934 = call i64 @freak_llvm_word_concat(i64 %t3931, i64 %t3933)
    %t3935 = load i64, i64* %pat_v3919
    %t3936 = call i64 @freak_llvm_word_concat(i64 %t3934, i64 %t3935)
    %out_v3937 = alloca i64
    store i64 %t3936, i64* %out_v3937
    %t3938 = load i64, i64* %pre_v3922
    %t3939 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.253, i64 0, i64 0
    %t3940 = ptrtoint i8* %t3939 to i64
    %t3941 = call i64 @freak_llvm_word_neq(i64 %t3938, i64 %t3940)
    %t3945 = icmp ne i64 %t3941, 0
    br i1 %t3945, label %if.then.3942, label %if.end.3944
if.then.3942:
    %t3946 = load i64, i64* %out_v3937
    %t3947 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.254, i64 0, i64 0
    %t3948 = ptrtoint i8* %t3947 to i64
    %t3949 = call i64 @freak_llvm_word_concat(i64 %t3946, i64 %t3948)
    %t3950 = load i64, i64* %pre_v3922
    %t3951 = call i64 @freak_llvm_word_concat(i64 %t3949, i64 %t3950)
    store i64 %t3951, i64* %out_v3937
    br label %if.end.3944
if.end.3944:
    %t3952 = load i64, i64* %bld_v3925
    %t3953 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.255, i64 0, i64 0
    %t3954 = ptrtoint i8* %t3953 to i64
    %t3955 = call i64 @freak_llvm_word_neq(i64 %t3952, i64 %t3954)
    %t3959 = icmp ne i64 %t3955, 0
    br i1 %t3959, label %if.then.3956, label %if.end.3958
if.then.3956:
    %t3960 = load i64, i64* %out_v3937
    %t3961 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.256, i64 0, i64 0
    %t3962 = ptrtoint i8* %t3961 to i64
    %t3963 = call i64 @freak_llvm_word_concat(i64 %t3960, i64 %t3962)
    %t3964 = load i64, i64* %bld_v3925
    %t3965 = call i64 @freak_llvm_word_concat(i64 %t3963, i64 %t3964)
    store i64 %t3965, i64* %out_v3937
    br label %if.end.3958
if.end.3958:
    %t3966 = load i64, i64* %out_v3937
    ret i64 %t3966
    ret i64 0
}

define i64 @freak_ver_compare(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t3967 = load i64, i64* %a
    %t3968 = call i64 @freak_ver_major(i64 %t3967)
    %a_major_v3969 = alloca i64
    store i64 %t3968, i64* %a_major_v3969
    %t3970 = load i64, i64* %b
    %t3971 = call i64 @freak_ver_major(i64 %t3970)
    %b_major_v3972 = alloca i64
    store i64 %t3971, i64* %b_major_v3972
    %t3973 = load i64, i64* %a_major_v3969
    %t3974 = load i64, i64* %b_major_v3972
    %t3976 = icmp slt i64 %t3973, %t3974
    %t3975 = zext i1 %t3976 to i64
    %t3980 = icmp ne i64 %t3975, 0
    br i1 %t3980, label %if.then.3977, label %if.end.3979
if.then.3977:
    %t3981 = sub i64 0, 1
    ret i64 %t3981
    br label %if.end.3979
if.end.3979:
    %t3982 = load i64, i64* %a_major_v3969
    %t3983 = load i64, i64* %b_major_v3972
    %t3985 = icmp sgt i64 %t3982, %t3983
    %t3984 = zext i1 %t3985 to i64
    %t3989 = icmp ne i64 %t3984, 0
    br i1 %t3989, label %if.then.3986, label %if.end.3988
if.then.3986:
    ret i64 1
    br label %if.end.3988
if.end.3988:
    %t3990 = load i64, i64* %a
    %t3991 = call i64 @freak_ver_minor(i64 %t3990)
    %a_minor_v3992 = alloca i64
    store i64 %t3991, i64* %a_minor_v3992
    %t3993 = load i64, i64* %b
    %t3994 = call i64 @freak_ver_minor(i64 %t3993)
    %b_minor_v3995 = alloca i64
    store i64 %t3994, i64* %b_minor_v3995
    %t3996 = load i64, i64* %a_minor_v3992
    %t3997 = load i64, i64* %b_minor_v3995
    %t3999 = icmp slt i64 %t3996, %t3997
    %t3998 = zext i1 %t3999 to i64
    %t4003 = icmp ne i64 %t3998, 0
    br i1 %t4003, label %if.then.4000, label %if.end.4002
if.then.4000:
    %t4004 = sub i64 0, 1
    ret i64 %t4004
    br label %if.end.4002
if.end.4002:
    %t4005 = load i64, i64* %a_minor_v3992
    %t4006 = load i64, i64* %b_minor_v3995
    %t4008 = icmp sgt i64 %t4005, %t4006
    %t4007 = zext i1 %t4008 to i64
    %t4012 = icmp ne i64 %t4007, 0
    br i1 %t4012, label %if.then.4009, label %if.end.4011
if.then.4009:
    ret i64 1
    br label %if.end.4011
if.end.4011:
    %t4013 = load i64, i64* %a
    %t4014 = call i64 @freak_ver_patch(i64 %t4013)
    %a_patch_v4015 = alloca i64
    store i64 %t4014, i64* %a_patch_v4015
    %t4016 = load i64, i64* %b
    %t4017 = call i64 @freak_ver_patch(i64 %t4016)
    %b_patch_v4018 = alloca i64
    store i64 %t4017, i64* %b_patch_v4018
    %t4019 = load i64, i64* %a_patch_v4015
    %t4020 = load i64, i64* %b_patch_v4018
    %t4022 = icmp slt i64 %t4019, %t4020
    %t4021 = zext i1 %t4022 to i64
    %t4026 = icmp ne i64 %t4021, 0
    br i1 %t4026, label %if.then.4023, label %if.end.4025
if.then.4023:
    %t4027 = sub i64 0, 1
    ret i64 %t4027
    br label %if.end.4025
if.end.4025:
    %t4028 = load i64, i64* %a_patch_v4015
    %t4029 = load i64, i64* %b_patch_v4018
    %t4031 = icmp sgt i64 %t4028, %t4029
    %t4030 = zext i1 %t4031 to i64
    %t4035 = icmp ne i64 %t4030, 0
    br i1 %t4035, label %if.then.4032, label %if.end.4034
if.then.4032:
    ret i64 1
    br label %if.end.4034
if.end.4034:
    %t4036 = load i64, i64* %a
    %t4037 = call i64 @freak_ver_pre(i64 %t4036)
    %a_pre_v4038 = alloca i64
    store i64 %t4037, i64* %a_pre_v4038
    %t4039 = load i64, i64* %b
    %t4040 = call i64 @freak_ver_pre(i64 %t4039)
    %b_pre_v4041 = alloca i64
    store i64 %t4040, i64* %b_pre_v4041
    %t4042 = load i64, i64* %a_pre_v4038
    %t4043 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.257, i64 0, i64 0
    %t4044 = ptrtoint i8* %t4043 to i64
    %t4045 = call i64 @freak_llvm_word_eq(i64 %t4042, i64 %t4044)
    %t4046 = load i64, i64* %b_pre_v4041
    %t4047 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.258, i64 0, i64 0
    %t4048 = ptrtoint i8* %t4047 to i64
    %t4049 = call i64 @freak_llvm_word_neq(i64 %t4046, i64 %t4048)
    %t4051 = icmp ne i64 %t4045, 0
    %t4052 = icmp ne i64 %t4049, 0
    %t4053 = and i1 %t4051, %t4052
    %t4050 = zext i1 %t4053 to i64
    %t4057 = icmp ne i64 %t4050, 0
    br i1 %t4057, label %if.then.4054, label %if.end.4056
if.then.4054:
    ret i64 1
    br label %if.end.4056
if.end.4056:
    %t4058 = load i64, i64* %a_pre_v4038
    %t4059 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.259, i64 0, i64 0
    %t4060 = ptrtoint i8* %t4059 to i64
    %t4061 = call i64 @freak_llvm_word_neq(i64 %t4058, i64 %t4060)
    %t4062 = load i64, i64* %b_pre_v4041
    %t4063 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.260, i64 0, i64 0
    %t4064 = ptrtoint i8* %t4063 to i64
    %t4065 = call i64 @freak_llvm_word_eq(i64 %t4062, i64 %t4064)
    %t4067 = icmp ne i64 %t4061, 0
    %t4068 = icmp ne i64 %t4065, 0
    %t4069 = and i1 %t4067, %t4068
    %t4066 = zext i1 %t4069 to i64
    %t4073 = icmp ne i64 %t4066, 0
    br i1 %t4073, label %if.then.4070, label %if.end.4072
if.then.4070:
    %t4074 = sub i64 0, 1
    ret i64 %t4074
    br label %if.end.4072
if.end.4072:
    %t4075 = load i64, i64* %a_pre_v4038
    %t4076 = call i64 @freak_llvm_word_length(i64 %t4075)
    %cmp_len_v4077 = alloca i64
    store i64 %t4076, i64* %cmp_len_v4077
    %t4078 = load i64, i64* %b_pre_v4041
    %t4079 = call i64 @freak_llvm_word_length(i64 %t4078)
    %t4080 = load i64, i64* %cmp_len_v4077
    %t4082 = icmp slt i64 %t4079, %t4080
    %t4081 = zext i1 %t4082 to i64
    %t4086 = icmp ne i64 %t4081, 0
    br i1 %t4086, label %if.then.4083, label %if.end.4085
if.then.4083:
    %t4087 = load i64, i64* %b_pre_v4041
    %t4088 = call i64 @freak_llvm_word_length(i64 %t4087)
    store i64 %t4088, i64* %cmp_len_v4077
    br label %if.end.4085
if.end.4085:
    %ci_v4089 = alloca i64
    store i64 0, i64* %ci_v4089
    br label %loop.cond.4090
loop.cond.4090:
    %t4093 = load i64, i64* %ci_v4089
    %t4094 = load i64, i64* %cmp_len_v4077
    %t4096 = icmp sge i64 %t4093, %t4094
    %t4095 = zext i1 %t4096 to i64
    %t4097 = icmp eq i64 %t4095, 0
    br i1 %t4097, label %loop.body.4091, label %loop.end.4092
loop.body.4091:
    %t4098 = load i64, i64* %a_pre_v4038
    %t4100 = load i64, i64* %ci_v4089
    %t4099 = call i64 @freak_llvm_word_char_at(i64 %t4098, i64 %t4100)
    %ac_v4101 = alloca i64
    store i64 %t4099, i64* %ac_v4101
    %t4102 = load i64, i64* %b_pre_v4041
    %t4104 = load i64, i64* %ci_v4089
    %t4103 = call i64 @freak_llvm_word_char_at(i64 %t4102, i64 %t4104)
    %bc_v4105 = alloca i64
    store i64 %t4103, i64* %bc_v4105
    %t4106 = load i64, i64* %ac_v4101
    %t4107 = load i64, i64* %bc_v4105
    %t4108 = call i64 @freak_llvm_word_neq(i64 %t4106, i64 %t4107)
    %t4112 = icmp ne i64 %t4108, 0
    br i1 %t4112, label %if.then.4109, label %if.end.4111
if.then.4109:
    %t4113 = load i64, i64* %ac_v4101
    %t4114 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.261, i64 0, i64 0
    %t4115 = ptrtoint i8* %t4114 to i64
    %t4116 = call i64 @freak_llvm_word_eq(i64 %t4113, i64 %t4115)
    %t4117 = load i64, i64* %bc_v4105
    %t4118 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.262, i64 0, i64 0
    %t4119 = ptrtoint i8* %t4118 to i64
    %t4120 = call i64 @freak_llvm_word_eq(i64 %t4117, i64 %t4119)
    %t4122 = icmp ne i64 %t4116, 0
    %t4123 = icmp ne i64 %t4120, 0
    %t4124 = and i1 %t4122, %t4123
    %t4121 = zext i1 %t4124 to i64
    %t4128 = icmp ne i64 %t4121, 0
    br i1 %t4128, label %if.then.4125, label %if.end.4127
if.then.4125:
    %t4129 = sub i64 0, 1
    ret i64 %t4129
    br label %if.end.4127
if.end.4127:
    %t4130 = load i64, i64* %ac_v4101
    %t4131 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.263, i64 0, i64 0
    %t4132 = ptrtoint i8* %t4131 to i64
    %t4133 = call i64 @freak_llvm_word_eq(i64 %t4130, i64 %t4132)
    %t4134 = load i64, i64* %bc_v4105
    %t4135 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.264, i64 0, i64 0
    %t4136 = ptrtoint i8* %t4135 to i64
    %t4137 = call i64 @freak_llvm_word_eq(i64 %t4134, i64 %t4136)
    %t4139 = icmp ne i64 %t4133, 0
    %t4140 = icmp ne i64 %t4137, 0
    %t4141 = and i1 %t4139, %t4140
    %t4138 = zext i1 %t4141 to i64
    %t4145 = icmp ne i64 %t4138, 0
    br i1 %t4145, label %if.then.4142, label %if.end.4144
if.then.4142:
    ret i64 1
    br label %if.end.4144
if.end.4144:
    %t4146 = load i64, i64* %ac_v4101
    %t4147 = call i64 @freak_llvm_word_to_int(i64 %t4146)
    %ai_v4148 = alloca i64
    store i64 %t4147, i64* %ai_v4148
    %t4149 = load i64, i64* %bc_v4105
    %t4150 = call i64 @freak_llvm_word_to_int(i64 %t4149)
    %bi_v4151 = alloca i64
    store i64 %t4150, i64* %bi_v4151
    %t4152 = load i64, i64* %ai_v4148
    %t4153 = load i64, i64* %bi_v4151
    %t4155 = icmp slt i64 %t4152, %t4153
    %t4154 = zext i1 %t4155 to i64
    %t4159 = icmp ne i64 %t4154, 0
    br i1 %t4159, label %if.then.4156, label %if.end.4158
if.then.4156:
    %t4160 = sub i64 0, 1
    ret i64 %t4160
    br label %if.end.4158
if.end.4158:
    %t4161 = load i64, i64* %ai_v4148
    %t4162 = load i64, i64* %bi_v4151
    %t4164 = icmp sgt i64 %t4161, %t4162
    %t4163 = zext i1 %t4164 to i64
    %t4168 = icmp ne i64 %t4163, 0
    br i1 %t4168, label %if.then.4165, label %if.end.4167
if.then.4165:
    ret i64 1
    br label %if.end.4167
if.end.4167:
    br label %if.end.4111
if.end.4111:
    %t4169 = load i64, i64* %ci_v4089
    %t4170 = add i64 %t4169, 1
    store i64 %t4170, i64* %ci_v4089
    br label %loop.cond.4090
loop.end.4092:
    %t4171 = load i64, i64* %a_pre_v4038
    %t4172 = call i64 @freak_llvm_word_length(i64 %t4171)
    %t4173 = load i64, i64* %b_pre_v4041
    %t4174 = call i64 @freak_llvm_word_length(i64 %t4173)
    %t4176 = icmp slt i64 %t4172, %t4174
    %t4175 = zext i1 %t4176 to i64
    %t4180 = icmp ne i64 %t4175, 0
    br i1 %t4180, label %if.then.4177, label %if.end.4179
if.then.4177:
    %t4181 = sub i64 0, 1
    ret i64 %t4181
    br label %if.end.4179
if.end.4179:
    %t4182 = load i64, i64* %a_pre_v4038
    %t4183 = call i64 @freak_llvm_word_length(i64 %t4182)
    %t4184 = load i64, i64* %b_pre_v4041
    %t4185 = call i64 @freak_llvm_word_length(i64 %t4184)
    %t4187 = icmp sgt i64 %t4183, %t4185
    %t4186 = zext i1 %t4187 to i64
    %t4191 = icmp ne i64 %t4186, 0
    br i1 %t4191, label %if.then.4188, label %if.end.4190
if.then.4188:
    ret i64 1
    br label %if.end.4190
if.end.4190:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_eq(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4192 = load i64, i64* %a
    %t4193 = load i64, i64* %b
    %t4194 = call i64 @freak_ver_compare(i64 %t4192, i64 %t4193)
    %t4196 = icmp eq i64 %t4194, 0
    %t4195 = zext i1 %t4196 to i64
    ret i64 %t4195
    ret i64 0
}

define i64 @freak_ver_lt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4197 = load i64, i64* %a
    %t4198 = load i64, i64* %b
    %t4199 = call i64 @freak_ver_compare(i64 %t4197, i64 %t4198)
    %t4201 = icmp slt i64 %t4199, 0
    %t4200 = zext i1 %t4201 to i64
    ret i64 %t4200
    ret i64 0
}

define i64 @freak_ver_gt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4202 = load i64, i64* %a
    %t4203 = load i64, i64* %b
    %t4204 = call i64 @freak_ver_compare(i64 %t4202, i64 %t4203)
    %t4206 = icmp sgt i64 %t4204, 0
    %t4205 = zext i1 %t4206 to i64
    ret i64 %t4205
    ret i64 0
}

define i64 @freak_ver_lte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4207 = load i64, i64* %a
    %t4208 = load i64, i64* %b
    %t4209 = call i64 @freak_ver_compare(i64 %t4207, i64 %t4208)
    %t4211 = icmp sle i64 %t4209, 0
    %t4210 = zext i1 %t4211 to i64
    ret i64 %t4210
    ret i64 0
}

define i64 @freak_ver_gte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4212 = load i64, i64* %a
    %t4213 = load i64, i64* %b
    %t4214 = call i64 @freak_ver_compare(i64 %t4212, i64 %t4213)
    %t4216 = icmp sge i64 %t4214, 0
    %t4215 = zext i1 %t4216 to i64
    ret i64 %t4215
    ret i64 0
}

define i64 @freak_ver_bump_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4217 = load i64, i64* %parsed
    %t4218 = call i64 @freak_ver_major(i64 %t4217)
    %t4219 = add i64 %t4218, 1
    %maj_v4220 = alloca i64
    store i64 %t4219, i64* %maj_v4220
    %t4221 = load i64, i64* %maj_v4220
    %t4222 = call i64 @freak_llvm_word_from_int(i64 %t4221)
    %t4223 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.265, i64 0, i64 0
    %t4224 = ptrtoint i8* %t4223 to i64
    %t4225 = call i64 @freak_llvm_word_concat(i64 %t4222, i64 %t4224)
    ret i64 %t4225
    ret i64 0
}

define i64 @freak_ver_bump_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4226 = load i64, i64* %parsed
    %t4227 = call i64 @freak_ver_major(i64 %t4226)
    %maj_v4228 = alloca i64
    store i64 %t4227, i64* %maj_v4228
    %t4229 = load i64, i64* %parsed
    %t4230 = call i64 @freak_ver_minor(i64 %t4229)
    %t4231 = add i64 %t4230, 1
    %min_v4232 = alloca i64
    store i64 %t4231, i64* %min_v4232
    %t4233 = load i64, i64* %maj_v4228
    %t4234 = call i64 @freak_llvm_word_from_int(i64 %t4233)
    %t4235 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.266, i64 0, i64 0
    %t4236 = ptrtoint i8* %t4235 to i64
    %t4237 = call i64 @freak_llvm_word_concat(i64 %t4234, i64 %t4236)
    %t4238 = load i64, i64* %min_v4232
    %t4239 = call i64 @freak_llvm_word_from_int(i64 %t4238)
    %t4240 = call i64 @freak_llvm_word_concat(i64 %t4237, i64 %t4239)
    %t4241 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.267, i64 0, i64 0
    %t4242 = ptrtoint i8* %t4241 to i64
    %t4243 = call i64 @freak_llvm_word_concat(i64 %t4240, i64 %t4242)
    ret i64 %t4243
    ret i64 0
}

define i64 @freak_ver_bump_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4244 = load i64, i64* %parsed
    %t4245 = call i64 @freak_ver_major(i64 %t4244)
    %maj_v4246 = alloca i64
    store i64 %t4245, i64* %maj_v4246
    %t4247 = load i64, i64* %parsed
    %t4248 = call i64 @freak_ver_minor(i64 %t4247)
    %min_v4249 = alloca i64
    store i64 %t4248, i64* %min_v4249
    %t4250 = load i64, i64* %parsed
    %t4251 = call i64 @freak_ver_patch(i64 %t4250)
    %t4252 = add i64 %t4251, 1
    %pat_v4253 = alloca i64
    store i64 %t4252, i64* %pat_v4253
    %t4254 = load i64, i64* %maj_v4246
    %t4255 = call i64 @freak_llvm_word_from_int(i64 %t4254)
    %t4256 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.268, i64 0, i64 0
    %t4257 = ptrtoint i8* %t4256 to i64
    %t4258 = call i64 @freak_llvm_word_concat(i64 %t4255, i64 %t4257)
    %t4259 = load i64, i64* %min_v4249
    %t4260 = call i64 @freak_llvm_word_from_int(i64 %t4259)
    %t4261 = call i64 @freak_llvm_word_concat(i64 %t4258, i64 %t4260)
    %t4262 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.269, i64 0, i64 0
    %t4263 = ptrtoint i8* %t4262 to i64
    %t4264 = call i64 @freak_llvm_word_concat(i64 %t4261, i64 %t4263)
    %t4265 = load i64, i64* %pat_v4253
    %t4266 = call i64 @freak_llvm_word_from_int(i64 %t4265)
    %t4267 = call i64 @freak_llvm_word_concat(i64 %t4264, i64 %t4266)
    %t4268 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.270, i64 0, i64 0
    %t4269 = ptrtoint i8* %t4268 to i64
    %t4270 = call i64 @freak_llvm_word_concat(i64 %t4267, i64 %t4269)
    ret i64 %t4270
    ret i64 0
}

define i64 @freak_ver_strip_prefix(i64 %arg_constraint, i64 %arg_prefix_len) {
entry:
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %prefix_len = alloca i64
    store i64 %arg_prefix_len, i64* %prefix_len
    %t4271 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.271, i64 0, i64 0
    %t4272 = ptrtoint i8* %t4271 to i64
    %stripped_v4273 = alloca i64
    store i64 %t4272, i64* %stripped_v4273
    %t4274 = load i64, i64* %prefix_len
    %si_v4275 = alloca i64
    store i64 %t4274, i64* %si_v4275
    br label %loop.cond.4276
loop.cond.4276:
    %t4279 = load i64, i64* %si_v4275
    %t4280 = load i64, i64* %constraint
    %t4281 = call i64 @freak_llvm_word_length(i64 %t4280)
    %t4283 = icmp sge i64 %t4279, %t4281
    %t4282 = zext i1 %t4283 to i64
    %t4284 = icmp eq i64 %t4282, 0
    br i1 %t4284, label %loop.body.4277, label %loop.end.4278
loop.body.4277:
    %t4285 = load i64, i64* %stripped_v4273
    %t4286 = load i64, i64* %constraint
    %t4288 = load i64, i64* %si_v4275
    %t4287 = call i64 @freak_llvm_word_char_at(i64 %t4286, i64 %t4288)
    %t4289 = call i64 @freak_llvm_word_concat(i64 %t4285, i64 %t4287)
    store i64 %t4289, i64* %stripped_v4273
    %t4290 = load i64, i64* %si_v4275
    %t4291 = add i64 %t4290, 1
    store i64 %t4291, i64* %si_v4275
    br label %loop.cond.4276
loop.end.4278:
    %t4292 = load i64, i64* %stripped_v4273
    ret i64 %t4292
    ret i64 0
}

define i64 @freak_ver_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t4293 = load i64, i64* %c
    %t4294 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.272, i64 0, i64 0
    %t4295 = ptrtoint i8* %t4294 to i64
    %t4296 = call i64 @freak_llvm_word_eq(i64 %t4293, i64 %t4295)
    %t4300 = icmp ne i64 %t4296, 0
    br i1 %t4300, label %if.then.4297, label %if.end.4299
if.then.4297:
    ret i64 1
    br label %if.end.4299
if.end.4299:
    %t4301 = load i64, i64* %c
    %t4302 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.273, i64 0, i64 0
    %t4303 = ptrtoint i8* %t4302 to i64
    %t4304 = call i64 @freak_llvm_word_eq(i64 %t4301, i64 %t4303)
    %t4308 = icmp ne i64 %t4304, 0
    br i1 %t4308, label %if.then.4305, label %if.end.4307
if.then.4305:
    ret i64 1
    br label %if.end.4307
if.end.4307:
    %t4309 = load i64, i64* %c
    %t4310 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.274, i64 0, i64 0
    %t4311 = ptrtoint i8* %t4310 to i64
    %t4312 = call i64 @freak_llvm_word_eq(i64 %t4309, i64 %t4311)
    %t4316 = icmp ne i64 %t4312, 0
    br i1 %t4316, label %if.then.4313, label %if.end.4315
if.then.4313:
    ret i64 1
    br label %if.end.4315
if.end.4315:
    %t4317 = load i64, i64* %c
    %t4318 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.275, i64 0, i64 0
    %t4319 = ptrtoint i8* %t4318 to i64
    %t4320 = call i64 @freak_llvm_word_eq(i64 %t4317, i64 %t4319)
    %t4324 = icmp ne i64 %t4320, 0
    br i1 %t4324, label %if.then.4321, label %if.end.4323
if.then.4321:
    ret i64 1
    br label %if.end.4323
if.end.4323:
    %t4325 = load i64, i64* %c
    %t4326 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.276, i64 0, i64 0
    %t4327 = ptrtoint i8* %t4326 to i64
    %t4328 = call i64 @freak_llvm_word_eq(i64 %t4325, i64 %t4327)
    %t4332 = icmp ne i64 %t4328, 0
    br i1 %t4332, label %if.then.4329, label %if.end.4331
if.then.4329:
    ret i64 1
    br label %if.end.4331
if.end.4331:
    %t4333 = load i64, i64* %c
    %t4334 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.277, i64 0, i64 0
    %t4335 = ptrtoint i8* %t4334 to i64
    %t4336 = call i64 @freak_llvm_word_eq(i64 %t4333, i64 %t4335)
    %t4340 = icmp ne i64 %t4336, 0
    br i1 %t4340, label %if.then.4337, label %if.end.4339
if.then.4337:
    ret i64 1
    br label %if.end.4339
if.end.4339:
    %t4341 = load i64, i64* %c
    %t4342 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.278, i64 0, i64 0
    %t4343 = ptrtoint i8* %t4342 to i64
    %t4344 = call i64 @freak_llvm_word_eq(i64 %t4341, i64 %t4343)
    %t4348 = icmp ne i64 %t4344, 0
    br i1 %t4348, label %if.then.4345, label %if.end.4347
if.then.4345:
    ret i64 1
    br label %if.end.4347
if.end.4347:
    %t4349 = load i64, i64* %c
    %t4350 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.279, i64 0, i64 0
    %t4351 = ptrtoint i8* %t4350 to i64
    %t4352 = call i64 @freak_llvm_word_eq(i64 %t4349, i64 %t4351)
    %t4356 = icmp ne i64 %t4352, 0
    br i1 %t4356, label %if.then.4353, label %if.end.4355
if.then.4353:
    ret i64 1
    br label %if.end.4355
if.end.4355:
    %t4357 = load i64, i64* %c
    %t4358 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.280, i64 0, i64 0
    %t4359 = ptrtoint i8* %t4358 to i64
    %t4360 = call i64 @freak_llvm_word_eq(i64 %t4357, i64 %t4359)
    %t4364 = icmp ne i64 %t4360, 0
    br i1 %t4364, label %if.then.4361, label %if.end.4363
if.then.4361:
    ret i64 1
    br label %if.end.4363
if.end.4363:
    %t4365 = load i64, i64* %c
    %t4366 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.281, i64 0, i64 0
    %t4367 = ptrtoint i8* %t4366 to i64
    %t4368 = call i64 @freak_llvm_word_eq(i64 %t4365, i64 %t4367)
    %t4372 = icmp ne i64 %t4368, 0
    br i1 %t4372, label %if.then.4369, label %if.end.4371
if.then.4369:
    ret i64 1
    br label %if.end.4371
if.end.4371:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_satisfies_single(i64 %arg_v, i64 %arg_constraint) {
entry:
    %v = alloca i64
    store i64 %arg_v, i64* %v
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4373 = load i64, i64* %constraint
    %t4374 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.282, i64 0, i64 0
    %t4375 = ptrtoint i8* %t4374 to i64
    %t4376 = call i64 @freak_llvm_word_eq(i64 %t4373, i64 %t4375)
    %t4377 = load i64, i64* %constraint
    %t4378 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.283, i64 0, i64 0
    %t4379 = ptrtoint i8* %t4378 to i64
    %t4380 = call i64 @freak_llvm_word_eq(i64 %t4377, i64 %t4379)
    %t4382 = icmp ne i64 %t4376, 0
    %t4383 = icmp ne i64 %t4380, 0
    %t4384 = or i1 %t4382, %t4383
    %t4381 = zext i1 %t4384 to i64
    %t4388 = icmp ne i64 %t4381, 0
    br i1 %t4388, label %if.then.4385, label %if.end.4387
if.then.4385:
    ret i64 1
    br label %if.end.4387
if.end.4387:
    %t4389 = load i64, i64* %constraint
    %t4391 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.284, i64 0, i64 0
    %t4392 = ptrtoint i8* %t4391 to i64
    %t4390 = call i64 @freak_llvm_word_starts_with(i64 %t4389, i64 %t4392)
    %t4396 = icmp ne i64 %t4390, 0
    br i1 %t4396, label %if.then.4393, label %if.end.4395
if.then.4393:
    %t4397 = load i64, i64* %constraint
    %t4398 = call i64 @freak_ver_strip_prefix(i64 %t4397, i64 1)
    %t4399 = call i64 @freak_ver_parse(i64 %t4398)
    %c_v4400 = alloca i64
    store i64 %t4399, i64* %c_v4400
    %t4401 = load i64, i64* %v
    %t4402 = call i64 @freak_ver_major(i64 %t4401)
    %t4403 = load i64, i64* %c_v4400
    %t4404 = call i64 @freak_ver_major(i64 %t4403)
    %t4406 = icmp ne i64 %t4402, %t4404
    %t4405 = zext i1 %t4406 to i64
    %t4410 = icmp ne i64 %t4405, 0
    br i1 %t4410, label %if.then.4407, label %if.end.4409
if.then.4407:
    ret i64 0
    br label %if.end.4409
if.end.4409:
    %t4411 = load i64, i64* %v
    %t4412 = load i64, i64* %c_v4400
    %t4413 = call i64 @freak_ver_gte(i64 %t4411, i64 %t4412)
    ret i64 %t4413
    br label %if.end.4395
if.end.4395:
    %t4414 = load i64, i64* %constraint
    %t4416 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.285, i64 0, i64 0
    %t4417 = ptrtoint i8* %t4416 to i64
    %t4415 = call i64 @freak_llvm_word_starts_with(i64 %t4414, i64 %t4417)
    %t4421 = icmp ne i64 %t4415, 0
    br i1 %t4421, label %if.then.4418, label %if.end.4420
if.then.4418:
    %t4422 = load i64, i64* %constraint
    %t4423 = call i64 @freak_ver_strip_prefix(i64 %t4422, i64 1)
    %t4424 = call i64 @freak_ver_parse(i64 %t4423)
    %t_v4425 = alloca i64
    store i64 %t4424, i64* %t_v4425
    %t4426 = load i64, i64* %v
    %t4427 = call i64 @freak_ver_major(i64 %t4426)
    %t4428 = load i64, i64* %t_v4425
    %t4429 = call i64 @freak_ver_major(i64 %t4428)
    %t4431 = icmp ne i64 %t4427, %t4429
    %t4430 = zext i1 %t4431 to i64
    %t4435 = icmp ne i64 %t4430, 0
    br i1 %t4435, label %if.then.4432, label %if.end.4434
if.then.4432:
    ret i64 0
    br label %if.end.4434
if.end.4434:
    %t4436 = load i64, i64* %v
    %t4437 = call i64 @freak_ver_minor(i64 %t4436)
    %t4438 = load i64, i64* %t_v4425
    %t4439 = call i64 @freak_ver_minor(i64 %t4438)
    %t4441 = icmp ne i64 %t4437, %t4439
    %t4440 = zext i1 %t4441 to i64
    %t4445 = icmp ne i64 %t4440, 0
    br i1 %t4445, label %if.then.4442, label %if.end.4444
if.then.4442:
    ret i64 0
    br label %if.end.4444
if.end.4444:
    %t4446 = load i64, i64* %v
    %t4447 = load i64, i64* %t_v4425
    %t4448 = call i64 @freak_ver_gte(i64 %t4446, i64 %t4447)
    ret i64 %t4448
    br label %if.end.4420
if.end.4420:
    %t4449 = load i64, i64* %constraint
    %t4451 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.286, i64 0, i64 0
    %t4452 = ptrtoint i8* %t4451 to i64
    %t4450 = call i64 @freak_llvm_word_starts_with(i64 %t4449, i64 %t4452)
    %t4456 = icmp ne i64 %t4450, 0
    br i1 %t4456, label %if.then.4453, label %if.end.4455
if.then.4453:
    %t4457 = load i64, i64* %v
    %t4458 = load i64, i64* %constraint
    %t4459 = call i64 @freak_ver_strip_prefix(i64 %t4458, i64 2)
    %t4460 = call i64 @freak_ver_parse(i64 %t4459)
    %t4461 = call i64 @freak_ver_gte(i64 %t4457, i64 %t4460)
    ret i64 %t4461
    br label %if.end.4455
if.end.4455:
    %t4462 = load i64, i64* %constraint
    %t4464 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.287, i64 0, i64 0
    %t4465 = ptrtoint i8* %t4464 to i64
    %t4463 = call i64 @freak_llvm_word_starts_with(i64 %t4462, i64 %t4465)
    %t4469 = icmp ne i64 %t4463, 0
    br i1 %t4469, label %if.then.4466, label %if.end.4468
if.then.4466:
    %t4470 = load i64, i64* %v
    %t4471 = load i64, i64* %constraint
    %t4472 = call i64 @freak_ver_strip_prefix(i64 %t4471, i64 2)
    %t4473 = call i64 @freak_ver_parse(i64 %t4472)
    %t4474 = call i64 @freak_ver_lte(i64 %t4470, i64 %t4473)
    ret i64 %t4474
    br label %if.end.4468
if.end.4468:
    %t4475 = load i64, i64* %constraint
    %t4477 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.288, i64 0, i64 0
    %t4478 = ptrtoint i8* %t4477 to i64
    %t4476 = call i64 @freak_llvm_word_starts_with(i64 %t4475, i64 %t4478)
    %t4482 = icmp ne i64 %t4476, 0
    br i1 %t4482, label %if.then.4479, label %if.end.4481
if.then.4479:
    %t4483 = load i64, i64* %v
    %t4484 = load i64, i64* %constraint
    %t4485 = call i64 @freak_ver_strip_prefix(i64 %t4484, i64 1)
    %t4486 = call i64 @freak_ver_parse(i64 %t4485)
    %t4487 = call i64 @freak_ver_gt(i64 %t4483, i64 %t4486)
    ret i64 %t4487
    br label %if.end.4481
if.end.4481:
    %t4488 = load i64, i64* %constraint
    %t4490 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.289, i64 0, i64 0
    %t4491 = ptrtoint i8* %t4490 to i64
    %t4489 = call i64 @freak_llvm_word_starts_with(i64 %t4488, i64 %t4491)
    %t4495 = icmp ne i64 %t4489, 0
    br i1 %t4495, label %if.then.4492, label %if.end.4494
if.then.4492:
    %t4496 = load i64, i64* %v
    %t4497 = load i64, i64* %constraint
    %t4498 = call i64 @freak_ver_strip_prefix(i64 %t4497, i64 1)
    %t4499 = call i64 @freak_ver_parse(i64 %t4498)
    %t4500 = call i64 @freak_ver_lt(i64 %t4496, i64 %t4499)
    ret i64 %t4500
    br label %if.end.4494
if.end.4494:
    %t4501 = load i64, i64* %constraint
    %t4503 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.290, i64 0, i64 0
    %t4504 = ptrtoint i8* %t4503 to i64
    %t4502 = call i64 @freak_llvm_word_starts_with(i64 %t4501, i64 %t4504)
    %t4508 = icmp ne i64 %t4502, 0
    br i1 %t4508, label %if.then.4505, label %if.end.4507
if.then.4505:
    %t4509 = load i64, i64* %v
    %t4510 = load i64, i64* %constraint
    %t4511 = call i64 @freak_ver_strip_prefix(i64 %t4510, i64 1)
    %t4512 = call i64 @freak_ver_parse(i64 %t4511)
    %t4513 = call i64 @freak_ver_eq(i64 %t4509, i64 %t4512)
    ret i64 %t4513
    br label %if.end.4507
if.end.4507:
    %t4514 = load i64, i64* %constraint
    %t4515 = call i64 @freak_llvm_word_length(i64 %t4514)
    %t4517 = icmp sgt i64 %t4515, 0
    %t4516 = zext i1 %t4517 to i64
    %t4521 = icmp ne i64 %t4516, 0
    br i1 %t4521, label %if.then.4518, label %if.end.4520
if.then.4518:
    %t4522 = load i64, i64* %constraint
    %t4523 = call i64 @freak_llvm_word_char_at(i64 %t4522, i64 0)
    %fc_v4524 = alloca i64
    store i64 %t4523, i64* %fc_v4524
    %t4525 = load i64, i64* %fc_v4524
    %t4526 = call i64 @freak_ver_is_digit(i64 %t4525)
    %t4530 = icmp ne i64 %t4526, 0
    br i1 %t4530, label %if.then.4527, label %if.end.4529
if.then.4527:
    %t4531 = load i64, i64* %constraint
    %t4532 = call i64 @freak_ver_parse(i64 %t4531)
    %c_v4533 = alloca i64
    store i64 %t4532, i64* %c_v4533
    %t4534 = load i64, i64* %v
    %t4535 = call i64 @freak_ver_major(i64 %t4534)
    %t4536 = load i64, i64* %c_v4533
    %t4537 = call i64 @freak_ver_major(i64 %t4536)
    %t4539 = icmp ne i64 %t4535, %t4537
    %t4538 = zext i1 %t4539 to i64
    %t4543 = icmp ne i64 %t4538, 0
    br i1 %t4543, label %if.then.4540, label %if.end.4542
if.then.4540:
    ret i64 0
    br label %if.end.4542
if.end.4542:
    %t4544 = load i64, i64* %v
    %t4545 = load i64, i64* %c_v4533
    %t4546 = call i64 @freak_ver_gte(i64 %t4544, i64 %t4545)
    ret i64 %t4546
    br label %if.end.4529
if.end.4529:
    br label %if.end.4520
if.end.4520:
    %t4547 = load i64, i64* %v
    %t4548 = load i64, i64* %constraint
    %t4549 = call i64 @freak_ver_parse(i64 %t4548)
    %t4550 = call i64 @freak_ver_eq(i64 %t4547, i64 %t4549)
    ret i64 %t4550
    ret i64 0
}

define i64 @freak_ver_satisfies(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4551 = load i64, i64* %version
    %t4552 = call i64 @freak_ver_parse(i64 %t4551)
    %v_v4553 = alloca i64
    store i64 %t4552, i64* %v_v4553
    %t4554 = load i64, i64* %constraint
    %t4555 = call i64 @freak_llvm_word_length(i64 %t4554)
    %clen_v4556 = alloca i64
    store i64 %t4555, i64* %clen_v4556
    %t4557 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.291, i64 0, i64 0
    %t4558 = ptrtoint i8* %t4557 to i64
    %current_v4559 = alloca i64
    store i64 %t4558, i64* %current_v4559
    %i_v4560 = alloca i64
    store i64 0, i64* %i_v4560
    br label %loop.cond.4561
loop.cond.4561:
    %t4564 = load i64, i64* %i_v4560
    %t4565 = load i64, i64* %clen_v4556
    %t4567 = icmp sge i64 %t4564, %t4565
    %t4566 = zext i1 %t4567 to i64
    %t4568 = icmp eq i64 %t4566, 0
    br i1 %t4568, label %loop.body.4562, label %loop.end.4563
loop.body.4562:
    %t4569 = load i64, i64* %constraint
    %t4571 = load i64, i64* %i_v4560
    %t4570 = call i64 @freak_llvm_word_char_at(i64 %t4569, i64 %t4571)
    %ch_v4572 = alloca i64
    store i64 %t4570, i64* %ch_v4572
    %t4573 = load i64, i64* %ch_v4572
    %t4574 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.292, i64 0, i64 0
    %t4575 = ptrtoint i8* %t4574 to i64
    %t4576 = call i64 @freak_llvm_word_eq(i64 %t4573, i64 %t4575)
    %t4580 = icmp ne i64 %t4576, 0
    br i1 %t4580, label %if.then.4577, label %if.else.4578
if.then.4577:
    %t4581 = load i64, i64* %current_v4559
    %t4582 = call i64 @freak_llvm_word_length(i64 %t4581)
    %t4584 = icmp sgt i64 %t4582, 0
    %t4583 = zext i1 %t4584 to i64
    %t4588 = icmp ne i64 %t4583, 0
    br i1 %t4588, label %if.then.4585, label %if.end.4587
if.then.4585:
    %t4589 = load i64, i64* %v_v4553
    %t4590 = load i64, i64* %current_v4559
    %t4591 = call i64 @freak_ver_satisfies_single(i64 %t4589, i64 %t4590)
    %t4593 = icmp eq i64 %t4591, 0
    %t4592 = zext i1 %t4593 to i64
    %t4597 = icmp ne i64 %t4592, 0
    br i1 %t4597, label %if.then.4594, label %if.end.4596
if.then.4594:
    ret i64 0
    br label %if.end.4596
if.end.4596:
    %t4598 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.293, i64 0, i64 0
    %t4599 = ptrtoint i8* %t4598 to i64
    store i64 %t4599, i64* %current_v4559
    br label %if.end.4587
if.end.4587:
    br label %if.end.4579
if.else.4578:
    %t4600 = load i64, i64* %current_v4559
    %t4601 = load i64, i64* %ch_v4572
    %t4602 = call i64 @freak_llvm_word_concat(i64 %t4600, i64 %t4601)
    store i64 %t4602, i64* %current_v4559
    br label %if.end.4579
if.end.4579:
    %t4603 = load i64, i64* %i_v4560
    %t4604 = add i64 %t4603, 1
    store i64 %t4604, i64* %i_v4560
    br label %loop.cond.4561
loop.end.4563:
    %t4605 = load i64, i64* %current_v4559
    %t4606 = call i64 @freak_llvm_word_length(i64 %t4605)
    %t4608 = icmp sgt i64 %t4606, 0
    %t4607 = zext i1 %t4608 to i64
    %t4612 = icmp ne i64 %t4607, 0
    br i1 %t4612, label %if.then.4609, label %if.end.4611
if.then.4609:
    %t4613 = load i64, i64* %v_v4553
    %t4614 = load i64, i64* %current_v4559
    %t4615 = call i64 @freak_ver_satisfies_single(i64 %t4613, i64 %t4614)
    %t4617 = icmp eq i64 %t4615, 0
    %t4616 = zext i1 %t4617 to i64
    %t4621 = icmp ne i64 %t4616, 0
    br i1 %t4621, label %if.then.4618, label %if.end.4620
if.then.4618:
    ret i64 0
    br label %if.end.4620
if.end.4620:
    br label %if.end.4611
if.end.4611:
    ret i64 1
    ret i64 0
}

define i64 @freak_version_matches_constraint(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4622 = load i64, i64* %version
    %t4623 = load i64, i64* %constraint
    %t4624 = call i64 @freak_ver_satisfies(i64 %t4622, i64 %t4623)
    ret i64 %t4624
    ret i64 0
}

define void @freak_http_init() {
entry:
    %t4625 = load i64, i64* @g_http_inited
    %t4627 = icmp eq i64 %t4625, 0
    %t4626 = zext i1 %t4627 to i64
    %t4631 = icmp ne i64 %t4626, 0
    br i1 %t4631, label %if.then.4628, label %if.end.4630
if.then.4628:
    %t4632 = call i64 @freak_llvm_array_new()
    store i64 %t4632, i64* @g_http_resp_statuses
    %t4633 = call i64 @freak_llvm_array_new()
    store i64 %t4633, i64* @g_http_resp_bodies
    %t4634 = call i64 @freak_llvm_array_new()
    store i64 %t4634, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 1, i64* @g_http_inited
    br label %if.end.4630
if.end.4630:
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
    %t4635 = load i64, i64* @g_http_resp_count
    %idx_v4636 = alloca i64
    store i64 %t4635, i64* %idx_v4636
    %t4637 = load i64, i64* @g_http_resp_statuses
    %t4638 = load i64, i64* %status
    %t4639 = call i64 @freak_llvm_word_from_int(i64 %t4638)
    call void @freak_llvm_array_push(i64 %t4637, i64 %t4639)
    %t4640 = load i64, i64* @g_http_resp_bodies
    %t4641 = load i64, i64* %body
    call void @freak_llvm_array_push(i64 %t4640, i64 %t4641)
    %t4642 = load i64, i64* @g_http_resp_headers_raw
    %t4643 = load i64, i64* %headers
    call void @freak_llvm_array_push(i64 %t4642, i64 %t4643)
    %t4644 = load i64, i64* @g_http_resp_count
    %t4645 = add i64 %t4644, 1
    store i64 %t4645, i64* @g_http_resp_count
    %t4646 = load i64, i64* %idx_v4636
    ret i64 %t4646
    ret i64 0
}

define i64 @freak_http_resp_status(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4647 = load i64, i64* @g_http_resp_statuses
    %t4648 = load i64, i64* %handle
    %t4649 = call i64 @freak_llvm_array_get(i64 %t4647, i64 %t4648)
    %v_v4650 = alloca i64
    store i64 %t4649, i64* %v_v4650
    %t4651 = load i64, i64* %v_v4650
    %t4652 = call i64 @freak_llvm_word_to_int(i64 %t4651)
    ret i64 %t4652
    ret i64 0
}

define i64 @freak_http_resp_body(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4653 = load i64, i64* @g_http_resp_bodies
    %t4654 = load i64, i64* %handle
    %t4655 = call i64 @freak_llvm_array_get(i64 %t4653, i64 %t4654)
    ret i64 %t4655
    ret i64 0
}

define i64 @freak_http_resp_headers(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4656 = load i64, i64* @g_http_resp_headers_raw
    %t4657 = load i64, i64* %handle
    %t4658 = call i64 @freak_llvm_array_get(i64 %t4656, i64 %t4657)
    ret i64 %t4658
    ret i64 0
}

define i64 @freak_http_parse_status(i64 %arg_line) {
entry:
    %line = alloca i64
    store i64 %arg_line, i64* %line
    %t4659 = load i64, i64* %line
    %t4660 = call i64 @freak_llvm_word_length(i64 %t4659)
    %slen_v4661 = alloca i64
    store i64 %t4660, i64* %slen_v4661
    %si_v4662 = alloca i64
    store i64 0, i64* %si_v4662
    %t4668 = load i64, i64* %slen_v4661
    %rep.4667 = alloca i64
    store i64 0, i64* %rep.4667
    br label %loop.cond.4663
loop.cond.4663:
    %t4669 = load i64, i64* %rep.4667
    %t4670 = icmp slt i64 %t4669, %t4668
    br i1 %t4670, label %loop.body.4664, label %loop.end.4665
loop.body.4664:
    %t4671 = load i64, i64* %line
    %t4673 = load i64, i64* %si_v4662
    %t4672 = call i64 @freak_llvm_word_char_at(i64 %t4671, i64 %t4673)
    %t4674 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.294, i64 0, i64 0
    %t4675 = ptrtoint i8* %t4674 to i64
    %t4676 = call i64 @freak_llvm_word_eq(i64 %t4672, i64 %t4675)
    %t4680 = icmp ne i64 %t4676, 0
    br i1 %t4680, label %if.then.4677, label %if.end.4679
if.then.4677:
    %t4681 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.295, i64 0, i64 0
    %t4682 = ptrtoint i8* %t4681 to i64
    %code_str_v4683 = alloca i64
    store i64 %t4682, i64* %code_str_v4683
    %t4684 = load i64, i64* %si_v4662
    %t4685 = add i64 %t4684, 1
    %ci_v4686 = alloca i64
    store i64 %t4685, i64* %ci_v4686
    %rep.4691 = alloca i64
    store i64 0, i64* %rep.4691
    br label %loop.cond.4687
loop.cond.4687:
    %t4692 = load i64, i64* %rep.4691
    %t4693 = icmp slt i64 %t4692, 3
    br i1 %t4693, label %loop.body.4688, label %loop.end.4689
loop.body.4688:
    %t4694 = load i64, i64* %ci_v4686
    %t4695 = load i64, i64* %slen_v4661
    %t4697 = icmp slt i64 %t4694, %t4695
    %t4696 = zext i1 %t4697 to i64
    %t4701 = icmp ne i64 %t4696, 0
    br i1 %t4701, label %if.then.4698, label %if.end.4700
if.then.4698:
    %t4702 = load i64, i64* %code_str_v4683
    %t4703 = load i64, i64* %line
    %t4705 = load i64, i64* %ci_v4686
    %t4704 = call i64 @freak_llvm_word_char_at(i64 %t4703, i64 %t4705)
    %t4706 = call i64 @freak_llvm_word_concat(i64 %t4702, i64 %t4704)
    store i64 %t4706, i64* %code_str_v4683
    %t4707 = load i64, i64* %ci_v4686
    %t4708 = add i64 %t4707, 1
    store i64 %t4708, i64* %ci_v4686
    br label %if.end.4700
if.end.4700:
    br label %loop.inc.4690
loop.inc.4690:
    %t4709 = load i64, i64* %rep.4691
    %t4710 = add i64 %t4709, 1
    store i64 %t4710, i64* %rep.4691
    br label %loop.cond.4687
loop.end.4689:
    %t4711 = load i64, i64* %code_str_v4683
    %t4712 = call i64 @freak_llvm_word_to_int(i64 %t4711)
    ret i64 %t4712
    br label %if.end.4679
if.end.4679:
    %t4713 = load i64, i64* %si_v4662
    %t4714 = add i64 %t4713, 1
    store i64 %t4714, i64* %si_v4662
    br label %loop.inc.4666
loop.inc.4666:
    %t4715 = load i64, i64* %rep.4667
    %t4716 = add i64 %t4715, 1
    store i64 %t4716, i64* %rep.4667
    br label %loop.cond.4663
loop.end.4665:
    ret i64 0
    ret i64 0
}

define i64 @freak_http_split_response(i64 %arg_raw) {
entry:
    %raw = alloca i64
    store i64 %arg_raw, i64* %raw
    %t4717 = load i64, i64* %raw
    %t4718 = call i64 @freak_llvm_word_length(i64 %t4717)
    %rlen_v4719 = alloca i64
    store i64 %t4718, i64* %rlen_v4719
    %ri_v4720 = alloca i64
    store i64 0, i64* %ri_v4720
    %t4721 = sub i64 0, 1
    %header_end_v4722 = alloca i64
    store i64 %t4721, i64* %header_end_v4722
    %t4723 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.296, i64 0, i64 0
    %t4724 = ptrtoint i8* %t4723 to i64
    %prev3_v4725 = alloca i64
    store i64 %t4724, i64* %prev3_v4725
    %t4726 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.297, i64 0, i64 0
    %t4727 = ptrtoint i8* %t4726 to i64
    %prev2_v4728 = alloca i64
    store i64 %t4727, i64* %prev2_v4728
    %t4729 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.298, i64 0, i64 0
    %t4730 = ptrtoint i8* %t4729 to i64
    %prev1_v4731 = alloca i64
    store i64 %t4730, i64* %prev1_v4731
    %t4737 = load i64, i64* %rlen_v4719
    %rep.4736 = alloca i64
    store i64 0, i64* %rep.4736
    br label %loop.cond.4732
loop.cond.4732:
    %t4738 = load i64, i64* %rep.4736
    %t4739 = icmp slt i64 %t4738, %t4737
    br i1 %t4739, label %loop.body.4733, label %loop.end.4734
loop.body.4733:
    %t4740 = load i64, i64* %raw
    %t4742 = load i64, i64* %ri_v4720
    %t4741 = call i64 @freak_llvm_word_char_at(i64 %t4740, i64 %t4742)
    %ch_v4743 = alloca i64
    store i64 %t4741, i64* %ch_v4743
    %t4744 = load i64, i64* %prev2_v4728
    %t4745 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.299, i64 0, i64 0
    %t4746 = ptrtoint i8* %t4745 to i64
    %t4747 = call i64 @freak_llvm_word_eq(i64 %t4744, i64 %t4746)
    %t4748 = load i64, i64* %prev1_v4731
    %t4749 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.300, i64 0, i64 0
    %t4750 = ptrtoint i8* %t4749 to i64
    %t4751 = call i64 @freak_llvm_word_eq(i64 %t4748, i64 %t4750)
    %t4753 = icmp ne i64 %t4747, 0
    %t4754 = icmp ne i64 %t4751, 0
    %t4755 = and i1 %t4753, %t4754
    %t4752 = zext i1 %t4755 to i64
    %t4756 = load i64, i64* %ch_v4743
    %t4757 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.301, i64 0, i64 0
    %t4758 = ptrtoint i8* %t4757 to i64
    %t4759 = call i64 @freak_llvm_word_eq(i64 %t4756, i64 %t4758)
    %t4761 = icmp ne i64 %t4752, 0
    %t4762 = icmp ne i64 %t4759, 0
    %t4763 = and i1 %t4761, %t4762
    %t4760 = zext i1 %t4763 to i64
    %t4767 = icmp ne i64 %t4760, 0
    br i1 %t4767, label %if.then.4764, label %if.end.4766
if.then.4764:
    %t4768 = load i64, i64* %ri_v4720
    %t4769 = add i64 %t4768, 1
    store i64 %t4769, i64* %header_end_v4722
    br label %if.end.4766
if.end.4766:
    %t4770 = load i64, i64* %prev3_v4725
    %t4771 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.302, i64 0, i64 0
    %t4772 = ptrtoint i8* %t4771 to i64
    %t4773 = call i64 @freak_llvm_word_eq(i64 %t4770, i64 %t4772)
    %t4774 = load i64, i64* %prev2_v4728
    %t4775 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.303, i64 0, i64 0
    %t4776 = ptrtoint i8* %t4775 to i64
    %t4777 = call i64 @freak_llvm_word_eq(i64 %t4774, i64 %t4776)
    %t4779 = icmp ne i64 %t4773, 0
    %t4780 = icmp ne i64 %t4777, 0
    %t4781 = and i1 %t4779, %t4780
    %t4778 = zext i1 %t4781 to i64
    %t4782 = load i64, i64* %prev1_v4731
    %t4783 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.304, i64 0, i64 0
    %t4784 = ptrtoint i8* %t4783 to i64
    %t4785 = call i64 @freak_llvm_word_eq(i64 %t4782, i64 %t4784)
    %t4787 = icmp ne i64 %t4778, 0
    %t4788 = icmp ne i64 %t4785, 0
    %t4789 = and i1 %t4787, %t4788
    %t4786 = zext i1 %t4789 to i64
    %t4790 = load i64, i64* %ch_v4743
    %t4791 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.305, i64 0, i64 0
    %t4792 = ptrtoint i8* %t4791 to i64
    %t4793 = call i64 @freak_llvm_word_eq(i64 %t4790, i64 %t4792)
    %t4795 = icmp ne i64 %t4786, 0
    %t4796 = icmp ne i64 %t4793, 0
    %t4797 = and i1 %t4795, %t4796
    %t4794 = zext i1 %t4797 to i64
    %t4801 = icmp ne i64 %t4794, 0
    br i1 %t4801, label %if.then.4798, label %if.end.4800
if.then.4798:
    %t4802 = load i64, i64* %ri_v4720
    %t4803 = add i64 %t4802, 1
    store i64 %t4803, i64* %header_end_v4722
    br label %if.end.4800
if.end.4800:
    %t4804 = load i64, i64* %prev2_v4728
    store i64 %t4804, i64* %prev3_v4725
    %t4805 = load i64, i64* %prev1_v4731
    store i64 %t4805, i64* %prev2_v4728
    %t4806 = load i64, i64* %ch_v4743
    store i64 %t4806, i64* %prev1_v4731
    %t4807 = load i64, i64* %ri_v4720
    %t4808 = add i64 %t4807, 1
    store i64 %t4808, i64* %ri_v4720
    br label %loop.inc.4735
loop.inc.4735:
    %t4809 = load i64, i64* %rep.4736
    %t4810 = add i64 %t4809, 1
    store i64 %t4810, i64* %rep.4736
    br label %loop.cond.4732
loop.end.4734:
    %t4811 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.306, i64 0, i64 0
    %t4812 = ptrtoint i8* %t4811 to i64
    %status_line_v4813 = alloca i64
    store i64 %t4812, i64* %status_line_v4813
    %li_v4814 = alloca i64
    store i64 0, i64* %li_v4814
    %t4820 = load i64, i64* %rlen_v4719
    %rep.4819 = alloca i64
    store i64 0, i64* %rep.4819
    br label %loop.cond.4815
loop.cond.4815:
    %t4821 = load i64, i64* %rep.4819
    %t4822 = icmp slt i64 %t4821, %t4820
    br i1 %t4822, label %loop.body.4816, label %loop.end.4817
loop.body.4816:
    %t4823 = load i64, i64* %raw
    %t4825 = load i64, i64* %li_v4814
    %t4824 = call i64 @freak_llvm_word_char_at(i64 %t4823, i64 %t4825)
    %lc_v4826 = alloca i64
    store i64 %t4824, i64* %lc_v4826
    %t4827 = load i64, i64* %lc_v4826
    %t4828 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.307, i64 0, i64 0
    %t4829 = ptrtoint i8* %t4828 to i64
    %t4830 = call i64 @freak_llvm_word_eq(i64 %t4827, i64 %t4829)
    %t4831 = load i64, i64* %lc_v4826
    %t4832 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.308, i64 0, i64 0
    %t4833 = ptrtoint i8* %t4832 to i64
    %t4834 = call i64 @freak_llvm_word_eq(i64 %t4831, i64 %t4833)
    %t4836 = icmp ne i64 %t4830, 0
    %t4837 = icmp ne i64 %t4834, 0
    %t4838 = or i1 %t4836, %t4837
    %t4835 = zext i1 %t4838 to i64
    %t4842 = icmp ne i64 %t4835, 0
    br i1 %t4842, label %if.then.4839, label %if.else.4840
if.then.4839:
    %t4843 = load i64, i64* %rlen_v4719
    store i64 %t4843, i64* %li_v4814
    br label %if.end.4841
if.else.4840:
    %t4844 = load i64, i64* %status_line_v4813
    %t4845 = load i64, i64* %lc_v4826
    %t4846 = call i64 @freak_llvm_word_concat(i64 %t4844, i64 %t4845)
    store i64 %t4846, i64* %status_line_v4813
    br label %if.end.4841
if.end.4841:
    %t4847 = load i64, i64* %li_v4814
    %t4848 = add i64 %t4847, 1
    store i64 %t4848, i64* %li_v4814
    br label %loop.inc.4818
loop.inc.4818:
    %t4849 = load i64, i64* %rep.4819
    %t4850 = add i64 %t4849, 1
    store i64 %t4850, i64* %rep.4819
    br label %loop.cond.4815
loop.end.4817:
    %t4851 = load i64, i64* %status_line_v4813
    %t4852 = call i64 @freak_http_parse_status(i64 %t4851)
    %status_v4853 = alloca i64
    store i64 %t4852, i64* %status_v4853
    %t4854 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.309, i64 0, i64 0
    %t4855 = ptrtoint i8* %t4854 to i64
    %headers_v4856 = alloca i64
    store i64 %t4855, i64* %headers_v4856
    %t4857 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.310, i64 0, i64 0
    %t4858 = ptrtoint i8* %t4857 to i64
    %body_v4859 = alloca i64
    store i64 %t4858, i64* %body_v4859
    %t4860 = load i64, i64* %header_end_v4722
    %t4862 = icmp sgt i64 %t4860, 0
    %t4861 = zext i1 %t4862 to i64
    %t4866 = icmp ne i64 %t4861, 0
    br i1 %t4866, label %if.then.4863, label %if.else.4864
if.then.4863:
    %hi_v4867 = alloca i64
    store i64 0, i64* %hi_v4867
    %t4873 = load i64, i64* %header_end_v4722
    %rep.4872 = alloca i64
    store i64 0, i64* %rep.4872
    br label %loop.cond.4868
loop.cond.4868:
    %t4874 = load i64, i64* %rep.4872
    %t4875 = icmp slt i64 %t4874, %t4873
    br i1 %t4875, label %loop.body.4869, label %loop.end.4870
loop.body.4869:
    %t4876 = load i64, i64* %hi_v4867
    %t4877 = load i64, i64* %rlen_v4719
    %t4879 = icmp slt i64 %t4876, %t4877
    %t4878 = zext i1 %t4879 to i64
    %t4883 = icmp ne i64 %t4878, 0
    br i1 %t4883, label %if.then.4880, label %if.end.4882
if.then.4880:
    %t4884 = load i64, i64* %headers_v4856
    %t4885 = load i64, i64* %raw
    %t4887 = load i64, i64* %hi_v4867
    %t4886 = call i64 @freak_llvm_word_char_at(i64 %t4885, i64 %t4887)
    %t4888 = call i64 @freak_llvm_word_concat(i64 %t4884, i64 %t4886)
    store i64 %t4888, i64* %headers_v4856
    br label %if.end.4882
if.end.4882:
    %t4889 = load i64, i64* %hi_v4867
    %t4890 = add i64 %t4889, 1
    store i64 %t4890, i64* %hi_v4867
    br label %loop.inc.4871
loop.inc.4871:
    %t4891 = load i64, i64* %rep.4872
    %t4892 = add i64 %t4891, 1
    store i64 %t4892, i64* %rep.4872
    br label %loop.cond.4868
loop.end.4870:
    %t4893 = load i64, i64* %header_end_v4722
    %bi_v4894 = alloca i64
    store i64 %t4893, i64* %bi_v4894
    %t4900 = load i64, i64* %rlen_v4719
    %rep.4899 = alloca i64
    store i64 0, i64* %rep.4899
    br label %loop.cond.4895
loop.cond.4895:
    %t4901 = load i64, i64* %rep.4899
    %t4902 = icmp slt i64 %t4901, %t4900
    br i1 %t4902, label %loop.body.4896, label %loop.end.4897
loop.body.4896:
    %t4903 = load i64, i64* %bi_v4894
    %t4904 = load i64, i64* %rlen_v4719
    %t4906 = icmp slt i64 %t4903, %t4904
    %t4905 = zext i1 %t4906 to i64
    %t4910 = icmp ne i64 %t4905, 0
    br i1 %t4910, label %if.then.4907, label %if.end.4909
if.then.4907:
    %t4911 = load i64, i64* %body_v4859
    %t4912 = load i64, i64* %raw
    %t4914 = load i64, i64* %bi_v4894
    %t4913 = call i64 @freak_llvm_word_char_at(i64 %t4912, i64 %t4914)
    %t4915 = call i64 @freak_llvm_word_concat(i64 %t4911, i64 %t4913)
    store i64 %t4915, i64* %body_v4859
    br label %if.end.4909
if.end.4909:
    %t4916 = load i64, i64* %bi_v4894
    %t4917 = add i64 %t4916, 1
    store i64 %t4917, i64* %bi_v4894
    br label %loop.inc.4898
loop.inc.4898:
    %t4918 = load i64, i64* %rep.4899
    %t4919 = add i64 %t4918, 1
    store i64 %t4919, i64* %rep.4899
    br label %loop.cond.4895
loop.end.4897:
    br label %if.end.4865
if.else.4864:
    %t4920 = load i64, i64* %raw
    store i64 %t4920, i64* %headers_v4856
    br label %if.end.4865
if.end.4865:
    %t4921 = load i64, i64* %status_v4853
    %t4922 = load i64, i64* %body_v4859
    %t4923 = load i64, i64* %headers_v4856
    %t4924 = call i64 @freak_http_alloc_resp(i64 %t4921, i64 %t4922, i64 %t4923)
    ret i64 %t4924
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
    %t4925 = load i64, i64* %host
    %t4926 = load i64, i64* %port
    %t4927 = call i64 @freak_llvm_tcp_connect(i64 %t4925, i64 %t4926)
    %fd_v4928 = alloca i64
    store i64 %t4927, i64* %fd_v4928
    %t4929 = load i64, i64* %fd_v4928
    %t4931 = icmp slt i64 %t4929, 0
    %t4930 = zext i1 %t4931 to i64
    %t4935 = icmp ne i64 %t4930, 0
    br i1 %t4935, label %if.then.4932, label %if.end.4934
if.then.4932:
    %t4936 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.311, i64 0, i64 0
    %t4937 = ptrtoint i8* %t4936 to i64
    %t4938 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.312, i64 0, i64 0
    %t4939 = ptrtoint i8* %t4938 to i64
    %t4940 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4937, i64 %t4939)
    ret i64 %t4940
    br label %if.end.4934
if.end.4934:
    %t4941 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.313, i64 0, i64 0
    %t4942 = ptrtoint i8* %t4941 to i64
    %t4943 = load i64, i64* %path
    %t4944 = call i64 @freak_llvm_word_concat(i64 %t4942, i64 %t4943)
    %t4945 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.314, i64 0, i64 0
    %t4946 = ptrtoint i8* %t4945 to i64
    %t4947 = call i64 @freak_llvm_word_concat(i64 %t4944, i64 %t4946)
    %t4948 = load i64, i64* %host
    %t4949 = call i64 @freak_llvm_word_concat(i64 %t4947, i64 %t4948)
    %t4950 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.315, i64 0, i64 0
    %t4951 = ptrtoint i8* %t4950 to i64
    %t4952 = call i64 @freak_llvm_word_concat(i64 %t4949, i64 %t4951)
    %req_v4953 = alloca i64
    store i64 %t4952, i64* %req_v4953
    %t4954 = load i64, i64* %fd_v4928
    %t4955 = load i64, i64* %req_v4953
    %t4956 = call i64 @freak_llvm_tcp_send(i64 %t4954, i64 %t4955)
    %t4957 = load i64, i64* %fd_v4928
    %t4958 = call i64 @freak_llvm_tcp_recv_all(i64 %t4957, i64 65536)
    %raw_v4959 = alloca i64
    store i64 %t4958, i64* %raw_v4959
    %t4960 = load i64, i64* %fd_v4928
    call void @freak_llvm_tcp_close(i64 %t4960)
    %t4961 = load i64, i64* %raw_v4959
    %t4962 = call i64 @freak_http_split_response(i64 %t4961)
    ret i64 %t4962
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
    %t4963 = load i64, i64* %host
    %t4964 = load i64, i64* %port
    %t4965 = call i64 @freak_llvm_tcp_connect(i64 %t4963, i64 %t4964)
    %fd_v4966 = alloca i64
    store i64 %t4965, i64* %fd_v4966
    %t4967 = load i64, i64* %fd_v4966
    %t4969 = icmp slt i64 %t4967, 0
    %t4968 = zext i1 %t4969 to i64
    %t4973 = icmp ne i64 %t4968, 0
    br i1 %t4973, label %if.then.4970, label %if.end.4972
if.then.4970:
    %t4974 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.316, i64 0, i64 0
    %t4975 = ptrtoint i8* %t4974 to i64
    %t4976 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.317, i64 0, i64 0
    %t4977 = ptrtoint i8* %t4976 to i64
    %t4978 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4975, i64 %t4977)
    ret i64 %t4978
    br label %if.end.4972
if.end.4972:
    %t4979 = load i64, i64* %body
    %t4980 = call i64 @freak_llvm_word_length(i64 %t4979)
    %t4981 = call i64 @freak_llvm_word_from_int(i64 %t4980)
    %body_len_v4982 = alloca i64
    store i64 %t4981, i64* %body_len_v4982
    %t4983 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.318, i64 0, i64 0
    %t4984 = ptrtoint i8* %t4983 to i64
    %t4985 = load i64, i64* %path
    %t4986 = call i64 @freak_llvm_word_concat(i64 %t4984, i64 %t4985)
    %t4987 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.319, i64 0, i64 0
    %t4988 = ptrtoint i8* %t4987 to i64
    %t4989 = call i64 @freak_llvm_word_concat(i64 %t4986, i64 %t4988)
    %t4990 = load i64, i64* %host
    %t4991 = call i64 @freak_llvm_word_concat(i64 %t4989, i64 %t4990)
    %t4992 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.320, i64 0, i64 0
    %t4993 = ptrtoint i8* %t4992 to i64
    %t4994 = call i64 @freak_llvm_word_concat(i64 %t4991, i64 %t4993)
    %t4995 = load i64, i64* %content_type
    %t4996 = call i64 @freak_llvm_word_concat(i64 %t4994, i64 %t4995)
    %t4997 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.321, i64 0, i64 0
    %t4998 = ptrtoint i8* %t4997 to i64
    %t4999 = call i64 @freak_llvm_word_concat(i64 %t4996, i64 %t4998)
    %t5000 = load i64, i64* %body_len_v4982
    %t5001 = call i64 @freak_llvm_word_concat(i64 %t4999, i64 %t5000)
    %t5002 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.322, i64 0, i64 0
    %t5003 = ptrtoint i8* %t5002 to i64
    %t5004 = call i64 @freak_llvm_word_concat(i64 %t5001, i64 %t5003)
    %t5005 = load i64, i64* %body
    %t5006 = call i64 @freak_llvm_word_concat(i64 %t5004, i64 %t5005)
    %req_v5007 = alloca i64
    store i64 %t5006, i64* %req_v5007
    %t5008 = load i64, i64* %fd_v4966
    %t5009 = load i64, i64* %req_v5007
    %t5010 = call i64 @freak_llvm_tcp_send(i64 %t5008, i64 %t5009)
    %t5011 = load i64, i64* %fd_v4966
    %t5012 = call i64 @freak_llvm_tcp_recv_all(i64 %t5011, i64 65536)
    %raw_v5013 = alloca i64
    store i64 %t5012, i64* %raw_v5013
    %t5014 = load i64, i64* %fd_v4966
    call void @freak_llvm_tcp_close(i64 %t5014)
    %t5015 = load i64, i64* %raw_v5013
    %t5016 = call i64 @freak_http_split_response(i64 %t5015)
    ret i64 %t5016
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
    %t5017 = load i64, i64* %host
    %t5018 = load i64, i64* %port
    %t5019 = call i64 @freak_llvm_tcp_connect(i64 %t5017, i64 %t5018)
    %fd_v5020 = alloca i64
    store i64 %t5019, i64* %fd_v5020
    %t5021 = load i64, i64* %fd_v5020
    %t5023 = icmp slt i64 %t5021, 0
    %t5022 = zext i1 %t5023 to i64
    %t5027 = icmp ne i64 %t5022, 0
    br i1 %t5027, label %if.then.5024, label %if.end.5026
if.then.5024:
    %t5028 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.323, i64 0, i64 0
    %t5029 = ptrtoint i8* %t5028 to i64
    %t5030 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.324, i64 0, i64 0
    %t5031 = ptrtoint i8* %t5030 to i64
    %t5032 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5029, i64 %t5031)
    ret i64 %t5032
    br label %if.end.5026
if.end.5026:
    %t5033 = load i64, i64* %body
    %t5034 = call i64 @freak_llvm_word_length(i64 %t5033)
    %t5035 = call i64 @freak_llvm_word_from_int(i64 %t5034)
    %body_len_v5036 = alloca i64
    store i64 %t5035, i64* %body_len_v5036
    %t5037 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.325, i64 0, i64 0
    %t5038 = ptrtoint i8* %t5037 to i64
    %t5039 = load i64, i64* %path
    %t5040 = call i64 @freak_llvm_word_concat(i64 %t5038, i64 %t5039)
    %t5041 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.326, i64 0, i64 0
    %t5042 = ptrtoint i8* %t5041 to i64
    %t5043 = call i64 @freak_llvm_word_concat(i64 %t5040, i64 %t5042)
    %t5044 = load i64, i64* %host
    %t5045 = call i64 @freak_llvm_word_concat(i64 %t5043, i64 %t5044)
    %t5046 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.327, i64 0, i64 0
    %t5047 = ptrtoint i8* %t5046 to i64
    %t5048 = call i64 @freak_llvm_word_concat(i64 %t5045, i64 %t5047)
    %t5049 = load i64, i64* %content_type
    %t5050 = call i64 @freak_llvm_word_concat(i64 %t5048, i64 %t5049)
    %t5051 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.328, i64 0, i64 0
    %t5052 = ptrtoint i8* %t5051 to i64
    %t5053 = call i64 @freak_llvm_word_concat(i64 %t5050, i64 %t5052)
    %t5054 = load i64, i64* %body_len_v5036
    %t5055 = call i64 @freak_llvm_word_concat(i64 %t5053, i64 %t5054)
    %t5056 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.329, i64 0, i64 0
    %t5057 = ptrtoint i8* %t5056 to i64
    %t5058 = call i64 @freak_llvm_word_concat(i64 %t5055, i64 %t5057)
    %t5059 = load i64, i64* %body
    %t5060 = call i64 @freak_llvm_word_concat(i64 %t5058, i64 %t5059)
    %req_v5061 = alloca i64
    store i64 %t5060, i64* %req_v5061
    %t5062 = load i64, i64* %fd_v5020
    %t5063 = load i64, i64* %req_v5061
    %t5064 = call i64 @freak_llvm_tcp_send(i64 %t5062, i64 %t5063)
    %t5065 = load i64, i64* %fd_v5020
    %t5066 = call i64 @freak_llvm_tcp_recv_all(i64 %t5065, i64 65536)
    %raw_v5067 = alloca i64
    store i64 %t5066, i64* %raw_v5067
    %t5068 = load i64, i64* %fd_v5020
    call void @freak_llvm_tcp_close(i64 %t5068)
    %t5069 = load i64, i64* %raw_v5067
    %t5070 = call i64 @freak_http_split_response(i64 %t5069)
    ret i64 %t5070
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
    %t5071 = load i64, i64* %host
    %t5072 = load i64, i64* %port
    %t5073 = call i64 @freak_llvm_tcp_connect(i64 %t5071, i64 %t5072)
    %fd_v5074 = alloca i64
    store i64 %t5073, i64* %fd_v5074
    %t5075 = load i64, i64* %fd_v5074
    %t5077 = icmp slt i64 %t5075, 0
    %t5076 = zext i1 %t5077 to i64
    %t5081 = icmp ne i64 %t5076, 0
    br i1 %t5081, label %if.then.5078, label %if.end.5080
if.then.5078:
    %t5082 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.330, i64 0, i64 0
    %t5083 = ptrtoint i8* %t5082 to i64
    %t5084 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.331, i64 0, i64 0
    %t5085 = ptrtoint i8* %t5084 to i64
    %t5086 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5083, i64 %t5085)
    ret i64 %t5086
    br label %if.end.5080
if.end.5080:
    %t5087 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.332, i64 0, i64 0
    %t5088 = ptrtoint i8* %t5087 to i64
    %t5089 = load i64, i64* %path
    %t5090 = call i64 @freak_llvm_word_concat(i64 %t5088, i64 %t5089)
    %t5091 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.333, i64 0, i64 0
    %t5092 = ptrtoint i8* %t5091 to i64
    %t5093 = call i64 @freak_llvm_word_concat(i64 %t5090, i64 %t5092)
    %t5094 = load i64, i64* %host
    %t5095 = call i64 @freak_llvm_word_concat(i64 %t5093, i64 %t5094)
    %t5096 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.334, i64 0, i64 0
    %t5097 = ptrtoint i8* %t5096 to i64
    %t5098 = call i64 @freak_llvm_word_concat(i64 %t5095, i64 %t5097)
    %req_v5099 = alloca i64
    store i64 %t5098, i64* %req_v5099
    %t5100 = load i64, i64* %fd_v5074
    %t5101 = load i64, i64* %req_v5099
    %t5102 = call i64 @freak_llvm_tcp_send(i64 %t5100, i64 %t5101)
    %t5103 = load i64, i64* %fd_v5074
    %t5104 = call i64 @freak_llvm_tcp_recv_all(i64 %t5103, i64 65536)
    %raw_v5105 = alloca i64
    store i64 %t5104, i64* %raw_v5105
    %t5106 = load i64, i64* %fd_v5074
    call void @freak_llvm_tcp_close(i64 %t5106)
    %t5107 = load i64, i64* %raw_v5105
    %t5108 = call i64 @freak_http_split_response(i64 %t5107)
    ret i64 %t5108
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
    %t5109 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.335, i64 0, i64 0
    %t5110 = ptrtoint i8* %t5109 to i64
    store i64 %t5110, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    store i64 0, i64* @g_json_len
    store i64 0, i64* @g_http_resp_statuses
    store i64 0, i64* @g_http_resp_bodies
    store i64 0, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 0, i64* @g_http_inited
    store i64 15, i64* @g_x
    %t5111 = load i64, i64* @g_x
    %t5113 = icmp sgt i64 %t5111, 20
    %t5112 = zext i1 %t5113 to i64
    %t5117 = icmp ne i64 %t5112, 0
    br i1 %t5117, label %if.then.5114, label %if.else.5115
if.then.5114:
    %t5118 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.336, i64 0, i64 0
    %t5119 = ptrtoint i8* %t5118 to i64
    call void @freak_llvm_say(i64 %t5119)
    br label %if.end.5116
if.else.5115:
    %t5120 = load i64, i64* @g_x
    %t5122 = icmp sgt i64 %t5120, 10
    %t5121 = zext i1 %t5122 to i64
    %t5126 = icmp ne i64 %t5121, 0
    br i1 %t5126, label %if.then.5123, label %if.else.5124
if.then.5123:
    %t5127 = getelementptr inbounds [4 x i8], [4 x i8]* @.str.337, i64 0, i64 0
    %t5128 = ptrtoint i8* %t5127 to i64
    call void @freak_llvm_say(i64 %t5128)
    br label %if.end.5125
if.else.5124:
    %t5129 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.338, i64 0, i64 0
    %t5130 = ptrtoint i8* %t5129 to i64
    call void @freak_llvm_say(i64 %t5130)
    br label %if.end.5125
if.end.5125:
    br label %if.end.5116
if.end.5116:
    store i64 3, i64* @g_day
    %t5131 = load i64, i64* @g_day
    br label %when.case.5133
when.case.5133:
    %t5136 = icmp eq i64 %t5131, 1
    br i1 %t5136, label %when.do.5135, label %when.case.5134
when.do.5135:
    %t5137 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.339, i64 0, i64 0
    %t5138 = ptrtoint i8* %t5137 to i64
    call void @freak_llvm_say(i64 %t5138)
    br label %when.end.5132
when.case.5134:
    %t5141 = icmp eq i64 %t5131, 2
    br i1 %t5141, label %when.do.5140, label %when.case.5139
when.do.5140:
    %t5142 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.340, i64 0, i64 0
    %t5143 = ptrtoint i8* %t5142 to i64
    call void @freak_llvm_say(i64 %t5143)
    br label %when.end.5132
when.case.5139:
    %t5146 = icmp eq i64 %t5131, 3
    br i1 %t5146, label %when.do.5145, label %when.case.5144
when.do.5145:
    %t5147 = getelementptr inbounds [10 x i8], [10 x i8]* @.str.341, i64 0, i64 0
    %t5148 = ptrtoint i8* %t5147 to i64
    call void @freak_llvm_say(i64 %t5148)
    br label %when.end.5132
when.case.5144:
    br label %when.do.5150
when.do.5150:
    %t5151 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.342, i64 0, i64 0
    %t5152 = ptrtoint i8* %t5151 to i64
    call void @freak_llvm_say(i64 %t5152)
    br label %when.end.5132
when.case.5149:
    br label %when.end.5132
when.end.5132:
    store i64 1, i64* @g_active
    %t5153 = load i64, i64* @g_active
    %t5157 = icmp ne i64 %t5153, 0
    br i1 %t5157, label %if.then.5154, label %if.end.5156
if.then.5154:
    %t5158 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.343, i64 0, i64 0
    %t5159 = ptrtoint i8* %t5158 to i64
    call void @freak_llvm_say(i64 %t5159)
    br label %if.end.5156
if.end.5156:
    %t5160 = load i64, i64* @g_active
    %t5162 = icmp eq i64 %t5160, 0
    %t5161 = zext i1 %t5162 to i64
    %t5166 = icmp ne i64 %t5161, 0
    br i1 %t5166, label %if.then.5163, label %if.end.5165
if.then.5163:
    %t5167 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.344, i64 0, i64 0
    %t5168 = ptrtoint i8* %t5167 to i64
    call void @freak_llvm_say(i64 %t5168)
    br label %if.end.5165
if.end.5165:
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
@.str.336 = private unnamed_addr constant [5 x i8] c"huge\00", align 1
@.str.337 = private unnamed_addr constant [4 x i8] c"big\00", align 1
@.str.338 = private unnamed_addr constant [6 x i8] c"small\00", align 1
@.str.339 = private unnamed_addr constant [7 x i8] c"Monday\00", align 1
@.str.340 = private unnamed_addr constant [8 x i8] c"Tuesday\00", align 1
@.str.341 = private unnamed_addr constant [10 x i8] c"Wednesday\00", align 1
@.str.342 = private unnamed_addr constant [6 x i8] c"Other\00", align 1
@.str.343 = private unnamed_addr constant [7 x i8] c"active\00", align 1
@.str.344 = private unnamed_addr constant [9 x i8] c"inactive\00", align 1

