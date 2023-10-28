-- Задание 1. Расчет кумулятивной выручки:
--			  Для каждой категории товаров (category) вычислите кумулятивную выручку на каждый день. 
--			  Это означает, что для каждой даты вам нужно будет посчитать сумму выручки для данной категории товаров на эту дату и для всех предыдущих дат.
SELECT 
	s.order_date,
	s.category,
	s.product_name,
	s.revenue,
	sum(s.revenue) OVER(PARTITION BY s.category ORDER BY s.order_date, s.product_name) AS cumulative_revenue
FROM course_1t.sales AS s




-- Задание 2. Расчет среднего чека:
-- 			  Для каждой категории товаров на каждый день вычислите средний чек, который равен кумулятивной выручке на этот день, 
--			  поделенной на кумулятивное количество заказов на этот день.
SELECT 
	s.order_date,
	s.category,
	s.product_name,
	s.revenue,
	sum(s.revenue) OVER(PARTITION BY s.category ORDER BY s.order_date, s.product_name) AS cumulative_revenue,
	ROW_NUMBER() OVER(PARTITION BY s.category ORDER BY s.order_date, s.product_name) AS cumulative_orders,
	ROUND(cumulative_revenue / cumulative_orders) AS average_check
FROM course_1t.sales AS s




-- Задание 3. Определение даты максимального среднего чека:
--			  Найдите дату, на которой был достигнут максимальный средний чек для каждой категории товаров, а также значение этого максимального среднего чека.
WITH average_check_calc AS
(
	SELECT 
		s.order_date,
		s.category,
		s.product_name,
		s.revenue,
		sum(s.revenue) OVER(PARTITION BY s.category ORDER BY s.order_date, s.product_name) AS cumulative_revenue,
		ROW_NUMBER() OVER(PARTITION BY s.category ORDER BY s.order_date, s.product_name) AS cumulative_orders,
		ROUND(cumulative_revenue / cumulative_orders) AS average_check
	FROM course_1t.sales AS s
),
max_avg_value_calc AS
(
	SELECT
		acc.order_date,
		acc.category,
		acc.product_name,
		acc.revenue,
		acc.cumulative_revenue,
		acc.cumulative_orders,
		acc.average_check,
		max(acc.average_check) OVER(PARTITION BY acc.category) AS max_avg_check_value
	FROM average_check_calc AS acc
)
SELECT
	m.order_date,
	m.category,
	m.product_name,
	m.revenue,
	m.cumulative_revenue,
	m.cumulative_orders,
	m.average_check,
	m.max_avg_check_value,
	macd.max_avg_check_date
FROM max_avg_value_calc AS m
INNER JOIN
	(
		SELECT order_date AS max_avg_check_date, category
		 FROM max_avg_value_calc
		 WHERE max_avg_check_value = average_check
	) AS macd
	ON macd.category = m.category
