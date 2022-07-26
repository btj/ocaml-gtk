[@@@alert "-unsafe"]

open Gobject

type application_ = [`GtkApplication|`GApplication] obj
type application_window_ = [`GtkApplicationWindow|`GtkWindow|`GtkWidget] obj
type widget_ = [`GtkWidget] obj
type window_ = [`GtkWindow|`GtkWidget] obj

module Application_ = struct
  let upcast: [>`GtkApplication] obj -> application_ = Obj.magic
  external _new: string option -> Gio.application_flags -> application_ = "ml_Gtk_Application_new"
end

module Widget_ = struct
  let upcast: [>`GtkWidget] obj -> widget_ = Obj.magic
  external show: [>`GtkWidget] obj -> unit = "ml_Gtk_Widget_show"
end

module Window_ = struct
  let upcast: [>`GtkWindow] obj -> window_ = Obj.magic
  external set_title: [>`GtkWindow] obj -> string -> unit = "ml_Gtk_Window_set_title"
  external set_default_size: [>`GtkWindow] obj -> int -> int -> unit = "ml_Gtk_Window_set_default_size"
end

module ApplicationWindow_ = struct
  external _new: [>`GtkApplication] obj -> application_window_ = "ml_Gtk_ApplicationWindow_new"
end

class application (self: application_) =
  object
    inherit Gio.application (Gio.Application_.upcast self)
    method as_GtkApplication: application_ = self
  end
and widget (self: widget_) =
  object
    method show = Widget_.show self
  end
and window (self: window_) =
  object
    inherit widget (Widget_.upcast self)
    method set_title title = Window_.set_title self title
    method set_default_size width height = Window_.set_default_size self width height
  end
and application_window (self: application_window_) =
  object
    inherit window (Window_.upcast self)
  end

module Application = struct
  let _new title flags = new application (Application_._new title flags)
end

module Widget = struct
end

module Window = struct
end

module ApplicationWindow = struct
  let _new app = new application_window (ApplicationWindow_._new app#as_GtkApplication)
end
