## 2024-05-15 - ARIA Labels for Icon Buttons
**Learning:** Found several icon-only buttons (like those in settings dialog or find bar) missing proper accessible names, which breaks screen reader support. PySide6 provides `setAccessibleName()` for this exact purpose.
**Action:** Add `setAccessibleName()` to icon-only buttons to ensure keyboard/screen-reader accessibility.

## 2024-05-16 - ARIA Labels for QActions
**Learning:** Found that `QAction` objects do not have an `accessibleName` property. When adding icon-only buttons to a toolbar using `addAction`, you must retrieve the underlying `QToolButton` via `toolbar.widgetForAction(action)` to set its accessible name for screen readers.
**Action:** Always retrieve the generated widget from the toolbar when adding QActions in order to set `accessibleName` on the widget itself.
