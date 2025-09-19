import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)

import os, sys, types as _types, pytest as _pytest, warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=PendingDeprecationWarning)
_t = os.environ.get('TARGET_ROOT') or 'target'
if _t and os.path.isdir(_t):
    _p = os.path.abspath(os.path.join(_t, os.pardir))
    [sys.path.insert(0, p) for p in (_p,_t) if p not in sys.path]
    _pkg=_types.ModuleType('target'); _pkg.__path__=[_t]; sys.modules.setdefault('target', _pkg)

import inspect
import types
import builtins

try:
    import pytest
    from conduit.articles import models as models_mod
    from conduit.articles import serializers as serializers_mod
    from conduit.articles import views as views_mod
except ImportError:
    import pytest  # re-import for skip
    pytest.skip("conduit package not available", allow_module_level=True)

def _get_callable(module, name, instance=None):
    """
    Helper to retrieve a callable: prefer module-level function, fall back to instance method.
    If instance provided and module does not expose function, try getattr(instance, name).
    """
    func = getattr(module, name, None)
    if callable(func):
        return func
    if instance is not None and hasattr(instance, name):
        return getattr(instance, name)
    return None

class DummyUser:
    def __init__(self, id=None, username=None):
        self.id = id
        self.username = username

    def __repr__(self):
        return f"DummyUser(id={self.id}, username={self.username})"

class DummyTag:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"DummyTag({self.name})"

class DummyArticle:
    def __init__(self, title="t", description="d", body="b", tags=None, favorites=None, author=None):
        self.title = title
        self.description = description
        self.body = body
        # tags as list of either strings or DummyTag
        self.tags = list(tags) if tags else []
        # favorites as list of DummyUser
        self.favorites = list(favorites) if favorites else []
        self.author = author
        # created/updated iso strings if needed by serializers
        self.created_at = getattr(self, "created_at", None)
        self.updated_at = getattr(self, "updated_at", None)
        # slug fallback
        self.slug = getattr(self, "slug", "dummy-slug")

def _tag_names(article):
    """Return list of tag names handling both strings and objects with .name"""
    return [getattr(t, "name", t) for t in article.tags]

def _call_maybe_bound(module, func_name, instance, *args, **kwargs):
    """
    Call a function from module if present else call instance method.
    Returns result or raises pytest.Skip if callable not found.
    """
    func = getattr(module, func_name, None)
    if callable(func):
        return func(instance, *args, **kwargs)
    if hasattr(instance, func_name):
        return getattr(instance, func_name)(*args, **kwargs)
    pytest.skip(f"{func_name} not available in module or instance")

def test_is_favourite_true_false_edge_cases():
    # Arrange
    user = DummyUser(id=1, username="u1")
    other = DummyUser(id=2, username="u2")

    article = DummyArticle(favorites=[user])

    # Act / Assert using module-level function or Article method
    is_fav_callable = _get_callable(models_mod, "is_favourite", article)
    assert callable(is_fav_callable), "is_favourite callable should exist"

    # True when user is in favorites
    res_true = is_fav_callable(article, user) if is_fav_callable is getattr(article, "is_favourite", None) else is_fav_callable(article, user)
    assert res_true is True or res_true == True

    # False for a different user
    res_false = is_fav_callable(article, other)
    assert res_false is False or res_false == False

    
    try:
        res_none = is_fav_callable(article, None)
        assert res_none is False or res_none == False
    except Exception as exc:
        pytest.fail(f"is_favourite raised unexpectedly for None: {exc}")

@pytest.mark.parametrize("initial_tags,add_tag_value,expect_count_after", [
    ([], "alpha", 1),
    (["alpha"], "alpha", 1),  # adding duplicate should not create another entry
    ([DummyTag("beta")], "gamma", 2),
])
def test_add_tag_handles_strings_and_duplicates(initial_tags, add_tag_value, expect_count_after):
    # Arrange
    article = DummyArticle(tags=initial_tags)

    add_tag_callable = _get_callable(models_mod, "add_tag", article)
    assert callable(add_tag_callable), "add_tag callable should exist"

    # Act
    add_tag_callable(article, add_tag_value) if add_tag_callable is getattr(article, "add_tag", None) else add_tag_callable(article, add_tag_value)

    # Assert: tag names should include the added tag
    names = _tag_names(article)
    assert add_tag_value in names
    # Count should match expectation (duplicates handled)
    assert len(names) == expect_count_after

def test_remove_tag_removes_and_handles_missing():
    # Arrange
    article = DummyArticle(tags=["x", DummyTag("y")])

    remove_tag_callable = _get_callable(models_mod, "remove_tag", article)
    assert callable(remove_tag_callable), "remove_tag callable should exist"

    # Act: remove existing tag by string
    remove_tag_callable(article, "x") if remove_tag_callable is getattr(article, "remove_tag", None) else remove_tag_callable(article, "x")

    # Assert removed
    names = _tag_names(article)
    assert "x" not in names
    assert "y" in names

    
    try:
        remove_tag_callable(article, "not-there")
    except ValueError:
        
        pass
    except Exception as exc:
        pytest.fail(f"remove_tag raised unexpected exception type: {type(exc)}")
    else:
        # no exception path: ensure still not present
        assert "not-there" not in _tag_names(article)

def test_favoritesCount_and_favorited_consistent_behavior():
    # Arrange
    alice = DummyUser(id=10, username="alice")
    bob = DummyUser(id=11, username="bob")
    article = DummyArticle(favorites=[alice, bob])

    # favoritesCount
    fav_count_callable = _get_callable(models_mod, "favoritesCount", article)
    assert callable(fav_count_callable), "favoritesCount callable should exist"
    count = fav_count_callable(article) if fav_count_callable is getattr(article, "favoritesCount", None) else fav_count_callable(article)
    assert isinstance(count, int)
    assert count == 2

    # favorited (per-user boolean)
    favorited_callable = _get_callable(models_mod, "favorited", article)
    assert callable(favorited_callable), "favorited callable should exist"
    # alice is favorited
    fav_alice = favorited_callable(article, alice) if favorited_callable is getattr(article, "favorited", None) else favorited_callable(article, alice)
    assert fav_alice is True or fav_alice == True
    # unknown user not favorited
    charlie = DummyUser(id=99)
    fav_charlie = favorited_callable(article, charlie)
    assert fav_charlie is False or fav_charlie == False

@pytest.mark.parametrize("input_data", [
    ({"title": "T", "description": "D", "body": "B", "tagList": ["x", "y"]}),
    ({"title": "Another", "description": "", "body": "Body"}),
])
def test_make_article_returns_model_or_mapping(input_data):
    # Arrange / Act
    make_article = getattr(serializers_mod, "make_article", None)
    if make_article is None:
        pytest.skip("make_article not available in serializers")

    result = make_article(input_data)

    # Assert: result should either be a mapping with keys or an object with attributes
    if isinstance(result, dict):
        # ensure title/body present
        assert "title" in result
        assert result["title"] == input_data["title"]
    else:
        # object path - prefer attribute access
        assert hasattr(result, "title")
        assert getattr(result, "title") == input_data["title"]

def test_dump_article_includes_expected_keys_and_handles_user_none():
    # Arrange
    author = DummyUser(id=5, username="auth")
    article = DummyArticle(title="X", description="D", body="B", tags=["t1", DummyTag("t2")], favorites=[author], author=author)
    dump_article = getattr(serializers_mod, "dump_article", None)
    if dump_article is None:
        pytest.skip("dump_article not available in serializers")

    # Act
    dumped = dump_article(article, user=None) if dump_article is getattr(article, "dump_article", None) else dump_article(article, user=None)

    # Assert structure tolerant: either dict representing article or dict with 'article' key
    assert isinstance(dumped, dict)
    container = dumped.get("article") if "article" in dumped else dumped
    # expected keys
    assert "title" in container
    assert container["title"] == "X"
    assert "description" in container
    assert "body" in container
    # tagList may be named differently but check presence of tags
    assert ("tagList" in container) or ("tags" in container) or ("taglist" in container)

def test_dump_articles_wraps_list_and_counts():
    # Arrange
    a1 = DummyArticle(title="A1")
    a2 = DummyArticle(title="A2")
    dump_articles = getattr(serializers_mod, "dump_articles", None)
    if dump_articles is None:
        pytest.skip("dump_articles not available in serializers")

    # Act
    dumped = dump_articles([a1, a2], total=2, user=None)

    # Assert
    assert isinstance(dumped, dict)
    assert ("articles" in dumped) or ("items" in dumped)
    # articlesCount or articles_count should reflect provided total
    found_counts = [dumped.get("articlesCount"), dumped.get("articles_count"), dumped.get("count"), dumped.get("total")]
    assert any((c == 2 for c in found_counts if c is not None))

def test_make_comment_and_dump_comment_behavior():
    # Arrange
    make_comment = getattr(serializers_mod, "make_comment", None)
    dump_comment = getattr(serializers_mod, "dump_comment", None)
    if make_comment is None or dump_comment is None:
        pytest.skip("make_comment or dump_comment not available in serializers")

    payload = {"body": "Nice article!"}
    comment_obj = make_comment(payload)

    
    if isinstance(comment_obj, dict):
        assert comment_obj.get("body") == payload["body"]
    else:
        assert getattr(comment_obj, "body", None) == payload["body"]

    # Prepare minimal comment-like object for dumping
    class MinimalComment:
        def __init__(self, id, body, author):
            self.id = id
            self.body = body
            self.author = author
            self.created_at = "2020-01-01T00:00:00Z"
            self.updated_at = "2020-01-01T00:00:00Z"

    author = DummyUser(id=7, username="auth7")
    minimal = MinimalComment(3, "Nice article!", author)
    dumped = dump_comment(minimal, user=None)

    assert isinstance(dumped, dict)
    comment_payload = dumped.get("comment") if "comment" in dumped else dumped
    assert comment_payload.get("body") == "Nice article!"
    assert comment_payload.get("id") == 3 or comment_payload.get("id") == "3"

def test_views_have_expected_signatures_get_articles_and_update_article():
    # Ensure get_articles exists and is callable
    get_articles = getattr(views_mod, "get_articles", None)
    assert callable(get_articles), "get_articles should be callable"

    sig_get = inspect.signature(get_articles)
    # get_articles typically has no required positional-only parameters
    params_get = list(sig_get.parameters.values())
    # ensure there are no required parameters without defaults
    assert all(p.default is not inspect._empty or p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for p in params_get)

    # Ensure update_article exists and likely takes a slug parameter
    update_article = getattr(views_mod, "update_article", None)
    assert callable(update_article), "update_article should be callable"
    sig_up = inspect.signature(update_article)
    names = [p.name for p in sig_up.parameters.values()]
    # Most implementations will have 'slug' as parameter name for update_article
    assert any(n in ("slug", "article_slug", "id") for n in names), f"update_article signature lacks expected slug parameter names: {names}"
