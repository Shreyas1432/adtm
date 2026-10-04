# ADTM — Design System

> UI design tokens, layout guidelines, and component styling for the ADTM
> frontend (React 18 + TypeScript + Vite; MUI as the locked component library per
> [`CLAUDE.md`](../CLAUDE.md)). **Last updated:** 2026-10-04.
>
> **Current state:** the Phase-0 shell ([`frontend/src/App.tsx`](../frontend/src/App.tsx))
> is plain React with inline styles and the brand navy `#1E2761`. Phase 1 adopts
> MUI and the tokens below. This document is the target; migrate the shell to it.

---

## 1. Principles

ADTM is an **operator tool for a regulated, high-trust migration** — not a
consumer app. The UI should be:

1. **Evidence-first** — counts, checksums, versions, and approval state are always
   visible; nothing important is hidden behind hover.
2. **Calm & dense** — operators scan tables of jobs/rules/mappings; favour clear
   data density over decoration.
3. **Auditable** — every destructive or approving action is explicit, labelled, and
   confirmable (maps to the hash-chained audit log).
4. **Accessible** — WCAG 2.1 AA: ≥4.5:1 text contrast, visible focus, full keyboard
   operation, never colour-only status.
5. **Deterministic** — the UI reflects versioned config; it never implies AI runs at
   execution time.

## 2. Design tokens

Define as CSS custom properties on `:root` and feed into the MUI theme. These are
the source of truth; components reference tokens, never raw hex.

### 2.1 Color — brand
| Token | Value | Use |
|---|---|---|
| `--color-brand-900` | `#141A45` | darkest navy, headers on light |
| `--color-brand-800` | `#1E2761` | **primary brand navy** (current `App.tsx` H1) |
| `--color-brand-600` | `#2E3A8C` | primary action hover |
| `--color-brand-500` | `#3B49B5` | primary action / links |
| `--color-brand-200` | `#C7CCEC` | selected row, subtle fill |
| `--color-brand-50`  | `#EEF0FB` | hover row, tinted surfaces |

### 2.2 Color — neutrals
| Token | Value | Use |
|---|---|---|
| `--color-ink-900` | `#14161C` | primary text |
| `--color-ink-700` | `#3A3F4B` | secondary text |
| `--color-ink-500` | `#555B66` | muted text (matches current `#555`) |
| `--color-line`    | `#E2E5EA` | borders, dividers |
| `--color-surface` | `#FFFFFF` | cards, tables |
| `--color-bg`      | `#F7F8FA` | app background |

### 2.3 Color — semantic status
Map directly to run/job/DQ/reconciliation states; always pair colour with an icon + label.
| Token | Value | Meaning |
|---|---|---|
| `--color-success` | `#1E7F4F` | succeeded · passed · reconciled |
| `--color-warning` | `#B06A00` | partial success · needs review · unmatched |
| `--color-danger`  | `#B3261E` | failed · DQ violation · chain broken |
| `--color-info`    | `#2E3A8C` | running · submitted · informational |
| `--color-neutral` | `#6B7280` | pending · draft · disabled |

Status → token: `pending→neutral`, `running/submitted→info`,
`succeeded/passed→success`, `partial/unmatched→warning`, `failed→danger`.

### 2.4 Typography
| Token | Value |
|---|---|
| `--font-sans` | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (matches current shell) |
| `--font-mono` | `"SF Mono", "JetBrains Mono", ui-monospace, monospace` — SQL, hashes, ids, counts |
| Scale | `--fs-xs 12 · --fs-sm 14 · --fs-md 16 (base) · --fs-lg 20 · --fs-xl 28 · --fs-2xl 36` (px) |
| Weights | 400 body · 500 labels/table headers · 700 headings |
| Line height | 1.5 body · 1.2 headings |

Use `--font-mono` for anything an operator must read character-exact: SQL,
sha256, UUIDs, row counts, idempotency/version ids.

### 2.5 Spacing, radius, elevation
- **Spacing scale (px):** `4 · 8 · 12 · 16 · 24 · 32 · 48` — tokens `--space-1…7`.
  Base page padding `32` (matches current shell).
- **Radius:** `--radius-sm 4` (inputs, chips) · `--radius-md 8` (cards) · `--radius-lg 12` (dialogs).
- **Elevation:** flat by default; `--shadow-1 0 1px 2px rgba(20,22,28,.08)` for cards;
  `--shadow-2 0 8px 24px rgba(20,22,28,.16)` for dialogs/menus only.

### 2.6 Example `:root`
```css
:root{
  --color-brand-800:#1E2761; --color-brand-500:#3B49B5; --color-brand-50:#EEF0FB;
  --color-ink-900:#14161C; --color-ink-500:#555B66; --color-line:#E2E5EA;
  --color-bg:#F7F8FA; --color-surface:#FFFFFF;
  --color-success:#1E7F4F; --color-warning:#B06A00; --color-danger:#B3261E; --color-info:#2E3A8C;
  --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --font-mono:"SF Mono","JetBrains Mono",ui-monospace,monospace;
  --space-4:16px; --radius-md:8px;
}
```

## 3. Layout guidelines

- **App frame:** left **nav rail** (Connections · Extraction · DQ · Mapping · Load ·
  Reconciliation · Audit) + top bar (workspace switcher, user/role, environment badge).
- **Content width:** work surfaces are full-width for tables; prose/forms cap at
  `820px` (matches the current shell `maxWidth`). Page gutter `24–32px`, `16px` on mobile.
- **Grid:** 12-column, `16px` gutters; one primary object per screen.
- **Density:** compact tables (row height `40px`), 8px vertical rhythm.
- **Primary/secondary actions:** primary action top-right of the work surface;
  destructive/approving actions are never the default focus.
- **Responsive:** desktop-first (operator tool); collapse the nav rail to icons below
  `1024px`; stack table toolbars below `768px`. No horizontal page scroll.
- **Empty/loading/error:** every data surface defines all three states (the shell's
  `checking… / api unreachable` pattern generalises to skeleton / toast / inline error).

## 4. Component styling

Built on **MUI**; override via the theme so tokens drive everything.

| Component | Guidance |
|---|---|
| **Button** | Primary = brand-500 fill / white text; hover brand-600. Secondary = outlined brand-500. Destructive = danger outline, requires confirm dialog. One primary per view. |
| **StatusChip** | Small chip: semantic background tint + darker text + icon + text label. Never colour-only. |
| **DataTable** | Header weight 500, `--color-line` bottom border, zebra via `--color-brand-50` hover, row-select via `--color-brand-200`. Mono font for id/count/hash columns. Sticky header. |
| **Form field** | 14px label (weight 500) above control; helper text `--color-ink-500`; error text `--color-danger` + aria-describedby. Radius-sm. |
| **SQL editor** | Mono font, line numbers, read-only diff view for versioned extraction. |
| **Card / Panel** | `--color-surface`, `--color-line` border, radius-md, `--shadow-1`, `--space-4` padding. |
| **Dialog** | For approvals, replays, and destructive actions. State the exact effect + object id in the body; explicit confirm label (“Approve mapping”, “Replay 42 failed records”). radius-lg, shadow-2. |
| **EvidenceBlock** | Read-only mono panel for reconciliation counts, control totals, sha256, and audit-chain verification result. |
| **Banner/Toast** | Info/success/warning/danger using semantic tokens; persistent banner for environment (“Production — source read-only”). |

### Status pattern (icon + colour + label)
```
● succeeded (success)   ◐ running (info)   ◇ pending (neutral)
⚠ partial  (warning)   ✕ failed (danger)   ⚠ chain broken (danger)
```

## 5. Accessibility checklist
- Text contrast ≥ 4.5:1 (brand-800 on white ≈ 12:1 ✓; verify brand-500 on white for small text).
- Visible focus ring on every interactive element (2px brand-500 outline).
- All actions keyboard-reachable; dialogs trap focus and restore it on close.
- Status conveyed by icon + text, never colour alone.
- Form errors programmatically associated (`aria-describedby`), not colour-only.

## 6. Do / don't
- **Do** keep SQL, hashes, counts, and ids in the mono font.
- **Do** show version + approval state next to any config the user acts on.
- **Don't** introduce gradients, marketing imagery, or decorative animation.
- **Don't** imply AI is live at runtime — AI surfaces are clearly labelled
  “suggestion (design-time)” and gated behind human approval.
- **Don't** hardcode hex in components — reference tokens / theme.
