from api.index import app
import uvicorn
import os

if __name__ == "__main__":
    # Standard entrypoint for platforms like Railpack, Railway, or Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
