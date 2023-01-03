

-- dpRequest
drop table if exists dp_requests;
create table if not exists dp_requests (
    id bigint(20) unsigned primary key,
    dpRequestId bigint(20) UNIQUE default 0,
    dproc varchar(70) not null default '' comment 'address',
    cpuRequest tinyint unsigned not null default 0,
    memoryRequest tinyint unsigned not null default 0,
    storageRequest tinyint unsigned not null default 0,
    bandwidthRequest tinyint unsigned not null default 0,
    duration tinyint unsigned not null default 0,
    minPrice tinyint unsigned not null default 0,
    `status` tinyint unsigned not null default 0,

    createdAt int(11) not null default 0,
    -- local dates
    local_created_at int(11) not null default unix_timestamp(),

    index dp_requests_dproc_idx(dproc),
    index dp_requests_dpRequestId_idx(dpRequestId),
    index dp_requests_createdAt_idx(createdAt)
);