"""
Avatar models for database operations
"""
from datetime import datetime


class Avatar:
    """Avatar model class"""
    
    def __init__(self, id=None, user_id=None, full_name=None, bio=None, age=None,
                 height=None, height_unit=None, weight=None, weight_unit=None,
                 avatar_type=None, generic_avatar_style=None, biometric_verified=False,
                 measurement_mode=None, auto_estimated=False, share_with_world=False,
                 create_assistant=False, create_greeting_cards=False, 
                 public_profile=False, allow_connections=True,
                 selected_greeting_template=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.full_name = full_name
        self.bio = bio
        self.age = age
        self.height = height
        self.height_unit = height_unit
        self.weight = weight
        self.weight_unit = weight_unit
        self.avatar_type = avatar_type
        self.generic_avatar_style = generic_avatar_style
        self.biometric_verified = biometric_verified
        self.measurement_mode = measurement_mode
        self.auto_estimated = auto_estimated
        self.share_with_world = share_with_world
        self.create_assistant = create_assistant
        self.create_greeting_cards = create_greeting_cards
        self.public_profile = public_profile
        self.allow_connections = allow_connections
        self.selected_greeting_template = selected_greeting_template
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert avatar object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'bio': self.bio,
            'age': self.age,
            'height': self.height,
            'height_unit': self.height_unit,
            'weight': self.weight,
            'weight_unit': self.weight_unit,
            'avatar_type': self.avatar_type,
            'generic_avatar_style': self.generic_avatar_style,
            'biometric_verified': self.biometric_verified,
            'measurement_mode': self.measurement_mode,
            'auto_estimated': self.auto_estimated,
            'share_with_world': self.share_with_world,
            'create_assistant': self.create_assistant,
            'create_greeting_cards': self.create_greeting_cards,
            'public_profile': self.public_profile,
            'allow_connections': self.allow_connections,
            'selected_greeting_template': self.selected_greeting_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Avatar object from dictionary"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            full_name=data.get('full_name'),
            bio=data.get('bio'),
            age=data.get('age'),
            height=data.get('height'),
            height_unit=data.get('height_unit'),
            weight=data.get('weight'),
            weight_unit=data.get('weight_unit'),
            avatar_type=data.get('avatar_type'),
            generic_avatar_style=data.get('generic_avatar_style'),
            biometric_verified=data.get('biometric_verified', False),
            measurement_mode=data.get('measurement_mode'),
            auto_estimated=data.get('auto_estimated', False),
            share_with_world=data.get('share_with_world', False),
            create_assistant=data.get('create_assistant', False),
            create_greeting_cards=data.get('create_greeting_cards', False),
            public_profile=data.get('public_profile', False),
            allow_connections=data.get('allow_connections', True),
            selected_greeting_template=data.get('selected_greeting_template'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class BodyMeasurement:
    """Body measurements model class"""
    
    def __init__(self, id=None, avatar_id=None, chest=None, waist=None, hips=None,
                 shoulder_width=None, inseam=None, arm_length=None, neck_size=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.avatar_id = avatar_id
        self.chest = chest
        self.waist = waist
        self.hips = hips
        self.shoulder_width = shoulder_width
        self.inseam = inseam
        self.arm_length = arm_length
        self.neck_size = neck_size
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert body measurement object to dictionary"""
        return {
            'id': self.id,
            'avatar_id': self.avatar_id,
            'chest': self.chest,
            'waist': self.waist,
            'hips': self.hips,
            'shoulder_width': self.shoulder_width,
            'inseam': self.inseam,
            'arm_length': self.arm_length,
            'neck_size': self.neck_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create BodyMeasurement object from dictionary"""
        return cls(
            id=data.get('id'),
            avatar_id=data.get('avatar_id'),
            chest=data.get('chest'),
            waist=data.get('waist'),
            hips=data.get('hips'),
            shoulder_width=data.get('shoulder_width'),
            inseam=data.get('inseam'),
            arm_length=data.get('arm_length'),
            neck_size=data.get('neck_size'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class AvatarGarment:
    """Avatar garments model class"""
    
    def __init__(self, id=None, avatar_id=None, garment_id=None, 
                 created_at=None):
        self.id = id
        self.avatar_id = avatar_id
        self.garment_id = garment_id
        self.created_at = created_at
    
    def to_dict(self):
        """Convert avatar garment object to dictionary"""
        return {
            'id': self.id,
            'avatar_id': self.avatar_id,
            'garment_id': self.garment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create AvatarGarment object from dictionary"""
        return cls(
            id=data.get('id'),
            avatar_id=data.get('avatar_id'),
            garment_id=data.get('garment_id'),
            created_at=data.get('created_at')
        )


class AvatarRepository:
    """Database operations for Avatar model"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def create_avatar(self, user_id, avatar_data):
        """Create a new avatar profile"""
        try:
            cursor = self.mysql.connection.cursor()
            
            query = """
                INSERT INTO avatars (
                    user_id, full_name, bio, age, height, height_unit, weight, weight_unit,
                    avatar_type, generic_avatar_style, biometric_verified, measurement_mode,
                    auto_estimated, share_with_world, create_assistant, create_greeting_cards,
                    public_profile, allow_connections, selected_greeting_template
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                user_id,
                avatar_data.get('full_name'),
                avatar_data.get('bio'),
                avatar_data.get('age'),
                avatar_data.get('height'),
                avatar_data.get('height_unit'),
                avatar_data.get('weight'),
                avatar_data.get('weight_unit'),
                avatar_data.get('avatar_type'),
                avatar_data.get('generic_avatar_style'),
                avatar_data.get('biometric_verified', False),
                avatar_data.get('measurement_mode'),
                avatar_data.get('auto_estimated', False),
                avatar_data.get('share_with_world', False),
                avatar_data.get('create_assistant', False),
                avatar_data.get('create_greeting_cards', False),
                avatar_data.get('public_profile', False),
                avatar_data.get('allow_connections', True),
                avatar_data.get('selected_greeting_template')
            ))
            
            self.mysql.connection.commit()
            avatar_id = cursor.lastrowid
            cursor.close()
            
            return self.get_avatar_by_id(avatar_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_avatar_by_id(self, avatar_id):
        """Get avatar by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM avatars WHERE id = %s"
        cursor.execute(query, (avatar_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return Avatar.from_dict(result)
        return None
    
    def get_avatar_by_user_id(self, user_id):
        """Get avatar by user ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM avatars WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return Avatar.from_dict(result)
        return None
    
    def update_avatar(self, avatar_id, avatar_data):
        """Update avatar profile"""
        allowed_fields = [
            'full_name', 'bio', 'age', 'height', 'height_unit', 'weight', 'weight_unit',
            'avatar_type', 'generic_avatar_style', 'biometric_verified', 'measurement_mode',
            'auto_estimated', 'share_with_world', 'create_assistant', 'create_greeting_cards',
            'public_profile', 'allow_connections', 'selected_greeting_template'
        ]
        
        update_fields = []
        values = []
        
        for field, value in avatar_data.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:
            return None
        
        values.append(avatar_id)
        query = f"UPDATE avatars SET {', '.join(update_fields)} WHERE id = %s"
        
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute(query, tuple(values))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_avatar_by_id(avatar_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def delete_avatar(self, avatar_id):
        """Delete avatar"""
        try:
            cursor = self.mysql.connection.cursor()
            query = "DELETE FROM avatars WHERE id = %s"
            cursor.execute(query, (avatar_id,))
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_public_avatars(self, limit=20, offset=0):
        """Get public avatars"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT * FROM avatars 
            WHERE public_profile = TRUE 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        cursor.close()
        
        return [Avatar.from_dict(row) for row in results]


class BodyMeasurementRepository:
    """Database operations for Body Measurements"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def create_measurements(self, avatar_id, measurements_data):
        """Create body measurements"""
        try:
            cursor = self.mysql.connection.cursor()
            
            query = """
                INSERT INTO body_measurements (
                    avatar_id, chest, waist, hips, shoulder_width, 
                    inseam, arm_length, neck_size
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                avatar_id,
                measurements_data.get('chest'),
                measurements_data.get('waist'),
                measurements_data.get('hips'),
                measurements_data.get('shoulder_width'),
                measurements_data.get('inseam'),
                measurements_data.get('arm_length'),
                measurements_data.get('neck_size')
            ))
            
            self.mysql.connection.commit()
            measurement_id = cursor.lastrowid
            cursor.close()
            
            return self.get_measurements_by_id(measurement_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_measurements_by_id(self, measurement_id):
        """Get measurements by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM body_measurements WHERE id = %s"
        cursor.execute(query, (measurement_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return BodyMeasurement.from_dict(result)
        return None
    
    def get_measurements_by_avatar_id(self, avatar_id):
        """Get measurements by avatar ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM body_measurements WHERE avatar_id = %s"
        cursor.execute(query, (avatar_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return BodyMeasurement.from_dict(result)
        return None
    
    def update_measurements(self, avatar_id, measurements_data):
        """Update body measurements"""
        allowed_fields = ['chest', 'waist', 'hips', 'shoulder_width', 
                         'inseam', 'arm_length', 'neck_size']
        
        update_fields = []
        values = []
        
        for field, value in measurements_data.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:
            return None
        
        values.append(avatar_id)
        query = f"UPDATE body_measurements SET {', '.join(update_fields)} WHERE avatar_id = %s"
        
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute(query, tuple(values))
            self.mysql.connection.commit()
            cursor.close()
            
            return self.get_measurements_by_avatar_id(avatar_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e


class AvatarGarmentRepository:
    """Database operations for Avatar Garments"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def add_garment(self, avatar_id, garment_id):
        """Add garment to avatar wardrobe"""
        try:
            cursor = self.mysql.connection.cursor()
            
            # Check if already exists
            check_query = """
                SELECT id FROM avatar_garments 
                WHERE avatar_id = %s AND garment_id = %s
            """
            cursor.execute(check_query, (avatar_id, garment_id))
            existing = cursor.fetchone()
            
            if existing:
                cursor.close()
                return AvatarGarment.from_dict(existing)
            
            query = """
                INSERT INTO avatar_garments (avatar_id, garment_id)
                VALUES (%s, %s)
            """
            cursor.execute(query, (avatar_id, garment_id))
            self.mysql.connection.commit()
            
            garment_link_id = cursor.lastrowid
            cursor.close()
            
            return self.get_garment_link_by_id(garment_link_id)
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def remove_garment(self, avatar_id, garment_id):
        """Remove garment from avatar wardrobe"""
        try:
            cursor = self.mysql.connection.cursor()
            query = "DELETE FROM avatar_garments WHERE avatar_id = %s AND garment_id = %s"
            cursor.execute(query, (avatar_id, garment_id))
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.mysql.connection.rollback()
            raise e
    
    def get_garment_link_by_id(self, garment_link_id):
        """Get garment link by ID"""
        cursor = self.mysql.connection.cursor()
        query = "SELECT * FROM avatar_garments WHERE id = %s"
        cursor.execute(query, (garment_link_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return AvatarGarment.from_dict(result)
        return None
    
    def get_avatar_garments(self, avatar_id):
        """Get all garments for an avatar"""
        cursor = self.mysql.connection.cursor()
        query = """
            SELECT ag.*, g.* 
            FROM avatar_garments ag
            LEFT JOIN garments g ON ag.garment_id = g.id
            WHERE ag.avatar_id = %s
        """
        cursor.execute(query, (avatar_id,))
        results = cursor.fetchall()
        cursor.close()
        
        return results
    
    def clear_avatar_garments(self, avatar_id):
        """Remove all garments from avatar"""
        try:
            cursor = self.mysql.connection.cursor()
            query = "DELETE FROM avatar_garments WHERE avatar_id = %s"
            cursor.execute(query, (avatar_id,))
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.mysql.connection.rollback()
            raise e