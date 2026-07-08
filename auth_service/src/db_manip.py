from .database import session_scope
from .models import User
        
def create_user(forename: str, surname: str, email: str, password: str, role: str):
    with session_scope() as session:
        existing_user : User | None= session.query(User).filter(User.email == email).first()

        if existing_user is not None:
            return False

        user: User = User(
            forename=forename,
            surname=surname,
            email=email,
            password=password,
            role=role,
        )

        print(f"Creating user: {user.forename} {user.surname} ({user.email}) with role {user.role}", flush=True)

        session.add(user)
        return True
    
    return False

def credentials_valid(email: str, password: str) -> User | None:
    with session_scope() as session:
        existing_user : User | None= session.query(User).filter(User.email == email).first()

        if existing_user is not None and existing_user.password == password:
            print(f"User {existing_user.forename} {existing_user.surname} ({existing_user.email}) logged in successfully.", flush=True)
            return existing_user
        else:
            print(f"Failed login attempt for user: {email}", flush=True)
            return None
            
    return None

def delete_user(email: str) -> bool:
    """
    returns True on success, False if user is not found or an error happend
    """
    with session_scope() as session:
        existing_user : User | None= session.query(User).filter(User.email == email).first()

        if existing_user is None:
            return False
        
        print(f"Deleting user: {existing_user.forename} {existing_user.surname} ({existing_user.email}) with role {existing_user.role}", flush=True)
        session.delete(existing_user)
        return True

    return False
