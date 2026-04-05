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
@g_count = global i64 0
@g_power = global i64 0
@g_i = global i64 0

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
    store i64 2, i64* @g_i
    br label %loop.cond.268
loop.cond.268:
    %t271 = load i64, i64* @g_i
    %t272 = load i64, i64* %n
    %t274 = icmp sgt i64 %t271, %t272
    %t273 = zext i1 %t274 to i64
    %t275 = icmp eq i64 %t273, 0
    br i1 %t275, label %loop.body.269, label %loop.end.270
loop.body.269:
    %t276 = load i64, i64* %f_v267
    %t277 = load i64, i64* @g_i
    %t278 = mul i64 %t276, %t277
    store i64 %t278, i64* %f_v267
    %t279 = load i64, i64* @g_i
    %t280 = add i64 %t279, 1
    store i64 %t280, i64* @g_i
    br label %loop.cond.268
loop.end.270:
    %t281 = load i64, i64* %f_v267
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
    store i64 2, i64* @g_i
    br label %loop.cond.298
loop.cond.298:
    %t301 = load i64, i64* @g_i
    %t302 = load i64, i64* %n
    %t304 = icmp sgt i64 %t301, %t302
    %t303 = zext i1 %t304 to i64
    %t305 = icmp eq i64 %t303, 0
    br i1 %t305, label %loop.body.299, label %loop.end.300
loop.body.299:
    %t306 = load i64, i64* %a_v296
    %t307 = load i64, i64* %b_v297
    %t308 = add i64 %t306, %t307
    %tmp_v309 = alloca i64
    store i64 %t308, i64* %tmp_v309
    %t310 = load i64, i64* %b_v297
    store i64 %t310, i64* %a_v296
    %t311 = load i64, i64* %tmp_v309
    store i64 %t311, i64* %b_v297
    %t312 = load i64, i64* @g_i
    %t313 = add i64 %t312, 1
    store i64 %t313, i64* @g_i
    br label %loop.cond.298
loop.end.300:
    %t314 = load i64, i64* %b_v297
    ret i64 %t314
    ret i64 0
}

define i64 @freak_std_is_even(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t315 = load i64, i64* %x
    %t316 = sdiv i64 %t315, 2
    %half_v317 = alloca i64
    store i64 %t316, i64* %half_v317
    %t318 = load i64, i64* %half_v317
    %t319 = mul i64 %t318, 2
    %t320 = load i64, i64* %x
    %t322 = icmp eq i64 %t319, %t320
    %t321 = zext i1 %t322 to i64
    ret i64 %t321
    ret i64 0
}

define i64 @freak_std_is_odd(i64 %arg_x) {
entry:
    %x = alloca i64
    store i64 %arg_x, i64* %x
    %t323 = load i64, i64* %x
    %t324 = call i64 @freak_std_is_even(i64 %t323)
    %t326 = icmp eq i64 %t324, 0
    %t325 = zext i1 %t326 to i64
    ret i64 %t325
    ret i64 0
}

define i64 @freak_string_repeat(i64 %arg_s, i64 %arg_count) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %count = alloca i64
    store i64 %arg_count, i64* %count
    %t327 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.7, i64 0, i64 0
    %t328 = ptrtoint i8* %t327 to i64
    %out_v329 = alloca i64
    store i64 %t328, i64* %out_v329
    store i64 0, i64* @g_i
    %t335 = load i64, i64* @g_count
    %rep.334 = alloca i64
    store i64 0, i64* %rep.334
    br label %loop.cond.330
loop.cond.330:
    %t336 = load i64, i64* %rep.334
    %t337 = icmp slt i64 %t336, %t335
    br i1 %t337, label %loop.body.331, label %loop.end.332
loop.body.331:
    %t338 = load i64, i64* %out_v329
    %t339 = load i64, i64* %s
    %t340 = call i64 @freak_llvm_word_concat(i64 %t338, i64 %t339)
    store i64 %t340, i64* %out_v329
    %t341 = load i64, i64* @g_i
    %t342 = add i64 %t341, 1
    store i64 %t342, i64* @g_i
    br label %loop.inc.333
loop.inc.333:
    %t343 = load i64, i64* %rep.334
    %t344 = add i64 %t343, 1
    store i64 %t344, i64* %rep.334
    br label %loop.cond.330
loop.end.332:
    %t345 = load i64, i64* %out_v329
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
    store i64 %t407, i64* @g_i
    %t413 = load i64, i64* %slen_v394
    %rep.412 = alloca i64
    store i64 0, i64* %rep.412
    br label %loop.cond.408
loop.cond.408:
    %t414 = load i64, i64* %rep.412
    %t415 = icmp slt i64 %t414, %t413
    br i1 %t415, label %loop.body.409, label %loop.end.410
loop.body.409:
    %t416 = load i64, i64* %out_v405
    %t417 = load i64, i64* %s
    %t419 = load i64, i64* @g_i
    %t418 = call i64 @freak_llvm_word_char_at(i64 %t417, i64 %t419)
    %t420 = call i64 @freak_llvm_word_concat(i64 %t416, i64 %t418)
    store i64 %t420, i64* %out_v405
    %t421 = load i64, i64* @g_i
    %t422 = sub i64 %t421, 1
    store i64 %t422, i64* @g_i
    br label %loop.inc.411
loop.inc.411:
    %t423 = load i64, i64* %rep.412
    %t424 = add i64 %t423, 1
    store i64 %t424, i64* %rep.412
    br label %loop.cond.408
loop.end.410:
    %t425 = load i64, i64* %out_v405
    ret i64 %t425
    ret i64 0
}

define i64 @freak_string_count(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t426 = load i64, i64* %haystack
    %t427 = call i64 @freak_llvm_word_length(i64 %t426)
    %hlen_v428 = alloca i64
    store i64 %t427, i64* %hlen_v428
    %t429 = load i64, i64* %needle
    %t430 = call i64 @freak_llvm_word_length(i64 %t429)
    %nlen_v431 = alloca i64
    store i64 %t430, i64* %nlen_v431
    %t432 = load i64, i64* %nlen_v431
    %t434 = icmp eq i64 %t432, 0
    %t433 = zext i1 %t434 to i64
    %t438 = icmp ne i64 %t433, 0
    br i1 %t438, label %if.then.435, label %if.end.437
if.then.435:
    ret i64 0
    br label %if.end.437
if.end.437:
    %t439 = load i64, i64* %nlen_v431
    %t440 = load i64, i64* %hlen_v428
    %t442 = icmp sgt i64 %t439, %t440
    %t441 = zext i1 %t442 to i64
    %t446 = icmp ne i64 %t441, 0
    br i1 %t446, label %if.then.443, label %if.end.445
if.then.443:
    ret i64 0
    br label %if.end.445
if.end.445:
    store i64 0, i64* @g_count
    store i64 0, i64* @g_i
    %t447 = load i64, i64* %hlen_v428
    %t448 = load i64, i64* %nlen_v431
    %t449 = sub i64 %t447, %t448
    %t450 = add i64 %t449, 1
    %limit_v451 = alloca i64
    store i64 %t450, i64* %limit_v451
    %t457 = load i64, i64* %limit_v451
    %rep.456 = alloca i64
    store i64 0, i64* %rep.456
    br label %loop.cond.452
loop.cond.452:
    %t458 = load i64, i64* %rep.456
    %t459 = icmp slt i64 %t458, %t457
    br i1 %t459, label %loop.body.453, label %loop.end.454
loop.body.453:
    %match_v460 = alloca i64
    store i64 1, i64* %match_v460
    %j_v461 = alloca i64
    store i64 0, i64* %j_v461
    %t467 = load i64, i64* %nlen_v431
    %rep.466 = alloca i64
    store i64 0, i64* %rep.466
    br label %loop.cond.462
loop.cond.462:
    %t468 = load i64, i64* %rep.466
    %t469 = icmp slt i64 %t468, %t467
    br i1 %t469, label %loop.body.463, label %loop.end.464
loop.body.463:
    %t470 = load i64, i64* %match_v460
    %t474 = icmp ne i64 %t470, 0
    br i1 %t474, label %if.then.471, label %if.end.473
if.then.471:
    %t475 = load i64, i64* %haystack
    %t477 = load i64, i64* @g_i
    %t478 = load i64, i64* %j_v461
    %t479 = add i64 %t477, %t478
    %t476 = call i64 @freak_llvm_word_char_at(i64 %t475, i64 %t479)
    %t480 = load i64, i64* %needle
    %t482 = load i64, i64* %j_v461
    %t481 = call i64 @freak_llvm_word_char_at(i64 %t480, i64 %t482)
    %t483 = call i64 @freak_llvm_word_neq(i64 %t476, i64 %t481)
    %t487 = icmp ne i64 %t483, 0
    br i1 %t487, label %if.then.484, label %if.end.486
if.then.484:
    store i64 0, i64* %match_v460
    br label %if.end.486
if.end.486:
    br label %if.end.473
if.end.473:
    %t488 = load i64, i64* %j_v461
    %t489 = add i64 %t488, 1
    store i64 %t489, i64* %j_v461
    br label %loop.inc.465
loop.inc.465:
    %t490 = load i64, i64* %rep.466
    %t491 = add i64 %t490, 1
    store i64 %t491, i64* %rep.466
    br label %loop.cond.462
loop.end.464:
    %t492 = load i64, i64* %match_v460
    %t496 = icmp ne i64 %t492, 0
    br i1 %t496, label %if.then.493, label %if.end.495
if.then.493:
    %t497 = load i64, i64* @g_count
    %t498 = add i64 %t497, 1
    store i64 %t498, i64* @g_count
    br label %if.end.495
if.end.495:
    %t499 = load i64, i64* @g_i
    %t500 = add i64 %t499, 1
    store i64 %t500, i64* @g_i
    br label %loop.inc.455
loop.inc.455:
    %t501 = load i64, i64* %rep.456
    %t502 = add i64 %t501, 1
    store i64 %t502, i64* %rep.456
    br label %loop.cond.452
loop.end.454:
    %t503 = load i64, i64* @g_count
    ret i64 %t503
    ret i64 0
}

define i64 @freak_string_split(i64 %arg_s, i64 %arg_delim) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %delim = alloca i64
    store i64 %arg_delim, i64* %delim
    %t504 = load i64, i64* %s
    %t505 = call i64 @freak_llvm_word_length(i64 %t504)
    %slen_v506 = alloca i64
    store i64 %t505, i64* %slen_v506
    %t507 = load i64, i64* %delim
    %t508 = call i64 @freak_llvm_word_length(i64 %t507)
    %dlen_v509 = alloca i64
    store i64 %t508, i64* %dlen_v509
    %t510 = load i64, i64* %dlen_v509
    %t512 = icmp eq i64 %t510, 0
    %t511 = zext i1 %t512 to i64
    %t516 = icmp ne i64 %t511, 0
    br i1 %t516, label %if.then.513, label %if.end.515
if.then.513:
    %t517 = load i64, i64* %s
    ret i64 %t517
    br label %if.end.515
if.end.515:
    %t518 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.9, i64 0, i64 0
    %t519 = ptrtoint i8* %t518 to i64
    %sp_out_v520 = alloca i64
    store i64 %t519, i64* %sp_out_v520
    %t521 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.10, i64 0, i64 0
    %t522 = ptrtoint i8* %t521 to i64
    %sp_cur_v523 = alloca i64
    store i64 %t522, i64* %sp_cur_v523
    %sp_i_v524 = alloca i64
    store i64 0, i64* %sp_i_v524
    %t530 = load i64, i64* %slen_v506
    %rep.529 = alloca i64
    store i64 0, i64* %rep.529
    br label %loop.cond.525
loop.cond.525:
    %t531 = load i64, i64* %rep.529
    %t532 = icmp slt i64 %t531, %t530
    br i1 %t532, label %loop.body.526, label %loop.end.527
loop.body.526:
    %sp_match_v533 = alloca i64
    store i64 1, i64* %sp_match_v533
    %t534 = load i64, i64* %sp_i_v524
    %t535 = load i64, i64* %dlen_v509
    %t536 = add i64 %t534, %t535
    %t537 = load i64, i64* %slen_v506
    %t539 = icmp sle i64 %t536, %t537
    %t538 = zext i1 %t539 to i64
    %t543 = icmp ne i64 %t538, 0
    br i1 %t543, label %if.then.540, label %if.else.541
if.then.540:
    %sp_j_v544 = alloca i64
    store i64 0, i64* %sp_j_v544
    %t550 = load i64, i64* %dlen_v509
    %rep.549 = alloca i64
    store i64 0, i64* %rep.549
    br label %loop.cond.545
loop.cond.545:
    %t551 = load i64, i64* %rep.549
    %t552 = icmp slt i64 %t551, %t550
    br i1 %t552, label %loop.body.546, label %loop.end.547
loop.body.546:
    %t553 = load i64, i64* %sp_match_v533
    %t557 = icmp ne i64 %t553, 0
    br i1 %t557, label %if.then.554, label %if.end.556
if.then.554:
    %t558 = load i64, i64* %s
    %t560 = load i64, i64* %sp_i_v524
    %t561 = load i64, i64* %sp_j_v544
    %t562 = add i64 %t560, %t561
    %t559 = call i64 @freak_llvm_word_char_at(i64 %t558, i64 %t562)
    %t563 = load i64, i64* %delim
    %t565 = load i64, i64* %sp_j_v544
    %t564 = call i64 @freak_llvm_word_char_at(i64 %t563, i64 %t565)
    %t566 = call i64 @freak_llvm_word_neq(i64 %t559, i64 %t564)
    %t570 = icmp ne i64 %t566, 0
    br i1 %t570, label %if.then.567, label %if.end.569
if.then.567:
    store i64 0, i64* %sp_match_v533
    br label %if.end.569
if.end.569:
    br label %if.end.556
if.end.556:
    %t571 = load i64, i64* %sp_j_v544
    %t572 = add i64 %t571, 1
    store i64 %t572, i64* %sp_j_v544
    br label %loop.inc.548
loop.inc.548:
    %t573 = load i64, i64* %rep.549
    %t574 = add i64 %t573, 1
    store i64 %t574, i64* %rep.549
    br label %loop.cond.545
loop.end.547:
    br label %if.end.542
if.else.541:
    store i64 0, i64* %sp_match_v533
    br label %if.end.542
if.end.542:
    %t575 = load i64, i64* %sp_match_v533
    %t579 = icmp ne i64 %t575, 0
    br i1 %t579, label %if.then.576, label %if.else.577
if.then.576:
    %t580 = load i64, i64* %sp_out_v520
    %t581 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.11, i64 0, i64 0
    %t582 = ptrtoint i8* %t581 to i64
    %t583 = call i64 @freak_llvm_word_eq(i64 %t580, i64 %t582)
    %t587 = icmp ne i64 %t583, 0
    br i1 %t587, label %if.then.584, label %if.else.585
if.then.584:
    %t588 = load i64, i64* %sp_cur_v523
    store i64 %t588, i64* %sp_out_v520
    br label %if.end.586
if.else.585:
    %t589 = load i64, i64* %sp_out_v520
    %t590 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.12, i64 0, i64 0
    %t591 = ptrtoint i8* %t590 to i64
    %t592 = call i64 @freak_llvm_word_concat(i64 %t589, i64 %t591)
    %t593 = load i64, i64* %sp_cur_v523
    %t594 = call i64 @freak_llvm_word_concat(i64 %t592, i64 %t593)
    store i64 %t594, i64* %sp_out_v520
    br label %if.end.586
if.end.586:
    %t595 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.13, i64 0, i64 0
    %t596 = ptrtoint i8* %t595 to i64
    store i64 %t596, i64* %sp_cur_v523
    %t597 = load i64, i64* %dlen_v509
    %t598 = load i64, i64* %sp_i_v524
    %t599 = add i64 %t598, %t597
    store i64 %t599, i64* %sp_i_v524
    br label %if.end.578
if.else.577:
    %t600 = load i64, i64* %sp_cur_v523
    %t601 = load i64, i64* %s
    %t603 = load i64, i64* %sp_i_v524
    %t602 = call i64 @freak_llvm_word_char_at(i64 %t601, i64 %t603)
    %t604 = call i64 @freak_llvm_word_concat(i64 %t600, i64 %t602)
    store i64 %t604, i64* %sp_cur_v523
    %t605 = load i64, i64* %sp_i_v524
    %t606 = add i64 %t605, 1
    store i64 %t606, i64* %sp_i_v524
    br label %if.end.578
if.end.578:
    br label %loop.inc.528
loop.inc.528:
    %t607 = load i64, i64* %rep.529
    %t608 = add i64 %t607, 1
    store i64 %t608, i64* %rep.529
    br label %loop.cond.525
loop.end.527:
    %t609 = load i64, i64* %sp_out_v520
    %t610 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.14, i64 0, i64 0
    %t611 = ptrtoint i8* %t610 to i64
    %t612 = call i64 @freak_llvm_word_eq(i64 %t609, i64 %t611)
    %t616 = icmp ne i64 %t612, 0
    br i1 %t616, label %if.then.613, label %if.else.614
if.then.613:
    %t617 = load i64, i64* %sp_cur_v523
    store i64 %t617, i64* %sp_out_v520
    br label %if.end.615
if.else.614:
    %t618 = load i64, i64* %sp_out_v520
    %t619 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.15, i64 0, i64 0
    %t620 = ptrtoint i8* %t619 to i64
    %t621 = call i64 @freak_llvm_word_concat(i64 %t618, i64 %t620)
    %t622 = load i64, i64* %sp_cur_v523
    %t623 = call i64 @freak_llvm_word_concat(i64 %t621, i64 %t622)
    store i64 %t623, i64* %sp_out_v520
    br label %if.end.615
if.end.615:
    %t624 = load i64, i64* %sp_out_v520
    ret i64 %t624
    ret i64 0
}

define i64 @freak_string_join(i64 %arg_parts, i64 %arg_separator) {
entry:
    %parts = alloca i64
    store i64 %arg_parts, i64* %parts
    %separator = alloca i64
    store i64 %arg_separator, i64* %separator
    %t625 = load i64, i64* %parts
    %t626 = call i64 @freak_llvm_word_length(i64 %t625)
    %plen_v627 = alloca i64
    store i64 %t626, i64* %plen_v627
    %t628 = load i64, i64* %plen_v627
    %t630 = icmp eq i64 %t628, 0
    %t629 = zext i1 %t630 to i64
    %t634 = icmp ne i64 %t629, 0
    br i1 %t634, label %if.then.631, label %if.end.633
if.then.631:
    %t635 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.16, i64 0, i64 0
    %t636 = ptrtoint i8* %t635 to i64
    ret i64 %t636
    br label %if.end.633
if.end.633:
    %t637 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.17, i64 0, i64 0
    %t638 = ptrtoint i8* %t637 to i64
    %jn_out_v639 = alloca i64
    store i64 %t638, i64* %jn_out_v639
    %t640 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.18, i64 0, i64 0
    %t641 = ptrtoint i8* %t640 to i64
    %jn_cur_v642 = alloca i64
    store i64 %t641, i64* %jn_cur_v642
    %jn_first_v643 = alloca i64
    store i64 1, i64* %jn_first_v643
    %jn_i_v644 = alloca i64
    store i64 0, i64* %jn_i_v644
    %t650 = load i64, i64* %plen_v627
    %rep.649 = alloca i64
    store i64 0, i64* %rep.649
    br label %loop.cond.645
loop.cond.645:
    %t651 = load i64, i64* %rep.649
    %t652 = icmp slt i64 %t651, %t650
    br i1 %t652, label %loop.body.646, label %loop.end.647
loop.body.646:
    %t653 = load i64, i64* %parts
    %t655 = load i64, i64* %jn_i_v644
    %t654 = call i64 @freak_llvm_word_char_at(i64 %t653, i64 %t655)
    %jn_c_v656 = alloca i64
    store i64 %t654, i64* %jn_c_v656
    %t657 = load i64, i64* %jn_c_v656
    %t658 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.19, i64 0, i64 0
    %t659 = ptrtoint i8* %t658 to i64
    %t660 = call i64 @freak_llvm_word_eq(i64 %t657, i64 %t659)
    %t664 = icmp ne i64 %t660, 0
    br i1 %t664, label %if.then.661, label %if.else.662
if.then.661:
    %t665 = load i64, i64* %jn_first_v643
    %t669 = icmp ne i64 %t665, 0
    br i1 %t669, label %if.then.666, label %if.else.667
if.then.666:
    %t670 = load i64, i64* %jn_cur_v642
    store i64 %t670, i64* %jn_out_v639
    store i64 0, i64* %jn_first_v643
    br label %if.end.668
if.else.667:
    %t671 = load i64, i64* %jn_out_v639
    %t672 = load i64, i64* %separator
    %t673 = call i64 @freak_llvm_word_concat(i64 %t671, i64 %t672)
    %t674 = load i64, i64* %jn_cur_v642
    %t675 = call i64 @freak_llvm_word_concat(i64 %t673, i64 %t674)
    store i64 %t675, i64* %jn_out_v639
    br label %if.end.668
if.end.668:
    %t676 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.20, i64 0, i64 0
    %t677 = ptrtoint i8* %t676 to i64
    store i64 %t677, i64* %jn_cur_v642
    br label %if.end.663
if.else.662:
    %t678 = load i64, i64* %jn_cur_v642
    %t679 = load i64, i64* %jn_c_v656
    %t680 = call i64 @freak_llvm_word_concat(i64 %t678, i64 %t679)
    store i64 %t680, i64* %jn_cur_v642
    br label %if.end.663
if.end.663:
    %t681 = load i64, i64* %jn_i_v644
    %t682 = add i64 %t681, 1
    store i64 %t682, i64* %jn_i_v644
    br label %loop.inc.648
loop.inc.648:
    %t683 = load i64, i64* %rep.649
    %t684 = add i64 %t683, 1
    store i64 %t684, i64* %rep.649
    br label %loop.cond.645
loop.end.647:
    %t685 = load i64, i64* %jn_first_v643
    %t689 = icmp ne i64 %t685, 0
    br i1 %t689, label %if.then.686, label %if.else.687
if.then.686:
    %t690 = load i64, i64* %jn_cur_v642
    store i64 %t690, i64* %jn_out_v639
    br label %if.end.688
if.else.687:
    %t691 = load i64, i64* %jn_out_v639
    %t692 = load i64, i64* %separator
    %t693 = call i64 @freak_llvm_word_concat(i64 %t691, i64 %t692)
    %t694 = load i64, i64* %jn_cur_v642
    %t695 = call i64 @freak_llvm_word_concat(i64 %t693, i64 %t694)
    store i64 %t695, i64* %jn_out_v639
    br label %if.end.688
if.end.688:
    %t696 = load i64, i64* %jn_out_v639
    ret i64 %t696
    ret i64 0
}

define i64 @freak_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t697 = load i64, i64* %c
    %t698 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.21, i64 0, i64 0
    %t699 = ptrtoint i8* %t698 to i64
    %t700 = call i64 @freak_llvm_word_eq(i64 %t697, i64 %t699)
    %t704 = icmp ne i64 %t700, 0
    br i1 %t704, label %if.then.701, label %if.end.703
if.then.701:
    ret i64 1
    br label %if.end.703
if.end.703:
    %t705 = load i64, i64* %c
    %t706 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.22, i64 0, i64 0
    %t707 = ptrtoint i8* %t706 to i64
    %t708 = call i64 @freak_llvm_word_eq(i64 %t705, i64 %t707)
    %t712 = icmp ne i64 %t708, 0
    br i1 %t712, label %if.then.709, label %if.end.711
if.then.709:
    ret i64 1
    br label %if.end.711
if.end.711:
    %t713 = load i64, i64* %c
    %t714 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.23, i64 0, i64 0
    %t715 = ptrtoint i8* %t714 to i64
    %t716 = call i64 @freak_llvm_word_eq(i64 %t713, i64 %t715)
    %t720 = icmp ne i64 %t716, 0
    br i1 %t720, label %if.then.717, label %if.end.719
if.then.717:
    ret i64 1
    br label %if.end.719
if.end.719:
    %t721 = load i64, i64* %c
    %t722 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.24, i64 0, i64 0
    %t723 = ptrtoint i8* %t722 to i64
    %t724 = call i64 @freak_llvm_word_eq(i64 %t721, i64 %t723)
    %t728 = icmp ne i64 %t724, 0
    br i1 %t728, label %if.then.725, label %if.end.727
if.then.725:
    ret i64 1
    br label %if.end.727
if.end.727:
    %t729 = load i64, i64* %c
    %t730 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.25, i64 0, i64 0
    %t731 = ptrtoint i8* %t730 to i64
    %t732 = call i64 @freak_llvm_word_eq(i64 %t729, i64 %t731)
    %t736 = icmp ne i64 %t732, 0
    br i1 %t736, label %if.then.733, label %if.end.735
if.then.733:
    ret i64 1
    br label %if.end.735
if.end.735:
    %t737 = load i64, i64* %c
    %t738 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.26, i64 0, i64 0
    %t739 = ptrtoint i8* %t738 to i64
    %t740 = call i64 @freak_llvm_word_eq(i64 %t737, i64 %t739)
    %t744 = icmp ne i64 %t740, 0
    br i1 %t744, label %if.then.741, label %if.end.743
if.then.741:
    ret i64 1
    br label %if.end.743
if.end.743:
    %t745 = load i64, i64* %c
    %t746 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.27, i64 0, i64 0
    %t747 = ptrtoint i8* %t746 to i64
    %t748 = call i64 @freak_llvm_word_eq(i64 %t745, i64 %t747)
    %t752 = icmp ne i64 %t748, 0
    br i1 %t752, label %if.then.749, label %if.end.751
if.then.749:
    ret i64 1
    br label %if.end.751
if.end.751:
    %t753 = load i64, i64* %c
    %t754 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.28, i64 0, i64 0
    %t755 = ptrtoint i8* %t754 to i64
    %t756 = call i64 @freak_llvm_word_eq(i64 %t753, i64 %t755)
    %t760 = icmp ne i64 %t756, 0
    br i1 %t760, label %if.then.757, label %if.end.759
if.then.757:
    ret i64 1
    br label %if.end.759
if.end.759:
    %t761 = load i64, i64* %c
    %t762 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.29, i64 0, i64 0
    %t763 = ptrtoint i8* %t762 to i64
    %t764 = call i64 @freak_llvm_word_eq(i64 %t761, i64 %t763)
    %t768 = icmp ne i64 %t764, 0
    br i1 %t768, label %if.then.765, label %if.end.767
if.then.765:
    ret i64 1
    br label %if.end.767
if.end.767:
    %t769 = load i64, i64* %c
    %t770 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.30, i64 0, i64 0
    %t771 = ptrtoint i8* %t770 to i64
    %t772 = call i64 @freak_llvm_word_eq(i64 %t769, i64 %t771)
    %t776 = icmp ne i64 %t772, 0
    br i1 %t776, label %if.then.773, label %if.end.775
if.then.773:
    ret i64 1
    br label %if.end.775
if.end.775:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_alpha(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t777 = load i64, i64* %c
    %t778 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.31, i64 0, i64 0
    %t779 = ptrtoint i8* %t778 to i64
    %t780 = call i64 @freak_llvm_word_eq(i64 %t777, i64 %t779)
    %t781 = load i64, i64* %c
    %t782 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.32, i64 0, i64 0
    %t783 = ptrtoint i8* %t782 to i64
    %t784 = call i64 @freak_llvm_word_eq(i64 %t781, i64 %t783)
    %t786 = icmp ne i64 %t780, 0
    %t787 = icmp ne i64 %t784, 0
    %t788 = or i1 %t786, %t787
    %t785 = zext i1 %t788 to i64
    %t789 = load i64, i64* %c
    %t790 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.33, i64 0, i64 0
    %t791 = ptrtoint i8* %t790 to i64
    %t792 = call i64 @freak_llvm_word_eq(i64 %t789, i64 %t791)
    %t794 = icmp ne i64 %t785, 0
    %t795 = icmp ne i64 %t792, 0
    %t796 = or i1 %t794, %t795
    %t793 = zext i1 %t796 to i64
    %t797 = load i64, i64* %c
    %t798 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.34, i64 0, i64 0
    %t799 = ptrtoint i8* %t798 to i64
    %t800 = call i64 @freak_llvm_word_eq(i64 %t797, i64 %t799)
    %t802 = icmp ne i64 %t793, 0
    %t803 = icmp ne i64 %t800, 0
    %t804 = or i1 %t802, %t803
    %t801 = zext i1 %t804 to i64
    %t805 = load i64, i64* %c
    %t806 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.35, i64 0, i64 0
    %t807 = ptrtoint i8* %t806 to i64
    %t808 = call i64 @freak_llvm_word_eq(i64 %t805, i64 %t807)
    %t810 = icmp ne i64 %t801, 0
    %t811 = icmp ne i64 %t808, 0
    %t812 = or i1 %t810, %t811
    %t809 = zext i1 %t812 to i64
    %t816 = icmp ne i64 %t809, 0
    br i1 %t816, label %if.then.813, label %if.end.815
if.then.813:
    ret i64 1
    br label %if.end.815
if.end.815:
    %t817 = load i64, i64* %c
    %t818 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.36, i64 0, i64 0
    %t819 = ptrtoint i8* %t818 to i64
    %t820 = call i64 @freak_llvm_word_eq(i64 %t817, i64 %t819)
    %t821 = load i64, i64* %c
    %t822 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.37, i64 0, i64 0
    %t823 = ptrtoint i8* %t822 to i64
    %t824 = call i64 @freak_llvm_word_eq(i64 %t821, i64 %t823)
    %t826 = icmp ne i64 %t820, 0
    %t827 = icmp ne i64 %t824, 0
    %t828 = or i1 %t826, %t827
    %t825 = zext i1 %t828 to i64
    %t829 = load i64, i64* %c
    %t830 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.38, i64 0, i64 0
    %t831 = ptrtoint i8* %t830 to i64
    %t832 = call i64 @freak_llvm_word_eq(i64 %t829, i64 %t831)
    %t834 = icmp ne i64 %t825, 0
    %t835 = icmp ne i64 %t832, 0
    %t836 = or i1 %t834, %t835
    %t833 = zext i1 %t836 to i64
    %t837 = load i64, i64* %c
    %t838 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.39, i64 0, i64 0
    %t839 = ptrtoint i8* %t838 to i64
    %t840 = call i64 @freak_llvm_word_eq(i64 %t837, i64 %t839)
    %t842 = icmp ne i64 %t833, 0
    %t843 = icmp ne i64 %t840, 0
    %t844 = or i1 %t842, %t843
    %t841 = zext i1 %t844 to i64
    %t845 = load i64, i64* %c
    %t846 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.40, i64 0, i64 0
    %t847 = ptrtoint i8* %t846 to i64
    %t848 = call i64 @freak_llvm_word_eq(i64 %t845, i64 %t847)
    %t850 = icmp ne i64 %t841, 0
    %t851 = icmp ne i64 %t848, 0
    %t852 = or i1 %t850, %t851
    %t849 = zext i1 %t852 to i64
    %t856 = icmp ne i64 %t849, 0
    br i1 %t856, label %if.then.853, label %if.end.855
if.then.853:
    ret i64 1
    br label %if.end.855
if.end.855:
    %t857 = load i64, i64* %c
    %t858 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.41, i64 0, i64 0
    %t859 = ptrtoint i8* %t858 to i64
    %t860 = call i64 @freak_llvm_word_eq(i64 %t857, i64 %t859)
    %t861 = load i64, i64* %c
    %t862 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.42, i64 0, i64 0
    %t863 = ptrtoint i8* %t862 to i64
    %t864 = call i64 @freak_llvm_word_eq(i64 %t861, i64 %t863)
    %t866 = icmp ne i64 %t860, 0
    %t867 = icmp ne i64 %t864, 0
    %t868 = or i1 %t866, %t867
    %t865 = zext i1 %t868 to i64
    %t869 = load i64, i64* %c
    %t870 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.43, i64 0, i64 0
    %t871 = ptrtoint i8* %t870 to i64
    %t872 = call i64 @freak_llvm_word_eq(i64 %t869, i64 %t871)
    %t874 = icmp ne i64 %t865, 0
    %t875 = icmp ne i64 %t872, 0
    %t876 = or i1 %t874, %t875
    %t873 = zext i1 %t876 to i64
    %t877 = load i64, i64* %c
    %t878 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.44, i64 0, i64 0
    %t879 = ptrtoint i8* %t878 to i64
    %t880 = call i64 @freak_llvm_word_eq(i64 %t877, i64 %t879)
    %t882 = icmp ne i64 %t873, 0
    %t883 = icmp ne i64 %t880, 0
    %t884 = or i1 %t882, %t883
    %t881 = zext i1 %t884 to i64
    %t885 = load i64, i64* %c
    %t886 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.45, i64 0, i64 0
    %t887 = ptrtoint i8* %t886 to i64
    %t888 = call i64 @freak_llvm_word_eq(i64 %t885, i64 %t887)
    %t890 = icmp ne i64 %t881, 0
    %t891 = icmp ne i64 %t888, 0
    %t892 = or i1 %t890, %t891
    %t889 = zext i1 %t892 to i64
    %t896 = icmp ne i64 %t889, 0
    br i1 %t896, label %if.then.893, label %if.end.895
if.then.893:
    ret i64 1
    br label %if.end.895
if.end.895:
    %t897 = load i64, i64* %c
    %t898 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.46, i64 0, i64 0
    %t899 = ptrtoint i8* %t898 to i64
    %t900 = call i64 @freak_llvm_word_eq(i64 %t897, i64 %t899)
    %t901 = load i64, i64* %c
    %t902 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.47, i64 0, i64 0
    %t903 = ptrtoint i8* %t902 to i64
    %t904 = call i64 @freak_llvm_word_eq(i64 %t901, i64 %t903)
    %t906 = icmp ne i64 %t900, 0
    %t907 = icmp ne i64 %t904, 0
    %t908 = or i1 %t906, %t907
    %t905 = zext i1 %t908 to i64
    %t909 = load i64, i64* %c
    %t910 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.48, i64 0, i64 0
    %t911 = ptrtoint i8* %t910 to i64
    %t912 = call i64 @freak_llvm_word_eq(i64 %t909, i64 %t911)
    %t914 = icmp ne i64 %t905, 0
    %t915 = icmp ne i64 %t912, 0
    %t916 = or i1 %t914, %t915
    %t913 = zext i1 %t916 to i64
    %t917 = load i64, i64* %c
    %t918 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.49, i64 0, i64 0
    %t919 = ptrtoint i8* %t918 to i64
    %t920 = call i64 @freak_llvm_word_eq(i64 %t917, i64 %t919)
    %t922 = icmp ne i64 %t913, 0
    %t923 = icmp ne i64 %t920, 0
    %t924 = or i1 %t922, %t923
    %t921 = zext i1 %t924 to i64
    %t925 = load i64, i64* %c
    %t926 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.50, i64 0, i64 0
    %t927 = ptrtoint i8* %t926 to i64
    %t928 = call i64 @freak_llvm_word_eq(i64 %t925, i64 %t927)
    %t930 = icmp ne i64 %t921, 0
    %t931 = icmp ne i64 %t928, 0
    %t932 = or i1 %t930, %t931
    %t929 = zext i1 %t932 to i64
    %t936 = icmp ne i64 %t929, 0
    br i1 %t936, label %if.then.933, label %if.end.935
if.then.933:
    ret i64 1
    br label %if.end.935
if.end.935:
    %t937 = load i64, i64* %c
    %t938 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.51, i64 0, i64 0
    %t939 = ptrtoint i8* %t938 to i64
    %t940 = call i64 @freak_llvm_word_eq(i64 %t937, i64 %t939)
    %t941 = load i64, i64* %c
    %t942 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.52, i64 0, i64 0
    %t943 = ptrtoint i8* %t942 to i64
    %t944 = call i64 @freak_llvm_word_eq(i64 %t941, i64 %t943)
    %t946 = icmp ne i64 %t940, 0
    %t947 = icmp ne i64 %t944, 0
    %t948 = or i1 %t946, %t947
    %t945 = zext i1 %t948 to i64
    %t949 = load i64, i64* %c
    %t950 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.53, i64 0, i64 0
    %t951 = ptrtoint i8* %t950 to i64
    %t952 = call i64 @freak_llvm_word_eq(i64 %t949, i64 %t951)
    %t954 = icmp ne i64 %t945, 0
    %t955 = icmp ne i64 %t952, 0
    %t956 = or i1 %t954, %t955
    %t953 = zext i1 %t956 to i64
    %t957 = load i64, i64* %c
    %t958 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.54, i64 0, i64 0
    %t959 = ptrtoint i8* %t958 to i64
    %t960 = call i64 @freak_llvm_word_eq(i64 %t957, i64 %t959)
    %t962 = icmp ne i64 %t953, 0
    %t963 = icmp ne i64 %t960, 0
    %t964 = or i1 %t962, %t963
    %t961 = zext i1 %t964 to i64
    %t965 = load i64, i64* %c
    %t966 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.55, i64 0, i64 0
    %t967 = ptrtoint i8* %t966 to i64
    %t968 = call i64 @freak_llvm_word_eq(i64 %t965, i64 %t967)
    %t970 = icmp ne i64 %t961, 0
    %t971 = icmp ne i64 %t968, 0
    %t972 = or i1 %t970, %t971
    %t969 = zext i1 %t972 to i64
    %t973 = load i64, i64* %c
    %t974 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.56, i64 0, i64 0
    %t975 = ptrtoint i8* %t974 to i64
    %t976 = call i64 @freak_llvm_word_eq(i64 %t973, i64 %t975)
    %t978 = icmp ne i64 %t969, 0
    %t979 = icmp ne i64 %t976, 0
    %t980 = or i1 %t978, %t979
    %t977 = zext i1 %t980 to i64
    %t984 = icmp ne i64 %t977, 0
    br i1 %t984, label %if.then.981, label %if.end.983
if.then.981:
    ret i64 1
    br label %if.end.983
if.end.983:
    %t985 = load i64, i64* %c
    %t986 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.57, i64 0, i64 0
    %t987 = ptrtoint i8* %t986 to i64
    %t988 = call i64 @freak_llvm_word_eq(i64 %t985, i64 %t987)
    %t989 = load i64, i64* %c
    %t990 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.58, i64 0, i64 0
    %t991 = ptrtoint i8* %t990 to i64
    %t992 = call i64 @freak_llvm_word_eq(i64 %t989, i64 %t991)
    %t994 = icmp ne i64 %t988, 0
    %t995 = icmp ne i64 %t992, 0
    %t996 = or i1 %t994, %t995
    %t993 = zext i1 %t996 to i64
    %t997 = load i64, i64* %c
    %t998 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.59, i64 0, i64 0
    %t999 = ptrtoint i8* %t998 to i64
    %t1000 = call i64 @freak_llvm_word_eq(i64 %t997, i64 %t999)
    %t1002 = icmp ne i64 %t993, 0
    %t1003 = icmp ne i64 %t1000, 0
    %t1004 = or i1 %t1002, %t1003
    %t1001 = zext i1 %t1004 to i64
    %t1005 = load i64, i64* %c
    %t1006 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.60, i64 0, i64 0
    %t1007 = ptrtoint i8* %t1006 to i64
    %t1008 = call i64 @freak_llvm_word_eq(i64 %t1005, i64 %t1007)
    %t1010 = icmp ne i64 %t1001, 0
    %t1011 = icmp ne i64 %t1008, 0
    %t1012 = or i1 %t1010, %t1011
    %t1009 = zext i1 %t1012 to i64
    %t1013 = load i64, i64* %c
    %t1014 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.61, i64 0, i64 0
    %t1015 = ptrtoint i8* %t1014 to i64
    %t1016 = call i64 @freak_llvm_word_eq(i64 %t1013, i64 %t1015)
    %t1018 = icmp ne i64 %t1009, 0
    %t1019 = icmp ne i64 %t1016, 0
    %t1020 = or i1 %t1018, %t1019
    %t1017 = zext i1 %t1020 to i64
    %t1024 = icmp ne i64 %t1017, 0
    br i1 %t1024, label %if.then.1021, label %if.end.1023
if.then.1021:
    ret i64 1
    br label %if.end.1023
if.end.1023:
    %t1025 = load i64, i64* %c
    %t1026 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.62, i64 0, i64 0
    %t1027 = ptrtoint i8* %t1026 to i64
    %t1028 = call i64 @freak_llvm_word_eq(i64 %t1025, i64 %t1027)
    %t1029 = load i64, i64* %c
    %t1030 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.63, i64 0, i64 0
    %t1031 = ptrtoint i8* %t1030 to i64
    %t1032 = call i64 @freak_llvm_word_eq(i64 %t1029, i64 %t1031)
    %t1034 = icmp ne i64 %t1028, 0
    %t1035 = icmp ne i64 %t1032, 0
    %t1036 = or i1 %t1034, %t1035
    %t1033 = zext i1 %t1036 to i64
    %t1037 = load i64, i64* %c
    %t1038 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.64, i64 0, i64 0
    %t1039 = ptrtoint i8* %t1038 to i64
    %t1040 = call i64 @freak_llvm_word_eq(i64 %t1037, i64 %t1039)
    %t1042 = icmp ne i64 %t1033, 0
    %t1043 = icmp ne i64 %t1040, 0
    %t1044 = or i1 %t1042, %t1043
    %t1041 = zext i1 %t1044 to i64
    %t1045 = load i64, i64* %c
    %t1046 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.65, i64 0, i64 0
    %t1047 = ptrtoint i8* %t1046 to i64
    %t1048 = call i64 @freak_llvm_word_eq(i64 %t1045, i64 %t1047)
    %t1050 = icmp ne i64 %t1041, 0
    %t1051 = icmp ne i64 %t1048, 0
    %t1052 = or i1 %t1050, %t1051
    %t1049 = zext i1 %t1052 to i64
    %t1053 = load i64, i64* %c
    %t1054 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.66, i64 0, i64 0
    %t1055 = ptrtoint i8* %t1054 to i64
    %t1056 = call i64 @freak_llvm_word_eq(i64 %t1053, i64 %t1055)
    %t1058 = icmp ne i64 %t1049, 0
    %t1059 = icmp ne i64 %t1056, 0
    %t1060 = or i1 %t1058, %t1059
    %t1057 = zext i1 %t1060 to i64
    %t1064 = icmp ne i64 %t1057, 0
    br i1 %t1064, label %if.then.1061, label %if.end.1063
if.then.1061:
    ret i64 1
    br label %if.end.1063
if.end.1063:
    %t1065 = load i64, i64* %c
    %t1066 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.67, i64 0, i64 0
    %t1067 = ptrtoint i8* %t1066 to i64
    %t1068 = call i64 @freak_llvm_word_eq(i64 %t1065, i64 %t1067)
    %t1069 = load i64, i64* %c
    %t1070 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.68, i64 0, i64 0
    %t1071 = ptrtoint i8* %t1070 to i64
    %t1072 = call i64 @freak_llvm_word_eq(i64 %t1069, i64 %t1071)
    %t1074 = icmp ne i64 %t1068, 0
    %t1075 = icmp ne i64 %t1072, 0
    %t1076 = or i1 %t1074, %t1075
    %t1073 = zext i1 %t1076 to i64
    %t1077 = load i64, i64* %c
    %t1078 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.69, i64 0, i64 0
    %t1079 = ptrtoint i8* %t1078 to i64
    %t1080 = call i64 @freak_llvm_word_eq(i64 %t1077, i64 %t1079)
    %t1082 = icmp ne i64 %t1073, 0
    %t1083 = icmp ne i64 %t1080, 0
    %t1084 = or i1 %t1082, %t1083
    %t1081 = zext i1 %t1084 to i64
    %t1085 = load i64, i64* %c
    %t1086 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.70, i64 0, i64 0
    %t1087 = ptrtoint i8* %t1086 to i64
    %t1088 = call i64 @freak_llvm_word_eq(i64 %t1085, i64 %t1087)
    %t1090 = icmp ne i64 %t1081, 0
    %t1091 = icmp ne i64 %t1088, 0
    %t1092 = or i1 %t1090, %t1091
    %t1089 = zext i1 %t1092 to i64
    %t1093 = load i64, i64* %c
    %t1094 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.71, i64 0, i64 0
    %t1095 = ptrtoint i8* %t1094 to i64
    %t1096 = call i64 @freak_llvm_word_eq(i64 %t1093, i64 %t1095)
    %t1098 = icmp ne i64 %t1089, 0
    %t1099 = icmp ne i64 %t1096, 0
    %t1100 = or i1 %t1098, %t1099
    %t1097 = zext i1 %t1100 to i64
    %t1104 = icmp ne i64 %t1097, 0
    br i1 %t1104, label %if.then.1101, label %if.end.1103
if.then.1101:
    ret i64 1
    br label %if.end.1103
if.end.1103:
    %t1105 = load i64, i64* %c
    %t1106 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.72, i64 0, i64 0
    %t1107 = ptrtoint i8* %t1106 to i64
    %t1108 = call i64 @freak_llvm_word_eq(i64 %t1105, i64 %t1107)
    %t1109 = load i64, i64* %c
    %t1110 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.73, i64 0, i64 0
    %t1111 = ptrtoint i8* %t1110 to i64
    %t1112 = call i64 @freak_llvm_word_eq(i64 %t1109, i64 %t1111)
    %t1114 = icmp ne i64 %t1108, 0
    %t1115 = icmp ne i64 %t1112, 0
    %t1116 = or i1 %t1114, %t1115
    %t1113 = zext i1 %t1116 to i64
    %t1117 = load i64, i64* %c
    %t1118 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.74, i64 0, i64 0
    %t1119 = ptrtoint i8* %t1118 to i64
    %t1120 = call i64 @freak_llvm_word_eq(i64 %t1117, i64 %t1119)
    %t1122 = icmp ne i64 %t1113, 0
    %t1123 = icmp ne i64 %t1120, 0
    %t1124 = or i1 %t1122, %t1123
    %t1121 = zext i1 %t1124 to i64
    %t1125 = load i64, i64* %c
    %t1126 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.75, i64 0, i64 0
    %t1127 = ptrtoint i8* %t1126 to i64
    %t1128 = call i64 @freak_llvm_word_eq(i64 %t1125, i64 %t1127)
    %t1130 = icmp ne i64 %t1121, 0
    %t1131 = icmp ne i64 %t1128, 0
    %t1132 = or i1 %t1130, %t1131
    %t1129 = zext i1 %t1132 to i64
    %t1133 = load i64, i64* %c
    %t1134 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.76, i64 0, i64 0
    %t1135 = ptrtoint i8* %t1134 to i64
    %t1136 = call i64 @freak_llvm_word_eq(i64 %t1133, i64 %t1135)
    %t1138 = icmp ne i64 %t1129, 0
    %t1139 = icmp ne i64 %t1136, 0
    %t1140 = or i1 %t1138, %t1139
    %t1137 = zext i1 %t1140 to i64
    %t1144 = icmp ne i64 %t1137, 0
    br i1 %t1144, label %if.then.1141, label %if.end.1143
if.then.1141:
    ret i64 1
    br label %if.end.1143
if.end.1143:
    %t1145 = load i64, i64* %c
    %t1146 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.77, i64 0, i64 0
    %t1147 = ptrtoint i8* %t1146 to i64
    %t1148 = call i64 @freak_llvm_word_eq(i64 %t1145, i64 %t1147)
    %t1149 = load i64, i64* %c
    %t1150 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.78, i64 0, i64 0
    %t1151 = ptrtoint i8* %t1150 to i64
    %t1152 = call i64 @freak_llvm_word_eq(i64 %t1149, i64 %t1151)
    %t1154 = icmp ne i64 %t1148, 0
    %t1155 = icmp ne i64 %t1152, 0
    %t1156 = or i1 %t1154, %t1155
    %t1153 = zext i1 %t1156 to i64
    %t1157 = load i64, i64* %c
    %t1158 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.79, i64 0, i64 0
    %t1159 = ptrtoint i8* %t1158 to i64
    %t1160 = call i64 @freak_llvm_word_eq(i64 %t1157, i64 %t1159)
    %t1162 = icmp ne i64 %t1153, 0
    %t1163 = icmp ne i64 %t1160, 0
    %t1164 = or i1 %t1162, %t1163
    %t1161 = zext i1 %t1164 to i64
    %t1165 = load i64, i64* %c
    %t1166 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.80, i64 0, i64 0
    %t1167 = ptrtoint i8* %t1166 to i64
    %t1168 = call i64 @freak_llvm_word_eq(i64 %t1165, i64 %t1167)
    %t1170 = icmp ne i64 %t1161, 0
    %t1171 = icmp ne i64 %t1168, 0
    %t1172 = or i1 %t1170, %t1171
    %t1169 = zext i1 %t1172 to i64
    %t1173 = load i64, i64* %c
    %t1174 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.81, i64 0, i64 0
    %t1175 = ptrtoint i8* %t1174 to i64
    %t1176 = call i64 @freak_llvm_word_eq(i64 %t1173, i64 %t1175)
    %t1178 = icmp ne i64 %t1169, 0
    %t1179 = icmp ne i64 %t1176, 0
    %t1180 = or i1 %t1178, %t1179
    %t1177 = zext i1 %t1180 to i64
    %t1181 = load i64, i64* %c
    %t1182 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.82, i64 0, i64 0
    %t1183 = ptrtoint i8* %t1182 to i64
    %t1184 = call i64 @freak_llvm_word_eq(i64 %t1181, i64 %t1183)
    %t1186 = icmp ne i64 %t1177, 0
    %t1187 = icmp ne i64 %t1184, 0
    %t1188 = or i1 %t1186, %t1187
    %t1185 = zext i1 %t1188 to i64
    %t1192 = icmp ne i64 %t1185, 0
    br i1 %t1192, label %if.then.1189, label %if.end.1191
if.then.1189:
    ret i64 1
    br label %if.end.1191
if.end.1191:
    ret i64 0
    ret i64 0
}

define i64 @freak_is_whitespace(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t1193 = load i64, i64* %c
    %t1194 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.83, i64 0, i64 0
    %t1195 = ptrtoint i8* %t1194 to i64
    %t1196 = call i64 @freak_llvm_word_eq(i64 %t1193, i64 %t1195)
    %t1200 = icmp ne i64 %t1196, 0
    br i1 %t1200, label %if.then.1197, label %if.end.1199
if.then.1197:
    ret i64 1
    br label %if.end.1199
if.end.1199:
    %t1201 = load i64, i64* %c
    %t1202 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.84, i64 0, i64 0
    %t1203 = ptrtoint i8* %t1202 to i64
    %t1204 = call i64 @freak_llvm_word_eq(i64 %t1201, i64 %t1203)
    %t1208 = icmp ne i64 %t1204, 0
    br i1 %t1208, label %if.then.1205, label %if.end.1207
if.then.1205:
    ret i64 1
    br label %if.end.1207
if.end.1207:
    %t1209 = load i64, i64* %c
    %t1210 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.85, i64 0, i64 0
    %t1211 = ptrtoint i8* %t1210 to i64
    %t1212 = call i64 @freak_llvm_word_eq(i64 %t1209, i64 %t1211)
    %t1216 = icmp ne i64 %t1212, 0
    br i1 %t1216, label %if.then.1213, label %if.end.1215
if.then.1213:
    ret i64 1
    br label %if.end.1215
if.end.1215:
    %t1217 = load i64, i64* %c
    %t1218 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.86, i64 0, i64 0
    %t1219 = ptrtoint i8* %t1218 to i64
    %t1220 = call i64 @freak_llvm_word_eq(i64 %t1217, i64 %t1219)
    %t1224 = icmp ne i64 %t1220, 0
    br i1 %t1224, label %if.then.1221, label %if.end.1223
if.then.1221:
    ret i64 1
    br label %if.end.1223
if.end.1223:
    ret i64 0
    ret i64 0
}

define i64 @freak_string_starts_with(i64 %arg_s, i64 %arg_prefix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %prefix = alloca i64
    store i64 %arg_prefix, i64* %prefix
    %t1225 = load i64, i64* %s
    %t1226 = call i64 @freak_llvm_word_length(i64 %t1225)
    %slen_v1227 = alloca i64
    store i64 %t1226, i64* %slen_v1227
    %t1228 = load i64, i64* %prefix
    %t1229 = call i64 @freak_llvm_word_length(i64 %t1228)
    %plen_v1230 = alloca i64
    store i64 %t1229, i64* %plen_v1230
    %t1231 = load i64, i64* %plen_v1230
    %t1232 = load i64, i64* %slen_v1227
    %t1234 = icmp sgt i64 %t1231, %t1232
    %t1233 = zext i1 %t1234 to i64
    %t1238 = icmp ne i64 %t1233, 0
    br i1 %t1238, label %if.then.1235, label %if.end.1237
if.then.1235:
    ret i64 0
    br label %if.end.1237
if.end.1237:
    %si_v1239 = alloca i64
    store i64 0, i64* %si_v1239
    %t1245 = load i64, i64* %plen_v1230
    %rep.1244 = alloca i64
    store i64 0, i64* %rep.1244
    br label %loop.cond.1240
loop.cond.1240:
    %t1246 = load i64, i64* %rep.1244
    %t1247 = icmp slt i64 %t1246, %t1245
    br i1 %t1247, label %loop.body.1241, label %loop.end.1242
loop.body.1241:
    %t1248 = load i64, i64* %s
    %t1250 = load i64, i64* %si_v1239
    %t1249 = call i64 @freak_llvm_word_char_at(i64 %t1248, i64 %t1250)
    %t1251 = load i64, i64* %prefix
    %t1253 = load i64, i64* %si_v1239
    %t1252 = call i64 @freak_llvm_word_char_at(i64 %t1251, i64 %t1253)
    %t1254 = call i64 @freak_llvm_word_neq(i64 %t1249, i64 %t1252)
    %t1258 = icmp ne i64 %t1254, 0
    br i1 %t1258, label %if.then.1255, label %if.end.1257
if.then.1255:
    ret i64 0
    br label %if.end.1257
if.end.1257:
    %t1259 = load i64, i64* %si_v1239
    %t1260 = add i64 %t1259, 1
    store i64 %t1260, i64* %si_v1239
    br label %loop.inc.1243
loop.inc.1243:
    %t1261 = load i64, i64* %rep.1244
    %t1262 = add i64 %t1261, 1
    store i64 %t1262, i64* %rep.1244
    br label %loop.cond.1240
loop.end.1242:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_ends_with(i64 %arg_s, i64 %arg_suffix) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %suffix = alloca i64
    store i64 %arg_suffix, i64* %suffix
    %t1263 = load i64, i64* %s
    %t1264 = call i64 @freak_llvm_word_length(i64 %t1263)
    %slen_v1265 = alloca i64
    store i64 %t1264, i64* %slen_v1265
    %t1266 = load i64, i64* %suffix
    %t1267 = call i64 @freak_llvm_word_length(i64 %t1266)
    %xlen_v1268 = alloca i64
    store i64 %t1267, i64* %xlen_v1268
    %t1269 = load i64, i64* %xlen_v1268
    %t1270 = load i64, i64* %slen_v1265
    %t1272 = icmp sgt i64 %t1269, %t1270
    %t1271 = zext i1 %t1272 to i64
    %t1276 = icmp ne i64 %t1271, 0
    br i1 %t1276, label %if.then.1273, label %if.end.1275
if.then.1273:
    ret i64 0
    br label %if.end.1275
if.end.1275:
    %t1277 = load i64, i64* %slen_v1265
    %t1278 = load i64, i64* %xlen_v1268
    %t1279 = sub i64 %t1277, %t1278
    %offset_v1280 = alloca i64
    store i64 %t1279, i64* %offset_v1280
    %ei_v1281 = alloca i64
    store i64 0, i64* %ei_v1281
    %t1287 = load i64, i64* %xlen_v1268
    %rep.1286 = alloca i64
    store i64 0, i64* %rep.1286
    br label %loop.cond.1282
loop.cond.1282:
    %t1288 = load i64, i64* %rep.1286
    %t1289 = icmp slt i64 %t1288, %t1287
    br i1 %t1289, label %loop.body.1283, label %loop.end.1284
loop.body.1283:
    %t1290 = load i64, i64* %s
    %t1292 = load i64, i64* %offset_v1280
    %t1293 = load i64, i64* %ei_v1281
    %t1294 = add i64 %t1292, %t1293
    %t1291 = call i64 @freak_llvm_word_char_at(i64 %t1290, i64 %t1294)
    %t1295 = load i64, i64* %suffix
    %t1297 = load i64, i64* %ei_v1281
    %t1296 = call i64 @freak_llvm_word_char_at(i64 %t1295, i64 %t1297)
    %t1298 = call i64 @freak_llvm_word_neq(i64 %t1291, i64 %t1296)
    %t1302 = icmp ne i64 %t1298, 0
    br i1 %t1302, label %if.then.1299, label %if.end.1301
if.then.1299:
    ret i64 0
    br label %if.end.1301
if.end.1301:
    %t1303 = load i64, i64* %ei_v1281
    %t1304 = add i64 %t1303, 1
    store i64 %t1304, i64* %ei_v1281
    br label %loop.inc.1285
loop.inc.1285:
    %t1305 = load i64, i64* %rep.1286
    %t1306 = add i64 %t1305, 1
    store i64 %t1306, i64* %rep.1286
    br label %loop.cond.1282
loop.end.1284:
    ret i64 1
    ret i64 0
}

define i64 @freak_string_contains(i64 %arg_haystack, i64 %arg_needle) {
entry:
    %haystack = alloca i64
    store i64 %arg_haystack, i64* %haystack
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1307 = load i64, i64* %haystack
    %t1308 = load i64, i64* %needle
    %t1309 = call i64 @freak_string_count(i64 %t1307, i64 %t1308)
    %t1311 = icmp sgt i64 %t1309, 0
    %t1310 = zext i1 %t1311 to i64
    ret i64 %t1310
    ret i64 0
}

define i64 @freak_string_trim(i64 %arg_s) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %t1312 = load i64, i64* %s
    %t1313 = call i64 @freak_llvm_word_length(i64 %t1312)
    %slen_v1314 = alloca i64
    store i64 %t1313, i64* %slen_v1314
    %t1315 = load i64, i64* %slen_v1314
    %t1317 = icmp eq i64 %t1315, 0
    %t1316 = zext i1 %t1317 to i64
    %t1321 = icmp ne i64 %t1316, 0
    br i1 %t1321, label %if.then.1318, label %if.end.1320
if.then.1318:
    %t1322 = load i64, i64* %s
    ret i64 %t1322
    br label %if.end.1320
if.end.1320:
    %tstart_v1323 = alloca i64
    store i64 0, i64* %tstart_v1323
    br label %loop.cond.1324
loop.cond.1324:
    %t1327 = load i64, i64* %tstart_v1323
    %t1328 = load i64, i64* %slen_v1314
    %t1330 = icmp sge i64 %t1327, %t1328
    %t1329 = zext i1 %t1330 to i64
    %t1331 = icmp eq i64 %t1329, 0
    br i1 %t1331, label %loop.body.1325, label %loop.end.1326
loop.body.1325:
    %t1332 = load i64, i64* %s
    %t1334 = load i64, i64* %tstart_v1323
    %t1333 = call i64 @freak_llvm_word_char_at(i64 %t1332, i64 %t1334)
    %t1335 = call i64 @freak_is_whitespace(i64 %t1333)
    %t1337 = icmp eq i64 %t1335, 0
    %t1336 = zext i1 %t1337 to i64
    %t1341 = icmp ne i64 %t1336, 0
    br i1 %t1341, label %if.then.1338, label %if.end.1340
if.then.1338:
    %t1342 = load i64, i64* %s
    %t1343 = load i64, i64* %tstart_v1323
    %t1344 = call i64 @freak_string_trim_end(i64 %t1342, i64 %t1343)
    ret i64 %t1344
    br label %if.end.1340
if.end.1340:
    %t1345 = load i64, i64* %tstart_v1323
    %t1346 = add i64 %t1345, 1
    store i64 %t1346, i64* %tstart_v1323
    br label %loop.cond.1324
loop.end.1326:
    %t1347 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.87, i64 0, i64 0
    %t1348 = ptrtoint i8* %t1347 to i64
    ret i64 %t1348
    ret i64 0
}

define i64 @freak_string_trim_end(i64 %arg_s, i64 %arg_tstart) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %tstart = alloca i64
    store i64 %arg_tstart, i64* %tstart
    %t1349 = load i64, i64* %s
    %t1350 = call i64 @freak_llvm_word_length(i64 %t1349)
    %t1351 = sub i64 %t1350, 1
    %tend_v1352 = alloca i64
    store i64 %t1351, i64* %tend_v1352
    br label %loop.cond.1353
loop.cond.1353:
    %t1356 = load i64, i64* %tend_v1352
    %t1357 = load i64, i64* %tstart
    %t1359 = icmp slt i64 %t1356, %t1357
    %t1358 = zext i1 %t1359 to i64
    %t1360 = icmp eq i64 %t1358, 0
    br i1 %t1360, label %loop.body.1354, label %loop.end.1355
loop.body.1354:
    %t1361 = load i64, i64* %s
    %t1363 = load i64, i64* %tend_v1352
    %t1362 = call i64 @freak_llvm_word_char_at(i64 %t1361, i64 %t1363)
    %t1364 = call i64 @freak_is_whitespace(i64 %t1362)
    %t1366 = icmp eq i64 %t1364, 0
    %t1365 = zext i1 %t1366 to i64
    %t1370 = icmp ne i64 %t1365, 0
    br i1 %t1370, label %if.then.1367, label %if.end.1369
if.then.1367:
    %t1371 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.88, i64 0, i64 0
    %t1372 = ptrtoint i8* %t1371 to i64
    %tout_v1373 = alloca i64
    store i64 %t1372, i64* %tout_v1373
    %t1374 = load i64, i64* %tstart
    %ti_v1375 = alloca i64
    store i64 %t1374, i64* %ti_v1375
    br label %loop.cond.1376
loop.cond.1376:
    %t1379 = load i64, i64* %ti_v1375
    %t1380 = load i64, i64* %tend_v1352
    %t1382 = icmp sgt i64 %t1379, %t1380
    %t1381 = zext i1 %t1382 to i64
    %t1383 = icmp eq i64 %t1381, 0
    br i1 %t1383, label %loop.body.1377, label %loop.end.1378
loop.body.1377:
    %t1384 = load i64, i64* %tout_v1373
    %t1385 = load i64, i64* %s
    %t1387 = load i64, i64* %ti_v1375
    %t1386 = call i64 @freak_llvm_word_char_at(i64 %t1385, i64 %t1387)
    %t1388 = call i64 @freak_llvm_word_concat(i64 %t1384, i64 %t1386)
    store i64 %t1388, i64* %tout_v1373
    %t1389 = load i64, i64* %ti_v1375
    %t1390 = add i64 %t1389, 1
    store i64 %t1390, i64* %ti_v1375
    br label %loop.cond.1376
loop.end.1378:
    %t1391 = load i64, i64* %tout_v1373
    ret i64 %t1391
    br label %if.end.1369
if.end.1369:
    %t1392 = load i64, i64* %tend_v1352
    %t1393 = sub i64 %t1392, 1
    store i64 %t1393, i64* %tend_v1352
    br label %loop.cond.1353
loop.end.1355:
    %t1394 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.89, i64 0, i64 0
    %t1395 = ptrtoint i8* %t1394 to i64
    ret i64 %t1395
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
    %t1396 = load i64, i64* %s
    %t1397 = call i64 @freak_llvm_word_length(i64 %t1396)
    %slen_v1398 = alloca i64
    store i64 %t1397, i64* %slen_v1398
    %t1399 = load i64, i64* %old_str
    %t1400 = call i64 @freak_llvm_word_length(i64 %t1399)
    %olen_v1401 = alloca i64
    store i64 %t1400, i64* %olen_v1401
    %t1402 = load i64, i64* %olen_v1401
    %t1404 = icmp eq i64 %t1402, 0
    %t1403 = zext i1 %t1404 to i64
    %t1408 = icmp ne i64 %t1403, 0
    br i1 %t1408, label %if.then.1405, label %if.end.1407
if.then.1405:
    %t1409 = load i64, i64* %s
    ret i64 %t1409
    br label %if.end.1407
if.end.1407:
    %t1410 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.90, i64 0, i64 0
    %t1411 = ptrtoint i8* %t1410 to i64
    %rout_v1412 = alloca i64
    store i64 %t1411, i64* %rout_v1412
    %ri_v1413 = alloca i64
    store i64 0, i64* %ri_v1413
    br label %loop.cond.1414
loop.cond.1414:
    %t1417 = load i64, i64* %ri_v1413
    %t1418 = load i64, i64* %slen_v1398
    %t1420 = icmp sge i64 %t1417, %t1418
    %t1419 = zext i1 %t1420 to i64
    %t1421 = icmp eq i64 %t1419, 0
    br i1 %t1421, label %loop.body.1415, label %loop.end.1416
loop.body.1415:
    %rmatch_v1422 = alloca i64
    store i64 1, i64* %rmatch_v1422
    %t1423 = load i64, i64* %ri_v1413
    %t1424 = load i64, i64* %olen_v1401
    %t1425 = add i64 %t1423, %t1424
    %t1426 = load i64, i64* %slen_v1398
    %t1428 = icmp sle i64 %t1425, %t1426
    %t1427 = zext i1 %t1428 to i64
    %t1432 = icmp ne i64 %t1427, 0
    br i1 %t1432, label %if.then.1429, label %if.else.1430
if.then.1429:
    %rj_v1433 = alloca i64
    store i64 0, i64* %rj_v1433
    %t1439 = load i64, i64* %olen_v1401
    %rep.1438 = alloca i64
    store i64 0, i64* %rep.1438
    br label %loop.cond.1434
loop.cond.1434:
    %t1440 = load i64, i64* %rep.1438
    %t1441 = icmp slt i64 %t1440, %t1439
    br i1 %t1441, label %loop.body.1435, label %loop.end.1436
loop.body.1435:
    %t1442 = load i64, i64* %rmatch_v1422
    %t1446 = icmp ne i64 %t1442, 0
    br i1 %t1446, label %if.then.1443, label %if.end.1445
if.then.1443:
    %t1447 = load i64, i64* %s
    %t1449 = load i64, i64* %ri_v1413
    %t1450 = load i64, i64* %rj_v1433
    %t1451 = add i64 %t1449, %t1450
    %t1448 = call i64 @freak_llvm_word_char_at(i64 %t1447, i64 %t1451)
    %t1452 = load i64, i64* %old_str
    %t1454 = load i64, i64* %rj_v1433
    %t1453 = call i64 @freak_llvm_word_char_at(i64 %t1452, i64 %t1454)
    %t1455 = call i64 @freak_llvm_word_neq(i64 %t1448, i64 %t1453)
    %t1459 = icmp ne i64 %t1455, 0
    br i1 %t1459, label %if.then.1456, label %if.end.1458
if.then.1456:
    store i64 0, i64* %rmatch_v1422
    br label %if.end.1458
if.end.1458:
    br label %if.end.1445
if.end.1445:
    %t1460 = load i64, i64* %rj_v1433
    %t1461 = add i64 %t1460, 1
    store i64 %t1461, i64* %rj_v1433
    br label %loop.inc.1437
loop.inc.1437:
    %t1462 = load i64, i64* %rep.1438
    %t1463 = add i64 %t1462, 1
    store i64 %t1463, i64* %rep.1438
    br label %loop.cond.1434
loop.end.1436:
    br label %if.end.1431
if.else.1430:
    store i64 0, i64* %rmatch_v1422
    br label %if.end.1431
if.end.1431:
    %t1464 = load i64, i64* %rmatch_v1422
    %t1468 = icmp ne i64 %t1464, 0
    br i1 %t1468, label %if.then.1465, label %if.else.1466
if.then.1465:
    %t1469 = load i64, i64* %rout_v1412
    %t1470 = load i64, i64* %new_str
    %t1471 = call i64 @freak_llvm_word_concat(i64 %t1469, i64 %t1470)
    store i64 %t1471, i64* %rout_v1412
    %t1472 = load i64, i64* %olen_v1401
    %t1473 = load i64, i64* %ri_v1413
    %t1474 = add i64 %t1473, %t1472
    store i64 %t1474, i64* %ri_v1413
    br label %if.end.1467
if.else.1466:
    %t1475 = load i64, i64* %rout_v1412
    %t1476 = load i64, i64* %s
    %t1478 = load i64, i64* %ri_v1413
    %t1477 = call i64 @freak_llvm_word_char_at(i64 %t1476, i64 %t1478)
    %t1479 = call i64 @freak_llvm_word_concat(i64 %t1475, i64 %t1477)
    store i64 %t1479, i64* %rout_v1412
    %t1480 = load i64, i64* %ri_v1413
    %t1481 = add i64 %t1480, 1
    store i64 %t1481, i64* %ri_v1413
    br label %if.end.1467
if.end.1467:
    br label %loop.cond.1414
loop.end.1416:
    %t1482 = load i64, i64* %rout_v1412
    ret i64 %t1482
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
    %t1483 = load i64, i64* %s
    %t1484 = call i64 @freak_llvm_word_length(i64 %t1483)
    %slen_v1485 = alloca i64
    store i64 %t1484, i64* %slen_v1485
    %t1486 = load i64, i64* %start_idx
    %ss_v1487 = alloca i64
    store i64 %t1486, i64* %ss_v1487
    %t1488 = load i64, i64* %end_idx
    %se_v1489 = alloca i64
    store i64 %t1488, i64* %se_v1489
    %t1490 = load i64, i64* %ss_v1487
    %t1492 = icmp slt i64 %t1490, 0
    %t1491 = zext i1 %t1492 to i64
    %t1496 = icmp ne i64 %t1491, 0
    br i1 %t1496, label %if.then.1493, label %if.end.1495
if.then.1493:
    store i64 0, i64* %ss_v1487
    br label %if.end.1495
if.end.1495:
    %t1497 = load i64, i64* %se_v1489
    %t1498 = load i64, i64* %slen_v1485
    %t1500 = icmp sgt i64 %t1497, %t1498
    %t1499 = zext i1 %t1500 to i64
    %t1504 = icmp ne i64 %t1499, 0
    br i1 %t1504, label %if.then.1501, label %if.end.1503
if.then.1501:
    %t1505 = load i64, i64* %slen_v1485
    store i64 %t1505, i64* %se_v1489
    br label %if.end.1503
if.end.1503:
    %t1506 = load i64, i64* %ss_v1487
    %t1507 = load i64, i64* %se_v1489
    %t1509 = icmp sge i64 %t1506, %t1507
    %t1508 = zext i1 %t1509 to i64
    %t1513 = icmp ne i64 %t1508, 0
    br i1 %t1513, label %if.then.1510, label %if.end.1512
if.then.1510:
    %t1514 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.91, i64 0, i64 0
    %t1515 = ptrtoint i8* %t1514 to i64
    ret i64 %t1515
    br label %if.end.1512
if.end.1512:
    %t1516 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.92, i64 0, i64 0
    %t1517 = ptrtoint i8* %t1516 to i64
    %sub_out_v1518 = alloca i64
    store i64 %t1517, i64* %sub_out_v1518
    %t1519 = load i64, i64* %ss_v1487
    %si_v1520 = alloca i64
    store i64 %t1519, i64* %si_v1520
    br label %loop.cond.1521
loop.cond.1521:
    %t1524 = load i64, i64* %si_v1520
    %t1525 = load i64, i64* %se_v1489
    %t1527 = icmp sge i64 %t1524, %t1525
    %t1526 = zext i1 %t1527 to i64
    %t1528 = icmp eq i64 %t1526, 0
    br i1 %t1528, label %loop.body.1522, label %loop.end.1523
loop.body.1522:
    %t1529 = load i64, i64* %sub_out_v1518
    %t1530 = load i64, i64* %s
    %t1532 = load i64, i64* %si_v1520
    %t1531 = call i64 @freak_llvm_word_char_at(i64 %t1530, i64 %t1532)
    %t1533 = call i64 @freak_llvm_word_concat(i64 %t1529, i64 %t1531)
    store i64 %t1533, i64* %sub_out_v1518
    %t1534 = load i64, i64* %si_v1520
    %t1535 = add i64 %t1534, 1
    store i64 %t1535, i64* %si_v1520
    br label %loop.cond.1521
loop.end.1523:
    %t1536 = load i64, i64* %sub_out_v1518
    ret i64 %t1536
    ret i64 0
}

define i64 @freak_string_index_of(i64 %arg_s, i64 %arg_needle) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %needle = alloca i64
    store i64 %arg_needle, i64* %needle
    %t1537 = load i64, i64* %s
    %t1538 = call i64 @freak_llvm_word_length(i64 %t1537)
    %slen_v1539 = alloca i64
    store i64 %t1538, i64* %slen_v1539
    %t1540 = load i64, i64* %needle
    %t1541 = call i64 @freak_llvm_word_length(i64 %t1540)
    %nlen_v1542 = alloca i64
    store i64 %t1541, i64* %nlen_v1542
    %t1543 = load i64, i64* %nlen_v1542
    %t1545 = icmp eq i64 %t1543, 0
    %t1544 = zext i1 %t1545 to i64
    %t1549 = icmp ne i64 %t1544, 0
    br i1 %t1549, label %if.then.1546, label %if.end.1548
if.then.1546:
    ret i64 0
    br label %if.end.1548
if.end.1548:
    %t1550 = load i64, i64* %nlen_v1542
    %t1551 = load i64, i64* %slen_v1539
    %t1553 = icmp sgt i64 %t1550, %t1551
    %t1552 = zext i1 %t1553 to i64
    %t1557 = icmp ne i64 %t1552, 0
    br i1 %t1557, label %if.then.1554, label %if.end.1556
if.then.1554:
    %t1558 = sub i64 0, 1
    ret i64 %t1558
    br label %if.end.1556
if.end.1556:
    %t1559 = load i64, i64* %slen_v1539
    %t1560 = load i64, i64* %nlen_v1542
    %t1561 = sub i64 %t1559, %t1560
    %t1562 = add i64 %t1561, 1
    %limit_v1563 = alloca i64
    store i64 %t1562, i64* %limit_v1563
    %fi_v1564 = alloca i64
    store i64 0, i64* %fi_v1564
    %t1570 = load i64, i64* %limit_v1563
    %rep.1569 = alloca i64
    store i64 0, i64* %rep.1569
    br label %loop.cond.1565
loop.cond.1565:
    %t1571 = load i64, i64* %rep.1569
    %t1572 = icmp slt i64 %t1571, %t1570
    br i1 %t1572, label %loop.body.1566, label %loop.end.1567
loop.body.1566:
    %fmatch_v1573 = alloca i64
    store i64 1, i64* %fmatch_v1573
    %fj_v1574 = alloca i64
    store i64 0, i64* %fj_v1574
    %t1580 = load i64, i64* %nlen_v1542
    %rep.1579 = alloca i64
    store i64 0, i64* %rep.1579
    br label %loop.cond.1575
loop.cond.1575:
    %t1581 = load i64, i64* %rep.1579
    %t1582 = icmp slt i64 %t1581, %t1580
    br i1 %t1582, label %loop.body.1576, label %loop.end.1577
loop.body.1576:
    %t1583 = load i64, i64* %fmatch_v1573
    %t1587 = icmp ne i64 %t1583, 0
    br i1 %t1587, label %if.then.1584, label %if.end.1586
if.then.1584:
    %t1588 = load i64, i64* %s
    %t1590 = load i64, i64* %fi_v1564
    %t1591 = load i64, i64* %fj_v1574
    %t1592 = add i64 %t1590, %t1591
    %t1589 = call i64 @freak_llvm_word_char_at(i64 %t1588, i64 %t1592)
    %t1593 = load i64, i64* %needle
    %t1595 = load i64, i64* %fj_v1574
    %t1594 = call i64 @freak_llvm_word_char_at(i64 %t1593, i64 %t1595)
    %t1596 = call i64 @freak_llvm_word_neq(i64 %t1589, i64 %t1594)
    %t1600 = icmp ne i64 %t1596, 0
    br i1 %t1600, label %if.then.1597, label %if.end.1599
if.then.1597:
    store i64 0, i64* %fmatch_v1573
    br label %if.end.1599
if.end.1599:
    br label %if.end.1586
if.end.1586:
    %t1601 = load i64, i64* %fj_v1574
    %t1602 = add i64 %t1601, 1
    store i64 %t1602, i64* %fj_v1574
    br label %loop.inc.1578
loop.inc.1578:
    %t1603 = load i64, i64* %rep.1579
    %t1604 = add i64 %t1603, 1
    store i64 %t1604, i64* %rep.1579
    br label %loop.cond.1575
loop.end.1577:
    %t1605 = load i64, i64* %fmatch_v1573
    %t1609 = icmp ne i64 %t1605, 0
    br i1 %t1609, label %if.then.1606, label %if.end.1608
if.then.1606:
    %t1610 = load i64, i64* %fi_v1564
    ret i64 %t1610
    br label %if.end.1608
if.end.1608:
    %t1611 = load i64, i64* %fi_v1564
    %t1612 = add i64 %t1611, 1
    store i64 %t1612, i64* %fi_v1564
    br label %loop.inc.1568
loop.inc.1568:
    %t1613 = load i64, i64* %rep.1569
    %t1614 = add i64 %t1613, 1
    store i64 %t1614, i64* %rep.1569
    br label %loop.cond.1565
loop.end.1567:
    %t1615 = sub i64 0, 1
    ret i64 %t1615
    ret i64 0
}

define i64 @freak_int_to_hex(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1616 = load i64, i64* %n
    %t1618 = icmp eq i64 %t1616, 0
    %t1617 = zext i1 %t1618 to i64
    %t1622 = icmp ne i64 %t1617, 0
    br i1 %t1622, label %if.then.1619, label %if.end.1621
if.then.1619:
    %t1623 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.93, i64 0, i64 0
    %t1624 = ptrtoint i8* %t1623 to i64
    ret i64 %t1624
    br label %if.end.1621
if.end.1621:
    %t1625 = getelementptr inbounds [17 x i8], [17 x i8]* @.str.94, i64 0, i64 0
    %t1626 = ptrtoint i8* %t1625 to i64
    %hex_chars_v1627 = alloca i64
    store i64 %t1626, i64* %hex_chars_v1627
    %neg_v1628 = alloca i64
    store i64 0, i64* %neg_v1628
    %t1629 = load i64, i64* %n
    %val_v1630 = alloca i64
    store i64 %t1629, i64* %val_v1630
    %t1631 = load i64, i64* %val_v1630
    %t1633 = icmp slt i64 %t1631, 0
    %t1632 = zext i1 %t1633 to i64
    %t1637 = icmp ne i64 %t1632, 0
    br i1 %t1637, label %if.then.1634, label %if.end.1636
if.then.1634:
    store i64 1, i64* %neg_v1628
    %t1638 = load i64, i64* %val_v1630
    %t1639 = sub i64 0, %t1638
    store i64 %t1639, i64* %val_v1630
    br label %if.end.1636
if.end.1636:
    %t1640 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.95, i64 0, i64 0
    %t1641 = ptrtoint i8* %t1640 to i64
    %hex_out_v1642 = alloca i64
    store i64 %t1641, i64* %hex_out_v1642
    br label %loop.cond.1643
loop.cond.1643:
    %t1646 = load i64, i64* %val_v1630
    %t1648 = icmp sle i64 %t1646, 0
    %t1647 = zext i1 %t1648 to i64
    %t1649 = icmp eq i64 %t1647, 0
    br i1 %t1649, label %loop.body.1644, label %loop.end.1645
loop.body.1644:
    %t1650 = load i64, i64* %val_v1630
    %t1651 = load i64, i64* %val_v1630
    %t1652 = sdiv i64 %t1651, 16
    %t1653 = mul i64 %t1652, 16
    %t1654 = sub i64 %t1650, %t1653
    %rem_v1655 = alloca i64
    store i64 %t1654, i64* %rem_v1655
    %t1656 = load i64, i64* %hex_chars_v1627
    %t1658 = load i64, i64* %rem_v1655
    %t1657 = call i64 @freak_llvm_word_char_at(i64 %t1656, i64 %t1658)
    %t1659 = load i64, i64* %hex_out_v1642
    %t1660 = call i64 @freak_llvm_word_concat(i64 %t1657, i64 %t1659)
    store i64 %t1660, i64* %hex_out_v1642
    %t1661 = load i64, i64* %val_v1630
    %t1662 = sdiv i64 %t1661, 16
    store i64 %t1662, i64* %val_v1630
    br label %loop.cond.1643
loop.end.1645:
    %t1663 = load i64, i64* %neg_v1628
    %t1667 = icmp ne i64 %t1663, 0
    br i1 %t1667, label %if.then.1664, label %if.end.1666
if.then.1664:
    %t1668 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.96, i64 0, i64 0
    %t1669 = ptrtoint i8* %t1668 to i64
    %t1670 = load i64, i64* %hex_out_v1642
    %t1671 = call i64 @freak_llvm_word_concat(i64 %t1669, i64 %t1670)
    store i64 %t1671, i64* %hex_out_v1642
    br label %if.end.1666
if.end.1666:
    %t1672 = load i64, i64* %hex_out_v1642
    ret i64 %t1672
    ret i64 0
}

define i64 @freak_int_to_bin(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1673 = load i64, i64* %n
    %t1675 = icmp eq i64 %t1673, 0
    %t1674 = zext i1 %t1675 to i64
    %t1679 = icmp ne i64 %t1674, 0
    br i1 %t1679, label %if.then.1676, label %if.end.1678
if.then.1676:
    %t1680 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.97, i64 0, i64 0
    %t1681 = ptrtoint i8* %t1680 to i64
    ret i64 %t1681
    br label %if.end.1678
if.end.1678:
    %neg_v1682 = alloca i64
    store i64 0, i64* %neg_v1682
    %t1683 = load i64, i64* %n
    %val_v1684 = alloca i64
    store i64 %t1683, i64* %val_v1684
    %t1685 = load i64, i64* %val_v1684
    %t1687 = icmp slt i64 %t1685, 0
    %t1686 = zext i1 %t1687 to i64
    %t1691 = icmp ne i64 %t1686, 0
    br i1 %t1691, label %if.then.1688, label %if.end.1690
if.then.1688:
    store i64 1, i64* %neg_v1682
    %t1692 = load i64, i64* %val_v1684
    %t1693 = sub i64 0, %t1692
    store i64 %t1693, i64* %val_v1684
    br label %if.end.1690
if.end.1690:
    %t1694 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.98, i64 0, i64 0
    %t1695 = ptrtoint i8* %t1694 to i64
    %bin_out_v1696 = alloca i64
    store i64 %t1695, i64* %bin_out_v1696
    br label %loop.cond.1697
loop.cond.1697:
    %t1700 = load i64, i64* %val_v1684
    %t1702 = icmp sle i64 %t1700, 0
    %t1701 = zext i1 %t1702 to i64
    %t1703 = icmp eq i64 %t1701, 0
    br i1 %t1703, label %loop.body.1698, label %loop.end.1699
loop.body.1698:
    %t1704 = load i64, i64* %val_v1684
    %t1705 = load i64, i64* %val_v1684
    %t1706 = sdiv i64 %t1705, 2
    %t1707 = mul i64 %t1706, 2
    %t1708 = sub i64 %t1704, %t1707
    %rem_v1709 = alloca i64
    store i64 %t1708, i64* %rem_v1709
    %t1710 = load i64, i64* %rem_v1709
    %t1712 = icmp eq i64 %t1710, 1
    %t1711 = zext i1 %t1712 to i64
    %t1716 = icmp ne i64 %t1711, 0
    br i1 %t1716, label %if.then.1713, label %if.else.1714
if.then.1713:
    %t1717 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.99, i64 0, i64 0
    %t1718 = ptrtoint i8* %t1717 to i64
    %t1719 = load i64, i64* %bin_out_v1696
    %t1720 = call i64 @freak_llvm_word_concat(i64 %t1718, i64 %t1719)
    store i64 %t1720, i64* %bin_out_v1696
    br label %if.end.1715
if.else.1714:
    %t1721 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.100, i64 0, i64 0
    %t1722 = ptrtoint i8* %t1721 to i64
    %t1723 = load i64, i64* %bin_out_v1696
    %t1724 = call i64 @freak_llvm_word_concat(i64 %t1722, i64 %t1723)
    store i64 %t1724, i64* %bin_out_v1696
    br label %if.end.1715
if.end.1715:
    %t1725 = load i64, i64* %val_v1684
    %t1726 = sdiv i64 %t1725, 2
    store i64 %t1726, i64* %val_v1684
    br label %loop.cond.1697
loop.end.1699:
    %t1727 = load i64, i64* %neg_v1682
    %t1731 = icmp ne i64 %t1727, 0
    br i1 %t1731, label %if.then.1728, label %if.end.1730
if.then.1728:
    %t1732 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.101, i64 0, i64 0
    %t1733 = ptrtoint i8* %t1732 to i64
    %t1734 = load i64, i64* %bin_out_v1696
    %t1735 = call i64 @freak_llvm_word_concat(i64 %t1733, i64 %t1734)
    store i64 %t1735, i64* %bin_out_v1696
    br label %if.end.1730
if.end.1730:
    %t1736 = load i64, i64* %bin_out_v1696
    ret i64 %t1736
    ret i64 0
}

define i64 @freak_int_to_oct(i64 %arg_n) {
entry:
    %n = alloca i64
    store i64 %arg_n, i64* %n
    %t1737 = load i64, i64* %n
    %t1739 = icmp eq i64 %t1737, 0
    %t1738 = zext i1 %t1739 to i64
    %t1743 = icmp ne i64 %t1738, 0
    br i1 %t1743, label %if.then.1740, label %if.end.1742
if.then.1740:
    %t1744 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.102, i64 0, i64 0
    %t1745 = ptrtoint i8* %t1744 to i64
    ret i64 %t1745
    br label %if.end.1742
if.end.1742:
    %t1746 = getelementptr inbounds [9 x i8], [9 x i8]* @.str.103, i64 0, i64 0
    %t1747 = ptrtoint i8* %t1746 to i64
    %oct_chars_v1748 = alloca i64
    store i64 %t1747, i64* %oct_chars_v1748
    %neg_v1749 = alloca i64
    store i64 0, i64* %neg_v1749
    %t1750 = load i64, i64* %n
    %val_v1751 = alloca i64
    store i64 %t1750, i64* %val_v1751
    %t1752 = load i64, i64* %val_v1751
    %t1754 = icmp slt i64 %t1752, 0
    %t1753 = zext i1 %t1754 to i64
    %t1758 = icmp ne i64 %t1753, 0
    br i1 %t1758, label %if.then.1755, label %if.end.1757
if.then.1755:
    store i64 1, i64* %neg_v1749
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
    %t1777 = load i64, i64* %oct_chars_v1748
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
    %t1784 = load i64, i64* %neg_v1749
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
    %neg_v1885 = alloca i64
    store i64 0, i64* %neg_v1885
    %wi_v1886 = alloca i64
    store i64 0, i64* %wi_v1886
    %t1887 = load i64, i64* %s
    %t1888 = call i64 @freak_llvm_word_char_at(i64 %t1887, i64 0)
    %t1889 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.116, i64 0, i64 0
    %t1890 = ptrtoint i8* %t1889 to i64
    %t1891 = call i64 @freak_llvm_word_eq(i64 %t1888, i64 %t1890)
    %t1895 = icmp ne i64 %t1891, 0
    br i1 %t1895, label %if.then.1892, label %if.end.1894
if.then.1892:
    store i64 1, i64* %neg_v1885
    store i64 1, i64* %wi_v1886
    br label %if.end.1894
if.end.1894:
    %num_v1896 = alloca i64
    store i64 0, i64* %num_v1896
    br label %loop.cond.1897
loop.cond.1897:
    %t1900 = load i64, i64* %wi_v1886
    %t1901 = load i64, i64* %slen_v1877
    %t1903 = icmp sge i64 %t1900, %t1901
    %t1902 = zext i1 %t1903 to i64
    %t1904 = icmp eq i64 %t1902, 0
    br i1 %t1904, label %loop.body.1898, label %loop.end.1899
loop.body.1898:
    %t1905 = load i64, i64* %s
    %t1907 = load i64, i64* %wi_v1886
    %t1906 = call i64 @freak_llvm_word_char_at(i64 %t1905, i64 %t1907)
    %t1908 = call i64 @freak_char_to_digit(i64 %t1906)
    %d_v1909 = alloca i64
    store i64 %t1908, i64* %d_v1909
    %t1910 = load i64, i64* %d_v1909
    %t1912 = icmp slt i64 %t1910, 0
    %t1911 = zext i1 %t1912 to i64
    %t1916 = icmp ne i64 %t1911, 0
    br i1 %t1916, label %if.then.1913, label %if.end.1915
if.then.1913:
    ret i64 0
    br label %if.end.1915
if.end.1915:
    %t1917 = load i64, i64* %num_v1896
    %t1918 = mul i64 %t1917, 10
    %t1919 = load i64, i64* %d_v1909
    %t1920 = add i64 %t1918, %t1919
    store i64 %t1920, i64* %num_v1896
    %t1921 = load i64, i64* %wi_v1886
    %t1922 = add i64 %t1921, 1
    store i64 %t1922, i64* %wi_v1886
    br label %loop.cond.1897
loop.end.1899:
    %t1923 = load i64, i64* %neg_v1885
    %t1927 = icmp ne i64 %t1923, 0
    br i1 %t1927, label %if.then.1924, label %if.end.1926
if.then.1924:
    %t1928 = load i64, i64* %num_v1896
    %t1929 = sub i64 0, %t1928
    ret i64 %t1929
    br label %if.end.1926
if.end.1926:
    %t1930 = load i64, i64* %num_v1896
    ret i64 %t1930
    ret i64 0
}

define i64 @freak_bool_to_word(i64 %arg_b) {
entry:
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t1931 = load i64, i64* %b
    %t1935 = icmp ne i64 %t1931, 0
    br i1 %t1935, label %if.then.1932, label %if.end.1934
if.then.1932:
    %t1936 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.117, i64 0, i64 0
    %t1937 = ptrtoint i8* %t1936 to i64
    ret i64 %t1937
    br label %if.end.1934
if.end.1934:
    %t1938 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.118, i64 0, i64 0
    %t1939 = ptrtoint i8* %t1938 to i64
    ret i64 %t1939
    ret i64 0
}

define void @freak_array_sort_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t1940 = load i64, i64* %handle
    %t1941 = call i64 @freak_llvm_array_len(i64 %t1940)
    %alen_v1942 = alloca i64
    store i64 %t1941, i64* %alen_v1942
    %t1943 = load i64, i64* %alen_v1942
    %t1945 = icmp sle i64 %t1943, 1
    %t1944 = zext i1 %t1945 to i64
    %t1949 = icmp ne i64 %t1944, 0
    br i1 %t1949, label %if.then.1946, label %if.end.1948
if.then.1946:
    ret void
    br label %if.end.1948
if.end.1948:
    %si_v1950 = alloca i64
    store i64 1, i64* %si_v1950
    br label %loop.cond.1951
loop.cond.1951:
    %t1954 = load i64, i64* %si_v1950
    %t1955 = load i64, i64* %alen_v1942
    %t1957 = icmp sge i64 %t1954, %t1955
    %t1956 = zext i1 %t1957 to i64
    %t1958 = icmp eq i64 %t1956, 0
    br i1 %t1958, label %loop.body.1952, label %loop.end.1953
loop.body.1952:
    %t1959 = load i64, i64* %handle
    %t1960 = load i64, i64* %si_v1950
    %t1961 = call i64 @freak_llvm_array_get(i64 %t1959, i64 %t1960)
    %key_w_v1962 = alloca i64
    store i64 %t1961, i64* %key_w_v1962
    %t1963 = load i64, i64* %key_w_v1962
    %t1964 = call i64 @freak_llvm_word_to_int(i64 %t1963)
    %key_v1965 = alloca i64
    store i64 %t1964, i64* %key_v1965
    %t1966 = load i64, i64* %si_v1950
    %t1967 = sub i64 %t1966, 1
    %sj_v1968 = alloca i64
    store i64 %t1967, i64* %sj_v1968
    %sorted_v1969 = alloca i64
    store i64 0, i64* %sorted_v1969
    br label %loop.cond.1970
loop.cond.1970:
    %t1973 = load i64, i64* %sj_v1968
    %t1975 = icmp slt i64 %t1973, 0
    %t1974 = zext i1 %t1975 to i64
    %t1976 = load i64, i64* %sorted_v1969
    %t1978 = icmp ne i64 %t1974, 0
    %t1979 = icmp ne i64 %t1976, 0
    %t1980 = or i1 %t1978, %t1979
    %t1977 = zext i1 %t1980 to i64
    %t1981 = icmp eq i64 %t1977, 0
    br i1 %t1981, label %loop.body.1971, label %loop.end.1972
loop.body.1971:
    %t1982 = load i64, i64* %handle
    %t1983 = load i64, i64* %sj_v1968
    %t1984 = call i64 @freak_llvm_array_get(i64 %t1982, i64 %t1983)
    %cw_v1985 = alloca i64
    store i64 %t1984, i64* %cw_v1985
    %t1986 = load i64, i64* %cw_v1985
    %t1987 = call i64 @freak_llvm_word_to_int(i64 %t1986)
    %cv_v1988 = alloca i64
    store i64 %t1987, i64* %cv_v1988
    %t1989 = load i64, i64* %cv_v1988
    %t1990 = load i64, i64* %key_v1965
    %t1992 = icmp sgt i64 %t1989, %t1990
    %t1991 = zext i1 %t1992 to i64
    %t1996 = icmp ne i64 %t1991, 0
    br i1 %t1996, label %if.then.1993, label %if.else.1994
if.then.1993:
    %t1997 = load i64, i64* %handle
    %t1998 = load i64, i64* %sj_v1968
    %t1999 = add i64 %t1998, 1
    %t2000 = load i64, i64* %cw_v1985
    call void @freak_llvm_array_set(i64 %t1997, i64 %t1999, i64 %t2000)
    %t2001 = load i64, i64* %sj_v1968
    %t2002 = sub i64 %t2001, 1
    store i64 %t2002, i64* %sj_v1968
    br label %if.end.1995
if.else.1994:
    store i64 1, i64* %sorted_v1969
    br label %if.end.1995
if.end.1995:
    br label %loop.cond.1970
loop.end.1972:
    %t2003 = load i64, i64* %handle
    %t2004 = load i64, i64* %sj_v1968
    %t2005 = add i64 %t2004, 1
    %t2006 = load i64, i64* %key_v1965
    %t2007 = call i64 @freak_llvm_word_from_int(i64 %t2006)
    call void @freak_llvm_array_set(i64 %t2003, i64 %t2005, i64 %t2007)
    %t2008 = load i64, i64* %si_v1950
    %t2009 = add i64 %t2008, 1
    store i64 %t2009, i64* %si_v1950
    br label %loop.cond.1951
loop.end.1953:
    ret void
}

define void @freak_array_sort_word(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2010 = load i64, i64* %handle
    %t2011 = call i64 @freak_llvm_array_len(i64 %t2010)
    %alen_v2012 = alloca i64
    store i64 %t2011, i64* %alen_v2012
    %t2013 = load i64, i64* %alen_v2012
    %t2015 = icmp sle i64 %t2013, 1
    %t2014 = zext i1 %t2015 to i64
    %t2019 = icmp ne i64 %t2014, 0
    br i1 %t2019, label %if.then.2016, label %if.end.2018
if.then.2016:
    ret void
    br label %if.end.2018
if.end.2018:
    %si_v2020 = alloca i64
    store i64 1, i64* %si_v2020
    br label %loop.cond.2021
loop.cond.2021:
    %t2024 = load i64, i64* %si_v2020
    %t2025 = load i64, i64* %alen_v2012
    %t2027 = icmp sge i64 %t2024, %t2025
    %t2026 = zext i1 %t2027 to i64
    %t2028 = icmp eq i64 %t2026, 0
    br i1 %t2028, label %loop.body.2022, label %loop.end.2023
loop.body.2022:
    %t2029 = load i64, i64* %handle
    %t2030 = load i64, i64* %si_v2020
    %t2031 = call i64 @freak_llvm_array_get(i64 %t2029, i64 %t2030)
    %key_w_v2032 = alloca i64
    store i64 %t2031, i64* %key_w_v2032
    %t2033 = load i64, i64* %si_v2020
    %t2034 = sub i64 %t2033, 1
    %sj_v2035 = alloca i64
    store i64 %t2034, i64* %sj_v2035
    %sorted_v2036 = alloca i64
    store i64 0, i64* %sorted_v2036
    br label %loop.cond.2037
loop.cond.2037:
    %t2040 = load i64, i64* %sj_v2035
    %t2042 = icmp slt i64 %t2040, 0
    %t2041 = zext i1 %t2042 to i64
    %t2043 = load i64, i64* %sorted_v2036
    %t2045 = icmp ne i64 %t2041, 0
    %t2046 = icmp ne i64 %t2043, 0
    %t2047 = or i1 %t2045, %t2046
    %t2044 = zext i1 %t2047 to i64
    %t2048 = icmp eq i64 %t2044, 0
    br i1 %t2048, label %loop.body.2038, label %loop.end.2039
loop.body.2038:
    %t2049 = load i64, i64* %handle
    %t2050 = load i64, i64* %sj_v2035
    %t2051 = call i64 @freak_llvm_array_get(i64 %t2049, i64 %t2050)
    %cw_v2052 = alloca i64
    store i64 %t2051, i64* %cw_v2052
    %t2053 = load i64, i64* %cw_v2052
    %t2054 = load i64, i64* %key_w_v2032
    %t2055 = call i64 @freak_word_compare(i64 %t2053, i64 %t2054)
    %t2057 = icmp sgt i64 %t2055, 0
    %t2056 = zext i1 %t2057 to i64
    %t2061 = icmp ne i64 %t2056, 0
    br i1 %t2061, label %if.then.2058, label %if.else.2059
if.then.2058:
    %t2062 = load i64, i64* %handle
    %t2063 = load i64, i64* %sj_v2035
    %t2064 = add i64 %t2063, 1
    %t2065 = load i64, i64* %cw_v2052
    call void @freak_llvm_array_set(i64 %t2062, i64 %t2064, i64 %t2065)
    %t2066 = load i64, i64* %sj_v2035
    %t2067 = sub i64 %t2066, 1
    store i64 %t2067, i64* %sj_v2035
    br label %if.end.2060
if.else.2059:
    store i64 1, i64* %sorted_v2036
    br label %if.end.2060
if.end.2060:
    br label %loop.cond.2037
loop.end.2039:
    %t2068 = load i64, i64* %handle
    %t2069 = load i64, i64* %sj_v2035
    %t2070 = add i64 %t2069, 1
    %t2071 = load i64, i64* %key_w_v2032
    call void @freak_llvm_array_set(i64 %t2068, i64 %t2070, i64 %t2071)
    %t2072 = load i64, i64* %si_v2020
    %t2073 = add i64 %t2072, 1
    store i64 %t2073, i64* %si_v2020
    br label %loop.cond.2021
loop.end.2023:
    ret void
}

define i64 @freak_array_binary_search_int(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %lo_v2074 = alloca i64
    store i64 0, i64* %lo_v2074
    %t2075 = load i64, i64* %handle
    %t2076 = call i64 @freak_llvm_array_len(i64 %t2075)
    %t2077 = sub i64 %t2076, 1
    %hi_v2078 = alloca i64
    store i64 %t2077, i64* %hi_v2078
    br label %loop.cond.2079
loop.cond.2079:
    %t2082 = load i64, i64* %lo_v2074
    %t2083 = load i64, i64* %hi_v2078
    %t2085 = icmp sgt i64 %t2082, %t2083
    %t2084 = zext i1 %t2085 to i64
    %t2086 = icmp eq i64 %t2084, 0
    br i1 %t2086, label %loop.body.2080, label %loop.end.2081
loop.body.2080:
    %t2087 = load i64, i64* %hi_v2078
    %t2088 = load i64, i64* %lo_v2074
    %t2089 = sub i64 %t2087, %t2088
    %range_v2090 = alloca i64
    store i64 %t2089, i64* %range_v2090
    %t2091 = load i64, i64* %range_v2090
    %t2092 = sdiv i64 %t2091, 2
    %half_v2093 = alloca i64
    store i64 %t2092, i64* %half_v2093
    %t2094 = load i64, i64* %lo_v2074
    %t2095 = load i64, i64* %half_v2093
    %t2096 = add i64 %t2094, %t2095
    %mid_v2097 = alloca i64
    store i64 %t2096, i64* %mid_v2097
    %t2098 = load i64, i64* %handle
    %t2099 = load i64, i64* %mid_v2097
    %t2100 = call i64 @freak_llvm_array_get(i64 %t2098, i64 %t2099)
    %mw_v2101 = alloca i64
    store i64 %t2100, i64* %mw_v2101
    %t2102 = load i64, i64* %mw_v2101
    %t2103 = call i64 @freak_llvm_word_to_int(i64 %t2102)
    %mv_v2104 = alloca i64
    store i64 %t2103, i64* %mv_v2104
    %t2105 = load i64, i64* %mv_v2104
    %t2106 = load i64, i64* %target
    %t2108 = icmp eq i64 %t2105, %t2106
    %t2107 = zext i1 %t2108 to i64
    %t2112 = icmp ne i64 %t2107, 0
    br i1 %t2112, label %if.then.2109, label %if.end.2111
if.then.2109:
    %t2113 = load i64, i64* %mid_v2097
    ret i64 %t2113
    br label %if.end.2111
if.end.2111:
    %t2114 = load i64, i64* %mv_v2104
    %t2115 = load i64, i64* %target
    %t2117 = icmp slt i64 %t2114, %t2115
    %t2116 = zext i1 %t2117 to i64
    %t2121 = icmp ne i64 %t2116, 0
    br i1 %t2121, label %if.then.2118, label %if.else.2119
if.then.2118:
    %t2122 = load i64, i64* %mid_v2097
    %t2123 = add i64 %t2122, 1
    store i64 %t2123, i64* %lo_v2074
    br label %if.end.2120
if.else.2119:
    %t2124 = load i64, i64* %mid_v2097
    %t2125 = sub i64 %t2124, 1
    store i64 %t2125, i64* %hi_v2078
    br label %if.end.2120
if.end.2120:
    br label %loop.cond.2079
loop.end.2081:
    %t2126 = sub i64 0, 1
    ret i64 %t2126
    ret i64 0
}

define i64 @freak_array_find(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2127 = load i64, i64* %handle
    %t2128 = call i64 @freak_llvm_array_len(i64 %t2127)
    %alen_v2129 = alloca i64
    store i64 %t2128, i64* %alen_v2129
    %fi_v2130 = alloca i64
    store i64 0, i64* %fi_v2130
    %t2136 = load i64, i64* %alen_v2129
    %rep.2135 = alloca i64
    store i64 0, i64* %rep.2135
    br label %loop.cond.2131
loop.cond.2131:
    %t2137 = load i64, i64* %rep.2135
    %t2138 = icmp slt i64 %t2137, %t2136
    br i1 %t2138, label %loop.body.2132, label %loop.end.2133
loop.body.2132:
    %t2139 = load i64, i64* %handle
    %t2140 = load i64, i64* %fi_v2130
    %t2141 = call i64 @freak_llvm_array_get(i64 %t2139, i64 %t2140)
    %fw_v2142 = alloca i64
    store i64 %t2141, i64* %fw_v2142
    %t2143 = load i64, i64* %fw_v2142
    %t2144 = load i64, i64* %target
    %t2145 = call i64 @freak_llvm_word_eq(i64 %t2143, i64 %t2144)
    %t2149 = icmp ne i64 %t2145, 0
    br i1 %t2149, label %if.then.2146, label %if.end.2148
if.then.2146:
    %t2150 = load i64, i64* %fi_v2130
    ret i64 %t2150
    br label %if.end.2148
if.end.2148:
    %t2151 = load i64, i64* %fi_v2130
    %t2152 = add i64 %t2151, 1
    store i64 %t2152, i64* %fi_v2130
    br label %loop.inc.2134
loop.inc.2134:
    %t2153 = load i64, i64* %rep.2135
    %t2154 = add i64 %t2153, 1
    store i64 %t2154, i64* %rep.2135
    br label %loop.cond.2131
loop.end.2133:
    %t2155 = sub i64 0, 1
    ret i64 %t2155
    ret i64 0
}

define i64 @freak_array_contains(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2156 = load i64, i64* %handle
    %t2157 = load i64, i64* %target
    %t2158 = call i64 @freak_array_find(i64 %t2156, i64 %t2157)
    %t2160 = icmp sge i64 %t2158, 0
    %t2159 = zext i1 %t2160 to i64
    ret i64 %t2159
    ret i64 0
}

define void @freak_array_reverse(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2161 = load i64, i64* %handle
    %t2162 = call i64 @freak_llvm_array_len(i64 %t2161)
    %alen_v2163 = alloca i64
    store i64 %t2162, i64* %alen_v2163
    %t2164 = load i64, i64* %alen_v2163
    %t2166 = icmp sle i64 %t2164, 1
    %t2165 = zext i1 %t2166 to i64
    %t2170 = icmp ne i64 %t2165, 0
    br i1 %t2170, label %if.then.2167, label %if.end.2169
if.then.2167:
    ret void
    br label %if.end.2169
if.end.2169:
    %lo_v2171 = alloca i64
    store i64 0, i64* %lo_v2171
    %t2172 = load i64, i64* %alen_v2163
    %t2173 = sub i64 %t2172, 1
    %hi_v2174 = alloca i64
    store i64 %t2173, i64* %hi_v2174
    br label %loop.cond.2175
loop.cond.2175:
    %t2178 = load i64, i64* %lo_v2171
    %t2179 = load i64, i64* %hi_v2174
    %t2181 = icmp sge i64 %t2178, %t2179
    %t2180 = zext i1 %t2181 to i64
    %t2182 = icmp eq i64 %t2180, 0
    br i1 %t2182, label %loop.body.2176, label %loop.end.2177
loop.body.2176:
    %t2183 = load i64, i64* %handle
    %t2184 = load i64, i64* %lo_v2171
    %t2185 = call i64 @freak_llvm_array_get(i64 %t2183, i64 %t2184)
    %tmp_v2186 = alloca i64
    store i64 %t2185, i64* %tmp_v2186
    %t2187 = load i64, i64* %handle
    %t2188 = load i64, i64* %hi_v2174
    %t2189 = call i64 @freak_llvm_array_get(i64 %t2187, i64 %t2188)
    %hw_v2190 = alloca i64
    store i64 %t2189, i64* %hw_v2190
    %t2191 = load i64, i64* %handle
    %t2192 = load i64, i64* %lo_v2171
    %t2193 = load i64, i64* %hw_v2190
    call void @freak_llvm_array_set(i64 %t2191, i64 %t2192, i64 %t2193)
    %t2194 = load i64, i64* %handle
    %t2195 = load i64, i64* %hi_v2174
    %t2196 = load i64, i64* %tmp_v2186
    call void @freak_llvm_array_set(i64 %t2194, i64 %t2195, i64 %t2196)
    %t2197 = load i64, i64* %lo_v2171
    %t2198 = add i64 %t2197, 1
    store i64 %t2198, i64* %lo_v2171
    %t2199 = load i64, i64* %hi_v2174
    %t2200 = sub i64 %t2199, 1
    store i64 %t2200, i64* %hi_v2174
    br label %loop.cond.2175
loop.end.2177:
    ret void
}

define i64 @freak_array_copy(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2201 = call i64 @freak_llvm_array_new()
    %new_arr_v2202 = alloca i64
    store i64 %t2201, i64* %new_arr_v2202
    %t2203 = load i64, i64* %handle
    %t2204 = call i64 @freak_llvm_array_len(i64 %t2203)
    %alen_v2205 = alloca i64
    store i64 %t2204, i64* %alen_v2205
    %ci_v2206 = alloca i64
    store i64 0, i64* %ci_v2206
    %t2212 = load i64, i64* %alen_v2205
    %rep.2211 = alloca i64
    store i64 0, i64* %rep.2211
    br label %loop.cond.2207
loop.cond.2207:
    %t2213 = load i64, i64* %rep.2211
    %t2214 = icmp slt i64 %t2213, %t2212
    br i1 %t2214, label %loop.body.2208, label %loop.end.2209
loop.body.2208:
    %t2215 = load i64, i64* %handle
    %t2216 = load i64, i64* %ci_v2206
    %t2217 = call i64 @freak_llvm_array_get(i64 %t2215, i64 %t2216)
    %cw_v2218 = alloca i64
    store i64 %t2217, i64* %cw_v2218
    %t2219 = load i64, i64* %new_arr_v2202
    %t2220 = load i64, i64* %cw_v2218
    call void @freak_llvm_array_push(i64 %t2219, i64 %t2220)
    %t2221 = load i64, i64* %ci_v2206
    %t2222 = add i64 %t2221, 1
    store i64 %t2222, i64* %ci_v2206
    br label %loop.inc.2210
loop.inc.2210:
    %t2223 = load i64, i64* %rep.2211
    %t2224 = add i64 %t2223, 1
    store i64 %t2224, i64* %rep.2211
    br label %loop.cond.2207
loop.end.2209:
    %t2225 = load i64, i64* %new_arr_v2202
    ret i64 %t2225
    ret i64 0
}

define i64 @freak_array_join(i64 %arg_handle, i64 %arg_sep) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %sep = alloca i64
    store i64 %arg_sep, i64* %sep
    %t2226 = load i64, i64* %handle
    %t2227 = call i64 @freak_llvm_array_len(i64 %t2226)
    %alen_v2228 = alloca i64
    store i64 %t2227, i64* %alen_v2228
    %t2229 = load i64, i64* %alen_v2228
    %t2231 = icmp eq i64 %t2229, 0
    %t2230 = zext i1 %t2231 to i64
    %t2235 = icmp ne i64 %t2230, 0
    br i1 %t2235, label %if.then.2232, label %if.end.2234
if.then.2232:
    %t2236 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.119, i64 0, i64 0
    %t2237 = ptrtoint i8* %t2236 to i64
    ret i64 %t2237
    br label %if.end.2234
if.end.2234:
    %t2238 = load i64, i64* %handle
    %t2239 = call i64 @freak_llvm_array_get(i64 %t2238, i64 0)
    %aj_out_v2240 = alloca i64
    store i64 %t2239, i64* %aj_out_v2240
    %ji_v2241 = alloca i64
    store i64 1, i64* %ji_v2241
    br label %loop.cond.2242
loop.cond.2242:
    %t2245 = load i64, i64* %ji_v2241
    %t2246 = load i64, i64* %alen_v2228
    %t2248 = icmp sge i64 %t2245, %t2246
    %t2247 = zext i1 %t2248 to i64
    %t2249 = icmp eq i64 %t2247, 0
    br i1 %t2249, label %loop.body.2243, label %loop.end.2244
loop.body.2243:
    %t2250 = load i64, i64* %handle
    %t2251 = load i64, i64* %ji_v2241
    %t2252 = call i64 @freak_llvm_array_get(i64 %t2250, i64 %t2251)
    %jw_v2253 = alloca i64
    store i64 %t2252, i64* %jw_v2253
    %t2254 = load i64, i64* %aj_out_v2240
    %t2255 = load i64, i64* %sep
    %t2256 = call i64 @freak_llvm_word_concat(i64 %t2254, i64 %t2255)
    %t2257 = load i64, i64* %jw_v2253
    %t2258 = call i64 @freak_llvm_word_concat(i64 %t2256, i64 %t2257)
    store i64 %t2258, i64* %aj_out_v2240
    %t2259 = load i64, i64* %ji_v2241
    %t2260 = add i64 %t2259, 1
    store i64 %t2260, i64* %ji_v2241
    br label %loop.cond.2242
loop.end.2244:
    %t2261 = load i64, i64* %aj_out_v2240
    ret i64 %t2261
    ret i64 0
}

define i64 @freak_array_count(i64 %arg_handle, i64 %arg_target) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %target = alloca i64
    store i64 %arg_target, i64* %target
    %t2262 = load i64, i64* %handle
    %t2263 = call i64 @freak_llvm_array_len(i64 %t2262)
    %alen_v2264 = alloca i64
    store i64 %t2263, i64* %alen_v2264
    %cnt_v2265 = alloca i64
    store i64 0, i64* %cnt_v2265
    %ci_v2266 = alloca i64
    store i64 0, i64* %ci_v2266
    %t2272 = load i64, i64* %alen_v2264
    %rep.2271 = alloca i64
    store i64 0, i64* %rep.2271
    br label %loop.cond.2267
loop.cond.2267:
    %t2273 = load i64, i64* %rep.2271
    %t2274 = icmp slt i64 %t2273, %t2272
    br i1 %t2274, label %loop.body.2268, label %loop.end.2269
loop.body.2268:
    %t2275 = load i64, i64* %handle
    %t2276 = load i64, i64* %ci_v2266
    %t2277 = call i64 @freak_llvm_array_get(i64 %t2275, i64 %t2276)
    %cw_v2278 = alloca i64
    store i64 %t2277, i64* %cw_v2278
    %t2279 = load i64, i64* %cw_v2278
    %t2280 = load i64, i64* %target
    %t2281 = call i64 @freak_llvm_word_eq(i64 %t2279, i64 %t2280)
    %t2285 = icmp ne i64 %t2281, 0
    br i1 %t2285, label %if.then.2282, label %if.end.2284
if.then.2282:
    %t2286 = load i64, i64* %cnt_v2265
    %t2287 = add i64 %t2286, 1
    store i64 %t2287, i64* %cnt_v2265
    br label %if.end.2284
if.end.2284:
    %t2288 = load i64, i64* %ci_v2266
    %t2289 = add i64 %t2288, 1
    store i64 %t2289, i64* %ci_v2266
    br label %loop.inc.2270
loop.inc.2270:
    %t2290 = load i64, i64* %rep.2271
    %t2291 = add i64 %t2290, 1
    store i64 %t2291, i64* %rep.2271
    br label %loop.cond.2267
loop.end.2269:
    %t2292 = load i64, i64* %cnt_v2265
    ret i64 %t2292
    ret i64 0
}

define i64 @freak_array_unique(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2293 = load i64, i64* %handle
    %t2294 = call i64 @freak_llvm_array_len(i64 %t2293)
    %alen_v2295 = alloca i64
    store i64 %t2294, i64* %alen_v2295
    %t2296 = load i64, i64* %alen_v2295
    %t2298 = icmp sle i64 %t2296, 1
    %t2297 = zext i1 %t2298 to i64
    %t2302 = icmp ne i64 %t2297, 0
    br i1 %t2302, label %if.then.2299, label %if.end.2301
if.then.2299:
    %t2303 = load i64, i64* %alen_v2295
    ret i64 %t2303
    br label %if.end.2301
if.end.2301:
    %write_idx_v2304 = alloca i64
    store i64 1, i64* %write_idx_v2304
    %ri_v2305 = alloca i64
    store i64 1, i64* %ri_v2305
    br label %loop.cond.2306
loop.cond.2306:
    %t2309 = load i64, i64* %ri_v2305
    %t2310 = load i64, i64* %alen_v2295
    %t2312 = icmp sge i64 %t2309, %t2310
    %t2311 = zext i1 %t2312 to i64
    %t2313 = icmp eq i64 %t2311, 0
    br i1 %t2313, label %loop.body.2307, label %loop.end.2308
loop.body.2307:
    %t2314 = load i64, i64* %handle
    %t2315 = load i64, i64* %ri_v2305
    %t2316 = call i64 @freak_llvm_array_get(i64 %t2314, i64 %t2315)
    %cur_v2317 = alloca i64
    store i64 %t2316, i64* %cur_v2317
    %t2318 = load i64, i64* %handle
    %t2319 = load i64, i64* %ri_v2305
    %t2320 = sub i64 %t2319, 1
    %t2321 = call i64 @freak_llvm_array_get(i64 %t2318, i64 %t2320)
    %prev_v2322 = alloca i64
    store i64 %t2321, i64* %prev_v2322
    %t2323 = load i64, i64* %cur_v2317
    %t2324 = load i64, i64* %prev_v2322
    %t2325 = call i64 @freak_llvm_word_neq(i64 %t2323, i64 %t2324)
    %t2329 = icmp ne i64 %t2325, 0
    br i1 %t2329, label %if.then.2326, label %if.end.2328
if.then.2326:
    %t2330 = load i64, i64* %handle
    %t2331 = load i64, i64* %write_idx_v2304
    %t2332 = load i64, i64* %cur_v2317
    call void @freak_llvm_array_set(i64 %t2330, i64 %t2331, i64 %t2332)
    %t2333 = load i64, i64* %write_idx_v2304
    %t2334 = add i64 %t2333, 1
    store i64 %t2334, i64* %write_idx_v2304
    br label %if.end.2328
if.end.2328:
    %t2335 = load i64, i64* %ri_v2305
    %t2336 = add i64 %t2335, 1
    store i64 %t2336, i64* %ri_v2305
    br label %loop.cond.2306
loop.end.2308:
    %t2337 = load i64, i64* %write_idx_v2304
    ret i64 %t2337
    ret i64 0
}

define i64 @freak_array_sum_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2338 = load i64, i64* %handle
    %t2339 = call i64 @freak_llvm_array_len(i64 %t2338)
    %alen_v2340 = alloca i64
    store i64 %t2339, i64* %alen_v2340
    %total_v2341 = alloca i64
    store i64 0, i64* %total_v2341
    %si_v2342 = alloca i64
    store i64 0, i64* %si_v2342
    %t2348 = load i64, i64* %alen_v2340
    %rep.2347 = alloca i64
    store i64 0, i64* %rep.2347
    br label %loop.cond.2343
loop.cond.2343:
    %t2349 = load i64, i64* %rep.2347
    %t2350 = icmp slt i64 %t2349, %t2348
    br i1 %t2350, label %loop.body.2344, label %loop.end.2345
loop.body.2344:
    %t2351 = load i64, i64* %handle
    %t2352 = load i64, i64* %si_v2342
    %t2353 = call i64 @freak_llvm_array_get(i64 %t2351, i64 %t2352)
    %sw_v2354 = alloca i64
    store i64 %t2353, i64* %sw_v2354
    %t2355 = load i64, i64* %sw_v2354
    %t2356 = call i64 @freak_llvm_word_to_int(i64 %t2355)
    %t2357 = load i64, i64* %total_v2341
    %t2358 = add i64 %t2357, %t2356
    store i64 %t2358, i64* %total_v2341
    %t2359 = load i64, i64* %si_v2342
    %t2360 = add i64 %t2359, 1
    store i64 %t2360, i64* %si_v2342
    br label %loop.inc.2346
loop.inc.2346:
    %t2361 = load i64, i64* %rep.2347
    %t2362 = add i64 %t2361, 1
    store i64 %t2362, i64* %rep.2347
    br label %loop.cond.2343
loop.end.2345:
    %t2363 = load i64, i64* %total_v2341
    ret i64 %t2363
    ret i64 0
}

define i64 @freak_array_max_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2364 = load i64, i64* %handle
    %t2365 = call i64 @freak_llvm_array_len(i64 %t2364)
    %alen_v2366 = alloca i64
    store i64 %t2365, i64* %alen_v2366
    %t2367 = load i64, i64* %alen_v2366
    %t2369 = icmp eq i64 %t2367, 0
    %t2368 = zext i1 %t2369 to i64
    %t2373 = icmp ne i64 %t2368, 0
    br i1 %t2373, label %if.then.2370, label %if.end.2372
if.then.2370:
    ret i64 0
    br label %if.end.2372
if.end.2372:
    %t2374 = load i64, i64* %handle
    %t2375 = call i64 @freak_llvm_array_get(i64 %t2374, i64 0)
    %mw_v2376 = alloca i64
    store i64 %t2375, i64* %mw_v2376
    %t2377 = load i64, i64* %mw_v2376
    %t2378 = call i64 @freak_llvm_word_to_int(i64 %t2377)
    %mx_v2379 = alloca i64
    store i64 %t2378, i64* %mx_v2379
    %mi_v2380 = alloca i64
    store i64 1, i64* %mi_v2380
    br label %loop.cond.2381
loop.cond.2381:
    %t2384 = load i64, i64* %mi_v2380
    %t2385 = load i64, i64* %alen_v2366
    %t2387 = icmp sge i64 %t2384, %t2385
    %t2386 = zext i1 %t2387 to i64
    %t2388 = icmp eq i64 %t2386, 0
    br i1 %t2388, label %loop.body.2382, label %loop.end.2383
loop.body.2382:
    %t2389 = load i64, i64* %handle
    %t2390 = load i64, i64* %mi_v2380
    %t2391 = call i64 @freak_llvm_array_get(i64 %t2389, i64 %t2390)
    %cw_v2392 = alloca i64
    store i64 %t2391, i64* %cw_v2392
    %t2393 = load i64, i64* %cw_v2392
    %t2394 = call i64 @freak_llvm_word_to_int(i64 %t2393)
    %cv_v2395 = alloca i64
    store i64 %t2394, i64* %cv_v2395
    %t2396 = load i64, i64* %cv_v2395
    %t2397 = load i64, i64* %mx_v2379
    %t2399 = icmp sgt i64 %t2396, %t2397
    %t2398 = zext i1 %t2399 to i64
    %t2403 = icmp ne i64 %t2398, 0
    br i1 %t2403, label %if.then.2400, label %if.end.2402
if.then.2400:
    %t2404 = load i64, i64* %cv_v2395
    store i64 %t2404, i64* %mx_v2379
    br label %if.end.2402
if.end.2402:
    %t2405 = load i64, i64* %mi_v2380
    %t2406 = add i64 %t2405, 1
    store i64 %t2406, i64* %mi_v2380
    br label %loop.cond.2381
loop.end.2383:
    %t2407 = load i64, i64* %mx_v2379
    ret i64 %t2407
    ret i64 0
}

define i64 @freak_array_min_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2408 = load i64, i64* %handle
    %t2409 = call i64 @freak_llvm_array_len(i64 %t2408)
    %alen_v2410 = alloca i64
    store i64 %t2409, i64* %alen_v2410
    %t2411 = load i64, i64* %alen_v2410
    %t2413 = icmp eq i64 %t2411, 0
    %t2412 = zext i1 %t2413 to i64
    %t2417 = icmp ne i64 %t2412, 0
    br i1 %t2417, label %if.then.2414, label %if.end.2416
if.then.2414:
    ret i64 0
    br label %if.end.2416
if.end.2416:
    %t2418 = load i64, i64* %handle
    %t2419 = call i64 @freak_llvm_array_get(i64 %t2418, i64 0)
    %mw_v2420 = alloca i64
    store i64 %t2419, i64* %mw_v2420
    %t2421 = load i64, i64* %mw_v2420
    %t2422 = call i64 @freak_llvm_word_to_int(i64 %t2421)
    %mn_v2423 = alloca i64
    store i64 %t2422, i64* %mn_v2423
    %mi_v2424 = alloca i64
    store i64 1, i64* %mi_v2424
    br label %loop.cond.2425
loop.cond.2425:
    %t2428 = load i64, i64* %mi_v2424
    %t2429 = load i64, i64* %alen_v2410
    %t2431 = icmp sge i64 %t2428, %t2429
    %t2430 = zext i1 %t2431 to i64
    %t2432 = icmp eq i64 %t2430, 0
    br i1 %t2432, label %loop.body.2426, label %loop.end.2427
loop.body.2426:
    %t2433 = load i64, i64* %handle
    %t2434 = load i64, i64* %mi_v2424
    %t2435 = call i64 @freak_llvm_array_get(i64 %t2433, i64 %t2434)
    %cw_v2436 = alloca i64
    store i64 %t2435, i64* %cw_v2436
    %t2437 = load i64, i64* %cw_v2436
    %t2438 = call i64 @freak_llvm_word_to_int(i64 %t2437)
    %cv_v2439 = alloca i64
    store i64 %t2438, i64* %cv_v2439
    %t2440 = load i64, i64* %cv_v2439
    %t2441 = load i64, i64* %mn_v2423
    %t2443 = icmp slt i64 %t2440, %t2441
    %t2442 = zext i1 %t2443 to i64
    %t2447 = icmp ne i64 %t2442, 0
    br i1 %t2447, label %if.then.2444, label %if.end.2446
if.then.2444:
    %t2448 = load i64, i64* %cv_v2439
    store i64 %t2448, i64* %mn_v2423
    br label %if.end.2446
if.end.2446:
    %t2449 = load i64, i64* %mi_v2424
    %t2450 = add i64 %t2449, 1
    store i64 %t2450, i64* %mi_v2424
    br label %loop.cond.2425
loop.end.2427:
    %t2451 = load i64, i64* %mn_v2423
    ret i64 %t2451
    ret i64 0
}

define void @freak_json_init() {
entry:
    %t2452 = load i64, i64* @g_json_inited
    %t2454 = icmp eq i64 %t2452, 0
    %t2453 = zext i1 %t2454 to i64
    %t2458 = icmp ne i64 %t2453, 0
    br i1 %t2458, label %if.then.2455, label %if.end.2457
if.then.2455:
    %t2459 = call i64 @freak_llvm_array_new()
    store i64 %t2459, i64* @g_json_types
    %t2460 = call i64 @freak_llvm_array_new()
    store i64 %t2460, i64* @g_json_vals
    %t2461 = call i64 @freak_llvm_array_new()
    store i64 %t2461, i64* @g_json_children
    %t2462 = call i64 @freak_llvm_array_new()
    store i64 %t2462, i64* @g_json_keys
    store i64 0, i64* @g_json_count
    store i64 1, i64* @g_json_inited
    br label %if.end.2457
if.end.2457:
    ret void
}

define i64 @freak_json_alloc(i64 %arg_jtype, i64 %arg_jval) {
entry:
    %jtype = alloca i64
    store i64 %arg_jtype, i64* %jtype
    %jval = alloca i64
    store i64 %arg_jval, i64* %jval
    %t2463 = load i64, i64* @g_json_count
    %idx_v2464 = alloca i64
    store i64 %t2463, i64* %idx_v2464
    %t2465 = load i64, i64* @g_json_types
    %t2466 = load i64, i64* %jtype
    call void @freak_llvm_array_push(i64 %t2465, i64 %t2466)
    %t2467 = load i64, i64* @g_json_vals
    %t2468 = load i64, i64* %jval
    call void @freak_llvm_array_push(i64 %t2467, i64 %t2468)
    %t2469 = load i64, i64* @g_json_children
    %t2470 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2469, i64 %t2470)
    %t2471 = load i64, i64* @g_json_keys
    %t2472 = call i64 @freak_llvm_word_from_int(i64 0)
    call void @freak_llvm_array_push(i64 %t2471, i64 %t2472)
    %t2473 = load i64, i64* @g_json_count
    %t2474 = add i64 %t2473, 1
    store i64 %t2474, i64* @g_json_count
    %t2475 = load i64, i64* %idx_v2464
    ret i64 %t2475
    ret i64 0
}

define i64 @freak_json_get_type(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2476 = load i64, i64* @g_json_types
    %t2477 = load i64, i64* %handle
    %t2478 = call i64 @freak_llvm_array_get(i64 %t2476, i64 %t2477)
    ret i64 %t2478
    ret i64 0
}

define i64 @freak_json_get_str(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2479 = load i64, i64* @g_json_vals
    %t2480 = load i64, i64* %handle
    %t2481 = call i64 @freak_llvm_array_get(i64 %t2479, i64 %t2480)
    ret i64 %t2481
    ret i64 0
}

define i64 @freak_json_get_int(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2482 = load i64, i64* @g_json_vals
    %t2483 = load i64, i64* %handle
    %t2484 = call i64 @freak_llvm_array_get(i64 %t2482, i64 %t2483)
    %v_v2485 = alloca i64
    store i64 %t2484, i64* %v_v2485
    %t2486 = load i64, i64* %v_v2485
    %t2487 = call i64 @freak_llvm_word_to_int(i64 %t2486)
    ret i64 %t2487
    ret i64 0
}

define i64 @freak_json_get_bool(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2488 = load i64, i64* @g_json_vals
    %t2489 = load i64, i64* %handle
    %t2490 = call i64 @freak_llvm_array_get(i64 %t2488, i64 %t2489)
    %v_v2491 = alloca i64
    store i64 %t2490, i64* %v_v2491
    %t2492 = load i64, i64* %v_v2491
    %t2493 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.120, i64 0, i64 0
    %t2494 = ptrtoint i8* %t2493 to i64
    %t2495 = call i64 @freak_llvm_word_eq(i64 %t2492, i64 %t2494)
    ret i64 %t2495
    ret i64 0
}

define i64 @freak_json_is_null(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2496 = load i64, i64* @g_json_types
    %t2497 = load i64, i64* %handle
    %t2498 = call i64 @freak_llvm_array_get(i64 %t2496, i64 %t2497)
    %t_v2499 = alloca i64
    store i64 %t2498, i64* %t_v2499
    %t2500 = load i64, i64* %t_v2499
    %t2501 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.121, i64 0, i64 0
    %t2502 = ptrtoint i8* %t2501 to i64
    %t2503 = call i64 @freak_llvm_word_eq(i64 %t2500, i64 %t2502)
    ret i64 %t2503
    ret i64 0
}

define i64 @freak_json_arr_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2504 = load i64, i64* @g_json_children
    %t2505 = load i64, i64* %handle
    %t2506 = call i64 @freak_llvm_array_get(i64 %t2504, i64 %t2505)
    %ch_v2507 = alloca i64
    store i64 %t2506, i64* %ch_v2507
    %t2508 = load i64, i64* %ch_v2507
    %t2509 = call i64 @freak_llvm_word_to_int(i64 %t2508)
    %ch_handle_v2510 = alloca i64
    store i64 %t2509, i64* %ch_handle_v2510
    %t2511 = load i64, i64* %ch_handle_v2510
    %t2512 = call i64 @freak_llvm_array_len(i64 %t2511)
    ret i64 %t2512
    ret i64 0
}

define i64 @freak_json_arr_get(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2513 = load i64, i64* @g_json_children
    %t2514 = load i64, i64* %handle
    %t2515 = call i64 @freak_llvm_array_get(i64 %t2513, i64 %t2514)
    %ch_v2516 = alloca i64
    store i64 %t2515, i64* %ch_v2516
    %t2517 = load i64, i64* %ch_v2516
    %t2518 = call i64 @freak_llvm_word_to_int(i64 %t2517)
    %ch_handle_v2519 = alloca i64
    store i64 %t2518, i64* %ch_handle_v2519
    %t2520 = load i64, i64* %ch_handle_v2519
    %t2521 = load i64, i64* %index
    %t2522 = call i64 @freak_llvm_array_get(i64 %t2520, i64 %t2521)
    %val_w_v2523 = alloca i64
    store i64 %t2522, i64* %val_w_v2523
    %t2524 = load i64, i64* %val_w_v2523
    %t2525 = call i64 @freak_llvm_word_to_int(i64 %t2524)
    ret i64 %t2525
    ret i64 0
}

define i64 @freak_json_obj_len(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t2526 = load i64, i64* @g_json_keys
    %t2527 = load i64, i64* %handle
    %t2528 = call i64 @freak_llvm_array_get(i64 %t2526, i64 %t2527)
    %ks_v2529 = alloca i64
    store i64 %t2528, i64* %ks_v2529
    %t2530 = load i64, i64* %ks_v2529
    %t2531 = call i64 @freak_llvm_word_to_int(i64 %t2530)
    %ks_handle_v2532 = alloca i64
    store i64 %t2531, i64* %ks_handle_v2532
    %t2533 = load i64, i64* %ks_handle_v2532
    %t2534 = call i64 @freak_llvm_array_len(i64 %t2533)
    ret i64 %t2534
    ret i64 0
}

define i64 @freak_json_obj_get(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2535 = load i64, i64* @g_json_keys
    %t2536 = load i64, i64* %handle
    %t2537 = call i64 @freak_llvm_array_get(i64 %t2535, i64 %t2536)
    %ks_v2538 = alloca i64
    store i64 %t2537, i64* %ks_v2538
    %t2539 = load i64, i64* %ks_v2538
    %t2540 = call i64 @freak_llvm_word_to_int(i64 %t2539)
    %ks_handle_v2541 = alloca i64
    store i64 %t2540, i64* %ks_handle_v2541
    %t2542 = load i64, i64* @g_json_children
    %t2543 = load i64, i64* %handle
    %t2544 = call i64 @freak_llvm_array_get(i64 %t2542, i64 %t2543)
    %ch_v2545 = alloca i64
    store i64 %t2544, i64* %ch_v2545
    %t2546 = load i64, i64* %ch_v2545
    %t2547 = call i64 @freak_llvm_word_to_int(i64 %t2546)
    %ch_handle_v2548 = alloca i64
    store i64 %t2547, i64* %ch_handle_v2548
    %t2549 = load i64, i64* %ks_handle_v2541
    %t2550 = call i64 @freak_llvm_array_len(i64 %t2549)
    %klen_v2551 = alloca i64
    store i64 %t2550, i64* %klen_v2551
    %ki_v2552 = alloca i64
    store i64 0, i64* %ki_v2552
    %t2558 = load i64, i64* %klen_v2551
    %rep.2557 = alloca i64
    store i64 0, i64* %rep.2557
    br label %loop.cond.2553
loop.cond.2553:
    %t2559 = load i64, i64* %rep.2557
    %t2560 = icmp slt i64 %t2559, %t2558
    br i1 %t2560, label %loop.body.2554, label %loop.end.2555
loop.body.2554:
    %t2561 = load i64, i64* %ks_handle_v2541
    %t2562 = load i64, i64* %ki_v2552
    %t2563 = call i64 @freak_llvm_array_get(i64 %t2561, i64 %t2562)
    %k_v2564 = alloca i64
    store i64 %t2563, i64* %k_v2564
    %t2565 = load i64, i64* %k_v2564
    %t2566 = load i64, i64* %key
    %t2567 = call i64 @freak_llvm_word_eq(i64 %t2565, i64 %t2566)
    %t2571 = icmp ne i64 %t2567, 0
    br i1 %t2571, label %if.then.2568, label %if.end.2570
if.then.2568:
    %t2572 = load i64, i64* %ch_handle_v2548
    %t2573 = load i64, i64* %ki_v2552
    %t2574 = call i64 @freak_llvm_array_get(i64 %t2572, i64 %t2573)
    %v_v2575 = alloca i64
    store i64 %t2574, i64* %v_v2575
    %t2576 = load i64, i64* %v_v2575
    %t2577 = call i64 @freak_llvm_word_to_int(i64 %t2576)
    ret i64 %t2577
    br label %if.end.2570
if.end.2570:
    %t2578 = load i64, i64* %ki_v2552
    %t2579 = add i64 %t2578, 1
    store i64 %t2579, i64* %ki_v2552
    br label %loop.inc.2556
loop.inc.2556:
    %t2580 = load i64, i64* %rep.2557
    %t2581 = add i64 %t2580, 1
    store i64 %t2581, i64* %rep.2557
    br label %loop.cond.2553
loop.end.2555:
    %t2582 = sub i64 0, 1
    ret i64 %t2582
    ret i64 0
}

define i64 @freak_json_obj_has(i64 %arg_handle, i64 %arg_key) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %key = alloca i64
    store i64 %arg_key, i64* %key
    %t2583 = load i64, i64* %handle
    %t2584 = load i64, i64* %key
    %t2585 = call i64 @freak_json_obj_get(i64 %t2583, i64 %t2584)
    %t2587 = icmp sge i64 %t2585, 0
    %t2586 = zext i1 %t2587 to i64
    ret i64 %t2586
    ret i64 0
}

define i64 @freak_json_obj_key_at(i64 %arg_handle, i64 %arg_index) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %index = alloca i64
    store i64 %arg_index, i64* %index
    %t2588 = load i64, i64* @g_json_keys
    %t2589 = load i64, i64* %handle
    %t2590 = call i64 @freak_llvm_array_get(i64 %t2588, i64 %t2589)
    %ks_v2591 = alloca i64
    store i64 %t2590, i64* %ks_v2591
    %t2592 = load i64, i64* %ks_v2591
    %t2593 = call i64 @freak_llvm_word_to_int(i64 %t2592)
    %ks_handle_v2594 = alloca i64
    store i64 %t2593, i64* %ks_handle_v2594
    %t2595 = load i64, i64* %ks_handle_v2594
    %t2596 = load i64, i64* %index
    %t2597 = call i64 @freak_llvm_array_get(i64 %t2595, i64 %t2596)
    ret i64 %t2597
    ret i64 0
}

define i64 @freak_json_cur() {
entry:
    %t2598 = load i64, i64* @g_json_pos
    %t2599 = load i64, i64* @g_json_len
    %t2601 = icmp sge i64 %t2598, %t2599
    %t2600 = zext i1 %t2601 to i64
    %t2605 = icmp ne i64 %t2600, 0
    br i1 %t2605, label %if.then.2602, label %if.end.2604
if.then.2602:
    %t2606 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.122, i64 0, i64 0
    %t2607 = ptrtoint i8* %t2606 to i64
    ret i64 %t2607
    br label %if.end.2604
if.end.2604:
    %t2608 = load i64, i64* @g_json_src
    %t2610 = load i64, i64* @g_json_pos
    %t2609 = call i64 @freak_llvm_word_char_at(i64 %t2608, i64 %t2610)
    ret i64 %t2609
    ret i64 0
}

define i64 @freak_json_advance() {
entry:
    %t2611 = call i64 @freak_json_cur()
    %c_v2612 = alloca i64
    store i64 %t2611, i64* %c_v2612
    %t2613 = load i64, i64* @g_json_pos
    %t2614 = add i64 %t2613, 1
    store i64 %t2614, i64* @g_json_pos
    %t2615 = load i64, i64* %c_v2612
    ret i64 %t2615
    ret i64 0
}

define void @freak_json_skip_ws() {
entry:
    br label %loop.cond.2616
loop.cond.2616:
    %t2619 = load i64, i64* @g_json_pos
    %t2620 = load i64, i64* @g_json_len
    %t2622 = icmp sge i64 %t2619, %t2620
    %t2621 = zext i1 %t2622 to i64
    %t2623 = icmp eq i64 %t2621, 0
    br i1 %t2623, label %loop.body.2617, label %loop.end.2618
loop.body.2617:
    %t2624 = call i64 @freak_json_cur()
    %c_v2625 = alloca i64
    store i64 %t2624, i64* %c_v2625
    %t2626 = load i64, i64* %c_v2625
    %t2627 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.123, i64 0, i64 0
    %t2628 = ptrtoint i8* %t2627 to i64
    %t2629 = call i64 @freak_llvm_word_neq(i64 %t2626, i64 %t2628)
    %t2630 = load i64, i64* %c_v2625
    %t2631 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.124, i64 0, i64 0
    %t2632 = ptrtoint i8* %t2631 to i64
    %t2633 = call i64 @freak_llvm_word_neq(i64 %t2630, i64 %t2632)
    %t2635 = icmp ne i64 %t2629, 0
    %t2636 = icmp ne i64 %t2633, 0
    %t2637 = and i1 %t2635, %t2636
    %t2634 = zext i1 %t2637 to i64
    %t2638 = load i64, i64* %c_v2625
    %t2639 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.125, i64 0, i64 0
    %t2640 = ptrtoint i8* %t2639 to i64
    %t2641 = call i64 @freak_llvm_word_neq(i64 %t2638, i64 %t2640)
    %t2643 = icmp ne i64 %t2634, 0
    %t2644 = icmp ne i64 %t2641, 0
    %t2645 = and i1 %t2643, %t2644
    %t2642 = zext i1 %t2645 to i64
    %t2646 = load i64, i64* %c_v2625
    %t2647 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.126, i64 0, i64 0
    %t2648 = ptrtoint i8* %t2647 to i64
    %t2649 = call i64 @freak_llvm_word_neq(i64 %t2646, i64 %t2648)
    %t2651 = icmp ne i64 %t2642, 0
    %t2652 = icmp ne i64 %t2649, 0
    %t2653 = and i1 %t2651, %t2652
    %t2650 = zext i1 %t2653 to i64
    %t2657 = icmp ne i64 %t2650, 0
    br i1 %t2657, label %if.then.2654, label %if.end.2656
if.then.2654:
    ret void
    br label %if.end.2656
if.end.2656:
    %t2658 = load i64, i64* @g_json_pos
    %t2659 = add i64 %t2658, 1
    store i64 %t2659, i64* @g_json_pos
    br label %loop.cond.2616
loop.end.2618:
    ret void
}

define void @freak_json_expect(i64 %arg_ch) {
entry:
    %ch = alloca i64
    store i64 %arg_ch, i64* %ch
    %t2660 = call i64 @freak_json_advance()
    %c_v2661 = alloca i64
    store i64 %t2660, i64* %c_v2661
    %t2662 = load i64, i64* %c_v2661
    %t2663 = load i64, i64* %ch
    %t2664 = call i64 @freak_llvm_word_neq(i64 %t2662, i64 %t2663)
    %t2668 = icmp ne i64 %t2664, 0
    br i1 %t2668, label %if.then.2665, label %if.end.2667
if.then.2665:
    %t2669 = getelementptr inbounds [29 x i8], [29 x i8]* @.str.127, i64 0, i64 0
    %t2670 = ptrtoint i8* %t2669 to i64
    %t2671 = load i64, i64* %ch
    %t2672 = call i64 @freak_llvm_word_concat(i64 %t2670, i64 %t2671)
    %t2673 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.128, i64 0, i64 0
    %t2674 = ptrtoint i8* %t2673 to i64
    %t2675 = call i64 @freak_llvm_word_concat(i64 %t2672, i64 %t2674)
    %t2676 = load i64, i64* %c_v2661
    %t2677 = call i64 @freak_llvm_word_concat(i64 %t2675, i64 %t2676)
    %t2678 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.129, i64 0, i64 0
    %t2679 = ptrtoint i8* %t2678 to i64
    %t2680 = call i64 @freak_llvm_word_concat(i64 %t2677, i64 %t2679)
    call void @freak_llvm_say(i64 %t2680)
    br label %if.end.2667
if.end.2667:
    ret void
}

define i64 @freak_json_parse_string() {
entry:
    %t2681 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.130, i64 0, i64 0
    %t2682 = ptrtoint i8* %t2681 to i64
    call void @freak_json_expect(i64 %t2682)
    %t2683 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.131, i64 0, i64 0
    %t2684 = ptrtoint i8* %t2683 to i64
    %ps_out_v2685 = alloca i64
    store i64 %t2684, i64* %ps_out_v2685
    br label %loop.cond.2686
loop.cond.2686:
    %t2689 = load i64, i64* @g_json_pos
    %t2690 = load i64, i64* @g_json_len
    %t2692 = icmp sge i64 %t2689, %t2690
    %t2691 = zext i1 %t2692 to i64
    %t2693 = icmp eq i64 %t2691, 0
    br i1 %t2693, label %loop.body.2687, label %loop.end.2688
loop.body.2687:
    %t2694 = call i64 @freak_json_advance()
    %c_v2695 = alloca i64
    store i64 %t2694, i64* %c_v2695
    %t2696 = load i64, i64* %c_v2695
    %t2697 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.132, i64 0, i64 0
    %t2698 = ptrtoint i8* %t2697 to i64
    %t2699 = call i64 @freak_llvm_word_eq(i64 %t2696, i64 %t2698)
    %t2703 = icmp ne i64 %t2699, 0
    br i1 %t2703, label %if.then.2700, label %if.end.2702
if.then.2700:
    %t2704 = load i64, i64* %ps_out_v2685
    ret i64 %t2704
    br label %if.end.2702
if.end.2702:
    %t2705 = load i64, i64* %c_v2695
    %t2706 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.133, i64 0, i64 0
    %t2707 = ptrtoint i8* %t2706 to i64
    %t2708 = call i64 @freak_llvm_word_eq(i64 %t2705, i64 %t2707)
    %t2712 = icmp ne i64 %t2708, 0
    br i1 %t2712, label %if.then.2709, label %if.else.2710
if.then.2709:
    %t2713 = call i64 @freak_json_advance()
    %esc_v2714 = alloca i64
    store i64 %t2713, i64* %esc_v2714
    %t2715 = load i64, i64* %esc_v2714
    %t2716 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.134, i64 0, i64 0
    %t2717 = ptrtoint i8* %t2716 to i64
    %t2718 = call i64 @freak_llvm_word_eq(i64 %t2715, i64 %t2717)
    %t2722 = icmp ne i64 %t2718, 0
    br i1 %t2722, label %if.then.2719, label %if.else.2720
if.then.2719:
    %t2723 = load i64, i64* %ps_out_v2685
    %t2724 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.135, i64 0, i64 0
    %t2725 = ptrtoint i8* %t2724 to i64
    %t2726 = call i64 @freak_llvm_word_concat(i64 %t2723, i64 %t2725)
    store i64 %t2726, i64* %ps_out_v2685
    br label %if.end.2721
if.else.2720:
    %t2727 = load i64, i64* %esc_v2714
    %t2728 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.136, i64 0, i64 0
    %t2729 = ptrtoint i8* %t2728 to i64
    %t2730 = call i64 @freak_llvm_word_eq(i64 %t2727, i64 %t2729)
    %t2734 = icmp ne i64 %t2730, 0
    br i1 %t2734, label %if.then.2731, label %if.else.2732
if.then.2731:
    %t2735 = load i64, i64* %ps_out_v2685
    %t2736 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.137, i64 0, i64 0
    %t2737 = ptrtoint i8* %t2736 to i64
    %t2738 = call i64 @freak_llvm_word_concat(i64 %t2735, i64 %t2737)
    store i64 %t2738, i64* %ps_out_v2685
    br label %if.end.2733
if.else.2732:
    %t2739 = load i64, i64* %esc_v2714
    %t2740 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.138, i64 0, i64 0
    %t2741 = ptrtoint i8* %t2740 to i64
    %t2742 = call i64 @freak_llvm_word_eq(i64 %t2739, i64 %t2741)
    %t2746 = icmp ne i64 %t2742, 0
    br i1 %t2746, label %if.then.2743, label %if.else.2744
if.then.2743:
    %t2747 = load i64, i64* %ps_out_v2685
    %t2748 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.139, i64 0, i64 0
    %t2749 = ptrtoint i8* %t2748 to i64
    %t2750 = call i64 @freak_llvm_word_concat(i64 %t2747, i64 %t2749)
    store i64 %t2750, i64* %ps_out_v2685
    br label %if.end.2745
if.else.2744:
    %t2751 = load i64, i64* %esc_v2714
    %t2752 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.140, i64 0, i64 0
    %t2753 = ptrtoint i8* %t2752 to i64
    %t2754 = call i64 @freak_llvm_word_eq(i64 %t2751, i64 %t2753)
    %t2758 = icmp ne i64 %t2754, 0
    br i1 %t2758, label %if.then.2755, label %if.else.2756
if.then.2755:
    %t2759 = load i64, i64* %ps_out_v2685
    %t2760 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.141, i64 0, i64 0
    %t2761 = ptrtoint i8* %t2760 to i64
    %t2762 = call i64 @freak_llvm_word_concat(i64 %t2759, i64 %t2761)
    store i64 %t2762, i64* %ps_out_v2685
    br label %if.end.2757
if.else.2756:
    %t2763 = load i64, i64* %esc_v2714
    %t2764 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.142, i64 0, i64 0
    %t2765 = ptrtoint i8* %t2764 to i64
    %t2766 = call i64 @freak_llvm_word_eq(i64 %t2763, i64 %t2765)
    %t2770 = icmp ne i64 %t2766, 0
    br i1 %t2770, label %if.then.2767, label %if.else.2768
if.then.2767:
    %t2771 = load i64, i64* %ps_out_v2685
    %t2772 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.143, i64 0, i64 0
    %t2773 = ptrtoint i8* %t2772 to i64
    %t2774 = call i64 @freak_llvm_word_concat(i64 %t2771, i64 %t2773)
    store i64 %t2774, i64* %ps_out_v2685
    br label %if.end.2769
if.else.2768:
    %t2775 = load i64, i64* %esc_v2714
    %t2776 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.144, i64 0, i64 0
    %t2777 = ptrtoint i8* %t2776 to i64
    %t2778 = call i64 @freak_llvm_word_eq(i64 %t2775, i64 %t2777)
    %t2782 = icmp ne i64 %t2778, 0
    br i1 %t2782, label %if.then.2779, label %if.else.2780
if.then.2779:
    %t2783 = load i64, i64* %ps_out_v2685
    %t2784 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.145, i64 0, i64 0
    %t2785 = ptrtoint i8* %t2784 to i64
    %t2786 = call i64 @freak_llvm_word_concat(i64 %t2783, i64 %t2785)
    store i64 %t2786, i64* %ps_out_v2685
    br label %if.end.2781
if.else.2780:
    %t2787 = load i64, i64* %ps_out_v2685
    %t2788 = load i64, i64* %esc_v2714
    %t2789 = call i64 @freak_llvm_word_concat(i64 %t2787, i64 %t2788)
    store i64 %t2789, i64* %ps_out_v2685
    br label %if.end.2781
if.end.2781:
    br label %if.end.2769
if.end.2769:
    br label %if.end.2757
if.end.2757:
    br label %if.end.2745
if.end.2745:
    br label %if.end.2733
if.end.2733:
    br label %if.end.2721
if.end.2721:
    br label %if.end.2711
if.else.2710:
    %t2790 = load i64, i64* %ps_out_v2685
    %t2791 = load i64, i64* %c_v2695
    %t2792 = call i64 @freak_llvm_word_concat(i64 %t2790, i64 %t2791)
    store i64 %t2792, i64* %ps_out_v2685
    br label %if.end.2711
if.end.2711:
    br label %loop.cond.2686
loop.end.2688:
    %t2793 = load i64, i64* %ps_out_v2685
    ret i64 %t2793
    ret i64 0
}

define i64 @freak_json_parse_number() {
entry:
    %t2794 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.146, i64 0, i64 0
    %t2795 = ptrtoint i8* %t2794 to i64
    %pn_out_v2796 = alloca i64
    store i64 %t2795, i64* %pn_out_v2796
    %t2797 = call i64 @freak_json_cur()
    %c_v2798 = alloca i64
    store i64 %t2797, i64* %c_v2798
    %t2799 = load i64, i64* %c_v2798
    %t2800 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.147, i64 0, i64 0
    %t2801 = ptrtoint i8* %t2800 to i64
    %t2802 = call i64 @freak_llvm_word_eq(i64 %t2799, i64 %t2801)
    %t2806 = icmp ne i64 %t2802, 0
    br i1 %t2806, label %if.then.2803, label %if.end.2805
if.then.2803:
    %t2807 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.148, i64 0, i64 0
    %t2808 = ptrtoint i8* %t2807 to i64
    store i64 %t2808, i64* %pn_out_v2796
    %t2809 = load i64, i64* @g_json_pos
    %t2810 = add i64 %t2809, 1
    store i64 %t2810, i64* @g_json_pos
    br label %if.end.2805
if.end.2805:
    br label %loop.cond.2811
loop.cond.2811:
    %t2814 = load i64, i64* @g_json_pos
    %t2815 = load i64, i64* @g_json_len
    %t2817 = icmp sge i64 %t2814, %t2815
    %t2816 = zext i1 %t2817 to i64
    %t2818 = icmp eq i64 %t2816, 0
    br i1 %t2818, label %loop.body.2812, label %loop.end.2813
loop.body.2812:
    %t2819 = call i64 @freak_json_cur()
    store i64 %t2819, i64* %c_v2798
    %t2820 = load i64, i64* %c_v2798
    %t2821 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.149, i64 0, i64 0
    %t2822 = ptrtoint i8* %t2821 to i64
    %t2823 = call i64 @freak_llvm_word_eq(i64 %t2820, i64 %t2822)
    %t2824 = load i64, i64* %c_v2798
    %t2825 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.150, i64 0, i64 0
    %t2826 = ptrtoint i8* %t2825 to i64
    %t2827 = call i64 @freak_llvm_word_eq(i64 %t2824, i64 %t2826)
    %t2829 = icmp ne i64 %t2823, 0
    %t2830 = icmp ne i64 %t2827, 0
    %t2831 = or i1 %t2829, %t2830
    %t2828 = zext i1 %t2831 to i64
    %t2832 = load i64, i64* %c_v2798
    %t2833 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.151, i64 0, i64 0
    %t2834 = ptrtoint i8* %t2833 to i64
    %t2835 = call i64 @freak_llvm_word_eq(i64 %t2832, i64 %t2834)
    %t2837 = icmp ne i64 %t2828, 0
    %t2838 = icmp ne i64 %t2835, 0
    %t2839 = or i1 %t2837, %t2838
    %t2836 = zext i1 %t2839 to i64
    %t2840 = load i64, i64* %c_v2798
    %t2841 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.152, i64 0, i64 0
    %t2842 = ptrtoint i8* %t2841 to i64
    %t2843 = call i64 @freak_llvm_word_eq(i64 %t2840, i64 %t2842)
    %t2845 = icmp ne i64 %t2836, 0
    %t2846 = icmp ne i64 %t2843, 0
    %t2847 = or i1 %t2845, %t2846
    %t2844 = zext i1 %t2847 to i64
    %t2848 = load i64, i64* %c_v2798
    %t2849 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.153, i64 0, i64 0
    %t2850 = ptrtoint i8* %t2849 to i64
    %t2851 = call i64 @freak_llvm_word_eq(i64 %t2848, i64 %t2850)
    %t2853 = icmp ne i64 %t2844, 0
    %t2854 = icmp ne i64 %t2851, 0
    %t2855 = or i1 %t2853, %t2854
    %t2852 = zext i1 %t2855 to i64
    %t2856 = load i64, i64* %c_v2798
    %t2857 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.154, i64 0, i64 0
    %t2858 = ptrtoint i8* %t2857 to i64
    %t2859 = call i64 @freak_llvm_word_eq(i64 %t2856, i64 %t2858)
    %t2861 = icmp ne i64 %t2852, 0
    %t2862 = icmp ne i64 %t2859, 0
    %t2863 = or i1 %t2861, %t2862
    %t2860 = zext i1 %t2863 to i64
    %t2864 = load i64, i64* %c_v2798
    %t2865 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.155, i64 0, i64 0
    %t2866 = ptrtoint i8* %t2865 to i64
    %t2867 = call i64 @freak_llvm_word_eq(i64 %t2864, i64 %t2866)
    %t2869 = icmp ne i64 %t2860, 0
    %t2870 = icmp ne i64 %t2867, 0
    %t2871 = or i1 %t2869, %t2870
    %t2868 = zext i1 %t2871 to i64
    %t2872 = load i64, i64* %c_v2798
    %t2873 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.156, i64 0, i64 0
    %t2874 = ptrtoint i8* %t2873 to i64
    %t2875 = call i64 @freak_llvm_word_eq(i64 %t2872, i64 %t2874)
    %t2877 = icmp ne i64 %t2868, 0
    %t2878 = icmp ne i64 %t2875, 0
    %t2879 = or i1 %t2877, %t2878
    %t2876 = zext i1 %t2879 to i64
    %t2880 = load i64, i64* %c_v2798
    %t2881 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.157, i64 0, i64 0
    %t2882 = ptrtoint i8* %t2881 to i64
    %t2883 = call i64 @freak_llvm_word_eq(i64 %t2880, i64 %t2882)
    %t2885 = icmp ne i64 %t2876, 0
    %t2886 = icmp ne i64 %t2883, 0
    %t2887 = or i1 %t2885, %t2886
    %t2884 = zext i1 %t2887 to i64
    %t2888 = load i64, i64* %c_v2798
    %t2889 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.158, i64 0, i64 0
    %t2890 = ptrtoint i8* %t2889 to i64
    %t2891 = call i64 @freak_llvm_word_eq(i64 %t2888, i64 %t2890)
    %t2893 = icmp ne i64 %t2884, 0
    %t2894 = icmp ne i64 %t2891, 0
    %t2895 = or i1 %t2893, %t2894
    %t2892 = zext i1 %t2895 to i64
    %t2896 = load i64, i64* %c_v2798
    %t2897 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.159, i64 0, i64 0
    %t2898 = ptrtoint i8* %t2897 to i64
    %t2899 = call i64 @freak_llvm_word_eq(i64 %t2896, i64 %t2898)
    %t2901 = icmp ne i64 %t2892, 0
    %t2902 = icmp ne i64 %t2899, 0
    %t2903 = or i1 %t2901, %t2902
    %t2900 = zext i1 %t2903 to i64
    %t2907 = icmp ne i64 %t2900, 0
    br i1 %t2907, label %if.then.2904, label %if.else.2905
if.then.2904:
    %t2908 = load i64, i64* %pn_out_v2796
    %t2909 = load i64, i64* %c_v2798
    %t2910 = call i64 @freak_llvm_word_concat(i64 %t2908, i64 %t2909)
    store i64 %t2910, i64* %pn_out_v2796
    %t2911 = load i64, i64* @g_json_pos
    %t2912 = add i64 %t2911, 1
    store i64 %t2912, i64* @g_json_pos
    br label %if.end.2906
if.else.2905:
    %t2913 = load i64, i64* %pn_out_v2796
    ret i64 %t2913
    br label %if.end.2906
if.end.2906:
    br label %loop.cond.2811
loop.end.2813:
    %t2914 = load i64, i64* %pn_out_v2796
    ret i64 %t2914
    ret i64 0
}

define i64 @freak_json_try_keyword(i64 %arg_kw) {
entry:
    %kw = alloca i64
    store i64 %arg_kw, i64* %kw
    %t2915 = load i64, i64* %kw
    %t2916 = call i64 @freak_llvm_word_length(i64 %t2915)
    %kwlen_v2917 = alloca i64
    store i64 %t2916, i64* %kwlen_v2917
    %t2918 = load i64, i64* @g_json_pos
    %t2919 = load i64, i64* %kwlen_v2917
    %t2920 = add i64 %t2918, %t2919
    %t2921 = load i64, i64* @g_json_len
    %t2923 = icmp sgt i64 %t2920, %t2921
    %t2922 = zext i1 %t2923 to i64
    %t2927 = icmp ne i64 %t2922, 0
    br i1 %t2927, label %if.then.2924, label %if.end.2926
if.then.2924:
    ret i64 0
    br label %if.end.2926
if.end.2926:
    %ki_v2928 = alloca i64
    store i64 0, i64* %ki_v2928
    %t2934 = load i64, i64* %kwlen_v2917
    %rep.2933 = alloca i64
    store i64 0, i64* %rep.2933
    br label %loop.cond.2929
loop.cond.2929:
    %t2935 = load i64, i64* %rep.2933
    %t2936 = icmp slt i64 %t2935, %t2934
    br i1 %t2936, label %loop.body.2930, label %loop.end.2931
loop.body.2930:
    %t2937 = load i64, i64* @g_json_src
    %t2939 = load i64, i64* @g_json_pos
    %t2940 = load i64, i64* %ki_v2928
    %t2941 = add i64 %t2939, %t2940
    %t2938 = call i64 @freak_llvm_word_char_at(i64 %t2937, i64 %t2941)
    %t2942 = load i64, i64* %kw
    %t2944 = load i64, i64* %ki_v2928
    %t2943 = call i64 @freak_llvm_word_char_at(i64 %t2942, i64 %t2944)
    %t2945 = call i64 @freak_llvm_word_neq(i64 %t2938, i64 %t2943)
    %t2949 = icmp ne i64 %t2945, 0
    br i1 %t2949, label %if.then.2946, label %if.end.2948
if.then.2946:
    ret i64 0
    br label %if.end.2948
if.end.2948:
    %t2950 = load i64, i64* %ki_v2928
    %t2951 = add i64 %t2950, 1
    store i64 %t2951, i64* %ki_v2928
    br label %loop.inc.2932
loop.inc.2932:
    %t2952 = load i64, i64* %rep.2933
    %t2953 = add i64 %t2952, 1
    store i64 %t2953, i64* %rep.2933
    br label %loop.cond.2929
loop.end.2931:
    %t2954 = load i64, i64* %kwlen_v2917
    %t2955 = load i64, i64* @g_json_pos
    %t2956 = add i64 %t2955, %t2954
    store i64 %t2956, i64* @g_json_pos
    ret i64 1
    ret i64 0
}

define i64 @freak_json_parse_value() {
entry:
    call void @freak_json_skip_ws()
    %t2957 = call i64 @freak_json_cur()
    %c_v2958 = alloca i64
    store i64 %t2957, i64* %c_v2958
    %t2959 = load i64, i64* %c_v2958
    %t2960 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.160, i64 0, i64 0
    %t2961 = ptrtoint i8* %t2960 to i64
    %t2962 = call i64 @freak_llvm_word_eq(i64 %t2959, i64 %t2961)
    %t2966 = icmp ne i64 %t2962, 0
    br i1 %t2966, label %if.then.2963, label %if.end.2965
if.then.2963:
    %t2967 = call i64 @freak_json_parse_string()
    %sv_v2968 = alloca i64
    store i64 %t2967, i64* %sv_v2968
    %t2969 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.161, i64 0, i64 0
    %t2970 = ptrtoint i8* %t2969 to i64
    %t2971 = load i64, i64* %sv_v2968
    %t2972 = call i64 @freak_json_alloc(i64 %t2970, i64 %t2971)
    ret i64 %t2972
    br label %if.end.2965
if.end.2965:
    %t2973 = load i64, i64* %c_v2958
    %t2974 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.162, i64 0, i64 0
    %t2975 = ptrtoint i8* %t2974 to i64
    %t2976 = call i64 @freak_llvm_word_eq(i64 %t2973, i64 %t2975)
    %t2977 = load i64, i64* %c_v2958
    %t2978 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.163, i64 0, i64 0
    %t2979 = ptrtoint i8* %t2978 to i64
    %t2980 = call i64 @freak_llvm_word_eq(i64 %t2977, i64 %t2979)
    %t2982 = icmp ne i64 %t2976, 0
    %t2983 = icmp ne i64 %t2980, 0
    %t2984 = or i1 %t2982, %t2983
    %t2981 = zext i1 %t2984 to i64
    %t2985 = load i64, i64* %c_v2958
    %t2986 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.164, i64 0, i64 0
    %t2987 = ptrtoint i8* %t2986 to i64
    %t2988 = call i64 @freak_llvm_word_eq(i64 %t2985, i64 %t2987)
    %t2990 = icmp ne i64 %t2981, 0
    %t2991 = icmp ne i64 %t2988, 0
    %t2992 = or i1 %t2990, %t2991
    %t2989 = zext i1 %t2992 to i64
    %t2993 = load i64, i64* %c_v2958
    %t2994 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.165, i64 0, i64 0
    %t2995 = ptrtoint i8* %t2994 to i64
    %t2996 = call i64 @freak_llvm_word_eq(i64 %t2993, i64 %t2995)
    %t2998 = icmp ne i64 %t2989, 0
    %t2999 = icmp ne i64 %t2996, 0
    %t3000 = or i1 %t2998, %t2999
    %t2997 = zext i1 %t3000 to i64
    %t3001 = load i64, i64* %c_v2958
    %t3002 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.166, i64 0, i64 0
    %t3003 = ptrtoint i8* %t3002 to i64
    %t3004 = call i64 @freak_llvm_word_eq(i64 %t3001, i64 %t3003)
    %t3006 = icmp ne i64 %t2997, 0
    %t3007 = icmp ne i64 %t3004, 0
    %t3008 = or i1 %t3006, %t3007
    %t3005 = zext i1 %t3008 to i64
    %t3009 = load i64, i64* %c_v2958
    %t3010 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.167, i64 0, i64 0
    %t3011 = ptrtoint i8* %t3010 to i64
    %t3012 = call i64 @freak_llvm_word_eq(i64 %t3009, i64 %t3011)
    %t3014 = icmp ne i64 %t3005, 0
    %t3015 = icmp ne i64 %t3012, 0
    %t3016 = or i1 %t3014, %t3015
    %t3013 = zext i1 %t3016 to i64
    %t3017 = load i64, i64* %c_v2958
    %t3018 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.168, i64 0, i64 0
    %t3019 = ptrtoint i8* %t3018 to i64
    %t3020 = call i64 @freak_llvm_word_eq(i64 %t3017, i64 %t3019)
    %t3022 = icmp ne i64 %t3013, 0
    %t3023 = icmp ne i64 %t3020, 0
    %t3024 = or i1 %t3022, %t3023
    %t3021 = zext i1 %t3024 to i64
    %t3025 = load i64, i64* %c_v2958
    %t3026 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.169, i64 0, i64 0
    %t3027 = ptrtoint i8* %t3026 to i64
    %t3028 = call i64 @freak_llvm_word_eq(i64 %t3025, i64 %t3027)
    %t3030 = icmp ne i64 %t3021, 0
    %t3031 = icmp ne i64 %t3028, 0
    %t3032 = or i1 %t3030, %t3031
    %t3029 = zext i1 %t3032 to i64
    %t3033 = load i64, i64* %c_v2958
    %t3034 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.170, i64 0, i64 0
    %t3035 = ptrtoint i8* %t3034 to i64
    %t3036 = call i64 @freak_llvm_word_eq(i64 %t3033, i64 %t3035)
    %t3038 = icmp ne i64 %t3029, 0
    %t3039 = icmp ne i64 %t3036, 0
    %t3040 = or i1 %t3038, %t3039
    %t3037 = zext i1 %t3040 to i64
    %t3041 = load i64, i64* %c_v2958
    %t3042 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.171, i64 0, i64 0
    %t3043 = ptrtoint i8* %t3042 to i64
    %t3044 = call i64 @freak_llvm_word_eq(i64 %t3041, i64 %t3043)
    %t3046 = icmp ne i64 %t3037, 0
    %t3047 = icmp ne i64 %t3044, 0
    %t3048 = or i1 %t3046, %t3047
    %t3045 = zext i1 %t3048 to i64
    %t3049 = load i64, i64* %c_v2958
    %t3050 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.172, i64 0, i64 0
    %t3051 = ptrtoint i8* %t3050 to i64
    %t3052 = call i64 @freak_llvm_word_eq(i64 %t3049, i64 %t3051)
    %t3054 = icmp ne i64 %t3045, 0
    %t3055 = icmp ne i64 %t3052, 0
    %t3056 = or i1 %t3054, %t3055
    %t3053 = zext i1 %t3056 to i64
    %t3060 = icmp ne i64 %t3053, 0
    br i1 %t3060, label %if.then.3057, label %if.end.3059
if.then.3057:
    %t3061 = call i64 @freak_json_parse_number()
    %nv_v3062 = alloca i64
    store i64 %t3061, i64* %nv_v3062
    %t3063 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.173, i64 0, i64 0
    %t3064 = ptrtoint i8* %t3063 to i64
    %t3065 = load i64, i64* %nv_v3062
    %t3066 = call i64 @freak_json_alloc(i64 %t3064, i64 %t3065)
    ret i64 %t3066
    br label %if.end.3059
if.end.3059:
    %t3067 = load i64, i64* %c_v2958
    %t3068 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.174, i64 0, i64 0
    %t3069 = ptrtoint i8* %t3068 to i64
    %t3070 = call i64 @freak_llvm_word_eq(i64 %t3067, i64 %t3069)
    %t3074 = icmp ne i64 %t3070, 0
    br i1 %t3074, label %if.then.3071, label %if.end.3073
if.then.3071:
    %t3075 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.175, i64 0, i64 0
    %t3076 = ptrtoint i8* %t3075 to i64
    %t3077 = call i64 @freak_json_try_keyword(i64 %t3076)
    %t3081 = icmp ne i64 %t3077, 0
    br i1 %t3081, label %if.then.3078, label %if.end.3080
if.then.3078:
    %t3082 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.176, i64 0, i64 0
    %t3083 = ptrtoint i8* %t3082 to i64
    %t3084 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.177, i64 0, i64 0
    %t3085 = ptrtoint i8* %t3084 to i64
    %t3086 = call i64 @freak_json_alloc(i64 %t3083, i64 %t3085)
    ret i64 %t3086
    br label %if.end.3080
if.end.3080:
    br label %if.end.3073
if.end.3073:
    %t3087 = load i64, i64* %c_v2958
    %t3088 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.178, i64 0, i64 0
    %t3089 = ptrtoint i8* %t3088 to i64
    %t3090 = call i64 @freak_llvm_word_eq(i64 %t3087, i64 %t3089)
    %t3094 = icmp ne i64 %t3090, 0
    br i1 %t3094, label %if.then.3091, label %if.end.3093
if.then.3091:
    %t3095 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.179, i64 0, i64 0
    %t3096 = ptrtoint i8* %t3095 to i64
    %t3097 = call i64 @freak_json_try_keyword(i64 %t3096)
    %t3101 = icmp ne i64 %t3097, 0
    br i1 %t3101, label %if.then.3098, label %if.end.3100
if.then.3098:
    %t3102 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.180, i64 0, i64 0
    %t3103 = ptrtoint i8* %t3102 to i64
    %t3104 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.181, i64 0, i64 0
    %t3105 = ptrtoint i8* %t3104 to i64
    %t3106 = call i64 @freak_json_alloc(i64 %t3103, i64 %t3105)
    ret i64 %t3106
    br label %if.end.3100
if.end.3100:
    br label %if.end.3093
if.end.3093:
    %t3107 = load i64, i64* %c_v2958
    %t3108 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.182, i64 0, i64 0
    %t3109 = ptrtoint i8* %t3108 to i64
    %t3110 = call i64 @freak_llvm_word_eq(i64 %t3107, i64 %t3109)
    %t3114 = icmp ne i64 %t3110, 0
    br i1 %t3114, label %if.then.3111, label %if.end.3113
if.then.3111:
    %t3115 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.183, i64 0, i64 0
    %t3116 = ptrtoint i8* %t3115 to i64
    %t3117 = call i64 @freak_json_try_keyword(i64 %t3116)
    %t3121 = icmp ne i64 %t3117, 0
    br i1 %t3121, label %if.then.3118, label %if.end.3120
if.then.3118:
    %t3122 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.184, i64 0, i64 0
    %t3123 = ptrtoint i8* %t3122 to i64
    %t3124 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.185, i64 0, i64 0
    %t3125 = ptrtoint i8* %t3124 to i64
    %t3126 = call i64 @freak_json_alloc(i64 %t3123, i64 %t3125)
    ret i64 %t3126
    br label %if.end.3120
if.end.3120:
    br label %if.end.3113
if.end.3113:
    %t3127 = load i64, i64* %c_v2958
    %t3128 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.186, i64 0, i64 0
    %t3129 = ptrtoint i8* %t3128 to i64
    %t3130 = call i64 @freak_llvm_word_eq(i64 %t3127, i64 %t3129)
    %t3134 = icmp ne i64 %t3130, 0
    br i1 %t3134, label %if.then.3131, label %if.end.3133
if.then.3131:
    %t3135 = load i64, i64* @g_json_pos
    %t3136 = add i64 %t3135, 1
    store i64 %t3136, i64* @g_json_pos
    %t3137 = call i64 @freak_llvm_array_new()
    %arr_children_v3138 = alloca i64
    store i64 %t3137, i64* %arr_children_v3138
    %t3139 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.187, i64 0, i64 0
    %t3140 = ptrtoint i8* %t3139 to i64
    %t3141 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.188, i64 0, i64 0
    %t3142 = ptrtoint i8* %t3141 to i64
    %t3143 = call i64 @freak_json_alloc(i64 %t3140, i64 %t3142)
    %arr_handle_v3144 = alloca i64
    store i64 %t3143, i64* %arr_handle_v3144
    %t3145 = load i64, i64* @g_json_children
    %t3146 = load i64, i64* %arr_handle_v3144
    %t3147 = load i64, i64* %arr_children_v3138
    %t3148 = call i64 @freak_llvm_word_from_int(i64 %t3147)
    call void @freak_llvm_array_set(i64 %t3145, i64 %t3146, i64 %t3148)
    call void @freak_json_skip_ws()
    %t3149 = call i64 @freak_json_cur()
    %t3150 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.189, i64 0, i64 0
    %t3151 = ptrtoint i8* %t3150 to i64
    %t3152 = call i64 @freak_llvm_word_neq(i64 %t3149, i64 %t3151)
    %t3156 = icmp ne i64 %t3152, 0
    br i1 %t3156, label %if.then.3153, label %if.end.3155
if.then.3153:
    %t3157 = call i64 @freak_json_parse_value()
    %first_val_v3158 = alloca i64
    store i64 %t3157, i64* %first_val_v3158
    %t3159 = load i64, i64* %arr_children_v3138
    %t3160 = load i64, i64* %first_val_v3158
    %t3161 = call i64 @freak_llvm_word_from_int(i64 %t3160)
    call void @freak_llvm_array_push(i64 %t3159, i64 %t3161)
    call void @freak_json_skip_ws()
    br label %loop.cond.3162
loop.cond.3162:
    %t3165 = call i64 @freak_json_cur()
    %t3166 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.190, i64 0, i64 0
    %t3167 = ptrtoint i8* %t3166 to i64
    %t3168 = call i64 @freak_llvm_word_neq(i64 %t3165, i64 %t3167)
    %t3169 = icmp eq i64 %t3168, 0
    br i1 %t3169, label %loop.body.3163, label %loop.end.3164
loop.body.3163:
    %t3170 = load i64, i64* @g_json_pos
    %t3171 = add i64 %t3170, 1
    store i64 %t3171, i64* @g_json_pos
    %t3172 = call i64 @freak_json_parse_value()
    %next_val_v3173 = alloca i64
    store i64 %t3172, i64* %next_val_v3173
    %t3174 = load i64, i64* %arr_children_v3138
    %t3175 = load i64, i64* %next_val_v3173
    %t3176 = call i64 @freak_llvm_word_from_int(i64 %t3175)
    call void @freak_llvm_array_push(i64 %t3174, i64 %t3176)
    call void @freak_json_skip_ws()
    br label %loop.cond.3162
loop.end.3164:
    br label %if.end.3155
if.end.3155:
    %t3177 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.191, i64 0, i64 0
    %t3178 = ptrtoint i8* %t3177 to i64
    call void @freak_json_expect(i64 %t3178)
    %t3179 = load i64, i64* %arr_handle_v3144
    ret i64 %t3179
    br label %if.end.3133
if.end.3133:
    %t3180 = load i64, i64* %c_v2958
    %t3181 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.192, i64 0, i64 0
    %t3182 = ptrtoint i8* %t3181 to i64
    %t3183 = call i64 @freak_llvm_word_eq(i64 %t3180, i64 %t3182)
    %t3187 = icmp ne i64 %t3183, 0
    br i1 %t3187, label %if.then.3184, label %if.end.3186
if.then.3184:
    %t3188 = load i64, i64* @g_json_pos
    %t3189 = add i64 %t3188, 1
    store i64 %t3189, i64* @g_json_pos
    %t3190 = call i64 @freak_llvm_array_new()
    %obj_children_v3191 = alloca i64
    store i64 %t3190, i64* %obj_children_v3191
    %t3192 = call i64 @freak_llvm_array_new()
    %obj_keys_v3193 = alloca i64
    store i64 %t3192, i64* %obj_keys_v3193
    %t3194 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.193, i64 0, i64 0
    %t3195 = ptrtoint i8* %t3194 to i64
    %t3196 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.194, i64 0, i64 0
    %t3197 = ptrtoint i8* %t3196 to i64
    %t3198 = call i64 @freak_json_alloc(i64 %t3195, i64 %t3197)
    %obj_handle_v3199 = alloca i64
    store i64 %t3198, i64* %obj_handle_v3199
    %t3200 = load i64, i64* @g_json_children
    %t3201 = load i64, i64* %obj_handle_v3199
    %t3202 = load i64, i64* %obj_children_v3191
    %t3203 = call i64 @freak_llvm_word_from_int(i64 %t3202)
    call void @freak_llvm_array_set(i64 %t3200, i64 %t3201, i64 %t3203)
    %t3204 = load i64, i64* @g_json_keys
    %t3205 = load i64, i64* %obj_handle_v3199
    %t3206 = load i64, i64* %obj_keys_v3193
    %t3207 = call i64 @freak_llvm_word_from_int(i64 %t3206)
    call void @freak_llvm_array_set(i64 %t3204, i64 %t3205, i64 %t3207)
    call void @freak_json_skip_ws()
    %t3208 = call i64 @freak_json_cur()
    %t3209 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.195, i64 0, i64 0
    %t3210 = ptrtoint i8* %t3209 to i64
    %t3211 = call i64 @freak_llvm_word_neq(i64 %t3208, i64 %t3210)
    %t3215 = icmp ne i64 %t3211, 0
    br i1 %t3215, label %if.then.3212, label %if.end.3214
if.then.3212:
    %t3216 = call i64 @freak_json_parse_string()
    %k1_v3217 = alloca i64
    store i64 %t3216, i64* %k1_v3217
    call void @freak_json_skip_ws()
    %t3218 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.196, i64 0, i64 0
    %t3219 = ptrtoint i8* %t3218 to i64
    call void @freak_json_expect(i64 %t3219)
    %t3220 = call i64 @freak_json_parse_value()
    %v1_v3221 = alloca i64
    store i64 %t3220, i64* %v1_v3221
    %t3222 = load i64, i64* %obj_keys_v3193
    %t3223 = load i64, i64* %k1_v3217
    call void @freak_llvm_array_push(i64 %t3222, i64 %t3223)
    %t3224 = load i64, i64* %obj_children_v3191
    %t3225 = load i64, i64* %v1_v3221
    %t3226 = call i64 @freak_llvm_word_from_int(i64 %t3225)
    call void @freak_llvm_array_push(i64 %t3224, i64 %t3226)
    call void @freak_json_skip_ws()
    br label %loop.cond.3227
loop.cond.3227:
    %t3230 = call i64 @freak_json_cur()
    %t3231 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.197, i64 0, i64 0
    %t3232 = ptrtoint i8* %t3231 to i64
    %t3233 = call i64 @freak_llvm_word_neq(i64 %t3230, i64 %t3232)
    %t3234 = icmp eq i64 %t3233, 0
    br i1 %t3234, label %loop.body.3228, label %loop.end.3229
loop.body.3228:
    %t3235 = load i64, i64* @g_json_pos
    %t3236 = add i64 %t3235, 1
    store i64 %t3236, i64* @g_json_pos
    call void @freak_json_skip_ws()
    %t3237 = call i64 @freak_json_parse_string()
    %kn_v3238 = alloca i64
    store i64 %t3237, i64* %kn_v3238
    call void @freak_json_skip_ws()
    %t3239 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.198, i64 0, i64 0
    %t3240 = ptrtoint i8* %t3239 to i64
    call void @freak_json_expect(i64 %t3240)
    %t3241 = call i64 @freak_json_parse_value()
    %vn_v3242 = alloca i64
    store i64 %t3241, i64* %vn_v3242
    %t3243 = load i64, i64* %obj_keys_v3193
    %t3244 = load i64, i64* %kn_v3238
    call void @freak_llvm_array_push(i64 %t3243, i64 %t3244)
    %t3245 = load i64, i64* %obj_children_v3191
    %t3246 = load i64, i64* %vn_v3242
    %t3247 = call i64 @freak_llvm_word_from_int(i64 %t3246)
    call void @freak_llvm_array_push(i64 %t3245, i64 %t3247)
    call void @freak_json_skip_ws()
    br label %loop.cond.3227
loop.end.3229:
    br label %if.end.3214
if.end.3214:
    %t3248 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.199, i64 0, i64 0
    %t3249 = ptrtoint i8* %t3248 to i64
    call void @freak_json_expect(i64 %t3249)
    %t3250 = load i64, i64* %obj_handle_v3199
    ret i64 %t3250
    br label %if.end.3186
if.end.3186:
    %t3251 = getelementptr inbounds [31 x i8], [31 x i8]* @.str.200, i64 0, i64 0
    %t3252 = ptrtoint i8* %t3251 to i64
    %t3253 = load i64, i64* %c_v2958
    %t3254 = call i64 @freak_llvm_word_concat(i64 %t3252, i64 %t3253)
    %t3255 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.201, i64 0, i64 0
    %t3256 = ptrtoint i8* %t3255 to i64
    %t3257 = call i64 @freak_llvm_word_concat(i64 %t3254, i64 %t3256)
    call void @freak_llvm_say(i64 %t3257)
    %t3258 = sub i64 0, 1
    ret i64 %t3258
    ret i64 0
}

define i64 @freak_json_parse(i64 %arg_source) {
entry:
    %source = alloca i64
    store i64 %arg_source, i64* %source
    call void @freak_json_init()
    %t3259 = load i64, i64* %source
    store i64 %t3259, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    %t3260 = load i64, i64* %source
    %t3261 = call i64 @freak_llvm_word_length(i64 %t3260)
    store i64 %t3261, i64* @g_json_len
    %t3262 = call i64 @freak_json_parse_value()
    ret i64 %t3262
    ret i64 0
}

define i64 @freak_json_stringify(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t3263 = load i64, i64* %handle
    %t3265 = icmp slt i64 %t3263, 0
    %t3264 = zext i1 %t3265 to i64
    %t3269 = icmp ne i64 %t3264, 0
    br i1 %t3269, label %if.then.3266, label %if.end.3268
if.then.3266:
    %t3270 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.202, i64 0, i64 0
    %t3271 = ptrtoint i8* %t3270 to i64
    ret i64 %t3271
    br label %if.end.3268
if.end.3268:
    %t3272 = load i64, i64* @g_json_types
    %t3273 = load i64, i64* %handle
    %t3274 = call i64 @freak_llvm_array_get(i64 %t3272, i64 %t3273)
    %t_v3275 = alloca i64
    store i64 %t3274, i64* %t_v3275
    %t3276 = load i64, i64* %t_v3275
    %t3277 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.203, i64 0, i64 0
    %t3278 = ptrtoint i8* %t3277 to i64
    %t3279 = call i64 @freak_llvm_word_eq(i64 %t3276, i64 %t3278)
    %t3283 = icmp ne i64 %t3279, 0
    br i1 %t3283, label %if.then.3280, label %if.end.3282
if.then.3280:
    %t3284 = load i64, i64* @g_json_vals
    %t3285 = load i64, i64* %handle
    %t3286 = call i64 @freak_llvm_array_get(i64 %t3284, i64 %t3285)
    %sv_v3287 = alloca i64
    store i64 %t3286, i64* %sv_v3287
    %t3288 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.204, i64 0, i64 0
    %t3289 = ptrtoint i8* %t3288 to i64
    %t3290 = load i64, i64* %sv_v3287
    %t3291 = call i64 @freak_llvm_word_concat(i64 %t3289, i64 %t3290)
    %t3292 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.205, i64 0, i64 0
    %t3293 = ptrtoint i8* %t3292 to i64
    %t3294 = call i64 @freak_llvm_word_concat(i64 %t3291, i64 %t3293)
    ret i64 %t3294
    br label %if.end.3282
if.end.3282:
    %t3295 = load i64, i64* %t_v3275
    %t3296 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.206, i64 0, i64 0
    %t3297 = ptrtoint i8* %t3296 to i64
    %t3298 = call i64 @freak_llvm_word_eq(i64 %t3295, i64 %t3297)
    %t3302 = icmp ne i64 %t3298, 0
    br i1 %t3302, label %if.then.3299, label %if.end.3301
if.then.3299:
    %t3303 = load i64, i64* @g_json_vals
    %t3304 = load i64, i64* %handle
    %t3305 = call i64 @freak_llvm_array_get(i64 %t3303, i64 %t3304)
    ret i64 %t3305
    br label %if.end.3301
if.end.3301:
    %t3306 = load i64, i64* %t_v3275
    %t3307 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.207, i64 0, i64 0
    %t3308 = ptrtoint i8* %t3307 to i64
    %t3309 = call i64 @freak_llvm_word_eq(i64 %t3306, i64 %t3308)
    %t3313 = icmp ne i64 %t3309, 0
    br i1 %t3313, label %if.then.3310, label %if.end.3312
if.then.3310:
    %t3314 = load i64, i64* @g_json_vals
    %t3315 = load i64, i64* %handle
    %t3316 = call i64 @freak_llvm_array_get(i64 %t3314, i64 %t3315)
    ret i64 %t3316
    br label %if.end.3312
if.end.3312:
    %t3317 = load i64, i64* %t_v3275
    %t3318 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.208, i64 0, i64 0
    %t3319 = ptrtoint i8* %t3318 to i64
    %t3320 = call i64 @freak_llvm_word_eq(i64 %t3317, i64 %t3319)
    %t3324 = icmp ne i64 %t3320, 0
    br i1 %t3324, label %if.then.3321, label %if.end.3323
if.then.3321:
    %t3325 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.209, i64 0, i64 0
    %t3326 = ptrtoint i8* %t3325 to i64
    ret i64 %t3326
    br label %if.end.3323
if.end.3323:
    %t3327 = load i64, i64* %t_v3275
    %t3328 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.210, i64 0, i64 0
    %t3329 = ptrtoint i8* %t3328 to i64
    %t3330 = call i64 @freak_llvm_word_eq(i64 %t3327, i64 %t3329)
    %t3334 = icmp ne i64 %t3330, 0
    br i1 %t3334, label %if.then.3331, label %if.end.3333
if.then.3331:
    %t3335 = load i64, i64* %handle
    %t3336 = call i64 @freak_json_arr_len(i64 %t3335)
    %alen_v3337 = alloca i64
    store i64 %t3336, i64* %alen_v3337
    %t3338 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.211, i64 0, i64 0
    %t3339 = ptrtoint i8* %t3338 to i64
    %a_out_v3340 = alloca i64
    store i64 %t3339, i64* %a_out_v3340
    %ai_v3341 = alloca i64
    store i64 0, i64* %ai_v3341
    %t3347 = load i64, i64* %alen_v3337
    %rep.3346 = alloca i64
    store i64 0, i64* %rep.3346
    br label %loop.cond.3342
loop.cond.3342:
    %t3348 = load i64, i64* %rep.3346
    %t3349 = icmp slt i64 %t3348, %t3347
    br i1 %t3349, label %loop.body.3343, label %loop.end.3344
loop.body.3343:
    %t3350 = load i64, i64* %ai_v3341
    %t3352 = icmp sgt i64 %t3350, 0
    %t3351 = zext i1 %t3352 to i64
    %t3356 = icmp ne i64 %t3351, 0
    br i1 %t3356, label %if.then.3353, label %if.end.3355
if.then.3353:
    %t3357 = load i64, i64* %a_out_v3340
    %t3358 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.212, i64 0, i64 0
    %t3359 = ptrtoint i8* %t3358 to i64
    %t3360 = call i64 @freak_llvm_word_concat(i64 %t3357, i64 %t3359)
    store i64 %t3360, i64* %a_out_v3340
    br label %if.end.3355
if.end.3355:
    %t3361 = load i64, i64* %handle
    %t3362 = load i64, i64* %ai_v3341
    %t3363 = call i64 @freak_json_arr_get(i64 %t3361, i64 %t3362)
    %child_v3364 = alloca i64
    store i64 %t3363, i64* %child_v3364
    %t3365 = load i64, i64* %a_out_v3340
    %t3366 = load i64, i64* %child_v3364
    %t3367 = call i64 @freak_json_stringify(i64 %t3366)
    %t3368 = call i64 @freak_llvm_word_concat(i64 %t3365, i64 %t3367)
    store i64 %t3368, i64* %a_out_v3340
    %t3369 = load i64, i64* %ai_v3341
    %t3370 = add i64 %t3369, 1
    store i64 %t3370, i64* %ai_v3341
    br label %loop.inc.3345
loop.inc.3345:
    %t3371 = load i64, i64* %rep.3346
    %t3372 = add i64 %t3371, 1
    store i64 %t3372, i64* %rep.3346
    br label %loop.cond.3342
loop.end.3344:
    %t3373 = load i64, i64* %a_out_v3340
    %t3374 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.213, i64 0, i64 0
    %t3375 = ptrtoint i8* %t3374 to i64
    %t3376 = call i64 @freak_llvm_word_concat(i64 %t3373, i64 %t3375)
    ret i64 %t3376
    br label %if.end.3333
if.end.3333:
    %t3377 = load i64, i64* %t_v3275
    %t3378 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.214, i64 0, i64 0
    %t3379 = ptrtoint i8* %t3378 to i64
    %t3380 = call i64 @freak_llvm_word_eq(i64 %t3377, i64 %t3379)
    %t3384 = icmp ne i64 %t3380, 0
    br i1 %t3384, label %if.then.3381, label %if.end.3383
if.then.3381:
    %t3385 = load i64, i64* %handle
    %t3386 = call i64 @freak_json_obj_len(i64 %t3385)
    %olen_v3387 = alloca i64
    store i64 %t3386, i64* %olen_v3387
    %t3388 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.215, i64 0, i64 0
    %t3389 = ptrtoint i8* %t3388 to i64
    %o_out_v3390 = alloca i64
    store i64 %t3389, i64* %o_out_v3390
    %oi_v3391 = alloca i64
    store i64 0, i64* %oi_v3391
    %t3397 = load i64, i64* %olen_v3387
    %rep.3396 = alloca i64
    store i64 0, i64* %rep.3396
    br label %loop.cond.3392
loop.cond.3392:
    %t3398 = load i64, i64* %rep.3396
    %t3399 = icmp slt i64 %t3398, %t3397
    br i1 %t3399, label %loop.body.3393, label %loop.end.3394
loop.body.3393:
    %t3400 = load i64, i64* %oi_v3391
    %t3402 = icmp sgt i64 %t3400, 0
    %t3401 = zext i1 %t3402 to i64
    %t3406 = icmp ne i64 %t3401, 0
    br i1 %t3406, label %if.then.3403, label %if.end.3405
if.then.3403:
    %t3407 = load i64, i64* %o_out_v3390
    %t3408 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.216, i64 0, i64 0
    %t3409 = ptrtoint i8* %t3408 to i64
    %t3410 = call i64 @freak_llvm_word_concat(i64 %t3407, i64 %t3409)
    store i64 %t3410, i64* %o_out_v3390
    br label %if.end.3405
if.end.3405:
    %t3411 = load i64, i64* %handle
    %t3412 = load i64, i64* %oi_v3391
    %t3413 = call i64 @freak_json_obj_key_at(i64 %t3411, i64 %t3412)
    %okey_v3414 = alloca i64
    store i64 %t3413, i64* %okey_v3414
    %t3415 = load i64, i64* %handle
    %t3416 = load i64, i64* %oi_v3391
    %t3417 = call i64 @freak_json_arr_get(i64 %t3415, i64 %t3416)
    %ov_v3418 = alloca i64
    store i64 %t3417, i64* %ov_v3418
    %t3419 = load i64, i64* %o_out_v3390
    %t3420 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.217, i64 0, i64 0
    %t3421 = ptrtoint i8* %t3420 to i64
    %t3422 = call i64 @freak_llvm_word_concat(i64 %t3419, i64 %t3421)
    %t3423 = load i64, i64* %okey_v3414
    %t3424 = call i64 @freak_llvm_word_concat(i64 %t3422, i64 %t3423)
    %t3425 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.218, i64 0, i64 0
    %t3426 = ptrtoint i8* %t3425 to i64
    %t3427 = call i64 @freak_llvm_word_concat(i64 %t3424, i64 %t3426)
    %t3428 = load i64, i64* %ov_v3418
    %t3429 = call i64 @freak_json_stringify(i64 %t3428)
    %t3430 = call i64 @freak_llvm_word_concat(i64 %t3427, i64 %t3429)
    store i64 %t3430, i64* %o_out_v3390
    %t3431 = load i64, i64* %oi_v3391
    %t3432 = add i64 %t3431, 1
    store i64 %t3432, i64* %oi_v3391
    br label %loop.inc.3395
loop.inc.3395:
    %t3433 = load i64, i64* %rep.3396
    %t3434 = add i64 %t3433, 1
    store i64 %t3434, i64* %rep.3396
    br label %loop.cond.3392
loop.end.3394:
    %t3435 = load i64, i64* %o_out_v3390
    %t3436 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.219, i64 0, i64 0
    %t3437 = ptrtoint i8* %t3436 to i64
    %t3438 = call i64 @freak_llvm_word_concat(i64 %t3435, i64 %t3437)
    ret i64 %t3438
    br label %if.end.3383
if.end.3383:
    %t3439 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.220, i64 0, i64 0
    %t3440 = ptrtoint i8* %t3439 to i64
    ret i64 %t3440
    ret i64 0
}

define i64 @freak_ver_parse_num(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3441 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.221, i64 0, i64 0
    %t3442 = ptrtoint i8* %t3441 to i64
    %res_v3443 = alloca i64
    store i64 %t3442, i64* %res_v3443
    %t3444 = load i64, i64* %start
    store i64 %t3444, i64* @g_i
    %t3445 = load i64, i64* %s
    %t3446 = call i64 @freak_llvm_word_length(i64 %t3445)
    %slen_v3447 = alloca i64
    store i64 %t3446, i64* %slen_v3447
    br label %loop.cond.3448
loop.cond.3448:
    %t3451 = load i64, i64* @g_i
    %t3452 = load i64, i64* %slen_v3447
    %t3454 = icmp sge i64 %t3451, %t3452
    %t3453 = zext i1 %t3454 to i64
    %t3455 = icmp eq i64 %t3453, 0
    br i1 %t3455, label %loop.body.3449, label %loop.end.3450
loop.body.3449:
    %t3456 = load i64, i64* %s
    %t3458 = load i64, i64* @g_i
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
    %t3484 = load i64, i64* @g_i
    %t3485 = add i64 %t3484, 1
    %t3486 = call i64 @freak_llvm_word_from_int(i64 %t3485)
    %pos_str_v3487 = alloca i64
    store i64 %t3486, i64* %pos_str_v3487
    %t3488 = load i64, i64* %res_v3443
    %t3489 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.225, i64 0, i64 0
    %t3490 = ptrtoint i8* %t3489 to i64
    %t3491 = call i64 @freak_llvm_word_concat(i64 %t3488, i64 %t3490)
    %t3492 = load i64, i64* %pos_str_v3487
    %t3493 = call i64 @freak_llvm_word_concat(i64 %t3491, i64 %t3492)
    ret i64 %t3493
    br label %if.end.3482
if.end.3482:
    %t3494 = load i64, i64* %res_v3443
    %t3495 = load i64, i64* %c_v3459
    %t3496 = call i64 @freak_llvm_word_concat(i64 %t3494, i64 %t3495)
    store i64 %t3496, i64* %res_v3443
    %t3497 = load i64, i64* @g_i
    %t3498 = add i64 %t3497, 1
    store i64 %t3498, i64* @g_i
    br label %loop.cond.3448
loop.end.3450:
    %t3499 = load i64, i64* @g_i
    %t3500 = call i64 @freak_llvm_word_from_int(i64 %t3499)
    %pos_str2_v3501 = alloca i64
    store i64 %t3500, i64* %pos_str2_v3501
    %t3502 = load i64, i64* %res_v3443
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
    store i64 %t3511, i64* @g_i
    %t3512 = load i64, i64* %s
    %t3513 = call i64 @freak_llvm_word_length(i64 %t3512)
    %slen_v3514 = alloca i64
    store i64 %t3513, i64* %slen_v3514
    br label %loop.cond.3515
loop.cond.3515:
    %t3518 = load i64, i64* @g_i
    %t3519 = load i64, i64* %slen_v3514
    %t3521 = icmp sge i64 %t3518, %t3519
    %t3520 = zext i1 %t3521 to i64
    %t3522 = icmp eq i64 %t3520, 0
    br i1 %t3522, label %loop.body.3516, label %loop.end.3517
loop.body.3516:
    %t3523 = load i64, i64* %s
    %t3525 = load i64, i64* @g_i
    %t3524 = call i64 @freak_llvm_word_char_at(i64 %t3523, i64 %t3525)
    %c_v3526 = alloca i64
    store i64 %t3524, i64* %c_v3526
    %t3527 = load i64, i64* %c_v3526
    %t3528 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.228, i64 0, i64 0
    %t3529 = ptrtoint i8* %t3528 to i64
    %t3530 = call i64 @freak_llvm_word_eq(i64 %t3527, i64 %t3529)
    %t3534 = icmp ne i64 %t3530, 0
    br i1 %t3534, label %if.then.3531, label %if.end.3533
if.then.3531:
    %t3535 = load i64, i64* %res_v3510
    ret i64 %t3535
    br label %if.end.3533
if.end.3533:
    %t3536 = load i64, i64* %res_v3510
    %t3537 = load i64, i64* %c_v3526
    %t3538 = call i64 @freak_llvm_word_concat(i64 %t3536, i64 %t3537)
    store i64 %t3538, i64* %res_v3510
    %t3539 = load i64, i64* @g_i
    %t3540 = add i64 %t3539, 1
    store i64 %t3540, i64* @g_i
    br label %loop.cond.3515
loop.end.3517:
    %t3541 = load i64, i64* %res_v3510
    ret i64 %t3541
    ret i64 0
}

define i64 @freak_ver_parse_build(i64 %arg_s, i64 %arg_start) {
entry:
    %s = alloca i64
    store i64 %arg_s, i64* %s
    %start = alloca i64
    store i64 %arg_start, i64* %start
    %t3542 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.229, i64 0, i64 0
    %t3543 = ptrtoint i8* %t3542 to i64
    %res_v3544 = alloca i64
    store i64 %t3543, i64* %res_v3544
    %t3545 = load i64, i64* %start
    store i64 %t3545, i64* @g_i
    %t3546 = load i64, i64* %s
    %t3547 = call i64 @freak_llvm_word_length(i64 %t3546)
    %slen_v3548 = alloca i64
    store i64 %t3547, i64* %slen_v3548
    br label %loop.cond.3549
loop.cond.3549:
    %t3552 = load i64, i64* @g_i
    %t3553 = load i64, i64* %slen_v3548
    %t3555 = icmp sge i64 %t3552, %t3553
    %t3554 = zext i1 %t3555 to i64
    %t3556 = icmp eq i64 %t3554, 0
    br i1 %t3556, label %loop.body.3550, label %loop.end.3551
loop.body.3550:
    %t3557 = load i64, i64* %res_v3544
    %t3558 = load i64, i64* %s
    %t3560 = load i64, i64* @g_i
    %t3559 = call i64 @freak_llvm_word_char_at(i64 %t3558, i64 %t3560)
    %t3561 = call i64 @freak_llvm_word_concat(i64 %t3557, i64 %t3559)
    store i64 %t3561, i64* %res_v3544
    %t3562 = load i64, i64* @g_i
    %t3563 = add i64 %t3562, 1
    store i64 %t3563, i64* @g_i
    br label %loop.cond.3549
loop.end.3551:
    %t3564 = load i64, i64* %res_v3544
    ret i64 %t3564
    ret i64 0
}

define i64 @freak_ver_get_val(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    %t3565 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.230, i64 0, i64 0
    %t3566 = ptrtoint i8* %t3565 to i64
    %res_v3567 = alloca i64
    store i64 %t3566, i64* %res_v3567
    store i64 0, i64* @g_i
    %t3568 = load i64, i64* %encoded
    %t3569 = call i64 @freak_llvm_word_length(i64 %t3568)
    %elen_v3570 = alloca i64
    store i64 %t3569, i64* %elen_v3570
    br label %loop.cond.3571
loop.cond.3571:
    %t3574 = load i64, i64* @g_i
    %t3575 = load i64, i64* %elen_v3570
    %t3577 = icmp sge i64 %t3574, %t3575
    %t3576 = zext i1 %t3577 to i64
    %t3578 = icmp eq i64 %t3576, 0
    br i1 %t3578, label %loop.body.3572, label %loop.end.3573
loop.body.3572:
    %t3579 = load i64, i64* %encoded
    %t3581 = load i64, i64* @g_i
    %t3580 = call i64 @freak_llvm_word_char_at(i64 %t3579, i64 %t3581)
    %c_v3582 = alloca i64
    store i64 %t3580, i64* %c_v3582
    %t3583 = load i64, i64* %c_v3582
    %t3584 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.231, i64 0, i64 0
    %t3585 = ptrtoint i8* %t3584 to i64
    %t3586 = call i64 @freak_llvm_word_eq(i64 %t3583, i64 %t3585)
    %t3590 = icmp ne i64 %t3586, 0
    br i1 %t3590, label %if.then.3587, label %if.end.3589
if.then.3587:
    %t3591 = load i64, i64* %res_v3567
    ret i64 %t3591
    br label %if.end.3589
if.end.3589:
    %t3592 = load i64, i64* %res_v3567
    %t3593 = load i64, i64* %c_v3582
    %t3594 = call i64 @freak_llvm_word_concat(i64 %t3592, i64 %t3593)
    store i64 %t3594, i64* %res_v3567
    %t3595 = load i64, i64* @g_i
    %t3596 = add i64 %t3595, 1
    store i64 %t3596, i64* @g_i
    br label %loop.cond.3571
loop.end.3573:
    %t3597 = load i64, i64* %res_v3567
    ret i64 %t3597
    ret i64 0
}

define i64 @freak_ver_get_pos(i64 %arg_encoded) {
entry:
    %encoded = alloca i64
    store i64 %arg_encoded, i64* %encoded
    store i64 0, i64* @g_i
    %t3598 = load i64, i64* %encoded
    %t3599 = call i64 @freak_llvm_word_length(i64 %t3598)
    %elen_v3600 = alloca i64
    store i64 %t3599, i64* %elen_v3600
    br label %loop.cond.3601
loop.cond.3601:
    %t3604 = load i64, i64* @g_i
    %t3605 = load i64, i64* %elen_v3600
    %t3607 = icmp sge i64 %t3604, %t3605
    %t3606 = zext i1 %t3607 to i64
    %t3608 = icmp eq i64 %t3606, 0
    br i1 %t3608, label %loop.body.3602, label %loop.end.3603
loop.body.3602:
    %t3609 = load i64, i64* %encoded
    %t3611 = load i64, i64* @g_i
    %t3610 = call i64 @freak_llvm_word_char_at(i64 %t3609, i64 %t3611)
    %c_v3612 = alloca i64
    store i64 %t3610, i64* %c_v3612
    %t3613 = load i64, i64* %c_v3612
    %t3614 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.232, i64 0, i64 0
    %t3615 = ptrtoint i8* %t3614 to i64
    %t3616 = call i64 @freak_llvm_word_eq(i64 %t3613, i64 %t3615)
    %t3620 = icmp ne i64 %t3616, 0
    br i1 %t3620, label %if.then.3617, label %if.end.3619
if.then.3617:
    %t3621 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.233, i64 0, i64 0
    %t3622 = ptrtoint i8* %t3621 to i64
    %pos_str_v3623 = alloca i64
    store i64 %t3622, i64* %pos_str_v3623
    %t3624 = load i64, i64* @g_i
    %t3625 = add i64 %t3624, 1
    %j_v3626 = alloca i64
    store i64 %t3625, i64* %j_v3626
    br label %loop.cond.3627
loop.cond.3627:
    %t3630 = load i64, i64* %j_v3626
    %t3631 = load i64, i64* %elen_v3600
    %t3633 = icmp sge i64 %t3630, %t3631
    %t3632 = zext i1 %t3633 to i64
    %t3634 = icmp eq i64 %t3632, 0
    br i1 %t3634, label %loop.body.3628, label %loop.end.3629
loop.body.3628:
    %t3635 = load i64, i64* %pos_str_v3623
    %t3636 = load i64, i64* %encoded
    %t3638 = load i64, i64* %j_v3626
    %t3637 = call i64 @freak_llvm_word_char_at(i64 %t3636, i64 %t3638)
    %t3639 = call i64 @freak_llvm_word_concat(i64 %t3635, i64 %t3637)
    store i64 %t3639, i64* %pos_str_v3623
    %t3640 = load i64, i64* %j_v3626
    %t3641 = add i64 %t3640, 1
    store i64 %t3641, i64* %j_v3626
    br label %loop.cond.3627
loop.end.3629:
    %t3642 = load i64, i64* %pos_str_v3623
    %t3643 = call i64 @freak_llvm_word_to_int(i64 %t3642)
    ret i64 %t3643
    br label %if.end.3619
if.end.3619:
    %t3644 = load i64, i64* @g_i
    %t3645 = add i64 %t3644, 1
    store i64 %t3645, i64* @g_i
    br label %loop.cond.3601
loop.end.3603:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_parse(i64 %arg_version) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %t3646 = load i64, i64* %version
    %s_v3647 = alloca i64
    store i64 %t3646, i64* %s_v3647
    %t3648 = load i64, i64* %s_v3647
    %t3649 = call i64 @freak_llvm_word_length(i64 %t3648)
    %t3651 = icmp sgt i64 %t3649, 0
    %t3650 = zext i1 %t3651 to i64
    %t3655 = icmp ne i64 %t3650, 0
    br i1 %t3655, label %if.then.3652, label %if.end.3654
if.then.3652:
    %t3656 = load i64, i64* %s_v3647
    %t3657 = call i64 @freak_llvm_word_char_at(i64 %t3656, i64 0)
    %fc_v3658 = alloca i64
    store i64 %t3657, i64* %fc_v3658
    %t3659 = load i64, i64* %fc_v3658
    %t3660 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.234, i64 0, i64 0
    %t3661 = ptrtoint i8* %t3660 to i64
    %t3662 = call i64 @freak_llvm_word_eq(i64 %t3659, i64 %t3661)
    %t3663 = load i64, i64* %fc_v3658
    %t3664 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.235, i64 0, i64 0
    %t3665 = ptrtoint i8* %t3664 to i64
    %t3666 = call i64 @freak_llvm_word_eq(i64 %t3663, i64 %t3665)
    %t3668 = icmp ne i64 %t3662, 0
    %t3669 = icmp ne i64 %t3666, 0
    %t3670 = or i1 %t3668, %t3669
    %t3667 = zext i1 %t3670 to i64
    %t3674 = icmp ne i64 %t3667, 0
    br i1 %t3674, label %if.then.3671, label %if.end.3673
if.then.3671:
    %t3675 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.236, i64 0, i64 0
    %t3676 = ptrtoint i8* %t3675 to i64
    %ns_v3677 = alloca i64
    store i64 %t3676, i64* %ns_v3677
    %vi_v3678 = alloca i64
    store i64 1, i64* %vi_v3678
    br label %loop.cond.3679
loop.cond.3679:
    %t3682 = load i64, i64* %vi_v3678
    %t3683 = load i64, i64* %s_v3647
    %t3684 = call i64 @freak_llvm_word_length(i64 %t3683)
    %t3686 = icmp sge i64 %t3682, %t3684
    %t3685 = zext i1 %t3686 to i64
    %t3687 = icmp eq i64 %t3685, 0
    br i1 %t3687, label %loop.body.3680, label %loop.end.3681
loop.body.3680:
    %t3688 = load i64, i64* %ns_v3677
    %t3689 = load i64, i64* %s_v3647
    %t3691 = load i64, i64* %vi_v3678
    %t3690 = call i64 @freak_llvm_word_char_at(i64 %t3689, i64 %t3691)
    %t3692 = call i64 @freak_llvm_word_concat(i64 %t3688, i64 %t3690)
    store i64 %t3692, i64* %ns_v3677
    %t3693 = load i64, i64* %vi_v3678
    %t3694 = add i64 %t3693, 1
    store i64 %t3694, i64* %vi_v3678
    br label %loop.cond.3679
loop.end.3681:
    %t3695 = load i64, i64* %ns_v3677
    store i64 %t3695, i64* %s_v3647
    br label %if.end.3673
if.end.3673:
    br label %if.end.3654
if.end.3654:
    %t3696 = load i64, i64* %s_v3647
    %t3697 = call i64 @freak_ver_parse_num(i64 %t3696, i64 0)
    %r1_v3698 = alloca i64
    store i64 %t3697, i64* %r1_v3698
    %t3699 = load i64, i64* %r1_v3698
    %t3700 = call i64 @freak_ver_get_val(i64 %t3699)
    %major_v3701 = alloca i64
    store i64 %t3700, i64* %major_v3701
    %t3702 = load i64, i64* %r1_v3698
    %t3703 = call i64 @freak_ver_get_pos(i64 %t3702)
    %pos1_v3704 = alloca i64
    store i64 %t3703, i64* %pos1_v3704
    %t3705 = load i64, i64* %s_v3647
    %t3706 = load i64, i64* %pos1_v3704
    %t3707 = call i64 @freak_ver_parse_num(i64 %t3705, i64 %t3706)
    %r2_v3708 = alloca i64
    store i64 %t3707, i64* %r2_v3708
    %t3709 = load i64, i64* %r2_v3708
    %t3710 = call i64 @freak_ver_get_val(i64 %t3709)
    %minor_v3711 = alloca i64
    store i64 %t3710, i64* %minor_v3711
    %t3712 = load i64, i64* %r2_v3708
    %t3713 = call i64 @freak_ver_get_pos(i64 %t3712)
    %pos2_v3714 = alloca i64
    store i64 %t3713, i64* %pos2_v3714
    %t3715 = load i64, i64* %s_v3647
    %t3716 = load i64, i64* %pos2_v3714
    %t3717 = call i64 @freak_ver_parse_num(i64 %t3715, i64 %t3716)
    %r3_v3718 = alloca i64
    store i64 %t3717, i64* %r3_v3718
    %t3719 = load i64, i64* %r3_v3718
    %t3720 = call i64 @freak_ver_get_val(i64 %t3719)
    %patch_v3721 = alloca i64
    store i64 %t3720, i64* %patch_v3721
    %t3722 = load i64, i64* %r3_v3718
    %t3723 = call i64 @freak_ver_get_pos(i64 %t3722)
    %pos3_v3724 = alloca i64
    store i64 %t3723, i64* %pos3_v3724
    %t3725 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.237, i64 0, i64 0
    %t3726 = ptrtoint i8* %t3725 to i64
    %pre_v3727 = alloca i64
    store i64 %t3726, i64* %pre_v3727
    %t3728 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.238, i64 0, i64 0
    %t3729 = ptrtoint i8* %t3728 to i64
    %bld_v3730 = alloca i64
    store i64 %t3729, i64* %bld_v3730
    %t3731 = load i64, i64* %pos3_v3724
    %t3732 = load i64, i64* %s_v3647
    %t3733 = call i64 @freak_llvm_word_length(i64 %t3732)
    %t3735 = icmp sle i64 %t3731, %t3733
    %t3734 = zext i1 %t3735 to i64
    %t3739 = icmp ne i64 %t3734, 0
    br i1 %t3739, label %if.then.3736, label %if.end.3738
if.then.3736:
    %t3740 = load i64, i64* %pos3_v3724
    %t3742 = icmp sgt i64 %t3740, 0
    %t3741 = zext i1 %t3742 to i64
    %t3746 = icmp ne i64 %t3741, 0
    br i1 %t3746, label %if.then.3743, label %if.end.3745
if.then.3743:
    %t3747 = load i64, i64* %s_v3647
    %t3749 = load i64, i64* %pos3_v3724
    %t3750 = sub i64 %t3749, 1
    %t3748 = call i64 @freak_llvm_word_char_at(i64 %t3747, i64 %t3750)
    %delim_v3751 = alloca i64
    store i64 %t3748, i64* %delim_v3751
    %t3752 = load i64, i64* %delim_v3751
    %t3753 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.239, i64 0, i64 0
    %t3754 = ptrtoint i8* %t3753 to i64
    %t3755 = call i64 @freak_llvm_word_eq(i64 %t3752, i64 %t3754)
    %t3759 = icmp ne i64 %t3755, 0
    br i1 %t3759, label %if.then.3756, label %if.else.3757
if.then.3756:
    %t3760 = load i64, i64* %s_v3647
    %t3761 = load i64, i64* %pos3_v3724
    %t3762 = call i64 @freak_ver_parse_pre(i64 %t3760, i64 %t3761)
    store i64 %t3762, i64* %pre_v3727
    br label %if.end.3758
if.else.3757:
    %t3763 = load i64, i64* %delim_v3751
    %t3764 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.240, i64 0, i64 0
    %t3765 = ptrtoint i8* %t3764 to i64
    %t3766 = call i64 @freak_llvm_word_eq(i64 %t3763, i64 %t3765)
    %t3770 = icmp ne i64 %t3766, 0
    br i1 %t3770, label %if.then.3767, label %if.end.3769
if.then.3767:
    %t3771 = load i64, i64* %s_v3647
    %t3772 = load i64, i64* %pos3_v3724
    %t3773 = call i64 @freak_ver_parse_build(i64 %t3771, i64 %t3772)
    store i64 %t3773, i64* %bld_v3730
    br label %if.end.3769
if.end.3769:
    br label %if.end.3758
if.end.3758:
    br label %if.end.3745
if.end.3745:
    br label %if.end.3738
if.end.3738:
    %t3774 = load i64, i64* %pre_v3727
    %t3775 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.241, i64 0, i64 0
    %t3776 = ptrtoint i8* %t3775 to i64
    %t3777 = call i64 @freak_llvm_word_neq(i64 %t3774, i64 %t3776)
    %t3781 = icmp ne i64 %t3777, 0
    br i1 %t3781, label %if.then.3778, label %if.end.3780
if.then.3778:
    %pi_v3782 = alloca i64
    store i64 0, i64* %pi_v3782
    %t3783 = load i64, i64* %s_v3647
    %t3784 = call i64 @freak_llvm_word_length(i64 %t3783)
    %plen_v3785 = alloca i64
    store i64 %t3784, i64* %plen_v3785
    br label %loop.cond.3786
loop.cond.3786:
    %t3789 = load i64, i64* %pi_v3782
    %t3790 = load i64, i64* %plen_v3785
    %t3792 = icmp sge i64 %t3789, %t3790
    %t3791 = zext i1 %t3792 to i64
    %t3793 = icmp eq i64 %t3791, 0
    br i1 %t3793, label %loop.body.3787, label %loop.end.3788
loop.body.3787:
    %t3794 = load i64, i64* %s_v3647
    %t3796 = load i64, i64* %pi_v3782
    %t3795 = call i64 @freak_llvm_word_char_at(i64 %t3794, i64 %t3796)
    %t3797 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.242, i64 0, i64 0
    %t3798 = ptrtoint i8* %t3797 to i64
    %t3799 = call i64 @freak_llvm_word_eq(i64 %t3795, i64 %t3798)
    %t3803 = icmp ne i64 %t3799, 0
    br i1 %t3803, label %if.then.3800, label %if.end.3802
if.then.3800:
    %t3804 = load i64, i64* %s_v3647
    %t3805 = load i64, i64* %pi_v3782
    %t3806 = add i64 %t3805, 1
    %t3807 = call i64 @freak_ver_parse_build(i64 %t3804, i64 %t3806)
    store i64 %t3807, i64* %bld_v3730
    br label %if.end.3802
if.end.3802:
    %t3808 = load i64, i64* %pi_v3782
    %t3809 = add i64 %t3808, 1
    store i64 %t3809, i64* %pi_v3782
    br label %loop.cond.3786
loop.end.3788:
    br label %if.end.3780
if.end.3780:
    %t3810 = load i64, i64* %major_v3701
    %t3811 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.243, i64 0, i64 0
    %t3812 = ptrtoint i8* %t3811 to i64
    %t3813 = call i64 @freak_llvm_word_concat(i64 %t3810, i64 %t3812)
    %t3814 = load i64, i64* %minor_v3711
    %t3815 = call i64 @freak_llvm_word_concat(i64 %t3813, i64 %t3814)
    %t3816 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.244, i64 0, i64 0
    %t3817 = ptrtoint i8* %t3816 to i64
    %t3818 = call i64 @freak_llvm_word_concat(i64 %t3815, i64 %t3817)
    %t3819 = load i64, i64* %patch_v3721
    %t3820 = call i64 @freak_llvm_word_concat(i64 %t3818, i64 %t3819)
    %t3821 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.245, i64 0, i64 0
    %t3822 = ptrtoint i8* %t3821 to i64
    %t3823 = call i64 @freak_llvm_word_concat(i64 %t3820, i64 %t3822)
    %t3824 = load i64, i64* %pre_v3727
    %t3825 = call i64 @freak_llvm_word_concat(i64 %t3823, i64 %t3824)
    %t3826 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.246, i64 0, i64 0
    %t3827 = ptrtoint i8* %t3826 to i64
    %t3828 = call i64 @freak_llvm_word_concat(i64 %t3825, i64 %t3827)
    %t3829 = load i64, i64* %bld_v3730
    %t3830 = call i64 @freak_llvm_word_concat(i64 %t3828, i64 %t3829)
    ret i64 %t3830
    ret i64 0
}

define i64 @freak_ver_field(i64 %arg_parsed, i64 %arg_field_idx) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %field_idx = alloca i64
    store i64 %arg_field_idx, i64* %field_idx
    %t3831 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.247, i64 0, i64 0
    %t3832 = ptrtoint i8* %t3831 to i64
    %res_v3833 = alloca i64
    store i64 %t3832, i64* %res_v3833
    %current_field_v3834 = alloca i64
    store i64 0, i64* %current_field_v3834
    store i64 0, i64* @g_i
    %t3835 = load i64, i64* %parsed
    %t3836 = call i64 @freak_llvm_word_length(i64 %t3835)
    %plen_v3837 = alloca i64
    store i64 %t3836, i64* %plen_v3837
    br label %loop.cond.3838
loop.cond.3838:
    %t3841 = load i64, i64* @g_i
    %t3842 = load i64, i64* %plen_v3837
    %t3844 = icmp sge i64 %t3841, %t3842
    %t3843 = zext i1 %t3844 to i64
    %t3845 = icmp eq i64 %t3843, 0
    br i1 %t3845, label %loop.body.3839, label %loop.end.3840
loop.body.3839:
    %t3846 = load i64, i64* %parsed
    %t3848 = load i64, i64* @g_i
    %t3847 = call i64 @freak_llvm_word_char_at(i64 %t3846, i64 %t3848)
    %c_v3849 = alloca i64
    store i64 %t3847, i64* %c_v3849
    %t3850 = load i64, i64* %c_v3849
    %t3851 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.248, i64 0, i64 0
    %t3852 = ptrtoint i8* %t3851 to i64
    %t3853 = call i64 @freak_llvm_word_eq(i64 %t3850, i64 %t3852)
    %t3857 = icmp ne i64 %t3853, 0
    br i1 %t3857, label %if.then.3854, label %if.else.3855
if.then.3854:
    %t3858 = load i64, i64* %current_field_v3834
    %t3859 = load i64, i64* %field_idx
    %t3861 = icmp eq i64 %t3858, %t3859
    %t3860 = zext i1 %t3861 to i64
    %t3865 = icmp ne i64 %t3860, 0
    br i1 %t3865, label %if.then.3862, label %if.end.3864
if.then.3862:
    %t3866 = load i64, i64* %res_v3833
    ret i64 %t3866
    br label %if.end.3864
if.end.3864:
    %t3867 = load i64, i64* %current_field_v3834
    %t3868 = add i64 %t3867, 1
    store i64 %t3868, i64* %current_field_v3834
    %t3869 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.249, i64 0, i64 0
    %t3870 = ptrtoint i8* %t3869 to i64
    store i64 %t3870, i64* %res_v3833
    br label %if.end.3856
if.else.3855:
    %t3871 = load i64, i64* %res_v3833
    %t3872 = load i64, i64* %c_v3849
    %t3873 = call i64 @freak_llvm_word_concat(i64 %t3871, i64 %t3872)
    store i64 %t3873, i64* %res_v3833
    br label %if.end.3856
if.end.3856:
    %t3874 = load i64, i64* @g_i
    %t3875 = add i64 %t3874, 1
    store i64 %t3875, i64* @g_i
    br label %loop.cond.3838
loop.end.3840:
    %t3876 = load i64, i64* %current_field_v3834
    %t3877 = load i64, i64* %field_idx
    %t3879 = icmp eq i64 %t3876, %t3877
    %t3878 = zext i1 %t3879 to i64
    %t3883 = icmp ne i64 %t3878, 0
    br i1 %t3883, label %if.then.3880, label %if.end.3882
if.then.3880:
    %t3884 = load i64, i64* %res_v3833
    ret i64 %t3884
    br label %if.end.3882
if.end.3882:
    %t3885 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.250, i64 0, i64 0
    %t3886 = ptrtoint i8* %t3885 to i64
    ret i64 %t3886
    ret i64 0
}

define i64 @freak_ver_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3887 = load i64, i64* %parsed
    %t3888 = call i64 @freak_ver_field(i64 %t3887, i64 0)
    %t3889 = call i64 @freak_llvm_word_to_int(i64 %t3888)
    ret i64 %t3889
    ret i64 0
}

define i64 @freak_ver_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3890 = load i64, i64* %parsed
    %t3891 = call i64 @freak_ver_field(i64 %t3890, i64 1)
    %t3892 = call i64 @freak_llvm_word_to_int(i64 %t3891)
    ret i64 %t3892
    ret i64 0
}

define i64 @freak_ver_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3893 = load i64, i64* %parsed
    %t3894 = call i64 @freak_ver_field(i64 %t3893, i64 2)
    %t3895 = call i64 @freak_llvm_word_to_int(i64 %t3894)
    ret i64 %t3895
    ret i64 0
}

define i64 @freak_ver_pre(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3896 = load i64, i64* %parsed
    %t3897 = call i64 @freak_ver_field(i64 %t3896, i64 3)
    ret i64 %t3897
    ret i64 0
}

define i64 @freak_ver_build(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3898 = load i64, i64* %parsed
    %t3899 = call i64 @freak_ver_field(i64 %t3898, i64 4)
    ret i64 %t3899
    ret i64 0
}

define i64 @freak_ver_to_string(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t3900 = load i64, i64* %parsed
    %t3901 = call i64 @freak_ver_field(i64 %t3900, i64 0)
    %maj_v3902 = alloca i64
    store i64 %t3901, i64* %maj_v3902
    %t3903 = load i64, i64* %parsed
    %t3904 = call i64 @freak_ver_field(i64 %t3903, i64 1)
    %min_v3905 = alloca i64
    store i64 %t3904, i64* %min_v3905
    %t3906 = load i64, i64* %parsed
    %t3907 = call i64 @freak_ver_field(i64 %t3906, i64 2)
    %pat_v3908 = alloca i64
    store i64 %t3907, i64* %pat_v3908
    %t3909 = load i64, i64* %parsed
    %t3910 = call i64 @freak_ver_field(i64 %t3909, i64 3)
    %pre_v3911 = alloca i64
    store i64 %t3910, i64* %pre_v3911
    %t3912 = load i64, i64* %parsed
    %t3913 = call i64 @freak_ver_field(i64 %t3912, i64 4)
    %bld_v3914 = alloca i64
    store i64 %t3913, i64* %bld_v3914
    %t3915 = load i64, i64* %maj_v3902
    %t3916 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.251, i64 0, i64 0
    %t3917 = ptrtoint i8* %t3916 to i64
    %t3918 = call i64 @freak_llvm_word_concat(i64 %t3915, i64 %t3917)
    %t3919 = load i64, i64* %min_v3905
    %t3920 = call i64 @freak_llvm_word_concat(i64 %t3918, i64 %t3919)
    %t3921 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.252, i64 0, i64 0
    %t3922 = ptrtoint i8* %t3921 to i64
    %t3923 = call i64 @freak_llvm_word_concat(i64 %t3920, i64 %t3922)
    %t3924 = load i64, i64* %pat_v3908
    %t3925 = call i64 @freak_llvm_word_concat(i64 %t3923, i64 %t3924)
    %out_v3926 = alloca i64
    store i64 %t3925, i64* %out_v3926
    %t3927 = load i64, i64* %pre_v3911
    %t3928 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.253, i64 0, i64 0
    %t3929 = ptrtoint i8* %t3928 to i64
    %t3930 = call i64 @freak_llvm_word_neq(i64 %t3927, i64 %t3929)
    %t3934 = icmp ne i64 %t3930, 0
    br i1 %t3934, label %if.then.3931, label %if.end.3933
if.then.3931:
    %t3935 = load i64, i64* %out_v3926
    %t3936 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.254, i64 0, i64 0
    %t3937 = ptrtoint i8* %t3936 to i64
    %t3938 = call i64 @freak_llvm_word_concat(i64 %t3935, i64 %t3937)
    %t3939 = load i64, i64* %pre_v3911
    %t3940 = call i64 @freak_llvm_word_concat(i64 %t3938, i64 %t3939)
    store i64 %t3940, i64* %out_v3926
    br label %if.end.3933
if.end.3933:
    %t3941 = load i64, i64* %bld_v3914
    %t3942 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.255, i64 0, i64 0
    %t3943 = ptrtoint i8* %t3942 to i64
    %t3944 = call i64 @freak_llvm_word_neq(i64 %t3941, i64 %t3943)
    %t3948 = icmp ne i64 %t3944, 0
    br i1 %t3948, label %if.then.3945, label %if.end.3947
if.then.3945:
    %t3949 = load i64, i64* %out_v3926
    %t3950 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.256, i64 0, i64 0
    %t3951 = ptrtoint i8* %t3950 to i64
    %t3952 = call i64 @freak_llvm_word_concat(i64 %t3949, i64 %t3951)
    %t3953 = load i64, i64* %bld_v3914
    %t3954 = call i64 @freak_llvm_word_concat(i64 %t3952, i64 %t3953)
    store i64 %t3954, i64* %out_v3926
    br label %if.end.3947
if.end.3947:
    %t3955 = load i64, i64* %out_v3926
    ret i64 %t3955
    ret i64 0
}

define i64 @freak_ver_compare(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t3956 = load i64, i64* %a
    %t3957 = call i64 @freak_ver_major(i64 %t3956)
    %a_major_v3958 = alloca i64
    store i64 %t3957, i64* %a_major_v3958
    %t3959 = load i64, i64* %b
    %t3960 = call i64 @freak_ver_major(i64 %t3959)
    %b_major_v3961 = alloca i64
    store i64 %t3960, i64* %b_major_v3961
    %t3962 = load i64, i64* %a_major_v3958
    %t3963 = load i64, i64* %b_major_v3961
    %t3965 = icmp slt i64 %t3962, %t3963
    %t3964 = zext i1 %t3965 to i64
    %t3969 = icmp ne i64 %t3964, 0
    br i1 %t3969, label %if.then.3966, label %if.end.3968
if.then.3966:
    %t3970 = sub i64 0, 1
    ret i64 %t3970
    br label %if.end.3968
if.end.3968:
    %t3971 = load i64, i64* %a_major_v3958
    %t3972 = load i64, i64* %b_major_v3961
    %t3974 = icmp sgt i64 %t3971, %t3972
    %t3973 = zext i1 %t3974 to i64
    %t3978 = icmp ne i64 %t3973, 0
    br i1 %t3978, label %if.then.3975, label %if.end.3977
if.then.3975:
    ret i64 1
    br label %if.end.3977
if.end.3977:
    %t3979 = load i64, i64* %a
    %t3980 = call i64 @freak_ver_minor(i64 %t3979)
    %a_minor_v3981 = alloca i64
    store i64 %t3980, i64* %a_minor_v3981
    %t3982 = load i64, i64* %b
    %t3983 = call i64 @freak_ver_minor(i64 %t3982)
    %b_minor_v3984 = alloca i64
    store i64 %t3983, i64* %b_minor_v3984
    %t3985 = load i64, i64* %a_minor_v3981
    %t3986 = load i64, i64* %b_minor_v3984
    %t3988 = icmp slt i64 %t3985, %t3986
    %t3987 = zext i1 %t3988 to i64
    %t3992 = icmp ne i64 %t3987, 0
    br i1 %t3992, label %if.then.3989, label %if.end.3991
if.then.3989:
    %t3993 = sub i64 0, 1
    ret i64 %t3993
    br label %if.end.3991
if.end.3991:
    %t3994 = load i64, i64* %a_minor_v3981
    %t3995 = load i64, i64* %b_minor_v3984
    %t3997 = icmp sgt i64 %t3994, %t3995
    %t3996 = zext i1 %t3997 to i64
    %t4001 = icmp ne i64 %t3996, 0
    br i1 %t4001, label %if.then.3998, label %if.end.4000
if.then.3998:
    ret i64 1
    br label %if.end.4000
if.end.4000:
    %t4002 = load i64, i64* %a
    %t4003 = call i64 @freak_ver_patch(i64 %t4002)
    %a_patch_v4004 = alloca i64
    store i64 %t4003, i64* %a_patch_v4004
    %t4005 = load i64, i64* %b
    %t4006 = call i64 @freak_ver_patch(i64 %t4005)
    %b_patch_v4007 = alloca i64
    store i64 %t4006, i64* %b_patch_v4007
    %t4008 = load i64, i64* %a_patch_v4004
    %t4009 = load i64, i64* %b_patch_v4007
    %t4011 = icmp slt i64 %t4008, %t4009
    %t4010 = zext i1 %t4011 to i64
    %t4015 = icmp ne i64 %t4010, 0
    br i1 %t4015, label %if.then.4012, label %if.end.4014
if.then.4012:
    %t4016 = sub i64 0, 1
    ret i64 %t4016
    br label %if.end.4014
if.end.4014:
    %t4017 = load i64, i64* %a_patch_v4004
    %t4018 = load i64, i64* %b_patch_v4007
    %t4020 = icmp sgt i64 %t4017, %t4018
    %t4019 = zext i1 %t4020 to i64
    %t4024 = icmp ne i64 %t4019, 0
    br i1 %t4024, label %if.then.4021, label %if.end.4023
if.then.4021:
    ret i64 1
    br label %if.end.4023
if.end.4023:
    %t4025 = load i64, i64* %a
    %t4026 = call i64 @freak_ver_pre(i64 %t4025)
    %a_pre_v4027 = alloca i64
    store i64 %t4026, i64* %a_pre_v4027
    %t4028 = load i64, i64* %b
    %t4029 = call i64 @freak_ver_pre(i64 %t4028)
    %b_pre_v4030 = alloca i64
    store i64 %t4029, i64* %b_pre_v4030
    %t4031 = load i64, i64* %a_pre_v4027
    %t4032 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.257, i64 0, i64 0
    %t4033 = ptrtoint i8* %t4032 to i64
    %t4034 = call i64 @freak_llvm_word_eq(i64 %t4031, i64 %t4033)
    %t4035 = load i64, i64* %b_pre_v4030
    %t4036 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.258, i64 0, i64 0
    %t4037 = ptrtoint i8* %t4036 to i64
    %t4038 = call i64 @freak_llvm_word_neq(i64 %t4035, i64 %t4037)
    %t4040 = icmp ne i64 %t4034, 0
    %t4041 = icmp ne i64 %t4038, 0
    %t4042 = and i1 %t4040, %t4041
    %t4039 = zext i1 %t4042 to i64
    %t4046 = icmp ne i64 %t4039, 0
    br i1 %t4046, label %if.then.4043, label %if.end.4045
if.then.4043:
    ret i64 1
    br label %if.end.4045
if.end.4045:
    %t4047 = load i64, i64* %a_pre_v4027
    %t4048 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.259, i64 0, i64 0
    %t4049 = ptrtoint i8* %t4048 to i64
    %t4050 = call i64 @freak_llvm_word_neq(i64 %t4047, i64 %t4049)
    %t4051 = load i64, i64* %b_pre_v4030
    %t4052 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.260, i64 0, i64 0
    %t4053 = ptrtoint i8* %t4052 to i64
    %t4054 = call i64 @freak_llvm_word_eq(i64 %t4051, i64 %t4053)
    %t4056 = icmp ne i64 %t4050, 0
    %t4057 = icmp ne i64 %t4054, 0
    %t4058 = and i1 %t4056, %t4057
    %t4055 = zext i1 %t4058 to i64
    %t4062 = icmp ne i64 %t4055, 0
    br i1 %t4062, label %if.then.4059, label %if.end.4061
if.then.4059:
    %t4063 = sub i64 0, 1
    ret i64 %t4063
    br label %if.end.4061
if.end.4061:
    %t4064 = load i64, i64* %a_pre_v4027
    %t4065 = call i64 @freak_llvm_word_length(i64 %t4064)
    %cmp_len_v4066 = alloca i64
    store i64 %t4065, i64* %cmp_len_v4066
    %t4067 = load i64, i64* %b_pre_v4030
    %t4068 = call i64 @freak_llvm_word_length(i64 %t4067)
    %t4069 = load i64, i64* %cmp_len_v4066
    %t4071 = icmp slt i64 %t4068, %t4069
    %t4070 = zext i1 %t4071 to i64
    %t4075 = icmp ne i64 %t4070, 0
    br i1 %t4075, label %if.then.4072, label %if.end.4074
if.then.4072:
    %t4076 = load i64, i64* %b_pre_v4030
    %t4077 = call i64 @freak_llvm_word_length(i64 %t4076)
    store i64 %t4077, i64* %cmp_len_v4066
    br label %if.end.4074
if.end.4074:
    %ci_v4078 = alloca i64
    store i64 0, i64* %ci_v4078
    br label %loop.cond.4079
loop.cond.4079:
    %t4082 = load i64, i64* %ci_v4078
    %t4083 = load i64, i64* %cmp_len_v4066
    %t4085 = icmp sge i64 %t4082, %t4083
    %t4084 = zext i1 %t4085 to i64
    %t4086 = icmp eq i64 %t4084, 0
    br i1 %t4086, label %loop.body.4080, label %loop.end.4081
loop.body.4080:
    %t4087 = load i64, i64* %a_pre_v4027
    %t4089 = load i64, i64* %ci_v4078
    %t4088 = call i64 @freak_llvm_word_char_at(i64 %t4087, i64 %t4089)
    %ac_v4090 = alloca i64
    store i64 %t4088, i64* %ac_v4090
    %t4091 = load i64, i64* %b_pre_v4030
    %t4093 = load i64, i64* %ci_v4078
    %t4092 = call i64 @freak_llvm_word_char_at(i64 %t4091, i64 %t4093)
    %bc_v4094 = alloca i64
    store i64 %t4092, i64* %bc_v4094
    %t4095 = load i64, i64* %ac_v4090
    %t4096 = load i64, i64* %bc_v4094
    %t4097 = call i64 @freak_llvm_word_neq(i64 %t4095, i64 %t4096)
    %t4101 = icmp ne i64 %t4097, 0
    br i1 %t4101, label %if.then.4098, label %if.end.4100
if.then.4098:
    %t4102 = load i64, i64* %ac_v4090
    %t4103 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.261, i64 0, i64 0
    %t4104 = ptrtoint i8* %t4103 to i64
    %t4105 = call i64 @freak_llvm_word_eq(i64 %t4102, i64 %t4104)
    %t4106 = load i64, i64* %bc_v4094
    %t4107 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.262, i64 0, i64 0
    %t4108 = ptrtoint i8* %t4107 to i64
    %t4109 = call i64 @freak_llvm_word_eq(i64 %t4106, i64 %t4108)
    %t4111 = icmp ne i64 %t4105, 0
    %t4112 = icmp ne i64 %t4109, 0
    %t4113 = and i1 %t4111, %t4112
    %t4110 = zext i1 %t4113 to i64
    %t4117 = icmp ne i64 %t4110, 0
    br i1 %t4117, label %if.then.4114, label %if.end.4116
if.then.4114:
    %t4118 = sub i64 0, 1
    ret i64 %t4118
    br label %if.end.4116
if.end.4116:
    %t4119 = load i64, i64* %ac_v4090
    %t4120 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.263, i64 0, i64 0
    %t4121 = ptrtoint i8* %t4120 to i64
    %t4122 = call i64 @freak_llvm_word_eq(i64 %t4119, i64 %t4121)
    %t4123 = load i64, i64* %bc_v4094
    %t4124 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.264, i64 0, i64 0
    %t4125 = ptrtoint i8* %t4124 to i64
    %t4126 = call i64 @freak_llvm_word_eq(i64 %t4123, i64 %t4125)
    %t4128 = icmp ne i64 %t4122, 0
    %t4129 = icmp ne i64 %t4126, 0
    %t4130 = and i1 %t4128, %t4129
    %t4127 = zext i1 %t4130 to i64
    %t4134 = icmp ne i64 %t4127, 0
    br i1 %t4134, label %if.then.4131, label %if.end.4133
if.then.4131:
    ret i64 1
    br label %if.end.4133
if.end.4133:
    %t4135 = load i64, i64* %ac_v4090
    %t4136 = call i64 @freak_llvm_word_to_int(i64 %t4135)
    %ai_v4137 = alloca i64
    store i64 %t4136, i64* %ai_v4137
    %t4138 = load i64, i64* %bc_v4094
    %t4139 = call i64 @freak_llvm_word_to_int(i64 %t4138)
    %bi_v4140 = alloca i64
    store i64 %t4139, i64* %bi_v4140
    %t4141 = load i64, i64* %ai_v4137
    %t4142 = load i64, i64* %bi_v4140
    %t4144 = icmp slt i64 %t4141, %t4142
    %t4143 = zext i1 %t4144 to i64
    %t4148 = icmp ne i64 %t4143, 0
    br i1 %t4148, label %if.then.4145, label %if.end.4147
if.then.4145:
    %t4149 = sub i64 0, 1
    ret i64 %t4149
    br label %if.end.4147
if.end.4147:
    %t4150 = load i64, i64* %ai_v4137
    %t4151 = load i64, i64* %bi_v4140
    %t4153 = icmp sgt i64 %t4150, %t4151
    %t4152 = zext i1 %t4153 to i64
    %t4157 = icmp ne i64 %t4152, 0
    br i1 %t4157, label %if.then.4154, label %if.end.4156
if.then.4154:
    ret i64 1
    br label %if.end.4156
if.end.4156:
    br label %if.end.4100
if.end.4100:
    %t4158 = load i64, i64* %ci_v4078
    %t4159 = add i64 %t4158, 1
    store i64 %t4159, i64* %ci_v4078
    br label %loop.cond.4079
loop.end.4081:
    %t4160 = load i64, i64* %a_pre_v4027
    %t4161 = call i64 @freak_llvm_word_length(i64 %t4160)
    %t4162 = load i64, i64* %b_pre_v4030
    %t4163 = call i64 @freak_llvm_word_length(i64 %t4162)
    %t4165 = icmp slt i64 %t4161, %t4163
    %t4164 = zext i1 %t4165 to i64
    %t4169 = icmp ne i64 %t4164, 0
    br i1 %t4169, label %if.then.4166, label %if.end.4168
if.then.4166:
    %t4170 = sub i64 0, 1
    ret i64 %t4170
    br label %if.end.4168
if.end.4168:
    %t4171 = load i64, i64* %a_pre_v4027
    %t4172 = call i64 @freak_llvm_word_length(i64 %t4171)
    %t4173 = load i64, i64* %b_pre_v4030
    %t4174 = call i64 @freak_llvm_word_length(i64 %t4173)
    %t4176 = icmp sgt i64 %t4172, %t4174
    %t4175 = zext i1 %t4176 to i64
    %t4180 = icmp ne i64 %t4175, 0
    br i1 %t4180, label %if.then.4177, label %if.end.4179
if.then.4177:
    ret i64 1
    br label %if.end.4179
if.end.4179:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_eq(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4181 = load i64, i64* %a
    %t4182 = load i64, i64* %b
    %t4183 = call i64 @freak_ver_compare(i64 %t4181, i64 %t4182)
    %t4185 = icmp eq i64 %t4183, 0
    %t4184 = zext i1 %t4185 to i64
    ret i64 %t4184
    ret i64 0
}

define i64 @freak_ver_lt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4186 = load i64, i64* %a
    %t4187 = load i64, i64* %b
    %t4188 = call i64 @freak_ver_compare(i64 %t4186, i64 %t4187)
    %t4190 = icmp slt i64 %t4188, 0
    %t4189 = zext i1 %t4190 to i64
    ret i64 %t4189
    ret i64 0
}

define i64 @freak_ver_gt(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4191 = load i64, i64* %a
    %t4192 = load i64, i64* %b
    %t4193 = call i64 @freak_ver_compare(i64 %t4191, i64 %t4192)
    %t4195 = icmp sgt i64 %t4193, 0
    %t4194 = zext i1 %t4195 to i64
    ret i64 %t4194
    ret i64 0
}

define i64 @freak_ver_lte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4196 = load i64, i64* %a
    %t4197 = load i64, i64* %b
    %t4198 = call i64 @freak_ver_compare(i64 %t4196, i64 %t4197)
    %t4200 = icmp sle i64 %t4198, 0
    %t4199 = zext i1 %t4200 to i64
    ret i64 %t4199
    ret i64 0
}

define i64 @freak_ver_gte(i64 %arg_a, i64 %arg_b) {
entry:
    %a = alloca i64
    store i64 %arg_a, i64* %a
    %b = alloca i64
    store i64 %arg_b, i64* %b
    %t4201 = load i64, i64* %a
    %t4202 = load i64, i64* %b
    %t4203 = call i64 @freak_ver_compare(i64 %t4201, i64 %t4202)
    %t4205 = icmp sge i64 %t4203, 0
    %t4204 = zext i1 %t4205 to i64
    ret i64 %t4204
    ret i64 0
}

define i64 @freak_ver_bump_major(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4206 = load i64, i64* %parsed
    %t4207 = call i64 @freak_ver_major(i64 %t4206)
    %t4208 = add i64 %t4207, 1
    %maj_v4209 = alloca i64
    store i64 %t4208, i64* %maj_v4209
    %t4210 = load i64, i64* %maj_v4209
    %t4211 = call i64 @freak_llvm_word_from_int(i64 %t4210)
    %t4212 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.265, i64 0, i64 0
    %t4213 = ptrtoint i8* %t4212 to i64
    %t4214 = call i64 @freak_llvm_word_concat(i64 %t4211, i64 %t4213)
    ret i64 %t4214
    ret i64 0
}

define i64 @freak_ver_bump_minor(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4215 = load i64, i64* %parsed
    %t4216 = call i64 @freak_ver_major(i64 %t4215)
    %maj_v4217 = alloca i64
    store i64 %t4216, i64* %maj_v4217
    %t4218 = load i64, i64* %parsed
    %t4219 = call i64 @freak_ver_minor(i64 %t4218)
    %t4220 = add i64 %t4219, 1
    %min_v4221 = alloca i64
    store i64 %t4220, i64* %min_v4221
    %t4222 = load i64, i64* %maj_v4217
    %t4223 = call i64 @freak_llvm_word_from_int(i64 %t4222)
    %t4224 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.266, i64 0, i64 0
    %t4225 = ptrtoint i8* %t4224 to i64
    %t4226 = call i64 @freak_llvm_word_concat(i64 %t4223, i64 %t4225)
    %t4227 = load i64, i64* %min_v4221
    %t4228 = call i64 @freak_llvm_word_from_int(i64 %t4227)
    %t4229 = call i64 @freak_llvm_word_concat(i64 %t4226, i64 %t4228)
    %t4230 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.267, i64 0, i64 0
    %t4231 = ptrtoint i8* %t4230 to i64
    %t4232 = call i64 @freak_llvm_word_concat(i64 %t4229, i64 %t4231)
    ret i64 %t4232
    ret i64 0
}

define i64 @freak_ver_bump_patch(i64 %arg_parsed) {
entry:
    %parsed = alloca i64
    store i64 %arg_parsed, i64* %parsed
    %t4233 = load i64, i64* %parsed
    %t4234 = call i64 @freak_ver_major(i64 %t4233)
    %maj_v4235 = alloca i64
    store i64 %t4234, i64* %maj_v4235
    %t4236 = load i64, i64* %parsed
    %t4237 = call i64 @freak_ver_minor(i64 %t4236)
    %min_v4238 = alloca i64
    store i64 %t4237, i64* %min_v4238
    %t4239 = load i64, i64* %parsed
    %t4240 = call i64 @freak_ver_patch(i64 %t4239)
    %t4241 = add i64 %t4240, 1
    %pat_v4242 = alloca i64
    store i64 %t4241, i64* %pat_v4242
    %t4243 = load i64, i64* %maj_v4235
    %t4244 = call i64 @freak_llvm_word_from_int(i64 %t4243)
    %t4245 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.268, i64 0, i64 0
    %t4246 = ptrtoint i8* %t4245 to i64
    %t4247 = call i64 @freak_llvm_word_concat(i64 %t4244, i64 %t4246)
    %t4248 = load i64, i64* %min_v4238
    %t4249 = call i64 @freak_llvm_word_from_int(i64 %t4248)
    %t4250 = call i64 @freak_llvm_word_concat(i64 %t4247, i64 %t4249)
    %t4251 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.269, i64 0, i64 0
    %t4252 = ptrtoint i8* %t4251 to i64
    %t4253 = call i64 @freak_llvm_word_concat(i64 %t4250, i64 %t4252)
    %t4254 = load i64, i64* %pat_v4242
    %t4255 = call i64 @freak_llvm_word_from_int(i64 %t4254)
    %t4256 = call i64 @freak_llvm_word_concat(i64 %t4253, i64 %t4255)
    %t4257 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.270, i64 0, i64 0
    %t4258 = ptrtoint i8* %t4257 to i64
    %t4259 = call i64 @freak_llvm_word_concat(i64 %t4256, i64 %t4258)
    ret i64 %t4259
    ret i64 0
}

define i64 @freak_ver_strip_prefix(i64 %arg_constraint, i64 %arg_prefix_len) {
entry:
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %prefix_len = alloca i64
    store i64 %arg_prefix_len, i64* %prefix_len
    %t4260 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.271, i64 0, i64 0
    %t4261 = ptrtoint i8* %t4260 to i64
    %stripped_v4262 = alloca i64
    store i64 %t4261, i64* %stripped_v4262
    %t4263 = load i64, i64* %prefix_len
    %si_v4264 = alloca i64
    store i64 %t4263, i64* %si_v4264
    br label %loop.cond.4265
loop.cond.4265:
    %t4268 = load i64, i64* %si_v4264
    %t4269 = load i64, i64* %constraint
    %t4270 = call i64 @freak_llvm_word_length(i64 %t4269)
    %t4272 = icmp sge i64 %t4268, %t4270
    %t4271 = zext i1 %t4272 to i64
    %t4273 = icmp eq i64 %t4271, 0
    br i1 %t4273, label %loop.body.4266, label %loop.end.4267
loop.body.4266:
    %t4274 = load i64, i64* %stripped_v4262
    %t4275 = load i64, i64* %constraint
    %t4277 = load i64, i64* %si_v4264
    %t4276 = call i64 @freak_llvm_word_char_at(i64 %t4275, i64 %t4277)
    %t4278 = call i64 @freak_llvm_word_concat(i64 %t4274, i64 %t4276)
    store i64 %t4278, i64* %stripped_v4262
    %t4279 = load i64, i64* %si_v4264
    %t4280 = add i64 %t4279, 1
    store i64 %t4280, i64* %si_v4264
    br label %loop.cond.4265
loop.end.4267:
    %t4281 = load i64, i64* %stripped_v4262
    ret i64 %t4281
    ret i64 0
}

define i64 @freak_ver_is_digit(i64 %arg_c) {
entry:
    %c = alloca i64
    store i64 %arg_c, i64* %c
    %t4282 = load i64, i64* %c
    %t4283 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.272, i64 0, i64 0
    %t4284 = ptrtoint i8* %t4283 to i64
    %t4285 = call i64 @freak_llvm_word_eq(i64 %t4282, i64 %t4284)
    %t4289 = icmp ne i64 %t4285, 0
    br i1 %t4289, label %if.then.4286, label %if.end.4288
if.then.4286:
    ret i64 1
    br label %if.end.4288
if.end.4288:
    %t4290 = load i64, i64* %c
    %t4291 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.273, i64 0, i64 0
    %t4292 = ptrtoint i8* %t4291 to i64
    %t4293 = call i64 @freak_llvm_word_eq(i64 %t4290, i64 %t4292)
    %t4297 = icmp ne i64 %t4293, 0
    br i1 %t4297, label %if.then.4294, label %if.end.4296
if.then.4294:
    ret i64 1
    br label %if.end.4296
if.end.4296:
    %t4298 = load i64, i64* %c
    %t4299 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.274, i64 0, i64 0
    %t4300 = ptrtoint i8* %t4299 to i64
    %t4301 = call i64 @freak_llvm_word_eq(i64 %t4298, i64 %t4300)
    %t4305 = icmp ne i64 %t4301, 0
    br i1 %t4305, label %if.then.4302, label %if.end.4304
if.then.4302:
    ret i64 1
    br label %if.end.4304
if.end.4304:
    %t4306 = load i64, i64* %c
    %t4307 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.275, i64 0, i64 0
    %t4308 = ptrtoint i8* %t4307 to i64
    %t4309 = call i64 @freak_llvm_word_eq(i64 %t4306, i64 %t4308)
    %t4313 = icmp ne i64 %t4309, 0
    br i1 %t4313, label %if.then.4310, label %if.end.4312
if.then.4310:
    ret i64 1
    br label %if.end.4312
if.end.4312:
    %t4314 = load i64, i64* %c
    %t4315 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.276, i64 0, i64 0
    %t4316 = ptrtoint i8* %t4315 to i64
    %t4317 = call i64 @freak_llvm_word_eq(i64 %t4314, i64 %t4316)
    %t4321 = icmp ne i64 %t4317, 0
    br i1 %t4321, label %if.then.4318, label %if.end.4320
if.then.4318:
    ret i64 1
    br label %if.end.4320
if.end.4320:
    %t4322 = load i64, i64* %c
    %t4323 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.277, i64 0, i64 0
    %t4324 = ptrtoint i8* %t4323 to i64
    %t4325 = call i64 @freak_llvm_word_eq(i64 %t4322, i64 %t4324)
    %t4329 = icmp ne i64 %t4325, 0
    br i1 %t4329, label %if.then.4326, label %if.end.4328
if.then.4326:
    ret i64 1
    br label %if.end.4328
if.end.4328:
    %t4330 = load i64, i64* %c
    %t4331 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.278, i64 0, i64 0
    %t4332 = ptrtoint i8* %t4331 to i64
    %t4333 = call i64 @freak_llvm_word_eq(i64 %t4330, i64 %t4332)
    %t4337 = icmp ne i64 %t4333, 0
    br i1 %t4337, label %if.then.4334, label %if.end.4336
if.then.4334:
    ret i64 1
    br label %if.end.4336
if.end.4336:
    %t4338 = load i64, i64* %c
    %t4339 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.279, i64 0, i64 0
    %t4340 = ptrtoint i8* %t4339 to i64
    %t4341 = call i64 @freak_llvm_word_eq(i64 %t4338, i64 %t4340)
    %t4345 = icmp ne i64 %t4341, 0
    br i1 %t4345, label %if.then.4342, label %if.end.4344
if.then.4342:
    ret i64 1
    br label %if.end.4344
if.end.4344:
    %t4346 = load i64, i64* %c
    %t4347 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.280, i64 0, i64 0
    %t4348 = ptrtoint i8* %t4347 to i64
    %t4349 = call i64 @freak_llvm_word_eq(i64 %t4346, i64 %t4348)
    %t4353 = icmp ne i64 %t4349, 0
    br i1 %t4353, label %if.then.4350, label %if.end.4352
if.then.4350:
    ret i64 1
    br label %if.end.4352
if.end.4352:
    %t4354 = load i64, i64* %c
    %t4355 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.281, i64 0, i64 0
    %t4356 = ptrtoint i8* %t4355 to i64
    %t4357 = call i64 @freak_llvm_word_eq(i64 %t4354, i64 %t4356)
    %t4361 = icmp ne i64 %t4357, 0
    br i1 %t4361, label %if.then.4358, label %if.end.4360
if.then.4358:
    ret i64 1
    br label %if.end.4360
if.end.4360:
    ret i64 0
    ret i64 0
}

define i64 @freak_ver_satisfies_single(i64 %arg_v, i64 %arg_constraint) {
entry:
    %v = alloca i64
    store i64 %arg_v, i64* %v
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4362 = load i64, i64* %constraint
    %t4363 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.282, i64 0, i64 0
    %t4364 = ptrtoint i8* %t4363 to i64
    %t4365 = call i64 @freak_llvm_word_eq(i64 %t4362, i64 %t4364)
    %t4366 = load i64, i64* %constraint
    %t4367 = getelementptr inbounds [7 x i8], [7 x i8]* @.str.283, i64 0, i64 0
    %t4368 = ptrtoint i8* %t4367 to i64
    %t4369 = call i64 @freak_llvm_word_eq(i64 %t4366, i64 %t4368)
    %t4371 = icmp ne i64 %t4365, 0
    %t4372 = icmp ne i64 %t4369, 0
    %t4373 = or i1 %t4371, %t4372
    %t4370 = zext i1 %t4373 to i64
    %t4377 = icmp ne i64 %t4370, 0
    br i1 %t4377, label %if.then.4374, label %if.end.4376
if.then.4374:
    ret i64 1
    br label %if.end.4376
if.end.4376:
    %t4378 = load i64, i64* %constraint
    %t4380 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.284, i64 0, i64 0
    %t4381 = ptrtoint i8* %t4380 to i64
    %t4379 = call i64 @freak_llvm_word_starts_with(i64 %t4378, i64 %t4381)
    %t4385 = icmp ne i64 %t4379, 0
    br i1 %t4385, label %if.then.4382, label %if.end.4384
if.then.4382:
    %t4386 = load i64, i64* %constraint
    %t4387 = call i64 @freak_ver_strip_prefix(i64 %t4386, i64 1)
    %t4388 = call i64 @freak_ver_parse(i64 %t4387)
    %c_v4389 = alloca i64
    store i64 %t4388, i64* %c_v4389
    %t4390 = load i64, i64* %v
    %t4391 = call i64 @freak_ver_major(i64 %t4390)
    %t4392 = load i64, i64* %c_v4389
    %t4393 = call i64 @freak_ver_major(i64 %t4392)
    %t4395 = icmp ne i64 %t4391, %t4393
    %t4394 = zext i1 %t4395 to i64
    %t4399 = icmp ne i64 %t4394, 0
    br i1 %t4399, label %if.then.4396, label %if.end.4398
if.then.4396:
    ret i64 0
    br label %if.end.4398
if.end.4398:
    %t4400 = load i64, i64* %v
    %t4401 = load i64, i64* %c_v4389
    %t4402 = call i64 @freak_ver_gte(i64 %t4400, i64 %t4401)
    ret i64 %t4402
    br label %if.end.4384
if.end.4384:
    %t4403 = load i64, i64* %constraint
    %t4405 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.285, i64 0, i64 0
    %t4406 = ptrtoint i8* %t4405 to i64
    %t4404 = call i64 @freak_llvm_word_starts_with(i64 %t4403, i64 %t4406)
    %t4410 = icmp ne i64 %t4404, 0
    br i1 %t4410, label %if.then.4407, label %if.end.4409
if.then.4407:
    %t4411 = load i64, i64* %constraint
    %t4412 = call i64 @freak_ver_strip_prefix(i64 %t4411, i64 1)
    %t4413 = call i64 @freak_ver_parse(i64 %t4412)
    %t_v4414 = alloca i64
    store i64 %t4413, i64* %t_v4414
    %t4415 = load i64, i64* %v
    %t4416 = call i64 @freak_ver_major(i64 %t4415)
    %t4417 = load i64, i64* %t_v4414
    %t4418 = call i64 @freak_ver_major(i64 %t4417)
    %t4420 = icmp ne i64 %t4416, %t4418
    %t4419 = zext i1 %t4420 to i64
    %t4424 = icmp ne i64 %t4419, 0
    br i1 %t4424, label %if.then.4421, label %if.end.4423
if.then.4421:
    ret i64 0
    br label %if.end.4423
if.end.4423:
    %t4425 = load i64, i64* %v
    %t4426 = call i64 @freak_ver_minor(i64 %t4425)
    %t4427 = load i64, i64* %t_v4414
    %t4428 = call i64 @freak_ver_minor(i64 %t4427)
    %t4430 = icmp ne i64 %t4426, %t4428
    %t4429 = zext i1 %t4430 to i64
    %t4434 = icmp ne i64 %t4429, 0
    br i1 %t4434, label %if.then.4431, label %if.end.4433
if.then.4431:
    ret i64 0
    br label %if.end.4433
if.end.4433:
    %t4435 = load i64, i64* %v
    %t4436 = load i64, i64* %t_v4414
    %t4437 = call i64 @freak_ver_gte(i64 %t4435, i64 %t4436)
    ret i64 %t4437
    br label %if.end.4409
if.end.4409:
    %t4438 = load i64, i64* %constraint
    %t4440 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.286, i64 0, i64 0
    %t4441 = ptrtoint i8* %t4440 to i64
    %t4439 = call i64 @freak_llvm_word_starts_with(i64 %t4438, i64 %t4441)
    %t4445 = icmp ne i64 %t4439, 0
    br i1 %t4445, label %if.then.4442, label %if.end.4444
if.then.4442:
    %t4446 = load i64, i64* %v
    %t4447 = load i64, i64* %constraint
    %t4448 = call i64 @freak_ver_strip_prefix(i64 %t4447, i64 2)
    %t4449 = call i64 @freak_ver_parse(i64 %t4448)
    %t4450 = call i64 @freak_ver_gte(i64 %t4446, i64 %t4449)
    ret i64 %t4450
    br label %if.end.4444
if.end.4444:
    %t4451 = load i64, i64* %constraint
    %t4453 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.287, i64 0, i64 0
    %t4454 = ptrtoint i8* %t4453 to i64
    %t4452 = call i64 @freak_llvm_word_starts_with(i64 %t4451, i64 %t4454)
    %t4458 = icmp ne i64 %t4452, 0
    br i1 %t4458, label %if.then.4455, label %if.end.4457
if.then.4455:
    %t4459 = load i64, i64* %v
    %t4460 = load i64, i64* %constraint
    %t4461 = call i64 @freak_ver_strip_prefix(i64 %t4460, i64 2)
    %t4462 = call i64 @freak_ver_parse(i64 %t4461)
    %t4463 = call i64 @freak_ver_lte(i64 %t4459, i64 %t4462)
    ret i64 %t4463
    br label %if.end.4457
if.end.4457:
    %t4464 = load i64, i64* %constraint
    %t4466 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.288, i64 0, i64 0
    %t4467 = ptrtoint i8* %t4466 to i64
    %t4465 = call i64 @freak_llvm_word_starts_with(i64 %t4464, i64 %t4467)
    %t4471 = icmp ne i64 %t4465, 0
    br i1 %t4471, label %if.then.4468, label %if.end.4470
if.then.4468:
    %t4472 = load i64, i64* %v
    %t4473 = load i64, i64* %constraint
    %t4474 = call i64 @freak_ver_strip_prefix(i64 %t4473, i64 1)
    %t4475 = call i64 @freak_ver_parse(i64 %t4474)
    %t4476 = call i64 @freak_ver_gt(i64 %t4472, i64 %t4475)
    ret i64 %t4476
    br label %if.end.4470
if.end.4470:
    %t4477 = load i64, i64* %constraint
    %t4479 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.289, i64 0, i64 0
    %t4480 = ptrtoint i8* %t4479 to i64
    %t4478 = call i64 @freak_llvm_word_starts_with(i64 %t4477, i64 %t4480)
    %t4484 = icmp ne i64 %t4478, 0
    br i1 %t4484, label %if.then.4481, label %if.end.4483
if.then.4481:
    %t4485 = load i64, i64* %v
    %t4486 = load i64, i64* %constraint
    %t4487 = call i64 @freak_ver_strip_prefix(i64 %t4486, i64 1)
    %t4488 = call i64 @freak_ver_parse(i64 %t4487)
    %t4489 = call i64 @freak_ver_lt(i64 %t4485, i64 %t4488)
    ret i64 %t4489
    br label %if.end.4483
if.end.4483:
    %t4490 = load i64, i64* %constraint
    %t4492 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.290, i64 0, i64 0
    %t4493 = ptrtoint i8* %t4492 to i64
    %t4491 = call i64 @freak_llvm_word_starts_with(i64 %t4490, i64 %t4493)
    %t4497 = icmp ne i64 %t4491, 0
    br i1 %t4497, label %if.then.4494, label %if.end.4496
if.then.4494:
    %t4498 = load i64, i64* %v
    %t4499 = load i64, i64* %constraint
    %t4500 = call i64 @freak_ver_strip_prefix(i64 %t4499, i64 1)
    %t4501 = call i64 @freak_ver_parse(i64 %t4500)
    %t4502 = call i64 @freak_ver_eq(i64 %t4498, i64 %t4501)
    ret i64 %t4502
    br label %if.end.4496
if.end.4496:
    %t4503 = load i64, i64* %constraint
    %t4504 = call i64 @freak_llvm_word_length(i64 %t4503)
    %t4506 = icmp sgt i64 %t4504, 0
    %t4505 = zext i1 %t4506 to i64
    %t4510 = icmp ne i64 %t4505, 0
    br i1 %t4510, label %if.then.4507, label %if.end.4509
if.then.4507:
    %t4511 = load i64, i64* %constraint
    %t4512 = call i64 @freak_llvm_word_char_at(i64 %t4511, i64 0)
    %fc_v4513 = alloca i64
    store i64 %t4512, i64* %fc_v4513
    %t4514 = load i64, i64* %fc_v4513
    %t4515 = call i64 @freak_ver_is_digit(i64 %t4514)
    %t4519 = icmp ne i64 %t4515, 0
    br i1 %t4519, label %if.then.4516, label %if.end.4518
if.then.4516:
    %t4520 = load i64, i64* %constraint
    %t4521 = call i64 @freak_ver_parse(i64 %t4520)
    %c_v4522 = alloca i64
    store i64 %t4521, i64* %c_v4522
    %t4523 = load i64, i64* %v
    %t4524 = call i64 @freak_ver_major(i64 %t4523)
    %t4525 = load i64, i64* %c_v4522
    %t4526 = call i64 @freak_ver_major(i64 %t4525)
    %t4528 = icmp ne i64 %t4524, %t4526
    %t4527 = zext i1 %t4528 to i64
    %t4532 = icmp ne i64 %t4527, 0
    br i1 %t4532, label %if.then.4529, label %if.end.4531
if.then.4529:
    ret i64 0
    br label %if.end.4531
if.end.4531:
    %t4533 = load i64, i64* %v
    %t4534 = load i64, i64* %c_v4522
    %t4535 = call i64 @freak_ver_gte(i64 %t4533, i64 %t4534)
    ret i64 %t4535
    br label %if.end.4518
if.end.4518:
    br label %if.end.4509
if.end.4509:
    %t4536 = load i64, i64* %v
    %t4537 = load i64, i64* %constraint
    %t4538 = call i64 @freak_ver_parse(i64 %t4537)
    %t4539 = call i64 @freak_ver_eq(i64 %t4536, i64 %t4538)
    ret i64 %t4539
    ret i64 0
}

define i64 @freak_ver_satisfies(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4540 = load i64, i64* %version
    %t4541 = call i64 @freak_ver_parse(i64 %t4540)
    %v_v4542 = alloca i64
    store i64 %t4541, i64* %v_v4542
    %t4543 = load i64, i64* %constraint
    %t4544 = call i64 @freak_llvm_word_length(i64 %t4543)
    %clen_v4545 = alloca i64
    store i64 %t4544, i64* %clen_v4545
    %t4546 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.291, i64 0, i64 0
    %t4547 = ptrtoint i8* %t4546 to i64
    %current_v4548 = alloca i64
    store i64 %t4547, i64* %current_v4548
    store i64 0, i64* @g_i
    br label %loop.cond.4549
loop.cond.4549:
    %t4552 = load i64, i64* @g_i
    %t4553 = load i64, i64* %clen_v4545
    %t4555 = icmp sge i64 %t4552, %t4553
    %t4554 = zext i1 %t4555 to i64
    %t4556 = icmp eq i64 %t4554, 0
    br i1 %t4556, label %loop.body.4550, label %loop.end.4551
loop.body.4550:
    %t4557 = load i64, i64* %constraint
    %t4559 = load i64, i64* @g_i
    %t4558 = call i64 @freak_llvm_word_char_at(i64 %t4557, i64 %t4559)
    %ch_v4560 = alloca i64
    store i64 %t4558, i64* %ch_v4560
    %t4561 = load i64, i64* %ch_v4560
    %t4562 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.292, i64 0, i64 0
    %t4563 = ptrtoint i8* %t4562 to i64
    %t4564 = call i64 @freak_llvm_word_eq(i64 %t4561, i64 %t4563)
    %t4568 = icmp ne i64 %t4564, 0
    br i1 %t4568, label %if.then.4565, label %if.else.4566
if.then.4565:
    %t4569 = load i64, i64* %current_v4548
    %t4570 = call i64 @freak_llvm_word_length(i64 %t4569)
    %t4572 = icmp sgt i64 %t4570, 0
    %t4571 = zext i1 %t4572 to i64
    %t4576 = icmp ne i64 %t4571, 0
    br i1 %t4576, label %if.then.4573, label %if.end.4575
if.then.4573:
    %t4577 = load i64, i64* %v_v4542
    %t4578 = load i64, i64* %current_v4548
    %t4579 = call i64 @freak_ver_satisfies_single(i64 %t4577, i64 %t4578)
    %t4581 = icmp eq i64 %t4579, 0
    %t4580 = zext i1 %t4581 to i64
    %t4585 = icmp ne i64 %t4580, 0
    br i1 %t4585, label %if.then.4582, label %if.end.4584
if.then.4582:
    ret i64 0
    br label %if.end.4584
if.end.4584:
    %t4586 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.293, i64 0, i64 0
    %t4587 = ptrtoint i8* %t4586 to i64
    store i64 %t4587, i64* %current_v4548
    br label %if.end.4575
if.end.4575:
    br label %if.end.4567
if.else.4566:
    %t4588 = load i64, i64* %current_v4548
    %t4589 = load i64, i64* %ch_v4560
    %t4590 = call i64 @freak_llvm_word_concat(i64 %t4588, i64 %t4589)
    store i64 %t4590, i64* %current_v4548
    br label %if.end.4567
if.end.4567:
    %t4591 = load i64, i64* @g_i
    %t4592 = add i64 %t4591, 1
    store i64 %t4592, i64* @g_i
    br label %loop.cond.4549
loop.end.4551:
    %t4593 = load i64, i64* %current_v4548
    %t4594 = call i64 @freak_llvm_word_length(i64 %t4593)
    %t4596 = icmp sgt i64 %t4594, 0
    %t4595 = zext i1 %t4596 to i64
    %t4600 = icmp ne i64 %t4595, 0
    br i1 %t4600, label %if.then.4597, label %if.end.4599
if.then.4597:
    %t4601 = load i64, i64* %v_v4542
    %t4602 = load i64, i64* %current_v4548
    %t4603 = call i64 @freak_ver_satisfies_single(i64 %t4601, i64 %t4602)
    %t4605 = icmp eq i64 %t4603, 0
    %t4604 = zext i1 %t4605 to i64
    %t4609 = icmp ne i64 %t4604, 0
    br i1 %t4609, label %if.then.4606, label %if.end.4608
if.then.4606:
    ret i64 0
    br label %if.end.4608
if.end.4608:
    br label %if.end.4599
if.end.4599:
    ret i64 1
    ret i64 0
}

define i64 @freak_version_matches_constraint(i64 %arg_version, i64 %arg_constraint) {
entry:
    %version = alloca i64
    store i64 %arg_version, i64* %version
    %constraint = alloca i64
    store i64 %arg_constraint, i64* %constraint
    %t4610 = load i64, i64* %version
    %t4611 = load i64, i64* %constraint
    %t4612 = call i64 @freak_ver_satisfies(i64 %t4610, i64 %t4611)
    ret i64 %t4612
    ret i64 0
}

define void @freak_http_init() {
entry:
    %t4613 = load i64, i64* @g_http_inited
    %t4615 = icmp eq i64 %t4613, 0
    %t4614 = zext i1 %t4615 to i64
    %t4619 = icmp ne i64 %t4614, 0
    br i1 %t4619, label %if.then.4616, label %if.end.4618
if.then.4616:
    %t4620 = call i64 @freak_llvm_array_new()
    store i64 %t4620, i64* @g_http_resp_statuses
    %t4621 = call i64 @freak_llvm_array_new()
    store i64 %t4621, i64* @g_http_resp_bodies
    %t4622 = call i64 @freak_llvm_array_new()
    store i64 %t4622, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 1, i64* @g_http_inited
    br label %if.end.4618
if.end.4618:
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
    %t4623 = load i64, i64* @g_http_resp_count
    %idx_v4624 = alloca i64
    store i64 %t4623, i64* %idx_v4624
    %t4625 = load i64, i64* @g_http_resp_statuses
    %t4626 = load i64, i64* %status
    %t4627 = call i64 @freak_llvm_word_from_int(i64 %t4626)
    call void @freak_llvm_array_push(i64 %t4625, i64 %t4627)
    %t4628 = load i64, i64* @g_http_resp_bodies
    %t4629 = load i64, i64* %body
    call void @freak_llvm_array_push(i64 %t4628, i64 %t4629)
    %t4630 = load i64, i64* @g_http_resp_headers_raw
    %t4631 = load i64, i64* %headers
    call void @freak_llvm_array_push(i64 %t4630, i64 %t4631)
    %t4632 = load i64, i64* @g_http_resp_count
    %t4633 = add i64 %t4632, 1
    store i64 %t4633, i64* @g_http_resp_count
    %t4634 = load i64, i64* %idx_v4624
    ret i64 %t4634
    ret i64 0
}

define i64 @freak_http_resp_status(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4635 = load i64, i64* @g_http_resp_statuses
    %t4636 = load i64, i64* %handle
    %t4637 = call i64 @freak_llvm_array_get(i64 %t4635, i64 %t4636)
    %v_v4638 = alloca i64
    store i64 %t4637, i64* %v_v4638
    %t4639 = load i64, i64* %v_v4638
    %t4640 = call i64 @freak_llvm_word_to_int(i64 %t4639)
    ret i64 %t4640
    ret i64 0
}

define i64 @freak_http_resp_body(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4641 = load i64, i64* @g_http_resp_bodies
    %t4642 = load i64, i64* %handle
    %t4643 = call i64 @freak_llvm_array_get(i64 %t4641, i64 %t4642)
    ret i64 %t4643
    ret i64 0
}

define i64 @freak_http_resp_headers(i64 %arg_handle) {
entry:
    %handle = alloca i64
    store i64 %arg_handle, i64* %handle
    %t4644 = load i64, i64* @g_http_resp_headers_raw
    %t4645 = load i64, i64* %handle
    %t4646 = call i64 @freak_llvm_array_get(i64 %t4644, i64 %t4645)
    ret i64 %t4646
    ret i64 0
}

define i64 @freak_http_parse_status(i64 %arg_line) {
entry:
    %line = alloca i64
    store i64 %arg_line, i64* %line
    %t4647 = load i64, i64* %line
    %t4648 = call i64 @freak_llvm_word_length(i64 %t4647)
    %slen_v4649 = alloca i64
    store i64 %t4648, i64* %slen_v4649
    %si_v4650 = alloca i64
    store i64 0, i64* %si_v4650
    %t4656 = load i64, i64* %slen_v4649
    %rep.4655 = alloca i64
    store i64 0, i64* %rep.4655
    br label %loop.cond.4651
loop.cond.4651:
    %t4657 = load i64, i64* %rep.4655
    %t4658 = icmp slt i64 %t4657, %t4656
    br i1 %t4658, label %loop.body.4652, label %loop.end.4653
loop.body.4652:
    %t4659 = load i64, i64* %line
    %t4661 = load i64, i64* %si_v4650
    %t4660 = call i64 @freak_llvm_word_char_at(i64 %t4659, i64 %t4661)
    %t4662 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.294, i64 0, i64 0
    %t4663 = ptrtoint i8* %t4662 to i64
    %t4664 = call i64 @freak_llvm_word_eq(i64 %t4660, i64 %t4663)
    %t4668 = icmp ne i64 %t4664, 0
    br i1 %t4668, label %if.then.4665, label %if.end.4667
if.then.4665:
    %t4669 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.295, i64 0, i64 0
    %t4670 = ptrtoint i8* %t4669 to i64
    %code_str_v4671 = alloca i64
    store i64 %t4670, i64* %code_str_v4671
    %t4672 = load i64, i64* %si_v4650
    %t4673 = add i64 %t4672, 1
    %ci_v4674 = alloca i64
    store i64 %t4673, i64* %ci_v4674
    %rep.4679 = alloca i64
    store i64 0, i64* %rep.4679
    br label %loop.cond.4675
loop.cond.4675:
    %t4680 = load i64, i64* %rep.4679
    %t4681 = icmp slt i64 %t4680, 3
    br i1 %t4681, label %loop.body.4676, label %loop.end.4677
loop.body.4676:
    %t4682 = load i64, i64* %ci_v4674
    %t4683 = load i64, i64* %slen_v4649
    %t4685 = icmp slt i64 %t4682, %t4683
    %t4684 = zext i1 %t4685 to i64
    %t4689 = icmp ne i64 %t4684, 0
    br i1 %t4689, label %if.then.4686, label %if.end.4688
if.then.4686:
    %t4690 = load i64, i64* %code_str_v4671
    %t4691 = load i64, i64* %line
    %t4693 = load i64, i64* %ci_v4674
    %t4692 = call i64 @freak_llvm_word_char_at(i64 %t4691, i64 %t4693)
    %t4694 = call i64 @freak_llvm_word_concat(i64 %t4690, i64 %t4692)
    store i64 %t4694, i64* %code_str_v4671
    %t4695 = load i64, i64* %ci_v4674
    %t4696 = add i64 %t4695, 1
    store i64 %t4696, i64* %ci_v4674
    br label %if.end.4688
if.end.4688:
    br label %loop.inc.4678
loop.inc.4678:
    %t4697 = load i64, i64* %rep.4679
    %t4698 = add i64 %t4697, 1
    store i64 %t4698, i64* %rep.4679
    br label %loop.cond.4675
loop.end.4677:
    %t4699 = load i64, i64* %code_str_v4671
    %t4700 = call i64 @freak_llvm_word_to_int(i64 %t4699)
    ret i64 %t4700
    br label %if.end.4667
if.end.4667:
    %t4701 = load i64, i64* %si_v4650
    %t4702 = add i64 %t4701, 1
    store i64 %t4702, i64* %si_v4650
    br label %loop.inc.4654
loop.inc.4654:
    %t4703 = load i64, i64* %rep.4655
    %t4704 = add i64 %t4703, 1
    store i64 %t4704, i64* %rep.4655
    br label %loop.cond.4651
loop.end.4653:
    ret i64 0
    ret i64 0
}

define i64 @freak_http_split_response(i64 %arg_raw) {
entry:
    %raw = alloca i64
    store i64 %arg_raw, i64* %raw
    %t4705 = load i64, i64* %raw
    %t4706 = call i64 @freak_llvm_word_length(i64 %t4705)
    %rlen_v4707 = alloca i64
    store i64 %t4706, i64* %rlen_v4707
    %ri_v4708 = alloca i64
    store i64 0, i64* %ri_v4708
    %t4709 = sub i64 0, 1
    %header_end_v4710 = alloca i64
    store i64 %t4709, i64* %header_end_v4710
    %t4711 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.296, i64 0, i64 0
    %t4712 = ptrtoint i8* %t4711 to i64
    %prev3_v4713 = alloca i64
    store i64 %t4712, i64* %prev3_v4713
    %t4714 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.297, i64 0, i64 0
    %t4715 = ptrtoint i8* %t4714 to i64
    %prev2_v4716 = alloca i64
    store i64 %t4715, i64* %prev2_v4716
    %t4717 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.298, i64 0, i64 0
    %t4718 = ptrtoint i8* %t4717 to i64
    %prev1_v4719 = alloca i64
    store i64 %t4718, i64* %prev1_v4719
    %t4725 = load i64, i64* %rlen_v4707
    %rep.4724 = alloca i64
    store i64 0, i64* %rep.4724
    br label %loop.cond.4720
loop.cond.4720:
    %t4726 = load i64, i64* %rep.4724
    %t4727 = icmp slt i64 %t4726, %t4725
    br i1 %t4727, label %loop.body.4721, label %loop.end.4722
loop.body.4721:
    %t4728 = load i64, i64* %raw
    %t4730 = load i64, i64* %ri_v4708
    %t4729 = call i64 @freak_llvm_word_char_at(i64 %t4728, i64 %t4730)
    %ch_v4731 = alloca i64
    store i64 %t4729, i64* %ch_v4731
    %t4732 = load i64, i64* %prev2_v4716
    %t4733 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.299, i64 0, i64 0
    %t4734 = ptrtoint i8* %t4733 to i64
    %t4735 = call i64 @freak_llvm_word_eq(i64 %t4732, i64 %t4734)
    %t4736 = load i64, i64* %prev1_v4719
    %t4737 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.300, i64 0, i64 0
    %t4738 = ptrtoint i8* %t4737 to i64
    %t4739 = call i64 @freak_llvm_word_eq(i64 %t4736, i64 %t4738)
    %t4741 = icmp ne i64 %t4735, 0
    %t4742 = icmp ne i64 %t4739, 0
    %t4743 = and i1 %t4741, %t4742
    %t4740 = zext i1 %t4743 to i64
    %t4744 = load i64, i64* %ch_v4731
    %t4745 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.301, i64 0, i64 0
    %t4746 = ptrtoint i8* %t4745 to i64
    %t4747 = call i64 @freak_llvm_word_eq(i64 %t4744, i64 %t4746)
    %t4749 = icmp ne i64 %t4740, 0
    %t4750 = icmp ne i64 %t4747, 0
    %t4751 = and i1 %t4749, %t4750
    %t4748 = zext i1 %t4751 to i64
    %t4755 = icmp ne i64 %t4748, 0
    br i1 %t4755, label %if.then.4752, label %if.end.4754
if.then.4752:
    %t4756 = load i64, i64* %ri_v4708
    %t4757 = add i64 %t4756, 1
    store i64 %t4757, i64* %header_end_v4710
    br label %if.end.4754
if.end.4754:
    %t4758 = load i64, i64* %prev3_v4713
    %t4759 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.302, i64 0, i64 0
    %t4760 = ptrtoint i8* %t4759 to i64
    %t4761 = call i64 @freak_llvm_word_eq(i64 %t4758, i64 %t4760)
    %t4762 = load i64, i64* %prev2_v4716
    %t4763 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.303, i64 0, i64 0
    %t4764 = ptrtoint i8* %t4763 to i64
    %t4765 = call i64 @freak_llvm_word_eq(i64 %t4762, i64 %t4764)
    %t4767 = icmp ne i64 %t4761, 0
    %t4768 = icmp ne i64 %t4765, 0
    %t4769 = and i1 %t4767, %t4768
    %t4766 = zext i1 %t4769 to i64
    %t4770 = load i64, i64* %prev1_v4719
    %t4771 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.304, i64 0, i64 0
    %t4772 = ptrtoint i8* %t4771 to i64
    %t4773 = call i64 @freak_llvm_word_eq(i64 %t4770, i64 %t4772)
    %t4775 = icmp ne i64 %t4766, 0
    %t4776 = icmp ne i64 %t4773, 0
    %t4777 = and i1 %t4775, %t4776
    %t4774 = zext i1 %t4777 to i64
    %t4778 = load i64, i64* %ch_v4731
    %t4779 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.305, i64 0, i64 0
    %t4780 = ptrtoint i8* %t4779 to i64
    %t4781 = call i64 @freak_llvm_word_eq(i64 %t4778, i64 %t4780)
    %t4783 = icmp ne i64 %t4774, 0
    %t4784 = icmp ne i64 %t4781, 0
    %t4785 = and i1 %t4783, %t4784
    %t4782 = zext i1 %t4785 to i64
    %t4789 = icmp ne i64 %t4782, 0
    br i1 %t4789, label %if.then.4786, label %if.end.4788
if.then.4786:
    %t4790 = load i64, i64* %ri_v4708
    %t4791 = add i64 %t4790, 1
    store i64 %t4791, i64* %header_end_v4710
    br label %if.end.4788
if.end.4788:
    %t4792 = load i64, i64* %prev2_v4716
    store i64 %t4792, i64* %prev3_v4713
    %t4793 = load i64, i64* %prev1_v4719
    store i64 %t4793, i64* %prev2_v4716
    %t4794 = load i64, i64* %ch_v4731
    store i64 %t4794, i64* %prev1_v4719
    %t4795 = load i64, i64* %ri_v4708
    %t4796 = add i64 %t4795, 1
    store i64 %t4796, i64* %ri_v4708
    br label %loop.inc.4723
loop.inc.4723:
    %t4797 = load i64, i64* %rep.4724
    %t4798 = add i64 %t4797, 1
    store i64 %t4798, i64* %rep.4724
    br label %loop.cond.4720
loop.end.4722:
    %t4799 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.306, i64 0, i64 0
    %t4800 = ptrtoint i8* %t4799 to i64
    %status_line_v4801 = alloca i64
    store i64 %t4800, i64* %status_line_v4801
    %li_v4802 = alloca i64
    store i64 0, i64* %li_v4802
    %t4808 = load i64, i64* %rlen_v4707
    %rep.4807 = alloca i64
    store i64 0, i64* %rep.4807
    br label %loop.cond.4803
loop.cond.4803:
    %t4809 = load i64, i64* %rep.4807
    %t4810 = icmp slt i64 %t4809, %t4808
    br i1 %t4810, label %loop.body.4804, label %loop.end.4805
loop.body.4804:
    %t4811 = load i64, i64* %raw
    %t4813 = load i64, i64* %li_v4802
    %t4812 = call i64 @freak_llvm_word_char_at(i64 %t4811, i64 %t4813)
    %lc_v4814 = alloca i64
    store i64 %t4812, i64* %lc_v4814
    %t4815 = load i64, i64* %lc_v4814
    %t4816 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.307, i64 0, i64 0
    %t4817 = ptrtoint i8* %t4816 to i64
    %t4818 = call i64 @freak_llvm_word_eq(i64 %t4815, i64 %t4817)
    %t4819 = load i64, i64* %lc_v4814
    %t4820 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.308, i64 0, i64 0
    %t4821 = ptrtoint i8* %t4820 to i64
    %t4822 = call i64 @freak_llvm_word_eq(i64 %t4819, i64 %t4821)
    %t4824 = icmp ne i64 %t4818, 0
    %t4825 = icmp ne i64 %t4822, 0
    %t4826 = or i1 %t4824, %t4825
    %t4823 = zext i1 %t4826 to i64
    %t4830 = icmp ne i64 %t4823, 0
    br i1 %t4830, label %if.then.4827, label %if.else.4828
if.then.4827:
    %t4831 = load i64, i64* %rlen_v4707
    store i64 %t4831, i64* %li_v4802
    br label %if.end.4829
if.else.4828:
    %t4832 = load i64, i64* %status_line_v4801
    %t4833 = load i64, i64* %lc_v4814
    %t4834 = call i64 @freak_llvm_word_concat(i64 %t4832, i64 %t4833)
    store i64 %t4834, i64* %status_line_v4801
    br label %if.end.4829
if.end.4829:
    %t4835 = load i64, i64* %li_v4802
    %t4836 = add i64 %t4835, 1
    store i64 %t4836, i64* %li_v4802
    br label %loop.inc.4806
loop.inc.4806:
    %t4837 = load i64, i64* %rep.4807
    %t4838 = add i64 %t4837, 1
    store i64 %t4838, i64* %rep.4807
    br label %loop.cond.4803
loop.end.4805:
    %t4839 = load i64, i64* %status_line_v4801
    %t4840 = call i64 @freak_http_parse_status(i64 %t4839)
    %status_v4841 = alloca i64
    store i64 %t4840, i64* %status_v4841
    %t4842 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.309, i64 0, i64 0
    %t4843 = ptrtoint i8* %t4842 to i64
    %headers_v4844 = alloca i64
    store i64 %t4843, i64* %headers_v4844
    %t4845 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.310, i64 0, i64 0
    %t4846 = ptrtoint i8* %t4845 to i64
    %body_v4847 = alloca i64
    store i64 %t4846, i64* %body_v4847
    %t4848 = load i64, i64* %header_end_v4710
    %t4850 = icmp sgt i64 %t4848, 0
    %t4849 = zext i1 %t4850 to i64
    %t4854 = icmp ne i64 %t4849, 0
    br i1 %t4854, label %if.then.4851, label %if.else.4852
if.then.4851:
    %hi_v4855 = alloca i64
    store i64 0, i64* %hi_v4855
    %t4861 = load i64, i64* %header_end_v4710
    %rep.4860 = alloca i64
    store i64 0, i64* %rep.4860
    br label %loop.cond.4856
loop.cond.4856:
    %t4862 = load i64, i64* %rep.4860
    %t4863 = icmp slt i64 %t4862, %t4861
    br i1 %t4863, label %loop.body.4857, label %loop.end.4858
loop.body.4857:
    %t4864 = load i64, i64* %hi_v4855
    %t4865 = load i64, i64* %rlen_v4707
    %t4867 = icmp slt i64 %t4864, %t4865
    %t4866 = zext i1 %t4867 to i64
    %t4871 = icmp ne i64 %t4866, 0
    br i1 %t4871, label %if.then.4868, label %if.end.4870
if.then.4868:
    %t4872 = load i64, i64* %headers_v4844
    %t4873 = load i64, i64* %raw
    %t4875 = load i64, i64* %hi_v4855
    %t4874 = call i64 @freak_llvm_word_char_at(i64 %t4873, i64 %t4875)
    %t4876 = call i64 @freak_llvm_word_concat(i64 %t4872, i64 %t4874)
    store i64 %t4876, i64* %headers_v4844
    br label %if.end.4870
if.end.4870:
    %t4877 = load i64, i64* %hi_v4855
    %t4878 = add i64 %t4877, 1
    store i64 %t4878, i64* %hi_v4855
    br label %loop.inc.4859
loop.inc.4859:
    %t4879 = load i64, i64* %rep.4860
    %t4880 = add i64 %t4879, 1
    store i64 %t4880, i64* %rep.4860
    br label %loop.cond.4856
loop.end.4858:
    %t4881 = load i64, i64* %header_end_v4710
    %bi_v4882 = alloca i64
    store i64 %t4881, i64* %bi_v4882
    %t4888 = load i64, i64* %rlen_v4707
    %rep.4887 = alloca i64
    store i64 0, i64* %rep.4887
    br label %loop.cond.4883
loop.cond.4883:
    %t4889 = load i64, i64* %rep.4887
    %t4890 = icmp slt i64 %t4889, %t4888
    br i1 %t4890, label %loop.body.4884, label %loop.end.4885
loop.body.4884:
    %t4891 = load i64, i64* %bi_v4882
    %t4892 = load i64, i64* %rlen_v4707
    %t4894 = icmp slt i64 %t4891, %t4892
    %t4893 = zext i1 %t4894 to i64
    %t4898 = icmp ne i64 %t4893, 0
    br i1 %t4898, label %if.then.4895, label %if.end.4897
if.then.4895:
    %t4899 = load i64, i64* %body_v4847
    %t4900 = load i64, i64* %raw
    %t4902 = load i64, i64* %bi_v4882
    %t4901 = call i64 @freak_llvm_word_char_at(i64 %t4900, i64 %t4902)
    %t4903 = call i64 @freak_llvm_word_concat(i64 %t4899, i64 %t4901)
    store i64 %t4903, i64* %body_v4847
    br label %if.end.4897
if.end.4897:
    %t4904 = load i64, i64* %bi_v4882
    %t4905 = add i64 %t4904, 1
    store i64 %t4905, i64* %bi_v4882
    br label %loop.inc.4886
loop.inc.4886:
    %t4906 = load i64, i64* %rep.4887
    %t4907 = add i64 %t4906, 1
    store i64 %t4907, i64* %rep.4887
    br label %loop.cond.4883
loop.end.4885:
    br label %if.end.4853
if.else.4852:
    %t4908 = load i64, i64* %raw
    store i64 %t4908, i64* %headers_v4844
    br label %if.end.4853
if.end.4853:
    %t4909 = load i64, i64* %status_v4841
    %t4910 = load i64, i64* %body_v4847
    %t4911 = load i64, i64* %headers_v4844
    %t4912 = call i64 @freak_http_alloc_resp(i64 %t4909, i64 %t4910, i64 %t4911)
    ret i64 %t4912
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
    %t4913 = load i64, i64* %host
    %t4914 = load i64, i64* %port
    %t4915 = call i64 @freak_llvm_tcp_connect(i64 %t4913, i64 %t4914)
    %fd_v4916 = alloca i64
    store i64 %t4915, i64* %fd_v4916
    %t4917 = load i64, i64* %fd_v4916
    %t4919 = icmp slt i64 %t4917, 0
    %t4918 = zext i1 %t4919 to i64
    %t4923 = icmp ne i64 %t4918, 0
    br i1 %t4923, label %if.then.4920, label %if.end.4922
if.then.4920:
    %t4924 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.311, i64 0, i64 0
    %t4925 = ptrtoint i8* %t4924 to i64
    %t4926 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.312, i64 0, i64 0
    %t4927 = ptrtoint i8* %t4926 to i64
    %t4928 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4925, i64 %t4927)
    ret i64 %t4928
    br label %if.end.4922
if.end.4922:
    %t4929 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.313, i64 0, i64 0
    %t4930 = ptrtoint i8* %t4929 to i64
    %t4931 = load i64, i64* %path
    %t4932 = call i64 @freak_llvm_word_concat(i64 %t4930, i64 %t4931)
    %t4933 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.314, i64 0, i64 0
    %t4934 = ptrtoint i8* %t4933 to i64
    %t4935 = call i64 @freak_llvm_word_concat(i64 %t4932, i64 %t4934)
    %t4936 = load i64, i64* %host
    %t4937 = call i64 @freak_llvm_word_concat(i64 %t4935, i64 %t4936)
    %t4938 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.315, i64 0, i64 0
    %t4939 = ptrtoint i8* %t4938 to i64
    %t4940 = call i64 @freak_llvm_word_concat(i64 %t4937, i64 %t4939)
    %req_v4941 = alloca i64
    store i64 %t4940, i64* %req_v4941
    %t4942 = load i64, i64* %fd_v4916
    %t4943 = load i64, i64* %req_v4941
    %t4944 = call i64 @freak_llvm_tcp_send(i64 %t4942, i64 %t4943)
    %t4945 = load i64, i64* %fd_v4916
    %t4946 = call i64 @freak_llvm_tcp_recv_all(i64 %t4945, i64 65536)
    %raw_v4947 = alloca i64
    store i64 %t4946, i64* %raw_v4947
    %t4948 = load i64, i64* %fd_v4916
    call void @freak_llvm_tcp_close(i64 %t4948)
    %t4949 = load i64, i64* %raw_v4947
    %t4950 = call i64 @freak_http_split_response(i64 %t4949)
    ret i64 %t4950
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
    %t4951 = load i64, i64* %host
    %t4952 = load i64, i64* %port
    %t4953 = call i64 @freak_llvm_tcp_connect(i64 %t4951, i64 %t4952)
    %fd_v4954 = alloca i64
    store i64 %t4953, i64* %fd_v4954
    %t4955 = load i64, i64* %fd_v4954
    %t4957 = icmp slt i64 %t4955, 0
    %t4956 = zext i1 %t4957 to i64
    %t4961 = icmp ne i64 %t4956, 0
    br i1 %t4961, label %if.then.4958, label %if.end.4960
if.then.4958:
    %t4962 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.316, i64 0, i64 0
    %t4963 = ptrtoint i8* %t4962 to i64
    %t4964 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.317, i64 0, i64 0
    %t4965 = ptrtoint i8* %t4964 to i64
    %t4966 = call i64 @freak_http_alloc_resp(i64 0, i64 %t4963, i64 %t4965)
    ret i64 %t4966
    br label %if.end.4960
if.end.4960:
    %t4967 = load i64, i64* %body
    %t4968 = call i64 @freak_llvm_word_length(i64 %t4967)
    %t4969 = call i64 @freak_llvm_word_from_int(i64 %t4968)
    %body_len_v4970 = alloca i64
    store i64 %t4969, i64* %body_len_v4970
    %t4971 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.318, i64 0, i64 0
    %t4972 = ptrtoint i8* %t4971 to i64
    %t4973 = load i64, i64* %path
    %t4974 = call i64 @freak_llvm_word_concat(i64 %t4972, i64 %t4973)
    %t4975 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.319, i64 0, i64 0
    %t4976 = ptrtoint i8* %t4975 to i64
    %t4977 = call i64 @freak_llvm_word_concat(i64 %t4974, i64 %t4976)
    %t4978 = load i64, i64* %host
    %t4979 = call i64 @freak_llvm_word_concat(i64 %t4977, i64 %t4978)
    %t4980 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.320, i64 0, i64 0
    %t4981 = ptrtoint i8* %t4980 to i64
    %t4982 = call i64 @freak_llvm_word_concat(i64 %t4979, i64 %t4981)
    %t4983 = load i64, i64* %content_type
    %t4984 = call i64 @freak_llvm_word_concat(i64 %t4982, i64 %t4983)
    %t4985 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.321, i64 0, i64 0
    %t4986 = ptrtoint i8* %t4985 to i64
    %t4987 = call i64 @freak_llvm_word_concat(i64 %t4984, i64 %t4986)
    %t4988 = load i64, i64* %body_len_v4970
    %t4989 = call i64 @freak_llvm_word_concat(i64 %t4987, i64 %t4988)
    %t4990 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.322, i64 0, i64 0
    %t4991 = ptrtoint i8* %t4990 to i64
    %t4992 = call i64 @freak_llvm_word_concat(i64 %t4989, i64 %t4991)
    %t4993 = load i64, i64* %body
    %t4994 = call i64 @freak_llvm_word_concat(i64 %t4992, i64 %t4993)
    %req_v4995 = alloca i64
    store i64 %t4994, i64* %req_v4995
    %t4996 = load i64, i64* %fd_v4954
    %t4997 = load i64, i64* %req_v4995
    %t4998 = call i64 @freak_llvm_tcp_send(i64 %t4996, i64 %t4997)
    %t4999 = load i64, i64* %fd_v4954
    %t5000 = call i64 @freak_llvm_tcp_recv_all(i64 %t4999, i64 65536)
    %raw_v5001 = alloca i64
    store i64 %t5000, i64* %raw_v5001
    %t5002 = load i64, i64* %fd_v4954
    call void @freak_llvm_tcp_close(i64 %t5002)
    %t5003 = load i64, i64* %raw_v5001
    %t5004 = call i64 @freak_http_split_response(i64 %t5003)
    ret i64 %t5004
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
    %t5005 = load i64, i64* %host
    %t5006 = load i64, i64* %port
    %t5007 = call i64 @freak_llvm_tcp_connect(i64 %t5005, i64 %t5006)
    %fd_v5008 = alloca i64
    store i64 %t5007, i64* %fd_v5008
    %t5009 = load i64, i64* %fd_v5008
    %t5011 = icmp slt i64 %t5009, 0
    %t5010 = zext i1 %t5011 to i64
    %t5015 = icmp ne i64 %t5010, 0
    br i1 %t5015, label %if.then.5012, label %if.end.5014
if.then.5012:
    %t5016 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.323, i64 0, i64 0
    %t5017 = ptrtoint i8* %t5016 to i64
    %t5018 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.324, i64 0, i64 0
    %t5019 = ptrtoint i8* %t5018 to i64
    %t5020 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5017, i64 %t5019)
    ret i64 %t5020
    br label %if.end.5014
if.end.5014:
    %t5021 = load i64, i64* %body
    %t5022 = call i64 @freak_llvm_word_length(i64 %t5021)
    %t5023 = call i64 @freak_llvm_word_from_int(i64 %t5022)
    %body_len_v5024 = alloca i64
    store i64 %t5023, i64* %body_len_v5024
    %t5025 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.325, i64 0, i64 0
    %t5026 = ptrtoint i8* %t5025 to i64
    %t5027 = load i64, i64* %path
    %t5028 = call i64 @freak_llvm_word_concat(i64 %t5026, i64 %t5027)
    %t5029 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.326, i64 0, i64 0
    %t5030 = ptrtoint i8* %t5029 to i64
    %t5031 = call i64 @freak_llvm_word_concat(i64 %t5028, i64 %t5030)
    %t5032 = load i64, i64* %host
    %t5033 = call i64 @freak_llvm_word_concat(i64 %t5031, i64 %t5032)
    %t5034 = getelementptr inbounds [59 x i8], [59 x i8]* @.str.327, i64 0, i64 0
    %t5035 = ptrtoint i8* %t5034 to i64
    %t5036 = call i64 @freak_llvm_word_concat(i64 %t5033, i64 %t5035)
    %t5037 = load i64, i64* %content_type
    %t5038 = call i64 @freak_llvm_word_concat(i64 %t5036, i64 %t5037)
    %t5039 = getelementptr inbounds [19 x i8], [19 x i8]* @.str.328, i64 0, i64 0
    %t5040 = ptrtoint i8* %t5039 to i64
    %t5041 = call i64 @freak_llvm_word_concat(i64 %t5038, i64 %t5040)
    %t5042 = load i64, i64* %body_len_v5024
    %t5043 = call i64 @freak_llvm_word_concat(i64 %t5041, i64 %t5042)
    %t5044 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.329, i64 0, i64 0
    %t5045 = ptrtoint i8* %t5044 to i64
    %t5046 = call i64 @freak_llvm_word_concat(i64 %t5043, i64 %t5045)
    %t5047 = load i64, i64* %body
    %t5048 = call i64 @freak_llvm_word_concat(i64 %t5046, i64 %t5047)
    %req_v5049 = alloca i64
    store i64 %t5048, i64* %req_v5049
    %t5050 = load i64, i64* %fd_v5008
    %t5051 = load i64, i64* %req_v5049
    %t5052 = call i64 @freak_llvm_tcp_send(i64 %t5050, i64 %t5051)
    %t5053 = load i64, i64* %fd_v5008
    %t5054 = call i64 @freak_llvm_tcp_recv_all(i64 %t5053, i64 65536)
    %raw_v5055 = alloca i64
    store i64 %t5054, i64* %raw_v5055
    %t5056 = load i64, i64* %fd_v5008
    call void @freak_llvm_tcp_close(i64 %t5056)
    %t5057 = load i64, i64* %raw_v5055
    %t5058 = call i64 @freak_http_split_response(i64 %t5057)
    ret i64 %t5058
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
    %t5059 = load i64, i64* %host
    %t5060 = load i64, i64* %port
    %t5061 = call i64 @freak_llvm_tcp_connect(i64 %t5059, i64 %t5060)
    %fd_v5062 = alloca i64
    store i64 %t5061, i64* %fd_v5062
    %t5063 = load i64, i64* %fd_v5062
    %t5065 = icmp slt i64 %t5063, 0
    %t5064 = zext i1 %t5065 to i64
    %t5069 = icmp ne i64 %t5064, 0
    br i1 %t5069, label %if.then.5066, label %if.end.5068
if.then.5066:
    %t5070 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.330, i64 0, i64 0
    %t5071 = ptrtoint i8* %t5070 to i64
    %t5072 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.331, i64 0, i64 0
    %t5073 = ptrtoint i8* %t5072 to i64
    %t5074 = call i64 @freak_http_alloc_resp(i64 0, i64 %t5071, i64 %t5073)
    ret i64 %t5074
    br label %if.end.5068
if.end.5068:
    %t5075 = getelementptr inbounds [8 x i8], [8 x i8]* @.str.332, i64 0, i64 0
    %t5076 = ptrtoint i8* %t5075 to i64
    %t5077 = load i64, i64* %path
    %t5078 = call i64 @freak_llvm_word_concat(i64 %t5076, i64 %t5077)
    %t5079 = getelementptr inbounds [18 x i8], [18 x i8]* @.str.333, i64 0, i64 0
    %t5080 = ptrtoint i8* %t5079 to i64
    %t5081 = call i64 @freak_llvm_word_concat(i64 %t5078, i64 %t5080)
    %t5082 = load i64, i64* %host
    %t5083 = call i64 @freak_llvm_word_concat(i64 %t5081, i64 %t5082)
    %t5084 = getelementptr inbounds [47 x i8], [47 x i8]* @.str.334, i64 0, i64 0
    %t5085 = ptrtoint i8* %t5084 to i64
    %t5086 = call i64 @freak_llvm_word_concat(i64 %t5083, i64 %t5085)
    %req_v5087 = alloca i64
    store i64 %t5086, i64* %req_v5087
    %t5088 = load i64, i64* %fd_v5062
    %t5089 = load i64, i64* %req_v5087
    %t5090 = call i64 @freak_llvm_tcp_send(i64 %t5088, i64 %t5089)
    %t5091 = load i64, i64* %fd_v5062
    %t5092 = call i64 @freak_llvm_tcp_recv_all(i64 %t5091, i64 65536)
    %raw_v5093 = alloca i64
    store i64 %t5092, i64* %raw_v5093
    %t5094 = load i64, i64* %fd_v5062
    call void @freak_llvm_tcp_close(i64 %t5094)
    %t5095 = load i64, i64* %raw_v5093
    %t5096 = call i64 @freak_http_split_response(i64 %t5095)
    ret i64 %t5096
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
    %t5097 = getelementptr inbounds [1 x i8], [1 x i8]* @.str.335, i64 0, i64 0
    %t5098 = ptrtoint i8* %t5097 to i64
    store i64 %t5098, i64* @g_json_src
    store i64 0, i64* @g_json_pos
    store i64 0, i64* @g_json_len
    store i64 0, i64* @g_http_resp_statuses
    store i64 0, i64* @g_http_resp_bodies
    store i64 0, i64* @g_http_resp_headers_raw
    store i64 0, i64* @g_http_resp_count
    store i64 0, i64* @g_http_inited
    store i64 0, i64* @g_count
    %rep.5103 = alloca i64
    store i64 0, i64* %rep.5103
    br label %loop.cond.5099
loop.cond.5099:
    %t5104 = load i64, i64* %rep.5103
    %t5105 = icmp slt i64 %t5104, 4
    br i1 %t5105, label %loop.body.5100, label %loop.end.5101
loop.body.5100:
    %t5106 = load i64, i64* @g_count
    %t5107 = add i64 %t5106, 1
    store i64 %t5107, i64* @g_count
    br label %loop.inc.5102
loop.inc.5102:
    %t5108 = load i64, i64* %rep.5103
    %t5109 = add i64 %t5108, 1
    store i64 %t5109, i64* %rep.5103
    br label %loop.cond.5099
loop.end.5101:
    %t5110 = load i64, i64* @g_count
    %t5111 = call i64 @freak_llvm_word_from_int(i64 %t5110)
    call void @freak_llvm_say(i64 %t5111)
    store i64 1, i64* @g_power
    %rep.5116 = alloca i64
    store i64 0, i64* %rep.5116
    br label %loop.cond.5112
loop.cond.5112:
    %t5117 = load i64, i64* %rep.5116
    %t5118 = icmp slt i64 %t5117, 20
    %t5119 = load i64, i64* @g_power
    %t5121 = icmp sge i64 %t5119, 16
    %t5120 = zext i1 %t5121 to i64
    %t5122 = icmp eq i64 %t5120, 0
    %t5123 = and i1 %t5118, %t5122
    br i1 %t5123, label %loop.body.5113, label %loop.end.5114
loop.body.5113:
    %t5124 = load i64, i64* @g_power
    %t5125 = mul i64 %t5124, 2
    store i64 %t5125, i64* @g_power
    br label %loop.inc.5115
loop.inc.5115:
    %t5126 = load i64, i64* %rep.5116
    %t5127 = add i64 %t5126, 1
    store i64 %t5127, i64* %rep.5116
    br label %loop.cond.5112
loop.end.5114:
    %t5128 = load i64, i64* @g_power
    %t5129 = call i64 @freak_llvm_word_from_int(i64 %t5128)
    call void @freak_llvm_say(i64 %t5129)
    store i64 0, i64* @g_i
    br label %loop.cond.5130
loop.cond.5130:
    %t5133 = load i64, i64* @g_i
    %t5135 = icmp sge i64 %t5133, 3
    %t5134 = zext i1 %t5135 to i64
    %t5136 = icmp eq i64 %t5134, 0
    br i1 %t5136, label %loop.body.5131, label %loop.end.5132
loop.body.5131:
    %t5137 = load i64, i64* @g_i
    %t5138 = add i64 %t5137, 1
    store i64 %t5138, i64* @g_i
    br label %loop.cond.5130
loop.end.5132:
    %t5139 = load i64, i64* @g_i
    %t5140 = call i64 @freak_llvm_word_from_int(i64 %t5139)
    call void @freak_llvm_say(i64 %t5140)
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

