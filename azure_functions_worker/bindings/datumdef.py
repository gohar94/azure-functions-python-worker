# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any
from typing import Optional
import json
from .. import protos
from .shared_memory_manager import SharedMemoryManager


class Datum:
    def __init__(self, value, type):
        self.value = value
        self.type = type

    @property
    def python_value(self) -> Any:
        if self.value is None or self.type is None:
            return None
        elif self.type in ('bytes', 'string', 'int', 'double'):
            return self.value
        elif self.type == 'json':
            return json.loads(self.value)
        elif self.type == 'collection_string':
            return [v for v in self.value.string]
        elif self.type == 'collection_bytes':
            return [v for v in self.value.bytes]
        elif self.type == 'collection_double':
            return [v for v in self.value.double]
        elif self.type == 'collection_sint64':
            return [v for v in self.value.sint64]
        else:
            return self.value

    @property
    def python_type(self) -> type:
        return type(self.python_value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.value == other.value and self.type == other.type

    def __hash__(self):
        return hash((type(self), (self.value, self.type)))

    def __repr__(self):
        val_repr = repr(self.value)
        if len(val_repr) > 10:
            val_repr = val_repr[:10] + '...'
        return '<Datum {} {}>'.format(self.type, val_repr)

    @classmethod
    def from_typed_data(cls, td: protos.TypedData):
        tt = td.WhichOneof('data')
        if tt == 'http':
            http = td.http
            val = dict(
                method=Datum(http.method, 'string'),
                url=Datum(http.url, 'string'),
                headers={
                    k: Datum(v, 'string') for k, v in http.headers.items()
                },
                body=(
                    Datum.from_typed_data(http.body)
                    or Datum(type='bytes', value=b'')
                ),
                params={
                    k: Datum(v, 'string') for k, v in http.params.items()
                },
                query={
                    k: Datum(v, 'string') for k, v in http.query.items()
                },
            )
        elif tt == 'string':
            val = td.string
        elif tt == 'bytes':
            val = td.bytes
        elif tt == 'json':
            val = td.json
        elif tt == 'collection_bytes':
            val = td.collection_bytes
        elif tt == 'collection_string':
            val = td.collection_string
        elif tt == 'collection_sint64':
            val = td.collection_sint64
        elif tt is None:
            return None
        else:
            raise NotImplementedError(
                'unsupported TypeData kind: {!r}'.format(tt)
            )

        return cls(val, tt)

    @classmethod
    def from_rpc_shared_memory(cls, shmem: protos.RpcSharedMemory, shmem_mgr: SharedMemoryManager) -> Optional[Datum]:
        """
        Reads the specified shared memory region and converts the read data into a datum object of
        the corresponding type.
        """
        mmap_name = shmem.name
        offset = shmem.offset
        count = shmem.count
        data_type = shmem.type
        if data_type == protos.RpcDataType.bytes:
            val = shmem_mgr.get_bytes(mmap_name, offset, count)
            if val is not None:
                return cls(val, 'bytes')
        elif data_type == protos.RpcDataType.string:
            val = shmem_mgr.get_string(mmap_name, offset, count)
            if val is not None:
                return cls(val, 'string')
        return None

    def to_rpc_shared_memory(self, shmem_mgr: SharedMemoryManager) -> protos.RpcSharedMemory:
        """
        Writes the given value to shared memory and returns the corresponding RpcSharedMemory
        object which can be sent back to the functions host over RPC.
        """
        if self.type == 'bytes':
            value = self.value
            map_name = shmem_mgr.put_bytes(value)
            if map_name is not None:
                shmem = protos.RpcSharedMemory(
                    name=map_name,
                    offset=0,
                    count=len(value),
                    type=protos.RpcDataType.bytes)
                return shmem
            else:
                raise Exception(
                    f'cannot write datum value (type: {self.type}) into '
                    f'shared memory (name: {map_name})'
                )
        elif self.type == 'string':
            value = self.value
            map_name = shmem_mgr.put_string(value)
            if map_name is not None:
                shmem = protos.RpcSharedMemory(
                    name=map_name,
                    offset=0,
                    count=len(value),
                    type=protos.RpcDataType.string)
                return shmem
            else:
                raise Exception(
                    f'cannot write datum value (type: {self.type}) into '
                    f'shared memory (name: {map_name})'
                )
        else:
            raise NotImplementedError(
                f'unsupported datum type ({self.type}) for shared memory'
            )

def datum_as_proto(datum: Datum) -> protos.TypedData:
    if datum.type == 'string':
        return protos.TypedData(string=datum.value)
    elif datum.type == 'bytes':
        return protos.TypedData(bytes=datum.value)
    elif datum.type == 'json':
        return protos.TypedData(json=datum.value)
    elif datum.type == 'http':
        return protos.TypedData(http=protos.RpcHttp(
            status_code=datum.value['status_code'].value,
            headers={
                k: v.value
                for k, v in datum.value['headers'].items()
            },
            enable_content_negotiation=False,
            body=datum_as_proto(datum.value['body']),
        ))
    else:
        raise NotImplementedError(
            'unexpected Datum type: {!r}'.format(datum.type)
        )