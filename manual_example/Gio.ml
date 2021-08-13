[@@@alert "-unsafe"]

open Gobject

type application = [`GApplication] obj

module Application_ = struct
  module ApplicationFlags = struct
    let _NONE = 0
  end
  let signal_connect_activate (instance: [>`GApplication] obj) (callback: unit -> unit): int = signal_connect instance "activate" callback
  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"
end
