from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://pypi.org/project/xsdata"


@dataclass
class TypeName:
    class Meta:
        name = "ClassName"
        namespace = "http://pypi.org/project/xsdata"

    case: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    safePrefix: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class CompoundFields:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    defaultName: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    forceDefaultName: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: bool | None = field(
        default=None,
        metadata={
            "required": True,
        },
    )


@dataclass
class ConstantName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    safePrefix: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class FieldName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    safePrefix: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Format:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    repr: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    eq: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    order: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    unsafeHash: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    frozen: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    slots: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    kwOnly: bool | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class ModuleName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    safePrefix: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class PackageName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    safePrefix: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Substitution:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    type_value: str | None = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    search: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    replace: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Conventions:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    ClassName: TypeName | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    FieldName: FieldName | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    ConstantName: ConstantName | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    ModuleName: ModuleName | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    PackageName: PackageName | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Output:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    maxLineLength: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    Package: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    Format: Format | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    Structure: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    DocstringStyle: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    FilterStrategy: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    RelativeImports: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    CompoundFields: CompoundFields | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    PostponedAnnotations: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    UnnestClasses: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    IgnorePatterns: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Substitutions:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    Substitution: list[Substitution] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Config:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    version: float | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    Output: Output | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    Conventions: Conventions | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    Substitutions: Substitutions | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
