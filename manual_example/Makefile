all: example0.ml.exe example0_oo.ml.exe

example0.ml.exe: example0.ml
	ocamlopt.opt -g -o example0.ml.exe -ccopt "-g -fno-inline-functions `pkg-config --cflags gtk4` `pkg-config --libs gtk4`" ml_gobject.c gobject.ml ml_gio.c gio.ml ml_gtk.c gtk.ml example0.ml

example0_oo.ml.exe: example0.ml
	ocamlopt.opt -g -o example0_oo.ml.exe -ccopt "-g -fno-inline-functions `pkg-config --cflags gtk4` `pkg-config --libs gtk4`" ml_gobject.c gobject.ml ml_gio.c gio.ml ml_gtk.c gtk.ml example0_oo.ml

example0.c.exe: example0.c
	gcc `pkg-config --cflags gtk4` -o example0.c.exe example0.c `pkg-config --libs gtk4`

clean:
	-rm *.o *.cm* *.exe
