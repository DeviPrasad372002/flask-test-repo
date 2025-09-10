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

import types
import pytest

def _invoke_maybe(fn, self_obj, *args, **kwargs):
    # Try calling fn(*args) first; if TypeError, try fn(self_obj, *args)
    try:
        return fn(*args, **kwargs)
    except TypeError:
        return fn(self_obj, *args, **kwargs)

def _extract_article_payload(payload):
    # payload might be a dict of article fields, or {"article": {...}}, or {"articles": [...]}.
    if payload is None:
        return None
    if isinstance(payload, dict):
        if "article" in payload and isinstance(payload["article"], dict):
            return payload["article"]
        # common serializer returns article fields at top level
        # or returns {'articles': [ ... ]}
        if "articles" in payload and isinstance(payload["articles"], list) and payload["articles"]:
            return payload["articles"][0]
        # if keys look like article fields, return as-is
        return payload
    return payload

def _safe_make_article(make_article_fn, data):
    # Try various call styles to construct an Article-like object
    try:
        return make_article_fn(data)
    except TypeError:
        # maybe signature is (current_user, data)
        try:
            return make_article_fn(None, data)
        except TypeError:
            # maybe signature is (**data)
            try:
                return make_article_fn(**data)
            except Exception:
                # last resort: try constructing Article class if provided instead of function
                raise

def test_article_tag_lifecycle_and_dump():
    # E2E-like flow: create article object, manage tags, and verify serializer output
    from conduit.articles import serializers as art_serializers
    from conduit.articles import models as art_models

    make_article_fn = getattr(art_serializers, "make_article", None)
    dump_article_fn = getattr(art_serializers, "dump_article", None)

    # Prepare input
    data = {"title": "E2E Tag Test", "description": "desc", "body": "content", "tagList": ["init"]}

    # Create article via available constructor/serializer
    if make_article_fn:
        article = _safe_make_article(make_article_fn, data)
    else:
        # fallback: try to instantiate Article class directly
        Article = getattr(art_models, "Article")
        try:
            article = Article()
        except TypeError:
            # try with common kwargs
            article = Article(title=data["title"], description=data["description"], body=data["body"])

    # Locate add_tag and remove_tag (could be bound methods or module-level functions)
    add_tag_fn = getattr(article, "add_tag", None) or getattr(art_models, "add_tag", None)
    remove_tag_fn = getattr(article, "remove_tag", None) or getattr(art_models, "remove_tag", None)

    # Ensure we can add and remove tags via flexible invocation
    assert add_tag_fn is not None, "add_tag API missing"
    assert remove_tag_fn is not None, "remove_tag API missing"

    # Add tags
    _invoke_maybe(add_tag_fn, article, "python")
    _invoke_maybe(add_tag_fn, article, "flask")
    # Remove the initial tag that may have been added by serializer
    _invoke_maybe(remove_tag_fn, article, "init")

    # Dump article and inspect tag list
    assert dump_article_fn is not None, "dump_article API missing"
    dumped = _invoke_maybe(dump_article_fn, None, article)
    payload = _extract_article_payload(dumped)

    # Accept both 'tagList' or 'tags' naming
    tags = payload.get("tagList") if isinstance(payload, dict) and payload.get("tagList") is not None else payload.get("tags")
    assert isinstance(tags, (list, tuple)), "expected tag list in dumped article"
    assert "flask" in tags
    assert "python" in tags
    assert "init" not in tags

def test_favorite_toggle_and_counts_reflected_in_serializer():
    # E2E-like flow: favorite/unfavorite an article and assert counts and favorited flag in serializer output
    from conduit.articles import serializers as art_serializers
    from conduit.articles import models as art_models

    make_article_fn = getattr(art_serializers, "make_article", None)
    dump_article_fn = getattr(art_serializers, "dump_article", None)

    data = {"title": "E2E Favorite Test", "description": "desc", "body": "content", "tagList": []}

    # Create article
    if make_article_fn:
        article = _safe_make_article(make_article_fn, data)
    else:
        Article = getattr(art_models, "Article")
        try:
            article = Article()
        except TypeError:
            article = Article(title=data["title"], description=data["description"], body=data["body"])

    # Prepare a simple fake user object (only attributes required by model methods)
    class FakeUser:
        def __init__(self, id=1, username="tester"):
            self.id = id
            self.username = username
    user = FakeUser(id=42, username="fav_user")

    # Locate favourite/unfavourite/is_favourite/favoritesCount APIs (method or module-level)
    fav_fn = getattr(article, "favourite", None) or getattr(art_models, "favourite", None) or getattr(art_models, "favorite", None)
    unfav_fn = getattr(article, "unfavourite", None) or getattr(art_models, "unfavourite", None) or getattr(art_models, "unfavorite", None)
    is_fav_fn = getattr(article, "is_favourite", None) or getattr(art_models, "is_favourite", None) or getattr(article, "is_favorited", None)
    fav_count_fn = getattr(article, "favoritesCount", None) or getattr(art_models, "favoritesCount", None) or getattr(article, "favorites_count", None)

    assert fav_fn is not None, "favourite API missing"
    assert unfav_fn is not None, "unfavourite API missing"
    assert is_fav_fn is not None, "is_favourite API missing"
    assert fav_count_fn is not None, "favoritesCount API missing"

    # Favorite the article
    _invoke_maybe(fav_fn, article, user)
    # Verify favorited state and count
    is_fav = _invoke_maybe(is_fav_fn, article, user)
    count = _invoke_maybe(fav_count_fn, article)

    assert bool(is_fav) is True
    assert int(count) >= 1

    # Inspect serializer output
    assert dump_article_fn is not None
    dumped = _invoke_maybe(dump_article_fn, None, article)
    payload = _extract_article_payload(dumped)

    # serializer may expose 'favoritesCount' or 'favorites_count', and 'favorited' or 'favorited_by_current_user'
    fav_count_field = None
    for key in ("favoritesCount", "favorites_count", "favorites"):
        if isinstance(payload, dict) and key in payload:
            fav_count_field = key
            break
    favorited_field = None
    for key in ("favorited", "favorited_by_current_user", "isFavorited", "is_favorited"):
        if isinstance(payload, dict) and key in payload:
            favorited_field = key
            break

    # If serializer doesn't include fields, at least ensure model state is correct
    if fav_count_field:
        assert int(payload[fav_count_field]) >= 1
    if favorited_field:
        assert bool(payload[favorited_field]) is True

    # Now unfavorite and ensure toggled off
    _invoke_maybe(unfav_fn, article, user)
    is_fav_after = _invoke_maybe(is_fav_fn, article, user)
    count_after = _invoke_maybe(fav_count_fn, article)

    assert bool(is_fav_after) is False
    assert int(count_after) >= 0

    # Re-check serializer if available
    dumped2 = _invoke_maybe(dump_article_fn, None, article)
    payload2 = _extract_article_payload(dumped2)
    if fav_count_field and isinstance(payload2, dict):
        assert int(payload2.get(fav_count_field, count_after)) == int(count_after)
    if favorited_field and isinstance(payload2, dict):
        assert bool(payload2.get(favorited_field, is_fav_after)) is bool(is_fav_after)


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
