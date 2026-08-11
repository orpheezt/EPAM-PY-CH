---
title: "JIT Execution & LLVM Dialect Conversion"
category: "MLIR / Execution & JIT"
file_name: "07_execution_engine_runner.md"
---

# JIT Execution & LLVM Dialect Conversion

The final phase of an MLIR compilation pipeline converts all high-level dialects (`linalg`, `scf`, `vector`, `memref`, `func`) into the `llvm` dialect, translates the module to native LLVM IR, and executes it using MLIR's **ExecutionEngine** Just-In-Time (JIT) runtime or `mlir-cpu-runner`.

---

## 1. The Full Lowering Pipeline to LLVM Dialect

To reach target execution, code must pass through a strict sequence of lowering passes:

```
┌─────────────────────────────────────────────────────────────┐
│                      Linalg / Tensor IR                     │
└─────────────────────────────────────────────────────────────┘
                               │  --one-shot-bufferize
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      MemRef / SCF Dialects                  │
└─────────────────────────────────────────────────────────────┘
                               │  --convert-linalg-to-loops
                               │  --convert-scf-to-cf
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Control Flow / MemRef / Arith               │
└─────────────────────────────────────────────────────────────┘
                               │  --expand-strided-metadata
                               │  --finalize-memref-to-llvm
                               │  --convert-func-to-llvm
                               │  --convert-arith-to-llvm
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        LLVM Dialect                         │
└─────────────────────────────────────────────────────────────┘
                               │  --reconcile-unrealized-casts
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Clean LLVM Dialect IR                    │
└─────────────────────────────────────────────────────────────┘
                               │  mlir-translate --mlir-to-llvmir
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Native LLVM IR                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Mandatory Final Lowering Passes Explained

### 1. `--convert-scf-to-cf`
Converts high-level structured loops (`scf.for`, `scf.if`) into explicit basic blocks with conditional and unconditional control-flow branches (`cf.br`, `cf.cond_br`).

### 2. `--convert-func-to-llvm`
Converts MLIR standard function declarations, function calls (`func.call`), and returns (`func.return`) into native LLVM function definitions (`llvm.func`, `llvm.return`) using LLVM C ABI calling conventions.

### 3. `--reconcile-unrealized-casts`
Eliminates transient `builtin.unrealized_conversion_cast` ops inserted during partial type conversions between dialects. **Failure to run this pass before translation results in translation errors.**

---

## 3. Translation to LLVM IR (`mlir-translate`)

Once an MLIR module contains exclusively `llvm` dialect operations, it can be translated into native text or bitcode LLVM IR using `mlir-translate`:

```bash
mlir-translate --mlir-to-llvmir input_lowered.mlir -o output.ll
```

---

## 4. Executing via MLIR ExecutionEngine & JIT

MLIR provides a C++ JIT execution wrapper called `mlir::ExecutionEngine`. It leverages LLVM's ORC JIT engine to dynamically compile MLIR LLVM IR in memory, resolve symbols, and execute function entry points.

### Running via `mlir-cpu-runner` CLI Tool

`mlir-cpu-runner` is the standard CLI utility for executing MLIR modules containing a `main` function:

```bash
mlir-cpu-runner input_lowered.mlir \
  -e main \
  -entry-point-result=void \
  -shared-libs=/path/to/libmlir_c_runner_utils.so
```

* `-e main`: Specifies the function entry point name.
* `-shared-libs`: Links runtime utility libraries providing C utilities like `printMemrefF32` for printing target arrays.

---

## 5. C++ ExecutionEngine API Integration Example

```cpp
#include "mlir/ExecutionEngine/ExecutionEngine.h"
#include "mlir/ExecutionEngine/OptUtils.h"
#include "mlir/IR/Module.h"

// Compiling and executing MLIR Module dynamically in C++
mlir::ModuleOp moduleOp = getLoweredModule();

// Set up optimization pipeline level
auto optPipeline = mlir::makeOptimizingTransformer(3, 0, nullptr);

// Create ExecutionEngine instance
llvm::Expected<std::unique_ptr<mlir::ExecutionEngine>> maybeEngine =
    mlir::ExecutionEngine::create(moduleOp, nullptr, optPipeline);

if (auto &engine = *maybeEngine) {
  // Invoke entry point function by string name
  llvm::Error error = engine->invokePacked("main");
  if (error) {
    llvm::errs() << "JIT Execution Failed!\n";
  }
}
```
