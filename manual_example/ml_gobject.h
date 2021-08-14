#ifndef ML_GOBJECT_H
#define ML_GOBJECT_H

#define GObject_val(v) (*((void **)Data_custom_val(v)))

value ml_GObject_signal_connect(value instance, const char *signal, void *c_handler, value callback);

#endif
