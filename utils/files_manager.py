import csv
import json

from datetime import datetime

from pathlib import Path
from pyparsing import Any

class FilesManager:
    filename = None
    folder_roots = {
        "data": "./data",
        "logs": "./logs",
    }

    def __init__(self, verbose=False, filename=None):
        self.verbose = verbose
        self.filename = filename

    def __strip_colors(self, text: str | list[str]) -> str:
        import re

        if isinstance(text, list):
            text = "\n".join(text)

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def read_file(self, path: Path, mode="bulk") -> list[str]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")

            if mode == "bulk":
                return [text]
            elif mode == "lines":
                return text.splitlines()
            else:
                return [line for line in text.splitlines() if line]
        except Exception as e:
            print(f"Error reading file: {e}")

    def write_to_file(self, data: str | list[str], prefix=None, **kwargs: Any) -> str:
        ext = kwargs.get("ext", "txt")
        filetype = kwargs.get("filetype", "data")
        mode = kwargs.get("mode", "w")
        strip_formatting = kwargs.get("strip_formatting", False)

        prefix = prefix if prefix else "output"
        auto_filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = kwargs.get("filename", auto_filename)
        path_to_write = f"{self.folder_roots.get(filetype, self.folder_roots['data'])}/{filename}.{ext}"

        with open(path_to_write, mode, encoding="utf-8") as file_to_write:
            clean_data = self.__strip_colors(data) if strip_formatting else data

            if ext == "json":
                json_indent = kwargs.get("json_indent", 2)
                json.dump(
                    clean_data, file_to_write, indent=json_indent, ensure_ascii=False
                )
            elif ext == "csv":
                csv_fieldnames = kwargs.get("csv_fieldnames")

                if csv_fieldnames is None:
                    self.log.error("CSV fieldnames must be provided for CSV export.")
                    return

                writer = csv.DictWriter(
                    file_to_write, fieldnames=csv_fieldnames, extrasaction="ignore"
                )
                writer.writeheader()
                writer.writerows(clean_data)
            else:
                file_to_write.write(clean_data)

        return path_to_write
