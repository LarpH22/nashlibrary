import os
from werkzeug.utils import secure_filename


class FileStorage:
    def __init__(self, upload_folder: str, allowed_extensions: set[str]):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        os.makedirs(upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save(self, file, filename: str | None = None) -> str:
        original_filename = filename or secure_filename(file.filename)
        destination = os.path.join(self.upload_folder, original_filename)
        file.save(destination)
        return original_filename
