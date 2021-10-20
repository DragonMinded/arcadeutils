import io
import unittest

from arcadeutils import BinaryDiff, BinaryDiffException, FileBytes


class TestBinaryDiffBytes(unittest.TestCase):

    def test_diff_no_differences(self) -> None:
        self.assertEqual(
            BinaryDiff.diff(b"abcd", b"abcd"),
            [],
        )
        self.assertEqual(
            BinaryDiff.diff(b"", b""),
            [],
        )

    def test_diff_different_sizes(self) -> None:
        with self.assertRaises(BinaryDiffException):
            BinaryDiff.diff(b"1234", b"123")
        with self.assertRaises(BinaryDiffException):
            BinaryDiff.diff(b"123", b"1234")

    def test_diff_simple(self) -> None:
        self.assertEqual(
            BinaryDiff.diff(b"abcd1234", b"bbcd1234"),
            [
                '# File size: 8',
                '00: 61 -> 62',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(b"abcd1234", b"abcd1235"),
            [
                '# File size: 8',
                '07: 34 -> 35',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(b"abcd1234", b"abdc1224"),
            [
                '# File size: 8',
                '02: 63 64 -> 64 63',
                '06: 33 -> 32',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(b"abcd1234", b"4321bcda"),
            [
                '# File size: 8',
                '00: 61 62 63 64 31 32 33 34 -> 34 33 32 31 62 63 64 61',
            ]
        )

    def test_size(self) -> None:
        self.assertEqual(
            BinaryDiff.size([]),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['# Comment']),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['00: 01 -> 02']),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['# File Size: 1024']),
            1024,
        )
        self.assertEqual(
            BinaryDiff.size(['# File Size: invalid']),
            None,
        )

    def test_description(self) -> None:
        self.assertEqual(
            BinaryDiff.description([]),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['# Comment']),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['00: 01 -> 02']),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['# Description: sample text']),
            "sample text",
        )

    def test_needed_amount(self) -> None:
        self.assertEqual(
            BinaryDiff.needed_amount([]),
            0,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '00: 61 -> 62',
                ]
            ),
            1,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '07: 34 -> 35',
                ]
            ),
            8,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ]
            ),
            7,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '00: 61 62 63 64 31 32 33 34 -> 34 33 32 31 62 63 64 61',
                ]
            ),
            8,
        )

    def test_can_patch_normal(self) -> None:
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd1234",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch is for binary of size 12 but binary is 8 bytes long!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd1234",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                ignore_size_differences=True,
            ),
            (True, '')
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd",
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch offset 06 is beyond the end of the binary!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"4321bcda",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch offset 02 expecting 63 but found 32!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
            ),
            (True, ''),
        )

    def test_can_patch_reverse(self) -> None:
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abdc1224",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abdc1224",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch is for binary of size 12 but binary is 8 bytes long!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abdc1224",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
                ignore_size_differences=True,
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abdc",
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 06 is beyond the end of the binary!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"4321bcda",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 02 expecting 64 but found 32!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 06 specifies a wildcard and cannot be reversed!'),
        )

    def test_patch_normal(self) -> None:
        self.assertEqual(
            BinaryDiff.patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            b'abdc1224',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"abcd1234",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch is for binary of size 12 but binary is 8 bytes long!')
        self.assertEqual(
            BinaryDiff.patch(
                b"abcd1234",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                ignore_size_differences=True,
            ),
            b'abdc1224',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"abcd",
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 is beyond the end of the binary!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"4321bcda",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch offset 02 expecting 63 but found 32!')
        self.assertEqual(
            BinaryDiff.patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
            ),
            b'abcd1224',
        )

    def test_patch_reverse(self) -> None:
        self.assertEqual(
            BinaryDiff.patch(
                b"abdc1224",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            b'abcd1234',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"abdc1224",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch is for binary of size 12 but binary is 8 bytes long!')
        self.assertEqual(
            BinaryDiff.patch(
                b"abdc1224",
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
                ignore_size_differences=True,
            ),
            b'abcd1234',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"abdc",
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 is beyond the end of the binary!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"4321bcda",
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 02 expecting 64 but found 32!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                b"abcd1234",
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 specifies a wildcard and cannot be reversed!')


class TestBinaryDiffFileBytes(unittest.TestCase):

    def __make_filebytes(self, data: bytes) -> FileBytes:
        return FileBytes(io.BytesIO(data))

    def __make_bytes(self, filebytes: FileBytes) -> bytes:
        return filebytes[:]

    def test_diff_no_differences(self) -> None:
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b"abcd"), self.__make_filebytes(b"abcd")),
            [],
        )
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b""), self.__make_filebytes(b"")),
            [],
        )

    def test_diff_different_sizes(self) -> None:
        with self.assertRaises(BinaryDiffException):
            BinaryDiff.diff(self.__make_filebytes(b"1234"), self.__make_filebytes(b"123"))
        with self.assertRaises(BinaryDiffException):
            BinaryDiff.diff(self.__make_filebytes(b"123"), self.__make_filebytes(b"1234"))

    def test_diff_simple(self) -> None:
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b"abcd1234"), self.__make_filebytes(b"bbcd1234")),
            [
                '# File size: 8',
                '00: 61 -> 62',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b"abcd1234"), self.__make_filebytes(b"abcd1235")),
            [
                '# File size: 8',
                '07: 34 -> 35',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b"abcd1234"), self.__make_filebytes(b"abdc1224")),
            [
                '# File size: 8',
                '02: 63 64 -> 64 63',
                '06: 33 -> 32',
            ]
        )
        self.assertEqual(
            BinaryDiff.diff(self.__make_filebytes(b"abcd1234"), self.__make_filebytes(b"4321bcda")),
            [
                '# File size: 8',
                '00: 61 62 63 64 31 32 33 34 -> 34 33 32 31 62 63 64 61',
            ]
        )

    def test_size(self) -> None:
        self.assertEqual(
            BinaryDiff.size([]),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['# Comment']),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['00: 01 -> 02']),
            None,
        )
        self.assertEqual(
            BinaryDiff.size(['# File Size: 1024']),
            1024,
        )
        self.assertEqual(
            BinaryDiff.size(['# File Size: invalid']),
            None,
        )

    def test_description(self) -> None:
        self.assertEqual(
            BinaryDiff.description([]),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['# Comment']),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['00: 01 -> 02']),
            None,
        )
        self.assertEqual(
            BinaryDiff.description(['# Description: sample text']),
            "sample text",
        )

    def test_needed_amount(self) -> None:
        self.assertEqual(
            BinaryDiff.needed_amount([]),
            0,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '00: 61 -> 62',
                ]
            ),
            1,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '07: 34 -> 35',
                ]
            ),
            8,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ]
            ),
            7,
        )
        self.assertEqual(
            BinaryDiff.needed_amount(
                [
                    '# File size: 8',
                    '00: 61 62 63 64 31 32 33 34 -> 34 33 32 31 62 63 64 61',
                ]
            ),
            8,
        )

    def test_can_patch_normal(self) -> None:
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch is for binary of size 12 but binary is 8 bytes long!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                ignore_size_differences=True,
            ),
            (True, '')
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd"),
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch offset 06 is beyond the end of the binary!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"4321bcda"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            ),
            (False, 'Patch offset 02 expecting 63 but found 32!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
            ),
            (True, ''),
        )

    def test_can_patch_reverse(self) -> None:
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch is for binary of size 12 but binary is 8 bytes long!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
                ignore_size_differences=True,
            ),
            (True, ''),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abdc"),
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 06 is beyond the end of the binary!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"4321bcda"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 02 expecting 64 but found 32!'),
        )
        self.assertEqual(
            BinaryDiff.can_patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
                reverse=True,
            ),
            (False, 'Patch offset 06 specifies a wildcard and cannot be reversed!'),
        )

    def test_patch_normal(self) -> None:
        self.assertEqual(
            self.__make_bytes(BinaryDiff.patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )),
            b'abdc1224',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch is for binary of size 12 but binary is 8 bytes long!')
        self.assertEqual(
            self.__make_bytes(BinaryDiff.patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                ignore_size_differences=True,
            )),
            b'abdc1224',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"abcd"),
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 is beyond the end of the binary!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"4321bcda"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
            )
        self.assertEqual(str(context.exception), 'Patch offset 02 expecting 63 but found 32!')
        self.assertEqual(
            self.__make_bytes(BinaryDiff.patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
            )),
            b'abcd1224',
        )

    def test_patch_reverse(self) -> None:
        self.assertEqual(
            self.__make_bytes(BinaryDiff.patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )),
            b'abcd1234',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch is for binary of size 12 but binary is 8 bytes long!')
        self.assertEqual(
            self.__make_bytes(BinaryDiff.patch(
                self.__make_filebytes(b"abdc1224"),
                [
                    '# File size: 12',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
                ignore_size_differences=True,
            )),
            b'abcd1234',
        )
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"abdc"),
                [
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 is beyond the end of the binary!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"4321bcda"),
                [
                    '# File size: 8',
                    '02: 63 64 -> 64 63',
                    '06: 33 -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 02 expecting 64 but found 32!')
        with self.assertRaises(BinaryDiffException) as context:
            BinaryDiff.patch(
                self.__make_filebytes(b"abcd1234"),
                [
                    '# File size: 8',
                    '06: * -> 32',
                ],
                reverse=True,
            )
        self.assertEqual(str(context.exception), 'Patch offset 06 specifies a wildcard and cannot be reversed!')
