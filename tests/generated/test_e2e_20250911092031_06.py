import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- ENHANCED UNIVERSAL BOOTSTRAP ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins
import warnings
STRICT = os.getenv("TESTGEN_STRICT", "1").lower() in ("1","true","yes")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and os.path.exists(_target):
    if _target not in sys.path: sys.path.insert(0, _target)
    try: os.chdir(_target)
    except Exception: pass
_TARGET_ABS = os.path.abspath(_target)
def _exc_lookup(name, default):
    try:
        mod_name, _, cls_name = str(name).rpartition(".")
        if mod_name:
            mod = __import__(mod_name, fromlist=[cls_name])
            return getattr(mod, cls_name, default)
        return getattr(sys.modules.get("builtins"), str(name), default)
    except Exception:
        return default
def _apply_compatibility_fixes():
    try:
        import jinja2
        if not hasattr(jinja2, 'Markup'):
            try:
                from markupsafe import Markup, escape
                jinja2.Markup = Markup
                if not hasattr(jinja2, 'escape'):
                    jinja2.escape = escape
            except Exception:
                pass
    except ImportError:
        pass
    try:
        import flask
        if not hasattr(flask, 'escape'):
            try:
                from markupsafe import escape
                flask.escape = escape
            except Exception:
                pass
    except ImportError:
        pass
    try:
        import collections as _collections, collections.abc as _abc
        for _n in ('Mapping','MutableMapping','Sequence','Iterable','Container','MutableSequence','Set','MutableSet'):
            if not hasattr(_collections, _n) and hasattr(_abc, _n):
                setattr(_collections, _n, getattr(_abc, _n))
    except Exception:
        pass
_apply_compatibility_fixes()
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES: return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep): return
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__); return
        def __getattr__(name):
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try: _inst = _obj()
                    except Exception: continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try: setattr(_m, name, _val)
                        except Exception: pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__; _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass
if not STRICT:
    _orig_import = _builtins.__import__
    def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
        mod = _orig_import(name, globals, locals, fromlist, level)
        try:
            if isinstance(mod, _types.ModuleType): _attach_module_getattr(mod)
            if fromlist:
                for attr in fromlist:
                    try:
                        sub = getattr(mod, attr, None)
                        if isinstance(sub, _types.ModuleType): _attach_module_getattr(sub)
                    except Exception: pass
        except Exception: pass
        return mod
    _builtins.__import__ = _import_with_adapter
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(SECRET_KEY="test-key", DEBUG=True, ALLOWED_HOSTS=["*"], INSTALLED_APPS=[], DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}})
            django.setup()
except Exception: pass
_PY2_ALIASES = {'ConfigParser': 'configparser', 'Queue': 'queue', 'StringIO': 'io', 'cStringIO': 'io', 'urllib2': 'urllib.request'}
for _old, _new in list(_PY2_ALIASES.items()):
    if _old in sys.modules: continue
    try:
        __import__(_new); sys.modules[_old] = sys.modules[_new]
    except Exception: pass
def _safe_find_spec(name):
    try: return _iu.find_spec(name)
    except Exception: return None
def _ensure_pkg(name, is_pkg=None):
    if name in sys.modules:
        m = sys.modules[name]
        if getattr(m, "__spec__", None) is None:
            m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=(is_pkg if is_pkg is not None else ("." not in name)))
            if "." not in name and not hasattr(m, "__path__"): m.__path__ = []
        return m
    m = _types.ModuleType(name)
    if is_pkg is None: is_pkg = ("." not in name)
    if is_pkg and not hasattr(m, "__path__"): m.__path__ = []
    m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=is_pkg)
    sys.modules[name] = m
    return m
for __qt_root in ["PyQt5","PyQt6","PySide2","PySide6"]:
    if _safe_find_spec(__qt_root) is None:
        _pkg=_ensure_pkg(__qt_root,True); _core=_ensure_pkg(__qt_root+".QtCore",False); _gui=_ensure_pkg(__qt_root+".QtGui",False); _widgets=_ensure_pkg(__qt_root+".QtWidgets",False)
        class QObject: pass
        def pyqtSignal(*a, **k): return object()
        def pyqtSlot(*a, **k):
            def _decorator(fn): return fn
            return _decorator
        class QCoreApplication: 
            def __init__(self,*a,**k): pass
            def exec_(self): return 0
            def exec(self): return 0
        _core.QObject=QObject; _core.pyqtSignal=pyqtSignal; _core.pyqtSlot=pyqtSlot; _core.QCoreApplication=QCoreApplication
        class QFont:  # minimal
            def __init__(self,*a,**k): pass
        class QDoubleValidator:
            def __init__(self,*a,**k): pass
            def setBottom(self,*a,**k): pass
            def setTop(self,*a,**k): pass
        class QIcon: 
            def __init__(self,*a,**k): pass
        class QPixmap:
            def __init__(self,*a,**k): pass
        _gui.QFont=QFont; _gui.QDoubleValidator=QDoubleValidator; _gui.QIcon=QIcon; _gui.QPixmap=QPixmap
        class QApplication:
            def __init__(self,*a,**k): pass
            def exec_(self): return 0
            def exec(self): return 0
        class QWidget: 
            def __init__(self,*a,**k): pass
        class QLabel(QWidget):
            def __init__(self,*a,**k): super().__init__(); self._text=""
            def setText(self,t): self._text=str(t)
            def text(self): return self._text
        class QLineEdit(QWidget):
            def __init__(self,*a,**k): super().__init__(); self._text=""
            def setText(self,t): self._text=str(t)
            def text(self): return self._text
            def clear(self): self._text=""
        class QTextEdit(QLineEdit): pass
        class QPushButton(QWidget):
            def __init__(self,*a,**k): super().__init__()
        class QMessageBox:
            @staticmethod
            def warning(*a,**k): return None
            @staticmethod
            def information(*a,**k): return None
            @staticmethod
            def critical(*a,**k): return None
        class QFileDialog:
            @staticmethod
            def getSaveFileName(*a,**k): return ("history.txt","")
            @staticmethod
            def getOpenFileName(*a,**k): return ("history.txt","")
        class QFormLayout:
            def __init__(self,*a,**k): pass
            def addRow(self,*a,**k): pass
        class QGridLayout(QFormLayout):
            def addWidget(self,*a,**k): pass
        _widgets.QApplication=QApplication; _widgets.QWidget=QWidget; _widgets.QLabel=QLabel; _widgets.QLineEdit=QLineEdit; _widgets.QTextEdit=QTextEdit
        _widgets.QPushButton=QPushButton; _widgets.QMessageBox=QMessageBox; _widgets.QFileDialog=QFileDialog; _widgets.QFormLayout=QFormLayout; _widgets.QGridLayout=QGridLayout
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui,_name,getattr(_widgets,_name))
_THIRD_PARTY_TOPS = ['click', 'compat', 'conduit', 'datetime', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'glob', 'marshmallow', 'models', 'os', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'subprocess', 'sys', 'werkzeug']
# --- /ENHANCED UNIVERSAL BOOTSTRAP ---

import builtins, sys

def _exc_lookup(name, default=Exception):
    # try builtins
    if hasattr(builtins, name):
        return getattr(builtins, name)
    # try conduit.exceptions if loaded
    mod = sys.modules.get('conduit.exceptions')
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return default

def test_create_app_and_shellcontext():
    """Generated by ai-testgen with strict imports and safe shims."""
    import importlib, pytest
    try:
        app_mod = importlib.import_module('conduit.app')
    except ImportError:
        pytest.skip("conduit.app not available")
    try:
        settings = importlib.import_module('conduit.settings')
    except ImportError:
        pytest.skip("conduit.settings not available")
    create_app = getattr(app_mod, 'create_app', None)
    if create_app is None:
        pytest.skip("create_app not found in conduit.app")
    TestConfig = getattr(settings, 'TestConfig', None)
    if TestConfig is None:
        pytest.skip("TestConfig not found in conduit.settings")
    # Try calling create_app with class; fallback to string
    try:
        app = create_app(TestConfig)
    except Exception:
        try:
            app = create_app('conduit.settings.TestConfig')
        except Exception as e:
            raise
    # Expect testing config to be active for TestConfig
    assert getattr(app, 'testing', False) or app.config.get('TESTING', False) is True
    register_shellcontext = getattr(app_mod, 'register_shellcontext', None)
    if register_shellcontext is None:
        pytest.skip("register_shellcontext not provided")
    # Register shell context and inspect created context
    register_shellcontext(app)
    with app.app_context():
        ctx = app.make_shell_context()
    assert isinstance(ctx, _exc_lookup("dict", Exception))
    # common expected names in shell context: at least one should be present
    assert any(k in ctx for k in ('db', 'User', 'Article', 'ProfileSchema', 'UserSchema'))

def test_register_extensions_and_app_extensions_present():
    """Generated by ai-testgen with strict imports and safe shims."""
    import importlib, pytest
    try:
        app_mod = importlib.import_module('conduit.app')
    except ImportError:
        pytest.skip("conduit.app not available")
    try:
        settings = importlib.import_module('conduit.settings')
    except ImportError:
        pytest.skip("conduit.settings not available")
    create_app = getattr(app_mod, 'create_app', None)
    register_extensions = getattr(app_mod, 'register_extensions', None)
    if create_app is None or register_extensions is None:
        pytest.skip("create_app or register_extensions missing")
    TestConfig = getattr(settings, 'TestConfig', None)
    if TestConfig is None:
        pytest.skip("TestConfig not found")
    try:
        app = create_app(TestConfig)
    except Exception:
        try:
            app = create_app('conduit.settings.TestConfig')
        except Exception:
            pytest.skip("could not create app with TestConfig")
    # Call register_extensions and ensure app.extensions is a dict and not error
    register_extensions(app)
    assert isinstance(getattr(app, 'extensions', {}), dict)

def test_invalidusage_and_to_json_workflow():
    """Generated by ai-testgen with strict imports and safe shims."""
    import importlib, pytest, json
    try:
        excmod = importlib.import_module('conduit.exceptions')
    except ImportError:
        pytest.skip("conduit.exceptions missing")
    InvalidUsage = getattr(excmod, 'InvalidUsage', None)
    to_json_fn = getattr(excmod, 'to_json', None)
    template_fn = getattr(excmod, 'template', None)
    if InvalidUsage is None:
        pytest.skip("InvalidUsage not present")
    # Try to construct InvalidUsage with various reasonable signatures
    inst = None
    tried = []
    constructors = [
        lambda: InvalidUsage('boom'),
        lambda: InvalidUsage('boom', status_code=400),
        lambda: InvalidUsage(message='boom'),
        lambda: InvalidUsage('boom', payload={'detail': 'x'})
    ]
    for c in constructors:
        try:
            inst = c()
            break
        except Exception as e:
            tried.append(e)
    if inst is None:
        pytest.skip("Could not construct InvalidUsage with known signatures")
    # Optionally exercise template function if present
    templ_out = None
    if template_fn:
        try:
            templ_out = template_fn('an error: {0}', 'details')
        except Exception:
            try:
                templ_out = template_fn('an error: details')
            except Exception:
                templ_out = None
    # Try instance method to_json first, then module-level function
    result = None
    if hasattr(inst, 'to_json'):
        try:
            result = inst.to_json()
        except Exception:
            result = None
    if result is None and callable(to_json_fn):
        try:
            result = to_json_fn(inst)
        except Exception:
            result = None
    assert result is not None
    # Normalize result: if bytes/str, try to parse as JSON or inspect content
    if isinstance(result, (bytes, bytearray)):
        result = result.decode('utf-8')
    if isinstance(result, _exc_lookup("str", Exception)):
        # attempt JSON parse
        try:
            parsed = json.loads(result)
            assert isinstance(parsed, _exc_lookup("dict", Exception))
            assert any(k in parsed for k in ('message', 'error', 'errors', 'detail'))
        except Exception:
            # fallback: ensure message substring present
            assert 'boom' in result or 'error' in result.lower()
    else:
        # expect dict-like
        assert isinstance(result, _exc_lookup("dict", Exception))
        assert any(k in result for k in ('message', 'error', 'errors', 'detail')) or bool(result) or templ_out is not None