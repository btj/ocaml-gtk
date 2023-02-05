let e = epsilon_float

(* For tests that need to be run within an initialised Gtk.application *)
let run_app f =
  let app = Gtk.application "org.gtk.example" Gio.ApplicationFlags.flags_none in
  ignore @@ app#signal_connect_activate f;
  ignore @@ app#run [||]

let int () =
  run_app begin fun () ->
    let p = Gtk.picture () in
    let _ = p#set_margin_start 1 in
    let v = p#get_margin_start in
    Alcotest.(check int) "Set and retrieved gint" v 1
  end

let double () =
  run_app begin fun () ->
    let ps = Gtk.page_setup () in
    let _ = ps#set_left_margin 1.0 1 in
    let margin = ps#get_left_margin 1 in
    Alcotest.(check @@ float e) "Set and retrieved gdouble" margin 1.0
  end

let float () =
  run_app begin fun () ->
    let a = Gtk.aspect_frame 1.0 1.0 1.0 true in
    a#set_xalign 0.5;
    let v = a#get_xalign in
    Alcotest.(check @@ float e) "Set and retrieved gfloat" v 0.5
  end

let string () =
  run_app begin fun () ->
    let label = Gtk.label "hello" in
    let v = label#get_label in
    Alcotest.(check string) "Set and retrieved string" v "hello"
  end

let string_option () =
  run_app begin fun () ->
    let button = Gtk.Button.new_with_label "hello" in
    let v = button#get_label in
    let v = match v with (Some s) -> s | None -> "none" in
    Alcotest.(check string) "Set and retrieved string option" v "hello"
  end

let test_set = [ 
  ("int", `Quick, int);
  ("double", `Quick, double);
  ("float", `Quick, float);
  ("string", `Quick, string);
  ("string_option", `Quick, string_option)
]

let () =
  Alcotest.run "Get and set tests"
    [ ("Tests", test_set) ]
