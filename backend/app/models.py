from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    species: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(100))
    date_acquired: Mapped[date] = mapped_column(Date)

    photos: Mapped[list["PlantPhoto"]] = relationship(
        back_populates="plant",
        cascade="all, delete-orphan",
        order_by=lambda: (PlantPhoto.date_taken.desc(), PlantPhoto.id.desc()),
    )

    @property
    def latest_photo_url(self) -> str | None:
        if not self.photos:
            return None
        return f"/plants/photos/{self.photos[0].id}/image"


class PlantPhoto(Base):
    __tablename__ = "plant_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(80), unique=True)
    content_type: Mapped[str] = mapped_column(String(32))
    date_taken: Mapped[date] = mapped_column(Date)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    plant: Mapped[Plant] = relationship(back_populates="photos")