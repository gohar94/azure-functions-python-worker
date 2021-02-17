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

    def _is_dirty_bit_set(self, map_name: str, mem_map) -> bool:
        """
        Checks if the dirty bit of the memory map has been set or not.
        """
        mem_map.seek(0)
        byte_read = mem_map.read(1)
        if byte_read == consts.DIRTY_BIT_SET:
            is_set = True
        else:
            is_set = False
        mem_map.seek(0)
        return is_set

    def _set_dirty_bit(self, map_name: str, mem_map):
        """
        Sets the dirty bit in the header of the memory map to indicate that this memory map is not
        new anymore.
        """
        mem_map.seek(0)
        mem_map.write(consts.DIRTY_BIT_SET)
        mem_map.seek(0)