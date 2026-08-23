Fix `astropy.io.fits.connect.is_fits()` so a non-FITS path with no positional
HDU argument returns `False` instead of raising `IndexError`.

The named implementation module is `astropy/io/fits/connect.py`. Keep the
repair local to that implementation module. Do not modify tests, metadata, or
dependencies. Use only the visible workspace. Do not use web search, a browser,
network access, or external documentation.

The visible regression test is already present and fails on the seed:

`PYTHONPATH="$PWD" python -m pytest -p no:warnings -q astropy/io/fits/tests/test_connect.py::test_is_fits_gh_14305`

Inspect the named implementation and nearest visible regression, implement the
smallest coherent repair, and report the modified file and final verification.
