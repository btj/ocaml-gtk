all: example0.ml.exe example0_oo.ml.exe

Gtk-4.0.xml:
	# g-ir-generate and typelibs provided by package gobject-introspection
	g-ir-generate -o GLib-2.0.xml /usr/local/lib/girepository-1.0/GLib-2.0.typelib
	g-ir-generate -o GObject-2.0.xml /usr/local/lib/girepository-1.0/GObject-2.0.typelib
	g-ir-generate -o Gio-2.0.xml /usr/local/lib/girepository-1.0/Gio-2.0.typelib
	g-ir-generate -o Gdk-4.0.xml /usr/local/lib/girepository-1.0/Gdk-4.0.typelib
	g-ir-generate -o Gtk-4.0.xml /usr/local/lib/girepository-1.0/Gtk-4.0.typelib

Gtk.ml: Gtk-4.0.xml
	python3 generate_bindings.py

example0.ml.exe: example0.ml Gtk.ml
	ocamlopt.opt -g -o example0.ml.exe -ccopt "-Wno-deprecated-declarations `pkg-config --cflags gtk4 gtk4-unix-print`" -cclib "`pkg-config --libs gtk4`" gobject0.ml ml_glib.c glib.ml ml_gobject0.c ml_gobject.c gobject.ml ml_gio.c gio.ml ml_gdk.c gdk.ml ml_gtk.c gtk.ml example0.ml

example0_oo.ml.exe: example0_oo.ml Gtk.ml
	ocamlopt.opt -g -o example0_oo.ml.exe -ccopt "-Wno-deprecated-declarations `pkg-config --cflags gtk4 gtk4-unix-print`" -cclib "`pkg-config --libs gtk4`" gobject0.ml ml_glib.c glib.ml ml_gobject0.c ml_gobject.c gobject.ml ml_gio.c gio.ml ml_gdk.c gdk.ml ml_gtk.c gtk.ml example0_oo.ml

clean:
	-rm ml_glib.c glib.ml ml_gobject.c gobject.ml ml_gio.c gio.ml ml_gdk.c gdk.ml ml_gtk.c gtk.ml
