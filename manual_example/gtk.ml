[@@@alert "-unsafe"]

open Gobject

type application = [`GtkApplication|`GApplication] obj
type application_window = [`GtkApplicationWindow|`GtkWindow|`GtkWidget] obj

module Application_ = struct
  let upcast: [>`GtkApplication] obj -> application = Obj.magic
  external _new: string option -> int -> application = "ml_Gtk_Application_new"
end

module Widget_ = struct
  external show: [>`GtkWidget] obj -> unit = "ml_Gtk_Widget_show"
end

module Window_ = struct
  external set_title: [>`GtkWindow] obj -> string -> unit = "ml_Gtk_Window_set_title"
  external set_default_size: [>`GtkWindow] obj -> int -> int -> unit = "ml_Gtk_Window_set_default_size"
end

module ApplicationWindow_ = struct
  external _new: [>`GtkApplication] obj -> application_window = "ml_Gtk_ApplicationWindow_new"
end
