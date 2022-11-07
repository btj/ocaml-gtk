let () =
  let app = Gtk.Application_._new "org.gtk.example" Gio.ApplicationFlags.flags_none  in
  ignore @@ Gio.Application_.signal_connect_activate app begin fun () ->

    let window = Gtk.ApplicationWindow_._new app in
    Gtk.Window_.set_title window "Window";
    Gtk.Window_.set_default_size window 200 200;

    let pack = Gtk.Box_._new 0 0 in
    Gtk.Widget_.set_margin_start pack 10;
    Gtk.Widget_.set_margin_end pack 10;
    Gtk.Widget_.set_margin_top pack 10;
    Gtk.Widget_.set_margin_bottom pack 10;

    let button = Gtk.Button_._new () in
    let _ = Gtk.Button_.signal_connect_clicked button (fun () -> print_endline "CLICKED!") in
    Gtk.Button_.set_label button "Hello";
    Gtk.Widget_.set_hexpand button true;

    Gtk.Box_.append pack button;
    Gtk.Window_.set_child window pack;
    let _ = Gtk.Window_.signal_connect_close_request window (fun () -> exit 0) in
    Gtk.Widget_.show window
  end;
  let status = Gio.Application_.run app Sys.argv in
  exit status
