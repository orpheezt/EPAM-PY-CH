---
title: "Lowering Linalg to Loops & Control Flow"
category: "MLIR / Lowering Pipelines"
file_name: "04_linalg_to_loops_lowering.md"
---

# Lowering Linalg to Loops & Control Flow

Lowering Linalg operations to structured loops (`scf.for`, `scf.parallel`, `affine.for`) is a critical step in lowering high-level tensor/buffer operations down to imperative control-flow instructions suitable for scalar CPU code generation or low-level target runtime compilation.

---

## 1. Overview of Linalg Lowering Passes

| Optimization / Lowering Pass | Description | Output Dialects |
| :--- | :--- | :--- |
| `--convert-linalg-to-loops` | Lowers all Linalg ops to sequential nested loop constructs (`scf.for`). | `scf`, `memref`, `arith` |
| `--convert-linalg-to-parallel-loops` | Maps parallel iterator dimensions (`#linalg.iterator_type<parallel>`) to `scf.parallel`. | `scf`, `memref`, `arith` |
| `--convert-linalg-to-affine-loops` | Lowers Linalg ops with affine indexing maps to `affine.for` loops for polyhedral analysis. | `affine`, `memref`, `arith` |
| `--lower-affine` | Expands `affine.for`, `affine.load`, and `affine.apply` into explicit `scf.for` and `arith` ops. | `scf`, `memref`, `arith` |

---

## 2. Transformation Pipeline Walkthrough

A typical lowering transformation sequence converts Linalg structured ops operating on MemRefs into scalar loop iterations:

```
┌─────────────────────────────────────────────────────────┐
│              Linalg Op on Buffer (MemRef)               │
│  linalg.generic ins(%A, %B) outs(%C)                    │
└─────────────────────────────────────────────────────────┘
                            │
                            │  --convert-linalg-to-loops
                            ▼
┌─────────────────────────────────────────────────────────┐
│               Structured Control Flow (SCF)             │
│  scf.for %i = %c0 to %c128 step %c1 {                    │
│    scf.for %j = %c0 to %c512 step %c1 {                 │
│      %a = memref.load %A[%i, %j]                        │
│      ...                                                │
│      memref.store %res, %C[%i, %j]                      │
│    }                                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
                            │
                            │  --convert-scf-to-cf
                            ▼
┌─────────────────────────────────────────────────────────┐
│            Control Flow Dialect (Basic Blocks)          │
│  cf.br ^bb1(%c0)                                        │
│  ^bb1(%i: index):                                       │
│    %cond = arith.cmpi slt, %i, %c128                    │
│    cf.cond_br %cond, ^bb2, ^bb3                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Code Example: `linalg.generic` to `scf.for` Lowering

### Input MLIR (Linalg Op on MemRef)
```mlir
func.func @add_buffers(%A: memref<128x256xf32>, 
                       %B: memref<128x256xf32>, 
                       %C: memref<128x256xf32>) {
  linalg.generic {
    indexing_maps = [
      affine_map<(d0, d1) -> (d0, d1)>,
      affine_map<(d0, d1) -> (d0, d1)>,
      affine_map<(d0, d1) -> (d0, d1)>
    ],
    iterator_types = [#linalg.iterator_type<parallel>, #linalg.iterator_type<parallel>]
  } ins(%A, %B : memref<128x256xf32>, memref<128x256xf32>)
    outs(%C : memref<128x256xf32>) {
  ^bb0(%a: f32, %b: f32, %c: f32):
    %res = arith.addf %a, %b : f32
    linalg.yield %res : f32
  }
  return
}
```

### Output MLIR after `--convert-linalg-to-loops`
```mlir
func.func @add_buffers(%A: memref<128x256xf32>, 
                       %B: memref<128x256xf32>, 
                       %C: memref<128x256xf32>) {
  %c0 = arith.constant 0 : index
  %c1 = arith.constant 1 : index
  %c128 = arith.constant 128 : index
  %c256 = arith.constant 256 : index

  scf.for %i = %c0 to %c128 step %c1 {
    scf.for %j = %c0 to %c256 step %c1 {
      %a = memref.load %A[%i, %j] : memref<128x256xf32>
      %b = memref.load %B[%i, %j] : memref<128x256xf32>
      %res = arith.addf %a, %b : f32
      memref.store %res, %C[%i, %j] : memref<128x256xf32>
    }
  }
  return
}
```

---

## 4. Tiling & Fusion Integration Prior to Loop Lowering

Lowering to loops directly on un-tiled Linalg operations can result in poor cache locality for large matrices. Compiler pipelines typically apply **Linalg Tiling** (`--linalg-tile-to-scf-for`) before converting remaining payload blocks to loops:

```bash
# Example optimization pipeline
mlir-opt input.mlir \
  --transform-interpreter \
  --one-shot-bufferize \
  --convert-linalg-to-loops \
  --lower-affine \
  --canonicalize
```

Tiling splits big iteration spaces into tile-sized sub-matrices, generating nested `scf.for` tiles containing smaller `linalg.generic` ops before final scalar loop materialization.
