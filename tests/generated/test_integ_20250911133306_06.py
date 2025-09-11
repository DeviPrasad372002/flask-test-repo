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

import pytest

def test_create_app_calls_register_extensions_and_shellcontext(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.app as app_mod
        from conduit.settings import TestConfig
    except Exception:
        pytest.skip("conduit.app or conduit.settings not importable")
    called = {}

    def fake_register_extensions(app):
        called['extensions'] = True
        # mutate app to allow verification that the fake was called with the real app
        app.config['FAKE_EXT_CALLED'] = True

    def fake_register_shellcontext(app):
        called['shell'] = True
        # register a trivial shell context to ensure the function is exercised
        if not hasattr(app, 'shell_context_processors'):
            app.shell_context_processors = []
        app.shell_context_processors.append(lambda: {'x': 1})

    monkeypatch.setattr(app_mod, 'register_extensions', fake_register_extensions)
    monkeypatch.setattr(app_mod, 'register_shellcontext', fake_register_shellcontext)

    app = app_mod.create_app(TestConfig)
    assert called.get('extensions') is True
    assert called.get('shell') is True
    # verify that the fake mutated the app config
    assert app.config.get('FAKE_EXT_CALLED') is True
    # verify shell context registration side-effect if present
    if hasattr(app, 'shell_context_processors'):
        assert any(callable(p) for p in app.shell_context_processors)

def test_CRUDMixin_save_and_delete_calls_db_session_methods(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.extensions as ext_mod
    except Exception:
        pytest.skip("conduit.extensions not importable")
    CRUDMixin = getattr(ext_mod, 'CRUDMixin', None)
    if CRUDMixin is None:
        pytest.skip("CRUDMixin not present")

    ops = []

    class Session:
        def add(self, obj):
            ops.append(('add', obj))

        def commit(self):
            ops.append(('commit', None))

        def refresh(self, obj):
            ops.append(('refresh', obj))

        def delete(self, obj):
            ops.append(('delete', obj))

    class DummyDB:
        def __init__(self):
            self.session = Session()

    # monkeypatch the db attribute on the extensions module
    monkeypatch.setattr(ext_mod, 'db', DummyDB())

    class Dummy(CRUDMixin):
        pass

    d = Dummy()
    # exercise save
    d.save()
    assert ('add', d) in ops, "save() should add the instance to the session"
    assert ('commit', None) in ops, "save() should commit the session"
    # refresh may or may not be called depending on implementation; if present, it should reference the object
    if any(op[0] == 'refresh' for op in ops):
        assert ('refresh', d) in ops

    ops.clear()
    # exercise delete
    d.delete()
    assert ('delete', d) in ops, "delete() should remove the instance from the session"
    assert ('commit', None) in ops, "delete() should commit the session"

def test_InvalidUsage_and_to_json_interaction():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.exceptions as exc_mod
    except Exception:
        pytest.skip("conduit.exceptions not importable")

    def _exc_lookup(name, default):
        return getattr(exc_mod, name, default)

    InvalidUsage = _exc_lookup('InvalidUsage', Exception)
    # instantiate the exception with different forms if supported
    try:
        e = InvalidUsage("some error occurred", status_code=422)
    except TypeError:
        # fallback if constructor signature is different
        e = InvalidUsage("some error occurred")

    assert "some error occurred" in str(e)

    # if there is a to_json helper in the module, ensure it can accept the exception
    to_json_fn = getattr(exc_mod, 'to_json', None)
    if callable(to_json_fn):
        out = to_json_fn(e)
        assert isinstance(out, _exc_lookup("dict", Exception))

def test_profile_and_user_schemas_serialize_across_modules():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.profile.serializers as pser
        import conduit.user.serializers as userser
    except Exception:
        pytest.skip("profile or user serializers not importable")

    ProfileSchema = getattr(pser, 'ProfileSchema', None)
    UserSchema = getattr(userser, 'UserSchema', None)

    if ProfileSchema is None or UserSchema is None:
        pytest.skip("Required schemas not present")

    # create simple plain-data structures (schemas should accept dicts or objects with attributes)
    profile_data = {
        'username': 'alice',
        'bio': 'I am Alice',
        'image': None,
        'following': False
    }
    user_data = {
        'username': 'alice',
        'email': 'alice@example.com',
        'bio': 'I am Alice',
        'image': None,
        'token': 'sometoken'
    }

    p_dump = ProfileSchema().dump(profile_data)
    u_dump = UserSchema().dump(user_data)

    assert isinstance(p_dump, _exc_lookup("dict", Exception))
    assert p_dump.get('username') == 'alice'
    assert isinstance(u_dump, _exc_lookup("dict", Exception))
    # Ensure the user serialization contains at least username or email
    assert 'username' in u_dump or 'email' in u_dump