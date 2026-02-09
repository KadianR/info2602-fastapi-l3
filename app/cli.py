from typing_extensions import Annotated
import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command(help = "Initializes the database and creates a default user 'bob")
def initialize():
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command(help = "Get a user by their username")
def get_user(username:Annotated[str, typer.Argument(help = "The username of the user to retrieve")]):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command(help = "Retrieves and prints all users from the database")
def get_all_users():
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command(help = "Updates a user's email by the given username")
def change_email(username: Annotated[str, typer.Argument(help = "The username of the user whose email is to be updated")],                 
                 new_email: Annotated[str, typer.Argument(help = "The new email address to update for the user")]):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command(help = "Creates a new user with the given username, email, and password and adds details to the database")
def create_user(username: Annotated[str, typer.Argument(help = "The username of the new user to be created")], 
                email: Annotated[str, typer.Argument(help = "The email address of the new user to be created")], 
                password: Annotated[str, typer.Argument(help = "The password of the new user to be created")]):
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command(help = "Deletes a user by the given username from the database")
def delete_user(username: Annotated[str, typer.Argument(help = "The username of the user to be deleted from the database")]):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

#Create a cli command that allows you to find a user using a partial match of their email OR username.
@cli.command(help = "Finds and prints users whose username or email contains the given partial string")
def find_user(query: Annotated[str, typer.Argument(help = "The partial string to search for in usernames and emails")]):
    with get_session() as db:
        users = db.exec(select(User).where((User.username.contains(query)) | (User.email.contains(query)))).all()
        if not users:
            print(f'No users found matching "{query}"')
            return
        for user in users:
            print(user)

#Create cli command that allows you to list the first N users of the database to be used by a paginated table. The command should accept 2 arguments limit and offset and return the appropriate result. limit should be defaulted to 10 and offset should be defaulted to 0
@cli.command(help = "Lists users from the database by a paginated table using limit and offset values")
def list_users(limit: Annotated[int, typer.Option(help = "The number of users to list (default 10)")] = 10, 
               offset: Annotated[int, typer.Option(help = "The offset from the beginning of the list (default 0)")] = 0):
    with get_session() as db:
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        if not users:
            print("No users found")
            return
        for user in users:
            print(user)

#Modify all the existing cli commands and add help statements for all arguments and documentation for all the functions

if __name__ == "__main__":
    cli()