-- Just provider IDs and names for active providers.
SELECT provider_id, last_name, first_name, department_code
FROM providers
WHERE active = 1
ORDER BY department_code, last_name;
