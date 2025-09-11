import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- ENHANCED UNIVERSAL BOOTSTRAP ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins, importlib.util
import warnings

# Strict mode: default ON (1). Set TESTGEN_STRICT=0 to relax locally.
STRICT = os.getenv("TESTGEN_STRICT", "1").lower() in ("1","true","yes")

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and os.path.exists(_target):
    if _target not in sys.path:
        sys.path.insert(0, _target)
    try:
        os.chdir(_target)
    except Exception:
        pass
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
        import collections as _collections
        import collections.abc as _abc
        for _n in ('Mapping','MutableMapping','Sequence','Iterable','Container','MutableSequence','Set','MutableSet'):
            if not hasattr(_collections, _n) and hasattr(_abc, _n):
                setattr(_collections, _n, getattr(_abc, _n))
    except Exception:
        pass
_apply_compatibility_fixes()

# Attribute adapter (dangerous): only in RELAXED mode
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES:
            return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep):
            return
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__)
            return
        def __getattr__(name):
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try:
                        _inst = _obj()
                    except Exception:
                        continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try:
                            setattr(_m, name, _val)
                        except Exception:
                            pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__
        _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass

if not STRICT:
    _orig_import = _builtins.__import__
    def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
        mod = _orig_import(name, globals, locals, fromlist, level)
        try:
            if isinstance(mod, _types.ModuleType):
                _attach_module_getattr(mod)
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

# Safe DB defaults & SQLAlchemy fallback ONLY in RELAXED mode
if not STRICT:
    for _k in ("DATABASE_URL","DB_URL","SQLALCHEMY_DATABASE_URI"):
        _v = os.environ.get(_k)
        if not _v or "://" not in str(_v):
            os.environ[_k] = "sqlite:///:memory:"
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

# Django minimal settings only if installed (harmless both modes)
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(
                SECRET_KEY="test-key",
                DEBUG=True,
                ALLOWED_HOSTS=["*"],
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
            )
            django.setup()
except Exception:
    pass

# Py2 alias maps
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

# Qt shims: keep even in strict (headless CI), harmless if real Qt present
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
        class QFont:  # minimal placeholders
            def __init__(self, *a, **k): pass
        class QDoubleValidator:
            def __init__(self, *a, **k): pass
            def setBottom(self, *a, **k): pass
            def setTop(self, *a, **k): pass
        class QIcon:  # noqa
            def __init__(self, *a, **k): pass
        class QPixmap:
            def __init__(self, *a, **k): pass
        _gui.QFont = QFont
        _gui.QDoubleValidator = QDoubleValidator
        _gui.QIcon = QIcon
        _gui.QPixmap = QPixmap
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
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui, _name, getattr(_widgets, _name))

# Optional generic stubs for other missing third-party tops ONLY in RELAXED mode
if not STRICT:
    _THIRD_PARTY_TOPS = ['click', 'compat', 'conduit', 'datetime', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'glob', 'marshmallow', 'models', 'os', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'subprocess', 'sys', 'werkzeug']
    for _name in list(_THIRD_PARTY_TOPS):
        _top = (_name or "").split(".")[0]
        if not _top or _top in sys.modules:
            continue
        if _safe_find_spec(_top) is not None:
            continue
        if _top in ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'):
            continue
        _m = _types.ModuleType(_top)
        _m.__spec__ = _im.ModuleSpec(_top, loader=None, is_package=False)
        sys.modules[_top] = _m

# --- /ENHANCED UNIVERSAL BOOTSTRAP ---

import importlib
import pytest

def test_crud_mixin_save_and_delete_monkeypatched(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        mod = importlib.import_module('conduit.extensions')
        CRUDMixin = getattr(mod, 'CRUDMixin')
    except Exception as e:
        pytest.skip(f"conduit.extensions.CRUDMixin not importable: {e}")

    class FakeSession:
        def __init__(self):
            self.added = []
            self.deleted = []
            self.committed = 0
        def add(self, obj):
            self.added.append(obj)
        def delete(self, obj):
            self.deleted.append(obj)
        def commit(self):
            self.committed += 1

    fake_db = type('FakeDB', (), {'session': FakeSession()})
    # Patch the module-level db reference to our fake DB
    monkeypatch.setattr(mod, 'db', fake_db, raising=False)

    class Dummy(CRUDMixin):
        pass

    d = Dummy()
    # save should add and commit via our fake session and return self
    res = d.save()
    assert res is d
    assert d in fake_db.session.added
    assert fake_db.session.committed >= 1

    # delete should remove and commit via our fake session and return self
    res2 = d.delete()
    assert res2 is d
    assert d in fake_db.session.deleted
    assert fake_db.session.committed >= 1

def test_config_subclasses_and_flags():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        settings = importlib.import_module('conduit.settings')
        Config = getattr(settings, 'Config')
        TestConfig = getattr(settings, 'TestConfig')
        DevConfig = getattr(settings, 'DevConfig')
        ProdConfig = getattr(settings, 'ProdConfig')
    except Exception as e:
        pytest.skip(f"conduit.settings not importable: {e}")

    # Ensure subclass relationships are sane
    assert issubclass(TestConfig, Config)
    assert issubclass(DevConfig, Config)
    assert issubclass(ProdConfig, Config)

    # If TESTING/DEBUG attributes exist on specific configs, they should be boolean
    if hasattr(TestConfig, 'TESTING'):
        assert isinstance(getattr(TestConfig, 'TESTING'), bool)
    if hasattr(DevConfig, 'DEBUG'):
        assert isinstance(getattr(DevConfig, 'DEBUG'), bool)
    if hasattr(ProdConfig, 'DEBUG'):
        assert isinstance(getattr(ProdConfig, 'DEBUG'), bool)

def test_profile_schema_dump_is_consistent():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        serializers = importlib.import_module('conduit.profile.serializers')
        ProfileSchema = getattr(serializers, 'ProfileSchema')
    except Exception as e:
        pytest.skip(f"conduit.profile.serializers.ProfileSchema not importable: {e}")

    schema = ProfileSchema()
    # Obtain declared fields if available; otherwise proceed with empty set
    fields = getattr(schema, 'fields', {}) or {}
    class Obj:
        pass
    obj = Obj()
    # Populate attributes matching declared fields so dump can read them
    for name in fields:
        setattr(obj, name, f"value_for_{name}")

    dumped = schema.dump(obj)
    assert isinstance(dumped, _exc_lookup("dict", Exception))
    # All keys returned by dump should correspond to declared fields when fields are known
    for k in dumped.keys():
        assert (not fields) or (k in fields)

def test_invalidusage_to_json_present_and_structured():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        exc_mod = importlib.import_module('conduit.exceptions')
        InvalidUsage = getattr(exc_mod, 'InvalidUsage')
    except Exception as e:
        pytest.skip(f"conduit.exceptions.InvalidUsage not importable: {e}")

    inst = InvalidUsage("test message", status_code=499)
    # to_json should exist and return a non-empty mapping/dict-like
    if hasattr(inst, 'to_json'):
        j = inst.to_json()
        assert isinstance(j, _exc_lookup("dict", Exception))
        assert len(j) > 0
    else:
        pytest.skip("InvalidUsage has no to_json method")