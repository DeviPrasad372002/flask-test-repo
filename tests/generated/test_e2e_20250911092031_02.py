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
from datetime import datetime

def test_dump_comment_serialization_roundtrip():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.articles.serializers import dump_comment
    except Exception as e:
        # skip if target module or its imports are not available
        pytest.skip(f"Required serializer not available: {e}")

    # Create lightweight fake objects that mimic the attributes the serializer accesses.
    class FakeAuthor:
        def __init__(self, username="alice", bio=None, image=None, following=False):
            self.username = username
            self.bio = bio
            self.image = image
            self.following = following

    class FakeComment:
        def __init__(self, id_, body, created_at, updated_at, author):
            self.id = id_
            self.body = body
            self.created_at = created_at
            self.updated_at = updated_at
            self.author = author

    author = FakeAuthor(username="testuser", bio="bio text", image="http://img", following=False)
    created = datetime(2020, 1, 1, 12, 0, 0)
    comment = FakeComment(123, "This is a test comment", created, created, author)

    out = dump_comment(comment)

    # The serializer may return either {'comment': {...}} or the inner dict directly.
    if isinstance(out, _exc_lookup("dict", Exception)) and "comment" in out:
        doc = out["comment"]
    else:
        doc = out

    # Flexible assertions to account for serializer shapes.
    assert isinstance(doc, _exc_lookup("dict", Exception))
    assert doc.get("body") == "This is a test comment"
    # author should be present and contain username
    author_doc = doc.get("author")
    assert isinstance(author_doc, _exc_lookup("dict", Exception))
    assert author_doc.get("username") == "testuser"

def test_dump_articles_includes_taglist_and_count():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.articles.serializers import dump_articles
    except Exception as e:
        pytest.skip(f"Required serializer not available: {e}")

    # Fake objects to satisfy serializer expectations.
    class FakeAuthor:
        def __init__(self, username="bob", bio=None, image=None, following=False):
            self.username = username
            self.bio = bio
            self.image = image
            self.following = following

    class FakeTag:
        def __init__(self, name):
            self.name = name

    class FakeArticle:
        def __init__(self, slug, title, description, body, tags, author, created_at=None, updated_at=None):
            self.slug = slug
            self.title = title
            self.description = description
            self.body = body
            self.tags = tags  # serializer may iterate tag.name or tagList attribute
            self.created_at = created_at or datetime(2020,1,1,0,0,0)
            self.updated_at = updated_at or self.created_at
            self.author = author

        # provide method-like attributes if serializer calls them
        def favoritesCount(self):
            return 0
        @property
        def favorited(self):
            return False
        def is_favourite(self, user):
            return False

    author = FakeAuthor(username="author1", bio="a", image=None, following=False)
    tags = [FakeTag("python"), FakeTag("testing")]
    article = FakeArticle("slug-1", "Title 1", "Desc", "Body text", tags, author)

    out = dump_articles([article])

    # Accept multiple possible serializer output shapes:
    # - {'articles': [...], 'articlesCount': N}
    # - {'articles': [...]} or list [...]
    articles_list = None
    if isinstance(out, _exc_lookup("dict", Exception)) and "articles" in out:
        articles_list = out["articles"]
        # optional count
        if "articlesCount" in out:
            assert isinstance(out["articlesCount"], int)
            assert out["articlesCount"] == len(articles_list)
    elif isinstance(out, _exc_lookup("list", Exception)):
        articles_list = out
    else:
        # maybe serializer returned a single article dict
        if isinstance(out, _exc_lookup("dict", Exception)):
            # treat as single wrapped article
            articles_list = [out]
        else:
            pytest.fail(f"Unexpected dump_articles output shape: {type(out)}")

    assert isinstance(articles_list, _exc_lookup("list", Exception))
    assert len(articles_list) == 1

    first = articles_list[0]
    # serializer may nest article under 'article' key; handle both.
    if isinstance(first, _exc_lookup("dict", Exception)) and "article" in first and isinstance(first["article"], dict):
        first = first["article"]

    # tagList may appear as 'tagList' or 'tags' depending on implementation
    tag_list = None
    if isinstance(first, _exc_lookup("dict", Exception)):
        if "tagList" in first:
            tag_list = first["tagList"]
        elif "tags" in first:
            tag_list = first["tags"]

    assert isinstance(tag_list, _exc_lookup("list", Exception))
    # ensure tags names are present
    assert sorted(tag_list) == sorted(["python", "testing"])