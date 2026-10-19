---
name: hidden-feature-gate
description: Blocking pre-upload check for App Review guideline 2.5.19 (no hidden, dormant or undocumented features). Use before any App Store or TestFlight upload, `asc builds upload`, `asc review submit`, Xcode archive upload or release prep, and whenever someone plans to "hide a feature behind a flag" in a release build.
---

# Hidden-feature gate (App Review 2.5.19)

Apple's App Review Guidelines (updated 16 October 2026) say:

> 2.5.19 Don't include any hidden, dormant, or undocumented features in your app; your app's functionality should be clear to end users and App Review. Attempting to hide undocumented features in your app binary, such as through code obfuscation or other methods, is grounds for removal of your app from the App Store and termination of your developer account.

The risk isn't only a rejection: it's the developer account. Leftover test switches in a release build count, even when no user can reach them.

## The rule for release builds

- Launch arguments, environment switches, and demo, mock, screenshot, unlock and test modes live only inside `#if DEBUG` or a test target.
- An unreleased feature is left out of the App Store target. It is never shipped switched off behind a flag or a remote config.
- Every user-visible feature is described in the App Store metadata or the Notes for Review (guideline 2.3.1 asks for new features "with specificity").
- A visible, documented demo mode is fine (for example a "Try a demo" button on the welcome screen). An invisible one isn't.

## Run the gate

Run these from the app's repository root. `SKILL_DIR` is the folder that contains this file.

1. Source scan (pass each app source folder; repeat `--source`):

   ```bash
   python3 "$SKILL_DIR/scripts/gate.py" --source Sources
   ```

2. Binary scan, on the archive or app you are about to upload. It scans the main executable and every Mach-O file in the bundle, including debug dylibs, frameworks and extensions:

   ```bash
   python3 "$SKILL_DIR/scripts/gate.py" --binary path/to/App.xcarchive
   ```

3. The script exits 0 (PASS), 1 (FAIL) or 2 (usage error), and prints every hit with `file:line` or the matched string. **A FAIL blocks the upload.** Don't upload or submit until it passes, or until each remaining hit is explained in writing as a documented, user-visible feature or an Apple or third-party framework symbol.
4. Keep the PASS output (or the written explanations) in the release notes or report. Note that `asc validate` and App Store Connect validation check metadata and packaging; they don't look for hidden switches in the binary.

## What it looks for

- **Source:** `ProcessInfo.processInfo.arguments` / `environment` reads and `UserDefaults` keys named like debug, demo, mock, unlock, screenshot, hidden or secret, outside `#if DEBUG`. It also flags identifiers containing Demo, Mock, Unlock, ScreenshotsMode, DebugMenu, HiddenFeature or SecretMenu, outside test folders and `#if DEBUG`. It skips `Tests/`, `UITests/`, `.build/`, `build/`, `DerivedData/` and `Preview Content/`.
- **Binary:** `strings` on every Mach-O file, looking for launch-argument style flags (`-xyzDemo`, `--app-offline-…`, `-openSomething`, `-skipX`, `-forceX`, `-seedX`, `-bypassX`, `-fakeX`), `Mock`/`Unlock` purchase names, debug menus, screenshot modes, and `localhost` / `127.0.0.1` URLs.

## Reading the results

False positives happen: a game role called "Demon", a Face ID "Unlock" button the user sees, `debugDescription` from the Swift standard library. Write one line per hit saying why it's fine, and keep that with the release record. **Never silence the gate by renaming a switch.** Renaming to dodge a scanner is exactly what the guideline calls hiding.

## Keeping switches out of release builds

```swift
#if DEBUG
// Screenshot and demo switches exist only in Debug builds.
if ProcessInfo.processInfo.arguments.contains("-screenshotMode") {
    model.loadScreenshotFixture()
}
#endif
```

For a feature that isn't ready, keep it out of the release target (a separate target, a Debug-only file, or an unmerged branch) rather than a release-build flag that is off.
