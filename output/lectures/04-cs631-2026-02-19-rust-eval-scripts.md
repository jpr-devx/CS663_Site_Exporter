# Evaluation and Scripts in Rust

## Overview

This lecture covers the Rust-specific implementation of AST evaluation and script execution for NTLang. We examine Rust's enum-based AST representation, HashMap-based environment implementation, pattern matching for evaluation, and idiomatic error handling. We also cover mutable references for environment passing, Option types for variable lookup, and wrapping arithmetic for u32 operations.

## Learning Objectives

- Design Rust enums for AST nodes using pattern matching
- Implement HashMap-based symbol table for O(1) lookup
- Use mutable references (`&mut`) for environment threading
- Apply pattern matching for recursive evaluation
- Handle Option types for variable lookup
- Use wrapping arithmetic for u32 operations
- Implement idiomatic Rust error handling with Result/panic
- Integrate evaluation with Rust's ownership system

## Prerequisites

- Understanding of AST evaluation and environments (previous lecture)
- Rust programming basics (enums, pattern matching, ownership)
- Binary and base conversion in Rust
- Familiarity with the NTLang project structure

---

## 1. AST Representation in Rust

### ParseNode Enum

Rust uses enums with associated data for AST nodes:

```
pub enum ParseNode {
    IntLit(u32),
    HexLit(u32),
    BinLit(u32),
    Ident(String),
    UnaryOp {
        op: UnaryOp,
        operand: Box<ParseNode>,
    },
    BinaryOp {
        op: BinaryOp,
        left: Box<ParseNode>,
        right: Box<ParseNode>,
    },
    Assign {
        name: String,
        expr: Box<ParseNode>,
    },
    Print {
        expr: Box<ParseNode>,
        base: Box<ParseNode>,
        width: Box<ParseNode>,
    },
}
```

### Operator Enums

```
pub enum UnaryOp {
    Neg,   // -
    Not,   // ~
}

pub enum BinaryOp {
    Add,   // +
    Sub,   // -
    Mul,   // *
    Div,   // /
    Shr,   // >>
    Shl,   // <<
    And,   // &
    Or,    // |
    Xor,   // ^
    Asr,   // >- (arithmetic shift right)
}
```

### Box for Heap Allocation

`Box<ParseNode>` allocates child nodes on the heap:

```
let node = ParseNode::BinaryOp {
    op: BinaryOp::Add,
    left: Box::new(ParseNode::IntLit(2)),
    right: Box::new(ParseNode::IntLit(3)),
};
```

**Why Box?**

- Recursive types need indirection
- Prevents infinite size at compile time
- Enables tree structures

---

## 2. Environment with HashMap

### HashMap-Based Symbol Table

```
use std::collections::HashMap;

pub type Environment = HashMap<String, u32>;
```

Idiomatic Rust: use built-in HashMap for O(1) lookup.

### Creating an Environment

```
fn main() {
    let mut env = HashMap::new();

    env.insert("x".to_string(), 10);
    env.insert("y".to_string(), 20);

    println!("{:?}", env);
}
```

### HashMap Operations

| Operation | Method | Example |
| --- | --- | --- |
| Insert/Update | `insert(key, value)` | `env.insert("x".to_string(), 10)` |
| Lookup | `get(key)` | `env.get("x")` → `Some(&10)` |
| Check existence | `contains_key(key)` | `env.contains_key("x")` → `true` |
| Remove | `remove(key)` | `env.remove("x")` → `Some(10)` |

---

## 3. Variable Lookup with Option

### Option Type

Rust's `Option<T>` represents a value that might not exist:

```
enum Option<T> {
    Some(T),
    None,
}
```

### Lookup Returns Option

```
fn lookup_var(env: &Environment, name: &str) -> u32 {
    match env.get(name) {
        Some(&value) => value,
        None => {
            eprintln!("Error: undefined variable '{}'", name);
            std::process::exit(1);
        }
    }
}
```

**Alternative with `expect`**:

```
fn lookup_var(env: &Environment, name: &str) -> u32 {
    *env.get(name)
        .unwrap_or_else(|| {
            eprintln!("Error: undefined variable '{}'", name);
            std::process::exit(1)
        })
}
```

### Idiomatic Pattern

```
let value = env.get(name)
    .copied()
    .unwrap_or_else(|| panic!("undefined variable: {}", name));
```

- `.copied()` converts `Option<&u32>` → `Option<u32>`
- `.unwrap_or_else()` provides error handling

---

## 4. Expression Evaluation

### Main Evaluation Function

```
pub fn eval_expression(node: &ParseNode, env: &mut Environment) -> u32 {
    match node {
        ParseNode::IntLit(val) => *val,
        ParseNode::HexLit(val) => *val,
        ParseNode::BinLit(val) => *val,

        ParseNode::Ident(name) => lookup_var(env, name),

        ParseNode::UnaryOp { op, operand } => {
            eval_unary(*op, operand, env)
        }

        ParseNode::BinaryOp { op, left, right } => {
            eval_binary(*op, left, right, env)
        }

        _ => panic!("Invalid expression node type"),
    }
}
```

Pattern matching on enums is exhaustive — compiler ensures all cases are handled.

### Literal Evaluation

```
ParseNode::IntLit(val) => *val,
```

Dereference the value from the enum variant.

### Identifier Evaluation

```
ParseNode::Ident(name) => lookup_var(env, name),
```

Call helper function to lookup variable.

---

## 5. Unary Operations

### Unary Evaluation

```
fn eval_unary(op: UnaryOp, operand: &ParseNode,
              env: &mut Environment) -> u32 {
    let val = eval_expression(operand, env);

    match op {
        UnaryOp::Neg => {
            // Negate as signed, return as unsigned
            (-(val as i32)) as u32
        }
        UnaryOp::Not => !val,
    }
}
```

### Type Casting for Negation

```
let x: u32 = 5;
let neg_x = (-(x as i32)) as u32;
// neg_x = 0xFFFFFFFB = -5 in two's complement
```

**Steps**:

1. Cast `u32` → `i32`
2. Apply unary `-`
3. Cast back to `u32`

### Bitwise NOT

```
UnaryOp::Not => !val,
```

Rust uses `!` for both logical and bitwise NOT (context-dependent).

---

## 6. Binary Operations

### Binary Evaluation

```
fn eval_binary(op: BinaryOp, left: &ParseNode,
               right: &ParseNode, env: &mut Environment) -> u32 {
    let left_val = eval_expression(left, env);
    let right_val = eval_expression(right, env);

    match op {
        BinaryOp::Add => left_val.wrapping_add(right_val),
        BinaryOp::Sub => left_val.wrapping_sub(right_val),
        BinaryOp::Mul => left_val.wrapping_mul(right_val),
        BinaryOp::Div => {
            if right_val == 0 {
                panic!("division by zero");
            }
            left_val / right_val
        }
        BinaryOp::Shr => left_val >> right_val,
        BinaryOp::Shl => left_val << right_val,
        BinaryOp::And => left_val & right_val,
        BinaryOp::Or => left_val | right_val,
        BinaryOp::Xor => left_val ^ right_val,
        BinaryOp::Asr => {
            ((left_val as i32) >> right_val) as u32
        }
    }
}
```

### Wrapping Arithmetic

Rust distinguishes between:

| Operation | Behavior |
| --- | --- |
| `+`, `-`, `*` | **Panics** on overflow in debug mode |
| `.wrapping_add()` | Wraps on overflow (two's complement) |
| `.checked_add()` | Returns `Option<u32>` |
| `.saturating_add()` | Clamps to min/max |

**For NTLang**: Use wrapping arithmetic to match u32 semantics.

```
let a: u32 = 0xFFFFFFFF;
let b: u32 = 1;
let c = a.wrapping_add(b);  // 0
```

### Arithmetic Shift Right

```
BinaryOp::Asr => {
    ((left_val as i32) >> right_val) as u32
}
```

Cast to `i32` to preserve sign bit during shift.

---

## 7. Statement Evaluation

### Statement Enum

```
pub enum Statement {
    Assign { name: String, expr: ParseNode },
    Print { expr: ParseNode, base: ParseNode, width: ParseNode },
}
```

Or use `ParseNode` directly for statements (as shown earlier).

### Statement Dispatch

```
pub fn eval_statement(node: &ParseNode, env: &mut Environment) {
    match node {
        ParseNode::Assign { name, expr } => {
            let value = eval_expression(expr, env);
            env.insert(name.clone(), value);
        }

        ParseNode::Print { expr, base, width } => {
            let value = eval_expression(expr, env);
            let base_val = eval_expression(base, env);
            let width_val = eval_expression(width, env);
            print_formatted(value, base_val, width_val);
        }

        _ => panic!("Invalid statement node type"),
    }
}
```

### Assignment Evaluation

```
ParseNode::Assign { name, expr } => {
    let value = eval_expression(expr, env);
    env.insert(name.clone(), value);
}
```

`HashMap::insert` performs upsert automatically.

### String Cloning

```
env.insert(name.clone(), value);
```

`clone()` creates a new `String` owned by the HashMap.

---

## 8. Mutable References

### Passing Environment

The environment must be mutable:

```
fn eval_expression(node: &ParseNode, env: &mut Environment) -> u32
```

`&mut Environment` means:

- Mutable reference
- Only one mutable reference at a time
- Can modify the HashMap

### Ownership Rules

```
let mut env = HashMap::new();

eval_statement(&stmt1, &mut env);  // Borrows env mutably
eval_statement(&stmt2, &mut env);  // OK: previous borrow ended
```

Multiple sequential mutable borrows are allowed.

### Immutable vs Mutable

| Reference Type | Syntax | Can Modify |
| --- | --- | --- |
| Immutable | `&T` | No |
| Mutable | `&mut T` | Yes |

For lookup-only: `&Environment`

For insert/update: `&mut Environment`

---

## 9. Print Formatting

### Print Function

```
fn print_formatted(value: u32, base: u32, width: u32) {
    if ![2, 10, 16].contains(&base) {
        panic!("base must be 2, 10, or 16");
    }
    if ![4, 8, 16, 32].contains(&width) {
        panic!("width must be 4, 8, 16, or 32");
    }

    let masked = apply_width_mask(value, width);

    match base {
        10 => {
            let signed = sign_extend(masked, width);
            println!("{}", signed);
        }
        16 => {
            let hex_str = format_hex(masked, width);
            println!("0x{}", hex_str);
        }
        2 => {
            let bin_str = format_binary(masked, width);
            println!("0b{}", bin_str);
        }
        _ => unreachable!(),
    }
}
```

### Width Masking

```
fn apply_width_mask(value: u32, width: u32) -> u32 {
    if width == 32 {
        value
    } else {
        let mask = (1u32 << width) - 1;
        value & mask
    }
}
```

### Sign Extension

```
fn sign_extend(value: u32, width: u32) -> i32 {
    let masked = apply_width_mask(value, width);
    let sign_bit = 1u32 << (width - 1);

    if masked & sign_bit != 0 {
        // Negative: sign extend
        let extension = !((1u32 << width) - 1);
        (masked | extension) as i32
    } else {
        // Positive
        masked as i32
    }
}
```

---

## 10. Base Conversion

### Hex Formatting

```
fn format_hex(value: u32, width: u32) -> String {
    let num_digits = width / 4;
    let mut result = String::new();

    for i in (0..num_digits).rev() {
        let shift = i * 4;
        let digit = (value >> shift) & 0xF;
        let ch = if digit < 10 {
            (b'0' + digit as u8) as char
        } else {
            (b'A' + (digit - 10) as u8) as char
        };
        result.push(ch);
    }

    result
}
```

### Binary Formatting

```
fn format_binary(value: u32, width: u32) -> String {
    let mut result = String::new();

    for i in (0..width).rev() {
        let bit = (value >> i) & 1;
        result.push(if bit == 1 { '1' } else { '0' });
    }

    result
}
```

### Alternative: format! Macro

**Not allowed for project**:

```
// Don't use these:
format!("{:x}", value)   // hex
format!("{:b}", value)   // binary
format!("{:o}", value)   // octal
```

Must implement conversion manually.

---

## 11. Program Evaluation

### Main Evaluation Function

```
pub fn eval_program(statements: &[ParseNode]) {
    let mut env = HashMap::new();

    for stmt in statements {
        eval_statement(stmt, &mut env);
    }
}
```

Simple iteration over statement slice.

### Integration with Main

```
fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: {} <script.ntl>", args[0]);
        std::process::exit(1);
    }

    let source = std::fs::read_to_string(&args[1])
        .expect("failed to read file");

    let tokens = scan(&source);
    let statements = parse_program(&tokens);
    eval_program(&statements);
}
```

---

## 12. Error Handling

### Panic vs Result

**Panic** (for unrecoverable errors):

```
if right_val == 0 {
    panic!("division by zero");
}
```

**Result** (for recoverable errors):

```
fn eval_expression(node: &ParseNode, env: &mut Environment)
    -> Result<u32, String> {
    // ...
}
```

### Using eprintln and exit

```
if !env.contains_key(name) {
    eprintln!("Error: undefined variable '{}'", name);
    std::process::exit(1);
}
```

- `eprintln!` writes to stderr
- `std::process::exit(1)` terminates with error code

### Match on Option

```
match env.get(name) {
    Some(&value) => value,
    None => {
        eprintln!("Error: undefined variable '{}'", name);
        std::process::exit(1);
    }
}
```

---

## 13. Ownership and Memory

### Automatic Memory Management

Rust's ownership system automatically frees memory:

```
{
    let node = ParseNode::IntLit(42);
    // node is used here
}  // node is automatically dropped and freed here
```

### Box Cleanup

`Box<ParseNode>` is freed when it goes out of scope:

```
let node = Box::new(ParseNode::IntLit(42));
// Use node...
// Automatically freed when node goes out of scope
```

### No Manual Free

Unlike C, no need for `free()` or recursive cleanup functions.

### Clone vs Reference

| Pattern | Ownership | Cost |
| --- | --- | --- |
| `name.clone()` | Creates new String | Allocation |
| `&name` | Borrows reference | Free |

For HashMap insert, must use `clone()` or move.

---

## 14. Pattern Matching Advantages

### Exhaustiveness Checking

```
match node {
    ParseNode::IntLit(val) => *val,
    ParseNode::Ident(name) => lookup_var(env, name),
    ParseNode::BinaryOp { .. } => eval_binary(...),
    // Compiler error if any variant is missing
}
```

### Destructuring

```
match node {
    ParseNode::BinaryOp { op, left, right } => {
        // Direct access to fields
        let left_val = eval_expression(left, env);
        let right_val = eval_expression(right, env);
        // ...
    }
}
```

### Wildcard Pattern

```
match node {
    ParseNode::Assign { .. } => eval_assignment(...),
    ParseNode::Print { .. } => eval_print(...),
    _ => panic!("Invalid statement"),
}
```

`_` matches any remaining cases.

---

## 15. Code Organization

### Module Structure

```
project01/rust/src/
├── main.rs          # Entry point
├── scan.rs          # Scanner
├── parse.rs         # Parser, AST definitions
├── eval.rs          # Evaluator
└── convert.rs       # Base conversion
```

### Module Declaration

**main.rs**:

```
mod scan;
mod parse;
mod eval;
mod convert;

use scan::scan;
use parse::parse_program;
use eval::eval_program;

fn main() {
    // ...
}
```

### Visibility

```
pub fn eval_expression(...) -> u32 {
    // Public function
}

fn lookup_var(...) -> u32 {
    // Private helper
}
```

---

## Key Concepts

| Concept | Description |
| --- | --- |
| Enum-based AST | Use Rust enums with associated data for nodes |
| HashMap environment | O(1) lookup with `HashMap<String, u32>` |
| Pattern matching | Exhaustive, compiler-checked dispatch |
| Option type | Represents presence/absence of value |
| Mutable reference | `&mut Environment` for modification |
| Wrapping arithmetic | `.wrapping_add()` for overflow wrapping |
| Box allocation | Heap-allocated tree nodes with `Box<T>` |
| Ownership | Automatic memory management, no manual free |
| Panic vs Result | Unrecoverable vs recoverable errors |
| Clone | Create owned copy of String for HashMap |

---

## Practice Problems

### Problem 1: Pattern Matching

What does this match expression evaluate to?

```
let node = ParseNode::IntLit(42);
let result = match node {
    ParseNode::IntLit(val) => val * 2,
    ParseNode::Ident(name) => name.len() as u32,
    _ => 0,
};
```

> **Click to reveal solution**
>
> ```
> result = 84
> 
> The match expression:
> 1. Matches the first pattern: ParseNode::IntLit(val)
> 2. Binds val = 42
> 3. Evaluates val * 2 = 42 * 2 = 84
> 4. Returns 84
> ```

### Problem 2: HashMap Operations

Given:

```
let mut env = HashMap::new();
env.insert("x".to_string(), 10);
env.insert("y".to_string(), 20);
env.insert("x".to_string(), 15);
```

What is the final state of `env`?

> **Click to reveal solution**
>
> ```
> env = {
>     "x" => 15,
>     "y" => 20,
> }
> 
> HashMap::insert performs upsert:
> - First insert: "x" => 10
> - Second insert: "y" => 20
> - Third insert: "x" => 15 (updates existing "x")
> 
> Final state has two entries, with "x" mapped to 15.
> ```

### Problem 3: Wrapping Arithmetic

What is the result?

```
let a: u32 = 0xFFFFFFFF;
let b: u32 = 2;
let c = a.wrapping_add(b);
```

> **Click to reveal solution**
>
> ```
> c = 1
> 
> a = 0xFFFFFFFF = 4,294,967,295 (max u32)
> b = 2
> 
> a + b = 4,294,967,295 + 2 = 4,294,967,297
> 
> This overflows u32 (max is 2^32 - 1), so it wraps:
>   4,294,967,297 mod 2^32 = 1
> 
> wrapping_add performs two's complement wrapping.
> 
> In binary:
>   1111 1111 1111 1111 1111 1111 1111 1111
> + 0000 0000 0000 0000 0000 0000 0000 0010
> ---------------------------------------
> 1 0000 0000 0000 0000 0000 0000 0000 0001
> ^ carry bit discarded
> 
> Result: 0x00000001 = 1
> ```

### Problem 4: Option Handling

What does this code do?

```
let env: HashMap<String, u32> = HashMap::new();
let value = env.get("x").copied().unwrap_or(0);
```

> **Click to reveal solution**
>
> ```
> value = 0
> 
> Breakdown:
> 1. env.get("x") returns Option<&u32>
> 2. Since "x" is not in the empty HashMap, returns None
> 3. .copied() converts Option<&u32> -> Option<u32>
>    - None.copied() = None
> 4. .unwrap_or(0) unwraps Some(v) to v, or returns 0 for None
>    - None.unwrap_or(0) = 0
> 5. value = 0
> 
> This pattern provides a default value when the key is not found,
> instead of panicking.
> ```

### Problem 5: Mutable References

Is this code valid?

```
let mut env = HashMap::new();
let ref1 = &mut env;
let ref2 = &mut env;
ref1.insert("x".to_string(), 10);
ref2.insert("y".to_string(), 20);
```

> **Click to reveal solution**
>
> ```
> No, this code does not compile.
> 
> Error: cannot borrow `env` as mutable more than once at a time
> 
> Rust's borrowing rules:
> - Only ONE mutable reference at a time
> - Or multiple immutable references
> - But not both simultaneously
> 
> The code creates two mutable references (ref1 and ref2) to env,
> which violates the single mutable reference rule.
> 
> To fix, use only one mutable reference:
> 
> let mut env = HashMap::new();
> env.insert("x".to_string(), 10);
> env.insert("y".to_string(), 20);
> ```

### Problem 6: Sign Extension

Given `value = 0x0B` (binary: `1011`) and `width = 4`, trace `sign_extend(value, width)`.

> **Click to reveal solution**
>
> ```
> value = 0x0B = 0000 1011
> width = 4
> 
> Step 1: Apply width mask
>   masked = apply_width_mask(0x0B, 4)
>          = 0x0B & 0x0F
>          = 0x0B (lower 4 bits: 1011)
> 
> Step 2: Compute sign bit
>   sign_bit = 1u32 << (4 - 1)
>            = 1u32 << 3
>            = 0x08
>            = 0000 1000 (bit 3)
> 
> Step 3: Check if sign bit is set
>   masked & sign_bit = 0x0B & 0x08
>                     = 0000 1011 & 0000 1000
>                     = 0000 1000
>                     = 0x08 (non-zero, so negative)
> 
> Step 4: Sign extend
>   extension = !((1u32 << 4) - 1)
>             = !(0x0F)
>             = 0xFFFFFFF0
>   masked | extension = 0x0B | 0xFFFFFFF0
>                      = 0xFFFFFFFB
> 
> Step 5: Cast to i32
>   (0xFFFFFFFB) as i32 = -5
> 
> Result: -5
> 
> In 4-bit two's complement, 1011 represents -5.
> Sign extending to 32 bits preserves this value.
> ```

---

## Summary

1. **Enum-based AST** with pattern matching provides type safety and exhaustiveness checking.
2. **HashMap environment** gives O(1) lookup and automatic upsert semantics with `insert()`.
3. **Pattern matching** on enums is idiomatic Rust for dispatching on node types.
4. **Option type** handles cases where values may not exist, requiring explicit handling.
5. **Mutable references** (`&mut`) allow modification while enforcing single-writer rule.
6. **Wrapping arithmetic** (`.wrapping_add()`) provides two's complement overflow behavior.
7. **Box allocation** enables recursive tree structures on the heap.
8. **Ownership system** automatically manages memory without manual `free()`.
9. **Error handling** uses panic for unrecoverable errors, Result for recoverable ones.
10. **Code organization** uses modules with pub/private visibility for clean separation.