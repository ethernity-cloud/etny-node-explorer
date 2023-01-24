
-- dpRequest
-- drop table if exists dp_requests;
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
    local_created_at int(11) unsigned not null default (cast(unix_timestamp() as unsigned)),

    index dp_requests_dproc_idx(dproc),
    index dp_requests_dpRequestId_idx(dpRequestId),
    index dp_requests_createdAt_idx(createdAt)
);

drop table if exists dp_unique_requests;
create table if not exists dp_unique_requests (
    id bigint(20) unsigned not null default 0,
    dpRequestId bigint(20) UNIQUE default 0,
    dproc varchar(70) unique not null default '' comment 'address',
    cpuRequest tinyint unsigned not null default 0,
    memoryRequest tinyint unsigned not null default 0,
    storageRequest tinyint unsigned not null default 0,
    bandwidthRequest tinyint unsigned not null default 0,
    duration tinyint unsigned not null default 0,
    minPrice tinyint unsigned not null default 0,
    `status` tinyint unsigned not null default 0,

    createdAt int(11) not null default 0,
    -- local dates
    local_created_at int(11) unsigned not null default (cast(unix_timestamp() as unsigned)),
    updated_at int(11) not null default 0,
    nodes_count mediumint unsigned default 0,

    index dp_requests_dproc_idx(dproc),
    index dp_requests_dpRequestId_idx(dpRequestId),
    index dp_requests_createdAt_idx(createdAt),
    index dp_requests_updated_at_idx(updated_at)
);