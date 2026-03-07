# 03 – Privacy Demo (deterministic scrub → LLM → deterministic restore)

Privacy is enforced **in code** using `DeterministicAgent` + `sequential()` orchestration — the LLM never has to call privacy tools itself:

1. **Scrubber** (deterministic) – `PrivacyPipeline.scrub()` replaces PII with placeholders
2. **Assistant** (LLM) – reasons over the scrubbed text; never sees real data
3. **Restorer** (deterministic) – `PrivacyPipeline.restore()` puts originals back

```bash
python examples/03_privacy_demo/run.py
```

Try pasting text with e-mails, IBANs, phone numbers, or monetary amounts.
