# Extra apps (not part of the automated build)

These are FAP source snapshots kept for reference / manual builds only.
They are **not** discovered by fbt (this directory is outside
`applications_user/`), so they cost zero CI build time and zero firmware
flash space — they don't ship in any release automatically.

To build and install one yourself:

```
cp -r extra_apps/<app> flipper-fw/applications_user/<app>
cd flipper-fw && ./fbt fap_<app>
# then copy the resulting .fap from dist/ onto the Flipper's SD card
```

## car_breaker19

Flipper Zero RKE threat monitor (Honda rolling-code anomaly / static-key
regression detection). Source: https://github.com/fbettag/car_breaker_19

Pulled out of the automated build on 2026-09-10 — it's an
`apptype=FlipperAppType.EXTERNAL` FAP, so it was never actually linked into
`firmware.dfu` (it shipped in `resources.ths` / the SD-card bundle), meaning
building it in CI never helped the flash-budget size check that was failing
at the time. Kept here rather than dropped outright so it's still easy to
build and flash manually.
