"""
Credit Transaction model for database operations
"""
import json


class CreditTransaction:
    """Credit Transaction model class"""
    
    def __init__(self, id=None, user_id=None, transaction_type=None, amount=None,
                 credits=None, description=None, status='completed', reference_id=None,
                 metadata=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.credits = credits
        self.description = description
        self.status = status
        self.reference_id = reference_id
        self.metadata = metadata
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert transaction object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.transaction_type,
            'amount': float(self.amount) if self.amount else 0.0,
            'credits': self.credits,
            'description': self.description,
            'status': self.status,
            'reference_id': self.reference_id,
            'metadata': json.loads(self.metadata) if isinstance(self.metadata, str) else self.metadata,
            'date': self.created_at.isoformat() if self.created_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create CreditTransaction object from dictionary"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            transaction_type=data.get('transaction_type'),
            amount=data.get('amount'),
            credits=data.get('credits'),
            description=data.get('description'),
            status=data.get('status', 'completed'),
            reference_id=data.get('reference_id'),
            metadata=data.get('metadata'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class CreditTransactionRepository:
    """Database operations for Credit Transaction model"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def create_transaction(self, user_id, transaction_type, credits, description,
                          amount=0.0, status='completed', reference_id=None, metadata=None):
        """Create a new credit transaction"""
        try:
            cursor = self.mysql.connection.cursor()
            
            # Convert metadata to JSON string if it's a dict
            metadata_json = json.dumps(metadata) if metadata else None
            
            query = """
                INSERT INTO credit_transactions 
                (user_id, transaction_type, amount, credits, description, status, reference_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                user_id, transaction_type, amount, credits, 
                description, status, reference_id, metadata_json
            ))
            self.mysql.connection.commit()
            
            transaction_id = cursor.lastrowid
            cursor.close()
            
            return self.get_transaction_by_id(transaction_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_transaction_by_id(self, transaction_id):
        """Get transaction by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM credit_transactions WHERE id = %s"
        cursor.execute(query, (transaction_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return CreditTransaction.from_dict(result)
        return None
    
    def get_user_transactions(self, user_id, limit=50, offset=0):
        """Get all transactions for a user with pagination"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT * FROM credit_transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, limit, offset))
        results = cursor.fetchall()
        cursor.close()
        
        return [CreditTransaction.from_dict(row) for row in results]
    
    def get_user_transactions_by_type(self, user_id, transaction_type, limit=50):
        """Get transactions by type for a user"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT * FROM credit_transactions 
            WHERE user_id = %s AND transaction_type = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        cursor.execute(query, (user_id, transaction_type, limit))
        results = cursor.fetchall()
        cursor.close()
        
        return [CreditTransaction.from_dict(row) for row in results]
    
    def get_transaction_stats(self, user_id):
        """Get transaction statistics for a user"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT 
                transaction_type,
                COUNT(*) as count,
                SUM(credits) as total_credits,
                SUM(amount) as total_amount
            FROM credit_transactions 
            WHERE user_id = %s AND status = 'completed'
            GROUP BY transaction_type
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        
        stats = {}
        for row in results:
            stats[row['transaction_type']] = {
                'count': row['count'],
                'total_credits': row['total_credits'],
                'total_amount': float(row['total_amount']) if row['total_amount'] else 0.0
            }
        
        return stats


class CreditPlan:
    """Credit Plan model class"""
    
    def __init__(self, id=None, credits=None, price=None, is_popular=False,
                 is_active=True, created_at=None, updated_at=None):
        self.id = id
        self.credits = credits
        self.price = price
        self.is_popular = is_popular
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert plan object to dictionary"""
        return {
            'id': str(self.id),
            'credits': self.credits,
            'price': float(self.price),
            'popular': self.is_popular,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create CreditPlan object from dictionary"""
        return cls(
            id=data.get('id'),
            credits=data.get('credits'),
            price=data.get('price'),
            is_popular=data.get('is_popular', False),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class CreditPlanRepository:
    """Database operations for Credit Plan model"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def get_all_plans(self):
        """Get all active credit plans"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT * FROM credit_plans 
            WHERE is_active = TRUE 
            ORDER BY credits ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        
        return [CreditPlan.from_dict(row) for row in results]
    
    def get_plan_by_id(self, plan_id):
        """Get plan by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM credit_plans WHERE id = %s AND is_active = TRUE"
        cursor.execute(query, (plan_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return CreditPlan.from_dict(result)
        return None