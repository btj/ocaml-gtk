#include <stdlib.h>
#include <stdio.h>
#include <gtk/gtk.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/callback.h>
#include "ml_gobject.h"

void void_signal_handler(GObject *self, value *callbackCell) {
  caml_callback(*callbackCell, Val_unit);
}

void dispose_signal_handler(void *callbackCell, GClosure *closure) {
  caml_remove_global_root(callbackCell);
  free(callbackCell);
}

CAMLprim value ml_GObject_signal_connect(value instance, value signal, value callback) {
  CAMLparam3(instance, signal, callback);

  value *callbackCell = malloc(sizeof(value));
  if (callbackCell == 0) abort();
  *callbackCell = callback;

  caml_register_global_root(callbackCell);

  gulong id = g_signal_connect_data(
      GObject_val(instance),
      "activate", // String_val(signal)
      G_CALLBACK(void_signal_handler),
      callbackCell,
      dispose_signal_handler,
      0);

  if (id > LONG_MAX)
    abort();
  CAMLreturn(Val_long(id));
}
