
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
    (select block_identifier || '-' || (block_identifier - d.block_identifier) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier
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
    -- if(o1.created_on, from_unixtime(o1.created_on), '') as created_on_date,
    o2.block_identifier as block_identifier2,
    o2.last_updated,
    -- if(o2.last_updated, from_unixtime(o2.last_updated), '') as last_updated_date,
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


select 
    o1.id,
    o1.block_identifier,
    d.address,
    d.cpu,
    d.memory,
    d.storage,
    d.bandwith,
    d.duration,
    d.status,
    d.cost,
    o1.created_on,
    (select (case when last_updated then last_updated else created_on end) from orders where id = o2.parent_id order by id desc) as last_updated,
    count(o2.address) as updates_count
from orders_details d 
join (select * from orders order by created_on asc) o1 on o1.id = d.parent_id
join (select * from orders_details order by id desc) o2 on o2.parent_id = d.parent_id
-- join (select * from orders order by last_updated desc) o3 on o3.id = d.parent_id
where d.address in ('0xfB8aAb6608E96E901630AD1D5de2c47C2710EAf1')
group by d.address;

select 
    o1.id,
    o1.block_identifier,
    d.address,
    d.cpu,
    d.memory,
    d.storage,
    d.bandwith,
    d.duration,
    d.status,
    d.cost,
    o1.created_on,
    -- (select (case when last_updated then last_updated else created_on end) from orders where id = d.parent_id order by id desc) as last_updated,
    (case o3.last_updated then o3.last_updated else o3.created_on) as last_updated,
    count(o2.address) as updates_count
from orders_details d 
join (select * from orders order by created_on asc) o1 on o1.id = d.parent_id
join (select * from orders_details order by id desc) o2 on o2.parent_id = d.parent_id
join (select * from orders order by last_updated desc) o3 on o3.id = d.parent_id
group by d.address order by d.id 
limit 20;


select 
    count(distinct d.address)
from orders o
join orders_details d on d.parent_id = o.id




select 
    o1.id,
    o1.block_identifier,
    d.address,
    d.cpu,
    d.memory,
    d.storage,
    d.bandwith,
    d.duration,
    d.status,
    d.cost,
    o1.created_on,
    group_concat(o1.last_updated) as sms,
    max(o1.last_updated) as last_updated,
    count(o2.address) as updates_count
from orders_details d 
join (select * from orders order by created_on asc) o1 on o1.id = d.parent_id
join (select * from orders_details order by id desc) o2 on o2.parent_id = d.parent_id
where d.address in ('0xfB8aAb6608E96E901630AD1D5de2c47C2710EAf1')
group by d.address order by d.id;



