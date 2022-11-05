all: example0.ml.exe example0_oo.ml.exe

Gtk-4.0.xml:
	PREFIX=${PREFIX:-/usr/local}
	# g-ir-generate and typelibs provided by package gobject-introspection
	g-ir-generate -o GLib-2.0.xml ${PREFIX}/lib/girepository-1.0/GLib-2.0.typelib
	g-ir-generate -o GObject-2.0.xml ${PREFIX}/lib/girepository-1.0/GObject-2.0.typelib
	g-ir-generate -o Gio-2.0.xml ${PREFIX}/lib/girepository-1.0/Gio-2.0.typelib
	g-ir-generate -o Gdk-4.0.xml ${PREFIX}/lib/girepository-1.0/Gdk-4.0.typelib
	g-ir-generate -o Gtk-4.0.xml ${PREFIX}/lib/girepository-1.0/Gtk-4.0.typelib

Gtk.ml: Gtk-4.0.xml
	python3 generate_bindings.py

example0.ml.exe: example0.ml Gtk.ml
	ocamlopt.opt -g -verbose -o example0.ml.exe \
		-ccopt "-Wno-deprecated-declarations `pkg-config --libs --cflags gtk4 gtk4-unix-print gio-unix-2.0`" \
		gobject0.ml ml_GLib.c GLib.ml ml_gobject0.c ml_GObject.c GObject.ml ml_Gio.c Gio.ml ml_Gdk.c Gdk.ml ml_Gtk.c Gtk.ml example0.ml
#		-cclib "`pkg-config --libs gtk4 gio-unix-2.0`" \

example0_oo.ml.exe: example0_oo.ml Gtk.ml
	ocamlopt.opt -g -o example0_oo.ml.exe -ccopt "-Wno-deprecated-declarations `pkg-config --libs --cflags gtk4 gtk4-unix-print gio-unix-2.0`" \
		gobject0.ml ml_GLib.c GLib.ml ml_gobject0.c ml_GObject.c GObject.ml ml_Gio.c Gio.ml ml_Gdk.c Gdk.ml ml_Gtk.c Gtk.ml example0_oo.ml
#		-cclib "`pkg-config --libs gtk4 gio-unix-2.0`" \

clean:
	-rm ml_GLib.c GLib.ml ml_GObject.c GObject.ml ml_Gio.c Gio.ml ml_Gdk.c Gdk.ml ml_Gtk.c Gtk.ml
