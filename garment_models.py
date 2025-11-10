"""
Garment models for managing garment items in the system
"""
from datetime import datetime


class Garment:
    """Garment model class"""
    
    def __init__(self, id=None, name=None, brand=None, price=None, rating=None,
                 image_url=None, description=None, category=None, style=None,
                 available=True, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.brand = brand
        self.price = price
        self.rating = rating
        self.image_url = image_url
        self.description = description
        self.category = category
        self.style = style
        self.available = available
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert garment object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'price': float(self.price) if self.price else None,
            'rating': float(self.rating) if self.rating else None,
            'imageUrl': self.image_url,
            'description': self.description,
            'category': self.category,
            'style': self.style,
            'available': self.available,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Garment object from dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            brand=data.get('brand'),
            price=data.get('price'),
            rating=data.get('rating'),
            image_url=data.get('image_url'),
            description=data.get('description'),
            category=data.get('category'),
            style=data.get('style'),
            available=data.get('available', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class GarmentRepository:
    """Database operations for Garment model"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def create_garment(self, garment_data):
        """Create a new garment"""
        try:
            cursor = self.mysql.connection.cursor()
            
            query = """
                INSERT INTO garments (
                    name, brand, price, rating, image_url, description,
                    category, style, available
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                garment_data.get('name'),
                garment_data.get('brand'),
                garment_data.get('price'),
                garment_data.get('rating', 0),
                garment_data.get('image_url'),
                garment_data.get('description'),
                garment_data.get('category'),
                garment_data.get('style'),
                garment_data.get('available', True)
            ))
            
            self.mysql.connection.commit()
            garment_id = cursor.lastrowid
            cursor.close()
            
            return self.get_garment_by_id(garment_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_garment_by_id(self, garment_id):
        """Get garment by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM garments WHERE id = %s"
        cursor.execute(query, (garment_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return Garment.from_dict(result)
        return None
    
    def get_all_garments(self, limit=50, offset=0, filters=None):
        """Get all garments with optional filters"""
        cursor = self.mysql.connection.cursor()
        
        query = "SELECT * FROM garments WHERE available = TRUE"
        params = []
        
        if filters:
            if filters.get('brand'):
                query += " AND brand = %s"
                params.append(filters['brand'])
            
            if filters.get('category'):
                query += " AND category = %s"
                params.append(filters['category'])
            
            if filters.get('style'):
                query += " AND style = %s"
                params.append(filters['style'])
            
            if filters.get('min_price'):
                query += " AND price >= %s"
                params.append(filters['min_price'])
            
            if filters.get('max_price'):
                query += " AND price <= %s"
                params.append(filters['max_price'])
            
            if filters.get('search'):
                query += " AND (name LIKE %s OR brand LIKE %s OR description LIKE %s)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        
        return [Garment.from_dict(row) for row in results]
    
    def update_garment(self, garment_id, garment_data):
        """Update garment"""
        allowed_fields = ['name', 'brand', 'price', 'rating', 'image_url',
                         'description', 'category', 'style', 'available']
        
        update_fields = []
        values = []
        
        for field, value in garment_data.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:
            return None
        
        values.append(garment_id)
        query = f"UPDATE garments SET {', '.join(update_fields)} WHERE id = %s"
        
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute(query, tuple(values))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_garment_by_id(garment_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def delete_garment(self, garment_id):
        """Soft delete garment (mark as unavailable)"""
        try:
            cursor = self.mysql.connection.cursor()
            query = "UPDATE garments SET available = FALSE WHERE id = %s"
            cursor.execute(query, (garment_id,))
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def search_garments(self, search_query, limit=20):
        """Search garments by name, brand, or description"""
        cursor = self.mysql.connection.cursor()
        
        query = """
            SELECT * FROM garments 
            WHERE available = TRUE 
            AND (name LIKE %s OR brand LIKE %s OR description LIKE %s)
            ORDER BY rating DESC
            LIMIT %s
        """
        
        search_term = f"%{search_query}%"
        cursor.execute(query, (search_term, search_term, search_term, limit))
        results = cursor.fetchall()
        cursor.close()
        
        return [Garment.from_dict(row) for row in results]
    
    def get_garments_by_brand(self, brand, limit=20):
        """Get garments by brand"""
        cursor = self.mysql.connection.cursor()
        
        query = """
            SELECT * FROM garments 
            WHERE available = TRUE AND brand = %s
            ORDER BY rating DESC
            LIMIT %s
        """
        
        cursor.execute(query, (brand, limit))
        results = cursor.fetchall()
        cursor.close()
        
        return [Garment.from_dict(row) for row in results]
    
    def get_garments_by_category(self, category, limit=20):
        """Get garments by category"""
        cursor = self.mysql.connection.cursor()
        
        query = """
            SELECT * FROM garments 
            WHERE available = TRUE AND category = %s
            ORDER BY rating DESC
            LIMIT %s
        """
        
        cursor.execute(query, (category, limit))
        results = cursor.fetchall()
        cursor.close()
        
        return [Garment.from_dict(row) for row in results]
    
    def get_top_rated_garments(self, limit=10):
        """Get top rated garments"""
        cursor = self.mysql.connection.cursor()
        
        query = """
            SELECT * FROM garments 
            WHERE available = TRUE 
            ORDER BY rating DESC, created_at DESC
            LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        cursor.close()
        
        return [Garment.from_dict(row) for row in results]