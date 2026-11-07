# EpochPlatformEngine release notes

## 0.2.2 — local unpublished candidate

- Default unselected frame pacing to 30 Hz; retain explicit finite rates, VSync
  and uncapped selection. Each limiter turn offers at most one cooperative yield.
- Record precise attachment refusal stages and native errors. Skip already-correct
  native attribute writes; reconcile error 87 only for verified changed style
  postconditions, preserving identity/readback checks and other refusals.
- Apply sibling/descendant clipping to admitted child attachments and restore
  their exact original styles on retirement.

Standalone Debug/Release static/shared/module builds and CPU contracts pass.
Native attachment, desktop responsiveness and exact-package acceptance remain
separate; no release or runtime success is claimed from these checks.

## 0.1.1

## DPI contract

- The Win32 driver now sizes the initial native window using the system DPI instead of a hard-coded 96 DPI.
- Every new Win32 context emits an initial `dpi_changed` event before normal frame processing.
- `dpi_changed` explicitly reports horizontal and vertical DPI in `WindowEvent::width` and `WindowEvent::height`.
- Existing per-monitor `WM_DPICHANGED` handling and suggested-window repositioning remain intact.

This allows renderer and GUI libraries to resolve logical font sizes correctly on the first frame, including 125%, 150%, 175%, and 200% Windows scaling.
