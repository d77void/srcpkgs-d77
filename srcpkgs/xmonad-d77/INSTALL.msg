xmonad-d77 ships a self-contained /usr/bin/xmonad with Daniel's config
compiled in, so nothing needs to be copied to make the window manager itself
work. Example configs are installed to /usr/share/examples/xmonad-d77/:

  xmobar/     -> copy to ~/.config/xmobar
  Wallpaper/  -> contains wallhaven-3lkqy9.png, copy to ~/Wallpaper

  $ cp -r /usr/share/examples/xmonad-d77/xmobar ~/.config/
  $ mkdir -p ~/Wallpaper && cp /usr/share/examples/xmonad-d77/Wallpaper/* ~/Wallpaper/

An "XMonad (d77)" entry is now available in your display manager's session
list.

The startup hook also spawns "vicinae server", which is not a dependency of
this package (it comes from the personal d77void-repo). Install it separately
if you want it, otherwise that spawnOnce simply does nothing.
