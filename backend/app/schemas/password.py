from pydantic import BaseModel


class ChangePasswordRequest(
    BaseModel
):
    old_password: str
    new_password: str


class ResetPasswordRequest(
    BaseModel
):
    token: str
    new_password: str


class ForgotPasswordRequest(
    BaseModel
):
    email: str

class AdminResetPasswordRequest(
    BaseModel
):
    new_password: str