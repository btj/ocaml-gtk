let () =
  let app = Gtk.Application._new "org.gtk.example" Gio.ApplicationFlags_.flags_none in
  ignore @@ app#signal_connect_activate begin fun () ->
    let window = Gtk.ApplicationWindow._new app in
    window#set_title "Window";
    window#set_default_size 200 200;
    window#show
  end;
  let status = app#run Sys.argv in
  exit status
