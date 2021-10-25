import shutil
from typing import BinaryIO, Dict, List, Optional, Set, Tuple, Union, overload
from typing_extensions import Final


class FileBytes:

    IO_SIZE: Final[int] = 0x8000

    def __init__(self, handle: BinaryIO) -> None:
        self.__handle: BinaryIO = handle
        self.__patches: Dict[int, int] = {}
        self.__regions: Set[int] = set()
        self.__copies: List["FileBytes"] = []
        self.__unsafe: bool = False
        self.__lowest_patch: Optional[int] = None
        self.__highest_patch: Optional[int] = None

        handle.seek(0, 2)
        self.__filelength: int = handle.tell()
        self.__origfilelength: int = self.__filelength
        self.__patchlength: int = self.__filelength

    @property
    def handle(self) -> BinaryIO:
        return self.__handle

    def search(self, search: Union[bytes, "FileBytes"], *, start: Optional[int] = None, end: Optional[int] = None) -> Optional[int]:
        # Search the file for search bytes in a faster manner than reloading the
        # file byte for byte for every position to search.

        searchlen = len(search)
        if searchlen > self.__patchlength:
            # There's no way that the search bytes could be in this file.
            return None
        if isinstance(search, FileBytes):
            search = search[:]

        if start is None:
            searchstart = 0
        else:
            searchstart = start
        if searchstart < 0 or searchstart > (self.__patchlength - (searchlen - 1)):
            # Never going to find it anyway.
            return None

        if end is None:
            searchend = self.__patchlength
        else:
            searchend = end
        searchend -= (searchlen - 1)
        if searchend <= searchstart:
            # Never going to find it anyway.
            return None

        chunksize = max(searchlen * 2, self.IO_SIZE)
        startoffset = searchstart
        data: bytes = self[searchstart:(searchstart + (chunksize * 3))]
        endoffset = searchstart + len(data)

        def addchunk() -> bool:
            nonlocal chunksize
            nonlocal startoffset
            nonlocal endoffset
            nonlocal data

            # Load the next chunk of data, including changes.
            newdata = self[endoffset:(endoffset + chunksize)]
            if not newdata:
                return False

            # Stick the data on the end of the cache.
            data = data + newdata

            # Update the end offset pointer so we know were to load from next time.
            endoffset += len(newdata)

            # If we got too long, then truncate ourselves so we don't blow up
            # our memory searching the file.
            if len(data) >= (3 * chunksize):
                data = data[chunksize:]
                startoffset += chunksize

            return True

        for offset in range(searchstart, searchend):
            start = offset
            end = offset + searchlen

            if end > endoffset:
                if not addchunk():
                    # No more chunks left to search, and we hit the end of the
                    # current chunk, so we have no more data to find.
                    return None

            actualstart = start - startoffset
            actualend = end - startoffset

            # If this chunk looks like a match, then return the start index.
            if data[actualstart:actualend] == search:
                return start

        # Could not find the data.
        return None

    def __len__(self) -> int:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")
        return self.__patchlength

    def __add__(self, other: object) -> "FileBytes":
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")
        if isinstance(other, FileBytes):
            clone = self.clone()
            clone.append(other[:])
        elif isinstance(other, bytes):
            clone = self.clone()
            clone.append(other)
        else:
            raise NotImplementedError("Not implemented!")
        return clone

    def clone(self) -> "FileBytes":
        # Make a safe copy so that in-memory patches can be changed.
        myclone = FileBytes(self.__handle)
        myclone.__patches = {k: v for k, v in self.__patches.items()}
        myclone.__lowest_patch = self.__lowest_patch
        myclone.__highest_patch = self.__highest_patch
        myclone.__regions = self.__regions
        myclone.__filelength = self.__filelength
        myclone.__patchlength = self.__patchlength
        myclone.__origfilelength = self.__origfilelength

        # Make sure we can invalidate copies if we write back the data.
        myclone.__copies.append(self)
        self.__copies.append(myclone)

        return myclone

    def append(self, data: Union[bytes, "FileBytes"]) -> None:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")

        # Add data to the end of our representation.
        data = data[:]
        lowest_loc = self.__patchlength
        highest_loc = self.__patchlength + len(data)

        for off, change in enumerate(data):
            self.__patches[self.__patchlength + off] = change

        self.__lowest_patch = min(self.__lowest_patch, lowest_loc) if self.__lowest_patch is not None else lowest_loc
        self.__highest_patch = max(self.__highest_patch, highest_loc + 1) if self.__highest_patch is not None else (highest_loc + 1)
        self.__regions.clear()
        self.__patchlength = highest_loc

    def truncate(self, size: int) -> None:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")

        # Truncate the resulting data
        if size < 0:
            raise NotImplementedError("Not implemented!")
        if size >= self.__patchlength:
            # We are already this short?
            return

        # Set the file length to this size so we don't read anything past it.
        if size < self.__filelength:
            self.__filelength = size

        # Get rid of any changes made in the truncation range.
        cleared: bool = False
        for off in range(size, self.__patchlength):
            if off in self.__patches:
                del self.__patches[off]
                cleared = True
        if cleared:
            self.__regions.clear()

        # Set the length of this object to the size as well so resizing will
        # zero out the data.
        self.__patchlength = size

    def __gather(self, already: Set["FileBytes"], need: "FileBytes") -> None:
        for inst in need.__copies:
            if inst not in already:
                already.add(inst)
                self.__gather(already, inst)

    def __write_changes(self, handle: BinaryIO) -> None:
        locations = sorted(self.__patches.keys())
        keys: Set[int] = set(locations)
        handled: Set[int] = set()
        for location in locations:
            if location in handled:
                # Already wrote this in a chunk.
                continue

            # Figure out the maximum range for this chunk.
            start = location
            end = location + 1
            while end in keys:
                end += 1

            # Sum it up
            data = bytes(self.__patches[loc] for loc in range(start, end))

            # Write it
            handle.seek(start)
            handle.write(data)

            # Mark it complete
            handled.update(range(start, end))

        if keys != handled:
            raise Exception("Logic error, failed to write some data!")

    def write_changes(self, new_file: Optional[BinaryIO] = None) -> None:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")

        if new_file is not None:
            # We want to serialize this out to a new file altogether.
            self.__handle.seek(0)
            new_file.seek(0)
            shutil.copyfileobj(self.__handle, new_file)

            # Now, truncate the new file to the right length.
            if self.__filelength < self.__origfilelength:
                new_file.truncate(self.__filelength)

            # Now, gather up any changes to the file and write them back.
            self.__write_changes(new_file)
            new_file.flush()
        else:
            # First off, see if we need to truncate the file.
            if self.__filelength < self.__origfilelength:
                self.__handle.truncate(self.__filelength)
                self.__origfilelength = self.__filelength
            if self.__filelength > self.__origfilelength:
                raise Exception("Logic error, somehow resized file bigger than it started?")

            # Now, gather up any changes to the file and write them back.
            self.__write_changes(self.__handle)

            # Now that we've serialized out the data, clean up our own representation.
            self.__handle.flush()
            self.__patches.clear()
            self.__regions.clear()
            self.__lowest_patch = None
            self.__highest_patch = None
            self.__filelength = self.__patchlength

            # Finally, find all other clones of this class and notify them that they're
            # unsafe, so that there isn't any surprise behavior if somebody clones a
            # FileBytes and then writes back to the underlying file on that clone. This
            # is because the only thing we have in memory is the patches we've made, so
            # if the underlying file is changed suddenly its all wrong.
            notify: Set[FileBytes] = {self}
            self.__gather(notify, self)
            for inst in notify:
                if inst is self:
                    continue

                # Mark this clone as unsafe for read/write operations.
                inst.__unsafe = True

                # Set up the clone so that if it is cloned itself, the clone will
                # work since it can read directly from the updated file.
                inst.__filelength = self.__filelength
                inst.__patchlength = self.__patchlength
                inst.__origfilelength = self.__origfilelength
                inst.__patches.clear()
                inst.__regions.clear()
                inst.__lowest_patch = None
                inst.__highest_patch = None

    def __slice(self, key: slice) -> Tuple[int, int, int]:
        # Determine step of slice
        if key.step is None:
            step = 1
        else:
            step = key.step

        # Determine start of slice
        if key.start is None:
            start = 0 if step > 0 else (self.__patchlength - 1)
        elif key.start < 0:
            start = self.__patchlength + key.start
        else:
            start = key.start

        # Determine end of slice
        if key.stop is None:
            stop = self.__patchlength if step > 0 else -1
        elif key.stop < 0:
            stop = self.__patchlength + key.stop
        else:
            stop = key.stop

        if start < 0:
            raise Exception("Logic error!")
        if start >= self.__patchlength:
            start = self.__patchlength
        if stop >= self.__patchlength:
            stop = self.__patchlength

        return (start, stop, step)

    @overload
    def __getitem__(self, key: int) -> int:
        ...

    @overload
    def __getitem__(self, key: slice) -> bytes:
        ...

    def __getitem__(self, key: Union[int, slice]) -> Union[int, bytes]:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")

        if isinstance(key, int):
            # Support negative indexing.
            if key < 0:
                key = self.__patchlength + key

            if key >= self.__patchlength:
                raise IndexError("FileBytes index out of range")

            # Look up in our modifications, and then fall back to the file.
            if key in self.__patches:
                return self.__patches[key]
            else:
                if key >= self.__filelength:
                    raise Exception("Logic error, should never fall through to loading file bytes in area enlarged by patches!")
                self.__handle.seek(key)
                return self.__handle.read(1)[0]

        elif isinstance(key, slice):
            # Grab our iterators.
            start, stop, step = self.__slice(key)

            if start == stop:
                return b""
            if start > stop and step > 0:
                return b""
            if start < stop and step < 0:
                return b""

            # Do we have any modifications to the file in this area?
            if start >= self.__filelength and stop >= self.__filelength:
                modifications = True
            elif self.__lowest_patch is None or (start < self.__lowest_patch and stop < self.__lowest_patch):
                modifications = False
            elif self.__highest_patch is None or (start > self.__highest_patch and stop > self.__highest_patch):
                modifications = False
            else:
                # Whether we should do the slow check or not.
                check = False

                if not self.__regions:
                    # Recreate the index.
                    last_index = -1
                    for iterval in sorted(self.__patches.keys()):
                        # Only attempt to update the region cache if we haven't already
                        # seen something in this section.
                        index = iterval // self.IO_SIZE
                        if index != last_index:
                            self.__regions.add(index)
                            last_index = index

                if start > stop:
                    iterstart = stop + 1
                    iterend = start + 1
                else:
                    iterstart = start
                    iterend = stop

                iterstart //= self.IO_SIZE
                iterend //= self.IO_SIZE

                if iterend == iterstart:
                    iterend += 1

                for index in range(iterstart, iterend):
                    if index in self.__regions:
                        check = True

                if check:
                    modifications = any(index in self.__patches for index in range(start, stop, step))
                else:
                    modifications = False

            # Now see if we can do any fast loading
            if start < stop and step == 1:
                if not modifications:
                    # This is just a contiguous read
                    self.__handle.seek(start)
                    return self.__handle.read(stop - start)
                else:
                    if start < self.__filelength:
                        # We need to modify at least one of the bytes in this read.
                        self.__handle.seek(start)
                        data = [x for x in self.__handle.read(stop - start)]

                        # Append any amount of data we need to read past the end of the file.
                        if len(data) < stop - start:
                            data.extend([0] * ((stop - start) - len(data)))
                    else:
                        data = [0] * (stop - start)

                    # Now we have to modify the data with our own overlay.
                    for off in range(start, stop):
                        if off in self.__patches:
                            data[off - start] = self.__patches[off]

                    return bytes(data)
            elif start > stop and step == -1:
                start += 1
                stop += 1
                if not modifications:
                    # This is just a continguous read, reversed
                    self.__handle.seek(stop)
                    return self.__handle.read(start - stop)[::-1]
                else:
                    if stop < self.__filelength:
                        self.__handle.seek(stop)
                        data = [x for x in self.__handle.read(start - stop)]

                        # Append any amount of data we need to read past the end of the file.
                        if len(data) < start - stop:
                            data.extend([0] * ((start - stop) - len(data)))
                    else:
                        data = [0] * (start - stop)

                    # Now we have to modify the data with our own overlay.
                    for index, off in enumerate(range(stop, start)):
                        if off in self.__patches:
                            data[index] = self.__patches[off]

                    return bytes(data[::-1])
            else:
                # Gotta load the slow way
                resp: List[bytes] = []
                for off in range(start, stop, step):
                    if off in self.__patches:
                        resp.append(bytes([self.__patches[off]]))
                    else:
                        if off >= self.__filelength:
                            raise Exception("Logic error, should never fall through to loading file bytes in area enlarged by patches!")
                        self.__handle.seek(off)
                        resp.append(self.__handle.read(1))
                return b"".join(resp)

        else:
            raise NotImplementedError("Not implemented!")

    @overload
    def __setitem__(self, key: int, val: int) -> None:
        ...

    @overload
    def __setitem__(self, key: slice, val: bytes) -> None:
        ...

    def __setitem__(self, key: Union[int, slice], val: Union[int, bytes]) -> None:
        if self.__unsafe:
            raise Exception("Another FileBytes instance representing the same file was written back!")

        if isinstance(key, int):
            if not isinstance(val, int):
                raise NotImplementedError("Not implemented!")

            # Support negative indexing.
            if key < 0:
                key = self.__patchlength + key
            if key >= self.__patchlength:
                raise IndexError("FileBytes index out of range")

            self.__patches[key] = val
            self.__lowest_patch = min(self.__lowest_patch, key) if self.__lowest_patch is not None else key
            self.__highest_patch = max(self.__highest_patch, key + 1) if self.__highest_patch is not None else (key + 1)
            self.__regions.clear()

        elif isinstance(key, slice):
            if not isinstance(val, bytes):
                raise NotImplementedError("Not implemented!")

            # Grab our iterators.
            start, stop, step = self.__slice(key)
            vallen = len(val)

            if start == stop:
                if vallen != 0:
                    raise NotImplementedError("Cannot resize FileBuffer!")
            if start > stop and step > 0:
                if vallen != 0:
                    raise NotImplementedError("Cannot resize FileBuffer!")
            if start < stop and step < 0:
                if vallen != 0:
                    raise NotImplementedError("Cannot resize FileBuffer!")

            # Now, verify the patches are the right length. Make sure that if
            # somebody catches NotImplementedError that we don't partially
            # modify ourselves.
            for index, _off in enumerate(range(start, stop, step)):
                if index >= vallen:
                    raise NotImplementedError("Cannot resize FileBuffer!")

            if index != (vallen - 1):
                raise NotImplementedError("Cannot resize FileBuffer!")

            # Finally, perform the modification.
            for index, off in enumerate(range(start, stop, step)):
                self.__patches[off] = val[index]
                self.__lowest_patch = min(self.__lowest_patch, off) if self.__lowest_patch is not None else off
                self.__highest_patch = max(self.__highest_patch, off + 1) if self.__highest_patch is not None else (off + 1)
                self.__regions.clear()

        else:
            raise NotImplementedError("Not implemented!")
