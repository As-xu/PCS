from pcs import db


class SystemConfigModel(db.Model):
    __tablename__ = "system_config_list"

    id = db.Column(db.Integer, db.Sequence(__tablename__ + '_id_seq'), primary_key=True)
    group_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.String)
    json_value = db.Column(db.JSON)
    create_date = db.Column(db.DateTime, nullable=False)
    create_uid = db.Column(db.Integer, nullable=False)
    write_date = db.Column(db.DateTime, nullable=False)
    write_uid = db.Column(db.Integer, nullable=False)
    memo = db.Column(db.String)



