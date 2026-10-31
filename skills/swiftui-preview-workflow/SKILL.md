---
name: swiftui-preview-workflow
description: Use when adding, rendering, or visually inspecting SwiftUI previews across Apple-platform apps, especially when previews lack fixtures or Xcode has multiple open workspaces.
---

# SwiftUI Preview Workflow

Render the actual view with isolated sample state; a preview is visual evidence, not proof of a working user flow.

1. Identify the project, active scheme, platform, minimum OS, existing previews, and the screen to inspect. Preserve existing work and follow repository ownership rules.
2. Prefer an existing `#Preview`. If none represents the requested state, add a minimal named preview next to the view. Inject deterministic sample data and an in-memory SwiftData container when required; do not use real user data, credentials, network calls, or device cameras.
3. Discover open Xcode workspaces and explicitly target the checkout under review. Use Xcode MCP's RenderPreview. If the convenience renderer cannot pass `workspaceIdentifier` in a multi-workspace/headless session, call the underlying `RenderPreview` tool with that identifier and the project-organized source path. Never silently render a different checkout.
4. Read the rendered image. Check clipping, overlapping controls, text legibility, and empty/populated states. Use supported preview variants to check Dynamic Type, appearance, and device/window sizes as relevant. Report exact failures or unavailable variants; do not claim a visual pass from a path or build alone.
5. Build the affected scheme and run focused behavior tests when applicable. A preview does not verify navigation, permissions, camera, or persistence: use a separately authorized simulator/device flow for those.
6. Report source path, checkout, state, destination, rendered image, build/test evidence, limitations, and uncommitted changes. Do not publish screenshots or change release configuration without approval.

Apple reference: https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files
