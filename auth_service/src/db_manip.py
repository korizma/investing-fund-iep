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

        session.add(user)
        return True
    
    return False

def credentials_valid(email: str, password: str) -> User | None:
    with session_scope() as session:
        existing_user : User | None= session.query(User).filter(User.email == email).first()

        if existing_user is not None and existing_user.password == password:
            return existing_user
        else:
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
        
        session.delete(existing_user)
        return True

    return False
