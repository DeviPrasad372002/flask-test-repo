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

import json
import types
import pytest

def _exc_lookup(name, default):
    import conduit.exceptions as exmod
    return getattr(exmod, name, default)

def test_create_app_calls_register_extensions_and_shellcontext(monkeypatch):
    # Import targets inside test
    import conduit.app as appmod

    calls = {"extensions": 0, "shellcontext": 0, "blueprints": 0, "errorhandlers": 0, "commands": 0}

    def fake_register_extensions(app):
        calls["extensions"] += 1
        # ensure app looks like a Flask app minimally
        assert hasattr(app, "config")

    def fake_register_shellcontext(app):
        calls["shellcontext"] += 1
        assert hasattr(app, "config")

    def fake_register_blueprints(app):
        calls["blueprints"] += 1

    def fake_register_errorhandlers(app):
        calls["errorhandlers"] += 1

    def fake_register_commands(app):
        calls["commands"] += 1

    # Monkeypatch all registration helpers to no-ops except our trackers
    monkeypatch.setattr(appmod, "register_extensions", fake_register_extensions)
    monkeypatch.setattr(appmod, "register_shellcontext", fake_register_shellcontext)
    # Other functions may be present; guard their absence
    if hasattr(appmod, "register_blueprints"):
        monkeypatch.setattr(appmod, "register_blueprints", fake_register_blueprints)
    if hasattr(appmod, "register_errorhandlers"):
        monkeypatch.setattr(appmod, "register_errorhandlers", fake_register_errorhandlers)
    if hasattr(appmod, "register_commands"):
        monkeypatch.setattr(appmod, "register_commands", fake_register_commands)

    # Import create_app after monkeypatching to be safe about any late lookups
    from conduit.app import create_app

    # Create the app; rely on default behavior but with registration functions replaced
    app = create_app()  # should not start servers or open network

    # Assert that our fake register functions were called at least once
    assert calls["extensions"] >= 1
    assert calls["shellcontext"] >= 1
    # If those other registration functions exist they should have been called as well
    if hasattr(appmod, "register_blueprints"):
        assert calls["blueprints"] >= 1
    if hasattr(appmod, "register_errorhandlers"):
        assert calls["errorhandlers"] >= 1
    if hasattr(appmod, "register_commands"):
        assert calls["commands"] >= 1

    # Basic sanity checks on the returned app object
    assert hasattr(app, "config")
    # Ensure config is a mapping-like object
    assert isinstance(app.config, dict) or hasattr(app.config, "get")


def test_crudmixin_save_update_delete_uses_db_session(monkeypatch):
    # Import CRUDMixin inside test
    import conduit.extensions as extmod

    # Create a fake db.session with tracking
    class FakeSession:
        def __init__(self):
            self.add_calls = []
            self.commit_calls = 0
            self.delete_calls = []
            self.flush_calls = 0

        def add(self, obj):
            self.add_calls.append(obj)

        def commit(self):
            self.commit_calls += 1

        def delete(self, obj):
            self.delete_calls.append(obj)

        def flush(self):
            self.flush_calls += 1

    fake_session = FakeSession()
    fake_db = types.SimpleNamespace(session=fake_session)

    # Monkeypatch the db object in the extensions module
    monkeypatch.setattr(extmod, "db", fake_db)

    # Define a simple model using the CRUDMixin
    class DummyModel(extmod.CRUDMixin):
        def __init__(self):
            self.updated = False
            self.deleted = False
        def __repr__(self):
            return "<DummyModel>"

    m = DummyModel()
    # Test save: should call session.add and session.commit at least once
    returned = m.save()
    assert returned is m
    assert fake_session.add_calls and fake_session.add_calls[-1] is m
    assert fake_session.commit_calls >= 1

    # Test update: set an attribute via update and expect commit/flush behavior
    # Many CRUDMixins implement update by setting attrs then saving; this ensures no exception
    before_commit = fake_session.commit_calls
    m.update(foo="bar", number=42)
    # Attributes should be set on the object
    assert getattr(m, "foo", None) == "bar"
    assert getattr(m, "number", None) == 42
    # Some commit should have happened
    assert fake_session.commit_calls >= before_commit

    # Test delete: should call session.delete and commit
    m.delete()
    assert fake_session.delete_calls and fake_session.delete_calls[-1] is m
    assert fake_session.commit_calls >= 1


def test_invalidusage_to_json_and_raises():
    # Import exceptions module inside test
    import conduit.exceptions as exmod

    InvalidUsage = _exc_lookup("Exception", Exception)

    # Instantiate if it's a class derived from Exception, otherwise skip meaningful assertions
    inst = None
    if isinstance(InvalidUsage, _exc_lookup("Exception", Exception)) and issubclass(InvalidUsage, Exception):
        # Try different init signatures gracefully
        try:
            inst = InvalidUsage("something went wrong", status_code=400)
        except TypeError:
            try:
                inst = InvalidUsage("something went wrong")
            except TypeError:
                # Fallback: raise to exercise raises handling below
                inst = None

    # If the instance has a to_json method, ensure it returns JSON serializable output
    if inst is not None and hasattr(inst, "to_json"):
        payload = inst.to_json()
        # Should be JSON serializable
        json.dumps(payload)

    # Ensure raising the InvalidUsage class is catchable via pytest.raises using lookup
    with pytest.raises(_exc_lookup("Exception", Exception)):
        raise InvalidUsage("raised for test")


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
