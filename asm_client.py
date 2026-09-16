# client.py

# https://developer.apple.com/documentation/apple-school-and-business-manager-api/implementing-oauth-for-the-apple-school-manager-and-apple-business-api

import datetime
from dotenv import load_dotenv
import jwt
import os
import uuid

load_dotenv()
private_key_file = "ASM.pem"
client_id = os.environ["ASM_CLIENT_ID"]
key_id = os.environ["ASM_KEY_ID"]
audience = "https://account.apple.com/auth/oauth2/v2/token"
alg = "ES256"

issued_at_timestamp = int(datetime.datetime.now(datetime.UTC).timestamp())
expiration_timestamp = issued_at_timestamp + 86400 * 180

headers = {
  "alg": alg,
  "kid": key_id,
}

payload = {
  "aud": audience,
  "exp": expiration_timestamp,
  "iat": issued_at_timestamp,
  "sub": client_id,
  "jti": str(uuid.uuid4()),
  "iss": client_id,
}

with open(private_key_file, "rb") as file:
  private_key_bytes = file.read()

client_assertion = jwt.encode(
  payload,
  private_key_bytes,
  headers=headers,
)

with open("asm_client_assertion.txt", "wt") as output:
  output.write(client_assertion)
