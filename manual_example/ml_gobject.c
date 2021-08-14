#include <stdlib.h>
#include <stdio.h>
#include <gtk/gtk.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/callback.h>
#include "ml_gobject.h"

void dispose_signal_handler(void *callbackCell, GClosure *closure) {
  caml_remove_global_root(callbackCell);
  free(callbackCell);
}

value ml_GObject_signal_connect(value instance, const char *signal, void *c_handler, value callback) {
  CAMLparam2(instance, callback);

  value *callbackCell = malloc(sizeof(value));
  if (callbackCell == 0) abort();
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
