/* FREAK single-translation-unit build shim. Upstream generated callbacks use
   unsigned char pointers while api.c/http.c use char pointers across object
   boundaries. These explicit byte-pointer bridges and the documented two-line generated span-type
   correction make the single translation unit type-correct when included in the shipping runtime. */
#include "include/llhttp.h"
#define llhttp__on_message_begin freak_llhttp_char_on_message_begin
#define llhttp__on_protocol freak_llhttp_char_on_protocol
#define llhttp__on_protocol_complete freak_llhttp_char_on_protocol_complete
#define llhttp__on_url freak_llhttp_char_on_url
#define llhttp__on_url_complete freak_llhttp_char_on_url_complete
#define llhttp__on_status freak_llhttp_char_on_status
#define llhttp__on_status_complete freak_llhttp_char_on_status_complete
#define llhttp__on_method freak_llhttp_char_on_method
#define llhttp__on_method_complete freak_llhttp_char_on_method_complete
#define llhttp__on_version freak_llhttp_char_on_version
#define llhttp__on_version_complete freak_llhttp_char_on_version_complete
#define llhttp__on_header_field freak_llhttp_char_on_header_field
#define llhttp__on_header_field_complete freak_llhttp_char_on_header_field_complete
#define llhttp__on_header_value freak_llhttp_char_on_header_value
#define llhttp__on_header_value_complete freak_llhttp_char_on_header_value_complete
#define llhttp__on_headers_complete freak_llhttp_char_on_headers_complete
#define llhttp__on_message_complete freak_llhttp_char_on_message_complete
#define llhttp__on_body freak_llhttp_char_on_body
#define llhttp__on_chunk_header freak_llhttp_char_on_chunk_header
#define llhttp__on_chunk_extension_name freak_llhttp_char_on_chunk_extension_name
#define llhttp__on_chunk_extension_name_complete freak_llhttp_char_on_chunk_extension_name_complete
#define llhttp__on_chunk_extension_value freak_llhttp_char_on_chunk_extension_value
#define llhttp__on_chunk_extension_value_complete freak_llhttp_char_on_chunk_extension_value_complete
#define llhttp__on_chunk_complete freak_llhttp_char_on_chunk_complete
#define llhttp__on_reset freak_llhttp_char_on_reset
#define llhttp__before_headers_complete freak_llhttp_char_before_headers_complete
#define llhttp__after_headers_complete freak_llhttp_char_after_headers_complete
#define llhttp__after_message_complete freak_llhttp_char_after_message_complete
#include "src/http.c"
#include "src/api.c"
#undef llhttp__on_message_begin
#undef llhttp__on_protocol
#undef llhttp__on_protocol_complete
#undef llhttp__on_url
#undef llhttp__on_url_complete
#undef llhttp__on_status
#undef llhttp__on_status_complete
#undef llhttp__on_method
#undef llhttp__on_method_complete
#undef llhttp__on_version
#undef llhttp__on_version_complete
#undef llhttp__on_header_field
#undef llhttp__on_header_field_complete
#undef llhttp__on_header_value
#undef llhttp__on_header_value_complete
#undef llhttp__on_headers_complete
#undef llhttp__on_message_complete
#undef llhttp__on_body
#undef llhttp__on_chunk_header
#undef llhttp__on_chunk_extension_name
#undef llhttp__on_chunk_extension_name_complete
#undef llhttp__on_chunk_extension_value
#undef llhttp__on_chunk_extension_value_complete
#undef llhttp__on_chunk_complete
#undef llhttp__on_reset
#undef llhttp__before_headers_complete
#undef llhttp__after_headers_complete
#undef llhttp__after_message_complete
int llhttp__on_message_begin(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_message_begin(parser,(const char *)at,(const char *)end);
}
int llhttp__on_protocol(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_protocol(parser,(const char *)at,(const char *)end);
}
int llhttp__on_protocol_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_protocol_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_url(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_url(parser,(const char *)at,(const char *)end);
}
int llhttp__on_url_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_url_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_status(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_status(parser,(const char *)at,(const char *)end);
}
int llhttp__on_status_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_status_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_method(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_method(parser,(const char *)at,(const char *)end);
}
int llhttp__on_method_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_method_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_version(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_version(parser,(const char *)at,(const char *)end);
}
int llhttp__on_version_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_version_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_header_field(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_header_field(parser,(const char *)at,(const char *)end);
}
int llhttp__on_header_field_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_header_field_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_header_value(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_header_value(parser,(const char *)at,(const char *)end);
}
int llhttp__on_header_value_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_header_value_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_headers_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_headers_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_message_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_message_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_body(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_body(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_header(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_header(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_extension_name(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_extension_name(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_extension_name_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_extension_name_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_extension_value(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_extension_value(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_extension_value_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_extension_value_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_chunk_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_chunk_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__on_reset(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_on_reset(parser,(const char *)at,(const char *)end);
}
int llhttp__before_headers_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_before_headers_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__after_headers_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_after_headers_complete(parser,(const char *)at,(const char *)end);
}
int llhttp__after_message_complete(llhttp__internal_t *parser,const unsigned char *at,const unsigned char *end) {
    return freak_llhttp_char_after_message_complete(parser,(const char *)at,(const char *)end);
}
#include "src/llhttp.c"
#undef ALIGN
#undef UNREACHABLE
#undef CALLBACK_MAYBE
#undef SPAN_CALLBACK_MAYBE
