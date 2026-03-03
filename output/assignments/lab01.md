# Scanning for ntlang

## Due Wed Feb 4th by 11:59pm in your Lab01 GitHub repo

## Links

Tests: <https://github.com/USF-CS631-S26/tests>

Autograder: <https://github.com/phpeterson-usf/autograder>

## Overview

Our goal for Project01 will be to implement an interpreter for *ntlang*, which is short for Number Tool Language, that will be able compute expressions on numbers in different bases and be able to output computed values in different bases. In this lab we are going to work on the first part of the ntlang implementation, which is the scanner. You will extend given C program to scan tokens from input text. Scanning is one of the first steps in program source code processing (interpretation or compilation). Your code should be able to compile and run in a RISC-V enironment. Note you can develop locally, but make sure that your code compiles, runs, and passes tests on a RISC-V machine (the Beagle machines or a RISC-V Qemu VM).

You will implement both C and Rust versions of the scanner.

## Program Requirements

For scanners and parsers, it is common to describe syntax using EBNF (Extended Backus-Naur Form):

<https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form>

<https://ics.uci.edu/~pattis/misc/ebnf2.pdf>

For scanning, also called lexing (for lexical analysis), we convert input text into a sequence of tokens. We also call the specification of accepted tokens, "microsyntax" of a programming langauge.

Here is the EBNF for the microsyntax of ntlang:

```
tokens     ::= (token)*
token      ::= intlit | binlit | symbol
symbol     ::= '+' | '-' | '*' | '/' | '>>' | '<<' | '~' | '&' | '|' | '^' | '>-'
intlit     ::= digit (digit)*
binlit     ::= '0b' ['0', '1'] (['0', '1'])*
digit      ::= '0' | ... | '9'

# Ignore
whitespace ::= ' ' | '\t' (' ' | '\t')*
```

## C Implementation

You should use the following enum and strings array. You need to use these as is to get autograding to work properly:

```
enum scan_token_enum {
    TK_INTLIT, /* 1, 22, 403 */
    TK_BINLIT, /* 0b1010, 0b11110000 */
    TK_PLUS,   /* + */
    TK_MINUS,  /* - */
    TK_MULT,   /* * */
    TK_DIV,    /* / */
    TK_LSR,    /* >> */
    TK_ASR,    /* >- */
    TK_LSL,    /* << */
    TK_NOT,    /* ~ */
    TK_AND,    /* & */
    TK_OR,     /* | */
    TK_XOR,    /* ^ */
    TK_LPAREN, /* ( */
    TK_RPAREN, /* ) */
    TK_EOT     /* end of text */
};

char *scan_token_strings[] = {
    "TK_INTLIT",
    "TK_BINLIT",
    "TK_PLUS",
    "TK_MINUS",
    "TK_MULT",
    "TK_DIV",
    "TK_LSR",
    "TK_ASR",
    "TK_LSL",
    "TK_NOT",
    "TK_AND",
    "TK_OR",
    "TK_XOR",
    "TK_LPAREN",
    "TK_RPAREN",
    "TK_EOT"
};
```

Your Lab01 repo in the `c` directory should have the following files:

```
Makefile
README
lab01.c
scan1.c
scan2.c
```

## make and the Makefile

The starter code includes a `Makefile` that automates building your programs. Here is the Makefile:

```
PROGS = scan1 scan2 lab01

all : $(PROGS)

% : %.c
    gcc -g -o $@ $<

clean :
    rm -f $(PROGS)
    rm -rf $(PROGS:=.dSYM)
```

### Using the Makefile

To build all programs, run `make` or `make all` in the directory containing the Makefile:

```
$ make
gcc -g -o scan1 scan1.c
gcc -g -o scan2 scan2.c
gcc -g -o lab01 lab01.c
```

To run the compiled programs:

```
$ ./scan1
TK_PLUS("+")
TK_MINUS("-")
TK_PLUS("+")
TK_EOT("")

TK_PLUS("+")
TK_MINUS("-")
TK_MULT("*")
TK_DIV("/")
TK_EOT("")

$ ./scan2 "1 + 2"
TK_INTLIT("1")
TK_PLUS("+")
TK_INTLIT("2")
TK_EOT("")
```

To remove the compiled executables and debug files, run `make clean`:

```
$ make clean
rm -f scan1 scan2 lab01
rm -rf scan1.dSYM scan2.dSYM lab01.dSYM
```

### How the Makefile Works

**`PROGS = scan1 scan2 lab01`** - This defines a variable called `PROGS` that lists the three programs to build.

**`all : $(PROGS)`** - The `all` target depends on all programs listed in `PROGS`. When you run `make` without arguments, it builds the first target (`all`), which causes all three programs to be built.

**`% : %.c`** - This is a pattern rule. The `%` is a wildcard that matches any target name. This rule says: to build any program (like `scan1`), look for a corresponding `.c` file (like `scan1.c`).

**`gcc -g -o $@ $<`** - This is the command that compiles each program:
- `gcc` - The C compiler
- `-g` - Include debugging information (useful for `gdb`)
- `-o $@` - Output file name; `$@` is an automatic variable that expands to the target name (e.g., `scan1`)
- `$<` - An automatic variable that expands to the first prerequisite (e.g., `scan1.c`)

**`clean`** - This target removes generated files:
- `rm -f $(PROGS)` - Removes the executables
- `rm -rf $(PROGS:=.dSYM)` - Removes `.dSYM` directories (macOS debug symbol directories created when compiling with `-g`)

## Rust Implementation

You should use the following enum. You need to use this as is to get autograding to work properly:

```
#[derive(Debug, Clone)]
enum Token {
    IntLit(String),  // Integer literal: "1", "22", "403"
    BinLit(String),  // Binary literal: "1010" (the "0b" prefix is stripped)
    Plus,            // +
    Minus,           // -
    Mult,            // *
    Div,             // /
    Lsr,             // >> (logical shift right)
    Asr,             // >- (arithmetic shift right)
    Lsl,             // << (logical shift left)
    Not,             // ~ (bitwise not)
    And,             // & (bitwise and)
    Or,              // | (bitwise or)
    Xor,             // ^ (bitwise xor)
    LParen,          // (
    RParen,          // )
    Eot,             // End of text
}
```

You also need to implement `name()` and `value()` methods on `Token` for output formatting. These methods return the token name (e.g., `"TK_PLUS"`) and the token value (e.g., `"+"`) respectively. The `Display` trait implementation should format tokens as `name("value")`:

```
impl Token {
    fn name(&self) -> &str {
        match self {
            Token::IntLit(_) => "TK_INTLIT",
            Token::BinLit(_) => "TK_BINLIT",
            Token::Plus => "TK_PLUS",
            // ... other variants
        }
    }

    fn value(&self) -> &str {
        match self {
            Token::IntLit(s) => s,
            Token::BinLit(s) => s,
            Token::Plus => "+",
            // ... other variants
        }
    }
}

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}(\"{}\")", self.name(), self.value())
    }
}
```

Your Lab01 repo in the `rust` directory should have the following files:

```
Cargo.toml
src/main.rs        (lab01 implementation)
src/bin/scan1.rs
src/bin/scan2.rs
```

## cargo and Cargo.toml

The starter code includes a `Cargo.toml` that configures your Rust project. Here is the Cargo.toml:

```
[package]
name = "lab01"
version = "0.1.0"
edition = "2021"

[dependencies]
```

### Using cargo

Cargo is Rust's build system and package manager. To build all programs, run `cargo build` in the directory containing `Cargo.toml`:

```
$ cargo build
   Compiling lab01 v0.1.0 (/path/to/rust)
    Finished dev [unoptimized + debuginfo] target(s)
```

To run the main program (src/main.rs), use `cargo run`:

```
$ cargo run
lab01: Not yet implemented
```

To run a specific binary from `src/bin/`, use `cargo run --bin`:

```
$ cargo run --bin scan1
TK_PLUS("+")
TK_MINUS("-")
TK_PLUS("+")
TK_EOT("")

TK_PLUS("+")
TK_MINUS("-")
TK_MULT("*")
TK_DIV("/")
TK_EOT("")

$ cargo run --bin scan2 "1 + 2"
TK_INTLIT("1")
TK_PLUS("+")
TK_INTLIT("2")
TK_EOT("")
```

To remove compiled artifacts, run `cargo clean`:

```
$ cargo clean
```

### How Cargo.toml Works

**`[package]`** - This section defines metadata about your project:
- `name = "lab01"` - The name of your package/crate
- `version = "0.1.0"` - The version number
- `edition = "2021"` - The Rust edition to use (determines language features)

**`[dependencies]`** - This section lists external crates your project depends on. For this lab, no external dependencies are needed.

**Binary discovery** - Cargo automatically discovers binaries:
- `src/main.rs` - The default binary, run with `cargo run`
- `src/bin/*.rs` - Additional binaries, run with `cargo run --bin <name>`

For example, `src/bin/scan1.rs` creates a binary named `scan1` that can be run with `cargo run --bin scan1`.

## Root Makefile

The starter code includes a root `Makefile` that builds both the C and Rust implementations. Here is the Makefile:

```
.PHONY: all clean c rust

all: c rust

c:
    $(MAKE) -C c

rust:
    cargo build --manifest-path rust/Cargo.toml

clean:
    $(MAKE) -C c clean
    cargo clean --manifest-path rust/Cargo.toml
```

### Using the Root Makefile

To build both C and Rust programs from the project root:

```
$ make
make -C c
gcc -g -o scan1 scan1.c
gcc -g -o scan2 scan2.c
gcc -g -o lab01 lab01.c
cargo build --manifest-path rust/Cargo.toml
   Compiling lab01 v0.1.0 (/path/to/rust)
    Finished dev [unoptimized + debuginfo] target(s)
```

To build only C or only Rust:

```
$ make c
$ make rust
```

To clean both:

```
$ make clean
```

### How the Root Makefile Works

**`.PHONY: all clean c rust`** - Declares these targets as "phony," meaning they don't represent actual files. This ensures make always runs the commands even if a file with that name exists.

**`all: c rust`** - The default target depends on both `c` and `rust`, so running `make` builds both implementations.

**`$(MAKE) -C c`** - Runs make in the `c` subdirectory. Using `$(MAKE)` instead of `make` ensures proper behavior with parallel builds and passes along any make flags.

**`cargo build --manifest-path rust/Cargo.toml`** - Builds the Rust project. The `--manifest-path` flag tells cargo where to find `Cargo.toml`, allowing you to run cargo from the project root.

**`clean`** - Cleans both projects by running `make clean` in the `c` directory and `cargo clean` for the Rust project.

## Autograder

To run the Autograder tests for Lab01, make sure you have cloned the tests repo for the class and you have configured the Autograder to point to the location of you tests repo in your home directory. Once you have the autograder installed and configured, you should be able to run the Lab01 tests like this:

```
$ grade test -p lab01
. c-01(5/5) c-02(5/5) c-03(10/10) c-04(5/5) c-05(10/10) c-06(5/5) c-07(10/10) rust-01(5/5) rust-02(5/5) rust-03(10/10) rust-04(5/5) rust-05(10/10) rust-06(5/5) rust-07(10/10) 100/100
```

Note that the `grade` program can detect the lab or project being autograded by looked at the current directory. So, if you are in your `lab01-<gitid>` repo, you can just type `grade test`:

```
$ grade test
. c-01(5/5) c-02(5/5) c-03(10/10) c-04(5/5) c-05(10/10) c-06(5/5) c-07(10/10) rust-01(5/5) rust-02(5/5) rust-03(10/10) rust-04(5/5) rust-05(10/10) rust-06(5/5) rust-07(10/10) 100/100
```

## Code Submission

You will submit your code in your Lab01 GitHub repo. You will be provided a link to create your repo. You goal is to complete `c/lab01.c` and `rust/src/main.rs`. There is a default `.gitignore` that should prevent the inclusion of any binary files into your repo.

## Rubric

100% Lab01 autograder tests.