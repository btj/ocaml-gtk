let () =
  let app = Gtk.application "org.gtk.example" Gio.ApplicationFlags.flags_none in
  ignore @@ app#signal_connect_activate begin fun () ->
    let window = Gtk.application_window app in
    window#set_title "Window";
    window#set_default_size 200 200;
    window#show;

    let textView = Gtk.text_view () in
    let textBuffer = textView#get_buffer in (* TODO: Check safety: get_buffer does not increment the reference count on the buffer! *)
    textBuffer#set_text "Hello, world!" (-1);
    let startIter = textBuffer#get_start_iter in
    let iter = textBuffer#get_start_iter in
    ignore @@ iter#forward_chars 5;
    textBuffer#delete startIter iter;
    textBuffer#insert_markup startIter "<span color=\"blue\">Bye</span>" (-1);

    window#set_child (textView :> Gtk.widget);
  end;
  let status = app#run Sys.argv in
  exit status
