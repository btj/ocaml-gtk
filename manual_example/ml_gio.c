#include <gtk/gtk.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include "ml_gobject.h"

CAMLprim value ml_Gio_Application_run(value application, value argvValue) {
  CAMLparam2(application, argvValue);
  int argc = Wosize_val(argvValue);
  const char **argv = malloc(argc * sizeof(char *));
  if (argv == 0) abort();
  for (int i = 0; i < argc; i++)
    argv[i] = String_val(Field(argvValue, i));

  int result = g_application_run(GObject_val(application), argc, (char **)(void *)argv); // FIXME: discarding the const qualifier

  free(argv);
  CAMLreturn(Val_int(result));
}
