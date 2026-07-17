dankcalendar has no system service (dcal was never meant to run as root --
it needs a real graphical session: DBUS_SESSION_BUS_ADDRESS, XDG_RUNTIME_DIR,
etc). If your shell doesn't already spawn it on demand, start it from your
own session/compositor startup instead, e.g. in niri's config.kdl:

  spawn-at-startup "dcal" "run" "--session" "--hidden"

or the equivalent exec-once/autostart mechanism for your compositor.
