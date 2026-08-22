## 2024-05-18 - Delegate Paint Loop Bottleneck
**Learning:** In Qt/PySide6 architectures, the `paint()` method of a `QStyledItemDelegate` is a critical hot path, executed for every visible item during scrolling or data changes. Performing expensive operations like `re.compile()` within this loop causes noticeable UI lag. Python caches compiled regexes, but the dictionary lookup and function call still add significant overhead when called hundreds of times per second.
**Action:** When creating custom Qt delegates that rely on regular expressions or other heavy computations, pre-calculate or compile these resources in setter methods (e.g., `set_term()`) and store them as instance variables, rather than computing them dynamically inside `paint()`.

## 2024-05-18 - Filter Matching Inner Loop Optimizaton
**Learning:** In highly frequent data filtering operations running on large arrays of complex objects (like PySide models sorting and filtering logs), repeating string manipulations (like `lower()`) and list lookups (O(n) on small level arrays) per object per loop causes measurable performance hits over time.
**Action:** When creating search or filter logic inside tight loops, aggressively leverage sets for O(1) membership testing and rely on lazy-evaluation caching (such as `LogEntry.raw_lower`) or pre-calculate query inputs once outside the iteration loop.

## 2024-05-18 - String Lowercasing in lessThan loop
**Learning:** In Qt/PySide6 sorting algorithms (`QSortFilterProxyModel.lessThan`), doing operations like `.lower()` on strings inside the sort comparison loop turns into an $O(N \log N)$ bottleneck, as it gets called continuously for every single comparison during sorting.
**Action:** Always pre-calculate and lazily cache lowercase versions of strings inside the data models (like `LogEntry.message_lower`) instead of doing it inline within the `lessThan` function.
## 2024-05-19 - Repeated Timestamp Format Parsing Optimization
**Learning:** In log ingestion loops, checking a raw timestamp string against a list of format definitions using repeated `datetime.strptime()` generates significant overhead due to consecutive `ValueError` exceptions for failed format matches. Because standard log files almost universally maintain a consistent timestamp format, this repetitive failing on $O(n)$ formats is extremely wasteful.
**Action:** Optimize timestamp parsing by caching the last successfully matched format string as an instance variable (`self._last_successful_fmt`). Check this cached format first. If it matches, immediately return the parsed `datetime`, successfully bypassing the slow-path iteration entirely and yielding an $O(1)$ fast path. This dropped parsing time from ~0.77s to ~0.24s in benchmarks.
## 2024-05-18 - [Performance] Cache upper/lower conversions in models
**Learning:** PySide models, especially custom proxy filter models and delegates, query row data extremely frequently (e.g., during filtering or redraws). Recomputing `.upper()` or `.lower()` on each item role query or filter check adds up to a huge overhead.
**Action:** Always lazily evaluate and cache these values directly in the `LogEntry` dataclass as properties (e.g., `_level_upper`, `_raw_lower`).

## 2024-05-18 - String Integer Casting in lessThan loop
**Learning:** In Qt/PySide6 sorting algorithms (`QSortFilterProxyModel.lessThan`), doing `try/except` integer casting (`int()`) on strings inside the sort comparison loop turns into an $O(N \log N)$ bottleneck, as it gets called continuously for every single comparison during sorting.
**Action:** Always pre-calculate and lazily cache typed versions of strings for sorting directly inside the data models (like `LogEntry.index_num`) instead of doing it inline within the `lessThan` function. Add a fallback exception handler for `TypeError` when dealing with heterogeneously parsed columns.
