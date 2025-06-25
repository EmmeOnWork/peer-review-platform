blacklisted_tokens = set()

def is_token_blacklisted(token):
    return token in blacklisted_tokens