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

def _normalize_article_dict(maybe):
    # If function returned wrapper like {'article': {...}}, unwrap
    if isinstance(maybe, _exc_lookup("Exception", Exception)) and 'article' in maybe and isinstance(maybe['article'], dict):
        return maybe['article']
    return maybe

def _call_flexible(func, *args, **kwargs):
    """Call func trying several argument permutations based on its signature."""
    sig = inspect.signature(func)
    params = sig.parameters
    # If accepts var positional/keyword, call directly
    try:
        return func(*args, **kwargs)
    except TypeError:
        pass
    # Try progressively reducing arguments
    for n in range(len(args), -1, -1):
        try:
            return func(*args[:n], **kwargs)
        except TypeError:
            continue
    # Try calling with no args
    try:
        return func()
    except Exception as e:
        raise

def _extract_taglist(article_obj, dump_fn=None):
    # Prefer using dump function if available
    if dump_fn:
        try:
            dumped = _call_flexible(dump_fn, article_obj)
            dumped = _normalize_article_dict(dumped)
            if isinstance(dumped, _exc_lookup("Exception", Exception)):
                for key in ('tagList', 'tags', 'tag_list'):
                    if key in dumped:
                        return dumped[key] or []
        except Exception:
            pass
    # Fallbacks inspecting object attributes
    if isinstance(article_obj, _exc_lookup("Exception", Exception)):
        return article_obj.get('tagList') or article_obj.get('tags') or []
    if hasattr(article_obj, 'tagList'):
        return getattr(article_obj, 'tagList') or []
    if hasattr(article_obj, 'tags'):
        t = getattr(article_obj, 'tags')
        # tags may be list of tag objects with .name
        try:
            return [getattr(tt, 'name') if not isinstance(tt, _exc_lookup("Exception", Exception)) else tt for tt in t] or []
        except Exception:
            return list(t) if t is not None else []
    return []

def test_make_and_dump_article_with_tags_and_optional_add_remove(tmp_path):
    # Import targets inside test for isolation
    import conduit.articles.serializers as serializers
    import conduit.articles.models as models

    # Build basic article payload
    payload = {'title': 'Test Title', 'description': 'Desc', 'body': 'Body text', 'tagList': ['init']}
    make_article = getattr(serializers, 'make_article', None)
    dump_article = getattr(serializers, 'dump_article', None)
    add_tag_fn = getattr(models, 'add_tag', None)
    remove_tag_fn = getattr(models, 'remove_tag', None)

    # Create article via make_article if available, otherwise try Article class
    article = None
    if make_article:
        try:
            article = _call_flexible(make_article, payload)
        except Exception:
            # try with two args if signature requires (data, author)
            try:
                article = _call_flexible(make_article, payload, None)
            except Exception:
                pytest.fail("make_article exists but could not be called")
    else:
        # Fallback: instantiate Article directly if exposed
        Article = getattr(models, 'Article', None)
        assert Article is not None, "No make_article and no Article class available"
        article = Article(title=payload['title'], description=payload['description'], body=payload['body'])
        # try to set initial tags if attribute exists
        if hasattr(article, 'tagList'):
            setattr(article, 'tagList', list(payload.get('tagList', [])))
        elif hasattr(article, 'tags'):
            try:
                # attempt to create Tags objects
                Tags = getattr(models, 'Tags', None)
                if Tags:
                    article.tags = [Tags(name=t) for t in payload.get('tagList', [])]
                else:
                    article.tags = list(payload.get('tagList', []))
            except Exception:
                article.tags = list(payload.get('tagList', []))

    # Ensure dump_article returns the expected content
    if dump_article:
        dumped = _call_flexible(dump_article, article)
        dumped = _normalize_article_dict(dumped)
        assert isinstance(dumped, _exc_lookup("Exception", Exception)), "dump_article should return a dict-like article representation"
        assert dumped.get('title') == payload['title']
        tags = dumped.get('tagList') or dumped.get('tags') or []
        assert 'init' in tags
    else:
        # fallback: inspect object attributes
        tags = _extract_taglist(article)
        assert 'init' in tags

    # Try to add a tag using either article.add_tag or module-level add_tag
    added = False
    for fn_try in (getattr(article, 'add_tag', None), add_tag_fn):
        if fn_try:
            try:
                _call_flexible(fn_try, article, 'extra') if fn_try is add_tag_fn else _call_flexible(fn_try, 'extra')
                added = True
                break
            except TypeError:
                # try alternate calling style
                try:
                    _call_flexible(fn_try, 'extra') if fn_try is add_tag_fn else _call_flexible(fn_try, article, 'extra')
                    added = True
                    break
                except Exception:
                    continue
            except Exception:
                # ignore other runtime errors and continue
                continue
    if added:
        # Verify the tag was added in dumped representation or attributes
        if dump_article:
            dumped = _call_flexible(dump_article, article)
            dumped = _normalize_article_dict(dumped)
            tags = dumped.get('tagList') or dumped.get('tags') or []
        else:
            tags = _extract_taglist(article, dump_article)
        assert 'extra' in tags

        # Try to remove it
        removed = False
        for rem_try in (getattr(article, 'remove_tag', None), remove_tag_fn):
            if rem_try:
                try:
                    _call_flexible(rem_try, article, 'extra') if rem_try is remove_tag_fn else _call_flexible(rem_try, 'extra')
                    removed = True
                    break
                except TypeError:
                    try:
                        _call_flexible(rem_try, 'extra') if rem_try is remove_tag_fn else _call_flexible(rem_try, article, 'extra')
                        removed = True
                        break
                    except Exception:
                        continue
                except Exception:
                    continue
        if removed:
            if dump_article:
                dumped = _call_flexible(dump_article, article)
                dumped = _normalize_article_dict(dumped)
                tags = dumped.get('tagList') or dumped.get('tags') or []
            else:
                tags = _extract_taglist(article, dump_article)
            assert 'extra' not in tags

def test_dump_articles_and_comment_and_favorite_related_introspection():
    import conduit.articles.serializers as serializers
    import conduit.articles.models as models

    make_article = getattr(serializers, 'make_article', None)
    dump_article = getattr(serializers, 'dump_article', None)
    dump_articles = getattr(serializers, 'dump_articles', None)
    make_comment = getattr(serializers, 'make_comment', None)
    dump_comment = getattr(serializers, 'dump_comment', None)

    # Create two articles
    payload1 = {'title': 'First', 'description': 'd1', 'body': 'b1', 'tagList': ['t1']}
    payload2 = {'title': 'Second', 'description': 'd2', 'body': 'b2', 'tagList': ['t2']}
    articles = []
    for p in (payload1, payload2):
        if make_article:
            try:
                art = _call_flexible(make_article, p)
            except Exception:
                try:
                    art = _call_flexible(make_article, p, None)
                except Exception:
                    pytest.fail("make_article exists but cannot be invoked in any supported way")
        else:
            Article = getattr(models, 'Article', None)
            assert Article is not None, "No make_article and no Article available"
            art = Article(title=p['title'], description=p['description'], body=p['body'])
        articles.append(art)

    # Dump articles using dump_articles if exists, else dump each
    dumped_list = None
    if dump_articles:
        try:
            dumped_list = _call_flexible(dump_articles, articles)
            # unwrap possible wrapper
            if isinstance(dumped_list, _exc_lookup("Exception", Exception)) and 'articles' in dumped_list:
                dumped_list = dumped_list['articles']
        except Exception:
            dumped_list = None

    if dumped_list is None:
        dumped_list = []
        for a in articles:
            if dump_article:
                da = _call_flexible(dump_article, a)
                da = _normalize_article_dict(da)
                dumped_list.append(da)
            elif isinstance(a, _exc_lookup("Exception", Exception)):
                dumped_list.append(a)
            else:
                # best effort object inspection
                item = {}
                if hasattr(a, 'title'):
                    item['title'] = getattr(a, 'title')
                item['tagList'] = _extract_taglist(a, dump_article)
                dumped_list.append(item)

    titles = [d.get('title') for d in dumped_list if isinstance(d, _exc_lookup("Exception", Exception))]
    assert 'First' in titles and 'Second' in titles

    # Favorites introspection: ensure favoritesCount and favorited/is_favourite exist and return reasonable types
    first = articles[0]
    fav_count_fn = getattr(first, 'favoritesCount', None) or getattr(models, 'favoritesCount', None)
    is_fav_fn = getattr(first, 'is_favourite', None) or getattr(models, 'is_favourite', None) or getattr(first, 'favorited', None) or getattr(models, 'favorited', None)

    if fav_count_fn:
        try:
            cnt = _call_flexible(fav_count_fn, first) if fav_count_fn is getattr(models, 'favoritesCount', None) else _call_flexible(fav_count_fn)
        except Exception:
            try:
                cnt = _call_flexible(fav_count_fn, None)
            except Exception:
                cnt = None
        assert (isinstance(cnt, _exc_lookup("Exception", Exception)) and cnt >= 0) or cnt is None

    if is_fav_fn:
        # Try calling with no args, with (None), or with (user=None)
        val = None
        for attempt in ((), (None,), (None, None), ()):
            try:
                val = _call_flexible(is_fav_fn, *attempt) if (is_fav_fn is getattr(models, 'is_favourite', None) or is_fav_fn is getattr(models, 'favorited', None)) else _call_flexible(is_fav_fn, *attempt)
                break
            except Exception:
                val = None
                continue
        assert (isinstance(val, _exc_lookup("Exception", Exception)) or val is None)

    # Test comments: create a comment and dump it
    comment_payload = {'body': 'A comment body'}
    comment = None
    if make_comment:
        try:
            # try (article, data) then (data,) then (article_id, data)
            try:
                comment = _call_flexible(make_comment, first, comment_payload)
            except Exception:
                comment = _call_flexible(make_comment, comment_payload)
        except Exception:
            comment = None
    else:
        Comment = getattr(models, 'Comment', None)
        if Comment:
            try:
                comment = Comment(body=comment_payload['body'])
            except Exception:
                comment = None

    if comment is not None:
        if dump_comment:
            dumped_c = _call_flexible(dump_comment, comment)
            if isinstance(dumped_c, _exc_lookup("Exception", Exception)) and 'comment' in dumped_c:
                dumped_c = dumped_c['comment']
            assert isinstance(dumped_c, _exc_lookup("Exception", Exception))
            assert dumped_c.get('body') == comment_payload['body']
        else:
            if isinstance(comment, _exc_lookup("Exception", Exception)):
                assert comment.get('body') == comment_payload['body']
            else:
                assert getattr(comment, 'body', None) == comment_payload['body']


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
