from fastapi import HTTPException
from fastapi import UploadFile
import cloudinary
import cloudinary.exceptions
import cloudinary.uploader

__all__ = ["upload_file"]


def upload_file(contents: bytes, username: str) -> str:
    public_id = f"RestApp/{username}"

    try:

        result = cloudinary.uploader.upload(
            contents, public_id=public_id, overwrite=True
        )
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250,
            height=250,
            crop="fill",
            version=result.get("version"),
            folder="RestApp",
            resource_type="image",
        )
        return src_url

    except cloudinary.exceptions.Error as e:
        raise HTTPException(status_code=400, detail=f"Cloudinary error: {e}") from e
