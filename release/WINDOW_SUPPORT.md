# Window frame verification

The custom frame uses Windows non-client hit testing for resizing, caption dragging and the maximize button. The maximize region returns HTMAXBUTTON, as required by Microsoft's Snap Layout guidance: https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/ui/apply-snap-layout-menu . This implementation does not by itself prove that the flyout appears under every Windows configuration.

Settings includes a standard Windows title-bar fallback, applied after restarting Luma. It preserves the document and editor functionality.

## Current evidence

17 October 2026: real Qt Windows platform on Windows build 26200, one HP 24f monitor, 1920×1080 at 100% scaling. A Windows message probe returned HTMAXBUTTON (9) at the maximize button. Maximized geometry was 0,0,1920,1080, contained within the monitor-reported available area. Local raw evidence is in the private verification directory. The available area equalled the full display, so this does not verify a visible taskbar configuration.

Automated checks cover corner hit regions, disabling resize hits while maximized, the standard-frame fallback, existing custom resize minimum bounds, and theme/editor regressions.

Desktop follow-up: maximize and restore clicks visibly changed between 1340×880 and the full display. Alt+Space displayed the Windows system menu with Restore, Move, Size, Minimise, Maximise and Close. Alt+F4 closed the isolated verification window. The capture exposed only a clipped portion of a Snap-style flyout; full layout selection remains unverified. The desktop check also exposed a hidden ordinary-text pane after Markdown Split view; this was corrected and covered by a regression test. The editor/release subset passed 26 tests after that correction.

## Pending verification

- Select a Windows 11 Snap layout and verify the resulting bounds. The full hover flyout is now visually confirmed.
- Verify caption drag/snap and additional keyboard controls on the desktop; maximize/restore, Alt+Space and Alt+F4 passed.
- Verify visible taskbar bounds and auto-hide behavior.
- Verify 125%, 150% and 200% scaling and mixed-scale monitor movement.
- Verify monitor disconnection, negative monitor coordinates and restore visibility.

Phase 3 remains in progress until its required desktop checks pass. Unsupported test configurations must remain explicitly unverified in release notes.

18 October desktop follow-up after unlock: the complete Windows Snap Layouts flyout appeared over the maximized custom frame at 1920x1080. A layout-selection click was blocked by desktop automation because the transient PopupHost belongs to Explorer and was not exposed in the selectable window inventory. No alternate input route was used. Escape dismissed the flyout and Alt+F4 closed the isolated Luma window. Layout selection remains unverified.
