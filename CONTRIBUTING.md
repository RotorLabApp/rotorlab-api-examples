# Contributing

Thank you for helping improve the RotorLab API examples. Everyone taking part follows our [Code of Conduct](CODE_OF_CONDUCT.md). Questions are welcome as issues, with the question template.

## What fits here

- Fixes to an example that does not work as documented.
- New examples for endpoints that are in RotorLab's published OpenAPI document.
- Clearer explanations.

`openapi/openapi.json` and `postman/rotorlab.postman_collection.json` are copies of RotorLab's published files and are not edited by hand here.

## Rules for examples

- Python 3.8 or later, standard library only.
- Read the key from `ROTORLAB_API_KEY` and the address from `ROTORLAB_URL`, never from a command-line argument or a file in the repository.
- Use placeholder keys that are obviously fake, like `rl_your_key`. Never commit a real key, credential or webhook secret.
- Every script takes `--help` and works offline until it makes its first request.
- Write in US English.
- RotorLab records, reminds and warns; it never authorizes, approves or clears a flight. Examples and text must not suggest otherwise.

## Before you open a pull request

Checklist:

- The tests pass (below).
- No real key, credential or secret anywhere in the change.
- MCP setup text tells the reader to untick every other area.
- Key setup never puts a key into a command line, shell history or a committed file.

```bash
python -m unittest discover -s tests -v
```

If you can, also run your change against a RotorLab organization with a test key, and say in the pull request what you ran.

By contributing, you agree that your contribution is licensed under the Apache License, Version 2.0.
