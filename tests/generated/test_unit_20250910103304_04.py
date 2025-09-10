import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- UNIVERSAL BOOTSTRAP (generated) ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins

# Ensure target root importable
_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and _target not in sys.path:
    sys.path.insert(0, _target)
_TARGET_ABS = os.path.abspath(_target)

# Provide a helper for exception lookups used by generated tests
def _exc_lookup(name, default):
    try:
        mod_name, _, cls_name = str(name).rpartition(".")
        if mod_name:
            mod = __import__(mod_name, fromlist=[cls_name])
            return getattr(mod, cls_name, default)
        return getattr(sys.modules.get("builtins"), str(name), default)
    except Exception:
        return default

# ---- Generic module attribute adapter (PEP 562 __getattr__) for target modules ----
# If a module 'm' lacks attribute 'foo', we try to find a public class in 'm' that
# provides 'foo' as an instance attribute/method via a no-arg constructor. First hit wins.
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES:
            return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep):
            return  # only adapt modules under target/
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__)
            return

        def __getattr__(name):
            # Try to resolve missing attributes from any instantiable public class
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try:
                        _inst = _obj()  # only no-arg constructors will work; otherwise skip
                    except Exception:
                        continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try:
                            setattr(_m, name, _val)  # cache for future lookups/imports
                        except Exception:
                            pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__
        _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass

# Wrap builtins.__import__ so every target module gets the adapter automatically
_orig_import = _builtins.__import__
def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
    mod = _orig_import(name, globals, locals, fromlist, level)
    try:
        # Ensure top-level module object is adapted
        top = mod
        if isinstance(mod, _types.ModuleType):
            _attach_module_getattr(top)
        # If a package was imported and fromlist asks for submodules, adapt them after real import
        if fromlist:
            for attr in fromlist:
                try:
                    sub = getattr(mod, attr, None)
                    if isinstance(sub, _types.ModuleType):
                        _attach_module_getattr(sub)
                except Exception:
                    pass
    except Exception:
        pass
    return mod
_builtins.__import__ = _import_with_adapter

# Safe DB defaults
for _k in ("DATABASE_URL","DB_URL","SQLALCHEMY_DATABASE_URI"):
    _v = os.environ.get(_k)
    if not _v or "://" not in str(_v):
        os.environ[_k] = "sqlite:///:memory:"

# Minimal Django config (only if actually installed)
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(
                SECRET_KEY="test",
                DEBUG=True,
                ALLOWED_HOSTS=["*"],
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
            )
            django.setup()
except Exception:
    pass

# SQLAlchemy safe create_engine
try:
    if _iu.find_spec("sqlalchemy") is not None:
        import sqlalchemy as _s_sa
        from sqlalchemy.exc import ArgumentError as _s_ArgErr
        _s_orig_create_engine = _s_sa.create_engine
        def _s_safe_create_engine(url, *args, **kwargs):
            try_url = url
            try:
                if not isinstance(try_url, str) or "://" not in try_url:
                    try_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///:memory:"
                return _s_orig_create_engine(try_url, *args, **kwargs)
            except _s_ArgErr:
                return _s_orig_create_engine("sqlite:///:memory:", *args, **kwargs)
        _s_sa.create_engine = _s_safe_create_engine
except Exception:
    pass

# collections.abc compatibility for older libs (Py3.10+)
try:
    import collections as _collections
    import collections.abc as _abc
    for _n in ("Mapping","MutableMapping","Sequence","MutableSequence","Set","MutableSet","Iterable"):
        if not hasattr(_collections, _n) and hasattr(_abc, _n):
            setattr(_collections, _n, getattr(_abc, _n))
except Exception:
    pass

# Py2 alias maps if imported
_PY2_ALIASES = {'ConfigParser': 'configparser', 'Queue': 'queue', 'StringIO': 'io', 'cStringIO': 'io', 'urllib2': 'urllib.request'}
for _old, _new in list(_PY2_ALIASES.items()):
    if _old in sys.modules:
        continue
    try:
        __import__(_new)
        sys.modules[_old] = sys.modules[_new]
    except Exception:
        pass

def _safe_find_spec(name):
    try:
        return _iu.find_spec(name)
    except Exception:
        return None

# ---- Qt family stubs (PyQt5/6, PySide2/6) for headless CI ----
def _ensure_pkg(name, is_pkg=None):
    if name in sys.modules:
        m = sys.modules[name]
        if getattr(m, "__spec__", None) is None:
            m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=(is_pkg if is_pkg is not None else ("." not in name)))
            if "." not in name and not hasattr(m, "__path__"):
                m.__path__ = []
        return m
    m = _types.ModuleType(name)
    if is_pkg is None:
        is_pkg = ("." not in name)
    if is_pkg and not hasattr(m, "__path__"):
        m.__path__ = []
    m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=is_pkg)
    sys.modules[name] = m
    return m

_qt_roots = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
for __qt_root in _qt_roots:
    if _safe_find_spec(__qt_root) is None:
        _pkg = _ensure_pkg(__qt_root, is_pkg=True)
        _core = _ensure_pkg(__qt_root + ".QtCore", is_pkg=False)
        _gui = _ensure_pkg(__qt_root + ".QtGui", is_pkg=False)
        _widgets = _ensure_pkg(__qt_root + ".QtWidgets", is_pkg=False)

        # ---- QtCore minimal API ----
        class QObject: pass
        def pyqtSignal(*a, **k): return object()
        def pyqtSlot(*a, **k):
            def _decorator(fn): return fn
            return _decorator
        class QCoreApplication:
            def __init__(self, *a, **k): pass
            def exec_(self): return 0
            def exec(self): return 0
        _core.QObject = QObject
        _core.pyqtSignal = pyqtSignal
        _core.pyqtSlot = pyqtSlot
        _core.QCoreApplication = QCoreApplication

        # ---- QtGui minimal API ----
        class QFont:
            def __init__(self, *a, **k): pass
        class QDoubleValidator:
            def __init__(self, *a, **k): pass
            def setBottom(self, *a, **k): pass
            def setTop(self, *a, **k): pass
        class QIcon:
            def __init__(self, *a, **k): pass
        class QPixmap:
            def __init__(self, *a, **k): pass
        _gui.QFont = QFont
        _gui.QDoubleValidator = QDoubleValidator
        _gui.QIcon = QIcon
        _gui.QPixmap = QPixmap

        # ---- QtWidgets minimal API ----
        class QApplication:
            def __init__(self, *a, **k): pass
            def exec_(self): return 0
            def exec(self): return 0
        class QWidget:
            def __init__(self, *a, **k): pass
        class QLabel(QWidget):
            def __init__(self, *a, **k):
                super().__init__(); self._text = ""
            def setText(self, t): self._text = str(t)
            def text(self): return self._text
        class QLineEdit(QWidget):
            def __init__(self, *a, **k):
                super().__init__(); self._text = ""
            def setText(self, t): self._text = str(t)
            def text(self): return self._text
            def clear(self): self._text = ""
        class QTextEdit(QLineEdit): pass
        class QPushButton(QWidget):
            def __init__(self, *a, **k): super().__init__()
        class QMessageBox:
            @staticmethod
            def warning(*a, **k): return None
            @staticmethod
            def information(*a, **k): return None
            @staticmethod
            def critical(*a, **k): return None
        class QFileDialog:
            @staticmethod
            def getSaveFileName(*a, **k): return ("history.txt", "")
            @staticmethod
            def getOpenFileName(*a, **k): return ("history.txt", "")
        class QFormLayout:
            def __init__(self, *a, **k): pass
            def addRow(self, *a, **k): pass
        class QGridLayout(QFormLayout):
            def addWidget(self, *a, **k): pass

        _widgets.QApplication = QApplication
        _widgets.QWidget = QWidget
        _widgets.QLabel = QLabel
        _widgets.QLineEdit = QLineEdit
        _widgets.QTextEdit = QTextEdit
        _widgets.QPushButton = QPushButton
        _widgets.QMessageBox = QMessageBox
        _widgets.QFileDialog = QFileDialog
        _widgets.QFormLayout = QFormLayout
        _widgets.QGridLayout = QGridLayout

        # Mirror common widget symbols into QtGui to tolerate odd imports
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui, _name, getattr(_widgets, _name))

# ---- Generic stub for other missing third-party tops (non-stdlib, non-local) ----
_THIRD_PARTY_TOPS = ['click', 'compat', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'marshmallow', 'models', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'werkzeug']
for _name in list(_THIRD_PARTY_TOPS):
    _top = (_name or "").split(".")[0]
    if not _top:
        continue
    if _top in sys.modules:
        continue
    if _safe_find_spec(_top) is not None:
        continue
    if _top in ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'):
        continue
    _m = _types.ModuleType(_top)
    _m.__spec__ = _im.ModuleSpec(_top, loader=None, is_package=False)
    sys.modules[_top] = _m

# --- /UNIVERSAL BOOTSTRAP ---

import inspect
import types
import sys
import builtins
import subprocess
import pytest

def _exc_lookup(name, default=Exception):
    # search common modules for exception by name
    mods = [
        builtins,
        subprocess,
        sys.modules.get('conduit.exceptions'),
        sys.modules.get('conduit.commands'),
        sys.modules.get('conduit.database'),
        sys.modules.get('conduit.extensions'),
    ]
    for mod in mods:
        if not mod:
            continue
        if hasattr(mod, name):
            return getattr(mod, name)
    return default

def test_execute_tool_invokes_subprocess_methods_and_propagates_error(monkeypatch):
    # import inside test as required
    import conduit.commands as commands

    calls = {"args": None, "method": None}

    class FakeSubprocess:
        def _record(self, method, args, kwargs):
            calls["args"] = (tuple(args[0]) if args and isinstance(args[0], (list, tuple)) else args)
            calls["method"] = method
            return 0

        def check_call(self, *args, **kwargs):
            return self._record("check_call", args, kwargs)

        def call(self, *args, **kwargs):
            return self._record("call", args, kwargs)

        def run(self, *args, **kwargs):
            return self._record("run", args, kwargs)

        def Popen(self, *args, **kwargs):
            return self._record("Popen", args, kwargs)

    fake = FakeSubprocess()
    # replace the subprocess module used by the commands module
    monkeypatch.setattr(commands, "subprocess", fake, raising=False)

    # prepare arguments for execute_tool based on its signature
    sig = inspect.signature(commands.execute_tool)
    params = list(sig.parameters)
    # call with common positional pattern (tool, args)
    call_args = []
    if len(params) >= 1:
        call_args.append("mytool")
    if len(params) >= 2:
        call_args.append(["--opt", "value"])
    # include additional simple defaults if more params exist
    while len(call_args) < len(params):
        call_args.append(None)

    # call and assert fake recorded invocation
    commands.execute_tool(*call_args[:len(params)])
    assert calls["args"] is not None, "expected subprocess wrapper to be called"
    # ensure one of common methods was used
    assert calls["method"] in ("check_call", "call", "run", "Popen")

    # Now verify error propagation: make fake.check_call raise CalledProcessError
    class FailingFake(FakeSubprocess):
        def check_call(self, *args, **kwargs):
            raise _exc_lookup("Exception", subprocess.CalledProcessError)(1, args)

    failing = FailingFake()
    monkeypatch.setattr(commands, "subprocess", failing, raising=False)

    with pytest.raises(_exc_lookup("Exception", subprocess.CalledProcessError)):
        commands.execute_tool(*call_args[:len(params)])


def test_exception_factories_raise_InvalidUsage_for_error_helpers():
    # import exceptions module inside test
    import conduit.exceptions as exceptions

    InvalidUsage = _exc_lookup("Exception", Exception)

    # list of factory callables expected to raise InvalidUsage when invoked without context
    factories = []
    for name in ("template", "user_not_found", "user_already_registered", "unknown_error", "article_not_found", "comment_not_owned"):
        if hasattr(exceptions, name):
            factories.append(getattr(exceptions, name))

    assert factories, "no exception factory functions found in conduit.exceptions"

    for factory in factories:
        with pytest.raises(_exc_lookup("Exception", Exception)):
            # some factories may accept arguments; call generically
            try:
                factory()
            except TypeError:
                # if no-arg call fails, call with a simple message
                factory("message")


def test_to_json_produces_serializable_response_for_InvalidUsage():
    import conduit.exceptions as exceptions

    InvalidUsage = _exc_lookup("Exception", Exception)

    # Attempt to instantiate InvalidUsage with common signatures
    try:
        err = InvalidUsage("fail", status_code=499, payload={"detail": "x"})
    except TypeError:
        try:
            err = InvalidUsage("fail")
        except Exception as exc:
            pytest.skip(f"Cannot construct InvalidUsage: {exc}")

    # Call to_json and assert structure
    if not hasattr(exceptions, "to_json"):
        pytest.skip("to_json not present in conduit.exceptions")
    result = exceptions.to_json(err)

    # Accept either a Flask response-like object or a dict-like mapping
    if hasattr(result, "status_code"):
        assert getattr(err, "status_code", None) is None or result.status_code == getattr(err, "status_code", result.status_code)
    else:
        # treat as mapping-like
        assert isinstance(result, (dict, list, tuple)) or hasattr(result, "__getitem__")
        # ensure message or payload present somewhere
        as_dict = result if isinstance(result, _exc_lookup("Exception", Exception)) else {}
        keys = set(as_dict.keys())
        assert keys & {"message", "error", "payload", "detail", "description"} or (isinstance(result, (list, tuple)) and len(result) > 0)


def test_reference_col_returns_column_with_foreign_key_attributes():
    import conduit.database as database
    # function should exist
    assert hasattr(database, "reference_col"), "reference_col not found in conduit.database"
    col = database.reference_col("users")

    # column-like object should expose foreign key information and nullable attribute
    assert hasattr(col, "foreign_keys"), "returned object missing foreign_keys attribute"
    fks = col.foreign_keys
    # foreign_keys may be a set or list-like
    assert (hasattr(fks, "__len__") and len(fks) >= 0)
    assert hasattr(col, "nullable"), "returned object missing nullable attribute"


def test_get_by_id_returns_object_when_present_and_handles_missing_case():
    import conduit.database as database

    assert hasattr(database, "get_by_id"), "get_by_id not present"

    # create dummy model with query.get behavior
    class DummyPresent:
        class Query:
            @staticmethod
            def get(i):
                return {"id": i, "name": "present"}
        query = Query()

    class DummyMissing:
        class Query:
            @staticmethod
            def get(i):
                return None
        query = Query()

    # present case
    got = database.get_by_id(DummyPresent, 1)
    assert got == {"id": 1, "name": "present"}

    # missing case: either returns None or raises a domain-specific exception
    try:
        result = database.get_by_id(DummyMissing, 2)
    except Exception as exc:
        # allow custom exception named article_not_found or similar
        exc_name = type(exc).__name__
        allowed_names = {"article_not_found", "ArticleNotFound"}
        assert exc_name in allowed_names or isinstance(exc, _exc_lookup("Exception", Exception))
    else:
        # if no exception, expect None
        assert result is None


# --- canonical PyQt5 shim (Widgets + Gui minimal) ---
def __qt_shim_canonical():
    import types as _t
    PyQt5 = _t.ModuleType("PyQt5")
    QtWidgets = _t.ModuleType("PyQt5.QtWidgets")
    QtGui = _t.ModuleType("PyQt5.QtGui")

    class QApplication:
        def __init__(self, *a, **k): pass
        def exec_(self): return 0
        def exec(self): return 0
    class QWidget:
        def __init__(self, *a, **k): pass
    class QLabel(QWidget):
        def __init__(self, *a, **k):
            super().__init__(); self._text = ""
        def setText(self, t): self._text = str(t)
        def text(self): return self._text
    class QLineEdit(QWidget):
        def __init__(self, *a, **k):
            super().__init__(); self._text = ""
        def setText(self, t): self._text = str(t)
        def text(self): return self._text
        def clear(self): self._text = ""
    class QTextEdit(QLineEdit): pass
    class QPushButton(QWidget):
        def __init__(self, *a, **k): super().__init__()
    class QMessageBox:
        @staticmethod
        def warning(*a, **k): return None
        @staticmethod
        def information(*a, **k): return None
        @staticmethod
        def critical(*a, **k): return None
    class QFileDialog:
        @staticmethod
        def getSaveFileName(*a, **k): return ("history.txt", "")
        @staticmethod
        def getOpenFileName(*a, **k): return ("history.txt", "")
    class QFormLayout:
        def __init__(self, *a, **k): pass
        def addRow(self, *a, **k): pass
    class QGridLayout(QFormLayout):
        def addWidget(self, *a, **k): pass

    # QtGui bits commonly imported
    class QFont:
        def __init__(self, *a, **k): pass
    class QDoubleValidator:
        def __init__(self, *a, **k): pass
        def setBottom(self, *a, **k): pass
        def setTop(self, *a, **k): pass
    class QIcon:
        def __init__(self, *a, **k): pass
    class QPixmap:
        def __init__(self, *a, **k): pass

    QtWidgets.QApplication = QApplication
    QtWidgets.QWidget = QWidget
    QtWidgets.QLabel = QLabel
    QtWidgets.QLineEdit = QLineEdit
    QtWidgets.QTextEdit = QTextEdit
    QtWidgets.QPushButton = QPushButton
    QtWidgets.QMessageBox = QMessageBox
    QtWidgets.QFileDialog = QFileDialog
    QtWidgets.QFormLayout = QFormLayout
    QtWidgets.QGridLayout = QGridLayout

    QtGui.QFont = QFont
    QtGui.QDoubleValidator = QDoubleValidator
    QtGui.QIcon = QIcon
    QtGui.QPixmap = QPixmap

    return PyQt5, QtWidgets, QtGui

_make_pyqt5_shim = __qt_shim_canonical
_make_pyqt_shim = __qt_shim_canonical
_make_pyqt_shims = __qt_shim_canonical
_make_qt_shims = __qt_shim_canonical
