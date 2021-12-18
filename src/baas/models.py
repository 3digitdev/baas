from datetime import datetime
from typing import Any, Dict

from pony import orm

db = orm.Database()


class User(db.Entity):
    _table_ = "user"
    key = orm.Required(str, unique=True)
    secret = orm.Required(bytes)
    created_on = orm.Required(datetime, default=datetime.now())
    last_accessed = orm.Required(datetime, default=datetime.now())
    # Relationship(s)
    bools = orm.Set(lambda: db.Bool)


class Bool(db.Entity):
    _table_ = "boolean"
    name = orm.Required(str)
    value = orm.Required(bool)
    created_on = orm.Required(datetime, default=datetime.now())
    # Relationship(s)
    owner = orm.Required(User)

    def as_json(self, simple: bool = False) -> Dict[str, Any]:
        if simple:
            return {"value": self.value}
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "owner": self.owner.id,
        }
