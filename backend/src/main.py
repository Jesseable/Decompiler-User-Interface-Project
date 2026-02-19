from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from pathlib import Path
import json
import hashlib

app = FastAPI()

# Allow frontend dev server to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the selected folder
selected_data_dir: Path = Path("test_data_1")  # default folder


class DirectorySelection(BaseModel):
    directoryPath: str


@app.post("/config/select-directory")
async def select_directory(data: DirectorySelection):
    global selected_data_dir
    dir_path = Path(data.directoryPath)
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Directory does not exist")
    selected_data_dir = dir_path
    return {"message": "Analysis triggered"}


@app.get("/epochs")
async def get_epochs():
    file_path = selected_data_dir / "epochs.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="epochs.json not found")
    with open(file_path) as f:
        return json.load(f)


def compute_hash(file_path: Path) -> str:
    """Return SHA256 hash of file, or empty string if missing."""
    if not file_path.exists():
        return ""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


# ----------------------------
# IR endpoints
# ----------------------------
@app.get("/ir/{epoch}/procedures")
async def get_procedures(epoch: str):
    """Return a list of procedure objects with name + before/after hashes."""
    epoch_dir = selected_data_dir / epoch
    procedures_file = epoch_dir / "procedures_with_lines.json"

    if not procedures_file.exists():
        raise HTTPException(
            status_code=404, detail=f"procedures_with_lines.json not found for epoch {epoch}"
        )

    with open(procedures_file) as f:
        procedures_data = json.load(f)

    result = []
    for proc in procedures_data:
        # normalize to dict with 'name'
        if isinstance(proc, dict) and "name" in proc:
            proc_name = proc["name"]
        elif isinstance(proc, str):
            proc_name = proc
        else:
            continue  # skip invalid entries

        # compute IR file paths
        before_file = epoch_dir / "procedures" / proc_name / "before.ir"
        after_file = epoch_dir / "procedures" / proc_name / "after.ir"

        result.append({
            "name": proc_name,
            "beforeHash": compute_hash(before_file),
            "afterHash": compute_hash(after_file)
        })

    return result


@app.get("/ir/{epoch}/procedures_with_lines")
async def get_procedures_with_lines(epoch: str):
    """Return same as /ir/{epoch}/procedures, for frontend backwards compatibility."""
    return await get_procedures(epoch)


@app.get("/ir/{epoch}/{procedureName}/{type}")
async def get_procedure_ir(epoch: str, procedureName: str, type: str):
    """Return IR file as plain text with newlines preserved."""
    epoch_dir = selected_data_dir / epoch
    file_path = epoch_dir / "procedures" / procedureName / f"{type}.ir"
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{type}.ir not found for procedure {procedureName} in epoch {epoch}"
        )
    # Return as plain text
    content = file_path.read_text(encoding="utf-8")
    return Response(content, media_type="text/plain")

@app.get("/ir/{epoch}/{type}")
async def get_ir(epoch: str, type: str):
    file_path = selected_data_dir / epoch / f"{type}.ir"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"{type}.ir not found for epoch {epoch}")
    content = file_path.read_text(encoding="utf-8")
    return Response(content, media_type="text/plain")


@app.get("/cfg/{epoch}/{type}")
async def get_cfg(epoch: str, type: str):
    file_path = selected_data_dir / epoch / f"cfg_{type}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"cfg_{type}.json not found for epoch {epoch}")
    with open(file_path) as f:
        return json.load(f)


@app.get("/procedures/{epoch}")
async def get_procedures(epoch: str):
    """
    Return a list of procedure names as plain strings.
    Works for both /ir/{epoch}/procedures and /procedures/{epoch}.
    """
    epoch_dir = selected_data_dir / epoch
    procedures_file = epoch_dir / "procedures_with_lines.json"

    if not procedures_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"procedures_with_lines.json not found for epoch {epoch}"
        )

    with open(procedures_file, encoding="utf-8") as f:
        procedures_data = json.load(f)

    # Normalize everything to strings
    result: list[str] = []
    for proc in procedures_data:
        if isinstance(proc, str):
            result.append(proc)
        elif isinstance(proc, dict) and "name" in proc:
            result.append(proc["name"])

    return result
