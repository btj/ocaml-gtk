[@@@alert "-unsafe"]

open Gobject

type application = [`GApplication] obj

module ApplicationFlags = struct
  let _NONE = 0
end

module Application_ = struct
  external signal_connect_activate: [>`GApplication] obj -> (unit -> unit) -> int = "ml_Gio_Application_signal_connect_activate"
  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"
end
