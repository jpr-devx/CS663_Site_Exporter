# Binary and Bases in Rust

## Overview

This lecture covers the Rust-specific implementation of binary representation, bitwise operations, and base conversion functions for NTLang. We examine Rust's built-in integer types, bitwise operators (noting the `!` vs `~` difference from C), shift behavior guarantees, and idiomatic Rust approaches to string-integer conversion. We also cover width masking with overflow-safe arithmetic and signed output using `as` casting.

## Learning Objectives

- Use Rust's integer types (`u32`, `i32`, `u8`) with explicit casting via `as`
- Apply Rust's bitwise operators (`!`, `&`, `|`, `^`) and understand differences from C
- Implement shift operations with guaranteed behavior for signed and unsigned types
- Write string-to-integer conversion using iterators and `to_digit()`
- Implement integer-to-string conversion using `String` operations
- Apply width masking with `wrapping_shl()` for overflow safety

## Prerequisites

- Understanding of binary, hex, and two's complement (previous lecture)
- Rust programming basics (types, ownership, pattern matching)
- Familiarity with the NTLang project structure

---

## 1. Rust Integer Types

### Built-in Integer Types

Rust has built-in fixed-width integer types — no imports needed:

| Type | Width | Range |
| --- | --- | --- |
| `u8` | 8 bits | 0 to 255 |
| `i8` | 8 bits | -128 to 127 |
| `u16` | 16 bits | 0 to 65,535 |
| `i16` | 16 bits | -32,768 to 32,767 |
| `u32` | 32 bits | 0 to 4,294,967,295 |
| `i32` | 32 bits | -2,147,483,648 to 2,147,483,647 |
| `u64` | 64 bits | 0 to 18,446,744,073,709,551,615 |
| `i64` | 64 bits | -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 |

### Explicit Types Required

Rust requires explicit types — there is no implicit widening:

```
let a: u32 = 42;
let b: u8 = 255;
// let c: u32 = a + b;  // ERROR: mismatched types

let c: u32 = a + b as u32;  // OK: explicit cast
```

### The `as` Keyword for Casting

```
let unsigned: u32 = 0xFFFFFFFB;
let signed: i32 = unsigned as i32;  // Reinterprets bits: -5
let back: u32 = signed as u32;      // Reinterprets bits: 0xFFFFFFFB

let small: u8 = 200;
let wide: u32 = small as u32;       // Zero-extends: 200
```

`as` performs **bit reinterpretation** between same-width types and **zero/sign extension** between different widths.

### Comparison with C

| Aspect | C | Rust |
| --- | --- | --- |
| Fixed types | `#include <stdint.h>` | Built-in |
| Type names | `uint32_t`, `int32_t` | `u32`, `i32` |
| Implicit widening | Yes (can be surprising) | No (compile error) |
| Cast syntax | `(int32_t)value` | `value as i32` |

---

## 2. Bitwise Operators in Rust

### The Operators

| Operator | Name | C Equivalent | Example |
| --- | --- | --- | --- |
| `!` | Bitwise NOT | `~` | `!0x0Fu32` → `0xFFFFFFF0` |
| `&` | Bitwise AND | `&` | `0xCA & 0xF0` → `0xC0` |
| `\|` | Bitwise OR | `\|` | `0xCA \| 0x0F` → `0xCF` |
| `^` | Bitwise XOR | `^` | `0xCA ^ 0xFF` → `0x35` |

### Important: `!` vs `~`

In Rust, `!` is used for **both** logical NOT (on `bool`) and bitwise NOT (on integers). C uses `~` for bitwise NOT and `!` for logical NOT:

```
let a: u32 = 0x0F;
let not_a = !a;        // 0xFFFFFFF0 (bitwise NOT)

let b: bool = true;
let not_b = !b;        // false (logical NOT)
```

### Code Examples

```
let a: u32 = 0xCA;      // 1100 1010
let b: u32 = 0xF0;      // 1111 0000

let not_a  = !a;         // 0xFFFFFF35
let and_ab = a & b;      // 0xC0
let or_ab  = a | b;      // 0xFA
let xor_ab = a ^ b;      // 0x3A
```

### Type Safety

Rust enforces that both operands have the same type:

```
let a: u32 = 0xFF;
let b: u8 = 0x0F;
// let c = a & b;       // ERROR: mismatched types
let c = a & (b as u32); // OK
```

### Precedence

Rust has the **same precedence** issue as C — bitwise operators have lower precedence than comparisons:

```
// BUG: evaluates as a & (0x80 == 0x80)
// if a & 0x80 == 0x80 { ... }  // Won't compile due to type mismatch

// CORRECT:
if (a & 0x80) == 0x80 { ... }
```

Rust's type system actually catches many precedence bugs that C would silently accept.

---

## 3. Shift Operators in Rust

### Guaranteed Behavior

Unlike C, Rust **guarantees** shift behavior:

| Type | `>>` Behavior | `<<` Behavior |
| --- | --- | --- |
| `u32` | Logical (fill with 0) | Fill with 0 |
| `i32` | Arithmetic (fill with sign bit) | Fill with 0 |

```
let u: u32 = 0x80000000;
let u_shifted = u >> 4;      // 0x08000000 (logical, always)

let s: i32 = -16;            // 0xFFFFFFF0
let s_shifted = s >> 2;      // -4 = 0xFFFFFFFC (arithmetic, always)
```

No implementation-defined behavior — Rust specifies this.

### NTLang `>-` Operator (Arithmetic Shift Right)

NTLang's `>-` operator forces arithmetic shift. In Rust, cast to `i32`, shift, cast back:

```
// ASR implementation
fn arithmetic_shift_right(value: u32, shift: u32) -> u32 {
    ((value as i32) >> shift) as u32
}
```

In the NTLang evaluator:

```
Operator::Asr => ((left as i32) >> right) as u32,
Operator::Lsr => left >> right,
Operator::Lsl => left << right,
```

### Overflow Protection

Shifting by 32 or more bits panics in debug mode:

```
let x: u32 = 1;
// let y = x << 32;  // PANIC in debug, wrapping in release

// Safe alternative:
let y = x.wrapping_shl(32);  // Always 0, no panic
```

---

## 4. String-to-Integer in Rust

### Using `str::parse()`

For simple cases, Rust provides built-in parsing:

```
let value: u32 = "42".parse().unwrap();     // 42
let hex: u32 = u32::from_str_radix("FF", 16).unwrap();  // 255
let bin: u32 = u32::from_str_radix("1010", 2).unwrap(); // 10
```

### Manual Implementation with Iterators

For NTLang, we implement manual conversion with base detection:

```
pub fn conv_str_to_u32(s: &str) -> Option<u32> {
    let (base, digits) = if s.starts_with("0b") {
        (2, &s[2..])
    } else if s.starts_with("0x") {
        (16, &s[2..])
    } else {
        (10, s)
    };

    let mut value: u32 = 0;
    for c in digits.chars() {
        let digit = c.to_digit(base)?;  // Returns None on invalid
        value = value * base + digit;
    }

    Some(value)
}
```

### Key Rust Features Used

**`chars()` iterator**: Iterates over Unicode characters:

```
for c in "1A3".chars() {
    // c = '1', then 'A', then '3'
}
```

**`to_digit(base)` method**: Converts a character to its digit value in the given base:

```
'A'.to_digit(16)  // Some(10)
'9'.to_digit(10)  // Some(9)
'2'.to_digit(2)   // None (invalid binary digit)
'G'.to_digit(16)  // None (invalid hex digit)
```

**`Option` for error handling**: Instead of C's `exit(-1)`, Rust returns `None` for invalid input:

```
// C approach:
// if (invalid) exit(-1);

// Rust approach:
let digit = c.to_digit(base)?;  // ? propagates None
```

### Comparison with C

| Aspect | C | Rust |
| --- | --- | --- |
| Char-to-digit | Manual: `c - '0'`, `c - 'a' + 10` | `c.to_digit(base)` |
| Error handling | `exit(-1)` | `Option<u32>` / `?` operator |
| String access | `str[i]` (char pointer) | `.chars()` iterator |
| Case handling | `tolower()` | `to_digit()` handles both cases |

---

## 5. Integer-to-String in Rust

### Using `format!` Macro

Rust's `format!` macro handles common cases:

```
let dec = format!("{}", 255);          // "255"
let hex = format!("0x{:X}", 255);     // "0xFF"
let bin = format!("0b{:b}", 255);     // "0b11111111"
```

### Manual Implementation

For NTLang, we implement manual conversion to match the C version's behavior:

```
pub fn conv_u32_to_decstr(value: u32) -> String {
    if value == 0 {
        return String::from("0");
    }

    let mut digits = Vec::new();
    let mut v = value;

    while v > 0 {
        digits.push((b'0' + (v % 10) as u8) as char);
        v /= 10;
    }

    digits.iter().rev().collect()
}
```

### Binary and Hex Conversion

```
pub fn conv_u32_to_binstr(value: u32) -> String {
    if value == 0 {
        return String::from("0b0");
    }

    let mut digits = Vec::new();
    let mut v = value;

    while v > 0 {
        digits.push(if v % 2 == 0 { '0' } else { '1' });
        v /= 2;
    }

    let bits: String = digits.iter().rev().collect();
    format!("0b{}", bits)
}

pub fn conv_u32_to_hexstr(value: u32) -> String {
    let hex_chars = ['0','1','2','3','4','5','6','7',
                     '8','9','A','B','C','D','E','F'];

    if value == 0 {
        return String::from("0x0");
    }

    let mut digits = Vec::new();
    let mut v = value;

    while v > 0 {
        digits.push(hex_chars[(v % 16) as usize]);
        v /= 16;
    }

    let hex: String = digits.iter().rev().collect();
    format!("0x{}", hex)
}
```

### Rust String Operations

| Operation | Rust | C Equivalent |
| --- | --- | --- |
| Create string | `String::from("0b")` | `str[0]='0'; str[1]='b';` |
| Append char | `s.push('A')` | `str[i] = 'A';` |
| Reverse | `.iter().rev().collect()` | Manual swap loop |
| Format | `format!("0x{}", hex)` | `sprintf(str, "0x%s", hex)` |
| Return | Return `String` (owned) | Write to caller's buffer |

---

## 6. Masking and Width in Rust

### Width Mask with `wrapping_shl()`

```
pub fn conv_width_mask(width: u32) -> u32 {
    if width >= 32 {
        return 0xFFFFFFFF;
    }
    1u32.wrapping_shl(width) - 1
}
```

**Why `wrapping_shl()`?** Normal `<<` panics in debug mode when shifting by 32 or more. `wrapping_shl()` always returns 0 for over-shifts, making the math work:

```
1u32.wrapping_shl(32)  // 0 (no panic)
// 0 - 1 would underflow, but we handle width >= 32 separately
```

### Applying the Mask

```
let value: u32 = 0xDEADBEEF;
let mask = conv_width_mask(8);     // 0xFF
let masked = value & mask;         // 0xEF
```

### Pattern Matching for Base Dispatch

```
pub fn conv_u32_to_str(value: u32, base: u32) -> String {
    match base {
        2 => conv_u32_to_binstr(value),
        10 => conv_u32_to_decstr(value),
        16 => conv_u32_to_hexstr(value),
        _ => panic!("Unsupported base: {}", base),
    }
}
```

### Overflow Checking: Debug vs Release

Rust has different overflow behavior depending on build mode:

| Mode | Arithmetic Overflow | Shift Overflow |
| --- | --- | --- |
| Debug (`cargo build`) | Panic | Panic |
| Release (`cargo build --release`) | Wrapping | Wrapping |

For explicit wrapping behavior regardless of mode:

```
let a: u32 = 0xFFFFFFFF;
let b = a.wrapping_add(1);      // 0 (always wraps)
let c = a.wrapping_mul(2);      // 0xFFFFFFFE (always wraps)
let d = 1u32.wrapping_shl(32);  // 0 (always wraps)
```

---

## 7. Signed Output in Rust

### Reinterpreting as Signed with `as i32`

```
let unsigned: u32 = 0xFFFFFFFB;
let signed = unsigned as i32;    // -5 (bit reinterpretation)
```

This doesn't change the bits — it reinterprets them as a two's complement signed value.

### Sign Extension

```
pub fn sign_extend(value: u32, width: u32) -> u32 {
    let msb = width - 1;
    if (value >> msb) & 1 == 1 {
        // MSB is set: fill upper bits with 1
        let mut result = value;
        for i in width..32 {
            result |= 1 << i;
        }
        result
    } else {
        value
    }
}
```

### Signed Output Implementation

```
pub fn print_signed(value: u32, width: u32, base: u32) {
    let mask = conv_width_mask(width);
    let masked = value & mask;

    let msb = width - 1;
    if (masked >> msb) & 1 == 1 {
        // Negative: sign-extend then negate
        let extended = sign_extend(masked, width);
        let positive = (-(extended as i32)) as u32;
        let s = conv_u32_to_str(positive, base);
        print!("-{}", s);
    } else {
        let s = conv_u32_to_str(masked, base);
        print!("{}", s);
    }
}
```

### Using `write!` / `format!` for Output

```
use std::fmt::Write;

fn format_result(value: u32, width: u32, base: u32,
                 unsigned: bool) -> String {
    let mask = conv_width_mask(width);
    let result = value & mask;

    if unsigned {
        conv_u32_to_str(result, base)
    } else {
        let msb = width - 1;
        if (result >> msb) & 1 == 1 {
            let extended = sign_extend(result, width);
            let positive = (-(extended as i32)) as u32;
            format!("-{}", conv_u32_to_str(positive, base))
        } else {
            conv_u32_to_str(result, base)
        }
    }
}
```

### Comparison with C Approach

| Aspect | C | Rust |
| --- | --- | --- |
| Signed reinterpretation | `(int32_t)value` | `value as i32` |
| Negation | `uint32_t pos = -value;` | `(-(val as i32)) as u32` |
| Output | `printf("-%s", str)` | `format!("-{}", s)` |
| String buffer | Caller-allocated `char[]` | Return owned `String` |
| Sign extension loop | `value \|= (1 << i)` | Same, or use arithmetic |

---

## 8. C vs Rust Comparison

### Bitwise Operations

| Aspect | C | Rust |
| --- | --- | --- |
| NOT operator | `~value` | `!value` |
| AND/OR/XOR | `&`, `\|`, `^` | `&`, `\|`, `^` (same) |
| Precedence bug | Silent wrong result | Often caught by type system |
| Type mixing | Implicit promotion | Compile error (must cast) |

### Shift Operations

| Aspect | C | Rust |
| --- | --- | --- |
| `>>` on unsigned | Logical (guaranteed) | Logical (guaranteed) |
| `>>` on signed | Implementation-defined | Arithmetic (guaranteed) |
| Over-shift (by 32+) | Undefined behavior | Panic (debug) / wrap (release) |
| Safe over-shift | Not available | `wrapping_shl()` / `wrapping_shr()` |

### Conversion Functions

| Aspect | C | Rust |
| --- | --- | --- |
| String type | `char*` (mutable buffer) | `String` (owned) / `&str` (borrowed) |
| Char-to-digit | `c - '0'`, `tolower()` | `.to_digit(base)` |
| Error handling | `exit(-1)` | `Option` / `Result` |
| String building | Array indexing + reversal | `Vec` + `.iter().rev().collect()` |
| Format output | `printf("0x%s", buf)` | `format!("0x{}", s)` |

---

## Key Concepts

| Concept | Description |
| --- | --- |
| `u32`, `i32` | Built-in fixed-width types (no import needed) |
| `!` operator | Bitwise NOT on integers (C uses `~`) |
| `as` casting | Bit reinterpretation between same-width types |
| `>>` on `i32` | Always arithmetic shift (guaranteed) |
| `wrapping_shl()` | Safe shift that wraps instead of panicking |
| `to_digit(base)` | Convert char to digit value in given base |
| `Option<T>` | Error handling without `exit(-1)` |
| `.chars().rev().collect()` | Reverse a string via iterator |
| `format!` | String formatting macro |

---

## Practice Problems

### Problem 1: NOT Operator Difference

What does this print in Rust vs C?

```
let x: u8 = 0x0F;
let y = !x;
println!("{:#04X}", y);
```

> **Click to reveal solution**
>
> ```
> Rust: 0xF0 (u8 bitwise NOT of 0x0F)
> 
> In C:
> uint8_t x = 0x0F;
> uint8_t y = ~x;    // y = 0xF0 (same result)
> // But: printf("%X", ~x);  would print FFFFFFF0
> // because ~x promotes to int first!
> 
> Rust avoids this: !x on u8 stays u8 = 0xF0
> ```
> 
> The key difference: C's `~` promotes to `int` before complementing, while Rust's `!` operates at the variable's type.

### Problem 2: Implement `to_digit` Manually

Write a Rust function that converts a char to a digit value for a given base, equivalent to Rust's `.to_digit()`.

> **Click to reveal solution**
>
> ```
> fn char_to_digit(c: char, base: u32) -> Option<u32> {
>     let digit = match c {
>         '0'..='9' => c as u32 - '0' as u32,
>         'a'..='f' => c as u32 - 'a' as u32 + 10,
>         'A'..='F' => c as u32 - 'A' as u32 + 10,
>         _ => return None,
>     };
> 
>     if digit < base {
>         Some(digit)
>     } else {
>         None  // e.g., '5' is not valid in base 2
>     }
> }
> 
> // Test:
> assert_eq!(char_to_digit('A', 16), Some(10));
> assert_eq!(char_to_digit('9', 10), Some(9));
> assert_eq!(char_to_digit('2', 2), None);  // Invalid
> ```

### Problem 3: Wrapping Arithmetic

What happens with each of these in debug mode? In release mode?

```
let a: u32 = 0xFFFFFFFF;
let b = a + 1;
let c = a.wrapping_add(1);
let d = 1u32 << 32;
let e = 1u32.wrapping_shl(32);
```

> **Click to reveal solution**
>
> ```
> Debug mode:
>   b = a + 1           → PANIC (overflow)
>   c = a.wrapping_add(1) → 0 (wraps, no panic)
>   d = 1u32 << 32      → PANIC (shift overflow)
>   e = wrapping_shl(32) → 0 (wraps, no panic)
> 
> Release mode:
>   b = a + 1           → 0 (wraps silently)
>   c = a.wrapping_add(1) → 0 (wraps, same as debug)
>   d = 1u32 << 32      → 0 (wraps silently)
>   e = wrapping_shl(32) → 0 (wraps, same as debug)
> 
> The wrapping_* methods give consistent behavior
> regardless of build mode.
> ```

### Problem 4: Sign Extension Comparison

Write the sign extension for width 4 on value `0x0B` in both C and Rust.

> **Click to reveal solution**
>
> \*\*C:\*\*
> 
> ```
> uint32_t value = 0x0B;
> int width = 4;
> int msb = width - 1;  // 3
> 
> if ((value >> msb) & 1) {
>     for (int i = width; i < 32; i++) {
>         value |= (1 << i);
>     }
> }
> // value = 0xFFFFFFFB = -5 as int32_t
> ```
> 
> \*\*Rust:\*\*
> 
> ```
> let mut value: u32 = 0x0B;
> let width: u32 = 4;
> let msb = width - 1;  // 3
> 
> if (value >> msb) & 1 == 1 {
>     for i in width..32 {
>         value |= 1 << i;
>     }
> }
> // value = 0xFFFFFFFB
> // value as i32 = -5
> ```
> 
> Both are structurally identical. The main difference is Rust's `as i32` for reinterpretation vs C's `(int32\_t)` cast.

---

## Summary

1. **Rust integer types** (`u32`, `i32`, etc.) are built-in with guaranteed widths. The `as` keyword reinterprets bits between types — no implicit widening is allowed.
2. **Bitwise NOT is `!`** in Rust (not `~`). The `!` operator works on both integers (bitwise) and booleans (logical). Other bitwise operators (`&`, `|`, `^`) are the same as C.
3. **Shift behavior is guaranteed**: `>>` on `u32` is always logical, `>>` on `i32` is always arithmetic. Use `wrapping_shl()` / `wrapping_shr()` to avoid panics on over-shifts.
4. **String-to-integer** uses `chars()` iterator and `to_digit(base)` for clean, safe conversion. `Option` replaces C's `exit(-1)` for error handling.
5. **Integer-to-string** uses `Vec<char>` and `.iter().rev().collect()` for reversal. Rust's `String` ownership model means functions return owned strings instead of writing to caller-provided buffers.
6. **Width masking** uses `wrapping_shl()` to safely compute `(1 << width) - 1`. Pattern matching dispatches to the correct conversion function.
7. **Signed output** uses `as i32` for bit reinterpretation and `-(val as i32)` for negation, with `format!` for string output. The logic mirrors the C implementation.