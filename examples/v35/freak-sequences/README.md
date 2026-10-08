# Pure arithmetic sequence library

`arithmetic_value(start, step, index)` returns `start + step * index` using
checked signed-int arithmetic. It has no initialization code, runtime-private
handles, native FFI, or application entry. Consumers import its public export:

```freak
use sequences::{arithmetic_value}
```

Run `freak test --c` and `freak test --llvm` in this directory. The companion
`sequence-service` validates request ranges before calling this API.
