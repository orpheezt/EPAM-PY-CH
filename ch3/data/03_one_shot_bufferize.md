---
title: "Modern One-Shot Bufferize Pass"
category: "MLIR / Bufferization"
file_name: "03_one_shot_bufferize.md"
---

# Modern One-Shot Bufferize Pass

`--one-shot-bufferize` is MLIR's state-of-the-art, module-level bufferization algorithm. Unlike legacy dialect-by-dialect partial bufferization passes, One-Shot Bufferize performs a comprehensive Read-After-Write (RAW) conflict and alias analysis to maximize in-place buffer reuse and minimize heap memory allocations.

---

## 1. Core Principles of One-Shot Bufferization

1. **Global Module Analysis:** Analyzes SSA use-def chains backwards and forwards across block boundaries and function calls.
2. **In-Place Execution Optimization:** Operates in-place on existing buffers whenever safe, preventing intermediate buffer copies.
3. **No Intermediate Casts:** Eliminates `to_tensor` / `to_memref` temporary boundary operations.
4. **Declarative Interface (`BufferizableOpInterface`):** Any dialect operation implementing this interface informs the driver of its memory access patterns (reads, writes, aliases, and buffer requirements).

---

## 2. In-Place vs. Copy Analysis (RAW Conflict Detection)

A buffer allocation can be converted to operate in-place if and only if modifying the target memory does not overwrite data required by a subsequent read of an earlier tensor state.

### Read-After-Write (RAW) Conflict Scenario

Consider the following SSA tensor flow:

```mlir
%t1 = ...                            : tensor<100xf32>
%t2 = linalg.elemwise_add %t1, %val  : tensor<100xf32>
%use = linalg.matmul ins(%t1, %t2)   : tensor<100xf32>
```

* **Analysis:** `%t2` is created by modifying `%t1`. However, `%t1` is read afterwards in `linalg.matmul`.
* **Decision:** Bufferizing `%t2` in-place into `%t1`'s memory would overwrite `%t1` before `linalg.matmul` reads it.
* **Resolution:** One-Shot Bufferize marks `%t2` as requiring a copy (`memref.copy` or `memref.alloc`). If `%t1` had no subsequent reads, `%t2` would be written in-place with **zero allocations**.

---

## 3. Explicit Tensor Allocation (`bufferization.alloc_tensor`)

`bufferization.alloc_tensor` is an explicit SSA tensor construct representing a buffer that will be materialized during bufferization.

```mlir
// Tensor representation before bufferization
%t = bufferization.alloc_tensor() : tensor<64x128xf32>

// After --one-shot-bufferize
%m = memref.alloc() : memref<64x128xf32>
```

### In-Place Hint Attributes
```mlir
// Forces bufferization engine to allocate in-place or copy explicitly
%t = bufferization.alloc_tensor() copy(%arg0) {bufferization.escape = [false]} : tensor<64x128xf32>
```

---

## 4. Key Pass Options & Command Line Usage

To run modern One-Shot Bufferization in `mlir-opt`:

```bash
mlir-opt input.mlir \
  --one-shot-bufferize="bufferize-function-boundaries=true allow-return-allocs=false function-boundary-type-conversion=identity-layout-map" \
  --canonicalize \
  --drop-equivalent-buffer-results
```

### Essential Pass Parameters

| Option Parameter | Type | Description |
| :--- | :--- | :--- |
| `bufferize-function-boundaries` | boolean | If true, bufferizes function signatures (`func.func` inputs/outputs). |
| `allow-return-allocs` | boolean | If false, disallows functions from returning newly allocated heap buffers (forces destination-passing style). |
| `function-boundary-type-conversion` | string | Specifies layout maps for function signatures (`fully-dynamic-layout-map` vs `identity-layout-map`). |
| `print-conflicts` | boolean | Debug option to output detected RAW conflicts causing memory copies. |

---

## 5. Destination-Passing Style (DPS)

To ensure optimal memory management, MLIR enforces Destination-Passing Style for structured operations. The caller allocates or provides the memory container (`outs`), and operations mutate or write directly into it.

```mlir
// Destination-Passing Style in Tensor Domain
func.func @dps_example(%arg0: tensor<128xf32>, %out_buffer: tensor<128xf32>) -> tensor<128xf32> {
  // %out_buffer is passed into 'outs'
  %res = linalg.exp ins(%arg0 : tensor<128xf32>) 
                    outs(%out_buffer : tensor<128xf32>) -> tensor<128xf32>
  return %res : tensor<128xf32>
}
```

When bufferized with `bufferize-function-boundaries=true`, this compiles directly to zero-copy memory mutation.
