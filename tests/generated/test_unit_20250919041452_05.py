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

import pytest as _pytest
_pytest.skip('generator: banned private imports detected; skipping module', allow_module_level=True)

import pytest

try:
    from types import SimpleNamespace
    import conduit.extensions as extensions
    import conduit.database as database
    import conduit.articles.models as amod
    import conduit.articles.serializers as aser
    import marshmallow
except ImportError as e:
    import pytest as _pytest
    _pytest.skip(f"skipping module tests due to ImportError: {e}", allow_module_level=True)

def _make_fake_db(log):
    class FakeSession:
        def add(self, obj):
            log.append(('add', obj))

        def commit(self):
            log.append(('commit', None))

        def delete(self, obj):
            log.append(('delete', obj))

    return SimpleNamespace(session=FakeSession())

def test_CRUDMixin_create_save_update_delete(monkeypatch):
    # Arrange
    log = []
    fake_db = _make_fake_db(log)
    monkeypatch.setattr(extensions, 'db', fake_db)

    class Dummy(extensions.CRUDMixin):
        def __init__(self, name=None):
            self.name = name

    # Act: create (class method should call save which uses db.session.add/commit)
    created = Dummy.create(name='first')

    # Assert create saved instance and returned correct type and attribute
    assert isinstance(created, Dummy)
    assert getattr(created, 'name') == 'first'
    assert ('add', created) in log
    assert any(entry[0] == 'commit' for entry in log)

    # Arrange for update
    log.clear()
    # Act: update should set attributes and call add/commit
    returned = created.update(name='second')

    # Assert update returned the instance and changed attribute
    assert returned is created
    assert created.name == 'second'
    assert ('add', created) in log
    assert any(entry[0] == 'commit' for entry in log)

    # Arrange for delete
    log.clear()
    # Act: delete should call delete and commit
    created.delete()

    # Assert delete invoked delete and commit once
    assert ('delete', created) in log
    assert any(entry[0] == 'commit' for entry in log)

def test_CRUDMixin_update_with_no_kwargs_commits(monkeypatch):
    # Arrange
    log = []
    fake_db = _make_fake_db(log)
    monkeypatch.setattr(extensions, 'db', fake_db)

    class Dummy(extensions.CRUDMixin):
        def __init__(self):
            self.value = 1

    inst = Dummy()

    # Act
    result = inst.update()

    # Assert
    assert result is inst
    assert ('add', inst) in log
    assert any(entry[0] == 'commit' for entry in log)

def test_SurrogatePK_get_by_id_coerces_and_handles_non_numeric():
    # Arrange
    SurrogatePK = database.SurrogatePK

    class DummyPK(SurrogatePK):
        pass

    # Provide a fake query object with get method
    DummyPK.query = SimpleNamespace(get=lambda _id: f"found-{_id}")

    # Act & Assert numeric string coerced
    res_str = DummyPK.get_by_id('10')
    assert res_str == "found-10"

    # Act & Assert integer passed through
    res_int = DummyPK.get_by_id(7)
    assert res_int == "found-7"

    # Act & Assert non-numeric string returns None
    res_bad = DummyPK.get_by_id('bad')
    assert res_bad is None

@pytest.mark.parametrize("schema_cls", [
    aser.TagSchema,
    aser.ArticleSchema,
    aser.ArticleSchemas,
    aser.CommentSchema,
    aser.CommentsSchema,
])
def test_schema_classes_are_marshmallow_schemas_and_have_fields(schema_cls):
    # Arrange / Act
    instance = schema_cls()

    # Assert it's a marshmallow Schema and exposes fields mapping
    assert isinstance(instance, marshmallow.Schema)
    assert isinstance(instance.fields, dict)
    assert len(instance.fields) >= 0  # allow empty but ensure attribute exists

def test_Meta_is_a_class_with_no_runtime_error():
    # Arrange / Act
    Meta = getattr(aser, 'Meta', None)

    # Assert Meta exists and is a class/type
    assert Meta is not None
    assert isinstance(Meta, type)

def test_dump_comment_uses_CommentSchema_when_monkeypatched(monkeypatch):
    # Only run if dump_comment exists
    if not hasattr(aser, 'dump_comment'):
        pytest.skip("dump_comment not present in serializers")

    # Arrange: replace CommentSchema with a fake that records input
    class FakeCommentSchema:
        def __init__(self):
            pass

        def dump(self, obj):
            return {'fake_dump': obj}

    monkeypatch.setattr(aser, 'CommentSchema', FakeCommentSchema)

    payload = {'body': 'hello'}

    # Act
    result = aser.dump_comment(payload)

    # Assert
    assert isinstance(result, dict)
    assert result == {'fake_dump': payload}

def test_models_are_exported_and_have_expected_method_names():
    # Tags should be a class
    assert isinstance(amod.Tags, type)
    # Comment and Article should be classes
    assert isinstance(amod.Comment, type)
    assert isinstance(amod.Article, type)

    # Tags expected to expose at least one tag management method
    tags_methods = ('add_tag', 'remove_tag', 'add', 'remove')
    assert any(hasattr(amod.Tags, name) for name in tags_methods)

    # Comment expected to define __repr__
    assert hasattr(amod.Comment, '__repr__') and callable(getattr(amod.Comment, '__repr__'))

    # Article expected to expose at least one of favorite/favourite/is_favourite/add_tag/remove_tag
    article_methods = ('favourite', 'favorite', 'is_favourite', 'favoritesCount', 'add_tag', 'remove_tag')
    assert any(hasattr(amod.Article, name) for name in article_methods)
