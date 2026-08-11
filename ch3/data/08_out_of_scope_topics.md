---
title: "Explicit Scope Boundaries & Non-Covered Topics"
category: "MLIR / Scope Boundaries"
file_name: "08_out_of_scope_topics.md"
---

# Explicit Scope Boundaries & Non-Covered Topics

This document establishes the explicit technical boundaries of this Knowledge Base repository. It defines specific technologies, dialects, runtime environments, and programming language bindings that are **strictly OUT OF SCOPE**.

This document serves as an explicit fallback boundary for RAG (Retrieval-Augmented Generation) indexing systems, ensuring that out-of-domain technical queries are correctly flagged as unhandled.

---

## 1. Strictly Out-of-Scope Technical Domains

The following technical areas are **NOT** covered within this repository or Knowledge Base:

### 1. Triton GPU Dialect & Triton IR
* **Excluded Topics:** Triton compiler internals, `tt.load`, `tt.store`, `tt.dot`, Triton block-level programming models, Triton-to-LLVMGPU translation, or OpenAI Triton custom kernel creation.

### 2. High-Level Language Bindings for MLIR
* **Excluded Topics:** Python MLIR bindings (`mlir-python`, `mlir.ir`, `mlir.passmanager`), Rust bindings (`melior`), C# wrappers, or Swift MLIR integrations.

### 3. SPIR-V Dialect & Vulkan / OpenCL Compute Targets
* **Excluded Topics:** `spirv` dialect, `--convert-gpu-to-spirv`, Vulkan shader translation, OpenCL SPIR-V binary generation, or WebGPU code generation pipelines.

### 4. Custom C++ Dialect Authoring & TableGen (ODS)
* **Excluded Topics:** Authoring new MLIR dialects from scratch using C++, TableGen Operation Definition Specification (`OpDefinitionGen`, `DialectGen`), writing custom `mlir-tblgen` rules, or implementing C++ C++ Pass plugins (`PassWrapper`).

---

## 2. Technical Summary of Covered vs. Non-Covered Topics

| Domain | Included in Knowledge Base? | Coverage Reference |
| :--- | :--- | :--- |
| **MLIR Linalg Dialect & Structured Ops** | **YES** | `01_mlir_linalg_overview.md` |
| **Bufferization Concepts (Tensor vs. MemRef)** | **YES** | `02_bufferization_concepts.md` |
| **Modern One-Shot Bufferize (`--one-shot-bufferize`)** | **YES** | `03_one_shot_bufferize.md` |
| **Linalg to Loops (`scf.for`, `scf.parallel`)** | **YES** | `04_linalg_to_loops_lowering.md` |
| **Vectorization Passes (`--linalg-vectorize`)** | **YES** | `05_vectorization_passes.md` |
| **MemRef Lowering & Struct Descriptors** | **YES** | `06_memref_lowering_pipeline.md` |
| **JIT Execution & `ExecutionEngine`** | **YES** | `07_execution_engine_runner.md` |
| **Triton GPU Dialect** | **NO (Out of Scope)** | Excluded |
| **Rust / Python MLIR Bindings** | **NO (Out of Scope)** | Excluded |
| **SPIR-V / Vulkan Target Lowering** | **NO (Out of Scope)** | Excluded |
| **Custom C++ Dialect Authoring via TableGen** | **NO (Out of Scope)** | Excluded |

---

## 3. Recommended RAG Fallback Handling Guidelines

When evaluating user prompts using LangChain or Qdrant similarity searches against this Knowledge Base:
1. **Detection:** If a query matches concepts listed in Section 1 (e.g., Triton, Python API bindings, SPIR-V, TableGen custom ops), the RAG retriever should score high relevance with `08_out_of_scope_topics.md`.
2. **Fallback Strategy:** The system should politely decline to answer, explicitly citing that the query falls outside the scope of the MLIR Linalg & Lowering Pipelines Knowledge Base.
