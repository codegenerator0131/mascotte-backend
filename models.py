"""
User model for database operations
"""
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()


class User:
    """User model class"""
    
    def __init__(self, id=None, email=None, full_name=None, password_hash=None,
                 credits=100, created_at=None, updated_at=None):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.password_hash = password_hash
        self.credits = credits
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.generate_password_hash(password).decode('utf-8')
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify a password against its hash"""
        return bcrypt.check_password_hash(password_hash, password)
    
    def to_dict(self):
        """Convert user object to dictionary (exclude password)"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'credits': self.credits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create User object from dictionary"""
        return cls(
            id=data.get('id'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            password_hash=data.get('password_hash'),
            credits=data.get('credits', 100),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class UserRepository:
    """Database operations for User model"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def create_user(self, email, full_name, password):
        """Create a new user with initial 100 credits"""
        try:
            password_hash = User.hash_password(password)
            cursor = self.mysql.connection.cursor()
            
            query = """
                INSERT INTO users (email, full_name, password_hash, credits)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (email, full_name, password_hash, 100))
            self.mysql.connection.commit()
            
            user_id = cursor.lastrowid
            cursor.close()
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_user_by_email(self, email):
        """Get user by email"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return User.from_dict(result)
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return User.from_dict(result)
        return None
    
    def email_exists(self, email):
        """Check if email already exists"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        
        return result['count'] > 0
    
    def update_user(self, user_id, **kwargs):
        """Update user fields"""
        allowed_fields = ['email', 'full_name', 'password_hash']
        update_fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:
            return None
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute(query, tuple(values))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def add_credits(self, user_id, credits):
        """Add credits to user account"""
        try:
            cursor = self.mysql.connection.cursor()
            query = "UPDATE users SET credits = credits + %s WHERE id = %s"
            cursor.execute(query, (credits, user_id))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def deduct_credits(self, user_id, credits):
        """Deduct credits from user account"""
        try:
            cursor = self.mysql.connection.cursor()
            
            # Check if user has enough credits
            query = "SELECT credits FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                raise ValueError("User not found")
            
            if result['credits'] < credits:
                cursor.close()
                raise ValueError("Insufficient credits")
            
            # Deduct credits
            query = "UPDATE users SET credits = credits - %s WHERE id = %s"
            cursor.execute(query, (credits, user_id))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_user_credits(self, user_id):
        """Get user's current credit balance"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT credits FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return result['credits']
        return None