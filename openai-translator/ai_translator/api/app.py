import os
import tempfile
from pathlib import Path
from typing import Dict

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..utils import ConfigLoader, LOG
from ..model import GLMModel, OpenAIModel
from ..translator import PDFTranslator

SUPPORTED_FORMATS = {"markdown", "pdf"}
MEDIA_TYPES = {
    "markdown": "text/markdown",
    "pdf": "application/pdf",
}

app = FastAPI(
    title="AI PDF Translator API",
    description="Synchronous API for translating PDF documents using configured AI models.",
    version="0.1.0",
)

_BASE_DIR = Path(__file__).resolve().parents[2]
_CONFIG_PATH = Path(os.getenv("AI_TRANSLATOR_CONFIG", _BASE_DIR / "config.yaml")).resolve()
_config_cache: Dict = {}

def get_config() -> Dict:
    global _config_cache
    if not _config_cache:
        loader = ConfigLoader(str(_CONFIG_PATH))
        _config_cache = loader.load_config()
        LOG.info(f"Configuration loaded from {_CONFIG_PATH}")
    return _config_cache

def build_model(model_type: str, config: Dict) -> object:
    if model_type == "GLMModel":
        glm_cfg = config.get("GLMModel", {})
        model_url = glm_cfg.get("model_url")
        timeout = glm_cfg.get("timeout", 300)
        if not model_url:
            raise HTTPException(status_code=500, detail="GLM model_url is not configured")
        return GLMModel(model_url=model_url, timeout=timeout)

    openai_cfg = config.get("OpenAIModel", {})
    model_name = openai_cfg.get("model")
    api_key = openai_cfg.get("api_key")
    if not model_name or not api_key:
        raise HTTPException(status_code=500, detail="OpenAI model configuration is incomplete")
    return OpenAIModel(model=model_name, api_key=api_key)

def cleanup_files(paths):
    for path in paths:
        try:
            if path and Path(path).exists():
                Path(path).unlink()
        except Exception as exc:
            LOG.warning(f"Failed to remove temporary file {path}: {exc}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/translate")
async def translate_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_language: str = Form(None),
    file_format: str = Form("markdown"),
    model_type: str = Form("OpenAIModel"),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if file.content_type not in {"application/pdf", "application/octet-stream"} and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    config = get_config()

    desired_format = (file_format or config.get("common", {}).get("file_format", "markdown")).lower()
    if desired_format not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {desired_format}")

    language = target_language or config.get("common", {}).get("target_language", "中文")
    translator = PDFTranslator(build_model(model_type, config))

    output_dir = Path(config.get("common", {}).get("output_dir", "./output")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        tmp.write(file_bytes)
        temp_path = Path(tmp.name)

    output_suffix = "md" if desired_format == "markdown" else "pdf"
    output_filename = f"{Path(file.filename).stem}_translated.{output_suffix}"
    output_path = output_dir / output_filename

    try:
        translator.translate_pdf(
            pdf_file_path=str(temp_path),
            file_format=desired_format,
            target_language=language,
            output_file_path=str(output_path),
        )
    except Exception as exc:
        cleanup_files([temp_path])
        LOG.error(f"Translation failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {exc}") from exc

    background_tasks.add_task(cleanup_files, [temp_path, output_path])

    media_type = MEDIA_TYPES[desired_format]
    headers = {}
    try:
        headers["X-Translation-Language"] = language.encode('ascii', 'ignore').decode('ascii') or 'unknown'
    except Exception:
        headers["X-Translation-Language"] = 'unknown'

    return FileResponse(
        path=str(output_path),
        media_type=media_type,
        filename=output_filename,
        background=background_tasks,
        headers=headers,
    )
