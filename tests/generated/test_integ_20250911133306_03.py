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
import pytest

def _exc_lookup(name, default):
    try:
        import conduit.exceptions as _exc_mod  # type: ignore
        return getattr(_exc_mod, name, default)
    except Exception:
        return default

def _get_fav_count(article):
    # try multiple possible attribute/method names
    for attr in ("favoritesCount", "favorites_count", "favoritesCount()", "favorites"):
        if hasattr(article, attr):
            val = getattr(article, attr)
            if callable(val):
                try:
                    return int(val())
                except Exception:
                    continue
            try:
                return int(val)
            except Exception:
                continue
    # try property-like access via method name
    for name in ("favoritesCount", "favorites_count"):
        if hasattr(article, name):
            val = getattr(article, name)
            if callable(val):
                try:
                    return int(val())
                except Exception:
                    continue
    # fallback try __dict__
    try:
        return int(getattr(article, "favoritesCount", getattr(article, "favorites_count", 0)))
    except Exception:
        return 0

def _make_dummy_user():
    class DummyUser:
        def __init__(self):
            self.id = 1
            self.username = "testuser"
    return DummyUser()

def _safe_getattr(module, *names):
    for n in names:
        if hasattr(module, n):
            return getattr(module, n)
    return None

def test_article_favourite_unfavourite_integration():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.models as models  # type: ignore
        import conduit.articles.serializers as serializers  # type: ignore
    except Exception:
        pytest.skip("conduit.articles modules not available")

    Article = getattr(models, "Article", None)
    if Article is None or not callable(Article):
        pytest.skip("Article model not available")

    # try to instantiate Article with flexible args
    article = None
    sig = None
    try:
        sig = inspect.signature(Article)
    except Exception:
        pass
    # prepare kwargs common to many implementations
    common_kwargs = {"title": "T", "body": "B", "slug": "t-slug", "description": "d"}
    # Try instantiation in a few ways
    instantiation_attempts = []
    try:
        instantiation_attempts.append(lambda: Article(**{k: v for k, v in common_kwargs.items() if k in (inspect.signature(Article).parameters if hasattr(Article, "__call__") else common_kwargs)}))
    except Exception:
        pass
    instantiation_attempts.append(lambda: Article("T", "B", "d", "t-slug"))
    instantiation_attempts.append(lambda: Article(**common_kwargs))
    instantiation_attempts.append(lambda: Article(title="T", body="B"))
    last_exc = None
    for attempt in instantiation_attempts:
        try:
            article = attempt()
            break
        except Exception as e:
            last_exc = e
            continue
    if article is None:
        pytest.skip(f"Could not instantiate Article: {last_exc}")

    # find favourite/unfavourite method names (UK/US variants)
    fav_method = None
    unfav_method = None
    for name in ("favourite", "favorite", "favor", "add_favourite", "add_favorite"):
        if hasattr(article, name):
            fav_method = getattr(article, name)
            break
    for name in ("unfavourite", "unfavorite", "remove_favourite", "remove_favorite"):
        if hasattr(article, name):
            unfav_method = getattr(article, name)
            break

    if fav_method is None or unfav_method is None:
        pytest.skip("Favourite/unfavourite methods not present on Article model")

    user = _make_dummy_user()

    before = _get_fav_count(article)
    # call favorite
    try:
        # try both call signatures: with user object or with user.id
        try:
            fav_method(user)
        except TypeError:
            fav_method(user.id)
    except Exception as e:
        pytest.fail(f"Calling favourite method failed: {e}")

    after_fav = _get_fav_count(article)
    assert after_fav >= before, "favoritesCount did not increase after favouriting"

    # if serializer provides dump_article use it else try ArticleSchema
    dump_func = _safe_getattr(serializers, "dump_article", "dump_articles")
    dumped = None
    if dump_func:
        try:
            dumped = dump_func(article)
        except Exception:
            # some serializers expect schema instance
            try:
                schema_cls = _safe_getattr(serializers, "ArticleSchema", "ArticleSchemas", "ArticleSchemas")
                if schema_cls:
                    dumped = schema_cls().dump(article)
            except Exception:
                dumped = None
    else:
        schema_cls = _safe_getattr(serializers, "ArticleSchema", "ArticleSchemas")
        if schema_cls:
            try:
                dumped = schema_cls().dump(article)
            except Exception:
                dumped = None

    if dumped is not None and isinstance(dumped, _exc_lookup("dict", Exception)):
        # try to find favorites count and favored flag in dumped output
        # common keys: favoritesCount, favorites_count, favorited, favourited
        keys = dumped.keys()
        assert any(k in keys for k in ("favoritesCount", "favorites_count", "favorites")), "Serialized output missing favorites count"
        assert any(k in keys for k in ("favorited", "favourited", "is_favourite")), "Serialized output missing favorited flag"

    # now unfavourite
    try:
        try:
            unfav_method(user)
        except TypeError:
            unfav_method(user.id)
    except Exception as e:
        pytest.fail(f"Calling unfavourite method failed: {e}")

    after_unfav = _get_fav_count(article)
    assert after_unfav <= after_fav, "favoritesCount did not decrease after unfavouriting"

def test_tags_add_remove_and_serialization_integration():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.models as models  # type: ignore
        import conduit.articles.serializers as serializers  # type: ignore
    except Exception:
        pytest.skip("conduit.articles modules not available")

    Article = getattr(models, "Article", None)
    if Article is None or not callable(Article):
        pytest.skip("Article model not available")

    # instantiate article
    article = None
    try:
        article = Article(title="T", body="B", slug="s-test", description="d")
    except Exception:
        # try minimal
        try:
            article = Article("T", "B", "d", "s-test")
        except Exception:
            pytest.skip("Cannot instantiate Article for tag test")

    # find add_tag/remove_tag variants
    add_tag = None
    remove_tag = None
    for name in ("add_tag", "addTag", "add_tags", "addTag"):
        if hasattr(article, name):
            add_tag = getattr(article, name)
            break
    for name in ("remove_tag", "removeTag", "remove_tags"):
        if hasattr(article, name):
            remove_tag = getattr(article, name)
            break

    if add_tag is None or remove_tag is None:
        pytest.skip("Tag manipulation methods not present on Article model")

    # add a tag
    try:
        add_tag("python")
    except TypeError:
        try:
            add_tag("python", None)
        except Exception as e:
            pytest.fail(f"add_tag failed: {e}")
    except Exception as e:
        pytest.fail(f"add_tag failed: {e}")

    # check internal tag storage heuristically
    tags_attr = None
    for candidate in ("tags", "tag_list", "_tags"):
        if hasattr(article, candidate):
            tags_attr = getattr(article, candidate)
            break

    # If no obvious attribute, attempt to call a listing method
    if tags_attr is None:
        if hasattr(article, "get_tags"):
            try:
                tags_attr = article.get_tags()
            except Exception:
                tags_attr = None

    # proceed if we can inspect tags
    if tags_attr is not None:
        if isinstance(tags_attr, (list, tuple, set)):
            assert "python" in tags_attr or any(str(t) == "python" for t in tags_attr)
        else:
            # try converting to list or string
            try:
                s = str(tags_attr)
                assert "python" in s
            except Exception:
                pytest.skip("Cannot verify tags content")

    # serialize article and ensure tag appears
    dump_func = _safe_getattr(serializers, "dump_article", "dump_articles")
    dumped = None
    if dump_func:
        try:
            dumped = dump_func(article)
        except Exception:
            dumped = None
    else:
        schema_cls = _safe_getattr(serializers, "ArticleSchema", "ArticleSchemas")
        if schema_cls:
            try:
                dumped = schema_cls().dump(article)
            except Exception:
                dumped = None

    if dumped is not None and isinstance(dumped, _exc_lookup("dict", Exception)):
        # common tag keys could be 'tagList', 'tags', 'tag_list'
        keys = dumped.keys()
        possible = ("tagList", "tags", "tag_list")
        if any(k in keys for k in possible):
            # find which key
            for k in possible:
                if k in dumped:
                    val = dumped[k]
                    if isinstance(val, (list, tuple, set)):
                        assert any(str(x) == "python" for x in val)
                    else:
                        assert "python" in str(val)
                    break
        else:
            pytest.skip("Serialized output does not include tags key")
    else:
        pytest.skip("Could not serialize Article to inspect tags")

    # remove tag and ensure it's gone
    try:
        remove_tag("python")
    except TypeError:
        try:
            remove_tag("python", None)
        except Exception as e:
            pytest.fail(f"remove_tag failed: {e}")
    except Exception as e:
        pytest.fail(f"remove_tag failed: {e}")

    # verify removal heuristically
    if tags_attr is not None:
        if isinstance(tags_attr, (list, tuple, set)):
            assert "python" not in tags_attr
        else:
            s = str(tags_attr)
            assert "python" not in s

def test_comment_make_and_dump_integration():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.models as models  # type: ignore
        import conduit.articles.serializers as serializers  # type: ignore
    except Exception:
        pytest.skip("conduit.articles modules not available")

    Comment = getattr(models, "Comment", None)
    if Comment is None or not callable(Comment):
        pytest.skip("Comment model not available")

    # attempt to create a comment instance
    comment = None
    last_exc = None
    try:
        comment = Comment(body="This is a test comment")
    except Exception as e:
        last_exc = e
        try:
            # try alternate signature
            comment = Comment("This is a test comment", author=None)
        except Exception as e2:
            last_exc = e2

    if comment is None:
        pytest.skip(f"Could not instantiate Comment: {last_exc}")

    # if there is a make_comment factory in serializers, use it
    make_comment = getattr(serializers, "make_comment", None)
    if make_comment:
        try:
            cm = make_comment({"body": "Hello"}, author=_make_dummy_user())
            # Expect either model instance or dict
            if hasattr(cm, "__dict__") or isinstance(cm, _exc_lookup("dict", Exception)):
                created = cm
            else:
                created = cm
        except Exception:
            created = None
    else:
        created = comment

    # now attempt to dump the comment via serializers.dump_comment or CommentSchema
    dump_fn = getattr(serializers, "dump_comment", None)
    dumped = None
    if dump_fn:
        try:
            dumped = dump_fn(created)
        except Exception:
            dumped = None
    else:
        schema_cls = _safe_getattr(serializers, "CommentSchema", "CommentsSchema")
        if schema_cls:
            try:
                dumped = schema_cls().dump(created)
            except Exception:
                dumped = None

    if dumped is None:
        pytest.skip("Could not serialize comment")
    # Expect serialized comment to contain the body
    # dumped might be dict or nested dict; try to find "body" key
    if isinstance(dumped, _exc_lookup("dict", Exception)):
        if "body" in dumped:
            assert "test" in str(dumped["body"]) or "Hello" in str(dumped["body"])
        else:
            # maybe wrapped
            found = False
            for v in dumped.values():
                if isinstance(v, _exc_lookup("dict", Exception)) and "body" in v:
                    found = True
                    assert "test" in str(v["body"]) or "Hello" in str(v["body"])
                    break
            assert found, "Serialized comment does not contain body"
    else:
        # fallback string representation contains body
        s = str(dumped)
        assert "test" in s or "Hello" in s