-- queries used for the 2021 annual report
SELECT site, COUNT(*) FROM specimens WHERE year=2020 GROUP BY site;
SELECT COUNT(DISTINCT taxon) FROM specimens WHERE site='BRF';
SELECT * FROM v_affinis ORDER BY date;
