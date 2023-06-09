from pcs import db


class UserLoginModel(db.Model):
    __tablename__ = "user_login_list"

    id = db.Column(db.Integer, db.Sequence(__tablename__ + '_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    login_time = db.Column(db.DateTime, nullable=False)
    login_ip = db.Column(db.String, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False)
    create_uid = db.Column(db.Integer, nullable=False)
    write_date = db.Column(db.DateTime, nullable=False)
    write_uid = db.Column(db.Integer, nullable=False)
