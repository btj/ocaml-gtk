let () =
  let app = Gtk.Application_._new (Some "org.gtk.example") Gio.Application_.ApplicationFlags._NONE in
  ignore @@ Gio.Application_.signal_connect_activate app begin fun _ ->
    let window = Gtk.ApplicationWindow_._new app in
    Gtk.Window_.set_title window "Window";
    Gtk.Window_.set_default_size window 200 200;
    Gtk.Widget_.show window
  end;
  let status = Gio.Application_.run app Sys.argv in
  exit status
