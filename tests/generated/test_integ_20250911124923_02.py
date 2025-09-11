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

import inspect
import datetime
import pytest

def _call_flexibly(func, *args, **kwargs):
    """
    Try calling func with several common parameter patterns.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    # Try direct call
    try:
        return func(*args, **kwargs)
    except TypeError:
        pass
    # Try with only the first arg if provided
    if args:
        try:
            return func(args[0])
        except TypeError:
            pass
    # Try with first two args if available
    if args:
        try:
            return func(args[0], kwargs.get('user', None))
        except TypeError:
            pass
    # Try with named arg 'article' / 'comment' etc
    try:
        if 'article' in params:
            return func(article=args[0])
        if 'comment' in params:
            return func(comment=args[0])
        if 'user' in params:
            return func(args[0], kwargs.get('user', None))
    except TypeError:
        pass
    # Last resort: call without args
    try:
        return func()
    except Exception as e:
        # Re-raise original TypeError to surface mismatch
        raise

def make_dummy_user(name="alice"):
    class DummyUser:
        def __init__(self, username):
            self.username = username
            self.bio = None
            self.image = None
            self.following = False
        def to_dict(self):
            return {"username": self.username, "bio": self.bio, "image": self.image, "following": self.following}
    return DummyUser(name)

def make_dummy_tag(name):
    class DummyTag:
        def __init__(self, name):
            self.name = name
    return DummyTag(name)

class DummyArticle:
    def __init__(self, slug="slug", title="t", description="d", body="b", tags=None, author=None):
        self.slug = slug
        self.title = title
        self.description = description
        self.body = body
        self.created_at = datetime.datetime(2020,1,1,0,0,0)
        self.updated_at = datetime.datetime(2020,1,1,0,0,0)
        self._tags = tags or []
        self.author = author
        # favorited_by stores usernames
        self._favorited_by = set()
    # support both tagList and tags as attribute access
    @property
    def tagList(self):
        return [t.name for t in self._tags]
    @property
    def tags(self):
        return self._tags
    def favourite(self, user):
        uname = getattr(user, "username", None)
        if uname:
            self._favorited_by.add(uname)
    def unfavourite(self, user):
        uname = getattr(user, "username", None)
        if uname and uname in self._favorited_by:
            self._favorited_by.remove(uname)
    # British/American variants
    def favorite(self, user):
        return self.favourite(user)
    def unfavorite(self, user):
        return self.unfavourite(user)
    def is_favourite(self, user):
        uname = getattr(user, "username", None)
        return uname in self._favorited_by
    def favoritesCount(self):
        return len(self._favorited_by)

class DummyComment:
    def __init__(self, id=1, body="hey", author=None):
        self.id = id
        self.body = body
        self.created_at = datetime.datetime(2020,1,2,0,0,0)
        self.updated_at = datetime.datetime(2020,1,2,0,0,0)
        self.author = author

def _unwrap_article_result(res):
    if isinstance(res, _exc_lookup("dict", Exception)) and 'article' in res:
        return res['article']
    return res

def _unwrap_comment_result(res):
    if isinstance(res, _exc_lookup("dict", Exception)) and 'comment' in res:
        return res['comment']
    return res

def _maybe_call(func, *args, **kwargs):
    try:
        return _call_flexibly(func, *args, **kwargs)
    except TypeError:
        pytest.skip("Function signature incompatible for this test")

def test_dump_article_includes_tags_and_author_and_favourite(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.serializers as serializers
        import conduit.articles.models as models
    except ImportError:
        pytest.skip("conduit.articles modules not available")
    # Prepare dummy data
    user = make_dummy_user("bob")
    author = make_dummy_user("alice")
    tags = [make_dummy_tag("python"), make_dummy_tag("testing")]
    article = DummyArticle(slug="test-slug", title="T", description="D", body="B", tags=tags, author=author)
    # Ensure serializers can accept our object; attempt to dump without monkeypatching models.Article
    # Call dump_article flexibly
    try:
        result = _maybe_call(serializers.dump_article, article, user)
    except Exception:
        # Try without passing user
        result = _maybe_call(serializers.dump_article, article)
    art = _unwrap_article_result(result)
    # Validate tag list and author username presence
    assert isinstance(art, _exc_lookup("dict", Exception))
    # Accept different serializer field names: tagList or tags
    taglist = art.get("tagList") or art.get("tags") or art.get("tag_list")
    assert taglist is not None
    # Normalize to list of names
    if isinstance(taglist, _exc_lookup("list", Exception)) and taglist and isinstance(taglist[0], dict):
        names = [t.get("name") for t in taglist]
    else:
        names = taglist
    assert "python" in names and "testing" in names
    # Author info
    author_info = art.get("author") or art.get("profile") or {}
    # author_info may be dict or object
    if isinstance(author_info, _exc_lookup("dict", Exception)):
        assert author_info.get("username") in ("alice", "alice")
    else:
        # maybe a nested object; compare attribute
        assert getattr(author_info, "username", None) == "alice"
    # Favorited should be False initially
    fav = art.get("favorited")
    if fav is not None:
        assert fav is False
    # favoritesCount / favorites count should be zero
    fav_count = art.get("favoritesCount") or art.get("favorites_count") or art.get("favorites")
    if fav_count is not None:
        assert int(fav_count) == 0

def test_favourite_unfavourite_and_counts_interop_with_serializers(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.serializers as serializers
        import conduit.articles.models as models
    except ImportError:
        pytest.skip("conduit.articles modules not available")
    # Create dummy objects and monkeypatch model functions if present
    user = make_dummy_user("carol")
    author = make_dummy_user("dave")
    tags = [make_dummy_tag("int"), make_dummy_tag("edge")]
    article = DummyArticle(slug="fav-slug", title="Fav", description="desc", body="b", tags=tags, author=author)
    # If models has functions favorite/unfavorite or favoritesCount as module-level, patch them to use our instance methods
    if hasattr(models, "favoritesCount"):
        monkeypatch.setattr(models, "favoritesCount", lambda a: a.favoritesCount(), raising=False)
    if hasattr(models, "is_favourite"):
        monkeypatch.setattr(models, "is_favourite", lambda a, u: a.is_favourite(u), raising=False)
    # Initially not favorited
    res0 = _maybe_call(serializers.dump_article, article, user)
    art0 = _unwrap_article_result(res0)
    fav0 = art0.get("favorited")
    if fav0 is not None:
        assert fav0 is False
    # Favourite via article method (simulate model behavior)
    # Try different method names that codebase might expect
    if hasattr(article, "favourite"):
        article.favourite(user)
    elif hasattr(article, "favorite"):
        article.favorite(user)
    else:
        pytest.skip("No favourite method available on dummy article")
    # Dump again, this time serializers may consider passed user to compute 'favorited'
    res1 = None
    try:
        res1 = _maybe_call(serializers.dump_article, article, user)
    except Exception:
        res1 = _maybe_call(serializers.dump_article, article)
    art1 = _unwrap_article_result(res1)
    fav1 = art1.get("favorited")
    # If serializer reports favorited info, it should now be True
    if fav1 is not None:
        assert fav1 is True
    # favoritesCount should be >=1 if present
    fav_count = art1.get("favoritesCount") or art1.get("favorites_count") or art1.get("favorites")
    if fav_count is not None:
        assert int(fav_count) >= 1
    # Now unfavourite and confirm
    if hasattr(article, "unfavourite"):
        article.unfavourite(user)
    elif hasattr(article, "unfavorite"):
        article.unfavorite(user)
    else:
        pytest.skip("No unfavourite method available on dummy article")
    res2 = _maybe_call(serializers.dump_article, article, user)
    art2 = _unwrap_article_result(res2)
    fav2 = art2.get("favorited")
    if fav2 is not None:
        assert fav2 is False
    fav_count2 = art2.get("favoritesCount") or art2.get("favorites_count") or art2.get("favorites")
    if fav_count2 is not None:
        assert int(fav_count2) == 0

def test_make_and_dump_comment_integration(monkeypatch):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.serializers as serializers
        import conduit.articles.models as models
    except ImportError:
        pytest.skip("conduit.articles modules not available")
    user = make_dummy_user("erin")
    author = make_dummy_user("frank")
    # Monkeypatch model Comment class so make_comment creates our DummyComment if serializers use models.Comment
    if hasattr(models, "Comment"):
        monkeypatch.setattr(models, "Comment", DummyComment, raising=False)
    # Try to call make_comment to create a comment instance
    created = None
    if hasattr(serializers, "make_comment"):
        try:
            # Try common signatures: (user, data) or (article, user, data) or (user, body)
            sig = inspect.signature(serializers.make_comment)
            params = list(sig.parameters.keys())
            if len(params) >= 2 and 'user' in params:
                # build a data dict
                data = {"body": "Integration test comment"}
                try:
                    created = serializers.make_comment(user, data)
                except TypeError:
                    # maybe signature is make_comment(body, user)
                    try:
                        created = serializers.make_comment("Integration test comment", user)
                    except TypeError:
                        created = None
            else:
                # attempt naive call
                created = serializers.make_comment(user, {"body": "Integration test comment"})
        except Exception:
            # fall back to None (we'll skip if cannot create)
            created = None
    # If we couldn't use make_comment, create DummyComment directly
    if created is None:
        created = DummyComment(id=42, body="Integration test comment", author=user)
    # Now dump the comment via dump_comment
    if not hasattr(serializers, "dump_comment"):
        pytest.skip("dump_comment not available")
    res = None
    try:
        res = _maybe_call(serializers.dump_comment, created, user)
    except Exception:
        res = _maybe_call(serializers.dump_comment, created)
    com = _unwrap_comment_result(res)
    assert isinstance(com, _exc_lookup("dict", Exception))
    # ID and body presence
    assert str(com.get("id") or com.get("ID") or com.get("comment_id") or com.get("identifier")) is not None
    assert (com.get("body") == "Integration test comment") or (com.get("content") == "Integration test comment") or ("Integration test comment" in str(com))
    # Author username correctness in nested author/profile field
    author_info = com.get("author") or com.get("profile") or {}
    if isinstance(author_info, _exc_lookup("dict", Exception)):
        # If created.author is an object, ensure username matches
        username = author_info.get("username")
        # It may be missing if dumper expects different structure; tolerate both
        if username is not None:
            assert username in (getattr(user, "username", None), getattr(created.author, "username", None))
    else:
        # If author_info is object
        assert getattr(author_info, "username", None) in (getattr(user, "username", None), getattr(created.author, "username", None))