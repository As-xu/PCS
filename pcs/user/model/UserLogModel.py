from pcs.common import db


class UserLogModel(db.Model):
    __tablename__ = "user_log_list"

    id = db.Column(db.Integer, db.Sequence(__tablename__ + '_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    log_type = db.Column(db.String, nullable=False)
    log_content = db.Column(db.String)
    create_date = db.Column(db.DateTime, nullable=False)
    create_uid = db.Column(db.Integer, nullable=False)
    write_date = db.Column(db.DateTime, nullable=False)
    write_uid = db.Column(db.Integer, nullable=False)
