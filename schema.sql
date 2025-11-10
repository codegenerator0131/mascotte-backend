-- Users table (already exists from auth system)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Avatars table
CREATE TABLE IF NOT EXISTS avatars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    bio TEXT,
    age INT NOT NULL,
    height DECIMAL(6,2) NOT NULL,
    height_unit ENUM('cm', 'in') NOT NULL DEFAULT 'cm',
    weight DECIMAL(6,2) NOT NULL,
    weight_unit ENUM('kg', 'lbs') NOT NULL DEFAULT 'kg',
    avatar_type ENUM('generic', 'biometric') NOT NULL,
    generic_avatar_style ENUM('classic', 'modern', 'casual', 'sporty') NULL,
    biometric_verified BOOLEAN DEFAULT FALSE,
    measurement_mode ENUM('auto', 'manual') NOT NULL,
    auto_estimated BOOLEAN DEFAULT FALSE,
    share_with_world BOOLEAN DEFAULT FALSE,
    create_assistant BOOLEAN DEFAULT FALSE,
    create_greeting_cards BOOLEAN DEFAULT FALSE,
    public_profile BOOLEAN DEFAULT FALSE,
    allow_connections BOOLEAN DEFAULT TRUE,
    selected_greeting_template VARCHAR(50) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_public_profile (public_profile),
    INDEX idx_avatar_type (avatar_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Body measurements table
CREATE TABLE IF NOT EXISTS body_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    avatar_id INT NOT NULL UNIQUE,
    chest DECIMAL(6,2) NULL,
    waist DECIMAL(6,2) NULL,
    hips DECIMAL(6,2) NULL,
    shoulder_width DECIMAL(6,2) NULL,
    inseam DECIMAL(6,2) NULL,
    arm_length DECIMAL(6,2) NULL,
    neck_size DECIMAL(6,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (avatar_id) REFERENCES avatars(id) ON DELETE CASCADE,
    INDEX idx_avatar_id (avatar_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Garments table
CREATE TABLE IF NOT EXISTS garments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    rating DECIMAL(3,2) DEFAULT 0.0,
    image_url TEXT,
    description TEXT,
    category VARCHAR(100),
    style VARCHAR(100),
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_brand (brand),
    INDEX idx_category (category),
    INDEX idx_style (style),
    INDEX idx_available (available),
    INDEX idx_rating (rating),
    FULLTEXT idx_search (name, brand, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Avatar garments junction table (wardrobe)
CREATE TABLE IF NOT EXISTS avatar_garments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    avatar_id INT NOT NULL,
    garment_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_avatar_garment (avatar_id, garment_id),
    FOREIGN KEY (avatar_id) REFERENCES avatars(id) ON DELETE CASCADE,
    FOREIGN KEY (garment_id) REFERENCES garments(id) ON DELETE CASCADE,
    INDEX idx_avatar_id (avatar_id),
    INDEX idx_garment_id (garment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample garments
INSERT INTO garments (name, brand, price, rating, image_url, description, category, style) VALUES
('Classic White T-Shirt', 'Uniqlo', 19.99, 4.5, '👕', 'A timeless white t-shirt made from premium cotton', 'tops', 'casual'),
('Slim Fit Jeans', 'Zara', 49.99, 4.3, '👖', 'Modern slim fit jeans with stretch fabric', 'bottoms', 'casual'),
('Running Shorts', 'Nike', 34.99, 4.7, '🩳', 'Performance running shorts with moisture-wicking technology', 'bottoms', 'sporty'),
('Blazer Jacket', 'H&M', 79.99, 4.2, '🧥', 'Professional blazer for business and formal occasions', 'outerwear', 'modern'),
('Summer Dress', 'Zara', 59.99, 4.6, '👗', 'Light and breezy summer dress perfect for warm weather', 'dresses', 'casual'),
('Hoodie', 'Adidas', 64.99, 4.4, '🧥', 'Comfortable hoodie with kangaroo pocket', 'outerwear', 'sporty');