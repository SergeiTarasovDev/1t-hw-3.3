CREATE TABLE rates
(
	rate_id bigserial primary key,
	get_date date,
	rate_base varchar(5),
	rate_target varchar(5),
	rate numeric(18,8)
)