# ocaml-gtk

Experimental bindings to GTK 4.0 for OCaml.

## Status

Generates direct OCaml C bindings using GObject introspection data

* No enumeration / constants mapping
* No inline docs
* Currently, impact on binary size is significant: `example0.exe`, a trivial hello-world example, is 4.7M on my Macbook. It is not yet clear whether it will be feasible to improve this significantly. See https://github.com/btj/ocaml-gtk/issues/11.

## Prerequisites

* Requires gtk-4 with its development files installed, and the GObject Introspection utilities (g-ir-generate).
* Python 3 (used to convert the GObject introspection files to ML and C code)
* OCaml: opam switch with dune installed

### Ubuntu

On Ubuntu 22.04.1, these system packages are required:

* libgtk-4-dev
* gobject-introspection
* gir1.2-glib-2.0
* gir1.2-gtk-4.0
* python3-minimal
* libpython3.10-stdlib

## Compiling

1. Set the PREFIX variable to the location where girepository-1.0 typelibs are installed
    - if using Ubuntu packages on x86-64, this is `/usr/lib/x86_64-linux-gnu`
    - if using Linux Brew, this is `/home/linuxbrew/.linuxbrew/lib`
2. Run `dune build`
3. Built example programme can be found at `_build/default/examples/example0.exe`

