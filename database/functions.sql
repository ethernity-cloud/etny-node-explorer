-- for-windows

SET GLOBAL log_bin_trust_function_creators = 1;

delimiter //
drop function if exists get_missing_records_count;
CREATE function get_missing_records_count() returns LONGTEXT
    BEGIN
        declare _max INT DEFAULT 0;
        declare _count INT DEFAULT 0;
        SET _max = (select max(id) from dp_requests);
        SET _count = (select count(id) from dp_requests);
        return (if(_max, _max, 0)) - (if(_count, _count, 0));
    END//

delimiter //
drop function if exists get_missing_records;
CREATE function get_missing_records(last_id mediumint(3), per_page mediumint(3) unsigned) returns LONGTEXT
    BEGIN
        declare str LONGTEXT default '';
        declare _max INT DEFAULT 0;
        declare inline_query int default 0;
        declare fount_items INT DEFAULT 0;
        declare current_iter INT DEFAULT (if(last_id > 1,last_id + 2, last_id));
        
        SET _max = (select max(id) from dp_requests);

        WHILE current_iter < _max and fount_items < per_page
            DO
                SET inline_query=(select id from dp_requests where id = current_iter);
                if inline_query is null then
                    SET str = CONCAT(str,current_iter-1,',');
                    set fount_items = fount_items + 1;
                end if;
                set current_iter = current_iter + 1;
            END WHILE;

        return concat(fount_items,'-',current_iter,'-',_max,'-',str);
    END//

