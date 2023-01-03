from dataclasses import dataclass
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

    def ml_name0_for(self, other_ns):
        if other_ns is self.ns:
            return self.ml_name0
        return self.ns.name + '.' + self.ml_name0

@dataclass
class Types:
    ml_type: str
    as_ml_value: str
    c_type: str
    oo_type: str
    unwrap: str

class Param:
    def __init__(self, ps_elem, types):
        name = ps_elem.attrib['name']
        self.c_name = escape_c_keyword(name)
        self.ml_name = escape_ml_keyword(name)
        self.types = types

    @property
    def ml_typed_param(self):
        return '(%s: %s)' % (self.ml_name, self.types.oo_type)

    @property
    def ml_arg(self):
        return self.types.unwrap % self.ml_name

    @property
    def c_value(self):
        return self.types.as_ml_value % self.c_name

class CMethodParam:
    def __init__(self, c_type_name):
        self.c_name = 'instance_'
        self.types = Types('[>`%s] obj' % c_type_name, 'GObject_val(%s)', '%s *' % c_type_name, None, None)
        self.ml_name = None

    @property
    def c_value(self):
        return self.types.as_ml_value % self.c_name

class Params:
    def __init__(self):
        self.params = []

    def append(self, param):
        self.params.append(param)

    def method_types(self):
        if self.params == []:
            return 'unit'
        else:
            return ' -> '.join(p.types.ml_type for p in self.params)

    def signal_types(self):
        if self.params == []:
            return 'unit'
        else:
            return ' -> '.join(p.types.oo_type for p in self.params)

    def ctor_params(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_typed_param for p in self.params)

    def ctor_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_arg for p in self.params)

    def method_params(self):
        return ''.join(' ' + p.ml_typed_param for p in self.params)

    def method_args(self):
        return ''.join(' ' + p.ml_arg for p in self.params)

    def callback_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_name for p in self.params)

    def callback_ret_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join('(%s)' % p.ml_arg for p in self.params)

    def c_callback_args(self):
        if self.params == []:
            return ['Val_unit']
        else:
            return [p.c_value for p in self.params]

    def drop_first(self):
        p = Params()
        p.params = self.params[1:]
        return p

class Class:
    def __init__(self, parent):
        self.parent = parent
        self.lines = []
        self.printed = False

class ClassPrinter:
    def __init__(self, classes, ml):
        self.classes = classes
        self.is_first_class = True
        self.ml = ml

    def print_class(self, class_):
        if not class_.printed:
            class_.printed = True
            if class_.parent is not None:
                self.print_class(self.classes[class_.parent])
            if self.is_first_class:
                self.ml('class ' + class_.lines[0])
                self.is_first_class = False
            else:
                self.ml('and ' + class_.lines[0])
            for line in itertools.islice(class_.lines, 1, None):
                self.ml(line)


_C_HEADERS = '''\
#define G_SETTINGS_ENABLE_BACKEND
#include <gio/gsettingsbackend.h>
#include <gio/gunixconnection.h>
#include <gio/gunixcredentialsmessage.h>
#include <gio/gunixfdlist.h>
#include <gio/gunixfdmessage.h>
#include <gio/gunixinputstream.h>
#include <gio/gunixmounts.h>
#include <gio/gunixoutputstream.h>
#include <gio/gunixsocketaddress.h>
#include <gtk/gtk.h>
#include <gtk/gtkunixprint.h>
#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/callback.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include "ml_gobject0.h"\
'''


_GIO_APPLICATION_RUN = '''
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
'''

def ml_to_c_type(typ, ns, local_env):
    name = typ.attrib.get('name')
    if name == 'utf8':
        return Types('string', 'String_val(%s)', 'const char *', 'string', '%s')
    elif name == 'gboolean':
        return Types('bool', 'Bool_val(%s)', 'gboolean', 'bool', '%s')
    elif name == 'gint32':
        return Types('int', 'Long_val(%s)', 'gint32', 'int', '%s')
    elif name == 'guint32':
        return Types('int', 'Long_val(%s)', 'guint32', 'int', '%s')
    ns_elem = local_env.get(name, None)
    if ns_elem is not None:
        if ns_elem.xml.tag == t_enumeration or ns_elem.xml.tag == t_bitfield:
            return Types('int', 'Int_val(%s)', 'int', 'int', '%s')
        elif ns_elem.xml.tag == t_class and ns_elem.is_GObject:
            c_type = ns_elem.c_type_name
            return Types('[>`%s] obj' % c_type, 'GObject_val(%s)', 'void *', ns_elem.ml_name0_for(ns), '%%s#as_%s' % c_type)
        else:
            return None
    else:
        return None

def c_to_ml_type(typ, ns, local_env):
    name = typ.attrib['name']
    if name == 'gint32':
        return Types('int', 'Val_long(%s)', 'gint32', 'int', '%s')
    elif name == 'guint32':
        return Types('int', 'Val_long(%s)', 'guint32', 'int', '%s')
    elif name == 'gboolean':
        return Types('bool', '(%s ? Val_true : Val_false)', 'gboolean', 'bool', '%s')
    ns_elem = local_env.get(name, None)
    if ns_elem != None:
        if ns_elem.xml.tag == t_enumeration:
            return Types('int', 'Val_int(%s)', 'int', 'int', '%s')
        elif ns_elem.xml.tag == t_class and ns_elem.is_GObject:
            ml_name0 = ns_elem.ml_name0_for(ns)
            return Types(ml_name0 + '_', 'Val_GObject((void *)(%s))', 'void *', ml_name0, 'new %s (%%s)' % ml_name0)
        else:
            return None
    else:
        return None

def print_skip(c_elem, ns_elem, reason):
    c_elem_tag = 'constructor' if c_elem.tag == t_constructor else 'method'
    skip = 'Skipping %s %s of class %s' % (c_elem_tag, c_elem.attrib['name'], ns_elem.attrib['name']) 
    print('%s: %s' % (skip, reason))

def output_gobject_types(ns, ml):
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
    cf(_C_HEADERS)
    ns = Namespace(env, namespace)
    local_env = ns.local_env
    namespaces[namespace_name] = ns
    output_gobject_types(ns, ml)
    classes = {}
    ctors_lines = []
    default_ctors_lines = []
    def ctl(line):
        ctors_lines.append(line)
    for ns_elem in namespace:
        if ns_elem.tag == t_bitfield or ns_elem.tag == t_enumeration:
            ml()
            ml('module %s = struct' % ns_elem.attrib['name'])
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
                qualifier = '' if nse.parent.ns is nse.ns else nse.parent.ns.name + '.'
                cl('    inherit %s (%s.upcast self)' % (qualifier + nse.parent.ml_name0, qualifier + nse.parent.name + '_'))
            cl('    method as_%s = self' % c_type_name)
            ctl('')
            ctl('module %s = struct' % ns_elem.attrib['name'])
            for c_elem in ns_elem:
                if c_elem.tag == t_attribute:
                    pass
                elif c_elem.tag == t_constructor or c_elem.tag == t_method:
                    c_elem_tag = 'constructor' if c_elem.tag == t_constructor else 'method'
                    params = Params()
                    if c_elem_tag == 'method':
                        params.append(CMethodParam(c_type_name))
                    throws = c_elem.attrib.get('throws', None) == '1'
                    result = None
                    skip = False
                    for m_elem in c_elem:
                        if m_elem.tag == t_parameters:
                            for ps_elem in m_elem:
                                ps_name = ps_elem.attrib['name']
                                assert ps_elem.tag == t_parameter
                                if ps_elem.attrib.get('transfer-ownership', None) != 'none':
                                    print_skip(c_elem, ns_elem, 'missing transfer-ownership="none" attribute for parameter %s' % ps_name)
                                    skip = True
                                    continue
                                if 'direction' in ps_elem.attrib:
                                    print_skip(c_elem, ns_elem, 'explicit "direction" attribute for parameter %s not yet supported' % ps_name)
                                    skip = True
                                    continue
                                typ = None
                                types = None
                                for p_elem in ps_elem:
                                    if p_elem.tag == t_type:
                                        typ = p_elem
                                if typ == None:
                                    print_skip(c_elem, ns_elem, 'no type specified for parameter %s' % ps_name)
                                    skip = True
                                    continue
                                types = ml_to_c_type(typ, ns, local_env)
                                if types == None:
                                    print_skip(c_elem, ns_elem, 'unsupported type %s of parameter %s' % (ET.tostring(typ), ps_name))
                                    skip = True
                                    continue
                                params.append(Param(ps_elem, types))
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
                                types = Types('unit', 'Val_unit', None, 'unit', '%s')
                            else:
                                types = c_to_ml_type(typ, ns, local_env)
                            if types == None:
                                print_skip(c_elem, ns_elem, 'unsupported return type %s' % ET.tostring(typ))
                                skip = True
                            result = types
                    if len(params.params) > 5:
                        # Skip for now; requires separate C functions for the bytecode runtime and the native code runtime
                        print_skip(c_elem, ns_elem, 'has more than 5 parameters')
                        skip = True
                    if c_elem.attrib[a_identifier] in c_functions_to_skip:
                        skip = True
                    if not skip:
                        if c_elem_tag == 'constructor':
                            expected_result = Types(nse.ml_name, 'Val_GObject((void *)(%s))', 'void *', None, None)
                            if result != expected_result:
                                if result.ml_type != 'widget' and result.ml_type != 'Gtk.widget':
                                    print('Warning: return type of constructor %s of class %s does not match class or GtkWidget' % (c_elem.attrib['name'], ns.name + '.' + ns_elem.attrib['name']))
                                result = expected_result
                        cfunc = 'ml_%s_%s_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_elem.attrib['name'])
                        mlfunc = escape_ml_keyword(c_elem.attrib['name'])
                        ml('  external %s: %s -> %s = "%s"' % (mlfunc, params.method_types(), result.ml_type, cfunc))
                        if c_elem_tag == 'constructor':
                            params_text = params.ctor_params()
                            args_text = params.ctor_args()
                            ctl('  let %s %s = new %s (%s_.%s %s)' % (mlfunc, params_text, nse.ml_name0, nse.name, mlfunc, args_text))
                            if c_elem.attrib['name'] == 'new':
                                default_ctors_lines.append('let %s %s = new %s (%s_.%s %s)' % (nse.ml_name0, params_text, nse.ml_name0, nse.name, mlfunc, args_text))
                        else:
                            mparams = params.drop_first()
                            method_name = mlfunc + '_' if ns.name == 'Gtk' and nse.name == 'Widget' and mlfunc == 'get_settings' else mlfunc # To work around a weird OCaml compiler error message
                            params_text = mparams.method_params()
                            args_text = mparams.method_args()
                            body = result.unwrap % ('%s_.%s self%s' % (nse.name, mlfunc, args_text))
                            cl('    method %s%s = %s' % (method_name, params_text, body))
                        cf()
                        cf('CAMLprim value %s(%s) {' % (cfunc, ', '.join('value %s' % p.c_name for p in params.params)))
                        params1 = params.params[:5]
                        params2 = params.params[5:]
                        cf('  CAMLparam%d(%s);' % (len(params1), ', '.join(p.c_name for p in params1)))
                        while params2 != []:
                            params2_1 = params2[:5]
                            params2 = params2[5:]
                            cf('  CAMLxparam%d(%s);' % (len(params2_1), ', '.join(p.c_name for p in params2_1)))
                        if throws:
                            cf('  CAMLlocal1(exn_msg);');
                            cf('  GError *err = NULL;')
                        args = ', '.join([p.c_value for p in params.params] + (['&err'] if throws else []))
                        call = '%s(%s)' % (c_elem.attrib[a_identifier], args)
                        if result.ml_type == 'unit':
                            cf('  %s;' % call)
                            ml_result = 'Val_unit'
                        else:
                            cf('  %s result = %s;' % (result.c_type, call))
                            ml_result = result.as_ml_value % 'result'
                        if throws:
                            cf('  if (err) { exn_msg = caml_copy_string(err->message); g_error_free(err); caml_failwith_value(exn_msg); }')
                        cf('  CAMLreturn(%s);' % ml_result)
                        cf('}')
                    elif ns.name == 'Gio' and ns_elem.attrib['name'] == 'Application' and c_elem.attrib['name'] == 'run':
                        ml('  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"')
                        cl('    method run argv = Application_.run self argv')
                        cf(_GIO_APPLICATION_RUN)
                elif c_elem.tag == t_signal:
                    params = Params()
                    result = None
                    skip = False
                    for s_elem in c_elem:
                        if s_elem.tag == t_parameters:
                            for ps_elem in s_elem:
                                assert ps_elem.tag == t_parameter
                                ps_name = ps_elem.attrib['name']
                                typ = None
                                types = None
                                for p_elem in ps_elem:
                                    if p_elem.tag == t_type:
                                        typ = p_elem
                                if typ == None:
                                    print_skip(c_elem, ns_elem, 'no type specified for parameter %s' % ps_name)
                                    skip = True
                                    continue
                                types = c_to_ml_type(typ, ns, local_env)
                                if types == None:
                                    print_skip(c_elem, ns_elem, 'unsupported type %s of parameter %s' % (ET.tostring(typ), ps_name))
                                    skip = True
                                    continue
                                params.append(Param(ps_elem, types))
                        elif s_elem.tag == t_return_value:
                            typ = None
                            types = None
                            for rv_elem in s_elem:
                                if rv_elem.tag == t_type:
                                    typ = rv_elem
                            if typ.attrib['name'] == 'none':
                                types = Types('unit', '', 'void', 'unit', '%s')
                            else:
                                types = ml_to_c_type(typ, ns, local_env)
                            if types == None:
                                print_skip(c_elem, ns_elem, 'unsupported return type %s' % ET.tostring(typ))
                                skip = True
                            result = types
                    if not skip:
                        c_name = c_elem.attrib['name'].replace('-', '_')
                        handlerfunc = 'ml_%s_%s_signal_handler_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_name)
                        cfunc = 'ml_%s_%s_signal_connect_%s' % (namespace.attrib['name'], ns_elem.attrib['name'], c_name)
                        ml('  external signal_connect_%s: [>`%s] obj -> (%s -> %s) -> int = "%s"' % (c_name, nse.c_type_name, params.method_types(), result.ml_type, cfunc))
                        cl('    method signal_connect_%s (callback: %s -> %s) = %s_.signal_connect_%s self (fun %s -> %s)' % (c_name, params.signal_types(), result.oo_type, nse.name, c_name, params.callback_args(), result.unwrap % ('(callback %s)' % params.callback_ret_args())))
                        cf()
                        cf('%s %s(GObject *instance_, %svalue *callbackCell) {' % (result.c_type, handlerfunc, ''.join('%s %s, ' % (p.types.c_type, p.c_name) for p in params.params)))
                        cf('  CAMLparam0();')
                        nb_args = max(1, len(params.params))
                        cf('  CAMLlocalN(args, %d);' % nb_args)
                        cf('  if (!callbacks_allowed) abort();')
                        cf('  callbacks_allowed = false;')
                        callback_args = params.c_callback_args()
                        for i in range(nb_args):
                            cf('  args[%d] = %s;' % (i, callback_args[i]))
                        result_decl, result_conv, return_stmt = (';', '%s', 'CAMLreturn0;') if result.ml_type == 'unit' else ('%s result = ' % result.c_type, result.as_ml_value, 'CAMLreturnT(%s, result);' % result.c_type)
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
            cl('  end')
            ctl('end')
    ml()
    class_printer = ClassPrinter(classes, ml)
    for class_ in classes.values():
        class_printer.print_class(class_)
    ml()
    for line in ctors_lines:
        ml(line)
    if default_ctors_lines != []:
        ml()
        for line in default_ctors_lines:
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
