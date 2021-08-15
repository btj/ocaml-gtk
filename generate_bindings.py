import xml.etree.ElementTree as ET

t_namespace = "{http://www.gtk.org/introspection/core/1.0}namespace"
t_class = "{http://www.gtk.org/introspection/core/1.0}class"
t_attribute = "{http://www.gtk.org/introspection/core/1.0}attribute"
t_constructor = "{http://www.gtk.org/introspection/core/1.0}constructor"
t_method = "{http://www.gtk.org/introspection/core/1.0}method"
t_parameters = "{http://www.gtk.org/introspection/core/1.0}parameters"
t_parameter = "{http://www.gtk.org/introspection/core/1.0}parameter"
t_return_value = "{http://www.gtk.org/introspection/core/1.0}return-value"
t_type = "{http://www.gtk.org/introspection/core/1.0}type"
t_property = "{http://www.gtk.org/introspection/core/1.0}property"
t_signal = "{http://www.gtk.org/introspection/glib/1.0}signal"
t_enumeration = "{http://www.gtk.org/introspection/core/1.0}enumeration"

a_type_name = "{http://www.gtk.org/introspection/glib/1.0}type-name"
a_identifier = "{http://www.gtk.org/introspection/c/1.0}identifier"

ml_keywords = {
        'and', 'as', 'assert', 'asr', 'begin', 'class',
        'constraint', 'do', 'done', 'downto', 'else', 'end',
        'exception', 'external', 'false', 'for', 'fun', 'function',
        'functor', 'if', 'in', 'include', 'inherit', 'initializer',
        'land', 'lazy', 'let', 'lor', 'lsl', 'lsr',
        'lxor', 'match', 'method', 'mod', 'module', 'mutable',
        'new', 'nonrec', 'object', 'of', 'open', 'or',
        'private', 'rec', 'sig', 'struct', 'then', 'to',
        'true', 'try', 'type', 'val', 'virtual', 'when',
        'while', 'with'
}

def escape_ml_keyword(name):
    return name + '_' if name in ml_keywords else name

def pascal_case_to_snake_case(name):
    result = name[0].lower()
    for i in range(1, len(name)):
        if name[i] <= 'Z':
            result += '_' + name[i].lower()
        else:
            result += name[i]
    return result

def process_namespace(namespace):
    ml_file = open(namespace.attrib['name'] + '.ml', 'w')
    def ml(*args):
        print(*args, file=ml_file)
    c_file = open('ml_' + namespace.attrib['name'] + '.c', 'w')
    def cf(*args):
        print(*args, file=c_file)
    ml('[@@@alert "-unsafe"]')
    ml()
    ml('open Gobject')
    ml()
    cf('#include <gtk/gtk.h>')
    cf('#define CAML_NAME_SPACE')
    cf('#include <caml/mlvalues.h>')
    cf('#include <caml/memory.h>')
    cf('#include <caml/callback.h>')
    cf('#include "ml_gobject.h"')
    classes = {}
    enums = {}
    for elem in namespace:
        if elem.tag == t_class:
            classes[elem.attrib['name']] = elem
        elif elem.tag == t_enumeration:
            enums[elem.attrib['name']] = elem
    for name, elem in classes.items():
        ancestor = name
        ancestors = []
        while ancestor != 'GObject.Object':
            if ancestor not in classes:
                print('Warning: incomplete ancestry of class %s due to unknown ancestor %s' % (name, ancestor))
                break
            ancestors.append(ancestor)
            ancestor = classes[ancestor].attrib['parent']
        ml('type %s = [%s]' % (pascal_case_to_snake_case(name),
            '|'.join(('`' + classes[a].attrib[a_type_name] for a in ancestors))))
    def ml_to_c_type(typ):
        if typ.attrib['name'] in enums:
            return ('int', 'Int_val(%s)', 'int')
        elif typ.attrib['name'] in classes:
            c_type = classes[typ.attrib['name']].attrib[a_type_name]
            return ('[>`%s] obj' % c_type, 'GObject_val(%s)', '%s *' % c_type)
        else:
            return None
    def c_to_ml_type(typ):
        if typ.attrib['name'] in enums:
            return ('int', 'Val_int(%s)', 'int')
        elif typ.attrib['name'] in classes:
            return (pascal_case_to_snake_case(typ.attrib['name']), 'Val_GObject(%s)', '%s *' % classes[typ.attrib['name']].attrib[a_type_name])
        else:
            return None
    for ns_elem in namespace:
        if ns_elem.tag == t_class:
            c_type_name = ns_elem.attrib[a_type_name]
            ml()
            ml('module %s_ = struct' % ns_elem.attrib['name'])
            for c_elem in ns_elem:
                if c_elem.tag == t_attribute:
                    pass
                elif c_elem.tag == t_constructor or c_elem.tag == t_method:
                    c_elem_tag = 'constructor' if c_elem.tag == t_constructor else 'method'
                    params = [('instance', ('[>`%s] obj' % c_type_name, 'GObject_val(%s)', '%s *' % c_type_name))] if c_elem_tag == 'method' else []
                    result = None
                    skip = False
                    for m_elem in c_elem:
                        if m_elem.tag == t_parameters:
                            for ps_elem in m_elem:
                                assert ps_elem.tag == t_parameter
                                typ = None
                                types = None
                                for p_elem in ps_elem:
                                    if p_elem.tag == t_type:
                                        typ = p_elem
                                if typ == None:
                                    print('Skipping %s %s of class %s: no type specified for parameter %s' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name'], ps_elem.attrib['name']))
                                    skip = True
                                    continue
                                types = ml_to_c_type(typ)
                                if types == None:
                                    print('Skipping %s %s of class %s: unsupported type %s of parameter %s' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name'], ET.tostring(typ), ps_elem.attrib['name']))
                                    skip = True
                                    continue
                                params.append((ps_elem.attrib['name'], types))
                        elif m_elem.tag == t_return_value:
                            typ = None
                            types = None
                            for rv_elem in m_elem:
                                if rv_elem.tag == t_type:
                                    typ = rv_elem
                            if typ == None:
                                types = None
                                typ = rv_elem
                            elif typ.attrib['name'] == 'none':
                                types = ('unit', 'Val_unit')
                            else:
                                types = c_to_ml_type(typ)
                            if types == None:
                                print('Skipping %s %s of class %s: unsupported return type %s' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name'], ET.tostring(typ)))
                                skip = True
                            result = types
                    if not skip:
                        cfunc = 'ml_%s_%s_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_elem.attrib['name'])
                        mlfunc = escape_ml_keyword(c_elem.attrib['name'])
                        ml('  external %s: %s -> %s = "%s"' % (mlfunc, "unit" if params == [] else " -> ".join(p[1][0] for p in params), result[0], cfunc))
                        cf()
                        cf('CAMLprim value %s(%s) {' % (cfunc, ', '.join('value %s' % p[0] for p in params)))
                        cf('  CAMLparam%d(%s);' % (len(params), ', '.join(p[0] for p in params)))
                        args = ', '.join(p[1][1] % p[0] for p in params)
                        call = '%s(%s)' % (c_elem.attrib[a_identifier], args)
                        if result[0] == 'unit':
                            cf('  %s;' % call)
                            cf('  CAMLreturn(Val_unit);')
                        else:
                            cf('  CAMLreturn(%s);' % (result[1] % call))
                        cf('}')
                elif c_elem.tag == t_signal:
                    params = []
                    result = None
                    skip = False
                    for s_elem in c_elem:
                        if s_elem.tag == t_parameters:
                            for ps_elem in s_elem:
                                assert ps_elem.tag == t_parameter
                                typ = None
                                types = None
                                for p_elem in ps_elem:
                                    if p_elem.tag == t_type:
                                        typ = p_elem
                                if typ == None:
                                    print('Skipping signal %s of class %s: no type specified for parameter %s' % (c_elem.attrib['name'], ns_elem.attrib['name'], ps_elem.attrib['name']))
                                    skip = True
                                    continue
                                types = c_to_ml_type(typ)
                                if types == None:
                                    print('Skipping signal %s of class %s: unsupported type %s of parameter %s' % (c_elem.attrib['name'], ns_elem.attrib['name'], ET.tostring(typ), ps_elem.attrib['name']))
                                    skip = True
                                    continue
                                params.append((ps_elem.attrib['name'], types))
                        elif s_elem.tag == t_return_value:
                            typ = None
                            types = None
                            for rv_elem in s_elem:
                                if rv_elem.tag == t_type:
                                    typ = rv_elem
                            if typ.attrib['name'] == 'none':
                                types = ('unit', '', 'void')
                            else:
                                types = ml_to_c_type(typ)
                            if types == None:
                                print('Skipping signal %s of class %s: unsupported return type %s' % (c_elem.attrib['name'], ns_elem.attrib['name'], ET.tostring(typ)))
                                skip = True
                            result = types
                    if not skip:
                        handlerfunc = 'ml_%s_%s_signal_handler_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_elem.attrib['name'])
                        cfunc = 'ml_%s_%s_signal_connect_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_elem.attrib['name'])
                        ml('  external signal_connect_%s: [>`%s] -> (%s -> %s) -> int = "%s"' % (c_elem.attrib['name'], ns_elem.attrib[a_type_name], "unit" if params == [] else " -> ".join(p[1][0] for p in params), result[0], cfunc))
                        cf()
                        cf('%s %s(%s) {' % (result[2], handlerfunc, ', '.join('%s %s' % (p[1][2], p[0]) for p in params)))
                        handler_return = '' if result[0] == 'unit' else 'return '
                        callback_args = 'Val_unit' if params == [] else ', '.join(p[1][1] % p[0] for p in params)
                        if len(params) <= 3:
                            cf('  %scaml_callback%s(*callbackCell, %s);' % (handler_return, '' if len(params) <= 1 else str(len(params)), callback_args))
                        else:
                            cf('  value[] args = {%s};' % callback_args)
                            cf('  %scaml_callbackN(*callbackCell, %d, args);' % (handler_return, len(params)))
                        cf('}')
                        cf()
                        cf('CAMLprim value %s(value instance, value callback) {' % cfunc)
                        cf('  return ml_GObject_signal_connect(instance, "%s", %s, callback);' % (c_elem.attrib['name'], handlerfunc))
                        cf('}')
            ml('end')

tree = ET.parse('Gio-2.0.xml')
root = tree.getroot()

for e in root:
    if e.tag == t_namespace:
        process_namespace(e)
    else:
        print('Ignoring "%s" element' % (e.tag,))

