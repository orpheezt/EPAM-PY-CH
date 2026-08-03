Mmmmm dont think this will fail but...

Ensure to have docker/podman installed and also buildah (this one is important)

Here I leave an run

```bash
$ ./e2e_challenge2.sh
=== Step 1: Building container image ===
Relabeling SELinux context for bind mounts...
Building container image api-server:0.1.0 using Python 3.14.6...
[1/2] STEP 1/8: FROM python:3.14.6-slim-trixie AS builder
[1/2] STEP 2/8: COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/
--> Using cache a925fc1c289a3477bc1388f2f32c548d8bbe6d01eb42881a0b54dcaa03376256
--> a925fc1c289a
[1/2] STEP 3/8: ENV PYTHONDONTWRITEBYTECODE=1     UV_NO_MANAGED_PYTHON=1     UV_PYTHON_DOWNLOADS=never     UV_COMPILE_BYTECODE=1     UV_LINK_MODE=copy
--> Using cache c8527284cfe02e79332d2c8e46e1d5873834b7dfa9f75f8dbc853950bfe736e8
--> c8527284cfe0
[1/2] STEP 4/8: WORKDIR /app
--> Using cache 984a5ab269138fa4ed251dceeb7cc8b33678b4eda9a616b8efc8c6d58337e277
--> 984a5ab26913
[1/2] STEP 5/8: RUN --mount=type=cache,target=/root/.cache/uv     --mount=type=bind,source=uv.lock,target=uv.lock     --mount=type=bind,source=pyproject.toml,target=pyproject.toml     uv sync --locked --no-install-project --no-dev
--> Using cache 6e0995a35031b0870e207dda5d560d2a74f8a5f3eca01247dd0b43e58f948eef
--> 6e0995a35031
[1/2] STEP 6/8: COPY . /app
--> Using cache 7b46d73618073dd00d48651dab1915fb2a47ccc8951f5324b3c5f0fa3fec315c
--> 7b46d7361807
[1/2] STEP 7/8: RUN --mount=type=cache,target=/root/.cache/uv     uv build --wheel --out-dir /tmp/dist
--> Using cache 45068f625f59cf534c17fb678eb0b0ccba389b8b7c54f55485fcb80036000aa5
--> 45068f625f59
[1/2] STEP 8/8: RUN --mount=type=cache,target=/root/.cache/uv     uv pip install /tmp/dist/*.whl --target /app/app-packages --no-deps
--> Using cache 7a1c6258f2cc07a11047b479c836e87c2e2f804e05be8eea4b6891f31d8e495c
--> 7a1c6258f2cc
[2/2] STEP 1/10: FROM python:3.14.6-slim-trixie
[2/2] STEP 2/10: WORKDIR /app
--> Using cache bef59a18584fd4b7f9cc27723a21332ce9c9e8ac2ffd39b0861e10a664a7c01e
--> bef59a18584f
[2/2] STEP 3/10: ENV PATH="/app/.venv/bin:$PATH"     PYTHONPATH="/app/app-packages:$PYTHONPATH"     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1
--> Using cache b28a97da3536ea1c77b18d674e8de928c8ab4700b2b9ea33b0ded0273c30a2f9
--> b28a97da3536
[2/2] STEP 4/10: COPY --from=builder /app/.venv /app/.venv
--> Using cache 4ba8de170d20066ce925ab322eadc5a1d6148fa897e0c942552f9d6912f2e41d
--> 4ba8de170d20
[2/2] STEP 5/10: COPY --from=builder /app/app-packages /app/app-packages
--> Using cache 0d0bcf8fb1885a04a3a09573ddbd607201de2d16fc8908b8068bd1261c00d59b
--> 0d0bcf8fb188
[2/2] STEP 6/10: ARG UID=10001
--> Using cache 2d23dd67d95b5d03fd61498ed54cc2d533705c28b369f2f92f5df369b8f25e66
--> 2d23dd67d95b
[2/2] STEP 7/10: RUN adduser     --disabled-password     --gecos ""     --home "/nonexistent"     --shell "/sbin/nologin"     --uid "${UID}"     appuser
--> Using cache 7fe3b69b817ec7eaf2bea803ea3a6dde8547e2df12b77645ac3b201cb5ce74e0
--> 7fe3b69b817e
[2/2] STEP 8/10: USER appuser
--> Using cache 3106375305782651a5adeb832a6e9025e07a14f04d5ebd5591d29f50f93abce6
--> 310637530578
[2/2] STEP 9/10: EXPOSE 8000
--> Using cache af90e093f3b0eff775a7915510e6007e0b4b785f409b78ba890e87f0bef78366
--> af90e093f3b0
[2/2] STEP 10/10: CMD ["fastapi", "run", "--entrypoint", "api_server.app:app", "--host", "0.0.0.0", "--port", "8000"]
--> Using cache 89c11e5d7b1fa3fb4758804a39c6e613354cfa9bb944726594baa669cc0400c0
[2/2] COMMIT api-server:0.1.0
--> 89c11e5d7b1f
Successfully tagged localhost/api-server:0.1.0
89c11e5d7b1fa3fb4758804a39c6e613354cfa9bb944726594baa669cc0400c0
Successfully built api-server:0.1.0 and tagged as api-server:latest
Pushing image to OCI archive with zstd compression: out/api-server-0.1.0.tar.zst...
Getting image source signatures
Copying blob f2ec4de84f55 done   | 
Copying blob 04bed2b2c283 done   | 
Copying blob f3e1c7200b91 done   | 
Copying blob 913a5e9a7672 done   | 
Copying blob 406e78f746e2 done   | 
Copying blob e90f0e01b91d done   | 
Copying blob 83764a04c904 done   | 
Copying config 89c11e5d7b done   | 
Writing manifest to image destination
Successfully exported OCI archive with zstd compression to out/api-server-0.1.0.tar.zst

=== Step 2: Displaying Container Image Diagnostics ===
╭─ IMAGE SIZE DIAGNOSTICS: api-server:0.1.0 ─╮
│ Image ID: 89c11e5d7b1f                     │
│ Created At: 2026-07-13T00:00:00Z           │
╰────────────────────────────────────────────╯
          Component Breakdown (Uncompressed Image)           
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Component                       ┃       Size ┃ Percentage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 1. Base Image (python slim)     │   123.4 MB │  [ 61.8% ] │
│ 2. Dependencies (/app/.venv)    │    76.3 MB │  [ 38.2% ] │
│ 3. App Code (/app/app-packages) │   103.4 kB │  [ <0.1% ] │
│ 4. Setup & Metadata             │    15.4 kB │  [ <0.1% ] │
└─────────────────────────────────┴────────────┴────────────┘
Total Uncompressed Image Size:   199.9 MB (199,910,912 bytes)

--- Compressed Export Archive ---
Archive Path:       out/api-server-0.1.0.tar.zst
Archive Size:          60.4 MB (60,412,416 bytes)
Compression Ratio:  30.2% of original size (3.31x compression)

--- Signature Status (GPG) ---
Signature File:     out/api-server-0.1.0.tar.zst.asc
Status:             UNSIGNED

--- Insights ---
* Base image accounts for 61.8% of total image footprint.
* Python dependencies (.venv) account for 38.2% of image size.
* Compressed zstd archive saves 133.04 MB compared to container storage.
* Archive is unsigned. Run './scripts/image.sh sign <KEY_ID>' to generate GPG signature.

=== Step 3: Starting container 'api-server-test-0.1.0-8000' on port 8000 ===
6c1b91a4cbf741875bcf650cb7f4111f3b972dc95178b8e2d3101deae0807192
Waiting for API server to become ready at http://127.0.0.1:8000/health...
API server healthcheck passed!

=== Step 4: Running Amazon Reviews Test Suite ===
╭───────────── AMAZON REVIEWS LIVE API TEST ──────────────╮
│ Target URL: http://127.0.0.1:8000                       │
│ Dataset:    SetFit/amazon_reviews_multi_en (test split) │
│ Samples:    2 per rating level (total 10)               │
╰─────────────────────────────────────────────────────────╯
⠴ Loading dataset from Hugging Face Hub...Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
✓ Server Healthcheck: {'status': 'OK', 'inference_provider': 'hf_api', 'version': '0.1.0'}

1. Testing /analyze-feedback (Single Reviews)
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Rating Category        ┃ Review Snippet                                   ┃ Predicted Label ┃  Score ┃   Latency ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ 1-Star (Very Negative) │ These are AWFUL. They are see through, the fa... │ NEUTRAL         │ 0.9928 │ 3867.4 ms │
│ 1-Star (Very Negative) │ I bought 4 and NONE of them worked. Yes I use... │ NEUTRAL         │ 0.9982 │  226.9 ms │
│ 2-Star (Negative)      │ I use these shoes when I’m kayaking, once the... │ NEUTRAL         │ 0.9952 │  191.3 ms │
│ 2-Star (Negative)      │ The LED ring works, but the remainder of the ... │ NEUTRAL         │ 0.9956 │  221.3 ms │
│ 3-Star (Neutral)       │ If you're into thick tshirts, then this is th... │ POSITIVE        │ 0.6740 │  253.8 ms │
└────────────────────────┴──────────────────────────────────────────────────┴─────────────────┴────────┴───────────┘

2. Testing /analyze-feedback/batch (Batch Analysis)
Total Reviews:     10
Negative Count:    0
Batch Processing:  5178.7 ms
Executive Summary: "These are AWFUL. They are see through, the fabric feels like tablecloth, and they fit like children’s clothing. Customer service did seem to be nice though, but I regret missing my return date
for these. I wouldn’t even donate them because the quality"

=== Step 5: Cleaning up test container 'api-server-test-0.1.0-8000' ===
Cleanup complete.

```
