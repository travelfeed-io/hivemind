CREATE EXTENSION postgis;
CREATE INDEX is_tf ON hive_posts_cache(is_travelfeed);