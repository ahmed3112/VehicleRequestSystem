CREATE TABLE IF NOT EXISTS lines (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles (
  id TEXT PRIMARY KEY,
  parking_name TEXT,
  plate_number TEXT,
  owner_name TEXT,
  chassis TEXT,
  line_id TEXT,
  phone TEXT,
  card_no TEXT,
  passengers INTEGER,
  license_image TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (line_id) REFERENCES lines(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_vehicles_line ON vehicles(line_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(plate_number);
