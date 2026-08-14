## 2024-05-15 - ARIA Labels for Icon Buttons
**Learning:** Found several icon-only buttons (like those in settings dialog or find bar) missing proper accessible names, which breaks screen reader support. PySide6 provides `setAccessibleName()` for this exact purpose.
**Action:** Add `setAccessibleName()` to icon-only buttons to ensure keyboard/screen-reader accessibility.
## 2024-08-14 - PySide6 Toolbar Accessibility
**Learning:** In PySide6, `QAction` objects do not have an `accessibleName` property natively. Setting accessibility attributes for toolbar actions requires retrieving the underlying `QToolButton` widget using `toolbar.widgetForAction(action)`.
**Action:** When adding accessible names to toolbars in PySide/Qt, loop over actions, get the widget via `widgetForAction`, and apply `setAccessibleName()` there.
