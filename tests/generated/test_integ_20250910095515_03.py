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

import datetime
import pytest

def _get_article_payload(res):
    # Accept either {'article': {...}} or {...}
    if isinstance(res, _exc_lookup("Exception", Exception)) and 'article' in res and isinstance(res['article'], dict):
        return res['article']
    return res

class FakeTag:
    def __init__(self, name):
        self.name = name

class FakeUser:
    def __init__(self, username='alice', bio='', image=None, following=False):
        self.username = username
        self.bio = bio
        self.image = image
        self.following = following

class FakeArticle:
    def __init__(self, slug, title, description, body, author,
                 tags=None, tag_list=None, favorites_count=0, favorited_users=None):
        self.slug = slug
        self.title = title
        self.description = description
        self.body = body
        # match common attribute names used by serializers
        self.created_at = datetime.datetime(2020, 1, 1, 0, 0)
        self.updated_at = datetime.datetime(2020, 1, 1, 0, 0)
        self.author = author
        # support both possible shapes: .tags (list of tag objects) and .tag_list (list of names)
        self.tags = [FakeTag(n) for n in (tags or [])]
        self.tag_list = tag_list if tag_list is not None else [t.name for t in self.tags]
        self._favorites_count = favorites_count
        self._favorited_users = set(favorited_users or [])

    @property
    def favoritesCount(self):
        return self._favorites_count

    @property
    def favorited(self):
        # some serializers may use .favorited property directly
        return len(self._favorited_users) > 0

    def is_favourite(self, user):
        return user and (user.username in self._favorited_users)

    # model-like mutators
    def favourite(self, user):
        if user and user.username not in self._favorited_users:
            self._favorited_users.add(user.username)
            self._favorites_count += 1

    def unfavourite(self, user):
        if user and user.username in self._favorited_users:
            self._favorited_users.remove(user.username)
            self._favorites_count -= 1

def _assert_taglist_in_payload(payload, expected):
    # payload may contain 'tagList' or 'tags'
    if 'tagList' in payload:
        assert payload['tagList'] == expected
    elif 'tags' in payload:
        assert payload['tags'] == expected
    else:
        # fallback: maybe serializer returned tag objects under 'tagList' as objects
        # try to extract names from any list value
        for v in payload.values():
            if isinstance(v, _exc_lookup("Exception", Exception)) and all(hasattr(x, 'get') or hasattr(x, 'name') or isinstance(x, _exc_lookup("Exception", Exception)) for x in v):
                # try normalize
                names = []
                for x in v:
                    if isinstance(x, _exc_lookup("Exception", Exception)):
                        names.append(x)
                    elif hasattr(x, 'name'):
                        names.append(x.name)
                    elif hasattr(x, 'get'):
                        names.append(x.get('name') or x.get('tag') or '')
                if names == expected:
                    return
        pytest.fail("No tag list found in payload")

def test_dump_article_reflects_favorite_state():
    # import inside test as required
    from conduit.articles.serializers import dump_article

    author = FakeUser(username='bob', bio='author bio', image='http://img')
    viewer = FakeUser(username='alice')

    art = FakeArticle(
        slug='test-slug',
        title='Test Title',
        description='desc',
        body='body',
        author=author,
        tags=['python', 'flask'],
        favorites_count=2,
        favorited_users=[]
    )

    # initial state: not favorited by viewer
    res1 = dump_article(art, viewer)
    payload1 = _get_article_payload(res1)
    assert payload1.get('title') == 'Test Title' or payload1.get('slug') == 'test-slug'
    # favorites count available either under 'favoritesCount' or 'favorites_count'
    fc = payload1.get('favoritesCount', payload1.get('favorites_count', None))
    assert fc == 2
    # favorited flag should be False for this viewer
    fav_flag = payload1.get('favorited', None)
    if fav_flag is not None:
        assert fav_flag is False
    else:
        # some serializers embed author follow info - at least ensure not True
        assert not art.is_favourite(viewer)

    # now simulate favourite action via model method and re-serialize
    art.favourite(viewer)
    res2 = dump_article(art, viewer)
    payload2 = _get_article_payload(res2)
    fc2 = payload2.get('favoritesCount', payload2.get('favorites_count', None))
    assert fc2 == 3
    fav_flag2 = payload2.get('favorited', None)
    if fav_flag2 is not None:
        assert fav_flag2 is True
    else:
        assert art.is_favourite(viewer)

    # tags should be present
    _assert_taglist_in_payload(payload2, ['python', 'flask'])

def test_dump_articles_returns_all_items_and_preserves_order():
    from conduit.articles.serializers import dump_articles

    author = FakeUser(username='carol')
    a1 = FakeArticle('s1', 'T1', 'd1', 'b1', author, tags=['x'])
    a2 = FakeArticle('s2', 'T2', 'd2', 'b2', author, tags=['y', 'z'])

    res = dump_articles([a1, a2], author)
    # Accept either {'articles': [...]} or a list directly or {'articles': {'articles': [...]}} weird wrappers
    if isinstance(res, _exc_lookup("Exception", Exception)):
        if 'articles' in res and isinstance(res['articles'], list):
            articles_list = res['articles']
        else:
            # try find first list value
            articles_list = None
            for v in res.values():
                if isinstance(v, _exc_lookup("Exception", Exception)):
                    articles_list = v
                    break
            assert articles_list is not None, "dump_articles returned unexpected dict shape"
    elif isinstance(res, _exc_lookup("Exception", Exception)):
        articles_list = res
    else:
        pytest.fail("dump_articles returned unexpected type")

    assert len(articles_list) == 2
    # check ordering and presence of titles/slugs
    first = _get_article_payload(articles_list[0]) if isinstance(articles_list[0], dict) else articles_list[0]
    second = _get_article_payload(articles_list[1]) if isinstance(articles_list[1], dict) else articles_list[1]
    # allow either title or slug presence
    assert first.get('title', first.get('slug')) in ('T1', 's1')
    assert second.get('title', second.get('slug')) in ('T2', 's2')

def test_dump_article_handles_tag_list_property_when_tags_missing():
    from conduit.articles.serializers import dump_article

    author = FakeUser(username='dorothy')
    # Provide tag_list but empty .tags
    art = FakeArticle('s3', 'T3', 'd3', 'b3', author, tags=[], tag_list=['alpha', 'beta'])

    res = dump_article(art, author)
    payload = _get_article_payload(res)
    _assert_taglist_in_payload(payload, ['alpha', 'beta'])


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
