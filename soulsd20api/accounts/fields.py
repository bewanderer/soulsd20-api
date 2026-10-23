import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

logger = logging.getLogger(__name__)

ENCRYPTED_PREFIX = 'enc1:'


def _fernet():
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', '')
    if not key:
        raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY is not set.')
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """
    TextField encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).

    Values written before encryption existed have no prefix; they are read as
    plain text and encrypted on their next save. A value that cannot be
    decrypted (wrong or rotated key) reads as None, so Patreon refreshes fail
    silently instead of crashing the request.
    """

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Same column as a TextField, so no schema migration is needed.
        return name, 'django.db.models.TextField', args, kwargs

    def from_db_value(self, value, expression, connection):
        if not value or not value.startswith(ENCRYPTED_PREFIX):
            return value
        try:
            return _fernet().decrypt(value[len(ENCRYPTED_PREFIX):].encode()).decode()
        except InvalidToken:
            logger.warning('Encrypted field value could not be decrypted; treating it as empty.')
            return None

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value or value.startswith(ENCRYPTED_PREFIX):
            return value
        return ENCRYPTED_PREFIX + _fernet().encrypt(value.encode()).decode()
