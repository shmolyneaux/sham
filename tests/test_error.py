from sham import error
from sham.error import Error

import pytest

@pytest.mark.parametrize(
    "arg,expected",
    [
        ([], ([],[])),
        ([3], ([3],[])),
        ([3, 2], ([3,2],[])),

        ([Error(3)], ([], [Error(3)])),
        ([Error(3), 2], ([2], [Error(3)])),
        ([2, Error(3)], ([2], [Error(3)])),
        ([2, Error(3), 4, Error(5)], ([2, 4], [Error(3), Error(5)])),
    ]
)
def test_partition_list(arg, expected):
    result = error.partition_list(arg)
    assert result == expected

@pytest.mark.parametrize(
    "arg,expected",
    [
        ({}, ({},{})),
        ({"a": 1}, ({"a": 1},{})),
        ({"a": 1, "b": 2}, ({"a": 1, "b": 2},{})),

        ({"a": Error(1)}, ({},{"a": Error(1)})),
        ({"a": Error(1), "b": 2}, ({"b": 2}, {"a": Error(1)})),
        ({"a": 2, "b": Error(3)}, ({"a": 2}, {"b": Error(3)})),
        (
            {"a": 1, "b": Error(2), "c": 3, "d": Error(4)},
            (
                {"a": 1, "c": 3},
                {"b": Error(2), "d": Error(4)},
            )
        ),
    ]
)
def test_partition_dict(arg, expected):
    result = error.partition_dict(arg)
    assert result == expected


@pytest.mark.parametrize(
    "arg,expected",
    [
        (Error("test"), "test"),
        (Error(["foo", "bar", "baz"]), "foo\nbar\nbaz"),
        (Error({"test": 3}), "test:\n    3"),
        (Error({"test": [3]}), "test:\n    3"),
        (Error({"test": ["foo", "bar", "baz"]}), "test:\n    foo\n    bar\n    baz"),
    ]
)
def test_format(arg, expected):
    result = error.format_recursive(arg)
    assert result == expected
