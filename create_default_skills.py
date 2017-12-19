from models import *

db.session.add(Skill(name='HTML'))
db.session.add(Skill(name='CSS'))
db.session.add(Skill(name='JavaScript'))
db.session.add(Skill(name='AngularJS'))
db.session.add(Skill(name='Node JS'))
db.session.add(Skill(name='Flask'))
db.session.add(Skill(name='PHP'))
db.session.add(Skill(name='SQL'))
db.session.add(Skill(name='MySQL'))
db.session.add(Skill(name='SQL Alchemy'))

db.session.commit()
