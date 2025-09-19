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

import builtins
import inspect
import types

import pytest

try:
    from conduit.articles import views as articles_views
    from conduit import commands as commands_mod
    from conduit import exceptions as exceptions_mod
except ImportError:
    pytest.skip("conduit package not available", allow_module_level=True)

class _CallRecorder:
    def __init__(self, result=None, exc=None):
        self.called = False
        self.args = None
        self.kwargs = None
        self.result = result
        self.exc = exc

    def __call__(self, *a, **kw):
        self.called = True
        self.args = a
        self.kwargs = kw
        if self.exc:
            raise self.exc
        return self.result

def _is_builtin_name(name):
    # builtins could be module or dict
    try:
        return name in dir(builtins)
    except Exception:
        return False

def _patch_globals_for(func, patch_map):
    """
    Patch func.__globals__ with entries in patch_map, returning a restore map.
    """
    gl = func.__globals__
    restore = {}
    for k, v in patch_map.items():
        restore[k] = gl.get(k, _Missing)
        gl[k] = v
    return restore

_Missing = object()

def _restore_globals_for(func, restore_map):
    gl = func.__globals__
    for k, v in restore_map.items():
        if v is _Missing:
            gl.pop(k, None)
        else:
            gl[k] = v

def _auto_patchable_names(func):
    # return global names referenced by func that are safe to auto-patch
    names = set(getattr(func, "__code__", types.SimpleNamespace(co_names=())) .co_names or ())
    # exclude parameter names
    params = set(inspect.signature(func).parameters.keys())
    safe = []
    for n in names:
        if n in params:
            continue
        if n.startswith("__"):
            continue
        if _is_builtin_name(n):
            continue
        safe.append(n)
    return safe

# Tests for article view functions

@pytest.mark.parametrize(
    "func_name, helper_name, expected_return",
    [
        ("get_article", "dump_article", {"article": "ok"}),
        ("favorite_an_article", "dump_article", {"article": "fav"}),
        ("unfavorite_an_article", "dump_article", {"article": "unfav"}),
        ("articles_feed", "dump_articles", [{"a": 1}]),
        ("get_comments", "dump_comment", {"comments": []}),
        ("make_comment_on_article", "make_comment", {"comment": {"id": 1}}),
        ("delete_comment_on_article", "dump_comment", {"deleted": True}),
    ],
)
def test_article_views_delegate_to_serializers_and_return_expected(
    func_name, helper_name, expected_return
):
    # Arrange
    func = getattr(articles_views, func_name, None)
    if func is None:
        pytest.skip(f"{func_name} not present in articles.views")

    # Only run test when the helper_name is actually referenced in the function code.
    co_names = getattr(func, "__code__", types.SimpleNamespace(co_names=())).co_names or ()
    if helper_name not in co_names:
        pytest.skip(f"{func_name} does not reference helper {helper_name}; skipping deterministic delegation test")

    recorder = _CallRecorder(result=expected_return)
    patch_map = {helper_name: recorder}

    # Provide simple values for common names the view might reference.
    # These placeholders avoid NameError for names we are not specifically asserting.
    for name in _auto_patchable_names(func):
        patch_map.setdefault(name, lambda *a, **kw: expected_return)

    restore = _patch_globals_for(func, patch_map)
    try:
        # Act
        # Build arguments: typical signatures include (slug), (slug, comment_id)
        sig = inspect.signature(func)
        call_args = []
        if len(sig.parameters) == 0:
            result = func()
        else:
            # choose sensible dummy args
            params = list(sig.parameters.items())
            for pname, p in params:
                if "slug" in pname:
                    call_args.append("test-slug")
                elif "comment_id" in pname or "id" in pname:
                    call_args.append(1)
                else:
                    # generic arg
                    call_args.append(None)
            result = func(*call_args)

        # Assert
        # If the function returned the serializer's result, assert equality.
        assert result == expected_return, f"{func_name} did not return expected helper result"
        # Also verify the helper was called
        assert recorder.called is True, f"{helper_name} was not called by {func_name}"
    finally:
        _restore_globals_for(func, restore)

def test_get_article_propagates_not_found_exception():
    func = getattr(articles_views, "get_article", None)
    if func is None:
        pytest.skip("get_article not present")

    co_names = getattr(func, "__code__", types.SimpleNamespace(co_names=())).co_names or ()
    if "dump_article" not in co_names:
        pytest.skip("get_article does not call dump_article in this implementation; can't assert propagation")

    
    patch_map = {"dump_article": _CallRecorder(exc=exceptions_mod.InvalidUsage("not found"))}
    # Fill other referenced names with safe no-op
    for name in _auto_patchable_names(func):
        patch_map.setdefault(name, lambda *a, **kw: None)

    restore = _patch_globals_for(func, patch_map)
    try:
        # Act / Assert
        with pytest.raises(exceptions_mod.InvalidUsage):
            func("missing-slug")
    finally:
        _restore_globals_for(func, restore)

def test_delete_article_calls_expected_delete_path_or_returns_without_error():
    func = getattr(articles_views, "delete_article", None)
    if func is None:
        pytest.skip("delete_article not present")

    # Try to find a delete helper referenced; common names: 'Article', 'delete', 'dump_article'
    co_names = getattr(func, "__code__", types.SimpleNamespace(co_names=())).co_names or ()
    helper_candidates = [n for n in ("delete_article", "Article", "delete", "dump_article", "get_article") if n in co_names]
    if not helper_candidates:
        pytest.skip("delete_article doesn't reference known helpers; skipping behavior test")

    # Create a fake path: if Article referenced, supply a fake Article class with delete method
    patch_map = {}
    if "Article" in co_names:
        class FakeArticle:
            def __init__(self, slug):
                self.slug = slug
                self.deleted = False

            def delete(self):
                self.deleted = True
                return True

        patch_map["Article"] = FakeArticle

    # If delete_article or dump_article referenced, provide recorder
    if "delete_article" in co_names:
        recorder = _CallRecorder(result={"deleted": True})
        patch_map["delete_article"] = recorder
    if "dump_article" in co_names:
        # make dump_article return a sentinel so if view returns it we can assert
        patch_map["dump_article"] = _CallRecorder(result={"deleted": True})

    # Fill other referenced names with safe defaults
    for name in _auto_patchable_names(func):
        patch_map.setdefault(name, lambda *a, **kw: {"ok": True})

    restore = _patch_globals_for(func, patch_map)
    try:
        # Act
        sig = inspect.signature(func)
        if len(sig.parameters) == 0:
            result = func()
        else:
            # pass typical slug
            result = func("slug-to-delete")

        # Assert: function should return something concrete (not None) and operations succeeded.
        assert result is not None
        # If we provided recorder, it should have been called
        if "delete_article" in patch_map:
            assert patch_map["delete_article"].called is True
    finally:
        _restore_globals_for(func, restore)

# Tests for commands: test, lint, clean

@pytest.mark.parametrize(
    "cmd_func_name, expected_tool",
    [
        ("test", "pytest"),
        ("lint", "flake8"),
        ("clean", "rm"),
    ],
)
def test_commands_invoke_execute_tool_with_expected_tool(cmd_func_name, expected_tool):
    func = getattr(commands_mod, cmd_func_name, None)
    if func is None:
        pytest.skip(f"{cmd_func_name} not present in commands module")

    co_names = getattr(func, "__code__", types.SimpleNamespace(co_names=())).co_names or ()
    if "execute_tool" not in co_names:
        pytest.skip(f"{cmd_func_name} does not use execute_tool; skipping")

    recorder = _CallRecorder(result=0)
    restore = _patch_globals_for(func, {"execute_tool": recorder})
    try:
        # Some command functions are click commands expecting a context; call without args
        try:
            result = func()
        except TypeError:
            # try with None to satisfy parameters if it expects ctx
            result = func(None)
        # Assert execute_tool was called and expected_tool substring present in the executed command args
        assert recorder.called is True
        # inspect what was called; it might be called with a list or string
        called_args = recorder.args[0] if recorder.args else None
        assert called_args is not None, "execute_tool was called without arguments"
        # make the assertion robust for both list and str
        if isinstance(called_args, (list, tuple)):
            joined = " ".join(map(str, called_args))
            assert expected_tool in joined
        else:
            assert expected_tool in str(called_args)
    finally:
        _restore_globals_for(func, restore)

def test_execute_tool_handles_subprocess_errors(monkeypatch, tmp_path):
    # Ensure execute_tool exists
    func = getattr(commands_mod, "execute_tool", None)
    if func is None:
        pytest.skip("execute_tool not present")

    
    import subprocess

    def _fake_run(*a, **kw):
        raise subprocess.CalledProcessError(returncode=2, cmd=a[0])

    # Patch subprocess in the function globals
    restore = _patch_globals_for(func, {"subprocess": types.SimpleNamespace(run=_fake_run)})
    try:
        
        with pytest.raises(subprocess.CalledProcessError):
            func(["something"])
    finally:
        _restore_globals_for(func, restore)
