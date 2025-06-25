def get_public_key():
    with open('public.pem', 'r') as f:
        public_key = f.read()
    return public_key, 200, {'Content-Type': 'text/plain'}