-- Active providers joined to their department metadata.
SELECT
  p.provider_id,
  p.npi,
  p.last_name,
  p.first_name,
  p.credentials,
  p.department_code,
  d.department_name,
  d.utilization_target,
  p.contracted_hours_per_week,
  p.hourly_rate
FROM providers p
JOIN departments d ON d.department_code = p.department_code
WHERE p.active = 1
ORDER BY d.department_code, p.last_name;
