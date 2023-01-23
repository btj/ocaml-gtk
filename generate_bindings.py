from dataclasses import dataclass
import platform
from typing import Optional, Any
import xml.etree.ElementTree as ET

c_functions_to_skip = {'g_io_module_load', 'g_io_module_unload'} # https://gitlab.gnome.org/GNOME/glib/-/issues/2498

t_include = "{http://www.gtk.org/introspection/core/1.0}include"
t_namespace = "{http://www.gtk.org/introspection/core/1.0}namespace"
t_class = "{http://www.gtk.org/introspection/core/1.0}class"
t_constant = "{http://www.gtk.org/introspection/core/1.0}constant"
t_attribute = "{http://www.gtk.org/introspection/core/1.0}attribute"
t_constructor = "{http://www.gtk.org/introspection/core/1.0}constructor"
t_method = "{http://www.gtk.org/introspection/core/1.0}method"
t_parameters = "{http://www.gtk.org/introspection/core/1.0}parameters"
t_parameter = "{http://www.gtk.org/introspection/core/1.0}parameter"
t_return_value = "{http://www.gtk.org/introspection/core/1.0}return-value"
t_type = "{http://www.gtk.org/introspection/core/1.0}type"
t_array = "{http://www.gtk.org/introspection/core/1.0}array"
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
        self.global_env = env | dict((self.name + '.' + ns_elem_name, ns_elem)
                                     for ns_elem_name, ns_elem in ns_elems.items())

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
        self.c_method_prefix = 'ml_%s_%s' % (ns.name, self.name)

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
    # For every parameter whose value is derived from this parameter's value, the derived parameter's index and a format string that given C code for this parameter's value, produces C code for the derived parameter's value
    derived_params: tuple[tuple[int, str], ...] = ()

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
    def c_typed_param(self):
        return '%s %s' % (self.types.c_type, self.c_name)

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
        self.nb_implicit_params = 0
        self.derived_params = {}
    
    def non_derived_params(self):
        return (p for i, p in enumerate(self.params) if i - self.nb_implicit_params not in self.derived_params)

    def append(self, param):
        self.params.append(param)

    def method_types(self):
        if self.params == []:
            return 'unit'
        else:
            return ' -> '.join(p.types.ml_type for p in self.non_derived_params())

    def signal_types(self):
        if self.params == []:
            return 'unit'
        else:
            return ' -> '.join(p.types.oo_type for p in self.non_derived_params())

    def ctor_params(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_typed_param for p in self.non_derived_params())

    def ctor_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_arg for p in self.non_derived_params())

    def method_params(self):
        return ''.join(' ' + p.ml_typed_param for p in self.non_derived_params())

    def method_args(self):
        return ''.join(' ' + p.ml_arg for p in self.non_derived_params())

    def callback_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join(p.ml_name for p in self.non_derived_params())

    def callback_ret_args(self):
        if self.params == []:
            return '()'
        else:
            return ' '.join('(%s)' % p.ml_arg for p in self.non_derived_params())

    def c_callback_args(self):
        if self.params == []:
            return ['Val_unit']
        else:
            return [p.c_value for p in self.params]

    def c_params(self):
        return ''.join('%s %s, ' % (p.types.c_type, p.c_name) for p in self.non_derived_params())

    def drop_first(self):
        assert self.nb_implicit_params == 1
        p = Params()
        p.params = self.params[1:]
        p.derived_params = self.derived_params
        return p

@dataclass
class ElementType:
    typename: str
    array: Optional[Any] # The XML 'array' element
    allow_none: bool
    transfer_ownership: Optional[str]
    direction: Optional[str]

    @property
    def to_str(self):
        ret = self.typename
        if self.array:
            ret += '[]'
        if self.allow_none:
            ret += '?'
        return ret

    @classmethod
    def make(cls, elem):
        typ = elem.find(t_type)
        array = None
        if typ is None:
            array_elem = elem.find(t_array)
            assert array_elem is not None, f"Unknown type {elem}"
            array = array_elem
            typ = array_elem.find(t_type)
            assert typ is not None, f"No type found for {elem}"
        allow_none = elem.get('allow-none', "0") == "1"
        transfer_ownership = elem.get('transfer-ownership', None)
        direction = elem.get('direction', None)
        typename = typ.attrib['name']
        return cls(typename, array, allow_none, transfer_ownership, direction)

@dataclass
class Method:
    name: str
    params: Params
    result: Types
    ml_func: str
    module_name: str

    def to_ml(self):
        params_text = self.params.method_params()
        args_text = self.params.method_args()
        body = self.result.unwrap % (
            '%s_.%s self%s' % (self.module_name, self.ml_func, args_text))
        return 'method %s%s = %s' % (self.name, params_text, body)

class GioApplicationRunMethod:
    def to_ml(self):
        return 'method run argv = Application_.run self argv'

@dataclass
class Constructor:
    name: str
    cls: 'Class'
    nse: NamespaceElement
    params: Params
    result: Types

    def __init__(self, name, cls, nse, params, result):
        self.name = name
        self.cls = cls
        self.nse = nse
        self.params = params
        self.set_expected_result(result)

    def set_expected_result(self, result):
        expected_result = Types(self.cls.self_type, 'Val_GObject((void *)(%s))', 'void *', None, None)
        if result != expected_result and result.ml_type not in ['widget', 'Gtk.widget']:
            print('Warning: return type of constructor %s of class %s does not match class or GtkWidget' %
                  (self.name, self.nse.qualified_name))
        self.result = expected_result

    def ml_lines(self):
        params_text = self.params.ctor_params()
        args_text = self.params.ctor_args()
        ml_func = escape_ml_keyword(self.name)
        new = 'new %s (%s_.%s %s)' % (self.cls.name, self.nse.name, ml_func, args_text)
        ctor = '  let %s %s = %s' % (ml_func, params_text, new)
        if self.name == 'new':
            default = 'let %s %s = %s' % (self.cls.name, params_text, new)
        else:
            default = None
        return ctor, default

@dataclass
class Signal:
    name: str
    params: Params
    result: Types
    module_name: str

    def to_ml(self):
        method_name = 'signal_connect_%s' % self.name
        res = self.result.unwrap % ('(callback %s)' % self.params.callback_ret_args())
        signal_fn = '(fun %s -> %s)' % (self.params.callback_args(), res)
        body = '%s_.%s self %s' % (self.module_name, method_name, signal_fn)
        return ('method %s (callback: %s -> %s) = %s' %
                (method_name, self.params.signal_types(), self.result.oo_type, body))

class Class:
    def __init__(self, nse):
        self.nse = nse
        self.name = nse.ml_name0
        self.self_type = nse.ml_name
        self.c_type_name = nse.c_type_name
        self.parent = None
        self.inherit = None
        self.fill_parent_details(nse)
        self.printed = False
        # Will be filled in while reading the xml file
        self.methods = []
        self.signals = []
        self.constructors = []

    def fill_parent_details(self, nse):
        if nse.parent and nse.parent.ns is nse.ns:
            self.parent = nse.parent.ml_name0
        if nse.parent_name is not None:
            qualifier = '' if nse.parent.ns is nse.ns else nse.parent.ns.name + '.'
            self.inherit = (qualifier + nse.parent.ml_name0, qualifier + nse.parent.name + '_')

    def ml_lines(self):
        lines = [
            '%s (self: %s) =' % (self.name, self.self_type),
            '  object',
        ]
        if self.inherit:
            lines.append('    inherit %s (%s.upcast self)' % self.inherit)
        lines.append('    method as_%s = self' % self.c_type_name)
        lines += ['    ' + x.to_ml() for x in (self.methods + self.signals)]
        lines.append('  end')
        return lines

    def constructor_lines(self):
        ctor_lines = [
            '',
            'module %s = struct' % self.nse.name,
        ]
        default_lines = []
        for c in self.constructors:
            ctor, default = c.ml_lines()
            ctor_lines.append(ctor)
            if default:
                default_lines.append(default)
        ctor_lines.append('end')
        return ctor_lines, default_lines

class ClassPrinter:
    def __init__(self, classes, ml):
        self.classes = classes
        self.is_first_class = True
        self.ml = ml

    def print_class(self, class_):
        if class_.printed:
            return
        class_.printed = True
        if class_.parent is not None:
            self.print_class(self.classes[class_.parent])
        first, *rest = class_.ml_lines()
        if self.is_first_class:
            self.ml('class ' + first)
            self.is_first_class = False
        else:
            self.ml('and ' + first)
        for line in rest:
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

if platform.system() == 'Darwin':
    _C_HEADERS += "\n#include <gio/gosxappinfo.h>"


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

def ml_to_c_type(typ, ns):
    if typ.array is not None:
        if 'length' not in typ.array.attrib:
            return None
        length_param_index = int(typ.array.attrib['length'])
        if typ.typename == 'guint8':
            return Types('string', '(const guchar *)String_val(%s)', 'const guchar *', 'string', '%s', ((length_param_index, 'caml_string_length(%s)'),))
        else:
            return None
    name = typ.typename
    if name == 'utf8':
        return Types('string', 'String_val(%s)', 'const char *', 'string', '%s')
    elif name == 'gboolean':
        return Types('bool', 'Bool_val(%s)', 'gboolean', 'bool', '%s')
    elif name == 'gint32':
        return Types('int', 'Long_val(%s)', 'gint32', 'int', '%s')
    elif name == 'guint32':
        return Types('int', 'Long_val(%s)', 'guint32', 'int', '%s')
    elif name == 'gint64':
        return Types('int64', 'caml_copy_int64(%s)', 'gint64', 'int64', '%s')
    ns_elem = ns.local_env.get(name, None)
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

def c_to_ml_type(typ, ns):
    if typ.array:
        # Not supported yet
        return None
    # TODO: We should not support allow_none either until we have some
    # mechanism for converting to an option type.
    name = typ.typename
    if name == 'gint32':
        return Types('int', 'Val_long(%s)', 'gint32', 'int', '%s')
    elif name == 'guint32':
        return Types('int', 'Val_long(%s)', 'guint32', 'int', '%s')
    elif name == 'gboolean':
        return Types('bool', '(%s ? Val_true : Val_false)', 'gboolean', 'bool', '%s')
    elif name == 'utf8':
        if typ.allow_none:
            return Types('string option', 'Val_string_option(%s)', 'const char *', 'string option', '%s')
        else:
            return Types('string', 'caml_copy_string(%s)', 'const char *', 'string', '%s')
    ns_elem = ns.local_env.get(name, None)
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

class BaseMethodParser:
    """Parse method params and return value from xml definition."""

    def __init__(self, elem, class_elem, ns):
        self.elem = elem
        self.class_name = class_elem.attrib['name']
        self.ns = ns
        self.params = Params()
        self.result = None

    def parse(self):
        if not self.get_params_and_return():
            return None, None
        if not self.validate():
            return None, None
        return self.params, self.result

    def print_skip(self, reason):
        elem_tag = 'constructor' if self.elem.tag == t_constructor else 'method'
        elem_name = self.elem.attrib['name']
        skip = 'Skipping %s %s of class %s' % (elem_tag, elem_name, self.class_name)
        print('%s: %s' % (skip, reason))

    def c_to_ml_type(self, t):
        return c_to_ml_type(t, self.ns)

    def ml_to_c_type(self, t):
        return ml_to_c_type(t, self.ns)

    def get_params_and_return(self):
        for m_elem in self.elem:
            if m_elem.tag == t_parameters:
                for ps_elem in m_elem:
                    assert ps_elem.tag == t_parameter
                    ps_name = ps_elem.attrib['name']
                    t = ElementType.make(ps_elem)
                    if not self.validate_param(t, ps_name):
                        return False
                    types = self.get_param_types(t)
                    if types == None:
                        self.print_skip('unsupported type %s of parameter %s' % (t.to_str, ps_name))
                        return False
                    param_index = len(self.params.params)
                    self.params.append(Param(ps_elem, types))
                    for derived_param in types.derived_params:
                        derived_param_index, derived_param_value = derived_param
                        if derived_param_index not in self.params.derived_params:
                            self.params.derived_params[derived_param_index] = []
                        self.params.derived_params[derived_param_index].append((param_index, derived_param_value))
            elif m_elem.tag == t_return_value:
                t = ElementType.make(m_elem)
                types = self.get_return_types(t)
                if types == None:
                    self.print_skip('unsupported return type %s' % t.to_str)
                    return False
                self.result = types
        return True

    def get_param_types(self, t):
        raise NotImplementedError()

    def get_return_types(self, t):
        raise NotImplementedError()

    def validate_param(self, t, ps_name):
        return True

    def validate(self):
        return True

class MethodParser(BaseMethodParser):
    def __init__(self, elem, c_type_name, class_elem, ns):
        super().__init__(elem, class_elem, ns)
        self.is_constructor = elem.tag == t_constructor
        if not self.is_constructor:
            self.params.nb_implicit_params = 1
            self.params.append(CMethodParam(c_type_name))

    def get_param_types(self, t):
        return self.ml_to_c_type(t)

    def get_return_types(self, t):
        if t.typename == 'none':
            return Types('unit', 'Val_unit', None, 'unit', '%s')
        else:
            return self.c_to_ml_type(t)

    def validate_param(self, t, ps_name):
        if t.transfer_ownership != 'none':
            self.print_skip('missing transfer-ownership="none" attribute for parameter %s' % ps_name)
            return False
        if t.direction is not None:
            self.print_skip('explicit "direction" attribute for parameter %s not yet supported' % ps_name)
            return False
        return True

    def validate(self):
        if len(self.params.params) > 5:
            # Skip for now; requires separate C functions for the bytecode
            # runtime and the native code runtime
            self.print_skip('has more than 5 parameters')
            return False
        if self.elem.attrib[a_identifier] in c_functions_to_skip:
            return False
        return True

class SignalParser(BaseMethodParser):
    def get_param_types(self, t):
        return self.c_to_ml_type(t)

    def get_return_types(self, t):
        if t.typename == 'none':
            return Types('unit', '', 'void', 'unit', '%s')
        else:
            return self.ml_to_c_type(t)

def output_method_code(c_elem, nse, params, result, ml, cf):
    c_elem_name = c_elem.attrib['name']
    c_func = '%s_%s' % (nse.c_method_prefix, c_elem_name)
    ml_func = escape_ml_keyword(c_elem_name)
    ml('  external %s: %s -> %s = "%s"' % (ml_func, params.method_types(), result.ml_type, c_func))
    output_method_c_code(c_elem, c_func, params, result, cf)

def output_method_c_code(c_elem, c_func, params, result, cf):
    cf()
    non_derived_params = list(params.non_derived_params())
    cf('CAMLprim value %s(%s) {' % (c_func, ', '.join('value %s' % p.c_name for p in non_derived_params)))
    params1 = non_derived_params[:5]
    params2 = non_derived_params[5:]
    cf('  CAMLparam%d(%s);' % (len(params1), ', '.join(p.c_name for p in params1)))
    while params2 != []:
        params2_1 = params2[:5]
        params2 = params2[5:]
        cf('  CAMLxparam%d(%s);' % (len(params2_1), ', '.join(p.c_name for p in params2_1)))
    for derived_param_index, derived_param_sources in params.derived_params.items():
        param = params.params[params.nb_implicit_params + derived_param_index]
        primary_source_index, primary_source_value = derived_param_sources[0]
        primary_source_param = params.params[primary_source_index]
        cf('  %s = %s;' % (param.c_typed_param, primary_source_value % primary_source_param.c_name))
        for secondary_source_index, secondary_source_value in derived_param_sources[1:]:
            secondary_source_param = params.params[secondary_source_index]
            cf('  if (%s != %s) caml_failwith("Array lengths do not match");' % (param.c_name, secondary_source_value % secondary_source_param.c_name))
    throws = c_elem.attrib.get('throws', None) == '1'
    if throws:
        cf('  CAMLlocal1(exn_msg);');
        cf('  GError *err = NULL;')
    args = ', '.join([p.c_value if i - params.nb_implicit_params not in params.derived_params else p.c_name for i, p in enumerate(params.params)] + (['&err'] if throws else []))
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

def output_signal_code(c_elem, nse, params, result, ml, cf):
    c_name = c_elem.attrib['name'].replace('-', '_')
    prefix = nse.c_method_prefix
    handler_func = '%s_signal_handler_%s' % (prefix, c_name)
    c_func = '%s_signal_connect_%s' % (prefix, c_name)
    ml('  external signal_connect_%s: [>`%s] obj -> (%s -> %s) -> int = "%s"' %
       (c_name, nse.c_type_name, params.method_types(), result.ml_type, c_func))
    output_signal_c_code(c_elem, c_func, handler_func, params, result, cf)

def output_signal_c_code(c_elem, c_func, handler_func, params, result, cf):
    cf()
    cf('%s %s(GObject *instance_, %svalue *callbackCell) {' % (result.c_type, handler_func, params.c_params()))
    cf('  CAMLparam0();')
    nb_args = max(1, len(params.params))
    cf('  CAMLlocalN(args, %d);' % nb_args)
    cf('  if (!callbacks_allowed) abort();')
    cf('  callbacks_allowed = false;')
    callback_args = params.c_callback_args()
    for i in range(nb_args):
        cf('  args[%d] = %s;' % (i, callback_args[i]))
    if result.ml_type == 'unit':
        result_decl, result_conv, return_stmt = (';', '%s', 'CAMLreturn0;')
    else:
        result_decl = '%s result = ' % result.c_type
        result_conv = result.as_ml_value
        return_stmt = 'CAMLreturnT(%s, result);' % result.c_type
    callback = 'caml_callbackN(*callbackCell, %d, args)' % nb_args
    cf('  %s%s;' % (result_decl, result_conv % callback))
    cf('  callbacks_allowed = true;')
    cf('  %s' % return_stmt)
    cf('}')
    cf()
    cf('CAMLprim value %s(value instance_, value callback) {' % c_func)
    cf('  return ml_GObject_signal_connect(instance_, "%s", %s, callback);' % (c_elem.attrib['name'], handler_func))
    cf('}')

NAMESPACES = {}

def process_namespace(namespace, env):
    ns = Namespace(env, namespace)
    NAMESPACES[ns.name] = ns
    ml_file = open(ns.name + '.ml', 'w')
    def ml(*args):
        print(*args, file=ml_file)
    c_file = open('ml_' + ns.name + '.c', 'w')
    def cf(*args):
        print(*args, file=c_file)
    ml('[@@@alert "-unsafe"]')
    ml()
    ml('open Gobject0')
    ml()
    cf(_C_HEADERS)
    output_gobject_types(ns, ml)
    classes = {}
    ctors_lines = []
    default_ctors_lines = []
    for ns_elem in namespace:
        if ns_elem.tag == t_bitfield or ns_elem.tag == t_enumeration:
            ml()
            ml('module %s = struct' % ns_elem.attrib['name'])
            for bf_elem in ns_elem:
                if bf_elem.tag == t_member:
                    ml('  let %s = %s' % (escape_ml_keyword(bf_elem.attrib['name']), bf_elem.attrib['value']))
            ml('end')
        elif ns_elem.tag == t_constant:
            constant_xml = ns_elem
            name = constant_xml.attrib['name']
            value = constant_xml.attrib['value']
            type_name = constant_xml.find(t_type).attrib['name']
            if type_name in {'gint8', 'guint8', 'gint16', 'guint16', 'gint32', 'guint32', 'gint64', 'guint64', 'gdouble'}:
                ml_value = value
            elif type_name == 'gboolean':
                if value == '0':
                    ml_value = 'false'
                elif value == '1':
                    ml_value = 'true'
                else:
                    print('Skipping constant %s: unknown gboolean literal %s' % (name, value))
                    continue
            elif type_name == 'utf8':
                ml_value = '"%s"' % ''.join('\\x%02x' % ord(c) if c < ' ' else c for c in value)
            else:
                print('Skipping constant %s: type "%s" is not yet supported' % (name, type_name))
                continue
            ml()
            ml('let _%s = %s' % (name, ml_value))
        elif ns_elem.tag == t_class:
            nse = ns.local_env[ns_elem.attrib['name']]
            if not nse.is_GObject:
                continue
            cls = Class(nse)
            classes[cls.name] = cls
            ml()
            ml('module %s_ = struct' % nse.name)
            ml('  let upcast: [>`%s] obj -> %s = Obj.magic' % (cls.c_type_name, cls.self_type))
            for c_elem in ns_elem:
                c_elem_name = c_elem.attrib['name']
                if c_elem.tag == t_attribute:
                    pass
                elif c_elem.tag == t_constructor:
                    parser = MethodParser(c_elem, cls.c_type_name, ns_elem, ns)
                    params, result = parser.parse()
                    if params:
                        constructor = Constructor(c_elem_name, cls, nse, params, result)
                        cls.constructors.append(constructor)
                        result = constructor.result
                        output_method_code(c_elem, nse, params, result, ml, cf)
                elif c_elem.tag == t_method:
                    parser = MethodParser(c_elem, cls.c_type_name, ns_elem, ns)
                    params, result = parser.parse()
                    if params:
                        ml_func = escape_ml_keyword(c_elem_name)
                        mparams = params.drop_first()
                        if nse.qualified_name == 'Gtk.Widget' and ml_func == 'get_settings':
                            # To work around a weird OCaml compiler error message
                            method_name = ml_func + '_'
                        else:
                            method_name = ml_func
                        cls.methods.append(Method(method_name, mparams, result, ml_func, nse.name))
                        output_method_code(c_elem, nse, params, result, ml, cf)
                    elif nse.qualified_name == 'Gio.Application' and c_elem_name == 'run':
                        ml('  external run: [>`GApplication] obj -> string array -> int = "ml_Gio_Application_run"')
                        cls.methods.append(GioApplicationRunMethod())
                        cf(_GIO_APPLICATION_RUN)
                elif c_elem.tag == t_signal:
                    parser = SignalParser(c_elem, ns_elem, ns)
                    params, result = parser.parse()
                    if params:
                        c_name = c_elem_name.replace('-', '_')
                        cls.signals.append(Signal(c_name, params, result, nse.name))
                        output_signal_code(c_elem, nse, params, result, ml, cf)
            ml('end')
            # Collect the ML lines for the class constructors
            ctor_lines, default = cls.constructor_lines()
            ctors_lines.extend(ctor_lines)
            default_ctors_lines.extend(default)
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
            ns = NAMESPACES.get(name, None)
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
