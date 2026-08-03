stumpwm-d77 installs Daniel's config as the system-wide default at
/etc/stumpwmrc. StumpWM only reads /etc/stumpwmrc when neither ~/.stumpwmrc
nor ~/.stumpwm.d/init.lisp exists, so if you have either of those they take
priority over the packaged config.

The contrib modules used by the config (end-session, swm-gaps, cpu, mem,
net, wifi, battery-portable) are vendored at
/usr/share/stumpwm-d77/modules/, pinned to stumpwm-contrib commit
78b574de489fa4a4c156d15a55ac991739a9c58f. StumpWM rescans that directory on
every startup, so no ~/.stumpwm.d/modules setup is required.

The keybindings reference "brave-browser-stable" (C-t b) and "emacs" (C-t e),
neither of which is a dependency of this package. Install them separately if
you want those bindings to do something; otherwise "exec" just fails
silently.

wallhaven-8xk6oo.png (the startup wallpaper) is installed as an example to
/usr/share/examples/stumpwm-d77/Wallpaper/ for a fresh machine that doesn't
already have it in ~/Wallpaper:

  $ mkdir -p ~/Wallpaper && cp /usr/share/examples/stumpwm-d77/Wallpaper/* ~/Wallpaper/

A "StumpWM (d77)" entry is now available in your display manager's session
list.
