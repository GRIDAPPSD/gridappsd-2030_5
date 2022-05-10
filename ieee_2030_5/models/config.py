from dataclasses import dataclass, field
from typing import List, Optional

__NAMESPACE__ = "http://pypi.org/project/xsdata"


@dataclass
class TypeName:
    class Meta:
        name = "ClassName"
        namespace = "http://pypi.org/project/xsdata"

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    safePrefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class CompoundFields:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    defaultName: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    forceDefaultName: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    value: Optional[bool] = field(
        default=None
    )


@dataclass
class ConstantName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    safePrefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class FieldName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    safePrefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Format:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    repr: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    eq: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    order: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    unsafeHash: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    frozen: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    slots: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    kwOnly: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class ModuleName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    safePrefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class PackageName:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    safePrefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Substitution:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    search: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    replace: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Conventions:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    ClassName: Optional[TypeName] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    FieldName: Optional[FieldName] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    ConstantName: Optional[ConstantName] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    ModuleName: Optional[ModuleName] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    PackageName: Optional[PackageName] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Output:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    maxLineLength: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    Package: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    Format: Optional[Format] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    Structure: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    DocstringStyle: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    RelativeImports: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    CompoundFields: Optional[CompoundFields] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    PostponedAnnotations: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    UnnestClasses: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Substitutions:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    Substitution: List[Substitution] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Config:
    class Meta:
        namespace = "http://pypi.org/project/xsdata"

    version: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    Output: Optional[Output] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    Conventions: Optional[Conventions] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    Substitutions: Optional[Substitutions] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
