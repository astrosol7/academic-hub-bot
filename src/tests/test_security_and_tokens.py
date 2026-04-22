import os
import unittest
from datetime import timedelta

from fastapi import HTTPException

from api.auth import create_token, decode_token, _require_access_token, _require_refresh_token
from api.bot import _validate_ids


class SecurityAndTokenTests(unittest.TestCase):
    def test_access_token_rejected_by_refresh_guard(self) -> None:
        token = create_token({"sub": "abc", "role": "ADMIN"}, timedelta(minutes=1))
        claims = decode_token(token)
        with self.assertRaises(HTTPException):
            _require_refresh_token(claims)

    def test_refresh_token_rejected_by_access_guard(self) -> None:
        token = create_token({"sub": "abc", "refresh": True}, timedelta(minutes=1))
        claims = decode_token(token)
        with self.assertRaises(HTTPException):
            _require_access_token(claims)

    def test_token_has_required_time_claims(self) -> None:
        token = create_token({"sub": "abc", "role": "ADMIN"}, timedelta(minutes=1))
        claims = decode_token(token)
        for key in ("iat", "nbf", "exp", "jti"):
            self.assertIn(key, claims)

    def test_validate_ids_accepts_expected_formats(self) -> None:
        _validate_ids("123456789", "SIT-ST-2029-00004")

    def test_validate_ids_rejects_bad_formats(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_ids("abc", "SIT-ST-2029-00004")
        with self.assertRaises(HTTPException):
            _validate_ids("123456789", "bad id !!!")


if __name__ == "__main__":
    unittest.main()

