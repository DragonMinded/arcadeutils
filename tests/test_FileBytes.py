import io
import random
import unittest

from arcadeutils import FileBytes


class TestFileBytes(unittest.TestCase):

    def test_read_only_operations(self) -> None:
        b = b"0123456789"
        fb = FileBytes(io.BytesIO(b))

        # Length check.
        self.assertEqual(
            len(fb),
            len(b),
        )

        # Basic index lookup.
        self.assertEqual(
            fb[5],
            b[5],
        )

        # Make sure negative indexing works.
        self.assertEqual(
            fb[-2],
            b[-2],
        )

        # Indexing outside of the length as an individual lookup
        # should cause an IndexError.
        with self.assertRaises(IndexError):
            fb[10]

        # Basic start:end lookups.
        self.assertEqual(
            fb[3:7],
            b[3:7],
        )

        # Leave out the start or end.
        self.assertEqual(
            fb[3:],
            b[3:],
        )
        self.assertEqual(
            fb[:5],
            b[:5],
        )
        self.assertEqual(
            fb[-2:],
            b[-2:],
        )
        self.assertEqual(
            fb[:-8],
            b[:-8]
        )

        # Mixed positive and negative indexes.
        self.assertEqual(
            fb[3:-2],
            b[3:-2],
        )
        self.assertEqual(
            fb[-8:5],
            b[-8:5],
        )

        # Resulting in no data.
        self.assertEqual(
            fb[3:3],
            b[3:3],
        )
        self.assertEqual(
            fb[5:3],
            fb[5:3],
        )

        # Out of range.
        self.assertEqual(
            fb[5:15],
            b[5:15],
        )

        # Copy
        self.assertEqual(
            fb[:],
            b,
        )

        # Indexing with a zero step should raise a ValueError.
        with self.assertRaises(ValueError):
            fb[3:5:0]

        # Lookups with a step.
        self.assertEqual(
            fb[3:7:2],
            b[3:7:2],
        )
        self.assertEqual(
            fb[7:3:-2],
            b[7:3:-2],
        )

        # Reverse copy.
        self.assertEqual(
            fb[::-1],
            b[::-1],
        )

        # Provide default explicitly.
        self.assertEqual(
            fb[3:7:1],
            b[3:7:1],
        )

        # Negative single step.
        self.assertEqual(
            fb[7:3:-1],
            b[7:3:-1],
        )

        # Lookups that result in no data.
        self.assertEqual(
            fb[3:7:-1],
            b[3:7:-1],
        )
        self.assertEqual(
            fb[7:3:1],
            b[7:3:1],
        )

        # Make sure that a clone of this object doesn't get any file changes
        # and that it is identical.
        self.assertEqual(
            fb.clone()[:],
            b,
        )

        # Attempt to serialize out the data and make sure it did not change
        # before calling write.
        handle = fb.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b,
        )

        # Make sure that the data is identical after calling write as well.
        fb.write_changes()
        handle = fb.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b,
        )

    def test_read_after_modify(self) -> None:
        b = b"012a456bc9"
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Do some simple modifications.
        fb[3] = 97
        fb[7:9] = b"bc"

        # Length check.
        self.assertEqual(
            len(fb),
            len(b),
        )

        # Basic index lookup.
        self.assertEqual(
            fb[5],
            b[5],
        )

        # Make sure negative indexing works.
        self.assertEqual(
            fb[-2],
            b[-2],
        )

        # Indexing outside of the length as an individual lookup
        # should cause an IndexError.
        with self.assertRaises(IndexError):
            fb[10]

        # Basic start:end lookups.
        self.assertEqual(
            fb[3:7],
            b[3:7],
        )

        # Leave out the start or end.
        self.assertEqual(
            fb[3:],
            b[3:],
        )
        self.assertEqual(
            fb[:5],
            b[:5],
        )
        self.assertEqual(
            fb[-2:],
            b[-2:],
        )
        self.assertEqual(
            fb[:-8],
            b[:-8]
        )

        # Mixed positive and negative indexes.
        self.assertEqual(
            fb[3:-2],
            b[3:-2],
        )
        self.assertEqual(
            fb[-8:5],
            b[-8:5],
        )

        # Resulting in no data.
        self.assertEqual(
            fb[3:3],
            b[3:3],
        )
        self.assertEqual(
            fb[5:3],
            fb[5:3],
        )

        # Out of range.
        self.assertEqual(
            fb[5:15],
            b[5:15],
        )

        # Copy
        self.assertEqual(
            fb[:],
            b,
        )

        # Indexing with a zero step should raise a ValueError.
        with self.assertRaises(ValueError):
            fb[3:5:0]

        # Lookups with a step.
        self.assertEqual(
            fb[3:7:2],
            b[3:7:2],
        )
        self.assertEqual(
            fb[7:3:-2],
            b[7:3:-2],
        )

        # Reverse copy.
        self.assertEqual(
            fb[::-1],
            b[::-1],
        )

        # Provide default explicitly.
        self.assertEqual(
            fb[3:7:1],
            b[3:7:1],
        )

        # Negative single step.
        self.assertEqual(
            fb[7:3:-1],
            b[7:3:-1],
        )

        # Lookups that result in no data.
        self.assertEqual(
            fb[3:7:-1],
            b[3:7:-1],
        )
        self.assertEqual(
            fb[7:3:1],
            b[7:3:1],
        )

        # Verify that it gets serialized correctly.
        fb.write_changes()
        handle = fb.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b,
        )

    def test_modify_variants(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        fb[3] = 97
        self.assertEqual(
            fb[:],
            b"012a456789",
        )

        fb[7:9] = b"bc"
        self.assertEqual(
            fb[:],
            b"012a456bc9",
        )

        fb[4:8:2] = b"de"
        self.assertEqual(
            fb[:],
            b"012ad5ebc9",
        )
        fb[-1] = 102
        self.assertEqual(
            fb[:],
            b"012ad5ebcf",
        )

        # Verify that it gets serialized correctly.
        fb.write_changes()
        handle = fb.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"012ad5ebcf",
        )

        fb[7:3:-2] = b"gh"
        self.assertEqual(
            fb[:],
            b"012adhegcf",
        )

        # Verify that it gets serialized correctly.
        fb.write_changes()
        handle = fb.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"012adhegcf",
        )

    def test_resize_fail(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        with self.assertRaises(NotImplementedError):
            fb[3:4] = b"long"
        with self.assertRaises(NotImplementedError):
            fb[3:7] = b""

    def test_append_modify(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Clone this so we can verify that clones don't receive additional modifications.
        clone = fb.clone()
        clone.append(b"abc")

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            13,
        )

        # Verify additional appends work.
        clone.append(b"def")

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            16,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456789abcdef",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"0123456789abcdef",
        )

    def test_modify_writeback_clones_unsafe(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        clone = fb.clone()
        clone.append(b"abcdef")

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456789abcdef",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"0123456789abcdef",
        )

        # Verify that accessing the clone data works.
        self.assertEqual(
            clone[:],
            b"0123456789abcdef",
        )
        clone[0:1] = b"z"
        self.assertEqual(
            clone[:],
            b"z123456789abcdef",
        )

        # Verify that attempting to read or modify the original raises
        # an error since we wrote the clone back to the original file.
        with self.assertRaisesRegex(Exception, "Another FileBytes instance representing the same file was written back!"):
            fb[:]
        with self.assertRaisesRegex(Exception, "Another FileBytes instance representing the same file was written back!"):
            fb[5] = 2

        # Verify that making a new clone works properly.
        newclone = fb.clone()
        self.assertEqual(
            newclone[:],
            b"0123456789abcdef",
        )

    def test_add(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Create a copy by adding to the original.
        clone = fb + b"abc"

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            13,
        )

        # Verify additional appends work including from FileBytes.
        clone = clone + FileBytes(io.BytesIO(b"def"))

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            16,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456789abcdef",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"0123456789abcdef",
        )

    def test_truncate_noop(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Create a copy by adding to the original.
        clone = fb.clone()
        clone.truncate(15)

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            10,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456789",
        )

    def test_truncate_simple(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Create a copy by adding to the original.
        clone = fb.clone()
        clone.truncate(5)

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            5,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"01234",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"01234",
        )

        # Verify everything is good after writeback.
        self.assertEqual(
            len(clone),
            5,
        )
        self.assertEqual(
            clone[:],
            b"01234",
        )

    def test_truncate_only_patches(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Create a copy by adding to the original.
        clone = fb.clone()
        clone.append(b"abcdef")
        clone.truncate(13)

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            13,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456789abc",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"0123456789abc",
        )

        # Verify that everything looks good still.
        self.assertEqual(
            len(clone),
            13,
        )
        self.assertEqual(
            clone[:],
            b"0123456789abc",
        )

    def test_truncate_overlap(self) -> None:
        fb = FileBytes(io.BytesIO(b"0123456789"))

        # Length check.
        self.assertEqual(
            len(fb),
            10,
        )

        # Create a copy by adding to the original.
        clone = fb.clone()
        clone.append(b"abcdef")
        clone.truncate(7)

        # New length check.
        self.assertEqual(
            len(fb),
            10,
        )
        self.assertEqual(
            len(clone),
            7,
        )

        # Verify modification stuck.
        self.assertEqual(
            fb[:],
            b"0123456789",
        )
        self.assertEqual(
            clone[:],
            b"0123456",
        )

        # Verify that it gets serialized correctly.
        clone.write_changes()
        handle = clone.handle
        if not isinstance(handle, io.BytesIO):
            raise Exception("File handle changed type somehow!")
        self.assertEqual(
            handle.getvalue(),
            b"0123456",
        )

        # Verify that everything looks good still.
        self.assertEqual(
            len(clone),
            7,
        )
        self.assertEqual(
            clone[:],
            b"0123456",
        )

    def test_search_basic(self) -> None:
        fb = FileBytes(io.BytesIO((b"\0" * 54321) + (b"0123456789") + (b"\0" * 54321)))
        self.assertEqual(
            fb.search(b"0123456789"),
            54321,
        )
        self.assertEqual(
            fb.search(b"4567"),
            54325,
        )
        self.assertEqual(
            fb.search(b"abcde"),
            None,
        )

    def test_search_bounds(self) -> None:
        fb = FileBytes(io.BytesIO((b"\0" * 5) + (b"0123456789") + (b"\0" * 5)))
        self.assertEqual(
            fb.search(b"0123456789", start=5),
            5,
        )
        self.assertEqual(
            fb.search(b"0123456789", start=6),
            None,
        )
        self.assertEqual(
            fb.search(b"0123456789", end=15),
            5,
        )
        self.assertEqual(
            fb.search(b"0123456789", end=14),
            None,
        )
        self.assertEqual(
            fb.search(b"0123456789", start=3, end=18),
            5,
        )
        self.assertEqual(
            fb.search(b"0123456789", start=5, end=15),
            5,
        )

    def test_search_edges(self) -> None:
        fb = FileBytes(io.BytesIO((b"\0" * 5) + (b"0123456789")))
        self.assertEqual(
            fb.search(b"0123456789"),
            5,
        )

        fb = FileBytes(io.BytesIO(b"0123456789"))
        self.assertEqual(
            fb.search(b"0123456789"),
            0,
        )

        fb = FileBytes(io.BytesIO(b"0123456789" + (b"\0" * 5)))
        self.assertEqual(
            fb.search(b"0123456789"),
            0,
        )

    def test_search_random(self) -> None:
        for _ in range(25):
            location = random.randint(1, 2000)
            fb = FileBytes(io.BytesIO((b"\0" * location) + (b"12345") + (b"\0" * random.randint(1, 2000))))
            self.assertEqual(
                fb.search(b"12345"),
                location,
            )
