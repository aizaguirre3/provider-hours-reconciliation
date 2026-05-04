-- Seed data for departments and providers.

INSERT OR REPLACE INTO departments (department_code, department_name, utilization_target) VALUES
  ('CARD',  'Cardiology',         0.85),
  ('PEDS',  'Pediatrics',         0.80),
  ('MH',    'Mental Health',      0.75),
  ('DERM',  'Dermatology',        0.85),
  ('ORTHO', 'Orthopedics',        0.85),
  ('ENDO',  'Endocrinology',      0.80),
  ('IM',    'Internal Medicine',  0.85),
  ('FM',    'Family Medicine',    0.85);

INSERT OR REPLACE INTO providers
  (provider_id, npi, last_name, first_name, credentials, department_code, contracted_hours_per_week, hourly_rate, active) VALUES
  ('PROV001', '1245678901', 'CHEN',     'SARAH',   'MD', 'CARD',  40, 195.00, 1),
  ('PROV002', '1234567890', 'PATEL',    'JAMES',   'MD', 'CARD',  36, 195.00, 1),
  ('PROV003', '1098765432', 'KIM',      'LINDA',   'DO', 'PEDS',  32, 145.00, 1),
  ('PROV004', '1567894123', 'WONG',     'BRIAN',   'MD', 'ORTHO', 40, 220.00, 1),
  ('PROV005', '1234509876', 'ROSS',     'MICHAEL', 'MD', 'MH',    32, 175.00, 1),
  ('PROV006', '1876543210', 'DIAZ',     'ROBERT',  'MD', 'CARD',  24, 195.00, 1),
  ('PROV007', '1432109876', 'KHAN',     'AISHA',   'MD', 'MH',    36, 175.00, 1),
  ('PROV008', '1654321098', 'LEE',      'SUSAN',   'MD', 'DERM',  32, 165.00, 1),
  ('PROV009', '1789012345', 'SANTOS',   'MARIA',   'MD', 'ENDO',  40, 180.00, 1),
  ('PROV010', '1890123456', 'PARK',     'DANIEL',  'MD', 'IM',    40, 175.00, 1),
  ('PROV011', '1098374651', 'BROWN',    'OLIVIA',  'MD', 'IM',    36, 175.00, 1),
  ('PROV012', '1357913579', 'GARCIA',   'MARIA',   'NP', 'FM',    40, 110.00, 1),
  ('PROV013', '1234511111', 'WALLACE',  'HENRY',   'MD', 'PEDS',  24, 150.00, 0),
  ('PROV014', '1888888888', 'TORRES',   'ELENA',   'PA', 'FM',    40,  95.00, 1);
