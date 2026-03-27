; FREAK — document outline / symbols for Zed

(function_declaration
  "task" @context
  name: (identifier) @name) @item

(launch_declaration
  "launch" @context
  name: (identifier) @name) @item

(shape_declaration
  "shape" @context
  name: (type_identifier) @name) @item

(doctrine_declaration
  "doctrine" @context
  name: (type_identifier) @name) @item

(impl_block
  "impl" @context
  type: (type_identifier) @name) @item

(route_declaration
  "route" @context
  name: (type_identifier) @name) @item

(test_block
  "test" @context
  name: (string) @name) @item
