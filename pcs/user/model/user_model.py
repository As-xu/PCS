from pcs.base.base_model import BaseModel
from pcs import db
from pcs.common.Enum.user_enum import UserTypeEnum


class UserModel(db.Model):
    __tablename__ = "user_list"

    id = db.Column(db.Integer, db.Sequence(__tablename__ + '_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    user_type = db.Column(db.Enum(UserTypeEnum), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False)
    create_uid = db.Column(db.Integer, nullable=False)
    write_date = db.Column(db.DateTime, nullable=False)
    write_uid = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)
    memo = db.Column(db.String)

