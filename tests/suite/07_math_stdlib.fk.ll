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
    %t190 = load i64, i64* %x
    %t192 = icmp sgt i64 %t190, 0
    %t191 = zext i1 %t192 to i64
    %t196 = icmp ne i64 %t191, 0
    br i1 %t196, label %if.then.193, label %if.end.195
if.then.193:
    ret i64 1
    br label %if.end.195
if.end.195:
    %t197 = load i64, i64* %x
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
    %x_v207 = alloca i64
    store i64 %t206, i64* %x_v207
    %t208 = load i64, i64* %b
    %t209 = call i64 @freak_std_abs(i64 %t208)
    %y_v210 = alloca i64
    store i64 %t209, i64* %y_v210
    br label %loop.cond.211
loop.cond.211:
    %t214 = load i64, i64* %y_v210
    %t216 = icmp eq i64 %t214, 0
    %t215 = zext i1 %t216 to i64
    %t217 = icmp eq i64 %t215, 0
    br i1 %t217, label %loop.body.212, label %loop.end.213
loop.body.212:
    %t218 = load i64, i64* %y_v210
    %tmp_v219 = alloca i64
    store i64 %t218, i64* %tmp_v219
    %t220 = load i64, i64* %x_v207
    %t221 = load i64, i64* %x_v207
    %t222 = load i64, i64* %y_v210
    %t223 = sdiv i64 %t221, %t222
    %t224 = load i64, i64* %y_v210
    %t225 = mul i64 %t223, %t224
    %t226 = sub i64 %t220, %t225
    %rem_v227 = alloca i64
    store i64 %t226, i64* %rem_v227
    %t228 = load i64, i64* %tmp_v219
    store i64 %t228, i64* %x_v207
    %t229 = load i64, i64* %rem_v227
    store i64 %t229, i64* %y_v210
    br label %loop.cond.211
loop.end.213:
    %t230 = load i64, i64* %x_v207
    ret i64 %t230
    ret i64 0
}

define i64 @freak_std_lcm(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t231 = load i64, i64* %a
    %t233 = icmp eq i64 %t231, 0
    %t232 = zext i1 %t233 to i64
    %t234 = load i64, i64* %b
    %t236 = icmp eq i64 %t234, 0
    %t235 = zext i1 %t236 to i64
    %t238 = icmp ne i64 %t232, 0
    %t239 = icmp ne i64 %t235, 0
    %t240 = or i1 %t238, %t239
    %t237 = zext i1 %t240 to i64
    %t244 = icmp ne i64 %t237, 0
    br i1 %t244, label %if.then.241, label %if.end.243
if.then.241:
    ret i64 0
    br label %if.end.243
if.end.243:
    %t245 = load i64, i64* %a
    %t246 = load i64, i64* %b
    %t247 = call i64 @freak_std_gcd(i64 %t245, i64 %t246)
    %g_v248 = alloca i64
    store i64 %t247, i64* %g_v248
    %t249 = load i64, i64* %a
    %t250 = call i64 @freak_std_abs(i64 %t249)
    %aa_v251 = alloca i64
    store i64 %t250, i64* %aa_v251
    %t252 = load i64, i64* %b
    %t253 = call i64 @freak_std_abs(i64 %t252)
    %bb_v254 = alloca i64
    store i64 %t253, i64* %bb_v254
    %t255 = load i64, i64* %aa_v251
    %t256 = load i64, i64* %g_v248
    %t257 = sdiv i64 %t255, %t256
    %t258 = load i64, i64* %bb_v254
    %t259 = mul i64 %t257, %t258
    ret i64 %t259
    ret i64 0
}

define i64 @freak_std_factorial(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t260 = load i64, i64* %n
    %t262 = icmp sle i64 %t260, 1
    %t261 = zext i1 %t262 to i64
    %t266 = icmp ne i64 %t261, 0
    br i1 %t266, label %if.then.263, label %if.end.265
if.then.263:
    ret i64 1
    br label %if.end.265
if.end.265:
    %f_v267 = alloca i64
    store i64 1, i64* %f_v267
    %i_v268 = alloca i64
    store i64 2, i64* %i_v268
    br label %loop.cond.269
loop.cond.269:
    %t272 = load i64, i64* %i_v268
    %t273 = load i64, i64* %n
    %t275 = icmp sgt i64 %t272, %t273
    %t274 = zext i1 %t275 to i64
    %t276 = icmp eq i64 %t274, 0
    br i1 %t276, label %loop.body.270, label %loop.end.271
loop.body.270:
    %t277 = load i64, i64* %f_v267
    %t278 = load i64, i64* %i_v268
    %t279 = mul i64 %t277, %t278
    store i64 %t279, i64* %f_v267
    %t280 = load i64, i64* %i_v268
    %t281 = add i64 %t280, 1
    store i64 %t281, i64* %i_v268
    br label %loop.cond.269
loop.end.271:
    %t282 = load i64, i64* %f_v267
    ret i64 %t282
    ret i64 0
}

define i64 @freak_std_fibonacci(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t283 = load i64, i64* %n
    %t285 = icmp sle i64 %t283, 0
    %t284 = zext i1 %t285 to i64
    %t289 = icmp ne i64 %t284, 0
    br i1 %t289, label %if.then.286, label %if.end.288
if.then.286:
    ret i64 0
    br label %if.end.288
if.end.288:
    %t290 = load i64, i64* %n
    %t292 = icmp eq i64 %t290, 1
    %t291 = zext i1 %t292 to i64
    %t296 = icmp ne i64 %t291, 0
    br i1 %t296, label %if.then.293, label %if.end.295
if.then.293:
    ret i64 1
    br label %if.end.295
if.end.295:
    %a_v297 = alloca i64
    store i64 0, i64* %a_v297
    %b_v298 = alloca i64
    store i64 1, i64* %b_v298
    %i_v299 = alloca i64
    store i64 2, i64* %i_v299
    br label %loop.cond.300
loop.cond.300:
    %t303 = load i64, i64* %i_v299
    %t304 = load i64, i64* %n
    %t306 = icmp sgt i64 %t303, %t304
    %t305 = zext i1 %t306 to i64
    %t307 = icmp eq i64 %t305, 0
    br i1 %t307, label %loop.body.301, label %loop.end.302
loop.body.301:
    %t308 = load i64, i64* %a_v297
    %t309 = load i64, i64* %b_v298
    %t310 = add i64 %t308, %t309
    %tmp_v311 = alloca i64
    store i64 %t310, i64* %tmp_v311
    %t312 = load i64, i64* %b_v298
    store i64 %t312, i64* %a_v297
    %t313 = load i64, i64* %tmp_v311
    store i64 %t313, i64* %b_v298
    %t314 = load i64, i64* %i_v299
    %t315 = add i64 %t314, 1
    store i64 %t315, i64* %i_v299
    br label %loop.cond.300
loop.end.302:
    %t316 = load i64, i64* %b_v298
    ret i64 %t316
    ret i64 0
}

define i64 @freak_std_is_even(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t317 = load i64, i64* %x
    %t318 = sdiv i64 %t317, 2
    %half_v319 = alloca i64
    store i64 %t318, i64* %half_v319
    %t320 = load i64, i64* %half_v319
    %t321 = mul i64 %t320, 2
    %t322 = load i64, i64* %x
    %t324 = icmp eq i64 %t321, %t322
    %t323 = zext i1 %t324 to i64
    ret i64 %t323
    ret i64 0
}

define i64 @freak_std_is_odd(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t325 = load i64, i64* %x
    %t326 = call i64 @freak_std_is_even(i64 %t325)
    %t328 = icmp eq i64 %t326, 0
    %t327 = zext i1 %t328 to i64
    ret i64 %t327
    ret i64 0
}

define i64 @freak_string_repeat(i64 %arg_s, i64 %arg_count) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %count = alloca i64
    store i64 %arg_count, i64* %count
    %t329 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.7, i64 0, i64 0
    %t330 = ptrtoint i8* %t329 to i64
    %out_v331 = alloca i64
    store i64 %t330, i64* %out_v331
    %i_v332 = alloca i64
    store i64 0, i64* %i_v332
    %t338 = load i64, i64* %count
    %rep.337 = alloca i64
    store i64 0, i64* %rep.337
    br label %loop.cond.333
loop.cond.333:
    %t339 = load i64, i64* %rep.337
    %t340 = icmp slt i64 %t339, %t338
    br i1 %t340, label %loop.body.334, label %loop.end.335
loop.body.334:
    %t341 = load i64, i64* %out_v331
    %t342 = load i64, i64* %s
    %t343 = call i64 @freak_llvm_word_concat(i64 %t341, i64 %t342)
    store i64 %t343, i64* %out_v331
    %t344 = load i64, i64* %i_v332
    %t345 = add i64 %t344, 1
    store i64 %t345, i64* %i_v332
    br label %loop.inc.336
loop.inc.336:
    %t346 = load i64, i64* %rep.337
    %t347 = add i64 %t346, 1
    store i64 %t347, i64* %rep.337
    br label %loop.cond.333
loop.end.335:
    %t348 = load i64, i64* %out_v331
    ret i64 %t348
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
    %t349 = load i64, i64* %s
    %t350 = call i64 @freak_llvm_word_length(i64 %t349)
    %slen_v351 = alloca i64
    store i64 %t350, i64* %slen_v351
    %t352 = load i64, i64* %slen_v351
    %t353 = load i64, i64* %width
    %t355 = icmp sge i64 %t352, %t353
    %t354 = zext i1 %t355 to i64
    %t359 = icmp ne i64 %t354, 0
    br i1 %t359, label %if.then.356, label %if.end.358
if.then.356:
    %t360 = load i64, i64* %s
    ret i64 %t360
    br label %if.end.358
if.end.358:
    %t361 = load i64, i64* %width
    %t362 = load i64, i64* %slen_v351
    %t363 = sub i64 %t361, %t362
    %needed_v364 = alloca i64
    store i64 %t363, i64* %needed_v364
    %t365 = load i64, i64* %pad_char
    %t366 = load i64, i64* %needed_v364
    %t367 = call i64 @freak_string_repeat(i64 %t365, i64 %t366)
    %padding_v368 = alloca i64
    store i64 %t367, i64* %padding_v368
    %t369 = load i64, i64* %padding_v368
    %t370 = load i64, i64* %s
    %t371 = call i64 @freak_llvm_word_concat(i64 %t369, i64 %t370)
    ret i64 %t371
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
    %t372 = load i64, i64* %s
    %t373 = call i64 @freak_llvm_word_length(i64 %t372)
    %slen_v374 = alloca i64
    store i64 %t373, i64* %slen_v374
    %t375 = load i64, i64* %slen_v374
    %t376 = load i64, i64* %width
    %t378 = icmp sge i64 %t375, %t376
    %t377 = zext i1 %t378 to i64
    %t382 = icmp ne i64 %t377, 0
    br i1 %t382, label %if.then.379, label %if.end.381
if.then.379:
    %t383 = load i64, i64* %s
    ret i64 %t383
    br label %if.end.381
if.end.381:
    %t384 = load i64, i64* %width
    %t385 = load i64, i64* %slen_v374
    %t386 = sub i64 %t384, %t385
    %needed_v387 = alloca i64
    store i64 %t386, i64* %needed_v387
    %t388 = load i64, i64* %pad_char
    %t389 = load i64, i64* %needed_v387
    %t390 = call i64 @freak_string_repeat(i64 %t388, i64 %t389)
    %padding_v391 = alloca i64
    store i64 %t390, i64* %padding_v391
    %t392 = load i64, i64* %s
    %t393 = load i64, i64* %padding_v391
    %t394 = call i64 @freak_llvm_word_concat(i64 %t392, i64 %t393)
    ret i64 %t394
    ret i64 0
}

define i64 @freak_string_reverse(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t395 = load i64, i64* %s
    %t396 = call i64 @freak_llvm_word_length(i64 %t395)
    %slen_v397 = alloca i64
    store i64 %t396, i64* %slen_v397
    %t398 = load i64, i64* %slen_v397
    %t400 = icmp sle i64 %t398, 1
    %t399 = zext i1 %t400 to i64
    %t404 = icmp ne i64 %t399, 0
    br i1 %t404, label %if.then.401, label %if.end.403
if.then.401:
    %t405 = load i64, i64* %s
    ret i64 %t405
    br label %if.end.403
if.end.403:
    %t406 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.8, i64 0, i64 0
    %t407 = ptrtoint i8* %t406 to i64
    %out_v408 = alloca i64
    store i64 %t407, i64* %out_v408
    %t409 = load i64, i64* %slen_v397
    %t410 = sub i64 %t409, 1
    %i_v411 = alloca i64
    store i64 %t410, i64* %i_v411
    %t417 = load i64, i64* %slen_v397
    %rep.416 = alloca i64
    store i64 0, i64* %rep.416
    br label %loop.cond.412
loop.cond.412:
    %t418 = load i64, i64* %rep.416
    %t419 = icmp slt i64 %t418, %t417
    br i1 %t419, label %loop.body.413, label %loop.end.414
loop.body.413:
    %t420 = load i64, i64* %out_v408
    %t421 = load i64, i64* %s
    %t423 = load i64, i64* %i_v411
    %t422 = call i64 @freak_llvm_word_char_at(i64 %t421, i64 %t423)
    %t424 = call i64 @freak_llvm_word_concat(i64 %t420, i64 %t422)
    store i64 %t424, i64* %out_v408
    %t425 = load i64, i64* %i_v411
    %t426 = sub i64 %t425, 1
    store i64 %t426, i64* %i_v411
    br label %loop.inc.415
loop.inc.415:
    %t427 = load i64, i64* %rep.416
    %t428 = add i64 %t427, 1
    store i64 %t428, i64* %rep.416
    br label %loop.cond.412
loop.end.414:
    %t429 = load i64, i64* %out_v408
    ret i64 %t429
    ret i64 0
}

define i64 @freak_string_count(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t430 = load i64, i64* %haystack
    %t431 = call i64 @freak_llvm_word_length(i64 %t430)
    %hlen_v432 = alloca i64
    store i64 %t431, i64* %hlen_v432
    %t433 = load i64, i64* %needle
    %t434 = call i64 @freak_llvm_word_length(i64 %t433)
    %nlen_v435 = alloca i64
    store i64 %t434, i64* %nlen_v435
    %t436 = load i64, i64* %nlen_v435
    %t438 = icmp eq i64 %t436, 0
    %t437 = zext i1 %t438 to i64
    %t442 = icmp ne i64 %t437, 0
    br i1 %t442, label %if.then.439, label %if.end.441
if.then.439:
    ret i64 0
    br label %if.end.441
if.end.441:
    %t443 = load i64, i64* %nlen_v435
    %t444 = load i64, i64* %hlen_v432
    %t446 = icmp sgt i64 %t443, %t444
    %t445 = zext i1 %t446 to i64
    %t450 = icmp ne i64 %t445, 0
    br i1 %t450, label %if.then.447, label %if.end.449
if.then.447:
    ret i64 0
    br label %if.end.449
if.end.449:
    %count_v451 = alloca i64
    store i64 0, i64* %count_v451
    %i_v452 = alloca i64
    store i64 0, i64* %i_v452
    %t453 = load i64, i64* %hlen_v432
    %t454 = load i64, i64* %nlen_v435
    %t455 = sub i64 %t453, %t454
    %t456 = add i64 %t455, 1
    %limit_v457 = alloca i64
    store i64 %t456, i64* %limit_v457
    %t463 = load i64, i64* %limit_v457
    %rep.462 = alloca i64
    store i64 0, i64* %rep.462
    br label %loop.cond.458
loop.cond.458:
    %t464 = load i64, i64* %rep.462
    %t465 = icmp slt i64 %t464, %t463
    br i1 %t465, label %loop.body.459, label %loop.end.460
loop.body.459:
    %match_v466 = alloca i64
    store i64 1, i64* %match_v466
    %j_v467 = alloca i64
    store i64 0, i64* %j_v467
    %t473 = load i64, i64* %nlen_v435
    %rep.472 = alloca i64
    store i64 0, i64* %rep.472
    br label %loop.cond.468
loop.cond.468:
    %t474 = load i64, i64* %rep.472
    %t475 = icmp slt i64 %t474, %t473
    br i1 %t475, label %loop.body.469, label %loop.end.470
loop.body.469:
    %t476 = load i64, i64* %match_v466
    %t480 = icmp ne i64 %t476, 0
    br i1 %t480, label %if.then.477, label %if.end.479
if.then.477:
    %t481 = load i64, i64* %haystack
    %t483 = load i64, i64* %i_v452
    %t484 = load i64, i64* %j_v467
    %t485 = add i64 %t483, %t484
    %t482 = call i64 @freak_llvm_word_char_at(i64 %t481, i64 %t485)
    %t486 = load i64, i64* %needle
    %t488 = load i64, i64* %j_v467
    %t487 = call i64 @freak_llvm_word_char_at(i64 %t486, i64 %t488)
    %t489 = call i64 @freak_llvm_word_neq(i64 %t482, i64 %t487)
    %t493 = icmp ne i64 %t489, 0
    br i1 %t493, label %if.then.490, label %if.end.492
if.then.490:
    store i64 0, i64* %match_v466
    br label %if.end.492
if.end.492:
    br label %if.end.479
if.end.479:
    %t494 = load i64, i64* %j_v467
    %t495 = add i64 %t494, 1
    store i64 %t495, i64* %j_v467
    br label %loop.inc.471
loop.inc.471:
    %t496 = load i64, i64* %rep.472
    %t497 = add i64 %t496, 1
    store i64 %t497, i64* %rep.472
    br label %loop.cond.468
loop.end.470:
    %t498 = load i64, i64* %match_v466
    %t502 = icmp ne i64 %t498, 0
    br i1 %t502, label %if.then.499, label %if.end.501
if.then.499:
    %t503 = load i64, i64* %count_v451
    %t504 = add i64 %t503, 1
    store i64 %t504, i64* %count_v451
    br label %if.end.501
if.end.501:
    %t505 = load i64, i64* %i_v452
    %t506 = add i64 %t505, 1
    store i64 %t506, i64* %i_v452
    br label %loop.inc.461
loop.inc.461:
    %t507 = load i64, i64* %rep.462
    %t508 = add i64 %t507, 1
    store i64 %t508, i64* %rep.462
    br label %loop.cond.458
loop.end.460:
    %t509 = load i64, i64* %count_v451
    ret i64 %t509
    ret i64 0
}

define i64 @freak_string_split(i64 %arg_s, i64 %arg_delim) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %delim = alloca i64
    store i64 %arg_delim, i64* %delim
    %t510 = load i64, i64* %s
    %t511 = call i64 @freak_llvm_word_length(i64 %t510)
    %slen_v512 = alloca i64
    store i64 %t511, i64* %slen_v512
    %t513 = load i64, i64* %delim
    %t514 = call i64 @freak_llvm_word_length(i64 %t513)
    %dlen_v515 = alloca i64
    store i64 %t514, i64* %dlen_v515
    %t516 = load i64, i64* %dlen_v515
    %t518 = icmp eq i64 %t516, 0
    %t517 = zext i1 %t518 to i64
    %t522 = icmp ne i64 %t517, 0
    br i1 %t522, label %if.then.519, label %if.end.521
if.then.519:
    %t523 = load i64, i64* %s
    ret i64 %t523
    br label %if.end.521
if.end.521:
    %t524 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.9, i64 0, i64 0
    %t525 = ptrtoint i8* %t524 to i64
    %sp_out_v526 = alloca i64
    store i64 %t525, i64* %sp_out_v526
    %t527 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.10, i64 0, i64 0
    %t528 = ptrtoint i8* %t527 to i64
    %sp_cur_v529 = alloca i64
    store i64 %t528, i64* %sp_cur_v529
    %sp_i_v530 = alloca i64
    store i64 0, i64* %sp_i_v530
    %t536 = load i64, i64* %slen_v512
    %rep.535 = alloca i64
    store i64 0, i64* %rep.535
    br label %loop.cond.531
loop.cond.531:
    %t537 = load i64, i64* %rep.535
    %t538 = icmp slt i64 %t537, %t536
    br i1 %t538, label %loop.body.532, label %loop.end.533
loop.body.532:
    %sp_match_v539 = alloca i64
    store i64 1, i64* %sp_match_v539
    %t540 = load i64, i64* %sp_i_v530
    %t541 = load i64, i64* %dlen_v515
    %t542 = add i64 %t540, %t541
    %t543 = load i64, i64* %slen_v512
    %t545 = icmp sle i64 %t542, %t543
    %t544 = zext i1 %t545 to i64
    %t549 = icmp ne i64 %t544, 0
    br i1 %t549, label %if.then.546, label %if.else.547
if.then.546:
    %sp_j_v550 = alloca i64
    store i64 0, i64* %sp_j_v550
    %t556 = load i64, i64* %dlen_v515
    %rep.555 = alloca i64
    store i64 0, i64* %rep.555
    br label %loop.cond.551
loop.cond.551:
    %t557 = load i64, i64* %rep.555
    %t558 = icmp slt i64 %t557, %t556
    br i1 %t558, label %loop.body.552, label %loop.end.553
loop.body.552:
    %t559 = load i64, i64* %sp_match_v539
    %t563 = icmp ne i64 %t559, 0
    br i1 %t563, label %if.then.560, label %if.end.562
if.then.560:
    %t564 = load i64, i64* %s
    %t566 = load i64, i64* %sp_i_v530
    %t567 = load i64, i64* %sp_j_v550
    %t568 = add i64 %t566, %t567
    %t565 = call i64 @freak_llvm_word_char_at(i64 %t564, i64 %t568)
    %t569 = load i64, i64* %delim
    %t571 = load i64, i64* %sp_j_v550
    %t570 = call i64 @freak_llvm_word_char_at(i64 %t569, i64 %t571)
    %t572 = call i64 @freak_llvm_word_neq(i64 %t565, i64 %t570)
    %t576 = icmp ne i64 %t572, 0
    br i1 %t576, label %if.then.573, label %if.end.575
if.then.573:
    store i64 0, i64* %sp_match_v539
    br label %if.end.575
if.end.575:
    br label %if.end.562
if.end.562:
    %t577 = load i64, i64* %sp_j_v550
    %t578 = add i64 %t577, 1
    store i64 %t578, i64* %sp_j_v550
    br label %loop.inc.554
loop.inc.554:
    %t579 = load i64, i64* %rep.555
    %t580 = add i64 %t579, 1
    store i64 %t580, i64* %rep.555
    br label %loop.cond.551
loop.end.553:
    br label %if.end.548
if.else.547:
    store i64 0, i64* %sp_match_v539
    br label %if.end.548
if.end.548:
    %t581 = load i64, i64* %sp_match_v539
    %t585 = icmp ne i64 %t581, 0
    br i1 %t585, label %if.then.582, label %if.else.583
if.then.582:
    %t586 = load i64, i64* %sp_out_v526
    %t587 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.11, i64 0, i64 0
    %t588 = ptrtoint i8* %t587 to i64
    %t589 = call i64 @freak_llvm_word_eq(i64 %t586, i64 %t588)
    %t593 = icmp ne i64 %t589, 0
    br i1 %t593, label %if.then.590, label %if.else.591
if.then.590:
    %t594 = load i64, i64* %sp_cur_v529
    store i64 %t594, i64* %sp_out_v526
    br label %if.end.592
if.else.591:
    %t595 = load i64, i64* %sp_out_v526
    %t596 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.12, i64 0, i64 0
    %t597 = ptrtoint i8* %t596 to i64
    %t598 = call i64 @freak_llvm_word_concat(i64 %t595, i64 %t597)
    %t599 = load i64, i64* %sp_cur_v529
    %t600 = call i64 @freak_llvm_word_concat(i64 %t598, i64 %t599)
    store i64 %t600, i64* %sp_out_v526
    br label %if.end.592
if.end.592:
    %t601 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.13, i64 0, i64 0
    %t602 = ptrtoint i8* %t601 to i64
    store i64 %t602, i64* %sp_cur_v529
    %t603 = load i64, i64* %dlen_v515
    %t604 = load i64, i64* %sp_i_v530
    %t605 = add i64 %t604, %t603
    store i64 %t605, i64* %sp_i_v530
    br label %if.end.584
if.else.583:
    %t606 = load i64, i64* %sp_cur_v529
    %t607 = load i64, i64* %s
    %t609 = load i64, i64* %sp_i_v530
    %t608 = call i64 @freak_llvm_word_char_at(i64 %t607, i64 %t609)
    %t610 = call i64 @freak_llvm_word_concat(i64 %t606, i64 %t608)
    store i64 %t610, i64* %sp_cur_v529
    %t611 = load i64, i64* %sp_i_v530
    %t612 = add i64 %t611, 1
    store i64 %t612, i64* %sp_i_v530
    br label %if.end.584
if.end.584:
    br label %loop.inc.534
loop.inc.534:
    %t613 = load i64, i64* %rep.535
    %t614 = add i64 %t613, 1
    store i64 %t614, i64* %rep.535
    br label %loop.cond.531
loop.end.533:
    %t615 = load i64, i64* %sp_out_v526
    %t616 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.14, i64 0, i64 0
    %t617 = ptrtoint i8* %t616 to i64
    %t618 = call i64 @freak_llvm_word_eq(i64 %t615, i64 %t617)
    %t622 = icmp ne i64 %t618, 0
    br i1 %t622, label %if.then.619, label %if.else.620
if.then.619:
    %t623 = load i64, i64* %sp_cur_v529
    store i64 %t623, i64* %sp_out_v526
    br label %if.end.621
if.else.620:
    %t624 = load i64, i64* %sp_out_v526
    %t625 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.15, i64 0, i64 0
    %t626 = ptrtoint i8* %t625 to i64
    %t627 = call i64 @freak_llvm_word_concat(i64 %t624, i64 %t626)
    %t628 = load i64, i64* %sp_cur_v529
    %t629 = call i64 @freak_llvm_word_concat(i64 %t627, i64 %t628)
    store i64 %t629, i64* %sp_out_v526
    br label %if.end.621
if.end.621:
    %t630 = load i64, i64* %sp_out_v526
    ret i64 %t630
    ret i64 0
}

define i64 @freak_string_join(i64 %arg_parts, i64 %arg_separator) {
entry:
    %parts = alloca i64
    store i64 %arg_parts, i64* %parts
    %separator = alloca i64
    store i64 %arg_separator, i64* %separator
    %t631 = load i64, i64* %parts
    %t632 = call i64 @freak_llvm_word_length(i64 %t631)
    %plen_v633 = alloca i64
    store i64 %t632, i64* %plen_v633
    %t634 = load i64, i64* %plen_v633
    %t636 = icmp eq i64 %t634, 0
    %t635 = zext i1 %t636 to i64
    %t640 = icmp ne i64 %t635, 0
    br i1 %t640, label %if.then.637, label %if.end.639
if.then.637:
    %t641 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.16, i64 0, i64 0
    %t642 = ptrtoint i8* %t641 to i64
    ret i64 %t642
    br label %if.end.639
if.end.639:
    %t643 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.17, i64 0, i64 0
    %t644 = ptrtoint i8* %t643 to i64
    %jn_out_v645 = alloca i64
    store i64 %t644, i64* %jn_out_v645
    %t646 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.18, i64 0, i64 0
    %t647 = ptrtoint i8* %t646 to i64
    %jn_cur_v648 = alloca i64
    store i64 %t647, i64* %jn_cur_v648
    %jn_first_v649 = alloca i64
    store i64 1, i64* %jn_first_v649
    %jn_i_v650 = alloca i64
    store i64 0, i64* %jn_i_v650
    %t656 = load i64, i64* %plen_v633
    %rep.655 = alloca i64
    store i64 0, i64* %rep.655
    br label %loop.cond.651
loop.cond.651:
    %t657 = load i64, i64* %rep.655
    %t658 = icmp slt i64 %t657, %t656
    br i1 %t658, label %loop.body.652, label %loop.end.653
loop.body.652:
    %t659 = load i64, i64* %parts
    %t661 = load i64, i64* %jn_i_v650
    %t660 = call i64 @freak_llvm_word_char_at(i64 %t659, i64 %t661)
    %jn_c_v662 = alloca i64
    store i64 %t660, i64* %jn_c_v662
    %t663 = load i64, i64* %jn_c_v662
    %t664 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.19, i64 0, i64 0
    %t665 = ptrtoint i8* %t664 to i64
    %t666 = call i64 @freak_llvm_word_eq(i64 %t663, i64 %t665)
    %t670 = icmp ne i64 %t666, 0
    br i1 %t670, label %if.then.667, label %if.else.668
if.then.667:
    %t671 = load i64, i64* %jn_first_v649
    %t675 = icmp ne i64 %t671, 0
    br i1 %t675, label %if.then.672, label %if.else.673
if.then.672:
    %t676 = load i64, i64* %jn_cur_v648
    store i64 %t676, i64* %jn_out_v645
    store i64 0, i64* %jn_first_v649
    br label %if.end.674
if.else.673:
    %t677 = load i64, i64* %jn_out_v645
    %t678 = load i64, i64* %separator
    %t679 = call i64 @freak_llvm_word_concat(i64 %t677, i64 %t678)
    %t680 = load i64, i64* %jn_cur_v648
    %t681 = call i64 @freak_llvm_word_concat(i64 %t679, i64 %t680)
    store i64 %t681, i64* %jn_out_v645
    br label %if.end.674
if.end.674:
    %t682 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.20, i64 0, i64 0
    %t683 = ptrtoint i8* %t682 to i64
    store i64 %t683, i64* %jn_cur_v648
    br label %if.end.669
if.else.668:
    %t684 = load i64, i64* %jn_cur_v648
    %t685 = load i64, i64* %jn_c_v662
    %t686 = call i64 @freak_llvm_word_concat(i64 %t684, i64 %t685)
    store i64 %t686, i64* %jn_cur_v648
    br label %if.end.669
if.end.669:
    %t687 = load i64, i64* %jn_i_v650
    %t688 = add i64 %t687, 1
    store i64 %t688, i64* %jn_i_v650
    br label %loop.inc.654
loop.inc.654:
    %t689 = load i64, i64* %rep.655
    %t690 = add i64 %t689, 1
    store i64 %t690, i64* %rep.655
    br label %loop.cond.651
loop.end.653:
    %t691 = load i64, i64* %jn_first_v649
    %t695 = icmp ne i64 %t691, 0
    br i1 %t695, label %if.then.692, label %if.else.693
if.then.692:
    %t696 = load i64, i64* %jn_cur_v648
    store i64 %t696, i64* %jn_out_v645
    br label %if.end.694
if.else.693:
    %t697 = load i64, i64* %jn_out_v645
    %t698 = load i64, i64* %separator
    %t699 = call i64 @freak_llvm_word_concat(i64 %t697, i64 %t698)
    %t700 = load i64, i64* %jn_cur_v648
    %t701 = call i64 @freak_llvm_word_concat(i64 %t699, i64 %t700)
    store i64 %t701, i64* %jn_out_v645
    br label %if.end.694
if.end.694:
    %t702 = load i64, i64* %jn_out_v645
    ret i64 %t702
    ret i64 0
}

define i64 @freak_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t703 = load i64, i64* %c
    %t704 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.21, i64 0, i64 0
    %t705 = ptrtoint i8* %t704 to i64
    %t706 = call i64 @freak_llvm_word_eq(i64 %t703, i64 %t705)
    %t710 = icmp ne i64 %t706, 0
    br i1 %t710, label %if.then.707, label %if.end.709
if.then.707:
    ret i64 1
    br label %if.end.709
if.end.709:
    %t711 = load i64, i64* %c
    %t712 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.22, i64 0, i64 0
    %t713 = ptrtoint i8* %t712 to i64
    %t714 = call i64 @freak_llvm_word_eq(i64 %t711, i64 %t713)
    %t718 = icmp ne i64 %t714, 0
    br i1 %t718, label %if.then.715, label %if.end.717
if.then.715:
    ret i64 1
    br label %if.end.717
if.end.717:
    %t719 = load i64, i64* %c
    %t720 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.23, i64 0, i64 0
    %t721 = ptrtoint i8* %t720 to i64
    %t722 = call i64 @freak_llvm_word_eq(i64 %t719, i64 %t721)
    %t726 = icmp ne i64 %t722, 0
    br i1 %t726, label %if.then.723, label %if.end.725
if.then.723:
    ret i64 1
    br label %if.end.725
if.end.725:
    %t727 = load i64, i64* %c
    %t728 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.24, i64 0, i64 0
    %t729 = ptrtoint i8* %t728 to i64
    %t730 = call i64 @freak_llvm_word_eq(i64 %t727, i64 %t729)
    %t734 = icmp ne i64 %t730, 0
    br i1 %t734, label %if.then.731, label %if.end.733
if.then.731:
    ret i64 1
    br label %if.end.733
if.end.733:
    %t735 = load i64, i64* %c
    %t736 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.25, i64 0, i64 0
    %t737 = ptrtoint i8* %t736 to i64
    %t738 = call i64 @freak_llvm_word_eq(i64 %t735, i64 %t737)
    %t742 = icmp ne i64 %t738, 0
    br i1 %t742, label %if.then.739, label %if.end.741
if.then.739:
    ret i64 1
    br label %if.end.741
if.end.741:
    %t743 = load i64, i64* %c
    %t744 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.26, i64 0, i64 0
    %t745 = ptrtoint i8* %t744 to i64
    %t746 = call i64 @freak_llvm_word_eq(i64 %t743, i64 %t745)
    %t750 = icmp ne i64 %t746, 0
    br i1 %t750, label %if.then.747, label %if.end.749
if.then.747:
    ret i64 1
    br label %if.end.749
if.end.749:
    %t751 = load i64, i64* %c
    %t752 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.27, i64 0, i64 0
    %t753 = ptrtoint i8* %t752 to i64
    %t754 = call i64 @freak_llvm_word_eq(i64 %t751, i64 %t753)
    %t758 = icmp ne i64 %t754, 0
    br i1 %t758, label %if.then.755, label %if.end.757
if.then.755:
    ret i64 1
    br label %if.end.757
if.end.757:
    %t759 = load i64, i64* %c
    %t760 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.28, i64 0, i64 0
    %t761 = ptrtoint i8* %t760 to i64
    %t762 = call i64 @freak_llvm_word_eq(i64 %t759, i64 %t761)
    %t766 = icmp ne i64 %t762, 0
    br i1 %t766, label %if.then.763, label %if.end.765
if.then.763:
    ret i64 1
    br label %if.end.765
if.end.765:
    %t767 = load i64, i64* %c
    %t768 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.29, i64 0, i64 0
    %t769 = ptrtoint i8* %t768 to i64
    %t770 = call i64 @freak_llvm_word_eq(i64 %t767, i64 %t769)
    %t774 = icmp ne i64 %t770, 0
    br i1 %t774, label %if.then.771, label %if.end.773
if.then.771:
    ret i64 1
    br label %if.end.773
if.end.773:
    %t775 = load i64, i64* %c
    %t776 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.30, i64 0, i64 0
    %t777 = ptrtoint i8* %t776 to i64
    %t778 = call i64 @freak_llvm_word_eq(i64 %t775, i64 %t777)
    %t782 = icmp ne i64 %t778, 0
    br i1 %t782, label %if.then.779, label %if.end.781
if.then.779:
    ret i64 1
    br label %if.end.781
if.end.781:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_alpha(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t783 = load i64, i64* %c
    %t784 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.31, i64 0, i64 0
    %t785 = ptrtoint i8* %t784 to i64
    %t786 = call i64 @freak_llvm_word_eq(i64 %t783, i64 %t785)
    %t787 = load i64, i64* %c
    %t788 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.32, i64 0, i64 0
    %t789 = ptrtoint i8* %t788 to i64
    %t790 = call i64 @freak_llvm_word_eq(i64 %t787, i64 %t789)
    %t792 = icmp ne i64 %t786, 0
    %t793 = icmp ne i64 %t790, 0
    %t794 = or i1 %t792, %t793
    %t791 = zext i1 %t794 to i64
    %t795 = load i64, i64* %c
    %t796 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.33, i64 0, i64 0
    %t797 = ptrtoint i8* %t796 to i64
    %t798 = call i64 @freak_llvm_word_eq(i64 %t795, i64 %t797)
    %t800 = icmp ne i64 %t791, 0
    %t801 = icmp ne i64 %t798, 0
    %t802 = or i1 %t800, %t801
    %t799 = zext i1 %t802 to i64
    %t803 = load i64, i64* %c
    %t804 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.34, i64 0, i64 0
    %t805 = ptrtoint i8* %t804 to i64
    %t806 = call i64 @freak_llvm_word_eq(i64 %t803, i64 %t805)
    %t808 = icmp ne i64 %t799, 0
    %t809 = icmp ne i64 %t806, 0
    %t810 = or i1 %t808, %t809
    %t807 = zext i1 %t810 to i64
    %t811 = load i64, i64* %c
    %t812 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.35, i64 0, i64 0
    %t813 = ptrtoint i8* %t812 to i64
    %t814 = call i64 @freak_llvm_word_eq(i64 %t811, i64 %t813)
    %t816 = icmp ne i64 %t807, 0
    %t817 = icmp ne i64 %t814, 0
    %t818 = or i1 %t816, %t817
    %t815 = zext i1 %t818 to i64
    %t822 = icmp ne i64 %t815, 0
    br i1 %t822, label %if.then.819, label %if.end.821
if.then.819:
    ret i64 1
    br label %if.end.821
if.end.821:
    %t823 = load i64, i64* %c
    %t824 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.36, i64 0, i64 0
    %t825 = ptrtoint i8* %t824 to i64
    %t826 = call i64 @freak_llvm_word_eq(i64 %t823, i64 %t825)
    %t827 = load i64, i64* %c
    %t828 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.37, i64 0, i64 0
    %t829 = ptrtoint i8* %t828 to i64
    %t830 = call i64 @freak_llvm_word_eq(i64 %t827, i64 %t829)
    %t832 = icmp ne i64 %t826, 0
    %t833 = icmp ne i64 %t830, 0
    %t834 = or i1 %t832, %t833
    %t831 = zext i1 %t834 to i64
    %t835 = load i64, i64* %c
    %t836 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.38, i64 0, i64 0
    %t837 = ptrtoint i8* %t836 to i64
    %t838 = call i64 @freak_llvm_word_eq(i64 %t835, i64 %t837)
    %t840 = icmp ne i64 %t831, 0
    %t841 = icmp ne i64 %t838, 0
    %t842 = or i1 %t840, %t841
    %t839 = zext i1 %t842 to i64
    %t843 = load i64, i64* %c
    %t844 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.39, i64 0, i64 0
    %t845 = ptrtoint i8* %t844 to i64
    %t846 = call i64 @freak_llvm_word_eq(i64 %t843, i64 %t845)
    %t848 = icmp ne i64 %t839, 0
    %t849 = icmp ne i64 %t846, 0
    %t850 = or i1 %t848, %t849
    %t847 = zext i1 %t850 to i64
    %t851 = load i64, i64* %c
    %t852 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.40, i64 0, i64 0
    %t853 = ptrtoint i8* %t852 to i64
    %t854 = call i64 @freak_llvm_word_eq(i64 %t851, i64 %t853)
    %t856 = icmp ne i64 %t847, 0
    %t857 = icmp ne i64 %t854, 0
    %t858 = or i1 %t856, %t857
    %t855 = zext i1 %t858 to i64
    %t862 = icmp ne i64 %t855, 0
    br i1 %t862, label %if.then.859, label %if.end.861
if.then.859:
    ret i64 1
    br label %if.end.861
if.end.861:
    %t863 = load i64, i64* %c
    %t864 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.41, i64 0, i64 0
    %t865 = ptrtoint i8* %t864 to i64
    %t866 = call i64 @freak_llvm_word_eq(i64 %t863, i64 %t865)
    %t867 = load i64, i64* %c
    %t868 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.42, i64 0, i64 0
    %t869 = ptrtoint i8* %t868 to i64
    %t870 = call i64 @freak_llvm_word_eq(i64 %t867, i64 %t869)
    %t872 = icmp ne i64 %t866, 0
    %t873 = icmp ne i64 %t870, 0
    %t874 = or i1 %t872, %t873
    %t871 = zext i1 %t874 to i64
    %t875 = load i64, i64* %c
    %t876 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.43, i64 0, i64 0
    %t877 = ptrtoint i8* %t876 to i64
    %t878 = call i64 @freak_llvm_word_eq(i64 %t875, i64 %t877)
    %t880 = icmp ne i64 %t871, 0
    %t881 = icmp ne i64 %t878, 0
    %t882 = or i1 %t880, %t881
    %t879 = zext i1 %t882 to i64
    %t883 = load i64, i64* %c
    %t884 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.44, i64 0, i64 0
    %t885 = ptrtoint i8* %t884 to i64
    %t886 = call i64 @freak_llvm_word_eq(i64 %t883, i64 %t885)
    %t888 = icmp ne i64 %t879, 0
    %t889 = icmp ne i64 %t886, 0
    %t890 = or i1 %t888, %t889
    %t887 = zext i1 %t890 to i64
    %t891 = load i64, i64* %c
    %t892 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.45, i64 0, i64 0
    %t893 = ptrtoint i8* %t892 to i64
    %t894 = call i64 @freak_llvm_word_eq(i64 %t891, i64 %t893)
    %t896 = icmp ne i64 %t887, 0
    %t897 = icmp ne i64 %t894, 0
    %t898 = or i1 %t896, %t897
    %t895 = zext i1 %t898 to i64
    %t902 = icmp ne i64 %t895, 0
    br i1 %t902, label %if.then.899, label %if.end.901
if.then.899:
    ret i64 1
    br label %if.end.901
if.end.901:
    %t903 = load i64, i64* %c
    %t904 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.46, i64 0, i64 0
    %t905 = ptrtoint i8* %t904 to i64
    %t906 = call i64 @freak_llvm_word_eq(i64 %t903, i64 %t905)
    %t907 = load i64, i64* %c
    %t908 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.47, i64 0, i64 0
    %t909 = ptrtoint i8* %t908 to i64
    %t910 = call i64 @freak_llvm_word_eq(i64 %t907, i64 %t909)
    %t912 = icmp ne i64 %t906, 0
    %t913 = icmp ne i64 %t910, 0
    %t914 = or i1 %t912, %t913
    %t911 = zext i1 %t914 to i64
    %t915 = load i64, i64* %c
    %t916 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.48, i64 0, i64 0
    %t917 = ptrtoint i8* %t916 to i64
    %t918 = call i64 @freak_llvm_word_eq(i64 %t915, i64 %t917)
    %t920 = icmp ne i64 %t911, 0
    %t921 = icmp ne i64 %t918, 0
    %t922 = or i1 %t920, %t921
    %t919 = zext i1 %t922 to i64
    %t923 = load i64, i64* %c
    %t924 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.49, i64 0, i64 0
    %t925 = ptrtoint i8* %t924 to i64
    %t926 = call i64 @freak_llvm_word_eq(i64 %t923, i64 %t925)
    %t928 = icmp ne i64 %t919, 0
    %t929 = icmp ne i64 %t926, 0
    %t930 = or i1 %t928, %t929
    %t927 = zext i1 %t930 to i64
    %t931 = load i64, i64* %c
    %t932 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.50, i64 0, i64 0
    %t933 = ptrtoint i8* %t932 to i64
    %t934 = call i64 @freak_llvm_word_eq(i64 %t931, i64 %t933)
    %t936 = icmp ne i64 %t927, 0
    %t937 = icmp ne i64 %t934, 0
    %t938 = or i1 %t936, %t937
    %t935 = zext i1 %t938 to i64
    %t942 = icmp ne i64 %t935, 0
    br i1 %t942, label %if.then.939, label %if.end.941
if.then.939:
    ret i64 1
    br label %if.end.941
if.end.941:
    %t943 = load i64, i64* %c
    %t944 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.51, i64 0, i64 0
    %t945 = ptrtoint i8* %t944 to i64
    %t946 = call i64 @freak_llvm_word_eq(i64 %t943, i64 %t945)
    %t947 = load i64, i64* %c
    %t948 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.52, i64 0, i64 0
    %t949 = ptrtoint i8* %t948 to i64
    %t950 = call i64 @freak_llvm_word_eq(i64 %t947, i64 %t949)
    %t952 = icmp ne i64 %t946, 0
    %t953 = icmp ne i64 %t950, 0
    %t954 = or i1 %t952, %t953
    %t951 = zext i1 %t954 to i64
    %t955 = load i64, i64* %c
    %t956 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.53, i64 0, i64 0
    %t957 = ptrtoint i8* %t956 to i64
    %t958 = call i64 @freak_llvm_word_eq(i64 %t955, i64 %t957)
    %t960 = icmp ne i64 %t951, 0
    %t961 = icmp ne i64 %t958, 0
    %t962 = or i1 %t960, %t961
    %t959 = zext i1 %t962 to i64
    %t963 = load i64, i64* %c
    %t964 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.54, i64 0, i64 0
    %t965 = ptrtoint i8* %t964 to i64
    %t966 = call i64 @freak_llvm_word_eq(i64 %t963, i64 %t965)
    %t968 = icmp ne i64 %t959, 0
    %t969 = icmp ne i64 %t966, 0
    %t970 = or i1 %t968, %t969
    %t967 = zext i1 %t970 to i64
    %t971 = load i64, i64* %c
    %t972 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.55, i64 0, i64 0
    %t973 = ptrtoint i8* %t972 to i64
    %t974 = call i64 @freak_llvm_word_eq(i64 %t971, i64 %t973)
    %t976 = icmp ne i64 %t967, 0
    %t977 = icmp ne i64 %t974, 0
    %t978 = or i1 %t976, %t977
    %t975 = zext i1 %t978 to i64
    %t979 = load i64, i64* %c
    %t980 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.56, i64 0, i64 0
    %t981 = ptrtoint i8* %t980 to i64
    %t982 = call i64 @freak_llvm_word_eq(i64 %t979, i64 %t981)
    %t984 = icmp ne i64 %t975, 0
    %t985 = icmp ne i64 %t982, 0
    %t986 = or i1 %t984, %t985
    %t983 = zext i1 %t986 to i64
    %t990 = icmp ne i64 %t983, 0
    br i1 %t990, label %if.then.987, label %if.end.989
if.then.987:
    ret i64 1
    br label %if.end.989
if.end.989:
    %t991 = load i64, i64* %c
    %t992 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.57, i64 0, i64 0
    %t993 = ptrtoint i8* %t992 to i64
    %t994 = call i64 @freak_llvm_word_eq(i64 %t991, i64 %t993)
    %t995 = load i64, i64* %c
    %t996 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.58, i64 0, i64 0
    %t997 = ptrtoint i8* %t996 to i64
    %t998 = call i64 @freak_llvm_word_eq(i64 %t995, i64 %t997)
    %t1000 = icmp ne i64 %t994, 0
    %t1001 = icmp ne i64 %t998, 0
    %t1002 = or i1 %t1000, %t1001
    %t999 = zext i1 %t1002 to i64
    %t1003 = load i64, i64* %c
    %t1004 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.59, i64 0, i64 0
    %t1005 = ptrtoint i8* %t1004 to i64
    %t1006 = call i64 @freak_llvm_word_eq(i64 %t1003, i64 %t1005)
    %t1008 = icmp ne i64 %t999, 0
    %t1009 = icmp ne i64 %t1006, 0
    %t1010 = or i1 %t1008, %t1009
    %t1007 = zext i1 %t1010 to i64
    %t1011 = load i64, i64* %c
    %t1012 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.60, i64 0, i64 0
    %t1013 = ptrtoint i8* %t1012 to i64
    %t1014 = call i64 @freak_llvm_word_eq(i64 %t1011, i64 %t1013)
    %t1016 = icmp ne i64 %t1007, 0
    %t1017 = icmp ne i64 %t1014, 0
    %t1018 = or i1 %t1016, %t1017
    %t1015 = zext i1 %t1018 to i64
    %t1019 = load i64, i64* %c
    %t1020 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.61, i64 0, i64 0
    %t1021 = ptrtoint i8* %t1020 to i64
    %t1022 = call i64 @freak_llvm_word_eq(i64 %t1019, i64 %t1021)
    %t1024 = icmp ne i64 %t1015, 0
    %t1025 = icmp ne i64 %t1022, 0
    %t1026 = or i1 %t1024, %t1025
    %t1023 = zext i1 %t1026 to i64
    %t1030 = icmp ne i64 %t1023, 0
    br i1 %t1030, label %if.then.1027, label %if.end.1029
if.then.1027:
    ret i64 1
    br label %if.end.1029
if.end.1029:
    %t1031 = load i64, i64* %c
    %t1032 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.62, i64 0, i64 0
    %t1033 = ptrtoint i8* %t1032 to i64
    %t1034 = call i64 @freak_llvm_word_eq(i64 %t1031, i64 %t1033)
    %t1035 = load i64, i64* %c
    %t1036 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.63, i64 0, i64 0
    %t1037 = ptrtoint i8* %t1036 to i64
    %t1038 = call i64 @freak_llvm_word_eq(i64 %t1035, i64 %t1037)
    %t1040 = icmp ne i64 %t1034, 0
    %t1041 = icmp ne i64 %t1038, 0
    %t1042 = or i1 %t1040, %t1041
    %t1039 = zext i1 %t1042 to i64
    %t1043 = load i64, i64* %c
    %t1044 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.64, i64 0, i64 0
    %t1045 = ptrtoint i8* %t1044 to i64
    %t1046 = call i64 @freak_llvm_word_eq(i64 %t1043, i64 %t1045)
    %t1048 = icmp ne i64 %t1039, 0
    %t1049 = icmp ne i64 %t1046, 0
    %t1050 = or i1 %t1048, %t1049
    %t1047 = zext i1 %t1050 to i64
    %t1051 = load i64, i64* %c
    %t1052 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.65, i64 0, i64 0
    %t1053 = ptrtoint i8* %t1052 to i64
    %t1054 = call i64 @freak_llvm_word_eq(i64 %t1051, i64 %t1053)
    %t1056 = icmp ne i64 %t1047, 0
    %t1057 = icmp ne i64 %t1054, 0
    %t1058 = or i1 %t1056, %t1057
    %t1055 = zext i1 %t1058 to i64
    %t1059 = load i64, i64* %c
    %t1060 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.66, i64 0, i64 0
    %t1061 = ptrtoint i8* %t1060 to i64
    %t1062 = call i64 @freak_llvm_word_eq(i64 %t1059, i64 %t1061)
    %t1064 = icmp ne i64 %t1055, 0
    %t1065 = icmp ne i64 %t1062, 0
    %t1066 = or i1 %t1064, %t1065
    %t1063 = zext i1 %t1066 to i64
    %t1070 = icmp ne i64 %t1063, 0
    br i1 %t1070, label %if.then.1067, label %if.end.1069
if.then.1067:
    ret i64 1
    br label %if.end.1069
if.end.1069:
    %t1071 = load i64, i64* %c
    %t1072 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.67, i64 0, i64 0
    %t1073 = ptrtoint i8* %t1072 to i64
    %t1074 = call i64 @freak_llvm_word_eq(i64 %t1071, i64 %t1073)
    %t1075 = load i64, i64* %c
    %t1076 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.68, i64 0, i64 0
    %t1077 = ptrtoint i8* %t1076 to i64
    %t1078 = call i64 @freak_llvm_word_eq(i64 %t1075, i64 %t1077)
    %t1080 = icmp ne i64 %t1074, 0
    %t1081 = icmp ne i64 %t1078, 0
    %t1082 = or i1 %t1080, %t1081
    %t1079 = zext i1 %t1082 to i64
    %t1083 = load i64, i64* %c
    %t1084 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.69, i64 0, i64 0
    %t1085 = ptrtoint i8* %t1084 to i64
    %t1086 = call i64 @freak_llvm_word_eq(i64 %t1083, i64 %t1085)
    %t1088 = icmp ne i64 %t1079, 0
    %t1089 = icmp ne i64 %t1086, 0
    %t1090 = or i1 %t1088, %t1089
    %t1087 = zext i1 %t1090 to i64
    %t1091 = load i64, i64* %c
    %t1092 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.70, i64 0, i64 0
    %t1093 = ptrtoint i8* %t1092 to i64
    %t1094 = call i64 @freak_llvm_word_eq(i64 %t1091, i64 %t1093)
    %t1096 = icmp ne i64 %t1087, 0
    %t1097 = icmp ne i64 %t1094, 0
    %t1098 = or i1 %t1096, %t1097
    %t1095 = zext i1 %t1098 to i64
    %t1099 = load i64, i64* %c
    %t1100 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.71, i64 0, i64 0
    %t1101 = ptrtoint i8* %t1100 to i64
    %t1102 = call i64 @freak_llvm_word_eq(i64 %t1099, i64 %t1101)
    %t1104 = icmp ne i64 %t1095, 0
    %t1105 = icmp ne i64 %t1102, 0
    %t1106 = or i1 %t1104, %t1105
    %t1103 = zext i1 %t1106 to i64
    %t1110 = icmp ne i64 %t1103, 0
    br i1 %t1110, label %if.then.1107, label %if.end.1109
if.then.1107:
    ret i64 1
    br label %if.end.1109
if.end.1109:
    %t1111 = load i64, i64* %c
    %t1112 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.72, i64 0, i64 0
    %t1113 = ptrtoint i8* %t1112 to i64
    %t1114 = call i64 @freak_llvm_word_eq(i64 %t1111, i64 %t1113)
    %t1115 = load i64, i64* %c
    %t1116 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.73, i64 0, i64 0
    %t1117 = ptrtoint i8* %t1116 to i64
    %t1118 = call i64 @freak_llvm_word_eq(i64 %t1115, i64 %t1117)
    %t1120 = icmp ne i64 %t1114, 0
    %t1121 = icmp ne i64 %t1118, 0
    %t1122 = or i1 %t1120, %t1121
    %t1119 = zext i1 %t1122 to i64
    %t1123 = load i64, i64* %c
    %t1124 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.74, i64 0, i64 0
    %t1125 = ptrtoint i8* %t1124 to i64
    %t1126 = call i64 @freak_llvm_word_eq(i64 %t1123, i64 %t1125)
    %t1128 = icmp ne i64 %t1119, 0
    %t1129 = icmp ne i64 %t1126, 0
    %t1130 = or i1 %t1128, %t1129
    %t1127 = zext i1 %t1130 to i64
    %t1131 = load i64, i64* %c
    %t1132 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.75, i64 0, i64 0
    %t1133 = ptrtoint i8* %t1132 to i64
    %t1134 = call i64 @freak_llvm_word_eq(i64 %t1131, i64 %t1133)
    %t1136 = icmp ne i64 %t1127, 0
    %t1137 = icmp ne i64 %t1134, 0
    %t1138 = or i1 %t1136, %t1137
    %t1135 = zext i1 %t1138 to i64
    %t1139 = load i64, i64* %c
    %t1140 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.76, i64 0, i64 0
    %t1141 = ptrtoint i8* %t1140 to i64
    %t1142 = call i64 @freak_llvm_word_eq(i64 %t1139, i64 %t1141)
    %t1144 = icmp ne i64 %t1135, 0
    %t1145 = icmp ne i64 %t1142, 0
    %t1146 = or i1 %t1144, %t1145
    %t1143 = zext i1 %t1146 to i64
    %t1150 = icmp ne i64 %t1143, 0
    br i1 %t1150, label %if.then.1147, label %if.end.1149
if.then.1147:
    ret i64 1
    br label %if.end.1149
if.end.1149:
    %t1151 = load i64, i64* %c
    %t1152 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.77, i64 0, i64 0
    %t1153 = ptrtoint i8* %t1152 to i64
    %t1154 = call i64 @freak_llvm_word_eq(i64 %t1151, i64 %t1153)
    %t1155 = load i64, i64* %c
    %t1156 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.78, i64 0, i64 0
    %t1157 = ptrtoint i8* %t1156 to i64
    %t1158 = call i64 @freak_llvm_word_eq(i64 %t1155, i64 %t1157)
    %t1160 = icmp ne i64 %t1154, 0
    %t1161 = icmp ne i64 %t1158, 0
    %t1162 = or i1 %t1160, %t1161
    %t1159 = zext i1 %t1162 to i64
    %t1163 = load i64, i64* %c
    %t1164 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.79, i64 0, i64 0
    %t1165 = ptrtoint i8* %t1164 to i64
    %t1166 = call i64 @freak_llvm_word_eq(i64 %t1163, i64 %t1165)
    %t1168 = icmp ne i64 %t1159, 0
    %t1169 = icmp ne i64 %t1166, 0
    %t1170 = or i1 %t1168, %t1169
    %t1167 = zext i1 %t1170 to i64
    %t1171 = load i64, i64* %c
    %t1172 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.80, i64 0, i64 0
    %t1173 = ptrtoint i8* %t1172 to i64
    %t1174 = call i64 @freak_llvm_word_eq(i64 %t1171, i64 %t1173)
    %t1176 = icmp ne i64 %t1167, 0
    %t1177 = icmp ne i64 %t1174, 0
    %t1178 = or i1 %t1176, %t1177
    %t1175 = zext i1 %t1178 to i64
    %t1179 = load i64, i64* %c
    %t1180 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.81, i64 0, i64 0
    %t1181 = ptrtoint i8* %t1180 to i64
    %t1182 = call i64 @freak_llvm_word_eq(i64 %t1179, i64 %t1181)
    %t1184 = icmp ne i64 %t1175, 0
    %t1185 = icmp ne i64 %t1182, 0
    %t1186 = or i1 %t1184, %t1185
    %t1183 = zext i1 %t1186 to i64
    %t1187 = load i64, i64* %c
    %t1188 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.82, i64 0, i64 0
    %t1189 = ptrtoint i8* %t1188 to i64
    %t1190 = call i64 @freak_llvm_word_eq(i64 %t1187, i64 %t1189)
    %t1192 = icmp ne i64 %t1183, 0
    %t1193 = icmp ne i64 %t1190, 0
    %t1194 = or i1 %t1192, %t1193
    %t1191 = zext i1 %t1194 to i64
    %t1198 = icmp ne i64 %t1191, 0
    br i1 %t1198, label %if.then.1195, label %if.end.1197
if.then.1195:
    ret i64 1
    br label %if.end.1197
if.end.1197:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_whitespace(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1199 = load i64, i64* %c
    %t1200 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.83, i64 0, i64 0
    %t1201 = ptrtoint i8* %t1200 to i64
    %t1202 = call i64 @freak_llvm_word_eq(i64 %t1199, i64 %t1201)
    %t1206 = icmp ne i64 %t1202, 0
    br i1 %t1206, label %if.then.1203, label %if.end.1205
if.then.1203:
    ret i64 1
    br label %if.end.1205
if.end.1205:
    %t1207 = load i64, i64* %c
    %t1208 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.84, i64 0, i64 0
    %t1209 = ptrtoint i8* %t1208 to i64
    %t1210 = call i64 @freak_llvm_word_eq(i64 %t1207, i64 %t1209)
    %t1214 = icmp ne i64 %t1210, 0
    br i1 %t1214, label %if.then.1211, label %if.end.1213
if.then.1211:
    ret i64 1
    br label %if.end.1213
if.end.1213:
    %t1215 = load i64, i64* %c
    %t1216 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.85, i64 0, i64 0
    %t1217 = ptrtoint i8* %t1216 to i64
    %t1218 = call i64 @freak_llvm_word_eq(i64 %t1215, i64 %t1217)
    %t1222 = icmp ne i64 %t1218, 0
    br i1 %t1222, label %if.then.1219, label %if.end.1221
if.then.1219:
    ret i64 1
    br label %if.end.1221
if.end.1221:
    %t1223 = load i64, i64* %c
    %t1224 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.86, i64 0, i64 0
    %t1225 = ptrtoint i8* %t1224 to i64
    %t1226 = call i64 @freak_llvm_word_eq(i64 %t1223, i64 %t1225)
    %t1230 = icmp ne i64 %t1226, 0
    br i1 %t1230, label %if.then.1227, label %if.end.1229
if.then.1227:
    ret i64 1
    br label %if.end.1229
if.end.1229:
    ret i64 0
    ret i64 0
}

define i64 @freak_string_starts_with(i64 %arg_s, i64 %arg_prefix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %prefix = alloca i64
    store i64 %arg_prefix, i64* %prefix
    %t1231 = load i64, i64* %s
    %t1232 = call i64 @freak_llvm_word_length(i64 %t1231)
    %slen_v1233 = alloca i64
    store i64 %t1232, i64* %slen_v1233
    %t1234 = load i64, i64* %prefix
    %t1235 = call i64 @freak_llvm_word_length(i64 %t1234)
    %plen_v1236 = alloca i64
    store i64 %t1235, i64* %plen_v1236
    %t1237 = load i64, i64* %plen_v1236
    %t1238 = load i64, i64* %slen_v1233
    %t1240 = icmp sgt i64 %t1237, %t1238
    %t1239 = zext i1 %t1240 to i64
    %t1244 = icmp ne i64 %t1239, 0
    br i1 %t1244, label %if.then.1241, label %if.end.1243
if.then.1241:
    ret i64 0
    br label %if.end.1243
if.end.1243:
    %si_v1245 = alloca i64
    store i64 0, i64* %si_v1245
    %t1251 = load i64, i64* %plen_v1236
    %rep.1250 = alloca i64
    store i64 0, i64* %rep.1250
    br label %loop.cond.1246
loop.cond.1246:
    %t1252 = load i64, i64* %rep.1250
    %t1253 = icmp slt i64 %t1252, %t1251
    br i1 %t1253, label %loop.body.1247, label %loop.end.1248
loop.body.1247:
    %t1254 = load i64, i64* %s
    %t1256 = load i64, i64* %si_v1245
    %t1255 = call i64 @freak_llvm_word_char_at(i64 %t1254, i64 %t1256)
    %t1257 = load i64, i64* %prefix
    %t1259 = load i64, i64* %si_v1245
    %t1258 = call i64 @freak_llvm_word_char_at(i64 %t1257, i64 %t1259)
    %t1260 = call i64 @freak_llvm_word_neq(i64 %t1255, i64 %t1258)
    %t1264 = icmp ne i64 %t1260, 0
    br i1 %t1264, label %if.then.1261, label %if.end.1263
if.then.1261:
    ret i64 0
    br label %if.end.1263
if.end.1263:
    %t1265 = load i64, i64* %si_v1245
    %t1266 = add i64 %t1265, 1
    store i64 %t1266, i64* %si_v1245
    br label %loop.inc.1249
loop.inc.1249:
    %t1267 = load i64, i64* %rep.1250
    %t1268 = add i64 %t1267, 1
    store i64 %t1268, i64* %rep.1250
    br label %loop.cond.1246
loop.end.1248:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_ends_with(i64 %arg_s, i64 %arg_suffix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %suffix = alloca i64
    store i64 %arg_suffix, i64* %suffix
    %t1269 = load i64, i64* %s
    %t1270 = call i64 @freak_llvm_word_length(i64 %t1269)
    %slen_v1271 = alloca i64
    store i64 %t1270, i64* %slen_v1271
    %t1272 = load i64, i64* %suffix
    %t1273 = call i64 @freak_llvm_word_length(i64 %t1272)
    %xlen_v1274 = alloca i64
    store i64 %t1273, i64* %xlen_v1274
    %t1275 = load i64, i64* %xlen_v1274
    %t1276 = load i64, i64* %slen_v1271
    %t1278 = icmp sgt i64 %t1275, %t1276
    %t1277 = zext i1 %t1278 to i64
    %t1282 = icmp ne i64 %t1277, 0
    br i1 %t1282, label %if.then.1279, label %if.end.1281
if.then.1279:
    ret i64 0
    br label %if.end.1281
if.end.1281:
    %t1283 = load i64, i64* %slen_v1271
    %t1284 = load i64, i64* %xlen_v1274
    %t1285 = sub i64 %t1283, %t1284
    %offset_v1286 = alloca i64
    store i64 %t1285, i64* %offset_v1286
    %ei_v1287 = alloca i64
    store i64 0, i64* %ei_v1287
    %t1293 = load i64, i64* %xlen_v1274
    %rep.1292 = alloca i64
    store i64 0, i64* %rep.1292
    br label %loop.cond.1288
loop.cond.1288:
    %t1294 = load i64, i64* %rep.1292
    %t1295 = icmp slt i64 %t1294, %t1293
    br i1 %t1295, label %loop.body.1289, label %loop.end.1290
loop.body.1289:
    %t1296 = load i64, i64* %s
    %t1298 = load i64, i64* %offset_v1286
    %t1299 = load i64, i64* %ei_v1287
    %t1300 = add i64 %t1298, %t1299
    %t1297 = call i64 @freak_llvm_word_char_at(i64 %t1296, i64 %t1300)
    %t1301 = load i64, i64* %suffix
    %t1303 = load i64, i64* %ei_v1287
    %t1302 = call i64 @freak_llvm_word_char_at(i64 %t1301, i64 %t1303)
    %t1304 = call i64 @freak_llvm_word_neq(i64 %t1297, i64 %t1302)
    %t1308 = icmp ne i64 %t1304, 0
    br i1 %t1308, label %if.then.1305, label %if.end.1307
if.then.1305:
    ret i64 0
    br label %if.end.1307
if.end.1307:
    %t1309 = load i64, i64* %ei_v1287
    %t1310 = add i64 %t1309, 1
    store i64 %t1310, i64* %ei_v1287
    br label %loop.inc.1291
loop.inc.1291:
    %t1311 = load i64, i64* %rep.1292
    %t1312 = add i64 %t1311, 1
    store i64 %t1312, i64* %rep.1292
    br label %loop.cond.1288
loop.end.1290:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_contains(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1313 = load i64, i64* %haystack
    %t1314 = load i64, i64* %needle
    %t1315 = call i64 @freak_string_count(i64 %t1313, i64 %t1314)
    %t1317 = icmp sgt i64 %t1315, 0
    %t1316 = zext i1 %t1317 to i64
    ret i64 %t1316
    ret i64 0
}

define i64 @freak_string_trim(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1318 = load i64, i64* %s
    %t1319 = call i64 @freak_llvm_word_length(i64 %t1318)
    %slen_v1320 = alloca i64
    store i64 %t1319, i64* %slen_v1320
    %t1321 = load i64, i64* %slen_v1320
    %t1323 = icmp eq i64 %t1321, 0
    %t1322 = zext i1 %t1323 to i64
    %t1327 = icmp ne i64 %t1322, 0
    br i1 %t1327, label %if.then.1324, label %if.end.1326
if.then.1324:
    %t1328 = load i64, i64* %s
    ret i64 %t1328
    br label %if.end.1326
if.end.1326:
    %tstart_v1329 = alloca i64
    store i64 0, i64* %tstart_v1329
    br label %loop.cond.1330
loop.cond.1330:
    %t1333 = load i64, i64* %tstart_v1329
    %t1334 = load i64, i64* %slen_v1320
    %t1336 = icmp sge i64 %t1333, %t1334
    %t1335 = zext i1 %t1336 to i64
    %t1337 = icmp eq i64 %t1335, 0
    br i1 %t1337, label %loop.body.1331, label %loop.end.1332
loop.body.1331:
    %t1338 = load i64, i64* %s
    %t1340 = load i64, i64* %tstart_v1329
    %t1339 = call i64 @freak_llvm_word_char_at(i64 %t1338, i64 %t1340)
    %t1341 = call i64 @freak_is_whitespace(i64 %t1339)
    %t1343 = icmp eq i64 %t1341, 0
    %t1342 = zext i1 %t1343 to i64
    %t1347 = icmp ne i64 %t1342, 0
    br i1 %t1347, label %if.then.1344, label %if.end.1346
if.then.1344:
    %t1348 = load i64, i64* %s
    %t1349 = load i64, i64* %tstart_v1329
    %t1350 = call i64 @freak_string_trim_end(i64 %t1348, i64 %t1349)
    ret i64 %t1350
    br label %if.end.1346
if.end.1346:
    %t1351 = load i64, i64* %tstart_v1329
    %t1352 = add i64 %t1351, 1
    store i64 %t1352, i64* %tstart_v1329
    br label %loop.cond.1330
loop.end.1332:
    %t1353 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.87, i64 0, i64 0
    %t1354 = ptrtoint i8* %t1353 to i64
    ret i64 %t1354
    ret i64 0
}

define i64 @freak_string_trim_end(i64 %arg_s, i64 %arg_tstart) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %tstart = alloca i64
    store i64 %arg_tstart, i64* %tstart
    %t1355 = load i64, i64* %s
    %t1356 = call i64 @freak_llvm_word_length(i64 %t1355)
    %t1357 = sub i64 %t1356, 1
    %tend_v1358 = alloca i64
    store i64 %t1357, i64* %tend_v1358
    br label %loop.cond.1359
loop.cond.1359:
    %t1362 = load i64, i64* %tend_v1358
    %t1363 = load i64, i64* %tstart
    %t1365 = icmp slt i64 %t1362, %t1363
    %t1364 = zext i1 %t1365 to i64
    %t1366 = icmp eq i64 %t1364, 0
    br i1 %t1366, label %loop.body.1360, label %loop.end.1361
loop.body.1360:
    %t1367 = load i64, i64* %s
    %t1369 = load i64, i64* %tend_v1358
    %t1368 = call i64 @freak_llvm_word_char_at(i64 %t1367, i64 %t1369)
    %t1370 = call i64 @freak_is_whitespace(i64 %t1368)
    %t1372 = icmp eq i64 %t1370, 0
    %t1371 = zext i1 %t1372 to i64
    %t1376 = icmp ne i64 %t1371, 0
    br i1 %t1376, label %if.then.1373, label %if.end.1375
if.then.1373:
    %t1377 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.88, i64 0, i64 0
    %t1378 = ptrtoint i8* %t1377 to i64
    %tout_v1379 = alloca i64
    store i64 %t1378, i64* %tout_v1379
    %t1380 = load i64, i64* %tstart
    %ti_v1381 = alloca i64
    store i64 %t1380, i64* %ti_v1381
    br label %loop.cond.1382
loop.cond.1382:
    %t1385 = load i64, i64* %ti_v1381
    %t1386 = load i64, i64* %tend_v1358
    %t1388 = icmp sgt i64 %t1385, %t1386
    %t1387 = zext i1 %t1388 to i64
    %t1389 = icmp eq i64 %t1387, 0
    br i1 %t1389, label %loop.body.1383, label %loop.end.1384
loop.body.1383:
    %t1390 = load i64, i64* %tout_v1379
    %t1391 = load i64, i64* %s
    %t1393 = load i64, i64* %ti_v1381
    %t1392 = call i64 @freak_llvm_word_char_at(i64 %t1391, i64 %t1393)
    %t1394 = call i64 @freak_llvm_word_concat(i64 %t1390, i64 %t1392)
    store i64 %t1394, i64* %tout_v1379
    %t1395 = load i64, i64* %ti_v1381
    %t1396 = add i64 %t1395, 1
    store i64 %t1396, i64* %ti_v1381
    br label %loop.cond.1382
loop.end.1384:
    %t1397 = load i64, i64* %tout_v1379
    ret i64 %t1397
    br label %if.end.1375
if.end.1375:
    %t1398 = load i64, i64* %tend_v1358
    %t1399 = sub i64 %t1398, 1
    store i64 %t1399, i64* %tend_v1358
    br label %loop.cond.1359
loop.end.1361:
    %t1400 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.89, i64 0, i64 0
    %t1401 = ptrtoint i8* %t1400 to i64
    ret i64 %t1401
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
    %t1402 = load i64, i64* %s
    %t1403 = call i64 @freak_llvm_word_length(i64 %t1402)
    %slen_v1404 = alloca i64
    store i64 %t1403, i64* %slen_v1404
    %t1405 = load i64, i64* %old_str
    %t1406 = call i64 @freak_llvm_word_length(i64 %t1405)
    %olen_v1407 = alloca i64
    store i64 %t1406, i64* %olen_v1407
    %t1408 = load i64, i64* %olen_v1407
    %t1410 = icmp eq i64 %t1408, 0
    %t1409 = zext i1 %t1410 to i64
    %t1414 = icmp ne i64 %t1409, 0
    br i1 %t1414, label %if.then.1411, label %if.end.1413
if.then.1411:
    %t1415 = load i64, i64* %s
    ret i64 %t1415
    br label %if.end.1413
if.end.1413:
    %t1416 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.90, i64 0, i64 0
    %t1417 = ptrtoint i8* %t1416 to i64
    %rout_v1418 = alloca i64
    store i64 %t1417, i64* %rout_v1418
    %ri_v1419 = alloca i64
    store i64 0, i64* %ri_v1419
    br label %loop.cond.1420
loop.cond.1420:
    %t1423 = load i64, i64* %ri_v1419
    %t1424 = load i64, i64* %slen_v1404
    %t1426 = icmp sge i64 %t1423, %t1424
    %t1425 = zext i1 %t1426 to i64
    %t1427 = icmp eq i64 %t1425, 0
    br i1 %t1427, label %loop.body.1421, label %loop.end.1422
loop.body.1421:
    %rmatch_v1428 = alloca i64
    store i64 1, i64* %rmatch_v1428
    %t1429 = load i64, i64* %ri_v1419
    %t1430 = load i64, i64* %olen_v1407
    %t1431 = add i64 %t1429, %t1430
    %t1432 = load i64, i64* %slen_v1404
    %t1434 = icmp sle i64 %t1431, %t1432
    %t1433 = zext i1 %t1434 to i64
    %t1438 = icmp ne i64 %t1433, 0
    br i1 %t1438, label %if.then.1435, label %if.else.1436
if.then.1435:
    %rj_v1439 = alloca i64
    store i64 0, i64* %rj_v1439
    %t1445 = load i64, i64* %olen_v1407
    %rep.1444 = alloca i64
    store i64 0, i64* %rep.1444
    br label %loop.cond.1440
loop.cond.1440:
    %t1446 = load i64, i64* %rep.1444
    %t1447 = icmp slt i64 %t1446, %t1445
    br i1 %t1447, label %loop.body.1441, label %loop.end.1442
loop.body.1441:
    %t1448 = load i64, i64* %rmatch_v1428
    %t1452 = icmp ne i64 %t1448, 0
    br i1 %t1452, label %if.then.1449, label %if.end.1451
if.then.1449:
    %t1453 = load i64, i64* %s
    %t1455 = load i64, i64* %ri_v1419
    %t1456 = load i64, i64* %rj_v1439
    %t1457 = add i64 %t1455, %t1456
    %t1454 = call i64 @freak_llvm_word_char_at(i64 %t1453, i64 %t1457)
    %t1458 = load i64, i64* %old_str
    %t1460 = load i64, i64* %rj_v1439
    %t1459 = call i64 @freak_llvm_word_char_at(i64 %t1458, i64 %t1460)
    %t1461 = call i64 @freak_llvm_word_neq(i64 %t1454, i64 %t1459)
    %t1465 = icmp ne i64 %t1461, 0
    br i1 %t1465, label %if.then.1462, label %if.end.1464
if.then.1462:
    store i64 0, i64* %rmatch_v1428
    br label %if.end.1464
if.end.1464:
    br label %if.end.1451
if.end.1451:
    %t1466 = load i64, i64* %rj_v1439
    %t1467 = add i64 %t1466, 1
    store i64 %t1467, i64* %rj_v1439
    br label %loop.inc.1443
loop.inc.1443:
    %t1468 = load i64, i64* %rep.1444
    %t1469 = add i64 %t1468, 1
    store i64 %t1469, i64* %rep.1444
    br label %loop.cond.1440
loop.end.1442:
    br label %if.end.1437
if.else.1436:
    store i64 0, i64* %rmatch_v1428
    br label %if.end.1437
if.end.1437:
    %t1470 = load i64, i64* %rmatch_v1428
    %t1474 = icmp ne i64 %t1470, 0
    br i1 %t1474, label %if.then.1471, label %if.else.1472
if.then.1471:
    %t1475 = load i64, i64* %rout_v1418
    %t1476 = load i64, i64* %new_str
    %t1477 = call i64 @freak_llvm_word_concat(i64 %t1475, i64 %t1476)
    store i64 %t1477, i64* %rout_v1418
    %t1478 = load i64, i64* %olen_v1407
    %t1479 = load i64, i64* %ri_v1419
    %t1480 = add i64 %t1479, %t1478
    store i64 %t1480, i64* %ri_v1419
    br label %if.end.1473
if.else.1472:
    %t1481 = load i64, i64* %rout_v1418
    %t1482 = load i64, i64* %s
    %t1484 = load i64, i64* %ri_v1419
    %t1483 = call i64 @freak_llvm_word_char_at(i64 %t1482, i64 %t1484)
    %t1485 = call i64 @freak_llvm_word_concat(i64 %t1481, i64 %t1483)
    store i64 %t1485, i64* %rout_v1418
    %t1486 = load i64, i64* %ri_v1419
    %t1487 = add i64 %t1486, 1
    store i64 %t1487, i64* %ri_v1419
    br label %if.end.1473
if.end.1473:
    br label %loop.cond.1420
loop.end.1422:
    %t1488 = load i64, i64* %rout_v1418
    ret i64 %t1488
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
    %t1489 = load i64, i64* %s
    %t1490 = call i64 @freak_llvm_word_length(i64 %t1489)
    %slen_v1491 = alloca i64
    store i64 %t1490, i64* %slen_v1491
    %t1492 = load i64, i64* %start_idx
    %ss_v1493 = alloca i64
    store i64 %t1492, i64* %ss_v1493
    %t1494 = load i64, i64* %end_idx
    %se_v1495 = alloca i64
    store i64 %t1494, i64* %se_v1495
    %t1496 = load i64, i64* %ss_v1493
    %t1498 = icmp slt i64 %t1496, 0
    %t1497 = zext i1 %t1498 to i64
    %t1502 = icmp ne i64 %t1497, 0
    br i1 %t1502, label %if.then.1499, label %if.end.1501
if.then.1499:
    store i64 0, i64* %ss_v1493
    br label %if.end.1501
if.end.1501:
    %t1503 = load i64, i64* %se_v1495
    %t1504 = load i64, i64* %slen_v1491
    %t1506 = icmp sgt i64 %t1503, %t1504
    %t1505 = zext i1 %t1506 to i64
    %t1510 = icmp ne i64 %t1505, 0
    br i1 %t1510, label %if.then.1507, label %if.end.1509
if.then.1507:
    %t1511 = load i64, i64* %slen_v1491
    store i64 %t1511, i64* %se_v1495
    br label %if.end.1509
if.end.1509:
    %t1512 = load i64, i64* %ss_v1493
    %t1513 = load i64, i64* %se_v1495
    %t1515 = icmp sge i64 %t1512, %t1513
    %t1514 = zext i1 %t1515 to i64
    %t1519 = icmp ne i64 %t1514, 0
    br i1 %t1519, label %if.then.1516, label %if.end.1518
if.then.1516:
    %t1520 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.91, i64 0, i64 0
    %t1521 = ptrtoint i8* %t1520 to i64
    ret i64 %t1521
    br label %if.end.1518
if.end.1518:
    %t1522 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.92, i64 0, i64 0
    %t1523 = ptrtoint i8* %t1522 to i64
    %sub_out_v1524 = alloca i64
    store i64 %t1523, i64* %sub_out_v1524
    %t1525 = load i64, i64* %ss_v1493
    %si_v1526 = alloca i64
    store i64 %t1525, i64* %si_v1526
    br label %loop.cond.1527
loop.cond.1527:
    %t1530 = load i64, i64* %si_v1526
    %t1531 = load i64, i64* %se_v1495
    %t1533 = icmp sge i64 %t1530, %t1531
    %t1532 = zext i1 %t1533 to i64
    %t1534 = icmp eq i64 %t1532, 0
    br i1 %t1534, label %loop.body.1528, label %loop.end.1529
loop.body.1528:
    %t1535 = load i64, i64* %sub_out_v1524
    %t1536 = load i64, i64* %s
    %t1538 = load i64, i64* %si_v1526
    %t1537 = call i64 @freak_llvm_word_char_at(i64 %t1536, i64 %t1538)
    %t1539 = call i64 @freak_llvm_word_concat(i64 %t1535, i64 %t1537)
    store i64 %t1539, i64* %sub_out_v1524
    %t1540 = load i64, i64* %si_v1526
    %t1541 = add i64 %t1540, 1
    store i64 %t1541, i64* %si_v1526
    br label %loop.cond.1527
loop.end.1529:
    %t1542 = load i64, i64* %sub_out_v1524
    ret i64 %t1542
    ret i64 0
}

define i64 @freak_string_index_of(i64 %arg_s, i64 %arg_needle) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1543 = load i64, i64* %s
    %t1544 = call i64 @freak_llvm_word_length(i64 %t1543)
    %slen_v1545 = alloca i64
    store i64 %t1544, i64* %slen_v1545
    %t1546 = load i64, i64* %needle
    %t1547 = call i64 @freak_llvm_word_length(i64 %t1546)
    %nlen_v1548 = alloca i64
    store i64 %t1547, i64* %nlen_v1548
    %t1549 = load i64, i64* %nlen_v1548
    %t1551 = icmp eq i64 %t1549, 0
    %t1550 = zext i1 %t1551 to i64
    %t1555 = icmp ne i64 %t1550, 0
    br i1 %t1555, label %if.then.1552, label %if.end.1554
if.then.1552:
    ret i64 0
    br label %if.end.1554
if.end.1554:
    %t1556 = load i64, i64* %nlen_v1548
    %t1557 = load i64, i64* %slen_v1545
    %t1559 = icmp sgt i64 %t1556, %t1557
    %t1558 = zext i1 %t1559 to i64
    %t1563 = icmp ne i64 %t1558, 0
    br i1 %t1563, label %if.then.1560, label %if.end.1562
if.then.1560:
    %t1564 = sub i64 0, 1
    ret i64 %t1564
    br label %if.end.1562
if.end.1562:
    %t1565 = load i64, i64* %slen_v1545
    %t1566 = load i64, i64* %nlen_v1548
    %t1567 = sub i64 %t1565, %t1566
    %t1568 = add i64 %t1567, 1
    %limit_v1569 = alloca i64
    store i64 %t1568, i64* %limit_v1569
    %fi_v1570 = alloca i64
    store i64 0, i64* %fi_v1570
    %t1576 = load i64, i64* %limit_v1569
    %rep.1575 = alloca i64
    store i64 0, i64* %rep.1575
    br label %loop.cond.1571
loop.cond.1571:
    %t1577 = load i64, i64* %rep.1575
    %t1578 = icmp slt i64 %t1577, %t1576
    br i1 %t1578, label %loop.body.1572, label %loop.end.1573
loop.body.1572:
    %fmatch_v1579 = alloca i64
    store i64 1, i64* %fmatch_v1579
    %fj_v1580 = alloca i64
    store i64 0, i64* %fj_v1580
    %t1586 = load i64, i64* %nlen_v1548
    %rep.1585 = alloca i64
    store i64 0, i64* %rep.1585
    br label %loop.cond.1581
loop.cond.1581:
    %t1587 = load i64, i64* %rep.1585
    %t1588 = icmp slt i64 %t1587, %t1586
    br i1 %t1588, label %loop.body.1582, label %loop.end.1583
loop.body.1582:
    %t1589 = load i64, i64* %fmatch_v1579
    %t1593 = icmp ne i64 %t1589, 0
    br i1 %t1593, label %if.then.1590, label %if.end.1592
if.then.1590:
    %t1594 = load i64, i64* %s
    %t1596 = load i64, i64* %fi_v1570
    %t1597 = load i64, i64* %fj_v1580
    %t1598 = add i64 %t1596, %t1597
    %t1595 = call i64 @freak_llvm_word_char_at(i64 %t1594, i64 %t1598)
    %t1599 = load i64, i64* %needle
    %t1601 = load i64, i64* %fj_v1580
    %t1600 = call i64 @freak_llvm_word_char_at(i64 %t1599, i64 %t1601)
    %t1602 = call i64 @freak_llvm_word_neq(i64 %t1595, i64 %t1600)
    %t1606 = icmp ne i64 %t1602, 0
    br i1 %t1606, label %if.then.1603, label %if.end.1605
if.then.1603:
    store i64 0, i64* %fmatch_v1579
    br label %if.end.1605
if.end.1605:
    br label %if.end.1592
if.end.1592:
    %t1607 = load i64, i64* %fj_v1580
    %t1608 = add i64 %t1607, 1
    store i64 %t1608, i64* %fj_v1580
    br label %loop.inc.1584
loop.inc.1584:
    %t1609 = load i64, i64* %rep.1585
    %t1610 = add i64 %t1609, 1
    store i64 %t1610, i64* %rep.1585
    br label %loop.cond.1581
loop.end.1583:
    %t1611 = load i64, i64* %fmatch_v1579
    %t1615 = icmp ne i64 %t1611, 0
    br i1 %t1615, label %if.then.1612, label %if.end.1614
if.then.1612:
    %t1616 = load i64, i64* %fi_v1570
    ret i64 %t1616
    br label %if.end.1614
if.end.1614:
    %t1617 = load i64, i64* %fi_v1570
    %t1618 = add i64 %t1617, 1
    store i64 %t1618, i64* %fi_v1570
    br label %loop.inc.1574
loop.inc.1574:
    %t1619 = load i64, i64* %rep.1575
    %t1620 = add i64 %t1619, 1
    store i64 %t1620, i64* %rep.1575
    br label %loop.cond.1571
loop.end.1573:
    %t1621 = sub i64 0, 1
    ret i64 %t1621
    ret i64 0
}

define i64 @freak_int_to_hex(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1622 = load i64, i64* %n
    %t1624 = icmp eq i64 %t1622, 0
    %t1623 = zext i1 %t1624 to i64
    %t1628 = icmp ne i64 %t1623, 0
    br i1 %t1628, label %if.then.1625, label %if.end.1627
if.then.1625:
    %t1629 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.93, i64 0, i64 0
    %t1630 = ptrtoint i8* %t1629 to i64
    ret i64 %t1630
    br label %if.end.1627
if.end.1627:
    %t1631 = getelementptr inbounds [17 x i8], [17 x i8]* @.str.94, i64 0, i64 0
    %t1632 = ptrtoint i8* %t1631 to i64
    %hex_chars_v1633 = alloca i64
    store i64 %t1632, i64* %hex_chars_v1633
    %neg_v1634 = alloca i64
    store i64 0, i64* %neg_v1634
    %t1635 = load i64, i64* %n
    %val_v1636 = alloca i64
    store i64 %t1635, i64* %val_v1636
    %t1637 = load i64, i64* %val_v1636
    %t1639 = icmp slt i64 %t1637, 0
    %t1638 = zext i1 %t1639 to i64
    %t1643 = icmp ne i64 %t1638, 0
    br i1 %t1643, label %if.then.1640, label %if.end.1642
if.then.1640:
    store i64 1, i64* %neg_v1634
    %t1644 = load i64, i64* %val_v1636
    %t1645 = sub i64 0, %t1644
    store i64 %t1645, i64* %val_v1636
    br label %if.end.1642
if.end.1642:
    %t1646 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.95, i64 0, i64 0
    %t1647 = ptrtoint i8* %t1646 to i64
    %hex_out_v1648 = alloca i64
    store i64 %t1647, i64* %hex_out_v1648
    br label %loop.cond.1649
loop.cond.1649:
    %t1652 = load i64, i64* %val_v1636
    %t1654 = icmp sle i64 %t1652, 0
    %t1653 = zext i1 %t1654 to i64
    %t1655 = icmp eq i64 %t1653, 0
    br i1 %t1655, label %loop.body.1650, label %loop.end.1651
loop.body.1650:
    %t1656 = load i64, i64* %val_v1636
    %t1657 = load i64, i64* %val_v1636
    %t1658 = sdiv i64 %t1657, 16
    %t1659 = mul i64 %t1658, 16
    %t1660 = sub i64 %t1656, %t1659
    %rem_v1661 = alloca i64
    store i64 %t1660, i64* %rem_v1661
    %t1662 = load i64, i64* %hex_chars_v1633
    %t1664 = load i64, i64* %rem_v1661
    %t1663 = call i64 @freak_llvm_word_char_at(i64 %t1662, i64 %t1664)
    %t1665 = load i64, i64* %hex_out_v1648
    %t1666 = call i64 @freak_llvm_word_concat(i64 %t1663, i64 %t1665)
    store i64 %t1666, i64* %hex_out_v1648
    %t1667 = load i64, i64* %val_v1636
    %t1668 = sdiv i64 %t1667, 16
    store i64 %t1668, i64* %val_v1636
    br label %loop.cond.1649
loop.end.1651:
    %t1669 = load i64, i64* %neg_v1634
    %t1673 = icmp ne i64 %t1669, 0
    br i1 %t1673, label %if.then.1670, label %if.end.1672
if.then.1670:
    %t1674 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.96, i64 0, i64 0
    %t1675 = ptrtoint i8* %t1674 to i64
    %t1676 = load i64, i64* %hex_out_v1648
    %t1677 = call i64 @freak_llvm_word_concat(i64 %t1675, i64 %t1676)
    store i64 %t1677, i64* %hex_out_v1648
    br label %if.end.1672
if.end.1672:
    %t1678 = load i64, i64* %hex_out_v1648
    ret i64 %t1678
    ret i64 0
}

define i64 @freak_int_to_bin(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1679 = load i64, i64* %n
    %t1681 = icmp eq i64 %t1679, 0
    %t1680 = zext i1 %t1681 to i64
    %t1685 = icmp ne i64 %t1680, 0
    br i1 %t1685, label %if.then.1682, label %if.end.1684
if.then.1682:
    %t1686 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.97, i64 0, i64 0
    %t1687 = ptrtoint i8* %t1686 to i64
    ret i64 %t1687
    br label %if.end.1684
if.end.1684:
    %neg_v1688 = alloca i64
    store i64 0, i64* %neg_v1688
    %t1689 = load i64, i64* %n
    %val_v1690 = alloca i64
    store i64 %t1689, i64* %val_v1690
    %t1691 = load i64, i64* %val_v1690
    %t1693 = icmp slt i64 %t1691, 0
    %t1692 = zext i1 %t1693 to i64
    %t1697 = icmp ne i64 %t1692, 0
    br i1 %t1697, label %if.then.1694, label %if.end.1696
if.then.1694:
    store i64 1, i64* %neg_v1688
    %t1698 = load i64, i64* %val_v1690
    %t1699 = sub i64 0, %t1698
    store i64 %t1699, i64* %val_v1690
    br label %if.end.1696
if.end.1696:
    %t1700 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.98, i64 0, i64 0
    %t1701 = ptrtoint i8* %t1700 to i64
    %bin_out_v1702 = alloca i64
    store i64 %t1701, i64* %bin_out_v1702
    br label %loop.cond.1703
loop.cond.1703:
    %t1706 = load i64, i64* %val_v1690
    %t1708 = icmp sle i64 %t1706, 0
    %t1707 = zext i1 %t1708 to i64
    %t1709 = icmp eq i64 %t1707, 0
    br i1 %t1709, label %loop.body.1704, label %loop.end.1705
loop.body.1704:
    %t1710 = load i64, i64* %val_v1690
    %t1711 = load i64, i64* %val_v1690
    %t1712 = sdiv i64 %t1711, 2
    %t1713 = mul i64 %t1712, 2
    %t1714 = sub i64 %t1710, %t1713
    %rem_v1715 = alloca i64
    store i64 %t1714, i64* %rem_v1715
    %t1716 = load i64, i64* %rem_v1715
    %t1718 = icmp eq i64 %t1716, 1
    %t1717 = zext i1 %t1718 to i64
    %t1722 = icmp ne i64 %t1717, 0
    br i1 %t1722, label %if.then.1719, label %if.else.1720
if.then.1719:
    %t1723 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.99, i64 0, i64 0
    %t1724 = ptrtoint i8* %t1723 to i64
    %t1725 = load i64, i64* %bin_out_v1702
    %t1726 = call i64 @freak_llvm_word_concat(i64 %t1724, i64 %t1725)
    store i64 %t1726, i64* %bin_out_v1702
    br label %if.end.1721
if.else.1720:
    %t1727 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.100, i64 0, i64 0
    %t1728 = ptrtoint i8* %t1727 to i64
    %t1729 = load i64, i64* %bin_out_v1702
    %t1730 = call i64 @freak_llvm_word_concat(i64 %t1728, i64 %t1729)
    store i64 %t1730, i64* %bin_out_v1702
    br label %if.end.1721
if.end.1721:
    %t1731 = load i64, i64* %val_v1690
    %t1732 = sdiv i64 %t1731, 2
    store i64 %t1732, i64* %val_v1690
    br label %loop.cond.1703
loop.end.1705:
    %t1733 = load i64, i64* %neg_v1688
    %t1737 = icmp ne i64 %t1733, 0
    br i1 %t1737, label %if.then.1734, label %if.end.1736
if.then.1734:
    %t1738 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.101, i64 0, i64 0
    %t1739 = ptrtoint i8* %t1738 to i64
    %t1740 = load i64, i64* %bin_out_v1702
    %t1741 = call i64 @freak_llvm_word_concat(i64 %t1739, i64 %t1740)
    store i64 %t1741, i64* %bin_out_v1702
    br label %if.end.1736
if.end.1736:
    %t1742 = load i64, i64* %bin_out_v1702
    ret i64 %t1742
    ret i64 0
}

define i64 @freak_int_to_oct(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1743 = load i64, i64* %n
    %t1745 = icmp eq i64 %t1743, 0
    %t1744 = zext i1 %t1745 to i64
    %t1749 = icmp ne i64 %t1744, 0
    br i1 %t1749, label %if.then.1746, label %if.end.1748
if.then.1746:
    %t1750 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.102, i64 0, i64 0
    %t1751 = ptrtoint i8* %t1750 to i64
    ret i64 %t1751
    br label %if.end.1748
if.end.1748:
    %t1752 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.103, i64 0, i64 0
    %t1753 = ptrtoint i8* %t1752 to i64
    %oct_chars_v1754 = alloca i64
    store i64 %t1753, i64* %oct_chars_v1754
    %neg_v1755 = alloca i64
    store i64 0, i64* %neg_v1755
    %t1756 = load i64, i64* %n
    %val_v1757 = alloca i64
    store i64 %t1756, i64* %val_v1757
    %t1758 = load i64, i64* %val_v1757
    %t1760 = icmp slt i64 %t1758, 0
    %t1759 = zext i1 %t1760 to i64
    %t1764 = icmp ne i64 %t1759, 0
    br i1 %t1764, label %if.then.1761, label %if.end.1763
if.then.1761:
    store i64 1, i64* %neg_v1755
    %t1765 = load i64, i64* %val_v1757
    %t1766 = sub i64 0, %t1765
    store i64 %t1766, i64* %val_v1757
    br label %if.end.1763
if.end.1763:
    %t1767 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.104, i64 0, i64 0
    %t1768 = ptrtoint i8* %t1767 to i64
    %oct_out_v1769 = alloca i64
    store i64 %t1768, i64* %oct_out_v1769
    br label %loop.cond.1770
loop.cond.1770:
    %t1773 = load i64, i64* %val_v1757
    %t1775 = icmp sle i64 %t1773, 0
    %t1774 = zext i1 %t1775 to i64
    %t1776 = icmp eq i64 %t1774, 0
    br i1 %t1776, label %loop.body.1771, label %loop.end.1772
loop.body.1771:
    %t1777 = load i64, i64* %val_v1757
    %t1778 = load i64, i64* %val_v1757
    %t1779 = sdiv i64 %t1778, 8
    %t1780 = mul i64 %t1779, 8
    %t1781 = sub i64 %t1777, %t1780
    %rem_v1782 = alloca i64
    store i64 %t1781, i64* %rem_v1782
    %t1783 = load i64, i64* %oct_chars_v1754
    %t1785 = load i64, i64* %rem_v1782
    %t1784 = call i64 @freak_llvm_word_char_at(i64 %t1783, i64 %t1785)
    %t1786 = load i64, i64* %oct_out_v1769
    %t1787 = call i64 @freak_llvm_word_concat(i64 %t1784, i64 %t1786)
    store i64 %t1787, i64* %oct_out_v1769
    %t1788 = load i64, i64* %val_v1757
    %t1789 = sdiv i64 %t1788, 8
    store i64 %t1789, i64* %val_v1757
    br label %loop.cond.1770
loop.end.1772:
    %t1790 = load i64, i64* %neg_v1755
    %t1794 = icmp ne i64 %t1790, 0
    br i1 %t1794, label %if.then.1791, label %if.end.1793
if.then.1791:
    %t1795 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.105, i64 0, i64 0
    %t1796 = ptrtoint i8* %t1795 to i64
    %t1797 = load i64, i64* %oct_out_v1769
    %t1798 = call i64 @freak_llvm_word_concat(i64 %t1796, i64 %t1797)
    store i64 %t1798, i64* %oct_out_v1769
    br label %if.end.1793
if.end.1793:
    %t1799 = load i64, i64* %oct_out_v1769
    ret i64 %t1799
    ret i64 0
}

define i64 @freak_char_to_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1800 = load i64, i64* %c
    %t1801 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.106, i64 0, i64 0
    %t1802 = ptrtoint i8* %t1801 to i64
    %t1803 = call i64 @freak_llvm_word_eq(i64 %t1800, i64 %t1802)
    %t1807 = icmp ne i64 %t1803, 0
    br i1 %t1807, label %if.then.1804, label %if.end.1806
if.then.1804:
    ret i64 0
    br label %if.end.1806
if.end.1806:
    %t1808 = load i64, i64* %c
    %t1809 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.107, i64 0, i64 0
    %t1810 = ptrtoint i8* %t1809 to i64
    %t1811 = call i64 @freak_llvm_word_eq(i64 %t1808, i64 %t1810)
    %t1815 = icmp ne i64 %t1811, 0
    br i1 %t1815, label %if.then.1812, label %if.end.1814
if.then.1812:
    ret i64 1
    br label %if.end.1814
if.end.1814:
    %t1816 = load i64, i64* %c
    %t1817 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.108, i64 0, i64 0
    %t1818 = ptrtoint i8* %t1817 to i64
    %t1819 = call i64 @freak_llvm_word_eq(i64 %t1816, i64 %t1818)
    %t1823 = icmp ne i64 %t1819, 0
    br i1 %t1823, label %if.then.1820, label %if.end.1822
if.then.1820:
    ret i64 2
    br label %if.end.1822
if.end.1822:
    %t1824 = load i64, i64* %c
    %t1825 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.109, i64 0, i64 0
    %t1826 = ptrtoint i8* %t1825 to i64
    %t1827 = call i64 @freak_llvm_word_eq(i64 %t1824, i64 %t1826)
    %t1831 = icmp ne i64 %t1827, 0
    br i1 %t1831, label %if.then.1828, label %if.end.1830
if.then.1828:
    ret i64 3
    br label %if.end.1830
if.end.1830:
    %t1832 = load i64, i64* %c
    %t1833 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.110, i64 0, i64 0
    %t1834 = ptrtoint i8* %t1833 to i64
    %t1835 = call i64 @freak_llvm_word_eq(i64 %t1832, i64 %t1834)
    %t1839 = icmp ne i64 %t1835, 0
    br i1 %t1839, label %if.then.1836, label %if.end.1838
if.then.1836:
    ret i64 4
    br label %if.end.1838
if.end.1838:
    %t1840 = load i64, i64* %c
    %t1841 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.111, i64 0, i64 0
    %t1842 = ptrtoint i8* %t1841 to i64
    %t1843 = call i64 @freak_llvm_word_eq(i64 %t1840, i64 %t1842)
    %t1847 = icmp ne i64 %t1843, 0
    br i1 %t1847, label %if.then.1844, label %if.end.1846
if.then.1844:
    ret i64 5
    br label %if.end.1846
if.end.1846:
    %t1848 = load i64, i64* %c
    %t1849 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.112, i64 0, i64 0
    %t1850 = ptrtoint i8* %t1849 to i64
    %t1851 = call i64 @freak_llvm_word_eq(i64 %t1848, i64 %t1850)
    %t1855 = icmp ne i64 %t1851, 0
    br i1 %t1855, label %if.then.1852, label %if.end.1854
if.then.1852:
    ret i64 6
    br label %if.end.1854
if.end.1854:
    %t1856 = load i64, i64* %c
    %t1857 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.113, i64 0, i64 0
    %t1858 = ptrtoint i8* %t1857 to i64
    %t1859 = call i64 @freak_llvm_word_eq(i64 %t1856, i64 %t1858)
    %t1863 = icmp ne i64 %t1859, 0
    br i1 %t1863, label %if.then.1860, label %if.end.1862
if.then.1860:
    ret i64 7
    br label %if.end.1862
if.end.1862:
    %t1864 = load i64, i64* %c
    %t1865 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.114, i64 0, i64 0
    %t1866 = ptrtoint i8* %t1865 to i64
    %t1867 = call i64 @freak_llvm_word_eq(i64 %t1864, i64 %t1866)
    %t1871 = icmp ne i64 %t1867, 0
    br i1 %t1871, label %if.then.1868, label %if.end.1870
if.then.1868:
    ret i64 8
    br label %if.end.1870
if.end.1870:
    %t1872 = load i64, i64* %c
    %t1873 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.115, i64 0, i64 0
    %t1874 = ptrtoint i8* %t1873 to i64
    %t1875 = call i64 @freak_llvm_word_eq(i64 %t1872, i64 %t1874)
    %t1879 = icmp ne i64 %t1875, 0
    br i1 %t1879, label %if.then.1876, label %if.end.1878
if.then.1876:
    ret i64 9
    br label %if.end.1878
if.end.1878:
    %t1880 = sub i64 0, 1
    ret i64 %t1880
    ret i64 0
}

define i64 @freak_word_to_int_safe(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1881 = load i64, i64* %s
    %t1882 = call i64 @freak_llvm_word_length(i64 %t1881)
    %slen_v1883 = alloca i64
    store i64 %t1882, i64* %slen_v1883
    %t1884 = load i64, i64* %slen_v1883
    %t1886 = icmp eq i64 %t1884, 0
    %t1885 = zext i1 %t1886 to i64
    %t1890 = icmp ne i64 %t1885, 0
    br i1 %t1890, label %if.then.1887, label %if.end.1889
if.then.1887:
    ret i64 0
    br label %if.end.1889
if.end.1889:
    %neg_v1891 = alloca i64
    store i64 0, i64* %neg_v1891
    %wi_v1892 = alloca i64
    store i64 0, i64* %wi_v1892
    %t1893 = load i64, i64* %s
    %t1894 = call i64 @freak_llvm_word_char_at(i64 %t1893, i64 0)
    %t1895 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.116, i64 0, i64 0
    %t1896 = ptrtoint i8* %t1895 to i64
    %t1897 = call i64 @freak_llvm_word_eq(i64 %t1894, i64 %t1896)
    %t1901 = icmp ne i64 %t1897, 0
    br i1 %t1901, label %if.then.1898, label %if.end.1900
if.then.1898:
    store i64 1, i64* %neg_v1891
    store i64 1, i64* %wi_v1892
    br label %if.end.1900
if.end.1900:
    %num_v1902 = alloca i64
    store i64 0, i64* %num_v1902
    br label %loop.cond.1903
loop.cond.1903:
    %t1906 = load i64, i64* %wi_v1892
    %t1907 = load i64, i64* %slen_v1883
    %t1909 = icmp sge i64 %t1906, %t1907
    %t1908 = zext i1 %t1909 to i64
    %t1910 = icmp eq i64 %t1908, 0
    br i1 %t1910, label %loop.body.1904, label %loop.end.1905
loop.body.1904:
    %t1911 = load i64, i64* %s
    %t1913 = load i64, i64* %wi_v1892
    %t1912 = call i64 @freak_llvm_word_char_at(i64 %t1911, i64 %t1913)
    %t1914 = call i64 @freak_char_to_digit(i64 %t1912)
    %d_v1915 = alloca i64
    store i64 %t1914, i64* %d_v1915
    %t1916 = load i64, i64* %d_v1915
    %t1918 = icmp slt i64 %t1916, 0
    %t1917 = zext i1 %t1918 to i64
    %t1922 = icmp ne i64 %t1917, 0
    br i1 %t1922, label %if.then.1919, label %if.end.1921
if.then.1919:
    ret i64 0
    br label %if.end.1921
if.end.1921:
    %t1923 = load i64, i64* %num_v1902
    %t1924 = mul i64 %t1923, 10
    %t1925 = load i64, i64* %d_v1915
    %t1926 = add i64 %t1924, %t1925
    store i64 %t1926, i64* %num_v1902
    %t1927 = load i64, i64* %wi_v1892
    %t1928 = add i64 %t1927, 1
    store i64 %t1928, i64* %wi_v1892
    br label %loop.cond.1903
loop.end.1905:
    %t1929 = load i64, i64* %neg_v1891
    %t1933 = icmp ne i64 %t1929, 0
    br i1 %t1933, label %if.then.1930, label %if.end.1932
if.then.1930:
    %t1934 = load i64, i64* %num_v1902
    %t1935 = sub i64 0, %t1934
    ret i64 %t1935
    br label %if.end.1932
if.end.1932:
    %t1936 = load i64, i64* %num_v1902
    ret i64 %t1936
    ret i64 0
}

define i64 @freak_bool_to_word(i64 %arg_b) {
entry:
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t1937 = load i64, i64* %b
    %t1941 = icmp ne i64 %t1937, 0
    br i1 %t1941, label %if.then.1938, label %if.end.1940
if.then.1938:
    %t1942 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.117, i64 0, i64 0
    %t1943 = ptrtoint i8* %t1942 to i64
    ret i64 %t1943
    br label %if.end.1940
if.end.1940:
    %t1944 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.118, i64 0, i64 0
    %t1945 = ptrtoint i8* %t1944 to i64
    ret i64 %t1945
    ret i64 0
}

define void @freak_array_sort_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t1946 = load i64, i64* %handle
    %t1947 = call i64 @freak_llvm_array_len(i64 %t1946)
    %alen_v1948 = alloca i64
    store i64 %t1947, i64* %alen_v1948
    %t1949 = load i64, i64* %alen_v1948
    %t1951 = icmp sle i64 %t1949, 1
    %t1950 = zext i1 %t1951 to i64
    %t1955 = icmp ne i64 %t1950, 0
    br i1 %t1955, label %if.then.1952, label %if.end.1954
if.then.1952:
    ret void
    br label %if.end.1954
if.end.1954:
    %si_v1956 = alloca i64
    store i64 1, i64* %si_v1956
    br label %loop.cond.1957
loop.cond.1957:
    %t1960 = load i64, i64* %si_v1956
    %t1961 = load i64, i64* %alen_v1948
    %t1963 = icmp sge i64 %t1960, %t1961
    %t1962 = zext i1 %t1963 to i64
    %t1964 = icmp eq i64 %t1962, 0
    br i1 %t1964, label %loop.body.1958, label %loop.end.1959
loop.body.1958:
    %t1965 = load i64, i64* %handle
    %t1966 = load i64, i64* %si_v1956
    %t1967 = call i64 @freak_llvm_array_get(i64 %t1965, i64 %t1966)
    %key_w_v1968 = alloca i64
    store i64 %t1967, i64* %key_w_v1968
    %t1969 = load i64, i64* %key_w_v1968
    %t1970 = call i64 @freak_llvm_word_to_int(i64 %t1969)
    %key_v1971 = alloca i64
    store i64 %t1970, i64* %key_v1971
    %t1972 = load i64, i64* %si_v1956
    %t1973 = sub i64 %t1972, 1
    %sj_v1974 = alloca i64
    store i64 %t1973, i64* %sj_v1974
    %sorted_v1975 = alloca i64
    store i64 0, i64* %sorted_v1975
    br label %loop.cond.1976
loop.cond.1976:
    %t1979 = load i64, i64* %sj_v1974
    %t1981 = icmp slt i64 %t1979, 0
    %t1980 = zext i1 %t1981 to i64
    %t1982 = load i64, i64* %sorted_v1975
    %t1984 = icmp ne i64 %t1980, 0
    %t1985 = icmp ne i64 %t1982, 0
    %t1986 = or i1 %t1984, %t1985
    %t1983 = zext i1 %t1986 to i64
    %t1987 = icmp eq i64 %t1983, 0
    br i1 %t1987, label %loop.body.1977, label %loop.end.1978
loop.body.1977:
    %t1988 = load i64, i64* %handle
    %t1989 = load i64, i64* %sj_v1974
    %t1990 = call i64 @freak_llvm_array_get(i64 %t1988, i64 %t1989)
    %cw_v1991 = alloca i64
    store i64 %t1990, i64* %cw_v1991
    %t1992 = load i64, i64* %cw_v1991
    %t1993 = call i64 @freak_llvm_word_to_int(i64 %t1992)
    %cv_v1994 = alloca i64
    store i64 %t1993, i64* %cv_v1994
    %t1995 = load i64, i64* %cv_v1994
    %t1996 = load i64, i64* %key_v1971
    %t1998 = icmp sgt i64 %t1995, %t1996
    %t1997 = zext i1 %t1998 to i64
    %t2002 = icmp ne i64 %t1997, 0
    br i1 %t2002, label %if.then.1999, label %if.else.2000
if.then.1999:
    %t2003 = load i64, i64* %handle
    %t2004 = load i64, i64* %sj_v1974
    %t2005 = add i64 %t2004, 1
    %t2006 = load i64, i64* %cw_v1991
    call void @freak_llvm_array_set(i64 %t2003, i64 %t2005, i64 %t2006)
    %t2007 = load i64, i64* %sj_v1974
    %t2008 = sub i64 %t2007, 1
    store i64 %t2008, i64* %sj_v1974
    br label %if.end.2001
if.else.2000:
    store i64 1, i64* %sorted_v1975
    br label %if.end.2001
if.end.2001:
    br label %loop.cond.1976
loop.end.1978:
    %t2009 = load i64, i64* %handle
    %t2010 = load i64, i64* %sj_v1974
    %t2011 = add i64 %t2010, 1
    %t2012 = load i64, i64* %key_v1971
    %t2013 = call i64 @freak_llvm_word_from_int(i64 %t2012)
    call void @freak_llvm_array_set(i64 %t2009, i64 %t2011, i64 %t2013)
    %t2014 = load i64, i64* %si_v1956
    %t2015 = add i64 %t2014, 1
    store i64 %t2015, i64* %si_v1956
    br label %loop.cond.1957
loop.end.1959:
    ret void
}

define void @freak_array_sort_word(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2016 = load i64, i64* %handle
    %t2017 = call i64 @freak_llvm_array_len(i64 %t2016)
    %alen_v2018 = alloca i64
    store i64 %t2017, i64* %alen_v2018
    %t2019 = load i64, i64* %alen_v2018
    %t2021 = icmp sle i64 %t2019, 1
    %t2020 = zext i1 %t2021 to i64
    %t2025 = icmp ne i64 %t2020, 0
    br i1 %t2025, label %if.then.2022, label %if.end.2024
if.then.2022:
    ret void
    br label %if.end.2024
if.end.2024:
    %si_v2026 = alloca i64
    store i64 1, i64* %si_v2026
    br label %loop.cond.2027
loop.cond.2027:
    %t2030 = load i64, i64* %si_v2026
    %t2031 = load i64, i64* %alen_v2018
    %t2033 = icmp sge i64 %t2030, %t2031
    %t2032 = zext i1 %t2033 to i64
    %t2034 = icmp eq i64 %t2032, 0
    br i1 %t2034, label %loop.body.2028, label %loop.end.2029
loop.body.2028:
    %t2035 = load i64, i64* %handle
    %t2036 = load i64, i64* %si_v2026
    %t2037 = call i64 @freak_llvm_array_get(i64 %t2035, i64 %t2036)
    %key_w_v2038 = alloca i64
    store i64 %t2037, i64* %key_w_v2038
    %t2039 = load i64, i64* %si_v2026
    %t2040 = sub i64 %t2039, 1
    %sj_v2041 = alloca i64
    store i64 %t2040, i64* %sj_v2041
    %sorted_v2042 = alloca i64
    store i64 0, i64* %sorted_v2042
    br label %loop.cond.2043
loop.cond.2043:
    %t2046 = load i64, i64* %sj_v2041
    %t2048 = icmp slt i64 %t2046, 0
    %t2047 = zext i1 %t2048 to i64
    %t2049 = load i64, i64* %sorted_v2042
    %t2051 = icmp ne i64 %t2047, 0
    %t2052 = icmp ne i64 %t2049, 0
    %t2053 = or i1 %t2051, %t2052
    %t2050 = zext i1 %t2053 to i64
    %t2054 = icmp eq i64 %t2050, 0
    br i1 %t2054, label %loop.body.2044, label %loop.end.2045
loop.body.2044:
    %t2055 = load i64, i64* %handle
    %t2056 = load i64, i64* %sj_v2041
    %t2057 = call i64 @freak_llvm_array_get(i64 %t2055, i64 %t2056)
    %cw_v2058 = alloca i64
    store i64 %t2057, i64* %cw_v2058
    %t2059 = load i64, i64* %cw_v2058
    %t2060 = load i64, i64* %key_w_v2038
    %t2061 = call i64 @freak_word_compare(i64 %t2059, i64 %t2060)
    %t2063 = icmp sgt i64 %t2061, 0
    %t2062 = zext i1 %t2063 to i64
    %t2067 = icmp ne i64 %t2062, 0
    br i1 %t2067, label %if.then.2064, label %if.else.2065
if.then.2064:
    %t2068 = load i64, i64* %handle
    %t2069 = load i64, i64* %sj_v2041
    %t2070 = add i64 %t2069, 1
    %t2071 = load i64, i64* %cw_v2058
    call void @freak_llvm_array_set(i64 %t2068, i64 %t2070, i64 %t2071)
    %t2072 = load i64, i64* %sj_v2041
    %t2073 = sub i64 %t2072, 1
    store i64 %t2073, i64* %sj_v2041
    br label %if.end.2066
if.else.2065:
    store i64 1, i64* %sorted_v2042
    br label %if.end.2066
if.end.2066:
    br label %loop.cond.2043
loop.end.2045:
    %t2074 = load i64, i64* %handle
    %t2075 = load i64, i64* %sj_v2041
    %t2076 = add i64 %t2075, 1
    %t2077 = load i64, i64* %key_w_v2038
    call void @freak_llvm_array_set(i64 %t2074, i64 %t2076, i64 %t2077)
    %t2078 = load i64, i64* %si_v2026
    %t2079 = add i64 %t2078, 1
    store i64 %t2079, i64* %si_v2026
    br label %loop.cond.2027
loop.end.2029:
    ret void
}

define i64 @freak_array_binary_search_int(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %lo_v2080 = alloca i64
    store i64 0, i64* %lo_v2080
    %t2081 = load i64, i64* %handle
    %t2082 = call i64 @freak_llvm_array_len(i64 %t2081)
    %t2083 = sub i64 %t2082, 1
    %hi_v2084 = alloca i64
    store i64 %t2083, i64* %hi_v2084
    br label %loop.cond.2085
loop.cond.2085:
    %t2088 = load i64, i64* %lo_v2080
    %t2089 = load i64, i64* %hi_v2084
    %t2091 = icmp sgt i64 %t2088, %t2089
    %t2090 = zext i1 %t2091 to i64
    %t2092 = icmp eq i64 %t2090, 0
    br i1 %t2092, label %loop.body.2086, label %loop.end.2087
loop.body.2086:
    %t2093 = load i64, i64* %hi_v2084
    %t2094 = load i64, i64* %lo_v2080
    %t2095 = sub i64 %t2093, %t2094
    %range_v2096 = alloca i64
    store i64 %t2095, i64* %range_v2096
    %t2097 = load i64, i64* %range_v2096
    %t2098 = sdiv i64 %t2097, 2
    %half_v2099 = alloca i64
    store i64 %t2098, i64* %half_v2099
    %t2100 = load i64, i64* %lo_v2080
    %t2101 = load i64, i64* %half_v2099
    %t2102 = add i64 %t2100, %t2101
    %mid_v2103 = alloca i64
    store i64 %t2102, i64* %mid_v2103
    %t2104 = load i64, i64* %handle
    %t2105 = load i64, i64* %mid_v2103
    %t2106 = call i64 @freak_llvm_array_get(i64 %t2104, i64 %t2105)
    %mw_v2107 = alloca i64
    store i64 %t2106, i64* %mw_v2107
    %t2108 = load i64, i64* %mw_v2107
    %t2109 = call i64 @freak_llvm_word_to_int(i64 %t2108)
    %mv_v2110 = alloca i64
    store i64 %t2109, i64* %mv_v2110
    %t2111 = load i64, i64* %mv_v2110
    %t2112 = load i64, i64* %target
    %t2114 = icmp eq i64 %t2111, %t2112
    %t2113 = zext i1 %t2114 to i64
    %t2118 = icmp ne i64 %t2113, 0
    br i1 %t2118, label %if.then.2115, label %if.end.2117
if.then.2115:
    %t2119 = load i64, i64* %mid_v2103
    ret i64 %t2119
    br label %if.end.2117
if.end.2117:
    %t2120 = load i64, i64* %mv_v2110
    %t2121 = load i64, i64* %target
    %t2123 = icmp slt i64 %t2120, %t2121
    %t2122 = zext i1 %t2123 to i64
    %t2127 = icmp ne i64 %t2122, 0
    br i1 %t2127, label %if.then.2124, label %if.else.2125
if.then.2124:
    %t2128 = load i64, i64* %mid_v2103
    %t2129 = add i64 %t2128, 1
    store i64 %t2129, i64* %lo_v2080
    br label %if.end.2126
if.else.2125:
    %t2130 = load i64, i64* %mid_v2103
    %t2131 = sub i64 %t2130, 1
    store i64 %t2131, i64* %hi_v2084
    br label %if.end.2126
if.end.2126:
    br label %loop.cond.2085
loop.end.2087:
    %t2132 = sub i64 0, 1
    ret i64 %t2132
    ret i64 0
}

define i64 @freak_array_find(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2133 = load i64, i64* %handle
    %t2134 = call i64 @freak_llvm_array_len(i64 %t2133)
    %alen_v2135 = alloca i64
    store i64 %t2134, i64* %alen_v2135
    %fi_v2136 = alloca i64
    store i64 0, i64* %fi_v2136
    %t2142 = load i64, i64* %alen_v2135
    %rep.2141 = alloca i64
    store i64 0, i64* %rep.2141
    br label %loop.cond.2137
loop.cond.2137:
    %t2143 = load i64, i64* %rep.2141
    %t2144 = icmp slt i64 %t2143, %t2142
    br i1 %t2144, label %loop.body.2138, label %loop.end.2139
loop.body.2138:
    %t2145 = load i64, i64* %handle
    %t2146 = load i64, i64* %fi_v2136
    %t2147 = call i64 @freak_llvm_array_get(i64 %t2145, i64 %t2146)
    %fw_v2148 = alloca i64
    store i64 %t2147, i64* %fw_v2148
    %t2149 = load i64, i64* %fw_v2148
    %t2150 = load i64, i64* %target
    %t2151 = call i64 @freak_llvm_word_eq(i64 %t2149, i64 %t2150)
    %t2155 = icmp ne i64 %t2151, 0
    br i1 %t2155, label %if.then.2152, label %if.end.2154
if.then.2152:
    %t2156 = load i64, i64* %fi_v2136
    ret i64 %t2156
    br label %if.end.2154
if.end.2154:
    %t2157 = load i64, i64* %fi_v2136
    %t2158 = add i64 %t2157, 1
    store i64 %t2158, i64* %fi_v2136
    br label %loop.inc.2140
loop.inc.2140:
    %t2159 = load i64, i64* %rep.2141
    %t2160 = add i64 %t2159, 1
    store i64 %t2160, i64* %rep.2141
    br label %loop.cond.2137
loop.end.2139:
    %t2161 = sub i64 0, 1
    ret i64 %t2161
    ret i64 0
}

define i64 @freak_array_contains(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2162 = load i64, i64* %handle
    %t2163 = load i64, i64* %target
    %t2164 = call i64 @freak_array_find(i64 %t2162, i64 %t2163)
    %t2166 = icmp sge i64 %t2164, 0
    %t2165 = zext i1 %t2166 to i64
    ret i64 %t2165
    ret i64 0
}

define void @freak_array_reverse(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2167 = load i64, i64* %handle
    %t2168 = call i64 @freak_llvm_array_len(i64 %t2167)
    %alen_v2169 = alloca i64
    store i64 %t2168, i64* %alen_v2169
    %t2170 = load i64, i64* %alen_v2169
    %t2172 = icmp sle i64 %t2170, 1
    %t2171 = zext i1 %t2172 to i64
    %t2176 = icmp ne i64 %t2171, 0
    br i1 %t2176, label %if.then.2173, label %if.end.2175
if.then.2173:
    ret void
    br label %if.end.2175
if.end.2175:
    %lo_v2177 = alloca i64
    store i64 0, i64* %lo_v2177
    %t2178 = load i64, i64* %alen_v2169
    %t2179 = sub i64 %t2178, 1
    %hi_v2180 = alloca i64
    store i64 %t2179, i64* %hi_v2180
    br label %loop.cond.2181
loop.cond.2181:
    %t2184 = load i64, i64* %lo_v2177
    %t2185 = load i64, i64* %hi_v2180
    %t2187 = icmp sge i64 %t2184, %t2185
    %t2186 = zext i1 %t2187 to i64
    %t2188 = icmp eq i64 %t2186, 0
    br i1 %t2188, label %loop.body.2182, label %loop.end.2183
loop.body.2182:
    %t2189 = load i64, i64* %handle
    %t2190 = load i64, i64* %lo_v2177
    %t2191 = call i64 @freak_llvm_array_get(i64 %t2189, i64 %t2190)
    %tmp_v2192 = alloca i64
    store i64 %t2191, i64* %tmp_v2192
    %t2193 = load i64, i64* %handle
    %t2194 = load i64, i64* %hi_v2180
    %t2195 = call i64 @freak_llvm_array_get(i64 %t2193, i64 %t2194)
    %hw_v2196 = alloca i64
    store i64 %t2195, i64* %hw_v2196
    %t2197 = load i64, i64* %handle
    %t2198 = load i64, i64* %lo_v2177
    %t2199 = load i64, i64* %hw_v2196
    call void @freak_llvm_array_set(i64 %t2197, i64 %t2198, i64 %t2199)
    %t2200 = load i64, i64* %handle
    %t2201 = load i64, i64* %hi_v2180
    %t2202 = load i64, i64* %tmp_v2192
    call void @freak_llvm_array_set(i64 %t2200, i64 %t2201, i64 %t2202)
    %t2203 = load i64, i64* %lo_v2177
    %t2204 = add i64 %t2203, 1
    store i64 %t2204, i64* %lo_v2177
    %t2205 = load i64, i64* %hi_v2180
    %t2206 = sub i64 %t2205, 1
    store i64 %t2206, i64* %hi_v2180
    br label %loop.cond.2181
loop.end.2183:
    ret void
}

define i64 @freak_array_copy(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2207 = call i64 @freak_llvm_array_new()
    %new_arr_v2208 = alloca i64
    store i64 %t2207, i64* %new_arr_v2208
    %t2209 = load i64, i64* %handle
    %t2210 = call i64 @freak_llvm_array_len(i64 %t2209)
    %alen_v2211 = alloca i64
    store i64 %t2210, i64* %alen_v2211
    %ci_v2212 = alloca i64
    store i64 0, i64* %ci_v2212
    %t2218 = load i64, i64* %alen_v2211
    %rep.2217 = alloca i64
    store i64 0, i64* %rep.2217
    br label %loop.cond.2213
loop.cond.2213:
    %t2219 = load i64, i64* %rep.2217
    %t2220 = icmp slt i64 %t2219, %t2218
    br i1 %t2220, label %loop.body.2214, label %loop.end.2215
loop.body.2214:
    %t2221 = load i64, i64* %handle
    %t2222 = load i64, i64* %ci_v2212
    %t2223 = call i64 @freak_llvm_array_get(i64 %t2221, i64 %t2222)
    %cw_v2224 = alloca i64
    store i64 %t2223, i64* %cw_v2224
    %t2225 = load i64, i64* %new_arr_v2208
    %t2226 = load i64, i64* %cw_v2224
    call void @freak_llvm_array_push(i64 %t2225, i64 %t2226)
    %t2227 = load i64, i64* %ci_v2212
    %t2228 = add i64 %t2227, 1
    store i64 %t2228, i64* %ci_v2212
    br label %loop.inc.2216
loop.inc.2216:
    %t2229 = load i64, i64* %rep.2217
    %t2230 = add i64 %t2229, 1
    store i64 %t2230, i64* %rep.2217
    br label %loop.cond.2213
loop.end.2215:
    %t2231 = load i64, i64* %new_arr_v2208
    ret i64 %t2231
    ret i64 0
}

define i64 @freak_array_join(i64 %arg_handle, i64 %arg_sep) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %sep = alloca i64
    store i64 %arg_sep, i64* %sep
    %t2232 = load i64, i64* %handle
    %t2233 = call i64 @freak_llvm_array_len(i64 %t2232)
    %alen_v2234 = alloca i64
    store i64 %t2233, i64* %alen_v2234
    %t2235 = load i64, i64* %alen_v2234
    %t2237 = icmp eq i64 %t2235, 0
    %t2236 = zext i1 %t2237 to i64
    %t2241 = icmp ne i64 %t2236, 0
    br i1 %t2241, label %if.then.2238, label %if.end.2240
if.then.2238:
    %t2242 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.119, i64 0, i64 0
    %t2243 = ptrtoint i8* %t2242 to i64
    ret i64 %t2243
    br label %if.end.2240
if.end.2240:
    %t2244 = load i64, i64* %handle
    %t2245 = call i64 @freak_llvm_array_get(i64 %t2244, i64 0)
    %aj_out_v2246 = alloca i64
    store i64 %t2245, i64* %aj_out_v2246
    %ji_v2247 = alloca i64
    store i64 1, i64* %ji_v2247
    br label %loop.cond.2248
loop.cond.2248:
    %t2251 = load i64, i64* %ji_v2247
    %t2252 = load i64, i64* %alen_v2234
    %t2254 = icmp sge i64 %t2251, %t2252
    %t2253 = zext i1 %t2254 to i64
    %t2255 = icmp eq i64 %t2253, 0
    br i1 %t2255, label %loop.body.2249, label %loop.end.2250
loop.body.2249:
    %t2256 = load i64, i64* %handle
    %t2257 = load i64, i64* %ji_v2247
    %t2258 = call i64 @freak_llvm_array_get(i64 %t2256, i64 %t2257)
    %jw_v2259 = alloca i64
    store i64 %t2258, i64* %jw_v2259
    %t2260 = load i64, i64* %aj_out_v2246
    %t2261 = load i64, i64* %sep
    %t2262 = call i64 @freak_llvm_word_concat(i64 %t2260, i64 %t2261)
    %t2263 = load i64, i64* %jw_v2259
    %t2264 = call i64 @freak_llvm_word_concat(i64 %t2262, i64 %t2263)
    store i64 %t2264, i64* %aj_out_v2246
    %t2265 = load i64, i64* %ji_v2247
    %t2266 = add i64 %t2265, 1
    store i64 %t2266, i64* %ji_v2247
    br label %loop.cond.2248
loop.end.2250:
    %t2267 = load i64, i64* %aj_out_v2246
    ret i64 %t2267
    ret i64 0
}

define i64 @freak_array_count(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2268 = load i64, i64* %handle
    %t2269 = call i64 @freak_llvm_array_len(i64 %t2268)
    %alen_v2270 = alloca i64
    store i64 %t2269, i64* %alen_v2270
    %cnt_v2271 = alloca i64
    store i64 0, i64* %cnt_v2271
    %ci_v2272 = alloca i64
    store i64 0, i64* %ci_v2272
    %t2278 = load i64, i64* %alen_v2270
    %rep.2277 = alloca i64
    store i64 0, i64* %rep.2277
    br label %loop.cond.2273
loop.cond.2273:
    %t2279 = load i64, i64* %rep.2277
    %t2280 = icmp slt i64 %t2279, %t2278
    br i1 %t2280, label %loop.body.2274, label %loop.end.2275
loop.body.2274:
    %t2281 = load i64, i64* %handle
    %t2282 = load i64, i64* %ci_v2272
    %t2283 = call i64 @freak_llvm_array_get(i64 %t2281, i64 %t2282)
    %cw_v2284 = alloca i64
    store i64 %t2283, i64* %cw_v2284
    %t2285 = load i64, i64* %cw_v2284
    %t2286 = load i64, i64* %target
    %t2287 = call i64 @freak_llvm_word_eq(i64 %t2285, i64 %t2286)
    %t2291 = icmp ne i64 %t2287, 0
    br i1 %t2291, label %if.then.2288, label %if.end.2290
if.then.2288:
    %t2292 = load i64, i64* %cnt_v2271
    %t2293 = add i64 %t2292, 1
    store i64 %t2293, i64* %cnt_v2271
    br label %if.end.2290
if.end.2290:
    %t2294 = load i64, i64* %ci_v2272
    %t2295 = add i64 %t2294, 1
    store i64 %t2295, i64* %ci_v2272
    br label %loop.inc.2276
loop.inc.2276:
    %t2296 = load i64, i64* %rep.2277
    %t2297 = add i64 %t2296, 1
    store i64 %t2297, i64* %rep.2277
    br label %loop.cond.2273
loop.end.2275:
    %t2298 = load i64, i64* %cnt_v2271
    ret i64 %t2298
    ret i64 0
}

define i64 @freak_array_unique(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2299 = load i64, i64* %handle
    %t2300 = call i64 @freak_llvm_array_len(i64 %t2299)
    %alen_v2301 = alloca i64
    store i64 %t2300, i64* %alen_v2301
    %t2302 = load i64, i64* %alen_v2301
    %t2304 = icmp sle i64 %t2302, 1
    %t2303 = zext i1 %t2304 to i64
    %t2308 = icmp ne i64 %t2303, 0
    br i1 %t2308, label %if.then.2305, label %if.end.2307
if.then.2305:
    %t2309 = load i64, i64* %alen_v2301
    ret i64 %t2309
    br label %if.end.2307
if.end.2307:
    %write_idx_v2310 = alloca i64
    store i64 1, i64* %write_idx_v2310
    %ri_v2311 = alloca i64
    store i64 1, i64* %ri_v2311
    br label %loop.cond.2312
loop.cond.2312:
    %t2315 = load i64, i64* %ri_v2311
    %t2316 = load i64, i64* %alen_v2301
    %t2318 = icmp sge i64 %t2315, %t2316
    %t2317 = zext i1 %t2318 to i64
    %t2319 = icmp eq i64 %t2317, 0
    br i1 %t2319, label %loop.body.2313, label %loop.end.2314
loop.body.2313:
    %t2320 = load i64, i64* %handle
    %t2321 = load i64, i64* %ri_v2311
    %t2322 = call i64 @freak_llvm_array_get(i64 %t2320, i64 %t2321)
    %cur_v2323 = alloca i64
    store i64 %t2322, i64* %cur_v2323
    %t2324 = load i64, i64* %handle
    %t2325 = load i64, i64* %ri_v2311
    %t2326 = sub i64 %t2325, 1
    %t2327 = call i64 @freak_llvm_array_get(i64 %t2324, i64 %t2326)
    %prev_v2328 = alloca i64
    store i64 %t2327, i64* %prev_v2328
    %t2329 = load i64, i64* %cur_v2323
    %t2330 = load i64, i64* %prev_v2328
    %t2331 = call i64 @freak_llvm_word_neq(i64 %t2329, i64 %t2330)
    %t2335 = icmp ne i64 %t2331, 0
    br i1 %t2335, label %if.then.2332, label %if.end.2334
if.then.2332:
    %t2336 = load i64, i64* %handle
    %t2337 = load i64, i64* %write_idx_v2310
    %t2338 = load i64, i64* %cur_v2323
    call void @freak_llvm_array_set(i64 %t2336, i64 %t2337, i64 %t2338)
    %t2339 = load i64, i64* %write_idx_v2310
    %t2340 = add i64 %t2339, 1
    store i64 %t2340, i64* %write_idx_v2310
    br label %if.end.2334
if.end.2334:
    %t2341 = load i64, i64* %ri_v2311
    %t2342 = add i64 %t2341, 1
    store i64 %t2342, i64* %ri_v2311
    br label %loop.cond.2312
loop.end.2314:
    %t2343 = load i64, i64* %write_idx_v2310
    ret i64 %t2343
    ret i64 0
}

define i64 @freak_array_sum_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2344 = load i64, i64* %handle
    %t2345 = call i64 @freak_llvm_array_len(i64 %t2344)
    %alen_v2346 = alloca i64
    store i64 %t2345, i64* %alen_v2346
    %total_v2347 = alloca i64
    store i64 0, i64* %total_v2347
    %si_v2348 = alloca i64
    store i64 0, i64* %si_v2348
    %t2354 = load i64, i64* %alen_v2346
    %rep.2353 = alloca i64
    store i64 0, i64* %rep.2353
    br label %loop.cond.2349
loop.cond.2349:
    %t2355 = load i64, i64* %rep.2353
    %t2356 = icmp slt i64 %t2355, %t2354
    br i1 %t2356, label %loop.body.2350, label %loop.end.2351
loop.body.2350:
    %t2357 = load i64, i64* %handle
    %t2358 = load i64, i64* %si_v2348
    %t2359 = call i64 @freak_llvm_array_get(i64 %t2357, i64 %t2358)
    %sw_v2360 = alloca i64
    store i64 %t2359, i64* %sw_v2360
    %t2361 = load i64, i64* %sw_v2360
    %t2362 = call i64 @freak_llvm_word_to_int(i64 %t2361)
    %t2363 = load i64, i64* %total_v2347
    %t2364 = add i64 %t2363, %t2362
    store i64 %t2364, i64* %total_v2347
    %t2365 = load i64, i64* %si_v2348
    %t2366 = add i64 %t2365, 1
    store i64 %t2366, i64* %si_v2348
    br label %loop.inc.2352
loop.inc.2352:
    %t2367 = load i64, i64* %rep.2353
    %t2368 = add i64 %t2367, 1
    store i64 %t2368, i64* %rep.2353
    br label %loop.cond.2349
loop.end.2351:
    %t2369 = load i64, i64* %total_v2347
    ret i64 %t2369
    ret i64 0
}

define i64 @freak_array_max_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2370 = load i64, i64* %handle
    %t2371 = call i64 @freak_llvm_array_len(i64 %t2370)
    %alen_v2372 = alloca i64
    store i64 %t2371, i64* %alen_v2372
    %t2373 = load i64, i64* %alen_v2372
    %t2375 = icmp eq i64 %t2373, 0
    %t2374 = zext i1 %t2375 to i64
    %t2379 = icmp ne i64 %t2374, 0
    br i1 %t2379, label %if.then.2376, label %if.end.2378
if.then.2376:
    ret i64 0
    br label %if.end.2378
if.end.2378:
    %t2380 = load i64, i64* %handle
    %t2381 = call i64 @freak_llvm_array_get(i64 %t2380, i64 0)
    %mw_v2382 = alloca i64
    store i64 %t2381, i64* %mw_v2382
    %t2383 = load i64, i64* %mw_v2382
    %t2384 = call i64 @freak_llvm_word_to_int(i64 %t2383)
    %mx_v2385 = alloca i64
    store i64 %t2384, i64* %mx_v2385
    %mi_v2386 = alloca i64
    store i64 1, i64* %mi_v2386
    br label %loop.cond.2387
loop.cond.2387:
    %t2390 = load i64, i64* %mi_v2386
    %t2391 = load i64, i64* %alen_v2372
    %t2393 = icmp sge i64 %t2390, %t2391
    %t2392 = zext i1 %t2393 to i64
    %t2394 = icmp eq i64 %t2392, 0
    br i1 %t2394, label %loop.body.2388, label %loop.end.2389
loop.body.2388:
    %t2395 = load i64, i64* %handle
    %t2396 = load i64, i64* %mi_v2386
    %t2397 = call i64 @freak_llvm_array_get(i64 %t2395, i64 %t2396)
    %cw_v2398 = alloca i64
    store i64 %t2397, i64* %cw_v2398
    %t2399 = load i64, i64* %cw_v2398
    %t2400 = call i64 @freak_llvm_word_to_int(i64 %t2399)
    %cv_v2401 = alloca i64
    store i64 %t2400, i64* %cv_v2401
    %t2402 = load i64, i64* %cv_v2401
    %t2403 = load i64, i64* %mx_v2385
    %t2405 = icmp sgt i64 %t2402, %t2403
    %t2404 = zext i1 %t2405 to i64
    %t2409 = icmp ne i64 %t2404, 0
    br i1 %t2409, label %if.then.2406, label %if.end.2408
if.then.2406:
    %t2410 = load i64, i64* %cv_v2401
    store i64 %t2410, i64* %mx_v2385
    br label %if.end.2408
if.end.2408:
    %t2411 = load i64, i64* %mi_v2386
    %t2412 = add i64 %t2411, 1
    store i64 %t2412, i64* %mi_v2386
    br label %loop.cond.2387
loop.end.2389:
    %t2413 = load i64, i64* %mx_v2385
    ret i64 %t2413
    ret i64 0
}

define i64 @freak_array_min_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2414 = load i64, i64* %handle
    %t2415 = call i64 @freak_llvm_array_len(i64 %t2414)
    %alen_v2416 = alloca i64
    store i64 %t2415, i64* %alen_v2416
    %t2417 = load i64, i64* %alen_v2416
    %t2419 = icmp eq i64 %t2417, 0
    %t2418 = zext i1 %t2419 to i64
    %t2423 = icmp ne i64 %t2418, 0
    br i1 %t2423, label %if.then.2420, label %if.end.2422
if.then.2420:
    ret i64 0
    br label %if.end.2422
if.end.2422:
    %t2424 = load i64, i64* %handle
    %t2425 = call i64 @freak_llvm_array_get(i64 %t2424, i64 0)
    %mw_v2426 = alloca i64
    store i64 %t2425, i64* %mw_v2426
    %t2427 = load i64, i64* %mw_v2426
    %t2428 = call i64 @freak_llvm_word_to_int(i64 %t2427)
    %mn_v2429 = alloca i64
    store i64 %t2428, i64* %mn_v2429
    %mi_v2430 = alloca i64
    store i64 1, i64* %mi_v2430
    br label %loop.cond.2431
loop.cond.2431:
    %t2434 = load i64, i64* %mi_v2430
    %t2435 = load i64, i64* %alen_v2416
    %t2437 = icmp sge i64 %t2434, %t2435
    %t2436 = zext i1 %t2437 to i64
    %t2438 = icmp eq i64 %t2436, 0
    br i1 %t2438, label %loop.body.2432, label %loop.end.2433
loop.body.2432:
    %t2439 = load i64, i64* %handle
    %t2440 = load i64, i64* %mi_v2430
    %t2441 = call i64 @freak_llvm_array_get(i64 %t2439, i64 %t2440)
    %cw_v2442 = alloca i64
    store i64 %t2441, i64* %cw_v2442
    %t2443 = load i64, i64* %cw_v2442
    %t2444 = call i64 @freak_llvm_word_to_int(i64 %t2443)
    %cv_v2445 = alloca i64
    store i64 %t2444, i64* %cv_v2445
    %t2446 = load i64, i64* %cv_v2445
    %t2447 = load i64, i64* %mn_v2429
    %t2449 = icmp slt i64 %t2446, %t2447
    %t2448 = zext i1 %t2449 to i64
    %t2453 = icmp ne i64 %t2448, 0
    br i1 %t2453, label %if.then.2450, label %if.end.2452
if.then.2450:
    %t2454 = load i64, i64* %cv_v2445
    store i64 %t2454, i64* %mn_v2429
    br label %if.end.2452
if.end.2452:
    %t2455 = load i64, i64* %mi_v2430
    %t2456 = add i64 %t2455, 1
    store i64 %t2456, i64* %mi_v2430
    br label %loop.cond.2431
loop.end.2433:
    %t2457 = load i64, i64* %mn_v2429
    ret i64 %t2457
    ret i64 0
}

define void @freak_json_init() {
entry:
    %t2458 = load i64, i64* @g_json_inited
    %t2460 = icmp eq i64 %t2458, 0
    %t2459 = zext i1 %t2460 to i64
    %t2464 = icmp ne i64 %t2459, 0
    br i1 %t2464, label %if.then.2461, label %if.end.2463
if.then.2461:
    %t2465 = call i64 @freak_llvm_array_new()
    store i64 %t2465, i64* @g_json_types
    %t2466 = call i64 @freak_llvm_array_new()
    store i64 %t2466, i64* @g_json_vals
    %t2467 = call i64 @freak_llvm_array_new()
    store i64 %t2467, i64* @g_json_children
    %t2468 = call i64 @freak_llvm_array_new()
    store i64 %t2468, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 1, i64* @g_json_inited
    br label %if.end.2463
if.end.2463:
    ret void
}

define i64 @freak_json_alloc(i64 %arg_jtype, i64 %arg_jval) {
entry:
    %jtype = alloca i64
    store i64 %arg_jtype, i64* %jtype
    %jval = alloca i64
    store i64 %arg_jval, i64* %jval
    %t2469 = load i64, i64* @g_json_count
    %idx_v2470 = alloca i64
    store i64 %t2469, i64* %idx_v2470
    %t2471 = load i64, i64* @g_json_types
    %t2472 = load i64, i64* %jtype
    call void @freak_llvm_array_push(i64 %t2471, i64 %t2472)
    %t2473 = load i64, i64* @g_json_vals
    %t2474 = load i64, i64* %jval
    call void @freak_llvm_array_push(i64 %t2473, i64 %t2474)
    %t2475 = load i64, i64* @g_json_children
    %t2476 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2475, i64 %t2476)
    %t2477 = load i64, i64* @g_json_keys
    %t2478 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2477, i64 %t2478)
    %t2479 = load i64, i64* @g_json_count
    %t2480 = add i64 %t2479, 1
    store i64 %t2480, i64* @g_json_count
    %t2481 = load i64, i64* %idx_v2470
    ret i64 %t2481
    ret i64 0
}

define i64 @freak_json_get_type(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2482 = load i64, i64* @g_json_types
    %t2483 = load i64, i64* %handle
    %t2484 = call i64 @freak_llvm_array_get(i64 %t2482, i64 %t2483)
    ret i64 %t2484
    ret i64 0
}

define i64 @freak_json_get_str(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2485 = load i64, i64* @g_json_vals
    %t2486 = load i64, i64* %handle
    %t2487 = call i64 @freak_llvm_array_get(i64 %t2485, i64 %t2486)
    ret i64 %t2487
    ret i64 0
}

define i64 @freak_json_get_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2488 = load i64, i64* @g_json_vals
    %t2489 = load i64, i64* %handle
    %t2490 = call i64 @freak_llvm_array_get(i64 %t2488, i64 %t2489)
    %v_v2491 = alloca i64
    store i64 %t2490, i64* %v_v2491
    %t2492 = load i64, i64* %v_v2491
    %t2493 = call i64 @freak_llvm_word_to_int(i64 %t2492)
    ret i64 %t2493
    ret i64 0
}

define i64 @freak_json_get_bool(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2494 = load i64, i64* @g_json_vals
    %t2495 = load i64, i64* %handle
    %t2496 = call i64 @freak_llvm_array_get(i64 %t2494, i64 %t2495)
    %v_v2497 = alloca i64
    store i64 %t2496, i64* %v_v2497
    %t2498 = load i64, i64* %v_v2497
    %t2499 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.120, i64 0, i64 0
    %t2500 = ptrtoint i8* %t2499 to i64
    %t2501 = call i64 @freak_llvm_word_eq(i64 %t2498, i64 %t2500)
    ret i64 %t2501
    ret i64 0
}

define i64 @freak_json_is_null(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2502 = load i64, i64* @g_json_types
    %t2503 = load i64, i64* %handle
    %t2504 = call i64 @freak_llvm_array_get(i64 %t2502, i64 %t2503)
    %t_v2505 = alloca i64
    store i64 %t2504, i64* %t_v2505
    %t2506 = load i64, i64* %t_v2505
    %t2507 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.121, i64 0, i64 0
    %t2508 = ptrtoint i8* %t2507 to i64
    %t2509 = call i64 @freak_llvm_word_eq(i64 %t2506, i64 %t2508)
    ret i64 %t2509
    ret i64 0
}

define i64 @freak_json_arr_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2510 = load i64, i64* @g_json_children
    %t2511 = load i64, i64* %handle
    %t2512 = call i64 @freak_llvm_array_get(i64 %t2510, i64 %t2511)
    %ch_v2513 = alloca i64
    store i64 %t2512, i64* %ch_v2513
    %t2514 = load i64, i64* %ch_v2513
    %t2515 = call i64 @freak_llvm_word_to_int(i64 %t2514)
    %ch_handle_v2516 = alloca i64
    store i64 %t2515, i64* %ch_handle_v2516
    %t2517 = load i64, i64* %ch_handle_v2516
    %t2518 = call i64 @freak_llvm_array_len(i64 %t2517)
    ret i64 %t2518
    ret i64 0
}

define i64 @freak_json_arr_get(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2519 = load i64, i64* @g_json_children
    %t2520 = load i64, i64* %handle
    %t2521 = call i64 @freak_llvm_array_get(i64 %t2519, i64 %t2520)
    %ch_v2522 = alloca i64
    store i64 %t2521, i64* %ch_v2522
    %t2523 = load i64, i64* %ch_v2522
    %t2524 = call i64 @freak_llvm_word_to_int(i64 %t2523)
    %ch_handle_v2525 = alloca i64
    store i64 %t2524, i64* %ch_handle_v2525
    %t2526 = load i64, i64* %ch_handle_v2525
    %t2527 = load i64, i64* %index
    %t2528 = call i64 @freak_llvm_array_get(i64 %t2526, i64 %t2527)
    %val_w_v2529 = alloca i64
    store i64 %t2528, i64* %val_w_v2529
    %t2530 = load i64, i64* %val_w_v2529
    %t2531 = call i64 @freak_llvm_word_to_int(i64 %t2530)
    ret i64 %t2531
    ret i64 0
}

define i64 @freak_json_obj_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2532 = load i64, i64* @g_json_keys
    %t2533 = load i64, i64* %handle
    %t2534 = call i64 @freak_llvm_array_get(i64 %t2532, i64 %t2533)
    %ks_v2535 = alloca i64
    store i64 %t2534, i64* %ks_v2535
    %t2536 = load i64, i64* %ks_v2535
    %t2537 = call i64 @freak_llvm_word_to_int(i64 %t2536)
    %ks_handle_v2538 = alloca i64
    store i64 %t2537, i64* %ks_handle_v2538
    %t2539 = load i64, i64* %ks_handle_v2538
    %t2540 = call i64 @freak_llvm_array_len(i64 %t2539)
    ret i64 %t2540
    ret i64 0
}

define i64 @freak_json_obj_get(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2541 = load i64, i64* @g_json_keys
    %t2542 = load i64, i64* %handle
    %t2543 = call i64 @freak_llvm_array_get(i64 %t2541, i64 %t2542)
    %ks_v2544 = alloca i64
    store i64 %t2543, i64* %ks_v2544
    %t2545 = load i64, i64* %ks_v2544
    %t2546 = call i64 @freak_llvm_word_to_int(i64 %t2545)
    %ks_handle_v2547 = alloca i64
    store i64 %t2546, i64* %ks_handle_v2547
    %t2548 = load i64, i64* @g_json_children
    %t2549 = load i64, i64* %handle
    %t2550 = call i64 @freak_llvm_array_get(i64 %t2548, i64 %t2549)
    %ch_v2551 = alloca i64
    store i64 %t2550, i64* %ch_v2551
    %t2552 = load i64, i64* %ch_v2551
    %t2553 = call i64 @freak_llvm_word_to_int(i64 %t2552)
    %ch_handle_v2554 = alloca i64
    store i64 %t2553, i64* %ch_handle_v2554
    %t2555 = load i64, i64* %ks_handle_v2547
    %t2556 = call i64 @freak_llvm_array_len(i64 %t2555)
    %klen_v2557 = alloca i64
    store i64 %t2556, i64* %klen_v2557
    %ki_v2558 = alloca i64
    store i64 0, i64* %ki_v2558
    %t2564 = load i64, i64* %klen_v2557
    %rep.2563 = alloca i64
    store i64 0, i64* %rep.2563
    br label %loop.cond.2559
loop.cond.2559:
    %t2565 = load i64, i64* %rep.2563
    %t2566 = icmp slt i64 %t2565, %t2564
    br i1 %t2566, label %loop.body.2560, label %loop.end.2561
loop.body.2560:
    %t2567 = load i64, i64* %ks_handle_v2547
    %t2568 = load i64, i64* %ki_v2558
    %t2569 = call i64 @freak_llvm_array_get(i64 %t2567, i64 %t2568)
    %k_v2570 = alloca i64
    store i64 %t2569, i64* %k_v2570
    %t2571 = load i64, i64* %k_v2570
    %t2572 = load i64, i64* %key
    %t2573 = call i64 @freak_llvm_word_eq(i64 %t2571, i64 %t2572)
    %t2577 = icmp ne i64 %t2573, 0
    br i1 %t2577, label %if.then.2574, label %if.end.2576
if.then.2574:
    %t2578 = load i64, i64* %ch_handle_v2554
    %t2579 = load i64, i64* %ki_v2558
    %t2580 = call i64 @freak_llvm_array_get(i64 %t2578, i64 %t2579)
    %v_v2581 = alloca i64
    store i64 %t2580, i64* %v_v2581
    %t2582 = load i64, i64* %v_v2581
    %t2583 = call i64 @freak_llvm_word_to_int(i64 %t2582)
    ret i64 %t2583
    br label %if.end.2576
if.end.2576:
    %t2584 = load i64, i64* %ki_v2558
    %t2585 = add i64 %t2584, 1
    store i64 %t2585, i64* %ki_v2558
    br label %loop.inc.2562
loop.inc.2562:
    %t2586 = load i64, i64* %rep.2563
    %t2587 = add i64 %t2586, 1
    store i64 %t2587, i64* %rep.2563
    br label %loop.cond.2559
loop.end.2561:
    %t2588 = sub i64 0, 1
    ret i64 %t2588
    ret i64 0
}

define i64 @freak_json_obj_has(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2589 = load i64, i64* %handle
    %t2590 = load i64, i64* %key
    %t2591 = call i64 @freak_json_obj_get(i64 %t2589, i64 %t2590)
    %t2593 = icmp sge i64 %t2591, 0
    %t2592 = zext i1 %t2593 to i64
    ret i64 %t2592
    ret i64 0
}

define i64 @freak_json_obj_key_at(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2594 = load i64, i64* @g_json_keys
    %t2595 = load i64, i64* %handle
    %t2596 = call i64 @freak_llvm_array_get(i64 %t2594, i64 %t2595)
    %ks_v2597 = alloca i64
    store i64 %t2596, i64* %ks_v2597
    %t2598 = load i64, i64* %ks_v2597
    %t2599 = call i64 @freak_llvm_word_to_int(i64 %t2598)
    %ks_handle_v2600 = alloca i64
    store i64 %t2599, i64* %ks_handle_v2600
    %t2601 = load i64, i64* %ks_handle_v2600
    %t2602 = load i64, i64* %index
    %t2603 = call i64 @freak_llvm_array_get(i64 %t2601, i64 %t2602)
    ret i64 %t2603
    ret i64 0
}

define i64 @freak_json_cur() {
entry:
    %t2604 = load i64, i64* @g_json_pos
    %t2605 = load i64, i64* @g_json_len
    %t2607 = icmp sge i64 %t2604, %t2605
    %t2606 = zext i1 %t2607 to i64
    %t2611 = icmp ne i64 %t2606, 0
    br i1 %t2611, label %if.then.2608, label %if.end.2610
if.then.2608:
    %t2612 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.122, i64 0, i64 0
    %t2613 = ptrtoint i8* %t2612 to i64
    ret i64 %t2613
    br label %if.end.2610
if.end.2610:
    %t2614 = load i64, i64* @g_json_src
    %t2616 = load i64, i64* @g_json_pos
    %t2615 = call i64 @freak_llvm_word_char_at(i64 %t2614, i64 %t2616)
    ret i64 %t2615
    ret i64 0
}

define i64 @freak_json_advance() {
entry:
    %t2617 = call i64 @freak_json_cur()
    %c_v2618 = alloca i64
    store i64 %t2617, i64* %c_v2618
    %t2619 = load i64, i64* @g_json_pos
    %t2620 = add i64 %t2619, 1
    store i64 %t2620, i64* @g_json_pos
    %t2621 = load i64, i64* %c_v2618
    ret i64 %t2621
    ret i64 0
}

define void @freak_json_skip_ws() {
entry:
    br label %loop.cond.2622
loop.cond.2622:
    %t2625 = load i64, i64* @g_json_pos
    %t2626 = load i64, i64* @g_json_len
    %t2628 = icmp sge i64 %t2625, %t2626
    %t2627 = zext i1 %t2628 to i64
    %t2629 = icmp eq i64 %t2627, 0
    br i1 %t2629, label %loop.body.2623, label %loop.end.2624
loop.body.2623:
    %t2630 = call i64 @freak_json_cur()
    %c_v2631 = alloca i64
    store i64 %t2630, i64* %c_v2631
    %t2632 = load i64, i64* %c_v2631
    %t2633 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.123, i64 0, i64 0
    %t2634 = ptrtoint i8* %t2633 to i64
    %t2635 = call i64 @freak_llvm_word_neq(i64 %t2632, i64 %t2634)
    %t2636 = load i64, i64* %c_v2631
    %t2637 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.124, i64 0, i64 0
    %t2638 = ptrtoint i8* %t2637 to i64
    %t2639 = call i64 @freak_llvm_word_neq(i64 %t2636, i64 %t2638)
    %t2641 = icmp ne i64 %t2635, 0
    %t2642 = icmp ne i64 %t2639, 0
    %t2643 = and i1 %t2641, %t2642
    %t2640 = zext i1 %t2643 to i64
    %t2644 = load i64, i64* %c_v2631
    %t2645 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.125, i64 0, i64 0
    %t2646 = ptrtoint i8* %t2645 to i64
    %t2647 = call i64 @freak_llvm_word_neq(i64 %t2644, i64 %t2646)
    %t2649 = icmp ne i64 %t2640, 0
    %t2650 = icmp ne i64 %t2647, 0
    %t2651 = and i1 %t2649, %t2650
    %t2648 = zext i1 %t2651 to i64
    %t2652 = load i64, i64* %c_v2631
    %t2653 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.126, i64 0, i64 0
    %t2654 = ptrtoint i8* %t2653 to i64
    %t2655 = call i64 @freak_llvm_word_neq(i64 %t2652, i64 %t2654)
    %t2657 = icmp ne i64 %t2648, 0
    %t2658 = icmp ne i64 %t2655, 0
    %t2659 = and i1 %t2657, %t2658
    %t2656 = zext i1 %t2659 to i64
    %t2663 = icmp ne i64 %t2656, 0
    br i1 %t2663, label %if.then.2660, label %if.end.2662
if.then.2660:
    ret void
    br label %if.end.2662
if.end.2662:
    %t2664 = load i64, i64* @g_json_pos
    %t2665 = add i64 %t2664, 1
    store i64 %t2665, i64* @g_json_pos
    br label %loop.cond.2622
loop.end.2624:
    ret void
}

define void @freak_json_expect(i64 %arg_ch) {
entry:
    %ch = alloca i64
    store i64 %arg_ch, i64* %ch
    %t2666 = call i64 @freak_json_advance()
    %c_v2667 = alloca i64
    store i64 %t2666, i64* %c_v2667
    %t2668 = load i64, i64* %c_v2667
    %t2669 = load i64, i64* %ch
    %t2670 = call i64 @freak_llvm_word_neq(i64 %t2668, i64 %t2669)
    %t2674 = icmp ne i64 %t2670, 0
    br i1 %t2674, label %if.then.2671, label %if.end.2673
if.then.2671:
    %t2675 = getelementptr inbounds [29 x i8], [29 x i8]* @.str.127, i64 0, i64 0
    %t2676 = ptrtoint i8* %t2675 to i64
    %t2677 = load i64, i64* %ch
    %t2678 = call i64 @freak_llvm_word_concat(i64 %t2676, i64 %t2677)
    %t2679 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.128, i64 0, i64 0
    %t2680 = ptrtoint i8* %t2679 to i64
    %t2681 = call i64 @freak_llvm_word_concat(i64 %t2678, i64 %t2680)
    %t2682 = load i64, i64* %c_v2667
    %t2683 = call i64 @freak_llvm_word_concat(i64 %t2681, i64 %t2682)
    %t2684 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.129, i64 0, i64 0
    %t2685 = ptrtoint i8* %t2684 to i64
    %t2686 = call i64 @freak_llvm_word_concat(i64 %t2683, i64 %t2685)
    call void @freak_llvm_say(i64 %t2686)
    br label %if.end.2673
if.end.2673:
    ret void
}

define i64 @freak_json_parse_string() {
entry:
    %t2687 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.130, i64 0, i64 0
    %t2688 = ptrtoint i8* %t2687 to i64
    call void @freak_json_expect(i64 %t2688)
    %t2689 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.131, i64 0, i64 0
    %t2690 = ptrtoint i8* %t2689 to i64
    %ps_out_v2691 = alloca i64
    store i64 %t2690, i64* %ps_out_v2691
    br label %loop.cond.2692
loop.cond.2692:
    %t2695 = load i64, i64* @g_json_pos
    %t2696 = load i64, i64* @g_json_len
    %t2698 = icmp sge i64 %t2695, %t2696
    %t2697 = zext i1 %t2698 to i64
    %t2699 = icmp eq i64 %t2697, 0
    br i1 %t2699, label %loop.body.2693, label %loop.end.2694
loop.body.2693:
    %t2700 = call i64 @freak_json_advance()
    %c_v2701 = alloca i64
    store i64 %t2700, i64* %c_v2701
    %t2702 = load i64, i64* %c_v2701
    %t2703 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.132, i64 0, i64 0
    %t2704 = ptrtoint i8* %t2703 to i64
    %t2705 = call i64 @freak_llvm_word_eq(i64 %t2702, i64 %t2704)
    %t2709 = icmp ne i64 %t2705, 0
    br i1 %t2709, label %if.then.2706, label %if.end.2708
if.then.2706:
    %t2710 = load i64, i64* %ps_out_v2691
    ret i64 %t2710
    br label %if.end.2708
if.end.2708:
    %t2711 = load i64, i64* %c_v2701
    %t2712 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.133, i64 0, i64 0
    %t2713 = ptrtoint i8* %t2712 to i64
    %t2714 = call i64 @freak_llvm_word_eq(i64 %t2711, i64 %t2713)
    %t2718 = icmp ne i64 %t2714, 0
    br i1 %t2718, label %if.then.2715, label %if.else.2716
if.then.2715:
    %t2719 = call i64 @freak_json_advance()
    %esc_v2720 = alloca i64
    store i64 %t2719, i64* %esc_v2720
    %t2721 = load i64, i64* %esc_v2720
    %t2722 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.134, i64 0, i64 0
    %t2723 = ptrtoint i8* %t2722 to i64
    %t2724 = call i64 @freak_llvm_word_eq(i64 %t2721, i64 %t2723)
    %t2728 = icmp ne i64 %t2724, 0
    br i1 %t2728, label %if.then.2725, label %if.else.2726
if.then.2725:
    %t2729 = load i64, i64* %ps_out_v2691
    %t2730 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.135, i64 0, i64 0
    %t2731 = ptrtoint i8* %t2730 to i64
    %t2732 = call i64 @freak_llvm_word_concat(i64 %t2729, i64 %t2731)
    store i64 %t2732, i64* %ps_out_v2691
    br label %if.end.2727
if.else.2726:
    %t2733 = load i64, i64* %esc_v2720
    %t2734 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.136, i64 0, i64 0
    %t2735 = ptrtoint i8* %t2734 to i64
    %t2736 = call i64 @freak_llvm_word_eq(i64 %t2733, i64 %t2735)
    %t2740 = icmp ne i64 %t2736, 0
    br i1 %t2740, label %if.then.2737, label %if.else.2738
if.then.2737:
    %t2741 = load i64, i64* %ps_out_v2691
    %t2742 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.137, i64 0, i64 0
    %t2743 = ptrtoint i8* %t2742 to i64
    %t2744 = call i64 @freak_llvm_word_concat(i64 %t2741, i64 %t2743)
    store i64 %t2744, i64* %ps_out_v2691
    br label %if.end.2739
if.else.2738:
    %t2745 = load i64, i64* %esc_v2720
    %t2746 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.138, i64 0, i64 0
    %t2747 = ptrtoint i8* %t2746 to i64
    %t2748 = call i64 @freak_llvm_word_eq(i64 %t2745, i64 %t2747)
    %t2752 = icmp ne i64 %t2748, 0
    br i1 %t2752, label %if.then.2749, label %if.else.2750
if.then.2749:
    %t2753 = load i64, i64* %ps_out_v2691
    %t2754 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.139, i64 0, i64 0
    %t2755 = ptrtoint i8* %t2754 to i64
    %t2756 = call i64 @freak_llvm_word_concat(i64 %t2753, i64 %t2755)
    store i64 %t2756, i64* %ps_out_v2691
    br label %if.end.2751
if.else.2750:
    %t2757 = load i64, i64* %esc_v2720
    %t2758 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.140, i64 0, i64 0
    %t2759 = ptrtoint i8* %t2758 to i64
    %t2760 = call i64 @freak_llvm_word_eq(i64 %t2757, i64 %t2759)
    %t2764 = icmp ne i64 %t2760, 0
    br i1 %t2764, label %if.then.2761, label %if.else.2762
if.then.2761:
    %t2765 = load i64, i64* %ps_out_v2691
    %t2766 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.141, i64 0, i64 0
    %t2767 = ptrtoint i8* %t2766 to i64
    %t2768 = call i64 @freak_llvm_word_concat(i64 %t2765, i64 %t2767)
    store i64 %t2768, i64* %ps_out_v2691
    br label %if.end.2763
if.else.2762:
    %t2769 = load i64, i64* %esc_v2720
    %t2770 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.142, i64 0, i64 0
    %t2771 = ptrtoint i8* %t2770 to i64
    %t2772 = call i64 @freak_llvm_word_eq(i64 %t2769, i64 %t2771)
    %t2776 = icmp ne i64 %t2772, 0
    br i1 %t2776, label %if.then.2773, label %if.else.2774
if.then.2773:
    %t2777 = load i64, i64* %ps_out_v2691
    %t2778 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.143, i64 0, i64 0
    %t2779 = ptrtoint i8* %t2778 to i64
    %t2780 = call i64 @freak_llvm_word_concat(i64 %t2777, i64 %t2779)
    store i64 %t2780, i64* %ps_out_v2691
    br label %if.end.2775
if.else.2774:
    %t2781 = load i64, i64* %esc_v2720
    %t2782 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.144, i64 0, i64 0
    %t2783 = ptrtoint i8* %t2782 to i64
    %t2784 = call i64 @freak_llvm_word_eq(i64 %t2781, i64 %t2783)
    %t2788 = icmp ne i64 %t2784, 0
    br i1 %t2788, label %if.then.2785, label %if.else.2786
if.then.2785:
    %t2789 = load i64, i64* %ps_out_v2691
    %t2790 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.145, i64 0, i64 0
    %t2791 = ptrtoint i8* %t2790 to i64
    %t2792 = call i64 @freak_llvm_word_concat(i64 %t2789, i64 %t2791)
    store i64 %t2792, i64* %ps_out_v2691
    br label %if.end.2787
if.else.2786:
    %t2793 = load i64, i64* %ps_out_v2691
    %t2794 = load i64, i64* %esc_v2720
    %t2795 = call i64 @freak_llvm_word_concat(i64 %t2793, i64 %t2794)
    store i64 %t2795, i64* %ps_out_v2691
    br label %if.end.2787
if.end.2787:
    br label %if.end.2775
if.end.2775:
    br label %if.end.2763
if.end.2763:
    br label %if.end.2751
if.end.2751:
    br label %if.end.2739
if.end.2739:
    br label %if.end.2727
if.end.2727:
    br label %if.end.2717
if.else.2716:
    %t2796 = load i64, i64* %ps_out_v2691
    %t2797 = load i64, i64* %c_v2701
    %t2798 = call i64 @freak_llvm_word_concat(i64 %t2796, i64 %t2797)
    store i64 %t2798, i64* %ps_out_v2691
    br label %if.end.2717
if.end.2717:
    br label %loop.cond.2692
loop.end.2694:
    %t2799 = load i64, i64* %ps_out_v2691
    ret i64 %t2799
    ret i64 0
}

define i64 @freak_json_parse_number() {
entry:
    %t2800 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.146, i64 0, i64 0
    %t2801 = ptrtoint i8* %t2800 to i64
    %pn_out_v2802 = alloca i64
    store i64 %t2801, i64* %pn_out_v2802
    %t2803 = call i64 @freak_json_cur()
    %c_v2804 = alloca i64
    store i64 %t2803, i64* %c_v2804
    %t2805 = load i64, i64* %c_v2804
    %t2806 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.147, i64 0, i64 0
    %t2807 = ptrtoint i8* %t2806 to i64
    %t2808 = call i64 @freak_llvm_word_eq(i64 %t2805, i64 %t2807)
    %t2812 = icmp ne i64 %t2808, 0
    br i1 %t2812, label %if.then.2809, label %if.end.2811
if.then.2809:
    %t2813 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.148, i64 0, i64 0
    %t2814 = ptrtoint i8* %t2813 to i64
    store i64 %t2814, i64* %pn_out_v2802
    %t2815 = load i64, i64* @g_json_pos
    %t2816 = add i64 %t2815, 1
    store i64 %t2816, i64* @g_json_pos
    br label %if.end.2811
if.end.2811:
    br label %loop.cond.2817
loop.cond.2817:
    %t2820 = load i64, i64* @g_json_pos
    %t2821 = load i64, i64* @g_json_len
    %t2823 = icmp sge i64 %t2820, %t2821
    %t2822 = zext i1 %t2823 to i64
    %t2824 = icmp eq i64 %t2822, 0
    br i1 %t2824, label %loop.body.2818, label %loop.end.2819
loop.body.2818:
    %t2825 = call i64 @freak_json_cur()
    store i64 %t2825, i64* %c_v2804
    %t2826 = load i64, i64* %c_v2804
    %t2827 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.149, i64 0, i64 0
    %t2828 = ptrtoint i8* %t2827 to i64
    %t2829 = call i64 @freak_llvm_word_eq(i64 %t2826, i64 %t2828)
    %t2830 = load i64, i64* %c_v2804
    %t2831 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.150, i64 0, i64 0
    %t2832 = ptrtoint i8* %t2831 to i64
    %t2833 = call i64 @freak_llvm_word_eq(i64 %t2830, i64 %t2832)
    %t2835 = icmp ne i64 %t2829, 0
    %t2836 = icmp ne i64 %t2833, 0
    %t2837 = or i1 %t2835, %t2836
    %t2834 = zext i1 %t2837 to i64
    %t2838 = load i64, i64* %c_v2804
    %t2839 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.151, i64 0, i64 0
    %t2840 = ptrtoint i8* %t2839 to i64
    %t2841 = call i64 @freak_llvm_word_eq(i64 %t2838, i64 %t2840)
    %t2843 = icmp ne i64 %t2834, 0
    %t2844 = icmp ne i64 %t2841, 0
    %t2845 = or i1 %t2843, %t2844
    %t2842 = zext i1 %t2845 to i64
    %t2846 = load i64, i64* %c_v2804
    %t2847 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.152, i64 0, i64 0
    %t2848 = ptrtoint i8* %t2847 to i64
    %t2849 = call i64 @freak_llvm_word_eq(i64 %t2846, i64 %t2848)
    %t2851 = icmp ne i64 %t2842, 0
    %t2852 = icmp ne i64 %t2849, 0
    %t2853 = or i1 %t2851, %t2852
    %t2850 = zext i1 %t2853 to i64
    %t2854 = load i64, i64* %c_v2804
    %t2855 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.153, i64 0, i64 0
    %t2856 = ptrtoint i8* %t2855 to i64
    %t2857 = call i64 @freak_llvm_word_eq(i64 %t2854, i64 %t2856)
    %t2859 = icmp ne i64 %t2850, 0
    %t2860 = icmp ne i64 %t2857, 0
    %t2861 = or i1 %t2859, %t2860
    %t2858 = zext i1 %t2861 to i64
    %t2862 = load i64, i64* %c_v2804
    %t2863 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.154, i64 0, i64 0
    %t2864 = ptrtoint i8* %t2863 to i64
    %t2865 = call i64 @freak_llvm_word_eq(i64 %t2862, i64 %t2864)
    %t2867 = icmp ne i64 %t2858, 0
    %t2868 = icmp ne i64 %t2865, 0
    %t2869 = or i1 %t2867, %t2868
    %t2866 = zext i1 %t2869 to i64
    %t2870 = load i64, i64* %c_v2804
    %t2871 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.155, i64 0, i64 0
    %t2872 = ptrtoint i8* %t2871 to i64
    %t2873 = call i64 @freak_llvm_word_eq(i64 %t2870, i64 %t2872)
    %t2875 = icmp ne i64 %t2866, 0
    %t2876 = icmp ne i64 %t2873, 0
    %t2877 = or i1 %t2875, %t2876
    %t2874 = zext i1 %t2877 to i64
    %t2878 = load i64, i64* %c_v2804
    %t2879 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.156, i64 0, i64 0
    %t2880 = ptrtoint i8* %t2879 to i64
    %t2881 = call i64 @freak_llvm_word_eq(i64 %t2878, i64 %t2880)
    %t2883 = icmp ne i64 %t2874, 0
    %t2884 = icmp ne i64 %t2881, 0
    %t2885 = or i1 %t2883, %t2884
    %t2882 = zext i1 %t2885 to i64
    %t2886 = load i64, i64* %c_v2804
    %t2887 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.157, i64 0, i64 0
    %t2888 = ptrtoint i8* %t2887 to i64
    %t2889 = call i64 @freak_llvm_word_eq(i64 %t2886, i64 %t2888)
    %t2891 = icmp ne i64 %t2882, 0
    %t2892 = icmp ne i64 %t2889, 0
    %t2893 = or i1 %t2891, %t2892
    %t2890 = zext i1 %t2893 to i64
    %t2894 = load i64, i64* %c_v2804
    %t2895 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.158, i64 0, i64 0
    %t2896 = ptrtoint i8* %t2895 to i64
    %t2897 = call i64 @freak_llvm_word_eq(i64 %t2894, i64 %t2896)
    %t2899 = icmp ne i64 %t2890, 0
    %t2900 = icmp ne i64 %t2897, 0
    %t2901 = or i1 %t2899, %t2900
    %t2898 = zext i1 %t2901 to i64
    %t2902 = load i64, i64* %c_v2804
    %t2903 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.159, i64 0, i64 0
    %t2904 = ptrtoint i8* %t2903 to i64
    %t2905 = call i64 @freak_llvm_word_eq(i64 %t2902, i64 %t2904)
    %t2907 = icmp ne i64 %t2898, 0
    %t2908 = icmp ne i64 %t2905, 0
    %t2909 = or i1 %t2907, %t2908
    %t2906 = zext i1 %t2909 to i64
    %t2913 = icmp ne i64 %t2906, 0
    br i1 %t2913, label %if.then.2910, label %if.else.2911
if.then.2910:
    %t2914 = load i64, i64* %pn_out_v2802
    %t2915 = load i64, i64* %c_v2804
    %t2916 = call i64 @freak_llvm_word_concat(i64 %t2914, i64 %t2915)
    store i64 %t2916, i64* %pn_out_v2802
    %t2917 = load i64, i64* @g_json_pos
    %t2918 = add i64 %t2917, 1
    store i64 %t2918, i64* @g_json_pos
    br label %if.end.2912
if.else.2911:
    %t2919 = load i64, i64* %pn_out_v2802
    ret i64 %t2919
    br label %if.end.2912
if.end.2912:
    br label %loop.cond.2817
loop.end.2819:
    %t2920 = load i64, i64* %pn_out_v2802
    ret i64 %t2920
    ret i64 0
}

define i64 @freak_json_try_keyword(i64 %arg_kw) {
entry:
    %kw = alloca i64
    store i64 %arg_kw, i64* %kw
    %t2921 = load i64, i64* %kw
    %t2922 = call i64 @freak_llvm_word_length(i64 %t2921)
    %kwlen_v2923 = alloca i64
    store i64 %t2922, i64* %kwlen_v2923
    %t2924 = load i64, i64* @g_json_pos
    %t2925 = load i64, i64* %kwlen_v2923
    %t2926 = add i64 %t2924, %t2925
    %t2927 = load i64, i64* @g_json_len
    %t2929 = icmp sgt i64 %t2926, %t2927
    %t2928 = zext i1 %t2929 to i64
    %t2933 = icmp ne i64 %t2928, 0
    br i1 %t2933, label %if.then.2930, label %if.end.2932
if.then.2930:
    ret i64 0
    br label %if.end.2932
if.end.2932:
    %ki_v2934 = alloca i64
    store i64 0, i64* %ki_v2934
    %t2940 = load i64, i64* %kwlen_v2923
    %rep.2939 = alloca i64
    store i64 0, i64* %rep.2939
    br label %loop.cond.2935
loop.cond.2935:
    %t2941 = load i64, i64* %rep.2939
    %t2942 = icmp slt i64 %t2941, %t2940
    br i1 %t2942, label %loop.body.2936, label %loop.end.2937
loop.body.2936:
    %t2943 = load i64, i64* @g_json_src
    %t2945 = load i64, i64* @g_json_pos
    %t2946 = load i64, i64* %ki_v2934
    %t2947 = add i64 %t2945, %t2946
    %t2944 = call i64 @freak_llvm_word_char_at(i64 %t2943, i64 %t2947)
    %t2948 = load i64, i64* %kw
    %t2950 = load i64, i64* %ki_v2934
    %t2949 = call i64 @freak_llvm_word_char_at(i64 %t2948, i64 %t2950)
    %t2951 = call i64 @freak_llvm_word_neq(i64 %t2944, i64 %t2949)
    %t2955 = icmp ne i64 %t2951, 0
    br i1 %t2955, label %if.then.2952, label %if.end.2954
if.then.2952:
    ret i64 0
    br label %if.end.2954
if.end.2954:
    %t2956 = load i64, i64* %ki_v2934
    %t2957 = add i64 %t2956, 1
    store i64 %t2957, i64* %ki_v2934
    br label %loop.inc.2938
loop.inc.2938:
    %t2958 = load i64, i64* %rep.2939
    %t2959 = add i64 %t2958, 1
    store i64 %t2959, i64* %rep.2939
    br label %loop.cond.2935
loop.end.2937:
    %t2960 = load i64, i64* %kwlen_v2923
    %t2961 = load i64, i64* @g_json_pos
    %t2962 = add i64 %t2961, %t2960
    store i64 %t2962, i64* @g_json_pos
    ret i64 1
    ret i64 0
}

define i64 @freak_json_parse_value() {
entry:
    call void @freak_json_skip_ws()
    %t2963 = call i64 @freak_json_cur()
    %c_v2964 = alloca i64
    store i64 %t2963, i64* %c_v2964
    %t2965 = load i64, i64* %c_v2964
    %t2966 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.160, i64 0, i64 0
    %t2967 = ptrtoint i8* %t2966 to i64
    %t2968 = call i64 @freak_llvm_word_eq(i64 %t2965, i64 %t2967)
    %t2972 = icmp ne i64 %t2968, 0
    br i1 %t2972, label %if.then.2969, label %if.end.2971
if.then.2969:
    %t2973 = call i64 @freak_json_parse_string()
    %sv_v2974 = alloca i64
    store i64 %t2973, i64* %sv_v2974
    %t2975 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.161, i64 0, i64 0
    %t2976 = ptrtoint i8* %t2975 to i64
    %t2977 = load i64, i64* %sv_v2974
    %t2978 = call i64 @freak_json_alloc(i64 %t2976, i64 %t2977)
    ret i64 %t2978
    br label %if.end.2971
if.end.2971:
    %t2979 = load i64, i64* %c_v2964
    %t2980 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.162, i64 0, i64 0
    %t2981 = ptrtoint i8* %t2980 to i64
    %t2982 = call i64 @freak_llvm_word_eq(i64 %t2979, i64 %t2981)
    %t2983 = load i64, i64* %c_v2964
    %t2984 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.163, i64 0, i64 0
    %t2985 = ptrtoint i8* %t2984 to i64
    %t2986 = call i64 @freak_llvm_word_eq(i64 %t2983, i64 %t2985)
    %t2988 = icmp ne i64 %t2982, 0
    %t2989 = icmp ne i64 %t2986, 0
    %t2990 = or i1 %t2988, %t2989
    %t2987 = zext i1 %t2990 to i64
    %t2991 = load i64, i64* %c_v2964
    %t2992 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.164, i64 0, i64 0
    %t2993 = ptrtoint i8* %t2992 to i64
    %t2994 = call i64 @freak_llvm_word_eq(i64 %t2991, i64 %t2993)
    %t2996 = icmp ne i64 %t2987, 0
    %t2997 = icmp ne i64 %t2994, 0
    %t2998 = or i1 %t2996, %t2997
    %t2995 = zext i1 %t2998 to i64
    %t2999 = load i64, i64* %c_v2964
    %t3000 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.165, i64 0, i64 0
    %t3001 = ptrtoint i8* %t3000 to i64
    %t3002 = call i64 @freak_llvm_word_eq(i64 %t2999, i64 %t3001)
    %t3004 = icmp ne i64 %t2995, 0
    %t3005 = icmp ne i64 %t3002, 0
    %t3006 = or i1 %t3004, %t3005
    %t3003 = zext i1 %t3006 to i64
    %t3007 = load i64, i64* %c_v2964
    %t3008 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.166, i64 0, i64 0
    %t3009 = ptrtoint i8* %t3008 to i64
    %t3010 = call i64 @freak_llvm_word_eq(i64 %t3007, i64 %t3009)
    %t3012 = icmp ne i64 %t3003, 0
    %t3013 = icmp ne i64 %t3010, 0
    %t3014 = or i1 %t3012, %t3013
    %t3011 = zext i1 %t3014 to i64
    %t3015 = load i64, i64* %c_v2964
    %t3016 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.167, i64 0, i64 0
    %t3017 = ptrtoint i8* %t3016 to i64
    %t3018 = call i64 @freak_llvm_word_eq(i64 %t3015, i64 %t3017)
    %t3020 = icmp ne i64 %t3011, 0
    %t3021 = icmp ne i64 %t3018, 0
    %t3022 = or i1 %t3020, %t3021
    %t3019 = zext i1 %t3022 to i64
    %t3023 = load i64, i64* %c_v2964
    %t3024 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.168, i64 0, i64 0
    %t3025 = ptrtoint i8* %t3024 to i64
    %t3026 = call i64 @freak_llvm_word_eq(i64 %t3023, i64 %t3025)
    %t3028 = icmp ne i64 %t3019, 0
    %t3029 = icmp ne i64 %t3026, 0
    %t3030 = or i1 %t3028, %t3029
    %t3027 = zext i1 %t3030 to i64
    %t3031 = load i64, i64* %c_v2964
    %t3032 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.169, i64 0, i64 0
    %t3033 = ptrtoint i8* %t3032 to i64
    %t3034 = call i64 @freak_llvm_word_eq(i64 %t3031, i64 %t3033)
    %t3036 = icmp ne i64 %t3027, 0
    %t3037 = icmp ne i64 %t3034, 0
    %t3038 = or i1 %t3036, %t3037
    %t3035 = zext i1 %t3038 to i64
    %t3039 = load i64, i64* %c_v2964
    %t3040 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.170, i64 0, i64 0
    %t3041 = ptrtoint i8* %t3040 to i64
    %t3042 = call i64 @freak_llvm_word_eq(i64 %t3039, i64 %t3041)
    %t3044 = icmp ne i64 %t3035, 0
    %t3045 = icmp ne i64 %t3042, 0
    %t3046 = or i1 %t3044, %t3045
    %t3043 = zext i1 %t3046 to i64
    %t3047 = load i64, i64* %c_v2964
    %t3048 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.171, i64 0, i64 0
    %t3049 = ptrtoint i8* %t3048 to i64
    %t3050 = call i64 @freak_llvm_word_eq(i64 %t3047, i64 %t3049)
    %t3052 = icmp ne i64 %t3043, 0
    %t3053 = icmp ne i64 %t3050, 0
    %t3054 = or i1 %t3052, %t3053
    %t3051 = zext i1 %t3054 to i64
    %t3055 = load i64, i64* %c_v2964
    %t3056 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.172, i64 0, i64 0
    %t3057 = ptrtoint i8* %t3056 to i64
    %t3058 = call i64 @freak_llvm_word_eq(i64 %t3055, i64 %t3057)
    %t3060 = icmp ne i64 %t3051, 0
    %t3061 = icmp ne i64 %t3058, 0
    %t3062 = or i1 %t3060, %t3061
    %t3059 = zext i1 %t3062 to i64
    %t3066 = icmp ne i64 %t3059, 0
    br i1 %t3066, label %if.then.3063, label %if.end.3065
if.then.3063:
    %t3067 = call i64 @freak_json_parse_number()
    %nv_v3068 = alloca i64
    store i64 %t3067, i64* %nv_v3068
    %t3069 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.173, i64 0, i64 0
    %t3070 = ptrtoint i8* %t3069 to i64
    %t3071 = load i64, i64* %nv_v3068
    %t3072 = call i64 @freak_json_alloc(i64 %t3070, i64 %t3071)
    ret i64 %t3072
    br label %if.end.3065
if.end.3065:
    %t3073 = load i64, i64* %c_v2964
    %t3074 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.174, i64 0, i64 0
    %t3075 = ptrtoint i8* %t3074 to i64
    %t3076 = call i64 @freak_llvm_word_eq(i64 %t3073, i64 %t3075)
    %t3080 = icmp ne i64 %t3076, 0
    br i1 %t3080, label %if.then.3077, label %if.end.3079
if.then.3077:
    %t3081 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.175, i64 0, i64 0
    %t3082 = ptrtoint i8* %t3081 to i64
    %t3083 = call i64 @freak_json_try_keyword(i64 %t3082)
    %t3087 = icmp ne i64 %t3083, 0
    br i1 %t3087, label %if.then.3084, label %if.end.3086
if.then.3084:
    %t3088 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.176, i64 0, i64 0
    %t3089 = ptrtoint i8* %t3088 to i64
    %t3090 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.177, i64 0, i64 0
    %t3091 = ptrtoint i8* %t3090 to i64
    %t3092 = call i64 @freak_json_alloc(i64 %t3089, i64 %t3091)
    ret i64 %t3092
    br label %if.end.3086
if.end.3086:
    br label %if.end.3079
if.end.3079:
    %t3093 = load i64, i64* %c_v2964
    %t3094 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.178, i64 0, i64 0
    %t3095 = ptrtoint i8* %t3094 to i64
    %t3096 = call i64 @freak_llvm_word_eq(i64 %t3093, i64 %t3095)
    %t3100 = icmp ne i64 %t3096, 0
    br i1 %t3100, label %if.then.3097, label %if.end.3099
if.then.3097:
    %t3101 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.179, i64 0, i64 0
    %t3102 = ptrtoint i8* %t3101 to i64
    %t3103 = call i64 @freak_json_try_keyword(i64 %t3102)
    %t3107 = icmp ne i64 %t3103, 0
    br i1 %t3107, label %if.then.3104, label %if.end.3106
if.then.3104:
    %t3108 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.180, i64 0, i64 0
    %t3109 = ptrtoint i8* %t3108 to i64
    %t3110 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.181, i64 0, i64 0
    %t3111 = ptrtoint i8* %t3110 to i64
    %t3112 = call i64 @freak_json_alloc(i64 %t3109, i64 %t3111)
    ret i64 %t3112
    br label %if.end.3106
if.end.3106:
    br label %if.end.3099
if.end.3099:
    %t3113 = load i64, i64* %c_v2964
    %t3114 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.182, i64 0, i64 0
    %t3115 = ptrtoint i8* %t3114 to i64
    %t3116 = call i64 @freak_llvm_word_eq(i64 %t3113, i64 %t3115)
    %t3120 = icmp ne i64 %t3116, 0
    br i1 %t3120, label %if.then.3117, label %if.end.3119
if.then.3117:
    %t3121 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.183, i64 0, i64 0
    %t3122 = ptrtoint i8* %t3121 to i64
    %t3123 = call i64 @freak_json_try_keyword(i64 %t3122)
    %t3127 = icmp ne i64 %t3123, 0
    br i1 %t3127, label %if.then.3124, label %if.end.3126
if.then.3124:
    %t3128 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.184, i64 0, i64 0
    %t3129 = ptrtoint i8* %t3128 to i64
    %t3130 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.185, i64 0, i64 0
    %t3131 = ptrtoint i8* %t3130 to i64
    %t3132 = call i64 @freak_json_alloc(i64 %t3129, i64 %t3131)
    ret i64 %t3132
    br label %if.end.3126
if.end.3126:
    br label %if.end.3119
if.end.3119:
    %t3133 = load i64, i64* %c_v2964
    %t3134 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.186, i64 0, i64 0
    %t3135 = ptrtoint i8* %t3134 to i64
    %t3136 = call i64 @freak_llvm_word_eq(i64 %t3133, i64 %t3135)
    %t3140 = icmp ne i64 %t3136, 0
    br i1 %t3140, label %if.then.3137, label %if.end.3139
if.then.3137:
    %t3141 = load i64, i64* @g_json_pos
    %t3142 = add i64 %t3141, 1
    store i64 %t3142, i64* @g_json_pos
    %t3143 = call i64 @freak_llvm_array_new()
    %arr_children_v3144 = alloca i64
    store i64 %t3143, i64* %arr_children_v3144
    %t3145 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.187, i64 0, i64 0
    %t3146 = ptrtoint i8* %t3145 to i64
    %t3147 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.188, i64 0, i64 0
    %t3148 = ptrtoint i8* %t3147 to i64
    %t3149 = call i64 @freak_json_alloc(i64 %t3146, i64 %t3148)
    %arr_handle_v3150 = alloca i64
    store i64 %t3149, i64* %arr_handle_v3150
    %t3151 = load i64, i64* @g_json_children
    %t3152 = load i64, i64* %arr_handle_v3150
    %t3153 = load i64, i64* %arr_children_v3144
    %t3154 = call i64 @freak_llvm_word_from_int(i64 %t3153)
    call void @freak_llvm_array_set(i64 %t3151, i64 %t3152, i64 %t3154)
    call void @freak_json_skip_ws()
    %t3155 = call i64 @freak_json_cur()
    %t3156 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.189, i64 0, i64 0
    %t3157 = ptrtoint i8* %t3156 to i64
    %t3158 = call i64 @freak_llvm_word_neq(i64 %t3155, i64 %t3157)
    %t3162 = icmp ne i64 %t3158, 0
    br i1 %t3162, label %if.then.3159, label %if.end.3161
if.then.3159:
    %t3163 = call i64 @freak_json_parse_value()
    %first_val_v3164 = alloca i64
    store i64 %t3163, i64* %first_val_v3164
    %t3165 = load i64, i64* %arr_children_v3144
    %t3166 = load i64, i64* %first_val_v3164
    %t3167 = call i64 @freak_llvm_word_from_int(i64 %t3166)
    call void @freak_llvm_array_push(i64 %t3165, i64 %t3167)
    call void @freak_json_skip_ws()
    br label %loop.cond.3168
loop.cond.3168:
    %t3171 = call i64 @freak_json_cur()
    %t3172 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.190, i64 0, i64 0
    %t3173 = ptrtoint i8* %t3172 to i64
    %t3174 = call i64 @freak_llvm_word_neq(i64 %t3171, i64 %t3173)
    %t3175 = icmp eq i64 %t3174, 0
    br i1 %t3175, label %loop.body.3169, label %loop.end.3170
loop.body.3169:
    %t3176 = load i64, i64* @g_json_pos
    %t3177 = add i64 %t3176, 1
    store i64 %t3177, i64* @g_json_pos
    %t3178 = call i64 @freak_json_parse_value()
    %next_val_v3179 = alloca i64
    store i64 %t3178, i64* %next_val_v3179
    %t3180 = load i64, i64* %arr_children_v3144
    %t3181 = load i64, i64* %next_val_v3179
    %t3182 = call i64 @freak_llvm_word_from_int(i64 %t3181)
    call void @freak_llvm_array_push(i64 %t3180, i64 %t3182)
    call void @freak_json_skip_ws()
    br label %loop.cond.3168
loop.end.3170:
    br label %if.end.3161
if.end.3161:
    %t3183 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.191, i64 0, i64 0
    %t3184 = ptrtoint i8* %t3183 to i64
    call void @freak_json_expect(i64 %t3184)
    %t3185 = load i64, i64* %arr_handle_v3150
    ret i64 %t3185
    br label %if.end.3139
if.end.3139:
    %t3186 = load i64, i64* %c_v2964
    %t3187 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.192, i64 0, i64 0
    %t3188 = ptrtoint i8* %t3187 to i64
    %t3189 = call i64 @freak_llvm_word_eq(i64 %t3186, i64 %t3188)
    %t3193 = icmp ne i64 %t3189, 0
    br i1 %t3193, label %if.then.3190, label %if.end.3192
if.then.3190:
    %t3194 = load i64, i64* @g_json_pos
    %t3195 = add i64 %t3194, 1
    store i64 %t3195, i64* @g_json_pos
    %t3196 = call i64 @freak_llvm_array_new()
    %obj_children_v3197 = alloca i64
    store i64 %t3196, i64* %obj_children_v3197
    %t3198 = call i64 @freak_llvm_array_new()
    %obj_keys_v3199 = alloca i64
    store i64 %t3198, i64* %obj_keys_v3199
    %t3200 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.193, i64 0, i64 0
    %t3201 = ptrtoint i8* %t3200 to i64
    %t3202 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.194, i64 0, i64 0
    %t3203 = ptrtoint i8* %t3202 to i64
    %t3204 = call i64 @freak_json_alloc(i64 %t3201, i64 %t3203)
    %obj_handle_v3205 = alloca i64
    store i64 %t3204, i64* %obj_handle_v3205
    %t3206 = load i64, i64* @g_json_children
    %t3207 = load i64, i64* %obj_handle_v3205
    %t3208 = load i64, i64* %obj_children_v3197
    %t3209 = call i64 @freak_llvm_word_from_int(i64 %t3208)
    call void @freak_llvm_array_set(i64 %t3206, i64 %t3207, i64 %t3209)
    %t3210 = load i64, i64* @g_json_keys
    %t3211 = load i64, i64* %obj_handle_v3205
    %t3212 = load i64, i64* %obj_keys_v3199
    %t3213 = call i64 @freak_llvm_word_from_int(i64 %t3212)
    call void @freak_llvm_array_set(i64 %t3210, i64 %t3211, i64 %t3213)
    call void @freak_json_skip_ws()
    %t3214 = call i64 @freak_json_cur()
    %t3215 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.195, i64 0, i64 0
    %t3216 = ptrtoint i8* %t3215 to i64
    %t3217 = call i64 @freak_llvm_word_neq(i64 %t3214, i64 %t3216)
    %t3221 = icmp ne i64 %t3217, 0
    br i1 %t3221, label %if.then.3218, label %if.end.3220
if.then.3218:
    %t3222 = call i64 @freak_json_parse_string()
    %k1_v3223 = alloca i64
    store i64 %t3222, i64* %k1_v3223
    call void @freak_json_skip_ws()
    %t3224 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.196, i64 0, i64 0
    %t3225 = ptrtoint i8* %t3224 to i64
    call void @freak_json_expect(i64 %t3225)
    %t3226 = call i64 @freak_json_parse_value()
    %v1_v3227 = alloca i64
    store i64 %t3226, i64* %v1_v3227
    %t3228 = load i64, i64* %obj_keys_v3199
    %t3229 = load i64, i64* %k1_v3223
    call void @freak_llvm_array_push(i64 %t3228, i64 %t3229)
    %t3230 = load i64, i64* %obj_children_v3197
    %t3231 = load i64, i64* %v1_v3227
    %t3232 = call i64 @freak_llvm_word_from_int(i64 %t3231)
    call void @freak_llvm_array_push(i64 %t3230, i64 %t3232)
    call void @freak_json_skip_ws()
    br label %loop.cond.3233
loop.cond.3233:
    %t3236 = call i64 @freak_json_cur()
    %t3237 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.197, i64 0, i64 0
    %t3238 = ptrtoint i8* %t3237 to i64
    %t3239 = call i64 @freak_llvm_word_neq(i64 %t3236, i64 %t3238)
    %t3240 = icmp eq i64 %t3239, 0
    br i1 %t3240, label %loop.body.3234, label %loop.end.3235
loop.body.3234:
    %t3241 = load i64, i64* @g_json_pos
    %t3242 = add i64 %t3241, 1
    store i64 %t3242, i64* @g_json_pos
    call void @freak_json_skip_ws()
    %t3243 = call i64 @freak_json_parse_string()
    %kn_v3244 = alloca i64
    store i64 %t3243, i64* %kn_v3244
    call void @freak_json_skip_ws()
    %t3245 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.198, i64 0, i64 0
    %t3246 = ptrtoint i8* %t3245 to i64
    call void @freak_json_expect(i64 %t3246)
    %t3247 = call i64 @freak_json_parse_value()
    %vn_v3248 = alloca i64
    store i64 %t3247, i64* %vn_v3248
    %t3249 = load i64, i64* %obj_keys_v3199
    %t3250 = load i64, i64* %kn_v3244
    call void @freak_llvm_array_push(i64 %t3249, i64 %t3250)
    %t3251 = load i64, i64* %obj_children_v3197
    %t3252 = load i64, i64* %vn_v3248
    %t3253 = call i64 @freak_llvm_word_from_int(i64 %t3252)
    call void @freak_llvm_array_push(i64 %t3251, i64 %t3253)
    call void @freak_json_skip_ws()
    br label %loop.cond.3233
loop.end.3235:
    br label %if.end.3220
if.end.3220:
    %t3254 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.199, i64 0, i64 0
    %t3255 = ptrtoint i8* %t3254 to i64
    call void @freak_json_expect(i64 %t3255)
    %t3256 = load i64, i64* %obj_handle_v3205
    ret i64 %t3256
    br label %if.end.3192
if.end.3192:
    %t3257 = getelementptr inbounds [31 x i8], [31 x i8]* @.str.200, i64 0, i64 0
    %t3258 = ptrtoint i8* %t3257 to i64
    %t3259 = load i64, i64* %c_v2964
    %t3260 = call i64 @freak_llvm_word_concat(i64 %t3258, i64 %t3259)
    %t3261 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.201, i64 0, i64 0
    %t3262 = ptrtoint i8* %t3261 to i64
    %t3263 = call i64 @freak_llvm_word_concat(i64 %t3260, i64 %t3262)
    call void @freak_llvm_say(i64 %t3263)
    %t3264 = sub i64 0, 1
    ret i64 %t3264
    ret i64 0
}

define i64 @freak_json_parse(i64 %arg_source) {
entry:
    %source = alloca i64
    store i64 %arg_source, i64* %source
    call void @freak_json_init()
    %t3265 = load i64, i64* %source
    store i64 %t3265, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    %t3266 = load i64, i64* %source
    %t3267 = call i64 @freak_llvm_word_length(i64 %t3266)
    store i64 %t3267, i64* @g_json_len
    %t3268 = call i64 @freak_json_parse_value()
    ret i64 %t3268
    ret i64 0
}

define i64 @freak_json_stringify(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t3269 = load i64, i64* %handle
    %t3271 = icmp slt i64 %t3269, 0
    %t3270 = zext i1 %t3271 to i64
    %t3275 = icmp ne i64 %t3270, 0
    br i1 %t3275, label %if.then.3272, label %if.end.3274
if.then.3272:
    %t3276 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.202, i64 0, i64 0
    %t3277 = ptrtoint i8* %t3276 to i64
    ret i64 %t3277
    br label %if.end.3274
if.end.3274:
    %t3278 = load i64, i64* @g_json_types
    %t3279 = load i64, i64* %handle
    %t3280 = call i64 @freak_llvm_array_get(i64 %t3278, i64 %t3279)
    %t_v3281 = alloca i64
    store i64 %t3280, i64* %t_v3281
    %t3282 = load i64, i64* %t_v3281
    %t3283 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.203, i64 0, i64 0
    %t3284 = ptrtoint i8* %t3283 to i64
    %t3285 = call i64 @freak_llvm_word_eq(i64 %t3282, i64 %t3284)
    %t3289 = icmp ne i64 %t3285, 0
    br i1 %t3289, label %if.then.3286, label %if.end.3288
if.then.3286:
    %t3290 = load i64, i64* @g_json_vals
    %t3291 = load i64, i64* %handle
    %t3292 = call i64 @freak_llvm_array_get(i64 %t3290, i64 %t3291)
    %sv_v3293 = alloca i64
    store i64 %t3292, i64* %sv_v3293
    %t3294 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.204, i64 0, i64 0
    %t3295 = ptrtoint i8* %t3294 to i64
    %t3296 = load i64, i64* %sv_v3293
    %t3297 = call i64 @freak_llvm_word_concat(i64 %t3295, i64 %t3296)
    %t3298 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.205, i64 0, i64 0
    %t3299 = ptrtoint i8* %t3298 to i64
    %t3300 = call i64 @freak_llvm_word_concat(i64 %t3297, i64 %t3299)
    ret i64 %t3300
    br label %if.end.3288
if.end.3288:
    %t3301 = load i64, i64* %t_v3281
    %t3302 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.206, i64 0, i64 0
    %t3303 = ptrtoint i8* %t3302 to i64
    %t3304 = call i64 @freak_llvm_word_eq(i64 %t3301, i64 %t3303)
    %t3308 = icmp ne i64 %t3304, 0
    br i1 %t3308, label %if.then.3305, label %if.end.3307
if.then.3305:
    %t3309 = load i64, i64* @g_json_vals
    %t3310 = load i64, i64* %handle
    %t3311 = call i64 @freak_llvm_array_get(i64 %t3309, i64 %t3310)
    ret i64 %t3311
    br label %if.end.3307
if.end.3307:
    %t3312 = load i64, i64* %t_v3281
    %t3313 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.207, i64 0, i64 0
    %t3314 = ptrtoint i8* %t3313 to i64
    %t3315 = call i64 @freak_llvm_word_eq(i64 %t3312, i64 %t3314)
    %t3319 = icmp ne i64 %t3315, 0
    br i1 %t3319, label %if.then.3316, label %if.end.3318
if.then.3316:
    %t3320 = load i64, i64* @g_json_vals
    %t3321 = load i64, i64* %handle
    %t3322 = call i64 @freak_llvm_array_get(i64 %t3320, i64 %t3321)
    ret i64 %t3322
    br label %if.end.3318
if.end.3318:
    %t3323 = load i64, i64* %t_v3281
    %t3324 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.208, i64 0, i64 0
    %t3325 = ptrtoint i8* %t3324 to i64
    %t3326 = call i64 @freak_llvm_word_eq(i64 %t3323, i64 %t3325)
    %t3330 = icmp ne i64 %t3326, 0
    br i1 %t3330, label %if.then.3327, label %if.end.3329
if.then.3327:
    %t3331 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.209, i64 0, i64 0
    %t3332 = ptrtoint i8* %t3331 to i64
    ret i64 %t3332
    br label %if.end.3329
if.end.3329:
    %t3333 = load i64, i64* %t_v3281
    %t3334 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.210, i64 0, i64 0
    %t3335 = ptrtoint i8* %t3334 to i64
    %t3336 = call i64 @freak_llvm_word_eq(i64 %t3333, i64 %t3335)
    %t3340 = icmp ne i64 %t3336, 0
    br i1 %t3340, label %if.then.3337, label %if.end.3339
if.then.3337:
    %t3341 = load i64, i64* %handle
    %t3342 = call i64 @freak_json_arr_len(i64 %t3341)
    %alen_v3343 = alloca i64
    store i64 %t3342, i64* %alen_v3343
    %t3344 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.211, i64 0, i64 0
    %t3345 = ptrtoint i8* %t3344 to i64
    %a_out_v3346 = alloca i64
    store i64 %t3345, i64* %a_out_v3346
    %ai_v3347 = alloca i64
    store i64 0, i64* %ai_v3347
    %t3353 = load i64, i64* %alen_v3343
    %rep.3352 = alloca i64
    store i64 0, i64* %rep.3352
    br label %loop.cond.3348
loop.cond.3348:
    %t3354 = load i64, i64* %rep.3352
    %t3355 = icmp slt i64 %t3354, %t3353
    br i1 %t3355, label %loop.body.3349, label %loop.end.3350
loop.body.3349:
    %t3356 = load i64, i64* %ai_v3347
    %t3358 = icmp sgt i64 %t3356, 0
    %t3357 = zext i1 %t3358 to i64
    %t3362 = icmp ne i64 %t3357, 0
    br i1 %t3362, label %if.then.3359, label %if.end.3361
if.then.3359:
    %t3363 = load i64, i64* %a_out_v3346
    %t3364 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.212, i64 0, i64 0
    %t3365 = ptrtoint i8* %t3364 to i64
    %t3366 = call i64 @freak_llvm_word_concat(i64 %t3363, i64 %t3365)
    store i64 %t3366, i64* %a_out_v3346
    br label %if.end.3361
if.end.3361:
    %t3367 = load i64, i64* %handle
    %t3368 = load i64, i64* %ai_v3347
    %t3369 = call i64 @freak_json_arr_get(i64 %t3367, i64 %t3368)
    %child_v3370 = alloca i64
    store i64 %t3369, i64* %child_v3370
    %t3371 = load i64, i64* %a_out_v3346
    %t3372 = load i64, i64* %child_v3370
    %t3373 = call i64 @freak_json_stringify(i64 %t3372)
    %t3374 = call i64 @freak_llvm_word_concat(i64 %t3371, i64 %t3373)
    store i64 %t3374, i64* %a_out_v3346
    %t3375 = load i64, i64* %ai_v3347
    %t3376 = add i64 %t3375, 1
    store i64 %t3376, i64* %ai_v3347
    br label %loop.inc.3351
loop.inc.3351:
    %t3377 = load i64, i64* %rep.3352
    %t3378 = add i64 %t3377, 1
    store i64 %t3378, i64* %rep.3352
    br label %loop.cond.3348
loop.end.3350:
    %t3379 = load i64, i64* %a_out_v3346
    %t3380 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.213, i64 0, i64 0
    %t3381 = ptrtoint i8* %t3380 to i64
    %t3382 = call i64 @freak_llvm_word_concat(i64 %t3379, i64 %t3381)
    ret i64 %t3382
    br label %if.end.3339
if.end.3339:
    %t3383 = load i64, i64* %t_v3281
    %t3384 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.214, i64 0, i64 0
    %t3385 = ptrtoint i8* %t3384 to i64
    %t3386 = call i64 @freak_llvm_word_eq(i64 %t3383, i64 %t3385)
    %t3390 = icmp ne i64 %t3386, 0
    br i1 %t3390, label %if.then.3387, label %if.end.3389
if.then.3387:
    %t3391 = load i64, i64* %handle
    %t3392 = call i64 @freak_json_obj_len(i64 %t3391)
    %olen_v3393 = alloca i64
    store i64 %t3392, i64* %olen_v3393
    %t3394 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.215, i64 0, i64 0
    %t3395 = ptrtoint i8* %t3394 to i64
    %o_out_v3396 = alloca i64
    store i64 %t3395, i64* %o_out_v3396
    %oi_v3397 = alloca i64
    store i64 0, i64* %oi_v3397
    %t3403 = load i64, i64* %olen_v3393
    %rep.3402 = alloca i64
    store i64 0, i64* %rep.3402
    br label %loop.cond.3398
loop.cond.3398:
    %t3404 = load i64, i64* %rep.3402
    %t3405 = icmp slt i64 %t3404, %t3403
    br i1 %t3405, label %loop.body.3399, label %loop.end.3400
loop.body.3399:
    %t3406 = load i64, i64* %oi_v3397
    %t3408 = icmp sgt i64 %t3406, 0
    %t3407 = zext i1 %t3408 to i64
    %t3412 = icmp ne i64 %t3407, 0
    br i1 %t3412, label %if.then.3409, label %if.end.3411
if.then.3409:
    %t3413 = load i64, i64* %o_out_v3396
    %t3414 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.216, i64 0, i64 0
    %t3415 = ptrtoint i8* %t3414 to i64
    %t3416 = call i64 @freak_llvm_word_concat(i64 %t3413, i64 %t3415)
    store i64 %t3416, i64* %o_out_v3396
    br label %if.end.3411
if.end.3411:
    %t3417 = load i64, i64* %handle
    %t3418 = load i64, i64* %oi_v3397
    %t3419 = call i64 @freak_json_obj_key_at(i64 %t3417, i64 %t3418)
    %okey_v3420 = alloca i64
    store i64 %t3419, i64* %okey_v3420
    %t3421 = load i64, i64* %handle
    %t3422 = load i64, i64* %oi_v3397
    %t3423 = call i64 @freak_json_arr_get(i64 %t3421, i64 %t3422)
    %ov_v3424 = alloca i64
    store i64 %t3423, i64* %ov_v3424
    %t3425 = load i64, i64* %o_out_v3396
    %t3426 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.217, i64 0, i64 0
    %t3427 = ptrtoint i8* %t3426 to i64
    %t3428 = call i64 @freak_llvm_word_concat(i64 %t3425, i64 %t3427)
    %t3429 = load i64, i64* %okey_v3420
    %t3430 = call i64 @freak_llvm_word_concat(i64 %t3428, i64 %t3429)
    %t3431 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.218, i64 0, i64 0
    %t3432 = ptrtoint i8* %t3431 to i64
    %t3433 = call i64 @freak_llvm_word_concat(i64 %t3430, i64 %t3432)
    %t3434 = load i64, i64* %ov_v3424
    %t3435 = call i64 @freak_json_stringify(i64 %t3434)
    %t3436 = call i64 @freak_llvm_word_concat(i64 %t3433, i64 %t3435)
    store i64 %t3436, i64* %o_out_v3396
    %t3437 = load i64, i64* %oi_v3397
    %t3438 = add i64 %t3437, 1
    store i64 %t3438, i64* %oi_v3397
    br label %loop.inc.3401
loop.inc.3401:
    %t3439 = load i64, i64* %rep.3402
    %t3440 = add i64 %t3439, 1
    store i64 %t3440, i64* %rep.3402
    br label %loop.cond.3398
loop.end.3400:
    %t3441 = load i64, i64* %o_out_v3396
    %t3442 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.219, i64 0, i64 0
    %t3443 = ptrtoint i8* %t3442 to i64
    %t3444 = call i64 @freak_llvm_word_concat(i64 %t3441, i64 %t3443)
    ret i64 %t3444
    br label %if.end.3389
if.end.3389:
    %t3445 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.220, i64 0, i64 0
    %t3446 = ptrtoint i8* %t3445 to i64
    ret i64 %t3446
    ret i64 0
}

define i64 @freak_ver_parse_num(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3447 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.221, i64 0, i64 0
    %t3448 = ptrtoint i8* %t3447 to i64
    %res_v3449 = alloca i64
    store i64 %t3448, i64* %res_v3449
    %t3450 = load i64, i64* %start
    %i_v3451 = alloca i64
    store i64 %t3450, i64* %i_v3451
    %t3452 = load i64, i64* %s
    %t3453 = call i64 @freak_llvm_word_length(i64 %t3452)
    %slen_v3454 = alloca i64
    store i64 %t3453, i64* %slen_v3454
    br label %loop.cond.3455
loop.cond.3455:
    %t3458 = load i64, i64* %i_v3451
    %t3459 = load i64, i64* %slen_v3454
    %t3461 = icmp sge i64 %t3458, %t3459
    %t3460 = zext i1 %t3461 to i64
    %t3462 = icmp eq i64 %t3460, 0
    br i1 %t3462, label %loop.body.3456, label %loop.end.3457
loop.body.3456:
    %t3463 = load i64, i64* %s
    %t3465 = load i64, i64* %i_v3451
    %t3464 = call i64 @freak_llvm_word_char_at(i64 %t3463, i64 %t3465)
    %c_v3466 = alloca i64
    store i64 %t3464, i64* %c_v3466
    %t3467 = load i64, i64* %c_v3466
    %t3468 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.222, i64 0, i64 0
    %t3469 = ptrtoint i8* %t3468 to i64
    %t3470 = call i64 @freak_llvm_word_eq(i64 %t3467, i64 %t3469)
    %t3471 = load i64, i64* %c_v3466
    %t3472 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.223, i64 0, i64 0
    %t3473 = ptrtoint i8* %t3472 to i64
    %t3474 = call i64 @freak_llvm_word_eq(i64 %t3471, i64 %t3473)
    %t3476 = icmp ne i64 %t3470, 0
    %t3477 = icmp ne i64 %t3474, 0
    %t3478 = or i1 %t3476, %t3477
    %t3475 = zext i1 %t3478 to i64
    %t3479 = load i64, i64* %c_v3466
    %t3480 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.224, i64 0, i64 0
    %t3481 = ptrtoint i8* %t3480 to i64
    %t3482 = call i64 @freak_llvm_word_eq(i64 %t3479, i64 %t3481)
    %t3484 = icmp ne i64 %t3475, 0
    %t3485 = icmp ne i64 %t3482, 0
    %t3486 = or i1 %t3484, %t3485
    %t3483 = zext i1 %t3486 to i64
    %t3490 = icmp ne i64 %t3483, 0
    br i1 %t3490, label %if.then.3487, label %if.end.3489
if.then.3487:
    %t3491 = load i64, i64* %i_v3451
    %t3492 = add i64 %t3491, 1
    %t3493 = call i64 @freak_llvm_word_from_int(i64 %t3492)
    %pos_str_v3494 = alloca i64
    store i64 %t3493, i64* %pos_str_v3494
    %t3495 = load i64, i64* %res_v3449
    %t3496 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.225, i64 0, i64 0
    %t3497 = ptrtoint i8* %t3496 to i64
    %t3498 = call i64 @freak_llvm_word_concat(i64 %t3495, i64 %t3497)
    %t3499 = load i64, i64* %pos_str_v3494
    %t3500 = call i64 @freak_llvm_word_concat(i64 %t3498, i64 %t3499)
    ret i64 %t3500
    br label %if.end.3489
if.end.3489:
    %t3501 = load i64, i64* %res_v3449
    %t3502 = load i64, i64* %c_v3466
    %t3503 = call i64 @freak_llvm_word_concat(i64 %t3501, i64 %t3502)
    store i64 %t3503, i64* %res_v3449
    %t3504 = load i64, i64* %i_v3451
    %t3505 = add i64 %t3504, 1
    store i64 %t3505, i64* %i_v3451
    br label %loop.cond.3455
loop.end.3457:
    %t3506 = load i64, i64* %i_v3451
    %t3507 = call i64 @freak_llvm_word_from_int(i64 %t3506)
    %pos_str2_v3508 = alloca i64
    store i64 %t3507, i64* %pos_str2_v3508
    %t3509 = load i64, i64* %res_v3449
    %t3510 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.226, i64 0, i64 0
    %t3511 = ptrtoint i8* %t3510 to i64
    %t3512 = call i64 @freak_llvm_word_concat(i64 %t3509, i64 %t3511)
    %t3513 = load i64, i64* %pos_str2_v3508
    %t3514 = call i64 @freak_llvm_word_concat(i64 %t3512, i64 %t3513)
    ret i64 %t3514
    ret i64 0
}

define i64 @freak_ver_parse_pre(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3515 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.227, i64 0, i64 0
    %t3516 = ptrtoint i8* %t3515 to i64
    %res_v3517 = alloca i64
    store i64 %t3516, i64* %res_v3517
    %t3518 = load i64, i64* %start
    %i_v3519 = alloca i64
    store i64 %t3518, i64* %i_v3519
    %t3520 = load i64, i64* %s
    %t3521 = call i64 @freak_llvm_word_length(i64 %t3520)
    %slen_v3522 = alloca i64
    store i64 %t3521, i64* %slen_v3522
    br label %loop.cond.3523
loop.cond.3523:
    %t3526 = load i64, i64* %i_v3519
    %t3527 = load i64, i64* %slen_v3522
    %t3529 = icmp sge i64 %t3526, %t3527
    %t3528 = zext i1 %t3529 to i64
    %t3530 = icmp eq i64 %t3528, 0
    br i1 %t3530, label %loop.body.3524, label %loop.end.3525
loop.body.3524:
    %t3531 = load i64, i64* %s
    %t3533 = load i64, i64* %i_v3519
    %t3532 = call i64 @freak_llvm_word_char_at(i64 %t3531, i64 %t3533)
    %c_v3534 = alloca i64
    store i64 %t3532, i64* %c_v3534
    %t3535 = load i64, i64* %c_v3534
    %t3536 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.228, i64 0, i64 0
    %t3537 = ptrtoint i8* %t3536 to i64
    %t3538 = call i64 @freak_llvm_word_eq(i64 %t3535, i64 %t3537)
    %t3542 = icmp ne i64 %t3538, 0
    br i1 %t3542, label %if.then.3539, label %if.end.3541
if.then.3539:
    %t3543 = load i64, i64* %res_v3517
    ret i64 %t3543
    br label %if.end.3541
if.end.3541:
    %t3544 = load i64, i64* %res_v3517
    %t3545 = load i64, i64* %c_v3534
    %t3546 = call i64 @freak_llvm_word_concat(i64 %t3544, i64 %t3545)
    store i64 %t3546, i64* %res_v3517
    %t3547 = load i64, i64* %i_v3519
    %t3548 = add i64 %t3547, 1
    store i64 %t3548, i64* %i_v3519
    br label %loop.cond.3523
loop.end.3525:
    %t3549 = load i64, i64* %res_v3517
    ret i64 %t3549
    ret i64 0
}

define i64 @freak_ver_parse_build(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3550 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.229, i64 0, i64 0
    %t3551 = ptrtoint i8* %t3550 to i64
    %res_v3552 = alloca i64
    store i64 %t3551, i64* %res_v3552
    %t3553 = load i64, i64* %start
    %i_v3554 = alloca i64
    store i64 %t3553, i64* %i_v3554
    %t3555 = load i64, i64* %s
    %t3556 = call i64 @freak_llvm_word_length(i64 %t3555)
    %slen_v3557 = alloca i64
    store i64 %t3556, i64* %slen_v3557
    br label %loop.cond.3558
loop.cond.3558:
    %t3561 = load i64, i64* %i_v3554
    %t3562 = load i64, i64* %slen_v3557
    %t3564 = icmp sge i64 %t3561, %t3562
    %t3563 = zext i1 %t3564 to i64
    %t3565 = icmp eq i64 %t3563, 0
    br i1 %t3565, label %loop.body.3559, label %loop.end.3560
loop.body.3559:
    %t3566 = load i64, i64* %res_v3552
    %t3567 = load i64, i64* %s
    %t3569 = load i64, i64* %i_v3554
    %t3568 = call i64 @freak_llvm_word_char_at(i64 %t3567, i64 %t3569)
    %t3570 = call i64 @freak_llvm_word_concat(i64 %t3566, i64 %t3568)
    store i64 %t3570, i64* %res_v3552
    %t3571 = load i64, i64* %i_v3554
    %t3572 = add i64 %t3571, 1
    store i64 %t3572, i64* %i_v3554
    br label %loop.cond.3558
loop.end.3560:
    %t3573 = load i64, i64* %res_v3552
    ret i64 %t3573
    ret i64 0
}

define i64 @freak_ver_get_val(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %t3574 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.230, i64 0, i64 0
    %t3575 = ptrtoint i8* %t3574 to i64
    %res_v3576 = alloca i64
    store i64 %t3575, i64* %res_v3576
    %i_v3577 = alloca i64
    store i64 0, i64* %i_v3577
    %t3578 = load i64, i64* %encoded
    %t3579 = call i64 @freak_llvm_word_length(i64 %t3578)
    %elen_v3580 = alloca i64
    store i64 %t3579, i64* %elen_v3580
    br label %loop.cond.3581
loop.cond.3581:
    %t3584 = load i64, i64* %i_v3577
    %t3585 = load i64, i64* %elen_v3580
    %t3587 = icmp sge i64 %t3584, %t3585
    %t3586 = zext i1 %t3587 to i64
    %t3588 = icmp eq i64 %t3586, 0
    br i1 %t3588, label %loop.body.3582, label %loop.end.3583
loop.body.3582:
    %t3589 = load i64, i64* %encoded
    %t3591 = load i64, i64* %i_v3577
    %t3590 = call i64 @freak_llvm_word_char_at(i64 %t3589, i64 %t3591)
    %c_v3592 = alloca i64
    store i64 %t3590, i64* %c_v3592
    %t3593 = load i64, i64* %c_v3592
    %t3594 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.231, i64 0, i64 0
    %t3595 = ptrtoint i8* %t3594 to i64
    %t3596 = call i64 @freak_llvm_word_eq(i64 %t3593, i64 %t3595)
    %t3600 = icmp ne i64 %t3596, 0
    br i1 %t3600, label %if.then.3597, label %if.end.3599
if.then.3597:
    %t3601 = load i64, i64* %res_v3576
    ret i64 %t3601
    br label %if.end.3599
if.end.3599:
    %t3602 = load i64, i64* %res_v3576
    %t3603 = load i64, i64* %c_v3592
    %t3604 = call i64 @freak_llvm_word_concat(i64 %t3602, i64 %t3603)
    store i64 %t3604, i64* %res_v3576
    %t3605 = load i64, i64* %i_v3577
    %t3606 = add i64 %t3605, 1
    store i64 %t3606, i64* %i_v3577
    br label %loop.cond.3581
loop.end.3583:
    %t3607 = load i64, i64* %res_v3576
    ret i64 %t3607
    ret i64 0
}

define i64 @freak_ver_get_pos(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %i_v3608 = alloca i64
    store i64 0, i64* %i_v3608
    %t3609 = load i64, i64* %encoded
    %t3610 = call i64 @freak_llvm_word_length(i64 %t3609)
    %elen_v3611 = alloca i64
    store i64 %t3610, i64* %elen_v3611
    br label %loop.cond.3612
loop.cond.3612:
    %t3615 = load i64, i64* %i_v3608
    %t3616 = load i64, i64* %elen_v3611
    %t3618 = icmp sge i64 %t3615, %t3616
    %t3617 = zext i1 %t3618 to i64
    %t3619 = icmp eq i64 %t3617, 0
    br i1 %t3619, label %loop.body.3613, label %loop.end.3614
loop.body.3613:
    %t3620 = load i64, i64* %encoded
    %t3622 = load i64, i64* %i_v3608
    %t3621 = call i64 @freak_llvm_word_char_at(i64 %t3620, i64 %t3622)
    %c_v3623 = alloca i64
    store i64 %t3621, i64* %c_v3623
    %t3624 = load i64, i64* %c_v3623
    %t3625 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.232, i64 0, i64 0
    %t3626 = ptrtoint i8* %t3625 to i64
    %t3627 = call i64 @freak_llvm_word_eq(i64 %t3624, i64 %t3626)
    %t3631 = icmp ne i64 %t3627, 0
    br i1 %t3631, label %if.then.3628, label %if.end.3630
if.then.3628:
    %t3632 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.233, i64 0, i64 0
    %t3633 = ptrtoint i8* %t3632 to i64
    %pos_str_v3634 = alloca i64
    store i64 %t3633, i64* %pos_str_v3634
    %t3635 = load i64, i64* %i_v3608
    %t3636 = add i64 %t3635, 1
    %j_v3637 = alloca i64
    store i64 %t3636, i64* %j_v3637
    br label %loop.cond.3638
loop.cond.3638:
    %t3641 = load i64, i64* %j_v3637
    %t3642 = load i64, i64* %elen_v3611
    %t3644 = icmp sge i64 %t3641, %t3642
    %t3643 = zext i1 %t3644 to i64
    %t3645 = icmp eq i64 %t3643, 0
    br i1 %t3645, label %loop.body.3639, label %loop.end.3640
loop.body.3639:
    %t3646 = load i64, i64* %pos_str_v3634
    %t3647 = load i64, i64* %encoded
    %t3649 = load i64, i64* %j_v3637
    %t3648 = call i64 @freak_llvm_word_char_at(i64 %t3647, i64 %t3649)
    %t3650 = call i64 @freak_llvm_word_concat(i64 %t3646, i64 %t3648)
    store i64 %t3650, i64* %pos_str_v3634
    %t3651 = load i64, i64* %j_v3637
    %t3652 = add i64 %t3651, 1
    store i64 %t3652, i64* %j_v3637
    br label %loop.cond.3638
loop.end.3640:
    %t3653 = load i64, i64* %pos_str_v3634
    %t3654 = call i64 @freak_llvm_word_to_int(i64 %t3653)
    ret i64 %t3654
    br label %if.end.3630
if.end.3630:
    %t3655 = load i64, i64* %i_v3608
    %t3656 = add i64 %t3655, 1
    store i64 %t3656, i64* %i_v3608
    br label %loop.cond.3612
loop.end.3614:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_parse(i64 %arg_version) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %t3657 = load i64, i64* %version
    %s_v3658 = alloca i64
    store i64 %t3657, i64* %s_v3658
    %t3659 = load i64, i64* %s_v3658
    %t3660 = call i64 @freak_llvm_word_length(i64 %t3659)
    %t3662 = icmp sgt i64 %t3660, 0
    %t3661 = zext i1 %t3662 to i64
    %t3666 = icmp ne i64 %t3661, 0
    br i1 %t3666, label %if.then.3663, label %if.end.3665
if.then.3663:
    %t3667 = load i64, i64* %s_v3658
    %t3668 = call i64 @freak_llvm_word_char_at(i64 %t3667, i64 0)
    %fc_v3669 = alloca i64
    store i64 %t3668, i64* %fc_v3669
    %t3670 = load i64, i64* %fc_v3669
    %t3671 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.234, i64 0, i64 0
    %t3672 = ptrtoint i8* %t3671 to i64
    %t3673 = call i64 @freak_llvm_word_eq(i64 %t3670, i64 %t3672)
    %t3674 = load i64, i64* %fc_v3669
    %t3675 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.235, i64 0, i64 0
    %t3676 = ptrtoint i8* %t3675 to i64
    %t3677 = call i64 @freak_llvm_word_eq(i64 %t3674, i64 %t3676)
    %t3679 = icmp ne i64 %t3673, 0
    %t3680 = icmp ne i64 %t3677, 0
    %t3681 = or i1 %t3679, %t3680
    %t3678 = zext i1 %t3681 to i64
    %t3685 = icmp ne i64 %t3678, 0
    br i1 %t3685, label %if.then.3682, label %if.end.3684
if.then.3682:
    %t3686 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.236, i64 0, i64 0
    %t3687 = ptrtoint i8* %t3686 to i64
    %ns_v3688 = alloca i64
    store i64 %t3687, i64* %ns_v3688
    %vi_v3689 = alloca i64
    store i64 1, i64* %vi_v3689
    br label %loop.cond.3690
loop.cond.3690:
    %t3693 = load i64, i64* %vi_v3689
    %t3694 = load i64, i64* %s_v3658
    %t3695 = call i64 @freak_llvm_word_length(i64 %t3694)
    %t3697 = icmp sge i64 %t3693, %t3695
    %t3696 = zext i1 %t3697 to i64
    %t3698 = icmp eq i64 %t3696, 0
    br i1 %t3698, label %loop.body.3691, label %loop.end.3692
loop.body.3691:
    %t3699 = load i64, i64* %ns_v3688
    %t3700 = load i64, i64* %s_v3658
    %t3702 = load i64, i64* %vi_v3689
    %t3701 = call i64 @freak_llvm_word_char_at(i64 %t3700, i64 %t3702)
    %t3703 = call i64 @freak_llvm_word_concat(i64 %t3699, i64 %t3701)
    store i64 %t3703, i64* %ns_v3688
    %t3704 = load i64, i64* %vi_v3689
    %t3705 = add i64 %t3704, 1
    store i64 %t3705, i64* %vi_v3689
    br label %loop.cond.3690
loop.end.3692:
    %t3706 = load i64, i64* %ns_v3688
    store i64 %t3706, i64* %s_v3658
    br label %if.end.3684
if.end.3684:
    br label %if.end.3665
if.end.3665:
    %t3707 = load i64, i64* %s_v3658
    %t3708 = call i64 @freak_ver_parse_num(i64 %t3707, i64 0)
    %r1_v3709 = alloca i64
    store i64 %t3708, i64* %r1_v3709
    %t3710 = load i64, i64* %r1_v3709
    %t3711 = call i64 @freak_ver_get_val(i64 %t3710)
    %major_v3712 = alloca i64
    store i64 %t3711, i64* %major_v3712
    %t3713 = load i64, i64* %r1_v3709
    %t3714 = call i64 @freak_ver_get_pos(i64 %t3713)
    %pos1_v3715 = alloca i64
    store i64 %t3714, i64* %pos1_v3715
    %t3716 = load i64, i64* %s_v3658
    %t3717 = load i64, i64* %pos1_v3715
    %t3718 = call i64 @freak_ver_parse_num(i64 %t3716, i64 %t3717)
    %r2_v3719 = alloca i64
    store i64 %t3718, i64* %r2_v3719
    %t3720 = load i64, i64* %r2_v3719
    %t3721 = call i64 @freak_ver_get_val(i64 %t3720)
    %minor_v3722 = alloca i64
    store i64 %t3721, i64* %minor_v3722
    %t3723 = load i64, i64* %r2_v3719
    %t3724 = call i64 @freak_ver_get_pos(i64 %t3723)
    %pos2_v3725 = alloca i64
    store i64 %t3724, i64* %pos2_v3725
    %t3726 = load i64, i64* %s_v3658
    %t3727 = load i64, i64* %pos2_v3725
    %t3728 = call i64 @freak_ver_parse_num(i64 %t3726, i64 %t3727)
    %r3_v3729 = alloca i64
    store i64 %t3728, i64* %r3_v3729
    %t3730 = load i64, i64* %r3_v3729
    %t3731 = call i64 @freak_ver_get_val(i64 %t3730)
    %patch_v3732 = alloca i64
    store i64 %t3731, i64* %patch_v3732
    %t3733 = load i64, i64* %r3_v3729
    %t3734 = call i64 @freak_ver_get_pos(i64 %t3733)
    %pos3_v3735 = alloca i64
    store i64 %t3734, i64* %pos3_v3735
    %t3736 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.237, i64 0, i64 0
    %t3737 = ptrtoint i8* %t3736 to i64
    %pre_v3738 = alloca i64
    store i64 %t3737, i64* %pre_v3738
    %t3739 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.238, i64 0, i64 0
    %t3740 = ptrtoint i8* %t3739 to i64
    %bld_v3741 = alloca i64
    store i64 %t3740, i64* %bld_v3741
    %t3742 = load i64, i64* %pos3_v3735
    %t3743 = load i64, i64* %s_v3658
    %t3744 = call i64 @freak_llvm_word_length(i64 %t3743)
    %t3746 = icmp sle i64 %t3742, %t3744
    %t3745 = zext i1 %t3746 to i64
    %t3750 = icmp ne i64 %t3745, 0
    br i1 %t3750, label %if.then.3747, label %if.end.3749
if.then.3747:
    %t3751 = load i64, i64* %pos3_v3735
    %t3753 = icmp sgt i64 %t3751, 0
    %t3752 = zext i1 %t3753 to i64
    %t3757 = icmp ne i64 %t3752, 0
    br i1 %t3757, label %if.then.3754, label %if.end.3756
if.then.3754:
    %t3758 = load i64, i64* %s_v3658
    %t3760 = load i64, i64* %pos3_v3735
    %t3761 = sub i64 %t3760, 1
    %t3759 = call i64 @freak_llvm_word_char_at(i64 %t3758, i64 %t3761)
    %delim_v3762 = alloca i64
    store i64 %t3759, i64* %delim_v3762
    %t3763 = load i64, i64* %delim_v3762
    %t3764 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.239, i64 0, i64 0
    %t3765 = ptrtoint i8* %t3764 to i64
    %t3766 = call i64 @freak_llvm_word_eq(i64 %t3763, i64 %t3765)
    %t3770 = icmp ne i64 %t3766, 0
    br i1 %t3770, label %if.then.3767, label %if.else.3768
if.then.3767:
    %t3771 = load i64, i64* %s_v3658
    %t3772 = load i64, i64* %pos3_v3735
    %t3773 = call i64 @freak_ver_parse_pre(i64 %t3771, i64 %t3772)
    store i64 %t3773, i64* %pre_v3738
    br label %if.end.3769
if.else.3768:
    %t3774 = load i64, i64* %delim_v3762
    %t3775 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.240, i64 0, i64 0
    %t3776 = ptrtoint i8* %t3775 to i64
    %t3777 = call i64 @freak_llvm_word_eq(i64 %t3774, i64 %t3776)
    %t3781 = icmp ne i64 %t3777, 0
    br i1 %t3781, label %if.then.3778, label %if.end.3780
if.then.3778:
    %t3782 = load i64, i64* %s_v3658
    %t3783 = load i64, i64* %pos3_v3735
    %t3784 = call i64 @freak_ver_parse_build(i64 %t3782, i64 %t3783)
    store i64 %t3784, i64* %bld_v3741
    br label %if.end.3780
if.end.3780:
    br label %if.end.3769
if.end.3769:
    br label %if.end.3756
if.end.3756:
    br label %if.end.3749
if.end.3749:
    %t3785 = load i64, i64* %pre_v3738
    %t3786 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.241, i64 0, i64 0
    %t3787 = ptrtoint i8* %t3786 to i64
    %t3788 = call i64 @freak_llvm_word_neq(i64 %t3785, i64 %t3787)
    %t3792 = icmp ne i64 %t3788, 0
    br i1 %t3792, label %if.then.3789, label %if.end.3791
if.then.3789:
    %pi_v3793 = alloca i64
    store i64 0, i64* %pi_v3793
    %t3794 = load i64, i64* %s_v3658
    %t3795 = call i64 @freak_llvm_word_length(i64 %t3794)
    %plen_v3796 = alloca i64
    store i64 %t3795, i64* %plen_v3796
    br label %loop.cond.3797
loop.cond.3797:
    %t3800 = load i64, i64* %pi_v3793
    %t3801 = load i64, i64* %plen_v3796
    %t3803 = icmp sge i64 %t3800, %t3801
    %t3802 = zext i1 %t3803 to i64
    %t3804 = icmp eq i64 %t3802, 0
    br i1 %t3804, label %loop.body.3798, label %loop.end.3799
loop.body.3798:
    %t3805 = load i64, i64* %s_v3658
    %t3807 = load i64, i64* %pi_v3793
    %t3806 = call i64 @freak_llvm_word_char_at(i64 %t3805, i64 %t3807)
    %t3808 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.242, i64 0, i64 0
    %t3809 = ptrtoint i8* %t3808 to i64
    %t3810 = call i64 @freak_llvm_word_eq(i64 %t3806, i64 %t3809)
    %t3814 = icmp ne i64 %t3810, 0
    br i1 %t3814, label %if.then.3811, label %if.end.3813
if.then.3811:
    %t3815 = load i64, i64* %s_v3658
    %t3816 = load i64, i64* %pi_v3793
    %t3817 = add i64 %t3816, 1
    %t3818 = call i64 @freak_ver_parse_build(i64 %t3815, i64 %t3817)
    store i64 %t3818, i64* %bld_v3741
    br label %if.end.3813
if.end.3813:
    %t3819 = load i64, i64* %pi_v3793
    %t3820 = add i64 %t3819, 1
    store i64 %t3820, i64* %pi_v3793
    br label %loop.cond.3797
loop.end.3799:
    br label %if.end.3791
if.end.3791:
    %t3821 = load i64, i64* %major_v3712
    %t3822 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.243, i64 0, i64 0
    %t3823 = ptrtoint i8* %t3822 to i64
    %t3824 = call i64 @freak_llvm_word_concat(i64 %t3821, i64 %t3823)
    %t3825 = load i64, i64* %minor_v3722
    %t3826 = call i64 @freak_llvm_word_concat(i64 %t3824, i64 %t3825)
    %t3827 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.244, i64 0, i64 0
    %t3828 = ptrtoint i8* %t3827 to i64
    %t3829 = call i64 @freak_llvm_word_concat(i64 %t3826, i64 %t3828)
    %t3830 = load i64, i64* %patch_v3732
    %t3831 = call i64 @freak_llvm_word_concat(i64 %t3829, i64 %t3830)
    %t3832 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.245, i64 0, i64 0
    %t3833 = ptrtoint i8* %t3832 to i64
    %t3834 = call i64 @freak_llvm_word_concat(i64 %t3831, i64 %t3833)
    %t3835 = load i64, i64* %pre_v3738
    %t3836 = call i64 @freak_llvm_word_concat(i64 %t3834, i64 %t3835)
    %t3837 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.246, i64 0, i64 0
    %t3838 = ptrtoint i8* %t3837 to i64
    %t3839 = call i64 @freak_llvm_word_concat(i64 %t3836, i64 %t3838)
    %t3840 = load i64, i64* %bld_v3741
    %t3841 = call i64 @freak_llvm_word_concat(i64 %t3839, i64 %t3840)
    ret i64 %t3841
    ret i64 0
}

define i64 @freak_ver_field(i64 %arg_parsed, i64 %arg_field_idx) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %field_idx = alloca i64
    store i64 %arg_field_idx, i64* %field_idx
    %t3842 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.247, i64 0, i64 0
    %t3843 = ptrtoint i8* %t3842 to i64
    %res_v3844 = alloca i64
    store i64 %t3843, i64* %res_v3844
    %current_field_v3845 = alloca i64
    store i64 0, i64* %current_field_v3845
    %i_v3846 = alloca i64
    store i64 0, i64* %i_v3846
    %t3847 = load i64, i64* %parsed
    %t3848 = call i64 @freak_llvm_word_length(i64 %t3847)
    %plen_v3849 = alloca i64
    store i64 %t3848, i64* %plen_v3849
    br label %loop.cond.3850
loop.cond.3850:
    %t3853 = load i64, i64* %i_v3846
    %t3854 = load i64, i64* %plen_v3849
    %t3856 = icmp sge i64 %t3853, %t3854
    %t3855 = zext i1 %t3856 to i64
    %t3857 = icmp eq i64 %t3855, 0
    br i1 %t3857, label %loop.body.3851, label %loop.end.3852
loop.body.3851:
    %t3858 = load i64, i64* %parsed
    %t3860 = load i64, i64* %i_v3846
    %t3859 = call i64 @freak_llvm_word_char_at(i64 %t3858, i64 %t3860)
    %c_v3861 = alloca i64
    store i64 %t3859, i64* %c_v3861
    %t3862 = load i64, i64* %c_v3861
    %t3863 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.248, i64 0, i64 0
    %t3864 = ptrtoint i8* %t3863 to i64
    %t3865 = call i64 @freak_llvm_word_eq(i64 %t3862, i64 %t3864)
    %t3869 = icmp ne i64 %t3865, 0
    br i1 %t3869, label %if.then.3866, label %if.else.3867
if.then.3866:
    %t3870 = load i64, i64* %current_field_v3845
    %t3871 = load i64, i64* %field_idx
    %t3873 = icmp eq i64 %t3870, %t3871
    %t3872 = zext i1 %t3873 to i64
    %t3877 = icmp ne i64 %t3872, 0
    br i1 %t3877, label %if.then.3874, label %if.end.3876
if.then.3874:
    %t3878 = load i64, i64* %res_v3844
    ret i64 %t3878
    br label %if.end.3876
if.end.3876:
    %t3879 = load i64, i64* %current_field_v3845
    %t3880 = add i64 %t3879, 1
    store i64 %t3880, i64* %current_field_v3845
    %t3881 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.249, i64 0, i64 0
    %t3882 = ptrtoint i8* %t3881 to i64
    store i64 %t3882, i64* %res_v3844
    br label %if.end.3868
if.else.3867:
    %t3883 = load i64, i64* %res_v3844
    %t3884 = load i64, i64* %c_v3861
    %t3885 = call i64 @freak_llvm_word_concat(i64 %t3883, i64 %t3884)
    store i64 %t3885, i64* %res_v3844
    br label %if.end.3868
if.end.3868:
    %t3886 = load i64, i64* %i_v3846
    %t3887 = add i64 %t3886, 1
    store i64 %t3887, i64* %i_v3846
    br label %loop.cond.3850
loop.end.3852:
    %t3888 = load i64, i64* %current_field_v3845
    %t3889 = load i64, i64* %field_idx
    %t3891 = icmp eq i64 %t3888, %t3889
    %t3890 = zext i1 %t3891 to i64
    %t3895 = icmp ne i64 %t3890, 0
    br i1 %t3895, label %if.then.3892, label %if.end.3894
if.then.3892:
    %t3896 = load i64, i64* %res_v3844
    ret i64 %t3896
    br label %if.end.3894
if.end.3894:
    %t3897 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.250, i64 0, i64 0
    %t3898 = ptrtoint i8* %t3897 to i64
    ret i64 %t3898
    ret i64 0
}

define i64 @freak_ver_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3899 = load i64, i64* %parsed
    %t3900 = call i64 @freak_ver_field(i64 %t3899, i64 0)
    %t3901 = call i64 @freak_llvm_word_to_int(i64 %t3900)
    ret i64 %t3901
    ret i64 0
}

define i64 @freak_ver_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3902 = load i64, i64* %parsed
    %t3903 = call i64 @freak_ver_field(i64 %t3902, i64 1)
    %t3904 = call i64 @freak_llvm_word_to_int(i64 %t3903)
    ret i64 %t3904
    ret i64 0
}

define i64 @freak_ver_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3905 = load i64, i64* %parsed
    %t3906 = call i64 @freak_ver_field(i64 %t3905, i64 2)
    %t3907 = call i64 @freak_llvm_word_to_int(i64 %t3906)
    ret i64 %t3907
    ret i64 0
}

define i64 @freak_ver_pre(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3908 = load i64, i64* %parsed
    %t3909 = call i64 @freak_ver_field(i64 %t3908, i64 3)
    ret i64 %t3909
    ret i64 0
}

define i64 @freak_ver_build(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3910 = load i64, i64* %parsed
    %t3911 = call i64 @freak_ver_field(i64 %t3910, i64 4)
    ret i64 %t3911
    ret i64 0
}

define i64 @freak_ver_to_string(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3912 = load i64, i64* %parsed
    %t3913 = call i64 @freak_ver_field(i64 %t3912, i64 0)
    %maj_v3914 = alloca i64
    store i64 %t3913, i64* %maj_v3914
    %t3915 = load i64, i64* %parsed
    %t3916 = call i64 @freak_ver_field(i64 %t3915, i64 1)
    %min_v3917 = alloca i64
    store i64 %t3916, i64* %min_v3917
    %t3918 = load i64, i64* %parsed
    %t3919 = call i64 @freak_ver_field(i64 %t3918, i64 2)
    %pat_v3920 = alloca i64
    store i64 %t3919, i64* %pat_v3920
    %t3921 = load i64, i64* %parsed
    %t3922 = call i64 @freak_ver_field(i64 %t3921, i64 3)
    %pre_v3923 = alloca i64
    store i64 %t3922, i64* %pre_v3923
    %t3924 = load i64, i64* %parsed
    %t3925 = call i64 @freak_ver_field(i64 %t3924, i64 4)
    %bld_v3926 = alloca i64
    store i64 %t3925, i64* %bld_v3926
    %t3927 = load i64, i64* %maj_v3914
    %t3928 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.251, i64 0, i64 0
    %t3929 = ptrtoint i8* %t3928 to i64
    %t3930 = call i64 @freak_llvm_word_concat(i64 %t3927, i64 %t3929)
    %t3931 = load i64, i64* %min_v3917
    %t3932 = call i64 @freak_llvm_word_concat(i64 %t3930, i64 %t3931)
    %t3933 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.252, i64 0, i64 0
    %t3934 = ptrtoint i8* %t3933 to i64
    %t3935 = call i64 @freak_llvm_word_concat(i64 %t3932, i64 %t3934)
    %t3936 = load i64, i64* %pat_v3920
    %t3937 = call i64 @freak_llvm_word_concat(i64 %t3935, i64 %t3936)
    %out_v3938 = alloca i64
    store i64 %t3937, i64* %out_v3938
    %t3939 = load i64, i64* %pre_v3923
    %t3940 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.253, i64 0, i64 0
    %t3941 = ptrtoint i8* %t3940 to i64
    %t3942 = call i64 @freak_llvm_word_neq(i64 %t3939, i64 %t3941)
    %t3946 = icmp ne i64 %t3942, 0
    br i1 %t3946, label %if.then.3943, label %if.end.3945
if.then.3943:
    %t3947 = load i64, i64* %out_v3938
    %t3948 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.254, i64 0, i64 0
    %t3949 = ptrtoint i8* %t3948 to i64
    %t3950 = call i64 @freak_llvm_word_concat(i64 %t3947, i64 %t3949)
    %t3951 = load i64, i64* %pre_v3923
    %t3952 = call i64 @freak_llvm_word_concat(i64 %t3950, i64 %t3951)
    store i64 %t3952, i64* %out_v3938
    br label %if.end.3945
if.end.3945:
    %t3953 = load i64, i64* %bld_v3926
    %t3954 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.255, i64 0, i64 0
    %t3955 = ptrtoint i8* %t3954 to i64
    %t3956 = call i64 @freak_llvm_word_neq(i64 %t3953, i64 %t3955)
    %t3960 = icmp ne i64 %t3956, 0
    br i1 %t3960, label %if.then.3957, label %if.end.3959
if.then.3957:
    %t3961 = load i64, i64* %out_v3938
    %t3962 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.256, i64 0, i64 0
    %t3963 = ptrtoint i8* %t3962 to i64
    %t3964 = call i64 @freak_llvm_word_concat(i64 %t3961, i64 %t3963)
    %t3965 = load i64, i64* %bld_v3926
    %t3966 = call i64 @freak_llvm_word_concat(i64 %t3964, i64 %t3965)
    store i64 %t3966, i64* %out_v3938
    br label %if.end.3959
if.end.3959:
    %t3967 = load i64, i64* %out_v3938
    ret i64 %t3967
    ret i64 0
}

define i64 @freak_ver_compare(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t3968 = load i64, i64* %a
    %t3969 = call i64 @freak_ver_major(i64 %t3968)
    %a_major_v3970 = alloca i64
    store i64 %t3969, i64* %a_major_v3970
    %t3971 = load i64, i64* %b
    %t3972 = call i64 @freak_ver_major(i64 %t3971)
    %b_major_v3973 = alloca i64
    store i64 %t3972, i64* %b_major_v3973
    %t3974 = load i64, i64* %a_major_v3970
    %t3975 = load i64, i64* %b_major_v3973
    %t3977 = icmp slt i64 %t3974, %t3975
    %t3976 = zext i1 %t3977 to i64
    %t3981 = icmp ne i64 %t3976, 0
    br i1 %t3981, label %if.then.3978, label %if.end.3980
if.then.3978:
    %t3982 = sub i64 0, 1
    ret i64 %t3982
    br label %if.end.3980
if.end.3980:
    %t3983 = load i64, i64* %a_major_v3970
    %t3984 = load i64, i64* %b_major_v3973
    %t3986 = icmp sgt i64 %t3983, %t3984
    %t3985 = zext i1 %t3986 to i64
    %t3990 = icmp ne i64 %t3985, 0
    br i1 %t3990, label %if.then.3987, label %if.end.3989
if.then.3987:
    ret i64 1
    br label %if.end.3989
if.end.3989:
    %t3991 = load i64, i64* %a
    %t3992 = call i64 @freak_ver_minor(i64 %t3991)
    %a_minor_v3993 = alloca i64
    store i64 %t3992, i64* %a_minor_v3993
    %t3994 = load i64, i64* %b
    %t3995 = call i64 @freak_ver_minor(i64 %t3994)
    %b_minor_v3996 = alloca i64
    store i64 %t3995, i64* %b_minor_v3996
    %t3997 = load i64, i64* %a_minor_v3993
    %t3998 = load i64, i64* %b_minor_v3996
    %t4000 = icmp slt i64 %t3997, %t3998
    %t3999 = zext i1 %t4000 to i64
    %t4004 = icmp ne i64 %t3999, 0
    br i1 %t4004, label %if.then.4001, label %if.end.4003
if.then.4001:
    %t4005 = sub i64 0, 1
    ret i64 %t4005
    br label %if.end.4003
if.end.4003:
    %t4006 = load i64, i64* %a_minor_v3993
    %t4007 = load i64, i64* %b_minor_v3996
    %t4009 = icmp sgt i64 %t4006, %t4007
    %t4008 = zext i1 %t4009 to i64
    %t4013 = icmp ne i64 %t4008, 0
    br i1 %t4013, label %if.then.4010, label %if.end.4012
if.then.4010:
    ret i64 1
    br label %if.end.4012
if.end.4012:
    %t4014 = load i64, i64* %a
    %t4015 = call i64 @freak_ver_patch(i64 %t4014)
    %a_patch_v4016 = alloca i64
    store i64 %t4015, i64* %a_patch_v4016
    %t4017 = load i64, i64* %b
    %t4018 = call i64 @freak_ver_patch(i64 %t4017)
    %b_patch_v4019 = alloca i64
    store i64 %t4018, i64* %b_patch_v4019
    %t4020 = load i64, i64* %a_patch_v4016
    %t4021 = load i64, i64* %b_patch_v4019
    %t4023 = icmp slt i64 %t4020, %t4021
    %t4022 = zext i1 %t4023 to i64
    %t4027 = icmp ne i64 %t4022, 0
    br i1 %t4027, label %if.then.4024, label %if.end.4026
if.then.4024:
    %t4028 = sub i64 0, 1
    ret i64 %t4028
    br label %if.end.4026
if.end.4026:
    %t4029 = load i64, i64* %a_patch_v4016
    %t4030 = load i64, i64* %b_patch_v4019
    %t4032 = icmp sgt i64 %t4029, %t4030
    %t4031 = zext i1 %t4032 to i64
    %t4036 = icmp ne i64 %t4031, 0
    br i1 %t4036, label %if.then.4033, label %if.end.4035
if.then.4033:
    ret i64 1
    br label %if.end.4035
if.end.4035:
    %t4037 = load i64, i64* %a
    %t4038 = call i64 @freak_ver_pre(i64 %t4037)
    %a_pre_v4039 = alloca i64
    store i64 %t4038, i64* %a_pre_v4039
    %t4040 = load i64, i64* %b
    %t4041 = call i64 @freak_ver_pre(i64 %t4040)
    %b_pre_v4042 = alloca i64
    store i64 %t4041, i64* %b_pre_v4042
    %t4043 = load i64, i64* %a_pre_v4039
    %t4044 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.257, i64 0, i64 0
    %t4045 = ptrtoint i8* %t4044 to i64
    %t4046 = call i64 @freak_llvm_word_eq(i64 %t4043, i64 %t4045)
    %t4047 = load i64, i64* %b_pre_v4042
    %t4048 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.258, i64 0, i64 0
    %t4049 = ptrtoint i8* %t4048 to i64
    %t4050 = call i64 @freak_llvm_word_neq(i64 %t4047, i64 %t4049)
    %t4052 = icmp ne i64 %t4046, 0
    %t4053 = icmp ne i64 %t4050, 0
    %t4054 = and i1 %t4052, %t4053
    %t4051 = zext i1 %t4054 to i64
    %t4058 = icmp ne i64 %t4051, 0
    br i1 %t4058, label %if.then.4055, label %if.end.4057
if.then.4055:
    ret i64 1
    br label %if.end.4057
if.end.4057:
    %t4059 = load i64, i64* %a_pre_v4039
    %t4060 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.259, i64 0, i64 0
    %t4061 = ptrtoint i8* %t4060 to i64
    %t4062 = call i64 @freak_llvm_word_neq(i64 %t4059, i64 %t4061)
    %t4063 = load i64, i64* %b_pre_v4042
    %t4064 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.260, i64 0, i64 0
    %t4065 = ptrtoint i8* %t4064 to i64
    %t4066 = call i64 @freak_llvm_word_eq(i64 %t4063, i64 %t4065)
    %t4068 = icmp ne i64 %t4062, 0
    %t4069 = icmp ne i64 %t4066, 0
    %t4070 = and i1 %t4068, %t4069
    %t4067 = zext i1 %t4070 to i64
    %t4074 = icmp ne i64 %t4067, 0
    br i1 %t4074, label %if.then.4071, label %if.end.4073
if.then.4071:
    %t4075 = sub i64 0, 1
    ret i64 %t4075
    br label %if.end.4073
if.end.4073:
    %t4076 = load i64, i64* %a_pre_v4039
    %t4077 = call i64 @freak_llvm_word_length(i64 %t4076)
    %cmp_len_v4078 = alloca i64
    store i64 %t4077, i64* %cmp_len_v4078
    %t4079 = load i64, i64* %b_pre_v4042
    %t4080 = call i64 @freak_llvm_word_length(i64 %t4079)
    %t4081 = load i64, i64* %cmp_len_v4078
    %t4083 = icmp slt i64 %t4080, %t4081
    %t4082 = zext i1 %t4083 to i64
    %t4087 = icmp ne i64 %t4082, 0
    br i1 %t4087, label %if.then.4084, label %if.end.4086
if.then.4084:
    %t4088 = load i64, i64* %b_pre_v4042
    %t4089 = call i64 @freak_llvm_word_length(i64 %t4088)
    store i64 %t4089, i64* %cmp_len_v4078
    br label %if.end.4086
if.end.4086:
    %ci_v4090 = alloca i64
    store i64 0, i64* %ci_v4090
    br label %loop.cond.4091
loop.cond.4091:
    %t4094 = load i64, i64* %ci_v4090
    %t4095 = load i64, i64* %cmp_len_v4078
    %t4097 = icmp sge i64 %t4094, %t4095
    %t4096 = zext i1 %t4097 to i64
    %t4098 = icmp eq i64 %t4096, 0
    br i1 %t4098, label %loop.body.4092, label %loop.end.4093
loop.body.4092:
    %t4099 = load i64, i64* %a_pre_v4039
    %t4101 = load i64, i64* %ci_v4090
    %t4100 = call i64 @freak_llvm_word_char_at(i64 %t4099, i64 %t4101)
    %ac_v4102 = alloca i64
    store i64 %t4100, i64* %ac_v4102
    %t4103 = load i64, i64* %b_pre_v4042
    %t4105 = load i64, i64* %ci_v4090
    %t4104 = call i64 @freak_llvm_word_char_at(i64 %t4103, i64 %t4105)
    %bc_v4106 = alloca i64
    store i64 %t4104, i64* %bc_v4106
    %t4107 = load i64, i64* %ac_v4102
    %t4108 = load i64, i64* %bc_v4106
    %t4109 = call i64 @freak_llvm_word_neq(i64 %t4107, i64 %t4108)
    %t4113 = icmp ne i64 %t4109, 0
    br i1 %t4113, label %if.then.4110, label %if.end.4112
if.then.4110:
    %t4114 = load i64, i64* %ac_v4102
    %t4115 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.261, i64 0, i64 0
    %t4116 = ptrtoint i8* %t4115 to i64
    %t4117 = call i64 @freak_llvm_word_eq(i64 %t4114, i64 %t4116)
    %t4118 = load i64, i64* %bc_v4106
    %t4119 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.262, i64 0, i64 0
    %t4120 = ptrtoint i8* %t4119 to i64
    %t4121 = call i64 @freak_llvm_word_eq(i64 %t4118, i64 %t4120)
    %t4123 = icmp ne i64 %t4117, 0
    %t4124 = icmp ne i64 %t4121, 0
    %t4125 = and i1 %t4123, %t4124
    %t4122 = zext i1 %t4125 to i64
    %t4129 = icmp ne i64 %t4122, 0
    br i1 %t4129, label %if.then.4126, label %if.end.4128
if.then.4126:
    %t4130 = sub i64 0, 1
    ret i64 %t4130
    br label %if.end.4128
if.end.4128:
    %t4131 = load i64, i64* %ac_v4102
    %t4132 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.263, i64 0, i64 0
    %t4133 = ptrtoint i8* %t4132 to i64
    %t4134 = call i64 @freak_llvm_word_eq(i64 %t4131, i64 %t4133)
    %t4135 = load i64, i64* %bc_v4106
    %t4136 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.264, i64 0, i64 0
    %t4137 = ptrtoint i8* %t4136 to i64
    %t4138 = call i64 @freak_llvm_word_eq(i64 %t4135, i64 %t4137)
    %t4140 = icmp ne i64 %t4134, 0
    %t4141 = icmp ne i64 %t4138, 0
    %t4142 = and i1 %t4140, %t4141
    %t4139 = zext i1 %t4142 to i64
    %t4146 = icmp ne i64 %t4139, 0
    br i1 %t4146, label %if.then.4143, label %if.end.4145
if.then.4143:
    ret i64 1
    br label %if.end.4145
if.end.4145:
    %t4147 = load i64, i64* %ac_v4102
    %t4148 = call i64 @freak_llvm_word_to_int(i64 %t4147)
    %ai_v4149 = alloca i64
    store i64 %t4148, i64* %ai_v4149
    %t4150 = load i64, i64* %bc_v4106
    %t4151 = call i64 @freak_llvm_word_to_int(i64 %t4150)
    %bi_v4152 = alloca i64
    store i64 %t4151, i64* %bi_v4152
    %t4153 = load i64, i64* %ai_v4149
    %t4154 = load i64, i64* %bi_v4152
    %t4156 = icmp slt i64 %t4153, %t4154
    %t4155 = zext i1 %t4156 to i64
    %t4160 = icmp ne i64 %t4155, 0
    br i1 %t4160, label %if.then.4157, label %if.end.4159
if.then.4157:
    %t4161 = sub i64 0, 1
    ret i64 %t4161
    br label %if.end.4159
if.end.4159:
    %t4162 = load i64, i64* %ai_v4149
    %t4163 = load i64, i64* %bi_v4152
    %t4165 = icmp sgt i64 %t4162, %t4163
    %t4164 = zext i1 %t4165 to i64
    %t4169 = icmp ne i64 %t4164, 0
    br i1 %t4169, label %if.then.4166, label %if.end.4168
if.then.4166:
    ret i64 1
    br label %if.end.4168
if.end.4168:
    br label %if.end.4112
if.end.4112:
    %t4170 = load i64, i64* %ci_v4090
    %t4171 = add i64 %t4170, 1
    store i64 %t4171, i64* %ci_v4090
    br label %loop.cond.4091
loop.end.4093:
    %t4172 = load i64, i64* %a_pre_v4039
    %t4173 = call i64 @freak_llvm_word_length(i64 %t4172)
    %t4174 = load i64, i64* %b_pre_v4042
    %t4175 = call i64 @freak_llvm_word_length(i64 %t4174)
    %t4177 = icmp slt i64 %t4173, %t4175
    %t4176 = zext i1 %t4177 to i64
    %t4181 = icmp ne i64 %t4176, 0
    br i1 %t4181, label %if.then.4178, label %if.end.4180
if.then.4178:
    %t4182 = sub i64 0, 1
    ret i64 %t4182
    br label %if.end.4180
if.end.4180:
    %t4183 = load i64, i64* %a_pre_v4039
    %t4184 = call i64 @freak_llvm_word_length(i64 %t4183)
    %t4185 = load i64, i64* %b_pre_v4042
    %t4186 = call i64 @freak_llvm_word_length(i64 %t4185)
    %t4188 = icmp sgt i64 %t4184, %t4186
    %t4187 = zext i1 %t4188 to i64
    %t4192 = icmp ne i64 %t4187, 0
    br i1 %t4192, label %if.then.4189, label %if.end.4191
if.then.4189:
    ret i64 1
    br label %if.end.4191
if.end.4191:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_eq(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4193 = load i64, i64* %a
    %t4194 = load i64, i64* %b
    %t4195 = call i64 @freak_ver_compare(i64 %t4193, i64 %t4194)
    %t4197 = icmp eq i64 %t4195, 0
    %t4196 = zext i1 %t4197 to i64
    ret i64 %t4196
    ret i64 0
}

define i64 @freak_ver_lt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4198 = load i64, i64* %a
    %t4199 = load i64, i64* %b
    %t4200 = call i64 @freak_ver_compare(i64 %t4198, i64 %t4199)
    %t4202 = icmp slt i64 %t4200, 0
    %t4201 = zext i1 %t4202 to i64
    ret i64 %t4201
    ret i64 0
}

define i64 @freak_ver_gt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4203 = load i64, i64* %a
    %t4204 = load i64, i64* %b
    %t4205 = call i64 @freak_ver_compare(i64 %t4203, i64 %t4204)
    %t4207 = icmp sgt i64 %t4205, 0
    %t4206 = zext i1 %t4207 to i64
    ret i64 %t4206
    ret i64 0
}

define i64 @freak_ver_lte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4208 = load i64, i64* %a
    %t4209 = load i64, i64* %b
    %t4210 = call i64 @freak_ver_compare(i64 %t4208, i64 %t4209)
    %t4212 = icmp sle i64 %t4210, 0
    %t4211 = zext i1 %t4212 to i64
    ret i64 %t4211
    ret i64 0
}

define i64 @freak_ver_gte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4213 = load i64, i64* %a
    %t4214 = load i64, i64* %b
    %t4215 = call i64 @freak_ver_compare(i64 %t4213, i64 %t4214)
    %t4217 = icmp sge i64 %t4215, 0
    %t4216 = zext i1 %t4217 to i64
    ret i64 %t4216
    ret i64 0
}

define i64 @freak_ver_bump_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4218 = load i64, i64* %parsed
    %t4219 = call i64 @freak_ver_major(i64 %t4218)
    %t4220 = add i64 %t4219, 1
    %maj_v4221 = alloca i64
    store i64 %t4220, i64* %maj_v4221
    %t4222 = load i64, i64* %maj_v4221
    %t4223 = call i64 @freak_llvm_word_from_int(i64 %t4222)
    %t4224 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.265, i64 0, i64 0
    %t4225 = ptrtoint i8* %t4224 to i64
    %t4226 = call i64 @freak_llvm_word_concat(i64 %t4223, i64 %t4225)
    ret i64 %t4226
    ret i64 0
}

define i64 @freak_ver_bump_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4227 = load i64, i64* %parsed
    %t4228 = call i64 @freak_ver_major(i64 %t4227)
    %maj_v4229 = alloca i64
    store i64 %t4228, i64* %maj_v4229
    %t4230 = load i64, i64* %parsed
    %t4231 = call i64 @freak_ver_minor(i64 %t4230)
    %t4232 = add i64 %t4231, 1
    %min_v4233 = alloca i64
    store i64 %t4232, i64* %min_v4233
    %t4234 = load i64, i64* %maj_v4229
    %t4235 = call i64 @freak_llvm_word_from_int(i64 %t4234)
    %t4236 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.266, i64 0, i64 0
    %t4237 = ptrtoint i8* %t4236 to i64
    %t4238 = call i64 @freak_llvm_word_concat(i64 %t4235, i64 %t4237)
    %t4239 = load i64, i64* %min_v4233
    %t4240 = call i64 @freak_llvm_word_from_int(i64 %t4239)
    %t4241 = call i64 @freak_llvm_word_concat(i64 %t4238, i64 %t4240)
    %t4242 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.267, i64 0, i64 0
    %t4243 = ptrtoint i8* %t4242 to i64
    %t4244 = call i64 @freak_llvm_word_concat(i64 %t4241, i64 %t4243)
    ret i64 %t4244
    ret i64 0
}

define i64 @freak_ver_bump_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4245 = load i64, i64* %parsed
    %t4246 = call i64 @freak_ver_major(i64 %t4245)
    %maj_v4247 = alloca i64
    store i64 %t4246, i64* %maj_v4247
    %t4248 = load i64, i64* %parsed
    %t4249 = call i64 @freak_ver_minor(i64 %t4248)
    %min_v4250 = alloca i64
    store i64 %t4249, i64* %min_v4250
    %t4251 = load i64, i64* %parsed
    %t4252 = call i64 @freak_ver_patch(i64 %t4251)
    %t4253 = add i64 %t4252, 1
    %pat_v4254 = alloca i64
    store i64 %t4253, i64* %pat_v4254
    %t4255 = load i64, i64* %maj_v4247
    %t4256 = call i64 @freak_llvm_word_from_int(i64 %t4255)
    %t4257 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.268, i64 0, i64 0
    %t4258 = ptrtoint i8* %t4257 to i64
    %t4259 = call i64 @freak_llvm_word_concat(i64 %t4256, i64 %t4258)
    %t4260 = load i64, i64* %min_v4250
    %t4261 = call i64 @freak_llvm_word_from_int(i64 %t4260)
    %t4262 = call i64 @freak_llvm_word_concat(i64 %t4259, i64 %t4261)
    %t4263 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.269, i64 0, i64 0
    %t4264 = ptrtoint i8* %t4263 to i64
    %t4265 = call i64 @freak_llvm_word_concat(i64 %t4262, i64 %t4264)
    %t4266 = load i64, i64* %pat_v4254
    %t4267 = call i64 @freak_llvm_word_from_int(i64 %t4266)
    %t4268 = call i64 @freak_llvm_word_concat(i64 %t4265, i64 %t4267)
    %t4269 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.270, i64 0, i64 0
    %t4270 = ptrtoint i8* %t4269 to i64
    %t4271 = call i64 @freak_llvm_word_concat(i64 %t4268, i64 %t4270)
    ret i64 %t4271
    ret i64 0
}

define i64 @freak_ver_strip_prefix(i64 %arg_constraint, i64 %arg_prefix_len) {
entry:
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %prefix_len = alloca i64
    store i64 %arg_prefix_len, i64* %prefix_len
    %t4272 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.271, i64 0, i64 0
    %t4273 = ptrtoint i8* %t4272 to i64
    %stripped_v4274 = alloca i64
    store i64 %t4273, i64* %stripped_v4274
    %t4275 = load i64, i64* %prefix_len
    %si_v4276 = alloca i64
    store i64 %t4275, i64* %si_v4276
    br label %loop.cond.4277
loop.cond.4277:
    %t4280 = load i64, i64* %si_v4276
    %t4281 = load i64, i64* %constraint
    %t4282 = call i64 @freak_llvm_word_length(i64 %t4281)
    %t4284 = icmp sge i64 %t4280, %t4282
    %t4283 = zext i1 %t4284 to i64
    %t4285 = icmp eq i64 %t4283, 0
    br i1 %t4285, label %loop.body.4278, label %loop.end.4279
loop.body.4278:
    %t4286 = load i64, i64* %stripped_v4274
    %t4287 = load i64, i64* %constraint
    %t4289 = load i64, i64* %si_v4276
    %t4288 = call i64 @freak_llvm_word_char_at(i64 %t4287, i64 %t4289)
    %t4290 = call i64 @freak_llvm_word_concat(i64 %t4286, i64 %t4288)
    store i64 %t4290, i64* %stripped_v4274
    %t4291 = load i64, i64* %si_v4276
    %t4292 = add i64 %t4291, 1
    store i64 %t4292, i64* %si_v4276
    br label %loop.cond.4277
loop.end.4279:
    %t4293 = load i64, i64* %stripped_v4274
    ret i64 %t4293
    ret i64 0
}

define i64 @freak_ver_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t4294 = load i64, i64* %c
    %t4295 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.272, i64 0, i64 0
    %t4296 = ptrtoint i8* %t4295 to i64
    %t4297 = call i64 @freak_llvm_word_eq(i64 %t4294, i64 %t4296)
    %t4301 = icmp ne i64 %t4297, 0
    br i1 %t4301, label %if.then.4298, label %if.end.4300
if.then.4298:
    ret i64 1
    br label %if.end.4300
if.end.4300:
    %t4302 = load i64, i64* %c
    %t4303 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.273, i64 0, i64 0
    %t4304 = ptrtoint i8* %t4303 to i64
    %t4305 = call i64 @freak_llvm_word_eq(i64 %t4302, i64 %t4304)
    %t4309 = icmp ne i64 %t4305, 0
    br i1 %t4309, label %if.then.4306, label %if.end.4308
if.then.4306:
    ret i64 1
    br label %if.end.4308
if.end.4308:
    %t4310 = load i64, i64* %c
    %t4311 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.274, i64 0, i64 0
    %t4312 = ptrtoint i8* %t4311 to i64
    %t4313 = call i64 @freak_llvm_word_eq(i64 %t4310, i64 %t4312)
    %t4317 = icmp ne i64 %t4313, 0
    br i1 %t4317, label %if.then.4314, label %if.end.4316
if.then.4314:
    ret i64 1
    br label %if.end.4316
if.end.4316:
    %t4318 = load i64, i64* %c
    %t4319 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.275, i64 0, i64 0
    %t4320 = ptrtoint i8* %t4319 to i64
    %t4321 = call i64 @freak_llvm_word_eq(i64 %t4318, i64 %t4320)
    %t4325 = icmp ne i64 %t4321, 0
    br i1 %t4325, label %if.then.4322, label %if.end.4324
if.then.4322:
    ret i64 1
    br label %if.end.4324
if.end.4324:
    %t4326 = load i64, i64* %c
    %t4327 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.276, i64 0, i64 0
    %t4328 = ptrtoint i8* %t4327 to i64
    %t4329 = call i64 @freak_llvm_word_eq(i64 %t4326, i64 %t4328)
    %t4333 = icmp ne i64 %t4329, 0
    br i1 %t4333, label %if.then.4330, label %if.end.4332
if.then.4330:
    ret i64 1
    br label %if.end.4332
if.end.4332:
    %t4334 = load i64, i64* %c
    %t4335 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.277, i64 0, i64 0
    %t4336 = ptrtoint i8* %t4335 to i64
    %t4337 = call i64 @freak_llvm_word_eq(i64 %t4334, i64 %t4336)
    %t4341 = icmp ne i64 %t4337, 0
    br i1 %t4341, label %if.then.4338, label %if.end.4340
if.then.4338:
    ret i64 1
    br label %if.end.4340
if.end.4340:
    %t4342 = load i64, i64* %c
    %t4343 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.278, i64 0, i64 0
    %t4344 = ptrtoint i8* %t4343 to i64
    %t4345 = call i64 @freak_llvm_word_eq(i64 %t4342, i64 %t4344)
    %t4349 = icmp ne i64 %t4345, 0
    br i1 %t4349, label %if.then.4346, label %if.end.4348
if.then.4346:
    ret i64 1
    br label %if.end.4348
if.end.4348:
    %t4350 = load i64, i64* %c
    %t4351 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.279, i64 0, i64 0
    %t4352 = ptrtoint i8* %t4351 to i64
    %t4353 = call i64 @freak_llvm_word_eq(i64 %t4350, i64 %t4352)
    %t4357 = icmp ne i64 %t4353, 0
    br i1 %t4357, label %if.then.4354, label %if.end.4356
if.then.4354:
    ret i64 1
    br label %if.end.4356
if.end.4356:
    %t4358 = load i64, i64* %c
    %t4359 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.280, i64 0, i64 0
    %t4360 = ptrtoint i8* %t4359 to i64
    %t4361 = call i64 @freak_llvm_word_eq(i64 %t4358, i64 %t4360)
    %t4365 = icmp ne i64 %t4361, 0
    br i1 %t4365, label %if.then.4362, label %if.end.4364
if.then.4362:
    ret i64 1
    br label %if.end.4364
if.end.4364:
    %t4366 = load i64, i64* %c
    %t4367 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.281, i64 0, i64 0
    %t4368 = ptrtoint i8* %t4367 to i64
    %t4369 = call i64 @freak_llvm_word_eq(i64 %t4366, i64 %t4368)
    %t4373 = icmp ne i64 %t4369, 0
    br i1 %t4373, label %if.then.4370, label %if.end.4372
if.then.4370:
    ret i64 1
    br label %if.end.4372
if.end.4372:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_satisfies_single(i64 %arg_v, i64 %arg_constraint) {
entry:
    %v = alloca i64
    store i64 %arg_v, i64* %v
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4374 = load i64, i64* %constraint
    %t4375 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.282, i64 0, i64 0
    %t4376 = ptrtoint i8* %t4375 to i64
    %t4377 = call i64 @freak_llvm_word_eq(i64 %t4374, i64 %t4376)
    %t4378 = load i64, i64* %constraint
    %t4379 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.283, i64 0, i64 0
    %t4380 = ptrtoint i8* %t4379 to i64
    %t4381 = call i64 @freak_llvm_word_eq(i64 %t4378, i64 %t4380)
    %t4383 = icmp ne i64 %t4377, 0
    %t4384 = icmp ne i64 %t4381, 0
    %t4385 = or i1 %t4383, %t4384
    %t4382 = zext i1 %t4385 to i64
    %t4389 = icmp ne i64 %t4382, 0
    br i1 %t4389, label %if.then.4386, label %if.end.4388
if.then.4386:
    ret i64 1
    br label %if.end.4388
if.end.4388:
    %t4390 = load i64, i64* %constraint
    %t4392 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.284, i64 0, i64 0
    %t4393 = ptrtoint i8* %t4392 to i64
    %t4391 = call i64 @freak_llvm_word_starts_with(i64 %t4390, i64 %t4393)
    %t4397 = icmp ne i64 %t4391, 0
    br i1 %t4397, label %if.then.4394, label %if.end.4396
if.then.4394:
    %t4398 = load i64, i64* %constraint
    %t4399 = call i64 @freak_ver_strip_prefix(i64 %t4398, i64 1)
    %t4400 = call i64 @freak_ver_parse(i64 %t4399)
    %c_v4401 = alloca i64
    store i64 %t4400, i64* %c_v4401
    %t4402 = load i64, i64* %v
    %t4403 = call i64 @freak_ver_major(i64 %t4402)
    %t4404 = load i64, i64* %c_v4401
    %t4405 = call i64 @freak_ver_major(i64 %t4404)
    %t4407 = icmp ne i64 %t4403, %t4405
    %t4406 = zext i1 %t4407 to i64
    %t4411 = icmp ne i64 %t4406, 0
    br i1 %t4411, label %if.then.4408, label %if.end.4410
if.then.4408:
    ret i64 0
    br label %if.end.4410
if.end.4410:
    %t4412 = load i64, i64* %v
    %t4413 = load i64, i64* %c_v4401
    %t4414 = call i64 @freak_ver_gte(i64 %t4412, i64 %t4413)
    ret i64 %t4414
    br label %if.end.4396
if.end.4396:
    %t4415 = load i64, i64* %constraint
    %t4417 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.285, i64 0, i64 0
    %t4418 = ptrtoint i8* %t4417 to i64
    %t4416 = call i64 @freak_llvm_word_starts_with(i64 %t4415, i64 %t4418)
    %t4422 = icmp ne i64 %t4416, 0
    br i1 %t4422, label %if.then.4419, label %if.end.4421
if.then.4419:
    %t4423 = load i64, i64* %constraint
    %t4424 = call i64 @freak_ver_strip_prefix(i64 %t4423, i64 1)
    %t4425 = call i64 @freak_ver_parse(i64 %t4424)
    %t_v4426 = alloca i64
    store i64 %t4425, i64* %t_v4426
    %t4427 = load i64, i64* %v
    %t4428 = call i64 @freak_ver_major(i64 %t4427)
    %t4429 = load i64, i64* %t_v4426
    %t4430 = call i64 @freak_ver_major(i64 %t4429)
    %t4432 = icmp ne i64 %t4428, %t4430
    %t4431 = zext i1 %t4432 to i64
    %t4436 = icmp ne i64 %t4431, 0
    br i1 %t4436, label %if.then.4433, label %if.end.4435
if.then.4433:
    ret i64 0
    br label %if.end.4435
if.end.4435:
    %t4437 = load i64, i64* %v
    %t4438 = call i64 @freak_ver_minor(i64 %t4437)
    %t4439 = load i64, i64* %t_v4426
    %t4440 = call i64 @freak_ver_minor(i64 %t4439)
    %t4442 = icmp ne i64 %t4438, %t4440
    %t4441 = zext i1 %t4442 to i64
    %t4446 = icmp ne i64 %t4441, 0
    br i1 %t4446, label %if.then.4443, label %if.end.4445
if.then.4443:
    ret i64 0
    br label %if.end.4445
if.end.4445:
    %t4447 = load i64, i64* %v
    %t4448 = load i64, i64* %t_v4426
    %t4449 = call i64 @freak_ver_gte(i64 %t4447, i64 %t4448)
    ret i64 %t4449
    br label %if.end.4421
if.end.4421:
    %t4450 = load i64, i64* %constraint
    %t4452 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.286, i64 0, i64 0
    %t4453 = ptrtoint i8* %t4452 to i64
    %t4451 = call i64 @freak_llvm_word_starts_with(i64 %t4450, i64 %t4453)
    %t4457 = icmp ne i64 %t4451, 0
    br i1 %t4457, label %if.then.4454, label %if.end.4456
if.then.4454:
    %t4458 = load i64, i64* %v
    %t4459 = load i64, i64* %constraint
    %t4460 = call i64 @freak_ver_strip_prefix(i64 %t4459, i64 2)
    %t4461 = call i64 @freak_ver_parse(i64 %t4460)
    %t4462 = call i64 @freak_ver_gte(i64 %t4458, i64 %t4461)
    ret i64 %t4462
    br label %if.end.4456
if.end.4456:
    %t4463 = load i64, i64* %constraint
    %t4465 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.287, i64 0, i64 0
    %t4466 = ptrtoint i8* %t4465 to i64
    %t4464 = call i64 @freak_llvm_word_starts_with(i64 %t4463, i64 %t4466)
    %t4470 = icmp ne i64 %t4464, 0
    br i1 %t4470, label %if.then.4467, label %if.end.4469
if.then.4467:
    %t4471 = load i64, i64* %v
    %t4472 = load i64, i64* %constraint
    %t4473 = call i64 @freak_ver_strip_prefix(i64 %t4472, i64 2)
    %t4474 = call i64 @freak_ver_parse(i64 %t4473)
    %t4475 = call i64 @freak_ver_lte(i64 %t4471, i64 %t4474)
    ret i64 %t4475
    br label %if.end.4469
if.end.4469:
    %t4476 = load i64, i64* %constraint
    %t4478 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.288, i64 0, i64 0
    %t4479 = ptrtoint i8* %t4478 to i64
    %t4477 = call i64 @freak_llvm_word_starts_with(i64 %t4476, i64 %t4479)
    %t4483 = icmp ne i64 %t4477, 0
    br i1 %t4483, label %if.then.4480, label %if.end.4482
if.then.4480:
    %t4484 = load i64, i64* %v
    %t4485 = load i64, i64* %constraint
    %t4486 = call i64 @freak_ver_strip_prefix(i64 %t4485, i64 1)
    %t4487 = call i64 @freak_ver_parse(i64 %t4486)
    %t4488 = call i64 @freak_ver_gt(i64 %t4484, i64 %t4487)
    ret i64 %t4488
    br label %if.end.4482
if.end.4482:
    %t4489 = load i64, i64* %constraint
    %t4491 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.289, i64 0, i64 0
    %t4492 = ptrtoint i8* %t4491 to i64
    %t4490 = call i64 @freak_llvm_word_starts_with(i64 %t4489, i64 %t4492)
    %t4496 = icmp ne i64 %t4490, 0
    br i1 %t4496, label %if.then.4493, label %if.end.4495
if.then.4493:
    %t4497 = load i64, i64* %v
    %t4498 = load i64, i64* %constraint
    %t4499 = call i64 @freak_ver_strip_prefix(i64 %t4498, i64 1)
    %t4500 = call i64 @freak_ver_parse(i64 %t4499)
    %t4501 = call i64 @freak_ver_lt(i64 %t4497, i64 %t4500)
    ret i64 %t4501
    br label %if.end.4495
if.end.4495:
    %t4502 = load i64, i64* %constraint
    %t4504 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.290, i64 0, i64 0
    %t4505 = ptrtoint i8* %t4504 to i64
    %t4503 = call i64 @freak_llvm_word_starts_with(i64 %t4502, i64 %t4505)
    %t4509 = icmp ne i64 %t4503, 0
    br i1 %t4509, label %if.then.4506, label %if.end.4508
if.then.4506:
    %t4510 = load i64, i64* %v
    %t4511 = load i64, i64* %constraint
    %t4512 = call i64 @freak_ver_strip_prefix(i64 %t4511, i64 1)
    %t4513 = call i64 @freak_ver_parse(i64 %t4512)
    %t4514 = call i64 @freak_ver_eq(i64 %t4510, i64 %t4513)
    ret i64 %t4514
    br label %if.end.4508
if.end.4508:
    %t4515 = load i64, i64* %constraint
    %t4516 = call i64 @freak_llvm_word_length(i64 %t4515)
    %t4518 = icmp sgt i64 %t4516, 0
    %t4517 = zext i1 %t4518 to i64
    %t4522 = icmp ne i64 %t4517, 0
    br i1 %t4522, label %if.then.4519, label %if.end.4521
if.then.4519:
    %t4523 = load i64, i64* %constraint
    %t4524 = call i64 @freak_llvm_word_char_at(i64 %t4523, i64 0)
    %fc_v4525 = alloca i64
    store i64 %t4524, i64* %fc_v4525
    %t4526 = load i64, i64* %fc_v4525
    %t4527 = call i64 @freak_ver_is_digit(i64 %t4526)
    %t4531 = icmp ne i64 %t4527, 0
    br i1 %t4531, label %if.then.4528, label %if.end.4530
if.then.4528:
    %t4532 = load i64, i64* %constraint
    %t4533 = call i64 @freak_ver_parse(i64 %t4532)
    %c_v4534 = alloca i64
    store i64 %t4533, i64* %c_v4534
    %t4535 = load i64, i64* %v
    %t4536 = call i64 @freak_ver_major(i64 %t4535)
    %t4537 = load i64, i64* %c_v4534
    %t4538 = call i64 @freak_ver_major(i64 %t4537)
    %t4540 = icmp ne i64 %t4536, %t4538
    %t4539 = zext i1 %t4540 to i64
    %t4544 = icmp ne i64 %t4539, 0
    br i1 %t4544, label %if.then.4541, label %if.end.4543
if.then.4541:
    ret i64 0
    br label %if.end.4543
if.end.4543:
    %t4545 = load i64, i64* %v
    %t4546 = load i64, i64* %c_v4534
    %t4547 = call i64 @freak_ver_gte(i64 %t4545, i64 %t4546)
    ret i64 %t4547
    br label %if.end.4530
if.end.4530:
    br label %if.end.4521
if.end.4521:
    %t4548 = load i64, i64* %v
    %t4549 = load i64, i64* %constraint
    %t4550 = call i64 @freak_ver_parse(i64 %t4549)
    %t4551 = call i64 @freak_ver_eq(i64 %t4548, i64 %t4550)
    ret i64 %t4551
    ret i64 0
}

define i64 @freak_ver_satisfies(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4552 = load i64, i64* %version
    %t4553 = call i64 @freak_ver_parse(i64 %t4552)
    %v_v4554 = alloca i64
    store i64 %t4553, i64* %v_v4554
    %t4555 = load i64, i64* %constraint
    %t4556 = call i64 @freak_llvm_word_length(i64 %t4555)
    %clen_v4557 = alloca i64
    store i64 %t4556, i64* %clen_v4557
    %t4558 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.291, i64 0, i64 0
    %t4559 = ptrtoint i8* %t4558 to i64
    %current_v4560 = alloca i64
    store i64 %t4559, i64* %current_v4560
    %i_v4561 = alloca i64
    store i64 0, i64* %i_v4561
    br label %loop.cond.4562
loop.cond.4562:
    %t4565 = load i64, i64* %i_v4561
    %t4566 = load i64, i64* %clen_v4557
    %t4568 = icmp sge i64 %t4565, %t4566
    %t4567 = zext i1 %t4568 to i64
    %t4569 = icmp eq i64 %t4567, 0
    br i1 %t4569, label %loop.body.4563, label %loop.end.4564
loop.body.4563:
    %t4570 = load i64, i64* %constraint
    %t4572 = load i64, i64* %i_v4561
    %t4571 = call i64 @freak_llvm_word_char_at(i64 %t4570, i64 %t4572)
    %ch_v4573 = alloca i64
    store i64 %t4571, i64* %ch_v4573
    %t4574 = load i64, i64* %ch_v4573
    %t4575 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.292, i64 0, i64 0
    %t4576 = ptrtoint i8* %t4575 to i64
    %t4577 = call i64 @freak_llvm_word_eq(i64 %t4574, i64 %t4576)
    %t4581 = icmp ne i64 %t4577, 0
    br i1 %t4581, label %if.then.4578, label %if.else.4579
if.then.4578:
    %t4582 = load i64, i64* %current_v4560
    %t4583 = call i64 @freak_llvm_word_length(i64 %t4582)
    %t4585 = icmp sgt i64 %t4583, 0
    %t4584 = zext i1 %t4585 to i64
    %t4589 = icmp ne i64 %t4584, 0
    br i1 %t4589, label %if.then.4586, label %if.end.4588
if.then.4586:
    %t4590 = load i64, i64* %v_v4554
    %t4591 = load i64, i64* %current_v4560
    %t4592 = call i64 @freak_ver_satisfies_single(i64 %t4590, i64 %t4591)
    %t4594 = icmp eq i64 %t4592, 0
    %t4593 = zext i1 %t4594 to i64
    %t4598 = icmp ne i64 %t4593, 0
    br i1 %t4598, label %if.then.4595, label %if.end.4597
if.then.4595:
    ret i64 0
    br label %if.end.4597
if.end.4597:
    %t4599 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.293, i64 0, i64 0
    %t4600 = ptrtoint i8* %t4599 to i64
    store i64 %t4600, i64* %current_v4560
    br label %if.end.4588
if.end.4588:
    br label %if.end.4580
if.else.4579:
    %t4601 = load i64, i64* %current_v4560
    %t4602 = load i64, i64* %ch_v4573
    %t4603 = call i64 @freak_llvm_word_concat(i64 %t4601, i64 %t4602)
    store i64 %t4603, i64* %current_v4560
    br label %if.end.4580
if.end.4580:
    %t4604 = load i64, i64* %i_v4561
    %t4605 = add i64 %t4604, 1
    store i64 %t4605, i64* %i_v4561
    br label %loop.cond.4562
loop.end.4564:
    %t4606 = load i64, i64* %current_v4560
    %t4607 = call i64 @freak_llvm_word_length(i64 %t4606)
    %t4609 = icmp sgt i64 %t4607, 0
    %t4608 = zext i1 %t4609 to i64
    %t4613 = icmp ne i64 %t4608, 0
    br i1 %t4613, label %if.then.4610, label %if.end.4612
if.then.4610:
    %t4614 = load i64, i64* %v_v4554
    %t4615 = load i64, i64* %current_v4560
    %t4616 = call i64 @freak_ver_satisfies_single(i64 %t4614, i64 %t4615)
    %t4618 = icmp eq i64 %t4616, 0
    %t4617 = zext i1 %t4618 to i64
    %t4622 = icmp ne i64 %t4617, 0
    br i1 %t4622, label %if.then.4619, label %if.end.4621
if.then.4619:
    ret i64 0
    br label %if.end.4621
if.end.4621:
    br label %if.end.4612
if.end.4612:
    ret i64 1
    ret i64 0
}

define i64 @freak_version_matches_constraint(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4623 = load i64, i64* %version
    %t4624 = load i64, i64* %constraint
    %t4625 = call i64 @freak_ver_satisfies(i64 %t4623, i64 %t4624)
    ret i64 %t4625
    ret i64 0
}

define void @freak_http_init() {
entry:
    %t4626 = load i64, i64* @g_http_inited
    %t4628 = icmp eq i64 %t4626, 0
    %t4627 = zext i1 %t4628 to i64
    %t4632 = icmp ne i64 %t4627, 0
    br i1 %t4632, label %if.then.4629, label %if.end.4631
if.then.4629:
    %t4633 = call i64 @freak_llvm_array_new()
    store i64 %t4633, i64* @g_http_resp_statuses
    %t4634 = call i64 @freak_llvm_array_new()
    store i64 %t4634, i64* @g_http_resp_bodies
    %t4635 = call i64 @freak_llvm_array_new()
    store i64 %t4635, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 1, i64* @g_http_inited
    br label %if.end.4631
if.end.4631:
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
    %t4636 = load i64, i64* @g_http_resp_count
    %idx_v4637 = alloca i64
    store i64 %t4636, i64* %idx_v4637
    %t4638 = load i64, i64* @g_http_resp_statuses
    %t4639 = load i64, i64* %status
    %t4640 = call i64 @freak_llvm_word_from_int(i64 %t4639)
    call void @freak_llvm_array_push(i64 %t4638, i64 %t4640)
    %t4641 = load i64, i64* @g_http_resp_bodies
    %t4642 = load i64, i64* %body
    call void @freak_llvm_array_push(i64 %t4641, i64 %t4642)
    %t4643 = load i64, i64* @g_http_resp_headers_raw
    %t4644 = load i64, i64* %headers
    call void @freak_llvm_array_push(i64 %t4643, i64 %t4644)
    %t4645 = load i64, i64* @g_http_resp_count
    %t4646 = add i64 %t4645, 1
    store i64 %t4646, i64* @g_http_resp_count
    %t4647 = load i64, i64* %idx_v4637
    ret i64 %t4647
    ret i64 0
}

define i64 @freak_http_resp_status(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4648 = load i64, i64* @g_http_resp_statuses
    %t4649 = load i64, i64* %handle
    %t4650 = call i64 @freak_llvm_array_get(i64 %t4648, i64 %t4649)
    %v_v4651 = alloca i64
    store i64 %t4650, i64* %v_v4651
    %t4652 = load i64, i64* %v_v4651
    %t4653 = call i64 @freak_llvm_word_to_int(i64 %t4652)
    ret i64 %t4653
    ret i64 0
}

define i64 @freak_http_resp_body(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4654 = load i64, i64* @g_http_resp_bodies
    %t4655 = load i64, i64* %handle
    %t4656 = call i64 @freak_llvm_array_get(i64 %t4654, i64 %t4655)
    ret i64 %t4656
    ret i64 0
}

define i64 @freak_http_resp_headers(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4657 = load i64, i64* @g_http_resp_headers_raw
    %t4658 = load i64, i64* %handle
    %t4659 = call i64 @freak_llvm_array_get(i64 %t4657, i64 %t4658)
    ret i64 %t4659
    ret i64 0
}

define i64 @freak_http_parse_status(i64 %arg_line) {
entry:
    %line = alloca i64
    store i64 %arg_line, i64* %line
    %t4660 = load i64, i64* %line
    %t4661 = call i64 @freak_llvm_word_length(i64 %t4660)
    %slen_v4662 = alloca i64
    store i64 %t4661, i64* %slen_v4662
    %si_v4663 = alloca i64
    store i64 0, i64* %si_v4663
    %t4669 = load i64, i64* %slen_v4662
    %rep.4668 = alloca i64
    store i64 0, i64* %rep.4668
    br label %loop.cond.4664
loop.cond.4664:
    %t4670 = load i64, i64* %rep.4668
    %t4671 = icmp slt i64 %t4670, %t4669
    br i1 %t4671, label %loop.body.4665, label %loop.end.4666
loop.body.4665:
    %t4672 = load i64, i64* %line
    %t4674 = load i64, i64* %si_v4663
    %t4673 = call i64 @freak_llvm_word_char_at(i64 %t4672, i64 %t4674)
    %t4675 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.294, i64 0, i64 0
    %t4676 = ptrtoint i8* %t4675 to i64
    %t4677 = call i64 @freak_llvm_word_eq(i64 %t4673, i64 %t4676)
    %t4681 = icmp ne i64 %t4677, 0
    br i1 %t4681, label %if.then.4678, label %if.end.4680
if.then.4678:
    %t4682 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.295, i64 0, i64 0
    %t4683 = ptrtoint i8* %t4682 to i64
    %code_str_v4684 = alloca i64
    store i64 %t4683, i64* %code_str_v4684
    %t4685 = load i64, i64* %si_v4663
    %t4686 = add i64 %t4685, 1
    %ci_v4687 = alloca i64
    store i64 %t4686, i64* %ci_v4687
    %rep.4692 = alloca i64
    store i64 0, i64* %rep.4692
    br label %loop.cond.4688
loop.cond.4688:
    %t4693 = load i64, i64* %rep.4692
    %t4694 = icmp slt i64 %t4693, 3
    br i1 %t4694, label %loop.body.4689, label %loop.end.4690
loop.body.4689:
    %t4695 = load i64, i64* %ci_v4687
    %t4696 = load i64, i64* %slen_v4662
    %t4698 = icmp slt i64 %t4695, %t4696
    %t4697 = zext i1 %t4698 to i64
    %t4702 = icmp ne i64 %t4697, 0
    br i1 %t4702, label %if.then.4699, label %if.end.4701
if.then.4699:
    %t4703 = load i64, i64* %code_str_v4684
    %t4704 = load i64, i64* %line
    %t4706 = load i64, i64* %ci_v4687
    %t4705 = call i64 @freak_llvm_word_char_at(i64 %t4704, i64 %t4706)
    %t4707 = call i64 @freak_llvm_word_concat(i64 %t4703, i64 %t4705)
    store i64 %t4707, i64* %code_str_v4684
    %t4708 = load i64, i64* %ci_v4687
    %t4709 = add i64 %t4708, 1
    store i64 %t4709, i64* %ci_v4687
    br label %if.end.4701
if.end.4701:
    br label %loop.inc.4691
loop.inc.4691:
    %t4710 = load i64, i64* %rep.4692
    %t4711 = add i64 %t4710, 1
    store i64 %t4711, i64* %rep.4692
    br label %loop.cond.4688
loop.end.4690:
    %t4712 = load i64, i64* %code_str_v4684
    %t4713 = call i64 @freak_llvm_word_to_int(i64 %t4712)
    ret i64 %t4713
    br label %if.end.4680
if.end.4680:
    %t4714 = load i64, i64* %si_v4663
    %t4715 = add i64 %t4714, 1
    store i64 %t4715, i64* %si_v4663
    br label %loop.inc.4667
loop.inc.4667:
    %t4716 = load i64, i64* %rep.4668
    %t4717 = add i64 %t4716, 1
    store i64 %t4717, i64* %rep.4668
    br label %loop.cond.4664
loop.end.4666:
    ret i64 0
    ret i64 0
}

define i64 @freak_http_split_response(i64 %arg_raw) {
entry:
    %raw = alloca i64
    store i64 %arg_raw, i64* %raw
    %t4718 = load i64, i64* %raw
    %t4719 = call i64 @freak_llvm_word_length(i64 %t4718)
    %rlen_v4720 = alloca i64
    store i64 %t4719, i64* %rlen_v4720
    %ri_v4721 = alloca i64
    store i64 0, i64* %ri_v4721
    %t4722 = sub i64 0, 1
    %header_end_v4723 = alloca i64
    store i64 %t4722, i64* %header_end_v4723
    %t4724 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.296, i64 0, i64 0
    %t4725 = ptrtoint i8* %t4724 to i64
    %prev3_v4726 = alloca i64
    store i64 %t4725, i64* %prev3_v4726
    %t4727 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.297, i64 0, i64 0
    %t4728 = ptrtoint i8* %t4727 to i64
    %prev2_v4729 = alloca i64
    store i64 %t4728, i64* %prev2_v4729
    %t4730 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.298, i64 0, i64 0
    %t4731 = ptrtoint i8* %t4730 to i64
    %prev1_v4732 = alloca i64
    store i64 %t4731, i64* %prev1_v4732
    %t4738 = load i64, i64* %rlen_v4720
    %rep.4737 = alloca i64
    store i64 0, i64* %rep.4737
    br label %loop.cond.4733
loop.cond.4733:
    %t4739 = load i64, i64* %rep.4737
    %t4740 = icmp slt i64 %t4739, %t4738
    br i1 %t4740, label %loop.body.4734, label %loop.end.4735
loop.body.4734:
    %t4741 = load i64, i64* %raw
    %t4743 = load i64, i64* %ri_v4721
    %t4742 = call i64 @freak_llvm_word_char_at(i64 %t4741, i64 %t4743)
    %ch_v4744 = alloca i64
    store i64 %t4742, i64* %ch_v4744
    %t4745 = load i64, i64* %prev2_v4729
    %t4746 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.299, i64 0, i64 0
    %t4747 = ptrtoint i8* %t4746 to i64
    %t4748 = call i64 @freak_llvm_word_eq(i64 %t4745, i64 %t4747)
    %t4749 = load i64, i64* %prev1_v4732
    %t4750 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.300, i64 0, i64 0
    %t4751 = ptrtoint i8* %t4750 to i64
    %t4752 = call i64 @freak_llvm_word_eq(i64 %t4749, i64 %t4751)
    %t4754 = icmp ne i64 %t4748, 0
    %t4755 = icmp ne i64 %t4752, 0
    %t4756 = and i1 %t4754, %t4755
    %t4753 = zext i1 %t4756 to i64
    %t4757 = load i64, i64* %ch_v4744
    %t4758 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.301, i64 0, i64 0
    %t4759 = ptrtoint i8* %t4758 to i64
    %t4760 = call i64 @freak_llvm_word_eq(i64 %t4757, i64 %t4759)
    %t4762 = icmp ne i64 %t4753, 0
    %t4763 = icmp ne i64 %t4760, 0
    %t4764 = and i1 %t4762, %t4763
    %t4761 = zext i1 %t4764 to i64
    %t4768 = icmp ne i64 %t4761, 0
    br i1 %t4768, label %if.then.4765, label %if.end.4767
if.then.4765:
    %t4769 = load i64, i64* %ri_v4721
    %t4770 = add i64 %t4769, 1
    store i64 %t4770, i64* %header_end_v4723
    br label %if.end.4767
if.end.4767:
    %t4771 = load i64, i64* %prev3_v4726
    %t4772 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.302, i64 0, i64 0
    %t4773 = ptrtoint i8* %t4772 to i64
    %t4774 = call i64 @freak_llvm_word_eq(i64 %t4771, i64 %t4773)
    %t4775 = load i64, i64* %prev2_v4729
    %t4776 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.303, i64 0, i64 0
    %t4777 = ptrtoint i8* %t4776 to i64
    %t4778 = call i64 @freak_llvm_word_eq(i64 %t4775, i64 %t4777)
    %t4780 = icmp ne i64 %t4774, 0
    %t4781 = icmp ne i64 %t4778, 0
    %t4782 = and i1 %t4780, %t4781
    %t4779 = zext i1 %t4782 to i64
    %t4783 = load i64, i64* %prev1_v4732
    %t4784 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.304, i64 0, i64 0
    %t4785 = ptrtoint i8* %t4784 to i64
    %t4786 = call i64 @freak_llvm_word_eq(i64 %t4783, i64 %t4785)
    %t4788 = icmp ne i64 %t4779, 0
    %t4789 = icmp ne i64 %t4786, 0
    %t4790 = and i1 %t4788, %t4789
    %t4787 = zext i1 %t4790 to i64
    %t4791 = load i64, i64* %ch_v4744
    %t4792 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.305, i64 0, i64 0
    %t4793 = ptrtoint i8* %t4792 to i64
    %t4794 = call i64 @freak_llvm_word_eq(i64 %t4791, i64 %t4793)
    %t4796 = icmp ne i64 %t4787, 0
    %t4797 = icmp ne i64 %t4794, 0
    %t4798 = and i1 %t4796, %t4797
    %t4795 = zext i1 %t4798 to i64
    %t4802 = icmp ne i64 %t4795, 0
    br i1 %t4802, label %if.then.4799, label %if.end.4801
if.then.4799:
    %t4803 = load i64, i64* %ri_v4721
    %t4804 = add i64 %t4803, 1
    store i64 %t4804, i64* %header_end_v4723
    br label %if.end.4801
if.end.4801:
    %t4805 = load i64, i64* %prev2_v4729
    store i64 %t4805, i64* %prev3_v4726
    %t4806 = load i64, i64* %prev1_v4732
    store i64 %t4806, i64* %prev2_v4729
    %t4807 = load i64, i64* %ch_v4744
    store i64 %t4807, i64* %prev1_v4732
    %t4808 = load i64, i64* %ri_v4721
    %t4809 = add i64 %t4808, 1
    store i64 %t4809, i64* %ri_v4721
    br label %loop.inc.4736
loop.inc.4736:
    %t4810 = load i64, i64* %rep.4737
    %t4811 = add i64 %t4810, 1
    store i64 %t4811, i64* %rep.4737
    br label %loop.cond.4733
loop.end.4735:
    %t4812 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.306, i64 0, i64 0
    %t4813 = ptrtoint i8* %t4812 to i64
    %status_line_v4814 = alloca i64
    store i64 %t4813, i64* %status_line_v4814
    %li_v4815 = alloca i64
    store i64 0, i64* %li_v4815
    %t4821 = load i64, i64* %rlen_v4720
    %rep.4820 = alloca i64
    store i64 0, i64* %rep.4820
    br label %loop.cond.4816
loop.cond.4816:
    %t4822 = load i64, i64* %rep.4820
    %t4823 = icmp slt i64 %t4822, %t4821
    br i1 %t4823, label %loop.body.4817, label %loop.end.4818
loop.body.4817:
    %t4824 = load i64, i64* %raw
    %t4826 = load i64, i64* %li_v4815
    %t4825 = call i64 @freak_llvm_word_char_at(i64 %t4824, i64 %t4826)
    %lc_v4827 = alloca i64
    store i64 %t4825, i64* %lc_v4827
    %t4828 = load i64, i64* %lc_v4827
    %t4829 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.307, i64 0, i64 0
    %t4830 = ptrtoint i8* %t4829 to i64
    %t4831 = call i64 @freak_llvm_word_eq(i64 %t4828, i64 %t4830)
    %t4832 = load i64, i64* %lc_v4827
    %t4833 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.308, i64 0, i64 0
    %t4834 = ptrtoint i8* %t4833 to i64
    %t4835 = call i64 @freak_llvm_word_eq(i64 %t4832, i64 %t4834)
    %t4837 = icmp ne i64 %t4831, 0
    %t4838 = icmp ne i64 %t4835, 0
    %t4839 = or i1 %t4837, %t4838
    %t4836 = zext i1 %t4839 to i64
    %t4843 = icmp ne i64 %t4836, 0
    br i1 %t4843, label %if.then.4840, label %if.else.4841
if.then.4840:
    %t4844 = load i64, i64* %rlen_v4720
    store i64 %t4844, i64* %li_v4815
    br label %if.end.4842
if.else.4841:
    %t4845 = load i64, i64* %status_line_v4814
    %t4846 = load i64, i64* %lc_v4827
    %t4847 = call i64 @freak_llvm_word_concat(i64 %t4845, i64 %t4846)
    store i64 %t4847, i64* %status_line_v4814
    br label %if.end.4842
if.end.4842:
    %t4848 = load i64, i64* %li_v4815
    %t4849 = add i64 %t4848, 1
    store i64 %t4849, i64* %li_v4815
    br label %loop.inc.4819
loop.inc.4819:
    %t4850 = load i64, i64* %rep.4820
    %t4851 = add i64 %t4850, 1
    store i64 %t4851, i64* %rep.4820
    br label %loop.cond.4816
loop.end.4818:
    %t4852 = load i64, i64* %status_line_v4814
    %t4853 = call i64 @freak_http_parse_status(i64 %t4852)
    %status_v4854 = alloca i64
    store i64 %t4853, i64* %status_v4854
    %t4855 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.309, i64 0, i64 0
    %t4856 = ptrtoint i8* %t4855 to i64
    %headers_v4857 = alloca i64
    store i64 %t4856, i64* %headers_v4857
    %t4858 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.310, i64 0, i64 0
    %t4859 = ptrtoint i8* %t4858 to i64
    %body_v4860 = alloca i64
    store i64 %t4859, i64* %body_v4860
    %t4861 = load i64, i64* %header_end_v4723
    %t4863 = icmp sgt i64 %t4861, 0
    %t4862 = zext i1 %t4863 to i64
    %t4867 = icmp ne i64 %t4862, 0
    br i1 %t4867, label %if.then.4864, label %if.else.4865
if.then.4864:
    %hi_v4868 = alloca i64
    store i64 0, i64* %hi_v4868
    %t4874 = load i64, i64* %header_end_v4723
    %rep.4873 = alloca i64
    store i64 0, i64* %rep.4873
    br label %loop.cond.4869
loop.cond.4869:
    %t4875 = load i64, i64* %rep.4873
    %t4876 = icmp slt i64 %t4875, %t4874
    br i1 %t4876, label %loop.body.4870, label %loop.end.4871
loop.body.4870:
    %t4877 = load i64, i64* %hi_v4868
    %t4878 = load i64, i64* %rlen_v4720
    %t4880 = icmp slt i64 %t4877, %t4878
    %t4879 = zext i1 %t4880 to i64
    %t4884 = icmp ne i64 %t4879, 0
    br i1 %t4884, label %if.then.4881, label %if.end.4883
if.then.4881:
    %t4885 = load i64, i64* %headers_v4857
    %t4886 = load i64, i64* %raw
    %t4888 = load i64, i64* %hi_v4868
    %t4887 = call i64 @freak_llvm_word_char_at(i64 %t4886, i64 %t4888)
    %t4889 = call i64 @freak_llvm_word_concat(i64 %t4885, i64 %t4887)
    store i64 %t4889, i64* %headers_v4857
    br label %if.end.4883
if.end.4883:
    %t4890 = load i64, i64* %hi_v4868
    %t4891 = add i64 %t4890, 1
    store i64 %t4891, i64* %hi_v4868
    br label %loop.inc.4872
loop.inc.4872:
    %t4892 = load i64, i64* %rep.4873
    %t4893 = add i64 %t4892, 1
    store i64 %t4893, i64* %rep.4873
    br label %loop.cond.4869
loop.end.4871:
    %t4894 = load i64, i64* %header_end_v4723
    %bi_v4895 = alloca i64
    store i64 %t4894, i64* %bi_v4895
    %t4901 = load i64, i64* %rlen_v4720
    %rep.4900 = alloca i64
    store i64 0, i64* %rep.4900
    br label %loop.cond.4896
loop.cond.4896:
    %t4902 = load i64, i64* %rep.4900
    %t4903 = icmp slt i64 %t4902, %t4901
    br i1 %t4903, label %loop.body.4897, label %loop.end.4898
loop.body.4897:
    %t4904 = load i64, i64* %bi_v4895
    %t4905 = load i64, i64* %rlen_v4720
    %t4907 = icmp slt i64 %t4904, %t4905
    %t4906 = zext i1 %t4907 to i64
    %t4911 = icmp ne i64 %t4906, 0
    br i1 %t4911, label %if.then.4908, label %if.end.4910
if.then.4908:
    %t4912 = load i64, i64* %body_v4860
    %t4913 = load i64, i64* %raw
    %t4915 = load i64, i64* %bi_v4895
    %t4914 = call i64 @freak_llvm_word_char_at(i64 %t4913, i64 %t4915)
    %t4916 = call i64 @freak_llvm_word_concat(i64 %t4912, i64 %t4914)
    store i64 %t4916, i64* %body_v4860
    br label %if.end.4910
if.end.4910:
    %t4917 = load i64, i64* %bi_v4895
    %t4918 = add i64 %t4917, 1
    store i64 %t4918, i64* %bi_v4895
    br label %loop.inc.4899
loop.inc.4899:
    %t4919 = load i64, i64* %rep.4900
    %t4920 = add i64 %t4919, 1
    store i64 %t4920, i64* %rep.4900
    br label %loop.cond.4896
loop.end.4898:
    br label %if.end.4866
if.else.4865:
    %t4921 = load i64, i64* %raw
    store i64 %t4921, i64* %headers_v4857
    br label %if.end.4866
if.end.4866:
    %t4922 = load i64, i64* %status_v4854
    %t4923 = load i64, i64* %body_v4860
    %t4924 = load i64, i64* %headers_v4857
    %t4925 = call i64 @freak_http_alloc_resp(i64 %t4922, i64 %t4923, i64 %t4924)
    ret i64 %t4925
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
    %t4926 = load i64, i64* %host
    %t4927 = load i64, i64* %port
    %t4928 = call i64 @freak_llvm_tcp_connect(i64 %t4926, i64 %t4927)
    %fd_v4929 = alloca i64
    store i64 %t4928, i64* %fd_v4929
    %t4930 = load i64, i64* %fd_v4929
    %t4932 = icmp slt i64 %t4930, 0
    %t4931 = zext i1 %t4932 to i64
    %t4936 = icmp ne i64 %t4931, 0
    br i1 %t4936, label %if.then.4933, label %if.end.4935
if.then.4933:
    %t4937 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.311, i64 0, i64 0
    %t4938 = ptrtoint i8* %t4937 to i64
    %t4939 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.312, i64 0, i64 0
    %t4940 = ptrtoint i8* %t4939 to i64
    %t4941 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4938, i64 %t4940)
    ret i64 %t4941
    br label %if.end.4935
if.end.4935:
    %t4942 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.313, i64 0, i64 0
    %t4943 = ptrtoint i8* %t4942 to i64
    %t4944 = load i64, i64* %path
    %t4945 = call i64 @freak_llvm_word_concat(i64 %t4943, i64 %t4944)
    %t4946 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.314, i64 0, i64 0
    %t4947 = ptrtoint i8* %t4946 to i64
    %t4948 = call i64 @freak_llvm_word_concat(i64 %t4945, i64 %t4947)
    %t4949 = load i64, i64* %host
    %t4950 = call i64 @freak_llvm_word_concat(i64 %t4948, i64 %t4949)
    %t4951 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.315, i64 0, i64 0
    %t4952 = ptrtoint i8* %t4951 to i64
    %t4953 = call i64 @freak_llvm_word_concat(i64 %t4950, i64 %t4952)
    %req_v4954 = alloca i64
    store i64 %t4953, i64* %req_v4954
    %t4955 = load i64, i64* %fd_v4929
    %t4956 = load i64, i64* %req_v4954
    %t4957 = call i64 @freak_llvm_tcp_send(i64 %t4955, i64 %t4956)
    %t4958 = load i64, i64* %fd_v4929
    %t4959 = call i64 @freak_llvm_tcp_recv_all(i64 %t4958, i64 65536)
    %raw_v4960 = alloca i64
    store i64 %t4959, i64* %raw_v4960
    %t4961 = load i64, i64* %fd_v4929
    call void @freak_llvm_tcp_close(i64 %t4961)
    %t4962 = load i64, i64* %raw_v4960
    %t4963 = call i64 @freak_http_split_response(i64 %t4962)
    ret i64 %t4963
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
    %t4964 = load i64, i64* %host
    %t4965 = load i64, i64* %port
    %t4966 = call i64 @freak_llvm_tcp_connect(i64 %t4964, i64 %t4965)
    %fd_v4967 = alloca i64
    store i64 %t4966, i64* %fd_v4967
    %t4968 = load i64, i64* %fd_v4967
    %t4970 = icmp slt i64 %t4968, 0
    %t4969 = zext i1 %t4970 to i64
    %t4974 = icmp ne i64 %t4969, 0
    br i1 %t4974, label %if.then.4971, label %if.end.4973
if.then.4971:
    %t4975 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.316, i64 0, i64 0
    %t4976 = ptrtoint i8* %t4975 to i64
    %t4977 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.317, i64 0, i64 0
    %t4978 = ptrtoint i8* %t4977 to i64
    %t4979 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4976, i64 %t4978)
    ret i64 %t4979
    br label %if.end.4973
if.end.4973:
    %t4980 = load i64, i64* %body
    %t4981 = call i64 @freak_llvm_word_length(i64 %t4980)
    %t4982 = call i64 @freak_llvm_word_from_int(i64 %t4981)
    %body_len_v4983 = alloca i64
    store i64 %t4982, i64* %body_len_v4983
    %t4984 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.318, i64 0, i64 0
    %t4985 = ptrtoint i8* %t4984 to i64
    %t4986 = load i64, i64* %path
    %t4987 = call i64 @freak_llvm_word_concat(i64 %t4985, i64 %t4986)
    %t4988 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.319, i64 0, i64 0
    %t4989 = ptrtoint i8* %t4988 to i64
    %t4990 = call i64 @freak_llvm_word_concat(i64 %t4987, i64 %t4989)
    %t4991 = load i64, i64* %host
    %t4992 = call i64 @freak_llvm_word_concat(i64 %t4990, i64 %t4991)
    %t4993 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.320, i64 0, i64 0
    %t4994 = ptrtoint i8* %t4993 to i64
    %t4995 = call i64 @freak_llvm_word_concat(i64 %t4992, i64 %t4994)
    %t4996 = load i64, i64* %content_type
    %t4997 = call i64 @freak_llvm_word_concat(i64 %t4995, i64 %t4996)
    %t4998 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.321, i64 0, i64 0
    %t4999 = ptrtoint i8* %t4998 to i64
    %t5000 = call i64 @freak_llvm_word_concat(i64 %t4997, i64 %t4999)
    %t5001 = load i64, i64* %body_len_v4983
    %t5002 = call i64 @freak_llvm_word_concat(i64 %t5000, i64 %t5001)
    %t5003 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.322, i64 0, i64 0
    %t5004 = ptrtoint i8* %t5003 to i64
    %t5005 = call i64 @freak_llvm_word_concat(i64 %t5002, i64 %t5004)
    %t5006 = load i64, i64* %body
    %t5007 = call i64 @freak_llvm_word_concat(i64 %t5005, i64 %t5006)
    %req_v5008 = alloca i64
    store i64 %t5007, i64* %req_v5008
    %t5009 = load i64, i64* %fd_v4967
    %t5010 = load i64, i64* %req_v5008
    %t5011 = call i64 @freak_llvm_tcp_send(i64 %t5009, i64 %t5010)
    %t5012 = load i64, i64* %fd_v4967
    %t5013 = call i64 @freak_llvm_tcp_recv_all(i64 %t5012, i64 65536)
    %raw_v5014 = alloca i64
    store i64 %t5013, i64* %raw_v5014
    %t5015 = load i64, i64* %fd_v4967
    call void @freak_llvm_tcp_close(i64 %t5015)
    %t5016 = load i64, i64* %raw_v5014
    %t5017 = call i64 @freak_http_split_response(i64 %t5016)
    ret i64 %t5017
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
    %t5018 = load i64, i64* %host
    %t5019 = load i64, i64* %port
    %t5020 = call i64 @freak_llvm_tcp_connect(i64 %t5018, i64 %t5019)
    %fd_v5021 = alloca i64
    store i64 %t5020, i64* %fd_v5021
    %t5022 = load i64, i64* %fd_v5021
    %t5024 = icmp slt i64 %t5022, 0
    %t5023 = zext i1 %t5024 to i64
    %t5028 = icmp ne i64 %t5023, 0
    br i1 %t5028, label %if.then.5025, label %if.end.5027
if.then.5025:
    %t5029 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.323, i64 0, i64 0
    %t5030 = ptrtoint i8* %t5029 to i64
    %t5031 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.324, i64 0, i64 0
    %t5032 = ptrtoint i8* %t5031 to i64
    %t5033 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5030, i64 %t5032)
    ret i64 %t5033
    br label %if.end.5027
if.end.5027:
    %t5034 = load i64, i64* %body
    %t5035 = call i64 @freak_llvm_word_length(i64 %t5034)
    %t5036 = call i64 @freak_llvm_word_from_int(i64 %t5035)
    %body_len_v5037 = alloca i64
    store i64 %t5036, i64* %body_len_v5037
    %t5038 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.325, i64 0, i64 0
    %t5039 = ptrtoint i8* %t5038 to i64
    %t5040 = load i64, i64* %path
    %t5041 = call i64 @freak_llvm_word_concat(i64 %t5039, i64 %t5040)
    %t5042 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.326, i64 0, i64 0
    %t5043 = ptrtoint i8* %t5042 to i64
    %t5044 = call i64 @freak_llvm_word_concat(i64 %t5041, i64 %t5043)
    %t5045 = load i64, i64* %host
    %t5046 = call i64 @freak_llvm_word_concat(i64 %t5044, i64 %t5045)
    %t5047 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.327, i64 0, i64 0
    %t5048 = ptrtoint i8* %t5047 to i64
    %t5049 = call i64 @freak_llvm_word_concat(i64 %t5046, i64 %t5048)
    %t5050 = load i64, i64* %content_type
    %t5051 = call i64 @freak_llvm_word_concat(i64 %t5049, i64 %t5050)
    %t5052 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.328, i64 0, i64 0
    %t5053 = ptrtoint i8* %t5052 to i64
    %t5054 = call i64 @freak_llvm_word_concat(i64 %t5051, i64 %t5053)
    %t5055 = load i64, i64* %body_len_v5037
    %t5056 = call i64 @freak_llvm_word_concat(i64 %t5054, i64 %t5055)
    %t5057 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.329, i64 0, i64 0
    %t5058 = ptrtoint i8* %t5057 to i64
    %t5059 = call i64 @freak_llvm_word_concat(i64 %t5056, i64 %t5058)
    %t5060 = load i64, i64* %body
    %t5061 = call i64 @freak_llvm_word_concat(i64 %t5059, i64 %t5060)
    %req_v5062 = alloca i64
    store i64 %t5061, i64* %req_v5062
    %t5063 = load i64, i64* %fd_v5021
    %t5064 = load i64, i64* %req_v5062
    %t5065 = call i64 @freak_llvm_tcp_send(i64 %t5063, i64 %t5064)
    %t5066 = load i64, i64* %fd_v5021
    %t5067 = call i64 @freak_llvm_tcp_recv_all(i64 %t5066, i64 65536)
    %raw_v5068 = alloca i64
    store i64 %t5067, i64* %raw_v5068
    %t5069 = load i64, i64* %fd_v5021
    call void @freak_llvm_tcp_close(i64 %t5069)
    %t5070 = load i64, i64* %raw_v5068
    %t5071 = call i64 @freak_http_split_response(i64 %t5070)
    ret i64 %t5071
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
    %t5072 = load i64, i64* %host
    %t5073 = load i64, i64* %port
    %t5074 = call i64 @freak_llvm_tcp_connect(i64 %t5072, i64 %t5073)
    %fd_v5075 = alloca i64
    store i64 %t5074, i64* %fd_v5075
    %t5076 = load i64, i64* %fd_v5075
    %t5078 = icmp slt i64 %t5076, 0
    %t5077 = zext i1 %t5078 to i64
    %t5082 = icmp ne i64 %t5077, 0
    br i1 %t5082, label %if.then.5079, label %if.end.5081
if.then.5079:
    %t5083 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.330, i64 0, i64 0
    %t5084 = ptrtoint i8* %t5083 to i64
    %t5085 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.331, i64 0, i64 0
    %t5086 = ptrtoint i8* %t5085 to i64
    %t5087 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5084, i64 %t5086)
    ret i64 %t5087
    br label %if.end.5081
if.end.5081:
    %t5088 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.332, i64 0, i64 0
    %t5089 = ptrtoint i8* %t5088 to i64
    %t5090 = load i64, i64* %path
    %t5091 = call i64 @freak_llvm_word_concat(i64 %t5089, i64 %t5090)
    %t5092 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.333, i64 0, i64 0
    %t5093 = ptrtoint i8* %t5092 to i64
    %t5094 = call i64 @freak_llvm_word_concat(i64 %t5091, i64 %t5093)
    %t5095 = load i64, i64* %host
    %t5096 = call i64 @freak_llvm_word_concat(i64 %t5094, i64 %t5095)
    %t5097 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.334, i64 0, i64 0
    %t5098 = ptrtoint i8* %t5097 to i64
    %t5099 = call i64 @freak_llvm_word_concat(i64 %t5096, i64 %t5098)
    %req_v5100 = alloca i64
    store i64 %t5099, i64* %req_v5100
    %t5101 = load i64, i64* %fd_v5075
    %t5102 = load i64, i64* %req_v5100
    %t5103 = call i64 @freak_llvm_tcp_send(i64 %t5101, i64 %t5102)
    %t5104 = load i64, i64* %fd_v5075
    %t5105 = call i64 @freak_llvm_tcp_recv_all(i64 %t5104, i64 65536)
    %raw_v5106 = alloca i64
    store i64 %t5105, i64* %raw_v5106
    %t5107 = load i64, i64* %fd_v5075
    call void @freak_llvm_tcp_close(i64 %t5107)
    %t5108 = load i64, i64* %raw_v5106
    %t5109 = call i64 @freak_http_split_response(i64 %t5108)
    ret i64 %t5109
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
    %t5110 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.335, i64 0, i64 0
    %t5111 = ptrtoint i8* %t5110 to i64
    store i64 %t5111, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    store i64 0, i64* @g_json_len
    store i64 0, i64* @g_http_resp_statuses
    store i64 0, i64* @g_http_resp_bodies
    store i64 0, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 0, i64* @g_http_inited
    %t5112 = sub i64 0, 42
    %t5113 = call i64 @freak_std_abs(i64 %t5112)
    %t5114 = call i64 @freak_llvm_word_from_int(i64 %t5113)
    call void @freak_llvm_say(i64 %t5114)
    %t5115 = call i64 @freak_std_abs(i64 7)
    %t5116 = call i64 @freak_llvm_word_from_int(i64 %t5115)
    call void @freak_llvm_say(i64 %t5116)
    %t5117 = call i64 @freak_std_pow(i64 2, i64 10)
    %t5118 = call i64 @freak_llvm_word_from_int(i64 %t5117)
    call void @freak_llvm_say(i64 %t5118)
    %t5119 = call i64 @freak_std_max(i64 42, i64 17)
    %t5120 = call i64 @freak_llvm_word_from_int(i64 %t5119)
    call void @freak_llvm_say(i64 %t5120)
    %t5121 = call i64 @freak_std_min(i64 42, i64 17)
    %t5122 = call i64 @freak_llvm_word_from_int(i64 %t5121)
    call void @freak_llvm_say(i64 %t5122)
    %t5123 = call i64 @freak_std_clamp(i64 15, i64 0, i64 10)
    %t5124 = call i64 @freak_llvm_word_from_int(i64 %t5123)
    call void @freak_llvm_say(i64 %t5124)
    %t5125 = sub i64 0, 5
    %t5126 = call i64 @freak_std_clamp(i64 %t5125, i64 0, i64 10)
    %t5127 = call i64 @freak_llvm_word_from_int(i64 %t5126)
    call void @freak_llvm_say(i64 %t5127)
    %t5128 = call i64 @freak_std_gcd(i64 48, i64 18)
    %t5129 = call i64 @freak_llvm_word_from_int(i64 %t5128)
    call void @freak_llvm_say(i64 %t5129)
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

