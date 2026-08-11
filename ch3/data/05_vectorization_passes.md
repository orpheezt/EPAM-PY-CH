---
title: "Vectorization and Vector Dialect Lowering"
category: "MLIR / Vectorization"
file_name: "05_vectorization_passes.md"
---

# Vectorization and Vector Dialect Lowering

**Vectorization** converts scalar iterations or high-level structured operations into hardware SIMD (Single Instruction, Multiple Data) operations. MLIR uses the `vector` dialect to express multi-dimensional vector operations independently of underlying target vector hardware (x86 AVX-512, ARM NEON/SVE, RISC-V Vector Extensions).

---

## 1. Structured Operation Vectorization (`--linalg-vectorize`)

Instead of lowering Linalg structured ops to scalar `scf.for` iterations, the compiler can vectorize contiguous dimensions directly using `--linalg-vectorize` or MLIR Transform Dialect rules.

### Vectorization Benefits
* Avoids scalar memory load/store overhead (`memref.load` / `memref.store`).
* Emits high-level vector primitives (`vector.transfer_read`, `vector.contract`, `vector.transfer_write`).
* Preserves multi-dimensional vector semantics prior to low-level SIMD target lowering.

---

## 2. Core Vector Dialect Primitives

| Vector Operation | Description |
| :--- | :--- |
| `vector.transfer_read` | Performs a contiguous or strided read from a `memref`/`tensor` into a 1D/2D/nD `vector`, supporting padding and dynamic masking. |
| `vector.transfer_write` | Writes a multi-dimensional vector back into memory (`memref`/`tensor`). |
| `vector.contract` | Generalized matrix/tensor contraction (dot products, matmul, convolutions) on pure vector types. |
| `vector.fma` | Multi-dimensional Fused Multiply-Add ($a \times b + c$). |
| `vector.broadcast` | Replicates lower-rank vectors or scalars into higher-rank vectors. |
| `vector.mask` | Wraps vector operations with dynamic execution masks for tail-handling. |

---

## 3. Code Example: Matrix Multiplication Vectorization

### Linalg Matmul Op
```mlir
func.func @matmul_on_buffers(%A: memref<8x16xf32>, %B: memref<16x32xf32>, %C: memref<8x32xf32>) {
  linalg.matmul ins(%A, %B : memref<8x16xf32>, memref<16x32xf32>)
                outs(%C : memref<8x32xf32>)
  return
}
```

### Vectorized IR (`--linalg-vectorize`)
```mlir
#map_a = affine_map<(i, j, k) -> (i, k)>
#map_b = affine_map<(i, j, k) -> (k, j)>
#map_c = affine_map<(i, j, k) -> (i, j)>

func.func @matmul_on_buffers_vectorized(%A: memref<8x16xf32>, 
                                        %B: memref<16x32xf32>, 
                                        %C: memref<8x32xf32>) {
  %c0 = arith.constant 0 : index
  %cf0 = arith.constant 0.0 : f32

  %vec_A = vector.transfer_read %A[%c0, %c0], %cf0 : memref<8x16xf32>, vector<8x16xf32>
  %vec_B = vector.transfer_read %B[%c0, %c0], %cf0 : memref<16x32xf32>, vector<16x32xf32>
  %vec_C = vector.transfer_read %C[%c0, %c0], %cf0 : memref<8x32xf32>, vector<8x32xf32>

  %res = vector.contract {
    indexing_maps = [#map_a, #map_b, #map_c],
    iterator_types = ["parallel", "parallel", "reduction"]
  } %vec_A, %vec_B, %vec_C : vector<8x16xf32>, vector<16x32xf32> into vector<8x32xf32>

  vector.transfer_write %res, %C[%c0, %c0] : vector<8x32xf32>, memref<8x32xf32>
  return
}
```

---

## 4. Lowering the Vector Dialect to LLVM SIMD Target Passes

Once operations are expressed in the `vector` dialect, they undergo unrolling and linear flat vector conversions before lowering to LLVM IR:

```
┌─────────────────────────────────────────────────────────┐
│               n-Dimensional Vector Ops                  │
│       vector<8x32xf32> (transfer_read/contract)         │
└─────────────────────────────────────────────────────────┘
                            │
                            │  --convert-vector-to-scf
                            │  --lower-vector-mask
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 1D Flat Vector Primitives               │
│       vector<16xf32> (vector.fma, vector.load)          │
└─────────────────────────────────────────────────────────┘
                            │
                            │  --convert-vector-to-llvm
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 LLVM Dialect Intrinsic Ops              │
│       llvm.x86.avx512.mask.fma.ps.512 / llvm.fmuladd    │
└─────────────────────────────────────────────────────────┘
```

### Essential Vector Lowering Passes
* `--lower-vector-mask`: Expands dynamic vector masks into logical mask operations.
* `--convert-vector-to-scf`: Converts high-dimensional vector transfers with dynamic strides into scalar loops + flat 1D vector operations.
* `--convert-vector-to-llvm`: Translates 1D MLIR vectors into native LLVM IR vector types (`<16 x float>`).
