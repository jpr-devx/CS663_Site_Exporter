# Binary and Bases in C

## Overview

This lecture covers the C-specific implementation of binary representation, bitwise operations, and base conversion functions for NTLang. We examine C's fixed-width integer types, bitwise and shift operators with their precedence rules, and the implementation of string-to-integer and integer-to-string conversion functions. We also cover width masking and signed output formatting.

## Learning Objectives

- Use fixed-width integer types from `<stdint.h>` for predictable behavior
- Apply C's bitwise operators (`~`, `&`, `|`, `^`) and understand precedence gotchas
- Implement shift operations and understand signed vs unsigned shift behavior
- Write string-to-integer conversion with base detection and overflow handling
- Implement integer-to-string conversion for decimal, binary, and hexadecimal
- Apply width masking and sign extension for NTLang output formatting

## Prerequisites

- Understanding of binary, hex, and two's complement (previous lecture)
- C programming with pointers and arrays
- Familiarity with the NTLang project structure

---

## 1. C Integer Types and `<stdint.h>`

### Native Integer Types

C's native integer types have **platform-dependent** sizes:

| Type | Typical Size | Guaranteed Minimum |
| --- | --- | --- |
| `char` | 1 byte | 1 byte |
| `short` | 2 bytes | 2 bytes |
| `int` | 4 bytes | 2 bytes |
| `long` | 4 or 8 bytes | 4 bytes |
| `long long` | 8 bytes | 8 bytes |

The size of `int` and `long` varies across platforms, which can cause bugs.

### Fixed-Width Types from `<stdint.h>`

For systems programming, use **fixed-width** types that guarantee exact sizes:

```
#include <stdint.h>

uint32_t value = 42;      /* Exactly 32 bits, unsigned */
int32_t  signed_val = -5; /* Exactly 32 bits, signed */
uint8_t  byte = 0xFF;     /* Exactly 8 bits, unsigned */
int8_t   sbyte = -128;    /* Exactly 8 bits, signed */
uint16_t half = 0xFFFF;   /* Exactly 16 bits, unsigned */
```

### Type Summary for NTLang

| Type | Width | Range | NTLang Use |
| --- | --- | --- | --- |
| `uint32_t` | 32 bits | 0 to 4,294,967,295 | Primary value type |
| `int32_t` | 32 bits | -2,147,483,648 to 2,147,483,647 | Signed interpretation |
| `uint8_t` | 8 bits | 0 to 255 | Single byte/character |

### Using `sizeof`

```
printf("uint32_t is %zu bytes\n", sizeof(uint32_t));  /* Always 4 */
printf("int is %zu bytes\n", sizeof(int));             /* Platform-dependent */
```

---

## 2. Bitwise Operators in C

### The Four Bitwise Operators

| Operator | Name | Example | Result |
| --- | --- | --- | --- |
| `~` | Bitwise NOT | `~0x0F` | `0xFFFFFFF0` |
| `&` | Bitwise AND | `0xCA & 0xF0` | `0xC0` |
| `\|` | Bitwise OR | `0xCA \| 0x0F` | `0xCF` |
| `^` | Bitwise XOR | `0xCA ^ 0xFF` | `0x35` |

### C Code Examples

```
uint32_t a = 0xCA;      /* 1100 1010 */
uint32_t b = 0xF0;      /* 1111 0000 */

uint32_t not_a   = ~a;       /* 0xFFFFFF35 (inverts all 32 bits) */
uint32_t and_ab  = a & b;    /* 0xC0 */
uint32_t or_ab   = a | b;    /* 0xFA */
uint32_t xor_ab  = a ^ b;    /* 0x3A */
```

### Operator Precedence Gotcha

Bitwise operators have **lower precedence** than comparison operators:

```
/* BUG: This checks (a) & (0x80 == 0x80), not (a & 0x80) == 0x80 */
if (a & 0x80 == 0x80) { ... }

/* CORRECT: Use parentheses */
if ((a & 0x80) == 0x80) { ... }
```

**Rule**: Always parenthesize bitwise operations in conditions.

| Precedence (high to low) | Operators |
| --- | --- |
| Arithmetic | `+`, `-`, `*`, `/` |
| Shift | `<<`, `>>` |
| Comparison | `<`, `>`, `==`, `!=` |
| Bitwise | `&`, `^`, `\|` |
| Logical | `&&`, `\|\|` |

---

## 3. Shift Operators in C

### Left Shift (`<<`)

Shifts bits left, filling with zeros:

```
uint32_t x = 1;
uint32_t shifted = x << 4;  /* 0x10 = 16 */
/* 0000 0001 → 0001 0000 */
```

Equivalent to multiplying by \(2^n\).

### Right Shift (`>>`)

**For unsigned types**: logical shift (fills with 0):

```
uint32_t x = 0x80;         /* 1000 0000 */
uint32_t shifted = x >> 4; /* 0x08 = 0000 1000 */
```

**For signed types**: the behavior is **implementation-defined**. Most compilers perform an arithmetic shift (fills with sign bit), but this is not guaranteed by the C standard.

```
int32_t x = -16;           /* 0xFFFFFFF0 */
int32_t shifted = x >> 2;  /* Usually 0xFFFFFFFC = -4 (ASR) */
/* But technically implementation-defined! */
```

### Casting for Arithmetic Shift

To ensure arithmetic shift behavior, cast to signed:

```
uint32_t value = 0xFFFFFFF0;
int32_t signed_result = ((int32_t)value) >> 2;  /* ASR */
```

To ensure logical shift, cast to unsigned:

```
int32_t value = -16;
uint32_t logical_result = ((uint32_t)value) >> 2;  /* LSR */
```

### NTLang Shift Operators

NTLang defines three shift operators:

| NTLang Op | Token | C Equivalent | Description |
| --- | --- | --- | --- |
| `<<` | `TK_LSL` | `<<` | Logical shift left |
| `>>` | `TK_LSR` | `>>` (unsigned) | Logical shift right |
| `>-` | `TK_ASR` | `>>` (signed cast) | Arithmetic shift right |

Implementation of `>-` (ASR) in the evaluator:

```
case OP_ASR:
    result = (uint32_t)(((int32_t)left) >> right);
    break;
```

---

## 4. String-to-Integer in C

### The `conv_str_to_uint32()` Function

This function converts a string representation (decimal, binary, or hex) to a `uint32_t` value.

### Base Detection from Prefix

```
uint32_t conv_str_to_uint32(char *str) {
    int base = 10;      /* Default base */
    int start = 0;      /* Starting index */

    /* Detect base from prefix */
    if (str[0] == '0' && str[1] == 'b') {
        base = 2;       /* Binary: "0b1010" */
        start = 2;
    } else if (str[0] == '0' && str[1] == 'x') {
        base = 16;      /* Hex: "0xFF" */
        start = 2;
    }

    /* ... convert digits ... */
}
```

### Character-to-Digit Conversion

```
int digit;
char c = tolower(str[i]);  /* Handle uppercase hex */

if (c >= '0' && c <= '9') {
    digit = c - '0';       /* '0'→0, '9'→9 */
} else if (c >= 'a' && c <= 'f') {
    digit = c - 'a' + 10;  /* 'a'→10, 'f'→15 */
} else {
    /* Invalid character */
    exit(-1);
}
```

### Right-to-Left Place-Value Approach

```
uint32_t conv_str_to_uint32(char *str) {
    uint32_t value = 0;
    uint32_t place = 1;    /* Current place value (base^i) */
    int base, start;
    int len;

    /* ... base detection (above) ... */

    len = strlen(str);

    /* Process digits right-to-left */
    for (int i = len - 1; i >= start; i--) {
        int digit;
        char c = tolower(str[i]);

        if (c >= '0' && c <= '9') {
            digit = c - '0';
        } else if (c >= 'a' && c <= 'f') {
            digit = c - 'a' + 10;
        } else {
            exit(-1);
        }

        value += digit * place;
        place *= base;
    }

    return value;
}
```

### Overflow Consideration

For 32-bit values, the maximum input is `0xFFFFFFFF` (4,294,967,295). Values larger than this will silently wrap around due to unsigned integer overflow in C, which is well-defined behavior.

---

## 5. Integer-to-String in C

### Overview of Conversion Functions

NTLang needs three conversion functions:

| Function | Output Format | Example |
| --- | --- | --- |
| `conv_uint32_to_decstr()` | Decimal digits | `"255"` |
| `conv_uint32_to_binstr()` | `0b` prefix + binary | `"0b11111111"` |
| `conv_uint32_to_hexstr()` | `0x` prefix + hex | `"0xFF"` |

### Decimal Conversion

```
void conv_uint32_to_decstr(uint32_t value, char *str) {
    char temp[32];
    int i = 0;

    if (value == 0) {
        str[0] = '0';
        str[1] = '\0';
        return;
    }

    /* Extract digits (reverse order) */
    while (value > 0) {
        temp[i] = '0' + (value % 10);
        value /= 10;
        i++;
    }

    /* Reverse into output string */
    int len = i;
    for (int j = 0; j < len; j++) {
        str[j] = temp[len - 1 - j];
    }
    str[len] = '\0';
}
```

### Binary Conversion

```
void conv_uint32_to_binstr(uint32_t value, char *str) {
    char temp[64];
    int i = 0;

    /* Add prefix */
    str[0] = '0';
    str[1] = 'b';

    if (value == 0) {
        str[2] = '0';
        str[3] = '\0';
        return;
    }

    /* Extract bits (reverse order) */
    while (value > 0) {
        temp[i] = '0' + (value % 2);
        value /= 2;
        i++;
    }

    /* Reverse into output after prefix */
    int len = i;
    for (int j = 0; j < len; j++) {
        str[2 + j] = temp[len - 1 - j];
    }
    str[2 + len] = '\0';
}
```

### Hexadecimal Conversion

```
void conv_uint32_to_hexstr(uint32_t value, char *str) {
    char temp[32];
    char hex_digits[] = "0123456789ABCDEF";
    int i = 0;

    /* Add prefix */
    str[0] = '0';
    str[1] = 'x';

    if (value == 0) {
        str[2] = '0';
        str[3] = '\0';
        return;
    }

    /* Extract hex digits (reverse order) */
    while (value > 0) {
        temp[i] = hex_digits[value % 16];
        value /= 16;
        i++;
    }

    /* Reverse into output after prefix */
    int len = i;
    for (int j = 0; j < len; j++) {
        str[2 + j] = temp[len - 1 - j];
    }
    str[2 + len] = '\0';
}
```

---

## 6. Masking and Width in C

### The `conv_width_mask()` Function

Compute a mask for a given bit width:

```
uint32_t conv_width_mask(int width) {
    if (width == 32) {
        return 0xFFFFFFFF;  /* Special case: 1 << 32 is undefined */
    }
    return (1 << width) - 1;
}
```

**Why the special case?** Shifting by the bit width of the type is undefined behavior in C. `1 << 32` for a 32-bit integer is undefined.

### Applying the Mask

```
uint32_t value = 0xDEADBEEF;
uint32_t mask = conv_width_mask(8);   /* 0xFF */
uint32_t masked = value & mask;       /* 0xEF */
```

### Sign Extension

When displaying a value as signed, check the MSB of the masked value and sign-extend:

```
/* Check MSB of the width-bit value */
int msb = width - 1;
if ((value >> msb) & 1) {
    /* MSB is 1: sign-extend by setting upper bits to 1 */
    for (int i = width; i < 32; i++) {
        value |= (1 << i);
    }
}
```

### The `conv_uint32_to_str()` Dispatch Function

The main conversion function selects the appropriate format:

```
void conv_uint32_to_str(uint32_t value, char *str, int base) {
    switch (base) {
        case 2:
            conv_uint32_to_binstr(value, str);
            break;
        case 10:
            conv_uint32_to_decstr(value, str);
            break;
        case 16:
            conv_uint32_to_hexstr(value, str);
            break;
        default:
            exit(-1);
    }
}
```

---

## 7. Signed Output in C

### NTLang Output Flags

NTLang supports several output modes controlled by command-line flags:

| Flag | Meaning | Example Output |
| --- | --- | --- |
| `-b 2` | Binary output | `0b1010` |
| `-b 10` | Decimal output (default) | `10` |
| `-b 16` | Hex output | `0xA` |
| `-w N` | Width in bits | (affects masking) |
| `-u` | Unsigned output | `4294967286` |
| (default) | Signed output | `-10` |

### MSB Check for Sign

```
/* After masking to width bits: */
uint32_t mask = conv_width_mask(width);
uint32_t masked = value & mask;

/* Check if MSB of masked value is set */
int msb = width - 1;
bool is_negative = (masked >> msb) & 1;
```

### Signed Output Implementation

```
void conv_print_signed(uint32_t value, int width, int base) {
    uint32_t mask = conv_width_mask(width);
    value = value & mask;
    char str[64];

    int msb = width - 1;
    if ((value >> msb) & 1) {
        /* Negative: sign-extend to 32 bits, then negate */
        for (int i = width; i < 32; i++) {
            value |= (1 << i);
        }
        /* Now value is the 32-bit two's complement representation */
        uint32_t positive = -value;  /* Negate using unsigned arithmetic */
        conv_uint32_to_str(positive, str, base);
        printf("-%s", str);
    } else {
        /* Positive: just convert */
        conv_uint32_to_str(value, str, base);
        printf("%s", str);
    }
}
```

### Complete NTLang Output Logic

```
uint32_t mask = conv_width_mask(width);
uint32_t result = eval(tree) & mask;
char str[64];

if (unsigned_flag) {
    /* -u flag: print as unsigned */
    conv_uint32_to_str(result, str, base);
    printf("%s\n", str);
} else {
    /* Default: print as signed */
    conv_print_signed(result, width, base);
    printf("\n");
}
```

---

## 8. C vs Rust Comparison

| Aspect | C | Rust |
| --- | --- | --- |
| Fixed-width types | `uint32_t` from `<stdint.h>` | `u32` built-in |
| NOT operator | `~` | `!` |
| Signed right shift | Implementation-defined | Always arithmetic for `i32` |
| Overflow behavior | Undefined (signed), wrapping (unsigned) | Panic in debug, wrapping in release |
| String conversion | Manual `char` array manipulation | `format!` macro or manual |
| Error handling | `exit(-1)` | `Result`/`Option` types |
| Type casting | `(int32_t)value` | `value as i32` |

---

## Key Concepts

| Concept | Description |
| --- | --- |
| `<stdint.h>` | Fixed-width integer types (`uint32_t`, `int32_t`) |
| Bitwise operators | `~`, `&`, `\|`, `^` operate on individual bits |
| Precedence gotcha | Bitwise ops have lower precedence than comparisons |
| `>>` on signed | Implementation-defined in C (usually ASR) |
| `conv_str_to_uint32()` | String to integer with base detection |
| `conv_uint32_to_*str()` | Integer to string (dec, bin, hex) |
| `conv_width_mask()` | `(1 << w) - 1` with special case for w=32 |
| Sign extension | Set upper bits to 1 for negative values |
| `value = -value` | Unsigned negation wraps correctly |

---

## Practice Problems

### Problem 1: Precedence Bug

What does this print? How do you fix it?

```
uint32_t flags = 0xFF;
if (flags & 0x10 != 0) {
    printf("bit 4 is set\n");
}
```

> **Click to reveal solution**
>
> \*\*Bug\*\*: `!=` has higher precedence than `&`, so this evaluates as `flags & (0x10 != 0)` which is `flags & 1` = `0xFF & 0x01` = `1` (truthy, but for the wrong reason).
> \*\*Fix\*\*: Add parentheses:
> 
> ```
> if ((flags & 0x10) != 0) {
>     printf("bit 4 is set\n");
> }
> ```
> 
> Both versions happen to print the message for `0xFF`, but for `flags = 0x20`, the buggy version would still print (checking bit 0), while the fixed version correctly wouldn't.

### Problem 2: Implement Hex String-to-Integer

Write a function that converts a hex string (without `0x` prefix) to `uint32_t` using the left-to-right algorithm.

> **Click to reveal solution**
>
> ```
> uint32_t hex_to_uint32(char *str) {
>     uint32_t value = 0;
> 
>     for (int i = 0; str[i] != '\0'; i++) {
>         int digit;
>         char c = tolower(str[i]);
> 
>         if (c >= '0' && c <= '9') {
>             digit = c - '0';
>         } else if (c >= 'a' && c <= 'f') {
>             digit = c - 'a' + 10;
>         } else {
>             exit(-1);  /* Invalid character */
>         }
> 
>         value = value * 16 + digit;
>     }
> 
>     return value;
> }
> 
> /* Test: hex_to_uint32("1A3") returns 419 */
> ```

### Problem 3: Width Mask Edge Cases

What does `conv_width_mask()` return for widths 1, 4, 8, and 32?

> **Click to reveal solution**
>
> ```
> Width 1:  (1 << 1) - 1  = 2 - 1   = 1          = 0x00000001
> Width 4:  (1 << 4) - 1  = 16 - 1  = 15         = 0x0000000F
> Width 8:  (1 << 8) - 1  = 256 - 1 = 255        = 0x000000FF
> Width 32: special case              = 4294967295 = 0xFFFFFFFF
> ```
> 
> The width-32 case must be handled separately because `1 << 32` is undefined behavior in C (shifting by the full width of the type).

### Problem 4: Sign Extension by Hand

Apply sign extension to the value `0x0B` with width 4. What is the 32-bit signed result?

> **Click to reveal solution**
>
> ```
> Value: 0x0B = 0000 1011
> Width: 4, so we only care about bits 3-0: 1011
> 
> MSB of 4-bit value (bit 3) = 1 → negative
> 
> Sign extend: set bits 4-31 to 1
>   Before: 0000 0000 0000 0000 0000 0000 0000 1011
>   After:  1111 1111 1111 1111 1111 1111 1111 1011
>         = 0xFFFFFFFB
> 
> As signed 32-bit: -5
> 
> Verify: in 4-bit two's complement, 1011 = -5 ✓
> ```

---

## Summary

1. **Fixed-width types** from `<stdint.h>` (`uint32_t`, `int32_t`) ensure predictable sizes across platforms, unlike native `int` and `long`.
2. **Bitwise operators** (`~`, `&`, `|`, `^`) work on individual bits. Always parenthesize them in conditions due to precedence rules.
3. **Shift operators** (`<<`, `>>`) multiply/divide by powers of 2. Right shift on signed types is implementation-defined in C — use explicit casts when you need guaranteed behavior.
4. **String-to-integer conversion** detects the base from prefix (`0b`, `0x`), converts characters to digits, and accumulates the value using place values.
5. **Integer-to-string conversion** uses division/modulo to extract digits in reverse order, then reverses the result. Separate functions handle decimal, binary, and hex output.
6. **Width masking** with `(1 << w) - 1` isolates the lower bits. The width-32 case needs special handling to avoid undefined behavior.
7. **Signed output** checks the MSB of the masked value, sign-extends if negative, negates to get the positive magnitude, and prepends a `-` sign.