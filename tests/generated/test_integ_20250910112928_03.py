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
import datetime
import pytest

def _callable_or_value(obj):
    return obj() if callable(obj) else obj

def _ensure_dict_like(res):
    # If Flask response tuple (body, status), or a Response, normalize to dict
    if isinstance(res, _exc_lookup("Exception", Exception)):
        res = res[0]
    if hasattr(res, "get_json"):
        try:
            return res.get_json()
        except Exception:
            pass
    if isinstance(res, _exc_lookup("Exception", Exception)):
        return res
    # If it's a toy object with attributes, convert likely fields
    if hasattr(res, "__dict__"):
        return dict(res.__dict__)
    # fallback: return as-is
    return res

def instantiate_without_init(cls, **attrs):
    inst = object.__new__(cls)
    for k, v in attrs.items():
        setattr(inst, k, v)
    return inst

def test_favourite_and_unfavourite_flow(monkeypatch):
    # Import targets inside test
    import conduit.articles.models as models
    import conduit.extensions as extensions_module

    # Create dummy user and article without invoking __init__
    user = instantiate_without_init(models.User, id=42, username="tester")
    article = instantiate_without_init(models.Article)
    # Ensure attributes that methods may use exist
    setattr(article, "favorited", [])  # sometimes called favorited/favourited
    setattr(article, "favourited", article.favorited)  # mirror both spellings
    # Provide minimal fields referenced by serializers or methods
    setattr(article, "slug", "test-slug")
    setattr(article, "title", "T")
    setattr(article, "description", "D")
    setattr(article, "body", "B")
    setattr(article, "author", user)

    # Monkeypatch save in both the models module and extensions to be a no-op
    monkeypatch.setattr(extensions_module, "save", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(models, "save", lambda *a, **k: None, raising=False)

    # Now exercise favourite/unfavourite methods across modules
    # Some implementations use British spelling 'favourite'
    fav_fn = getattr(article, "favourite", None)
    unfav_fn = getattr(article, "unfavourite", None)
    # Fallback to American spelling if present
    if fav_fn is None:
        fav_fn = getattr(article, "favorite", None)
    if unfav_fn is None:
        unfav_fn = getattr(article, "unfavorite", None)

    assert fav_fn is not None, "Article model has no favourite/favorite method"
    assert unfav_fn is not None, "Article model has no unfavourite/unfavorite method"

    # Call favourite
    fav_fn(user)
    # Check counts via favoritesCount attribute/method or favorited list length
    fav_count_attr = getattr(article, "favoritesCount", None)
    if fav_count_attr is not None:
        count = _callable_or_value(fav_count_attr)
    else:
        # fallback to len of favorited list
        count = len(getattr(article, "favorited", [])) if getattr(article, "favorited", None) is not None else 0

    assert count == 1

    # Check is_favourite/is_favorite
    is_fav_fn = getattr(article, "is_favourite", None) or getattr(article, "is_favorite", None)
    assert is_fav_fn is not None
    assert is_fav_fn(user) is True

    # Unfavourite and check back to zero
    unfav_fn(user)
    if fav_count_attr is not None:
        count2 = _callable_or_value(fav_count_attr)
    else:
        count2 = len(getattr(article, "favorited", [])) if getattr(article, "favorited", None) is not None else 0
    assert count2 == 0
    assert is_fav_fn(user) is False

def test_tags_add_remove_and_serialization(monkeypatch):
    # Import inside test
    import conduit.articles.models as models
    import conduit.articles.serializers as serializers

    # Create fake tag objects and article
    TagCls = getattr(models, "Tags", None)
    assert TagCls is not None, "Tags class not present"

    tag1 = object.__new__(TagCls)
    setattr(tag1, "name", "python")
    tag2 = object.__new__(TagCls)
    setattr(tag2, "name", "flask")

    article = object.__new__(models.Article)
    # some implementations use .tags or .tagList; set both
    setattr(article, "tags", [tag1, tag2])
    setattr(article, "tag_list", ["python", "flask"])
    setattr(article, "title", "Hello")
    setattr(article, "description", "Desc")
    setattr(article, "body", "Body")
    setattr(article, "slug", "hello-world")
    # Ensure add_tag/remove_tag exist and operate on article.tags
    add_tag_fn = getattr(article, "add_tag", None) or getattr(models.Article, "add_tag", None)
    remove_tag_fn = getattr(article, "remove_tag", None) or getattr(models.Article, "remove_tag", None)

    # If methods exist on class, bind them to our instance properly
    if callable(getattr(models.Article, "add_tag", None)) and not callable(article.add_tag if hasattr(article, "add_tag") else None):
        add_tag_fn = types.MethodType(models.Article.add_tag, article)
    if callable(getattr(models.Article, "remove_tag", None)) and not callable(article.remove_tag if hasattr(article, "remove_tag") else None):
        remove_tag_fn = types.MethodType(models.Article.remove_tag, article)

    # Add a new tag via add_tag if present, otherwise manipulate tags directly
    new_tag = object.__new__(TagCls)
    setattr(new_tag, "name", "testing")
    if callable(add_tag_fn):
        add_tag_fn("testing")
    else:
        article.tags.append(new_tag)

    # Remove an existing tag
    if callable(remove_tag_fn):
        remove_tag_fn("flask")
    else:
        article.tags = [t for t in article.tags if getattr(t, "name", None) != "flask"]

    # Now serialize via dump_article if available
    dump_article = getattr(serializers, "dump_article", None) or getattr(serializers, "dump_articles", None)
    assert dump_article is not None

    result = dump_article(article)
    result = _ensure_dict_like(result)

    # Accept either 'tagList' or 'tags'
    tag_list = result.get("tagList") or result.get("tags") or result.get("tag_list")
    assert tag_list is not None, "Serialized article missing tags list"
    # Ensure 'python' and 'testing' present and 'flask' removed
    assert "python" in tag_list
    assert "testing" in tag_list
    assert "flask" not in tag_list

def test_comment_make_dump_and_delete(monkeypatch):
    # Import inside test
    import conduit.articles.models as models
    import conduit.articles.serializers as serializers
    import conduit.articles.views as views

    # Create a fake user and comment
    user = object.__new__(models.User)
    setattr(user, "id", 7)
    setattr(user, "username", "commenter")
    # Create comment instance without __init__
    comment = object.__new__(models.Comment)
    setattr(comment, "id", 101)
    setattr(comment, "body", "Nice article")
    setattr(comment, "author", user)
    setattr(comment, "created_at", datetime.datetime.utcnow())
    # Many serializers expect comment.author to have a profile or username
    # Use dump_comment serializer if present
    dump_comment = getattr(serializers, "dump_comment", None)
    assert dump_comment is not None

    result = dump_comment(comment)
    result = _ensure_dict_like(result)
    # Typical fields: id, createdAt/created_at, body, author
    assert "body" in result and result["body"] == "Nice article"
    assert result.get("id", None) == 101
    # Author may be nested dict or username
    author_field = result.get("author") or result.get("author_username") or result.get("author_id")
    assert author_field is not None

    # Now exercise delete_comment_on_article view function by mocking lookup and deletion
    delete_fn = getattr(views, "delete_comment_on_article", None)
    if delete_fn is None:
        pytest.skip("delete_comment_on_article view not present")
    # Monkeypatch models.Comment query/getter used by the view to return our comment
    # Try to patch a common attribute name used: Comment.get_by_id or Comment.query.get
    if hasattr(models.Comment, "get_by_id"):
        monkeypatch.setattr(models.Comment, "get_by_id", lambda _id: comment)
    else:
        # patch in module where view will look it up
        monkeypatch.setattr(models, "Comment", types.SimpleNamespace(get_by_id=lambda _id: comment), raising=False)
    # Also patch permission checks to allow deletion (if view checks ownership)
    # Call delete function - many view functions expect (slug, id) or (article_id, comment_id)
    try:
        res = delete_fn("slug-placeholder", 101)
    except TypeError:
        # try alternative signature (article_id, comment_id)
        res = delete_fn(1, 101)
    # Normalize response and assert deletion response shape
    res = _ensure_dict_like(res)
    # Many implementations return empty dict or {'message': 'deleted'}
    assert res is not None

def test_get_tags_view_with_mocked_tags(monkeypatch):
    # Import inside test
    import conduit.articles.views as views
    import conduit.articles.models as models

    # Prepare fake tags list and a fake Tags class with a classmethod or query
    fake_tags = ["py", "flask", "testing"]

    class FakeTags:
        @staticmethod
        def get_all():
            return fake_tags
        @staticmethod
        def all():
            return fake_tags

    # Monkeypatch the Tags reference in the views module to our FakeTags
    monkeypatch.setattr(views, "Tags", FakeTags, raising=False)
    # Also defensively monkeypatch in models if views imported from models earlier
    monkeypatch.setattr(models, "Tags", FakeTags, raising=False)

    get_tags_fn = getattr(views, "get_tags", None)
    assert get_tags_fn is not None

    res = get_tags_fn()
    res = _ensure_dict_like(res)
    # Expect a dict with key 'tags' mapping to list
    tags_list = res.get("tags") or res.get("tagList") or res.get("tags_list") or res
    # Normalize if nested
    if isinstance(tags_list, _exc_lookup("Exception", Exception)) and "tags" in tags_list:
        tags_list = tags_list["tags"]
    assert isinstance(tags_list, (list, tuple))
    for t in fake_tags:
        assert t in tags_list


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
