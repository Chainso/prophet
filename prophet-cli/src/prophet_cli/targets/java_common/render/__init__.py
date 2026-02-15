from __future__ import annotations

from .support import add_java_imports_for_type
from .support import annotate_generated_java_files
from .support import effective_base_package
from .support import java_type_for_field
from .support import java_type_for_type_descriptor
from .support import render_javadoc_block
from .support import render_java_record_with_builder
from .support import struct_target_ids_for_type

__all__ = [
    "add_java_imports_for_type",
    "annotate_generated_java_files",
    "effective_base_package",
    "java_type_for_field",
    "java_type_for_type_descriptor",
    "render_javadoc_block",
    "render_java_record_with_builder",
    "struct_target_ids_for_type",
]
