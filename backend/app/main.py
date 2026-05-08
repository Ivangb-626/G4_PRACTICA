import os
from app import create_app
import asyncio

app = create_app()

async def main():
    port = int(os.environ.get('FLASK_RUN_PORT', '8000'))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    asyncio.run(main())
