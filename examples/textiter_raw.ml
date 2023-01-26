let () =
  let app = Gtk.Application_._new "org.gtk.example" Gio.ApplicationFlags.flags_none  in
  ignore @@ Gio.Application_.signal_connect_activate app begin fun () ->

    let window = Gtk.ApplicationWindow_._new app in
    Gtk.Window_.set_title window "Window";
    Gtk.Window_.set_default_size window 200 200;

    let textView = Gtk.TextView_._new () in
    let textBuffer = Gtk.TextView_.get_buffer textView in (* TODO: Check safety: get_buffer does not increment the reference count on the buffer! *)
    Gtk.TextBuffer_.set_text textBuffer "Hello, world!";
    let startIter = Gtk.TextIter_.alloc_uninit_UNSAFE () in
    Gtk.TextBuffer_.get_start_iter textBuffer startIter;
    let iter = Gtk.TextIter_.alloc_uninit_UNSAFE () in
    Gtk.TextIter_.assign iter startIter;
    ignore @@ Gtk.TextIter_.forward_chars iter 5; (* After "Hello" *)
    Gtk.TextBuffer_.delete textBuffer startIter iter;
    Gtk.TextBuffer_.insert_markup textBuffer startIter "<span color=\"blue\">Bye</span>";

    Gtk.Window_.set_child window textView;
    let _ = Gtk.Window_.signal_connect_close_request window (fun () -> exit 0) in
    Gtk.Widget_.show window
  end;
  let status = Gio.Application_.run app Sys.argv in
  exit status
