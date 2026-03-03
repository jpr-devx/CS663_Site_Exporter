# NTlang - Number Tool Language

**Due Wed Feb 25th by 11:59pm in your Project01 GitHub repo**

## Links

Tests: <https://github.com/USF-CS631-S26/tests>

## Background

The goal of this project is to implement a command line program that can interpret NTlang expressions and scripts for working with different number bases and bit widths. You will implement NTlang in both C and Rust. Your project repo should have a `c/` directory for your C implementation and a `rust/` directory for your Rust implementation. This tool will also be handy later on when working on other projects to do various types of number conversions and bit twiddling.

## Requirements

1. You will implement NTlang in both C and Rust. The automated tests expect:

   - C binary at `./c/project01`
   - Rust binary at `./rust/target/debug/project01`
2. Start with expression mode (`-e`) in Section 1, then add script file support in Section 2.
3. You will write the scanner and parser yourself, without using C `strtok()` or `scanf()` or compiler generators such as lex, yacc, bison, antlr, etc.
4. You will write the base conversion tools yourself without using C `printf("%d", i)`, `printf("%x", i)`, or `strtol()`. That is, you must write conversion functions that convert binary forms into strings, then you can only use `printf("%s", str)` to output the converted string.
5. For Rust, the equivalent restrictions apply: do not use `format!` with `{:x}`, `{:b}`, `{:o}`, or `{:d}` for base conversion. Write your own conversion functions.

## Section 1: NTLang Expressions

### Command Line Options

| Option | Description | Valid Values | Default |
| --- | --- | --- | --- |
| `-e expression` | Evaluate an expression | any NTlang expression | (required for expression mode) |
| `-b base` | Output base | 2, 10, 16 | 10 |
| `-w width` | Output bit width | 4, 8, 16, 32 | 32 |
| `-u` | Unsigned output (only affects `-b 10`) |  |  |

### Examples

Basic arithmetic:

```
$ ./project01 -e "1 + 2"
3
$ ./project01 -e "10 + 1"
11
```

Hex output:

```
$ ./project01 -e "10" -b 16
0x0000000A
$ ./project01 -e "10 + 1" -b 16
0x0000000B
```

Width control:

```
$ ./project01 -e "10" -b 16 -w 16
0x000A
```

Binary output:

```
$ ./project01 -e "10" -b 2
0b00000000000000000000000000001010
$ ./project01 -e "10" -b 2 -w 4
0b1010
```

Hex input:

```
$ ./project01 -e "0x0A" -b 10
10
$ ./project01 -e "0x0A" -b 2 -w 8
0b00001010
```

Nested expressions:

```
$ ./project01 -e "((1 + 1) * 1)" -b 16 -w 16
0x0002
$ ./project01 -e "((1 + 1) * 1)" -b 2 -w 8
0b00000010
```

Width truncation with shift:

```
$ ./project01 -e "(1 << 16)" -b 10 -w 32
65536
$ ./project01 -e "(1 << 16)" -b 10 -w 16
0
$ ./project01 -e "(1 << 16)" -b 16 -w 32
0x00010000
```

Bitwise operations:

```
$ ./project01 -b 10 -w 8 -e "(2 * (0b1111 & 0b1010))"
20
```

Signed and unsigned output:

```
$ ./project01 -b 10 -w 8 -e "0b00001000"
8
$ ./project01 -b 10 -w 4 -e "0b00001000"
-8
$ ./project01 -b 10 -u -w 4 -e "0b00001000"
8
```

Arithmetic shift right:

```
$ ./project01 -b 10 -w 8 -e "-128 >- 2"
-32
```

Complex expression:

```
$ ./project01 -e "(((((~((-(2 * ((1023 + 1) / 4)) >- 2) << 8)) >> 10) ^ 0b01110) & 0x1E) | ~(0b10000))"
-1
```

Overflow detection:

```
$ ./project01 -e "0xffffffff"
-1
$ ./project01 -e "0xffffffff1"
overflows uint32_t: ffffffff1
$ ./project01 -e "0x000000000ffffffff"
-1
```

### Scanner EBNF

```
whitespace  ::=  (' ' | '\t') (' ' | '\t')*

tokenlist   ::= (token)*
token       ::= intlit | hexlit | binlit | symbol
symbol      ::= '+' | '-' | '*' | '/' | '>>' | '>-' | '<<' | '~' | '&' | '|' | '^'
intlit      ::= digit (digit)*
hexlit      ::= '0x' hexdigit (hexdigit)*
binlit      ::= '0b' ['0', '1'] (['0', '1'])*
hexdigit    ::= 'a' | ... | 'f' | 'A' | ... | 'F' | digit
digit       ::= '0' | ... | '9'
```

### Parser EBNF

```
program    ::= expression EOT

expression ::= operand (operator operand)*

operand    ::= intlit
             | hexlit
             | binlit
             | '-' operand
             | '~' operand
             | '(' expression ')'

operator   ::= '+' | '-' | '*' | '/' | '>>' | '<<' | '&' | '|' | '^' | '>-'
```

### Operators

```
Binary operators:

>>   logical shift right
>-   arithmetic shift right (note that C does not have this operator)
<<   logical shift left
&    bitwise and
|    bitwise or
^    bitwise xor

Unary operators:

~    bitwise not
```

### Interpreter

1. Your interpreter will walk the AST depth-first, evaluating the expressions defined by the nodes, and printing the results.
2. Store intermediate results in a C `uint32_t` (or Rust `u32`) to make conversion to binary or hexadecimal easy.
3. When evaluating, you will need to typecast `uint32_t` values into a signed value for some operators, such as `-` and `>-`.
4. The width parameter controls how many bits wide the output should be. For `-b 2` and `-b 16`, this controls the number of output digits. For `-b 10`, the value is sign-extended (or zero-extended with `-u`) to the given width before printing.

## Section 2: NTLang Scripts

### Overview

In addition to expression mode, NTlang supports executing programs from `.ntl` script files. Scripts add variables, assignment statements, print statements, and comments.

### Command Line

```
$ ./project01 <filename.ntl>
```

When a filename (without `-e`) is given as a command line argument, NTlang reads and executes the script file.

### Extended Scanner EBNF

Add the following to the Section 1 scanner:

```
token      ::= ... | ident | assign | comma
ident      ::= alpha (alpha | '_')*
alpha      ::= 'a' | ... | 'z' | 'A' | ... | 'Z'
assign     ::= '='
comma      ::= ','
comment    ::= '#' (any)* '\n'
newline    ::= '\n'
```

Comments begin with `#` and extend to the end of the line. They should be ignored by the scanner.

### Extended Parser EBNF

```
program    ::= (statement '\n')* EOT

statement  ::= assignment | print_statement

assignment ::= ident '=' expression

print_statement ::= 'print' '(' expression ',' expression ',' expression ')'

expression ::= operand (operator operand)*

operand    ::= intlit | hexlit | binlit | ident
             | '-' operand | '~' operand
             | '(' expression ')'
```

The `print` statement takes three arguments: `print(expression, base, width)` where base is 2, 10, or 16 and width is 4, 8, 16, or 32. For base 10 output, values are printed as signed.

### Script Examples

**p1.ntl** - Basic variable assignment and print:

```
x = 1 + 2
print(x, 10, 32)
print(x, 2, 32)
print(x, 16, 32)
print(x, 2, 4)
print(x, 16, 4)
```

```
$ ./project01 p1.ntl
3
0b00000000000000000000000000000011
0x00000003
0b0011
0x3
```

**p2.ntl** - Quadratic equation:

```
# Quadratic equation

x = 7
a = 3
b = 4
c = 5

q = (a * x * x) + (b * x) + c

print(q, 10, 32)
```

```
$ ./project01 p2.ntl
180
```

**p3.ntl** - Two's complement:

```
# Two's Complement

x = 241
y = (~x) + 1

print(x, 10, 32)
print(x, 2, 32)
print(y, 10, 32)
print(y, 2, 32)
print((~x) + 1, 10, 32)
print((~x) + 1, 2, 32)
```

```
$ ./project01 p3.ntl
241
0b00000000000000000000000011110001
-241
0b11111111111111111111111100001111
-241
0b11111111111111111111111100001111
```

**p4.ntl** - Expression with print:

```
x = (2 * 3) + 4
print(x, 10, 32)
```

```
$ ./project01 p4.ntl
10
```

## Grading

Tests: <https://github.com/USF-CS631-S26/tests>

Grading is based on automated tests (100 points total):

| Tests | Points | Description |
| --- | --- | --- |
| c-01 to c-04 | 4 | C: basic arithmetic and hex output (1 pt each) |
| c-05 to c-23 | 38 | C: base conversion, width, bitwise ops, overflow (2 pts each) |
| c-24 to c-27 | 8 | C: script file execution (2 pts each) |
| rust-01 to rust-04 | 4 | Rust: basic arithmetic and hex output (1 pt each) |
| rust-05 to rust-23 | 38 | Rust: base conversion, width, bitwise ops, overflow (2 pts each) |
| rust-24 to rust-27 | 8 | Rust: script file execution (2 pts each) |
| **Total** | **100** |  |

## Code Quality

Code quality deductions may be applied and can be earned back. We are looking for:

- Consistent spacing and indentation
- Consistent naming and commenting
- No commented-out ("dead") code
- No redundant or overly complicated code
- A clean repo, that is no build products, extra files, etc.