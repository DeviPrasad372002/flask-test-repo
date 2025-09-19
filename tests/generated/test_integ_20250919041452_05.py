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

from unittest import mock

try:
    from conduit.app import create_app, register_commands
    from conduit.settings import TestConfig
    from conduit.extensions import db
    from conduit.user.models import User
    from conduit.articles.models import Article, Tags, Comment
    from conduit.articles.serializers import (
        TagSchema,
        ArticleSchema,
        ArticleSchemas,
        CommentSchema,
        CommentsSchema,
        Meta,
    )
    from conduit.database import SurrogatePK
    import conduit.exceptions as exceptions_mod
except ImportError as e:
    pytest.skip(f"Required project imports not available: {e}", allow_module_level=True)

@pytest.fixture
def app():
    # Arrange: create app and initialize DB
    try:
        app = create_app(TestConfig)
    except TypeError:
        # fallback if create_app expects import string
        app = create_app("conduit.settings.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def _create_user(username="tester", email=None):
    if email is None:
        email = f"{username}@example.com"
    
    try:
        return User.create(username=username, email=email, password="secret")
    except Exception:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user

def _create_article(author, title="A title", body="body", description="desc"):
    try:
        return Article.create(title=title, body=body, description=description, author=author)
    except Exception:
        art = Article(title=title, body=body, description=description, author=author)
        db.session.add(art)
        db.session.commit()
        return art

def test_surrogatepk_and_crud_save_update(app):
    
    # Arrange
    with app.app_context():
        author = _create_user("author1")
        # Act
        article = _create_article(author, title="Original")
        # Assert initial persistence
        assert isinstance(article.id, int)
        assert article.title == "Original"
        # Act: update via model update() if present, otherwise modify and save
        try:
            returned = article.update(title="Updated Title")
            # update() in CRUDMixin may return self
            if returned is not None:
                article = returned
        except Exception:
            article.title = "Updated Title"
            db.session.add(article)
            db.session.commit()
            db.session.refresh(article)
        # Assert updated value persisted
        assert article.title == "Updated Title"
        # SurrogatePK behavior: id shouldn't change and should be positive
        assert article.id > 0

@pytest.mark.parametrize("add_twice", [False, True])
def test_tags_add_remove_and_serializers(app, add_twice):
    
    # Arrange
    with app.app_context():
        author = _create_user("tagger")
        article = _create_article(author, title="Taggable")
        # Act: add tags
        article.add_tag("python")
        if add_twice:
            article.add_tag("python")
        # Ensure tags persisted
        tags = Tags.query.filter_by(article_id=article.id).all()
        # Assert tag uniqueness (no duplicate entries)
        assert len({t.tag for t in tags}) == 1
        assert tags[0].tag == "python"
        # Act: remove tag
        article.remove_tag("python")
        # Assert removal
        remaining = Tags.query.filter_by(article_id=article.id).all()
        assert all(t.tag != "python" for t in remaining)
        # Test TagSchema dumps
        serialized = TagSchema().dump({"tag": "example"})
        assert isinstance(serialized, dict)
        assert serialized.get("tag") == "example"

def test_favourite_unfavourite_and_favoritesCount(app):
    
    # Arrange
    with app.app_context():
        author = _create_user("author_fav")
        user_a = _create_user("alice")
        user_b = _create_user("bob")
        article = _create_article(author, title="FavTest")
        # Act: favourite by alice
        article.favourite(user_a)
        # Assert: favorited status and count
        assert article.favorited(user_a) is True
        # favoritesCount may be a property or method
        try:
            count = article.favoritesCount()
        except TypeError:
            count = article.favoritesCount
        except Exception:
            
            count = len(getattr(article, "favorites", []) or [])
        assert count == 1
        # Assert bob did not favorite
        assert article.favorited(user_b) is False
        # Act: unfavourite
        article.unfavourite(user_a)
        assert article.favorited(user_a) is False
        try:
            count2 = article.favoritesCount()
        except TypeError:
            count2 = article.favoritesCount
        except Exception:
            count2 = len(getattr(article, "favorites", []) or [])
        assert count2 == 0

def test_comments_create_and_comment_serializers(app):
    
    # Arrange
    with app.app_context():
        author = _create_user("article_author")
        commenter = _create_user("comm")
        article = _create_article(author, title="Commented")
        # Act: create comment either via Comment.create or relationship
        try:
            comment = Comment.create(body="Nice article", author=commenter, article=article)
        except Exception:
            comment = Comment(body="Nice article", author=commenter, article=article)
            db.session.add(comment)
            db.session.commit()
            db.session.refresh(comment)
        # Assert comment persisted and linked
        assert isinstance(comment.id, int)
        assert comment.body == "Nice article"
        assert comment.article_id == article.id
        # Serialize comment
        dumped = CommentSchema().dump(comment)
        assert isinstance(dumped, dict)
        assert dumped.get("body") == "Nice article"
        # Test CommentsSchema for list dump
        dumped_list = CommentsSchema().dump([comment])
        assert isinstance(dumped_list, list)
        assert dumped_list and dumped_list[0].get("body") == "Nice article"

def test_article_serializers_include_tags_and_meta(app):
    
    # Arrange
    with app.app_context():
        author = _create_user("serializer_author")
        article = _create_article(author, title="SerializeMe", body="b", description="d")
        article.add_tag("alpha")
        article.add_tag("beta")
        # Act: dump using ArticleSchema and ArticleSchemas
        single = ArticleSchema().dump(article)
        multiple = ArticleSchemas().dump([article])
        # Assert keys and types
        assert isinstance(single, dict)
        assert "tags" in single or "tagList" in single or "meta" in single
        assert isinstance(multiple, list)
        assert any(isinstance(m, dict) for m in multiple)
        # Meta schema instantiation
        meta = Meta().dump({"count": 1})
        assert isinstance(meta, dict)

def test_register_commands_presence(app):
    
    # Arrange & Act
    # register_commands should attach CLI commands like 'test', 'lint', 'clean', 'urls'
    register_commands(app)
    commands = getattr(app, "cli", None)
    
    assert commands is not None
    cmd_names = set(commands.commands.keys())
    for expected in ("test", "lint", "clean", "urls"):
        assert expected in cmd_names

@pytest.mark.parametrize("factory_func_name", ["user_not_found", "unknown_error"])
def test_exceptions_factories_return_invalidusage(factory_func_name):
    
    # Arrange / Act
    factory = getattr(exceptions_mod, factory_func_name, None)
    assert callable(factory)
    exc = factory("problem occurred")
    # Assert type and message
    from conduit.exceptions import InvalidUsage
    assert isinstance(exc, InvalidUsage)
    # InvalidUsage might store message in .message or .to_json()
    msg = getattr(exc, "message", None)
    if msg is not None:
        assert "problem occurred" in msg
    else:
        # fallback to to_json structure
        try:
            body = exc.to_json()
            assert "problem occurred" in str(body)
        except Exception:
            
            assert "problem occurred" in str(exc)

def test_tags_and_articles_end_to_end_integration(app):
    
    # This test simulates multiple interactions: tags, favorites, comments and serialization
    with app.app_context():
        # Arrange
        author = _create_user("int_author")
        user = _create_user("int_user")
        article = _create_article(author, title="Integration")
        # Act: mix operations
        article.add_tag("x")
        article.add_tag("y")
        article.favourite(user)
        comment = Comment.create(body="I like it", author=user, article=article) if hasattr(Comment, "create") else Comment(body="I like it", author=user, article=article)
        if not hasattr(comment, "id"):
            db.session.add(comment)
            db.session.commit()
            db.session.refresh(comment)
        # Assert state
        tags = [t.tag for t in Tags.query.filter_by(article_id=article.id).all()]
        assert set(tags) == {"x", "y"}
        assert article.favorited(user) is True
        # Serialization roundtrip-like checks
        art_out = ArticleSchema().dump(article)
        assert isinstance(art_out, dict)
        # ensure comments serialization includes our comment
        comments_out = CommentsSchema().dump([comment])
        assert comments_out and comments_out[0].get("body") == "I like it"
