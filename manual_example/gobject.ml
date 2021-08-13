type -'a obj
external signal_connect: [>] obj -> string -> 'a -> int = "ml_GObject_signal_connect"
  [@@alert unsafe]
