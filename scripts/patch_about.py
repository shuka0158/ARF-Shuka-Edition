#!/usr/bin/env python3
"""
Patch about.c to add a Shuka-ARF attribution screen.

ARF's about.c uses a const AboutDialogScreen about_screens[] array of function
pointers. We inject a new shuka_info_screen() function and prepend it to the array.
"""

import sys, os, glob, re

GUARD = "shuka_attribution_patched"

CANDIDATES = [
    "flipper-fw/applications/settings/about/about.c",
    "flipper-fw/applications/about/about.c",
    "flipper-fw/applications/main/about/about.c",
]

path = next((c for c in CANDIDATES if os.path.exists(c)), None)
if not path:
    hits = glob.glob("flipper-fw/**/about.c", recursive=True)
    path = hits[0] if hits else None

if not path:
    print("WARNING: about.c not found — skipping attribution patch", file=sys.stderr)
    sys.exit(0)

print(f"Patching: {path}")

with open(path) as f:
    src = f.read()

if GUARD in src:
    print("Already patched — skipping")
    sys.exit(0)

# ── Fix firmware name in the ARF info screen header ──────────────────────────
# ARF uses "ARF Firmware\n" (space, not hyphen) — the sed in build.yml only
# replaces "ARF-Firmware" (hyphen), so we fix it here too.
src = src.replace('"ARF Firmware\\n"', '"Shuka-ARF\\n"')
src = src.replace('"ARF-Firmware\\n"', '"Shuka-ARF\\n"')

# ── New screen function to inject ─────────────────────────────────────────────
NEW_FUNC = '''\
static DialogMessageButton shuka_info_screen(DialogsApp* dialogs, DialogMessage* message) {
    DialogMessageButton result;

    const char* screen_header = "Shuka-ARF";
    const char* screen_text = "Built by Heisenberg\\n"
                              "[shuka0158]\\n"
                              "github.com/shuka0158/\\n"
                              "ARF-Shuka-Edition";

    dialog_message_set_header(message, screen_header, 0, 0, AlignLeft, AlignTop);
    dialog_message_set_text(message, screen_text, 0, 11, AlignLeft, AlignTop);
    result = dialog_message_show(dialogs, message);
    dialog_message_set_header(message, NULL, 0, 0, AlignLeft, AlignTop);
    dialog_message_set_text(message, NULL, 0, 0, AlignLeft, AlignTop);

    return result;
}

'''

# ── Strategy: find the about_screens[] array and inject ──────────────────────
# Matches:  const AboutDialogScreen about_screens[] = {
#               screen_fn1,
#               ...
#           };
array_pat = re.compile(
    r'(const\s+AboutDialogScreen\s+about_screens\s*\[\s*\]\s*=\s*\{)',
    re.DOTALL
)

m = array_pat.search(src)
if m:
    insert_pos = m.start()
    # Inject function before the array, then prepend entry inside array
    src = src[:insert_pos] + NEW_FUNC + src[insert_pos:]

    # Now add shuka_info_screen as the first entry in the array
    src = re.sub(
        r'(const\s+AboutDialogScreen\s+about_screens\s*\[\s*\]\s*=\s*\{)',
        r'\1\n    shuka_info_screen,',
        src
    )
    print("Patched: injected shuka_info_screen into about_screens[]")
else:
    print("WARNING: about_screens[] array not found in about.c — attribution not added", file=sys.stderr)
    print("  File:", path, file=sys.stderr)
    sys.exit(0)

src = f"// {GUARD}\n" + src

with open(path, "w") as f:
    f.write(src)

print(f"about.c attribution patch applied OK ({path})")
