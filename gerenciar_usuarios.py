"""Gerencia usuários do controle de acesso sem abrir o app.

Uso:
    python gerenciar_usuarios.py listar
    python gerenciar_usuarios.py adicionar <usuario> [--senha X] [--sem-visualizar] [--sem-importar] [--admin]
    python gerenciar_usuarios.py senha <usuario> --nova X
    python gerenciar_usuarios.py remover <usuario>
"""
import argparse
import getpass

from acesso import alterar_senha, carregar_usuarios, criar_usuario, remover_usuario, salvar_usuarios


def cmd_listar():
    usuarios = carregar_usuarios()
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return
    for nome, reg in sorted(usuarios.items()):
        perm = []
        if reg.get("admin"):
            perm.append("admin")
        if reg.get("pode_visualizar"):
            perm.append("visualizar")
        if reg.get("pode_importar"):
            perm.append("importar")
        print(f"- {nome}: {', '.join(perm) or 'sem permissões'}")


def cmd_adicionar(args):
    senha = args.senha or getpass.getpass("Senha: ")
    criar_usuario(
        args.usuario,
        senha,
        pode_visualizar=not args.sem_visualizar,
        pode_importar=not args.sem_importar,
        admin=args.admin,
    )
    print(f"Usuário '{args.usuario}' criado.")


def cmd_senha(args):
    if alterar_senha(args.usuario, args.nova):
        print(f"Senha de '{args.usuario}' alterada.")
    else:
        print(f"Usuário '{args.usuario}' não existe.")


def cmd_remover(args):
    remover_usuario(args.usuario)
    print(f"Usuário '{args.usuario}' removido.")


def main():
    p = argparse.ArgumentParser(prog="gerenciar_usuarios")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar", help="lista usuários e permissões")

    pa = sub.add_parser("adicionar", help="cadastra novo usuário")
    pa.add_argument("usuario")
    pa.add_argument("--senha", default=None)
    pa.add_argument("--sem-visualizar", action="store_true")
    pa.add_argument("--sem-importar", action="store_true")
    pa.add_argument("--admin", action="store_true")
    pa.set_defaults(func=cmd_adicionar)

    ps = sub.add_parser("senha", help="altera a senha de um usuário")
    ps.add_argument("usuario")
    ps.add_argument("--nova", required=True)
    ps.set_defaults(func=cmd_senha)

    pr = sub.add_parser("remover", help="remove um usuário")
    pr.add_argument("usuario")
    pr.set_defaults(func=cmd_remover)

    args = p.parse_args()
    if args.cmd == "listar":
        cmd_listar()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
