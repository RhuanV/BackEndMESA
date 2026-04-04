from backend.repository import UsuarioRepository

ALLOWED_ROLES = {"analista", "administrador", "desenvolvedor"}


class UsuarioService:
    def __init__(self) -> None:
        self.repo = UsuarioRepository()

    def listar_usuarios(self) -> list[dict]:
        # Futura lógica: Filtrar usuários ativos ou verificar permissões
        return self.repo.get_all()

    def cadastrar_usuario(self, username: str, password: str, role: str = "analista") -> int:
        # Futura lógica: Aqui você faria o hash real da senha ou validações de segurança
        fake_hash = f"hash_de_{password}"

        clean_role = role.strip().lower()
        if clean_role not in ALLOWED_ROLES:
            raise ValueError("Role inválida. Use: analista, administrador ou desenvolvedor")

        return self.repo.create(username, fake_hash, clean_role)

    def alterar_nome_usuario(self, user_id: int, new_username: str) -> bool:
        """Altera o nome de usuário com validação básica de entrada."""
        clean_username = new_username.strip()
        if not clean_username:
            raise ValueError("O username não pode ser vazio")

        return self.repo.update_username(user_id, clean_username)

    def excluir_usuario(self, user_id: int) -> bool:
        """Exclui um usuário pelo ID no banco de dados."""
        return self.repo.delete(user_id)