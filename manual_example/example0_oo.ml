let () =
  let app = Gtk.Application._new (Some "org.gtk.example") [`NONE] in
  ignore @@ app#signal_connect_activate begin fun _ ->
    let window = Gtk.ApplicationWindow._new app in
    window#set_title "Window";
    window#set_default_size 200 200;
    window#show
  end;
  let status = app#run Sys.argv in
  exit status
