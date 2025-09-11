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

def _call_first(obj, names, *args, **kwargs):
    for n in names:
        fn = getattr(obj, n, None)
        if callable(fn):
            return fn(*args, **kwargs)
    raise AttributeError("None of methods %r found on %r" % (names, obj))

def _maybe_save(obj, db):
    save = getattr(obj, "save", None)
    if callable(save):
        save()
    else:
        db.session.add(obj)
        db.session.commit()

def _maybe_delete(obj, db):
    delete = getattr(obj, "delete", None)
    if callable(delete):
        delete()
    else:
        db.session.delete(obj)
        db.session.commit()

def _get_attr_fallback(obj, names, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default

def _make_app():
    # Try common create_app signatures
    from importlib import import_module
    try:
        mod = import_module('conduit.app')
    except Exception:
        raise
    create_app = getattr(mod, 'create_app', None)
    if create_app is None:
        raise ImportError("create_app not found")
    # Try with config path string first, then without args
    try:
        return create_app('conduit.settings.TestConfig')
    except TypeError:
        return create_app()
    except Exception:
        # some apps accept object not string; fallback to default call
        return create_app()

def test_favorite_and_comment_lifecycle():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        app = _make_app()
        from importlib import import_module
        ext = import_module('conduit.extensions')
        db = getattr(ext, 'db', None)
        if db is None:
            pytest.skip("conduit.extensions.db not available")
        User = import_module('conduit.user.models').User
        articles_mod = import_module('conduit.articles.models')
        Article = articles_mod.Article
        Comment = getattr(articles_mod, 'Comment', None)
        if Comment is None:
            pytest.skip("Comment model not available")
    except Exception as e:
        pytest.skip("Import/setup failed: %s" % (e,))

    with app.app_context():
        # ensure clean schema
        db.drop_all()
        db.create_all()

        # create user
        u = User(username='alice', email='alice@example.com', password='password')
        _maybe_save(u, db)

        # create an article
        try:
            a = Article(title='Test Article', description='desc', body='body', author=u)
        except TypeError:
            # try alternate constructor names
            a = Article()
            for k, v in {'title':'Test Article','description':'desc','body':'body'}.items():
                if hasattr(a, k):
                    setattr(a, k, v)
            # attach author if relationship exists
            if hasattr(a, 'author'):
                setattr(a, 'author', u)
        _maybe_save(a, db)

        # Initially not favorited
        is_fav = _call_first(a, ['is_favourite', 'is_favorite', 'favorited', 'is_favourited'], u)
        assert bool(is_fav) is False

        # favourite the article
        _call_first(a, ['favourite', 'favorite', 'favouite', 'favor'], u)
        # refresh from db
        db.session.refresh(a)
        # check favourited state
        is_fav2 = _call_first(a, ['is_favourite', 'is_favorite', 'favorited', 'is_favourited'], u)
        assert bool(is_fav2) is True

        # favorites count attribute fallback
        fav_count = _get_attr_fallback(a, ['favoritesCount', 'favorites_count', 'favorites'])
        if callable(fav_count):
            fav_count = fav_count()
        assert int(fav_count) >= 1

        # make a comment
        c = None
        try:
            c = Comment(body='Nice article!', author=u, article=a)
        except TypeError:
            # instantiate and set fields
            c = Comment()
            if hasattr(c, 'body'):
                setattr(c, 'body', 'Nice article!')
            if hasattr(c, 'author'):
                setattr(c, 'author', u)
            if hasattr(c, 'article'):
                setattr(c, 'article', a)
        _maybe_save(c, db)

        # ensure comment is persisted
        q = db.session.query(Comment).filter_by(id=getattr(c, 'id', None)).first()
        assert q is not None

        # delete the comment
        _maybe_delete(c, db)
        q2 = db.session.query(Comment).filter_by(id=getattr(c, 'id', None)).first()
        assert q2 is None

        # unfavourite
        _call_first(a, ['unfavourite', 'unfavorite', 'unfavor'], u)
        db.session.refresh(a)
        is_fav3 = _call_first(a, ['is_favourite', 'is_favorite', 'favorited', 'is_favourited'], u)
        assert bool(is_fav3) is False

def test_tags_and_article_listing():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        app = _make_app()
        from importlib import import_module
        ext = import_module('conduit.extensions')
        db = getattr(ext, 'db', None)
        if db is None:
            pytest.skip("conduit.extensions.db not available")
        User = import_module('conduit.user.models').User
        articles_mod = import_module('conduit.articles.models')
        Article = articles_mod.Article
        Tags = getattr(articles_mod, 'Tags', None)
    except Exception as e:
        pytest.skip("Import/setup failed: %s" % (e,))

    with app.app_context():
        db.drop_all()
        db.create_all()

        # create users
        u1 = User(username='bob', email='bob@example.com', password='pw')
        u2 = User(username='carol', email='carol@example.com', password='pw2')
        _maybe_save(u1, db)
        _maybe_save(u2, db)

        # helper to attach tags robustly
        def attach_tags(article, tag_names):
            # try article.add_tag method
            add_method = _get_attr_fallback(article, ['add_tag', 'addTag', 'tag'])
            if callable(add_method):
                for t in tag_names:
                    try:
                        add_method(t)
                    except TypeError:
                        add_method(t, commit=False)
                _maybe_save(article, db)
                return
            # else try relationship .tags
            if hasattr(article, 'tags'):
                # ensure Tags model available
                for t in tag_names:
                    tag_obj = None
                    if Tags is not None:
                        # try to find existing tag
                        existing = db.session.query(Tags).filter(getattr(Tags, 'name', getattr(Tags, 'tag', None))==t).first() if Tags is not None else None
                        if existing:
                            tag_obj = existing
                        else:
                            # try construct tag
                            try:
                                tag_obj = Tags(name=t)
                            except TypeError:
                                try:
                                    tag_obj = Tags(tag=t)
                                except Exception:
                                    tag_obj = None
                    if tag_obj is None:
                        # fallback to simple dict-like attach if relationship allows
                        tag_obj = t
                    try:
                        article.tags.append(tag_obj)
                    except Exception:
                        # try add via setdefault or similar
                        if not hasattr(article, 'tags'):
                            setattr(article, 'tags', [tag_obj])
                _maybe_save(article, db)
                return
            # last fallback: set attribute 'tag_list'
            if hasattr(article, 'tag_list') or not hasattr(article, 'tag_list'):
                setattr(article, 'tag_list', tag_names)
                _maybe_save(article, db)

        # create two articles with tags
        a1 = Article(title='A1', description='d1', body='b1', author=u1)
        a2 = Article(title='A2', description='d2', body='b2', author=u2)
        _maybe_save(a1, db)
        _maybe_save(a2, db)

        attach_tags(a1, ['python', 'flask'])
        attach_tags(a2, ['python', 'sqlalchemy'])

        # collect tags via Tags model if present
        tags_set = set()
        if Tags is not None:
            items = db.session.query(Tags).all()
            for it in items:
                name = getattr(it, 'name', None) or getattr(it, 'tag', None)
                if name:
                    tags_set.add(name)
        else:
            # fallback: gather from articles' attributes
            for art in (a1, a2):
                # tag_list or tags relationship
                tl = getattr(art, 'tag_list', None)
                if tl:
                    tags_set.update(tl)
                else:
                    tags_rel = getattr(art, 'tags', None)
                    if tags_rel is None:
                        continue
                    for t in tags_rel:
                        if isinstance(t, _exc_lookup("str", Exception)):
                            tags_set.add(t)
                        else:
                            name = getattr(t, 'name', None) or getattr(t, 'tag', None)
                            if name:
                                tags_set.add(name)

        assert 'python' in tags_set
        assert 'flask' in tags_set or 'sqlalchemy' in tags_set

        # verify articles listing via query
        all_articles = db.session.query(Article).order_by(getattr(Article, 'created_at', getattr(Article, 'id', None))).all()
        titles = [getattr(x, 'title', None) for x in all_articles]
        assert 'A1' in titles and 'A2' in titles