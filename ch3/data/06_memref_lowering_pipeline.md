---
title: "MemRef Lowering & Memory Management"
category: "MLIR / MemRef"
file_name: "06_memref_lowering_pipeline.md"
---

# MemRef Lowering & Memory Management

The `memref` dialect represents multi-dimensional memory buffers with dynamic or static shapes, strides, layouts, and memory spaces. Lowering `memref` operations converts abstract multi-dimensional indices into raw pointer arithmetic and low-level memory allocation calls compatible with standard C/C++ runtime ABIs and LLVM IR.

---

## 1. Allocation Policies: Stack vs. Heap

In MLIR compiler pipelines, memory buffers are allocated using two distinct allocation mechanisms:

### 1. Heap Allocation (`memref.alloc`)
* **Behavior:** Allocates memory dynamically on the heap via standard C runtime `malloc` or aligned memory allocation calls (`posix_memalign`).
* **Lifetime:** Persistent across stack frames; requires explicit deallocation via `memref.dealloc`.
* **Use Case:** Large tensors, function return values, dynamic shape buffers.

```mlir
%heap_mem = memref.alloc(%dim0) : memref<?x128xf32>
// ... operations ...
memref.dealloc %heap_mem : memref<?x128xf32>
```

### 2. Stack Allocation (`memref.alloca`)
* **Behavior:** Allocates memory on the thread stack frame using `alloca`.
* **Lifetime:** Automatically reclaimed when the surrounding function frame pops.
* **Use Case:** Small, fixed-size intermediate tile buffers created during loop tiling. Zero runtime allocation cost.

```mlir
%stack_tile = memref.alloca() : memref<16x16xf32>
// Reclaimed automatically at func return
```

---

## 2. Memory Lifetime Management & Buffer Deallocation Pass

To prevent memory leaks without requiring garbage collection, MLIR provides automated buffer deallocation transformations:

* `--buffer-deallocation`: Automatically places `memref.dealloc` operations at the end of buffer lifetimes using dataflow analysis.
* `--buffer-loop-hoisting`: Hoists buffer allocations out of inner loop iterations to prevent repeated allocation/deallocation overhead.

---

## 3. Key Transformation Passes

Lowering memref operations to LLVM requires expanding complex strided layout metadata prior to struct descriptor conversion:

```
┌──────────────────────────────────────────────────────────┐
│                   Abstract MemRef IR                     │
│         memref<128x256xf32, strided<[256, 1]>>           │
└──────────────────────────────────────────────────────────┘
                             │
                             │  --expand-strided-metadata
                             ▼
┌──────────────────────────────────────────────────────────┐
│             Flat Base MemRef + Offset Compute            │
│         memref.extract_aligned_pointer_as_index          │
│         memref.extract_strided_metadata                  │
└──────────────────────────────────────────────────────────┘
                             │
                             │  --finalize-memref-to-llvm
                             ▼
┌──────────────────────────────────────────────────────────┐
│              LLVM Bare-Ptr / Struct Descriptor           │
│        !llvm.struct<(ptr, ptr, i64, array<2xi64>, ...)>  │
└──────────────────────────────────────────────────────────┘
```

### Detailed Pass Roles
1. `--expand-strided-metadata`: Replaces complex subviews and strided memref operations with explicit linear pointer offset arithmetic (`base_ptr + offset + i * stride0 + j * stride1`).
2. `--finalize-memref-to-llvm`: Translates MLIR `memref` types into standard LLVM struct descriptors.

---

## 4. The C/LLVM MemRef Descriptor ABI Structure

When a `memref<Rank x Type>` is lowered to the LLVM dialect, it is converted into an explicit C-compatible struct descriptor holding pointer and layout metadata:

```cpp
// Equivalent C++ struct definition for memref<2x3xf32>
template <typename T, size_t Rank>
struct MemRefDescriptor {
  T *allocated_ptr;       // Pointer to raw allocated buffer base
  T *aligned_ptr;         // Pointer to data start (aligned for SIMD loads)
  int64_t offset;         // Initial offset (in elements)
  int64_t sizes[Rank];    // Extents of each dimension
  int64_t strides[Rank];  // Stride (element step) of each dimension
};
```

### LLVM Dialect Representation
```mlir
// MLIR Representation of a 2D float memref descriptor:
!llvm.struct<(
  ptr<f32>,              // allocatedPtr
  ptr<f32>,              // alignedPtr
  i64,                   // offset
  array<2 x i64>,        // sizes [dim0, dim1]
  array<2 x i64>         // strides [stride0, stride1]
)>
```

This descriptor ABI allows C/C++ applications or runtime wrappers to pass dynamic arrays directly into compiled MLIR functions via pointers.
