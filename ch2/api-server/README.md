```text
"I'm sorry, Dave. I'm afraid I can't do that."
```

Hi!

This is my solution for the challenge, feel free to run

```bash
./e2e_challenge.sh
```

it will run the challenge E2E

```text
Pipeline Steps:
  1. Build container image (api-server:TAG) via buildah & export zstd archive
  2. Display image size & layer breakdown diagnostics (scripts/image_diagnostics.py)
  3. Start containerized application on a free port (podman/docker) with .env
  4. Wait for /health endpoint readiness
  5. Execute Amazon Reviews test suite (scripts/test_amazon_reviews.py)
  6. Automatically clean up test container on exit
```

I hope you appreciate the docker containerization. It allows me to use on the flow `uv build`.
So that we consume the app wheel. So that we can also package it in an index.

And two of my additions, diagnostics and signing.

Also as said in the statement I used the models

- `finiteautomata/beto-sentiment-analysis`
- `facebook/bart-large-cnn`

And the dataset

- `SetFit/amazon_reviews_multi_en`

**WHICH IS USED IN E2E**

Also put an `.env` with

```bash
HF_TOKEN=<your-token>
```

What I offer is an summary and quantification of user reviews with bad comments.

So I orchestrate both the sentiment analysis API and summarization

Although I had some problems, spanish models were not good or those were not offered on inference API.
Also it would be better to use an small LLM and structure an prompt like:

`Arrange those bad comments into categories and put improvement suggestions`

To end this, I made it so that I can interchange inference provider, but there is an caveat about the design.

For the moment, or on early versions it was static typed. I have to build an way to manage deps, env/config and DI seamlessly.
