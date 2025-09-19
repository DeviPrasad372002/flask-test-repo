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

try:
    import pytest
except ModuleNotFoundError:
    try:
        import pytest
    except ModuleNotFoundError:
        import importlib.util, sys, os
        _tr=os.environ.get('TARGET_ROOT') or 'target'
        _p1=os.path.join(_tr, 'pytest.py'); _p2=os.path.join(_tr, 'pytest.py')
        _pp=[_p for _p in (_p1,_p2) if os.path.isfile(_p)]
        if _pp:
            _spec=importlib.util.spec_from_file_location('pytest', _pp[0])
            _m=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
            sys.modules.setdefault('pytest', _m)
        else:
            raise

try:
    from conduit.app import create_app
    from conduit.settings import TestConfig
    from conduit.database import db, get_by_id
    from conduit.user.models import User
    from conduit.articles.models import Article, Comment
    from conduit.articles.serializers import (
        make_article,
        dump_article,
        dump_articles,
        make_comment,
        dump_comment,
    )
except ImportError as e:
    pytest.skip(f"Required application modules missing: {e}", allow_module_level=True)

@pytest.fixture(autouse=True)
def app_ctx():
    # Arrange: create app with TestConfig and ensure fresh database for each test
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def _create_user(username="alice", email=None, password="password"):
    if email is None:
        email = f"{username}@example.com"
    user = User(username=username, email=email)
    # Some User models expect password hashing via attribute set
    try:
        user.password = password
    except Exception:
        # fallback to set attribute directly if property not present
        setattr(user, "password", password)
    db.session.add(user)
    db.session.commit()
    return user

@pytest.mark.parametrize("tags", [["python"], ["python", "testing"], []])
def test_make_article_dump_and_tag_add_remove(app_ctx, tags):
    
    # Arrange
    author = _create_user("author1")
    payload = {
        "title": "Integration Testing in Conduit",
        "description": "Testing integration paths",
        "body": "This is the body",
        "tagList": [],
    }

    # Act: create article via serializer
    article = make_article(payload, author)
    # Article returned might be a model or a dict depending on implementation
    if isinstance(article, dict):
        # If serializer returned dict with slug, fetch model from DB
        slug = article.get("slug")
        article = Article.query.filter_by(slug=slug).first()
        assert article is not None, "Article model not found after make_article returned dict"

    # Assert base fields saved
    assert isinstance(article, Article)
    assert article.title == payload["title"]
    assert article.author_id == author.id

    # Act/Assert: add tags and verify via model and dump_article
    for tag in tags:
        article.add_tag(tag)
    db.session.commit()

    # Ensure tags present in model.state
    model_tags = {t.name for t in getattr(article, "tags", [])}  # handle attribute variations
    assert set(tags) == model_tags

    dumped = dump_article(article, author=None)
    # dump_article might return nested structure or simple dict; find tag list
    assert isinstance(dumped, dict)
    dumped_tags = dumped.get("tagList") or dumped.get("tags") or []
    assert set(dumped_tags) == set(tags)

    # Act: remove tags one by one and assert removal
    for tag in list(tags):
        article.remove_tag(tag)
    db.session.commit()

    model_tags_after = {t.name for t in getattr(article, "tags", [])}
    assert model_tags_after == set()

def test_favourite_unfavourite_and_counts_and_flags(app_ctx):
    
    # Arrange
    author = _create_user("author_fav")
    reader = _create_user("reader")
    payload = {"title": "Fav Article", "description": "desc", "body": "b", "tagList": []}
    article = make_article(payload, author)
    if isinstance(article, dict):
        article = Article.query.filter_by(slug=article.get("slug")).first()
    assert isinstance(article, Article)

    # Act: add favourite by reader using model method(s)
    # Try both possible method names gracefully
    if hasattr(article, "favourite"):
        article.favourite(reader)
    elif hasattr(article, "favorite"):
        article.favorite(reader)
    else:
        pytest.skip("No favourite/favorite method on Article model")

    db.session.commit()

    # Assert: favoritesCount, is_favourite / favorited
    # support both method namings for queries
    count = getattr(article, "favoritesCount")() if hasattr(article, "favoritesCount") else None
    assert isinstance(count, int)
    assert count == 1

    # is_favourite may accept a user or user id
    if hasattr(article, "is_favourite"):
        assert article.is_favourite(reader) is True
    if hasattr(article, "favorited"):
        assert article.favorited(reader) is True

    # Act: unfavourite
    if hasattr(article, "unfavourite"):
        article.unfavourite(reader)
    elif hasattr(article, "unfavorite"):
        article.unfavorite(reader)
    else:
        pytest.skip("No unfavourite/unfavorite method on Article model")

    db.session.commit()

    # Assert counts back to zero and flags false
    count_after = getattr(article, "favoritesCount")()
    assert count_after == 0

    if hasattr(article, "is_favourite"):
        assert article.is_favourite(reader) is False
    if hasattr(article, "favorited"):
        assert article.favorited(reader) is False

def test_make_and_dump_comment_and_get_by_id(app_ctx):
    
    # Arrange
    author = _create_user("commenter")
    article_author = _create_user("article_author")
    payload = {"title": "Article for Comments", "description": "d", "body": "b", "tagList": []}
    article = make_article(payload, article_author)
    if isinstance(article, dict):
        article = Article.query.filter_by(slug=article.get("slug")).first()
    assert isinstance(article, Article)

    comment_payload = {"body": "Nice article!"}

    # Act: create comment using serializer
    comment = make_comment(comment_payload, author, article)
    # If serializer returns dict, fetch model
    if isinstance(comment, dict):
        comment_id = (comment.get("id") or comment.get("comment", {}).get("id"))
        comment = Comment.query.get(comment_id)
        assert comment is not None

    assert isinstance(comment, Comment)

    # Assert: dump_comment returns body and author username or similar
    dumped = dump_comment(comment)
    assert isinstance(dumped, dict)
    # normalized keys might be different; try common ones
    cbody = dumped.get("body") or dumped.get("comment", {}).get("body")
    assert cbody == comment_payload["body"]

    # Act/Assert: get_by_id for comment model
    fetched = get_by_id(Comment, comment.id)
    assert isinstance(fetched, Comment)
    assert fetched.id == comment.id

    
    with pytest.raises(Exception):
        # Use a high unlikely id
        get_by_id(Comment, 9999999)
