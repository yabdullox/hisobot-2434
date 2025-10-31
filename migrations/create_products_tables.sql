-- Ombor va sotilgan mahsulotlar uchun jadval
CREATE TABLE IF NOT EXISTS warehouse (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    quantity NUMERIC DEFAULT 0,
    unit TEXT DEFAULT 'dona',
    price BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sold_products (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    branch_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    amount NUMERIC NOT NULL,
    unit TEXT,
    price BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
