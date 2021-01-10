#! /usr/bin/env python3

import argparse
import csv

from database import DBHelper, Voter, User, get_password_hash


def import_users(filename: str):
    users = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            user = User()
            print(row)
            user.username = row["username"]
            user.hashed_password = get_password_hash(row["password"])
            users.append(user)
    with DBHelper() as session:
        print(f'Adding {len(users)} users…')
        session.add_all(users)
        session.commit()
        print(f'Done!')


def import_voters(filename: str):
    voters = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            voter = Voter()
            voter.number = row["Matrikelnummer"]
            voter.name = f'{row["Vorname"]} {row["Nachname"]}'
            voters.append(voter)
    with DBHelper() as session:
        print(f'Adding {len(voters)} voters…')
        session.add_all(voters)
        session.commit()
        print(f'Done!')


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
        parser.print_help()
