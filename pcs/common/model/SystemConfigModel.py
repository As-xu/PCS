from pcs.common import db
from pcs.common.Enum.UserEnum import UserTypeEnum


class SystemConfigModel(db.Model):
    __tablename__ = "system_model_list"

    id = db.Column(db.Integer, db.Sequence(__tablename__ + '_id_seq'), primary_key=True)
    group_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.String)
    json_value = db.Column(db.Json)
