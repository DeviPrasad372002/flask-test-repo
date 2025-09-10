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

import pytest

def _exc_lookup(name, default=Exception):
    # helper to lookup exceptions from conduit.exceptions if available
    try:
        import conduit.exceptions as exc_mod
        return getattr(exc_mod, name, default)
    except Exception:
        return default

def test_dump_article_enriches_schema_output(monkeypatch):
    # Import target module inside test
    import conduit.articles.serializers as serializers

    # Create a fake article object with the attributes/methods the serializer is expected to call
    class FakeAuthor:
        def __init__(self):
            self.username = "auth"
            self.bio = "bio"
            self.image = None
            self.following = False

    class FakeArticle:
        def __init__(self):
            self.slug = "test-slug"
            self.title = "Test"
            self.description = "Desc"
            self.body = "Body"
            self.tagList = ["tag1", "tag2"]
            self.author = FakeAuthor()
            self._favorites = set()

        def is_favourite(self, user):
            # serializer may call is_favourite or favorited; support both styles
            return user == "current_user"

        @property
        def favorited(self):
            return False

        def favoritesCount(self):
            return 7

    fake_article = FakeArticle()

    # Fake ArticleSchema.dump should be used by the serializer to get base data
    class FakeArticleSchema:
        def dump(self, obj):
            # return a minimal representation; serializer should then add favorites, author, etc.
            return {
                "slug": obj.slug,
                "title": obj.title,
                "description": obj.description,
                "body": obj.body,
                "tagList": list(obj.tagList),
                "createdAt": "2020-01-01T00:00:00Z",
                "updatedAt": "2020-01-01T00:00:00Z",
            }

    # ProfileSchema for author serialization
    class FakeProfileSchema:
        def dump(self, author):
            return {
                "username": getattr(author, "username", None),
                "bio": getattr(author, "bio", None),
                "image": getattr(author, "image", None),
                "following": getattr(author, "following", False),
            }

    # Monkeypatch the schema classes used by the serializer module
    monkeypatch.setattr(serializers, "ArticleSchema", FakeArticleSchema)
    # The module may import ProfileSchema from profile.serializers; patch where serializer expects it
    monkeypatch.setattr(serializers, "ProfileSchema", FakeProfileSchema)

    # Call dump_article with a simulated "current_user"
    result = serializers.dump_article(fake_article, "current_user")

    # Assertions: base fields preserved and favorites/enrichment present
    assert result["slug"] == "test-slug"
    assert result["title"] == "Test"
    assert "tagList" in result and result["tagList"] == ["tag1", "tag2"]
    # Check favoritesCount presence (the serializer should add this)
    assert "favoritesCount" in result
    # It should reflect the FakeArticle.favoritesCount result (7)
    assert result["favoritesCount"] == 7
    # favorited should reflect is_favourite/current_user
    assert "favorited" in result
    assert result["favorited"] is True
    # Author profile should be included as serialized by FakeProfileSchema
    assert "author" in result and result["author"]["username"] == "auth"

def test_dump_articles_iterates_and_counts(monkeypatch):
    import conduit.articles.serializers as serializers

    # Prepare a list of fake articles
    class FakeArticle:
        def __init__(self, slug):
            self.slug = slug

    articles = [FakeArticle("s1"), FakeArticle("s2"), FakeArticle("s3")]

    # Monkeypatch dump_article in the module to confirm it's called per-article
    calls = []

    def fake_dump_article(article, user=None):
        calls.append((article.slug, user))
        return {"slug": article.slug, "dummy": True}

    monkeypatch.setattr(serializers, "dump_article", fake_dump_article)

    # Call dump_articles and expect it to iterate
    result = serializers.dump_articles(articles, user="u1")

    # Expect result to be a mapping with articles and articlesCount or similar
    # The exact shape can vary; assert that our fake_dump_article was applied to each item
    assert len(calls) == 3
    assert calls[0] == ("s1", "u1")
    assert calls[1] == ("s2", "u1")
    assert calls[2] == ("s3", "u1")

    # If dump_articles returns a dict with 'articles' key, check it; otherwise accept a list
    if isinstance(result, _exc_lookup("Exception", Exception)):
        assert "articles" in result
        assert isinstance(result["articles"], list)
        assert len(result["articles"]) == 3
        # confirm our fake outputs are present
        assert {"slug": "s2", "dummy": True} in result["articles"]
    else:
        # allow list return
        assert isinstance(result, _exc_lookup("Exception", Exception))
        assert len(result) == 3
        assert {"slug": "s2", "dummy": True} in result

def test_make_article_constructs_and_saves(monkeypatch):
    import conduit.articles.serializers as serializers

    # Track whether save was called and what was passed to the constructor
    created = {}

    class FakeArticle:
        def __init__(self, title=None, description=None, body=None, author=None, **kwargs):
            created["title"] = title
            created["description"] = description
            created["body"] = body
            created["author"] = author
            self.title = title
            self.description = description
            self.body = body
            self.author = author
            self.saved = False

        def save(self):
            self.saved = True
            created["saved"] = True
            return self

    # Monkeypatch the Article model/class the serializer uses
    monkeypatch.setattr(serializers, "Article", FakeArticle)

    # Prepare payload and author
    payload = {"title": "My Title", "description": "D", "body": "B"}
    fake_author = object()

    # Call make_article (typical signature: make_article(data, author))
    article = serializers.make_article(payload, fake_author)

    # Verify that Article was constructed with expected fields and saved
    assert created.get("title") == "My Title"
    assert created.get("description") == "D"
    assert created.get("body") == "B"
    assert created.get("author") is fake_author
    # The returned object should have been saved
    assert getattr(article, "saved", False) is True
    assert created.get("saved", False) is True

def test_dump_comment_uses_schema_and_includes_author(monkeypatch):
    import conduit.articles.serializers as serializers

    # Create fake comment object
    class FakeAuthor:
        def __init__(self):
            self.username = "comm_author"
            self.bio = ""
            self.image = None
            self.following = False

    class FakeComment:
        def __init__(self, id_, body, author):
            self.id = id_
            self.body = body
            self.createdAt = "2020-01-02T00:00:00Z"
            self.updatedAt = "2020-01-02T00:00:00Z"
            self.author = author

    fake_author = FakeAuthor()
    fake_comment = FakeComment(10, "a comment", fake_author)

    # Fake CommentSchema.dump
    class FakeCommentSchema:
        def dump(self, obj):
            return {
                "id": obj.id,
                "body": obj.body,
                "createdAt": obj.createdAt,
                "updatedAt": obj.updatedAt,
            }

    class FakeProfileSchema:
        def dump(self, author):
            return {"username": author.username, "bio": author.bio, "image": author.image, "following": author.following}

    # Patch CommentSchema and ProfileSchema used in serializer module
    monkeypatch.setattr(serializers, "CommentSchema", FakeCommentSchema)
    monkeypatch.setattr(serializers, "ProfileSchema", FakeProfileSchema)

    # Call dump_comment (typical signature: dump_comment(comment, current_user=None))
    res = serializers.dump_comment(fake_comment, current_user=None)

    # Assert base fields preserved and author serialized
    assert res["id"] == 10
    assert res["body"] == "a comment"
    assert "author" in res and res["author"]["username"] == "comm_author"


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
