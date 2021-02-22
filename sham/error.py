import textwrap
import typing
from dataclasses import dataclass

# Ideally the "Any" is where this would be recursive
ErrorInfo = str | list[typing.Any] | dict[str, typing.Any]

@dataclass
class Error:
    error_info: ErrorInfo

    @staticmethod
    def wrap(info: str, value: Any):
        error_info = {info: _to_error_info(value)}
        return Error(error_info)

    def __str__(self):
        return format_recursive(self.error_info)

def _to_error_info(value: Any) -> ErrorInfo:
    match value:
        case dict():
            return {
                _to_error_info(k): _to_error_info(v)
                for k,v in value.items()
            }

        case list():
            return [
                _to_error_info(item)
                for item in value
            ]

    return str(value)


def format_recursive(error_info):
    match error_info:
        case list():
            return "\n".join(format_recursive(item) for item in error_info)

        case dict():
            return "\n".join(
                f"{k}:\n" + textwrap.indent(format_recursive(v), "    ")
                for k, v in error_info.items()
            )

        case other:
            return str(other)


T = typing.TypeVar("T")
K = typing.TypeVar("K")


def partition_list(iterable: typing.Iterable[T | Error]) -> Tuple[list[T], list[Error]]:
    errors: list[Error] = []
    values: list[T] = []

    for value in iterable:
        match value:
            case Error():
                errors.append(value)

            case success:
                values.append(success)

    return values, errors


def partition_dict(mapping: typing.Mapping[K, T | Error]) -> Tuple[dict[K, T], list[K, Error]]:
    errors: dict[K, Error] = {}
    values: dict[K, T] = {}

    for key, value in mapping.items():
        match value:
            case Error():
                errors[key] = value

            case _:
                values[key] = value

    return values, errors
