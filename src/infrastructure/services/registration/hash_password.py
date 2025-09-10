import bcrypt
import asyncio

async def hash_password(password) -> str:
    loop = asyncio.get_running_loop()
    salt = await loop.run_in_executor(None, bcrypt.gensalt)
    hashed_password = await loop.run_in_executor(None, bcrypt.hashpw, password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')
