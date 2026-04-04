from passlib.context import CryptContext

from backend.repository import UsuarioRepository

ALLOWED_ROLES = {"analista", "administrador", "desenvolvedor"}


class SecurityService:
    """Concentra a lógica de criptografia de senhas da aplicação."""

    def __init__(self) -> None:
        # bcrypt_sha256 evita a limitação prática de 72 bytes do bcrypt puro.
        # Mantemos bcrypt no contexto para reconhecer hashes legados, se existirem.
        self._pwd_context = CryptContext(
            schemes=["bcrypt_sha256", "bcrypt"],
            deprecated="auto",
        )

    def get_password_hash(self, password: str) -> str:
        """Gera o hash da senha para armazenamento seguro no banco."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Compara uma senha em texto puro com o hash armazenado."""
        return self._pwd_context.verify(plain_password, hashed_password)


class UsuarioService:
    def __init__(self) -> None:
        self.repo = UsuarioRepository()
        self.security = SecurityService()

    def listar_usuarios(self) -> list[dict]:
        # Futura lógica: Filtrar usuários ativos ou verificar permissões
        return self.repo.get_all()

    def cadastrar_usuario(self, username: str, password: str, role: str = "analista") -> int:
        """Cadastra um usuário gerando hash da senha antes de persistir."""

        clean_username = username.strip()
        if not clean_username:
            raise ValueError("O username não pode ser vazio")

        clean_password = password.strip()
        if not clean_password:
            raise ValueError("A senha não pode ser vazia")

        clean_role = role.strip().lower()
        if clean_role not in ALLOWED_ROLES:
            raise ValueError("Role inválida. Use: analista, administrador ou desenvolvedor")

        password_hash = self.security.get_password_hash(clean_password)
        return self.repo.create(clean_username, password_hash, clean_role)

    def alterar_nome_usuario(self, user_id: int, new_username: str) -> bool:
        """Altera o nome de usuário com validação básica de entrada."""
        clean_username = new_username.strip()
        if not clean_username:
            raise ValueError("O username não pode ser vazio")

        return self.repo.update_username(user_id, clean_username)

    def excluir_usuario(self, user_id: int) -> bool:
        """Exclui um usuário pelo ID no banco de dados."""
        return self.repo.delete(user_id)