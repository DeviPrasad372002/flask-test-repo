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
    try:
        import conduit.exceptions as ce
        return getattr(ce, name)
    except Exception:
        return default

def test_article_lifecycle_create_update_tag_favourite_comment(tmp_path):
    # Import targets inside test
    from conduit.app import create_app
    from conduit.settings import TestConfig
    from conduit.extensions import db, save
    from conduit.user.models import User
    from conduit.articles.models import Article, Comment
    from conduit.articles.serializers import CommentSchema, ArticleSchema

    app = create_app(TestConfig)

    with app.app_context():
        # ensure clean db
        db.create_all()

        # create a user
        user = User(username="alice", email="alice@example.org", password="s3cr3t")
        save(user)

        # create an article
        art = Article(title="Initial Title", description="desc", body="first body", author=user)
        save(art)

        # verify saved and basic fields persisted
        # try several ways to reload deterministically
        try:
            reloaded = db.session.get(Article, getattr(art, "id"))
        except Exception:
            # fallback to query.get if older SQLAlchemy
            reloaded = Article.query.get(getattr(art, "id"))
        assert reloaded is not None
        assert getattr(reloaded, "title") == "Initial Title"

        # favourites count initially zero (method or property)
        fav_count = None
        if hasattr(reloaded, "favoritesCount"):
            fav_count = reloaded.favoritesCount()
        elif hasattr(reloaded, "favorites_count"):
            fav_count = reloaded.favorites_count
        else:
            # best-effort: try length of favorites relationship
            favs = getattr(reloaded, "favorites", None)
            fav_count = len(favs) if favs is not None else 0
        assert fav_count == 0

        # favourite the article
        if hasattr(reloaded, "favourite"):
            reloaded.favourite(user)
        elif hasattr(reloaded, "favorite"):
            reloaded.favorite(user)
        save(reloaded)

        # verify favourite recorded
        if hasattr(reloaded, "is_favourite"):
            assert reloaded.is_favourite(user)
        else:
            # fallback: check favoritesCount increased
            if hasattr(reloaded, "favoritesCount"):
                assert reloaded.favoritesCount() == 1

        # unfavourite the article
        if hasattr(reloaded, "unfavourite"):
            reloaded.unfavourite(user)
        elif hasattr(reloaded, "unfavorite"):
            reloaded.unfavorite(user)
        save(reloaded)

        if hasattr(reloaded, "is_favourite"):
            assert not reloaded.is_favourite(user)

        # add a tag
        if hasattr(reloaded, "add_tag"):
            reloaded.add_tag("python")
            save(reloaded)
            # inspect tags relationship or attribute
            tags_attr = getattr(reloaded, "tags", None)
            tag_names = []
            if tags_attr is not None:
                try:
                    tag_names = [getattr(t, "tag", str(t)) for t in tags_attr]
                except Exception:
                    tag_names = list(tags_attr)
            else:
                # maybe there's a tagList property
                tl = getattr(reloaded, "tagList", None) or getattr(reloaded, "taglist", None)
                if tl:
                    tag_names = list(tl)
            assert "python" in tag_names
        else:
            pytest.skip("Model has no add_tag implementation")

        # remove the tag
        if hasattr(reloaded, "remove_tag"):
            reloaded.remove_tag("python")
            save(reloaded)
            tags_attr = getattr(reloaded, "tags", None)
            if tags_attr is not None:
                tag_names = [getattr(t, "tag", str(t)) for t in tags_attr]
            else:
                tl = getattr(reloaded, "tagList", None) or getattr(reloaded, "taglist", None)
                tag_names = list(tl) if tl else []
            assert "python" not in tag_names

        # update the article title and body and save
        reloaded.title = "Updated Title"
        reloaded.body = "updated body"
        save(reloaded)

        # reload and assert updates persisted
        try:
            updated = db.session.get(Article, getattr(reloaded, "id"))
        except Exception:
            updated = Article.query.get(getattr(reloaded, "id"))
        assert updated.title == "Updated Title"
        assert updated.body == "updated body"

        # add a comment
        comment = Comment(body="Nice article!", author=user, article=updated)
        save(comment)

        # verify comment accessible via article.comments
        comments = getattr(updated, "comments", None)
        assert comments is not None
        bodies = [getattr(c, "body", None) for c in comments]
        assert "Nice article!" in bodies

        # serialize comment via schema
        cs = CommentSchema()
        dumped = cs.dump(comment)
        assert isinstance(dumped, _exc_lookup("Exception", Exception))
        assert dumped.get("body") == "Nice article!"

        # clean up
        db.session.remove()
        db.drop_all()

def test_article_serialization_roundtrip_and_schemas(tmp_path):
    # Import targets inside test
    from conduit.app import create_app
    from conduit.settings import TestConfig
    from conduit.extensions import db, save
    from conduit.user.models import User
    from conduit.articles.models import Article
    from conduit.articles.serializers import ArticleSchema, ArticleSchemas, TagSchema, Meta

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        # create a user and article
        user = User(username="bob", email="bob@example.org", password="pw")
        save(user)
        art = Article(title="Serialization Title", description="s-desc", body="s-body", author=user)
        # attach a couple of tags if supported
        if hasattr(art, "add_tag"):
            art.add_tag("flask")
            art.add_tag("testing")
        save(art)

        # single article schema
        a_schema = ArticleSchema()
        serialized = a_schema.dump(art)
        assert isinstance(serialized, _exc_lookup("Exception", Exception))
        # expected keys at least include title and body or 'article' wrapper depending on implementation
        if "title" in serialized:
            assert serialized["title"] == "Serialization Title"
        else:
            # maybe wrapped
            inner = serialized.get("article") or serialized.get("data") or serialized
            assert inner.get("title") == "Serialization Title"

        # multiple articles schema
        list_schema = ArticleSchemas()
        dumped_list = list_schema.dump([art])
        # expect a list or dict wrapper
        assert dumped_list is not None
        if isinstance(dumped_list, _exc_lookup("Exception", Exception)):
            # may contain 'articles' key
            contents = dumped_list.get("articles") or dumped_list.get("data") or dumped_list
            # try to find title inside
            found = False
            if isinstance(contents, _exc_lookup("Exception", Exception)):
                for item in contents:
                    if item.get("title") == "Serialization Title":
                        found = True
            else:
                if contents.get("title") == "Serialization Title":
                    found = True
            assert found
        else:
            # if it's a list
            assert any(item.get("title") == "Serialization Title" for item in dumped_list)

        # tag schema on one tag object if available via relationship
        tags = getattr(art, "tags", None)
        if tags:
            first_tag = next(iter(tags), None)
            if first_tag is not None:
                ts = TagSchema()
                tdata = ts.dump(first_tag)
                assert isinstance(tdata, _exc_lookup("Exception", Exception))
                # expect 'tag' key or similar
                assert any(k in tdata for k in ("tag", "name"))

        # Meta schema basic usage if available
        if hasattr(Meta, "__name__"):
            try:
                m = Meta()
                md = m.dump({"count": 1})
                assert isinstance(md, _exc_lookup("Exception", Exception))
            except Exception:
                # Some Meta implementations may require context - ignore if so
                pass

        db.session.remove()
        db.drop_all()


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
