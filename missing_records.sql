
select 
    d.id as real_id,
    (d.id + 1) as missing_id_from, 
    (select min(id) from orders where id > d.id) as next_id,
    ((select min(id) from orders where id > d.id) - (id + 1)) as diff,
    d.block_identifier,
    (select concat(block_identifier, '-', (block_identifier - d.block_identifier)) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier
from orders d 
where d.id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders) 
order by d.id asc limit 10;


select 
    d.id as real_id,
    (d.id + 1) as missing_id_from, 
    (select min(id) from orders where id > d.id) as next_id,
    ((select min(id) from orders where id > d.id) - (id + 1)) as diff,
    d.block_identifier,
    (select concat(block_identifier, '-', (block_identifier - d.block_identifier)) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier
from orders d 
where id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders)
and d.id = 1208
order by d.id;


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
order by d.id asc limit 0, 10;



select 
    o1.id,
    o1.block_identifier,
    o1.created_on,
    if(o1.created_on, from_unixtime(o1.created_on), '') as created_on_date,
    o2.block_identifier as block_identifier2,
    o2.last_updated,
    if(o2.last_updated, from_unixtime(o2.last_updated), '') as last_updated_date,
    d.address,
    d.cpu,
    d.memory,
    d.storage,
    d.bandwith,
    d.duration,
    d.status,
    d.cost
from orders_details d 
join (select * from orders order by created_on asc) o1 on o1.id = d.parent_id
join (select * from orders order by last_updated desc) o2 on o2.id = d.parent_id
group by d.address
limit 20;


select 
    count(distinct d.address)
from orders o
join orders_details d on d.parent_id = o.id