import pytest
import jwt

from App.Services.Auth.JwtService import JwtService

_svc = JwtService(secret="test-secret", algorithm="HS256", expire_minutes=60)


def test_encode_decode_roundtrip():
    token = _svc.encode("42")
    payload = _svc.decode(token)
    assert payload["sub"] == "42"


def test_decode_expired_token():
    expired_svc = JwtService(secret="test-secret", algorithm="HS256", expire_minutes=0)
    token = expired_svc.encode("1")
    with pytest.raises(jwt.ExpiredSignatureError):
        expired_svc.decode(token)


def test_decode_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        _svc.decode("not.a.valid.token")


def test_decode_wrong_secret():
    token = _svc.encode("99")
    other_svc = JwtService(secret="different-secret", algorithm="HS256", expire_minutes=60)
    with pytest.raises(jwt.InvalidSignatureError):
        other_svc.decode(token)
