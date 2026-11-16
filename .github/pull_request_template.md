## What this changes and why

<!-- One or two sentences. Link the issue if there is one. -->

## How you tested it

<!-- The commands you ran and what you saw. If you ran it against a RotorLab organization
     with a test key, say which example and which call. Never paste the key. -->

## Checklist

- [ ] The tests pass: `python -m unittest discover -s tests -v`
- [ ] Python 3.8 or later, standard library only.
- [ ] The key comes from `ROTORLAB_API_KEY` and the address from `ROTORLAB_URL`, never from an argument or a file in the repository.
- [ ] Key setup never puts a key into a command line, shell history or a committed file.
- [ ] MCP setup text tells the reader to untick every other area.
- [ ] `openapi/` and `postman/` are unchanged (they are copies of RotorLab's published files).
- [ ] No real key, credential, webhook secret, personal data or real host name anywhere in the change.
- [ ] US spelling, and no claim that RotorLab authorizes, approves or clears a flight.

By opening this pull request, I agree that my contribution is licensed under the Apache License, Version 2.0.
