"""What the structs of the settings say of themselves: the keys of a table, and the
description of a field, which is the fix a refusal of its value names."""

import typing

import msgspec


def struct_of(shape: object) -> type[msgspec.Struct] | None:
    """The struct type `shape` is, or holds as the one struct of a union with None."""
    given = typing.get_args(shape) or (shape,)
    found = (
        one
        for one in given
        if isinstance(one, type) and issubclass(one, msgspec.Struct)
    )
    return next(found, None)


def fields_of(shape: object) -> tuple[msgspec.structs.FieldInfo, ...]:
    """The fields of a struct type, or of the struct of an optional one; none for another
    type."""
    found = struct_of(shape)
    return msgspec.structs.fields(found) if found else ()


def keys_of(shape: type, table: str) -> tuple[str, ...]:
    """The keys of the table `table` of the file struct `shape`; none for a table with no
    fixed keys (`[peers]`) or one the struct does not have."""
    found = field_of(shape, table)
    inner = fields_of(found.type) if found else ()
    return tuple(field.name for field in inner)


def described(annotated: object) -> str | None:
    """The description of an annotated field type, or None."""
    metadata = getattr(annotated, "__metadata__", ())
    said = (getattr(meta, "description", None) for meta in metadata)
    return next((one for one in said if one), None)


def fix_of(shape: type, where: str) -> str | None:
    """The description of the field at `where` (`branch.base`, `seats.experts[0]`) of the
    struct `shape`, or None."""
    table, _, rest = where.partition(".")
    holder = field_of(shape, table)
    if holder is None:
        return None
    if not rest:
        return described(hinted(shape).get(table))
    key = rest.split(".")[0].split("[")[0]
    return described(hinted(holder.type).get(key))


def field_of(shape: type, name: str) -> msgspec.structs.FieldInfo | None:
    """The field `name` of the struct `shape`, or None."""
    return next((field for field in fields_of(shape) if field.name == name), None)


def hinted(shape: object) -> dict[str, object]:
    """The annotations of a struct type, with their metadata; none for another type."""
    found = struct_of(shape)
    return typing.get_type_hints(found, include_extras=True) if found else {}
