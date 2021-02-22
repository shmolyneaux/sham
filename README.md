# Testing
Test by running `make test`. Testing requires (`pg_tmp`](https://eradman.com/ephemeralpg/).

# Running in Development
Install `sham` into the poetry virtualenv:
```
poetry install
```

Then run `sham`:
```
poetry run sham
```

# Running with Python 3.10 Pattern Matching

This project uses a development branch of Python 3.10 that supports pattern
matching. This is pretty weird! I do not recommend this, I just wanted to try
it out.

Here's the setup I needed to get this working:
- Pattern Matching Python Version: d5f32da322
- uvloop version: c808a663b2 (version "0.16.0.dev0" hardcoded in setup.py)
- asyncpg version: a308a9736e (I had to hack up the cpython output to not reference `_PyGen_Send`... it's not clear to me how PY_VERSION_HEX is set, so I could not do this automatically) (also updated the minimum Cython version to 0.29.22)
