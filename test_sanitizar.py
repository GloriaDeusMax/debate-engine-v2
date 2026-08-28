import re

def _sanitizar_codigo(texto):
    padrao_segredos = (
        r'(?i)(api[_-]?key|token|secret|password|passwd|pwd|senha)'
        r'(\s*:\s*\w+\s*)?\s*=\s*["\'][^"\']+["\']'
    )
    texto = re.sub(padrao_segredos, r'\1 = "***MASKED***"', texto)
    texto = re.sub(r'sk-[a-zA-Z0-9]{20,}', '***MASKED_KEY***', texto)
    texto = re.sub(r'AIza[a-zA-Z0-9_-]{30,}', '***MASKED_KEY***', texto)
    return texto

casos = [
    'api_key = "sk-abcdefghijklmnopqrstuvwxyz"',
    'GEMINI_KEY = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"',
    'password: str = "minhasenha123"',
    'token = os.getenv("TOKEN")',
    'api_key: str = "outra_chave_aqui"',
]

for caso in casos:
    resultado = _sanitizar_codigo(caso)
    print(f"ORIGINAL: {caso}")
    print(f"RESULTADO: {resultado}")
    print("-" * 50)