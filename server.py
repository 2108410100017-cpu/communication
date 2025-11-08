import socket
import threading
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI(title="Product Receiver via TCP Socket")
templates = Jinja2Templates(directory="templates")

received_products = []

HOST = "0.0.0.0"
PORT = 5000


def recv_until_newline(conn):
    """Read incoming data until a newline '\n' is found."""
    buffer = ""
    while True:
        chunk = conn.recv(4096).decode("utf-8")
        if not chunk:
            break
        buffer += chunk
        if "\n" in buffer:
            break
    return buffer.strip()


def handle_client(conn, addr):
    """Handle an incoming TCP client connection."""
    try:
        data = recv_until_newline(conn)
        if not data:
            print(f"⚠️ No data received from {addr}")
            conn.close()
            return

        try:
            product = json.loads(data)
            received_products.append(product)

            # Create a unified structured response
            log_info = {
                "client": str(addr),
                "product": product,
                "message": "✅ Product received successfully!"
            }

            # Log to console neatly
            print(json.dumps(log_info, indent=4))

            # Send back acknowledgment JSON (with newline terminator)
            conn.sendall((json.dumps(log_info) + "\n").encode("utf-8"))

        except json.JSONDecodeError:
            err = {"error": "Invalid JSON received!", "client": str(addr)}
            print(json.dumps(err, indent=4))
            conn.sendall((json.dumps(err) + "\n").encode("utf-8"))

    except Exception as e:
        print(f"❌ Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"🔌 Connection closed for {addr}")


def start_tcp_server():
    """Start TCP server in a background thread."""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"🚀 TCP server listening on {HOST}:{PORT}")
    except Exception as e:
        print(f"❌ Failed to start TCP server: {e}")
        return

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# Start TCP server in background thread
threading.Thread(target=start_tcp_server, daemon=True).start()

@app.get("/")
async def home():
    """Redirect to /products"""
    return RedirectResponse(url="/products")

@app.get("/products", response_class=HTMLResponse)
async def view_products(request: Request):
    """HTML view to see all received products."""
    print(f"🔍 Rendering UI with {len(received_products)} products")
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": received_products}
    )



@app.get("/products_json")
async def products_json():
    """JSON view for received products."""
    return JSONResponse(content=received_products)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=7000, reload=True)
