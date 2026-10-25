import pytest

from apps.kardex.models import TipoDocumento


@pytest.fixture(autouse=True)
def _media_temporal(settings, tmp_path):
    """Los archivos subidos en las pruebas no quedan en MEDIA_ROOT."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def tipo_ci(db):
    return TipoDocumento.objects.get(descripcion="CI")
