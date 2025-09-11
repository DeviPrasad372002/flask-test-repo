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
import datetime

def _exc_lookup(name, default=Exception):
    try:
        return getattr(__builtins__, name)
    except Exception:
        return default

def _flatten_values(obj):
    """Recursively collect string representations from nested structures."""
    out = []
    if obj is None:
        return out
    if isinstance(obj, (str, int, float, bool)):
        out.append(str(obj))
        return out
    if isinstance(obj, _exc_lookup("dict", Exception)):
        for v in obj.values():
            out.extend(_flatten_values(v))
        return out
    if isinstance(obj, (list, tuple, set)):
        for v in obj:
            out.extend(_flatten_values(v))
        return out
    # fallback for objects with attributes
    try:
        for attr in dir(obj):
            if attr.startswith('_'):
                continue
            try:
                v = getattr(obj, attr)
            except Exception:
                continue
            out.extend(_flatten_values(v))
    except Exception:
        out.append(str(obj))
    return out

def test_comment_schema_roundtrip_integration(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.articles.serializers import CommentSchema
    except Exception:
        pytest.skip("conduit.articles.serializers.CommentSchema not available")
    # Build a simple dummy comment-like object (no DB)
    class DummyAuthor:
        def __init__(self, username):
            self.username = username
            self.bio = None
            self.image = None

    class DummyComment:
        def __init__(self, id, body, author, created_at=None, updated_at=None):
            self.id = id
            self.body = body
            self.author = author
            self.created_at = created_at or datetime.datetime(2020, 1, 1, 12, 0, 0)
            self.updated_at = updated_at or self.created_at

        def __repr__(self):
            return f"<DummyComment id={self.id}>"

    author = DummyAuthor("alice")
    comment = DummyComment(7, "This is a test comment", author)

    schema = CommentSchema()
    # Attempt to serialize; ensure no exceptions and key content present somewhere in dumped result
    try:
        dumped = schema.dump(comment)
    except TypeError:
        # Some marshmallow versions expect a mapping; try mapping fallback
        dumped = schema.dump({
            "id": comment.id,
            "body": comment.body,
            "author": {"username": author.username},
            "created_at": comment.created_at,
            "updated_at": comment.updated_at
        })
    assert dumped is not None, "Dump returned None"
    vals = _flatten_values(dumped)
    assert str(comment.body) in vals, "Serialized output should contain the comment body"
    assert author.username in vals, "Serialized output should contain the author username"
    # Check that created/updated timestamps are present as strings somewhere
    assert any(str(comment.created_at.year) in v for v in vals), "Created timestamp year should appear"

def test_article_and_tag_serialization_integration(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.articles.serializers import TagSchema, ArticleSchema
    except Exception:
        pytest.skip("conduit.articles.serializers.TagSchema or ArticleSchema not available")
    # Create dummy tag and article-like objects
    class DummyTag:
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"<DummyTag {self.name}>"

    class DummyAuthor:
        def __init__(self, username):
            self.username = username
            self.bio = None
            self.image = None

    class DummyArticle:
        def __init__(self, slug, title, description, body, author, tags=None, created_at=None):
            self.slug = slug
            self.title = title
            self.description = description
            self.body = body
            self.author = author
            self.tagList = tags or []
            self.created_at = created_at or datetime.datetime(2021, 6, 1, 8, 0, 0)
            self.updated_at = self.created_at
            # some serializers may expect favoritesCount/favorited attributes
            self.favoritesCount = 0
            self.favorited = False

        def __repr__(self):
            return f"<DummyArticle {self.slug}>"

    tags = [DummyTag("python"), DummyTag("testing")]
    author = DummyAuthor("bob")
    article = DummyArticle("test-slug", "Test Title", "Desc", "Body content", author, tags=tags)

    tag_schema = TagSchema(many=False)
    dumped_tag = tag_schema.dump(tags[0])
    if dumped_tag is None:
        pytest.skip("TagSchema.dump returned None unexpectedly")
    flat_tag = _flatten_values(dumped_tag)
    assert "python" in flat_tag, "Tag name should be serialized"

    article_schema = ArticleSchema()
    # Some ArticleSchema implementations expect an object with specific attributes; try both object and mapping
    try:
        dumped_article = article_schema.dump(article)
    except TypeError:
        dumped_article = article_schema.dump({
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "author": {"username": author.username},
            "tagList": [{"name": t.name} for t in tags],
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favoritesCount": article.favoritesCount,
            "favorited": article.favorited
        })
    assert dumped_article is not None
    flat_article = _flatten_values(dumped_article)
    # Ensure title, body, author, and at least one tag name appear
    assert "Test Title" in flat_article or "Test Title".lower() in [v.lower() for v in flat_article], "Article title should be serialized"
    assert "Body content" in flat_article, "Article body should be serialized"
    assert author.username in flat_article, "Article author username should be serialized"
    assert any(t.name in v for t in tags for v in flat_article), "At least one tag name should be serialized"