## 2024-05-18 - Delegate Paint Loop Bottleneck
**Learning:** In Qt/PySide6 architectures, the `paint()` method of a `QStyledItemDelegate` is a critical hot path, executed for every visible item during scrolling or data changes. Performing expensive operations like `re.compile()` within this loop causes noticeable UI lag. Python caches compiled regexes, but the dictionary lookup and function call still add significant overhead when called hundreds of times per second.
**Action:** When creating custom Qt delegates that rely on regular expressions or other heavy computations, pre-calculate or compile these resources in setter methods (e.g., `set_term()`) and store them as instance variables, rather than computing them dynamically inside `paint()`.

## 2024-05-18 - Filter Matching Inner Loop Optimizaton
**Learning:** In highly frequent data filtering operations running on large arrays of complex objects (like PySide models sorting and filtering logs), repeating string manipulations (like `lower()`) and list lookups (O(n) on small level arrays) per object per loop causes measurable performance hits over time.
**Action:** When creating search or filter logic inside tight loops, aggressively leverage sets for O(1) membership testing and rely on lazy-evaluation caching (such as `LogEntry.raw_lower`) or pre-calculate query inputs once outside the iteration loop.

## 2024-05-18 - Delegate Document Instantiation Bottleneck
**Learning:** Instantiating `QTextDocument` and `QTextCharFormat` objects dynamically inside the `paint()` method of a `QStyledItemDelegate` is a major performance bottleneck during list/table scrolling in PySide6. The `paint()` method is invoked extremely frequently, causing thousands of unnecessary memory allocations which induce UI jank.
**Action:** Always pre-instantiate heavy Qt objects like `QTextDocument` and `QTextCharFormat` as instance variables in the delegate's `__init__` method. Inside `paint()`, reuse these objects by simply updating their state (e.g., `doc.setPlainText(text)` or `doc.setDefaultFont()`) to drastically reduce rendering overhead.
