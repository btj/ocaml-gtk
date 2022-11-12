let () =
  let app = Gtk.application "org.gtk.example" Gio.ApplicationFlags.flags_none in
  ignore @@ app#signal_connect_activate begin fun () ->
    let window = Gtk.application_window app in
    window#set_title "Window";
    window#set_default_size 200 200;
    window#show;

    let pack = Gtk.box Gtk.Orientation.horizontal 0 in
    let button = Gtk.Button.new_with_label "Click Me!" in
    pack#append (button :> Gtk.widget) ;
    window#set_child (pack :> Gtk.widget);
    ignore @@ button#signal_connect_clicked (fun () -> print_endline("I'm clicked"));
  end;
  let status = app#run Sys.argv in
  exit status
