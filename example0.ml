let () =
  let app = Gtk.Application._new "org.gtk.example" Gio.ApplicationFlags.flags_none  in
  ignore @@ Gio.Application.signal_connect_activate app begin fun () ->

    let window = Gtk.ApplicationWindow._new app in
    Gtk.Window.set_title window "Window";
    Gtk.Window.set_default_size window 200 200;

    let pack = Gtk.Box._new 0 0 in
    Gtk.Widget.set_margin_start pack 10;
    Gtk.Widget.set_margin_end pack 10;
    Gtk.Widget.set_margin_top pack 10;
    Gtk.Widget.set_margin_bottom pack 10;

    let button = Gtk.Button._new () in
    let _ = Gtk.Button.signal_connect_clicked button (fun () -> print_endline "CLICKED!") in
    Gtk.Button.set_label button "Hello";
    Gtk.Widget.set_hexpand button true;

    Gtk.Box.append pack button;
    Gtk.Window.set_child window pack;
    let _ = Gtk.Window.signal_connect_close_request window (fun () -> exit 0) in
    Gtk.Widget.show window
  end;
  let status = Gio.Application.run app Sys.argv in
  exit status
