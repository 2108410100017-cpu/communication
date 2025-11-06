from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import socket
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# TCP server configuration
SERVER_IP = "192.168.1.201"
SERVER_PORT = 5000

MODEL_OPTIONS = ["Rodigo", "Douglous", "Andre"]
BRAND_OPTIONS = ["LP", "VH"]


def build_folder_structure(files: list[UploadFile]):
    """Build nested folder structure JSON for uploaded folder."""
    folder_data = {}
    for file in files:
        rel_path = file.filename.replace("\\", "/")
        parts = rel_path.split("/")
        if len(parts) == 1:
            folder_data.setdefault("", []).append(parts[-1])
        else:
            subfolder = "/".join(parts[:-1])
            folder_data.setdefault(subfolder, []).append(parts[-1])

    first_path = files[0].filename.replace("\\", "/")
    root_folder = first_path.split("/")[0] if "/" in first_path else "UploadedFolder"
    return {"folder_name": root_folder, "files": folder_data}


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "models": MODEL_OPTIONS,
        "brands": BRAND_OPTIONS
    })


@app.post("/send", response_class=HTMLResponse)
async def send_form(
    request: Request,
    model: str = Form(...),
    brand: str = Form(...),
    length: str = Form(...),
    width: str = Form(...),
    height: str = Form(...),
    folder: list[UploadFile] = File(None)
):
    # Validate and build product JSON
    try:
        product_data = {
            "Model": model,
            "Brand": brand,
            "Size": {
                "Length": float(length),
                "Width": float(width),
                "Height": float(height)
            }
        }
    except ValueError:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "models": MODEL_OPTIONS,
            "brands": BRAND_OPTIONS,
            "error": "Length, Width, and Height must be numbers!"
        })

    # Add folder info if present
    if folder:
        folder_info = build_folder_structure(folder)
        product_data["FolderData"] = folder_info
    else:
        folder_info = None

    # --- Smooth TCP send & receive ---
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_IP, SERVER_PORT))

            # Send single-line JSON to avoid partial read errors
            json_message = json.dumps(product_data) + "\n"
            client_socket.sendall(json_message.encode("utf-8"))

            # Receive response until newline
            response_buffer = ""
            while True:
                chunk = client_socket.recv(4096).decode("utf-8")
                if not chunk:
                    break
                response_buffer += chunk
                if "\n" in response_buffer:
                    break

        # Try parsing server response
        response_data = response_buffer.strip()
        try:
            parsed_response = json.loads(response_data)
            response_message = json.dumps(parsed_response, indent=4)
        except json.JSONDecodeError:
            response_message = response_data

    except Exception as e:
        response_message = f"❌ Failed to send data: {e}"

    # Pretty-print what was sent
    sent_pretty = json.dumps(product_data, indent=4)

    return templates.TemplateResponse("form.html", {
        "request": request,
        "models": MODEL_OPTIONS,
        "brands": BRAND_OPTIONS,
        "success": response_message,
        "sent_data": sent_pretty
    })
