SELECT DISTINCT * FROM
(SELECT name, 0 AS property
FROM transaction_details A
WHERE A.address_book_type = 'Business Entity'
UNION ALL
SELECT employer_name, 1 AS property
FROM transaction_details A
WHERE A.address_book_type = 'Individual') B;
