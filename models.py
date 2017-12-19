from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    image_url = db.Column(db.String(250), nullable=False)
    google_plus_link = db.Column(db.String(250), nullable=False)

    @property
    def serialize(self):
        """Returns serialized form of the User object."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'image_url': self.image_url,
            'google_plus_link': self.google_plus_link
        }


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class UserSkill(db.Model):
    __tablename__ = 'user_skills'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'),
                         primary_key=True)
    user = db.relationship(User)
    skill = db.relationship(Skill)

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'skill_id': self.skill_id
        }


class Endorse(db.Model):
    __tablename__ = 'endorses'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'),
                         primary_key=True)
    endorser_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    user = db.relationship(User, foreign_keys=[user_id])
    skill = db.relationship(Skill)
    endorser = db.relationship(User, foreign_keys=[endorser_id])

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'skill_id': self.skill_id,
            'endorser_id': self.endorser_id
        }
