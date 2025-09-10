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
import pytest

def _try_call(func, *candidates):
    """
    Try calling func with various positional/keyword patterns provided in candidates.
    Each candidate is a tuple (args, kwargs). Returns the first successful result.
    Raises the last exception if all fail.
    """
    last_exc = None
    for args, kwargs in candidates:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
    # Re-raise the last exception to give full failure context
    raise last_exc

def _contains_value(obj, value):
    """Recursively search for value in mappings, iterables, or strings."""
    if obj is None:
        return False
    if isinstance(obj, _exc_lookup("Exception", Exception)):
        return value in obj
    if isinstance(obj, _exc_lookup("Exception", Exception)):
        for k, v in obj.items():
            if _contains_value(k, value) or _contains_value(v, value):
                return True
        return False
    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            if _contains_value(item, value):
                return True
        return False
    # fallback to attribute inspection
    try:
        for attr in ('title', 'body', 'description'):
            if hasattr(obj, attr) and _contains_value(getattr(obj, attr), value):
                return True
    except Exception:
        pass
    return False

def _call_flexibly(func, primary_arg):
    """
    Try a few calling conventions for functions whose exact signature can vary
    between versions. Returns the function's result.
    """
    sig = None
    try:
        sig = inspect.signature(func)
    except Exception:
        sig = None

    candidates = []
    # Try raw object/dict as sole positional
    candidates.append(((primary_arg,), {}))
    # Try wrapped under 'article' / 'comment' keys
    candidates.append((( {'article': primary_arg}, ), {}))
    candidates.append((( {'comment': primary_arg}, ), {}))
    # Try as keyword unpack if primary_arg is a dict
    if isinstance(primary_arg, _exc_lookup("Exception", Exception)):
        candidates.append(((), primary_arg))
    # If signature shows a single parameter name 'data' or 'obj', try kwargs
    if sig:
        for name, p in sig.parameters.items():
            if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                candidates.append(((), {name: primary_arg}))
                break
    return _try_call(func, *candidates)

def test_make_and_dump_article_roundtrip():
    # Integration between serializers: make_article -> dump_article
    from conduit.articles import serializers as s_mod

    # Build a representative article payload
    payload = {
        "title": "Integration Test Title",
        "description": "Short desc",
        "body": "Full body text of the article used for serializer roundtrip.",
        "tagList": ["testing", "integration"],
    }

    # Try to locate make_article and dump_article in the module
    assert hasattr(s_mod, "make_article"), "make_article not found in serializers module"
    assert hasattr(s_mod, "dump_article"), "dump_article not found in serializers module"

    make_article = s_mod.make_article
    dump_article = s_mod.dump_article

    # Create article-like object using flexible calling
    article_obj = _call_flexibly(make_article, payload)

    # Serialize back
    dumped = _call_flexibly(dump_article, article_obj)

    # Ensure the resulting serialization contains some of the original content
    assert _contains_value(dumped, payload["title"]), "Serialized output does not contain the article title"
    assert _contains_value(dumped, payload["body"]), "Serialized output does not contain the article body"

def test_dump_articles_with_multiple_entries():
    # Integration: make multiple articles then dump_articles
    from conduit.articles import serializers as s_mod

    assert hasattr(s_mod, "make_article"), "make_article not found in serializers module"
    assert hasattr(s_mod, "dump_articles"), "dump_articles not found in serializers module"

    make_article = s_mod.make_article
    dump_articles = s_mod.dump_articles

    payloads = [
        {"title": "First", "description": "d1", "body": "b1", "tagList": ["a"]},
        {"title": "Second", "description": "d2", "body": "b2", "tagList": ["b"]},
    ]

    created = []
    for p in payloads:
        created.append(_call_flexibly(make_article, p))

    # Try calling dump_articles with either a list or with a keyword wrapper
    try:
        dumped = _try_call(dump_articles,
                           (((created,), {}),),
                           ((({"articles": created},), {}),),
                           (((created,), {"many": True}),))
    except Exception:
        # Fall back to trying a single flexible wrapper call
        dumped = _call_flexibly(dump_articles, created)

    # Ensure both titles appear somewhere in the dumped representation
    for p in payloads:
        assert _contains_value(dumped, p["title"]), f"Dumped articles missing title {p['title']}"

def test_make_and_dump_comment_integration_with_article():
    # Integration across comment serializers and article serializer: attach comment to article-like object
    from conduit.articles import serializers as s_mod

    assert hasattr(s_mod, "make_comment"), "make_comment not found in serializers module"
    assert hasattr(s_mod, "dump_comment"), "dump_comment not found in serializers module"
    assert hasattr(s_mod, "make_article"), "make_article not found in serializers module"
    assert hasattr(s_mod, "dump_article"), "dump_article not found in serializers module"

    make_comment = s_mod.make_comment
    dump_comment = s_mod.dump_comment
    make_article = s_mod.make_article
    dump_article = s_mod.dump_article

    article_payload = {
        "title": "Article for comments",
        "description": "desc",
        "body": "body",
        "tagList": ["c"]
    }
    comment_payload = {"body": "This is a test comment body"}

    article_obj = _call_flexibly(make_article, article_payload)
    comment_obj = _call_flexibly(make_comment, comment_payload)

    # Many implementations expect comments to be a collection attribute on the article.
    # Attach comments heuristically.
    try:
        # Prefer standard attribute names if present
        if hasattr(article_obj, "comments"):
            getattr(article_obj, "comments").append(comment_obj)
        elif hasattr(article_obj, "comment_list"):
            getattr(article_obj, "comment_list").append(comment_obj)
        else:
            # Try setting an attribute
            setattr(article_obj, "comments", [comment_obj])
    except Exception:
        # If attaching fails, proceed to independently serialize comment and article
        pass

    dumped_comment = _call_flexibly(dump_comment, comment_obj)
    dumped_article = _call_flexibly(dump_article, article_obj)

    # Ensure comment body is serialized
    assert _contains_value(dumped_comment, comment_payload["body"]), "Serialized comment missing its body"

    # If comments were attached to the article and serialization includes them, ensure presence
    if _contains_value(dumped_article, comment_payload["body"]):
        assert True
    else:
        # If not included, at least the article's title and body should be present
        assert _contains_value(dumped_article, article_payload["title"])
        assert _contains_value(dumped_article, article_payload["body"])


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
