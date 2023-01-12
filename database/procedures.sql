delimiter //
drop procedure if exists group_by_dp_requests;
create procedure if not exists group_by_dp_requests()
    begin
        insert into dp_unique_requests (
            id,
            dpRequestId,
            dproc,
            cpuRequest,
            memoryRequest,
            storageRequest,
            bandwidthRequest,
            duration,
            minPrice,
            `status`,
            createdAt,
            local_created_at,
            updated_at,
            nodes_count
        ) select
            max(id) as id,
            max(dpRequestId) as dpRequestId,
            dproc,
            cpuRequest,
            memoryRequest,
            storageRequest,
            bandwidthRequest,
            duration,
            minPrice,
            max(`status`) as `status`,
            createdAt,
            local_created_at,
            max(createdAt) as updated_at,
            count(id) as nodes_count
         from dp_requests group by dproc order by createdAt desc
            ON DUPLICATE KEY UPDATE
                id = values(id),
                dpRequestId = values(dpRequestId),
                cpuRequest = values(cpuRequest),
                memoryRequest = values(memoryRequest),
                storageRequest = values(storageRequest),
                bandwidthRequest = values(bandwidthRequest),
                duration = values(duration),
                minPrice = values(minPrice),
                `status` = values(`status`),
                createdAt = values(createdAt),
                local_created_at = values(local_created_at),
                updated_at = values(updated_at),
                nodes_count = values(nodes_count);
end //
