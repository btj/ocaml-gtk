import xml.etree.ElementTree as ET

t_include = "{http://www.gtk.org/introspection/core/1.0}include"
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
t_bitfield = "{http://www.gtk.org/introspection/core/1.0}bitfield"

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
    return '_' + name if name in ml_keywords else name

def pascal_case_to_snake_case(name):
    result = name[0].lower()
    for i in range(1, len(name)):
        if name[i] <= 'Z':
            result += '_' + name[i].lower()
        else:
            result += name[i]
    return result

class Namespace:
    def __init__(self, env, xml):
        self.xml = xml
        self.name = xml.attrib['name']
        ns_elems = {}
        for elem_xml in xml:
            name = elem_xml.attrib.get('name', None)
            if name is not None:
                ns_elem = NamespaceElement(self, elem_xml)
                ns_elems[name] = ns_elem
        self.elems = ns_elems
        self.local_env = env | ns_elems
        self.global_env = env | dict((self.name + '.' + ns_elem_name, ns_elem) for ns_elem_name, ns_elem in ns_elems.items())

class NamespaceElement:
    def __init__(self, ns, xml):
        self.ns = ns
        self.xml = xml
        self.name = xml.attrib['name']
        self.qualified_name = ns.name + '.' + self.name
    
    def qualify_for(self, other_ns):
        if other_ns is self.ns:
            return self.name
        else:
            return self.qualified_name

namespaces = {}

def process_namespace(namespace, env):
    namespace_name = namespace.attrib['name']
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
    ns = Namespace(env, namespace)
    local_env = ns.local_env
    namespaces[namespace_name] = ns
    for ns_elem_name, ns_elem in ns.elems.items():
        if ns_elem.xml.tag != t_class:
            continue
        ancestors = []
        ancestor = ns_elem
        while True:
            if ancestor.qualified_name == "GObject.Object" or ancestor.qualified_name == "GObject.InitiallyUnowned":
                break
            ancestors.append(ancestor)
            parent_name = ancestor.xml.attrib.get('parent', None)
            if parent_name is None:
                print('Warning: while determining ancestry of class %s: class %s has no parent' % (ns_elem_name, ancestor.qualified_name))
                break
            ancestor = ancestor.ns.local_env.get(parent_name, None)
            if ancestor is None:
                print('Warning: incomplete ancestry of class %s due to unknown ancestor %s' % (ns_elem_name, parent_name))
                break
        ml('type %s = [%s]' % (pascal_case_to_snake_case(ns_elem_name),
            '|'.join('`' + a.xml.attrib[a_type_name] for a in ancestors)))
    def ml_to_c_type(typ):
        name = typ.attrib.get('name')
        if name == 'utf8':
            return ('string', 'String_val(%s)', 'const char *')
        elif name == 'gboolean':
            return ('bool', 'Bool_val(%s)', 'gboolean')
        elif name == 'gint32':
            return ('int', 'Long_val(%s)', 'gint32')
        elif name == 'guint32':
            return ('int', 'Long_val(%s)', 'guint32')
        ns_elem = local_env.get(name, None)
        if ns_elem is not None:
            if ns_elem.xml.tag == t_enumeration or ns_elem.xml.tag == t_bitfield:
                return ('int', 'Int_val(%s)', 'int')
            elif ns_elem.xml.tag == t_class:
                c_type = ns_elem.xml.attrib[a_type_name]
                return ('[>`%s] obj' % c_type, 'GObject_val(%s)', '%s *' % c_type)
            else:
                return None
        else:
            return None
    def c_to_ml_type(typ):
        name = typ.attrib['name']
        if name == 'gint32':
            return ('int', 'Val_long(%s)', 'gint32')
        elif name == 'guint32':
            return ('int', 'Val_long(%s)', 'guint32')
        elif name == 'gboolean':
            return ('bool', '(%s ? Val_true : Val_false)', 'gboolean')
        ns_elem = local_env.get(name, None)
        if ns_elem != None:
            if ns_elem.xml.tag == t_enumeration:
                return ('int', 'Val_int(%s)', 'int')
            elif ns_elem.xml.tag == t_class:
                return (("" if ns_elem.ns is ns else ns_elem.ns.name + '.') + pascal_case_to_snake_case(name), 'Val_GObject(%s)', '%s *' % ns_elem.xml.attrib[a_type_name])
            else:
                return None
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
                        if c_elem_tag == 'constructor':
                            expected_result = (pascal_case_to_snake_case(ns_elem.attrib['name']), 'Val_GObject(%s)', '%s *' % c_type_name)
                            if result != expected_result:
                                if result[0] != 'widget' and result[0] != 'Gtk.widget':
                                    print('Warning: return type of constructor %s of class %s does not match class or GtkWidget' % (c_elem.attrib['name'], ns.name + '.' + ns_elem.attrib['name']))
                                result = expected_result
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
                        c_name = c_elem.attrib['name'].replace('-', '_')
                        handlerfunc = 'ml_%s_%s_signal_handler_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_name)
                        cfunc = 'ml_%s_%s_signal_connect_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_name)
                        ml('  external signal_connect_%s: [>`%s] -> (%s -> %s) -> int = "%s"' % (c_name, ns_elem.attrib[a_type_name], "unit" if params == [] else " -> ".join(p[1][0] for p in params), result[0], cfunc))
                        cf()
                        cf('%s %s(%s) {' % (result[2], handlerfunc, ', '.join('%s %s' % (p[1][2], p[0]) for p in params)))
                        cf('  CAMLparam0();')
                        nb_args = max(1, len(params))
                        cf('  CAMLlocalN(args, %d);' % nb_args)
                        cf('  if (!callbacks_allowed) abort();')
                        cf('  callbacks_allowed = false;')
                        callback_args = 'Val_unit' if params == [] else ', '.join(p[1][1] % p[0] for p in params)
                        for i in range(nb_args):
                            cf('  args[%d] = %s;' % (i, callback_args[i]))
                        result_decl, return_stmt = (';', 'CAMLreturn0();') if result[0] == 'unit' else ('%s result = ' % result[2], 'CAMLreturnT(%s, result);' % result[2])
                        callback = 'caml_callbackN(*callbackCell, %d, args)' % nb_args
                        cf('  %s%s;' % (result_decl, callback))
                        cf('  %s' % return_stmt)
                        cf('}')
                        cf()
                        cf('CAMLprim value %s(value instance, value callback) {' % cfunc)
                        cf('  return ml_GObject_signal_connect(instance, "%s", %s, callback);' % (c_elem.attrib['name'], handlerfunc))
                        cf('}')
            ml('end')

def process_root(filepath):
    print('Processing %s...' % filepath)
    tree = ET.parse(filepath)
    root = tree.getroot()

    env = {}
    for e in root:
        if e.tag == t_include:
            name = e.attrib['name']
            ns = namespaces.get(name, None)
            if ns is None:
                print('%s: ignoring include of %s: no such namespace' % (filepath, name))
                continue
            env.update(ns.global_env)
        elif e.tag == t_namespace:
            process_namespace(e, env)
        else:
            print('Ignoring "%s" element' % (e.tag,))

for filepath in ['GLib-2.0.xml', 'GObject-2.0.xml', 'Gio-2.0.xml', 'Gdk-4.0.xml', 'Gtk-4.0.xml']:
    process_root(filepath)
