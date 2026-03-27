; FREAK language — Tree-sitter highlight queries for Zed
; "Every keyword has a soul. Now they have colors too."

; ============================================================
;  Comments
; ============================================================

(comment) @comment

; ============================================================
;  Strings and interpolation
; ============================================================

(string) @string
(string_content) @string
(escape_sequence) @string.escape
(string_interpolation
  "{" @punctuation.special
  "}" @punctuation.special)

; ============================================================
;  Numbers and constants
; ============================================================

(number) @number

(boolean) @constant.builtin
(nobody_literal) @constant.builtin
(mood_literal) @constant.builtin

; ============================================================
;  Keywords — declarations
; ============================================================

"pilot" @keyword
"fixed" @keyword
"task" @keyword
"shape" @keyword
"doctrine" @keyword
"impl" @keyword
"launch" @keyword
"extern" @keyword
"use" @keyword
"route" @keyword
"for" @keyword
"lend" @keyword
"mut" @keyword
"copy" @keyword

; ============================================================
;  Keywords — control flow
; ============================================================

"if" @keyword.control
"else" @keyword.control
"when" @keyword.control
"repeat" @keyword.control
"times" @keyword.control
"until" @keyword.control
"training" @keyword.control
"arc" @keyword.control
"each" @keyword.control
"in" @keyword.control
"give" @keyword.control
"back" @keyword.control
"break" @keyword.control
"continue" @keyword.control
"done" @keyword.control

; ============================================================
;  Keywords — special blocks
; ============================================================

"eventually" @keyword.control
"trust-me" @keyword.control
"isekai" @keyword.control
"bringing" @keyword.control
"deus_ex_machina" @keyword.control
"foreshadow" @keyword.control
"payoff" @keyword.control

; ============================================================
;  Keywords — expressions
; ============================================================

"say" @function.builtin
"some" @function.builtin
"ok" @function.builtin
"err" @function.builtin
"check" @keyword.control
"test" @keyword
"expect" @keyword

; ============================================================
;  Keywords — logical operators
; ============================================================

"and" @keyword.operator
"or" @keyword.operator
"not" @keyword.operator

; ============================================================
;  Types
; ============================================================

(primitive_type) @type.builtin

(type_identifier) @type

(generic_type
  name: (type_identifier) @type)
(generic_type
  name: (identifier) @type)

(generic_parameters
  (type_identifier) @type)

; ============================================================
;  Functions
; ============================================================

(function_declaration
  name: (identifier) @function)

(launch_declaration
  name: (identifier) @function)

(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (scoped_identifier
    scope: (_) @type
    name: (identifier) @function.call))

(method_call
  method: (identifier) @function.method)

(parameter
  name: (identifier) @variable.parameter)

; ============================================================
;  Shapes and fields
; ============================================================

(shape_declaration
  name: (type_identifier) @type)

(doctrine_declaration
  name: (type_identifier) @type)

(impl_block
  type: (type_identifier) @type)
(impl_block
  target: (type_identifier) @type)

(route_declaration
  name: (type_identifier) @type)

(route_variant
  name: (type_identifier) @type.enum.variant)

(field_declaration
  name: (identifier) @property)

(field_access
  field: (identifier) @property)

(shape_field_init
  name: (identifier) @property)

; ============================================================
;  Variables
; ============================================================

(variable_declaration
  name: (identifier) @variable)

(fixed_variable_declaration
  name: (identifier) @variable)

(for_each_statement
  variable: (identifier) @variable)

; ============================================================
;  Annotations
; ============================================================

(annotation
  "@" @attribute
  name: (identifier) @attribute)

; ============================================================
;  Operators
; ============================================================

"|>" @operator
"->" @operator
"?" @operator
"=" @operator
"+=" @operator
"-=" @operator
"*=" @operator
"/=" @operator
"+" @operator
"-" @operator
"*" @operator
"/" @operator
"%" @operator
"==" @operator
"!=" @operator
"<" @operator
">" @operator
"<=" @operator
">=" @operator

; ============================================================
;  Punctuation
; ============================================================

"(" @punctuation.bracket
")" @punctuation.bracket
"[" @punctuation.bracket
"]" @punctuation.bracket
"{" @punctuation.bracket
"}" @punctuation.bracket

"," @punctuation.delimiter
":" @punctuation.delimiter
"::" @punctuation.delimiter
"." @punctuation.delimiter
