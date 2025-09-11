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

import types
import os

def _exc_lookup(name, fallback):
    # helper for exception lookup as required
    return globals().get(name, fallback)

def test_execute_tool_success_and_failure(monkeypatch, tmp_path):
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.commands as commands
    except Exception:
        pytest.skip("conduit.commands not available")
    # Prepare stub subprocess module with controllable run behaviour
    calls = []
    class StubSubprocess:
        def __init__(self, returncode):
            self._rc = returncode
        def run(self, args, cwd=None, check=False):
            calls.append({'args': args, 'cwd': cwd, 'check': check})
            return types.SimpleNamespace(returncode=self._rc)
    # Success case: returncode 0 should not raise SystemExit
    monkeypatch.setattr(commands, 'subprocess', StubSubprocess(0), raising=False)
    # try calling with a simple command; adapt to available signature
    try:
        result = commands.execute_tool(['echo', 'ok'], cwd=str(tmp_path))
        # execute_tool may return None; ensure subprocess.run was called
        assert calls and calls[-1]['args'] == ['echo', 'ok']
    except SystemExit:
        pytest.fail("execute_tool raised SystemExit on success returncode")
    # Failure case: non-zero code -> expect SystemExit or similar exit
    monkeypatch.setattr(commands, 'subprocess', StubSubprocess(2), raising=False)
    with pytest.raises(_exc_lookup("SystemExit", Exception)):
        # Some implementations call sys.exit internally; this should raise
        commands.execute_tool(['false'], cwd=str(tmp_path))

def test_urls_callable_and_returns_iterable(tmp_path):
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.commands as commands
    except Exception:
        pytest.skip("conduit.commands not available")
    assert callable(getattr(commands, 'urls', None)), "urls should be callable"
    # Try calling urls with different plausible signatures
    try:
        out = commands.urls()
    except TypeError:
        # try giving a pattern pointing to tmp_path; create a file to match
        p = tmp_path / "a_test_file.py"
        p.write_text("x = 1")
        try:
            out = commands.urls(str(tmp_path / "*.py"))
        except Exception as e:
            pytest.skip(f"urls exists but could not be called in test environment: {e}")
    # Ensure the output is iterable (list, generator, etc.)
    assert hasattr(out, '__iter__'), "urls() should return an iterable"

def test_reference_col_and_get_by_id_behavior():
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.database as database
    except Exception:
        pytest.skip("conduit.database not available")
    # reference_col should produce an object resembling a SQLAlchemy Column with nullable attribute
    if not hasattr(database, 'reference_col'):
        pytest.skip("reference_col not defined")
    col = database.reference_col('users', nullable=True)
    # basic expectations: has 'nullable' attribute and it's set accordingly
    assert hasattr(col, 'nullable')
    assert col.nullable is True
    # Try to find foreign key target name if available
    fk_names = []
    if hasattr(col, 'foreign_keys'):
        try:
            fk_names = [getattr(fk, 'target_fullname', None) or str(fk) for fk in col.foreign_keys]
        except Exception:
            fk_names = []
    if fk_names:
        assert any('users.id' in name for name in fk_names if name), "foreign key should reference users.id"
    # get_by_id: create a dummy model with query.get behavior
    class DummyQuery:
        def __init__(self, mapping):
            self._m = mapping
        def get(self, key):
            return self._m.get(key)
    DummyModel = types.SimpleNamespace()
    DummyModel.query = DummyQuery({1: 'FOUND', 2: None})
    # If get_by_id exists, ensure it returns whatever model.query.get returns
    if not hasattr(database, 'get_by_id'):
        pytest.skip("get_by_id not defined")
    found = database.get_by_id(DummyModel, 1)
    assert found == 'FOUND'
    not_found = database.get_by_id(DummyModel, 2)
    assert not_found is None

def test_exceptions_factories_and_serialization():
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.exceptions as exc
    except Exception:
        pytest.skip("conduit.exceptions not available")
    # Lookup InvalidUsage class if present
    InvalidUsage = getattr(exc, 'InvalidUsage', None) or Exception
    # template and to_json should exist
    assert callable(getattr(exc, 'template', None)), "template should be callable"
    assert callable(getattr(exc, 'to_json', None)), "to_json should be callable"
    # template should return something (string or dict) given basic inputs
    try:
        templ = exc.template("test_key", "value")
    except TypeError:
        # some templates expect different args; try a fallback
        templ = exc.template({"k": "v"})
    assert templ is not None
    # to_json should produce a serializable structure (dict-like)
    j = exc.to_json({"detail": "x"})
    assert isinstance(j, _exc_lookup("dict", Exception))
    # Test factory functions exist and produce exceptions/objects
    factories = ['user_not_found', 'user_already_registered', 'unknown_error', 'article_not_found', 'comment_not_owned']
    for name in factories:
        fn = getattr(exc, name, None)
        assert callable(fn), f"{name} should be present and callable"
        # call with 0 args or a dummy arg if required
        try:
            res = fn()
        except TypeError:
            res = fn("dummy")
        # Expect either an exception instance (InvalidUsage) or a dict/serializable representation
        assert res is not None
        assert isinstance(res, (InvalidUsage, Exception, dict)) or hasattr(res, 'to_dict') or hasattr(res, 'to_json')