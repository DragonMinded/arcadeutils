# arcadeutils

Collection of utilities written in Python for working with various arcade binaries.
This is mostly suited towards the separated formats found in MAME archival releases
but also work on a variety of binaries from basically anywhere.

## bindiff

Create a binary diff from two same-length binaries, or apply a previously created
diff to a binary to patch that binary. Run it like `./bindiff diff --help` to see
options for diffing, and `./bindiff patch --help` to see options for patching.

The patch format is simple. The number on the left of the colon is the hex offset where
the difference was found, and the numbers on the right are the hex values to find
and replace. A wildcard (`*`) can be substituted for a hex pair for any byte in
the before section if you do not care what the value is, but be aware that this will
make the patch non-reversible. Arbitrary comments are supported anywhere in the diff.
Start a line with the `#` character to create a comment. Special values are recognized
in comments. If you create a comment starting with `# File size:` then the the base
file will be compared against the decimal number placed after the colon and any file
not matching that length will be rejected. If you create a comment starting with
`# Description` then all text after the colon will be seen as a description for the
whole patch. Various code uses this description as a patch title.

Some examples are as follows:

A simple patch changing a byte in a file at offset `0x256` from `0xAA` to `0xDD`:

```
256: AA -> DD
```

That same patch, but only for files that are exactly 1024 bytes long:

```
# File size: 1024
256: AA -> DD
```

A patch that does not care about one of the bytes it is patching. The byte at `0x513`
can be any value and the patch will still be applied, and altogether 4 bytes starting
at `0x512` will be changed to the hex value `0x00 0x11 0x22 0x33`:

```
512: AA * CC DD -> 00 11 22 33
```

A patch with multiple offsets, and helpful author descriptions for each section:

```
# This part of the patch fixes a sprite offset issue.
128: AA -> BB

# This part of the patch fixes sound playback issues.
256: 33 -> 44
```

## splitrom

Utility for combining/splitting/byteswapping ROM files. Run it like `./splitrom --help`
to see generic help and what commands are available, and like `./splitrom <command> --help`
for a specific command's help.

## Developing

The tools here are fully typed, and should be kept that way. To verify type hints, run the following:

```
mypy --strict .
```

The tools are also lint clean (save for line length lints which are useless drivel). To verify lint, run the following:

```
flake8 --ignore E501 .
```

The tools also have their own unit tests. To verify tests, run the following:

```
python3 -m unittest discover tests
```

## Including This Package

By design, this code can be used as a library by other python code, and as it is Public Domain,
it can be included wherever. I would prefer that you attribute me when possible, but it is not
necessary. This package can be found on PyPI under "arcadeutils", or you can clone the repo and
run `pip install .` on the root and the package will be installed for you. Alternatively if you
place the line `git+https://github.com/DragonMinded/arcadeutils.git@main#egg=arcadeutils` in your
requirements file, then when you run `pip install -r requirements.txt` on your own code, the latest
version of this package will be installed for you.
