import numpy as np
import pytest

from support_copilot.config import Settings
from support_copilot.embeddings import FastEmbedAdapter, validate_vector


class FakeModel:
    def embed(self, texts, batch_size):
        return iter([np.ones(384) * (index + 1) for index, _ in enumerate(texts)])

    def query_embed(self, text):
        # A distinct output proves the adapter uses the query-specific encoding path.
        return iter([np.arange(384, dtype=float)])


def test_adapter_with_fixed_vectors_and_query_path():
    adapter = FastEmbedAdapter(Settings(), model_factory=lambda **kwargs: FakeModel())
    assert adapter.embed_documents(["return an item", "shipping"]) == [[1.0] * 384, [2.0] * 384]
    assert adapter.embed_query("refund") == list(map(float, range(384)))


def test_model_is_lazy_and_empty_batch_does_not_load_it():
    def fail_if_loaded(**kwargs):
        pytest.fail("An empty batch must not load the model")

    adapter = FastEmbedAdapter(Settings(), model_factory=fail_if_loaded)
    assert adapter.embed_documents([]) == []


@pytest.mark.parametrize("text", ["", " ", "\n"])
def test_empty_query_and_document_rejected(text):
    adapter = FastEmbedAdapter(Settings())
    with pytest.raises(ValueError):
        adapter.embed_query(text)
    with pytest.raises(ValueError):
        adapter.embed_documents([text])


@pytest.mark.parametrize(
    "vector",
    [[1.0] * 383, [0.0] * 384, [float("nan")] * 384, [float("inf")] * 384],
)
def test_bad_embeddings_rejected_before_storage(vector):
    with pytest.raises(ValueError):
        validate_vector(vector)


def test_model_returning_too_few_vectors_is_rejected():
    class ShortModel(FakeModel):
        def embed(self, texts, batch_size):
            return iter([np.ones(384)])

    adapter = FastEmbedAdapter(Settings(), model_factory=lambda **kwargs: ShortModel())
    with pytest.raises(ValueError, match="number"):
        adapter.embed_documents(["first", "second"])


def test_unsupported_embedding_provider_rejected():
    with pytest.raises(ValueError, match="provider"):
        FastEmbedAdapter(Settings(embed_provider="unknown"))


def test_settings_repr_does_not_reveal_database_credentials():
    settings = Settings(database_url="postgresql://name:private-value@localhost/db")
    assert "private-value" not in repr(settings)
