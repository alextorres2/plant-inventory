from datetime import date
from io import BytesIO

import av
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from PIL.ImageOps import exif_transpose
from pillow_heif import register_avif_opener, register_heif_opener
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import Plant as PlantSchema, PlantCreate, PlantPhotoRead
from app.storage import LocalPhotoStorage, get_photo_storage

router = APIRouter(
    prefix="/plants",
    tags=["plants"]
)

register_heif_opener()
register_avif_opener()

MAX_PHOTO_SIZE = 10 * 1024 * 1024
MAX_LIVE_PHOTO_VIDEO_SIZE = 50 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MAX_LIVE_PHOTO_DURATION_SECONDS = 30
SUPPORTED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}
NORMALIZE_TO_JPEG_FORMATS = {"HEIF", "HEIC", "AVIF", "MPO"}

@router.get("/", response_model=list[PlantSchema])
def get_plants(db: Session = Depends(get_db)):
    return db.query(models.Plant).all()

@router.get("/{plant_id}", response_model=PlantSchema)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant

@router.post("/", response_model=PlantSchema)
def create_plant(plant: PlantCreate, db: Session = Depends(get_db)):
    new_plant = models.Plant(**plant.model_dump())
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    return new_plant

@router.put("/{plant_id}", response_model=PlantSchema)
def update_plant(plant_id: int, updated_plant: PlantCreate, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    for field, value in updated_plant.model_dump().items():
        setattr(plant, field, value)

    db.commit()
    db.refresh(plant)
    return plant

@router.delete("/{plant_id}")
def delete_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    storage: LocalPhotoStorage = Depends(get_photo_storage),
):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    photo_storage_keys = [photo.storage_key for photo in plant.photos]
    db.delete(plant)
    db.commit()
    for storage_key in photo_storage_keys:
        storage.delete(storage_key)
    return {"message": "Plant deleted successfully"}


def _photo_response(photo: models.PlantPhoto) -> dict:
    return {
        "id": photo.id,
        "date_taken": photo.date_taken,
        "caption": photo.caption,
        "image_url": f"/plants/photos/{photo.id}/image",
    }


def _validate_image(content: bytes) -> tuple[bytes, str, str]:
    try:
        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions are too large.")
            image.verify()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning, ValueError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from None

    if image_format in SUPPORTED_IMAGE_FORMATS:
        content_type, extension = SUPPORTED_IMAGE_FORMATS[image_format]
        return content, content_type, extension
    if image_format in NORMALIZE_TO_JPEG_FORMATS:
        try:
            with Image.open(BytesIO(content)) as image:
                normalized = exif_transpose(image).convert("RGB")
                jpeg = BytesIO()
                normalized.save(jpeg, format="JPEG", quality=90, optimize=True)
        except (OSError, ValueError):
            raise HTTPException(status_code=400, detail="The uploaded HEIF-family image could not be decoded.") from None
        return jpeg.getvalue(), "image/jpeg", "jpg"
    raise HTTPException(
        status_code=415,
        detail=(
            f"Unsupported image format ({image_format or 'unrecognized'}). "
            "Upload JPEG, PNG, WebP, HEIC/HEIF, or AVIF."
        ),
    )


def _extract_video_frame(content: bytes) -> tuple[bytes, str, str]:
    try:
        with av.open(BytesIO(content), mode="r") as video:
            if video.duration is not None and video.duration / av.time_base > MAX_LIVE_PHOTO_DURATION_SECONDS:
                raise HTTPException(status_code=413, detail="Live Photo video component exceeds 30 seconds.")
            stream = next((item for item in video.streams if item.type == "video"), None)
            if stream is None:
                raise HTTPException(status_code=400, detail="The uploaded MOV file has no video stream.")

            frame = next(video.decode(stream), None)
            if frame is None:
                raise HTTPException(status_code=400, detail="The uploaded MOV file contains no decodable video frame.")
            if frame.width * frame.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Video frame dimensions are too large.")

            image = frame.to_image()
            image = exif_transpose(image).convert("RGB")
            jpeg = BytesIO()
            image.save(jpeg, format="JPEG", quality=90, optimize=True)
            return jpeg.getvalue(), "image/jpeg", "jpg"
    except HTTPException:
        raise
    except (av.error.FFmpegError, OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="The uploaded MOV file could not be decoded. Upload a valid iPhone Live Photo video component.",
        ) from None


def _is_video_upload(image: UploadFile, content: bytes) -> bool:
    filename = image.filename or ""
    content_type = image.content_type or ""
    video_brands = {b"qt  ", b"isom", b"iso2", b"mp41", b"mp42", b"M4V ", b"MSNV", b"3gp4"}
    is_quicktime_container = (
        len(content) >= 12
        and content[4:8] == b"ftyp"
        and content[8:12] in video_brands
    )
    return (
        filename.lower().endswith(".mov")
        or content_type.lower().startswith("video/")
        or is_quicktime_container
    )


@router.get("/{plant_id}/photos", response_model=list[PlantPhotoRead])
def get_plant_photos(plant_id: int, db: Session = Depends(get_db)):
    if db.get(models.Plant, plant_id) is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    photos = (
        db.query(models.PlantPhoto)
        .filter(models.PlantPhoto.plant_id == plant_id)
        .order_by(models.PlantPhoto.date_taken.desc(), models.PlantPhoto.id.desc())
        .all()
    )
    return [_photo_response(photo) for photo in photos]


@router.post("/{plant_id}/photos", response_model=PlantPhotoRead, status_code=201)
async def upload_plant_photo(
    plant_id: int,
    image: UploadFile = File(...),
    date_taken: date | None = Form(default=None),
    caption: str | None = Form(default=None, max_length=1000),
    db: Session = Depends(get_db),
    storage: LocalPhotoStorage = Depends(get_photo_storage),
):
    if db.get(models.Plant, plant_id) is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    content = await image.read(MAX_LIVE_PHOTO_VIDEO_SIZE + 1)
    if len(content) > MAX_LIVE_PHOTO_VIDEO_SIZE:
        raise HTTPException(status_code=413, detail="Upload exceeds the 50 MB limit.")
    is_video = _is_video_upload(image, content)
    if not is_video and len(content) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=413, detail="Still photo exceeds the 10 MB upload limit.")
    if is_video:
        stored_content, content_type, extension = _extract_video_frame(content)
    else:
        stored_content, content_type, extension = _validate_image(content)

    storage_key = storage.save(stored_content, extension)
    photo = models.PlantPhoto(
        plant_id=plant_id,
        storage_key=storage_key,
        content_type=content_type,
        date_taken=date_taken or date.today(),
        caption=caption.strip() if caption and caption.strip() else None,
    )
    try:
        db.add(photo)
        db.commit()
        db.refresh(photo)
    except Exception:
        db.rollback()
        storage.delete(storage_key)
        raise
    return _photo_response(photo)


@router.delete("/{plant_id}/photos/{photo_id}")
def delete_plant_photo(
    plant_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    storage: LocalPhotoStorage = Depends(get_photo_storage),
):
    photo = (
        db.query(models.PlantPhoto)
        .filter(
            models.PlantPhoto.id == photo_id,
            models.PlantPhoto.plant_id == plant_id,
        )
        .first()
    )
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    storage_key = photo.storage_key
    db.delete(photo)
    db.commit()
    storage.delete(storage_key)
    return {"message": "Photo deleted successfully"}


@router.get("/photos/{photo_id}/image")
def get_photo_image(
    photo_id: int,
    db: Session = Depends(get_db),
    storage: LocalPhotoStorage = Depends(get_photo_storage),
):
    photo = db.get(models.PlantPhoto, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    path = storage.path_for(photo.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(path, media_type=photo.content_type)