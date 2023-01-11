let () =
  let app = Gtk.application "org.gtk.example" Gio.ApplicationFlags.flags_none in
  ignore @@ app#signal_connect_activate begin fun () ->
    let window = Gtk.application_window app in
    window#set_title "Window";
    window#set_default_size 200 200;
    window#show;

    let pack = Gtk.box Gtk.Orientation.vertical 0 in
    let button = Gtk.Button.new_with_label "+" in
    let label = Gtk.label "1" in
    pack#append (label :> Gtk.widget);
    pack#append (button :> Gtk.widget);
    window#set_child (pack :> Gtk.widget);
    ignore @@ button#signal_connect_clicked (fun () -> begin
      let text = label#get_label in
      let i = int_of_string text in
      label#set_label @@ string_of_int (i + 1);
      let t = match button#get_label with
      | Some s -> s ^ "+"
      | None -> "*"
      in
      button#set_label t
    end);
  end;
  let status = app#run Sys.argv in
  exit status
