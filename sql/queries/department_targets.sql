-- Department roster size and total contracted weekly hours.
SELECT
  d.department_code,
  d.department_name,
  d.utilization_target,
  COUNT(p.provider_id) AS active_providers,
  SUM(p.contracted_hours_per_week) AS total_contracted_hours
FROM departments d
LEFT JOIN providers p
  ON p.department_code = d.department_code AND p.active = 1
GROUP BY d.department_code, d.department_name, d.utilization_target
ORDER BY d.department_code;
