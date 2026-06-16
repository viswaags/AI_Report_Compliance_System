from app.database.db import Base, engine
from app.models import *

Base.metadata.create_all(bind=engine)

print("Tables created successfully")