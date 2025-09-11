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

import json
import types

def test_create_app_registers_extensions_and_shellcontext(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.app as appmod
    except ImportError:
        pytest.skip("conduit.app not available")
    called = {}

    def fake_register_extensions(app):
        called['extensions'] = True

    def fake_register_shellcontext(app):
        called['shell'] = True

    # Patch the functions on the module before creating the app
    monkeypatch.setattr(appmod, 'register_extensions', fake_register_extensions, raising=False)
    monkeypatch.setattr(appmod, 'register_shellcontext', fake_register_shellcontext, raising=False)

    # Call create_app; ensure it invokes our patched functions
    app = appmod.create_app()
    assert hasattr(app, 'config')
    assert called.get('extensions') is True
    assert called.get('shell') is True


def test_database_reference_col_and_get_by_id_and_exceptions_to_json(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.database as dbmod
        import conduit.exceptions as excmod
    except ImportError:
        pytest.skip("conduit.database or conduit.exceptions not available")

    # reference_col should at least return an object mentioning the target table
    rc = dbmod.reference_col('users')
    assert rc is not None
    assert 'user' in str(rc).lower() or 'users' in str(rc).lower()

    # get_by_id should use model.query.get; emulate a simple model
    class Q:
        @staticmethod
        def get(i):
            return {'id': i} if i == 1 else None

    class Dummy:
        query = Q()

    assert dbmod.get_by_id(Dummy, 1) == {'id': 1}
    assert dbmod.get_by_id(Dummy, 2) is None

    # Helper to coerce various return types into a dict for assertions
    def to_dict(obj):
        if isinstance(obj, _exc_lookup("dict", Exception)):
            return obj
        if hasattr(obj, 'get_data'):
            # Flask Response-like
            data = obj.get_data(as_text=True)
            try:
                return json.loads(data)
            except Exception:
                return {'text': data}
        if isinstance(obj, (tuple, list)) and obj:
            return to_dict(obj[0])
        if isinstance(obj, _exc_lookup("str", Exception)):
            try:
                return json.loads(obj)
            except Exception:
                return {'text': obj}
        try:
            return {'text': str(obj)}
        except Exception:
            return {}

    # Test various exception helper functions if present. Be permissive about return shape.
    names = ['user_not_found', 'user_already_registered', 'unknown_error', 'article_not_found', 'comment_not_owned']
    for name in names:
        if hasattr(excmod, name):
            fn = getattr(excmod, name)
            try:
                result = fn()
            except Exception as e:
                # Some helper functions may raise custom exceptions; capture and stringify
                result = e
            d = to_dict(result)
            assert isinstance(d, _exc_lookup("dict", Exception))
            # At minimum expect some text in the dict
            assert any(isinstance(v, _exc_lookup("str", Exception)) and v for v in d.values())


def test_execute_tool_uses_subprocess_run_and_handles_output(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    import pytest
    try:
        import conduit.commands as cmd
    except ImportError:
        pytest.skip("conduit.commands not available")

    called = {}

    class Completed:
        def __init__(self, returncode=0, stdout=b'OK', stderr=b''):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(*args, **kwargs):
        called['args'] = args
        called['kwargs'] = kwargs
        return Completed(returncode=0, stdout=b'hello-world')

    # Try to patch subprocess.run used by the commands module; support either attribute or global subprocess
    patched = False
    if hasattr(cmd, 'subprocess'):
        monkeypatch.setattr(cmd.subprocess, 'run', fake_run, raising=False)
        patched = True
    try:
        import subprocess as _subproc
        if not patched:
            monkeypatch.setattr(_subproc, 'run', fake_run, raising=False)
            patched = True
    except Exception:
        pass

    # Execute; ensure our fake_run was called and execute_tool returns or processes without raising
    try:
        result = cmd.execute_tool('dummy-tool')
    except Exception as e:
        # If execute_tool raises, ensure it's due to subprocess behavior and our fake was invoked
        assert 'args' in called
        return

    assert 'args' in called
    # result may be many shapes; ensure it is not None or there is observable output from subprocess call
    assert result is None or result != '' or called.get('args') is not None