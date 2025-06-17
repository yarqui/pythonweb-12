from fastapi import HTTPException
from fastapi import UploadFile
import cloudinary
import cloudinary.exceptions
import cloudinary.uploader

__all__ = ["upload_file"]


def upload_file(contents: bytes, username: str) -> str:
    """
    Uploads file content to Cloudinary and constructs a formatted URL.

    This function takes raw file content as bytes, uploads it to a specific
    folder in Cloudinary using the username to create a unique public ID,
    and overwrites any existing file for that user. It then generates and
    returns a URL for a 250x250 cropped version of the image.

    Args:
        contents (bytes): The raw byte content of the file to be uploaded.
        username (str): The username of the user, used to create a unique path
                        for the file in Cloudinary.

    Raises:
        HTTPException: Raises a 400 Bad Request if the Cloudinary API
                       returns an error during the upload process.

    Returns:
        str: The public URL of the transformed and uploaded image.
    """
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
