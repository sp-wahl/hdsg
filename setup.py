import argparse
import csv

from database import DBHelper, Voter, User, get_password_hash, verify_password


def import_users(filename: str):
    users = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i % 100:
                print(f"{i}/{len(reader)}", end="")
            user = User()
            print(row)
            user.username = row["username"]
            user.hashed_password = get_password_hash(row["password"])
            users.append(user)
    with DBHelper() as session:
        session.add_all(users)
        session.commit()


def import_voters(filename: str):
    voters = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for i, row in enumerate(reader):
            if i % 100:
                print(f"{i}/{len(reader)}", end="")
            voter = Voter()
            voter.number = row["Matrikelnummer"]
            voter.name = f'{row["Nachname"]}, {row["Vorname"]}'
            voters.append(voter)
    with DBHelper() as session:
        session.add_all(voters)
        session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This skript will help you setup the hdsg tool database. There are two functionalities: Generating users and importing voter-tsv"
    )

    subparsers = parser.add_subparsers(dest="command")

    import_users_parser = subparsers.add_parser("import_users")
    import_users_parser.add_argument("filename", type=str)

    import_voter_parser = subparsers.add_parser("import_voter")
    import_voter_parser.add_argument("filename", type=str)

    args = parser.parse_args()

    if args.command == "import_users":
        import_users(args.filename)
    elif args.command == "import_voter":
        import_voters(args.filename)
    else:
        print("not a valid command")