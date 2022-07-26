[@@@alert "-unsafe"]

open Gobject

type application_ = [`GApplication] obj

module ApplicationFlags = struct
  let _NONE = 0
end

type application_flags = [`NONE] list

module Application_ = struct
  let upcast: [>`GApplication] obj -> application_ = Obj.magic
  external signal_connect_activate: [>`GApplication] obj -> (unit -> unit) -> int = "ml_Gio_Application_signal_connect_activate"
  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"
end

class application (self: application_) =
  object
    method as_GApplication: application_ = self
    method signal_connect_activate callback = Application_.signal_connect_activate self callback
    method run argv = Application_.run self argv
  end

