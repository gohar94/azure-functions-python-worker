# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import abc
import mmap
from typing import Optional
from .memorymappedfile_constants import MemoryMappedFileConstants as consts


class FileAccessor(metaclass=abc.ABCMeta):
    """
    For accessing memory maps.
    This is an interface that must be implemented by sub-classes to provide platform-specific
    support for accessing memory maps.
    Currently the following two sub-classes are implemented:
        1) FileAccessorWindows
        2) FileAccessorLinux
    """
    @abc.abstractmethod
    def open_mem_map(self, map_name: str, map_size: int , access: int) -> Optional[mmap.mmap]:
        """
        Opens an existing memory map.
        Returns the mmap if successful, None otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_mem_map(self, map_name: str, map_size: int) -> Optional[mmap.mmap]:
        """
        Creates a new memory map.
        Returns the mmap if successful, None otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_mem_map(self, map_name: str, mem_map: mmap.mmap) -> bool:
        """
        Deletes the memory map and any backing resources associated with it.
        If there is no memory map with the given name, then no action is performed.
        Returns True if the memory map was successfully deleted, False otherwise.
        """
        raise NotImplementedError

    def _verify_new_map_created(self, map_name: str, mem_map) -> bool:
        """Checks if the first byte of the memory map is zero.
        If it is not, this memory map already existed.
        """
        mem_map.seek(0)
        byte_read = mem_map.read(1)
        is_new_mmap = False
        if byte_read != consts.ZERO_BYTE:
            is_new_mmap = False
        else:
            is_new_mmap = True
        mem_map.seek(0)
        return is_new_mmap