from typing import List, Optional, Tuple, Union, cast, overload
from typing_extensions import Final

from .filebytes import FileBytes


class BinaryDiffException(Exception):
    pass


class BinaryDiff:

    CHUNK_SIZE: Final[int] = 1024

    @staticmethod
    def _hex(val: int) -> str:
        out = hex(val)[2:]
        out = out.upper()
        if len(out) == 1:
            out = "0" + out
        return out

    @staticmethod
    def diff(bin1: Union[bytes, FileBytes], bin2: Union[bytes, FileBytes]) -> List[str]:
        binlength = len(bin1)
        if binlength != len(bin2):
            raise BinaryDiffException("Cannot diff different-sized binary blobs!")

        # First, get the list of differences
        differences: List[Tuple[int, bytes, bytes]] = []

        # Chunk the differences, assuming files are usually about the same,
        # for a massive speed boost.
        for offset in range(0, binlength, BinaryDiff.CHUNK_SIZE):
            length = min(BinaryDiff.CHUNK_SIZE, binlength - offset)
            if bin1[offset:(offset + length)] != bin2[offset:(offset + length)]:
                for i in range(length):
                    byte1 = bin1[offset + i]
                    byte2 = bin2[offset + i]

                    if byte1 != byte2:
                        differences.append((offset + i, bytes([byte1]), bytes([byte2])))

        # Don't bother with any combination crap if we have nothing to do
        if not differences:
            return []

        # Now, combine them for easier printing
        cur_block: Tuple[int, bytes, bytes] = differences[0]
        ret: List[str] = []

        # Now, include the original byte size for later comparison/checks
        ret.append(f"# File size: {len(bin1)}")

        def _hexrun(val: bytes) -> str:
            return " ".join(BinaryDiff._hex(v) for v in val)

        def _output(val: Tuple[int, bytes, bytes]) -> None:
            start = val[0] - len(val[1]) + 1

            ret.append(
                f"{BinaryDiff._hex(start)}: {_hexrun(val[1])} -> {_hexrun(val[2])}"
            )

        def _combine(val: Tuple[int, bytes, bytes]) -> None:
            nonlocal cur_block

            if cur_block[0] + 1 == val[0]:
                # This is a continuation of a run
                cur_block = (
                    val[0],
                    cur_block[1] + val[1],
                    cur_block[2] + val[2],
                )
            else:
                # This is a new run
                _output(cur_block)
                cur_block = val

        # Combine and output runs of differences
        for diff in differences[1:]:
            _combine(diff)

        # Make sure we output the last difference
        _output(cur_block)

        # Return our summation
        return ret

    @staticmethod
    def size(patchlines: List[str]) -> Optional[int]:
        for patch in patchlines:
            if patch.startswith('#'):
                # This is a comment, ignore it, unless its a file-size comment
                patch = patch[1:].strip().lower()
                if patch.startswith('file size:'):
                    try:
                        return int(patch[10:].strip())
                    except ValueError:
                        return None
        return None

    @staticmethod
    def _convert(val: str) -> Optional[int]:
        val = val.strip()
        if val == '*':
            return None
        return int(val, 16)

    @staticmethod
    def _gather_differences(patchlines: List[str], reverse: bool) -> List[Tuple[int, Optional[bytes], bytes]]:
        # First, separate out into a list of offsets and old/new bytes
        differences: List[Tuple[int, Optional[bytes], bytes]] = []

        for patch in patchlines:
            if patch.startswith('#'):
                # This is a comment, ignore it.
                continue
            start_offset, patch_contents = patch.split(':', 1)
            before, after = patch_contents.split('->')
            beforevals = [
                BinaryDiff._convert(x) for x in before.split(" ") if x.strip()
            ]
            aftervals = [
                BinaryDiff._convert(x) for x in after.split(" ") if x.strip()
            ]

            if len(beforevals) != len(aftervals):
                raise BinaryDiffException(
                    f"Patch before and after length mismatch at "
                    f"offset {start_offset}!"
                )
            if len(beforevals) == 0:
                raise BinaryDiffException(
                    f"Must have at least one byte to change at "
                    f"offset {start_offset}!"
                )

            offset = int(start_offset.strip(), 16)

            for i in range(len(beforevals)):
                if aftervals[i] is None:
                    raise BinaryDiffException(
                        f"Cannot convert a location to a wildcard "
                        f"at offset {start_offset}"
                    )
                if beforevals[i] is None and reverse:
                    raise BinaryDiffException(
                        f"Patch offset {start_offset} specifies a wildcard and cannot "
                        f"be reversed!"
                    )
                differences.append(
                    (
                        offset + i,
                        bytes([beforevals[i] or 0]) if beforevals[i] is not None else None,
                        bytes([aftervals[i] or 0]),
                    )
                )

        # Now, if we're doing the reverse, just switch them
        if reverse:
            # We cast here because mypy can't see that we have already asserted that x[2] will never
            # be optional in the above loop if reverse is set to True.
            differences = [cast(Tuple[int, Optional[bytes], bytes], (x[0], x[2], x[1])) for x in differences]

        # Finally, return it
        return differences

    @overload
    @staticmethod
    def patch(
        binary: bytes,
        patchlines: List[str],
        *,
        reverse: bool = False,
        ignore_size_differences: bool = False,
    ) -> bytes:
        ...

    @overload
    @staticmethod
    def patch(
        binary: FileBytes,
        patchlines: List[str],
        *,
        reverse: bool = False,
        ignore_size_differences: bool = False,
    ) -> FileBytes:
        ...

    @staticmethod
    def patch(
        binary: Union[bytes, FileBytes],
        patchlines: List[str],
        *,
        reverse: bool = False,
        ignore_size_differences: bool = False,
    ) -> Union[bytes, FileBytes]:
        # If we were given filebytes, get a clone of it so we don't modify the input.
        if isinstance(binary, FileBytes):
            binary = binary.clone()

        # First, grab the differences
        if not ignore_size_differences:
            file_size = BinaryDiff.size(patchlines)
            if file_size is not None and file_size != len(binary):
                raise BinaryDiffException(
                    f"Patch is for binary of size {file_size} but binary is {len(binary)} "
                    f"bytes long!"
                )

        differences: List[Tuple[int, Optional[bytes], bytes]] = sorted(
            BinaryDiff._gather_differences(patchlines, reverse),
            key=lambda diff: diff[0],
        )
        chunks: List[bytes] = []
        last_patch_end: int = 0

        # Now, apply the changes to the binary data
        for diff in differences:
            offset, old, new = diff

            if len(binary) < offset:
                raise BinaryDiffException(
                    f"Patch offset {BinaryDiff._hex(offset)} is beyond the end of "
                    f"the binary!"
                )
            if old is not None and binary[offset:(offset + 1)] != old:
                raise BinaryDiffException(
                    f"Patch offset {BinaryDiff._hex(offset)} expecting {BinaryDiff._hex(old[0])} "
                    f"but found {BinaryDiff._hex(binary[offset])}!"
                )

            if isinstance(binary, bytes):
                if last_patch_end < offset:
                    chunks.append(binary[last_patch_end:offset])
                chunks.append(new)
                last_patch_end = offset + 1
            elif isinstance(binary, FileBytes):
                binary[offset:(offset + len(new))] = new
            else:
                # This should never happen?
                raise NotImplementedError("Not implemented!")

        if isinstance(binary, bytes):
            # Return the new data!
            chunks.append(binary[last_patch_end:])
            return b"".join(chunks)
        elif isinstance(binary, FileBytes):
            # We modified the filebytes object in place.
            return binary
        else:
            # This should never happen?
            raise NotImplementedError("Not implemented!")

    @staticmethod
    def can_patch(
        binary: Union[bytes, FileBytes],
        patchlines: List[str],
        *,
        reverse: bool = False,
        ignore_size_differences: bool = False,
    ) -> Tuple[bool, str]:
        # First, grab the differences
        if not ignore_size_differences:
            file_size = BinaryDiff.size(patchlines)
            if file_size is not None and file_size != len(binary):
                return (
                    False,
                    f"Patch is for binary of size {file_size} but binary is {len(binary)} "
                    f"bytes long!"
                )

        try:
            differences: List[Tuple[int, Optional[bytes], bytes]] = BinaryDiff._gather_differences(patchlines, reverse)
        except BinaryDiffException as e:
            return (False, str(e))

        # Now, verify the changes to the binary data
        for diff in differences:
            offset, old, _ = diff

            if len(binary) < offset:
                return (
                    False,
                    f"Patch offset {BinaryDiff._hex(offset)} is beyond the end of "
                    f"the binary!"
                )
            if old is not None and binary[offset:(offset + 1)] != old:
                return (
                    False,
                    f"Patch offset {BinaryDiff._hex(offset)} expecting {BinaryDiff._hex(old[0])} "
                    f"but found {BinaryDiff._hex(binary[offset])}!"
                )

        # Didn't find any problems
        return (True, "")

    @staticmethod
    def description(patchlines: List[str]) -> Optional[str]:
        for patch in patchlines:
            if patch.startswith('#'):
                # This is a comment, ignore it, unless its a description comment
                patch = patch[1:].strip().lower()
                if patch.startswith('description:'):
                    return patch[12:].strip()
        return None

    @staticmethod
    def needed_amount(patchlines: List[str]) -> int:
        # First, grab the differences.
        differences: List[Tuple[int, Optional[bytes], bytes]] = BinaryDiff._gather_differences(patchlines, False)

        # Now, get the maximum byte we need to apply this patch.
        return max([offset for offset, _, _ in differences]) + 1 if differences else 0


class ByteUtil:

    @staticmethod
    def byteswap(data: bytes) -> bytes:
        even = [d for d in data[::2]]
        odd = [d for d in data[1::2]]
        chunks = [bytes([odd[i], even[i]]) for i in range(len(even))]
        return b''.join(chunks)

    @staticmethod
    def wordswap(data: bytes) -> bytes:
        one = [d for d in data[::4]]
        two = [d for d in data[1::4]]
        three = [d for d in data[2::4]]
        four = [d for d in data[3::4]]
        chunks = [
            bytes([four[i], three[i], two[i], one[i]])
            for i in range(len(one))
        ]
        return b''.join(chunks)

    @staticmethod
    def combine16bithalves(upper: bytes, lower: bytes) -> bytes:
        chunks = [
            b''.join([upper[i:(i + 2)], lower[i:(i + 2)]])
            for i in range(0, len(upper), 2)
        ]
        return b''.join(chunks)

    @staticmethod
    def split16bithalves(data: bytes) -> Tuple[bytes, bytes]:
        length = len(data)
        return(
            b''.join(data[x:(x + 2)] for x in range(0, length, 4)),
            b''.join(data[(x + 2):(x + 4)] for x in range(0, length, 4)),
        )

    @staticmethod
    def combine8bithalves(upper: bytes, lower: bytes) -> bytes:
        chunks = [bytes([upper[i], lower[i]]) for i in range(len(upper))]
        return b''.join(chunks)

    @staticmethod
    def split8bithalves(data: bytes) -> Tuple[bytes, bytes]:
        return (
            bytes([d for d in data[::2]]),
            bytes([d for d in data[1::2]]),
        )
