from backend.repository import UsuarioRepository

class UsuarioService:
    def __init__(self):
        self.repo = UsuarioRepository()

    def listar_usuarios(self):
        # Futura lógica: Filtrar usuários ativos ou verificar permissões
        return self.repo.get_all()

    def cadastrar_usuario(self, username, password):
        # Futura lógica: Aqui você faria o hash real da senha ou validações de segurança
        fake_hash = f"hash_de_{password}" 
        return self.repo.create(username, fake_hash)