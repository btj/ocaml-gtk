#ifndef ML_GOBJECT_H
#define ML_GOBJECT_H

extern bool callbacks_allowed;

#define GObject_val(v) (*((void **)Data_custom_val(v)))

value Val_GObject(GObject *obj);

value ml_GObject_signal_connect(value instance, const char *signal, void *c_handler, value callback);

value Val_string_option(const char *s);
#endif
