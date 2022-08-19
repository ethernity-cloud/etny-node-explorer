select 
    d.id as real_id,
    (d.id + 1) as id, 
    (select min(id) from orders where id > d.id) as second,
    ((select min(id) from orders where id > d.id) - (id + 1)) as diff,
    -- sum(((select min(id) from orders where id > d.id) - (id + 1))) as _sum,
    d.block_identifier,
    (select concat(id,' - ', block_identifier) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier
from orders d 
where id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders)
order by d.id asc limit 100;



select 
    count(d.id)
from orders d 
where id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders);



select 
    (d.id + 1) as id, 
    block_identifier,
    (select min(block_identifier) from orders where block_identifier > d.block_identifier) as next_block_identifier
from orders d where id > -1 and not exists (select id from orders where id = d.id + 1)
and d.id < (select max(id) from orders)
order by d.id asc limit 100;
