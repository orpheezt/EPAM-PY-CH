---
title: "Fundamentals of Bufferization in MLIR"
category: "MLIR / Bufferization"
file_name: "02_bufferization_concepts.md"
---

# Fundamentals of Bufferization in MLIR

**Bufferization** is the process of converting operations operating on values with **value semantics** (such as MLIR `tensor` types) to operations operating on memory buffers with **buffer semantics** (such as MLIR `memref` types).

---

## 1. The Dual Domains: Tensor vs. MemRef

In MLIR optimization pipelines, high-level transformation and code generation take place in two distinct computational domains:

```
           High-Level Transformations (Tiling, Fusion, SSA Optimizations)
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                          TENSOR DOMAIN                            │
│  - Pure Value Semantics (Immutable values, SSA form)             │
│  - No physical allocation, layout, or pointer aliases             │
│  - Represented by: tensor<16x32xf32>                             │
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  │  BUFFERIZATION PROCESS
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                          MEMREF DOMAIN                            │
│  - Buffer Semantics (Mutable memory buffers)                      │
│  - Explicit allocation, dynamic sizes, offsets, and strides       │
│  - Represented by: memref<16x32xf32, strided<[32, 1], offset: 0>> │
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
             Low-Level Code Generation (LLVM IR, CPU / GPU Execution)
```

---

## 2. Structural Differences Between Tensors and MemRefs

| Characteristic | Tensor (`tensor<...>`) | MemRef (`memref<...>`) |
| :--- | :--- | :--- |
| **Semantics** | Immutable SSA Value | Mutable Memory Reference |
| **Storage Model** | Abstract mathematical container | Physical memory address (Pointer + Descriptor) |
| **Aliasing** | Alias-free by definition | Subject to memory aliasing and pointer side effects |
| **Allocation** | No runtime allocation or deallocation | Explicit `memref.alloc`, `memref.alloca`, `memref.dealloc` |
| **Modification** | Functional update (`tensor.insert`) returns new value | In-place mutation (`memref.store`) modifies underlying memory |

---

## 3. Why Is Bufferization Required Before Target Code Generation?

Physical computing hardware (x86 CPU SIMD, ARM, NVIDIA/AMD GPUs) does not possess hardware primitives for infinite mathematical SSA tensors. Hardware operates on hardware addresses, caches, registers, and memory buses.

Bufferization bridge the gap between high-level optimizations and hardware targets by:
1. **Materializing Memory Allocation:** Determining where buffers reside (heap vs. stack).
2. **Eliminating Unnecessary Copies:** Reusing memory slots for operations that can safely mutate data in-place.
3. **Establishing Concrete Data Layouts:** Defining strides, offsets, and alignment required for vector read/write operations and cache performance.

---

## 4. Tensor-to-MemRef Boundary Transformations

During bufferization, tensor operations are transformed into their corresponding memref operations:

### Tensor Definition (Pre-Bufferization)
```mlir
func.func @tensor_example(%A: tensor<4x4xf32>, %B: tensor<4x4xf32>) -> tensor<4x4xf32> {
  %init = tensor.empty() : tensor<4x4xf32>
  %res = linalg.add ins(%A, %B : tensor<4x4xf32>, tensor<4x4xf32>)
                    outs(%init : tensor<4x4xf32>) -> tensor<4x4xf32>
  return %res : tensor<4x4xf32>
}
```

### Bufferized MemRef Definition (Post-Bufferization)
```mlir
func.func @memref_example(%A: memref<4x4xf32>, %B: memref<4x4xf32>) -> memref<4x4xf32> {
  %alloc = memref.alloc() : memref<4x4xf32>
  linalg.add ins(%A, %B : memref<4x4xf32>, memref<4x4xf32>)
             outs(%alloc : memref<4x4xf32>)
  return %alloc : memref<4x4xf32>
}
```

---

## 5. Partial vs. Full Module Bufferization

Historically, MLIR relied on dialect-by-dialect partial bufferization (`--bufferize-linalg`, `--bufferize-scf`, `--bufferize-arith`), which introduced `bufferization.to_memref` and `bufferization.to_tensor` boundary casts. Modern production compilation relies on **One-Shot Module Bufferize**, which analyzes the complete IR globally to produce copy-optimized and cast-free MLIR modules.
