# reference: https://codeburst.io/jwt-authorization-in-flask-c63c1acf4eeb
import validators
from datetime import datetime
from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jti)
from libraries.devetek.session import store_revoke_token, store_revoke_refresh_token
from models.account.client import AccountClient
from models.account.member import AccountMember, member_data_input_serializer
from models.account.email import AccountEmail
from web.helpers import success_http_response, cleaning_dict
from web.helpers.error_handler import error_http_code
from libraries.hash import verify_hash256
from web.helpers.jwt_handler import generate_token

parser = reqparse.RequestParser()
parser.add_argument('X-Devetek-App-Id', required=True,
                    location='headers', type=int)
parser.add_argument('member_email', required=False)
parser.add_argument('member_username', required=False)
parser.add_argument('member_password',
                    help='Password cannot be blank', required=True)


class AuthorizationController(Resource):
    def __init__(self):
        self.data = cleaning_dict(parser.parse_args())
        self.app_id = self.data['X-Devetek-App-Id']
        self.valid_user = member_data_input_serializer(self.data)
        self.return_user = self.data["member_email"] if "member_email" in self.data else self.data["member_username"]

    def post(self):
        try:
            is_password_valid = False
            is_user_registered = False

            if self.app_id is None:
                return success_http_response("You're not sending correct app identifier.", False)

            client = AccountClient.query.filter_by(
                client_id=self.app_id).first()

            if client is None:
                return success_http_response("App not registered in Devetek.", False)

            validate_input = self.authorization_validation(client)

            if validate_input["invalid_key"] != "":
                return success_http_response(validate_input["message"], False)

            if validate_input["valid_key"] != "member_username":
                member_email = AccountEmail.query.filter_by(
                    email_text=self.data["member_email"]).first()

                member = None if member_email is None else AccountMember.query.filter_by(
                    member_id=member_email.email_member_id).first()

                if member is None:
                    return success_http_response("You're not register in {}.".format(client.client_name), False)

                if member is not None:
                    is_password_valid = verify_hash256(
                        self.data["member_password"], member.member_password)
                    if is_password_valid == False:
                        return success_http_response("You're input invalid password.", False)
            else:
                member = AccountMember.query.filter_by(
                    member_username=self.data["member_username"]).first()

                if member is None:
                    return success_http_response(
                        "You're not register in {}.".format(client.client_name), False)

                if member is not None:
                    is_password_valid = verify_hash256(
                        self.data["member_password"], member.member_password)
                    if is_password_valid == False:
                        return success_http_response("You're input invalid password.", False)

            if member is not None:
                member_dict = member.to_dict()

                if member.member_apps_ids is not None:
                    for app in member.member_apps_ids:
                        if app.client_id == int(self.app_id):
                            is_user_registered = True

                if is_user_registered == False:
                    return success_http_response("You're not registered in this app.", False)

                member_id = member_dict["email_member_id"] if "email_member_id" in member_dict else member_dict["member_id"]

                token = generate_token(member_id)

                if token["access_token"]:
                    return success_http_response('{} success create session/token.'. format(self.return_user), True, token)

                return success_http_response('{} fail create session/token, contact administrator.'. format(self.return_user), True, token)

        except Exception as error:
            # TODO: Log error to logger services
            return error_http_code(500, {"message": "Something went wrong, please try again later."})

    def authorization_validation(self, client):
        valid_response = {
            "valid_key": "",
            "invalid_key": "",
            "message": "",
        }

        if "member_email" in self.data:
            if not validators.email(self.data["member_email"]):
                valid_response["invalid_key"] = "member_email"
                valid_response["message"] = "Your email address is invalid. Please enter a valid address."
            else:
                valid_response["valid_key"] = "member_email"

        if "member_username" in self.data:
            if self.data['member_username'].isalnum() == False:
                valid_response["invalid_key"] = "member_username"
                valid_response["message"] = "Username only allow alphanumeric characters."
            else:
                valid_response["valid_key"] = "member_username"

        return valid_response
