from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any, Literal, TypedDict, TypeVar, overload

from valkey.asyncio.client import Valkey
from valkey.asyncio.connection import (
    BaseParser,
    ConnectCallbackT,
    Connection,
    ConnectionPool,
    Encoder,
    SSLConnection,
    _ConnectionT,
    _Sentinel,
)
from valkey.asyncio.retry import Retry
from valkey.commands import AsyncSentinelCommands
from valkey.credentials import CredentialProvider
from valkey.exceptions import ConnectionError, ValkeyError

_ValkeyT = TypeVar("_ValkeyT", bound=Valkey[Any])

class MasterNotFoundError(ConnectionError): ...
class SlaveNotFoundError(ConnectionError): ...

class SentinelManagedConnection(Connection):
    connection_pool: ConnectionPool[Any] | None
    def __init__(
        self,
        *,
        connection_pool: ConnectionPool[Any] | None,
        # **kwargs forwarded to Connection.
        host: str = "localhost",
        port: str | int = 6379,
        socket_keepalive: bool = False,
        socket_keepalive_options: Mapping[int, int | bytes] | None = None,
        socket_type: int = 0,
        db: str | int = 0,
        password: str | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        retry_on_timeout: bool = False,
        retry_on_error: list[type[ValkeyError]] | _Sentinel = ...,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: type[BaseParser] = ...,
        socket_read_size: int = 65536,
        health_check_interval: float = 0,
        client_name: str | None = None,
        username: str | None = None,
        retry: Retry | None = None,
        valkey_connect_func: ConnectCallbackT | None = None,
        encoder_class: type[Encoder] = ...,
        credential_provider: CredentialProvider | None = None,
    ) -> None: ...
    async def connect_to(self, address: tuple[str, int]) -> None: ...
    async def connect(self) -> None: ...

class SentinelManagedSSLConnection(SentinelManagedConnection, SSLConnection): ...

class SentinelConnectionPool(ConnectionPool[_ConnectionT]):
    is_master: bool
    check_connection: bool
    service_name: str
    sentinel_manager: Sentinel
    master_address: tuple[str, int] | None
    slave_rr_counter: int | None

    def __init__(
        self,
        service_name: str,
        sentinel_manager: Sentinel,
        *,
        ssl: bool = False,
        connection_class: type[SentinelManagedConnection] = ...,
        is_master: bool = True,
        check_connection: bool = False,
        # **kwargs ultimately forwarded to construction Connection instances.
        host: str = "localhost",
        port: str | int = 6379,
        socket_keepalive: bool = False,
        socket_keepalive_options: Mapping[int, int | bytes] | None = None,
        socket_type: int = 0,
        db: str | int = 0,
        password: str | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        retry_on_timeout: bool = False,
        retry_on_error: list[type[ValkeyError]] | _Sentinel = ...,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: type[BaseParser] = ...,
        socket_read_size: int = 65536,
        health_check_interval: float = 0,
        client_name: str | None = None,
        username: str | None = None,
        retry: Retry | None = None,
        valkey_connect_func: ConnectCallbackT | None = None,
        encoder_class: type[Encoder] = ...,
        credential_provider: CredentialProvider | None = None,
    ) -> None: ...
    async def get_master_address(self) -> tuple[str, int]: ...
    async def rotate_slaves(self) -> AsyncIterator[tuple[str, int]]: ...

_State = TypedDict(
    "_State", {"ip": str, "port": int, "is_master": bool, "is_sdown": bool, "is_odown": bool, "num-other-sentinels": int}
)

class Sentinel(AsyncSentinelCommands):
    sentinel_kwargs: Mapping[str, Any]
    sentinels: list[Valkey[Any]]
    min_other_sentinels: int
    connection_kwargs: Mapping[str, Any]
    def __init__(
        self,
        sentinels: Iterable[tuple[str, int]],
        min_other_sentinels: int = 0,
        sentinel_kwargs: Mapping[str, Any] | None = None,
        **connection_kwargs: Any,
    ) -> None: ...
    async def execute_command(self, *args: Any, once: bool = False, **kwargs: Any) -> Literal[True]: ...
    def check_master_state(self, state: _State, service_name: str) -> bool: ...
    async def discover_master(self, service_name: str) -> tuple[str, int]: ...
    def filter_slaves(self, slaves: Iterable[_State]) -> list[tuple[str, int]]: ...
    async def discover_slaves(self, service_name: str) -> list[tuple[str, int]]: ...
    @overload
    def master_for(
        self,
        service_name: str,
        valkey_class: type[_ValkeyT],
        connection_pool_class: type[SentinelConnectionPool[Any]] = ...,
        # Forwarded to the connection pool constructor.
        **kwargs: Any,
    ) -> _ValkeyT: ...
    @overload
    def master_for(
        self,
        service_name: str,
        *,
        connection_pool_class: type[SentinelConnectionPool[Any]] = ...,
        # Forwarded to the connection pool constructor.
        **kwargs: Any,
    ) -> Valkey[Any]: ...
    @overload
    def slave_for(
        self,
        service_name: str,
        valkey_class: type[_ValkeyT],
        connection_pool_class: type[SentinelConnectionPool[Any]] = ...,
        # Forwarded to the connection pool constructor.
        **kwargs: Any,
    ) -> _ValkeyT: ...
    @overload
    def slave_for(
        self,
        service_name: str,
        *,
        connection_pool_class: type[SentinelConnectionPool[Any]] = ...,
        # Forwarded to the connection pool constructor.
        **kwargs: Any,
    ) -> Valkey[Any]: ...