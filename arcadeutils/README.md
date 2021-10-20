# arcadeutils

Collection of utilities written in Python for working with various arcade binaries.
This is mostly suited towards the separated formats found in MAME archival releases
but also work on a variety of binaries from basically anywhere. It is fully typed
and requires a minimum of Python 3.6 to operate.

## ByteUtil

The ByteUtil class provides a series of handy ROM manipulation functions for combining
split ROMs and byteswapping ROMs. Use these when you are attempting to combine ROMs
that are dumped from multiple chips but are meant to be mapped to high and low bytes
in memory on a 16-bit or 32-bit arcade system.

### ByteUtil.byteswap

Takes a single byte argument "data", assumes that it is a 16-bit ROM where the upper and
lower bytes have been swapped and swaps them. Returns a new bytes object of the same
length where the upper and lower bytes of each 16-bit pair are swapped.

### ByteUtil.wordswap

Takes a single byte argument "data", assumes that it is a 32-bit ROM where each of the 32-bit
words is swapped. Returns a new bytes object of the same length where each 32-bit chunk
of bytes is swapped.

## ByteUtil.combine16bithalves

Takes two byte aruments "upper" and "lower" and assumes that these represent a ROM dump from
two 16-bit chips that are memory-mapped to a 32-bit word on the hardware they were dumped
from. Assembles them both into a single 32-bit ROM file where each 32-bit word is made
up of the 16-bit upper value and 16-bit lower value of the two inputs.

## ByteUtil.combine8bithalves

Takes two byte aruments "upper" and "lower" and assumes that these represent a ROM dump from
two 8-bit chips that are memory-mapped to a 16-bit word on the hardware they were dumped
from. Assembles them both into a single 16-bit ROM file where each half-word is made
up of the 8-bit upper value and 8-bit lower value of the two inputs.

# ByteUtil.split16bithalves

Takes a single byte argument "data", assumes that it is a 32-bit ROM and splits it into
two 16-bit ROMs of the upper and lower halves of each 32-bit value, returning a tuple of
the upper and lower bytes. This is the exact reciprocal of `combine16bithalves`.

# ByteUtil.split8bithalves

Takes a single byte argument "data", assumes that it is a 16-bit ROM and splits it into
two 8-bit ROMs of the upper and lower halves of each 16-bit value, returning a tuple of
the upper and lower bytes. This is the exact reciprocal of `combine8bithalves`.

## FileBytes

A class that can be passed an open file handle for a binary file that was opened either
in read-only or append mode. Presents a bytearray-like interface where data can read
or written as if it was an array in memory without loading the file into RAM. This can
be used with any function in `BinaryDiff` that takes an argument of type bytes in order
to minimize the memory footprint of patching on systems with limited RAM.

In addition to the properties and methods below, you can call len() on an instance of
FileBytes to get the length, you can index into it using array syntax, and you can add
an instance of FileBytes or binary data to an existing FileBytes instance in order to
append data, much like a bytes or bytearray instance.

### handle property

Returns the original handle that this FileBytes instance was constructed with. Note that
this is read-only by design so that the handle cannot be changed out from under the
class.

### clone() method

Returns a clone of the current FileBytes instance so that the clone or original can be
safely modified without affecting the other copy. Note that if you choose to call
`write_changes()` on any instance of a FileBytes, all clones of that instance will
be placed into a mode where they can only be cloned themselves to prevent surprises.

### append() method

Appends bytes or the contents of another FileBytes instance to the end of this instance.
The data will be placed at the very end, resizing the internal representation of the file
to fit the data. When calling `write_changes()` these bytes will be included and the file
will be resized accordingly. Note that appending from another FileBytes will cause the
entire file to be read before it is appended.

### truncate() method

Truncates the internal representation of the file to the number of bytes specified.
This discards any data or changes applied after the truncation. When calling `write_changes()`
the file will be resized accordingly to truncate it down.

### search() method

Takes a single bytes or FileBytes object and searches the current instance for those
bytes. Returns the index of the first found occurence of those bytes if they are present
or None of they are not. Note that much like `append()`, searching from another FileBytes
will cause the entire file to be read before it is used as the search term. Optionally
a start keyword argument can be supplied to specify an offset to start searching at.
Optionally an end keyword argument can be supplied to specify an offset to stop searching at.

### write_changes() method

Applies all append, truncate and update operations that were performed to the instance
of FileBytes. The file will be updated to match the contents of FileBytes and then the
FileBytes instance will be updated to reflect that new file. Once you call this method,
any clones of the instance you have written changes back from will invalidate themselves
so that you are not surprised by their contents changing out from under you.

## BinaryDiff

The BinaryDiff class provides a series of handy functions for manipulating binary data
based on a series of hex differences. It also provides functions for creating a series
of hex differences based on two identically-sized binaries. The format is designed to
be human-readable.

### BinaryDiff.diff

Given two identically-lengthed bytes arguments "bin1" and "bin2", returns a list of
patches that would need to be applied to "bin1" to convert it to "bin2". See the below
patch format for documentation as to what each list entry will look like. Note that in
addition to bytes, either "bin1", "bin2" or both can be provided instead an instance of
`FileBytes` to diff data that is not loaded into RAM.

### BinaryDiff.size

Given a list of patches as documented in the patch format section below, looks for a
"File Size" special comment and returns the value found. If no such section exists in
the list of patches it returns None.

### BinaryDiff.description

Given a list of patches as documented in the patch format section below, looks for a
"Description" special comment and returns the value found. If no such section exists in
the list of patches it returns None.

### BinaryDiff.needed_amount

Given a list of patches as documented in the patch format section below, examines the
list of patches and determines the minimum length of a binary that could be patched
by these patch bytes. Note that this ignores the "File Size" special comment and instead
focuses on the highest address of any byte changed by any single patch line.

### BinaryDiff.can_patch

Given a byte argument "binary" and a list of patches argument "patchlines", examines
the series of patches including the "File Size" comment and returns True if the binary
supplied could be patched by the patches supplied and False otherwise. Things that could
make a binary ineliglbe for patching include having the wrong file size, having not enough
bytes to patch or having incorrect bytes at a particular patch offset. If you pass in
the optional boolean keyword argument "reverse" set to True, this function will calculate
whether the reverse of the patch could instead be applied. If you pass in the optional
boolean keyword argument "ignore_size_differences" then the "File Size" comment will be
ignored. Note that in addition to bytes, the "binary" argument can be passed an instance
of `FileBytes` in order to check a file for patch applicability without loading it into
RAM.

### BinaryDiff.patch

Given a byte argument "binary" and a list of patches argument "patchlines", actually
perform the patches requested and return a new binary with the patches applied. If you
supply the optional boolean keyword argument "reverse" set to True, this function will
instead patch the reverse of each patch. A binary that was patched using `BinaryDiff.patch`
can be reverted back to the original format by calling `BinaryDiff.patch` again with
the "reverse" argument set to True. Note that the only restriction to this is if any of
the patches include wildcards then the resulting patched binary cannot be reversed.
If you pass in the optional boolean keyword argument "ignore_size_differences" then the
"File Size" comment will be ignored. Note that in addition to bytes, the "binary" argument
can be passed an instance of `FileBytes` in order to patch a file without loading it into
RAM. If you go this route, make sure to call `FileBytes.write_changes` after calling
`BinaryDiff.patch`.

### Patch Format

The patch format is simple. For each item in the patch list, the number on the left of
the colon is the hex offset where the difference was found, and the numbers on the right
are the hex values to find and replace. A wildcard (`*`) can be substituted for a hex
pair for any byte in the before section if you do not care what the value is, but be
aware that this will make the patch non-reversible. Arbitrary comments are supported
anywhere in the list of patches. If a list entry starts with the `#` character to it will
be seen as a comment. Special values are recognized in comments. If you create a comment
starting with `# File size:` then the the data length will be compared against the decimal
number placed after the colon and any file not matching that length will be rejected.
If you create a comment starting with `# Description` then all text after the colon will
be returned as the patch top level description.

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
