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

import importlib
import pytest


def _find_attr(mod_names, attr_name):
    for m in mod_names:
        try:
            mod = importlib.import_module(m)
        except Exception:
            continue
        if hasattr(mod, attr_name):
            return getattr(mod, attr_name)
    return None


def _get_db_or_skip():
    db = _find_attr(
        ["conduit.extensions", "conduit.database", "conduit.app", "conduit"],
        "db",
    )
    if db is None:
        pytest.skip("SQLAlchemy db object not found in conduit extensions/database")
    return db


def _get_create_app_or_skip():
    try:
        mod = importlib.import_module("conduit.app")
    except Exception:
        pytest.skip("conduit.app not available")
    if not hasattr(mod, "create_app"):
        pytest.skip("create_app not found in conduit.app")
    return mod.create_app


def _get_test_config_or_skip():
    try:
        settings = importlib.import_module("conduit.settings")
    except Exception:
        pytest.skip("conduit.settings not available")
    for name in ("TestConfig", "DevConfig", "Config"):
        if hasattr(settings, name):
            return getattr(settings, name)
    pytest.skip("No TestConfig/DevConfig/Config found in conduit.settings")


def _get_crudmixin_or_skip():
    try:
        mod = importlib.import_module("conduit.extensions")
    except Exception:
        pytest.skip("conduit.extensions not available")
    if hasattr(mod, "CRUDMixin"):
        return getattr(mod, "CRUDMixin")
    pytest.skip("CRUDMixin not found in conduit.extensions")


def _get_surrogate_or_skip():
    try:
        mod = importlib.import_module("conduit.database")
    except Exception:
        pytest.skip("conduit.database not available")
    if hasattr(mod, "SurrogatePK"):
        return getattr(mod, "SurrogatePK")
    pytest.skip("SurrogatePK not found in conduit.database")


def _maybe_call(obj, name, *args, **kwargs):
    fn = getattr(obj, name, None)
    if callable(fn):
        return fn(*args, **kwargs)
    return None


def _safe_save(instance, db):
    if hasattr(instance, "save") and callable(getattr(instance, "save")):
        instance.save()
    else:
        db.session.add(instance)
        db.session.commit()


def _safe_delete(instance, db):
    if hasattr(instance, "delete") and callable(getattr(instance, "delete")):
        instance.delete()
    else:
        db.session.delete(instance)
        db.session.commit()


def test_crud_create_and_query_roundtrip():
    """Generated by ai-testgen with strict imports and safe shims."""
    create_app = _get_create_app_or_skip()
    TestConfig = _get_test_config_or_skip()
    db = _get_db_or_skip()
    CRUDMixin = _get_crudmixin_or_skip()

    # Build a test app with sqlite in-memory for determinism
    app = create_app(TestConfig)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True)

    with app.app_context():
        # Define a simple model dynamically that uses the project's db and CRUDMixin
        class Item(db.Model, CRUDMixin):
            __tablename__ = "test_items"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(80), unique=True, nullable=False)

            def __repr__(self):
                return "<Item %r>" % self.name

        # Ensure tables exist
        db.create_all()

        # Create an instance and persist it using the mixin if available
        item = Item(name="widget")
        _safe_save(item, db)

        # Query back
        q = db.session.query(Item).filter_by(name="widget").one_or_none()
        assert q is not None, "saved item was not found in DB"
        assert q.name == "widget"
        assert getattr(q, "id", None) is not None

        # Clean up via delete
        _safe_delete(q, db)
        q2 = db.session.query(Item).filter_by(name="widget").one_or_none()
        assert q2 is None


def test_crud_update_persists_changes():
    """Generated by ai-testgen with strict imports and safe shims."""
    create_app = _get_create_app_or_skip()
    TestConfig = _get_test_config_or_skip()
    db = _get_db_or_skip()
    CRUDMixin = _get_crudmixin_or_skip()

    app = create_app(TestConfig)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True)

    with app.app_context():
        class Thing(db.Model, CRUDMixin):
            __tablename__ = "test_things"
            id = db.Column(db.Integer, primary_key=True)
            label = db.Column(db.String(100), unique=True, nullable=False)
            value = db.Column(db.Integer, nullable=False, default=0)

        db.create_all()

        t = Thing(label="alpha", value=1)
        _safe_save(t, db)

        # Mutate and save again to ensure update path works
        t.value = 42
        _safe_save(t, db)

        loaded = db.session.query(Thing).filter_by(label="alpha").one_or_none()
        assert loaded is not None
        assert loaded.value == 42

        # teardown
        _safe_delete(loaded, db)


def test_surrogatepk_and_get_by_id_integration():
    """Generated by ai-testgen with strict imports and safe shims."""
    # This test ensures the SurrogatePK utility and database get_by_id behave as expected
    create_app = _get_create_app_or_skip()
    TestConfig = _get_test_config_or_skip()
    db = _get_db_or_skip()
    CRUDMixin = _get_crudmixin_or_skip()
    SurrogatePK = _get_surrogate_or_skip()

    # Try to import get_by_id utility if present
    try:
        db_mod = importlib.import_module("conduit.database")
    except Exception:
        pytest.skip("conduit.database not importable")
    get_by_id = getattr(db_mod, "get_by_id", None)
    if get_by_id is None:
        pytest.skip("get_by_id function not found in conduit.database")

    app = create_app(TestConfig)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True)

    with app.app_context():
        class Person(SurrogatePK, db.Model, CRUDMixin):
            __tablename__ = "test_people"
            # SurrogatePK typically provides an 'id' primary key

            name = db.Column(db.String(80), nullable=False)

            def __repr__(self):
                return "<Person %r>" % self.name

        db.create_all()

        p = Person(name="Ada")
        _safe_save(p, db)
        assert getattr(p, "id", None) is not None

        # Use the project's get_by_id helper
        found = get_by_id(Person, p.id)
        assert found is not None
        assert found.id == p.id
        assert found.name == "Ada"

        # cleanup
        _safe_delete(found, db)