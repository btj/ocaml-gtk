#include <gtk/gtk.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/custom.h>
#include "ml_gobject.h"

void finalize_GObject(value v) {
  g_object_unref(GObject_val(v));
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
  value result = caml_alloc_custom(&GObject_custom_operations, sizeof(GObject *), 1, 100);
  // Do 1 full GC per 100 allocations.
  GObject_val(result) = obj;
  return result;
}

CAMLprim value ml_Gtk_Application_new(value application_id_value, value flags) {
  CAMLparam2(application_id_value, flags);

  const char *application_id = application_id_value == Val_int(0) ? NULL : String_val(Field(application_id_value, 0));
  GtkApplication *result = gtk_application_new(application_id, Int_val(flags));

  CAMLreturn(Val_GObject(&result->parent_instance.parent_instance));
}

CAMLprim value ml_Gtk_Widget_show(value widget) {
  CAMLparam1(widget);

  gtk_widget_show(GObject_val(widget));

  CAMLreturn(Val_unit);
}

CAMLprim value ml_Gtk_Window_set_title(value window, value title) {
  CAMLparam2(window, title);

  gtk_window_set_title(GObject_val(window), String_val(title));

  CAMLreturn(Val_unit);
}

CAMLprim value ml_Gtk_Window_set_default_size(value window, value width, value height) {
  CAMLparam3(window, width, height);

  gtk_window_set_default_size(GObject_val(window), Int_val(width), Int_val(height));

  CAMLreturn(Val_unit);
}

CAMLprim value ml_Gtk_ApplicationWindow_new(value application) {
  CAMLparam1(application);

  GtkWidget *result = gtk_application_window_new(GObject_val(application));

  CAMLreturn(Val_GObject(&result->parent_instance));
}
