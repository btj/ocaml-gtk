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
    let iter = textBuffer#get_start_iter in
    ignore @@ iter#forward_chars 5;
    textBuffer#delete textBuffer#get_start_iter iter;
    textBuffer#insert_markup iter "<span color=\"blue\">Bye</span>" (-1);

    let tag = Gtk.text_tag "red" in
    tag#set_foreground "red";
    tag#set_editable false;
    tag#set_weight 900; (* https://docs.gtk.org/Pango/enum.Weight.html *)
    tag#set_line_height 3.0;
    tag#set_scale 1.5;
    ignore @@ textBuffer#get_tag_table#add tag;
    textBuffer#apply_tag tag iter textBuffer#get_end_iter;

    window#set_child (textView :> Gtk.widget);
  end;
  let status = app#run Sys.argv in
  exit status
