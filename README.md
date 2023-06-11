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

## Safety

We intend for the following safety property to hold:

Assuming the GObject Introspection data is accurate, an OCaml program that uses the generated bindings (and that does not use unsafe OCaml features such as `Obj.magic`) shall not exhibit undefined behavior, except that:
- record allocation functions such as `Gtk.TextIter_.alloc_uninit_UNSAFE` do not initialize the record's fields; passing such uninitialized records to APIs that expect the record to be initialized is unsafe
- `textBuffer#get_start_iter` and similar APIs do not increment the TextBuffer object's refcount; i.e. a TextIter does not own a reference to a TextBuffer. So the existence of a TextIter `i` does not keep `i#get_buffer` alive. However, if [GNOME/gtk!6087](https://gitlab.gnome.org/GNOME/gtk/-/merge_requests/6087) is merged, using a TextIter after the TextBuffer has been freed will with very large probability either cause a clean segfault or cause an "Invalid text buffer iterator" warning to be printed. (Using `i#get_buffer` in other ways, however, has undefined behavior.)
- Similar issues probably exist with other types of records.

Known violations of this property should be recorded as issues with label `safety`.
