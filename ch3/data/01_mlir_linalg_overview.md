---
title: "MLIR Linalg Dialect Overview & Structured Ops"
category: "MLIR / Linalg"
file_name: "01_mlir_linalg_overview.md"
---

# MLIR Linalg Dialect Overview & Structured Ops

The **Linalg dialect** (Linear Algebra dialect) in MLIR provides high-level representation and transformation abstractions for dense tensor and buffer compute operations. It serves as a central domain for high-performance computing (HPC), machine learning compilation, and tensor transformations prior to loop generation or vectorization.

---

## 1. Core Design Philosophy & Value Semantics

The primary design principle of the Linalg dialect is **Structured Operations (Structured Ops)** operating on payload data with explicit iteration domain descriptions.

Linalg operations support two distinct semantics models:
* **Value Semantics (Tensor Domain):** Operations take input tensors, yield new result tensors, and preserve pure Static Single Assignment (SSA) form with immutability.
* **Buffer Semantics (MemRef Domain):** Operations operate in-place on mutable memory references (`memref`), reading from and writing to explicit memory locations without returning SSA values.

### Value Semantics Example (`linalg.matmul` on Tensors)
```mlir
%C = linalg.matmul 
  ins(%A, %B : tensor<128x256xf32>, tensor<256x512xf32>)
  outs(%C_init : tensor<128x512xf32>) -> tensor<128x512xf32>
```

---

## 2. The `linalg.generic` Op Anatomy

`linalg.generic` is the core generic structured operation in MLIR. Every named operation (e.g., `linalg.matmul`, `linalg.add`, `linalg.conv_2d`) is a specialized instance or concept subset of `linalg.generic`.

### Key Attributes of `linalg.generic`

1. **`indexing_maps` (`affine_map` array):** Defines how iteration domain dimensions map to input/output multi-dimensional indices.
2. **`iterator_types`:** Defines the behavior of each loop dimension in the iteration domain:
   * `#linalg.iterator_type<parallel>`: Elements within this dimension can be processed independently.
   * `#linalg.iterator_type<reduction>`: Elements require accumulation/reduction across iterations.
3. **Payload Region:** A basic block containing scalar calculations that execute at each point in the iteration domain.

### Complete `linalg.generic` Example: Matrix Multiplication ($C = A \cdot B + C$)

```mlir
#map_A = affine_map<(i, j, k) -> (i, k)>
#map_B = affine_map<(i, j, k) -> (k, j)>
#map_C = affine_map<(i, j, k) -> (i, j)>

func.func @matmul_generic(%A: tensor<128x256xf32>, 
                          %B: tensor<256x512xf32>, 
                          %C_init: tensor<128x512xf32>) -> tensor<128x512xf32> {
  %C = linalg.generic {
    indexing_maps = [#map_A, #map_B, #map_C],
    iterator_types = [#linalg.iterator_type<parallel>, 
                      #linalg.iterator_type<parallel>, 
                      #linalg.iterator_type<reduction>]
  } ins(%A, %B : tensor<128x256xf32>, tensor<256x512xf32>)
    outs(%C_init : tensor<128x512xf32>) {
  ^bb0(%a_val: f32, %b_val: f32, %c_val: f32):
    %mul = arith.mulf %a_val, %b_val : f32
    %add = arith.addf %c_val, %mul : f32
    linalg.yield %add : f32
  } -> tensor<128x512xf32>

  return %C : tensor<128x512xf32>
}
```

---

## 3. Key Differences: Linalg vs. Standard Loops

| Feature | Standard LLVM/SCF Loops (`scf.for`) | MLIR Linalg Structured Ops |
| :--- | :--- | :--- |
| **Domain Representation** | Explicit loop bounds (`lower`, `upper`, `step`) | Implicit hyper-rectangular iteration space |
| **Data Access** | Explicit multi-dimensional indexing operations (`memref.load`) | Declarative Affine Maps (`indexing_maps`) |
| **Order Dependency** | Enforces sequential or parallel execution ordering | Dimension order invariant until lowered |
| **Tiling & Fusion** | Requires complex polyhedral analysis or AST rewrites | Trivial algebraic transformations on `indexing_maps` |
| **Semantics** | Explicit pointer/memory access | Dual: Tensor (SSA) and MemRef (Buffer) |

---

## 4. Why Use Linalg in Compiler Pipelines?

* **Declarative Payload:** Separates computation payload (e.g., `arith.mulf`) from iteration space structure.
* **Transformability:** Provides a uniform target for high-level compiler optimizations including tiling, vectorization, operator fusion, and bufferization.
* **Dialect Interoperability:** Bridges high-level framework dialects (Tosa, StableHLO, Torch) and low-level loop/vector dialects (`scf`, `vector`, `llvm`).
