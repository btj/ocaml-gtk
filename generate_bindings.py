import xml.etree.ElementTree as ET
import itertools

c_functions_to_skip = {'g_io_module_load', 'g_io_module_unload'} # https://gitlab.gnome.org/GNOME/glib/-/issues/2498

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
t_member = "{http://www.gtk.org/introspection/core/1.0}member"

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

c_keywords = {
        'value'
}

def escape_c_keyword(name):
    return '_' + name if name in c_keywords else name

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
        self.ml_name = self.name.lower().capitalize()
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
        self.ml_name0 = escape_ml_keyword(pascal_case_to_snake_case(self.name))
        self.ml_name = self.ml_name0 + '_'
        self.qualified_name = ns.name + '.' + self.name
        c_type_name = xml.attrib.get(a_type_name, None)
        self.c_type_name = 'GParamSpec' if c_type_name == 'GParam' else c_type_name
    
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
    ml('open Gobject0')
    ml()
    cf('#define G_SETTINGS_ENABLE_BACKEND')
    cf('#include <gio/gsettingsbackend.h>')
    cf('#include <gio/gunixconnection.h>')
    cf('#include <gio/gunixcredentialsmessage.h>')
    cf('#include <gio/gunixfdlist.h>')
    cf('#include <gio/gunixfdmessage.h>')
    cf('#include <gio/gunixinputstream.h>')
    cf('#include <gio/gunixmounts.h>')
    cf('#include <gio/gunixoutputstream.h>')
    cf('#include <gio/gunixsocketaddress.h>')
    cf('#include <gtk/gtk.h>')
    cf('#include <gtk/gtkunixprint.h>')
    cf('#define CAML_NAME_SPACE')
    cf('#include <caml/mlvalues.h>')
    cf('#include <caml/memory.h>')
    cf('#include <caml/callback.h>')
    cf('#include <caml/alloc.h>')
    cf('#include <caml/fail.h>')
    cf('#include "ml_gobject0.h"')
    ns = Namespace(env, namespace)
    local_env = ns.local_env
    namespaces[namespace_name] = ns
    for ns_elem_name, ns_elem in ns.elems.items():
        if ns_elem.xml.tag != t_class:
            continue
        ancestors = []
        ancestor = ns_elem
        ns_elem.is_GObject = False
        while True:
            ancestors.append(ancestor)
            parent_name = ancestor.xml.attrib.get('parent', None)
            ancestor.parent_name = parent_name
            if ancestor.qualified_name == "GObject.Object": # or ancestor.qualified_name == "GObject.InitiallyUnowned":
                ancestor.parent = None
                ns_elem.is_GObject = True
                break
            if parent_name is None:
                ancestor.parent = None
                print('Warning: while determining ancestry of class %s: class %s has no parent' % (ns_elem_name, ancestor.qualified_name))
                break
            ancestor0 = ancestor
            ancestor = ancestor.ns.local_env.get(parent_name, None)
            ancestor0.parent = ancestor
            if ancestor is None:
                print('Warning: incomplete ancestry of class %s due to unknown ancestor %s' % (ns_elem_name, parent_name))
                break
        if ns_elem.is_GObject:
            ml('type %s = [%s] obj' % (ns_elem.ml_name,
                '|'.join('`' + a.c_type_name for a in ancestors)))
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
            elif ns_elem.xml.tag == t_class and ns_elem.is_GObject:
                c_type = ns_elem.c_type_name
                return ('[>`%s] obj' % c_type, 'GObject_val(%s)', 'void *') # '%s *' % c_type
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
            elif ns_elem.xml.tag == t_class and ns_elem.is_GObject:
                return (("" if ns_elem.ns is ns else ns_elem.ns.name.capitalize() + '.') + ns_elem.ml_name, 'Val_GObject((void *)(%s))', 'void *') # '%s *' % ns_elem.c_type_name)
            else:
                return None
        else:
            return None
    class Class:
        def __init__(self, parent):
            self.parent = parent
            self.lines = []
            self.printed = False
    classes = {}
    ctors_lines = []
    def ctl(line):
        ctors_lines.append(line)
    for ns_elem in namespace:
        if ns_elem.tag == t_bitfield:
            ml()
            ml('module %s_ = struct' % ns_elem.attrib['name'])
            for bf_elem in ns_elem:
                if bf_elem.tag == t_member:
                    ml('  let %s = %s' % (escape_ml_keyword(bf_elem.attrib['name']), bf_elem.attrib['value']))
            ml('end')
        if ns_elem.tag == t_class:
            nse = local_env[ns_elem.attrib['name']]
            if not nse.is_GObject:
                continue
            class_ = Class(None if nse.parent is None else nse.parent.ml_name0 if nse.parent.ns is nse.ns else None)
            classes[nse.ml_name0] = class_
            def cl(line):
                class_.lines.append(line)
            c_type_name = nse.c_type_name
            ml()
            ml('module %s_ = struct' % ns_elem.attrib['name'])
            ml('  let upcast: [>`%s] obj -> %s = Obj.magic' % (c_type_name, nse.ml_name))
            cl('%s (self: %s) =' % (nse.ml_name0, nse.ml_name))
            cl('  object')
            if nse.parent_name is not None:
                qualifier = '' if nse.parent.ns is nse.ns else nse.parent.ns.ml_name + '.'
                cl('    inherit %s (%s.upcast self)' % (qualifier + nse.parent.ml_name0, qualifier + nse.parent.name + '_'))
            cl('  end')
            ctl('')
            ctl('module %s = struct' % ns_elem.attrib['name'])
            for c_elem in ns_elem:
                if c_elem.tag == t_attribute:
                    pass
                elif c_elem.tag == t_constructor or c_elem.tag == t_method:
                    c_elem_tag = 'constructor' if c_elem.tag == t_constructor else 'method'
                    params = [('instance_', ('[>`%s] obj' % c_type_name, 'GObject_val(%s)', '%s *' % c_type_name))] if c_elem_tag == 'method' else []
                    throws = c_elem.attrib.get('throws', None) == '1'
                    result = None
                    skip = False
                    for m_elem in c_elem:
                        if m_elem.tag == t_parameters:
                            for ps_elem in m_elem:
                                assert ps_elem.tag == t_parameter
                                if ps_elem.attrib.get('transfer-ownership', None) != 'none':
                                    print('Skipping %s %s of class %s: missing transfer-ownership="none" attribute for parameter %s' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name'], ps_elem.attrib['name']))
                                    skip = True
                                    continue
                                if 'direction' in ps_elem.attrib:
                                    print('Skipping %s %s of class %s: explicit "direction" attribute for parameter %s not yet supported' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name'], ps_elem.attrib['name']))
                                    skip = True
                                    continue
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
                                params.append((escape_c_keyword(ps_elem.attrib['name']), types, escape_ml_keyword(ps_elem.attrib['name'])))
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
                    if len(params) > 5:
                        # Skip for now; requires separate C functions for the bytecode runtime and the native code runtime
                        print('Skipping %s %s of class %s: has more than 5 parameters' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name']))
                        skip = True
                    if c_elem.attrib[a_identifier] in c_functions_to_skip:
                        skip = True
                    if not skip:
                        if c_elem_tag == 'constructor':
                            expected_result = (nse.ml_name, 'Val_GObject((void *)(%s))', 'void *')
                            if result != expected_result:
                                if result[0] != 'widget' and result[0] != 'Gtk.widget':
                                    print('Warning: return type of constructor %s of class %s does not match class or GtkWidget' % (c_elem.attrib['name'], ns.name + '.' + ns_elem.attrib['name']))
                                result = expected_result
                        cfunc = 'ml_%s_%s_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_elem.attrib['name'])
                        mlfunc = escape_ml_keyword(c_elem.attrib['name'])
                        ml('  external %s: %s -> %s = "%s"' % (mlfunc, "unit" if params == [] else " -> ".join(p[1][0] for p in params), result[0], cfunc))
                        if c_elem_tag == 'constructor':
                            params_text = ' '.join(p[2] for p in params) if params != [] else '()'
                            ctl('  let %s %s = new %s (%s_.%s %s)' % (mlfunc, params_text, nse.ml_name0, nse.name, mlfunc, params_text))
                        cf()
                        cf('CAMLprim value %s(%s) {' % (cfunc, ', '.join('value %s' % p[0] for p in params)))
                        params1 = params[:5]
                        params2 = params[5:]
                        cf('  CAMLparam%d(%s);' % (len(params1), ', '.join(p[0] for p in params1)))
                        while params2 != []:
                            params2_1 = params2[:5]
                            params2 = params2[5:]
                            cf('  CAMLxparam%d(%s);' % (len(params2_1), ', '.join(p[0] for p in params2_1)))
                        if throws:
                            cf('  CAMLlocal1(exn_msg);');
                            cf('  GError *err = NULL;')
                        args = ', '.join([p[1][1] % p[0] for p in params] + (['&err'] if throws else []))
                        call = '%s(%s)' % (c_elem.attrib[a_identifier], args)
                        if result[0] == 'unit':
                            cf('  %s;' % call)
                            ml_result = 'Val_unit'
                        else:
                            cf('  %s result = %s;' % (result[2], call))
                            ml_result = result[1] % 'result'
                        if throws:
                            cf('  if (err) { exn_msg = caml_copy_string(err->message); g_error_free(err); caml_failwith_value(exn_msg); }')
                        cf('  CAMLreturn(%s);' % ml_result)
                        cf('}')
                    elif ns.name == 'Gio' and ns_elem.attrib['name'] == 'Application' and c_elem.attrib['name'] == 'run':
                        ml('  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"')
                        cf('''
CAMLprim value ml_Gio_Application_run(value application, value argvValue) {
  CAMLparam2(application, argvValue);
  int argc = Wosize_val(argvValue);
  char **argv = malloc(argc * sizeof(char *));
  if (argv == 0) abort();
  for (int i = 0; i < argc; i++)
    argv[i] = strdup(String_val(Field(argvValue, i)));

  callbacks_allowed = true;
  int result = g_application_run(GObject_val(application), argc, argv);
  callbacks_allowed = false;

  for (int i = 0; i < argc; i++)
    free(argv[i]);
  free(argv);
  CAMLreturn(Val_int(result));
}
''')
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
                                params.append((escape_c_keyword(ps_elem.attrib['name']), types))
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
                        ml('  external signal_connect_%s: [>`%s] obj -> (%s -> %s) -> int = "%s"' % (c_name, nse.c_type_name, "unit" if params == [] else " -> ".join(p[1][0] for p in params), result[0], cfunc))
                        cf()
                        cf('%s %s(GObject *instance_, %svalue *callbackCell) {' % (result[2], handlerfunc, ''.join('%s %s, ' % (p[1][2], p[0]) for p in params)))
                        cf('  CAMLparam0();')
                        nb_args = max(1, len(params))
                        cf('  CAMLlocalN(args, %d);' % nb_args)
                        cf('  if (!callbacks_allowed) abort();')
                        cf('  callbacks_allowed = false;')
                        callback_args = ['Val_unit'] if params == [] else [p[1][1] % p[0] for p in params]
                        for i in range(nb_args):
                            cf('  args[%d] = %s;' % (i, callback_args[i]))
                        result_decl, result_conv, return_stmt = (';', '%s', 'CAMLreturn0;') if result[0] == 'unit' else ('%s result = ' % result[2], result[1], 'CAMLreturnT(%s, result);' % result[2])
                        callback = 'caml_callbackN(*callbackCell, %d, args)' % nb_args
                        cf('  %s%s;' % (result_decl, result_conv % callback))
                        cf('  callbacks_allowed = true;')
                        cf('  %s' % return_stmt)
                        cf('}')
                        cf()
                        cf('CAMLprim value %s(value instance_, value callback) {' % cfunc)
                        cf('  return ml_GObject_signal_connect(instance_, "%s", %s, callback);' % (c_elem.attrib['name'], handlerfunc))
                        cf('}')
            ml('end')
            ctl('end')
    ml()
    is_first_class = True
    def print_class(class_):
        nonlocal is_first_class
        if not class_.printed:
            class_.printed = True
            if class_.parent is not None:
                print_class(classes[class_.parent])
            if is_first_class:
                ml('class ' + class_.lines[0])
                is_first_class = False
            else:
                ml('and ' + class_.lines[0])
            for line in itertools.islice(class_.lines, 1, None):
                ml(line)
    for class_ in classes.values():
        print_class(class_)
    ml()
    for line in ctors_lines:
        ml(line)

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
