from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi import HTTPException

import os
import uuid


app = FastAPI()


# ============================================================
# CONFIGURATION
# ============================================================

PORT = 8000

UPLOAD_FOLDER = "uploads"

MAX_FILE_SIZE = 50 * 1024 * 1024       # 50 MB

CHUNK_SIZE = 64 * 1024                 # 64 KB


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# CONNECTED CLIENTS
# ============================================================

clients = {}


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
async def home():

    return FileResponse(
        "index.html"
    )


# ============================================================
# DOWNLOAD FILE
# ============================================================

@app.get("/download/{file_id}")
async def download_file(file_id: str):

    # Find the file by ID

    matching_file = None

    for filename in os.listdir(
        UPLOAD_FOLDER
    ):

        if filename.startswith(
            file_id + "_"
        ):

            matching_file = filename

            break


    if matching_file is None:

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )


    filepath = os.path.join(
        UPLOAD_FOLDER,
        matching_file
    )


    # Original filename after ID_
    original_filename = matching_file[
        len(file_id) + 1:
    ]


    return FileResponse(
        filepath,
        filename=original_filename
    )


# ============================================================
# BROADCAST
# ============================================================

async def broadcast(data):

    disconnected = []


    for client_id, websocket in list(
        clients.items()
    ):

        try:

            await websocket.send_json(
                data
            )

        except Exception:

            disconnected.append(
                client_id
            )


    for client_id in disconnected:

        clients.pop(
            client_id,
            None
        )


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()


    # --------------------------------------------------------
    # CREATE CLIENT
    # --------------------------------------------------------

    client_id = str(
        uuid.uuid4()
    )


    username =  username = f"Client-{len(clients) + 1}"  #for multiple client
        # ( "User-" +
        # client_id[:4]
        #)
        # OR
        # username = "Client"  this is for single client
       


    clients[client_id] = websocket


    print(
        f"{username} connected"
    )


    await websocket.send_json({

        "type": "system",

        "message":
            f"You are {username}"

    })


    await broadcast({

        "type": "system",

        "message":
            f"{username} joined the chat"

    })


    # --------------------------------------------------------
    # FILE STATE FOR THIS CLIENT
    # --------------------------------------------------------

    receiving_file = False

    current_file = None

    current_file_id = None

    current_filename = None

    current_size = 0

    received_size = 0


    try:

        while True:

            data = await websocket.receive()


            # =================================================
            # TEXT MESSAGE
            # =================================================

            if "text" in data:

                import json

                message = json.loads(
                    data["text"]
                )


                message_type = message.get(
                    "type"
                )


                # ---------------------------------------------
                # CHAT
                # ---------------------------------------------

                if message_type == "chat":

                    text = message.get(
                        "message",
                        ""
                    )


                    if text.strip():

                        print(
                            f"{username}: {text}"
                        )


                        await broadcast({

                            "type": "chat",

                            "username":
                                username,

                            "message":
                                text

                        })


                # ---------------------------------------------
                # FILE START
                # ---------------------------------------------

                elif message_type == "file_start":


                    filename = message.get(
                        "filename",
                        "unknown"
                    )


                    filesize = int(
                        message.get(
                            "size",
                            0
                        )
                    )


                    # Check file size

                    if filesize > MAX_FILE_SIZE:

                        await websocket.send_json({

                            "type": "file_error",

                            "message":
                                "File is larger than 50 MB"

                        })

                        continue


                    if filesize <= 0:

                        await websocket.send_json({

                            "type": "file_error",

                            "message":
                                "Invalid file size"

                        })

                        continue


                    # Remove path information

                    filename = os.path.basename(
                        filename
                    )


                    # Generate unique ID

                    file_id = str(
                        uuid.uuid4()
                    )


                    # Save as:
                    #
                    # UUID_originalfilename

                    stored_filename = (
                        file_id +
                        "_" +
                        filename
                    )


                    filepath = os.path.join(
                        UPLOAD_FOLDER,
                        stored_filename
                    )


                    current_file = open(
                        filepath,
                        "wb"
                    )


                    current_file_id = file_id

                    current_filename = filename

                    current_size = filesize

                    received_size = 0

                    receiving_file = True


                    print()

                    print(
                        f"Receiving file:"
                        f" {filename}"
                    )

                    print(
                        f"Expected:"
                        f" {filesize} bytes"
                    )


                    await websocket.send_json({

                        "type":
                            "file_status",

                        "message":
                            "File transfer started"

                    })


                # ---------------------------------------------
                # FILE END
                # ---------------------------------------------

                elif message_type == "file_end":


                    if not receiving_file:

                        continue


                    # Close file

                    current_file.close()


                    receiving_file = False


                    print(
                        f"File received:"
                        f" {current_filename}"
                    )


                    print(
                        f"Received:"
                        f" {received_size}"
                        f"/{current_size}"
                    )


                    # Make sure entire file arrived

                    if received_size != current_size:

                        try:

                            os.remove(
                                os.path.join(
                                    UPLOAD_FOLDER,
                                    current_file_id +
                                    "_" +
                                    current_filename
                                )
                            )

                        except Exception:

                            pass


                        await websocket.send_json({

                            "type":
                                "file_error",

                            "message":
                                "File transfer incomplete"

                        })


                        continue


                    # Tell everyone about file

                    await broadcast({

                        "type": "file",

                        "username":
                            username,

                        "filename":
                            current_filename,

                        "file_id":
                            current_file_id

                    })


                    # Reset state

                    current_file = None

                    current_file_id = None

                    current_filename = None

                    current_size = 0

                    received_size = 0


            # =================================================
            # BINARY DATA
            # =================================================

            elif "bytes" in data:

                binary_data = data["bytes"]


                if not receiving_file:

                    print(
                        "Received binary data "
                        "without file_start"
                    )

                    continue


                # Prevent overflow

                if (
                    received_size +
                    len(binary_data)
                    >
                    current_size
                ):

                    print(
                        "File size overflow"
                    )

                    current_file.close()

                    receiving_file = False

                    continue


                # Write binary chunk

                current_file.write(
                    binary_data
                )


                received_size += len(
                    binary_data
                )


                # Send progress to sender

                await websocket.send_json({

                    "type":
                        "file_progress",

                    "received":
                        received_size,

                    "total":
                        current_size

                })


    except WebSocketDisconnect:

        print(
            f"{username} disconnected"
        )


    finally:

        # Close incomplete file

        if current_file is not None:

            try:

                current_file.close()

            except Exception:

                pass


        # Remove client

        clients.pop(
            client_id,
            None
        )


        await broadcast({

            "type": "system",

            "message":
                f"{username} left the chat"

        })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn


    print()

    print("=" * 55)

    print(
        "       LAN WEBSOCKET CHAT SERVER"
    )

    print("=" * 55)

    print()

    print(
        "Local:"
    )

    print(
        "http://localhost:8000"
    )

    print()

    print(
        "LAN:"
    )

    print(
        "http://YOUR_IPV4:8000"
    )

    print()

    print(
        "Maximum file size: 50 MB"
    )

    print()

    print("=" * 55)

    print()


    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )