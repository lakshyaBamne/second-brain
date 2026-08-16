from bson import ObjectId
from bson.errors import InvalidId
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    def __init__(self, doc):
        self._doc = doc

    @property
    def id(self):
        return str(self._doc["_id"])

    @property
    def email(self):
        return self._doc["email"]

    def check_password(self, password):
        return check_password_hash(self._doc["password_hash"], password)


def get_user_by_id(db, user_id):
    try:
        doc = db.users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        return None
    return User(doc) if doc else None


def get_user_by_email(db, email):
    doc = db.users.find_one({"email": email.strip().lower()})
    return User(doc) if doc else None


def create_user(db, email, password):
    doc = {"email": email.strip().lower(), "password_hash": generate_password_hash(password)}
    result = db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return User(doc)


def any_user_exists(db):
    return db.users.count_documents({}, limit=1) > 0
