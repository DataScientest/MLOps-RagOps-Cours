import importlib
import pkgutil

import app


def test_import_all_backend_modules():
    names = [m.name for m in pkgutil.walk_packages(app.__path__, prefix="app.")]
    assert "app.main" in names
    for name in names:
        importlib.import_module(name)


def test_models_are_configurable_by_env():
    from app.core.config import settings

    assert settings.LITELLM_MODEL == "groq-llama3"
    assert settings.EMBEDDING_MODEL_NAME == "local-embeddings"
    assert settings.EMBED_DIM == 384
