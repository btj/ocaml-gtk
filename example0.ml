let () =
  let app = Gtk.Application._new "org.gtk.example" Gio.ApplicationFlags.flags_none  in
  ignore @@ Gio.Application.signal_connect_activate app begin fun () ->
    let window = Gtk.ApplicationWindow._new app in
    Gtk.Window.set_title window "Window";
    Gtk.Window.set_default_size window 200 200;
    Gtk.Widget.show window
  end;
  let status = Gio.Application.run app Sys.argv in
  exit status
