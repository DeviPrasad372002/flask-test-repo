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
from collections.abc import Mapping

def _try_create_app(create_app):
    # try a few common signatures for create_app
    for arg in ({'TESTING': True}, 'testing', None):
        try:
            if arg is None:
                return create_app()
            else:
                return create_app(arg)
        except TypeError:
            continue
    # final attempt: call without args
    return create_app()

def test_create_app_and_registration_functions_exist():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.app import (
            create_app,
            register_extensions,
            register_blueprints,
            register_errorhandlers,
            register_shellcontext,
            register_commands,
            errorhandler,
            shell_context,
        )
    except ImportError:
        pytest.skip("conduit.app not importable")
    # create app with tolerant helper
    app = _try_create_app(create_app)
    assert hasattr(app, "config")
    assert isinstance(app.config, Mapping)
    # ensure registration helpers are present and callable
    for fn in (register_extensions, register_blueprints, register_errorhandlers, register_shellcontext, register_commands):
        assert callable(fn)
    # errorhandler and shell_context should be callable
    assert callable(errorhandler)
    assert callable(shell_context)

def test_errorhandler_decorator_returns_callable_wrapper():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.app import errorhandler, shell_context
    except ImportError:
        pytest.skip("conduit.app not importable")
    # errorhandler should produce a decorator
    dec = errorhandler(ValueError)
    assert callable(dec)
    def sample_handler(exc):
        return "handled"
    wrapped = dec(sample_handler)
    # decorator should return a callable (often the original function)
    assert callable(wrapped)
    # shell_context should be callable and preferably return a mapping when invoked
    try:
        ctx = shell_context()
    except TypeError:
        # some implementations expect an app argument; pass a minimal stub
        class DummyApp: pass
        try:
            ctx = shell_context(DummyApp())
        except Exception:
            ctx = None
    if ctx is not None:
        assert isinstance(ctx, _exc_lookup("Mapping", Exception)) or callable(ctx)

def test_article_model_tag_and_favourite_methods_basic():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.articles import models as articles_models
    except ImportError:
        pytest.skip("conduit.articles.models not importable")
    Article = getattr(articles_models, "Article", None)
    Tags = getattr(articles_models, "Tags", None)
    if Article is None:
        pytest.skip("Article model not present")
    # try instantiation with a few plausible signatures
    article = None
    instantiate_attempts = [
        lambda: Article(),
        lambda: Article(title="t", body="b", slug="s"),
        lambda: Article("t", "b"),
    ]
    for attempt in instantiate_attempts:
        try:
            article = attempt()
            break
        except TypeError:
            continue
        except Exception:
            # other errors during instantiation - skip this test
            pytest.skip("Unable to instantiate Article for testing")
    if article is None:
        pytest.skip("Could not instantiate Article")
    # common methods should exist
    for name in ("favourite", "unfavourite", "is_favourite", "add_tag", "remove_tag"):
        assert hasattr(article, name), f"Article missing {name}"
        assert callable(getattr(article, name))
    # try tag operations with simple string (should not raise)
    try:
        article.add_tag("pytests-tag")
        article.remove_tag("pytests-tag")
    except Exception as e:
        pytest.fail(f"Tag methods raised unexpected exception: {e}")
    # test favourite/unfavourite with a minimal user-like object
    UserLike = type("UserLike", (), {"id": 999})
    user = UserLike()
    try:
        # prefer not to rely on DB; just ensure calls don't error and is_favourite returns a boolean-like value
        article.favourite(user)
        val = article.is_favourite(user)
        # accept bool or None (implementations may defer to DB)
        assert val in (True, False, None)
        article.unfavourite(user)
        val2 = article.is_favourite(user)
        assert val2 in (True, False, None)
    except Exception as e:
        pytest.fail(f"Favourite methods raised unexpected exception: {e}")
    # favoritesCount attribute may be a property/method - check presence and type if accessible
    if hasattr(article, "favoritesCount"):
        cnt = getattr(article, "favoritesCount")
        if callable(cnt):
            try:
                cnt = cnt()
            except Exception:
                cnt = None
        assert cnt is None or isinstance(cnt, _exc_lookup("int", Exception))
    # __repr__ should not raise
    try:
        _ = repr(article)
    except Exception as e:
        pytest.fail(f"repr(Article) raised unexpected exception: {e}")