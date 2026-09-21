# Required `common/shlibs` entries

The templates in this repository build against libraries that are **not**
in upstream void-packages' `common/shlibs`, or that are provided by packages
of this repository instead of the official ones. `xbps-src` uses
`common/shlibs` to map a library SONAME to the package that provides it; if an
entry is missing, building anything that links against that library fails
with an error like:

```
=> ERROR: hyprland-0.56.2_2: cannot guess dependency for SONAME libhyprutils.so.13
```

So, **before building any template from this repository, add the lines below
to `common/shlibs` in your void-packages checkout.**

## Entries

Directly needed by `hyprland` (repository `hypr-d77`):

```
libaquamarine.so.14 aquamarine-0.15.1_1
libhyprcursor.so.0 hyprcursor-0.1.13_1
libhyprgraphics.so.4 hyprgraphics-0.5.1_2
libhyprlang.so.2 hyprlang-0.6.8_5
libhyprutils.so.13 hyprutils-0.14.2_1
libhyprwire.so.3 hyprwire-0.3.1_1
liblua5.5.so.5.5 lua55-5.5.0_1
libtomlplusplus.so.3 tomlplusplus-3.4.0_1
```

Needed by the rest of the Hyprland ecosystem (`hyprpaper`, `hyprland-guiutils`,
`hyprlauncher`, `hyprpwcenter`, `hyprshutdown`, `hyprsysteminfo`,
`hyprpolkitagent`; repository `hypr-d77`):

```
libhyprtoolkit.so.6 hyprtoolkit-0.6.0_1
```

Needed by `mango` (repository `d77`):

```
libscenefx-0.5.so scenefx-0.5_1
```

## Apply them (idempotent)

Run from the root of your void-packages checkout. It replaces the line if the
SONAME is already listed, and appends it otherwise:

```sh
while read -r lib pkg; do
    if grep -q "^${lib} " common/shlibs; then
        sed -i "s|^${lib} .*|${lib} ${pkg}|" common/shlibs
    else
        echo "${lib} ${pkg}" >> common/shlibs
    fi
done <<'EOF'
libaquamarine.so.14 aquamarine-0.15.1_1
libhyprcursor.so.0 hyprcursor-0.1.13_1
libhyprgraphics.so.4 hyprgraphics-0.5.1_2
libhyprlang.so.2 hyprlang-0.6.8_5
libhyprutils.so.13 hyprutils-0.14.2_1
libhyprwire.so.3 hyprwire-0.3.1_1
libhyprtoolkit.so.6 hyprtoolkit-0.6.0_1
liblua5.5.so.5.5 lua55-5.5.0_1
libtomlplusplus.so.3 tomlplusplus-3.4.0_1
libscenefx-0.5.so scenefx-0.5_1
EOF
```

Check the result with:

```sh
grep -E '^(libaquamarine|libhypr|liblua5.5|libtomlplusplus|libscenefx)' common/shlibs
```

The same file is used for glibc and musl builds; nothing extra is needed for
musl.

## Keeping them up to date

- The version in a `shlibs` line is the **minimum** version xbps will require
  at runtime (`hyprutils>=0.14.2_1`). Bumping it is optional for a normal
  update.
- When a package's SONAME changes, `xbps-src` refuses to package it and prints
  the exact line to use (`please update common/shlibs with this line: ...`) and
  the list of reverse dependencies that must be revbumped and rebuilt. Update
  the line and revbump those templates. Example: `hyprtoolkit` 0.5.4 -> 0.6.0
  changed `libhyprtoolkit.so.5` to `libhyprtoolkit.so.6`.
- Whenever you update one of the templates listed above, re-check this file
  (the `libaquamarine`, `libhypr*` and `libscenefx` entries follow the
  versions in `hyprland/*/template` and `srcpkgs/scenefx/template`).

## Notes

- `libinput.so.10`: `hyprland` links against the patched `libinput-hypr`, which
  provides the same SONAME as the stock `libinput`. `common/shlibs` keeps
  mapping it to the stock package, which is fine because `hyprland` declares
  `depends="libinput-hypr"` explicitly. No shlibs change is needed.
- `libsdbus-c++.so.2` (used by `hyprlock`, `hypridle`,
  `xdg-desktop-portal-hyprland`, `hyprpolkitagent`): upstream already lists it
  (`sdbus-c++`); `sdbus-cpp` from this repository provides the same SONAME.
  No shlibs change is needed.
- `glaze` and `hyprland-protocols` are header-only/data packages and provide no
  shared library.
