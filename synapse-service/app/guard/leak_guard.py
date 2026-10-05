import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LeakGuardResult:
    passed: bool
    leaked_count: int
    leaked_values: list[str]


class LeakGuard:
    def check(self, outgoing_text: str, originals: list[str]) -> LeakGuardResult:
        leaked_values: list[str] = []
        for original in originals:
            clean = original.strip()
            if len(clean) < 3:
                continue
            pattern = re.compile(rf"(?<![\w]){re.escape(clean)}(?![\w])", re.IGNORECASE)
            if pattern.search(outgoing_text):
                leaked_values.append(clean)
                continue
            digits = re.sub(r"\D", "", clean)
            if len(digits) >= 6 and digits in re.sub(r"\D", "", outgoing_text):
                leaked_values.append(clean)
        unique: list[str] = []
        seen: set[str] = set()
        for item in leaked_values:
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return LeakGuardResult(passed=len(unique) == 0, leaked_count=len(unique), leaked_values=unique)
