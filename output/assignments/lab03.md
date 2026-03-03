# Introduction to RISC-V Assembly Programming

**Due Wed Mar 4th by 11:59pm in your Lab03 GitHub repo**

## Links

Tests: <https://github.com/USF-CS631-S26/tests>

## Overview

In this lab you will be introduced to RISC-V assembly programming. You will be given Rust programs that contain a Rust implementation of a simple function and a declaration of an external assembly function. Your job is to write the equivalent RISC-V assembly implementation in `.s` files. Each program compares the output of the Rust implementation and your assembly implementation to verify correctness.

There are six programs to implement: `add4`, `quadratic`, `min`, `findmax`, `grade`, and `sum_to_n`.

## Programs

### add4

Adds four 32-bit integers together and returns the result.

```
$ cargo run --bin add4 -- 1 2 3 4
Rust: 10
Asm: 10
```

### quadratic

Runs the quadratic equation (ax^2 + bx + c) on the 32-bit integers x, a, b, c and returns the result.

```
$ cargo run --bin quadratic -- 4 3 2 1
Rust: 57
Asm: 57
```

### min

Calculates the smaller of two 32-bit integers and returns its value.

```
$ cargo run --bin min -- 2 3
Rust: 2
Asm: 2
```

### findmax

Finds the maximum integer in an array.

```
$ cargo run --bin findmax -- 1 2 99 4 5
Rust: 99
Asm: 99
```

### grade

Given a score (0-100), return a letter grade value:

- `score >= 90` → 4 (A)
- `score >= 80` → 3 (B)
- `score >= 70` → 2 (C)
- `score >= 60` → 1 (D)
- otherwise → 0 (F)

```
$ cargo run --bin grade -- 85
Rust: 3
Asm: 3
```

### sum\_to\_n

Sum integers from 1 to n.

```
$ cargo run --bin sum_to_n -- 10
Rust: 55
Asm: 55
```

## Given Code

Your Lab03 repo will have the following structure:

```
Cargo.toml
build.rs
src/bin/add4.rs
src/bin/quadratic.rs
src/bin/min.rs
src/bin/findmax.rs
src/bin/grade.rs
src/bin/sum_to_n.rs
asm/add4_s.s          (student fills in)
asm/quadratic_s.s     (student fills in)
asm/min_s.s           (student fills in)
asm/findmax_s.s       (student fills in)
asm/grade_s.s         (student fills in)
asm/sum_to_n_s.s      (student fills in)
```

The Rust source files and build configuration are provided. Your job is to fill in the assembly files in the `asm/` directory.

## Cargo.toml

```
[package]
name = "lab03"
version = "0.1.0"
edition = "2021"

[build-dependencies]
cc = "1"

[[bin]]
name = "add4"
path = "src/bin/add4.rs"

[[bin]]
name = "quadratic"
path = "src/bin/quadratic.rs"

[[bin]]
name = "min"
path = "src/bin/min.rs"

[[bin]]
name = "findmax"
path = "src/bin/findmax.rs"

[[bin]]
name = "grade"
path = "src/bin/grade.rs"

[[bin]]
name = "sum_to_n"
path = "src/bin/sum_to_n.rs"
```

The `[build-dependencies]` section includes the `cc` crate, which is used to compile the assembly files into a library that Rust can link against. Each `[[bin]]` section defines one of the six programs.

## build.rs

```
fn main() {
    cc::Build::new()
        .file("asm/add4_s.s")
        .file("asm/quadratic_s.s")
        .file("asm/min_s.s")
        .file("asm/findmax_s.s")
        .file("asm/grade_s.s")
        .file("asm/sum_to_n_s.s")
        .compile("asm_functions");

    println!("cargo:rerun-if-changed=asm/add4_s.s");
    println!("cargo:rerun-if-changed=asm/quadratic_s.s");
    println!("cargo:rerun-if-changed=asm/min_s.s");
    println!("cargo:rerun-if-changed=asm/findmax_s.s");
    println!("cargo:rerun-if-changed=asm/grade_s.s");
    println!("cargo:rerun-if-changed=asm/sum_to_n_s.s");
}
```

The `build.rs` file is a Cargo build script that runs before compilation. It uses the `cc` crate to compile all six assembly files into a static library called `asm_functions`. The `cargo:rerun-if-changed` lines tell Cargo to re-run the build script when any assembly file changes.

## Rust Source Files

Here is the `add4.rs` source file as an example:

```
use std::env;
use std::process;

extern "C" {
    fn add4_s(a: i32, b: i32, c: i32, d: i32) -> i32;
}

fn add4(a: i32, b: i32, c: i32, d: i32) -> i32 {
    a + b + c + d
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 5 {
        println!("usage: add4 a b c d");
        process::exit(-1);
    }

    let a: i32 = args[1].parse().unwrap_or(0);
    let b: i32 = args[2].parse().unwrap_or(0);
    let c: i32 = args[3].parse().unwrap_or(0);
    let d: i32 = args[4].parse().unwrap_or(0);

    let rust_result = add4(a, b, c, d);
    println!("Rust: {}", rust_result);

    let s_result = unsafe { add4_s(a, b, c, d) };
    println!("Asm: {}", s_result);
}
```

The key parts are:

- **`extern "C" { fn add4_s(...) -> i32; }`** - This declares an external function `add4_s` that follows the C calling convention. This is the assembly function you will implement.
- **`fn add4(...)`** - This is the Rust reference implementation. Your assembly should produce the same result.
- **`unsafe { add4_s(a, b, c, d) }`** - Calling the external assembly function requires `unsafe` because Rust cannot verify the safety of foreign functions.

The other source files (`quadratic.rs`, `min.rs`, `findmax.rs`, `grade.rs`, `sum_to_n.rs`) follow the same pattern with the appropriate arguments and operations.

## RISC-V Assembly Basics

### Calling Convention

RISC-V uses registers to pass arguments and return values:

| Register | Usage |
| --- | --- |
| `a0` | First argument / return value |
| `a1` | Second argument |
| `a2` | Third argument |
| `a3` | Fourth argument |

Temporary registers `t0`-`t6` can be used freely for intermediate calculations.

### Key Instructions

| Instruction | Description | Example |
| --- | --- | --- |
| `add rd, rs1, rs2` | rd = rs1 + rs2 | `add a0, a0, a1` |
| `mul rd, rs1, rs2` | rd = rs1 \* rs2 | `mul a0, a0, a1` |
| `mv rd, rs` | rd = rs (copy register) | `mv a0, a1` |
| `li rd, imm` | rd = immediate value | `li t0, 1` |
| `addi rd, rs, imm` | rd = rs + immediate | `addi t0, t0, 1` |
| `lw rd, (rs)` | Load word from memory | `lw t0, (a0)` |
| `slli rd, rs, imm` | Shift left logical immediate | `slli t0, t0, 2` |
| `blt rs1, rs2, label` | Branch if rs1 < rs2 | `blt a0, a1, skip` |
| `beq rs1, rs2, label` | Branch if rs1 == rs2 | `beq t0, a1, done` |
| `ble rs1, rs2, label` | Branch if rs1 <= rs2 | `ble t0, t1, next` |
| `j label` | Unconditional jump | `j loop` |
| `ret` | Return to caller | `ret` |

### Assembly File Format

Each assembly file should declare a global function and implement it. Here is the structure:

```
.global function_name

function_name:
    # your instructions here
    ret
```

The `.global` directive makes the function visible to the linker so Rust can call it. The function name must match the `extern "C"` declaration in the Rust source (e.g., `add4_s`, `quadratic_s`, `min_s`, `findmax_s`, `grade_s`, `sum_to_n_s`).

### Example

For `add4_s`, you need to add the values in `a0`, `a1`, `a2`, and `a3` and return the result in `a0`:

```
.global add4_s

add4_s:
    add a0, a0, a1
    add a0, a0, a2
    add a0, a0, a3
    ret
```

## Autograder

To run the Autograder tests for Lab03:

```
$ grade test -p lab03
```

Or if you are in your `lab03-<gitid>` repo:

```
$ grade test
```

## Code Submission

You will submit your code in your Lab03 GitHub repo. You will be provided a link to create your repo. Your goal is to complete the six assembly files in the `asm/` directory. There is a default `.gitignore` that should prevent the inclusion of any binary files into your repo.

## Rubric

100% Lab03 autograder tests.