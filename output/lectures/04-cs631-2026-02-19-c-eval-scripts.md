# Evaluation and Scripts in C

## Overview

This lecture covers the C-specific implementation of AST evaluation and script execution for NTLang. We examine C struct-based environment implementation, recursive evaluation patterns for statements and expressions, memory management considerations, and error handling strategies. We also cover the integration of evaluation with parsing and the implementation of print statement formatting.

## Learning Objectives

- Design C structs for AST nodes and environment storage
- Implement recursive evaluation functions for statements and expressions
- Build an array-based symbol table with linear search
- Use string operations (`strncmp`, `strncpy`) for variable name handling
- Apply proper error handling with descriptive messages and `exit()`
- Integrate expression and statement evaluation with the parser
- Implement print formatting with base conversion functions

## Prerequisites

- Understanding of AST evaluation and environments (previous lecture)
- C programming with structs and pointers
- Binary and base conversion in C
- Familiarity with the NTLang project structure

---

## 1. AST Representation in C

### Parse Node Structure

The AST is represented as a tree of `parse_node_st` structs:

```
typedef enum {
    NODE_INTLIT,      /* Integer literal */
    NODE_BINLIT,      /* Binary literal */
    NODE_HEXLIT,      /* Hexadecimal literal */
    NODE_IDENT,       /* Identifier (variable name) */
    NODE_UNARY_OP,    /* Unary operation (-, ~) */
    NODE_BINARY_OP,   /* Binary operation (+, -, *, /, etc.) */
    NODE_ASSIGN,      /* Assignment statement */
    NODE_PRINT        /* Print statement */
} node_type_t;

typedef struct parse_node_st {
    node_type_t type;
    union {
        uint32_t value;          /* For literals */
        char name[MAX_NAME_LEN]; /* For identifiers */
        struct {
            char op;
            struct parse_node_st *operand;
        } unary;
        struct {
            char op[3];          /* Operators like ">>", ">-" */
            struct parse_node_st *left;
            struct parse_node_st *right;
        } binary;
        struct {
            char name[MAX_NAME_LEN];
            struct parse_node_st *expr;
        } assign;
        struct {
            struct parse_node_st *expr;
            struct parse_node_st *base;
            struct parse_node_st *width;
        } print;
    } data;
} parse_node_t;
```

### Node Type Patterns

| Node Type | Usage | Fields |
| --- | --- | --- |
| `NODE_INTLIT` | Integer literal | `data.value` |
| `NODE_IDENT` | Variable reference | `data.name` |
| `NODE_BINARY_OP` | Binary expression | `data.binary.op`, `.left`, `.right` |
| `NODE_ASSIGN` | Assignment | `data.assign.name`, `.expr` |
| `NODE_PRINT` | Print statement | `data.print.expr`, `.base`, `.width` |

---

## 2. Environment Structure

### Array-Based Symbol Table

For NTLang's small programs, an array-based symbol table is sufficient:

```
#define MAX_VARS 100
#define MAX_NAME_LEN 32

typedef struct {
    char name[MAX_NAME_LEN];
    uint32_t value;
    int is_defined;  /* 0 = empty slot, 1 = defined variable */
} var_entry_t;

typedef struct {
    var_entry_t vars[MAX_VARS];
    int count;  /* Number of defined variables */
} environment_t;
```

### Initialization

```
void env_init(environment_t *env) {
    env->count = 0;
    for (int i = 0; i < MAX_VARS; i++) {
        env->vars[i].is_defined = 0;
        env->vars[i].name[0] = '\0';
        env->vars[i].value = 0;
    }
}
```

---

## 3. Environment Operations

### Lookup

Find a variable by name (linear search):

```
int env_lookup(environment_t *env, const char *name, uint32_t *value) {
    for (int i = 0; i < env->count; i++) {
        if (env->vars[i].is_defined &&
            strncmp(env->vars[i].name, name, MAX_NAME_LEN) == 0) {
            *value = env->vars[i].value;
            return 1;  /* Found */
        }
    }
    return 0;  /* Not found */
}
```

**Using the lookup**:

```
uint32_t value;
if (!env_lookup(env, "x", &value)) {
    fprintf(stderr, "Error: undefined variable '%s'\n", "x");
    exit(1);
}
/* Use value here */
```

### Upsert (Insert or Update)

```
void env_set(environment_t *env, const char *name, uint32_t value) {
    /* First, check if variable already exists (update) */
    for (int i = 0; i < env->count; i++) {
        if (env->vars[i].is_defined &&
            strncmp(env->vars[i].name, name, MAX_NAME_LEN) == 0) {
            env->vars[i].value = value;
            return;
        }
    }

    /* Not found, insert new variable */
    if (env->count >= MAX_VARS) {
        fprintf(stderr, "Error: too many variables (max %d)\n", MAX_VARS);
        exit(1);
    }

    strncpy(env->vars[env->count].name, name, MAX_NAME_LEN - 1);
    env->vars[env->count].name[MAX_NAME_LEN - 1] = '\0';
    env->vars[env->count].value = value;
    env->vars[env->count].is_defined = 1;
    env->count++;
}
```

### String Operations

| Function | Purpose | Example |
| --- | --- | --- |
| `strncmp(s1, s2, n)` | Compare strings | `strncmp("abc", "abc", 3) == 0` |
| `strncpy(dst, src, n)` | Copy string | `strncpy(buf, "hello", 32)` |
| `strlen(s)` | Get length | `strlen("hello") == 5` |

**Important**: Always null-terminate strings when using `strncpy`:

```
strncpy(dest, src, MAX_NAME_LEN - 1);
dest[MAX_NAME_LEN - 1] = '\0';
```

---

## 4. Expression Evaluation

### Main Evaluation Function

```
uint32_t eval_expression(parse_node_t *node, environment_t *env) {
    if (node == NULL) {
        fprintf(stderr, "Error: null node in eval_expression\n");
        exit(1);
    }

    switch (node->type) {
        case NODE_INTLIT:
        case NODE_BINLIT:
        case NODE_HEXLIT:
            return node->data.value;

        case NODE_IDENT:
            return eval_identifier(node, env);

        case NODE_UNARY_OP:
            return eval_unary(node, env);

        case NODE_BINARY_OP:
            return eval_binary(node, env);

        default:
            fprintf(stderr, "Error: invalid expression node type\n");
            exit(1);
    }
}
```

### Identifier Evaluation

```
uint32_t eval_identifier(parse_node_t *node, environment_t *env) {
    uint32_t value;
    if (!env_lookup(env, node->data.name, &value)) {
        fprintf(stderr, "Error: undefined variable '%s'\n",
                node->data.name);
        exit(1);
    }
    return value;
}
```

### Unary Operation Evaluation

```
uint32_t eval_unary(parse_node_t *node, environment_t *env) {
    uint32_t operand = eval_expression(node->data.unary.operand, env);
    char op = node->data.unary.op;

    switch (op) {
        case '-':
            return (uint32_t)(-(int32_t)operand);
        case '~':
            return ~operand;
        default:
            fprintf(stderr, "Error: unknown unary operator '%c'\n", op);
            exit(1);
    }
}
```

**Type casting for negation**:

- Store as `uint32_t` internally
- Cast to `int32_t` for negation
- Cast back to `uint32_t`

```
uint32_t x = 5;
uint32_t neg_x = (uint32_t)(-(int32_t)x);  /* -5 in two's complement */
```

### Binary Operation Evaluation

```
uint32_t eval_binary(parse_node_t *node, environment_t *env) {
    uint32_t left = eval_expression(node->data.binary.left, env);
    uint32_t right = eval_expression(node->data.binary.right, env);
    const char *op = node->data.binary.op;

    if (strcmp(op, "+") == 0) return left + right;
    if (strcmp(op, "-") == 0) return left - right;
    if (strcmp(op, "*") == 0) return left * right;
    if (strcmp(op, "/") == 0) {
        if (right == 0) {
            fprintf(stderr, "Error: division by zero\n");
            exit(1);
        }
        return left / right;
    }
    if (strcmp(op, ">>") == 0) return left >> right;
    if (strcmp(op, "<<") == 0) return left << right;
    if (strcmp(op, "&") == 0) return left & right;
    if (strcmp(op, "|") == 0) return left | right;
    if (strcmp(op, "^") == 0) return left ^ right;
    if (strcmp(op, ">-") == 0) {
        /* Arithmetic shift right */
        return (uint32_t)((int32_t)left >> right);
    }

    fprintf(stderr, "Error: unknown binary operator '%s'\n", op);
    exit(1);
}
```

### Arithmetic Shift Right

C's `>>` operator on signed types performs arithmetic shift (sign-extending):

```
int32_t signed_val = (int32_t)left;
int32_t shifted = signed_val >> right;
return (uint32_t)shifted;
```

---

## 5. Statement Evaluation

### Statement Dispatch

```
void eval_statement(parse_node_t *stmt, environment_t *env) {
    if (stmt == NULL) {
        return;
    }

    switch (stmt->type) {
        case NODE_ASSIGN:
            eval_assignment(stmt, env);
            break;

        case NODE_PRINT:
            eval_print(stmt, env);
            break;

        default:
            fprintf(stderr, "Error: invalid statement node type\n");
            exit(1);
    }
}
```

### Assignment Evaluation

```
void eval_assignment(parse_node_t *stmt, environment_t *env) {
    const char *var_name = stmt->data.assign.name;
    uint32_t value = eval_expression(stmt->data.assign.expr, env);
    env_set(env, var_name, value);
}
```

**Simple pattern**:

1. Get variable name
2. Evaluate right-hand side expression
3. Store in environment

### Print Statement Evaluation

```
void eval_print(parse_node_t *stmt, environment_t *env) {
    uint32_t value = eval_expression(stmt->data.print.expr, env);
    uint32_t base = eval_expression(stmt->data.print.base, env);
    uint32_t width = eval_expression(stmt->data.print.width, env);

    /* Validate base and width */
    if (base != 2 && base != 10 && base != 16) {
        fprintf(stderr, "Error: base must be 2, 10, or 16\n");
        exit(1);
    }
    if (width != 4 && width != 8 && width != 16 && width != 32) {
        fprintf(stderr, "Error: width must be 4, 8, 16, or 32\n");
        exit(1);
    }

    print_formatted(value, base, width);
}
```

---

## 6. Print Formatting

### Width Masking

Apply width mask before formatting:

```
uint32_t apply_width_mask(uint32_t value, uint32_t width) {
    if (width == 32) {
        return value;
    }
    uint32_t mask = (1U << width) - 1;
    return value & mask;
}
```

### Sign Extension for Base 10

```
int32_t sign_extend(uint32_t value, uint32_t width) {
    uint32_t masked = apply_width_mask(value, width);

    /* Check if MSB of the width is set */
    uint32_t sign_bit = 1U << (width - 1);
    if (masked & sign_bit) {
        /* Negative - fill upper bits with 1 */
        uint32_t extension = ~((1U << width) - 1);
        masked |= extension;
    }
    return (int32_t)masked;
}
```

### Formatted Output

```
void print_formatted(uint32_t value, uint32_t base, uint32_t width) {
    uint32_t masked = apply_width_mask(value, width);

    if (base == 10) {
        /* Print as signed */
        int32_t signed_val = sign_extend(value, width);
        printf("%d\n", signed_val);
    } else if (base == 16) {
        /* Print as hex with 0x prefix */
        char buf[64];
        uint_to_hex(masked, buf, width);
        printf("0x%s\n", buf);
    } else if (base == 2) {
        /* Print as binary with 0b prefix */
        char buf[64];
        uint_to_bin(masked, buf, width);
        printf("0b%s\n", buf);
    }
}
```

### Base Conversion Functions

These functions convert values to strings (from the binary/bases lecture):

```
void uint_to_hex(uint32_t value, char *buf, uint32_t width) {
    int num_digits = width / 4;
    for (int i = num_digits - 1; i >= 0; i--) {
        uint32_t digit = value & 0xF;
        buf[i] = (digit < 10) ? ('0' + digit) : ('A' + digit - 10);
        value >>= 4;
    }
    buf[num_digits] = '\0';
}

void uint_to_bin(uint32_t value, char *buf, uint32_t width) {
    for (int i = width - 1; i >= 0; i--) {
        buf[i] = (value & 1) ? '1' : '0';
        value >>= 1;
    }
    buf[width] = '\0';
}
```

---

## 7. Program Evaluation

### Main Evaluation Loop

For scripts, evaluate a list of statements:

```
void eval_program(parse_node_t **statements, int num_statements) {
    environment_t env;
    env_init(&env);

    for (int i = 0; i < num_statements; i++) {
        eval_statement(statements[i], &env);
    }
}
```

### Integration with Parser

```
int main(int argc, char *argv[]) {
    /* Parse command line arguments */
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <script.ntl>\n", argv[0]);
        return 1;
    }

    /* Read file */
    char *source = read_file(argv[1]);

    /* Scan */
    token_t *tokens = scan(source);

    /* Parse */
    parse_node_t **statements;
    int num_statements = parse_program(tokens, &statements);

    /* Evaluate */
    eval_program(statements, num_statements);

    /* Clean up */
    free_statements(statements, num_statements);
    free(tokens);
    free(source);

    return 0;
}
```

---

## 8. Error Handling

### Error Reporting Pattern

For runtime errors, use descriptive messages and exit:

```
void error_exit(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(1);
}

void error_exit_fmt(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
    exit(1);
}
```

**Usage**:

```
if (!env_lookup(env, name, &value)) {
    error_exit_fmt("undefined variable '%s'", name);
}

if (base != 2 && base != 10 && base != 16) {
    error_exit("base must be 2, 10, or 16");
}
```

### Common Errors

| Error | Check | Example |
| --- | --- | --- |
| Undefined variable | Lookup fails | `print(x, 10, 32)` when x not defined |
| Division by zero | Right operand is 0 | `10 / 0` |
| Invalid base | Base not in | `print(5, 11, 32)` |
| Invalid width | Width not in | `print(5, 10, 7)` |
| Too many variables | `count >= MAX_VARS` | More than 100 variables |

---

## 9. Memory Management

### Stack Allocation

For NTLang, the environment can be stack-allocated:

```
void eval_program(parse_node_t **statements, int num_statements) {
    environment_t env;  /* Stack allocation */
    env_init(&env);
    /* ... */
}
```

### Heap Allocation (If Needed)

If passing environment across function boundaries:

```
environment_t *env = malloc(sizeof(environment_t));
if (env == NULL) {
    error_exit("out of memory");
}
env_init(env);

/* Use env */

free(env);
```

### AST Memory Management

Parser allocates AST nodes:

```
parse_node_t *node = malloc(sizeof(parse_node_t));
node->type = NODE_INTLIT;
node->data.value = 42;
```

After evaluation, free all nodes:

```
void free_node(parse_node_t *node) {
    if (node == NULL) return;

    switch (node->type) {
        case NODE_UNARY_OP:
            free_node(node->data.unary.operand);
            break;
        case NODE_BINARY_OP:
            free_node(node->data.binary.left);
            free_node(node->data.binary.right);
            break;
        case NODE_ASSIGN:
            free_node(node->data.assign.expr);
            break;
        case NODE_PRINT:
            free_node(node->data.print.expr);
            free_node(node->data.print.base);
            free_node(node->data.print.width);
            break;
        default:
            break;
    }
    free(node);
}
```

---

## 10. Code Organization

### File Structure

```
project01/c/
├── main.c          # Main entry point, command-line handling
├── scan.c          # Scanner implementation
├── scan.h          # Scanner interface
├── parse.c         # Parser implementation
├── parse.h         # Parser interface, AST definitions
├── eval.c          # Evaluator implementation
├── eval.h          # Evaluator interface
├── convert.c       # Base conversion functions
├── convert.h       # Conversion interface
└── Makefile
```

### Header Guards

```
#ifndef EVAL_H
#define EVAL_H

#include "parse.h"
#include <stdint.h>

typedef struct environment_st environment_t;

void eval_program(parse_node_t **statements, int num_statements);
uint32_t eval_expression(parse_node_t *node, environment_t *env);
void eval_statement(parse_node_t *stmt, environment_t *env);

#endif /* EVAL_H */
```

### Separation of Concerns

| Module | Responsibility |
| --- | --- |
| `scan` | Tokenize source code |
| `parse` | Build AST from tokens |
| `eval` | Traverse AST and compute results |
| `convert` | Format output in different bases |
| `main` | Handle command-line arguments and file I/O |

---

## Key Concepts

| Concept | Description |
| --- | --- |
| Parse node struct | Represents AST nodes with union for different types |
| Environment struct | Array-based symbol table with name-value pairs |
| Linear search | O(n) lookup for variable names |
| Upsert | Insert new variable or update existing one |
| String operations | `strncmp`, `strncpy`, `strlen` for name handling |
| Recursive evaluation | Functions call themselves for child nodes |
| Type casting | `(int32_t)` for signed operations, `(uint32_t)` for storage |
| Error handling | `fprintf(stderr, ...)` and `exit(1)` for runtime errors |
| Width masking | Apply `(1U << width) - 1` mask before output |
| Sign extension | Fill upper bits with sign bit for base 10 output |

---

## Practice Problems

### Problem 1: Environment Lookup

What is the output of `env_lookup` given this environment?

```
env.vars[0] = {"x", 10, 1};
env.vars[1] = {"y", 20, 1};
env.count = 2;

uint32_t value;
int result = env_lookup(&env, "y", &value);
```

> **Click to reveal solution**
>
> ```
> result = 1       /* Found */
> value = 20       /* Value of y */
> 
> The function searches the array, finds "y" at index 1,
> sets *value = 20, and returns 1.
> ```

### Problem 2: Upsert Behavior

Given an empty environment, trace the state after these operations:

```
env_set(&env, "a", 5);
env_set(&env, "b", 10);
env_set(&env, "a", 15);  /* Update existing */
```

> **Click to reveal solution**
>
> ```
> After env_set(&env, "a", 5):
>   vars[0] = {"a", 5, 1}
>   count = 1
> 
> After env_set(&env, "b", 10):
>   vars[0] = {"a", 5, 1}
>   vars[1] = {"b", 10, 1}
>   count = 2
> 
> After env_set(&env, "a", 15):
>   vars[0] = {"a", 15, 1}    /* Updated, not inserted */
>   vars[1] = {"b", 10, 1}
>   count = 2                 /* Count unchanged */
> ```

### Problem 3: Sign Extension

Given `value = 0x0B` (binary: `1011`) and `width = 4`, what does `sign_extend(value, width)` return?

> **Click to reveal solution**
>
> ```
> value = 0x0B = 0000 1011
> width = 4
> 
> Step 1: Apply width mask
>   masked = 0x0B & 0x0F = 0x0B (lower 4 bits: 1011)
> 
> Step 2: Check sign bit
>   sign_bit = 1 << (4 - 1) = 1 << 3 = 0x08 (bit 3)
>   masked & sign_bit = 0x0B & 0x08 = 0x08 (non-zero, so negative)
> 
> Step 3: Sign extend
>   extension = ~((1 << 4) - 1) = ~0x0F = 0xFFFFFFF0
>   masked |= extension = 0x0B | 0xFFFFFFF0 = 0xFFFFFFFB
> 
> Step 4: Cast to int32_t
>   return (int32_t)0xFFFFFFFB = -5
> 
> Answer: -5
> ```

### Problem 4: Arithmetic Shift Right

What is the result of `>-` operation on `-8` shifted right by 2?

```
uint32_t left = (uint32_t)(-8);   /* 0xFFFFFFF8 */
uint32_t right = 2;
uint32_t result = (uint32_t)((int32_t)left >> right);
```

> **Click to reveal solution**
>
> ```
> left = (uint32_t)(-8) = 0xFFFFFFF8
>      = 1111 1111 1111 1111 1111 1111 1111 1000 (binary)
> 
> Cast to int32_t: -8 (two's complement)
> 
> Arithmetic shift right by 2:
>   int32_t signed_left = (int32_t)0xFFFFFFF8 = -8
>   int32_t shifted = -8 >> 2 = -2
> 
>   In binary:
>   1111 1111 1111 1111 1111 1111 1111 1000  (-8)
>   >> 2 (arithmetic, preserves sign)
>   1111 1111 1111 1111 1111 1111 1111 1110  (-2)
> 
> Cast back to uint32_t: 0xFFFFFFFE
> 
> Result: 0xFFFFFFFE (unsigned), -2 (signed)
> ```

### Problem 5: Recursive Evaluation

Trace the recursive calls for evaluating `a + b` where `a = 3`, `b = 4`:

```
environment_t env;
env_set(&env, "a", 3);
env_set(&env, "b", 4);

/* AST for "a + b" */
parse_node_t *expr = make_binary_node("+",
    make_ident_node("a"),
    make_ident_node("b")
);

uint32_t result = eval_expression(expr, &env);
```

> **Click to reveal solution**
>
> ```
> Call stack trace:
> 
> 1. eval_expression(binary_node "+", env)
>    → type is NODE_BINARY_OP
>    → calls eval_binary(node, env)
> 
> 2. eval_binary(node, env)
>    → calls eval_expression(left child "a", env)
> 
> 3. eval_expression(ident_node "a", env)
>    → type is NODE_IDENT
>    → calls eval_identifier(node, env)
>    → env_lookup(env, "a", &value) → value = 3
>    → returns 3
> 
> 4. (back in eval_binary)
>    → left = 3
>    → calls eval_expression(right child "b", env)
> 
> 5. eval_expression(ident_node "b", env)
>    → type is NODE_IDENT
>    → calls eval_identifier(node, env)
>    → env_lookup(env, "b", &value) → value = 4
>    → returns 4
> 
> 6. (back in eval_binary)
>    → right = 4
>    → op = "+"
>    → returns left + right = 3 + 4 = 7
> 
> 7. (back in top-level eval_expression)
>    → returns 7
> 
> Result: 7
> ```

---

## Summary

1. **AST nodes** are represented using C structs with a type tag and union for different node data.
2. **Environment** is implemented as an array of name-value pairs with linear search for lookup.
3. **Upsert semantics** check if variable exists (update) or insert new entry.
4. **String operations** use `strncmp` for comparison and `strncpy` for copying variable names.
5. **Recursive evaluation** dispatches on node type and recursively evaluates child nodes.
6. **Type casting** is needed for signed operations: cast to `int32_t`, apply operation, cast back to `uint32_t`.
7. **Error handling** uses `fprintf(stderr, ...)` for messages and `exit(1)` to terminate on runtime errors.
8. **Print formatting** applies width masks and sign extension, then calls base conversion functions.
9. **Memory management** requires freeing AST nodes after evaluation (recursive free function).
10. **Code organization** separates concerns into modules: scan, parse, eval, convert, main.