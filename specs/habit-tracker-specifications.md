Habit Tracker — Specification

Purpose

- Replace the repository's Hello World page with a monthly habit-tracking feature composed of:
  1. An editable, scrollable table (rows = habits, columns = days of the selected month) with per-day markers, and
  2. A synced calendar view that maps those markers to day cells.

Key rule (icons & identity)

- Each habit is assigned a single icon (shape) and color that is used consistently across every day in the table and calendar. A habit’s identity = {icon, color}. Different habits must use different icon+color combinations to ensure clear, consistent recognition in both the table and the calendar.

Components

1. Editable, scrollable table

- Layout: sticky left column (habit name) and sticky top row (days 1..N for the selected month); body scrolls both axes.
- Columns: day headers labeled with weekday + date.
- Rows: user-created, reorderable habits.
- Cells: square cells (default 36px) with three states: empty, marked (shows the habit’s assigned icon in its assigned color), and editing (temporary overlay for adding a note). When marked, the same icon and color assigned to the habit must be rendered in every marked cell for that habit.
- Icons: consistent per-habit SVG icons (Heart, Diamond, Circle, Square, Star, Triangle, etc.). Icon + color together represent habit identity (necessary for color-blind accessibility). The UI ensures two habits do not share the same icon; color choices should maximize distinctness.
- Editing & interactions: add/rename/delete/reorder habits; choose shape (icon) & color at creation; bulk-mark (drag/shift+click); undo/redo; keyboard navigation (arrow keys, space/enter to toggle, shift+arrow for range select). Context menus for cell-specific actions (note, clear, repeat).
- Performance: virtualization support when row count is large; day columns capped at 31.

2. Calendar view

- Standard month grid synced to the selected month in the table.
- Day cells display the icons of all habits marked for that day. Render up to 4 icons with overflow +N indicator; tooltip or tap expands full list.
- Interactions: clicking a day focuses/highlights the corresponding column in the table; clicking an icon in the calendar focuses that habit’s row and scrolls the table to show the day cell.
- Legend: maps all habit icons+colors to habit names; clicking a legend item toggles visibility or filters for that habit across both views.

Data model

- Habit { id: UUID, name: string, icon: enum, color: string (hex), order: int, created_at: timestamp, updated_at: timestamp }
- Entry { id: UUID, habit_id: UUID, date: DATE (YYYY-MM-DD), done: boolean, note?: string, created_at: timestamp, updated_at: timestamp }
- Business rule: icon+color uniqueness per user; UI enforces when creating or editing habits.

API (REST)

- GET /api/habits -> [{id, name, icon, color, order}]
- POST /api/habits {name, icon?, color?} -> creates habit (assign defaults if not provided)
- PUT /api/habits/:id -> update name, icon, color, order
- DELETE /api/habits/:id -> deletes habit and associated entries (soft-delete option configurable)
- GET /api/entries?month=YYYY-MM -> [{id, habit_id, date, done, note}]
- POST /api/entries {habit_id, date, done, note?} -> create or update entry
- POST /api/entries/bulk {entries: [{habit_id, date, done}]} -> optimize range/bulk updates
- DELETE /api/entries/:id -> remove entry (or support PATCH to set done=false)
  Notes: API returns habit icon+color so client can render consistently. Server validates icon+color uniqueness per user.

Client state & sync

- Cache per-month entries. Use optimistic UI for toggles with background reconciliation. On conflict, show clear UI affordance and allow retry.
- Optional real-time sync via WebSockets/SSE for multi-device updates (v2).

UX & Interaction details

- Route: /habits replaces Hello World route (or root redirects to /habits). Minimal migration notes included in README.
- Two-pane responsive layout (desktop two-column, mobile stacked). Date/month selector controls both views.
- Table interactions:
  - Single click/tap: toggle entry for that habit/date. When marking, render the habit’s icon and color consistently.
  - Shift+click or drag: range selection & marking. Bulk actions call the bulk API for efficiency.
  - Keyboard accessibility: arrows to move focus; Space/Enter toggles; Shift+Arrows to select ranges; Ctrl/Cmd+Z undo.
  - Right-click/context menu: Add note, Clear, Repeat weekly, etc.
- Calendar interactions:
  - Hover/tap to see which habits are marked that day; click an icon to focus that habit row and highlight the corresponding table cells.
  - Tooltip includes habit icon+name+note if present.
- Legend interactions: clicking a habit in the legend filters/highlights across both table and calendar.

Accessibility

- Combined icon + color identity for habits to avoid reliance on color alone.
- All interactive elements (table cells, calendar icons, legend items) include ARIA attributes: role, aria-pressed, aria-label describing "Habit: <name> — <date> — marked/unmarked" and aria-describedby for notes.
- Focus rings and keyboard-only affordances are present. High-contrast theme available; color contrast checked against WCAG.

Wireframes (textual)

- Desktop (two-pane): Top bar [Back] [Month selector ▼] [Add Habit +] [Export] [Profile]
  - Left: Habit Table (sticky header/column). Example row: | ▷ Meditation | □ | ♥ | □ | ♦ | ... |
  - Right: Calendar (month grid) and Legend (icon+color + name list)
- Mobile (stacked): Top: month selector + add; Center: compact calendar or week scroller; Below: habit list with each habit expandable to horizontal day-scroller; Legend available via drawer or FAB.
- Habit Editor modal: Name, Icon picker (grid of icons, shows preview), Color picker (preset palette + custom hex, contrast meter), Order, Default repeat settings.

Visual & implementation notes

- Use SVG icons for crisp scaling; icon size in table cells approx 20px.
- Ensure icon uniqueness: when user picks an icon in editor, the UI either prevents selecting already-used icons or prompts to change the other habit.
- Default assignment: on habit creation, auto-assign the next available icon from a palette and a distinct color.

Acceptance criteria

- Each habit has one icon+color consistently used across all table cells and calendar days.
- Different habits use distinct icon+color combinations.
- Add/rename/delete/reorder habits and choose icon+color; changes persist via API.
- Toggle cells (single & bulk) persist and reflect in calendar; table and calendar remain bi-directionally synced.
- Legend correctly maps icon+color → habit name and toggles visibility.
- Keyboard navigation, screen-reader labels, and mobile layout function correctly.

Testing & validation

- Unit tests for components: HabitTable, HabitCell, CalendarView, Legend, HabitEditor.
- Integration tests for table↔calendar synchronization (simulate toggles, bulk updates, edits).
- E2E: simulate user flows (create habit, mark multiple days, verify calendar markers, mobile interactions).
- Visual snapshot tests for marker rendering with overlapping habits and overflow states.

Files & components (suggested)

- frontend/src/components/HabitTable.{tsx,css}
- frontend/src/components/HabitCell.{tsx,css}
- frontend/src/components/CalendarView.{tsx,css}
- frontend/src/components/Legend.{tsx,css}
- frontend/src/components/HabitEditor.{tsx,css}
- frontend/src/hooks/useHabits.ts (client caching, optimistic updates)
- backend/src/api/habits.py, backend/src/api/entries.py (or equivalent in project stack)
- migrations/xxxx_create_habits_entries.sql

Implementation Plan (10 days condensed)

- Day 1: Create DB migrations, API stubs, route scaffolding, basic wireframe UI.
- Day 2–4: Implement table UI, single-cell toggle persistence, optimistic UI.
- Day 5–6: Implement habit CRUD and editor (icon+color picker), legend UI.
- Day 7–8: Implement calendar view, syncing interactions, and linking to table.
- Day 9: Performance: virtualization, bulk API, mobile layout tweaks.
- Day 10: Accessibility fixes, keyboard nav, tests, replace Hello World route, docs, deploy.

Notes & next steps

- Real-time multi-device sync can be added later via WebSockets/SSE.
- Optionally provide Figma/SVG wireframes for visual handoff.

Contact & review

- Include this specifications.md in the repository root to guide implementation and code review. Update as designs or requirements change.
