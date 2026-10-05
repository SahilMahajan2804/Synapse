import re

from app.mapping.session import SessionContext


class DefaultReverseMapper:
    def restore(self, text: str, session: SessionContext) -> tuple[str, int]:
        replacements: list[tuple[str, str]] = []

        def add_mapping(surrogate: str | None, original: str | None) -> None:
            if surrogate and original and surrogate.strip() and original.strip():
                replacements.append((surrogate, original))

        for mapping in session.by_surrogate.values():
            surrogate = getattr(mapping, "surrogate", None)
            original = getattr(mapping, "original", None)
            add_mapping(surrogate, original)

        for mapping in session.by_original.values():
            surrogate = getattr(mapping, "surrogate", None)
            original = getattr(mapping, "original", None)
            add_mapping(surrogate, original)

        for alias in session.persons:
            add_mapping(alias.sur_first, alias.orig_first)
            add_mapping(alias.sur_last, alias.orig_last)
            add_mapping(alias.sur_full, alias.orig_full)

        if not replacements:
            return text, 0

        deduped: dict[str, str] = {}
        for surrogate, original in replacements:
            deduped.setdefault(surrogate, original)

        sorted_replacements = sorted(deduped.items(), key=lambda item: len(item[0]), reverse=True)
        pattern = re.compile(
            r"(?<![\w])(?:" + "|".join(re.escape(surrogate) for surrogate, _ in sorted_replacements) + r")(?![\w])",
            re.IGNORECASE,
        )

        def replace(match: re.Match[str]) -> str:
            found = match.group(0)
            for surrogate, original in sorted_replacements:
                if found.casefold() == surrogate.casefold():
                    return original.upper() if found.isupper() else original
            return found

        restored = pattern.sub(replace, text)
        return restored, len(pattern.findall(text))
