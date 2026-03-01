from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base


class Theme(Base):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("themes.id"), nullable=True)


class Color(Base):
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    rgb = Column(String(6), nullable=False)
    is_trans = Column(Boolean, nullable=False, default=False)


class PartCategory(Base):
    __tablename__ = "part_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)


class Part(Base):
    __tablename__ = "parts"

    part_num = Column(String(20), primary_key=True)
    name = Column(String(250), nullable=False)
    part_cat_id = Column(Integer, ForeignKey("part_categories.id"), nullable=True)
    part_material = Column(String(50), nullable=True)


class PartRelationship(Base):
    __tablename__ = "part_relationships"

    rel_type = Column(String(1), nullable=False)
    child_part_num = Column(String(20), ForeignKey("parts.part_num"), primary_key=True)
    parent_part_num = Column(String(20), ForeignKey("parts.part_num"), primary_key=True)


class Set(Base):
    __tablename__ = "sets"

    set_num = Column(String(20), primary_key=True)
    name = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    theme_id = Column(Integer, ForeignKey("themes.id"), nullable=True)
    num_parts = Column(Integer, nullable=False, default=0)
    img_url = Column(String(500), nullable=True)


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, default=1)
    set_num = Column(String(20), ForeignKey("sets.set_num"), nullable=False)


class InventoryPart(Base):
    __tablename__ = "inventory_parts"

    inventory_id = Column(Integer, ForeignKey("inventories.id"), primary_key=True)
    part_num = Column(String(20), ForeignKey("parts.part_num"), primary_key=True)
    color_id = Column(Integer, ForeignKey("colors.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    is_spare = Column(Boolean, nullable=False, default=False)
    img_url = Column(String(500), nullable=True)
