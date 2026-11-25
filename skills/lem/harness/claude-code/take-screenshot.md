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

The call ends on a page that holds a request open, as every page of Lem's board holds its event
stream: on 2026-11-22, with Chrome 157.0.8103.51 on macOS, it wrote the board's "Waits for you" page,
served by `lem serve`, in 3.9 s, with the stream live at the page's foot. Add no
`--virtual-time-budget` to it on such a page: with the budget, the same call on the same page did not
end in 30 s and wrote no picture, and a page of 30 lines with one open `EventSource` did the same. A
page that needs time to draw after its load takes a DevTools driver, as below, with a fixed wait
before the picture.

A phone, a dark scheme, a click before the picture or a part of a page take the DevTools protocol:
`Emulation.setDeviceMetricsOverride` (390 x 844, `deviceScaleFactor` 2, `mobile` true),
`Emulation.setTouchEmulationEnabled`, `Emulation.setEmulatedMedia` with `prefers-color-scheme`,
`Page.navigate`, then `Page.captureScreenshot`. A project with Playwright or another driver of its
own uses that; with none, a short script over the DevTools protocol takes these steps. Both ways were
checked on 2026-11-20 with Chrome 157.0.8103.51 and Node 26.9.0 on macOS: the call above wrote a
2560 x 1600 picture, and a DevTools driver in Node a 780 x 1688 one of a phone. A screen that is no web page
(a native window, a terminal) has no way checked here: say in one line that no picture was taken, and
why.
