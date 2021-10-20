from arcadeutils import ByteUtil
import unittest


class TestBinaryDiff(unittest.TestCase):

    def test_byteswap(self) -> None:
        self.assertEqual(
            ByteUtil.byteswap(b"abcd1234"),
            b'badc2143',
        )

    def test_wordswap(self) -> None:
        self.assertEqual(
            ByteUtil.wordswap(b"abcd1234"),
            b'dcba4321',
        )

    def test_combine8bithalves(self) -> None:
        self.assertEqual(
            ByteUtil.combine8bithalves(b"1234", b"abcd"),
            b"1a2b3c4d",
        )

    def test_split8bithalves(self) -> None:
        self.assertEqual(
            ByteUtil.split8bithalves(b"1a2b3c4d"),
            (b"1234", b"abcd"),
        )

    def test_combine16bithalves(self) -> None:
        self.assertEqual(
            ByteUtil.combine16bithalves(b"1234", b"abcd"),
            b"12ab34cd",
        )

    def test_split16bithalves(self) -> None:
        self.assertEqual(
            ByteUtil.split16bithalves(b"1a2b3c4d"),
            (b"1a3c", b"2b4d"),
        )
