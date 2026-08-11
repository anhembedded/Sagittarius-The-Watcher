## 2024-05-15 - ARIA Labels for Icon Buttons
**Learning:** Found several icon-only buttons (like those in settings dialog or find bar) missing proper accessible names, which breaks screen reader support. PySide6 provides `setAccessibleName()` for this exact purpose.
**Action:** Add `setAccessibleName()` to icon-only buttons to ensure keyboard/screen-reader accessibility.
