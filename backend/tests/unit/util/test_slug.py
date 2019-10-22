import pytest
from uuid import uuid4

from backend.util.slug import slug_to_uuid, uuid_to_slug
from backend.errors.request_error import SlugDecodeError


def test_uuid_slug_uuid():
    uuid_value = uuid4()
    slug_value = uuid_to_slug(uuid_value)

    assert uuid_value == slug_to_uuid(slug_value)

    with pytest.raises(SlugDecodeError):
        slug_to_uuid("randomstring")
