#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <gtk/gtk.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/callback.h>
#include <caml/custom.h>
#include <caml/fail.h>
#include "ml_gobject0.h"

bool callbacks_allowed;

void finalize_GObject(value v) {
  int old_callbacks_allowed = callbacks_allowed;
  callbacks_allowed = false;
  g_object_unref(GObject_val(v));
  callbacks_allowed = old_callbacks_allowed;
}

struct custom_operations GObject_custom_operations = {
  "ocaml-gtk/GObject/1",
  finalize_GObject,
  custom_compare_default,
  custom_compare_ext_default,
  custom_hash_default,
  custom_serialize_default,
  custom_deserialize_default,
  0
};

value Val_GObject(GObject *obj) {
  if (g_object_is_floating(obj))
    g_object_ref_sink(obj);

  value result = caml_alloc_custom(&GObject_custom_operations, sizeof(GObject *), 1, 100);
  // Do 1 full GC per 100 allocations.
  GObject_val(result) = obj;
  return result;
}

value Val_string_option(char *s) {
  CAMLparam0();
  CAMLlocal2(ml_s, result);
  if (s) {
    ml_s = caml_copy_string(s);
    result = caml_alloc_some(ml_s);
    CAMLreturn(result);
  } else {
    CAMLreturn(Val_none);
  }
}

void dispose_signal_handler(void *callbackCell, GClosure *closure) {
  caml_remove_global_root(callbackCell);
  free(callbackCell);
}

value ml_GObject_signal_connect(value instance, const char *signal, void *c_handler, value callback) {
  CAMLparam2(instance, callback);

  value *callbackCell = malloc(sizeof(value));
  if (callbackCell == 0) caml_raise_out_of_memory();
  *callbackCell = callback;

  caml_register_global_root(callbackCell);

  gulong id = g_signal_connect_data(
      GObject_val(instance),
      signal,
      G_CALLBACK(c_handler),
      callbackCell,
      dispose_signal_handler,
      0);

  if (id > LONG_MAX)
    abort();
  CAMLreturn(Val_long(id));
}
