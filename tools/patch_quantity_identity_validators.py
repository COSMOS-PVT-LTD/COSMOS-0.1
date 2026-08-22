"""One-time patch: replace corrupted identity validator methods in quantity.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "knowledge/models/quantity.py"

REPLACEMENT = '''
    def _validate_required_identity_fields(self) -> None:
        """Validate that every mandatory identity field exists."""

        required_fields = (
            ("quantity_id", self.quantity_id),
            ("name", self.name),
            ("short_name", self.short_name),
            ("symbol", self.symbol),
            ("description", self.description),
            ("physical_quantity_name", self.physical_quantity_name),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )

        for field_name, value in required_fields:
            if value is None:
                raise ValueError(f"{field_name} cannot be None.")
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be blank.")

    def _validate_identity_strings(self) -> None:
        """Validate identity strings for formatting and whitespace."""

        fields = (
            ("quantity_id", self.quantity_id),
            ("name", self.name),
            ("short_name", self.short_name),
            ("symbol", self.symbol),
            ("description", self.description),
            ("physical_quantity_name", self.physical_quantity_name),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )

        for field_name, value in fields:
            if value != value.strip():
                raise ValueError(
                    f"{field_name} cannot contain leading or trailing whitespace."
                )
            if any(ch in value for ch in ('\n', '\r', '\t')):
                raise ValueError(f"{field_name} cannot contain control characters.")
            if "  " in value:
                raise ValueError(f"{field_name} cannot contain consecutive spaces.")

    def _validate_identifier(self) -> None:
        """Validate the engineering identifier."""

        if not _IDENTIFIER_PATTERN.fullmatch(self.quantity_id):
            raise ValueError("quantity_id contains invalid characters.")
        if self.quantity_id.startswith(".") or self.quantity_id.endswith("."):
            raise ValueError("quantity_id cannot begin or end with '.'.")

        reserved = {"NULL", "NONE", "UNKNOWN", "UNDEFINED", "DEFAULT"}
        if self.quantity_id.upper() in reserved:
            raise ValueError("quantity_id uses a reserved identifier.")

    def _validate_name(self) -> None:
        """Validate engineering names."""

        names = (
            ("name", self.name),
            ("short_name", self.short_name),
            ("physical_quantity_name", self.physical_quantity_name),
        )
        reserved = {"unknown", "undefined", "null", "none", "default", "temp", "test"}

        for field_name, value in names:
            if not _NAME_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} contains invalid characters.")
            if value.lower() in reserved:
                raise ValueError(f"{field_name} uses a reserved engineering name.")
            if value[0].isdigit():
                raise ValueError(f"{field_name} cannot begin with a digit.")
            if value.endswith("."):
                raise ValueError(f"{field_name} cannot end with '.'.")
            if "--" in value or "__" in value:
                raise ValueError(f"{field_name} contains repeated separators.")

        if self.name.casefold() == self.short_name.casefold():
            raise ValueError("short_name should differ from name.")
        if (
            self.name.casefold() == self.physical_quantity_name.casefold()
            and len(self.name) < 3
        ):
            raise ValueError("Engineering names are too short.")

    def _validate_symbol(self) -> None:
        """Validate engineering and scientific symbols."""

        symbols = (
            ("symbol", self.symbol),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )
        reserved = {"unknown", "undefined", "null", "none"}

        for field_name, value in symbols:
            if not _SYMBOL_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} contains invalid characters.")
            if value.casefold() in reserved:
                raise ValueError(f"{field_name} uses a reserved symbol.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be blank.")

        if self.symbol.casefold() == self.name.casefold():
            raise ValueError("symbol should not equal name.")
        if self.symbol.casefold() == self.description.casefold():
            raise ValueError("symbol should not equal description.")
        if len(self.symbol) > 32:
            raise ValueError("Engineering symbols should remain concise.")
        if len(self.physical_quantity_symbol) > 32:
            raise ValueError("physical_quantity_symbol is too long.")

    def _validate_aliases(self) -> None:
        """Validate engineering aliases."""

        if not isinstance(self.aliases, tuple):
            raise TypeError("aliases must be a tuple.")

        reserved_aliases = {
            "unknown", "undefined", "none", "null", "default", "temp", "test",
        }
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        }
        normalized_aliases: set[str] = set()

        for alias in self.aliases:
            if not isinstance(alias, str):
                raise TypeError("Each alias must be a string.")
            cleaned = alias.strip()
            if not cleaned:
                raise ValueError("Aliases cannot contain blank values.")
            if len(cleaned) < 2 or len(cleaned) > 128:
                raise ValueError(f"Alias '{cleaned}' has invalid length.")
            if not _NAME_PATTERN.fullmatch(cleaned):
                raise ValueError(f"Alias '{cleaned}' contains invalid characters.")
            lowered = cleaned.casefold()
            if lowered in reserved_aliases:
                raise ValueError(f"Alias '{cleaned}' is reserved.")
            if lowered in normalized_aliases:
                raise ValueError(f"Duplicate alias '{cleaned}'.")
            if lowered in canonical_identity:
                raise ValueError(
                    f"Alias '{cleaned}' duplicates a canonical identity field."
                )
            normalized_aliases.add(lowered)

        if len(self.aliases) > 100:
            raise ValueError("A Quantity may define at most 100 aliases.")

    def _validate_search_keywords(self) -> None:
        """Validate search keywords."""

        if not isinstance(self.search_keywords, tuple):
            raise TypeError("search_keywords must be a tuple.")

        reserved_keywords = {"unknown", "undefined", "null", "none", "default"}
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
        }
        normalized_keywords: set[str] = set()

        for keyword in self.search_keywords:
            if not isinstance(keyword, str):
                raise TypeError("Each search keyword must be a string.")
            cleaned = keyword.strip()
            if not cleaned:
                raise ValueError("Search keywords cannot be blank.")
            if len(cleaned) < 2 or len(cleaned) > 64:
                raise ValueError(f"Keyword '{cleaned}' has invalid length.")
            if cleaned.startswith("-") or cleaned.endswith("-"):
                raise ValueError(f"Keyword '{cleaned}' has invalid hyphen placement.")
            lowered = cleaned.casefold()
            if lowered in reserved_keywords:
                raise ValueError(f"Keyword '{cleaned}' is reserved.")
            if lowered in normalized_keywords:
                raise ValueError(f"Duplicate search keyword '{cleaned}'.")
            normalized_keywords.add(lowered)

        if len(self.search_keywords) > 200:
            raise ValueError("A Quantity may define at most 200 search keywords.")

    def _validate_tags(self) -> None:
        """Validate engineering tags."""

        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be a tuple.")

        reserved_tags = {
            "unknown", "undefined", "none", "null", "default",
            "misc", "temporary", "temp", "test",
        }
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        }
        normalized_tags: set[str] = set()

        for tag in self.tags:
            if not isinstance(tag, str):
                raise TypeError("Each tag must be a string.")
            cleaned = tag.strip()
            if not cleaned:
                raise ValueError("Tags cannot contain blank values.")
            if len(cleaned) < 2 or len(cleaned) > 64:
                raise ValueError(f"Tag '{cleaned}' has invalid length.")
            if not _NAME_PATTERN.fullmatch(cleaned):
                raise ValueError(f"Tag '{cleaned}' contains invalid characters.")
            if cleaned != tag:
                raise ValueError(f"Tag '{tag}' contains leading or trailing whitespace.")
            lowered = cleaned.casefold()
            if lowered in reserved_tags:
                raise ValueError(f"Tag '{cleaned}' is reserved.")
            if lowered in normalized_tags:
                raise ValueError(f"Duplicate tag '{cleaned}'.")
            if lowered in canonical_identity:
                raise ValueError(f"Tag '{cleaned}' duplicates a canonical identity field.")
            normalized_tags.add(lowered)

        if len(self.tags) > 100:
            raise ValueError("A Quantity may define at most 100 tags.")

    def _validate_identity_lengths(self) -> None:
        """Validate length constraints for identity fields."""

        field_limits = (
            ("quantity_id", self.quantity_id, 128),
            ("name", self.name, 256),
            ("short_name", self.short_name, 64),
            ("symbol", self.symbol, 32),
            ("physical_quantity_name", self.physical_quantity_name, 256),
            ("physical_quantity_symbol", self.physical_quantity_symbol, 32),
            ("description", self.description, 4096),
        )

        for field_name, value, maximum_length in field_limits:
            if len(value) == 0:
                raise ValueError(f"{field_name} cannot be empty.")
            if len(value) > maximum_length:
                raise ValueError(
                    f"{field_name} exceeds the maximum supported length "
                    f"of {maximum_length} characters."
                )

        if len(self.aliases) > 100:
            raise ValueError("A Quantity may define at most 100 aliases.")
        if len(self.search_keywords) > 200:
            raise ValueError("A Quantity may define at most 200 search keywords.")
        if len(self.tags) > 100:
            raise ValueError("A Quantity may define at most 100 tags.")

    def _validate_identity_duplicates(self) -> None:
        """Validate duplicate values across identity collections."""

        collections = (
            ("aliases", self.aliases),
            ("search_keywords", self.search_keywords),
            ("tags", self.tags),
        )

        for collection_name, values in collections:
            normalized: set[str] = set()
            for value in values:
                lowered = value.casefold()
                if lowered in normalized:
                    raise ValueError(
                        f"Duplicate value '{value}' found in {collection_name}."
                    )
                normalized.add(lowered)

        alias_set = {value.casefold() for value in self.aliases}
        keyword_set = {value.casefold() for value in self.search_keywords}
        tag_set = {value.casefold() for value in self.tags}

        duplicate_alias_keywords = alias_set & keyword_set
        if duplicate_alias_keywords:
            raise ValueError(
                "Aliases and search_keywords contain duplicate values: "
                f"{sorted(duplicate_alias_keywords)}"
            )

        duplicate_alias_tags = alias_set & tag_set
        if duplicate_alias_tags:
            raise ValueError(
                "Aliases and tags contain duplicate values: "
                f"{sorted(duplicate_alias_tags)}"
            )

        duplicate_keyword_tags = keyword_set & tag_set
        if duplicate_keyword_tags:
            raise ValueError(
                "search_keywords and tags contain duplicate values: "
                f"{sorted(duplicate_keyword_tags)}"
            )

    def _validate_identity_consistency(self) -> None:
        """Validate consistency between all identity fields."""

        if self.name.casefold() == self.short_name.casefold():
            raise ValueError("short_name must differ from name.")
        if self.name.casefold() == self.symbol.casefold():
            raise ValueError("symbol must differ from name.")
        if (
            self.physical_quantity_name.casefold() == self.name.casefold()
            and self.category is not QuantityCategory.SCALAR
        ):
            raise ValueError(
                "physical_quantity_name should provide additional scientific meaning."
            )
        if self.symbol.casefold() == self.physical_quantity_symbol.casefold():
            raise ValueError("symbol and physical_quantity_symbol must differ.")
        if len(self.symbol) > len(self.name):
            raise ValueError("Engineering symbols should normally be shorter than names.")
        if self.description.casefold() == self.name.casefold():
            raise ValueError("description cannot duplicate name.")
        if self.description.casefold() == self.short_name.casefold():
            raise ValueError("description cannot duplicate short_name.")

        canonical_values = (
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        )
        if len(canonical_values) != len(set(canonical_values)):
            raise ValueError("Canonical identity fields must all be unique.")

        if len(self.search_keywords) == 0 and len(self.aliases) == 0:
            raise ValueError("At least one alias or search keyword must be provided.")

        if len(self.name.split()) > 10:
            raise ValueError("Engineering names should remain concise.")
        if len(self.description.split()) < 5:
            raise ValueError(
                "description is too short to adequately describe the quantity."
            )

'''


def main() -> None:
    lines = TARGET.read_text().splitlines()
    start = next(
        i for i, line in enumerate(lines)
        if line.strip() == "def _validate_required_identity_fields(self) -> None:"
    )
    end = next(
        i for i, line in enumerate(lines)
        if i > start and line.strip() == "# Identity & Display Properties"
    )
  # section header is two lines above @property; find comment block start
    while end > start and not lines[end - 1].strip().startswith("# ====="):
        end -= 1

    new_block = [line for line in REPLACEMENT.strip("\n").splitlines()]
    updated = lines[:start] + new_block + lines[end:]
    TARGET.write_text("\n".join(updated) + "\n")
    print(f"Patched lines {start + 1}-{end} ({end - start} -> {len(new_block)} lines)")


if __name__ == "__main__":
    main()
