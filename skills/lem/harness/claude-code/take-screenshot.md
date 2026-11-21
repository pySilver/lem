# Claude Code: take-screenshot

A part of `../claude-code.md`, read when an agent takes a picture of the product.

## take-screenshot

A page: headless Chrome with a throwaway profile, which is removed after the picture. On macOS Chrome
needs `--use-mock-keychain` and a `--user-data-dir` of its own, or it asks the login keychain and
writes into the owner's profile. A desktop picture is one call:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --use-mock-keychain \
  --user-data-dir="$(mktemp -d)" --hide-scrollbars --window-size=1440,900 --force-device-scale-factor=2 \
  --screenshot=media/NAME-after.png URL
```

A phone, a dark scheme, a click before the picture or a part of a page take the DevTools protocol:
`Emulation.setDeviceMetricsOverride` (390 x 844, `deviceScaleFactor` 2, `mobile` true),
`Emulation.setTouchEmulationEnabled`, `Emulation.setEmulatedMedia` with `prefers-color-scheme`,
`Page.navigate`, then `Page.captureScreenshot`. Lem's own `tests/board-cdp.mjs` is such a driver in
Node, with the steps as JSON; a project with Playwright or another driver of its own uses that. Both
ways were checked on 2026-11-20 with Chrome 157.0.8103.51 and Node 26.9.0 on macOS: the call above
wrote a 2560 x 1600 picture, and the driver a 780 x 1688 one of a phone. A screen that is no web page
(a native window, a terminal) has no way checked here: say in one line that no picture was taken, and
why.
